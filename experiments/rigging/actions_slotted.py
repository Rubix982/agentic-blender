"""Keyframes and F-curves in 4.5's slotted (layered) actions: what keyframe_insert makes, what action.fcurves does,
the channelbag route, making an action from scratch, sharing one action between two objects, and the fast path for many
keys."""
import os, sys, time; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy
import numpy as np
import exp
E = exp.Experiment(__file__)


def err_of(fn):
    try:
        return ("ok", fn())
    except Exception as e:
        return ("error", f"{type(e).__name__}: {str(e).strip().splitlines()[0]}")


# 1. keyframe_insert
bpy.ops.mesh.primitive_cube_add()
ob = bpy.context.object
ob.location = (0, 0, 0); ob.keyframe_insert("location", frame=1)
ob.location = (1, 2, 3); ob.keyframe_insert("location", frame=11)
ad = ob.animation_data
act = ad.action
slot = ad.action_slot
E.fact("keyframe_insert makes a layered action with one slot, one layer and one keyframe strip",
       action=act.name, is_layered=act.is_action_layered, is_legacy=act.is_action_legacy,
       slots=[(s.identifier, s.name_display, s.target_id_type) for s in act.slots],
       assigned_slot=slot.identifier if slot else None, layers=len(act.layers),
       strips=[st.type for st in act.layers[0].strips])
cb = act.layers[0].strips[0].channelbag(slot)
E.fact("the F-curves live in the strip's channelbag for the slot: strip.channelbag(slot).fcurves",
       fcurves=[(fc.data_path, fc.array_index) for fc in cb.fcurves],
       groups=[g.name for g in cb.groups])
legacy = err_of(lambda: [(fc.data_path, fc.array_index) for fc in act.fcurves])
E.fact("action.fcurves still works in 4.5 on a one-slot action (it reads the first slot's channelbag)",
       result=legacy)
fc = cb.fcurves.find("location", index=1)
E.fact("an F-curve evaluates at any frame without changing the scene; new keys are BEZIER by default",
       y_at_6=round(fc.evaluate(6), 4), interpolation=fc.keyframe_points[0].interpolation,
       pref_default=bpy.context.preferences.edit.keyframe_new_interpolation_type)
bpy.context.scene.frame_set(6)
E.fact("frame_set applies the action to the object", location_at_6=[round(x, 4) for x in ob.location])

ba = err_of(lambda: hasattr(__import__("bpy_extras.anim_utils", fromlist=["x"]), "action_get_channelbag_for_slot"))
be = err_of(lambda: hasattr(__import__("bpy_extras.anim_utils", fromlist=["x"]), "action_ensure_channelbag_for_slot"))
E.fact("bpy_extras.anim_utils has the channelbag helpers", get_helper=ba, ensure_helper=be)

# 2. an action from scratch
exp.empty()
bpy.ops.mesh.primitive_cube_add()
ob = bpy.context.object
a2 = bpy.data.actions.new("Made")
r_legacy_new = err_of(lambda: a2.fcurves.new("location", index=2).data_path)
E.fact("action.fcurves.new() on a new, empty action in 4.5",
       result=r_legacy_new, layers_after=len(a2.layers), slots_after=[s.identifier for s in a2.slots],
       is_layered=a2.is_action_layered, is_legacy=a2.is_action_legacy)

fz = a2.fcurves[0]
fz.keyframe_points.insert(1, 0.0); fz.keyframe_points.insert(25, 2.0)
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0)); obL = bpy.context.object
obL.animation_data_create()
obL.animation_data.action = a2
slotL = obL.animation_data.action_slot
bpy.context.scene.frame_set(25)
E.fact("an action made through action.fcurves.new(), assigned to an object: which slot the object gets and whether it moves",
       slot=slotL.identifier if slotL else None, z_at_25=round(obL.location.z, 4),
       slot_after=a2.slots[0].identifier, target_id_type=a2.slots[0].target_id_type)
bpy.context.scene.frame_set(1)

a3 = bpy.data.actions.new("MadeLayered")
s3 = a3.slots.new(id_type="OBJECT", name="Cube")
lay = a3.layers.new("Layer")
strip = lay.strips.new(type="KEYFRAME")
cb3 = strip.channelbag(s3, ensure=True)
fcz = cb3.fcurves.new("location", index=2)
fcz.keyframe_points.insert(1, 0.0)
fcz.keyframe_points.insert(25, 5.0)
ob.animation_data_create()
ob.animation_data.action = a3
auto_slot = ob.animation_data.action_slot
if auto_slot is None:
    ob.animation_data.action_slot = s3
bpy.context.scene.frame_set(25)
E.fact("an action built by hand (slots.new, layers.new, strips.new, channelbag(slot, ensure=True), fcurves.new) "
       "drives the object once assigned; assigning the action picks its slot automatically when there is one",
       slot_identifier=s3.identifier, auto_assigned_slot=auto_slot.identifier if auto_slot else None,
       z_at_25=round(ob.location.z, 4))

# 3. two objects sharing one action
exp.empty()
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0)); A = bpy.context.object; A.name = "A"
bpy.ops.mesh.primitive_cube_add(location=(3, 0, 0)); B = bpy.context.object; B.name = "B"
A.keyframe_insert("location", frame=1)
A.location.z = 2; A.keyframe_insert("location", frame=10)
act = A.animation_data.action
B.animation_data_create()
B.animation_data.action = act
sB = B.animation_data.action_slot
bpy.context.scene.frame_set(10)
E.fact("assigning A's action to B: which slot B gets, and whether B moves",
       slots=[s.identifier for s in act.slots], B_slot=sB.identifier if sB else None,
       B_suitable=[s.identifier for s in B.animation_data.action_suitable_slots],
       B_location=[round(x, 3) for x in B.location])
B.animation_data.action_slot = act.slots["OBA"]
bpy.context.scene.frame_set(1); bpy.context.scene.frame_set(10)
E.fact("setting B.animation_data.action_slot to A's slot makes B follow A's curves (to the same absolute location)",
       B_slot=B.animation_data.action_slot.identifier, B_location=[round(x, 3) for x in B.location])
B.animation_data.action_slot = None
B.keyframe_insert("location", frame=1)
E.fact("keying B afterwards adds a second slot to the shared action",
       slots=[s.identifier for s in act.slots], B_slot=B.animation_data.action_slot.identifier,
       legacy_fcurves=err_of(lambda: len(act.fcurves)))

# 4. many keys: keyframe_insert loop vs keyframe_points.add + foreach_set
exp.empty()
bpy.ops.mesh.primitive_cube_add(); ob = bpy.context.object
n = 1000
t = time.time()
for f in range(n):
    ob.location.x = f * 0.01
    ob.keyframe_insert("location", index=0, frame=f + 1)
t_insert = time.time() - t
bpy.ops.mesh.primitive_cube_add(); ob2 = bpy.context.object
ob2.keyframe_insert("location", index=0, frame=1)
cb = ob2.animation_data.action.layers[0].strips[0].channelbag(ob2.animation_data.action_slot)
fc = cb.fcurves.find("location", index=0)
t = time.time()
fc.keyframe_points.clear()
fc.keyframe_points.add(n)
co = np.empty(2 * n)
co[0::2] = np.arange(1, n + 1)
co[1::2] = np.arange(n) * 0.01
fc.keyframe_points.foreach_set("co", co)
fc.keyframe_points.foreach_set("interpolation", [2] * n) if False else None
fc.update()
t_bulk = time.time() - t
E.fact("1,000 keys: a keyframe_insert loop against keyframe_points.add + foreach_set('co') + update()",
       insert_loop_s=round(t_insert, 3), bulk_s=round(t_bulk, 4), bulk_value_at_500=round(fc.evaluate(500), 4))
E.save()
