"""Render passes and the compositor in background mode, 4.5: which passes each engine writes to a multilayer EXR and
under what channel names, what the Depth pass measures, whether compositor nodes run in -b, what a File Output node
writes, and whether the Viewer Node image can be read."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import glob
import math
import bpy
import numpy as np
import OpenImageIO as oiio
from mathutils import Vector
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene
bpy.ops.mesh.primitive_plane_add(size=40)  # floor at z = 0
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 1))
sphere = bpy.context.object
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
sun.rotation_euler = (0.5, 0.3, 0)
scene.collection.objects.link(sun)
w = bpy.data.worlds.new("w")
w.color = (0.3, 0.3, 0.3)
scene.world = w
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
cam.location = (0, -6, 6)
cam.rotation_euler = (Vector((0, 0, 0)) - cam.location).to_track_quat("-Z", "Y").to_euler()  # aimed at the origin
scene.collection.objects.link(cam)
scene.camera = cam
scene.render.resolution_x = scene.render.resolution_y = 64
scene.cycles.samples = 8
scene.cycles.use_denoising = False
scene.eevee.taa_render_samples = 4
exp.metal()
vl = scene.view_layers[0]
for p in ("use_pass_z", "use_pass_normal", "use_pass_ambient_occlusion", "use_pass_mist", "use_pass_position",
          "use_pass_diffuse_color", "use_pass_shadow", "use_pass_object_index", "use_pass_cryptomatte_object",
          "use_pass_cryptomatte_material"):
    setattr(vl, p, True)
scene.render.image_settings.file_format = "OPEN_EXR_MULTILAYER"
scene.render.image_settings.color_depth = "32"
chans = {}
for eng in ("CYCLES", "BLENDER_EEVEE_NEXT"):
    scene.render.engine = eng
    scene.render.filepath = E.out(f"{eng}.exr")
    bpy.ops.render.render(write_still=True)
    names = list(oiio.ImageBuf(scene.render.filepath).spec().channelnames)
    chans[eng] = sorted({n.rsplit(".", 1)[0] for n in names})
E.fact("passes written to a multilayer EXR with Z, Normal, AO, Mist, Position, DiffCol, Shadow, IndexOB and Cryptomatte "
       "(object, material) enabled on the view layer; channel names are '<ViewLayer>.<Pass>.<channel>'. Cycles has no "
       "Shadow pass (use_pass_shadow is EEVEE's; Cycles has Shadow Catcher instead) and EEVEE has no object index pass",
       cycles=chans["CYCLES"], eevee=chans["BLENDER_EEVEE_NEXT"])

# what the Depth pass measures: distance along the view axis (planar) or along the ray (radial)?
buf = oiio.ImageBuf(E.out("CYCLES.exr"))
names = list(buf.spec().channelnames)
px = buf.get_pixels(oiio.FLOAT)
z = px[..., names.index("ViewLayer.Depth.Z")]
pos = np.stack([px[..., names.index(f"ViewLayer.Position.{c}")] for c in "XYZ"], axis=-1)
cam_loc = np.array(cam.location)
fwd = np.array(cam.matrix_world.to_3x3() @ Vector((0, 0, -1)))
y, x = 2, 2  # a corner pixel, far off the view axis
radial = float(np.linalg.norm(pos[y, x] - cam_loc))
planar = float(np.dot(pos[y, x] - cam_loc, fwd))
E.fact("Cycles' Depth (Z) pass is the distance along the camera's view axis (planar depth), not the distance along the ray",
       corner_depth=round(float(z[y, x]), 3), planar=round(planar, 3), radial=round(radial, 3))
os.remove(E.out("CYCLES.exr"))
os.remove(E.out("BLENDER_EEVEE_NEXT.exr"))

# the compositor: scene.use_nodes creates scene.node_tree with Render Layers -> Composite
scene.render.engine = "CYCLES"
E.fact("in 4.5 the compositor is scene.node_tree, created by scene.use_nodes = True (in 5.0 this becomes "
       "scene.compositing_node_group); before use_nodes it is None",
       node_tree_before=scene.node_tree is not None, has_compositing_node_group=hasattr(scene, "compositing_node_group"))
scene.use_nodes = True
tree = scene.node_tree
E.fact("a new compositor tree in 4.5 holds Render Layers, Composite, a Viewer and a Reroute: Render Layers Image -> "
       "Reroute -> Composite and Viewer",
       nodes=[(n.bl_idname, n.name) for n in tree.nodes],
       links=[(l.from_node.bl_idname, l.from_socket.name, l.to_node.bl_idname, l.to_socket.name) for l in tree.links])
rl = next(n for n in tree.nodes if n.type == "R_LAYERS")
comp = next(n for n in tree.nodes if n.type == "COMPOSITE")
viewer = next(n for n in tree.nodes if n.type == "VIEWER")
E.fact("the Render Layers node exposes one output per enabled pass, by pass name",
       outputs=[s.name for s in rl.outputs if s.enabled])
scene.render.image_settings.file_format = "OPEN_EXR"
scene.render.filepath = E.out("plain.exr")
scene.frame_set(1)
bpy.ops.render.render(write_still=True)
plain = oiio.ImageBuf(E.out("plain.exr")).get_pixels(oiio.FLOAT)[..., :3]
v = bpy.data.images.get("Viewer Node")
vpx = np.array(v.pixels[:], np.float32).reshape(v.size[1], v.size[0], 4)[::-1, :, :3] if v and len(v.pixels) else None
ok = bool(vpx is not None and vpx.shape == plain.shape and np.allclose(vpx, plain, atol=1e-3))
E.fact(f"the 'Viewer Node' image after a background render {'holds' if ok else 'does not hold'} the render "
       f"({'readable' if ok else 'a 256x256 placeholder here'}); save the render to a file and read that instead",
       viewer_exists=v is not None, size=list(v.size) if v else None,
       matches_render=bool(vpx is not None and vpx.shape == plain.shape and np.allclose(vpx, plain, atol=1e-3)))
inv = tree.nodes.new("CompositorNodeInvert")
tree.links.new(rl.outputs["Image"], inv.inputs["Color"])
tree.links.new(inv.outputs["Color"], comp.inputs["Image"])
fo = tree.nodes.new("CompositorNodeOutputFile")
fo.base_path = E.out("fileout") + os.sep
fo.format.file_format = "OPEN_EXR"
fo.file_slots[0].path = "depth_"
tree.links.new(rl.outputs["Depth"], fo.inputs[0])
fo.file_slots.new("normal_")
tree.links.new(rl.outputs["Normal"], fo.inputs["normal_"])
scene.render.filepath = E.out("composite.exr")
bpy.ops.render.render(write_still=True)
img = oiio.ImageBuf(E.out("composite.exr")).get_pixels(oiio.FLOAT)[..., :3]
E.fact("compositor nodes run in background renders: the written image is what reaches the Composite node (here an Invert: "
       "written = 1 - plain render, to float precision)",
       max_err=float(np.abs(img - (1 - plain)).max()), sample_plain=[round(float(x), 3) for x in plain[32, 32]],
       sample_written=[round(float(x), 3) for x in img[32, 32]])
os.remove(E.out("plain.exr"))
written = sorted(os.path.basename(p) for p in glob.glob(E.out("fileout") + "/*"))
E.fact("a File Output node writes one file per slot, named base_path + slot path + 4-digit frame number + extension "
       "(depth_0001.exr), as part of the render",
       files=written)
for p in glob.glob(E.out("fileout") + "/*"):
    os.remove(p)
os.rmdir(E.out("fileout"))
os.remove(E.out("composite.exr"))
E.save(channels=chans)
