"""Shape keys and drivers from Python, headless: where a shape key's animation lives, what the evaluated mesh shows,
a driver from an object and from a bone's rotation (a corrective key), and whether a Python (non-simple) driver
expression runs in a background job started with --factory-startup."""
import os, sys, math; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy
import numpy as np
import exp
E = exp.Experiment(__file__)


def top_z(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    z = max(v.co.z for v in me.vertices)
    ev.to_mesh_clear()
    return round(z, 4)


bpy.ops.mesh.primitive_cube_add(size=2)
ob = bpy.context.object
basis = ob.shape_key_add(name="Basis", from_mix=False)
up = ob.shape_key_add(name="up", from_mix=False)
for i, v in enumerate(ob.data.vertices):
    if v.co.z > 0:
        up.data[i].co.z += 1.0
up.value = 0.5
E.fact("a shape key's value mixes into the evaluated mesh; the mesh's own vertices stay at the basis",
       evaluated_top_z=top_z(ob), mesh_data_top_z=round(max(v.co.z for v in ob.data.vertices), 4),
       key_name=ob.data.shape_keys.name, key_blocks=[k.name for k in ob.data.shape_keys.key_blocks],
       slider_max=up.slider_max)

# keyframing a key's value: the action goes on the Key datablock
up.value = 0.0; up.keyframe_insert("value", frame=1)
up.value = 1.0; up.keyframe_insert("value", frame=11)
key = ob.data.shape_keys
E.fact("keyframing key_block.value puts the action on the Key datablock (mesh.shape_keys.animation_data), "
       "not on the object", object_has_anim=ob.animation_data is not None,
       key_action=key.animation_data.action.name if key.animation_data and key.animation_data.action else None,
       key_slot=key.animation_data.action_slot.identifier if key.animation_data and key.animation_data.action_slot else None,
       data_path=[fc.data_path for fc in key.animation_data.action.layers[0].strips[0].channelbag(key.animation_data.action_slot).fcurves])
bpy.context.scene.frame_set(6)
E.fact("at frame 6 of a 0 -> 1 key over frames 1-11 the key's value and the evaluated mesh follow",
       value=round(up.value, 4), evaluated_top_z=top_z(ob))
key.animation_data_clear()

# driver from an empty's X location
bpy.ops.object.empty_add(location=(0, 0, 0))
ctl = bpy.context.object
fc = up.driver_add("value")
drv = fc.driver
drv.type = "SCRIPTED"
var = drv.variables.new()
var.name = "x"
var.type = "TRANSFORMS"
var.targets[0].id = ctl
var.targets[0].transform_type = "LOC_X"
drv.expression = "x * 0.5"
ctl.location.x = 1.0
bpy.context.view_layer.update()
E.fact("a driver 'x * 0.5' on the key's value from an empty's X location: moving the empty to x = 1 sets the value "
       "to 0.5 after a depsgraph update; it is a 'simple expression' (no Python needed)",
       value=round(up.value, 4), evaluated_top_z=top_z(ob), is_simple_expression=drv.is_simple_expression,
       is_valid=drv.is_valid)

drv.expression = "sum([x, x]) * 0.25"     # needs Python
ctl.location.x = 0.8
bpy.context.view_layer.update()
E.fact("a non-simple (Python) driver expression in this background job started with --factory-startup",
       expression=drv.expression, is_simple_expression=drv.is_simple_expression, value=round(up.value, 4),
       expected=0.4, autoexec=bool(bpy.app.autoexec_fail is False), autoexec_fail=bpy.app.autoexec_fail,
       use_scripts_auto_execute=bpy.context.preferences.filepaths.use_scripts_auto_execute)
up.driver_remove("value")

# corrective key from a bone's rotation
arm = bpy.data.armatures.new("Rig")
rig = bpy.data.objects.new("Rig", arm)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode="EDIT")
b = arm.edit_bones.new("bend"); b.head = (0, 0, 0); b.tail = (0, 0, 1)
bpy.ops.object.mode_set(mode="OBJECT")
fc = up.driver_add("value")
drv = fc.driver
drv.type = "SCRIPTED"
var = drv.variables.new()
var.name = "a"
var.type = "TRANSFORMS"
var.targets[0].id = rig
var.targets[0].bone_target = "bend"
var.targets[0].transform_type = "ROT_X"
var.targets[0].transform_space = "LOCAL_SPACE"
var.targets[0].rotation_mode = "AUTO"
drv.expression = "a / 1.5708"       # 90 degrees -> 1.0
pb = rig.pose.bones["bend"]
vals = {}
for deg in (0, 45, 90):
    pb.rotation_quaternion = (math.cos(math.radians(deg) / 2), math.sin(math.radians(deg) / 2), 0, 0)
    bpy.context.view_layer.update()
    vals[deg] = round(up.value, 4)
E.fact("a corrective-key driver reading a bone's local X rotation (TRANSFORMS, ROT_X, LOCAL_SPACE) follows the bone "
       "set by quaternion", value_by_degrees=vals)
E.save()
