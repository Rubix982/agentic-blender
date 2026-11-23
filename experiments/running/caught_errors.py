"""Does an operator error that the script catches still fail the run? Exit codes of headless Blender with
--python-exit-code 1 for scripts that catch an operator's RuntimeError, then end or go on.

Run with the system Python:  python3 experiments/running/caught_errors.py
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
TMP = tempfile.mkdtemp(prefix="bfg-caught-")
facts = []

HEAD = "import bpy\nbpy.ops.wm.read_factory_settings(use_empty=True)\nbpy.ops.mesh.primitive_cube_add()\n"
RENDER_FAIL = ("try:\n    bpy.ops.render.render()\nexcept RuntimeError as e:\n    print('CAUGHT', e)\n")
POLL_FAIL = ("try:\n    bpy.ops.view3d.snap_cursor_to_center()\nexcept RuntimeError as e:\n    print('CAUGHT', e)\n")
ADD_CAMERA_AND_RENDER = ("c = bpy.data.objects.new('C', bpy.data.cameras.new('C'))\nbpy.context.scene.collection.objects.link(c)\n"
                         "bpy.context.scene.camera = c\ns = bpy.context.scene\ns.render.engine = 'BLENDER_WORKBENCH'\n"
                         "s.render.resolution_x = s.render.resolution_y = 16\nbpy.ops.render.render()\n")
OK_OP = "bpy.ops.object.select_all(action='SELECT')\n"
cases = {
    "nothing fails": HEAD,
    "caught render error ('no camera'), script ends": HEAD + RENDER_FAIL,
    "caught render error, then a successful operator": HEAD + RENDER_FAIL + OK_OP,
    "caught render error, then a successful render": HEAD + RENDER_FAIL + ADD_CAMERA_AND_RENDER,
    "caught poll failure, script ends": HEAD + POLL_FAIL,
    "caught Python error (not an operator)": HEAD + "try:\n    1 / 0\nexcept ZeroDivisionError:\n    pass\n",
}
codes = {}
for label, body in cases.items():
    p = os.path.join(TMP, f"c{len(codes)}.py")
    open(p, "w").write(body)
    r = subprocess.run([B, "-b", "--factory-startup", "--python-exit-code", "1", "--python", p], capture_output=True, text=True)
    codes[label] = r.returncode
p = os.path.join(TMP, "noflag.py")
open(p, "w").write(HEAD + RENDER_FAIL)
noflag = subprocess.run([B, "-b", "--factory-startup", "--python", p], capture_output=True, text=True).returncode
facts.append(dict(fact="A failed render sets headless Blender's exit code to 1 even when the script catches the error and "
                       "goes on; a later successful render clears it. Other caught operator errors (a poll failure) and "
                       "caught Python errors leave it at 0. Exit codes with --python-exit-code 1 (0 = success), and the "
                       "caught render error without the flag", **codes, **{"caught render error, no --python-exit-code": noflag}))
print("FACT", codes)
rec = dict(experiment=os.path.relpath(os.path.abspath(__file__), ROOT),
           blender=subprocess.run([B, "--version"], capture_output=True, text=True).stdout.splitlines()[0],
           machine=f"{platform.system()} {platform.machine()}", date=datetime.date.today().isoformat(), facts=facts)
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results"), exist_ok=True)
json.dump(rec, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "caught_errors.json"), "w"), indent=1)
