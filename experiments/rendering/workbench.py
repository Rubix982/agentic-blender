"""What does the Workbench engine render in background mode, how fast, and which colour does it take from a material:
the node tree's Base Color or material.diffuse_color (the viewport colour)?"""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import time
import bpy
import numpy as np
import OpenImageIO as oiio
from mathutils import Vector
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene
bpy.ops.mesh.primitive_plane_add(size=20)
plane = bpy.context.object
m = bpy.data.materials.new("two_colours")
m.use_nodes = True
next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (1, 0, 0, 1)  # red in nodes
m.diffuse_color = (0, 1, 0, 1)  # green in the viewport colour
plane.data.materials.append(m)
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
cam.location = (0, 0, 5)
scene.collection.objects.link(cam)
scene.camera = cam
scene.render.resolution_x = scene.render.resolution_y = 64
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "Standard"


def render(engine):
    scene.render.engine = engine
    scene.render.filepath = E.out(f"tmp_{engine}.png")
    t = time.time()
    bpy.ops.render.render(write_still=True)
    dt = time.time() - t
    px = oiio.ImageBuf(scene.render.filepath).get_pixels(oiio.UINT8)[32, 32, :3]
    os.remove(scene.render.filepath)
    return round(dt, 3), [int(v) for v in px]


d = scene.display.shading
E.fact("Workbench render shading defaults (scene.display.shading) in a new file",
       light=d.light, color_type=d.color_type, show_shadows=d.show_shadows, show_cavity=d.show_cavity,
       render_aa=scene.display.render_aa,
       light_items=[i.identifier for i in type(d).bl_rna.properties["light"].enum_items],
       color_type_items=[i.identifier for i in type(d).bl_rna.properties["color_type"].enum_items])
d.light = "FLAT"
d.color_type = "MATERIAL"
t_wb, px_wb = render("BLENDER_WORKBENCH")
scene.world = bpy.data.worlds.new("w")
scene.world.color = (0, 0, 0)
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
scene.collection.objects.link(sun)
scene.cycles.samples = 4
t_cy, px_cy = render("CYCLES")
E.fact("Workbench (color_type MATERIAL) draws material.diffuse_color, not the node tree's Base Color; Cycles draws the node colour",
       workbench_rgb=px_wb, cycles_rgb=px_cy, diffuse_color=(0, 1, 0), base_color=(1, 0, 0))
d.color_type = "OBJECT"
plane.color = (0, 0, 1, 1)
_, px_obj = render("BLENDER_WORKBENCH")
E.fact("color_type OBJECT draws object.color", rgb=px_obj, object_color=(0, 0, 1))
scene.render.resolution_x = scene.render.resolution_y = 512
d.light = "STUDIO"
d.color_type = "MATERIAL"
times = [render("BLENDER_WORKBENCH")[0] for _ in range(3)]
E.fact("a 512 px Workbench render (studio light, default 8 AA samples) takes well under a second", seconds=times)
E.save()
