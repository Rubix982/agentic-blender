"""C-009: the jali's own symmetry. Find the lattice's repeat and the screen's mirror axis, and average the photo over
both, so each motif is cleaned by every other copy of it.

    python3 skills/blender/scripts/run.py shots/jali-match/symmetry.py
build.py imports average(); run alone it writes out/symmetry.png (photo | averaged | heights) and
results/symmetry.json.

  repeat    the two shortest non-parallel vectors among the strong peaks (at least 0.25) of the openings'
            autocorrelation, over the lower field where the lattice is plain; refined below a pixel by a parabola
  mirror    the column x0 where the field best matches its own mirror image about x0
  average   for every pixel, the photo there and at each lattice translate of it up to MAX_STEPS away, of itself and of
            its mirror image; each copy registered locally (the best match of its 15 x 15 neighbourhood within
            +/- SEARCH px) and weighted by how alike they are (exp(-d / (SHARP x median d))); where a part does not
            repeat (the arch and scrolls at the top) its copies differ and it mostly keeps its own value
  light     luminance is divided by its own 101 px blur first, so the light's slow change across the screen drops out
  heights   from the averaged shading by one least-squares solve over the stone (heights(), below)"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common as C  # noqa: E402

LATTICE_ROWS = (450, 1250)          # the lower field, where the lattice is plain, for finding the repeat
FIELD = (140, 1250, 170, 1060)      # y0, y1, x0, x1 of the carved field inside the frame (half-size pixels)
PATCH = 15
SEARCH = 3                          # each copy is registered locally: the best match within +/- SEARCH px, per pixel
SHARP = 0.5                         # weights exp(-d / (SHARP x the median best distance)): only close matches count
MAX_STEPS = 3                       # average over repeats at most this many lattice steps away: neighbours agree (0.61 at
                                    # 1 step, 0.63 at 2, 0.55 at 3) and far copies do not (0.17 at 6); C-009's card


def box(a, r):
    """Mean over a (2r+1) square, by cumulative sums."""
    p = np.pad(a, ((r + 1, r), (r + 1, r)), mode="edge").cumsum(0).cumsum(1)
    n = 2 * r + 1
    return (p[n:, n:] - p[:-n, n:] - p[n:, :-n] + p[:-n, :-n]) / (n * n)


def peak_refine(ac, y, x):
    def par(m, c, p):
        d = m - 2 * c + p
        return 0.0 if d == 0 else 0.5 * (m - p) / d
    return x + par(ac[y, x - 1], ac[y, x], ac[y, x + 1]), y + par(ac[y - 1, x], ac[y, x], ac[y + 1, x])


def repeat_vectors(opening):
    y0, y1 = LATTICE_ROWS
    m = opening[y0:y1, FIELD[2]:FIELD[3]].astype(np.float64)
    m -= m.mean()
    h, w = m.shape
    F = np.fft.rfft2(m, s=(2 * h, 2 * w))
    ac = np.fft.fftshift(np.fft.irfft2(F * np.conj(F), s=(2 * h, 2 * w)))
    cy, cx = h, w
    ac /= ac[cy, cx]
    peaks = []
    for y in range(cy - 400, cy + 401):
        row = ac[y]
        for x in range(cx, cx + 460):
            v = row[x]
            if v < 0.15 or (abs(y - cy) < 15 and abs(x - cx) < 15):
                continue
            if v >= ac[y - 6:y + 7, x - 6:x + 7].max():
                px, py = peak_refine(ac, y, x)
                peaks.append((float(v), px - cx, py - cy))
    strong = sorted([p for p in peaks if p[0] >= 0.25], key=lambda p: np.hypot(p[1], p[2]))
    # among the strong peaks only: a weak short one (0.18 at 29 px) is an echo inside each motif, not the lattice
    b1 = np.array(strong[0][1:])
    b2 = next(np.array(p[1:]) for p in strong[1:] if abs(np.cross(b1, np.array(p[1:]))) > 0.3 * np.hypot(*b1) ** 2)
    return b1, b2, [(round(v, 3), round(x, 1), round(y, 1)) for v, x, y in sorted(peaks, reverse=True)[:8]]


def mirror_axis(opening):
    y0, y1, x0f, x1f = FIELD
    f = opening[y0:y1].astype(np.float64)
    best = (-2.0, None)
    for x0 in range((x0f + x1f) // 2 - 60, (x0f + x1f) // 2 + 60):
        d = min(x0 - x0f, x1f - x0)
        a = f[:, x0 - d:x0] - f[:, x0 - d:x0].mean()
        b = f[:, x0 + 1:x0 + d + 1][:, ::-1]
        b = b - b.mean()
        r = float((a * b).sum() / np.sqrt((a * a).sum() * (b * b).sum()))
        best = max(best, (r, x0))
    return best[1], best[0]


def shifted(a, dx, dy):
    """a sampled at (x + dx, y + dy), and where that falls inside the picture."""
    h, w = a.shape[:2]
    out = np.zeros_like(a)
    ok = np.zeros((h, w), bool)
    ys, yd = (slice(dy, h), slice(0, h - dy)) if dy >= 0 else (slice(0, h + dy), slice(-dy, h))
    xs, xd = (slice(dx, w), slice(0, w - dx)) if dx >= 0 else (slice(0, w + dx), slice(-dx, w))
    out[yd, xd] = a[ys, xs]
    ok[yd, xd] = True
    return out, ok


SMOOTH_ACROSS = 1.0                 # the solve's weight on neighbouring columns agreeing, against the shading's slope


def heights(lavg, stone, iters=400):
    """Heights from the averaged shading, by least squares over all the stone at once. The light is from above, so a
    surface brighter than its surroundings faces up: the slope going down the picture follows the shading (less its
    31 px mean); neighbouring columns are asked to agree (weight SMOOTH_ACROSS); outside the stone the height is 0, so
    every form comes back to 0 at the openings. Solved by conjugate gradients, matrix-free. (A first version integrated
    each column alone; each column drifted on its own and the heights came out in vertical streaks.)"""
    g = ((lavg - box(lavg, 15)) * stone)[:-1].astype(np.float64)       # slope between row v and v + 1
    m = stone.astype(np.float64)
    lam, mu = SMOOTH_ACROSS, 1e-4

    def dv(h):
        return h[1:] - h[:-1]

    def dvt(r):
        out = np.zeros((r.shape[0] + 1, r.shape[1]))
        out[:-1] -= r
        out[1:] += r
        return out

    def du(h):
        return h[:, 1:] - h[:, :-1]

    def dut(r):
        out = np.zeros((r.shape[0], r.shape[1] + 1))
        out[:, :-1] -= r
        out[:, 1:] += r
        return out

    def A(h):
        h = h * m
        return (dvt(dv(h)) + lam * dut(du(h)) + mu * h) * m

    bvec = dvt(g) * m
    h = np.zeros_like(m)
    r = bvec - A(h)
    p = r.copy()
    rr = float((r * r).sum())
    r0 = rr
    for it in range(iters):
        Ap = A(p)
        alpha = rr / max(float((p * Ap).sum()), 1e-30)
        h += alpha * p
        r -= alpha * Ap
        rr_new = float((r * r).sum())
        if rr_new < 1e-10 * r0:
            break
        p = r + (rr_new / rr) * p
        rr = rr_new
    return (h * m).astype(np.float32), dict(iterations=it + 1, residual=round(float(np.sqrt(rr_new / max(r0, 1e-30))), 6))


def average(rgb, k):
    """The photo averaged over its lattice and its mirror. Returns, at full size, the averaged normalised luminance,
    the averaged opening mask (a fraction 0..1), the heights from the averaged shading (integrated brightness, for the
    caller to scale; 0 outside the stone), and what was found."""
    H, W = k["y"].shape
    fy0, fy1, fx0, fx1 = FIELD
    y = k["y"].astype(np.float32)
    ln_full = y / np.maximum(box(y, 50), 0.05)                         # the light's slow change divided out
    b1, b2, peaks = repeat_vectors(k["opening"])
    x0, mr = mirror_axis(k["opening"])
    ln = ln_full[fy0:fy1, fx0:fx1].astype(np.float32)                 # work inside the carved field
    op = k["opening"][fy0:fy1, fx0:fx1].astype(np.float32)
    h, w = ln.shape
    xs = np.clip(2 * (x0 - fx0) - np.arange(w), 0, w - 1)             # the mirror image about x0, in field columns
    mirror_ok = (2 * (x0 - fx0) - np.arange(w) >= 0) & (2 * (x0 - fx0) - np.arange(w) < w)
    mln, mop = ln[:, xs], op[:, xs]
    offsets = []
    for i in range(-6, 7):
        for j in range(-6, 7):
            t = i * b1 + j * b2
            if abs(t[0]) < w and abs(t[1]) < h and max(abs(i), abs(j), abs(i + j)) <= MAX_STEPS:
                offsets.append((int(round(t[0])), int(round(t[1])), i, j))
    srcs = [(ln, op, np.ones((h, w), bool), False)]
    srcs.append((mln, mop, np.broadcast_to(mirror_ok, (h, w)), True))

    def views():
        for img_l, img_o, okm, mirrored in srcs:
            for dx, dy, i, j in offsets:
                if (dx, dy) == (0, 0) and not mirrored:
                    continue
                sl, ok = shifted(img_l, dx, dy)
                so, _ = shifted(img_o, dx, dy)
                okm2, _ = shifted(okm.astype(np.float32), dx, dy)
                yield sl, so, ok & (okm2 > 0.5), mirrored, i, j

    def registered(sl_unused=None):
        """For each copy, per pixel, the best-matching position within +/- SEARCH px of its lattice place."""
        for img_l, img_o, okm, mirrored in srcs:
            for dx, dy, i, j in offsets:
                if (dx, dy) == (0, 0) and not mirrored:
                    continue
                best_d = np.full((h, w), np.inf, np.float32)
                best_l = np.zeros((h, w), np.float32)
                best_o = np.zeros((h, w), np.float32)
                any_ok = np.zeros((h, w), bool)
                for ex in range(-SEARCH, SEARCH + 1):
                    for ey in range(-SEARCH, SEARCH + 1):
                        sl, ok = shifted(img_l, dx + ex, dy + ey)
                        okm2, _ = shifted(okm.astype(np.float32), dx + ex, dy + ey)
                        ok &= okm2 > 0.5
                        if ok.sum() < 1000:
                            continue
                        d = box(((ln - sl) ** 2) * ok, PATCH // 2).astype(np.float32)
                        d[~ok] = np.inf
                        better = d < best_d
                        if better.any():
                            so, _ = shifted(img_o, dx + ex, dy + ey)
                            best_d[better], best_l[better], best_o[better] = d[better], sl[better], so[better]
                            any_ok |= ok
                if any_ok.sum() > 1000:
                    yield best_l, best_o, best_d, any_ok & np.isfinite(best_d), mirrored, i, j

    copies = list(registered())
    scale = SHARP * float(np.median([np.median(d[ok]) for _, _, d, ok, _, _, _ in copies]))
    num_l, num_o, den = ln.copy(), op.copy(), np.ones((h, w), np.float32)
    for bl, bo, d, ok, mirrored, i, j in copies:
        wgt = np.where(ok, np.exp(-np.where(ok, d, 0) / max(scale, 1e-9)), 0).astype(np.float32)
        num_l += bl * wgt
        num_o += bo * wgt
        den += wgt
    lat = np.zeros((h, w), bool)
    lat[LATTICE_ROWS[0] - fy0:LATTICE_ROWS[1] - fy0, :] = True
    lavg, oavg = num_l / den, num_o / den
    corr, steps = [], []                                              # the card's check, on the plain lattice
    for bl, bo, d, ok, mirrored, i, j in copies:
        m = ok & lat
        if mirrored or m.sum() < 20000:
            continue
        a_, b_ = bo[m] - bo[m].mean(), oavg[m] - oavg[m].mean()
        corr.append(float((a_ * b_).sum() / np.sqrt((a_ * a_).sum() * (b_ * b_).sum() + 1e-12)))
        steps.append(max(abs(i), abs(j), abs(i + j)))                   # lattice steps apart (a hexagon-like count)
    stone = (oavg < 0.5) & ~k["outside"][fy0:fy1, fx0:fx1]
    hgt, cg = heights(lavg, stone)
    full = lambda a, fill: np.pad(a, ((fy0, H - fy1), (fx0, W - fx1)), constant_values=fill)
    info = dict(repeat_vectors_px=[[round(float(v), 2) for v in b1], [round(float(v), 2) for v in b2]],
                autocorrelation_peaks=peaks, mirror_axis_x=int(x0), mirror_correlation=round(mr, 4),
                translates=len(offsets), patch_distance_scale=round(scale, 5), heights_solve=cg,
                repeat_vs_average_correlation=dict(median=round(float(np.median(corr)), 4) if corr else None,
                                                   n=len(corr), all=[round(c, 3) for c in sorted(corr)],
                                                   median_by_steps_apart={str(n): dict(
                                                       median=round(float(np.median([c for c, st in zip(corr, steps) if st == n])), 4),
                                                       n=sum(1 for st in steps if st == n))
                                                       for n in sorted(set(steps))}))
    return full(lavg, 0.0), full(oavg, -1.0), full(hgt, 0.0), info


if __name__ == "__main__":
    W_, H_ = C.size()
    rgb = C.load(os.path.join(HERE, "photo", "agra-jali.jpg"), (W_, H_))
    k = C.classify(rgb)
    lavg, oavg, hgt, info = average(rgb, k)
    print("SYMMETRY", json.dumps(info), flush=True)
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    y = k["y"].astype(np.float32)
    ln = y / np.maximum(box(y, 50), 0.05)
    g = lambda a: np.repeat(np.clip(a, 0, 1)[:, :, None], 3, 2).astype(np.float32)
    hn = hgt / max(float(np.percentile(np.abs(hgt[hgt != 0]), 99)), 1e-6) if (hgt != 0).any() else hgt
    C.write_png(os.path.join(HERE, "out", "symmetry.png"),
                np.concatenate([g(ln * 0.5), g(lavg * 0.5), g(0.5 + 0.5 * hn)], axis=1))
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    with open(os.path.join(HERE, "results", "symmetry.json"), "w") as f:
        json.dump(info, f, indent=1)
