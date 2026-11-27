"""C-024: each screen's structure from its traced openings. For every shot: the two repeat vectors of its opening mask
(the strongest peaks of the mask's autocorrelation), its best left-right mirror axis, and how much of the mask its
copies one lattice step away and its mirror image predict, each pixel's own value left out.

    .venv/bin/python shots/jali-batch/structure.py [SLUG[:fx0,fy0,fx1,fy1] ...]   (no slug: ours and all the batch)

A slug with fractions measures that part of the field only (one panel, cut by hand), into results/structure_panels.json
under the fractions; without, the whole field, into results/structure.json.

Reads each shot's out/classes.png (the traced reading: openings white, stone orange, outside black) and
results/read_photo.json (the carved field's box). Writes results/structure.json per shot and prints one line each.

  autocorrelation  of the opening mask less its mean, over the field, divided by how many pixels overlap at each shift
                   (so a long shift is not weakened by the field's edge), and by its value at no shift
  repeat           the shortest peak of at least 0.25, and the shortest such peak not along it (as symmetry.py, C-009);
                   the peaks are local maxima outside the central lobe (the part around no shift above 0.05)
  mirror           the column where the field best matches its own left-right mirror image (correlation), searched
                   over the middle half of the field
  prediction       each pixel from the mean of its copies at +-b1, +-b2 (bilinear, inside the field) and its mirror
                   image; an opening where the mean is at least 0.5. No copy is registered locally, so a screen carved
                   by hand, or seen at a slant, drifts and loses: the score is a lower bound
  baseline         the same prediction from the same number of copies at random shifts as long as the lattice's, kept
                   a quarter of b1 away from every lattice point; the mean of five draws
  drift            b1 and b2 found again in each quarter of the field (the peak nearest each, within a quarter of its
                   length); how far they move says whether the lattice bends across the photo (the camera's slant)
"""
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OURS = os.path.join(ROOT, "shots", "jali-match")
STRONG = 0.25
LOBE = 0.05


def load(d):
    cl = np.asarray(Image.open(os.path.join(d, "out", "classes.png")).convert("RGB"))
    rp = json.load(open(os.path.join(d, "results", "read_photo.json")))
    x0, y0, x1, y1 = rp.get("field_box", rp.get("box"))
    c = cl[y0:y1 + 1, x0:x1 + 1]
    return (c.min(-1) > 200), (c.max(-1) >= 30), (x0, y0, x1, y1)


def autocorr(m, valid):
    a = np.where(valid, m - m[valid].mean(), 0.0)
    h, w = a.shape
    s = (2 * h, 2 * w)
    F = np.fft.rfft2(a, s=s)
    V = np.fft.rfft2(valid.astype(np.float64), s=s)
    ac = np.fft.fftshift(np.fft.irfft2(F * np.conj(F), s=s))
    n = np.fft.fftshift(np.fft.irfft2(V * np.conj(V), s=s))
    ac = ac / np.maximum(n, 1.0)
    ac /= ac[h, w]
    return ac, (h, w), n


def peaks_of(ac, c, n, min_overlap):
    cy, cx = c
    lobe_lab, _ = ndi.label(ac > LOBE)
    lobe = lobe_lab == lobe_lab[cy, cx]
    mx = ndi.maximum_filter(ac, size=7)
    cand = (ac >= mx) & ~lobe & (ac >= 0.15) & (n >= min_overlap)
    ys, xs = np.nonzero(cand)
    out = []
    for y, x in zip(ys, xs):
        if x < cx or (x == cx and y <= cy):                       # one of each +-pair
            continue
        if 0 < y < ac.shape[0] - 1 and 0 < x < ac.shape[1] - 1:
            def par(m_, c_, p_):
                d = m_ - 2 * c_ + p_
                return 0.0 if d == 0 else 0.5 * (m_ - p_) / d
            fx = x + par(ac[y, x - 1], ac[y, x], ac[y, x + 1])
            fy = y + par(ac[y - 1, x], ac[y, x], ac[y + 1, x])
            out.append((float(ac[y, x]), fx - cx, fy - cy))
    return out, lobe


def lattice(peaks):
    strong = sorted([p for p in peaks if p[0] >= STRONG], key=lambda p: np.hypot(p[1], p[2]))
    if not strong:
        return None, None
    b1 = np.array(strong[0][1:])
    b2 = next((np.array(p[1:]) for p in strong[1:] if abs(b1[0] * p[2] - b1[1] * p[1]) > 0.3 * (b1 @ b1)), None)
    return b1, b2


def ac_at(ac, c, n, v, min_overlap):
    """The autocorrelation at the shift v, bilinear; None outside it or where fewer than min_overlap pixels overlap."""
    x, y = c[1] + v[0], c[0] + v[1]
    if not (0 <= x < ac.shape[1] - 1 and 0 <= y < ac.shape[0] - 1) or n[int(round(y)), int(round(x))] < min_overlap:
        return None
    x0, y0 = int(x), int(y)
    fx, fy = x - x0, y - y0
    return float(ac[y0, x0] * (1 - fx) * (1 - fy) + ac[y0, x0 + 1] * fx * (1 - fy) + ac[y0 + 1, x0] * (1 - fx) * fy
                 + ac[y0 + 1, x0 + 1] * fx * fy)


def reduce_basis(b1, b2):
    """The lattice's shortest basis (Gauss-Lagrange reduction): the same lattice, its two shortest vectors."""
    while True:
        if b1 @ b1 > b2 @ b2:
            b1, b2 = b2, b1
        mu = round(float(b1 @ b2) / float(b1 @ b1))
        if mu == 0:
            return b1, b2
        b2 = b2 - mu * b1


def lattice_consistent(ac, c, n, peaks, min_overlap, top=12):
    """C-026: of the pairs among the strongest peaks (0.15 or more, the TOP strongest), the lattice whose points (every
    sum of up to two steps of each vector, where enough overlaps) have the highest mean autocorrelation; of those within
    a tenth of the best, the smallest cell. A vector that is an echo inside the motif puts lattice points where the
    pattern does not repeat. Returns b1, b2 (the shortest basis) and the mean."""
    vecs = [np.array(p[1:]) for p in sorted([p for p in peaks if p[0] >= 0.15], key=lambda p: -p[0])[:top]]
    found = []
    for i in range(len(vecs)):
        for j in range(i + 1, len(vecs)):
            b1, b2 = vecs[i], vecs[j]
            cell = abs(b1[0] * b2[1] - b1[1] * b2[0])
            if cell < 0.3 * min(b1 @ b1, b2 @ b2):
                continue
            vals = [a for n1 in range(-2, 3) for n2 in range(-2, 3) if (n1, n2) != (0, 0)
                    for a in [ac_at(ac, c, n, n1 * b1 + n2 * b2, min_overlap)] if a is not None]
            if len(vals) >= 4:
                found.append((float(np.mean(vals)), cell, b1, b2))
    if not found:
        return None, None, None
    best = max(f[0] for f in found)
    score, _, b1, b2 = min([f for f in found if f[0] >= 0.9 * best], key=lambda f: f[1])
    b1, b2 = reduce_basis(b1, b2)
    return b1, b2, score


def mirror_axis(m, valid):
    h, w = m.shape
    f = np.where(valid, m - m[valid].mean(), 0.0)
    best = (-2.0, None)
    for x0 in range(w // 4, 3 * w // 4):
        d = min(x0, w - 1 - x0)
        if d < 20:
            continue
        a = f[:, x0 - d:x0]
        b = f[:, x0 + 1:x0 + d + 1][:, ::-1]
        r = float((a * b).sum() / max(np.sqrt((a * a).sum() * (b * b).sum()), 1e-9))
        best = max(best, (r, x0))
    return best[1], best[0]


def shifted(a, valid, v):
    """a and valid sampled at (x + vx, y + vy), bilinear; outside the field invalid."""
    dx, dy = float(v[0]), float(v[1])
    sa = ndi.shift(a.astype(np.float64), (-dy, -dx), order=1, mode="constant", cval=0.0)
    sv = ndi.shift(valid.astype(np.float64), (-dy, -dx), order=1, mode="constant", cval=0.0) > 0.999
    return sa, sv


def mirrored(a, valid, x0):
    h, w = a.shape
    xs = 2 * x0 - np.arange(w)
    ok = (xs >= 0) & (xs < w)
    out = np.zeros_like(a, dtype=np.float64)
    ov = np.zeros_like(valid)
    out[:, ok] = a[:, xs[ok]]
    ov[:, ok] = valid[:, xs[ok]]
    return out, ov


def predict(m, valid, copies):
    s = np.zeros(m.shape)
    k = np.zeros(m.shape)
    for ca, cv in copies:
        s += np.where(cv, ca, 0.0)
        k += cv
    have = valid & (k > 0)
    pred = np.where(have, s / np.maximum(k, 1), 0.0) >= 0.5
    inter = (pred & m & have).sum()
    union = ((pred | m) & have).sum()
    return float(inter / max(union, 1)), float(have.sum() / max(valid.sum(), 1))


def random_shifts(b1, b2, count, rng):
    lens = [np.hypot(*b1)] + ([np.hypot(*b2)] if b2 is not None else [])
    lo, hi = min(lens), max(lens)
    out = []
    while len(out) < count:
        r, t = rng.uniform(lo, hi), rng.uniform(0, 2 * np.pi)
        v = np.array([r * np.cos(t), r * np.sin(t)])
        near = False
        for i in range(-3, 4):
            for j in range(-3, 4):
                p = i * b1 + (j * b2 if b2 is not None else 0)
                if np.hypot(*(v - p)) < 0.25 * lens[0]:
                    near = True
        if not near:
            out.append(v)
    return out


def drift(m, valid, b1, b2):
    h, w = m.shape
    res = []
    for qy in range(2):
        for qx in range(2):
            sl = (slice(qy * h // 2, (qy + 1) * h // 2), slice(qx * w // 2, (qx + 1) * w // 2))
            mq, vq = m[sl], valid[sl]
            if vq.sum() < 0.3 * vq.size or mq[vq].std() == 0:
                res.append(None)
                continue
            ac, c, n = autocorr(mq, vq)
            pk, _ = peaks_of(ac, c, n, 0.15 * vq.sum())
            found = []
            for b in (b1, b2):
                if b is None:
                    continue
                best = None
                for v, x, y in pk:
                    for sgn in (1, -1):
                        dv = np.hypot(sgn * x - b[0], sgn * y - b[1])
                        if dv < 0.25 * np.hypot(*b) and (best is None or dv < best[0]):
                            best = (dv, v)
                found.append(None if best is None else round(best[0], 2))
            res.append(found)
    return res


def run(d, crop=None, finder="shortest"):
    m, valid, box = load(d)
    if crop:
        h, w = m.shape
        a, b, c, e = crop
        sl = (slice(int(b * h), int(e * h)), slice(int(a * w), int(c * w)))
        m, valid = m[sl], valid[sl]
        box = (box[0] + sl[1].start, box[1] + sl[0].start, box[0] + sl[1].stop - 1, box[1] + sl[0].stop - 1)
    rng = np.random.default_rng(0)
    ac, c, n = autocorr(m.astype(np.float64), valid)
    pk, lobe = peaks_of(ac, c, n, 0.25 * valid.sum())
    b1, b2 = lattice(pk)
    if finder == "consistent":                                          # C-026
        b1, b2, _ = lattice_consistent(ac, c, n, pk, 0.1 * valid.sum())
    x0, mr = mirror_axis(m.astype(np.float64), valid)
    mf = m.astype(np.float64)
    copies, scores = [], {}
    if b1 is not None:
        for b in [b1, -b1] + ([b2, -b2] if b2 is not None else []):
            copies.append(shifted(mf, valid, b))
        scores["lattice_only"] = round(predict(m, valid, copies)[0], 4)
    mir = mirrored(mf, valid, x0) if x0 is not None else None
    if mir is not None:
        scores["mirror_only"] = round(predict(m, valid, [mir])[0], 4)
    allc = copies + ([mir] if mir is not None else [])
    iou, cover = predict(m, valid, allc) if allc else (0.0, 0.0)
    base = []
    if b1 is not None:
        for _ in range(5):
            rc = [shifted(mf, valid, v) for v in random_shifts(b1, b2, len(allc), rng)]
            base.append(predict(m, valid, rc)[0])
    out = dict(field_box=list(map(int, box)), opening_share=round(float(m[valid].mean()), 4),
               repeat_vectors_px=[None if b is None else [round(float(b[0]), 2), round(float(b[1]), 2)] for b in (b1, b2)],
               central_lobe_px=int(lobe.sum()),
               peaks=[(round(v, 3), round(x, 1), round(y, 1)) for v, x, y in sorted(pk, reverse=True)[:8]],
               mirror_x=None if x0 is None else int(x0 + box[0]), mirror_r=round(mr, 4),
               prediction_iou=round(iou, 4), predicted_share=round(cover, 4),
               baseline_iou=round(float(np.mean(base)), 4) if base else None, **scores,
               drift_px=drift(m, valid, b1, b2) if b1 is not None else None)
    out["counts_as_lattice"] = bool(out["baseline_iou"] is not None and iou >= 0.70 and iou - out["baseline_iou"] >= 0.15)
    os.makedirs(os.path.join(d, "results"), exist_ok=True)
    if crop:
        pp = os.path.join(d, "results", "structure_panels.json")
        allp = json.load(open(pp)) if os.path.exists(pp) else {}
        allp[",".join(f"{v:g}" for v in crop)] = out
        json.dump(allp, open(pp, "w"), indent=1)
    else:
        json.dump(out, open(os.path.join(d, "results", "structure.json"), "w"), indent=1)
    return out


def probe(d, crop, finder):
    """The repeat alone, by another finder, written nowhere (C-026's check)."""
    m, valid, box = load(d)
    if crop:
        h, w = m.shape
        a, b, c, e = crop
        sl = (slice(int(b * h), int(e * h)), slice(int(a * w), int(c * w)))
        m, valid = m[sl], valid[sl]
    ac, c, n = autocorr(m.astype(np.float64), valid)
    pk, _ = peaks_of(ac, c, n, 0.25 * valid.sum())
    b1, b2, sc = lattice_consistent(ac, c, n, pk, 0.1 * valid.sum())
    return dict(repeat_vectors_px=[None if b is None else [round(float(b[0]), 2), round(float(b[1]), 2)] for b in (b1, b2)],
                mirror_r=0.0, prediction_iou=0.0, baseline_iou=None, counts_as_lattice=False, drift_px=None,
                lattice_mean_ac=None if sc is None else round(sc, 4))


if __name__ == "__main__":
    argv = sys.argv[1:]
    finder = argv[argv.index("--finder") + 1] if "--finder" in argv else "shortest"   # C-026: consistent
    args = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or argv[i - 1] != "--finder")]
    if finder != "shortest":
        print("finder", finder, "(the results files are C-024's and are not written)")
    for arg in args or ["ours"] + sorted(os.listdir(os.path.join(HERE, "shots"))):
        name, _, fr = arg.partition(":")
        crop = tuple(float(v) for v in fr.split(",")) if fr else None
        d = OURS if name == "ours" else os.path.join(HERE, "shots", name)
        name = arg
        try:
            r = run(d, crop, finder) if finder == "shortest" else probe(d, crop, finder)
        except (FileNotFoundError, KeyError) as e:
            print(f"{name:22s} skipped: {e}")
            continue
        print(f"{name:22s} b1 {r['repeat_vectors_px'][0]} b2 {r['repeat_vectors_px'][1]} mirror r {r['mirror_r']:.3f} "
              f"| iou {r['prediction_iou']:.3f} base {r['baseline_iou']} lat {r.get('lattice_only')} mir "
              f"{r.get('mirror_only')} | lattice {r['counts_as_lattice']} | drift {r['drift_px']}", flush=True)
