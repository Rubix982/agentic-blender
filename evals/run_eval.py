#!/usr/bin/env python3
"""Run the held-out tasks (evals/tasks.md) with the skill and without it, and score each first script.

  python3 evals/run_eval.py [--set writer|independent] [--tasks 1-10] [--arms with,without] [--runs 1] [--model MODEL]
                            [--max-turns 40]

--set writer (default) uses evals/tasks.md and evals/checks.py; --set independent uses evals/independent/tasks.md and
evals/independent/checks.py, written by an agent that never saw the guide. The card's claim rests on the independent set.

For each task, arm and run: a fresh `claude -p` session in an empty folder gets the task. The "with" arm loads this
plugin through --plugin-dir (a copy without evals/, so the checks can't be read); the "without" arm loads nothing.
The agent writes ./task.py and must not run Blender; this script then runs task.py exactly once, headless, and grades
what it saved with evals/checks.py. "Right first time" = the script exits 0 and its output passes the check.

Each session is a full Claude Code run on the user's account: 10 tasks x 2 arms is 20 sessions. Ask before running.
Results: evals/runs/<timestamp>/results.jsonl and summary.md (git-ignored transcripts stay beside them).
"""
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from run import blender  # noqa: E402

OUT_EXT = {1: ".glb", 9: ".exr"}
PROMPT = """Write a Python script for Blender 4.5 that does the task below.

Your script will be run exactly once, headless, by this command (do not run Blender yourself):
    {blender} -b --factory-startup --python-exit-code 1 --python task.py -- OUTPUT_PATH
The output path is the first argument after '--' in sys.argv. Write the script to ./task.py in the current folder,
then stop and say it is written. Its first run is what counts.

Task:
{task}
"""


SETS = {"writer": (os.path.join(HERE, "tasks.md"), os.path.join(HERE, "checks.py")),
        "independent": (os.path.join(HERE, "independent", "tasks.md"), os.path.join(HERE, "independent", "checks.py"))}
TASKS_MD, CHECKS = SETS["writer"]


def tasks():
    text = open(TASKS_MD).read().split("## Order of work")[0]
    items = re.split(r"(?m)^(\d+)\. ", text)[1:]
    return {int(items[i]): re.sub(r"\s+", " ", items[i + 1]).strip() for i in range(0, len(items), 2)}


def plugin_copy(dest):
    """The plugin as the with-arm sees it: everything but the held-out tasks and checks."""
    shutil.copytree(ROOT, dest, ignore=shutil.ignore_patterns(".git", "evals", "__pycache__", "*.blend1"))
    return dest


def transcript_facts(lines):
    skill_used = blender_called = False
    usage, cost, turns = {}, None, None
    for line in lines:
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        msg = ev.get("message") or {}
        for part in msg.get("content", []) if isinstance(msg.get("content"), list) else []:
            if part.get("type") == "tool_use":
                inp = json.dumps(part.get("input", {}))
                if part.get("name") == "Skill" or "SKILL.md" in inp or "kb.py" in inp:
                    skill_used = True
                if part.get("name") == "Bash" and re.search(r"Blender(\.app)?/Contents/MacOS/Blender|\bblender\b.*-b", inp):
                    blender_called = True
        if ev.get("type") == "result":
            usage, cost, turns = ev.get("usage", {}), ev.get("total_cost_usd"), ev.get("num_turns")
    return dict(skill_used=skill_used, agent_ran_blender=blender_called, cost_usd=cost, turns=turns,
                output_tokens=usage.get("output_tokens"))


def main():
    global TASKS_MD, CHECKS
    a = sys.argv[1:]
    which = a[a.index("--set") + 1] if "--set" in a else "writer"
    TASKS_MD, CHECKS = SETS[which]
    pick = a[a.index("--tasks") + 1] if "--tasks" in a else "1-10"
    lo, _, hi = pick.partition("-")
    wanted = range(int(lo), int(hi or lo) + 1)
    arms = (a[a.index("--arms") + 1] if "--arms" in a else "with,without").split(",")
    runs = int(a[a.index("--runs") + 1]) if "--runs" in a else 1
    model = a[a.index("--model") + 1] if "--model" in a else None
    max_turns = a[a.index("--max-turns") + 1] if "--max-turns" in a else "40"
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    base = os.path.join(HERE, "runs", f"{stamp}-{which}")
    os.makedirs(base)
    plugin = plugin_copy(os.path.join(base, "plugin")) if "with" in arms else None
    B = blender()
    T = tasks()
    results = []
    for n in wanted:
        for arm in arms:
            for r in range(runs):
                work = os.path.join(base, f"task{n}-{arm}-{r}")
                os.makedirs(work)
                cmd = ["claude", "-p", PROMPT.format(blender=B, task=T[n]), "--output-format", "stream-json", "--verbose",
                       "--allowedTools", "Read,Write,Edit,Glob,Grep,Bash,Skill", "--max-turns", max_turns]
                if model:
                    cmd += ["--model", model]
                if arm == "with":
                    cmd += ["--plugin-dir", plugin]
                t = time.time()
                p = subprocess.run(cmd, cwd=work, capture_output=True, text=True, timeout=1800)
                open(os.path.join(work, "transcript.jsonl"), "w").write(p.stdout)
                info = transcript_facts(p.stdout.splitlines())
                rec = dict(task=n, arm=arm, run=r, agent_seconds=round(time.time() - t, 1), **info)
                script = os.path.join(work, "task.py")
                out = os.path.join(work, f"out{OUT_EXT.get(n, '.blend')}")
                if not os.path.exists(script):
                    rec.update(script_written=False, script_ran=False, check_passed=False, reasons=["no task.py"])
                else:
                    run = subprocess.run([B, "-b", "--factory-startup", "--python-exit-code", "1", "--python", script,
                                          "--", out], cwd=work, capture_output=True, text=True, timeout=900)
                    open(os.path.join(work, "run.log"), "w").write(run.stdout + run.stderr)
                    chk = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "run.py"),
                                          CHECKS, "--", str(n), out],
                                         capture_output=True, text=True, timeout=600)
                    line = [l for l in chk.stdout.splitlines() if l.startswith("CHECK ")]
                    verdict = json.loads(line[0][6:]) if line else dict(passed=False, reasons=["check did not run"])
                    rec.update(script_written=True, script_ran=run.returncode == 0, run_exit=run.returncode,
                               check_passed=bool(verdict.get("passed")) and run.returncode == 0,
                               reasons=verdict.get("reasons"), numbers=verdict.get("numbers"))
                rec["right_first_time"] = rec["check_passed"]
                results.append(rec)
                print(json.dumps({k: rec[k] for k in ("task", "arm", "run", "right_first_time", "skill_used",
                                                      "agent_ran_blender", "cost_usd")}), flush=True)
                with open(os.path.join(base, "results.jsonl"), "a") as f:
                    f.write(json.dumps(rec, default=str) + "\n")
    lines = ["| task | " + " | ".join(arms) + " |", "|---|" + "---|" * len(arms)]
    for n in wanted:
        cells = []
        for arm in arms:
            rs = [x for x in results if x["task"] == n and x["arm"] == arm]
            cells.append(f"{sum(x['right_first_time'] for x in rs)}/{len(rs)}")
        lines.append(f"| {n} | " + " | ".join(cells) + " |")
    totals = {arm: sum(x["right_first_time"] for x in results if x["arm"] == arm) for arm in arms}
    lines.append("| total | " + " | ".join(str(totals[arm]) for arm in arms) + " |")
    open(os.path.join(base, "summary.md"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
