# Wrong solution, task 10: everything right except the view transform, left at the default.
import bpy, sys, math

out = sys.argv[sys.argv.index("--") + 1]

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

# Red emissive 1 x 1 m square at x = -1, z = 0.5, facing the camera (-Y).
bpy.ops.mesh.primitive_plane_add(size=1.0, location=(-1.0, 0.0, 0.5), rotation=(math.radians(90), 0, 0))
sq = bpy.context.active_object
m = bpy.data.materials.new("Red")
m.use_nodes = True
nt = m.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
em = nt.nodes.new("ShaderNodeEmission")
em.inputs["Color"].default_value = (1, 0, 0, 1)
em.inputs["Strength"].default_value = 1.0
mo = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(em.outputs["Emission"], mo.inputs["Surface"])
sq.data.materials.append(m)

cam_data = bpy.data.cameras.new("Cam")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 4.0
cam = bpy.data.objects.new("Cam", cam_data)
cam.location = (0, -10, 0)
cam.rotation_euler = (math.radians(90), 0, 0)
sc.collection.objects.link(cam)
sc.camera = cam

sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = 16
sc.cycles.use_denoising = False
sc.render.resolution_x = 400
sc.render.resolution_y = 300
sc.render.resolution_percentage = 100
sc.render.film_transparent = True
sc.view_settings.look = 'None'
sc.view_settings.exposure = 0.0
sc.view_settings.gamma = 1.0

def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

hexcol = "1A2B3C"
lin = [srgb_to_linear(int(hexcol[i:i + 2], 16) / 255.0) for i in (0, 2, 4)]

sc.use_nodes = True
tree = sc.node_tree
for n in list(tree.nodes):
    tree.nodes.remove(n)
rl = tree.nodes.new("CompositorNodeRLayers")
rgb = tree.nodes.new("CompositorNodeRGB")
rgb.outputs[0].default_value = (*lin, 1.0)      # compositor values are scene-linear
over = tree.nodes.new("CompositorNodeAlphaOver")
flip = tree.nodes.new("CompositorNodeFlip")
flip.axis = 'X'
comp = tree.nodes.new("CompositorNodeComposite")
tree.links.new(rgb.outputs[0], over.inputs[1])          # background
tree.links.new(rl.outputs["Image"], over.inputs[2])     # foreground
tree.links.new(over.outputs["Image"], flip.inputs["Image"])
tree.links.new(flip.outputs["Image"], comp.inputs["Image"])

sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGB'
sc.render.image_settings.color_depth = '8'
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
