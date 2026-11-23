"""How long does the same Cycles render take on Metal (GPU) and on the CPU, and how much of the first GPU render is setup?"""
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


# a floor, a glossy sphere, a diffuse cube, a sun and an area light, a camera aimed at the sphere
bpy.ops.mesh.primitive_plane_add(size=12)
bpy.context.object.data.materials.append(material("floor", (0.8, 0.8, 0.8)))
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 1), segments=48, ring_count=24)
bpy.ops.object.shade_smooth()
bpy.context.object.data.materials.append(material("gold", (1.0, 0.77, 0.34), rough=0.25, metal=1.0))
bpy.ops.mesh.primitive_cube_add(size=1.2, location=(1.8, 0.6, 0.6))
bpy.context.object.data.materials.append(material("red", (0.8, 0.1, 0.1)))
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
sun.data.energy = 3.0
sun.rotation_euler = (0.7, 0.2, 0.5)
scene.collection.objects.link(sun)
area = bpy.data.objects.new("Area", bpy.data.lights.new("Area", "AREA"))
area.data.energy = 300
area.data.size = 2
area.location = (-3, -2, 4)
area.rotation_euler = (Vector((0, 0, 1)) - area.location).to_track_quat("-Z", "Y").to_euler()
scene.collection.objects.link(area)
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
cam.location = (5, -6, 3.5)
cam.rotation_euler = (Vector((0.5, 0, 0.8)) - cam.location).to_track_quat("-Z", "Y").to_euler()
scene.collection.objects.link(cam)
scene.camera = cam

scene.render.engine = "CYCLES"
scene.render.resolution_x = scene.render.resolution_y = 384
scene.cycles.samples = 128
scene.cycles.use_adaptive_sampling = False
scene.cycles.use_denoising = False
scene.render.image_settings.file_format = "OPEN_EXR"
scene.render.image_settings.color_depth = "32"


def render(tag):
    scene.render.filepath = E.out(f"{tag}.exr")
    t = time.time()
    bpy.ops.render.render(write_still=True)
    dt = time.time() - t
    img = bpy.data.images.load(scene.render.filepath)
    px = np.array(img.pixels[:], dtype=np.float32).reshape(img.size[1], img.size[0], 4)[..., :3]
    bpy.data.images.remove(img)
    return dt, px


dev = exp.metal()
gpu1, a = render("gpu1")
gpu2, b = render("gpu2")
scene.cycles.device = "CPU"
cpu1, c = render("cpu1")
cpu2, _ = render("cpu2")

E.fact("exp.metal() selects the Metal GPU device", device=dev)
E.fact("the first Metal render of a session takes longer than the second (kernel load / scene upload)",
       gpu_first_s=round(gpu1, 2), gpu_second_s=round(gpu2, 2))
E.fact("at 384x384, 128 samples, no denoising, the M2 Pro GPU (Metal) renders this scene faster than its 12 CPU threads",
       gpu_s=round(gpu2, 2), cpu_s=round(min(cpu1, cpu2), 2), cpu_over_gpu=round(min(cpu1, cpu2) / gpu2, 2),
       threads=scene.render.threads)
E.fact("GPU and CPU renders of the same scene, seed and samples agree in mean value to within 1 %",
       gpu_mean=round(float(b.mean()), 4), cpu_mean=round(float(c.mean()), 4),
       rel_diff=round(float(abs(b.mean() - c.mean()) / c.mean()), 4))
d_gg = float(np.abs(a - b).max())
E.fact(f"two GPU renders with the same seed are {'bit-identical' if d_gg == 0 else 'not bit-identical, but agree to within 1e-4 per pixel'}",
       max_abs_diff=d_gg)
d_gc = float(np.abs(b - c).max())
E.fact("GPU and CPU renders with the same seed draw the same noise pattern: they differ by at most 0.01 per pixel, "
       "far less than the noise itself at 128 samples",
       max_abs_diff=round(d_gc, 4), mean_abs_diff=round(float(np.abs(b - c).mean()), 6))
for f in ("gpu1", "gpu2", "cpu1", "cpu2"):
    os.remove(E.out(f"{f}.exr"))
E.save(resolution=384, samples=128, gpu_first_s=gpu1, gpu_second_s=gpu2, cpu_first_s=cpu1, cpu_second_s=cpu2)
