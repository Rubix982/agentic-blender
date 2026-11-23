"""Building an armature from Python in background mode: edit bones need edit mode; what mode_set needs; what happens to a
zero-length bone; roll; and what the bones read back as in object mode."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy
import exp
from mathutils import Vector
E = exp.Experiment(__file__)

arm = bpy.data.armatures.new("Rig")
rig = bpy.data.objects.new("Rig", arm)
bpy.context.scene.collection.objects.link(rig)

# edit bones outside edit mode
err = None
try:
    arm.edit_bones.new("x")
except Exception as e:
    err = f"{type(e).__name__}: {str(e).strip().splitlines()[0]}"
E.fact("arm.edit_bones.new() outside edit mode fails (edit bones exist only in edit mode)",
       error=err, edit_bones_len_in_object_mode=len(arm.edit_bones))

# mode_set when the armature is not the active object
bpy.context.view_layer.objects.active = None
err = None
try:
    bpy.ops.object.mode_set(mode="EDIT")
except Exception as e:
    err = str(e).strip().splitlines()[0]
E.fact("object.mode_set(mode='EDIT') with no active object fails in background mode", error=err)

# with the armature active it works headless
bpy.context.view_layer.objects.active = rig
r = list(bpy.ops.object.mode_set(mode="EDIT"))
mode = rig.mode
eb = arm.edit_bones
root = eb.new("root"); root.head = (0, 0, 0); root.tail = (0, 0, 1)
up = eb.new("upper"); up.head = (0, 0, 1); up.tail = (0, 0, 2); up.parent = root; up.use_connect = True
zero = eb.new("zero"); zero.head = (1, 0, 0); zero.tail = (1, 0, 0)            # zero length
side = eb.new("side"); side.head = (0, 0, 1); side.tail = (1, 0, 1); side.parent = root
side.roll = 0.5
rolled = round(side.roll, 4)
side2 = eb.new("side_aligned"); side2.head = (0, 0, 1); side2.tail = (1, 0, 1)
side2.align_roll(Vector((0, 0, 1)))       # the bone's Z axis toward world +Z
names_in_edit = [b.name for b in eb]
r2 = list(bpy.ops.object.mode_set(mode="OBJECT"))
names = [b.name for b in arm.bones]
E.fact("with the armature as the active object, mode_set('EDIT') works in background mode and edit bones can be made",
       result=r, mode=mode, back_to_object=r2)
E.fact("a zero-length edit bone is deleted when edit mode is left", in_edit=names_in_edit, after=names)
b = arm.bones["upper"]
E.fact("in object mode the bones read back through arm.bones: head_local, tail_local, parent, use_connect, matrix_local",
       upper_head=list(b.head_local), upper_tail=list(b.tail_local), parent=b.parent.name, connected=b.use_connect,
       side_matrix_local=[list(map(lambda x: round(x, 4), row)) for row in arm.bones["side"].matrix_local])
E.fact("a bone pointing along +X with roll 0.5 rad, and one aligned with align_roll(+Z): their local Z axes",
       roll_set=rolled, side_z_axis=[round(x, 4) for x in arm.bones["side"].matrix_local.col[2][:3]],
       aligned_z_axis=[round(x, 4) for x in arm.bones["side_aligned"].matrix_local.col[2][:3]])
E.fact("pose bones appear for every bone after leaving edit mode, rotation mode QUATERNION by default",
       pose_bones=[p.name for p in rig.pose.bones], rotation_mode=rig.pose.bones["upper"].rotation_mode)

# a temp_override is enough to enter edit mode on a non-active armature
arm2 = bpy.data.armatures.new("Rig2")
rig2 = bpy.data.objects.new("Rig2", arm2)
bpy.context.scene.collection.objects.link(rig2)
bpy.context.view_layer.objects.active = rig
err = None
try:
    with bpy.context.temp_override(active_object=rig2, object=rig2, selected_objects=[rig2], editable_objects=[rig2]):
        r3 = list(bpy.ops.object.mode_set(mode="EDIT"))
        m3 = rig2.mode
        if rig2.mode == "EDIT":
            arm2.edit_bones.new("b").tail = (0, 0, 1)
        bpy.ops.object.mode_set(mode="OBJECT")
except Exception as e:
    r3, m3, err = None, None, str(e).strip().splitlines()[0]
E.fact("mode_set on an armature that is not the active object, through temp_override(active_object=...)",
       result=r3, mode_inside=m3, error=err, bones_made=[b.name for b in arm2.bones], rig_mode=rig.mode)
E.save()
