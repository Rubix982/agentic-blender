"""C-006's sheet: the same crop of the foreground plants in every flicker variant, beside what changed between two
consecutive frames.

flicker.py deletes its frames when it ends, so frames 113 and 114 of each variant were copied out during the run. This
reads them (multilayer EXR, the Combined pass), brings the super-resolution frames down to the scene's 1280 x 720 as
the measurement did, and lays out, per variant: frame 113's crop (display gamma 1/2.2), then |frame 114 - frame 113|
times 8 on the same crop. Change between two frames is camera motion plus noise; the 1,024-sample floor shows the
motion nearly alone.

    python3 skills/blender/scripts/run.py experiments/animation/flicker_sheet.py -- FRAMES_DIR OUT.png
FRAMES_DIR holds one folder per variant, each with 0113.exr and 0114.exr. OUT may be .png or .jpg. Also writes
results/flicker_sheet.json: each variant's mean change from frame 113 to 114 over the whole frame, and what
OpenImageIO's render_text returned here."""
import json
import os
import sys

import blf
import imbuf
import numpy as np
import OpenImageIO as oiio

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SRC, OUT = argv[0], argv[1]
W, H = 1280, 720
X0, Y0, CW, CH = 120, 400, 480, 270                    # a crop inside the lower-left quarter: sorrel and ferns
FONT = next((f for f in ("/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Helvetica.ttc")
             if os.path.exists(f)), "")                    # for blf; 0, Blender's own font, if neither
ORDER = ["baseline", "animated seed", "no denoise", "super-res 141 % at 64 samples", "384 samples",
         "denoise_animation", "1024 samples (floor)", "raw with passes"]


def load(path):
    buf = oiio.ImageBuf(path)
    names = list(buf.spec().channelnames)
    want = [f"ViewLayer.Combined.{c}" for c in "RGB"]
    idx = [names.index(n) for n in want] if all(n in names for n in want) else [0, 1, 2]
    px = buf.get_pixels(oiio.FLOAT)[:, :, idx]
    if px.shape[1] != W:
        src = oiio.ImageBuf(oiio.ImageSpec(px.shape[1], px.shape[0], 3, oiio.FLOAT))
        src.set_pixels(oiio.ROI(0, px.shape[1], 0, px.shape[0]), np.ascontiguousarray(px))
        px = oiio.ImageBufAlgo.resize(src, roi=oiio.ROI(0, W, 0, H, 0, 1, 0, 3)).get_pixels(oiio.FLOAT)
    return np.clip(px, 0, 1) ** (1 / 2.2)


def find(folder, frame):
    for name in sorted(os.listdir(folder)):
        if name.endswith(".exr") and f"{frame:04d}" in name:
            return os.path.join(folder, name)
    return None


tiles = []
for v in ORDER:
    d = os.path.join(SRC, v)
    if not os.path.isdir(d):
        continue
    a, b = find(d, 113), find(d, 114)
    if not (a and b):
        continue
    fa, fb = load(a), load(b)
    crop = fa[Y0:Y0 + CH, X0:X0 + CW]
    diff = np.clip(np.abs(fb - fa)[Y0:Y0 + CH, X0:X0 + CW] * 8, 0, 1)
    tiles.append((v, crop, diff, float(np.abs(fb - fa).mean())))
    print("TILE", v, round(tiles[-1][3], 5), flush=True)

LAB = 28
cols = 2                                                  # two variants per row, each as picture + change
rows = (len(tiles) + cols - 1) // cols
sheet = np.full((rows * (CH + LAB), cols * 2 * CW, 3), 0.08, np.float32)
for i, (v, crop, diff, _) in enumerate(tiles):
    r, c = divmod(i, cols)
    y, x = r * (CH + LAB) + LAB, c * 2 * CW
    sheet[y:y + CH, x:x + CW] = crop
    sheet[y:y + CH, x + CW:x + 2 * CW] = diff
buf = oiio.ImageBuf(oiio.ImageSpec(sheet.shape[1], sheet.shape[0], 3, oiio.FLOAT))
buf.set_pixels(oiio.ROI(0, sheet.shape[1], 0, sheet.shape[0]), np.ascontiguousarray(sheet))
out = oiio.ImageBuf(oiio.ImageSpec(sheet.shape[1], sheet.shape[0], 3, oiio.UINT8))
oiio.ImageBufAlgo.copy(out, buf, oiio.UINT8)
out.write(OUT)

# Labels. Blender's OpenImageIO has no FreeType ("OpenImageIO was not compiled with FreeType for font rendering"), so
# render_text fails; blf draws into an ImBuf headless (bind_imbuf), whose origin is the bottom-left corner.
ib = imbuf.load(OUT)
fid = blf.load(FONT) if FONT else 0
with blf.bind_imbuf(fid, ib):
    blf.size(fid, 18)
    blf.color(fid, 0.92, 0.92, 0.92, 1.0)
    for i, (v, *_rest, mean_change) in enumerate(tiles):
        r, c = divmod(i, cols)
        blf.position(fid, c * 2 * CW + 8, ib.size[1] - (r * (CH + LAB) + 21), 0)
        blf.draw_buffer(fid, f"{v}   |   change 113->114 x8 (mean {mean_change:.4f})")
imbuf.write(ib, filepath=OUT)

probe = oiio.ImageBuf(oiio.ImageSpec(64, 16, 3, oiio.FLOAT))
ok = bool(oiio.ImageBufAlgo.render_text(probe, 0, 12, "test", 12))
err = (probe.geterror() or oiio.geterror()).strip()
res = dict(experiment="experiments/animation/flicker_sheet.py", frames=[113, 114], crop_x_y_w_h=[X0, Y0, CW, CH],
           mean_change_113_to_114={v: round(m, 5) for v, _c, _d, m in tiles},
           oiio_render_text=dict(returned=ok, error=err), sheet=os.path.basename(OUT))
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "flicker_sheet.json"), "w") as f:
    json.dump(res, f, indent=1)
print("RESULT", json.dumps(res["oiio_render_text"]), flush=True)
print("SHEET", OUT, sheet.shape[1], "x", sheet.shape[0], flush=True)
