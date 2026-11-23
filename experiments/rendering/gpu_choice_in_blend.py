"""Found by C-005's shot: is choosing the GPU saved in the .blend? A file is saved with Cycles set to the Metal GPU,
then opened again in a new headless Blender with --factory-startup, which is how scripts/run.py runs.

Run with the system Python:  python3 experiments/rendering/gpu_choice_in_blend.py
Writes experiments/rendering/results/gpu_choice_in_blend.json."""
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
tmp = tempfile.mkdtemp(prefix="ab-gpu-")
path = os.path.join(tmp, "gpu.blend")
SET = f"""
import bpy, time
s = bpy.context.scene
s.render.engine = "CYCLES"
p = bpy.context.preferences.addons["cycles"].preferences
p.compute_device_type = "METAL"
p.get_devices()
for d in p.devices:
    d.use = d.type == "METAL"
s.cycles.device = "GPU"
bpy.ops.wm.save_as_mainfile(filepath={path!r})
print("SAVED", s.cycles.device, p.compute_device_type, p.has_active_device())
"""
READ = """
import bpy, time
print("FACTORY_TYPE", bpy.context.preferences.addons["cycles"].preferences.compute_device_type)
s = bpy.context.scene
p = bpy.context.preferences.addons["cycles"].preferences
print("READ", s.cycles.device, p.compute_device_type, p.has_active_device(), [d.name for d in p.devices if d.use])
"""
facts = []
out = subprocess.run([B, "-b", "--factory-startup", "--python-expr", SET], capture_output=True, text=True).stdout
saved = next(l for l in out.splitlines() if l.startswith("SAVED")).split(maxsplit=3)[1:]
out = subprocess.run([B, "-b", "--factory-startup", path, "--python-expr", READ], capture_output=True, text=True).stdout
read = next(l for l in out.splitlines() if l.startswith("READ"))
factory = next(l for l in out.splitlines() if l.startswith("FACTORY_TYPE")).split()[1]
facts.append(dict(fact="a file saved with scene.cycles.device = 'GPU' and the Metal device chosen, opened again with "
                       "--factory-startup: what the scene and the device preference say, and whether a GPU is active "
                       "(on this Mac the factory preference already names METAL, so the GPU stays in use)",
                  when_saved=dict(scene_device=saved[0], compute_device_type=saved[1], has_active_device=saved[2]),
                  when_reopened=read, factory_compute_device_type=factory))
rec = dict(experiment=os.path.relpath(os.path.abspath(__file__), ROOT),
           blender=subprocess.run([B, "-b", "--factory-startup", "--version"], capture_output=True, text=True).stdout.split()[1],
           machine=f"{platform.system()} {platform.machine()}", date=datetime.date.today().isoformat(), facts=facts, data={})
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results"), exist_ok=True)
json.dump(rec, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "gpu_choice_in_blend.json"), "w"), indent=1)
print(json.dumps(facts, indent=1))
