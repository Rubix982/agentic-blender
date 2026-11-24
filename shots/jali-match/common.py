"""Shared by read_photo.py, build.py and compare.py (all run inside Blender's Python: numpy and OpenImageIO).

One rule sorts the pixels of the photograph and of the render alike, so the comparison measures the build and not two
different rules:
  outside  the dark museum surround: luminance below DARK
  opening  the wall seen through the screen: green above GREEN_RED of red, or (C-008) smooth and within WALL_DIST
           of the wall's colour where it is (a field estimated from the sure wall pixels)
  stone    everything else
Values are the stored (display) values in 0..1, luminance by the Rec. 709 weights.

The first rule (opening: saturation below 0.22 and luminance at least 0.30) found 6.9 % openings and missed most of
them in the upper half (3.5 % there, against 10.9 % by this rule; results/read_photo.json), where the wall behind is dim and warm (saturation 0.2 to 0.35, as low in luminance as lit
stone). Green over red separates the two everywhere in this photo: on smooth pixels the frame's stone reads 0.70 to
0.80, the dim upper wall about 0.86 to 0.96, the lit lower wall about 0.99. At 0.86 the frame bands are 0.01 % opening
and the carved field 17.7 %.

C-008 found the cut still missing about half the wall in the middle of the screen, where it is dim and warm (green
over red 0.82 to 0.85). The wall's colour changes slowly across the picture, so the pixels the cut is sure of give a
colour field for the wall everywhere; a smooth pixel close to that field is wall too. Either rule makes an opening:
13.3 % of the screen against 11.7 %, the frame still clean.

C-009 found the reverse error, which the user saw on the sheet: the lit top edges of the bars, and some thin pale stems,
are pale enough to pass as grey (green over red 0.87 to 0.92) and were called wall. They are brighter than the wall
around them. Of the pixels the cut was sure of, the middle half lie between 0.98 and 1.05 of the local wall's luminance
and the top tenth above 1.27. So a pixel more than LIT above the local wall's luminance, plus LIT_ABS for the noise in
the dim wall, is lit stone, whatever its colour, and the field is worked again without those pixels among its seeds. It
takes 9.6 % of what C-008 called opening: 17.5 % in the top half, where the light catches the bars' upper edges against
a dim wall, and 2.0 % in the bottom (results/read_photo.json, lit_stone).

C-011 found the mirror error at the bottom, where the wall behind is lit almost white: pale, greyish lit stone passed
the cut as wall while darker than the wall around it. The user saw the bottom row's arches missing. Of what the cut
called opening there, 47 % lay more than 15 % below the local wall's luminance, against 0.8 % in the top half, where
smooth wall pixels never went below 0.95 of it (5th percentile). So a pixel more than DIM below the local wall, less
DIM_ABS, is stone too (results/read_photo.json, dim_stone)."""
import numpy as np
import OpenImageIO as oiio

DARK = 0.08
GREEN_RED = 0.86
WALL_DIST = 0.12                    # colour distance from the local wall, as a fraction of the wall's colour
WALL_TEX = 0.05                     # and smooth: luminance's standard deviation over about 5 px below this
WALL_GR_MIN = 0.80                  # and not as red as stone: a render's stone is smooth, so smoothness alone let it in
LIT = 0.12                          # C-009: brighter than the local wall by more than this fraction, plus LIT_ABS, is lit stone
LIT_ABS = 0.03
DIM = 0.15                          # C-011: darker than the local wall by more than this fraction, less DIM_ABS, is stone
DIM_ABS = 0.03
VETO_AREA = 400                     # C-012: an opening smaller than this (px) whose normals lean more than VETO_DEG from
VETO_DEG = 15.0                     # the wall's is lit stone (when the photo's normals are given)
SCALE = 0.5                         # the photo is worked at half its size: 1230 x 1402
PHOTO_W, PHOTO_H = 2460, 2803


def size():
    return round(PHOTO_W * SCALE), round(PHOTO_H * SCALE)


def load(path, wh=None):
    """An image's RGB as float 0..1, resized to wh = (width, height) if given."""
    buf = oiio.ImageBuf(path)
    if wh and (buf.spec().width, buf.spec().height) != tuple(wh):
        buf = oiio.ImageBufAlgo.resize(buf, roi=oiio.ROI(0, wh[0], 0, wh[1], 0, 1, 0, buf.spec().nchannels))
    px = buf.get_pixels(oiio.FLOAT)
    return np.clip(px[:, :, :3], 0, 1)


def luminance(rgb):
    return rgb @ np.array([0.2126, 0.7152, 0.0722], np.float32)


def classify(rgb, normals=None):
    y = luminance(rgb)
    gr = rgb[:, :, 1] / np.maximum(rgb[:, :, 0], 1e-4)
    outside = y < DARK
    sure = ~outside & (gr > GREEN_RED)
    m1 = blur(y, 5)
    tex = np.sqrt(np.maximum(blur(y * y, 5) - m1 * m1, 0))
    seed = sure & (tex < 0.03)
    wall, wsum = wall_field(rgb, seed)

    def off_wall(wall, wsum):
        wy = luminance(wall)
        return ((wsum > 0.003) & (y > wy * (1 + LIT) + LIT_ABS),
                (wsum > 0.003) & (y < wy * (1 - DIM) - DIM_ABS))
    lit, dim = off_wall(wall, wsum)
    wall, wsum = wall_field(rgb, seed & ~lit & ~dim)                   # again, without that stone among the seeds
    lit, dim = off_wall(wall, wsum)
    d = np.linalg.norm(rgb - wall, axis=2) / np.maximum(np.linalg.norm(wall, axis=2), 1e-3)
    near = ~outside & (d < WALL_DIST) & (tex < WALL_TEX) & (wsum > 0.003) & (gr > WALL_GR_MIN)
    opening = (sure | near) & ~lit & ~dim
    veto = np.zeros_like(opening)
    if normals is not None:                                            # C-012: fragments of lit rim the tests missed
        veto = veto_openings(opening, normals)
        opening &= ~veto
    stone = ~outside & ~opening
    return dict(outside=outside, opening=opening, stone=stone, y=y, gr=gr, lit=lit & ~outside & (sure | near),
                dim=dim & ~lit & ~outside & (sure | near), sure=sure, wall_y=luminance(wall), veto=veto)


def label(mask):
    """Connected parts of a boolean mask (4-neighbour): each pixel's label is the smallest index + 1 in its part, 0
    outside. Neighbours' minimum, with pointer jumping (each label replaced by its own pixel's label) to converge fast."""
    h, w = mask.shape
    big = np.int64(h * w + 1)
    lab = np.where(mask, np.arange(1, h * w + 1, dtype=np.int64).reshape(h, w), 0)
    while True:
        l2 = np.where(mask, lab, big)
        m = l2.copy()
        m[1:] = np.minimum(m[1:], l2[:-1])
        m[:-1] = np.minimum(m[:-1], l2[1:])
        m[:, 1:] = np.minimum(m[:, 1:], l2[:, :-1])
        m[:, :-1] = np.minimum(m[:, :-1], l2[:, 1:])
        m = np.where(mask, m, 0)
        flat = m.ravel()
        jumped = np.where(mask, flat[np.maximum(m, 1) - 1].reshape(h, w), 0)
        jumped = np.minimum(jumped, m)
        if (jumped == lab).all():
            return lab
        lab = jumped


def veto_openings(opening, normals):
    """C-012: the openings that are lit stone. Marigold sees the wall through an opening as one flat surface facing the
    camera; a fragment of lit rim the colour tests missed sits on a bar that faces up. Of the photo's openings of 400 px
    or more, the median one's normals lean 5.1 degrees from the wall's (the 99th percentile 10.4); so a smaller opening
    whose normals lean more than VETO_DEG on average is stone. Returns the pixels to make stone."""
    lab = label(opening)
    core = erode(opening, 3)
    nw = np.median(normals[core], axis=0)
    nw = nw / max(float(np.linalg.norm(nw)), 1e-6)
    ang = np.degrees(np.arccos(np.clip(normals @ nw, -1, 1)))
    area = np.bincount(lab.ravel())
    lean = np.bincount(lab.ravel(), weights=ang.ravel()) / np.maximum(area, 1)
    bad = (area < VETO_AREA) & (lean > VETO_DEG)
    bad[0] = False
    return bad[lab]


def wall_field(rgb, seed):
    """The wall's colour everywhere, from the seed pixels: their colour blurred over about 60 px, worked at quarter
    size, and the seeds' blurred weight (where it is near 0 there is no wall nearby to judge by)."""
    seed = seed.astype(np.float32)
    h, w = seed.shape
    q = (max(w // 4, 1), max(h // 4, 1))
    wsum = blur(resize(seed, q), 15)
    wall = np.stack([blur(resize(rgb[:, :, c] * seed, q), 15) for c in range(3)], -1) / np.maximum(wsum, 1e-4)[:, :, None]
    return resize(wall, (w, h)), resize(wsum, (w, h))


def resize(a, wh):
    """Resize a 2D or (H, W, C) float array to wh = (width, height)."""
    a = np.asarray(a, np.float32)
    flat = a.ndim == 2
    a3 = a[:, :, None] if flat else a
    h, w, c = a3.shape
    src = oiio.ImageBuf(oiio.ImageSpec(w, h, c, oiio.FLOAT))
    src.set_pixels(oiio.ROI(0, w, 0, h, 0, 1, 0, c), np.ascontiguousarray(a3))
    out = oiio.ImageBufAlgo.resize(src, roi=oiio.ROI(0, wh[0], 0, wh[1], 0, 1, 0, c)).get_pixels(oiio.FLOAT)
    return out[:, :, 0] if flat else out


def blur(a, width):
    """A Gaussian blur of a 2D float array, by OpenImageIO."""
    h, w = a.shape
    src = oiio.ImageBuf(oiio.ImageSpec(w, h, 1, oiio.FLOAT))
    src.set_pixels(oiio.ROI(0, w, 0, h), np.ascontiguousarray(a[:, :, None].astype(np.float32)))
    k = oiio.ImageBufAlgo.make_kernel("gaussian", width, width)
    return oiio.ImageBufAlgo.convolve(src, k).get_pixels(oiio.FLOAT)[:, :, 0]


def contours(field, level=0.5):
    """Closed outlines of field > level, by marching squares with linear interpolation on the cell edges. The field is
    padded with zeros so every outline closes. Returns a list of (N, 2) arrays of (x, y) pixel coordinates, each
    turned so the inside (field > level) lies on its left in image coordinates (y down)."""
    f = np.pad(field.astype(np.float64), 1)
    H, W = f.shape
    inside = f > level
    tl, tr, br, bl = inside[:-1, :-1], inside[:-1, 1:], inside[1:, 1:], inside[1:, :-1]
    case = tl * 1 + tr * 2 + br * 4 + bl * 8
    ys, xs = np.nonzero((case != 0) & (case != 15))
    centre = (f[:-1, :-1] + f[:-1, 1:] + f[1:, 1:] + f[1:, :-1]) / 4 > level

    def hid(y, x):                                                    # the edge from (y, x) to (y, x + 1)
        return 2 * (y * W + x)

    def vid(y, x):                                                    # the edge from (y, x) to (y + 1, x)
        return 2 * (y * W + x) + 1

    def point(e):
        y, x = divmod(e // 2, W)
        if e % 2 == 0:
            a, b = f[y, x], f[y, x + 1]
            return (x + (level - a) / (b - a) - 1, y - 1)
        a, b = f[y, x], f[y + 1, x]
        return (x - 1, y + (level - a) / (b - a) - 1)

    T, R, B, L = 0, 1, 2, 3
    table = {1: [(T, L)], 2: [(T, R)], 3: [(L, R)], 4: [(R, B)], 6: [(T, B)], 7: [(L, B)], 8: [(L, B)],
             9: [(T, B)], 11: [(R, B)], 12: [(L, R)], 13: [(T, R)], 14: [(T, L)]}
    nbr = {}
    for y, x in zip(ys.tolist(), xs.tolist()):
        c = int(case[y, x])
        if c == 5:
            segs = [(T, R), (L, B)] if centre[y, x] else [(T, L), (R, B)]
        elif c == 10:
            segs = [(T, L), (R, B)] if centre[y, x] else [(T, R), (L, B)]
        else:
            segs = table[c]
        ids = (hid(y, x), vid(y, x + 1), hid(y + 1, x), vid(y, x))
        for a, b in segs:
            ea, eb = ids[a], ids[b]
            nbr.setdefault(ea, []).append(eb)
            nbr.setdefault(eb, []).append(ea)
    loops, seen = [], set()
    for start in list(nbr):
        if start in seen:
            continue
        loop, prev, cur = [start], None, start
        seen.add(start)
        while True:
            nxt = [e for e in nbr[cur] if e != prev]
            if not nxt:
                break
            prev, cur = cur, nxt[0]
            if cur == start:
                break
            if cur in seen:
                break
            seen.add(cur)
            loop.append(cur)
        if len(loop) >= 3:
            loops.append(np.array([point(e) for e in loop]))

    out = []
    for p in loops:                                                   # inside on the left of the direction of travel
        i = len(p) // 2
        d = p[(i + 1) % len(p)] - p[i]
        n = np.hypot(*d)
        if n == 0:
            out.append(p)
            continue
        mid = (p[i] + p[(i + 1) % len(p)]) / 2
        left = mid + np.array([d[1], -d[0]]) / n * 0.35                 # left of travel, image coordinates (y down)
        x, y = int(round(left[0])) + 1, int(round(left[1])) + 1
        x, y = min(max(x, 0), W - 1), min(max(y, 0), H - 1)
        out.append(p if f[y, x] > level else p[::-1])
    return out


def erode(m, r=1):
    """Shrink a boolean mask by r pixels (4-neighbour)."""
    for _ in range(r):
        e = m.copy()
        e[1:] &= m[:-1]; e[:-1] &= m[1:]; e[:, 1:] &= m[:, :-1]; e[:, :-1] &= m[:, 1:]
        m = e
    return m


def dilate(m, r=1):
    """Grow a boolean mask by r pixels (4-neighbour)."""
    for _ in range(r):
        d = m.copy()
        d[1:] |= m[:-1]; d[:-1] |= m[1:]; d[:, 1:] |= m[:, :-1]; d[:, :-1] |= m[:, 1:]
        m = d
    return m


LINE_T = 0.15                       # darker than the surroundings by this fraction
LINE_THIN = 2                       # a dark patch that survives this many erosions is a shadow, not a line
LINE_NEIGHBOURS = 4                 # a line pixel with fewer line pixels in its 5 x 5 window is a speck
LINE_RUN = 8                        # and one with fewer than this in its 9 x 9 window is a short dash: cut as a
                                    # groove, a dash reads as a pit (C-008)


def cut_lines(k):
    """The carved lines inside the stone: pixels darker than their surroundings at a small scale (luminance blurred
    3 px against 15 px, as a fraction of the latter), in dark patches thin enough to vanish under LINE_THIN erosions,
    with specks and short dashes removed. k is classify()'s dict; openings are never lines."""
    small, large = blur(k["y"], 3), blur(k["y"], 15)
    valley = ((large - small) / np.maximum(large, 0.05) > LINE_T) & ~k["opening"]
    lines = valley & ~dilate(erode(valley, LINE_THIN), LINE_THIN)
    def count(m, r):
        n = np.zeros(m.shape, np.int32)
        p = np.pad(m, r)
        for dy in range(2 * r + 1):
            for dx in range(2 * r + 1):
                n += p[dy:dy + m.shape[0], dx:dx + m.shape[1]]
        return n
    lines &= count(lines, 2) >= LINE_NEIGHBOURS + 1
    return lines & (count(lines, 4) >= LINE_RUN + 1)


def area(p):
    x, y = p[:, 0], p[:, 1]
    return 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def write_png(path, a):
    a = np.asarray(a, np.float32)
    if a.ndim == 2:
        a = a[:, :, None]
    h, w, c = a.shape
    f = oiio.ImageBuf(oiio.ImageSpec(w, h, c, oiio.FLOAT))
    f.set_pixels(oiio.ROI(0, w, 0, h, 0, 1, 0, c), np.ascontiguousarray(a))
    o = oiio.ImageBuf(oiio.ImageSpec(w, h, c, oiio.UINT8))
    oiio.ImageBufAlgo.copy(o, f, oiio.UINT8)
    o.write(path)


def write_exr(path, a):
    a = np.asarray(a, np.float32)
    h, w = a.shape
    f = oiio.ImageBuf(oiio.ImageSpec(w, h, 1, oiio.FLOAT))
    f.set_pixels(oiio.ROI(0, w, 0, h), np.ascontiguousarray(a[:, :, None]))
    f.write(path)


def load_array_resized(a, wh):
    """Resize an (H, W, 3) float array to wh = (width, height)."""
    h, w, c = a.shape
    src = oiio.ImageBuf(oiio.ImageSpec(w, h, c, oiio.FLOAT))
    src.set_pixels(oiio.ROI(0, w, 0, h, 0, 1, 0, c), np.ascontiguousarray(a.astype(np.float32)))
    return oiio.ImageBufAlgo.resize(src, roi=oiio.ROI(0, wh[0], 0, wh[1], 0, 1, 0, c)).get_pixels(oiio.FLOAT)


def heights_from_normals(n, region, iters=3000, nz_min=0.2, screen_px=None):
    """C-011: heights, in pixels, whose slopes are the normals' (n: H x W x 3; x right, y up, z towards the viewer).
    Slopes: along a row -nx / nz, down a column +ny / nz (rows count downwards), with nz held at nz_min or more so the
    steep sides at the openings do not dominate. Only slopes between two pixels of the region count; the region's edge
    pixels are held at 0 and everything outside it is 0. Least squares by conjugate gradients, matrix-free, so a bias in
    the normals (the whole picture facing a little up, say) cannot run on across a bar pinned at both its edges.
    screen_px: if given, each height is also pulled towards 0 with weight 1 / screen_px^2 (a screened solve), so slope
    errors cannot add up over more than about that distance: the first C-011 build, unscreened, came out as broad
    bulges about a hundred pixels across that hid the carving."""
    m = region.astype(np.float64)
    inner = (region & erode(region, 1)).astype(np.float64)              # the unknowns: the edge stays at 0
    nz = np.maximum(n[:, :, 2].astype(np.float64), nz_min)
    p = -n[:, :, 0] / nz
    q = n[:, :, 1] / nz
    wu = m[:, 1:] * m[:, :-1]
    wv = m[1:] * m[:-1]
    gu = 0.5 * (p[:, 1:] + p[:, :-1]) * wu
    gv = 0.5 * (q[1:] + q[:-1]) * wv
    h_, w_ = m.shape

    def dt(ru, rv):
        out = np.zeros((h_, w_))
        out[:, :-1] -= ru
        out[:, 1:] += ru
        out[:-1] -= rv
        out[1:] += rv
        return out

    def A(x):
        x = x * inner
        return dt(wu * (x[:, 1:] - x[:, :-1]), wv * (x[1:] - x[:-1])) * inner + mu * x

    mu = 1.0 / screen_px ** 2 if screen_px else 1e-6
    b = dt(gu, gv) * inner
    x = np.zeros_like(m)
    r = b.copy()
    pk = r.copy()
    rr = r0 = float((r * r).sum())
    it = 0
    for it in range(iters):
        Ap = A(pk)
        alpha = rr / max(float((pk * Ap).sum()), 1e-30)
        x += alpha * pk
        r -= alpha * Ap
        rr_new = float((r * r).sum())
        if rr_new < 1e-10 * r0:
            break
        pk = r + (rr_new / rr) * pk
        rr = rr_new
    return (x * inner).astype(np.float32), dict(iterations=it + 1, residual=round(float(np.sqrt(rr / max(r0, 1e-30))), 6))


def field_box(opening, box, min_area=400, pad=6):
    """C-014: the carved field, as the box around every opening of min_area px or more inside the screen's box (x0, y0,
    x1, y1), padded. The frame around it is solid: pale lit stone along its top edge passed the colour rule as wall,
    and Marigold sees the plain frame as flat as a wall, so the normals' veto missed it."""
    x0, y0, x1, y1 = box
    inside = np.zeros_like(opening)
    inside[y0:y1 + 1, x0:x1 + 1] = opening[y0:y1 + 1, x0:x1 + 1]
    lab = label(inside)
    area = np.bincount(lab.ravel())
    big = area >= min_area
    big[0] = False
    # an opening that reaches within 20 px of the box's edge is not the field's (the frame surrounds the field): the
    # pale band along the frame's top was one part of 2,739 px and stretched the field to the top
    edge = np.zeros_like(opening)
    edge[y0:y1 + 1, x0:x1 + 1] = True
    edge[y0 + 20:y1 - 19, x0 + 20:x1 - 19] = False
    big[np.unique(lab[edge & inside])] = False
    big[0] = False
    ys, xs = np.nonzero(big[lab])
    return [int(max(xs.min() - pad, x0)), int(max(ys.min() - pad, y0)), int(min(xs.max() + pad, x1)), int(min(ys.max() + pad, y1))]


def keep_field(k, fb, box):
    """Inside the screen's box (x0, y0, x1, y1), openings only inside the carved field fb; the rest of the box that is
    not the dark surround is stone. Outside the box nothing changes (a first version turned the lit floor below the
    screen to stone, and the screen's box grew to take it in)."""
    x0, y0, x1, y1 = fb
    m = np.ones_like(k["opening"])
    m[box[1]:box[3] + 1, box[0]:box[2] + 1] = False
    m[y0:y1 + 1, x0:x1 + 1] = True
    k["frame_openings"] = k["opening"] & ~m
    k["opening"] = k["opening"] & m
    k["stone"] = ~k["outside"] & ~k["opening"]
    return k


def grey_open(a, r):
    """A grey-scale opening (the minimum over a (2r+1)^2 square, then the maximum): bright features narrower than the
    square go, dark ones stay. C-015 uses it to take the photo's pale specks out of the detail tilt."""
    def shifted(x, f):
        h, w = x.shape
        p = np.pad(x, r, mode="edge")
        out = p[r:r + h, r:r + w].copy()
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                out = f(out, p[r + dy:r + dy + h, r + dx:r + dx + w])
        return out
    return shifted(shifted(np.asarray(a, np.float32), np.minimum), np.maximum)
