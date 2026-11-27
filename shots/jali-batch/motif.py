"""C-025: one motif per panel from its copies. On each panel (a part of a shot's carved field holding one design, cut by
hand as fractions of the field): find its two repeat vectors (structure.py, C-024), cut a square patch 1.2 repeats
wide at every lattice point, and move each patch by the one whole-pixel shift (within a tenth of the repeat) that best
matches the mean of all the other patches, ITER times over. Then each patch is predicted by the others' mean (an
opening where it is 0.5 or more), its own pixels never used for themselves, and the openings scored by IoU over all
patches. The same is done from patches at random places (the baseline, with the same shifts allowed) and from the
lattice's patches left unshifted (what the shifts add).

    .venv/bin/python shots/jali-batch/motif.py [--finder consistent] [--score balanced] [SLUG:fx0,fy0,fx1,fy1 ...]
                                                                     (no slug: C-025's seven panels)
C-026's switches: --finder consistent (structure.lattice_consistent: the lattice its points agree on, not the shortest
strong peak) and --score balanced (the mean of the openings' IoU and the stone's, bar 0.80, not the openings' alone,
bar 0.70). Results under the fractions, with the method appended when it is not C-025's; the sheet c026_motifs.jpg.

Writes results/motif_panels.json per shot (keyed by the fractions), out/motif_<fractions>.png (one patch | the
motif's mean | the motif at 0.5), and shots/jali-batch/c025_motifs.jpg, all the panels' motifs on one sheet.
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy.signal import fftconvolve

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import structure as S  # noqa: E402

PANELS = ["ours:0,0.35,1,1", "08-humayun-mihrab:0.35,0.52,0.65,0.80", "10-humayun-d:0.36,0.55,0.64,0.82",
          "12-jaisalmer-slide:0.05,0.55,0.95,0.92", "13-jaali-window-a:0.01,0.74,0.44,0.99",
          "16-bibi-ka-maqbara:0.43,0.55,0.62,0.78", "18-fatehpur-sikri-b:0.23,0.76,0.48,0.99"]
ITER = 4
WIDTH = 1.2            # a patch's width in repeats (the longer vector)
SEARCH = 0.1           # the shift allowed, as a share of the shorter repeat (at least 3 px)
MIN_VALID = 0.9        # a patch is used when this share of it lies in the screen
_argv = sys.argv[1:]
FINDER = _argv[_argv.index("--finder") + 1] if "--finder" in _argv else "shortest"   # C-026: consistent
SCORE = _argv[_argv.index("--score") + 1] if "--score" in _argv else "openings"      # C-026: balanced
BAR = 0.80 if SCORE == "balanced" else 0.70
METHOD = "" if (FINDER, SCORE) == ("shortest", "openings") else f" {FINDER} {SCORE}"


def lattice2(pk):
    """C-024's two vectors; when only one peak of 0.25 is found, the second from the peaks of 0.15 or more."""
    b1, b2 = S.lattice(pk)
    if b1 is not None and b2 is None:
        weak = sorted([p for p in pk if p[0] >= 0.15], key=lambda p: np.hypot(p[1], p[2]))
        b2 = next((np.array(p[1:]) for p in weak if abs(b1[0] * p[2] - b1[1] * p[1]) > 0.3 * (b1 @ b1)), None)
    return b1, b2


def lattice_points(shape, b1, b2, M):
    h, w = shape
    o = np.array([w / 2.0, h / 2.0])
    n = int(max(h, w) / min(np.hypot(*b1), np.hypot(*b2))) + 2
    pts = set()
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            x, y = (int(round(v)) for v in o + i * b1 + j * b2)
            if M <= x < w - M and M <= y < h - M:
                pts.add((x, y))
    return sorted(pts)


def fit(m, valid, pts, R, SR, iters):
    """Shifts for every patch, then the leave-one-out IoU. Returns (iou, offsets, the motif's mean over all patches)."""
    mf = m.astype(np.float64)
    vf = valid.astype(np.float64)
    sv = np.where(valid, 2 * mf - 1, 0.0)
    K = len(pts)
    off = np.zeros((K, 2), int)
    n = 2 * R + 1

    def stack():
        P = np.empty((K, n, n))
        Wt = np.empty((K, n, n))
        for k, (x, y) in enumerate(pts):
            dx, dy = off[k]
            P[k] = mf[y + dy - R:y + dy + R + 1, x + dx - R:x + dx + R + 1]
            Wt[k] = vf[y + dy - R:y + dy + R + 1, x + dx - R:x + dx + R + 1]
        return P, Wt

    for _ in range(iters):
        P, Wt = stack()
        sP, sW = (P * Wt).sum(0), Wt.sum(0)
        new = off.copy()
        for k, (x, y) in enumerate(pts):
            w = sW - Wt[k]
            t = np.where(w > 0, 2 * (sP - P[k] * Wt[k]) / np.maximum(w, 1e-9) - 1, 0.0)
            reg = sv[y - R - SR:y + R + SR + 1, x - R - SR:x + R + SR + 1]
            sc = fftconvolve(reg, t[::-1, ::-1], mode="valid")
            iy, ix = np.unravel_index(int(np.argmax(sc)), sc.shape)
            new[k] = (ix - SR, iy - SR)
        if (new == off).all():
            break
        off = new
    P, Wt = stack()
    sP, sW = (P * Wt).sum(0), Wt.sum(0)
    inter = union = inter_s = union_s = 0.0
    for k in range(K):
        w = sW - Wt[k]
        have = (w > 0) & (Wt[k] > 0.5)
        pred = (sP - P[k] * Wt[k]) / np.maximum(w, 1e-9) >= 0.5
        own = P[k] > 0.5
        inter += float((pred & own & have).sum())
        union += float(((pred | own) & have).sum())
        inter_s += float((~pred & ~own & have).sum())
        union_s += float(((~pred | ~own) & have).sum())
    iou_o, iou_s = inter / max(union, 1.0), inter_s / max(union_s, 1.0)
    return (iou_o if SCORE == "openings" else 0.5 * (iou_o + iou_s)), off, sP / np.maximum(sW, 1e-9)


def run(name, d, crop, rng):
    m, valid, box = S.load(d)
    h, w = m.shape
    a, b, c, e = crop
    sl = (slice(int(b * h), int(e * h)), slice(int(a * w), int(c * w)))
    m, valid = m[sl], valid[sl]
    ac, cc, nn = S.autocorr(m.astype(np.float64), valid)
    pk, _ = S.peaks_of(ac, cc, nn, 0.25 * valid.sum())
    b1, b2 = lattice2(pk)
    if FINDER == "consistent":
        b1, b2, _ = S.lattice_consistent(ac, cc, nn, pk, 0.1 * valid.sum())
    out = dict(size=[int(m.shape[1]), int(m.shape[0])],
               repeat_vectors_px=[None if v is None else [round(float(v[0]), 2), round(float(v[1]), 2)] for v in (b1, b2)])
    if b1 is None or b2 is None:
        out["skipped"] = "fewer than two repeat vectors"
        return out, None
    L1, L2 = np.hypot(*b1), np.hypot(*b2)
    R = int(np.ceil(WIDTH * max(L1, L2) / 2))
    SR = max(3, int(round(SEARCH * min(L1, L2))))
    M = R + SR
    pts = [p for p in lattice_points(m.shape, b1, b2, M)
           if valid[p[1] - R:p[1] + R + 1, p[0] - R:p[0] + R + 1].mean() >= MIN_VALID]
    out.update(patch_px=2 * R + 1, shift_max_px=SR, patches=len(pts))
    if len(pts) < 4:
        out["skipped"] = "fewer than four patches"
        return out, None
    iou0, _, _ = fit(m, valid, pts, R, SR, 0)
    iou, off, motif = fit(m, valid, pts, R, SR, ITER)
    base = []
    for _ in range(3):
        rp = []
        while len(rp) < len(pts):
            x, y = int(rng.integers(M, m.shape[1] - M)), int(rng.integers(M, m.shape[0] - M))
            if valid[y - R:y + R + 1, x - R:x + R + 1].mean() >= MIN_VALID:
                rp.append((x, y))
        base.append(fit(m, valid, rp, R, SR, ITER)[0])
    out.update(iou_unshifted=round(iou0, 4), iou=round(iou, 4), baseline_iou=round(float(np.mean(base)), 4),
               shift_px_median=round(float(np.median(np.hypot(off[:, 0], off[:, 1]))), 2),
               shift_px_max=round(float(np.hypot(off[:, 0], off[:, 1]).max()), 2))
    out["counts"] = bool(iou >= BAR and iou - out["baseline_iou"] >= 0.15)
    x, y = pts[len(pts) // 2]
    dx, dy = off[len(pts) // 2]
    patch = m[y + dy - R:y + dy + R + 1, x + dx - R:x + dx + R + 1]
    return out, (patch, motif)


if __name__ == "__main__":
    tiles = []
    slugs = [a for i, a in enumerate(_argv) if not a.startswith("--") and (i == 0 or _argv[i - 1] not in ("--finder", "--score"))]
    for arg in slugs or PANELS:
        name, _, fr = arg.partition(":")
        crop = tuple(float(v) for v in fr.split(","))
        d = S.OURS if name == "ours" else os.path.join(HERE, "shots", name)
        out, img = run(name, d, crop, np.random.default_rng(0))
        key = ",".join(f"{v:g}" for v in crop) + METHOD
        pp = os.path.join(d, "results", "motif_panels.json")
        allp = json.load(open(pp)) if os.path.exists(pp) else {}
        allp[key] = out
        json.dump(allp, open(pp, "w"), indent=1)
        print(f"{name:20s} {key:22s} " + " ".join(f"{k} {v}" for k, v in out.items() if k != "size"), flush=True)
        if img is not None:
            patch, motif = img
            row = np.concatenate([patch * 255.0, np.full((patch.shape[0], 4), 40.0), motif * 255.0,
                                  np.full((patch.shape[0], 4), 40.0), (motif >= 0.5) * 255.0], 1).astype(np.uint8)
            im = Image.fromarray(row)
            im.save(os.path.join(d, "out", f"motif_{key.replace(' ', '_')}.png"))
            s = 220 / im.height
            im = im.resize((int(im.width * s), 220), Image.NEAREST)
            t = Image.new("L", (im.width, 240), 30)
            t.paste(im, (0, 20))
            ImageDraw.Draw(t).text((4, 4), f"{name[:2]}  IoU {out['iou']:.2f} (unshifted {out['iou_unshifted']:.2f}, "
                                   f"random {out['baseline_iou']:.2f})", fill=255)
            tiles.append(t)
    if tiles:
        sheet = Image.new("L", (max(t.width for t in tiles), 240 * len(tiles)), 30)
        for i, t in enumerate(tiles):
            sheet.paste(t, (0, 240 * i))
        sheet.convert("RGB").save(os.path.join(HERE, "c025_motifs.jpg" if not METHOD else "c026_motifs.jpg"), quality=90)
