"""C-003's second pass: the add-ons whose operators did nothing with default settings on one cube
(results/top_addons.json), given the input each is made for: A.N.T. Landscape with its `refresh` flag set, Bool Tool
with a canvas and a cutter selected, F2 with a hole's boundary selected, Sapling with leaves.

Run with the system Python, after top_addons.py (it uses the packages that run cached and checked):
    python3 experiments/extensions/targeted_addons.py
Same containment as top_addons.py: a throwaway profile under /private/tmp, and Blender inside macOS sandbox-exec with
no network, no writes under the home folder, no launching other programs, no opening URLs or apps.
Writes experiments/extensions/results/targeted_addons.json.
"""
import datetime
import glob
import json
import os
import platform
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from run import blender  # noqa: E402

CACHE = os.path.expanduser("~/.cache/agentic-blender/extensions")
PROBE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "probe", "targeted.py")
B = os.path.realpath(blender())
APP = B.split("/Contents/MacOS/")[0]
SLUGS = ("antlandscape", "bool-tool", "f2", "sapling-tree-gen")

zips = {}
for s in SLUGS:
    found = sorted(glob.glob(os.path.join(CACHE, f"add-on-{s}-v*.zip")))
    if not found:
        raise SystemExit(f"no cached package for {s}: run top_addons.py first")
    zips[s] = found[-1]

prof = tempfile.mkdtemp(prefix="ab-ext-", dir="/private/tmp")
sb = os.path.join(prof, "sandbox.sb")
open(sb, "w").write(f"""(version 1)
(allow default)
(deny network*)
(deny file-write* (subpath "{os.path.expanduser('~')}"))
(allow file-write* (subpath "{prof}"))
(deny lsopen)
(deny appleevent-send)
(deny process-exec)
(allow process-exec (subpath "{APP}"))
""")
env = dict(os.environ, BLENDER_USER_RESOURCES=prof)


def boxed(args, timeout):
    return subprocess.run(["sandbox-exec", "-f", sb, B] + args, env=env, cwd=prof, capture_output=True, text=True,
                          timeout=timeout)


installed = {}
for s, z in zips.items():
    p = boxed(["--factory-startup", "-c", "extension", "install-file", "-r", "user_default", z], 300)
    installed[s] = p.returncode == 0
out = os.path.join(prof, "targeted.json")
p = boxed(["-b", "--factory-startup", "--python-exit-code", "1", "--python", PROBE, "--", out], 900)
cases = json.load(open(out)) if os.path.exists(out) else [dict(error=(p.stdout + p.stderr)[-600:])]

facts = [dict(fact="the four packages installed into the throwaway profile", installed=installed,
              packages=[os.path.basename(z) for z in zips.values()])]
for c in cases:
    facts.append(dict(fact=f"{c.get('addon')}: {c.get('what')}", **{k: v for k, v in c.items() if k not in ("addon", "what")}))
    print("FACT", facts[-1]["fact"], c.get("result"), c.get("changed"), flush=True)
version = subprocess.run([B, "-b", "--factory-startup", "--version"], capture_output=True, text=True).stdout.split()[1]
rec = dict(experiment=os.path.relpath(os.path.abspath(__file__), ROOT), blender=version,
           machine=f"{platform.system()} {platform.machine()}", date=datetime.date.today().isoformat(), facts=facts,
           data={})
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results"), exist_ok=True)
text = json.dumps(rec, indent=1, default=str).replace(os.path.expanduser("~"), "~")
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "targeted_addons.json"), "w").write(text)
