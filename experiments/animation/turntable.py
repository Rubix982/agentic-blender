"""A turntable camera in 4.5, three ways: a camera parented to an empty whose Z rotation is keyed; Follow Path on a
circle; and a Track To constraint aiming it at the subject. For each: is the angle step even from frame to frame (or
does it ease in and out), does the camera keep looking at the centre, and does the loop close without a repeated frame.
Also: the ways to make keys LINEAR in 4.5's slotted actions, and what a new Track To constraint aims with by default."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import math

import bpy
import numpy as np
from bpy_extras import anim_utils
from mathutils import Vector

import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene
N = 24                                   # frames in one turn; key 0 at frame 1 and 360 at frame N + 1
scene.frame_start, scene.frame_end = 1, N
R, H = 6.0, 2.0


def err(fn):
    try:
        return "ok", fn()
    except Exception as e:  # noqa: BLE001
        return "error", f"{type(e).__name__}: {str(e).strip()[:200]}"


def measure(cam, frames=range(1, N + 2)):
    """Azimuth of the camera about the origin per frame (degrees, unwrapped), its distance from the Z axis, and the
    angle between its view direction and the direction to the origin."""
    az, dist, aim = [], [], []
    for f in frames:
        scene.frame_set(f)
        m = cam.matrix_world
        p = m.translation
        az.append(math.degrees(math.atan2(p.y, p.x)))
        dist.append(math.hypot(p.x, p.y))
        view = -(m.to_3x3() @ Vector((0, 0, 1)))
        to_c = Vector((0, 0, 0)) - p
        aim.append(math.degrees(view.angle(to_c)))
    az = np.degrees(np.unwrap(np.radians(az)))
    steps = np.diff(az)
    return dict(step_first=round(float(steps[0]), 3), step_mid=round(float(steps[N // 2]), 3),
                step_min=round(float(steps.min()), 3), step_max=round(float(steps.max()), 3),
                turn_deg=round(float(az[-1] - az[0]), 2), radius_spread=round(float(max(dist) - min(dist)), 5),
                aim_error_max_deg=round(float(max(aim)), 3))


def channelbag(ob):
    ad = ob.animation_data
    return anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)


def camera(name):
    cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
    scene.collection.objects.link(cam)
    return cam


# ---- 1. Camera parented to an empty, empty's Z rotation keyed 0 -> 360.
pivot = bpy.data.objects.new("Pivot", None)
scene.collection.objects.link(pivot)
cam = camera("CamA")
cam.parent = pivot
cam.location = (R, 0, H)
look = (Vector((0, 0, 0)) - Vector((R, 0, H))).to_track_quat("-Z", "Y")
cam.rotation_euler = look.to_euler()
pivot.rotation_euler.z = 0
pivot.keyframe_insert("rotation_euler", index=2, frame=1)
pivot.rotation_euler.z = 2 * math.pi
pivot.keyframe_insert("rotation_euler", index=2, frame=N + 1)
fc = channelbag(pivot).fcurves.find("rotation_euler", index=2)
default_interp = fc.keyframe_points[0].interpolation
bezier = measure(cam)
E.fact("keyed with keyframe_insert, the empty's rotation eases in and out (BEZIER, the default): the first step is far "
       "smaller than the middle one", interpolation=default_interp, **bezier)

for kp in fc.keyframe_points:
    kp.interpolation = "LINEAR"
linear = measure(cam)
E.fact("setting each key's interpolation to LINEAR through the action's channelbag gives an even step of 360/24 = 15 "
       "degrees, and frame N + 1 equals frame 1, so rendering 1..N loops without a repeated frame", **linear)

# The same F-curve reached three ways in 4.5.
ad = pivot.animation_data
routes = dict(
    legacy_action_fcurves=err(lambda: ad.action.fcurves.find("rotation_euler", index=2) is not None),
    channelbag_helper=err(lambda: anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
                          .fcurves.find("rotation_euler", index=2) is not None),
    layers_strips=err(lambda: ad.action.layers[0].strips[0].channelbag(ad.action_slot)
                      .fcurves.find("rotation_euler", index=2) is not None))
E.fact("in 4.5 the F-curve is reachable through action.fcurves (one slot), anim_utils.action_get_channelbag_for_slot, "
       "and action.layers[0].strips[0].channelbag(slot)", **routes)

# Preference route: keys inserted after setting the user preference.
prefs = bpy.context.preferences.edit
old = prefs.keyframe_new_interpolation_type
prefs.keyframe_new_interpolation_type = "LINEAR"
p2 = bpy.data.objects.new("Pivot2", None)
scene.collection.objects.link(p2)
p2.rotation_euler.z = 0; p2.keyframe_insert("rotation_euler", index=2, frame=1)
p2.rotation_euler.z = 2 * math.pi; p2.keyframe_insert("rotation_euler", index=2, frame=N + 1)
pref_interp = [k.interpolation for k in channelbag(p2).fcurves.find("rotation_euler", index=2).keyframe_points]
prefs.keyframe_new_interpolation_type = old
E.fact("setting preferences.edit.keyframe_new_interpolation_type = 'LINEAR' before keyframe_insert makes linear keys",
       interpolations=pref_interp, default_pref=old)

# Keep turning past N + 1: extrapolation.
scene.frame_set(N * 2 + 1)
const = round(math.degrees(pivot.matrix_world.to_euler().z) % 360, 2)
fc.extrapolation = "LINEAR"
scene.frame_set(N + 1 + N // 4)
lin_ext = round(math.degrees(pivot.rotation_euler.z), 2)
E.fact("past the last key the rotation holds (CONSTANT extrapolation, the default); extrapolation = 'LINEAR' keeps "
       "turning (frame N + 1 + 6 reads 450 degrees)", z_at_2N_plus_1_mod360=const, z_linear_ext=lin_ext)
fc.extrapolation = "CONSTANT"
pivot.hide_render = True

# ---- 2. Follow Path on a circle, eval_time keyed, plus Track To for aim.
cu = bpy.data.curves.new("Circle", "CURVE")
cu.dimensions = "3D"
sp = cu.splines.new("NURBS")
pts = 16
sp.points.add(pts - 1)
for i, p in enumerate(sp.points):
    a = 2 * math.pi * i / pts
    p.co = (R * math.cos(a), R * math.sin(a), H, 1)
sp.use_cyclic_u = True
sp.order_u = 3
circle = bpy.data.objects.new("Circle", cu)
scene.collection.objects.link(circle)
camB = camera("CamB")
fp = camB.constraints.new("FOLLOW_PATH")
fp.target = circle
defaults_fp = dict(use_curve_follow=fp.use_curve_follow, use_fixed_location=fp.use_fixed_location,
                   forward_axis=fp.forward_axis, up_axis=fp.up_axis, path_duration=cu.path_duration,
                   use_path=cu.use_path)
scene.frame_set(1); a1 = camB.matrix_world.translation.copy()
scene.frame_set(50); a50 = camB.matrix_world.translation.copy()
E.fact("a Follow Path constraint alone does not move the camera over time: the curve's eval_time is not animated "
       "(path_duration 100) until it is keyed", moved_between_1_and_50=round((a50 - a1).length, 4), **defaults_fp)
cu.path_duration = N
cu.eval_time = 0; cu.keyframe_insert("eval_time", frame=1)
cu.eval_time = N; cu.keyframe_insert("eval_time", frame=N + 1)
cb = anim_utils.action_get_channelbag_for_slot(cu.animation_data.action, cu.animation_data.action_slot)
for k in cb.fcurves.find("eval_time").keyframe_points:
    k.interpolation = "LINEAR"
tt = camB.constraints.new("TRACK_TO")
tdef = dict(track_axis=tt.track_axis, up_axis=tt.up_axis)
target = bpy.data.objects.new("Target", None)
scene.collection.objects.link(target)
tt.target = target
followpath = measure(camB)
E.fact("Follow Path on a 16-point NURBS circle with eval_time keyed linearly 0 -> path_duration: steps vary with the "
       "curve's parametrisation and the radius wobbles", **followpath)
# Bezier circle instead.
cu2 = bpy.data.curves.new("BCircle", "CURVE"); cu2.dimensions = "3D"
bz = cu2.splines.new("BEZIER"); bz.bezier_points.add(3)
k = 4 / 3 * math.tan(math.pi / 8) * R
for i, bp in enumerate(bz.bezier_points):
    a = math.pi / 2 * i
    c, s_ = math.cos(a), math.sin(a)
    bp.co = (R * c, R * s_, H)
    bp.handle_left = (R * c + k * s_, R * s_ - k * c, H)
    bp.handle_right = (R * c - k * s_, R * s_ + k * c, H)
bz.use_cyclic_u = True
bcircle = bpy.data.objects.new("BCircle", cu2); scene.collection.objects.link(bcircle)
fp.target = bcircle
cu2.path_duration = N
cu2.eval_time = 0; cu2.keyframe_insert("eval_time", frame=1)
cu2.eval_time = N; cu2.keyframe_insert("eval_time", frame=N + 1)
cb2 = anim_utils.action_get_channelbag_for_slot(cu2.animation_data.action, cu2.animation_data.action_slot)
for kk in cb2.fcurves.find("eval_time").keyframe_points:
    kk.interpolation = "LINEAR"
fp_bez = measure(camB)
E.fact("Follow Path on a 4-point Bezier circle, eval_time linear: the step is even only to within the Bezier's speed "
       "variation", **fp_bez)

# ---- 3. Track To alone, defaults: what a new constraint aims with.
camC = camera("CamC")
camC.location = (R, 0, H)
t3 = camC.constraints.new("TRACK_TO"); t3.target = target
scene.frame_set(1)
m = camC.matrix_world
view = -(m.to_3x3() @ Vector((0, 0, 1)))
E.fact("a Track To constraint made with constraints.new aims the camera's -Z at the target with Y up (TRACK_NEGATIVE_Z, "
       "UP_Y), so a camera needs no axis change", track_axis=tdef["track_axis"], up_axis=tdef["up_axis"],
       aim_error_deg=round(math.degrees(view.angle(-m.translation)), 4))

E.save(N=N, radius=R, height=H)
