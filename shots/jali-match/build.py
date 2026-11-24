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
NORMALS_NPY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "normals.npy")
if (FORMS == "normals" or NORMAL_MAP) and not os.path.exists(NORMALS_NPY):
    raise SystemExit("out/normals.npy is missing: run make.py, or .venv/bin/python shots/jali-match/normals.py, first "
                     "(or build C-009's version with --forms shading --no-normal-map)")
FILTER_PX = float(argv[argv.index("--filter") + 1]) if "--filter" in argv else 1.8   # Cycles' pixel filter width:
# the render's edges were 1.072 x as sharp as the photo's at 1.5 px and 0.853 x at 2.5 (compare.json, edge_gradient)
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)
T0 = time.time()
log = {}

WIDTH_M = 1.05                         # the screen's width (estimate, photo/CREDIT.md)
THICK_M = THICK_ARG or 0.010          # the pierced field's thickness (--thick to try another). C-008: the openings
                                       # agree best when it is thin (IoU 0.564 at the catalogue's 61 mm, 0.737 at 20,
                                       # 0.754 at 10), and took 20. C-011, with the lit and dim tests in the photo's
                                       # rule: 0.7596 at 10, 0.7501 at 15, 0.7354 at 20, 0.715 at 25; now 10 (at 5 the
                                       # curve's fill broke past repair)
BEVEL_M = 0.0005                       # the radius every edge is rounded to (it widens the outline by this). C-007 to
                                       # C-009 used 1 mm and shrank the traced stone by a pixel to make up for it; the
                                       # shrink took the photo's thin connecting pieces (6.8 % of them survived it)
MIN_AREA_PX = 30                       # holes smaller than this (slivers, dust) are dropped; 12 left slivers (C-007)
MIN_ISLAND_PX = 30                     # stone pieces down to this size are kept: small leaf tips are pieces too
RELIEF_M = 0.005                       # C-008: how far the bars rise at most, rounded across their width (C-009: 5 mm,
                                       # under the forms read from the shading)
RELIEF_PX = 20                         # how far in from an opening or the outline (18 mm) they reach that height
FORMS_M = 0.004                        # C-009: the forms read from the averaged shading, at their 99th percentile,
                                       # clipped at 1.5 x that (at 6 mm unclipped they reached 17 mm and read as melted)
# The camera: a Samsung SM-G998B main camera, 24 mm equivalent (EXIF). Assumed: a 12 MP 3000 x 4000 portrait frame
# cropped to 2460 px wide, so the crop spans 2460 / 3000 of the 25.96 mm equivalent short side of a 4:3 frame.
LENS_MM, SENSOR_MM = 24.0, 25.96 * 2460 / 3000

# --- the photograph ----------------------------------------------------------------------------------------------
W, H = C.size()
rgb = C.load(os.path.join(HERE, "photo", "agra-jali.jpg"), (W, H))
k = C.classify(rgb, np.load(NORMALS_NPY) if os.path.exists(NORMALS_NPY) else None)   # C-012: with the normals' veto
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
y0, y1, x0, x1 = int(rows[0]), int(rows[-1]), int(cols[0]), int(cols[-1])
dark = np.zeros((H, W), bool)
dark[y0:y1 + 1, x0:x1 + 1] = k["outside"][y0:y1 + 1, x0:x1 + 1]
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
sy = np.clip(np.round(H / 2 + (yy - H / 2) * KB).astype(int), 0, H - 1)
sx = np.clip(np.round(W / 2 + (xx - W / 2) * KB).astype(int), 0, W - 1)
# Thin stone in the photo (strips about 4 px wide or less): connecting pieces. The user saw them missing in C-009; the
# one-pixel shrink, not the widening, was what took them (see BEVEL_M). --thin-protect also keeps the widening off them:
# it shows 94 % of them against 89 %, but costs the openings 0.05 of IoU (0.678 against 0.725), so it is off by default.
stone_ph = ~k["opening"] & ~k["outside"]
thin = stone_ph & ~C.dilate(C.erode(stone_ph, 2), 2)
hole = k["opening"] | (k["opening"][sy, sx] & (~thin if "--thin-protect" in argv else True))
solid = np.zeros((H, W), bool)
solid[y0:y1 + 1, x0:x1 + 1] = True
solid &= ~hole & ~sur
field = C.blur(solid.astype(np.float32), 3)
loops = C.contours(field, 0.5)
outer_sign = np.sign(C.area(max(loops, key=lambda p: abs(C.area(p)))))   # the frame's outline winds as stone does
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
                       surround_in_box=int(sur.sum()), back_face_scale=round(KB, 4),
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


def trace_mesh(L, flat=False):
    """The outlines as a 2D curve in pixels, filled (and, unless flat, extruded and bevelled), made a mesh."""
    cu = bpy.data.curves.new("jali", "CURVE")
    cu.dimensions = "2D"
    cu.fill_mode = "BOTH"
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


# The fill can still fail in pixels (C-011, at 15 mm: front face 0.280 m2 of 1.145), and both times it was one small
# smoothed island, at about (981, 141), that filled correctly unsmoothed; why is not known (T-014). So when the fill
# falls short, the outlines are halved until the one that breaks it is found, it is swapped for its unsmoothed outline,
# and that is logged; if the same outline is found again, it is dropped (at 5 mm a 120 px hole broke the fill either
# way). At most five times, then the build stops.
me_c = trace_mesh(loops)
repairs = []
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
        again = any(r["loop"] == i for r in repairs)                   # its unsmoothed outline broke it too: drop it
        repairs.append(dict(loop=i, centre_px=[round(float(v), 1) for v in loops[i].mean(0)],
                            area_px=round(float(abs(C.area(loops[i]))), 1), action="dropped" if again else "unsmoothed"))
        loops[i] = loops_raw[i] if not again else None
        if again:
            keep = [j for j in range(len(loops)) if loops[j] is not None]
            loops = [loops[j] for j in keep]
            loops_raw = [loops_raw[j] for j in keep]
            outer = max(range(len(loops)), key=lambda j: abs(C.area(loops[j])))
            for r in repairs:                                          # indices shift after a drop
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
        b5, b21 = C.blur(yph, 5), C.blur(yph, 21)
        var = sum(C.blur(NM[:, :, c] ** 2, 9) - C.blur(NM[:, :, c], 9) ** 2 for c in (0, 1))
        flatw = C.blur(np.clip(1 - np.sqrt(np.maximum(var, 0)) / 0.08, 0, 1).astype(np.float32), 9)
        # On the carving, where the normals already carry the forms, the fine band is used at CARVED_SHARE: at full
        # strength there the photo's pale specks became bumps and the carving read as crusted (C-011, strength 8).
        detail = ((yph - b5) * (CARVED_SHARE + (1 - CARVED_SHARE) * flatw) + (b5 - b21) * flatw) * k["stone"]
        NM = NM.copy()
        NM[:, :, 1] += PHOTO_DETAIL * detail
        NM /= np.maximum(np.linalg.norm(NM, axis=2, keepdims=True), 1e-6)
        log["photo_detail"] = dict(tilt_per_unit=PHOTO_DETAIL, carved_share=CARVED_SHARE, flat_share_of_stone=round(float((flatw[k["stone"]] > 0.5).mean()), 4),
                                   detail_std=round(float(detail[k["stone"]].std()), 4))
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


band_rows = np.array_split(np.arange(y0, y1 + 1), 10)
ph, z_bottom = bh * 0.95 / KW, bz / KW - bh * 0.95 / KW / 2
bands = []
for rr in band_rows:
    o = k["opening"][rr[0]:rr[-1] + 1, x0:x1 + 1]
    if o.sum() < 200:
        continue
    lin = to_lin3(np.median(rgb[rr[0]:rr[-1] + 1, x0:x1 + 1][o], axis=0))
    z = (cy - (rr[0] + rr[-1]) / 2) * S / KW
    bands.append(((z - z_bottom) / ph, lin))
bands.sort(key=lambda b: b[0])
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
for el, (pos, lin) in zip(els, bands):
    el.position = float(min(max(pos, 0.0), 1.0))
    el.color = tuple(float(c) / WALL_MAX for c in lin) + (1.0,)
wn.links.new(wtc.outputs["Generated"], sep.inputs["Vector"])
wn.links.new(sep.outputs["Y"], ramp_w.inputs["Fac"])
wn.links.new(ramp_w.outputs["Color"], em.inputs["Color"])
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
cyc.use_denoising = True

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


def medians(img_rgb, wall_by_colour=False):
    """The stone's median luminance inside the screen's box, and the openings' in its lower and upper halves. In a
    render the wall is found by colour alone (wall_by_colour), so a dim wall still counts and the fit cannot chase it
    to black."""
    q = C.classify(img_rgb)
    if wall_by_colour:
        q["opening"] = q["gr"] > C.GREEN_RED
        q["stone"] = ~q["opening"] & ~q["outside"]
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


LIGHT_JSON = os.path.join(HERE, "results", "light_fit.json")
reuse = not FIXED_LIGHT and not REFIT_LIGHT and os.path.exists(LIGHT_JSON)
if reuse:                                                              # the search takes ~130 renders (2.5 min)
    saved = json.load(open(LIGHT_JSON))
    light = dict(saved["best"])
    log["light_fit"] = dict(reused=LIGHT_JSON.replace(HERE + os.sep, ""), best=saved["best"],
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

# --- fit the spotlight's power to the photo (the wall is set above) --------------------------------------------
target = medians(rgb)
log["fit"] = dict(target_stone_y=round(target[0], 4), target_opening_y_lower=round(target[1], 4),
                  target_opening_y_upper=round(target[2], 4), steps=[])


def gain(want, got):
    return min(10.0, max(0.1, to_lin(want) / max(to_lin(got), 1e-4)))


for step in range(3):
    path = os.path.join(OUT, f"fit_{step}.png")
    sec = render(path, 25, 32)
    st, op_lo, op_hi = medians(C.load(path, (W, H)), wall_by_colour=True)
    log["fit"]["steps"].append(dict(spot_w=round(spot.energy, 2), stone_y=round(st, 4),
                                    opening_y_lower=round(op_lo, 4), opening_y_upper=round(op_hi, 4),
                                    seconds=round(sec, 1)))
    print("FIT", log["fit"]["steps"][-1], flush=True)
    spot.energy *= gain(target[0], st)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "scene.blend"))
sec = render(os.path.join(OUT, "render.png"), 100, SAMPLES)
log["render"] = dict(seconds=round(sec, 1), samples=SAMPLES, size=[W, H], spot_w=round(spot.energy, 2),
                     wall_strength=round(WALL_MAX, 4), albedo=[round(c, 4) for c in ALBEDO], look=LOOK,
                     filter_px=FILTER_PX)
log["seconds"] = round(time.time() - T0, 1)
for path in (os.path.join(OUT, "build.json"), os.path.join(HERE, "results", "build.json")):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(log, f, indent=1)
print("BUILD", json.dumps(log["render"]), "total", log["seconds"], flush=True)
