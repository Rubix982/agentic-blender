"""Motion blur in Cycles (and EEVEE) on a moving object: what scene.render.use_motion_blur, motion_blur_shutter and
motion_blur_position do, measured as the length and centre of the smear in a render.

A 0.2 m emissive square moves along +x at 1 m per frame (linear keys: x = -1 at frame 1, +1 at frame 3) and is
rendered at frame 2, where it sits at x = 0, by an orthographic camera (4 m across 128 px: 32 px per metre). The smear's
extent is where alpha > 0.02; its centre is the alpha-weighted mean x."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy  # noqa: E402
import numpy as np  # noqa: E402
import OpenImageIO as oiio  # noqa: E402

import exp  # noqa: E402

E = exp.Experiment(__file__)
scene = bpy.context.scene
device = exp.metal()
scene.cycles.samples = 64
scene.cycles.use_denoising = False
scene.eevee.taa_render_samples = 64
scene.render.film_transparent = True
scene.view_settings.view_transform = "Standard"
R = 128
scene.render.resolution_x = scene.render.resolution_y = R
scene.render.image_settings.file_format = "OPEN_EXR"
scene.render.image_settings.color_depth = "32"
TMP = tempfile.mkdtemp(prefix="bfg-mblur-")

bpy.context.preferences.edit.keyframe_new_interpolation_type = "LINEAR"
bpy.ops.mesh.primitive_plane_add(size=0.2)
sq = bpy.context.object
m = bpy.data.materials.new("e")
m.use_nodes = True
nt = m.node_tree
nt.nodes.clear()
em = nt.nodes.new("ShaderNodeEmission")
out = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(em.outputs[0], out.inputs["Surface"])
sq.data.materials.append(m)
sq.location = (-1, 0, 0)
sq.keyframe_insert("location", frame=1)
sq.location = (1, 0, 0)
sq.keyframe_insert("location", frame=3)
fcs = sq.animation_data.action.fcurves      # the legacy shortcut to the first slot's curves (rigging-animation.md)
interp_with_pref = sorted({k.interpolation for fc in fcs for k in fc.keyframe_points})
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
cam.data.type = "ORTHO"
cam.data.ortho_scale = 4
cam.location = (0, 0, 3)
scene.collection.objects.link(cam)
scene.camera = cam
scene.frame_set(2)
PX = R / cam.data.ortho_scale
defaults = dict(use_motion_blur=scene.render.use_motion_blur, shutter=scene.render.motion_blur_shutter,
                position=scene.render.motion_blur_position, object_use_motion_blur=sq.cycles.use_motion_blur,
                positions=[i.identifier for i in scene.render.bl_rna.properties["motion_blur_position"].enum_items])


def smear(engine="CYCLES", on=True, shutter=0.5, position="CENTER"):
    scene.render.engine = engine
    scene.render.use_motion_blur = on
    scene.render.motion_blur_shutter = shutter
    scene.render.motion_blur_position = position
    p = os.path.join(TMP, "r.exr")
    scene.render.filepath = p
    bpy.ops.render.render(write_still=True)
    a = oiio.ImageBuf(p).get_pixels(oiio.FLOAT)[..., 3]
    os.remove(p)
    col = a.max(axis=0)
    xs = (np.arange(R) + 0.5) / PX - cam.data.ortho_scale / 2
    cov = np.nonzero(col > 0.02)[0]
    prof = a.sum(axis=0)
    return dict(length_m=round(float(xs[cov[-1]] - xs[cov[0]] + 1 / PX), 3),
                centre_x_m=round(float((prof * xs).sum() / prof.sum()), 3), peak_alpha=round(float(a.max()), 3))


bezier = smear()
for fc in fcs:
    for k in fc.keyframe_points:
        k.interpolation = "LINEAR"
linear = smear()
E.fact("keyframe_insert from Python made BEZIER keys although preferences.edit.keyframe_new_interpolation_type was set "
       "to 'LINEAR' first; with those eased keys the square passes frame 2 faster than the 1 m per frame average, and "
       "the shutter-0.5 smear was longer than with LINEAR keys (keyframe_points[i].interpolation = 'LINEAR')",
       interpolation=interp_with_pref, bezier_keys=bezier, linear_keys=linear)
rows = {"off": smear(on=False)}
for sh in (0.5, 1.0, 0.25):
    rows[f"on, shutter {sh}"] = smear(shutter=sh)
E.fact("Cycles motion blur is off in a new file (render.use_motion_blur False, shutter 0.5 frames, position CENTER). "
       "Turned on, the 0.2 m square moving 1 m per frame smeared to about its size + shutter x speed (0.2 + 0.5 = "
       "0.7 m at shutter 0.5, 1.2 m at 1.0; the measured extents include the 1.5 px pixel filter, 0.25 m with no "
       "blur), centred on where it is at the frame", defaults=defaults, square_m=0.2,
       speed_m_per_frame=1.0, **rows)

pos = {p: smear(position=p) for p in ("START", "CENTER", "END")}
E.fact("motion_blur_position moves the shutter interval: START opens it at the frame, so the smear lies ahead of the "
       "frame's position (centre +0.25 m at shutter 0.5), END behind it (-0.25 m), CENTER around it", **pos)

sq.cycles.use_motion_blur = False
obj_off = smear()
sq.cycles.use_motion_blur = True
E.fact("Per object, object.cycles.use_motion_blur = False turns the blur off for that object while the scene's is on",
       **obj_off)

ee = {"off": smear("BLENDER_EEVEE_NEXT", on=False), "on, shutter 0.5": smear("BLENDER_EEVEE_NEXT"),
      "on, shutter 1.0": smear("BLENDER_EEVEE_NEXT", shutter=1.0)}
E.fact("EEVEE reads the same scene.render.use_motion_blur and shutter (scene.eevee.use_motion_blur is gone in 4.5)",
       eevee_has_use_motion_blur=hasattr(scene.eevee, "use_motion_blur"), **ee)

os.rmdir(TMP)
E.save(device=device, px_per_m=PX)
