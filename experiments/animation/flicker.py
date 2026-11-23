"""C-006: flicker in a moving-camera Cycles shot on this Mac, and what lowers it at what cost. The study of 49 Blender
productions and contest entries (kb/research/competitions-study.md, section 6) found low-sample denoising flickers in
animation, a fixed seed helps only with a still camera, more samples did not cure it (A-01), and temporal denoising
came from outside Blender. Blender 4.5 has bpy.ops.cycles.denoise_animation, documented nowhere in the manual.

Frames 101-125 of shots/morning-clearing (run its build.py first), rendered as multilayer EXR with the compositor off
so every variant is measured the same way, on linear Combined, clipped to 0..1 and given a 1/2.2 gamma:
  baseline       128 samples, OpenImageDenoise per frame, constant seed (as the shot was rendered)
  animated seed  the same with use_animated_seed
  no denoise     128 samples, raw
  super-res      141 % resolution (twice the pixels) at 64 samples, denoised, then downscaled (A-01's trial)
  384 samples    three times the samples
  denoise_animation  the raw 128-sample frames with denoising and motion-vector passes stored, then
                 bpy.ops.cycles.denoise_animation (it refuses frames without the vector pass)
  1024 samples   the floor: the least noisy render the night allows, not the truth
The shot samples adaptively (noise threshold 0.03 at 128 samples), so raising only the cap would change little: every
variant's threshold is scaled with its samples, threshold x sqrt(128 / samples), so 3x the samples means 1/sqrt(3) the
noise allowed.
Flicker: each frame against the mean of its neighbours, mean over pixels; also the 99th percentile, and the mean over
the lower-left quarter, where the foreground plants are. It includes the camera's motion, which is the same in every
variant; the floor's flicker estimates that part. Detail: the mean difference between neighbouring pixels of the
middle frame, so that a variant which steadies the picture by blurring it shows as a loss of detail."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import glob
import math
import shutil
import tempfile
import time
import bpy
import numpy as np
import OpenImageIO as oiio
import exp

E = exp.Experiment(__file__, keep_scene=True)
BLEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "shots", "morning-clearing", "out", "scene.blend"))
if not os.path.exists(BLEND):
    raise SystemExit(f"{BLEND} is missing: run shots/morning-clearing/build.py first")
bpy.ops.wm.open_mainfile(filepath=BLEND)
scene = bpy.context.scene
F0, F1 = (int(x) for x in os.environ.get("FLICKER_FRAMES", "101 125").split())   # a smoke run: fewer frames
SCALE = float(os.environ.get("FLICKER_SCALE", "1"))                     # and a smaller picture
scene.frame_start, scene.frame_end, scene.frame_step = F0, F1, 1
scene.render.use_compositing = False
scene.render.use_overwrite, scene.render.use_placeholder = True, False
scene.render.image_settings.file_format = "OPEN_EXR_MULTILAYER"
scene.render.image_settings.color_depth = "32"
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "METAL"
prefs.get_devices()
for d in prefs.devices:
    d.use = d.type == "METAL"
scene.cycles.device = "GPU"
vl = scene.view_layers[0]
THR = scene.cycles.adaptive_threshold                                    # the shot's: 0.03 at 128 samples
TMP = tempfile.mkdtemp(prefix="ab-flicker-")
BASE = dict(samples=128, use_denoising=True, use_animated_seed=False, res=100, store=False)


def render(name, **kw):
    cfg = dict(BASE, **kw)
    scene.cycles.samples = cfg["samples"]
    scene.cycles.adaptive_threshold = THR * math.sqrt(128 / cfg["samples"])
    scene.cycles.use_denoising = cfg["use_denoising"]
    scene.cycles.use_animated_seed = cfg["use_animated_seed"]
    scene.render.resolution_percentage = round(cfg["res"] * SCALE)
    vl.cycles.denoising_store_passes = cfg["store"]
    vl.use_pass_vector = cfg["store"]                                    # denoise_animation also needs motion vectors
    out = os.path.join(TMP, name)
    os.makedirs(out, exist_ok=True)
    scene.render.filepath = os.path.join(out, "")
    times = []
    t0 = {}
    pre = lambda s, *a: t0.__setitem__("t", time.time())
    post = lambda s, *a: times.append(time.time() - t0["t"])
    bpy.app.handlers.render_pre.append(pre)
    bpy.app.handlers.render_post.append(post)
    bpy.ops.render.render(animation=True)
    bpy.app.handlers.render_pre.remove(pre)
    bpy.app.handlers.render_post.remove(post)
    return out, round(float(np.mean(times)), 2), dict(samples=cfg["samples"], threshold=round(scene.cycles.adaptive_threshold, 4),
                                                       resolution_percent=cfg["res"], denoise=cfg["use_denoising"],
                                                       animated_seed=cfg["use_animated_seed"])


def frames_of(folder):
    size = (round(scene.render.resolution_x * SCALE), round(scene.render.resolution_y * SCALE))
    out = []
    for f in sorted(glob.glob(os.path.join(folder, "*.exr"))):
        buf = oiio.ImageBuf(f)
        names = list(buf.spec().channelnames)
        idx = [names.index(f"ViewLayer.Combined.{c}") for c in "RGB"]
        px = buf.get_pixels(oiio.FLOAT)[:, :, idx]
        if px.shape[1] != size[0]:
            src = oiio.ImageBuf(oiio.ImageSpec(px.shape[1], px.shape[0], 3, oiio.FLOAT))
            src.set_pixels(oiio.ROI(0, px.shape[1], 0, px.shape[0]), np.ascontiguousarray(px))
            px = oiio.ImageBufAlgo.resize(src, roi=oiio.ROI(0, size[0], 0, size[1], 0, 1, 0, 3)).get_pixels(oiio.FLOAT)
        out.append(np.clip(px, 0, 1) ** (1 / 2.2))
    return out


def flicker(fr):
    m, p, q = [], [], []
    h, w = fr[0].shape[:2]
    for a, b, c in zip(fr, fr[1:], fr[2:]):
        r = np.abs(b - (a + c) / 2).mean(axis=2)
        m.append(r.mean())
        p.append(np.percentile(r, 99))
        q.append(r[h // 2:, : w // 2].mean())
    mid = fr[len(fr) // 2]
    detail = (np.abs(np.diff(mid, axis=0)).mean() + np.abs(np.diff(mid, axis=1)).mean()) / 2
    return dict(mean=round(float(np.mean(m)), 5), p99=round(float(np.mean(p)), 5), plants=round(float(np.mean(q)), 5),
                detail=round(float(detail), 5), frames=len(fr))


BASEFR = []                                                              # the baseline's frames, to compare others with


def from_baseline(fr):
    return round(float(np.mean([np.abs(a - b).mean() for a, b in zip(fr, BASEFR)])), 5) if BASEFR else None


def keep():
    E.save(rows=rows)                                                     # after every row: a stop keeps what was done


rows = {}


def variant(name, **kw):
    folder, spf, cfg = render(name, **kw)
    fr = frames_of(folder)
    rows[name] = dict(seconds_per_frame=spf, settings=cfg, difference_from_baseline=from_baseline(fr), **flicker(fr))
    if not BASEFR:
        BASEFR.extend(fr)
    print("ROW", name, rows[name], flush=True)
    keep()


for name, kw in (("baseline", {}), ("animated seed", dict(use_animated_seed=True)), ("no denoise", dict(use_denoising=False)),
                 ("super-res 141 % at 64 samples", dict(res=141, samples=64)), ("384 samples", dict(samples=384))):
    variant(name, **kw)

# denoise_animation: raw frames with the denoising passes, then the operator, written to a separate folder
folder, spf, cfg = render("raw with passes", use_denoising=False, store=True)
den = os.path.join(TMP, "denoise_animation")
os.makedirs(den, exist_ok=True)
scene.render.filepath = os.path.join(folder, "")
t = time.time()
try:
    res = sorted(bpy.ops.cycles.denoise_animation(output_filepath=os.path.join(den, "")))
except Exception as e:
    res = f"{type(e).__name__}: {str(e).strip().splitlines()[-1][:200]}"
op_s = round(time.time() - t, 1)
written = sorted(glob.glob(os.path.join(den, "*.exr")))
if written:
    fr = frames_of(den)
    rows["denoise_animation"] = dict(seconds_per_frame=round(spf + op_s / (F1 - F0 + 1), 2), operator=res,
                                     operator_seconds=op_s, settings=cfg, difference_from_baseline=from_baseline(fr),
                                     raw_difference_from_baseline=from_baseline(frames_of(folder)), **flicker(fr))
else:
    rows["denoise_animation"] = dict(operator=res, operator_seconds=op_s, written=len(written),
                                     in_place_changed=None)
print("ROW denoise_animation", rows["denoise_animation"], flush=True)
keep()
vl.cycles.denoising_store_passes = False
variant("1024 samples (floor)", samples=1024)

E.fact("flicker of frames 101-125 of the forest shot (each frame against the mean of its neighbours; mean, 99th "
       "percentile, and the lower-left quarter where the foreground plants are) and render seconds per frame, by "
       "variant", rows=rows)
keep()
shutil.rmtree(TMP, ignore_errors=True)
