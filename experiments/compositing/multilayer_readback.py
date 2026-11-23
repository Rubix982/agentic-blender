"""How do you read individual passes back from a multilayer EXR in 4.5: with OpenImageIO (bundled in Blender's Python),
and with bpy.data.images.load? And what does a File Output node in OPEN_EXR_MULTILAYER mode write?"""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import glob
import bpy
import numpy as np
import OpenImageIO as oiio
from mathutils import Vector
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene
bpy.ops.mesh.primitive_plane_add(size=40)
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 1))
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
scene.collection.objects.link(sun)
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
cam.location = (0, -6, 6)
cam.rotation_euler = (Vector((0, 0, 0)) - cam.location).to_track_quat("-Z", "Y").to_euler()
scene.collection.objects.link(cam)
scene.camera = cam
scene.render.engine = "CYCLES"
scene.cycles.samples = 4
scene.cycles.use_denoising = False
scene.render.resolution_x, scene.render.resolution_y = 48, 32
vl = scene.view_layers[0]
vl.use_pass_z = True
vl.use_pass_normal = True
scene.render.image_settings.file_format = "OPEN_EXR_MULTILAYER"
scene.render.image_settings.color_depth = "32"
path = E.out("ml.exr")
scene.render.filepath = path
bpy.ops.render.render(write_still=True)

# OpenImageIO: one subimage, all passes as named channels
buf = oiio.ImageBuf(path)
spec = buf.spec()
names = list(spec.channelnames)
px = buf.get_pixels(oiio.FLOAT)  # (height, width, channels), row 0 at the top
nrm = px[..., [names.index(f"ViewLayer.Normal.{c}") for c in "XYZ"]]
E.fact("OpenImageIO is importable in Blender 4.5's Python; ImageBuf(path).spec().channelnames lists every pass channel "
       "and get_pixels(oiio.FLOAT) returns a (height, width, channels) array, top row first",
       channels=names, shape=list(px.shape), subimages=buf.nsubimages)
E.fact("the Normal pass is world-space: floor pixels read (0, 0, 1) though the camera looks down at 45 degrees",
       floor_normal_top_left=[round(float(v), 3) for v in nrm[1, 2]],
       floor_normal_bottom_right=[round(float(v), 3) for v in nrm[30, 46]])

# bpy: can a multilayer EXR be read through bpy.data.images.load?
img = bpy.data.images.load(path)
try:
    img.update()
    upd = "ok"
except RuntimeError as e:
    upd = str(e).strip()
E.fact("bpy.data.images.load of a multilayer EXR in background mode gives an Image of size (0, 0) with no pixels, and "
       "image.update() raises 'does not have any image data': read multilayer EXRs with OpenImageIO",
       type=img.type, size=list(img.size), n_pixels=len(img.pixels), update=upd)

# File Output node in multilayer mode: one file, one layer per slot
scene.use_nodes = True
tree = scene.node_tree
rl = next(n for n in tree.nodes if n.type == "R_LAYERS")
fo = tree.nodes.new("CompositorNodeOutputFile")
fo.format.file_format = "OPEN_EXR_MULTILAYER"
fo.base_path = E.out("fo") + os.sep + "passes_"
fo.layer_slots.clear()
for name, out in (("beauty", "Image"), ("depth", "Depth"), ("normal", "Normal")):
    fo.layer_slots.new(name)
    tree.links.new(rl.outputs[out], fo.inputs[name])
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = E.out("main.png")
bpy.ops.render.render(write_still=True)
files = sorted(glob.glob(E.out("fo") + os.sep + "*"))
ch = list(oiio.ImageBuf(files[0]).spec().channelnames) if files else []
E.fact("a File Output node in OPEN_EXR_MULTILAYER mode uses layer_slots (not file_slots) and writes one file, "
       "base_path + frame number + .exr, with one layer per slot",
       files=[os.path.basename(f) for f in files], channels=ch)
for f in files + [path, E.out("main.png")]:
    os.remove(f)
os.rmdir(E.out("fo"))
E.save()
