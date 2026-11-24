"""Does scaling a spot light's object stretch its cone? C-012 fitted a museum spot's pool with the spot scaled
sideways (a pool wider than round); this checks the effect alone.

A spot 2 m above a white plane, pointing straight down, cone 40 degrees, blend 0 (a hard edge), in Cycles; an
orthographic camera looks straight down at 128 x 128 px over 4 m. For each object scale, the lit pool's width along x
and along y: the extent of pixels brighter than half the pool's peak, in metres. Rows: scale (1, 1, 1), (2, 1, 1) and
(1, 1, 3), the last to see whether scaling along the beam does anything (it narrows the pool, about threefold).
"""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import math
import bpy
import numpy as np
import exp
E = exp.Experiment(__file__)

scene = bpy.context.scene
for ob in list(scene.objects):
    bpy.data.objects.remove(ob)
bpy.ops.mesh.primitive_plane_add(size=4.0)
mat = bpy.data.materials.new("white")
mat.use_nodes = True
next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (0.8, 0.8, 0.8, 1)
bpy.context.object.data.materials.append(mat)
spot = bpy.data.lights.new("spot", "SPOT")
spot.energy, spot.spot_size, spot.spot_blend, spot.shadow_soft_size = 200.0, math.radians(40), 0.0, 0.0
so = bpy.data.objects.new("spot", spot)
so.location = (0, 0, 2.0)                                              # a light points down its -Z: straight down
scene.collection.objects.link(so)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
cam.data.type, cam.data.ortho_scale = "ORTHO", 4.0
cam.location = (0, 0, 5.0)
scene.collection.objects.link(cam)
scene.camera = cam
world = bpy.data.worlds.new("black")
world.use_nodes = True
next(n for n in world.node_tree.nodes if n.type == "BACKGROUND").inputs["Color"].default_value = (0, 0, 0, 1)
scene.world = world
r = scene.render
r.engine = "CYCLES"
r.resolution_x = r.resolution_y = 128
scene.cycles.samples = 16
scene.cycles.use_denoising = False
scene.view_settings.view_transform = "Standard"
exp.metal(scene)
out = E.out("pool.exr")
r.image_settings.file_format = "OPEN_EXR"
m_per_px = 4.0 / 128


def pool(scale):
    so.scale = scale
    r.filepath = out
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(out)
    px = np.array(img.pixels[:]).reshape(128, 128, 4)[:, :, 0]
    bpy.data.images.remove(img)
    lit = px > 0.5 * px.max()
    xs, ys = np.nonzero(lit.any(axis=0))[0], np.nonzero(lit.any(axis=1))[0]
    return round(float((xs.max() - xs.min() + 1) * m_per_px), 3), round(float((ys.max() - ys.min() + 1) * m_per_px), 3)


rows = {}
for scale in ((1, 1, 1), (2, 1, 1), (1, 1, 3)):
    wx, wy = pool(scale)
    rows[f"scale {scale}"] = dict(width_x_m=wx, width_y_m=wy)
    print("ROW", scale, rows[f"scale {scale}"], flush=True)
expected = round(2 * 2.0 * math.tan(math.radians(20)), 3)
a, b, c = rows["scale (1, 1, 1)"], rows["scale (2, 1, 1)"], rows["scale (1, 1, 3)"]
E.fact("Scaling a spot light's object along its local x widens the pool along x (a little less than by that factor, "
       "at half the peak); y is unchanged",
       round_pool_m=a["width_x_m"], cone_says_m=expected, scaled_x_m=b["width_x_m"], scaled_y_m=b["width_y_m"],
       x_ratio=round(b["width_x_m"] / a["width_x_m"], 3))
E.fact("Scaling along the beam (local z) narrows the pool in both directions, by about that factor (expected: little "
       "change; it is the cone's angle that is scaled)", width_x_m=c["width_x_m"], width_y_m=c["width_y_m"],
       ratio=round(a["width_x_m"] / c["width_x_m"], 3))
E.save(rows=rows, cone_deg=40, height_m=2.0, metres_per_px=m_per_px, expected_round_width_m=expected)
