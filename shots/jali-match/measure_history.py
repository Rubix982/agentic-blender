"""C-016: which measures follow the judge? Every candidate measure, recomputed on the same patch of each card's
committed sheet, ranked against the judge's verdicts.

    python3 skills/blender/scripts/run.py shots/jali-match/measure_history.py
Each closing commit's sheet.jpg (from git) holds a detail patch of the photo and of the render at full size, the same
560 x 420 px of the carved field since C-007 (compare.py: DX, DY = 520, 330). On it, by the rule in common.py applied to
each image: the openings' IoU; the forms band (luminance blurred over 5 px less over 21 px) and the fine band (less its
5 px blur), each as the correlation render against photo and the amplitude ratio, on stone in both 3 px from any
opening; the stone's bright end (90th percentile) and contrast (90th less 10th) as render over photo; the colour spread
(log(R/G), log(B/G) over a 5 px blur) render over photo; the lines (C-008, both ways within 2 px); the openings' edge
gradient render over photo; and SSIM over the patch (luminance, an 11 px Gaussian window), which no card used. A ratio
is scored by its distance from 1 in log terms (smaller is nearer the photo). Each measure's Spearman rank correlation
with the ladder, signed so that +1 means it improves exactly as the verdicts rose. The same again on the sheet's top
row (the whole photo and render at half size, the frame and borders included). Writes results/measure_history.json.
"""
import json
import os
import subprocess
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import common as C  # noqa: E402

# The judge's verdicts in CARD.md, as a ladder, and each card's closing commit.
CARDS = [("C-007", "19d86a3", 0, "no"), ("C-008", "a7f31cc", 0, "no"),
         ("C-009", "13b599a", 1, "vastly improved even further (not a yes)"),
         ("C-011", "cd13b8c", 2, "at a glance, yes"), ("C-012", "4e158df", 3, "yes, it reads better"),
         ("C-013", "cf6bbe9", 4, "almost very realistic in a passing glance"),
         ("C-014", "39fed4a", 5, "I really love it"), ("C-015", "805b65a", 6, "this looks so real!")]
ROW0, DW, DH = 30 + 701 + 30, 560, 420                                 # the detail row in the sheet (compare.py)


def sheet(commit):
    data = subprocess.run(["git", "show", f"{commit}:shots/jali-match/sheet.jpg"], cwd=ROOT, capture_output=True,
                          check=True).stdout
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        f.write(data)
        path = f.name
    img = C.load(path)
    os.unlink(path)
    return img


def patch(img):
    """The detail row: photo and render at full size, the carved field's middle."""
    return img[ROW0:ROW0 + DH, :DW], img[ROW0:ROW0 + DH, DW:2 * DW]


def whole(img):
    """The top row: the whole photo and the whole render at half size (frame and borders included)."""
    return img[30:731, :615], img[30:731, 615:1230]


def bands(y):
    b5, b21 = C.blur(y, 5), C.blur(y, 21)
    return dict(fine=y - b5, forms=b5 - b21)


def chroma(img, mask):
    b = np.stack([C.blur(img[:, :, c].astype(np.float32), 5) for c in range(3)], -1)
    a = np.log(np.maximum(b[:, :, 0], 1e-3) / np.maximum(b[:, :, 1], 1e-3))[mask]
    bb = np.log(np.maximum(b[:, :, 2], 1e-3) / np.maximum(b[:, :, 1], 1e-3))[mask]
    return float(np.sqrt(a.var() + bb.var()))


def edge_gradient(k):
    y = k["y"]
    g = np.hypot(np.gradient(y, axis=0), np.gradient(y, axis=1))
    e = C.dilate(k["opening"], 1) & ~C.erode(k["opening"], 1)
    return float(g[e].mean())


def ssim(a, b):
    c1, c2 = 0.01 ** 2, 0.03 ** 2
    ma, mb = C.blur(a, 11), C.blur(b, 11)
    va, vb = C.blur(a * a, 11) - ma * ma, C.blur(b * b, 11) - mb * mb
    cov = C.blur(a * b, 11) - ma * mb
    s = ((2 * ma * mb + c1) * (2 * cov + c2)) / ((ma * ma + mb * mb + c1) * (va + vb + c2))
    return float(s[10:-10, 10:-10].mean())


def measures(p, r):
    kp, kr = C.classify(p), C.classify(r)
    out = {}
    out["openings_iou"] = float((kp["opening"] & kr["opening"]).sum() / max((kp["opening"] | kr["opening"]).sum(), 1))
    m = C.erode(kp["stone"], 3) & C.erode(kr["stone"], 3)
    bp, br = bands(kp["y"]), bands(kr["y"])
    for n in ("forms", "fine"):
        out[f"{n}_correlation"] = float(np.corrcoef(bp[n][m], br[n][m])[0, 1])
        out[f"{n}_amplitude_ratio"] = float(br[n][m].std() / max(bp[n][m].std(), 1e-9))
    sp, sr = kp["y"][kp["stone"]], kr["y"][kr["stone"]]
    out["bright_end_ratio"] = float(np.percentile(sr, 90) / np.percentile(sp, 90))
    out["contrast_ratio"] = float((np.percentile(sr, 90) - np.percentile(sr, 10)) / (np.percentile(sp, 90) - np.percentile(sp, 10)))
    out["colour_spread_ratio"] = chroma(r, m) / max(chroma(p, m), 1e-9)
    lp, lr = C.cut_lines(kp), C.cut_lines(kr)
    out["lines_render_near_photo"] = float((lr & C.dilate(lp, 2)).sum() / max(lr.sum(), 1))
    out["lines_photo_near_render"] = float((lp & C.dilate(lr, 2)).sum() / max(lp.sum(), 1))
    out["edge_gradient_ratio"] = edge_gradient(kr) / max(edge_gradient(kp), 1e-9)
    out["ssim"] = ssim(kp["y"].astype(np.float32), kr["y"].astype(np.float32))
    return out


RATIOS = {"forms_amplitude_ratio", "fine_amplitude_ratio", "bright_end_ratio", "contrast_ratio", "colour_spread_ratio",
          "edge_gradient_ratio"}


def ranks(v):
    v = np.asarray(v, float)
    order = v.argsort()
    r = np.empty(len(v))
    r[order] = np.arange(len(v))
    for x in np.unique(v):                                             # ties share their mean rank
        r[v == x] = r[v == x].mean()
    return r


def spearman(a, b):
    return float(np.corrcoef(ranks(a), ranks(b))[0, 1])


def agree(rows):
    ladder = [r["ladder"] for r in rows]
    out = {}
    for key in rows[0]:
        if key in ("card", "commit", "ladder", "verdict"):
            continue
        vals = np.array([r[key] for r in rows], float)
        score = -np.abs(np.log(np.maximum(vals, 1e-6))) if key in RATIOS else vals   # nearer the photo is better
        out[key] = round(spearman(ladder, score), 3)
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


views = {"patch": [], "whole": []}
for card, commit, step, words in CARDS:
    img = sheet(commit)
    for view, cut in (("patch", patch), ("whole", whole)):
        mm = measures(*cut(img))
        views[view].append(dict(card=card, commit=commit, ladder=step, verdict=words, **{k: round(v, 4) for k, v in mm.items()}))
        print("ROW", view, card, {k: round(v, 3) for k, v in mm.items()}, flush=True)
agreement = {v: agree(rows) for v, rows in views.items()}
for v, a in agreement.items():
    print("AGREEMENT", v, json.dumps(a), flush=True)
with open(os.path.join(HERE, "results", "measure_history.json"), "w") as f:
    json.dump(dict(patch=dict(x=520, y=330, w=DW, h=DH, scale="full"), whole=dict(scale="half, frame included"),
                   ladder={c[0]: c[2] for c in CARDS}, rows=views, spearman_with_ladder=agreement,
                   scored_by_distance_from_1=sorted(RATIOS)), f, indent=1)
