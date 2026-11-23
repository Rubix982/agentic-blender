# Wrong (rotation = elevation): Low sun: a white sphere (r 1 m) on a grey plane, lit only by a sun 20 degrees above the horizon, no world light;
# Cycles, 256 x 256, 32 samples; the .blend at the path and the render beside it as .png.
import math, os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from _common import OUT, link
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
def mat(name, rgb):
    m = bpy.data.materials.new(name); m.use_nodes = True
    next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (*rgb, 1)
    return m
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 1), segments=48, ring_count=24)
bpy.context.active_object.data.materials.append(mat("White", (0.9, 0.9, 0.9)))
bpy.ops.mesh.primitive_plane_add(size=10)
bpy.context.active_object.data.materials.append(mat("Grey", (0.3, 0.3, 0.3)))
sun = link(bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN")))
sun.data.energy = 3
sun.rotation_euler = (math.radians(20), 0, math.radians(30))   # wrong: tilting by 20 gives a 70-degree sun
cam = link(bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")))
cam.location = (0, -7, 2.5); cam.rotation_euler = (math.radians(78), 0, 0); sc.camera = cam
sc.world = None
sc.render.engine = "CYCLES"; sc.cycles.samples = 32
sc.render.resolution_x = sc.render.resolution_y = 256; sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = "PNG"
sc.render.filepath = os.path.splitext(OUT)[0] + ".png"
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
