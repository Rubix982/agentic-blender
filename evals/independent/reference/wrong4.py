# Wrong solution, task 4: confuses light linking with shadow linking (blocker collection).
import bpy, sys, math

out = sys.argv[sys.argv.index("--") + 1]

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

def white_material(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs["Base Color"].default_value = (0.8, 0.8, 0.8, 1.0)
    b.inputs["Roughness"].default_value = 1.0
    return m

mat = white_material("White")

bpy.ops.mesh.primitive_plane_add(size=10.0, location=(0, 0, 0))
ground = bpy.context.active_object
ground.data.materials.append(mat)

bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=(-1.5, 0, 1.0), segments=64, ring_count=32)
left = bpy.context.active_object
left.name = "SphereLeft"
bpy.ops.object.shade_smooth()
left.data.materials.append(mat)

bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=(1.5, 0, 1.0), segments=64, ring_count=32)
right = bpy.context.active_object
right.name = "SphereRight"
bpy.ops.object.shade_smooth()
right.data.materials.append(mat)

sun_data = bpy.data.lights.new("Sun", 'SUN')
sun_data.energy = 3.0
sun = bpy.data.objects.new("Sun", sun_data)
sun.location = (0, 0, 10)
sun.rotation_euler = (0, 0, 0)          # sun shines along -Z
sc.collection.objects.link(sun)

# Light linking (Blender 4.0+): the sun's receiver collection excludes the right sphere.
receivers = bpy.data.collections.new("SunReceivers")
receivers.objects.link(right)
# collection_objects runs parallel to collection.objects (no string lookup on it).
idx = list(receivers.objects).index(right)
receivers.collection_objects[idx].light_linking.link_state = 'EXCLUDE'
sun.light_linking.blocker_collection = receivers

world = bpy.data.worlds.new("Black")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)
sc.world = world

cam_data = bpy.data.cameras.new("Cam")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 8.0
cam = bpy.data.objects.new("Cam", cam_data)
cam.location = (0, 0, 10)
cam.rotation_euler = (0, 0, 0)          # looks straight down -Z, +X to the right
sc.collection.objects.link(cam)
sc.camera = cam

sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = 32
sc.render.resolution_x = 400
sc.render.resolution_y = 200
sc.render.resolution_percentage = 100
sc.view_settings.view_transform = 'Standard'
sc.render.image_settings.file_format = 'PNG'
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
