"""What are Cycles' light path (bounce) defaults in 4.5, and how much light and time do bounces add in a closed room?"""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import time
import bpy
import numpy as np
from mathutils import Vector
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene
c = scene.cycles
E.fact("Cycles light path defaults in 4.5",
       max_bounces=c.max_bounces, diffuse_bounces=c.diffuse_bounces, glossy_bounces=c.glossy_bounces,
       transmission_bounces=c.transmission_bounces, volume_bounces=c.volume_bounces,
       transparent_max_bounces=c.transparent_max_bounces, sample_clamp_direct=c.sample_clamp_direct,
       sample_clamp_indirect=c.sample_clamp_indirect, caustics_reflective=c.caustics_reflective,
       caustics_refractive=c.caustics_refractive, blur_glossy=c.blur_glossy, use_fast_gi=c.use_fast_gi,
       use_light_tree=c.use_light_tree)

# a closed white room (a cube seen from inside, normals flipped) with one small point light, camera inside
bpy.ops.mesh.primitive_cube_add(size=4, location=(0, 0, 2))
room = bpy.context.object
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.flip_normals()
bpy.ops.object.mode_set(mode="OBJECT")
m = bpy.data.materials.new("white")
m.use_nodes = True
next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (0.8, 0.8, 0.8, 1)
room.data.materials.append(m)
lamp = bpy.data.objects.new("Lamp", bpy.data.lights.new("Lamp", "POINT"))
lamp.data.energy = 200
lamp.location = (0, 0, 3.5)
scene.collection.objects.link(lamp)
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
cam.data.lens = 18
cam.location = (0, -1.8, 1.5)
cam.rotation_euler = (Vector((0, 2, 1.2)) - cam.location).to_track_quat("-Z", "Y").to_euler()
scene.collection.objects.link(cam)
scene.camera = cam
scene.render.engine = "CYCLES"
exp.metal()
scene.render.resolution_x = scene.render.resolution_y = 192
c.samples = 128
c.use_adaptive_sampling = False
c.use_denoising = False
scene.render.image_settings.file_format = "OPEN_EXR"
scene.render.image_settings.color_depth = "32"


def render():
    scene.render.filepath = E.out("tmp.exr")
    t = time.time()
    bpy.ops.render.render(write_still=True)
    dt = time.time() - t
    img = bpy.data.images.load(scene.render.filepath)
    px = np.array(img.pixels[:], dtype=np.float32).reshape(192, 192, 4)[..., :3]
    bpy.data.images.remove(img)
    return dt, float(px.mean())


render()
rows = []
for b in (0, 1, 2, 4, 8, 12, 32):
    c.max_bounces = b
    c.diffuse_bounces = b
    dt, mean = render()
    rows.append(dict(bounces=b, seconds=round(dt, 2), mean=round(mean, 4)))
    print(rows[-1])
# the default: max 12 but diffuse 4 -> diffuse is capped at 4
c.max_bounces, c.diffuse_bounces = 12, 4
dt, mean_default = render()
c.glossy_bounces = 0
dt, mean_default_noglossy = render()
c.glossy_bounces = 4
os.remove(E.out("tmp.exr"))
full = rows[-1]["mean"]
E.fact("in a closed white room (albedo 0.8) lit by one point light, 0 bounces gives direct light only; each bounce adds light "
       "and the image keeps brightening up to 32 bounces",
       rows=rows, share_of_32_at_0=round(rows[0]["mean"] / full, 3), share_of_32_at_4=round(rows[3]["mean"] / full, 3),
       share_of_32_at_12=round(rows[5]["mean"] / full, 3))
E.fact("the default (max_bounces 12, diffuse_bounces 4) lands near 4 bounces of everything, a little above it, because "
       "the Principled BSDF's specular layer adds glossy bounces (glossy_bounces 4) on top of the 4 diffuse ones",
       mean_default=round(mean_default, 4), mean_default_with_glossy_bounces_0=round(mean_default_noglossy, 4),
       mean_4=rows[3]["mean"], mean_32=full)
E.save(rows=rows)
