"""How do render time and noise grow with Cycles samples on Metal, and what does adaptive sampling change?

Noise = RMSE of the linear image against a 4096-sample reference of the same scene."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import time
import bpy
import numpy as np
from mathutils import Vector
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene


def material(name, color, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


bpy.ops.mesh.primitive_plane_add(size=12)
bpy.context.object.data.materials.append(material("floor", (0.8, 0.8, 0.8)))
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 1), segments=48, ring_count=24)
bpy.ops.object.shade_smooth()
bpy.context.object.data.materials.append(material("gold", (1.0, 0.77, 0.34), rough=0.25, metal=1.0))
bpy.ops.mesh.primitive_cube_add(size=1.2, location=(1.8, 0.6, 0.6))
bpy.context.object.data.materials.append(material("red", (0.8, 0.1, 0.1)))
area = bpy.data.objects.new("Area", bpy.data.lights.new("Area", "AREA"))
area.data.energy = 500
area.data.size = 1
area.location = (-3, -2, 4)
area.rotation_euler = (Vector((0, 0, 1)) - area.location).to_track_quat("-Z", "Y").to_euler()
scene.collection.objects.link(area)
world = bpy.data.worlds.new("World")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.3
scene.world = world
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
cam.location = (5, -6, 3.5)
cam.rotation_euler = (Vector((0.5, 0, 0.8)) - cam.location).to_track_quat("-Z", "Y").to_euler()
scene.collection.objects.link(cam)
scene.camera = cam

scene.render.engine = "CYCLES"
exp.metal()
scene.render.resolution_x = scene.render.resolution_y = 256
scene.render.image_settings.file_format = "OPEN_EXR"
scene.render.image_settings.color_depth = "32"
E.fact("Cycles render defaults in 4.5: 4096 max samples, adaptive sampling on with noise threshold 0.01 and "
       "min samples 0 (automatic), denoising on",
       samples=scene.cycles.samples, use_adaptive_sampling=scene.cycles.use_adaptive_sampling,
       adaptive_threshold=round(scene.cycles.adaptive_threshold, 4), adaptive_min_samples=scene.cycles.adaptive_min_samples,
       use_denoising=scene.cycles.use_denoising)
scene.cycles.use_denoising = False


def render(samples, adaptive, threshold=0.01):
    scene.cycles.samples = samples
    scene.cycles.use_adaptive_sampling = adaptive
    scene.cycles.adaptive_threshold = threshold
    scene.render.filepath = E.out("tmp.exr")
    t = time.time()
    bpy.ops.render.render(write_still=True)
    dt = time.time() - t
    img = bpy.data.images.load(scene.render.filepath)
    px = np.array(img.pixels[:], dtype=np.float32).reshape(256, 256, 4)[..., :3]
    bpy.data.images.remove(img)
    return dt, px


render(16, False)  # warm-up (kernel load)
t_ref, ref = render(4096, False)
rows = []
for s in (16, 64, 256, 1024):
    dt, px = render(s, False)
    rows.append(dict(samples=s, adaptive=False, seconds=round(dt, 2), rmse=round(float(np.sqrt(((px - ref) ** 2).mean())), 5)))
for s, th in ((1024, 0.01), (1024, 0.05), (4096, 0.01)):
    dt, px = render(s, True, th)
    rows.append(dict(samples=s, adaptive=True, threshold=th, seconds=round(dt, 2),
                     rmse=round(float(np.sqrt(((px - ref) ** 2).mean())), 5)))
os.remove(E.out("tmp.exr"))
for r in rows:
    print(r)
fixed = [r for r in rows if not r["adaptive"]]
E.fact("without adaptive sampling, noise (RMSE vs a 4096-sample reference) roughly halves for each 4x samples "
       "(Monte Carlo 1/sqrt(N)); time grows about linearly with samples",
       table=fixed, ratio_16_to_64=round(fixed[0]["rmse"] / fixed[1]["rmse"], 2),
       ratio_64_to_256=round(fixed[1]["rmse"] / fixed[2]["rmse"], 2), reference_seconds=round(t_ref, 2))
ad = [r for r in rows if r["adaptive"]]
E.fact("adaptive sampling at 1024 max samples, threshold 0.01, takes less time than 1024 fixed samples, at a higher RMSE",
       fixed_1024=fixed[3], adaptive_1024=ad[0])
E.fact("the 4.5 default (4096 max samples, adaptive, threshold 0.01) on this 256 px scene", default=ad[2])
E.fact("raising the noise threshold to 0.05 cuts time further at more noise", adaptive_005=ad[1])
E.save(rows=rows)
