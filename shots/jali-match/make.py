"""The jali match, start to finish: read the photo, predict its normals, build and render, compare.

    python3 shots/jali-match/make.py [--force-normals] [-- build.py's options]
Runs, from the repo's root:
  1. normals.py      in the repo's .venv: Marigold's normals (out/normals.npy), skipped when they are newer than the
                     photo and normals.py, unless --force-normals
  1b. intrinsics.py in the .venv: Marigold's albedo of the photo (out/albedo.npy), skipped when up to date
  2. read_photo.py   in Blender: the photo sorted into surround, opening and stone, the normals vetoing fragments of
                     lit rim (results/read_photo.json)
  3. build.py        in Blender: the screen built, lit and rendered (out/render.png, results/build.json); anything
                     after -- is passed to it (e.g. --forms shading --no-normal-map for C-009's version)
  4. compare.py      in Blender: the measures and the sheet (results/compare.json, sheet.jpg)
Stops at the first step that fails. The .venv, once: python3.12 -m venv .venv &&
.venv/bin/pip install -r shots/jali-match/requirements.txt"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import shot  # noqa: E402  (C-022: JALI_SHOT=<folder> runs the chain on that folder's photo)
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
RUN = os.path.join(ROOT, "skills", "blender", "scripts", "run.py")
VENV_PY = os.path.join(ROOT, ".venv", "bin", "python")
argv = sys.argv[1:]
build_args = argv[argv.index("--") + 1:] if "--" in argv else []
force = "--force-normals" in argv


def step(name, cmd):
    t = time.time()
    print(f"== {name}", flush=True)
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode:
        raise SystemExit(f"{name} failed (exit {r.returncode}); stopping")
    print(f"== {name}: {time.time() - t:.0f} s", flush=True)


def blender(script, timeout, extra=()):
    return [sys.executable, RUN, os.path.join(HERE, script), "--timeout", str(timeout)] + (["--", *extra] if extra else [])


npy = os.path.join(shot.OUT, "normals.npy")
inputs = [shot.PHOTO, os.path.join(HERE, "normals.py")]
fresh = os.path.exists(npy) and os.path.getmtime(npy) > max(os.path.getmtime(p) for p in inputs)
if force or not fresh:
    if not os.path.exists(VENV_PY):
        raise SystemExit("no .venv: python3.12 -m venv .venv && .venv/bin/pip install -r shots/jali-match/requirements.txt")
    step("normals", [VENV_PY, os.path.join(HERE, "normals.py")])
else:
    print("== normals: out/normals.npy is newer than the photo and normals.py; kept (--force-normals to redo)")
alb = os.path.join(shot.OUT, "albedo.npy")
ins = [shot.PHOTO, os.path.join(HERE, "intrinsics.py")]
if force or not (os.path.exists(alb) and os.path.getmtime(alb) > max(os.path.getmtime(p) for p in ins)):
    step("intrinsics", [VENV_PY, os.path.join(HERE, "intrinsics.py")])  # C-015: the stone's albedo
else:
    print("== intrinsics: out/albedo.npy is newer than the photo and intrinsics.py; kept (--force-normals to redo)")
step("read_photo", blender("read_photo.py", 300))                     # after the normals: its rule uses them (C-012)
step("build", blender("build.py", 1800, build_args))
step("compare", blender("compare.py", 300))
res = json.load(open(os.path.join(shot.RESULTS, "compare.json")))
print(json.dumps(dict(openings_iou=res["openings_iou"], thin_stone_shown=res["thin_stone_shown"],
                      forms_band=res["detail"]["forms"], frame_texture={k: v["ratio"] for k, v in res["frame_texture"].items()},
                      stone_p90=[res["render"]["stone_y"][2], res["photo"]["stone_y"][2]]), indent=1))
print("sheet:", shot.SHEET)
