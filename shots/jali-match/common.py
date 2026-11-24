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
13.3 % of the screen against 11.7 %, the frame still clean."""
import numpy as np
import OpenImageIO as oiio

DARK = 0.08
GREEN_RED = 0.86
WALL_DIST = 0.12                    # colour distance from the local wall, as a fraction of the wall's colour
WALL_TEX = 0.05                     # and smooth: luminance's standard deviation over about 5 px below this
WALL_GR_MIN = 0.80                  # and not as red as stone: a render's stone is smooth, so smoothness alone let it in
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


def classify(rgb):
    y = luminance(rgb)
    gr = rgb[:, :, 1] / np.maximum(rgb[:, :, 0], 1e-4)
    outside = y < DARK
    sure = ~outside & (gr > GREEN_RED)
    m1 = blur(y, 5)
    tex = np.sqrt(np.maximum(blur(y * y, 5) - m1 * m1, 0))
    seed = (sure & (tex < 0.03)).astype(np.float32)
    h, w = y.shape
    q = (max(w // 4, 1), max(h // 4, 1))                               # the wall's field, worked at quarter size
    sq = resize(seed, q)
    wsum = blur(sq, 15)
    wall = np.stack([blur(resize(rgb[:, :, c] * seed, q), 15) for c in range(3)], -1) / np.maximum(wsum, 1e-4)[:, :, None]
    wall, wsum = resize(wall, (w, h)), resize(wsum, (w, h))
    d = np.linalg.norm(rgb - wall, axis=2) / np.maximum(np.linalg.norm(wall, axis=2), 1e-3)
    near = ~outside & (d < WALL_DIST) & (tex < WALL_TEX) & (wsum > 0.003) & (gr > WALL_GR_MIN)
    opening = sure | near
    stone = ~outside & ~opening
    return dict(outside=outside, opening=opening, stone=stone, y=y, gr=gr)


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
