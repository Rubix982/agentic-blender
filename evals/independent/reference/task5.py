# Reference solution, task 5: a 360 x 180 equirectangular panorama from the origin.
import bpy, sys, math

out = sys.argv[sys.argv.index("--") + 1]

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

def emissive(name, rgb):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*rgb, 1.0)
    em.inputs["Strength"].default_value = 1.0
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(em.outputs["Emission"], o.inputs["Surface"])
    return m

markers = {
    "PlusY":  ((0, 5, 0),  (1, 0, 0)),
    "PlusX":  ((5, 0, 0),  (0, 1, 0)),
    "MinusY": ((0, -5, 0), (0, 0, 1)),
    "MinusX": ((-5, 0, 0), (1, 1, 0)),
    "PlusZ":  ((0, 0, 5),  (1, 1, 1)),
    "MinusZ": ((0, 0, -5), (1, 0, 1)),
}
for name, (loc, rgb) in markers.items():
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.data.materials.append(emissive(name, rgb))

world = bpy.data.worlds.new("Black")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)
sc.world = world

cam_data = bpy.data.cameras.new("Pano")
cam_data.type = 'PANO'
# Blender 3.0+: panorama settings live on the camera itself, not camera.cycles.
cam_data.panorama_type = 'EQUIRECTANGULAR'
cam_data.longitude_min = -math.pi
cam_data.longitude_max = math.pi
cam_data.latitude_min = -math.pi / 2
cam_data.latitude_max = math.pi / 2
cam = bpy.data.objects.new("Pano", cam_data)
cam.location = (0, 0, 0)
cam.rotation_euler = (math.radians(90), 0, 0)   # view axis along +Y, camera up = +Z
sc.collection.objects.link(cam)
sc.camera = cam

sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = 16
sc.cycles.use_denoising = False
sc.render.resolution_x = 512
sc.render.resolution_y = 256
sc.render.resolution_percentage = 100
sc.view_settings.view_transform = 'Standard'
sc.render.image_settings.file_format = 'PNG'
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
