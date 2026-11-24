"""C-007, step 2: rebuild the carved jali from its photograph, light it like the photo, and render it from the photo's
viewpoint.

    python3 skills/blender/scripts/run.py shots/jali-match/build.py [-- --samples 256]

What comes from the photograph, and nothing else:
  - the outline of the stone and of every opening (inside the screen's box, every pixel common.classify does not call
    an opening, less the dark surround reaching in from the box's edge; blurred 3 px and traced at 0.5 by marching
    squares);
  - the carved lines inside the stone (common.cut_lines; C-008), which become grooves in a relief;
  - the stone's hue (its median colour, brought to an albedo of 0.45 at the brightest channel);
  - the wall's colour in ten bands from top to bottom (the openings' median colour in each), set exactly: the wall
    only emits and is seen straight through the openings;
  - the spotlight's power, fitted by rendering so the stone's median luminance matches the photo's;
  - the pierced field's thickness, 20 mm, chosen because the openings agree best when it is thin (C-008).
Everything else is made here: the solid (a 2D curve, extruded to the screen's thickness, every edge rounded by the
curve's bevel), a carved front over it (every piece between the lines rising with a rounded profile), a procedural sandstone, a lit panel behind the screen, a spotlight from above and in front, and a
camera from the photo's EXIF. The size is an estimate (photo/CREDIT.md): the screen 1.05 m wide, 6.1 cm thick.

Writes shots/jali-match/out/: scene.blend, render.png, build.json (also results/build.json)."""
import json
import math
import os
import sys
import time

import bpy
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common as C  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAMPLES = int(argv[argv.index("--samples") + 1]) if "--samples" in argv else 256
THICK_ARG = float(argv[argv.index("--thick") + 1]) if "--thick" in argv else None
LOOK = argv[argv.index("--look") + 1] if "--look" in argv else "None"
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)
T0 = time.time()
log = {}

WIDTH_M = 1.05                         # the screen's width (estimate, photo/CREDIT.md)
THICK_M = THICK_ARG or 0.020          # the pierced field's thickness, fitted in C-008 (--thick to try another):
                                       # the openings agree best when it is thin (IoU 0.564 at the catalogue's 61 mm,
                                       # 0.737 at 20, 0.754 at 10); 20 mm is within 0.02 of the best
BEVEL_M = 0.001                        # the radius every edge is rounded to; the bevel widens the outline by this,
                                       # so the traced stone is first shrunk by one pixel (0.92 mm)
MIN_AREA_PX = 30                       # outlines smaller than this (slivers, dust) are dropped; 12 left slivers (C-007)
RELIEF_M = 0.010                       # C-008: how far the bars rise at most, rounded across their width
RELIEF_PX = 20                         # how far in from an opening or the outline (18 mm) they reach that height
GROOVE_M = 0.003                       # how deep the traced cut lines are cut into that surface
# The camera: a Samsung SM-G998B main camera, 24 mm equivalent (EXIF). Assumed: a 12 MP 3000 x 4000 portrait frame
# cropped to 2460 px wide, so the crop spans 2460 / 3000 of the 25.96 mm equivalent short side of a 4:3 frame.
LENS_MM, SENSOR_MM = 24.0, 25.96 * 2460 / 3000

# --- the photograph ----------------------------------------------------------------------------------------------
W, H = C.size()
rgb = C.load(os.path.join(HERE, "photo", "agra-jali.jpg"), (W, H))
k = C.classify(rgb)
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
hole = k["opening"] | k["opening"][sy, sx]
solid = np.zeros((H, W), bool)
solid[y0:y1 + 1, x0:x1 + 1] = True
solid &= ~hole & ~sur
shrunk = solid.copy()                                                  # one pixel off every edge, for the bevel
shrunk[1:] &= solid[:-1]; shrunk[:-1] &= solid[1:]; shrunk[:, 1:] &= solid[:, :-1]; shrunk[:, :-1] &= solid[:, 1:]
field = C.blur(shrunk.astype(np.float32), 3)
loops = [p for p in C.contours(field, 0.5) if abs(C.area(p)) >= MIN_AREA_PX]
# C-008: the carving. The bars round across their width: the height rises with distance from the nearest opening or
# outline, RELIEF_M at most, about RELIEF_PX in. The distance is smooth: the stone mask blurred over 2 x RELIEF_PX reads
# 0.5 at an edge and 1 deep inside, so (b - 0.5) x 2, eased, goes 0 to 1. The cut lines traced from the photo
# (common.cut_lines) are cut GROOVE_M into that surface.
# Two first versions, recorded in the card: every piece between the lines rising on its own (the lines cut the stone
# into hundreds of small humps; it read as crumbled rock), and the distance counted by erosions (it stepped in blocks).
closed = C.erode(C.dilate(solid, 2), 2) | solid                       # pin-prick holes (dropped from the trace) filled
skin = C.erode(closed, 1)                                              # stays inside the curve's outline
lines = C.cut_lines(k) & skin
b = np.clip((C.blur(skin.astype(np.float32), 2 * RELIEF_PX) - 0.5) * 2, 0, 1)
prof = b * b * (3 - 2 * b)                                             # smoothstep
groove = np.clip(C.blur(lines.astype(np.float32), 5) * 2.0, 0, 1)
height = (np.maximum(prof * RELIEF_M - groove * GROOVE_M, 0) * skin).astype(np.float32)
C.write_png(os.path.join(OUT, "height.png"), height / RELIEF_M)
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
cu = bpy.data.curves.new("jali", "CURVE")
cu.dimensions = "2D"
cu.fill_mode = "BOTH"
cu.resolution_u = 1
cu.extrude = THICK_M / 2 - BEVEL_M
cu.bevel_depth = BEVEL_M
cu.bevel_resolution = 3
# cu.offset stays 0: any other value broke the fill of these nested outlines (front face 0.24 m2 at -3 mm, 0.09 at
# +3 mm, against 1.10 at 0; the outlines enclose 1.15 m2).
cx, cy = W / 2, H / 2
for p in loops:
    sp = cu.splines.new("POLY")
    sp.points.add(len(p) - 1)
    co = np.zeros((len(p), 4), np.float32)
    co[:, 0] = (p[:, 0] - cx) * S
    co[:, 1] = (cy - p[:, 1]) * S
    co[:, 3] = 1.0
    sp.points.foreach_set("co", co.ravel())
    sp.use_cyclic_u = True
    sp.use_smooth = True                                               # flat facets striped the holes' side walls
screen = bpy.data.objects.new("jali", cu)
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
cu.materials.append(mat)

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
log["relief"] = dict(max_m=RELIEF_M, reach_px=RELIEF_PX, groove_m=GROOVE_M, vertices=len(co), faces=len(quads))

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
so.location = (0, -1.2, 2.0)                                           # about 60 degrees up: lit tops, dark undersides
so.rotation_euler = (Vector((0, 0, 0.0)) - so.location).to_track_quat("-Z", "Y").to_euler()
scene.collection.objects.link(so)

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
expected = abs(sum(C.area(p) for p in loops)) * S * S
front = sum(f.area for f in me.polygons if f.normal.z > 0.99)
log["mesh"] = dict(vertices=len(me.vertices), faces=len(me.polygons), front_face_m2=round(front, 4),
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


# --- fit the spotlight to the photo (the wall is set above) ------------------------------------------------------
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
                     wall_strength=round(WALL_MAX, 4), albedo=[round(c, 4) for c in ALBEDO], look=LOOK)
log["seconds"] = round(time.time() - T0, 1)
for path in (os.path.join(OUT, "build.json"), os.path.join(HERE, "results", "build.json")):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(log, f, indent=1)
print("BUILD", json.dumps(log["render"]), "total", log["seconds"], flush=True)
