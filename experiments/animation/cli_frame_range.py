"""Rendering a frame range from the command line: -s / -e / -a / -j / -f lists, -o and -F, and whether the order of the
arguments matters. Blender is started several times, one after another, on a small saved .blend (Workbench, 64 px).

Run with the system Python (it starts Blender itself):  python3 experiments/animation/cli_frame_range.py
Writes experiments/animation/results/cli_frame_range.json.
"""
import datetime
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from run import blender  # noqa: E402

B = blender()
TMP = tempfile.mkdtemp(prefix="bfg-cli-anim-")
BLEND = os.path.join(TMP, "scene.blend")
facts, data = [], {}
t_all = time.time()


def fact(sentence, **numbers):
    facts.append(dict(fact=sentence, **numbers))
    print("FACT", sentence, numbers, flush=True)


def run(args, timeout=120):
    t = time.time()
    r = subprocess.run([B] + args, capture_output=True, text=True, timeout=timeout)
    return r, round(time.time() - t, 2)


def outputs():
    """Every file under TMP except the .blend, relative, then removed."""
    found = []
    for dp, _, fs in os.walk(TMP):
        for f in fs:
            p = os.path.join(dp, f)
            if p == BLEND or f.endswith(".py") or f.endswith(".blend1"):
                continue
            found.append(os.path.relpath(p, TMP))
            os.remove(p)
    return sorted(found)


build = os.path.join(TMP, "build.py")
with open(build, "w") as f:
    f.write(f"""
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
s = bpy.context.scene
me = bpy.data.meshes.new('c'); import bmesh; bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1); bm.to_mesh(me)
ob = bpy.data.objects.new('c', me); s.collection.objects.link(ob)
ob.location.x = -1; ob.keyframe_insert('location', frame=1); ob.location.x = 1; ob.keyframe_insert('location', frame=10)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); cam.location = (0, -6, 0); cam.rotation_euler = (1.5708, 0, 0)
s.collection.objects.link(cam); s.camera = cam
s.render.engine = 'BLENDER_WORKBENCH'; s.render.resolution_x = s.render.resolution_y = 64
s.frame_start, s.frame_end = 1, 10
s.render.filepath = '//out/f_####'
s.render.image_settings.file_format = 'PNG'
bpy.ops.wm.save_as_mainfile(filepath={BLEND!r})
""")
r, _ = run(["-b", "--factory-startup", "--python-exit-code", "1", "--python", build])
assert r.returncode == 0, r.stderr[-2000:]

cases = {
    "-a": ["-a"],
    "-s 2 -e 4 -a": ["-s", "2", "-e", "4", "-a"],
    "-a -s 2 -e 4": ["-a", "-s", "2", "-e", "4"],
    "-s 1 -e 9 -j 3 -a": ["-s", "1", "-e", "9", "-j", "3", "-a"],
    "-f 3": ["-f", "3"],
    "-f 1,3,5..6": ["-f", "1,3,5..6"],
    "-f -1 (relative to end)": ["-f", "-1"],
    "-o //other/g_## -F JPEG -s 1 -e 2 -a": ["-o", "//other/g_##", "-F", "JPEG", "-s", "1", "-e", "2", "-a"],
    "-o /abs/h_ -x 0 -f 1": ["-o", os.path.join(TMP, "abs", "h_"), "-x", "0", "-f", "1"],
    "-F FFMPEG -s 1 -e 10 -a (file never set FFMPEG)": ["-F", "FFMPEG", "-s", "1", "-e", "10", "-a"],
}
res = {}
for label, args in cases.items():
    r, dt = run(["-b", BLEND, "--factory-startup"] + args)
    files = outputs()
    res[label] = dict(exit=r.returncode, seconds=dt, files=files,
                      saved_lines=sum(1 for l in r.stdout.splitlines() if l.strip().startswith("Saved:")),
                      errors=[l for l in (r.stdout + r.stderr).splitlines() if "rror" in l][:3])
    print(label, res[label], flush=True)
data["cases"] = res

fact("-a renders the file's own range (frame_start..frame_end, 1-10 here) to its render.filepath, relative to the .blend",
     files=res["-a"]["files"], seconds=res["-a"]["seconds"])
fact("-s and -e take effect only before -a: '-s 2 -e 4 -a' renders 2-4; '-a -s 2 -e 4' renders the file's whole range",
     before=res["-s 2 -e 4 -a"]["files"], after=res["-a -s 2 -e 4"]["files"])
fact("-j 3 renders every third frame of the range", files=res["-s 1 -e 9 -j 3 -a"]["files"])
fact("-f takes one frame, a comma list with '..' ranges, or a negative number counted back from the range's end",
     f3=res["-f 3"]["files"], f_list=res["-f 1,3,5..6"]["files"], f_minus1=res["-f -1 (relative to end)"]["files"])
fact("-o replaces the output path (// is the .blend's folder, '#' the frame padding); -F sets the format; -x 0 drops the "
     "extension", o_F=res["-o //other/g_## -F JPEG -s 1 -e 2 -a"]["files"],
     x0=res["-o /abs/h_ -x 0 -f 1"]["files"])
fact("-F FFMPEG on a file whose FFMPEG settings were never set: what is written",
     files=res["-F FFMPEG -s 1 -e 10 -a (file never set FFMPEG)"]["files"],
     exit=res["-F FFMPEG -s 1 -e 10 -a (file never set FFMPEG)"]["exit"],
     errors=res["-F FFMPEG -s 1 -e 10 -a (file never set FFMPEG)"]["errors"])

shutil.rmtree(TMP)
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results"), exist_ok=True)
version = subprocess.run([B, "--version"], capture_output=True, text=True).stdout.splitlines()[0].replace("Blender ", "")
rec = dict(experiment=os.path.relpath(os.path.abspath(__file__), ROOT),
           blender=version, machine=f"{platform.system()} {platform.machine()}", date=datetime.date.today().isoformat(),
           seconds=round(time.time() - t_all, 2), facts=facts, data=data, args=[])
text = json.dumps(rec, indent=1, default=str).replace(os.path.expanduser("~"), "~").replace(TMP, "<tmp>")
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "cli_frame_range.json"), "w") as f:
    f.write(text)
print("SAVED")
