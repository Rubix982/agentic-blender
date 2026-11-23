"""The Blender process itself: memory of a headless job, what a crash leaves behind, the --command subcommands, and
whether bpy can be used as a plain Python module here.

Run with the system Python:  python3 experiments/running/process.py
Writes experiments/running/results/process.json.
"""
import datetime
import glob
import json
import os
import platform
import re
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from run import blender  # noqa: E402

B = blender()
TMP = tempfile.mkdtemp(prefix="bfg-proc-")
facts, data = [], {}


def fact(sentence, **numbers):
    facts.append(dict(fact=sentence, **numbers))
    print("FACT", sentence, numbers, flush=True)


def script(name, body):
    p = os.path.join(TMP, name)
    open(p, "w").write(body)
    return p


def peak_rss_mb(args):
    """Peak resident memory of a Blender run, from /usr/bin/time -l (macOS reports bytes)."""
    r = subprocess.run(["/usr/bin/time", "-l", B] + args, capture_output=True, text=True, timeout=600)
    m = re.search(r"(\d+)\s+maximum resident set size", r.stderr)
    return (round(int(m.group(1)) / 2**20) if m else None), r


version = subprocess.run([B, "--version"], capture_output=True, text=True).stdout.splitlines()[0]

# 1. Memory.
jobs = {
    "empty script, factory file": "pass",
    "1M-vertex grid mesh": "import bpy\nbpy.ops.mesh.primitive_grid_add(x_subdivisions=1000, y_subdivisions=1000)\n",
    "Cycles render 512 px, 64 samples, CPU": (
        "import bpy\ns=bpy.context.scene; s.render.engine='CYCLES'; s.cycles.samples=64\n"
        "s.render.resolution_x=s.render.resolution_y=512; s.render.filepath='" + os.path.join(TMP, "r.png") + "'\n"
        "bpy.ops.render.render(write_still=True)\n"),
}
mem = {}
for label, body in jobs.items():
    mb, _ = peak_rss_mb(["-b", "--factory-startup", "--python", script(f"m{len(mem)}.py", body)])
    mem[label] = mb
fact("Peak memory (resident) of a headless Blender job, in MB", **mem)

# 2. A crash.
before = set(glob.glob(os.path.join(tempfile.gettempdir(), "*.crash.txt")))
t0 = time.time()
r = subprocess.run([B, "-b", "--factory-startup", "--python-expr", "import ctypes; ctypes.string_at(0)"],
                   capture_output=True, text=True, timeout=120)
after = [p for p in glob.glob(os.path.join(tempfile.gettempdir(), "*.crash.txt")) if os.path.getmtime(p) >= t0 - 1]
crash_head = open(after[0]).read().splitlines()[:6] if after else None
data["crash"] = dict(returncode=r.returncode, crash_files=[os.path.basename(p) for p in after], head=crash_head,
                     stderr_tail=r.stderr.splitlines()[-5:], stdout_tail=r.stdout.splitlines()[-5:])
fact("A segmentation fault in a headless run ends Blender with a negative return code (the signal); Blender prints "
     "'Writing: <path>' and leaves a backtrace in the system temp folder (blender.crash.txt with no file open)",
     returncode=r.returncode, crash_file=[os.path.basename(p) for p in after],
     temp_folder="$TMPDIR (tempfile.gettempdir())")

# 3. The --command subcommands (4.2+).
r = subprocess.run([B, "--factory-startup", "--command", "help"], capture_output=True, text=True, timeout=60)
cmds = [l.strip() for l in r.stdout.splitlines() if l.startswith("\t") or l.startswith("    ")]
data["command_help"] = [l for l in r.stdout.splitlines() if not l.startswith("[")][:40]
r2 = subprocess.run([B, "--factory-startup", "--command", "extension", "--help"], capture_output=True, text=True, timeout=60)
data["extension_help"] = r2.stdout.splitlines()[:40]
fact("blender --command runs a named subcommand without a scene; 4.5 lists these", listed=cmds[:20])

# 4. bpy as a module from PyPI.
try:
    req = urllib.request.Request("https://pypi.org/pypi/bpy/json", headers={"User-Agent": "python-client"})
    info = json.load(urllib.request.urlopen(req, timeout=30))
    rel = info["releases"]
    v45 = sorted(k for k in rel if k.startswith("4.5"))
    files = rel[v45[-1]] if v45 else []
    data["pypi_bpy"] = dict(latest=info["info"]["version"], v45=v45,
                            files_4_5=[f["filename"] for f in files], requires_python=info["info"].get("requires_python"))
    tags = sorted({re.search(r"-(cp\d+)-", f["filename"]).group(1) for f in files if re.search(r"-(cp\d+)-", f["filename"])})
    fact("bpy, Blender as a Python module, is on PyPI; its 4.5 wheels are built for one Python version only",
         latest=info["info"]["version"], newest_4_5=v45[-1] if v45 else None, python_tags=tags,
         mac_arm=[f["filename"] for f in files if "macosx" in f["filename"] and "arm64" in f["filename"]])
except Exception as e:  # noqa: BLE001
    data["pypi_bpy"] = repr(e)

rec = dict(experiment=os.path.relpath(os.path.abspath(__file__), ROOT), blender=version,
           machine=f"{platform.system()} {platform.machine()}", date=datetime.date.today().isoformat(), facts=facts, data=data)
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results"), exist_ok=True)
json.dump(rec, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "process.json"), "w"), indent=1)
print("SAVED")
