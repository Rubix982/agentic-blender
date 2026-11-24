"""C-007, step 2: rebuild the carved jali from its photograph, light it like the photo, and render it from the photo's
viewpoint.

    python3 skills/blender/scripts/run.py shots/jali-match/build.py [-- --samples 256]

What comes from the photograph, and nothing else:
  - the outline of the stone and of every opening (inside the screen's box, every pixel common.classify does not call
    an opening, less the dark surround reaching in from the box's edge; blurred 3 px and traced at 0.5 by marching
    squares);
  - the stone's hue (its median colour, brought to an albedo of 0.45 at the brightest channel);
  - the wall's colour (the openings' median colour);
  - three numbers fitted by rendering: the spotlight's power, so the stone's median luminance matches the photo's, and
    the lit wall's strength at its bottom and top, so the openings' medians in the screen's lower and upper halves do.
Everything else is made here: the solid (a 2D curve, extruded to the screen's thickness, every edge rounded by the
curve's bevel), a procedural sandstone, a lit panel behind the screen, a spotlight from above and in front, and a
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
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)
T0 = time.time()
log = {}

WIDTH_M = 1.05                         # the screen's width (estimate, photo/CREDIT.md)
THICK_M = 0.061                        # its thickness
BEVEL_M = 0.001                        # the radius every edge is rounded to; the bevel widens the outline by this,
                                       # so the traced stone is first shrunk by one pixel (0.92 mm)
PILLOW_PX = 25                         # the blur that turns the outline into a rounded height for the bars
MIN_AREA_PX = 12                       # outlines smaller than this (dust, noise) are dropped
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
pillow = C.blur(solid.astype(np.float32), PILLOW_PX) * solid           # from the outline only, not the photo's shading
pillow = (pillow / max(float(pillow.max()), 1e-6)).astype(np.float32)
C.write_exr(os.path.join(OUT, "pillow.exr"), pillow)
log["sizes"] = dict(width_m=WIDTH_M, thick_m=THICK_M, thick_cm=THICK_M * 100, bevel_m=BEVEL_M)
log["outlines"] = dict(count=len(loops), points=int(sum(len(p) for p in loops)), metres_per_px=round(S, 6),
                       screen_width_px=width_px, box=[x0, y0, x1, y1], dark_in_box_made_stone=int((dark & ~sur).sum()),
                       surround_in_box=int(sur.sum()), back_face_scale=round(KB, 4),
                       seen_opening_share=round(float(k["opening"][y0:y1 + 1, x0:x1 + 1].mean()), 4),
                       hole_share=round(float(hole[y0:y1 + 1, x0:x1 + 1].mean()), 4))
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
img = bpy.data.images.load(os.path.join(OUT, "pillow.exr"))
img.colorspace_settings.name = "Non-Color"
mapn = nt.nodes.new("ShaderNodeMapping")                               # the curve's own x, y onto the image
mapn.inputs["Location"].default_value = (0.5, 0.5, 0.0)
mapn.inputs["Scale"].default_value = (1 / (W * S), 1 / (H * S), 1.0)
tex = nt.nodes.new("ShaderNodeTexImage")
tex.image = img
tex.extension = "EXTEND"
pb = nt.nodes.new("ShaderNodeBump")
pb.inputs["Strength"].default_value = 1.0
pb.inputs["Distance"].default_value = 0.03                              # the bars' rounding: 30 mm at the widest
L.new(tc.outputs["Object"], mapn.inputs["Vector"])
L.new(mapn.outputs["Vector"], tex.inputs["Vector"])
L.new(tex.outputs["Color"], pb.inputs["Height"])
L.new(pb.outputs["Normal"], bump.inputs["Normal"])
L.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
bsdf.inputs["Roughness"].default_value = 0.9
cu.materials.append(mat)

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
# The wall glows, like the museum's lit backdrop: brighter at the bottom than the top. Its colour is the photo's
# openings' median; its two ends are fitted below to the openings' median luminance in the screen's lower and upper
# halves.
wall_rgb = np.median(rgb[k["opening"]], axis=0)
wall_lin = np.where(wall_rgb <= 0.04045, wall_rgb / 12.92, ((wall_rgb + 0.055) / 1.055) ** 2.4)
WALL = tuple(float(c) for c in wall_lin / wall_lin.max())
wm = bpy.data.materials.new("lit wall")
wm.use_nodes = True
wn = wm.node_tree
for n in list(wn.nodes):
    if n.type != "OUTPUT_MATERIAL":
        wn.nodes.remove(n)
em = wn.nodes.new("ShaderNodeEmission")
em.inputs["Color"].default_value = WALL + (1.0,)
wtc = wn.nodes.new("ShaderNodeTexCoord")
sep = wn.nodes.new("ShaderNodeSeparateXYZ")
ramp_w = wn.nodes.new("ShaderNodeMapRange")                            # Generated y: 0 at the bottom, 1 at the top
ramp_w.inputs["To Min"].default_value = 1.0                            # bottom strength
ramp_w.inputs["To Max"].default_value = 0.3                            # top strength
wn.links.new(wtc.outputs["Generated"], sep.inputs["Vector"])
wn.links.new(sep.outputs["Y"], ramp_w.inputs["Value"])
wn.links.new(ramp_w.outputs["Result"], em.inputs["Strength"])
wn.links.new(em.outputs["Emission"], next(n for n in wn.nodes if n.type == "OUTPUT_MATERIAL").inputs["Surface"])
wall.data.materials.append(wm)

spot = bpy.data.lights.new("spot", "SPOT")
spot.energy = 400.0
spot.spot_size = math.radians(45)
spot.spot_blend = 0.6
spot.shadow_soft_size = 0.05
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
scene.view_settings.look = "None"
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


# --- fit the two lights to the photo -----------------------------------------------------------------------------
target = medians(rgb)
log["fit"] = dict(target_stone_y=round(target[0], 4), target_opening_y_lower=round(target[1], 4),
                  target_opening_y_upper=round(target[2], 4), steps=[])
lo_in, hi_in = ramp_w.inputs["To Min"], ramp_w.inputs["To Max"]


def gain(want, got):
    return min(10.0, max(0.1, to_lin(want) / max(to_lin(got), 1e-4)))


for step in range(4):
    path = os.path.join(OUT, f"fit_{step}.png")
    sec = render(path, 25, 32)
    st, op_lo, op_hi = medians(C.load(path, (W, H)), wall_by_colour=True)
    log["fit"]["steps"].append(dict(spot_w=round(spot.energy, 2), wall_bottom=round(lo_in.default_value, 4),
                                    wall_top=round(hi_in.default_value, 4), stone_y=round(st, 4),
                                    opening_y_lower=round(op_lo, 4), opening_y_upper=round(op_hi, 4),
                                    seconds=round(sec, 1)))
    print("FIT", log["fit"]["steps"][-1], flush=True)
    spot.energy *= gain(target[0], st)
    lo_in.default_value *= gain(target[1], op_lo)
    hi_in.default_value *= gain(target[2], op_hi)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "scene.blend"))
sec = render(os.path.join(OUT, "render.png"), 100, SAMPLES)
log["render"] = dict(seconds=round(sec, 1), samples=SAMPLES, size=[W, H], spot_w=round(spot.energy, 2),
                     wall_bottom=round(lo_in.default_value, 4), wall_top=round(hi_in.default_value, 4),
                     wall_rgb=[round(c, 4) for c in WALL], albedo=[round(c, 4) for c in ALBEDO])
log["seconds"] = round(time.time() - T0, 1)
for path in (os.path.join(OUT, "build.json"), os.path.join(HERE, "results", "build.json")):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(log, f, indent=1)
print("BUILD", json.dumps(log["render"]), "total", log["seconds"], flush=True)
