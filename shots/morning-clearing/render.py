"""C-005: render the saved shot, logging each frame's time. Run from the repository root:
    python3 skills/blender/scripts/run.py --blend shots/morning-clearing/out/scene.blend \
        shots/morning-clearing/render.py -- START END [STEP] [OUT_DIR]
Frames already written are skipped (use_overwrite off, placeholders on), so a stopped run resumes where it was; an
empty placeholder left by a crash is skipped too, so delete empty files first (experiments/animation/resume_render.py).
The GPU is chosen again here in case the preferences differ; on this Mac the factory ones already name METAL, so a
.blend saved with the GPU keeps it (experiments/rendering/gpu_choice_in_blend.py)."""
import os
import sys
import time

import bpy

sys.stdout.reconfigure(line_buffering=True)
argv = sys.argv[sys.argv.index("--") + 1:]
start, end = int(argv[0]), int(argv[1])
step = int(argv[2]) if len(argv) > 2 else 1
scene = bpy.context.scene
here = os.path.dirname(bpy.data.filepath)
out = os.path.abspath(argv[3]) if len(argv) > 3 else here
scene.frame_start, scene.frame_end, scene.frame_step = start, end, step
scene.render.filepath = os.path.join(out, "frames", "")
for n in scene.node_tree.nodes:
    if n.type == "OUTPUT_FILE":
        n.base_path = os.path.join(out, "clean", "")

prefs = bpy.context.preferences.addons["cycles"].preferences
for kind in ("METAL", "OPTIX", "CUDA", "HIP", "ONEAPI"):
    try:
        prefs.compute_device_type = kind
    except TypeError:
        continue
    prefs.get_devices()
    if any(d.type == kind for d in prefs.devices):
        for d in prefs.devices:
            d.use = d.type == kind
        scene.cycles.device = "GPU"
        break
print("DEVICE", scene.cycles.device, prefs.compute_device_type, [d.name for d in prefs.devices if d.use], flush=True)

os.makedirs(out, exist_ok=True)
log = open(os.path.join(out, "times.csv"), "a")
t0 = {}


def pre(scene, *_):
    t0["t"] = time.time()


def post(scene, *_):
    s = time.time() - t0.get("t", time.time())
    log.write(f"{scene.frame_current},{s:.2f}\n")
    log.flush()
    print(f"FRAME {scene.frame_current} {s:.1f} s", flush=True)


bpy.app.handlers.render_pre.append(pre)
bpy.app.handlers.render_post.append(post)
t = time.time()
bpy.ops.render.render(animation=True)
print(f"DONE frames {start}-{end} step {step} in {time.time() - t:.1f} s", flush=True)
