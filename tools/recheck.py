#!/usr/bin/env python3
"""Run the experiments again and list the facts whose numbers changed: how this guide notices that a new Blender (or
another machine) no longer behaves as written.

  python3 tools/recheck.py [AREA ...] [--only NAME] [--timeout S] [--update]

Each experiment is re-run the way it ran (the arguments its result recorded; for older results without them, the
suffix of the result's file name, e.g. boolean_solvers-30.json -> 30). The stored results are what the area pages cite,
so they are put back after the comparison; --update keeps the new ones instead (then update the pages). This prints a
summary: facts unchanged, changed (with the old and new numbers), new, gone, and experiments that failed. Timings are compared loosely (within a factor of 2); everything else exactly, floats to 0.1 %.
"""
import glob
import json
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
TIMING = re.compile(r"(^|_)(s|ms|sec|secs|seconds|time|times|fps|per_s|speed|duration)($|_)|seconds|_s$|_ms$|"
                    r"\btakes\b|\bfaster\b|\bslower\b|\bhow long\b")
MEMORY = re.compile(r"memory|\bmb\b|_mb$|\bgb\b|_gb$|rss")


def same(key, a, b, kind=None):
    """kind: 'time' (within a factor of 2), 'mem' (within 10 %), else exact (floats to 0.1 %)."""
    kind = kind or ("time" if TIMING.search(key.lower()) else "mem" if MEMORY.search(key.lower()) else None)
    if isinstance(a, bool) or isinstance(b, bool) or a is None or b is None:
        return a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if kind == "time":
            return (a == b) or (min(a, b) > 0 and max(a, b) / min(a, b) <= 2) or abs(a - b) < 0.05
        if kind == "mem":
            return abs(a - b) <= 0.1 * max(abs(a), abs(b))
        return abs(a - b) <= max(1e-6, 1e-3 * max(abs(a), abs(b)))
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same(key, x, y, kind) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(same(f"{key}.{k}", a[k], b[k], kind) for k in a)
    return a == b


def facts_of(path):
    try:
        rec = json.load(open(path))
    except (OSError, ValueError):
        return None, []
    return rec, {f["fact"]: {k: v for k, v in f.items() if k != "fact"} for f in rec.get("facts", [])}


def runs_for(script):
    """(result path, args) pairs: one per result this experiment wrote before."""
    rel = os.path.relpath(script, ROOT)
    name = os.path.splitext(os.path.basename(script))[0]
    out = []
    for r in glob.glob(os.path.join(os.path.dirname(script), "results", f"{name}*.json")):
        rec, _ = facts_of(r)
        if not rec or rec.get("experiment", rel) != rel:
            continue
        base = os.path.splitext(os.path.basename(r))[0]
        args = rec.get("args")
        if args is None:
            args = [base[len(name) + 1:]] if base != name and base.startswith(name + "-") else []
        out.append((r, args))
    return out or [(os.path.join(os.path.dirname(script), "results", f"{name}.json"), [])]


def main():
    a = sys.argv[1:]
    only = a[a.index("--only") + 1] if "--only" in a else None
    timeout = a[a.index("--timeout") + 1] if "--timeout" in a else "900"
    areas = [x for i, x in enumerate(a) if not x.startswith("--") and (i == 0 or a[i - 1] not in ("--only", "--timeout"))]
    scripts = sorted(glob.glob(os.path.join(ROOT, "experiments", "*", "*.py")))
    if areas:
        scripts = [s for s in scripts if os.path.basename(os.path.dirname(s)) in areas]
    if only:
        scripts = [s for s in scripts if os.path.splitext(os.path.basename(s))[0] == only]
    totals = dict(unchanged=0, changed=0, new=0, gone=0, failed=0)
    for script in scripts:
        src = open(script).read()
        inside = "exp.Experiment(" in src
        for result, args in runs_for(script):
            _, before = facts_of(result)
            stored = open(result, "rb").read() if os.path.exists(result) else None
            cmd = ([sys.executable, os.path.join(ROOT, "tools", "run.py"), script, "--timeout", timeout, "--"] + args
                   if inside else [sys.executable, script] + args)
            r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
            label = os.path.relpath(result, ROOT)
            if r.returncode != 0:
                if stored is not None:
                    open(result, "wb").write(stored)
                totals["failed"] += 1
                tail = (r.stderr or r.stdout).strip().splitlines()[-3:]
                print(f"FAILED  {label}\n        " + "\n        ".join(tail))
                continue
            _, after = facts_of(result)
            for fact, nums in after.items():
                if fact not in before:
                    totals["new"] += 1
                    print(f"NEW     {label}: {fact}")
                    continue
                kind = "time" if TIMING.search(fact.lower()) else "mem" if MEMORY.search(fact.lower()) else None
                diffs = {k: (before[fact].get(k), v) for k, v in nums.items()
                         if not same(k, before[fact].get(k), v, kind)}
                if diffs:
                    totals["changed"] += 1
                    print(f"CHANGED {label}: {fact}")
                    for k, (o, n) in diffs.items():
                        print(f"        {k}: {json.dumps(o)} -> {json.dumps(n)}")
                else:
                    totals["unchanged"] += 1
            for fact in before:
                if fact not in after:
                    totals["gone"] += 1
                    print(f"GONE    {label}: {fact}")
            if stored is not None and "--update" not in sys.argv:
                open(result, "wb").write(stored)
    print("\n" + ", ".join(f"{k} {v}" for k, v in totals.items()))
    sys.exit(1 if totals["changed"] or totals["failed"] or totals["gone"] else 0)


if __name__ == "__main__":
    main()
