"""C-005: after the render, inside Blender (run from the repository root):
    python3 skills/blender/scripts/run.py shots/morning-clearing/finish.py --blend shots/morning-clearing/out/scene.blend \
        -- shots/morning-clearing/out
Checks the card's numbers (frames present, time per frame, the boulder's size, flicker before grain), joins the frames
into an MP4 with the Video Sequencer (animation-video.md), and writes contact sheets. Results:
shots/morning-clearing/results.json (committed) and out/ (git-ignored: the video, a 1280 px sheet)."""
import json
import os
import statistics
import sys

import bpy
import numpy as np
import OpenImageIO as oiio

sys.stdout.reconfigure(line_buffering=True)
OUT = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "skills", "blender", "scripts"))
import asset_import as ai  # noqa: E402

res = {}
frames = sorted(f for f in os.listdir(os.path.join(OUT, "frames")) if f.endswith(".png") and os.path.getsize(os.path.join(OUT, "frames", f)) > 0)
clean = sorted(f for f in os.listdir(os.path.join(OUT, "clean")) if f.endswith(".png") and os.path.getsize(os.path.join(OUT, "clean", f)) > 0)
res["frames"] = dict(graded=len(frames), clean=len(clean), wanted=240)

times = {}
for line in open(os.path.join(OUT, "times.csv")):
    f, s = line.strip().split(",")
    times[int(f)] = float(s)                                          # a resumed run keeps the last time per frame
t = list(times.values())
res["seconds_per_frame"] = dict(mean=round(statistics.mean(t), 2), median=round(statistics.median(t), 2),
                                max=round(max(t), 2), first=times.get(1), total_hours=round(sum(t) / 3600, 3))

boulder = next(o for o in bpy.data.objects if o.type == "MESH" and o.name.lower().startswith("boulder"))
pts = [boulder.matrix_world @ v.co for v in boulder.data.vertices]
size = [max(p[i] for p in pts) - min(p[i] for p in pts) for i in range(3)]
stated = ai.manifest("polyhaven", "boulder_01")["size_m"]
res["boulder"] = dict(size_m=[round(s, 4) for s in size], stated_m=stated,
                      max_error=round(max(abs(a - b) / b for a, b in zip(sorted(size), sorted(stated))), 5))


def load(folder, name, step=2):
    return oiio.ImageBuf(os.path.join(OUT, folder, name)).get_pixels(oiio.FLOAT)[::step, ::step, :3]


# flicker: each clean frame against the mean of its neighbours (slow, smooth motion leaves little else)
resid = []
prev, cur = load("clean", clean[0]), load("clean", clean[1])
for name in clean[2:]:
    nxt = load("clean", name)
    resid.append(float(np.abs(cur - (prev + nxt) / 2).mean()))
    prev, cur = cur, nxt
res["flicker_before_grain"] = dict(mean=round(statistics.mean(resid), 5), max=round(max(resid), 5),
                                   frames_above_0_01=sum(r > 0.01 for r in resid), bar=0.01)
mid = clean[len(clean) // 2]
res["grain"] = dict(mean_abs_difference_graded_vs_clean=round(float(np.abs(load("frames", mid) - load("clean", mid)).mean()), 5))

# contact sheets: 8 frames
pick = [frames[round(i * (len(frames) - 1) / 7)] for i in range(8)]
for tile_w, path in ((128, os.path.join(HERE, "sheet.png")), (320, os.path.join(OUT, "sheet-large.png"))):
    tile_h = tile_w * 9 // 16
    sheet = np.zeros((2 * tile_h, 4 * tile_w, 3), np.float32)
    for i, name in enumerate(pick):
        img = load("frames", name, 1)
        ys = np.linspace(0, img.shape[0] - 1, tile_h).astype(int)
        xs = np.linspace(0, img.shape[1] - 1, tile_w).astype(int)
        r, c = divmod(i, 4)
        sheet[r * tile_h:(r + 1) * tile_h, c * tile_w:(c + 1) * tile_w] = img[ys][:, xs]
    buf = oiio.ImageBuf(oiio.ImageSpec(sheet.shape[1], sheet.shape[0], 3, oiio.UINT8))
    buf.set_pixels(oiio.ROI(0, sheet.shape[1], 0, sheet.shape[0]), (np.clip(sheet, 0, 1) * 255).astype(np.uint8))
    buf.write(path)
res["sheet_frames"] = pick

# the video (animation-video.md: a separate scene, image strip, FFMPEG H.264 in MPEG-4)
vse = bpy.data.scenes.new("Edit")
vse.render.resolution_x, vse.render.resolution_y, vse.render.resolution_percentage = 1280, 720, 100
vse.render.fps = 24
ed = vse.sequence_editor_create()
d = os.path.join(OUT, "frames")
s = ed.strips.new_image(name="frames", filepath=os.path.join(d, frames[0]), channel=1, frame_start=1)
for f in frames[1:]:
    s.elements.append(f)
vse.frame_start, vse.frame_end = 1, s.frame_final_end - 1
vse.render.image_settings.file_format = "FFMPEG"
vse.render.ffmpeg.format, vse.render.ffmpeg.codec = "MPEG4", "H264"
vse.render.ffmpeg.constant_rate_factor = "HIGH"
vse.view_settings.view_transform = "Standard"                         # the frames are already graded: pass them through
vse.render.filepath = os.path.join(OUT, "morning-clearing-")
with bpy.context.temp_override(scene=vse):
    bpy.ops.render.render(animation=True, scene=vse.name)
mp4 = [f for f in os.listdir(OUT) if f.startswith("morning-clearing-") and f.endswith(".mp4")]
res["video"] = dict(files=mp4, mb=[round(os.path.getsize(os.path.join(OUT, f)) / 1e6, 2) for f in mp4],
                    strip_frames=s.frame_final_duration)

ok = (res["frames"]["graded"] == 240 and res["frames"]["clean"] == 240 and res["seconds_per_frame"]["total_hours"] <= 9
      and res["boulder"]["max_error"] <= 0.02 and res["flicker_before_grain"]["mean"] <= 0.01)
res["card_bar_met"] = ok
json.dump(res, open(os.path.join(HERE, "results.json"), "w"), indent=1)
print("FINISH", json.dumps(res), flush=True)
