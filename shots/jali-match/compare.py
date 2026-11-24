"""C-007, step 3: the render against the photograph, by the one rule in common.py, and the sheet for the user.

    python3 skills/blender/scripts/run.py shots/jali-match/compare.py
Reads photo/agra-jali.jpg (at half size) and out/render.png. Measures, inside the photo's screen box:
  openings_iou     pixels that are opening in both, over pixels that are opening in either
  stone_iou        the same for stone
  stone_y          the stone's luminance, 10th / 50th / 90th percentiles (the 50th was fitted by the lights)
  stone_spread     90th minus 10th percentile: the stone's contrast, which nothing was fitted to
  stone_y_bands    the stone's median luminance in ten bands from top to bottom
Writes shots/jali-match/sheet.jpg (the two side by side, and the same detail of each at full size) and
results/compare.json."""
import json
import os
import sys

import blf
import imbuf
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common as C  # noqa: E402
from read_photo import stats  # noqa: E402

W, H = C.size()
photo = C.load(os.path.join(HERE, "photo", "agra-jali.jpg"), (W, H))
render = C.load(os.path.join(HERE, "out", "render.png"), (W, H))
kp, sp = stats(photo)
kr, sr = stats(render)
x0, y0, x1, y1 = sp["box"]
box = (slice(y0, y1 + 1), slice(x0, x1 + 1))


def iou(a, b):
    a, b = a[box], b[box]
    return round(float((a & b).sum() / max((a | b).sum(), 1)), 4)


res = dict(openings_iou=iou(kp["opening"], kr["opening"]), stone_iou=iou(kp["stone"], kr["stone"]),
           photo=dict(stone_y=sp["stone_y"], stone_y_p99=sp["stone_y_p99"], stone_rgb_median=sp["stone_rgb_median"],
                      stone_spread=round(sp["stone_y"][2] - sp["stone_y"][0], 4),
                      opening_y=sp["opening_y"], opening_share=sp["opening_share"], stone_y_bands=sp["stone_y_bands"]),
           render=dict(stone_y=sr["stone_y"], stone_y_p99=sr["stone_y_p99"], stone_rgb_median=sr["stone_rgb_median"],
                       stone_spread=round(sr["stone_y"][2] - sr["stone_y"][0], 4),
                       opening_y=sr["opening_y"], opening_share=sr["opening_share"], stone_y_bands=sr["stone_y_bands"]))
res["spread_ratio"] = round(res["render"]["stone_spread"] / res["photo"]["stone_spread"], 4)
res["bar"] = dict(openings_iou_at_least=0.90, spread_ratio_within=[0.8, 1.2])
res["measures_pass"] = res["openings_iou"] >= 0.90 and 0.8 <= res["spread_ratio"] <= 1.2
# Where the photo sees the wall, what the render shows there, and the IoU by thirds of the screen's height.
po, ro = kp["opening"][box], kr["opening"][box]
res["photo_openings_in_render"] = dict(opening=round(float((po & ro).sum() / po.sum()), 4),
                                       stone=round(float((po & kr["stone"][box]).sum() / po.sum()), 4),
                                       dark=round(float((po & kr["outside"][box]).sum() / po.sum()), 4))
res["render_openings_on_photo_stone"] = round(float((ro & kp["stone"][box]).sum() / max(ro.sum(), 1)), 4)
thirds = np.array_split(np.arange(y0, y1 + 1), 3)
res["openings_iou_by_third"] = [round(float((kp["opening"][t[0]:t[-1] + 1, x0:x1 + 1] & kr["opening"][t[0]:t[-1] + 1, x0:x1 + 1]).sum()
                                      / max((kp["opening"][t[0]:t[-1] + 1, x0:x1 + 1] | kr["opening"][t[0]:t[-1] + 1, x0:x1 + 1]).sum(), 1)), 4)
                                for t in thirds]
print("COMPARE", json.dumps(res), flush=True)

# The sheet: both whole, then one detail of each at full size, with the openings that disagree marked.
half = (W // 2, H // 2)
a = C.load(os.path.join(HERE, "photo", "agra-jali.jpg"), half)
b = C.load(os.path.join(HERE, "out", "render.png"), half)
DX, DY, DW, DH = 520, 330, 560, 420                                    # a detail: two rows of cells and their rosettes
LAB = 30
top = np.concatenate([a, b], axis=1)
det = np.concatenate([photo[DY:DY + DH, DX:DX + DW], render[DY:DY + DH, DX:DX + DW]], axis=1)
miss = np.zeros((H, W, 3), np.float32)
miss[kp["opening"] & ~kr["opening"]] = (1.0, 0.2, 0.2)                 # open in the photo only: red
miss[kr["opening"] & ~kp["opening"]] = (0.2, 0.6, 1.0)                 # open in the render only: blue
diffw = C.load_array_resized(miss, half)
cols = max(top.shape[1], det.shape[1], diffw.shape[1])


def pad(x):
    return np.pad(x, ((0, 0), (0, cols - x.shape[1]), (0, 0)), constant_values=0.08)


band = np.full((LAB, cols, 3), 0.08, np.float32)
sheet = np.concatenate([band, pad(top), band, pad(det), band, pad(diffw)], axis=0)
path = os.path.join(HERE, "sheet.jpg")
C.write_png(path, sheet)
ib = imbuf.load(path)
fid = blf.load("/System/Library/Fonts/Supplemental/Arial.ttf") if os.path.exists(
    "/System/Library/Fonts/Supplemental/Arial.ttf") else 0
labels = [(0, "photograph (Prof. Mortel, CC BY 2.0)"), (half[0], "render"),
          (0, None), (0, "detail, photograph"), (DW, "detail, render"),
          (0, f"openings that disagree: red = open only in the photo, blue = open only in the render "
              f"(IoU {res['openings_iou']})")]
ys = [0, 0, None, LAB + top.shape[0], LAB + top.shape[0], 2 * LAB + top.shape[0] + det.shape[0]]
with blf.bind_imbuf(fid, ib):
    blf.size(fid, 20)
    blf.color(fid, 0.95, 0.95, 0.95, 1.0)
    for (x, text), y in zip(labels, ys):
        if text:
            blf.position(fid, x + 8, ib.size[1] - (y + 22), 0)
            blf.draw_buffer(fid, text)
imbuf.write(ib, filepath=path)
os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
with open(os.path.join(HERE, "results", "compare.json"), "w") as f:
    json.dump(res, f, indent=1)
print("SHEET", path, sheet.shape, flush=True)
