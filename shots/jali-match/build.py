"""C-007 to C-011: rebuild the carved jali from its photograph, light it like the photo, and render it from the photo's
viewpoint. Usually run by make.py, after read_photo.py and normals.py:

    python3 skills/blender/scripts/run.py shots/jali-match/build.py [-- --samples 256]

What comes from the photograph, and nothing else:
  - the outline of the stone and of every opening (inside the screen's box, every pixel common.classify does not call
    an opening, less the dark surround reaching in from the box's edge; blurred 3 px, traced at 0.5 by marching
    squares, smoothed);
  - which way the carving faces at every pixel: Marigold's normals (normals.py, out/normals.npy), integrated into
    heights for the forms' shadows and used as the front's normal map for its shading (C-011);
  - the weathering: the photo's own light and dark, tilting those normals (C-011);
  - the stone's hue (its median colour, brought to an albedo of 0.45 at the brightest channel);
  - the wall's colour in ten bands from top to bottom (the openings' median colour in each), set exactly: the wall
    only emits and is seen straight through the openings;
  - the spotlight's power, fitted by rendering so the stone's median luminance matches the photo's;
  - the pierced field's thickness, 10 mm, chosen because the openings agree best when it is thin (C-008, C-011).
Everything else is made here: the solid (a 2D curve, extruded to the screen's thickness, every edge rounded by the
curve's bevel), a carved front over it, a procedural sandstone, a lit panel behind the screen, a spotlight from above
and in front, and a camera from the photo's EXIF. The size is an estimate (photo/CREDIT.md): the screen 1.05 m wide.

The earlier builds stay as switches: --forms shading (C-009's forms, read from the photo averaged over its repeats),
--no-normal-map, --photo-detail 0, --screen 0 (an unscreened solve), --thick 0.020 (C-008's fit), --fixed-light
(C-011's spot). The spot's pool is fitted to the photo's light map once and kept in results/light_fit.json;
--refit-light searches again (do so after changing the geometry or the photo's rule).

Writes shots/jali-match/out/: scene.blend, render.png, build.json (also results/build.json)."""
import json
import math
import os
import sys
import time

import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common as C  # noqa: E402
import shot  # noqa: E402  (C-022: which photo, its camera and size, and where the outputs go)

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAMPLES = int(argv[argv.index("--samples") + 1]) if "--samples" in argv else 256
THICK_ARG = float(argv[argv.index("--thick") + 1]) if "--thick" in argv else None
LOOK = argv[argv.index("--look") + 1] if "--look" in argv else "None"
# C-011's settings are the defaults; each earlier build is a switch away.
FORMS = argv[argv.index("--forms") + 1] if "--forms" in argv else "normals"   # or "shading" (C-009)
SCREEN_PX = float(argv[argv.index("--screen") + 1]) if "--screen" in argv else 30.0   # the normals' solve; 0: none
SCREEN_PX = SCREEN_PX or None
NORMAL_MAP = "--no-normal-map" not in argv                             # the normals also shade the front
PHOTO_DETAIL = float(argv[argv.index("--photo-detail") + 1]) if "--photo-detail" in argv else 8.0   # tilt; 0: none
PHOTO_DETAIL = PHOTO_DETAIL if NORMAL_MAP else 0.0                     # it tilts the normal map, so needs it
CARVED_SHARE = float(argv[argv.index("--carved-share") + 1]) if "--carved-share" in argv else 0.3
FIXED_LIGHT = "--fixed-light" in argv                                  # C-012: C-011's spot, not fitted to the pool
REFIT_LIGHT = "--refit-light" in argv                                  # C-012: search again (else results/light_fit.json)
TONE = "--no-tone" not in argv                                        # C-013: the photo's tone curve on the render
ALBEDO_NPY = os.path.join(shot.OUT, "albedo.npy")
USE_ALBEDO = "--no-albedo" not in argv and os.path.exists(ALBEDO_NPY)    # C-015: the stone's colour from the photo
SPECK_MAX = float(argv[argv.index("--speck-max") + 1]) if "--speck-max" in argv else 1.6   # C-015: the specks' brightening
SATURATION = "--no-saturation" not in argv                             # C-018: colour falling with brightness
ALBEDO_BLUR = int(argv[argv.index("--albedo-blur") + 1]) if "--albedo-blur" in argv else 41  # C-018: the albedo's stains
MID_W = float(argv[argv.index("--mid-tilt") + 1]) if "--mid-tilt" in argv else 1.0   # C-018: the forms band's tilt weight
SPECK_FLOOR = float(argv[argv.index("--speck-floor") + 1]) if "--speck-floor" in argv else 0.0   # C-018: tried 0.05
TILT_MIN = "--tilt-min" in argv                                         # C-018: tried; see the card
SPOT_WHITE = "--fit-spot-colour" not in argv                            # C-017: fitting the spot's colour did not
                                                                       # move the slopes (2,700 to 10,000 K), so off
NORMALS_NPY = os.path.join(shot.OUT, "normals.npy")
if (FORMS == "normals" or NORMAL_MAP) and not os.path.exists(NORMALS_NPY):
    raise SystemExit("out/normals.npy is missing: run make.py, or .venv/bin/python shots/jali-match/normals.py, first "
                     "(or build C-009's version with --forms shading --no-normal-map)")
FILTER_PX = float(argv[argv.index("--filter") + 1]) if "--filter" in argv else 1.8   # Cycles' pixel filter width:
# the render's edges were 1.072 x as sharp as the photo's at 1.5 px and 0.853 x at 2.5 (compare.json, edge_gradient)
OUT = shot.OUT
os.makedirs(OUT, exist_ok=True)
T0 = time.time()
log = {}

WIDTH_M = shot.WIDTH_M                 # the screen's width (ours 1.05 m, an estimate, photo/CREDIT.md)
THICK_M = THICK_ARG or 0.010          # the pierced field's thickness (--thick to try another). C-008: the openings
                                       # agree best when it is thin (IoU 0.564 at the catalogue's 61 mm, 0.737 at 20,
                                       # 0.754 at 10), and took 20. C-011, with the lit and dim tests in the photo's
                                       # rule: 0.7596 at 10, 0.7501 at 15, 0.7354 at 20, 0.715 at 25; now 10 (at 5 the
                                       # curve's fill broke past repair)
BEVEL_M = float(argv[argv.index("--bevel") + 1]) if "--bevel" in argv else 0.0005   # C-023: a switch. The radius every edge is rounded to (it widens the outline by this). C-007 to
                                       # C-009 used 1 mm and shrank the traced stone by a pixel to make up for it; the
                                       # shrink took the photo's thin connecting pieces (6.8 % of them survived it)
MIN_AREA_PX = 30                       # holes smaller than this (slivers, dust) are dropped; 12 left slivers (C-007)
MIN_ISLAND_PX = 30                     # stone pieces down to this size are kept: small leaf tips are pieces too
RELIEF_M = 0.005                       # C-008: how far the bars rise at most, rounded across their width (C-009: 5 mm,
                                       # under the forms read from the shading)
RELIEF_PX = 20                         # how far in from an opening or the outline (18 mm) they reach that height
FORMS_M = 0.004                        # C-009: the forms read from the averaged shading, at their 99th percentile,
                                       # clipped at 1.5 x that (at 6 mm unclipped they reached 17 mm and read as melted)
# The camera (shot.py): ours a Samsung SM-G998B main camera, 24 mm equivalent, its frame cropped to 2460 px wide.
LENS_MM, SENSOR_MM = shot.LENS_MM, shot.SENSOR_MM

# --- the photograph ----------------------------------------------------------------------------------------------
W, H = C.size()
rgb = C.load(shot.PHOTO, (W, H))
k = C.classify(rgb, np.load(NORMALS_NPY) if os.path.exists(NORMALS_NPY) else None)   # C-012: with the normals' veto
_rp = json.load(open(os.path.join(shot.RESULTS, "read_photo.json"))) if os.path.exists(os.path.join(shot.RESULTS, "read_photo.json")) else {}
if "field_box" in _rp and "--frame-openings" not in argv:              # C-014: the frame is solid (read_photo.py)
    _fmp = os.path.join(shot.OUT, "field_mask.npy")                    # C-023, fix 29: the openings' lattice
    C.keep_field(k, _rp["field_box"], _rp["screen_box_for_field"],
                 np.load(_fmp) if _rp.get("field_mask") and os.path.exists(_fmp) and "--field-box" not in argv else None)
import symmetry  # noqa: E402
if FORMS == "shading":                                                 # C-009: the photo averaged over its repeats
    LAVG, OAVG, HSHADE, SYM = symmetry.average(rgb, k)
else:                                                                  # unused by the normals' forms: skipped (55 s)
    HSHADE = np.zeros(k["y"].shape, np.float32)
    SYM = dict(skipped="the forms come from the normals (--forms normals)")
# The openings stay the photo's own: the averaged mask, tried first, smoothed every repeat's edges and, in the arch at
# the top, mixed in copies that do not belong (openings IoU 0.55, 0.29 in the top third, against 0.725).
rows = np.nonzero(k["stone"].mean(axis=1) > 0.2)[0]
cols = np.nonzero(k["stone"].mean(axis=0) > 0.2)[0]
width_px = int(cols[-1] - cols[0] + 1)
S = WIDTH_M / width_px                                                 # metres per pixel
# The solid: inside the screen's box (the same box compare.py measures in), everything that is not an opening. Dark
# pixels count as stone (deep shadow in the carving) unless they connect to the box's edge (the museum's surround).
# C-014: and unless they are stone-coloured. Once the light pooled in the centre (C-012) the frame's corners fell into
# shadow, and the frame was cut away there with the surround ("vanishing borders"): what was cut inside the box had
# green over red of 0.667 at the median, the real surround outside the box 1.000. So the surround is dark and neutral
# (green over red above 0.8, over a 5 px blur, for the noise) or too dark to tell (luminance under 0.02).
y0, y1, x0, x1 = int(rows[0]), int(rows[-1]), int(cols[0]), int(cols[-1])
dark = np.zeros((H, W), bool)
dark[y0:y1 + 1, x0:x1 + 1] = k["outside"][y0:y1 + 1, x0:x1 + 1]
if "--surround-dark" not in argv:
    gr_blur = C.blur(rgb[:, :, 1].astype(np.float32), 5) / np.maximum(C.blur(rgb[:, :, 0].astype(np.float32), 5), 1e-4)
    dark &= (gr_blur > 0.8) | (k["y"] < 0.02)
# C-023, fix 30 (off): the surround's thin parts (common.keep_field: shadow lines on a facade) kept solid. Tried on 05:
# lit, they rendered at 0.148 where the photo's are 0.008, and with the photo's darkness as their albedo at 0.110; SSIM
# over the box 0.724 (fix 29) to 0.687 and 0.690, the facade's away from the strips 0.661 to 0.618. Cut, they look onto
# the dark panel, as dark as the photo's; the asset takes render.png outside the field (fix 28). --thin-surround-solid.
THIN_SOLID = "thin_surround" in k and "--thin-surround-solid" in argv
if THIN_SOLID:
    dark &= ~k["thin_surround"]
sur = np.zeros_like(dark)
sur[y0, :], sur[y1, :], sur[:, x0], sur[:, x1] = dark[y0, :], dark[y1, :], dark[:, x0], dark[:, x1]
for _ in range(2000):                                                  # grow along dark pixels from the box's edge
    grown = sur.copy()
    grown[1:] |= sur[:-1]; grown[:-1] |= sur[1:]; grown[:, 1:] |= sur[:, :-1]; grown[:, :-1] |= sur[:, 1:]
    grown &= dark
    if (grown == sur).all():
        break
    sur = grown
# The photo shows what can be seen through each opening: the hole's front outline overlapping its back outline, which
# the camera sees scaled towards the picture's centre by dist / (dist + thickness). Extruding that seen region would
# narrow every opening a second time (at 6.1 cm and 1.28 m, by up to 23 mm at the edges). For straight-through holes
# the front outline contains both the seen region and the seen region scaled back out, so their union is the hole.
DIST = LENS_MM / SENSOR_MM * W * S                                     # the camera's distance to the front face
KB = DIST / (DIST + THICK_M)
yy, xx = np.mgrid[0:H, 0:W]


def shifted(kb):
    return (np.clip(np.round(H / 2 + (yy - H / 2) * kb).astype(int), 0, H - 1),
            np.clip(np.round(W / 2 + (xx - W / 2) * kb).astype(int), 0, W - 1))


# C-023: on a fine lattice the offset can be wider than the bars (18: 7.6 px at the field's corners, its bars about 6),
# and the union then cuts through them, joining neighbouring holes into streaks that point at the picture's centre
# (the user: "simmering kind of wave patterns" in the corner panels; 12's holes so merged its fill failed). The photo
# shows those holes apart. So the offset is the camera's unless that merges more than MERGE_MAX of the holes (of 10 px
# or more, in the carved field: a hole merged when its widened outline holds another); then the largest offset that
# merges no more, by halving. Ours merges 4.1 % and keeps the camera's. --no-merge-cap: the camera's always.
MERGE_MAX = 0.10
KB_CAMERA = KB
_fb = _rp.get("field_box", [x0, y0, x1, y1])
FIELD_M = np.zeros((H, W), bool)
FIELD_M[_fb[1]:_fb[3] + 1, _fb[0]:_fb[2] + 1] = True
_lab0 = C.label(k["opening"] & FIELD_M)
_area0 = np.bincount(_lab0.ravel())
_holes = np.nonzero(_area0 >= 10)[0]
_holes = _holes[_holes > 0]


def merged_share(kb):
    if not len(_holes):
        return 0.0
    ssy, ssx = shifted(kb)
    lab1 = C.label((k["opening"] | k["opening"][ssy, ssx]) & FIELD_M)
    comp = np.zeros(_lab0.max() + 1, np.int64)
    np.maximum.at(comp, _lab0.ravel(), lab1.ravel())
    _, inv, cnt = np.unique(comp[_holes], return_inverse=True, return_counts=True)
    return float((cnt[inv] >= 2).mean())


MERGE = dict(kb_camera=round(KB_CAMERA, 5), holes=int(len(_holes)), merged_at_camera=round(merged_share(KB), 4))
# C-023, fix 9: the cap kept the holes apart but left them as straight 1 cm tunnels seen at an angle, and towards the
# picture's edges each tunnel's far wall covered part of its hole (03, 05, 15, 17 were capped to a tenth of the
# camera's offset or less): the bars looked thicker (the user, on 15), the holes dark (17: "unable to decipher what
# belongs to the background and what belongs to the foreground"), the damage growing away from the centre (03, 05).
# So when the widening would merge more than MERGE_MAX of the holes, it is not done: the holes are cut as the photo
# shows them, and every point of the screen is moved back along the camera's ray through it (the back face scaled by
# (dist + thickness) / dist about the camera's axis), so each tunnel's walls lie along the rays and the camera sees
# through every hole whole, as in the photo. Ours merges 4.1 % and keeps its straight, widened tunnels.
# --tunnels camera: aimed at the camera always; --tunnels straight: straight, with the cap (fix 4) as before.
TUNNELS = argv[argv.index("--tunnels") + 1] if "--tunnels" in argv else (
    "camera" if "--no-merge-cap" not in argv and MERGE["merged_at_camera"] > MERGE_MAX else "straight")
if TUNNELS == "camera":
    KB = 1.0                                                           # no widening: the cut is the photo's openings
    MERGE["tunnels"] = "camera"
elif "--no-merge-cap" not in argv and MERGE["merged_at_camera"] > MERGE_MAX:
    lo, hi = 0.0, 1.0 - KB                                             # the offset's share of the camera's, by halving
    for _ in range(6):
        mid = (lo + hi) / 2
        if merged_share(1.0 - mid) <= MERGE_MAX:
            lo = mid
        else:
            hi = mid
    KB = 1.0 - lo
    MERGE.update(kb=round(KB, 5), merged=round(merged_share(KB), 4))
print("MERGE", MERGE, flush=True)
sy, sx = shifted(KB)
# Thin stone in the photo (strips about 4 px wide or less): connecting pieces. The user saw them missing in C-009; the
# one-pixel shrink, not the widening, was what took them (see BEVEL_M). --thin-protect also keeps the widening off them:
# it shows 94 % of them against 89 %, but costs the openings 0.05 of IoU (0.678 against 0.725), so it is off by default.
stone_ph = ~k["opening"] & ~k["outside"]
thin = stone_ph & ~C.dilate(C.erode(stone_ph, 2), 2)
hole = k["opening"] | (k["opening"][sy, sx] & (~thin if "--thin-protect" in argv else True))
solid = np.zeros((H, W), bool)
solid[y0:y1 + 1, x0:x1 + 1] = True
solid &= ~hole & ~sur
# C-023, fix 12 (revised): the holes' half-width, their area over their edge's length in the carved field (ours 4.64 px)
_fbw = _rp.get("field_box", [x0, y0, x1, y1])
_ofw = k["opening"][_fbw[1]:_fbw[3] + 1, _fbw[0]:_fbw[2] + 1]
_inw = _ofw.copy()
_inw[1:-1, 1:-1] = _ofw[1:-1, 1:-1] & _ofw[:-2, 1:-1] & _ofw[2:, 1:-1] & _ofw[1:-1, :-2] & _ofw[1:-1, 2:]
HALF_W_PX = float(_ofw.sum()) / max(float((_ofw & ~_inw).sum()), 1.0)
BACKLIT = C.SIDE == "bright" and C.RULE == "brightness"                # fix 12, third form: see BEVEL below
FINE_HOLES = HALF_W_PX < (2.8 if BACKLIT else 4.2) and "--fixed-bevel" not in argv
OUTLINE_BLUR = int(argv[argv.index("--outline-blur") + 1]) if "--outline-blur" in argv else 3   # C-023: a switch, to
if FINE_HOLES and "--outline-blur" not in argv:                       # (fix 12 revised: see BEVEL below)
    OUTLINE_BLUR = max(1, int(round(3 * HALF_W_PX / 4.64)))
field = C.blur(solid.astype(np.float32), OUTLINE_BLUR)                 # test what the 3 px blur costs fine edges
# C-023, fix 20 (the user, on 03 and 05's lattice: "there are still gaps, some minute details are lost"). Where the
# outline is not blurred (fine holes, a 1 px blur, which OIIO makes the identity) two stone pixels that touch only at a
# corner were always cut apart: the saddle's centre averages exactly 0.5 and counted as hole. A thin stone strand
# running diagonally then broke into pieces of a pixel or two, and the pieces under the island floor (30 px) were
# dropped: in 05's lower-left crop, of the photo's bright stone the render showed dark (10.2 %, all of it read as
# stone), 74 % lay in such pieces (03: 5.2 % and 47 %); counted with corner contacts joined, 23 % (03: 20 %). So a
# corner contact joins the class that is the minority around it (in a 9 x 9 window), the one drawn as lines: the stone
# of a fine tracery on dark holes, the holes of a dense screen as before. Only where the outline is not blurred (OIIO's
# widths 1 and 2 are both the identity): a blurred field ties only by chance (ours, 3 px: 6 exact ties, 4 of them
# joined as stone, no measure moved), and is left as it was. --saddle-split: always cut, as before.
SADDLES = {}
if "--saddle-split" not in argv and OUTLINE_BLUR < 3:
    _sv = np.pad(solid.astype(np.float64), 4, mode="edge").cumsum(0).cumsum(1)
    _sv = np.pad(_sv, ((1, 0), (1, 0)))
    STONE_MINOR = (_sv[9:, 9:] - _sv[:-9, 9:] - _sv[9:, :-9] + _sv[:-9, :-9]) / 81.0 < 0.5
    _fi = field > 0.5
    _sd = ((_fi[:-1, :-1] & _fi[1:, 1:] & ~_fi[:-1, 1:] & ~_fi[1:, :-1]) |
           (~_fi[:-1, :-1] & ~_fi[1:, 1:] & _fi[:-1, 1:] & _fi[1:, :-1]))
    _sd &= np.abs((field[:-1, :-1] + field[:-1, 1:] + field[1:, 1:] + field[1:, :-1]) / 4 - 0.5) < 1e-9
    _sj = STONE_MINOR[:-1, :-1] | STONE_MINOR[:-1, 1:] | STONE_MINOR[1:, 1:] | STONE_MINOR[1:, :-1]
    SADDLES = dict(ties=int(_sd.sum()), stone_joined=int((_sd & _sj).sum()))
    print("SADDLES", SADDLES, flush=True)
    loops = C.contours(field, 0.5, tie=STONE_MINOR)
else:
    loops = C.contours(field, 0.5)
outer_sign = np.sign(C.area(max(loops, key=lambda p: abs(C.area(p)))))   # the frame's outline winds as stone does
# C-023, fix 13: common.contours turns each outline by one sample, the pixel nearest a point 0.35 px to its left; on a
# thin bar or a small hole that pixel can lie across the outline. With the photo's own fine holes cut (fix 9) 1,453 of
# 15's 1,632 outlines came out turned the wrong way (12: 628 of 5,543; 17: 6,660 of 6,973). The fill does not read the
# turning (scanfill and Fill Curve both gave 15's even-odd area, 831,855 px2, to the pixel), but the build does: the
# fill's check sums the outlines' signed areas (1,099,762 for 15, so the check failed at 0.756), and the repairs then
# dropped outlines that were never broken (03 lost a 115,719 px opening to the halving, and rendered it as a grey haze);
# the size floors tell holes from stone pieces by the sign too. So each outline is turned by how many others hold it:
# stone at an even depth, a hole at an odd one, as the fill counts. --sample-turning: as common.contours turned them.
TURNED = 0
if "--sample-turning" not in argv:
    _A = np.array([C.area(q) for q in loops])
    _bb = np.array([[q[:, 0].min(), q[:, 1].min(), q[:, 0].max(), q[:, 1].max()] for q in loops])

    def _holds(pt, q):                                                 # even-odd point in polygon
        xs, ys = q[:, 0], q[:, 1]
        xe, ye = np.roll(xs, -1), np.roll(ys, -1)
        dy = np.where(ye == ys, 1e-12, ye - ys)
        return bool((((ys > pt[1]) != (ye > pt[1])) & (pt[0] < (xe - xs) * (pt[1] - ys) / dy + xs)).sum() % 2)
    for _i in range(len(loops)):
        _pt = loops[_i][0]
        _cand = np.nonzero((_bb[:, 0] <= _pt[0]) & (_bb[:, 2] >= _pt[0]) & (_bb[:, 1] <= _pt[1]) & (_bb[:, 3] >= _pt[1])
                           & (np.abs(_A) > abs(_A[_i])))[0]
        _depth = sum(1 for _j in _cand if _holds(_pt, loops[_j]))
        if np.sign(_A[_i]) != outer_sign * (1 if _depth % 2 == 0 else -1):
            loops[_i] = loops[_i][::-1].copy()
            TURNED += 1
print("TURNED", TURNED, "of", len(loops), flush=True)
# C-023: MIN_AREA_PX and MIN_ISLAND_PX were set on ours, whose holes are large (half its hole area lies in holes of 515 px
# or more), and there the holes under 30 px are 1.6 % of the hole area, specks. A fine lattice's are its pattern: 04
# (half in holes of 89 px or more) lost 20.7 % of its hole area, the tree's pinpricks of light. So each floor is the
# smaller of its value and a twelfth of the hole size that holds half the screen's hole area (in the carved field),
# and never under 4 px. Ours keeps 30. --fixed-floors: 30 always.
_fb2 = _rp.get("field_box", [x0, y0, x1, y1])
_lab_f = C.label(k["opening"][_fb2[1]:_fb2[3] + 1, _fb2[0]:_fb2[2] + 1])
_ha = np.sort(np.bincount(_lab_f.ravel())[1:])
_ha = _ha[_ha > 0]
HOLE_A50 = float(_ha[np.searchsorted(np.cumsum(_ha) / _ha.sum(), 0.5)]) if len(_ha) else 1e9
FLOORS = dict(hole_area_half_at=int(min(HOLE_A50, 1e9)))
if "--fixed-floors" not in argv:
    _floor = max(4.0, HOLE_A50 / 12.0)
    if _floor < MIN_AREA_PX or _floor < MIN_ISLAND_PX:
        MIN_AREA_PX, MIN_ISLAND_PX = min(MIN_AREA_PX, _floor), min(MIN_ISLAND_PX, _floor)
        FLOORS.update(min_area_px=round(MIN_AREA_PX, 1), min_island_px=round(MIN_ISLAND_PX, 1))
print("FLOORS", FLOORS, flush=True)
# C-023, fix 12: the bevel rounds every edge outwards, so the stone widens by its radius on each side. On ours that is
# 11.7 % of the holes' half-width (their area over their edge's length in the carved field, 4.64 px; the bevel 0.54 px);
# on the batch up to 37 % (17), and 03 built without it came out better on every measure (SSIM 0.497 to 0.529,
# openings IoU 0.612 to 0.671, the render's open share 0.244 to 0.276 against the photo's 0.287). First form: the
# bevel no larger a share of a hole than 12.5 % of its half-width. --bevel R sets it.
BEVEL_RULE = dict(hole_half_width_px=round(HALF_W_PX, 3))
# Revised: on 15 (half-width 2.0 px) the share rule's 0.37 mm (0.25 px) still left each hole's edge ring at 0.675 against
# the photo's 0.32, its rounded rim catching the light; with no bevel and the outline blurred over 1 px in place of 3,
# 0.576, SSIM 0.597 to 0.625, openings IoU 0.530 to 0.595 (the blur alone: 0.602 and 0.540). So where the holes are
# finer than ours's there is no bevel, and the outline's blur (above) is 3 px times the half-width over ours's, at
# least 1 px. The cut was first 4.2 px; 09 (3.92) lost by it, SSIM 0.566 with its bevel against 0.553 without, 08 (4.08)
# and 10 (3.48) a little; 15 (2.0), 03 (2.47) and 01 (2.23) gained. Second form: under 3.0 px; that cost 02 (3.12:
# SSIM 0.588 without its bevel, 0.582 with). Then taken apart on the backlit 13 and 10: 13 with its bevel 0.725 against
# 0.716 (IoU 0.817 against 0.791), 10 without it 0.810 against 0.826, as 09 (0.566 against 0.553). Every loss had been
# on a screen lit from behind, every gain on lit stone (03, 15 under the dark rule; 01, 02 under the colour rule). Lit
# from the front, the rounded rim catches the light as a pale ring inside each dark hole; lit from behind it lies on the
# bright edge, as the glow at a backlit hole's edge does. Third form, not backlit: that cost the finest backlit
# lattices, where the bevel also takes a large share of each hole (17, half-width 1.81 px: SSIM 0.690 without, 0.647
# with; 14 (2.58) 0.783 and 0.755; 18 (2.57) 0.798 and 0.769; 16 (2.72) 0.564 and 0.563). In order of half-width the
# backlit seven are hurt at 1.81, 2.57 and 2.58, level at 2.72, helped at 2.995, 3.48 and 3.92. Fourth form: under
# 4.2 px lit from the front, under 2.8 px backlit. Ours (4.64) keeps 0.5 mm and 3 px. --fixed-bevel: always.
if FINE_HOLES and "--bevel" not in argv:
    BEVEL_M = 0.0
    BEVEL_RULE.update(bevel_m=0.0)
if FINE_HOLES and "--outline-blur" not in argv:
    BEVEL_RULE.update(outline_blur_px=OUTLINE_BLUR)
print("BEVEL", BEVEL_RULE, flush=True)
loops = [p for p in loops if abs(C.area(p)) >= (MIN_ISLAND_PX if np.sign(C.area(p)) == outer_sign else MIN_AREA_PX)]


def taubin(p, n=20, lam=0.5, mu=-0.53):                               # 6 passes left 1-2 px notches
    """Smooth a closed outline without shrinking it (Taubin): each point moves towards its neighbours' mean, then back
    a little further. The user saw the openings' edges as rough (C-009): the trace followed the mask's pixel noise."""
    for _ in range(n):
        for f in (lam, mu):
            p = p + f * ((np.roll(p, 1, 0) + np.roll(p, -1, 0)) / 2 - p)
    return p


loops_raw = list(loops)                                                # kept: the fill's repair falls back on them
loops = [taubin(p) if len(p) >= 8 else p for p in loops]
thin_in = thin & np.pad(np.ones((y1 - y0 + 1, x1 - x0 + 1), bool), ((y0, H - y1 - 1), (x0, W - x1 - 1)))
log["thin_stone"] = dict(photo_px=int(thin_in.sum()), kept_by_widening=round(float((thin_in & solid).sum() / max(thin_in.sum(), 1)), 4),
                         kept_by_trace=round(float((thin_in & (field > 0.5)).sum() / max(thin_in.sum(), 1)), 4))
# C-008: the carving. The bars round across their width: the height rises with distance from the nearest opening or
# outline, RELIEF_M at most, about RELIEF_PX in. The distance is smooth: the stone mask blurred over 2 x RELIEF_PX reads
# 0.5 at an edge and 1 deep inside, so (b - 0.5) x 2, eased, goes 0 to 1. The cut lines traced from the photo
# (common.cut_lines) are cut GROOVE_M into that surface.
# Two first versions, recorded in the card: every piece between the lines rising on its own (the lines cut the stone
# into hundreds of small humps; it read as crumbled rock), and the distance counted by erosions (it stepped in blocks).
# C-009: the forms. The averaged shading, integrated down each column of stone (symmetry.average), scaled so its 99th
# percentile is FORMS_M, is added to the rounded bars; C-008's grooves from traced lines are gone.
# Pin-prick holes (dropped from the trace) are filled where the stone around them nearly closes over them. A closing
# (dilate 2, erode 2), used first, also bridged every opening under ~4 px wide, and the skin overhung the smooth outline
# there with its pixel-stepped edge: the "rough edges" the user saw. The skin also stays 2 px inside the stone, where
# its relief has faded to 0, so the visible edge is the body's smoothed outline.
closed = solid | (C.blur(solid.astype(np.float32), 5) > 0.85)
skin = C.erode(closed, 2)
lines = C.cut_lines(k) & skin                                          # kept for the log; no longer cut
b = np.clip((C.blur(skin.astype(np.float32), 2 * RELIEF_PX) - 0.5) * 2, 0, 1)
prof = b * b * (3 - 2 * b)                                             # smoothstep
hs = HSHADE * skin
p99 = float(np.percentile(np.abs(hs[hs != 0]), 99)) if (hs != 0).any() else 1.0
forms = np.clip(hs / max(p99, 1e-6), -1.5, 1.5) * FORMS_M
# The skin's edge is stepped (it is built on the pixel grid); everything on it fades to 0 over the last ~4 px, so the
# steps sit flat on the body's front face instead of catching light. Then a light smoothing of the heights.
e = np.clip((C.blur(skin.astype(np.float32), 9) - 0.5) * 2, 0, 1)
edge = e * e * (3 - 2 * e)
height = np.maximum(prof * RELIEF_M + forms, 0) * edge
# C-011: --forms normals. The heights come from Marigold's normals (normals.py), integrated over the skin and held at 0
# on its edge, in pixels of height per pixel, so in metres with no scale fitted unless their 99th percentile falls
# outside 2 to 12 mm (then scaled to FORMS_M, and logged). The bars' rounded profile is dropped: the normals carry it.
if FORMS == "normals":
    NRM = np.load(os.path.join(OUT, "normals.npy"))
    hn_px, nsolve = C.heights_from_normals(NRM, skin, screen_px=SCREEN_PX)
    hn = hn_px * S
    p99n = float(np.percentile(hn[skin], 99))
    scale_n = 1.0 if 0.002 <= p99n <= 0.012 else FORMS_M / max(p99n, 1e-9)
    height = np.maximum(hn * scale_n, 0) * edge
    log["normals"] = dict(solve=nsolve, screen_px=SCREEN_PX, p99_m=round(p99n, 5), p1_m=round(float(np.percentile(hn[skin], 1)), 5),
                          below_front_share=round(float((hn[skin] < 0).mean()), 4), scale=round(scale_n, 4))
    print("NORMALS", log["normals"], flush=True)
height = (C.blur(height.astype(np.float32), 3) * edge * skin).astype(np.float32)
C.write_png(os.path.join(OUT, "height.png"), height / max(float(height.max()), 1e-6))
log["sizes"] = dict(width_m=WIDTH_M, thick_m=THICK_M, thick_cm=THICK_M * 100, bevel_m=BEVEL_M)
log["outlines"] = dict(count=len(loops), points=int(sum(len(p) for p in loops)), metres_per_px=round(S, 6),
                       screen_width_px=width_px, box=[x0, y0, x1, y1], dark_in_box_made_stone=int((dark & ~sur).sum()),
                       surround_in_box=int(sur.sum()), back_face_scale=round(KB, 4), **({'merge_cap': MERGE} if 'kb' in MERGE or 'tunnels' in MERGE else {}), **({'floors': FLOORS} if 'min_area_px' in FLOORS else {}), **({'bevel_rule': BEVEL_RULE} if 'bevel_m' in BEVEL_RULE else {}), **({'turned': TURNED} if TURNED else {}), **({'saddles': SADDLES} if SADDLES.get('ties') else {}),
                       seen_opening_share=round(float(k["opening"][y0:y1 + 1, x0:x1 + 1].mean()), 4),
                       hole_share=round(float(hole[y0:y1 + 1, x0:x1 + 1].mean()), 4),
                       cut_line_share=round(float(lines[y0:y1 + 1, x0:x1 + 1].mean()), 4))
print("OUTLINES", log["outlines"], flush=True)

stone_rgb = np.median(rgb[k["stone"]], axis=0)
lin = np.where(stone_rgb <= 0.04045, stone_rgb / 12.92, ((stone_rgb + 0.055) / 1.055) ** 2.4)
ALBEDO = tuple(float(c) for c in lin / lin.max() * 0.45)

# --- the scene ---------------------------------------------------------------------------------------------------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
# The curve is built in pixels and only its mesh is scaled to metres. At 0.92 mm a pixel one smoothed island of
# 15 x 4 px turned the whole fill inside out (front face 0.31 m2 of the 1.15 the outlines enclose; C-009, when the lit
# edges became stone); the same outlines fill as they should at 1 or 0.01 units a pixel (probably the fill merges points
# closer than a fixed distance; not checked). The mesh, not the object, is scaled, because the stone's texture is read
# in object coordinates.
cx, cy = W / 2, H / 2
# C-023, fix 25: the outlines (common.contours) put a pixel's centre at whole coordinates, pixel i at i; the camera's
# frame, W x S wide and centred on 0, puts pixel i's centre at (i + 0.5 - W / 2) x S. Centred at W / 2, the geometry and
# its textures (mapped through the same cx, cy) sat half a pixel up and left of the camera's grid: every render was
# (0.41 to 0.47, 0.30 to 0.54) px off its photo by phase correlation (ours 0.46, 0.38; 03 0.47, 0.54; 05 0.46, 0.51),
# which on bars 4 to 10 px wide read as their top and left edges bright and their bottom and right edges dark
# (03: 0.743 and 0.729 against 0.579 and 0.588, the photo's within 0.024 of each other), and cost every measure taken
# pixel by pixel. So the centre is the grid's. --old-centre: as before.
if "--old-centre" not in argv:
    cx, cy = (W - 1) / 2, (H - 1) / 2


def trace_mesh(L, flat=False, fill="BOTH"):
    """The outlines as a 2D curve in pixels, filled (and, unless flat, extruded and bevelled), made a mesh."""
    cu = bpy.data.curves.new("jali", "CURVE")
    cu.dimensions = "2D"
    cu.fill_mode = fill
    cu.resolution_u = 1
    if not flat:
        cu.extrude = (THICK_M / 2 - BEVEL_M) / S
        cu.bevel_depth = BEVEL_M / S
        cu.bevel_resolution = 3
    # cu.offset stays 0: any other value broke the fill of these nested outlines (front face 0.24 m2 at -3 mm, 0.09 at
    # +3 mm, against 1.10 at 0; the outlines enclose 1.15 m2).
    for p in L:
        sp = cu.splines.new("POLY")
        sp.points.add(len(p) - 1)
        co = np.zeros((len(p), 4), np.float32)
        co[:, 0] = p[:, 0] - cx
        co[:, 1] = cy - p[:, 1]
        co[:, 3] = 1.0
        sp.points.foreach_set("co", co.ravel())
        sp.use_cyclic_u = True
        sp.use_smooth = True                                           # flat facets striped the holes' side walls
    trace = bpy.data.objects.new("jali trace", cu)
    scene.collection.objects.link(trace)
    me = bpy.data.meshes.new_from_object(trace.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(trace)
    bpy.data.curves.remove(cu)
    return me


def front_px(me):
    return sum(f.area for f in me.polygons if f.normal.z > 0.99)


# C-020: Blender's curve fill (its scan-fill) can break on a few outlines, at some scales and positions and not others:
# moving one island by 0.0005 px, or rounding the points to 1e-5 px, turns the break on and off (experiments/curves/
# curve_fill_knife_edge.py). Geometry Nodes' Fill Curve (constrained Delaunay) filled the same outlines every time. So
# the repair keeps the curve's extruded, bevelled walls with its fill off, and takes the front and back from Fill Curve
# at the walls' top and bottom.
FILL_NG = bpy.data.node_groups.new("fill curve", "GeometryNodeTree")
FILL_NG.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
FILL_NG.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
_gi, _go, _fc = FILL_NG.nodes.new("NodeGroupInput"), FILL_NG.nodes.new("NodeGroupOutput"), FILL_NG.nodes.new("GeometryNodeFillCurve")
FILL_NG.links.new(_gi.outputs[0], _fc.inputs[0])
FILL_NG.links.new(_fc.outputs[0], _go.inputs[0])


def trace_mesh_cdt(L):
    import bmesh
    walls = trace_mesh(L, fill="NONE")
    zc = max(v.co.z for v in walls.vertices)                            # the walls' top: where the curve's cap sits
    cu = bpy.data.curves.new("caps", "CURVE")
    cu.dimensions, cu.fill_mode, cu.resolution_u = "2D", "NONE", 1
    for p in L:
        sp = cu.splines.new("POLY")
        sp.points.add(len(p) - 1)
        co = np.zeros((len(p), 4), np.float32)
        co[:, 0], co[:, 1], co[:, 3] = p[:, 0] - cx, cy - p[:, 1], 1.0
        sp.points.foreach_set("co", co.ravel())
        sp.use_cyclic_u = True
    ob = bpy.data.objects.new("caps", cu)
    scene.collection.objects.link(ob)
    ob.modifiers.new("fill", "NODES").node_group = FILL_NG
    cap = bpy.data.meshes.new_from_object(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(ob)
    bpy.data.curves.remove(cu)
    bm = bmesh.new()
    bm.from_mesh(walls)
    for sign in (1.0, -1.0):
        part = bmesh.new()
        part.from_mesh(cap)
        for v in part.verts:
            v.co.z = sign * zc
        if sign < 0:
            bmesh.ops.reverse_faces(part, faces=part.faces)
        tmp = bpy.data.meshes.new("cap part")
        part.to_mesh(tmp)
        part.free()
        bm.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)
    out = bpy.data.meshes.new("jali")
    bm.to_mesh(out)
    bm.free()
    bpy.data.meshes.remove(walls)
    bpy.data.meshes.remove(cap)
    return out


# The fill can still fail in pixels (C-011, at 15 mm: front face 0.280 m2 of 1.145), and both times it was one small
# smoothed island, at about (981, 141), that filled correctly unsmoothed; why is not known (T-014). So when the fill
# falls short, the outlines are halved until the one that breaks it is found, it is swapped for its unsmoothed outline,
# and that is logged; if the same outline is found again, it is dropped (at 5 mm a 120 px hole broke the fill either
# way). At most five times, then the build stops.
if "--dump-loops" in argv:                                             # C-023: to study the fill's failures (T-014)
    _dp = argv[argv.index("--dump-loops") + 1]
    np.savez_compressed(_dp, n=len(loops), field_box=np.array(_rp.get("field_box", [0, 0, 0, 0])), outer_sign=outer_sign,
                        **{f"s{i}": q for i, q in enumerate(loops)}, **{f"r{i}": q for i, q in enumerate(loops_raw)})
    print("DUMPED", _dp, len(loops), flush=True)
    raise SystemExit(0)
me_c = trace_mesh_cdt(loops) if "--cdt-caps" in argv else trace_mesh(loops)
repairs = []
if front_px(me_c) < 0.85 * abs(sum(C.area(p) for p in loops)):         # C-020: first the constrained Delaunay caps
    bpy.data.meshes.remove(me_c)
    me_c = trace_mesh_cdt(loops)
    repairs.append(dict(action="caps from Fill Curve (constrained Delaunay)"))
# C-023, fix 10: after fix 8, 15's fill failed past the halving's five tries, and the outlines it found were all on one
# row, y = 1334.5: the carved field's bottom edge, where keep_field cuts every opening that crosses it with a straight
# line (the frame's carved grooves, read as holes). Many holes ending on one line is what the fill breaks on, it
# seems. So the second repair makes those cut-off openings stone: every hole outline with a point within
# 1.5 px of the field box's edge. Only on a failed fill: ours fills first time and keeps the 22 px its box cuts.
_fbc = _rp.get("field_box")
if _fbc and front_px(me_c) < 0.85 * abs(sum(C.area(p) for p in loops)):
    _lines = ((0, _fbc[0] - 0.5), (0, _fbc[2] + 0.5), (1, _fbc[1] - 0.5), (1, _fbc[3] + 0.5))

    def _cut(p):                                                       # (any point within 1.5 px: three within
        return np.sign(C.area(p)) != outer_sign and any(                # 1 px missed 15's small holes on the row)
            bool((np.abs(p[:, ax] - v) <= 1.5).any()) for ax, v in _lines)
    _drop = [i for i in range(len(loops)) if _cut(loops[i])]
    if _drop:
        repairs.append(dict(action="openings cut by the carved field's edge made stone", loops=len(_drop),
                            area_px=round(float(sum(abs(C.area(loops[i])) for i in _drop)), 1)))
        _keep = [i for i in range(len(loops)) if i not in set(_drop)]
        loops, loops_raw = [loops[i] for i in _keep], [loops_raw[i] for i in _keep]
        bpy.data.meshes.remove(me_c)
        me_c = trace_mesh_cdt(loops)
if front_px(me_c) < 0.85 * abs(sum(C.area(p) for p in loops)):
    bpy.data.meshes.remove(me_c)
    outer = max(range(len(loops)), key=lambda i: abs(C.area(loops[i])))

    def fills(ids):
        L = [loops[outer]] + [loops[i] for i in ids]
        me = trace_mesh(L, flat=True)
        a = front_px(me)
        bpy.data.meshes.remove(me)
        return a > 0.85 * abs(sum(C.area(p) for p in L))
    for _ in range(5):
        cand = [i for i in range(len(loops)) if i != outer]
        if fills(cand):
            break
        while len(cand) > 1:
            half = cand[:len(cand) // 2]
            cand = half if not fills(half) else cand[len(cand) // 2:]
        i = cand[0]
        again = any(r.get("loop") == i for r in repairs)               # its unsmoothed outline broke it too: drop it
        # (C-022: .get, since the Fill Curve repair's entry has no loop; 15-nilabagh-palace crashed on it)
        repairs.append(dict(loop=i, centre_px=[round(float(v), 1) for v in loops[i].mean(0)],
                            area_px=round(float(abs(C.area(loops[i]))), 1), action="dropped" if again else "unsmoothed"))
        loops[i] = loops_raw[i] if not again else None
        if again:
            keep = [j for j in range(len(loops)) if loops[j] is not None]
            loops = [loops[j] for j in keep]
            loops_raw = [loops_raw[j] for j in keep]
            outer = max(range(len(loops)), key=lambda j: abs(C.area(loops[j])))
            for r in repairs:                                          # indices shift after a drop
                if "loop" in r:
                    r["loop"] = -1 if r["loop"] == i else r["loop"] - (r["loop"] > i)
    me_c = trace_mesh(loops)
me_c.transform(Matrix.Scale(S, 4))
expected = abs(sum(C.area(p) for p in loops)) * S * S
front_m2 = sum(f.area for f in me_c.polygons if f.normal.z > 0.99)
log["fill_repairs"] = repairs
if repairs:
    print("FILL REPAIRED", repairs, flush=True)
if front_m2 < 0.85 * expected:                                         # a broken fill: stop before rendering it
    raise RuntimeError(f"the curve's fill failed: front face {front_m2:.3f} m2 of {expected:.3f}")
# Kept as a measurement: the same outlines built in metres, as before C-009's fix, and their front face.
cu_m = bpy.data.curves.new("jali in metres", "CURVE")
cu_m.dimensions, cu_m.fill_mode, cu_m.resolution_u = "2D", "BOTH", 1
cu_m.extrude, cu_m.bevel_depth, cu_m.bevel_resolution = THICK_M / 2 - BEVEL_M, BEVEL_M, 3
for p in loops:
    sp = cu_m.splines.new("POLY")
    sp.points.add(len(p) - 1)
    co = np.zeros((len(p), 4), np.float32)
    co[:, 0], co[:, 1], co[:, 3] = (p[:, 0] - cx) * S, (cy - p[:, 1]) * S, 1.0
    sp.points.foreach_set("co", co.ravel())
    sp.use_cyclic_u = True
ob_m = bpy.data.objects.new("jali in metres", cu_m)
scene.collection.objects.link(ob_m)
ev_m = ob_m.evaluated_get(bpy.context.evaluated_depsgraph_get())
me_m = ev_m.to_mesh()
front_in_metres_m2 = sum(f.area for f in me_m.polygons if f.normal.z > 0.99)
ev_m.to_mesh_clear()
bpy.data.objects.remove(ob_m)
bpy.data.curves.remove(cu_m)
if TUNNELS == "camera":                                                # C-023, fix 9: each point back along its ray
    _v = np.empty(len(me_c.vertices) * 3, np.float32)
    me_c.vertices.foreach_get("co", _v)
    _v = _v.reshape(-1, 3)
    _f = (DIST + (THICK_M / 2 - _v[:, 2])) / DIST                      # 1 on the front face, its depth behind it
    _v[:, 0] *= _f
    _v[:, 1] *= _f
    me_c.vertices.foreach_set("co", _v.ravel())
    me_c.update()
    log["outlines"]["tunnels"] = dict(aimed_at_camera=True, back_face_scale=round(float((DIST + THICK_M) / DIST), 5))
screen = bpy.data.objects.new("jali", me_c)
scene.collection.objects.link(screen)
screen.rotation_euler = (math.radians(90), 0, 0)                      # stands up, facing -Y

def sock(node, ident, out=False):
    """A socket by identifier: the Mix node's float and colour sockets share their names."""
    return next(x for x in (node.outputs if out else node.inputs) if x.identifier == ident)


mat = bpy.data.materials.new("red sandstone")
mat.use_nodes = True
nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
tc = nt.nodes.new("ShaderNodeTexCoord")
noise = nt.nodes.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 25.0
noise.inputs["Detail"].default_value = 6.0
ramp = nt.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].color = tuple(c * 0.75 for c in ALBEDO) + (1.0,)
ramp.color_ramp.elements[1].color = tuple(min(1.0, c * 1.1) for c in ALBEDO) + (1.0,)
vor = nt.nodes.new("ShaderNodeTexVoronoi")                            # the pale specks seen in the photo
vor.inputs["Scale"].default_value = 450.0
speck = nt.nodes.new("ShaderNodeMath")
speck.operation = "LESS_THAN"
speck.inputs[1].default_value = 0.07
mix = nt.nodes.new("ShaderNodeMix")
mix.data_type = "RGBA"
grain = nt.nodes.new("ShaderNodeTexNoise")
grain.inputs["Scale"].default_value = 600.0
grain.inputs["Detail"].default_value = 2.0
wear = nt.nodes.new("ShaderNodeTexNoise")
wear.inputs["Scale"].default_value = 40.0
add = nt.nodes.new("ShaderNodeMath")
add.operation = "MULTIPLY_ADD"
add.inputs[1].default_value = 0.3
bump = nt.nodes.new("ShaderNodeBump")
bump.inputs["Strength"].default_value = 0.3
bump.inputs["Distance"].default_value = 0.0008
scale_speck = nt.nodes.new("ShaderNodeMath")
scale_speck.operation = "MULTIPLY"
scale_speck.inputs[1].default_value = 0.5
L = nt.links
L.new(tc.outputs["Object"], noise.inputs["Vector"])
L.new(tc.outputs["Object"], vor.inputs["Vector"])
L.new(tc.outputs["Object"], grain.inputs["Vector"])
L.new(tc.outputs["Object"], wear.inputs["Vector"])
L.new(noise.outputs["Fac"], ramp.inputs["Fac"])
L.new(vor.outputs["Distance"], speck.inputs[0])
L.new(speck.outputs["Value"], scale_speck.inputs[0])
L.new(scale_speck.outputs["Value"], sock(mix, "Factor_Float"))
L.new(ramp.outputs["Color"], sock(mix, "A_Color"))
sock(mix, "B_Color").default_value = tuple(min(1.0, c * 1.6) for c in ALBEDO) + (1.0,)
L.new(sock(mix, "Result_Color", out=True), bsdf.inputs["Base Color"])
L.new(wear.outputs["Fac"], add.inputs[0])
L.new(grain.outputs["Fac"], add.inputs[2])
L.new(add.outputs["Value"], bump.inputs["Height"])
L.new(bump.outputs["Normal"], bsdf.inputs["Normal"])                  # (C-007's bump from a blurred outline is gone:
bsdf.inputs["Roughness"].default_value = 0.9                           #  the relief below is geometry)
# C-011, --normal-map: the model's normals also shade the front, as an object-space normal map. Integrated into heights
# they lost most of the carving (the solve smooths it, and the skin's edge fade takes all the relief off a bar under
# ~12 px wide); used as normals they keep it, and the heights still give the forms their shadows. Marigold's frame (x
# right, y up, z towards the viewer) is the screen's own: it stands facing the camera. A point's object position gives
# its pixel in the photo; the map is used only where the surface faces the camera (the openings' inner walls keep their
# own normals).
# C-011, --photo-detail A: the weathering, from the photo itself. Marigold's normals are flat on the frame (their y part
# varies 0.07 there against 0.28 in the carved field) and the user saw it "VERY smooth" against the photo's scratches
# and uneven indentations. So each normal is tilted towards the light from above by A x the photo's own light and dark:
# its fine band (luminance less its blur over 5 px) on all stone, at CARVED_SHARE of A where the normals are not flat;
# its forms band (blur over 5 less over 21 px) only where they are flat, so the carving's shading is not counted twice. A bump from the same light and dark,
# tried first (dark as low), put each scratch's light and dark half a feature off the photo's: a bump's shading
# follows its slope, not its height (the fine band's correlation went to -0.20).
if NORMAL_MAP:
    NM = np.load(os.path.join(OUT, "normals.npy"))
    if PHOTO_DETAIL:
        yph = k["y"].astype(np.float32)
        if USE_ALBEDO:                                                 # C-015: the pale specks are colour, not relief
            # (C-018) the photo's own pixels wherever darker than the smoothed opening: scratches and pits keep their
            # shape exactly and only bright dots are lowered; the opening alone left square plateaus (blocky crumbs)
            yph = np.minimum(yph, C.blur(C.grey_open(yph, 2), 5)) if TILT_MIN else C.grey_open(yph, 2)
        b5, b21 = C.blur(yph, 5), C.blur(yph, 21)
        var = sum(C.blur(NM[:, :, c] ** 2, 9) - C.blur(NM[:, :, c], 9) ** 2 for c in (0, 1))
        flatw = C.blur(np.clip(1 - np.sqrt(np.maximum(var, 0)) / 0.08, 0, 1).astype(np.float32), 9)
        # On the carving, where the normals already carry the forms, the fine band is used at CARVED_SHARE: at full
        # strength there the photo's pale specks became bumps and the carving read as crusted (C-011, strength 8).
        # The forms band at MID_W: at full weight the photo's larger specks (too big for the opening) made soft lit
        # bumps on the frame, the user's "bluriness" (the frame's top band had 1.85 times the photo's mid-scale texture)
        detail = ((yph - b5) * (CARVED_SHARE + (1 - CARVED_SHARE) * flatw) + MID_W * (b5 - b21) * flatw) * k["stone"]
        NM = NM.copy()
        # C-023, fix 15: the tilt's strength, 8 per unit, was set on ours, whose detail has a spread of 0.0171 on the
        # stone. 03's has 0.0793 (05 0.0565, 15 0.0515): the normals were tilted past where the shading saturates, and
        # the saturated tilts read as hard-edged square patches across 03's pale wall (built with 1.7: the patches
        # gone, SSIM 0.541 to 0.547, lines near the photo's 0.450 to 0.618, the forms band's amplitude 1.25 to 0.93).
        # First form: the tilt scaled so the detail's spread is at most 0.018. It cost 09 (a black-and-white photo,
        # spread 0.0811, scaled to 0.22): SSIM 0.563 to 0.553, fine detail's correlation 0.31 to 0.15. Measured
        # (scratch probe_tilt.py), 8 x the detail on the stone: ours median 0.055, 0.03 % over 1, at most 2.4; 03
        # median 0.24, 8.7 % over 1; 09 median 0.02, 15 % over 1. On 03 most of the stone is tilted hard, which is
        # the squares; on 09 most is flat and the strong tilts are its bars' edges, the detail itself. So the tilt
        # is scaled so its median is at most 0.06 (ours 0.055 keeps 8; 03 about 2.0). --fixed-detail: unscaled.
        _dmed = PHOTO_DETAIL * float(np.median(np.abs(detail[k["stone"]]))) if k["stone"].any() else 0.0
        DETAIL_SCALE = 1.0 if "--fixed-detail" in argv or _dmed <= 0.06 else 0.06 / _dmed
        NM[:, :, 1] += PHOTO_DETAIL * DETAIL_SCALE * detail
        NM /= np.maximum(np.linalg.norm(NM, axis=2, keepdims=True), 1e-6)
        log["photo_detail"] = dict(tilt_per_unit=PHOTO_DETAIL, **({"scaled_by": round(DETAIL_SCALE, 4)} if DETAIL_SCALE < 1 else {}), carved_share=CARVED_SHARE, mid_weight=MID_W, flat_share_of_stone=round(float((flatw[k["stone"]] > 0.5).mean()), 4),
                                   detail_std=round(float(detail[k["stone"]].std()), 4))
    # C-023, fix 24 (the user: "there is some shine on the originals, that our renders do not capture"). In the photo
    # the stone along a hole is about as bright whichever side the hole is on, and each bar brighter along its crest:
    # rounded bars. Marigold's normals round ours's bars (at stone 1 to 2 px from a hole, their part towards the hole
    # is 0.33 above, 0.25 below, 0.19 left, 0.25 right), but not 03's or 05's, whose bars are 4 to 10 px wide on its
    # 768 px tiles: there every edge has the same normal, (0.18, 0.13, 0.97) on 03, one tilt for the whole lattice,
    # and the relief (2 px in, blended over 40 px) is set for wide bars and gives these none. With --round-bars, where
    # the map's part towards the nearest hole at 1 to 2 px from it is under ROUND_MIN, each bar's normals are tilted
    # towards its nearest hole, none at its crest (the largest distance from a hole within 3 px) and most at its edge,
    # scaled so that part comes to ROUND_TARGET, ours's by the same measure (0.208; 03 0.031, 05 0.023, 12 0.001).
    ROUND = {}
    if "--round-bars" in argv:
        ROUND_MIN, ROUND_TARGET = 0.10, 0.21
        if "--round-target" in argv:                                 # a switch, to test the rounding's strength
            ROUND_TARGET = float(argv[argv.index("--round-target") + 1])
        st_r = k["stone"]
        dist_r = np.zeros(st_r.shape, np.float32)
        e_r = st_r.copy()
        for _ in range(12):                                            # distance from a hole, 4-neighbour, to 12 px
            dist_r += e_r
            e_r = C.erode(e_r, 1)
        gy_r, gx_r = np.gradient(C.blur(dist_r, 3))
        g_r = np.sqrt(gx_r ** 2 + gy_r ** 2) + 1e-6
        tx_r, ty_r = -gx_r / g_r, gy_r / g_r                           # towards the hole, Marigold's frame (y up)
        _fbr = _rp.get("field_box", [x0, y0, x1, y1])
        in_f = np.zeros(st_r.shape, bool)
        in_f[_fbr[1]:_fbr[3] + 1, _fbr[0]:_fbr[2] + 1] = True
        edge_r = st_r & in_f & (dist_r <= 2) & (g_r > 0.05)
        curv0 = float(np.median(NM[:, :, 0][edge_r] * tx_r[edge_r] + NM[:, :, 1][edge_r] * ty_r[edge_r])) if edge_r.any() else 1.0
        ROUND = dict(towards_hole_before=round(curv0, 4))
        if curv0 < ROUND_MIN:
            crest = dist_r.copy()
            pad = np.pad(dist_r, 3, mode="edge")
            for dy in range(7):
                for dx in range(7):
                    crest = np.maximum(crest, pad[dy:dy + st_r.shape[0], dx:dx + st_r.shape[1]])
            xr = np.clip((crest - dist_r + 0.5) / np.maximum(crest, 1.0), 0.0, 1.0) * st_r
            med_x = float(np.median(xr[edge_r])) if edge_r.any() else 1.0
            tilt = (ROUND_TARGET - curv0) / max(med_x, 0.1)
            NM = NM.copy()
            NM[:, :, 0] += tilt * xr * tx_r
            NM[:, :, 1] += tilt * xr * ty_r
            NM /= np.maximum(np.linalg.norm(NM, axis=2, keepdims=True), 1e-6)
            curv1 = float(np.median(NM[:, :, 0][edge_r] * tx_r[edge_r] + NM[:, :, 1][edge_r] * ty_r[edge_r]))
            ROUND.update(edge_tilt=round(tilt, 4), towards_hole_after=round(curv1, 4))
        log["round_bars"] = ROUND
        print("ROUND", ROUND, flush=True)
    nimg = bpy.data.images.new("marigold normals", W, H, alpha=False, float_buffer=True)
    nimg.colorspace_settings.name = "Non-Color"
    px = np.ones((H, W, 4), np.float32)
    px[:, :, :3] = NM * 0.5 + 0.5
    nimg.pixels.foreach_set(np.flipud(px).ravel())                     # Blender's rows start at the bottom
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = nimg
    tex.interpolation = "Linear"
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1 / (S * W), 1 / (S * H), 1.0)
    mp.inputs["Location"].default_value = ((cx + 0.5) / W, 1 - (cy + 0.5) / H, 0.0)
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    L.new(mp.outputs["Vector"], tex.inputs["Vector"])
    nmap = nt.nodes.new("ShaderNodeNormalMap")
    nmap.space = "OBJECT"
    L.new(tex.outputs["Color"], nmap.inputs["Color"])
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    L.new(geo.outputs["Normal"], sep.inputs["Vector"])
    facing = nt.nodes.new("ShaderNodeMapRange")                       # world -Y is towards the camera
    facing.inputs["From Min"].default_value, facing.inputs["From Max"].default_value = -0.95, -0.8
    facing.inputs["To Min"].default_value, facing.inputs["To Max"].default_value = 1.0, 0.0
    L.new(sep.outputs["Y"], facing.inputs["Value"])
    nmix = nt.nodes.new("ShaderNodeMix")
    nmix.data_type = "VECTOR"
    L.new(facing.outputs["Result"], sock(nmix, "Factor_Float"))
    L.new(geo.outputs["Normal"], sock(nmix, "A_Vector"))
    L.new(nmap.outputs["Normal"], sock(nmix, "B_Vector"))
    unit = nt.nodes.new("ShaderNodeVectorMath")
    unit.operation = "NORMALIZE"
    L.new(sock(nmix, "Result_Vector", out=True), unit.inputs[0])
    L.new(unit.outputs["Vector"], bump.inputs["Normal"])
    # C-015: the stone's colour from the photo's albedo (intrinsics.py: Marigold's intrinsic decomposition), linear,
    # scaled channel by channel so its median over the stone is the albedo used so far (the light's power and the tone
    # curve keep their level); projected like the normal map where the surface faces the camera, the procedural colour
    # elsewhere (a front projection smears on faces that turn away).
    if USE_ALBEDO:
        AL = np.load(ALBEDO_NPY).astype(np.float64)
        # Only the albedo's slow change (stains, discolour) is kept: at the fine scale the model draws soft round
        # blobs 8 to 15 px across, which on the plain frame read as the user's "bluriness". A 9 px blur, tried first,
        # was smaller than the blobs and changed nothing (the frame's fine-to-mid texture 0.421 to 0.429).
        # C-023, fix 18 (the user, on 03 and 05's lattice: "the color is a bit darkened than expected"). The model reads
        # a thin bar together with the dark holes beside it: 03's raw albedo on the stone of its lower-left lattice is
        # 0.114 against 0.224 over all its stone, rising to 0.153, 0.177, 0.194 on the stone 1, 2, 3 px from a hole,
        # while the photo shows the same stone as bright as the wall (linear 0.63 to 0.66 on those cores, 0.67 over all);
        # the render's lattice came out at half the wall's brightness, the albedo's ratio (05: 0.096 and 0.265). So where
        # the albedo on the stone's edges is darker than on its cores (2 px in) by more than a tenth, its slow change is
        # taken from the cores alone (where cores are under 2 % of the blur's window, from all the stone, as before).
        # Ours: 0.98, unchanged; dark: 03 0.86, 05 0.78, 07 0.69, 12 0.77, 16 0.87, 17 0.80. Backlit screens' edges are
        # brighter (08 1.58, 14 2.01), the glow; left as they are. --albedo-edges: all the stone always.
        _lw = np.array([0.2126, 0.7152, 0.0722])
        _core = C.erode(k["stone"], 2)
        _bx = np.zeros(k["stone"].shape, bool)
        _bx[y0:y1 + 1, x0:x1 + 1] = True
        _al_l = AL @ _lw
        _edge_core = (float(np.median(_al_l[k["stone"] & _bx]) / max(float(np.median(_al_l[_core & _bx])), 1e-6))
                      if (_core & _bx).sum() > 100 else 1.0)
        ALBEDO_LEAK = _edge_core < 1 / 1.1 and "--albedo-edges" not in argv
        if ALBEDO_BLUR:                                                # within the stone only: across the openings
            sm = k["stone"].astype(np.float32)                         # the wall's pale grey leaked into the stone
            den = np.maximum(C.blur(sm, ALBEDO_BLUR), 1e-3)            # (the openings' IoU fell from 0.809 to 0.778)
            slow = [C.blur(AL[:, :, c].astype(np.float32) * sm, ALBEDO_BLUR) / den for c in range(3)]
            if ALBEDO_LEAK:
                cm = _core.astype(np.float32)
                den_c = C.blur(cm, ALBEDO_BLUR)
                a = np.clip(den_c / 0.02, 0.0, 1.0)
                slow = [a * C.blur(AL[:, :, c].astype(np.float32) * cm, ALBEDO_BLUR) / np.maximum(den_c, 1e-6) + (1 - a) * slow[c]
                        for c in range(3)]
            AL = np.stack([np.where(k["stone"], slow[c], AL[:, :, c]) for c in range(3)], -1).astype(np.float64)
        st_box = np.zeros(k["stone"].shape, bool)
        st_box[y0:y1 + 1, x0:x1 + 1] = k["stone"][y0:y1 + 1, x0:x1 + 1]
        med = np.median(AL[st_box], axis=0)
        AL = AL * (np.array(ALBEDO) / np.maximum(med, 1e-4))
        # The photo's pale specks (mineral grains) are colour: the model left them out of its albedo, and the first
        # build with it read as clean clay. Each bright dot narrower than about 2 px (the photo's luminance over its
        # 3 x 3 grey opening) brightens the albedo by its own contrast, decoded to linear; wider bright features (lit
        # rims) are left to the shading.
        # C-023, fix 19 (the user: "on the top left corners, the areas look a bit grainy"). Against dark holes every bar
        # narrower than the 3 x 3 square is such a dot: in 05's lower-left corner 87 % of the stone was brightened (69 %
        # by the most, 2.8 times), the wider parts of the same tracery not at all (03: 66 % and 32 %). Where the
        # albedo's edges leak (fix 18), the holes are first filled with the stone's level around them (a 5 px blur over
        # the stone), so only a dot paler than the stone around it counts. --speck-holes: as before.
        y_sp = k["y"]
        if ALBEDO_LEAK and "--speck-holes" not in argv:
            _sm = k["stone"].astype(np.float32)
            _d5 = C.blur(_sm, 5)
            y_sp = np.where(k["stone"], k["y"], np.where(_d5 > 0.05, C.blur(k["y"].astype(np.float32) * _sm, 5)
                                                         / np.maximum(_d5, 1e-3), k["y"]))
        y_open = C.grey_open(y_sp, 1)
        speck = np.clip(k["y"] / np.maximum(y_open, 0.03) - SPECK_FLOOR, 1.0, SPECK_MAX) ** 2.2   # at 2.5 some went white, and the
                                                                       # render's rule took them for wall (IoU 0.795)
        AL = np.clip(AL * np.where(st_box, speck, 1.0)[:, :, None], 0.0, 1.0)
        # C-023, fix 30: the shadow lines kept solid (common.keep_field) are deep recesses under cornices and
        # mouldings, which the relief does not cast: lit, 05's came out at 0.148 where the photo's are 0.008. Their
        # albedo is the photo's darkness there: the stone's albedo times their linear luminance over the lit stone's.
        if THIN_SOLID and k["thin_surround"].any() and "--thin-surround-lit" not in argv:
            _yl = np.where(k["y"] <= 0.04045, k["y"] / 12.92, ((k["y"] + 0.055) / 1.055) ** 2.4)
            _ts = k["thin_surround"]
            AL[_ts] = np.clip(np.array(ALBEDO)[None, :] * (_yl[_ts] / max(float(np.median(_yl[st_box])), 1e-4))[:, None], 0.0, 1.0)
        aimg = bpy.data.images.new("photo albedo", W, H, alpha=False, float_buffer=True)
        aimg.colorspace_settings.name = "Non-Color"                    # linear values, as the model gives them
        apx = np.ones((H, W, 4), np.float32)
        apx[:, :, :3] = AL
        aimg.pixels.foreach_set(np.flipud(apx).ravel())
        atex = nt.nodes.new("ShaderNodeTexImage")
        atex.image = aimg
        atex.interpolation = "Linear"
        L.new(mp.outputs["Vector"], atex.inputs["Vector"])
        amix = nt.nodes.new("ShaderNodeMix")
        amix.data_type = "RGBA"
        L.new(facing.outputs["Result"], sock(amix, "Factor_Float"))
        L.new(sock(mix, "Result_Color", out=True), sock(amix, "A_Color"))
        L.new(atex.outputs["Color"], sock(amix, "B_Color"))
        L.new(sock(amix, "Result_Color", out=True), bsdf.inputs["Base Color"])
        log["albedo"] = dict(blur_px=ALBEDO_BLUR, speck_max=SPECK_MAX, speck_floor=SPECK_FLOOR,
                             **(dict(edge_over_core=round(_edge_core, 3), cores_only=True,
                                     speck_share=round(float((speck[st_box] > 1.2).mean()), 4)) if ALBEDO_LEAK else {}), map_median_linear=[round(float(v), 4) for v in med], scaled_to=[round(float(v), 4) for v in ALBEDO],
                             map_p10_p90_luminance=[round(float(np.percentile(AL[st_box] @ np.array([0.2126, 0.7152, 0.0722]), q)), 4)
                                                    for q in (10, 90)])
# C-017: a colour multiplied into the base colour, to divide out the spot's colour (white until the spot's colour is
# fitted below), so the lit stone keeps the photo's median colour whatever the light's temperature.
base_link = next(l for l in nt.links if l.to_socket == bsdf.inputs["Base Color"])
base_src = base_link.from_socket
nt.links.remove(base_link)
comp = nt.nodes.new("ShaderNodeRGB")
comp.label = "light colour compensation"
comp.outputs[0].default_value = (1.0, 1.0, 1.0, 1.0)
cmul = nt.nodes.new("ShaderNodeMix")
cmul.data_type, cmul.blend_type = "RGBA", "MULTIPLY"
sock(cmul, "Factor_Float").default_value = 1.0
L.new(base_src, sock(cmul, "A_Color"))
L.new(comp.outputs[0], sock(cmul, "B_Color"))
L.new(sock(cmul, "Result_Color", out=True), bsdf.inputs["Base Color"])
screen.data.materials.append(mat)

# The carved front: a grid at the photo's pixel spacing over the stone, lifted by the relief, 0.1 mm proud of the
# curve's front face so the two never fight. Its edge stays a pixel inside the outline, where the height is 0.
quad = skin[:-1, :-1] & skin[:-1, 1:] & skin[1:, 1:] & skin[1:, :-1]
qy, qx = np.nonzero(quad)
used = np.zeros((H, W), bool)
used[qy, qx] = used[qy, qx + 1] = used[qy + 1, qx + 1] = used[qy + 1, qx] = True
vy, vx = np.nonzero(used)
idx = np.full((H, W), -1, np.int64)
idx[vy, vx] = np.arange(len(vy))
co = np.stack([(vx - cx) * S, (cy - vy) * S, THICK_M / 2 + 0.0001 + height[vy, vx]], 1).astype(np.float32)
quads = np.stack([idx[qy, qx], idx[qy + 1, qx], idx[qy + 1, qx + 1], idx[qy, qx + 1]], 1).astype(np.int32)
me_s = bpy.data.meshes.new("carved front")
me_s.vertices.add(len(co))
me_s.attributes["position"].data.foreach_set("vector", co.ravel())
me_s.loops.add(len(quads) * 4)
me_s.attributes[".corner_vert"].data.foreach_set("value", quads.ravel())
me_s.polygons.add(len(quads))
me_s.polygons.foreach_set("loop_start", np.arange(0, len(quads) * 4, 4, dtype=np.int32))
me_s.update(calc_edges=True)
me_s.shade_smooth()
me_s.materials.append(mat)
front = bpy.data.objects.new("carved front", me_s)
front.rotation_euler = screen.rotation_euler
scene.collection.objects.link(front)
log["relief"] = dict(forms=FORMS, normal_map=NORMAL_MAP, bars_m=RELIEF_M, reach_px=RELIEF_PX, forms_m_at_p99=FORMS_M, height_max_m=round(float(height.max()), 5),
                     vertices=len(co), faces=len(quads))
log["symmetry"] = SYM

# The wall: a panel 0.4 m behind the screen, as in the photo, where the surround is dark and the wall shows only
# through the openings. Seen from the camera it covers 95 % of the screen's box: past the carved field, so every opening
# looks onto it, and inside the frame's back edge (95.5 %), so it stays hidden. (Sized to the box itself, it covered
# only 75 % from the camera, and the top and bottom openings looked past it into black.)
bw, bh = (x1 - x0 + 1) * S, (y1 - y0 + 1) * S
bx, bz = ((x0 + x1) / 2 - cx) * S, (cy - (y0 + y1) / 2) * S
KW = DIST / (DIST + THICK_M / 2 + 0.40)
bpy.ops.mesh.primitive_plane_add(size=1.0, location=(bx / KW, 0.40, bz / KW), rotation=(math.radians(90), 0, 0))
wall = bpy.context.object
wall.name = "wall"
wall.scale = (bw * 0.95 / KW, bh * 0.95 / KW, 1.0)
log["wall"] = dict(panel_seen_from_camera_at=round(KW, 4), panel_covers_box=0.95)
# The wall glows, like the museum's lit backdrop. It is seen straight through the openings and only emits, so the
# colour shown is its emission through the sRGB curve: it is set, not fitted. In ten bands from the screen's top to its
# bottom, the photo's openings' median colour, decoded to linear, goes into a colour ramp at the height on the panel
# that those rows look onto (the panel is KW times further away, so a row's height on it is its height on the screen
# over KW). C-007's two-number fit kept dimming the panel's top, chasing the upper half's median.
def to_lin3(c):
    c = np.asarray(c, np.float64)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


# C-013: the photo's tone curve. On luminance, through 0, 1 and the pivot m (the photo's stone median, so the power fit
# stands): a power curve below m and a mirrored one above it, exponents a and b (1 and 1 is no curve). The render
# goes through it; the wall, seen straight through the openings, is set through its inverse, so it still shows the
# photo's colour.
def tone(v, m, a, b):
    v = np.clip(np.asarray(v, np.float64), 0.0, 1.0)
    lo = m * (np.maximum(v, 1e-6) / m) ** a
    hi = 1 - (1 - m) * (np.maximum(1 - v, 1e-6) / (1 - m)) ** b
    return np.where(v <= m, lo, hi)


def tone_inv(v, m, a, b):
    return tone(v, m, 1.0 / a, 1.0 / b)


# Applied to luminance, R, G and B scaled together: per channel, a colour that straddles the pivot changes hue (a dim
# grey wall turned warmer, failed the green-over-red cut, and the openings' IoU fell from 0.795 to 0.758).
LUM = np.array([0.2126, 0.7152, 0.0722])


def tone_rgb(rgb_, cv, inverse=False):
    rgb_ = np.asarray(rgb_, np.float64)
    yy = np.maximum(rgb_ @ LUM, 1e-6)
    f = tone_inv if inverse else tone
    return np.clip(rgb_ * (f(yy, cv["m"], cv["a"], cv["b"]) / yy)[..., None], 0.0, 1.0)


TONE_M = float(np.median(k["y"][y0:y1 + 1, x0:x1 + 1][k["stone"][y0:y1 + 1, x0:x1 + 1]]))
curve = dict(m=TONE_M, a=1.0, b=1.0)
band_rows = np.array_split(np.arange(y0, y1 + 1), 10)
ph, z_bottom = bh * 0.95 / KW, bz / KW - bh * 0.95 / KW / 2


def wall_bands(cv):
    out = []
    for rr in band_rows:
        o = k["opening"][rr[0]:rr[-1] + 1, x0:x1 + 1]
        if o.sum() < 200:
            continue
        shown = np.median(rgb[rr[0]:rr[-1] + 1, x0:x1 + 1][o], axis=0)
        lin = to_lin3(tone_rgb(shown, cv, inverse=True))
        z = (cy - (rr[0] + rr[-1]) / 2) * S / KW
        out.append(((z - z_bottom) / ph, lin))
    return sorted(out, key=lambda b: b[0])


bands = wall_bands(curve)
WALL_MAX = float(max(b[1].max() for b in bands))
wm = bpy.data.materials.new("lit wall")
wm.use_nodes = True
wn = wm.node_tree
for n in list(wn.nodes):
    if n.type != "OUTPUT_MATERIAL":
        wn.nodes.remove(n)
em = wn.nodes.new("ShaderNodeEmission")
em.inputs["Strength"].default_value = WALL_MAX
wtc = wn.nodes.new("ShaderNodeTexCoord")
sep = wn.nodes.new("ShaderNodeSeparateXYZ")
ramp_w = wn.nodes.new("ShaderNodeValToRGB")                            # Generated y: 0 at the panel's bottom, 1 at top
els = ramp_w.color_ramp.elements
while len(els) < len(bands):
    els.new(0.5)
def set_wall(bs):
    global WALL_MAX
    WALL_MAX = float(max(b[1].max() for b in bs))
    em.inputs["Strength"].default_value = WALL_MAX
    for el, (pos, lin) in zip(els, bs):
        el.position = float(min(max(pos, 0.0), 1.0))
        el.color = tuple(float(c) / WALL_MAX for c in lin) + (1.0,)


set_wall(bands)
# C-023: --wall photo. Ten flat bands cannot draw what some screens look onto: 14's arcade of dark arches (its bands go
# from 0.92 to 0.047 within a tenth of the screen's height, a level change in the middle of a panel), 17's and 18's lit
# courtyard, the green, blue and yellow light through 04's tree. So the wall's colour can be the photo itself, seen
# from the camera (window coordinates: the render's frame is the photo's): where the photo shows an opening, its colour,
# through the tone curve's inverse as the bands are; across the stone, those colours filled in (normalised
# convolution, at a quarter of the size, widening until every pixel has some), since the stone hides it but for the
# openings' edges. Each tone round sets it again, as it sets the bands. The bands stay the default (ours is a lit wall).
WALL_PHOTO = "--wall" in argv and argv[argv.index("--wall") + 1] == "photo"


def filled_openings():
    q = (max(W // 4, 1), max(H // 4, 1))
    have = C.resize(k["opening"].astype(np.float32), q) > 0.5
    img = np.stack([C.resize(rgb[:, :, c].astype(np.float32), q) for c in range(3)], -1)
    out = np.where(have[..., None], img, 0.0)
    for width in (3, 7, 15, 31, 63):
        if have.all():
            break
        wsum = C.blur(have.astype(np.float32), width)
        est = np.stack([C.blur((img[:, :, c] * have).astype(np.float32), width) for c in range(3)], -1) / np.maximum(wsum, 1e-4)[..., None]
        new = ~have & (wsum > 0.02)
        out[new] = est[new]
        have = have | new
    if not have.all():
        out[~have] = np.median(rgb[k["opening"]], axis=0) if k["opening"].any() else 0.5
    full = np.stack([C.resize(out[:, :, c].astype(np.float32), (W, H)) for c in range(3)], -1)
    return np.where(k["opening"][..., None], rgb, full)


if WALL_PHOTO:
    WALL_SHOWN = filled_openings()                                     # the photo's display values, all over
    wall_img = bpy.data.images.new("wall photo", W, H, float_buffer=True)
    wall_tex = wn.nodes.new("ShaderNodeTexImage")
    wall_tex.image = wall_img
    wall_tex.interpolation = "Linear"
    wall_tco = wn.nodes.new("ShaderNodeTexCoord")
    wn.links.new(wall_tco.outputs["Window"], wall_tex.inputs["Vector"])

    def set_wall_photo(cv):
        global WALL_MAX
        lin = to_lin3(tone_rgb(WALL_SHOWN, cv, inverse=True))
        WALL_MAX = float(max(lin.max(), 1e-4))
        em.inputs["Strength"].default_value = WALL_MAX
        px = np.concatenate([lin / WALL_MAX, np.ones(lin.shape[:2] + (1,))], -1)[::-1].astype(np.float32)
        wall_img.pixels.foreach_set(px.ravel())
        wall_img.update()

    set_wall_photo(curve)
wn.links.new(wtc.outputs["Generated"], sep.inputs["Vector"])
wn.links.new(sep.outputs["Y"], ramp_w.inputs["Fac"])
wn.links.new((wall_tex if WALL_PHOTO else ramp_w).outputs["Color"], em.inputs["Color"])
if WALL_PHOTO:
    log["wall"]["photo"] = dict(source="the photo's openings, filled in across the stone; window coordinates")
log["wall"]["bands"] = [dict(at=round(pos, 4), linear_rgb=[round(float(c), 4) for c in lin]) for pos, lin in bands]
wn.links.new(em.outputs["Emission"], next(n for n in wn.nodes if n.type == "OUTPUT_MATERIAL").inputs["Surface"])
wall.data.materials.append(wm)

spot = bpy.data.lights.new("spot", "SPOT")
spot.energy = 400.0
spot.spot_size = math.radians(45)
spot.spot_blend = 0.6
spot.shadow_soft_size = 0.02                                           # crisp shadows under the carving
so = bpy.data.objects.new("spot", spot)
scene.collection.objects.link(so)
SPOT_EL = math.atan2(2.0, 1.2)                                         # 59 degrees up, straight on: C-007's choice,
                                                                       # and what the photo's shading says (C-012)
if "--spot-el" in argv:                                                # C-023: a switch, to test the light's angle
    SPOT_EL = math.radians(float(argv[argv.index("--spot-el") + 1]))


def place_spot(ax, az, d):
    """The spot d metres from the point (ax, az) on the screen, along its fixed direction, aimed at that point."""
    aim = Vector((ax, 0.0, az))
    so.location = aim + d * Vector((0.0, -math.cos(SPOT_EL), math.sin(SPOT_EL)))
    so.rotation_euler = (aim - so.location).to_track_quat("-Z", "Y").to_euler()


place_spot(0.0, 0.0, math.hypot(1.2, 2.0))                             # C-011's spot: (0, -1.2, 2.0), at the centre

world = bpy.data.worlds.new("dark")
world.use_nodes = True
next(n for n in world.node_tree.nodes if n.type == "BACKGROUND").inputs["Color"].default_value = (0.003, 0.003, 0.003, 1.0)
scene.world = world

cam = bpy.data.cameras.new("photo camera")
cam.lens, cam.sensor_width, cam.sensor_fit = LENS_MM, SENSOR_MM, "HORIZONTAL"
frame_w = W * S
dist = LENS_MM / SENSOR_MM * frame_w
co = bpy.data.objects.new("photo camera", cam)
co.location = (0, -THICK_M / 2 - dist, 0)
co.rotation_euler = (math.radians(90), 0, 0)
scene.collection.objects.link(co)
scene.camera = co
log["camera"] = dict(lens_mm=LENS_MM, sensor_mm=round(SENSOR_MM, 3), distance_m=round(dist, 4),
                     frame_width_m=round(frame_w, 4))

r = scene.render
r.engine = "CYCLES"
r.resolution_x, r.resolution_y = W, H
r.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "Standard"
r.filter_size = FILTER_PX                                              # does nothing in Cycles (C-009: identical at 1.5,
scene.cycles.filter_width = FILTER_PX                                  # 2.5, 3.5); Cycles reads its own filter_width
scene.view_settings.look = LOOK                                         # the photo was edited (Polarr): --look tries a curve
cyc = scene.cycles
prefs = bpy.context.preferences.addons["cycles"].preferences
for kind in ("METAL", "OPTIX", "CUDA", "HIP", "ONEAPI"):
    try:
        prefs.compute_device_type = kind
    except TypeError:
        continue
    prefs.get_devices()
    if any(d.type == kind for d in prefs.devices):
        for d in prefs.devices:
            d.use = d.type == kind
        cyc.device = "GPU"
        break
cyc.use_denoising = "--no-denoise" not in argv                   # C-023: off, to test what it costs fine detail

depsgraph = bpy.context.evaluated_depsgraph_get()
ev = screen.evaluated_get(depsgraph)
me = ev.to_mesh()
log["mesh"] = dict(vertices=len(me.vertices), faces=len(me.polygons), front_face_m2=round(front_m2, 4),
                   front_face_m2_if_built_in_metres=round(front_in_metres_m2, 4), metres_per_curve_unit=round(S, 6),
                   outlines_enclose_m2=round(expected, 4))
ev.to_mesh_clear()
print("MESH", log["mesh"], "CAMERA", log["camera"], flush=True)


def render(path, pct, samples):
    r.resolution_percentage = pct
    cyc.samples = samples
    r.filepath = path
    t = time.time()
    bpy.ops.render.render(write_still=True)
    return time.time() - t


BOX = (slice(y0, y1 + 1), slice(x0, x1 + 1))


MID = (y0 + y1) // 2
FIT_STONE_MIN = 0.5                                                    # C-022: see medians()
STONE_PH_BOX = int(stone_ph[BOX].sum())
STONE_FIT = C.erode(stone_ph, 2)
FIT_READ = {}                                                          # set by medians() when it falls back


def medians(img_rgb, wall_by_colour=False):
    """The stone's median luminance inside the screen's box, and the openings' in its lower and upper halves. In a
    render the wall is found by colour alone (wall_by_colour), so a dim wall still counts and the fit cannot chase it
    to black."""
    q = C.classify(img_rgb)
    if wall_by_colour and C.SIDE != "dark" and C.RULE == "colour":     # C-023: nor is grey stone
        q["opening"] = q["gr"] > C.GREEN_RED
        q["stone"] = ~q["opening"] & ~q["outside"]
        # C-022: a grey or white stone passes green over red as wall, so the fit saw almost none of it (4 % of the
        # photo's stone in 03, none in 09 and 15) and set the power from what was left, or from a nan. Under half the
        # photo's stone, the render is measured where the photo's stone is: the two share one camera and one outline.
        # Ours stays on its own reading (102 to 106 % of the photo's stone in every fit render).
        if q["stone"][BOX].sum() < FIT_STONE_MIN * STONE_PH_BOX:
            q["stone"], q["opening"] = STONE_FIT.copy(), k["opening"].copy()
            FIT_READ["stone_from_photo"] = True
    # C-023, fix 23: read by brightness, a render's stone and openings are split at a threshold found again on each
    # render, and over a range of powers the split jumps: 18's fit renders read 0.0738, 0.0671, 0.0705 at 564, 920,
    # 1,706 W, then at 2,962 W 0.3405 in one build and 0.1234 in the next, the same scene, so one build settled at 27.8 W
    # (SSIM 0.798) and the next at 2,166 W (0.467, its stone 0.249 against the photo's 0.103). So under the brightness
    # rules a render is measured where the photo's stone and openings are (one camera, one outline), at every power the
    # same pixels. Ours is read by colour and stays on its own reading. --fit-own-reading: as before.
    elif wall_by_colour and C.RULE == "brightness" and "--fit-own-reading" not in argv:
        q["stone"], q["opening"] = STONE_FIT.copy(), k["opening"].copy()
        FIT_READ["stone_from_photo"] = True
    st = q["stone"][BOX]
    lo = q["opening"][MID:y1 + 1, x0:x1 + 1]
    hi = q["opening"][y0:MID, x0:x1 + 1]
    return (float(np.median(q["y"][BOX][st])),
            float(np.median(q["y"][MID:y1 + 1, x0:x1 + 1][lo])) if lo.any() else 0.0,
            float(np.median(q["y"][y0:MID, x0:x1 + 1][hi])) if hi.any() else 0.0)


def to_lin(v):
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


# --- C-012: fit where the spot pools ----------------------------------------------------------------------------
# The light map (compare.py): the stone's median in 6 x 7 cells over the box, each over the median cell, on the photo's
# stone (3 px from any opening), at the size the candidates are rendered. The error is the RMS of log(render / photo).
FIT_PCT = 25
fw, fh = W * FIT_PCT // 100, H * FIT_PCT // 100
fit_mask = C.resize(C.erode(k["stone"], 3).astype(np.float32), (fw, fh)) > 0.9
fit_y_photo = C.resize(k["y"].astype(np.float32), (fw, fh))
fbx = [round(v * FIT_PCT / 100) for v in (x0, y0, x1, y1)]


def light_map(yy):
    xs = np.linspace(fbx[0], fbx[2] + 1, 7).astype(int)
    ys = np.linspace(fbx[1], fbx[3] + 1, 8).astype(int)
    out = np.full((7, 6), np.nan)
    for j in range(7):
        for i in range(6):
            mm = fit_mask[ys[j]:ys[j + 1], xs[i]:xs[i + 1]]
            if mm.sum() > 5:
                out[j, i] = np.median(yy[ys[j]:ys[j + 1], xs[i]:xs[i + 1]][mm])
    return out / np.nanmedian(out)


LM_PHOTO = light_map(fit_y_photo)


def map_error(path):
    img = C.load(path)
    yy = C.luminance(img) if img.shape[:2] == (fh, fw) else C.resize(C.luminance(img), (fw, fh))
    return float(np.sqrt(np.nanmean(np.log(np.maximum(light_map(yy), 1e-3) / LM_PHOTO) ** 2)))


# The candidates are set by where the pool falls on the screen, not by the cone's angle, so distance and pool size do
# not fight: the aim (ax, az), the distance d, the pool's half-height rv on the screen (the cone's half-angle is
# atan(rv sin(el) / d), the beam meeting the upright screen 59 degrees off its face, which stretches a round pool to
# about twice as tall as wide), its width over a round pool's (sx: the spot object scaled sideways, which Blender
# allows), and the edge's softness (blend). The first search, by cone angle and without sx, got the error to 0.327
# and no further: a round pool from this direction is taller than the photo's.
def half_angle(c):
    return math.atan(c["rv"] * math.sin(SPOT_EL) / c["d"])


light = dict(ax=0.0, az=0.0, d=math.hypot(1.2, 2.0), rv=math.hypot(1.2, 2.0) * math.tan(math.radians(22.5)) / math.sin(SPOT_EL),
             sx=1.0, blend=0.6)                                        # C-011's spot: 45 degrees, round, 0.6
E0 = spot.energy / light["d"] ** 2                                     # power kept in step with distance squared


def set_light(c):
    place_spot(c["ax"], c["az"], c["d"])
    spot.spot_size, spot.spot_blend = 2 * half_angle(c), c["blend"]
    so.scale = (c["sx"], 1.0, 1.0)
    spot.energy = E0 * c["d"] ** 2


def try_light(c):
    set_light(c)
    path = os.path.join(OUT, "light_fit.png")
    render(path, FIT_PCT, 32)
    return map_error(path)


LIGHT_JSON = os.path.join(shot.RESULTS, "light_fit.json")
reuse = not FIXED_LIGHT and not REFIT_LIGHT and os.path.exists(LIGHT_JSON)
if reuse:                                                              # the search takes ~130 renders (2.5 min)
    saved = json.load(open(LIGHT_JSON))
    light = dict(saved["best"])
    log["light_fit"] = dict(reused=LIGHT_JSON.replace(shot.FOLDER + os.sep, ""), best=saved["best"],
                            error_when_fitted=saved["best_error"], error_now=round(try_light(light), 4))
    print("LIGHT reused", log["light_fit"], flush=True)
else:
    log["light_fit"] = dict(fixed=FIXED_LIGHT, start={k: round(v, 4) for k, v in light.items()},
                            start_error=round(try_light(light), 4), steps=[])
if not FIXED_LIGHT and not reuse:
    grids = [dict(rv=[0.4, 0.6, 0.8, 1.0, 1.3], sx=[1.0, 1.5, 2.0, 2.5], az=[-0.25, -0.1, 0.0, 0.1, 0.2],
                  d=[1.6, 2.33, 3.5, 5.0, 8.0], blend=[0.3, 0.6, 1.0], ax=[-0.06, 0.0, 0.06]),
             dict(rv=[0.85, 0.92, 1.08, 1.15], sx=[0.85, 0.92, 1.08, 1.15], az=[-0.08, -0.04, 0.04, 0.08],
                  d=[0.7, 0.85, 1.2, 1.4], blend=[-0.2, -0.1, 0.1], ax=[-0.03, 0.03]),
             dict(rv=[0.95, 1.05], sx=[0.95, 1.05], az=[-0.02, 0.02], d=[0.9, 1.1], blend=[-0.05, 0.05], ax=[-0.015, 0.015])]
    best_e = log["light_fit"]["start_error"]
    for rnd, grid in enumerate(grids):
        for key, vals in grid.items():
            for v in vals:
                c = dict(light)
                c[key] = v if rnd == 0 else (light[key] * v if key in ("d", "rv", "sx") else light[key] + v)
                c["blend"] = min(max(c["blend"], 0.0), 1.0)
                if c == light or math.degrees(2 * half_angle(c)) > 170:
                    continue
                e = try_light(c)
                log["light_fit"]["steps"].append(dict(round=rnd, key=key, value=round(c[key], 4), error=round(e, 4)))
                if e < best_e:
                    best_e, light = e, c
            print("LIGHT", rnd, key, {k: round(v, 3) for k, v in light.items()}, round(best_e, 4), flush=True)
    # Then all six together (Nelder-Mead from the grids' best): one at a time, the search stalls where they trade off.
    keys = ["ax", "az", "d", "rv", "sx", "blend"]
    logk = {"d", "rv", "sx"}

    def unpack(x):
        c = {k: (math.exp(v) if k in logk else v) for k, v in zip(keys, x)}
        c["blend"] = min(max(c["blend"], 0.0), 1.0)
        return c

    def f(x):
        c = unpack(x)
        if math.degrees(2 * half_angle(c)) > 170 or c["sx"] > 4 or c["sx"] < 0.25:
            return 9.0
        e = try_light(c)
        log["light_fit"]["steps"].append(dict(round="nm", **{k: round(v, 4) for k, v in c.items()}, error=round(e, 4)))
        return e

    x0n = np.array([math.log(light[k]) if k in logk else light[k] for k in keys])
    steps = np.array([0.05, 0.08, 0.3, 0.2, 0.25, 0.2])
    simplex = [x0n] + [x0n + np.eye(6)[i] * steps[i] for i in range(6)]
    fs = [best_e] + [f(x) for x in simplex[1:]]
    for _ in range(60):                                                # about 70 renders in all
        order = np.argsort(fs)
        simplex, fs = [simplex[i] for i in order], [fs[i] for i in order]
        cen = np.mean(simplex[:-1], axis=0)
        xr = cen + (cen - simplex[-1])
        fr = f(xr)
        if fr < fs[0]:
            xe = cen + 2 * (cen - simplex[-1])
            fe = f(xe)
            simplex[-1], fs[-1] = (xe, fe) if fe < fr else (xr, fr)
        elif fr < fs[-2]:
            simplex[-1], fs[-1] = xr, fr
        else:
            xc = cen + 0.5 * (simplex[-1] - cen)
            fc = f(xc)
            if fc < fs[-1]:
                simplex[-1], fs[-1] = xc, fc
            else:                                                      # shrink towards the best
                simplex = [simplex[0]] + [simplex[0] + 0.5 * (x - simplex[0]) for x in simplex[1:]]
                fs = [fs[0]] + [f(x) for x in simplex[1:]]
        if max(fs) - min(fs) < 0.003:
            break
    i = int(np.argmin(fs))
    if fs[i] < best_e:
        best_e, light = fs[i], unpack(simplex[i])
    print("LIGHT nm", {k: round(v, 3) for k, v in light.items()}, round(best_e, 4), flush=True)
    log["light_fit"].update(best={k: round(v, 4) for k, v in light.items()}, best_error=round(best_e, 4),
                            cone_deg=round(math.degrees(2 * half_angle(light)), 2), renders=len(log["light_fit"]["steps"]) + 1)
    with open(LIGHT_JSON, "w") as fjson:
        json.dump(log["light_fit"], fjson, indent=1)
set_light(light)

# --- C-017: the spot's colour -------------------------------------------------------------------------------------
# In the photo the lit faces are paler and the shadows redder (log(R/G) falls and log(B/G) rises with luminance). A
# spot cooler than the warm light bounced inside red stone does that, with the stone's colour divided by the spot's so
# the lit stone keeps its colour. The spot's colour from its temperature (Helland's fit to the blackbody, linearised,
# luminance 1); candidates rendered at FIT_PCT before the tone curve, their slopes against the photo's at that size.
def blackbody(t):
    t = t / 100.0
    r = 255.0 if t <= 66 else 329.698727446 * (t - 60) ** -0.1332047592
    g = 99.4708025861 * math.log(t) - 161.1195681661 if t <= 66 else 288.1221695283 * (t - 60) ** -0.0755148492
    b = 255.0 if t >= 66 else (0.0 if t <= 19 else 138.5177312231 * math.log(t - 10) - 305.0447927307)
    srgb = np.clip(np.array([r, g, b]) / 255.0, 0, 1)
    lin = np.where(srgb <= 0.04045, srgb / 12.92, ((srgb + 0.055) / 1.055) ** 2.4)
    return lin / float(lin @ np.array([0.2126, 0.7152, 0.0722]))


def slopes(img_rgb):
    b = np.stack([C.blur(img_rgb[:, :, c].astype(np.float32), 5) for c in range(3)], -1)
    ly = np.log(np.maximum(C.luminance(b), 1e-3))[fit_mask]
    out = []
    for i, j in ((0, 1), (2, 1)):
        c = np.log(np.maximum(b[:, :, i], 1e-3) / np.maximum(b[:, :, j], 1e-3))[fit_mask]
        out.append(float(np.polyfit(ly, c, 1)[0]))
    return out


def set_spot_colour(t):
    col = np.ones(3) if t is None else blackbody(t)
    spot.color = tuple(float(c) for c in col)
    inv = 1.0 / col
    comp.outputs[0].default_value = tuple(float(c) for c in inv / float(inv @ np.array([0.2126, 0.7152, 0.0722]))) + (1.0,)


SLOPES_PHOTO = slopes(C.resize(rgb.astype(np.float32), (fw, fh)))
log["spot_colour"] = dict(photo_slopes_at_fit_size=[round(v, 4) for v in SLOPES_PHOTO], tries=[])
best_t, best_err = None, None
if not SPOT_WHITE:
    for t in (None, 2700, 3500, 4500, 5500, 6500, 8000, 10000):
        set_spot_colour(t)
        path = os.path.join(OUT, "colour_fit.png")
        render(path, FIT_PCT, 32)
        sl = slopes(C.load(path))
        err = sum(abs(math.log(max(a / b, 1e-3))) if a * b > 0 else 5.0 for a, b in zip(sl, SLOPES_PHOTO))
        log["spot_colour"]["tries"].append(dict(kelvin=t, slopes=[round(v, 4) for v in sl], error=round(err, 4)))
        print("SPOT", t, [round(v, 4) for v in sl], round(err, 4), flush=True)
        if best_err is None or err < best_err:
            best_t, best_err = t, err
set_spot_colour(best_t)
log["spot_colour"].update(kelvin=best_t, error=None if best_err is None else round(best_err, 4),
                          spot_rgb=[round(float(c), 4) for c in spot.color])

# --- fit the spotlight's power to the photo (the wall is set above) --------------------------------------------
target = medians(rgb)
log["fit"] = dict(target_stone_y=round(target[0], 4), target_opening_y_lower=round(target[1], 4),
                  target_opening_y_upper=round(target[2], 4), steps=[])


def gain(want, got):
    return min(10.0, max(0.1, to_lin(want) / max(to_lin(got), 1e-4)))


def fit_power(n):
    for step in range(n):
        path = os.path.join(OUT, f"fit_{len(log['fit']['steps'])}.png")
        sec = render(path, 25, 32)
        img = tone_rgb(C.load(path, (W, H)), curve).astype(np.float32)
        FIT_READ.clear()
        st, op_lo, op_hi = medians(img, wall_by_colour=True)
        log["fit"]["steps"].append(dict(spot_w=round(spot.energy, 2), stone_y=round(st, 4),
                                        opening_y_lower=round(op_lo, 4), opening_y_upper=round(op_hi, 4),
                                        seconds=round(sec, 1), curve=[round(curve["a"], 4), round(curve["b"], 4)],
                                        **({"stone_from_photo": True} if FIT_READ else {})))
        print("FIT", log["fit"]["steps"][-1], flush=True)
        spot.energy *= gain(target[0], st)


fit_power(3)
# C-023, fix 26 (the user, on 03 and 05: still "a bit darker", and "there is some shine on the originals"). With the
# render on the photo's grid (fix 25), 05's lattice is darker than its wall where the photo's is not: by band, 0.62,
# 0.59, 0.59 against 0.72, 0.67, 0.64, the wall above 0.86 against 0.86; its stone's top end 0.837 at the 95th
# percentile against 0.956. Fix 18's cores still give its lattice 0.74 of its wall's albedo where the photo shows the
# stone at 0.89 of the wall's brightness, and the spot's pool and the pixel filter on thin bars add to it. So, with
# --albedo-refine, one render at half size, and the albedo's slow change is put right by the photo: over the stone's
# cores (2 px in) inside the box, in linear light, the photo over the render, both blurred as the albedo is
# (ALBEDO_BLUR), normalised to a median of 1 so only the balance between regions moves, held to 0.5 to 2; then the
# power is fitted again.
ALBEDO_REFINE = "--albedo-refine" in argv and USE_ALBEDO and NORMAL_MAP     # the albedo map is made with the normal map
if ALBEDO_REFINE:
    def _lin(v):
        v = np.asarray(v, np.float64)
        return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)
    _rpath = os.path.join(OUT, "refine.png")
    render(_rpath, 50, 32)
    _yr = _lin(C.luminance(C.load(_rpath, (W, H))))
    _yp = _lin(k["y"])
    _m = np.zeros((H, W), np.float32)
    _m[BOX] = C.erode(k["stone"], 2)[BOX]
    _den = C.blur(_m, ALBEDO_BLUR)
    _num_p = C.blur((_yp * _m).astype(np.float32), ALBEDO_BLUR)
    _num_r = C.blur((_yr * _m).astype(np.float32), ALBEDO_BLUR)
    _ok = (_den > 0.05) & (_num_r > 1e-5)
    _ratio = np.where(_ok, _num_p / np.maximum(_num_r, 1e-6), 1.0)
    _med = float(np.median(_ratio[_m > 0.5])) if (_m > 0.5).any() else 1.0
    _ratio = np.clip(_ratio / max(_med, 1e-6), 0.5, 2.0)
    _ratio = np.where(k["stone"], _ratio, 1.0)
    AL_REF = np.clip(AL * _ratio[:, :, None], 0.0, 1.0)
    apx[:, :, :3] = AL_REF
    aimg.pixels.foreach_set(np.flipud(apx).ravel())
    aimg.update()
    log["albedo_refine"] = dict(ratio_p10_p90=[round(float(np.percentile(_ratio[_m > 0.5], q)), 4) for q in (10, 90)],
                                held=round(float(((_ratio <= 0.5) | (_ratio >= 2.0))[_m > 0.5].mean()), 4))
    print("ALBEDO_REFINE", log["albedo_refine"], flush=True)
    fit_power(2)
r.image_settings.color_depth = "16"                                    # a curve on 8 bits would band
UNTONED = os.path.join(OUT, "render_untoned.png")
TONE_MASK = (C.erode(k["stone"], 3) & np.pad(np.ones((y1 - y0 + 1, x1 - x0 + 1), bool), ((y0, H - y1 - 1), (x0, W - x1 - 1))))
P10, P90 = (float(np.percentile(k["y"][TONE_MASK], q)) for q in (10, 90))


def fit_curve(path):
    """The two exponents that send the untoned render's stone 10th and 90th percentiles to the photo's."""
    u = C.luminance(C.load(path))[TONE_MASK]
    u10, u90 = float(np.percentile(u, 10)), float(np.percentile(u, 90))
    m = curve["m"]
    # C-022: a percentile at pure white or black (a sunlit stone clipping in the render, or sunlight on the floor taken
    # for stone in the photo) made a log of 0; held just inside, the exponent goes to its clamp instead of crashing
    lo, hi = 1e-3, 1 - 1e-3
    p10, p90 = min(max(P10, lo), hi), min(max(P90, lo), hi)
    u10c, u90c = min(max(u10, lo), hi), min(max(u90, lo), hi)
    a = math.log(p10 / m) / math.log(min(u10c, 0.999 * m) / m)
    b = math.log((1 - p90) / (1 - m)) / math.log((1 - min(max(u90c, 1.001 * m), hi)) / (1 - m))
    return dict(m=m, a=float(min(max(a, 0.3), 4.0)), b=float(min(max(b, 0.3), 4.0)), untoned_p10=round(u10, 4),
                untoned_p90=round(u90, 4), clipped=(u10, u90, P10, P90) != (u10c, u90c, p10, p90))


# C-023, fix 21 (the user, on 03 and 05's lattices after fixes 18 to 20: "the tone is still a bit darker than the
# original"). Before the curve the render's lattice stone matches the photo's (03: 0.689 against 0.686 next to the
# holes, 0.80 to 0.81 against 0.80 to 0.82 further in); the curve takes it to 0.484 and 0.75. Its lower exponent is
# 2.82 on 03 (2.27 on 05) because the photo's darkest tenth of stone (0.556) is far darker than the render's (0.723):
# the shadows of the wall's mouldings and the stains, which the render does not have at any scale up to 10 px (fitted
# on both smoothed, 2.59), and a percentile match cannot tell which pixel is which, so the curve darkens every mid-tone
# instead. Checked pixel by pixel on the stone the fit uses, 03's curve fits the photo worse than no curve (mean error
# 0.111 against 0.108). So, with --tone-check, each half of the curve is kept only where it brings the render's stone
# nearer the photo's, pixel by pixel, than none: below the pivot 03 0.187 against 0.175 with none, dropped; above it
# 0.079 against 0.080, kept. On ours it drops the lower half too (0.0718 against 0.0702; a 1.06 to 1.00: SSIM 0.5429 to
# 0.5427), and the user said yes to that (2026-11-27, on `c023_tonecheck.jpg`). Run on all 18 it helped where the stone
# is read by brightness, whose darkest tenth lies at the threshold that defines it (with fix 23: 05 +0.024, 09 +0.040,
# 10 +0.031, 16 +0.018, 17 +0.014 in SSIM, 03 and 08 +0.002; 12 -0.011, 15 -0.010, 13 -0.006, their stone's median
# nearer the photo's in all three), and hurt where it is read by colour, whose darkest tenth is the carving's own
# recesses and the curve's contrast real: 01 0.549 to 0.507 (flatter and greyer than its photo, by eye), 11 0.399 to
# 0.381. So it runs under the brightness rules only, and ours (the colour rule) keeps its curve as fitted.
# --no-tone-check: never; --tone-check: under every rule.
TONE_CHECK = "--no-tone-check" not in argv and (C.RULE == "brightness" or "--tone-check" in argv)


def check_curve(path, c):
    u = C.luminance(C.load(path))[TONE_MASK].astype(np.float64)
    py = k["y"][TONE_MASK].astype(np.float64)
    lo, hi = u <= c["m"], u > c["m"]
    err = lambda sel, a, b: float(np.abs(tone(u[sel], c["m"], a, b) - py[sel]).mean()) if sel.any() else 0.0
    keep_a = err(lo, c["a"], c["b"]) < err(lo, 1.0, 1.0)
    keep_b = err(hi, c["a"], c["b"]) < err(hi, 1.0, 1.0)
    return dict(c, a=c["a"] if keep_a else 1.0, b=c["b"] if keep_b else 1.0,
                checked=dict(a=round(c["a"], 4), b=round(c["b"], 4), kept=[bool(keep_a), bool(keep_b)],
                             lower_error=[round(err(lo, c["a"], c["b"]), 4), round(err(lo, 1.0, 1.0), 4)],
                             upper_error=[round(err(hi, c["a"], c["b"]), 4), round(err(hi, 1.0, 1.0), 4)]))


# The curve and the wall depend on each other: the wall, set through the curve's inverse, lights the stone's sides and
# backs, so the stone's percentiles move and the curve with them (a first try, fitted once: the openings came out 0.05
# too bright). So: render, fit the curve, set the wall through it, fit the power again, until the curve holds still.
if TONE:
    log["tone"] = dict(pivot=round(curve["m"], 4), photo_p10=round(P10, 4), photo_p90=round(P90, 4), rounds=[])
    for it in range(8):
        render(UNTONED, 100, 64)
        c = fit_curve(UNTONED)
        if TONE_CHECK:
            c = check_curve(UNTONED, c)
        log["tone"]["rounds"].append(dict(a=round(c["a"], 4), b=round(c["b"], 4), untoned_p10=c["untoned_p10"],
                                          untoned_p90=c["untoned_p90"], **({"clipped": True} if c["clipped"] else {}),
                                          **({"checked": c["checked"]} if TONE_CHECK else {})))
        print("TONE", it, log["tone"]["rounds"][-1], flush=True)
        still = abs(c["a"] - curve["a"]) < 0.02 and abs(c["b"] - curve["b"]) < 0.02
        curve.update(a=c["a"], b=c["b"])
        set_wall(wall_bands(curve))                                    # the wall through the curve's inverse
        if WALL_PHOTO:
            set_wall_photo(curve)
        fit_power(2)
        if still:
            break
# C-023, fix 27 (the user's shine): the pixel filter, FILTER_PX = 1.8, was set on ours so its edges came out about as
# sharp as its photo's (compare.py's edge gradient: the luminance gradient's mean along each image's own opening edges).
# On a fine lattice it smears each thin bar's light into the black holes beside it: 05's edges 0.79 as sharp as its
# photo's, its stone's 95th percentile 0.837 against 0.956. At 1.2 px 05's SSIM went 0.672 to 0.701, its openings IoU
# 0.699 to 0.749, at 0.8 px to 0.715 and 0.797, the edges 0.88 and 0.97, the 95th percentile 0.861 and 0.883; 03 at 1.2
# 0.702 to 0.728, IoU 0.735 to 0.786, edges 0.91 to 1.01, its 95th percentile 0.941 to 0.964 against 0.973. So the
# filter is fitted per shot the way 1.8 was on ours: full renders at a few widths, toned, read, and the width where the
# edges are as sharp as the photo's, interpolated (0.6 to 3.5 px). --filter W or --fixed-filter: no fit.
FILTER_FIT = "--fixed-filter" not in argv and "--filter" not in argv
if FILTER_FIT:
    def _edge_g(kk):
        yy = kk["y"]
        g = np.hypot(np.gradient(yy, axis=0), np.gradient(yy, axis=1))
        e = (C.dilate(kk["opening"], 1) & ~C.erode(kk["opening"], 1))[BOX]
        return float(g[BOX][e].mean()) if e.any() else 0.0
    _eg_photo = _edge_g(k)
    _ftry = os.path.join(OUT, "filter_try.png")

    def _edge_ratio(width):
        scene.cycles.filter_width = width
        render(_ftry, 100, SAMPLES)
        img = C.load(_ftry)
        if TONE:
            img = tone_rgb(img, curve)
        return _edge_g(C.classify(img.astype(np.float32))) / max(_eg_photo, 1e-6)
    _tries = [(FILTER_PX, _edge_ratio(FILTER_PX))]
    _steps = (1.2, 0.8, 0.6) if _tries[0][1] < 0.97 else ((2.5, 3.2) if _tries[0][1] > 1.05 else ())
    for _w in _steps:
        _tries.append((_w, _edge_ratio(_w)))
        if (_tries[0][1] - 1.0) * (_tries[-1][1] - 1.0) <= 0:
            break
    _tries_s = sorted(_tries, key=lambda t: t[1])
    _lo = max([t for t in _tries_s if t[1] <= 1.0], key=lambda t: t[1], default=None)
    _hi = min([t for t in _tries_s if t[1] >= 1.0], key=lambda t: t[1], default=None)
    if _lo and _hi and _hi[1] > _lo[1]:
        _wf = _lo[0] + (1.0 - _lo[1]) * (_hi[0] - _lo[0]) / (_hi[1] - _lo[1])
    else:
        _wf = min(_tries, key=lambda t: abs(t[1] - 1.0))[0]
    FILTER_FIT_W = float(min(max(_wf, 0.6), 3.5))
    scene.cycles.filter_width = FILTER_FIT_W
    log["filter_fit"] = dict(tries=[dict(width=round(w, 3), edge_ratio=round(e, 4)) for w, e in _tries], width=round(FILTER_FIT_W, 3))
    print("FILTER", log["filter_fit"], flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "scene.blend"))
sec = render(UNTONED if TONE else os.path.join(OUT, "render.png"), 100, SAMPLES)
FINISH = []                                                            # fix 28: the steps below, for the asset
if TONE:
    toned = tone_rgb(C.load(UNTONED), curve)
    FINISH.append(lambda im: tone_rgb(im, curve))
    # C-018: the processing's colour. Each pixel's colour (its distance from grey at the same luminance) scaled by
    # (Y / m)^-k: less above the stone's median, more below, luminance kept. In the photo log(R/G) falls and log(B/G)
    # rises with luminance over the stone (-0.100, 0.113), the render's far less; a cooler spot did not do it (C-017).
    # k is the one that brings the stone's two slopes nearest the photo's, the slopes measured as compare.py does.
    if SATURATION:
        def saturate(img, kk):
            yy = np.maximum(img @ LUM, 1e-6)[..., None]
            f = (np.maximum(yy, SAT_Y_FLOOR) / curve["m"]) ** -kk
            if SAT_Y_FLOOR > 1e-3:
                # C-023, fix 11: fix 5 held the factor at the floor's below it, which at 05's refitted k (0.85, the
                # stone's median 0.86, its floor 0.048) is 11.6: the interior's faint tint came out purple again. The
                # factor was fitted on the stone, so below the stone's darkest it fades to none at black. Only where
                # the floor is set (the dark rule); ours keeps 1e-3 and the step as it was.
                f = 1.0 + (f - 1.0) * np.clip(yy / SAT_Y_FLOOR, 0.0, 1.0)
                # C-023, fix 16: and at most 3. Round 3 refitted 05 at k 1.2 with both slopes within a factor of two
                # (fix 14 kept it), and the factor at the stone's darkest (0.048 against its median 0.80) was 29: the
                # interior, near black and faintly purple in the photo (0.031, 0.020, 0.027), came out purple (0.051,
                # 0.016, 0.043), the ledge's shadow green. The fit sees the cap, so it picks k with it.
                f = np.minimum(f, 3.0)
            return np.clip(yy + (img - yy) * f, 0.0, 1.0)

        # on stone in both images (3 px from any opening), as compare.py measures: a first fit on the photo's stone
        # alone took in the render's wall at the openings' edges, bright and grey, and fitted k = 0.10 where
        # compare.py then measured half the photo's slopes
        render_stone = C.classify(toned.astype(np.float32))["stone"]
        sat_from_photo = bool(render_stone[BOX].sum() < FIT_STONE_MIN * STONE_PH_BOX)   # C-022: as in medians()
        sat_mask = TONE_MASK & C.erode(k["stone"] if sat_from_photo else render_stone, 3)
        # C-023: the factor is fitted on the stone and was applied everywhere: through dark holes (03, 05: a stone median
        # of 0.86, k 1.05 and 1.2) the interior's faint tint came out 50 to 90 times as strong, red and purple. So where
        # the openings are dark, no pixel is taken darker than the stone's 1st percentile (as toned) when its factor is
        # worked out. --sat-everywhere: the factor at every luminance, as before.
        # Only where the openings are dark: on ours the floor (its stone's 1st percentile, 0.118) moved the colour spread
        # from 0.7457 to 0.7232, through the museum's dark surround and deep shadows, which C-018 fitted as they were.
        SAT_Y_FLOOR = 1e-3 if ("--sat-everywhere" in argv or C.SIDE != "dark" or not sat_mask.any()) else max(
            1e-3, float(np.percentile((toned @ LUM)[sat_mask], 1)))

        def full_slopes(img):
            b = np.stack([C.blur(img[:, :, c].astype(np.float32), 5) for c in range(3)], -1)
            ly = np.log(np.maximum(C.luminance(b), 1e-3))[sat_mask]
            return [float(np.polyfit(ly, np.log(np.maximum(b[:, :, i], 1e-3) / np.maximum(b[:, :, 1], 1e-3))[sat_mask], 1)[0])
                    for i in (0, 2)]
        sat_photo = full_slopes(rgb)
        tries = []
        for kk in np.arange(0.0, 1.21, 0.05):
            sl = full_slopes(saturate(toned, kk))
            err = sum(abs(math.log(max(a / b, 1e-3))) if a * b > 0 else 5.0 for a, b in zip(sl, sat_photo))
            tries.append((err, float(kk), sl))
        err, k_sat, sl = min(tries)
        if err >= 5.0:                                                 # C-023: no k matched both slopes' signs (03)
            err, k_sat, sl = next(t for t in tries if t[1] == 0.0)
        # C-023, fix 14: fix 11 let 03's fit land at k 1.05 (error 3.50): the red slope matched (-0.071 against -0.072)
        # and the blue was 30 times too small (0.003 against 0.091), and at that k a pixel of luminance 0.1 has its
        # colour made about ten times as strong: the ledge's shadow and the rosettes' holes came out red. A k is kept
        # only when both slopes come within a factor of two of the photo's; else no colour step. Ours (0.998 and 1.05
        # of the photo's) keeps its k; 03, 05, 06 and 15 (pale stone, k 1.05, 1.05, 0.15, 1.2) get none.
        # --sat-any-fit: the best k whatever its slopes, as before.
        SAT_REJECTED = None
        if "--sat-any-fit" not in argv and k_sat > 0 and any(
                a * b_ <= 0 or abs(math.log(a / b_)) > math.log(2.0) for a, b_ in zip(sl, sat_photo)):
            SAT_REJECTED = dict(k=round(k_sat, 3), slopes=[round(v, 4) for v in sl])
            err, k_sat, sl = next(t for t in tries if t[1] == 0.0)
        toned = saturate(toned, k_sat)
        FINISH.append(lambda im, kk=k_sat: saturate(im, kk))
        log["saturation"] = dict(k=round(k_sat, 3), photo_slopes=[round(v, 4) for v in sat_photo],
                                 render_slopes=[round(v, 4) for v in sl], error=round(err, 4),
                                 **({"y_floor": round(SAT_Y_FLOOR, 4)} if SAT_Y_FLOOR > 1e-3 else {}),
                                 **({"rejected": SAT_REJECTED} if SAT_REJECTED else {}),
                                 **({"stone_from_photo": True} if sat_from_photo else {}),
                                 tries=[dict(k=round(t[1], 3), slopes=[round(v, 4) for v in t[2]]) for t in sorted(tries, key=lambda t: t[1])])
        print("SATURATION", {k: v for k, v in log["saturation"].items() if k != "tries"}, flush=True)
    # C-023, fix 22 (with fix 21, on the user's yes): the curve's lower half also crushed the grey left in dark holes
    # (the pixel filter's spill of the stone's light, lit tunnel walls); without it 03's lattice holes are 0.048 where
    # the photo's are 0.013. A plain black point fitted on the openings took the stone down 0.013 and 03's lattice
    # holes to 0.000 (the box's other openings set it). So a toe: luminance y less t (1 - y / K) where y < K, K the
    # stone's 10th percentile as toned (stone above it untouched), t solved so the openings' median in the box comes
    # to the photo's. Only where the openings are dark (the dark rule); ours's are its lit wall. --no-toe: none.
    if C.SIDE == "dark" and "--no-toe" not in argv:
        y_t = np.maximum(toned @ LUM, 1e-6)
        op_box = k["opening"][BOX]
        r_med, p_med = float(np.median(y_t[BOX][op_box])), float(np.median(k["y"][BOX][op_box]))
        K_TOE = float(np.percentile(y_t[TONE_MASK], 10))
        if r_med > p_med and K_TOE > r_med:
            def toe(yv, t):
                return np.maximum(yv - t * np.clip(1.0 - yv / K_TOE, 0.0, 1.0), 0.0)
            lo_t, hi_t = 0.0, K_TOE
            for _ in range(40):
                mid_t = (lo_t + hi_t) / 2
                if np.median(toe(y_t[BOX][op_box], mid_t)) > p_med:
                    lo_t = mid_t
                else:
                    hi_t = mid_t
            T_TOE = (lo_t + hi_t) / 2
            toned = np.clip(toned * (toe(y_t, T_TOE) / y_t)[..., None], 0.0, 1.0)

            def _toe_rgb(im, t=T_TOE):
                yv = np.maximum(im @ LUM, 1e-6)
                return np.clip(im * (toe(yv, t) / yv)[..., None], 0.0, 1.0)
            FINISH.append(_toe_rgb)
            log["tone"]["toe"] = dict(t=round(T_TOE, 4), knee=round(K_TOE, 4), openings_before=round(r_med, 4),
                                      photo_openings=round(p_med, 4))
            print("TOE", log["tone"]["toe"], flush=True)
    C.write_png(os.path.join(OUT, "render.png"), toned)
    log["tone"].update(a=round(curve["a"], 4), b=round(curve["b"], 4))
log["render"] = dict(seconds=round(sec, 1), samples=SAMPLES, size=[W, H], spot_w=round(spot.energy, 2),
                     wall_strength=round(WALL_MAX, 4), albedo=[round(c, 4) for c in ALBEDO], look=LOOK,
                     filter_px=round(float(scene.cycles.filter_width), 3))
# C-023, fix 28 (the user, on 05: "for the visuals BEHIND the jali ... it should become white as the asset we are
# deriving in Blender is just the jali itself, not the area behind it"). render.png stays the photo's match: the wall
# glows with what the photo shows through the openings, so the fits and compare.py measure the openings against the
# photo's (05's upper bands were brown, linear 0.084, 0.050, 0.037, and its colour step tripled that). The asset is
# rendered once more from the same scene: on camera rays the wall is a holdout, so where the camera would see the wall
# or the world the asset is empty (asset_rgba.png, alpha 0), while the wall still lights the stone as it did. Then
# the same tone curve, colour step and toe as render.png, and over white: asset.png. --no-asset: none.
if "--no-asset" not in argv:
    _out_node = next(n for n in wn.nodes if n.type == "OUTPUT_MATERIAL")
    _lp = wn.nodes.new("ShaderNodeLightPath")
    _hold = wn.nodes.new("ShaderNodeHoldout")
    _msh = wn.nodes.new("ShaderNodeMixShader")
    wn.links.new(_lp.outputs["Is Camera Ray"], _msh.inputs["Fac"])
    wn.links.new(em.outputs["Emission"], _msh.inputs[1])
    wn.links.new(_hold.outputs["Holdout"], _msh.inputs[2])
    wn.links.new(_msh.outputs["Shader"], _out_node.inputs["Surface"])
    scene.render.film_transparent = True
    r.image_settings.color_mode = "RGBA"
    r.image_settings.color_depth = "16"
    _apath = os.path.join(OUT, "asset_untoned.png")
    sec_a = render(_apath, 100, SAMPLES)
    _px = C.oiio.ImageBuf(_apath).get_pixels(C.oiio.FLOAT)              # OpenImageIO premultiplies on reading
    _al = np.clip(_px[:, :, 3], 0.0, 1.0).astype(np.float64)
    _st = np.clip(_px[:, :, :3] / np.maximum(_al, 1e-4)[..., None], 0.0, 1.0).astype(np.float64)
    for _f in FINISH:
        _st = _f(_st)
    # Outside the carved field (fix 29's mask, 3 px wider) the asset is render.png: the two are the same scene and
    # light, and differ there only where the camera looks through the facade's shadow lines, cut as surround, which
    # render.png shows as dark as the photo does (05: 0.008 both) and the asset showed white.
    _fmp = os.path.join(shot.OUT, "field_mask.npy")
    if _rp.get("field_mask") and os.path.exists(_fmp) and "--asset-everywhere" not in argv:
        _away = ~C.dilate(np.load(_fmp), 3)
        _rd = C.load(os.path.join(OUT, "render.png")).astype(np.float64)
        _st = np.where(_away[..., None], _rd, _st)
        _al = np.where(_away, 1.0, _al)
    C.write_png(os.path.join(OUT, "asset_rgba.png"), np.concatenate([_st * _al[..., None], _al[..., None]], -1))   # and
    C.write_png(os.path.join(OUT, "asset.png"), _st * _al[..., None] + (1.0 - _al[..., None]))     # un-premultiplies
    log["asset"] = dict(seconds=round(sec_a, 1), empty_share=round(float((_al < 0.5).mean()), 4),
                        finish=len(FINISH), files=["asset.png (over white)", "asset_rgba.png"])
    print("ASSET", log["asset"], flush=True)
log["seconds"] = round(time.time() - T0, 1)
for path in (os.path.join(OUT, "build.json"), os.path.join(shot.RESULTS, "build.json")):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(log, f, indent=1)
print("BUILD", json.dumps(log["render"]), "total", log["seconds"], flush=True)
