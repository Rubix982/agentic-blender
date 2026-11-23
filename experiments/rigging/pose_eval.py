"""Posing bones from Python and reading the result: rotation modes, when pose_bone.matrix is up to date, setting a chain's
matrices, and an IK constraint headless."""
import os, sys, math; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy
import numpy as np
import exp
from mathutils import Matrix, Vector, Euler
E = exp.Experiment(__file__)


def rig():
    exp.empty()
    arm = bpy.data.armatures.new("Rig")
    r = bpy.data.objects.new("Rig", arm)
    bpy.context.scene.collection.objects.link(r)
    bpy.context.view_layer.objects.active = r
    bpy.ops.object.mode_set(mode="EDIT")
    a = arm.edit_bones.new("lower"); a.head = (0, 0, 0); a.tail = (0, 0, 1)
    b = arm.edit_bones.new("upper"); b.head = (0, 0, 1); b.tail = (0, 0, 2); b.parent = a; b.use_connect = True
    bpy.ops.object.mode_set(mode="OBJECT")
    return r


def tail_world(r, name):
    return np.round(np.array(r.matrix_world @ r.pose.bones[name].tail), 4).tolist()


# 1. rotation_euler on a QUATERNION bone does nothing; switching the mode converts (and overwrites) the rotation
r = rig()
pb = r.pose.bones["lower"]
mode = pb.rotation_mode
pb.rotation_euler = (math.radians(90), 0, 0)
bpy.context.view_layer.update()
t_euler_ignored = tail_world(r, "upper")
pb.rotation_mode = "XYZ"
euler_after_switch = [round(x, 4) for x in pb.rotation_euler]
bpy.context.view_layer.update()
t_after_switch = tail_world(r, "upper")
pb.rotation_euler = (math.radians(90), 0, 0)
bpy.context.view_layer.update()
t_euler_used = tail_world(r, "upper")
E.fact("a pose bone's rotation_mode is QUATERNION by default, so setting rotation_euler alone does not turn it; "
       "switching rotation_mode to 'XYZ' converts the current rotation (identity) and overwrites the euler set before, "
       "so the euler must be set after the mode",
       default_mode=mode, upper_tail_with_quaternion_mode=t_euler_ignored, euler_after_mode_switch=euler_after_switch,
       upper_tail_after_switch=t_after_switch, upper_tail_euler_set_after_switch=t_euler_used)

# 2. pose_bone.matrix / tail are stale until the depsgraph updates
r = rig()
pb = r.pose.bones["lower"]
pb.rotation_quaternion = Euler((math.radians(90), 0, 0)).to_quaternion()
stale = tail_world(r, "upper")
dg = bpy.context.evaluated_depsgraph_get()     # does fetching the depsgraph update the originals' pose?
after_get = tail_world(r, "upper")
bpy.context.view_layer.update()
fresh = tail_world(r, "upper")
E.fact("after setting a pose bone's rotation, pose_bone.tail/matrix still read the old pose until the depsgraph "
       "is evaluated: view_layer.update() or context.evaluated_depsgraph_get() both bring them up to date", before_update=stale, after_evaluated_depsgraph_get=after_get,
       after_view_layer_update=fresh)

# 3. setting pose_bone.matrix down a chain: with and without an update between parent and child
def set_chain(update_between):
    r = rig()
    target_lower = Matrix.Rotation(math.radians(45), 4, "X")                       # lower bone turned 45 deg about X
    target_upper = Matrix.Translation(target_lower @ Vector((0, 1, 0))) @ Matrix.Rotation(math.radians(90), 4, "X")
    # the bones' rest points along +Y in bone space; in armature space the rest matrix of 'lower' is a -90 X turn
    rest_l = r.data.bones["lower"].matrix_local.copy()
    rest_u = r.data.bones["upper"].matrix_local.copy()
    want_l = target_lower @ rest_l
    want_u = Matrix.Translation((target_lower @ Vector((0, 0, 1)))) @ Matrix.Rotation(math.radians(90), 4, "X") @ \
        Matrix.Translation(-Vector((0, 0, 1))) @ rest_u
    r.pose.bones["lower"].matrix = want_l
    if update_between:
        bpy.context.view_layer.update()
    r.pose.bones["upper"].matrix = want_u
    bpy.context.view_layer.update()
    got = r.pose.bones["upper"].matrix
    return float(np.abs(np.array(got) - np.array(want_u)).max())


E.fact("setting pose_bone.matrix on a parent and then its child: the child lands where asked only if the depsgraph "
       "is updated between the two", error_without_update=round(set_chain(False), 4),
       error_with_update=round(set_chain(True), 4))

# 4. IK constraint headless
r = rig()
bpy.ops.object.empty_add(location=(0, 1.2, 1.2))
tgt = bpy.context.object
ik = r.pose.bones["upper"].constraints.new("IK")
ik.target = tgt
ik.chain_count = 2
bpy.context.view_layer.update()
tip = np.array(r.matrix_world @ r.pose.bones["upper"].tail)
E.fact("an IK constraint added from Python solves in background mode: the chain's tip reaches a reachable target",
       tip=np.round(tip, 4).tolist(), target=list(tgt.location), miss_m=round(float(np.linalg.norm(tip - np.array(tgt.location))), 4))

# 5. reading bone positions: pose_bone.head is armature space, not world
r = rig()
r.location = (5, 0, 0)
bpy.context.view_layer.update()
E.fact("pose_bone.head/tail are in armature (object) space: an armature moved 5 m along X still reports x = 0; "
       "multiply by the object's matrix_world for world space",
       pose_head=list(r.pose.bones["upper"].head), world_head=list(r.matrix_world @ r.pose.bones["upper"].head))
# 6. an object parented to a bone sits at the bone's TAIL, in the bone's frame
r = rig()
bpy.ops.object.empty_add(location=(0, 0, 0))
emp = bpy.context.object
emp.parent = r
emp.parent_type = "BONE"
emp.parent_bone = "lower"
bpy.context.view_layer.update()
at_identity = [round(x, 4) for x in emp.matrix_world.translation]
r.pose.bones["lower"].rotation_quaternion = Euler((math.radians(90), 0, 0)).to_quaternion()
bpy.context.view_layer.update()
after_pose = [round(x, 4) for x in emp.matrix_world.translation]
E.fact("an object parented to a bone (parent_type 'BONE') with an identity parent inverse and location 0 sits at the "
       "bone's tail, not its head, and follows the bone's pose", bone_head=list(r.data.bones["lower"].head_local),
       bone_tail=list(r.data.bones["lower"].tail_local), empty_world=at_identity, empty_after_90deg=after_pose)

# 7. a bone with use_deform off ignores its vertex group
r = rig()
bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2.0, location=(0, 0, 1.0), vertices=12)
cyl = bpy.context.object
for name in ("lower", "upper"):
    vg = cyl.vertex_groups.new(name=name)
    vg.add([v.index for v in cyl.data.vertices if (v.co.z + 1.0 > 1.0) == (name == "upper")], 1.0, "REPLACE")
md = cyl.modifiers.new("Armature", "ARMATURE"); md.object = r
r.pose.bones["upper"].rotation_quaternion = Euler((math.radians(90), 0, 0)).to_quaternion()


def top_y():
    dg = bpy.context.evaluated_depsgraph_get()
    ev = cyl.evaluated_get(dg)
    return round(max(abs((ev.matrix_world @ v.co).y) for v in ev.data.vertices), 4)


moved = top_y()
r.data.bones["upper"].use_deform = False
not_moved = top_y()
E.fact("a bone with use_deform = False does not move the points weighted to it", top_offset_deform_on=moved,
       top_offset_deform_off=not_moved)
E.save()
