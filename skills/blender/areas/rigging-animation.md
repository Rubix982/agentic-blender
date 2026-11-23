# Rigging and animation: armatures, weights, poses, actions, shape keys, drivers

Blender 4.5.14 LTS on Apple Silicon. Tags: `[inv]` read from Blender (`scripts/kb.py`), `[exp: path]` measured here,
`[lesson]` from a real project (`kb/lessons/rigging-animation.md`), `[doc: link]` Blender's manual or API reference.

## What goes wrong most often

1. **Setting `rotation_euler` on a pose bone.** Pose bones are QUATERNION by default, so the euler does nothing; and
   switching `rotation_mode` afterwards converts the current rotation, overwriting the euler you set (it read (0, 0, 0))
   `[exp: experiments/rigging/pose_eval.py]`. Set the mode first, or set `rotation_quaternion`.
2. **Reading a pose before Blender has evaluated it.** Right after a pose change, `pose_bone.matrix`, `.head`, `.tail`
   still hold the old pose; `view_layer.update()` (or `context.evaluated_depsgraph_get()`) brings them up to date. Set a
   parent's and then a child's `.matrix` without an update in between and the child misses by 0.71 m
   `[exp: experiments/rigging/pose_eval.py]`.
3. **Trusting FINISHED from `parent_set`.** `bpy.ops.object.parent_set(type='ARMATURE_AUTO')` with the armature active but
   the mesh not selected returned FINISHED and did nothing to the mesh: no groups, no modifier, no parent
   `[exp: experiments/rigging/auto_weights.py]`. Check the groups and that no point is unweighted.
4. **Assuming an action animates whatever it is assigned to.** Since 4.4 actions have slots. Object B given object A's
   action got no slot and did not move until `B.animation_data.action_slot = act.slots["OBA"]`
   `[exp: experiments/rigging/actions_slotted.py]`.
5. **Looking for F-curves only in `action.fcurves`.** In 4.5 it is a legacy shortcut to the first slot's curves
   `[doc: https://docs.blender.org/api/4.5/bpy.types.Action.html]`; the curves live in
   `action.layers[i].strips[j].channelbag(slot).fcurves` `[exp: experiments/rigging/actions_slotted.py]`.
6. **Building bones outside edit mode, or entering it with an override.** `edit_bones.new()` raises in object mode;
   `mode_set(mode='EDIT')` needs the armature to be the view layer's active object, and a
   `temp_override(active_object=...)` does not redirect it: it toggled the real active object instead
   `[exp: experiments/rigging/armature_build.py]`.
7. **Reading pose positions as world positions.** `pose_bone.head`/`.tail` are in armature space; multiply by
   `rig.matrix_world` `[exp: experiments/rigging/pose_eval.py]`.
8. **Weighting to bones that do not deform, or with stray weights.** A bone with `use_deform = False` moves nothing
   `[exp: experiments/rigging/pose_eval.py]`; automatic weights on a real figure leaked onto other limbs and onto a root
   bone that never moves (14,110 points carried root weight) `[lesson]`.
9. **Waiting for bone heat to report the points it left empty.** It did not: loose parts beside a closed tube lost all
   their weight with `FINISHED` and no message (a sphere 1.5 m away, 62 of 62 points; a small cube 10 m away, 8 of 8).
   None of the classic causes tried printed "Bone Heat Weighting: failed to find solution for one or more bones"
   (table below). Count the unweighted points after every `parent_set`.
   `[exp: experiments/rigging/auto_weights_fail.py]`

## Build an armature

From `experiments/rigging/armature_build.py` (background mode):

```python
arm = bpy.data.armatures.new("Rig")
rig = bpy.data.objects.new("Rig", arm)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode="EDIT")
eb = arm.edit_bones
root = eb.new("root"); root.head = (0, 0, 0); root.tail = (0, 0, 1)
up = eb.new("upper"); up.head = (0, 0, 1); up.tail = (0, 0, 2); up.parent = root; up.use_connect = True
side = eb.new("side"); side.head = (0, 0, 1); side.tail = (1, 0, 1); side.parent = root
side.roll = 0.5
side2 = eb.new("side_aligned"); side2.head = (0, 0, 1); side2.tail = (1, 0, 1)
side2.align_roll(Vector((0, 0, 1)))       # the bone's Z axis toward world +Z
bpy.ops.object.mode_set(mode="OBJECT")
```

- A zero-length edit bone (head = tail) is deleted when edit mode is left, silently `[exp: experiments/rigging/armature_build.py]`.
- In object mode read bones through `arm.bones` (`head_local`, `tail_local`, `matrix_local`, `parent`, `use_connect`). A
  bone's Y axis runs head to tail; roll turns X and Z about it: a +X bone with roll 0.5 has local Z (0, -0.479, 0.878),
  and `align_roll((0, 0, 1))` gives (0, 0, 1) `[exp: experiments/rigging/armature_build.py]`.
- Re-aiming a bone by head and tail keeps its old roll; copying a rest pose by direction alone made a figure's elbows bend
  about the wrong axes `[lesson]`. Set roll whenever you move a bone.
- EditBone references die when the mode changes; re-fetch from `arm.bones` or `rig.pose.bones`
  `[doc: https://docs.blender.org/api/4.5/info_gotchas_crashes.html]`.

## Skin a mesh to it

With selection, as the operator expects (`experiments/rigging/auto_weights.py`):

```python
bpy.ops.object.select_all(action="DESELECT")
m.select_set(True); r.select_set(True)
bpy.context.view_layer.objects.active = r
res = list(bpy.ops.object.parent_set(type="ARMATURE_AUTO"))
```

Or with nothing selected, through an override (same result):

```python
with bpy.context.temp_override(active_object=r, object=r, selected_objects=[m, r], selected_editable_objects=[m, r]):
    res = list(bpy.ops.object.parent_set(type="ARMATURE_AUTO"))
```

On a 336-point tube and a two-bone rig both gave groups `lower` and `upper`, 0 unweighted points, an Armature modifier and
the parent; object scale 0.01 or 0.001, a doubled inner shell and a loose cube 3 m away all weighted fully here.
`ARMATURE_ENVELOPE` weighted every point; `ARMATURE_NAME` made empty groups
`[exp: experiments/rigging/auto_weights.py]`. Bone heat works "based on the distance from those vertices to a particular
bone" `[doc: https://docs.blender.org/manual/en/4.5/animation/armatures/skinning/parenting.html]`; on real figures the
project welded seam splits first (heat spreads only over connected surface), turned `use_deform` off on face, toe and
finger helpers, and afterwards stripped weight from points more than 7-8.5 cm from a limb's bones and all root weight
`[lesson]`. Any vertex group whose name matches a bone deforms, so clear an imported mesh's groups first `[lesson]`.

### When bone heat leaves points without weight

The same 336-point tube (2 m, closed) and two-bone rig, changed one way at a time; every case returned `FINISHED`, and
Blender's console output during the call was captured (it does carry operator reports: a bake run the same way printed
its "Info: Baking map saved ..." line) `[exp: experiments/rigging/auto_weights_fail.py]`:

| change | points | unweighted |
|---|---|---|
| none | 336 | 0 |
| size applied to the data: 0.0001, 0.001, 0.01, 100, 1000 (0.2 mm to 2 km tall) | 336 | 0 |
| caps removed (open tube) | 336 | 0 |
| a fin: one edge with 3 faces | 338 | 0 |
| a second tube crossing through it, not joined | 672 | 0 |
| every face split apart (duplicate vertices) | 1312 | 0 |
| a coincident duplicate of the whole surface | 672 | 0 |
| one ring moved onto the next (zero-area faces) | 336 | 0 |
| a loose 0.2 m cube 3 m away, at the tube's base | 344 | 0 |
| the same cube 10, 20, 30 or 50 m away | 344 | 8 (the whole cube) |
| a loose box shell beside the tube (x 1 to 2 m) | 344 | 8 (the whole box) |
| a loose sphere there | 398 | 62 (the whole sphere) |
| the sphere inside the box | 406 | 70 (both) |
| an open strip beside the bones instead of the tube, plus the same sphere, or the cube at 10 or 50 m | 125, 71, 71 | 0 |

None printed "Bone Heat Weighting: failed to find solution for one or more bones", and the tube itself was always fully
weighted. What emptied the loose parts was the closed tube standing between them and the bones: with an open strip in
its place even the cube 50 m away was weighted. On a figure, separate pieces outside a closed body (buttons, straps)
probably come back the same way, with no weight. The 3 m cube kept its weight, probably because its line to the root
bone's head, which sits on the tube's base, does not cross the wall (not tested further).
`[exp: experiments/rigging/auto_weights_fail.py]`

Read the result from the evaluated mesh; the mesh data never moves (top ring at (0, 0, 2) in the data, (0, -1, 1)
evaluated after a 90-degree pose) `[exp: experiments/rigging/auto_weights.py]`:

```python
pb = r.pose.bones["upper"]
pb.rotation_mode = "XYZ"
pb.rotation_euler = (math.radians(90), 0, 0)
dg = bpy.context.evaluated_depsgraph_get()
ev = m.evaluated_get(dg)
after = np.array([ev.matrix_world @ ev.data.vertices[i].co for i in top]).mean(axis=0)
```

## Pose

| what | measured | |
|---|---|---|
| euler set on a QUATERNION bone | no turn: child tail stays (0, 0, 2) | `[exp: experiments/rigging/pose_eval.py]` |
| `rotation_mode = 'XYZ'` after that | euler now (0, 0, 0): converted from the quaternion | same |
| euler set after the mode switch | tail (0, -2, 0) | same |
| tail read right after a rotation | (0, 0, 2), stale | same |
| after `evaluated_depsgraph_get()` or `view_layer.update()` | (0, -2, 0) | same |
| parent then child `.matrix` set, no update between | child off by 0.707 m; with an update 0.0 | same |
| armature moved 5 m: `pose_bone.head` | x = 0 (armature space); `matrix_world @ head` x = 5 | same |
| empty parented to a bone (`parent_type='BONE'`, identity inverse) | sits at the bone's tail (0, 0, 1), follows its pose | same |
| `use_deform = False` on a weighted bone | its points do not move (0.1 m vs 1.0 m offset) | same |
| IK constraint, chain 2, reachable target | tip on target, 0.0 mm | same |

An IK constraint from Python (`experiments/rigging/pose_eval.py`):

```python
bpy.ops.object.empty_add(location=(0, 1.2, 1.2))
tgt = bpy.context.object
ik = r.pose.bones["upper"].constraints.new("IK")
ik.target = tgt
ik.chain_count = 2
bpy.context.view_layer.update()
```

For a whole clip, setting `pose_bone.matrix` bone by bone (with updates) is slow; compute each bone's basis
(`(parent_pose @ parent.matrix_local.inverted() @ bone.matrix_local).inverted() @ target`), set `rotation_quaternion`
and key it: a 300-frame retarget took seconds, and the project's own forward kinematics matched Blender's to 0.0 mm
`[lesson]`. To parent an object to a bone where it already is:
`o.matrix_parent_inverse = (rig.matrix_world @ pb.matrix @ Matrix.Translation((0, pb.length, 0))).inverted()`
`[lesson]`. Motion capture (BVH) needs Y-up to Z-up, rate, rest-pose and floor conversion, and feet retargeted by IK to the
actor's scaled ankle path (joint angles alone slid a planted heel 45 cm) `[lesson]`.

## Keyframes and actions (slotted, 4.4+)

`keyframe_insert` makes a layered action with one slot, one layer, one keyframe strip
`[exp: experiments/rigging/actions_slotted.py]`:

```python
ob.location = (0, 0, 0); ob.keyframe_insert("location", frame=1)
ob.location = (1, 2, 3); ob.keyframe_insert("location", frame=11)
ad = ob.animation_data
act = ad.action                     # "CubeAction"
slot = ad.action_slot               # identifier "OBCube": "OB" + the name
cb = act.layers[0].strips[0].channelbag(slot)
fc = cb.fcurves.find("location", index=1)
fc.evaluate(6)                      # 1.0, without changing the scene; keys are BEZIER by default
```

`action.fcurves` gave the same three curves here (one slot); it is "a legacy API that is unaware of action slots, and
will only consider the F-Curves for this action's first slot" `[doc: https://docs.blender.org/api/4.5/bpy.types.ActionFCurves.html]`.
`bpy_extras.anim_utils.action_get_channelbag_for_slot` exists in 4.5; `action_ensure_channelbag_for_slot` does not
`[exp: experiments/rigging/actions_slotted.py]`.

Build an action by hand, the slotted way (z reached 5.0 at frame 25; assigning the action picked its one slot):

```python
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
```

`action.fcurves.new()` on an empty action also works: it makes a layer and a slot named "Legacy Slot"
(`OBLegacy Slot` once assigned), and an object assigned that action animated `[exp: experiments/rigging/actions_slotted.py]`.

**Sharing an action.** Object B assigned object A's action got `action_slot = None` (A's slot was in
`action_suitable_slots`) and stayed put; setting the slot made it follow A's curves to the same absolute location; keying B
with the slot cleared added a second slot to the action `[exp: experiments/rigging/actions_slotted.py]`:

```python
B.animation_data_create()
B.animation_data.action = act
B.animation_data.action_slot = act.slots["OBA"]
```

**Many keys.** 1,000 keys by `keyframe_insert` took 0.022 s; by bulk add 0.0002 s
`[exp: experiments/rigging/actions_slotted.py]`:

```python
fc.keyframe_points.clear()
fc.keyframe_points.add(n)
co = np.empty(2 * n)
co[0::2] = np.arange(1, n + 1)
co[1::2] = np.arange(n) * 0.01
fc.keyframe_points.foreach_set("co", co)
fc.update()
```

## Shape keys

From `experiments/rigging/shapekeys_drivers.py`:

```python
basis = ob.shape_key_add(name="Basis", from_mix=False)
up = ob.shape_key_add(name="up", from_mix=False)
for i, v in enumerate(ob.data.vertices):
    if v.co.z > 0:
        up.data[i].co.z += 1.0
up.value = 0.5
up.value = 0.0; up.keyframe_insert("value", frame=1)
up.value = 1.0; up.keyframe_insert("value", frame=11)
```

- The mix shows in the evaluated mesh (top at z = 1.5 at value 0.5); `ob.data.vertices` stay at the basis (1.0).
- The key's animation is on the Key datablock: `ob.data.shape_keys.animation_data.action`, slot `KEKey`, curve
  `key_blocks["up"].value`; the object has no animation data `[exp: experiments/rigging/shapekeys_drivers.py]`.
- Shape keys block applying modifiers and cutting the mesh; bake the mix in with
  `bpy.ops.object.shape_key_remove(all=True, apply_mix=True)` `[lesson]`.

## Drivers

A driver from an empty's X location, and a corrective key from a bone's rotation
(`experiments/rigging/shapekeys_drivers.py`):

```python
fc = up.driver_add("value")
drv = fc.driver
drv.type = "SCRIPTED"
var = drv.variables.new()
var.name = "x"
var.type = "TRANSFORMS"
var.targets[0].id = ctl
var.targets[0].transform_type = "LOC_X"
drv.expression = "x * 0.5"

# corrective key: the bone's local X rotation, 90 degrees -> 1.0
up.driver_remove("value")
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
drv.expression = "a / 1.5708"
```

| expression | `is_simple_expression` | result | |
|---|---|---|---|
| `x * 0.5`, empty at x = 1 | True | 0.5 | `[exp: experiments/rigging/shapekeys_drivers.py]` |
| `sum([x, x]) * 0.25`, x = 0.8 | False | 0.4 in a fresh `-b --factory-startup` session | same |
| `a / 1.5708`, bone at 0 / 45 / 90 degrees | True | 0.0 / 0.5 / 1.0 | same |

Driven values update after `view_layer.update()`. Simple expressions (arithmetic, comparisons, `min`, `max`, `sin`,
`clamp`, `lerp`, ...) "are evaluated even when Python script execution is disabled"
`[doc: https://docs.blender.org/manual/en/4.5/animation/drivers/drivers_panel.html]`; a Python-only expression in a file
opened headless read 0 without `-y` `[exp: experiments/running/cli_behaviour.py]` (see `running.md`).

## Reference

| need | call | evidence |
|---|---|---|
| enter edit mode on an armature | `view_layer.objects.active = rig; bpy.ops.object.mode_set(mode='EDIT')` | `[exp: experiments/rigging/armature_build.py]` |
| automatic weights | mesh selected, rig active and selected, `parent_set(type='ARMATURE_AUTO')` | `[exp: experiments/rigging/auto_weights.py]` |
| a pose bone's world head | `rig.matrix_world @ pb.head` after `view_layer.update()` | `[exp: experiments/rigging/pose_eval.py]` |
| an action's curves | `act.layers[0].strips[0].channelbag(slot).fcurves` | `[exp: experiments/rigging/actions_slotted.py]` |
| make an object use an action | `ad.action = act; ad.action_slot = act.slots[...]` | same |
| shape-key animation | `ob.data.shape_keys.animation_data` | `[exp: experiments/rigging/shapekeys_drivers.py]` |
| a driver | `prop_owner.driver_add("prop")`, variables, `expression` | same |
| pose bone defaults | `rotation_mode` QUATERNION | `[exp: experiments/rigging/armature_build.py]` |

Project lessons behind this page, including MPFB figures (helper geometry inside the skin, the `body` group, rig axes) and
motion capture: `kb/lessons/rigging-animation.md`.
