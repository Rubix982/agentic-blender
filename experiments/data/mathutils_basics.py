"""mathutils in 4.5: the @ operator, building and decomposing matrices, rotations, and transforming points vs directions."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import math
import bpy
from mathutils import Vector, Matrix, Quaternion, Euler
import exp
E = exp.Experiment(__file__)

M = Matrix.Translation((1, 2, 3))
v = Vector((1, 0, 0))
try:
    r = M * v; star = f"accepted: {tuple(r)}"
except Exception as e:
    star = f"{type(e).__name__}: {e}"
E.fact("matrix * vector raises in 2.8+; use matrix @ vector", star=star, at=tuple(M @ v))
E.fact("vector * vector is element-wise; dot and cross are methods", elementwise=tuple(Vector((1, 2, 3)) * Vector((2, 2, 2))),
       dot=Vector((1, 2, 3)).dot(Vector((2, 2, 2))), cross=tuple(Vector((1, 0, 0)).cross(Vector((0, 1, 0)))))

R = Matrix.Rotation(math.radians(90), 4, "Z")
S = Matrix.Diagonal((2, 2, 2, 1))
TRS = M @ R @ S
p = TRS @ Vector((1, 0, 0))
E.fact("T @ R @ S applies scale first, then rotation, then translation", point=tuple(round(x, 4) for x in p))
lrs = Matrix.LocRotScale(Vector((1, 2, 3)), Euler((0, 0, math.radians(90))), Vector((2, 2, 2)))
E.fact("Matrix.LocRotScale(loc, rot, scale) builds the same matrix", same=all(abs(a - b) < 1e-6 for ra, rb in zip(lrs, TRS) for a, b in zip(ra, rb)))
loc, rot, sca = TRS.decompose()
E.fact("matrix.decompose() returns (Vector, Quaternion, Vector)", loc=tuple(loc), rot_euler_deg=tuple(round(math.degrees(a), 3) for a in rot.to_euler()),
       scale=tuple(round(x, 4) for x in sca), types=[type(loc).__name__, type(rot).__name__, type(sca).__name__])
# directions: use the 3x3 part (no translation); normals: inverse transpose
d = Vector((1, 0, 0))
E.fact("a direction must be transformed by matrix.to_3x3() (a 4x4 @ 3D vector also translates it)",
       with_4x4=tuple(round(x, 4) for x in TRS @ d), with_3x3=tuple(round(x, 4) for x in TRS.to_3x3() @ d))
NS = Matrix.Diagonal((1, 4, 1, 1))
n = Vector((1, 1, 0)).normalized()
wrong = (NS.to_3x3() @ n).normalized()
right = (NS.to_3x3().inverted().transposed() @ n).normalized()
E.fact("under non-uniform scale, normals must use the inverse-transpose; the plain 3x3 gives a different (wrong) normal",
       plain=tuple(round(x, 4) for x in wrong), inverse_transpose=tuple(round(x, 4) for x in right))

# Euler order, quaternion
e = Euler((math.radians(90), 0, math.radians(90)), "XYZ")
q = e.to_quaternion()
E.fact("Euler defaults to order XYZ; to_quaternion / to_matrix convert", order=e.order, quat=tuple(round(x, 4) for x in q))
q1 = Quaternion((0, 0, 1), 0); q2 = Quaternion((0, 0, 1), math.radians(90))
E.fact("Quaternion(axis, angle) and slerp", half=tuple(round(math.degrees(a), 3) for a in q1.slerp(q2, 0.5).to_euler()))
# object rotation modes
bpy.ops.object.empty_add(); ob = bpy.context.object
E.fact("a new object uses rotation_mode XYZ; setting rotation_quaternion has no effect until rotation_mode='QUATERNION'",
       rotation_mode=ob.rotation_mode)
ob.rotation_quaternion = q2; bpy.context.view_layer.update()
before = tuple(round(x, 3) for x in ob.matrix_world.to_euler())
ob.rotation_mode = "QUATERNION"; bpy.context.view_layer.update()
after = tuple(round(x, 3) for x in ob.matrix_world.to_euler())
q_after_switch = tuple(round(x, 4) for x in ob.rotation_quaternion)
ob.rotation_quaternion = q2; bpy.context.view_layer.update()
after_set = tuple(round(x, 3) for x in ob.matrix_world.to_euler())
E.fact("rotation_quaternion is ignored under XYZ mode; switching rotation_mode converts the CURRENT rotation into the new mode, overwriting the quaternion you set before; set rotation_mode first, then the value",
       under_xyz=before, after_switch=after, quaternion_after_switch=q_after_switch, after_setting_again=after_set)
# matrix_world assignment and matrix_basis
ob.matrix_world = TRS; bpy.context.view_layer.update()
E.fact("assigning obj.matrix_world sets location/rotation/scale from it", location=tuple(ob.location), scale=tuple(round(x, 4) for x in ob.scale))
# to_track_quat: point -Z at a target (camera convention)
direction = Vector((0, 0, 0)) - Vector((5, -5, 5))
qt = direction.to_track_quat("-Z", "Y")
E.fact("direction.to_track_quat('-Z', 'Y') aims an object's -Z axis (a camera's view axis) along direction",
       check=tuple(round(x, 4) for x in (qt.to_matrix() @ Vector((0, 0, -1)))), direction_normalized=tuple(round(x, 4) for x in direction.normalized()))
# copies: Vector from object is a live reference
loc_ref = ob.location
loc_copy = ob.location.copy()
ob.location.x = 42
E.fact("obj.location returns a live wrapper; keep .copy() if you need the old value", ref_x=loc_ref.x, copy_x=loc_copy.x)
# freeze for dict keys
try:
    {Vector((1, 2, 3)): 1}; h = "hashable"
except TypeError as e:
    h = f"TypeError: {e}"
E.fact("a Vector is not hashable until .freeze()", plain=h, frozen=hash(Vector((1, 2, 3)).freeze()) is not None)
E.save()
