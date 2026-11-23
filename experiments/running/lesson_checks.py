"""Re-checks two lessons about running Blender: does Blender's bundled Python have Pillow (and what image tools it does
have), and does a Python atexit hook run when a headless Blender quits?

Run with the system Python:  python3 experiments/running/lesson_checks.py
"""
import datetime
import json
import os
import platform
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from run import blender  # noqa: E402

B = blender()
TMP = tempfile.mkdtemp(prefix="bfg-lessons-")
facts = []


def fact(sentence, **numbers):
    facts.append(dict(fact=sentence, **numbers))
    print("FACT", sentence, numbers, flush=True)


probe = os.path.join(TMP, "mods.py")
open(probe, "w").write(
    "import importlib, json\n"
    "out = {}\n"
    "for m in ('PIL', 'numpy', 'OpenImageIO', 'imageio', 'cv2', 'scipy', 'requests', 'MaterialX'):\n"
    "    try:\n"
    "        mod = importlib.import_module(m); out[m] = getattr(mod, '__version__', 'present')\n"
    "    except Exception as e:\n"
    "        out[m] = None\n"
    "print('MODS', json.dumps(out))\n")
r = subprocess.run([B, "-b", "--factory-startup", "--python", probe], capture_output=True, text=True)
mods = json.loads([l for l in r.stdout.splitlines() if l.startswith("MODS")][0][5:])
fact("Python packages bundled with Blender 4.5 (None = not importable): no Pillow; numpy and OpenImageIO are there",
     **mods)

marker = os.path.join(TMP, "atexit.txt")
script = os.path.join(TMP, "atexit_probe.py")
open(script, "w").write(f"import atexit\natexit.register(lambda: open({marker!r}, 'w').write('ran'))\nprint('registered')\n")
results = {}
for label, args in (("script ends normally", []), ("script calls sys.exit(0)", ["--python-expr", "import sys; sys.exit(0)"])):
    if os.path.exists(marker):
        os.remove(marker)
    subprocess.run([B, "-b", "--factory-startup", "--python", script] + args, capture_output=True, text=True)
    results[label] = os.path.exists(marker)
fact("Does a Python atexit hook run when headless Blender quits? (True = the hook's file was written)", **results)

rec = dict(experiment=os.path.relpath(os.path.abspath(__file__), ROOT),
           blender=subprocess.run([B, "--version"], capture_output=True, text=True).stdout.splitlines()[0],
           machine=f"{platform.system()} {platform.machine()}", date=datetime.date.today().isoformat(), facts=facts)
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results"), exist_ok=True)
json.dump(rec, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "lesson_checks.json"), "w"), indent=1)
print("SAVED")
