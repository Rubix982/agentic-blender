"""Motion blur on and off in 4.5: where the switch is (render.use_motion_blur for both engines), how far a moving object
is smeared for a given shutter in EEVEE, Cycles and Workbench, and what it costs in render time. A 1 m white emissive
square moving 1 m per frame, seen from above by an orthographic camera at 32 px per metre."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import time

import bmesh
import bpy
import numpy as np
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene
W, Hh = 256, 64

me = bpy.data.meshes.new("Sq")
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)   # 1 m x 1 m
bm.to_mesh(me); bm.free()
sq = bpy.data.objects.new("Sq", me)
scene.collection.objects.link(sq)
mat = bpy.data.materials.new("Emit"); mat.use_nodes = True
nt = mat.node_tree; nt.nodes.clear()
em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = 1.0
out = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(em.outputs[0], out.inputs["Surface"])
me.materials.append(mat)
sq.location = (-3, 0, 0); sq.keyframe_insert("location", index=0, frame=1)
sq.location = (3, 0, 0); sq.keyframe_insert("location", index=0, frame=7)
for fc in sq.animation_data.action.fcurves:
    for k in fc.keyframe_points:
        k.interpolation = "LINEAR"
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
cam.data.type = "ORTHO"; cam.data.ortho_scale = 8.0
cam.location = (0, 0, 5)
scene.collection.objects.link(cam); scene.camera = cam
world = bpy.data.worlds.new("W"); scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)
world.color = (0, 0, 0)                             # Workbench's background
sh = scene.display.shading                          # Workbench: flat white square
sh.light, sh.color_type, sh.single_color = "FLAT", "SINGLE", (1, 1, 1)
scene.render.resolution_x, scene.render.resolution_y = W, Hh
scene.view_settings.view_transform = "Standard"
scene.render.image_settings.file_format = "PNG"
scene.render.dither_intensity = 0
scene.frame_set(4)                                  # square centred, moving +1 m (32 px) per frame
path = E.out("mb.png")

E.fact("motion blur is one switch for EEVEE and Cycles in 4.5, render.use_motion_blur (off by default), shutter 0.5 "
       "frames centred on the frame; EEVEE adds motion_blur_steps (1) and motion_blur_max (32 px)",
       use_motion_blur=scene.render.use_motion_blur, shutter=scene.render.motion_blur_shutter,
       position=scene.render.motion_blur_position, eevee_steps=scene.eevee.motion_blur_steps,
       eevee_max_px=scene.eevee.motion_blur_max)


def render():
    scene.render.filepath = path
    t = time.time()
    bpy.ops.render.render(write_still=True)
    dt = time.time() - t
    img = bpy.data.images.load(path, check_existing=False)
    px = np.array(img.pixels[:], dtype=np.float32).reshape(img.size[1], img.size[0], 4)
    bpy.data.images.remove(img)
    row = px[Hh // 2, :, 0]
    lit = np.where(row > 0.02)[0]
    return dict(seconds=round(dt, 3), extent_px=int(lit[-1] - lit[0] + 1) if len(lit) else 0,
                partial_px=int(((row > 0.02) & (row < 0.98)).sum()), full_px=int((row >= 0.98).sum()))


res = {}
for eng in ("BLENDER_WORKBENCH", "BLENDER_EEVEE_NEXT", "CYCLES"):
    scene.render.engine = eng
    if eng == "CYCLES":
        dev = exp.metal(scene)
        scene.cycles.samples = 64
        scene.cycles.use_denoising = False
        scene.cycles.use_adaptive_sampling = False
    if eng == "BLENDER_EEVEE_NEXT":
        scene.eevee.taa_render_samples = 64
    for shutter in (None, 0.5, 1.0):
        scene.render.use_motion_blur = shutter is not None
        if shutter:
            scene.render.motion_blur_shutter = shutter
        res[f"{eng} {'off' if shutter is None else shutter}"] = render()
    if eng == "BLENDER_EEVEE_NEXT":
        scene.render.use_motion_blur = True
        scene.render.motion_blur_shutter = 0.5
        scene.eevee.motion_blur_steps = 4
        res[f"{eng} 0.5 steps4"] = render()
        scene.eevee.motion_blur_steps = 1
    print(eng, {k: v for k, v in res.items() if k.startswith(eng)}, flush=True)
scene.render.use_motion_blur = False

E.fact("without motion blur the 1 m square is about 32 px wide in every engine", **{k: v for k, v in res.items()
                                                                                   if k.endswith("off")})
E.fact("with motion blur, shutter 0.5 widens it by about 16 px (half a frame of travel) and shutter 1.0 by about 32 px "
       "in EEVEE and Cycles; Workbench ignores the switch", **{k: v for k, v in res.items() if not k.endswith("off")})
os.remove(path)
E.save(results=res, cycles_device=dev, px_per_m=W / 8.0)
