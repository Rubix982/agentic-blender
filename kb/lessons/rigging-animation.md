# Lessons: armatures, weights, poses, motion capture, actions

From a project that built human figures with MPFB (the MakeHuman add-on for Blender), rigged and posed them from photos
and motion capture, and dressed them in cloth, on Blender 4.5.14; and from experiments in this repository. Numbers are
the project's unless a line says "Re-checked here".

## Building and posing

### Edit bones exist only in edit mode, and mode_set needs the armature to be the real active object
**What happens:** `armature.edit_bones.new()` outside edit mode raises; `bpy.ops.object.mode_set(mode='EDIT')` works in
background mode once the armature is the view layer's active object. A `temp_override(active_object=...)` does not
redirect it.
**Evidence:** Re-checked here `[exp: experiments/rigging/armature_build.py]`: in object mode "RuntimeError: Error:
Armature 'Rig' not in edit mode, cannot add an editbone"; with no active object "Operator bpy.ops.object.mode_set.poll()
Context missing active object"; with `view_layer.objects.active = rig`, FINISHED and bones made. With another armature
active and `temp_override(active_object=rig2, object=rig2, ...)`, mode_set reported FINISHED, rig2 stayed in OBJECT mode
(no bone could be added to it) and the real active armature was left in EDIT mode.
**What to do:** `bpy.context.view_layer.objects.active = rig; bpy.ops.object.mode_set(mode='EDIT')`, build, then
`mode_set(mode='OBJECT')`. Do not keep EditBone references after leaving edit mode.
**How it was found:** measured here.

### A zero-length bone is deleted when edit mode is left
**What happens:** an edit bone whose head equals its tail disappears on the switch back to object mode, silently.
**Evidence:** Re-checked here `[exp: experiments/rigging/armature_build.py]`: bones in edit mode
`[root, upper, zero, side, side_aligned]`; after `mode_set('OBJECT')`, `[root, upper, side, side_aligned]`.
**What to do:** give every bone a length; check `len(arm.bones)` after building.
**How it was found:** measured here.

### Roll decides a bone's local axes; setting a bone by direction alone keeps the old roll
**What happens:** a bone's Y axis runs head to tail; its X and Z axes turn about Y by the roll. Re-aiming a bone by its
direction only (head and tail) keeps whatever roll it had, so hinges then bend about the wrong axes.
**Evidence:** copying a rest pose from another figure by bone direction only made elbows and wrists bend about the wrong
axes (forearms reached out palm up); copying the full orientation, roll included, fixed it. Re-checked here
`[exp: experiments/rigging/armature_build.py]`: a bone along +X with `roll = 0.5` has its local Z at (0, -0.479, 0.878);
`align_roll((0, 0, 1))` gives (0, 0, 1).
**What to do:** set roll explicitly (`edit_bone.roll`, or `edit_bone.align_roll(vector)` to point local Z), and re-set it
after moving a head or tail.
**How it was found:** pose fits whose elbows bent sideways.

### A pose bone's rotation_mode is QUATERNION, and switching the mode overwrites the euler you set
**What happens:** new pose bones use quaternions, so setting `rotation_euler` alone does nothing. Changing
`rotation_mode` converts the current rotation into the new representation, overwriting any euler set before the switch.
**Evidence:** Re-checked here `[exp: experiments/rigging/pose_eval.py]`: euler 90 degrees on a QUATERNION bone: the
child's tail stayed at (0, 0, 2); after `rotation_mode = 'XYZ'` the euler read (0, 0, 0) and the tail was still at
(0, 0, 2); setting the euler again after the switch moved it to (0, -2, 0).
**What to do:** set `rotation_mode` first, then the rotation; or set `rotation_quaternion`.
**How it was found:** measured here.

### Pose matrices are stale until the depsgraph is evaluated; set a chain parent first, updating between bones
**What happens:** after changing a pose bone, `pose_bone.matrix`, `.head` and `.tail` still read the old pose until
`view_layer.update()` (or `context.evaluated_depsgraph_get()`) runs. Setting `pose_bone.matrix` on a child is computed
against its parent's current (possibly stale) matrix.
**Evidence:** Re-checked here `[exp: experiments/rigging/pose_eval.py]`: the tail read (0, 0, 2) right after the rotation,
(0, -2, 0) after either call. Setting a parent's and then its child's `.matrix` to targets: the child missed by 0.707 m
without an update between them, 0.0 with one. The project set every bone of a rest change in POSE mode, parents first
(sorted by `len(bone.parent_recursive)`), with `view_layer.update()` after each.
**What to do:** update between bones; for whole clips, compute each bone's basis yourself instead (next lesson).
**How it was found:** measured here; the project's rest-pose copier.

### Key whole clips by computing each bone's basis, not by setting pose matrices bone by bone
**What happens:** setting `pose_bone.matrix` needs a scene update between parent and child, which is slow over hundreds of
frames and bones.
**Evidence:** computing `basis = (parent_pose @ parent.matrix_local.inverted() @ bone.matrix_local).inverted() @ target`
per bone in Python, then setting `rotation_quaternion` (and the root's `location`) and `keyframe_insert` per frame,
retargeted a 300-frame clip in seconds. The project's own forward kinematics matched Blender's evaluation to 0.0 mm.
(not re-checked here)
**What to do:** as above.
**How it was found:** retargeting motion capture.

### pose_bone.head and .tail are in armature space
**What happens:** they do not include the armature object's transform.
**Evidence:** Re-checked here `[exp: experiments/rigging/pose_eval.py]`: an armature moved 5 m along X still reported the
bone head at x = 0; `rig.matrix_world @ pose_bone.head` gave x = 5.
**What to do:** multiply by `rig.matrix_world` for world positions.
**How it was found:** measured here.

### An object parented to a bone hangs from the bone's tail, in the bone's frame
**What happens:** with `parent_type = 'BONE'`, the child's origin is relative to the bone's tail, with the bone's axes. A
naive parent inverse places it wrongly.
**Evidence:** Re-checked here `[exp: experiments/rigging/pose_eval.py]`: an empty at location 0 parented to a bone from
(0, 0, 0) to (0, 0, 1), identity parent inverse: at (0, 0, 1), the tail; after a 90-degree pose, at (0, -1, 0). The project's
hair cards were left behind when the head turned until parented this way.
**What to do:** `o.parent = rig; o.parent_type = 'BONE'; o.parent_bone = name;
o.matrix_parent_inverse = (rig.matrix_world @ pb.matrix @ Matrix.Translation((0, pb.length, 0))).inverted()`; or set the
parent fields, `view_layer.update()`, and re-assign the `matrix_world` you saved. Re-take the inverse after any rest change.
**How it was found:** hair that did not follow the head.

### An object parented to a rig that is not in the scene has a stale matrix_world
**What happens:** objects loaded from another .blend but not linked into the scene are never evaluated, so a child's world
matrix reads its parent's unevaluated state.
**Evidence:** hair carried from one figure to another landed with its crown 20 cm over the scalp and 17 % too long.
(not re-checked here)
**What to do:** link the source rig into the scene and `view_layer.update()` before reading or unparenting the child.
**How it was found:** hair measured on the new figure.

### An IK constraint made from Python solves headless; its targets are points, not rays
**What happens:** a constraint added with `pose_bone.constraints.new('IK')` and `chain_count` works in background mode.
Blender's IK reaches 3D points; aiming a limb so it projects onto a photo's 2D keypoint (a ray from the camera) is not
something it solves.
**Evidence:** Re-checked here `[exp: experiments/rigging/pose_eval.py]`: a two-bone chain reached a target at
(0, 1.2, 1.2) to 0.0 mm. The project fitted arms to photo keypoints with its own ray solver. (re-checked for the first part)
**What to do:** use IK for 3D targets; for 2D targets write the solve.
**How it was found:** pose fitting from photos.

### Changing a rig's rest pose: apply the armature, then armature_apply
**What happens:** an armature deforms by the change from rest; a new rest needs the mesh baked into the posed shape and the
pose made the rest.
**Evidence:** the project's sequence: set `pb.matrix` with full orientation (roll included) parents first, updating after
each; remove shape keys (`shape_key_remove(all=True, apply_mix=True)`); apply the Armature modifier with other modifiers
off; `bpy.ops.pose.armature_apply(selected=False)`; re-add the Armature modifier, re-bind Corrective Smooth, re-take
bone-parent inverses. `armature.pose_position = 'REST'` reads the rest pose without clearing the pose. New bones and
weights added to a posed rig must be made in rest space. (not re-checked here)
**What to do:** as above.
**How it was found:** re-resting figures into an A-pose for draping.

## Weights

### parent_set(type='ARMATURE_AUTO') works headless with the mesh selected and the armature active
**What happens:** automatic (bone heat) weights run in background mode when the mesh is selected and the armature is
active and selected, or when a context override supplies the same. With the mesh not selected, it does nothing to it and
still reports FINISHED.
**Evidence:** Re-checked here `[exp: experiments/rigging/auto_weights.py]`: a 336-point tube on a two-bone rig: FINISHED,
groups `lower`, `upper`, 0 unweighted points, an Armature modifier and the parent set. With nothing selected,
`temp_override(active_object=rig, object=rig, selected_objects=[mesh, rig], selected_editable_objects=[mesh, rig])` did
the same. With the rig active but the mesh unselected: FINISHED, no groups, no modifier, no parent. The tube at object
scale 0.01 and 0.001, with a doubled inner shell, and with a loose cube 3 m away all weighted fully (no heat failure
reproduced). ARMATURE_ENVELOPE weighted every point; ARMATURE_NAME made empty groups.
**What to do:** select the mesh, make the armature active and selected (or override), then check the groups and that no
point is unweighted; never trust FINISHED alone.
**How it was found:** measured here.

### Bone heat needs one connected surface and only deforming bones
**What happens:** heat spreads only over connected surface, so a mesh split at texture seams weights badly; many tiny
helper bones (face, toes, fingers) make the solve fail.
**Evidence:** the project welded seam splits (`bmesh.ops.remove_doubles(dist=0.0002)`), recalculated normals and set
`bone.use_deform = False` on face, toe and finger helpers before `ARMATURE_AUTO`. (not re-checked here; the failure did
not reproduce on the simple cases above)
**What to do:** as above.
**How it was found:** weighting a downloaded figure.

### A bone with use_deform off ignores its vertex group
**What happens:** weights to a non-deforming bone move nothing.
**Evidence:** hands that never curled: the rig's finger bones were non-deforming and the body had no finger groups (37
groups, none for fingers). Re-checked here `[exp: experiments/rigging/pose_eval.py]`: a cylinder's top weighted to
`upper`, the bone turned 90 degrees: top offset 1.0 m with `use_deform` on, 0.1 m (unmoved) with it off.
**What to do:** set `bone.use_deform = True` on bones you weight to; weight fingers to the nearest hand bone if the body
has none.
**How it was found:** stiff, splayed hands in every pose.

### Automatic weights leak onto nearby limbs, and onto a root that never moves
**What happens:** points near another limb take some of its weight (invisible at rest, wings when the limb moves); weight
on the root bone, which never moves, holds points partly at the rest pose.
**Evidence:** 14,110 body points carried 10-20 % root weight (about 5,000 on shins, spine and forearms), so every pose
left limbs partly lagging; 5,391 points had a shin's weight on a forearm; 15,610 skin points carried stray arm weight, and
raising the arms dragged the hips into "wings" (117 faces stretched to 27 cm edges). (not re-checked here)
**What to do:** strip a limb's weight from points more than about 7-8.5 cm from that limb's bone segments, drop root weight
where a real bone has some, renormalise; measure face edge lengths after posing (any edge far longer than at rest is a
stray weight).
**How it was found:** splitting the posed body into connected pieces found two stray shells of 50 and 32 points.

### Any vertex group named like a bone deforms
**What happens:** the Armature modifier uses every vertex group whose name matches a bone; imported meshes carry their own
skinning groups (and helper groups at full weight) that can share names or outrank your weights.
**Evidence:** a raw MakeHuman mesh carried helper geometry and non-bone groups (one named "body" at full weight); the first
drape and clip on it were wrecked (legs detached). (not re-checked here)
**What to do:** `vertex_groups.clear()` and remove old Armature modifiers before weighting to your rig; delete helper
geometry and non-bone groups.
**How it was found:** a figure that came apart when posed.

### Weights copied through bmesh need matching vertex groups and an Armature modifier
**What happens:** a bmesh deform layer stores weights by group index; they do nothing until the object has groups at those
indices and an Armature modifier.
**Evidence:** shoes built with copied weights stayed in the rest stance. (not re-checked here)
**What to do:** recreate the source's vertex groups by name, in order, then add an `ARMATURE` modifier.
**How it was found:** shoes left behind when the figure posed.

### Remove from a vertex-group collection only after collecting what to remove
**What happens:** removing groups (or entries) while iterating over them skips some.
**Evidence:** some weights survived a removal loop. (not re-checked here)
**What to do:** `for g in list(obj.vertex_groups): ...` and remove after collecting.
**How it was found:** a check found leftover weights.

### Skinning cloth to the body: each garment follows only the bones it hangs from
**What happens:** weights copied from the body by nearest point give a garment weights of limbs it does not belong to: a
lifted arm stretches the torso cloth, trouser legs that touch take each other's weights.
**Evidence:** lifting an arm stretched a tunic's body x75 (a web from sleeve to hip) until garments followed only their own
bones (torso and legs; shoulder and arm for sleeves); wide trouser hems took the feet's weights; touching inner seams took
the other leg and stretched webs between the legs; with the body's Mask modifier on during the copy, sleeves stretched
x59 (weights from hands and neck only). Raising an arm past about 45 degrees stretches a skinned underarm x8 whatever the
weights. (not re-checked here)
**What to do:** weight each garment point to its own limb's chain (by which pattern piece it belongs to), blending the
nearest two bones along the limb; copy weights from the body's rest mesh with its Mask and Armature off (see
`modifiers.md`, Data Transfer); simulate the underarm rather than skinning it.
**How it was found:** stretch checks with the arm raised.

### Points posed in Python from bone matrices match Blender's armature deform closely
**What happens:** linear blend skinning computed from `pose_bone.matrix @ bone.matrix_local.inverted()` and the weights
reproduces the Armature modifier, so measures can pose points without toggling modifiers (which would free a cloth cache).
**Evidence:** hand points posed from the bones matched the posed mesh to within 1.7 mm. (not re-checked here)
**What to do:** as above, when a measure must not touch the scene.
**How it was found:** a check that had been toggling modifiers per frame.

### Corrective Smooth and preserve-volume settle skinning artefacts
**What happens:** bones pinch skin, and a bent hip folds skinned cloth into the body.
**Evidence:** the project used `CORRECTIVE_SMOOTH` after the Armature (`rest_source='ORCO'` or a bound rest) and
`use_deform_preserve_volume = True` (dual quaternion) on the Armature for cloth at a seated hip, which folded less into the
body. A Mask placed before Corrective Smooth broke it (it needs every vertex). (not re-checked here)
**What to do:** Armature -> Corrective Smooth -> Mask -> Subdivision.
**How it was found:** pinching at joints.

## MPFB and downloaded figures

### MPFB builds a human from a headless script
**What happens:** MPFB's services work without its UI.
**Evidence:** installed with `Blender --online-mode -c extension install --sync --enable mpfb`; then
`import bl_ext.blender_org.mpfb`, `HumanService.create_human(macro_detail_dict=..., scale=0.1)` (metres),
`TargetService.load_target(body, path, weight)` (targets in `-incr`/`-decr` pairs, net weight in [-1, 1]),
`HumanService.add_builtin_rig(body, 'default')`. Its shape lives in shape keys, which block cutting, subdividing and
applying modifiers until baked with `shape_key_remove(all=True, apply_mix=True)`. (not re-checked here)
**What to do:** as above; run without `--factory-startup` (the extension is a user extension) or enable it in the script.
**How it was found:** building figures in batch.

### The MPFB base mesh is full of helper geometry
**What happens:** eyes, teeth, tongue, joint cubes and tights/skirt/hair helpers sit inside the skin, hidden by a Mask; the
real skin is the `body` vertex group. The raw body's rest pose had the arms out about 55 degrees with forearms forward.
**Evidence:** landmarks read from `joint-*` groups (`joint-l-eye`, `joint-head-2`); the male figure's MakeHuman rest made
every pose's turns wrong until his rest was copied from the female figure. Half the head's faces pointed inward, and the
skin was a thin double shell (rays hit twice, 4 mm apart). (not re-checked here)
**What to do:** read landmarks from the `joint-*` groups first, then delete vertices outside `body` and remove non-bone
groups; recalculate normals before any signed test; never use the raw skin as a cloth collider (see `cloth.md`).
**How it was found:** checks that passed obvious faults until the mesh itself was examined.

### The MPFB default rig's axes, as measured
**What happens:** forearm and shin hinge about local +X (forward for the forearm, back for the shin), sideways is local Z;
fingers curl toward the palm about local X; each bone's Y runs along its length (the head bone's Y up the neck). The
shin's two bones and the foot's head sit off the hinge line.
**Evidence:** an analytic two-bone leg solve missed the ankle by up to 35 mm until finished with a correction on distance.
(not re-checked here)
**What to do:** bend hinges about local X only; finish leg solves numerically.
**How it was found:** 306 of 432 pose fits had bent an elbow or knee sideways (up to 47 degrees) before hinges were solved
as hinges.

### Two figures with the same vertex count need not share vertex order
**What happens:** body meshes built from the same base can have the same number of points in a different order.
**Evidence:** two figures' meshes: 0.4 % of points within 1 cm of each other by index. (not re-checked here)
**What to do:** match points by position (KD-tree), not by index.
**How it was found:** carrying a garment from one body to another.

## Motion capture

### BVH motion needs axis, rate, rest and floor conversion before it fits a Blender rig
**What happens:** BVH data is Y-up, often 120 fps, and its rest skeleton may be a T-pose or not upright.
**Evidence:** the project converted Y-up to Z-up with a rotation, took every 5th frame of 120 fps (upsampling 60 fps
sources first, angles unwrapped), swung limbs along source segments (a T-pose source on an A-pose rest leaves arms 45
degrees out), and used a local floor (the capture floor drifted 0.5-3.7 cm, left and right markers at different heights).
One dataset's rest skeleton was not upright and needed a rest correction first. (not re-checked here)
**What to do:** as above, and check foot slide on planted frames.
**How it was found:** retargeting free motion-capture clips.

### Retargeting by joint angles slides the feet on a figure of other proportions
**What happens:** copying the actor's joint angles and moving the pelvis along the scaled hip path does not keep a planted
foot still when the legs' proportions differ.
**Evidence:** a just-landed heel slid up to 45 cm on the floor; grounding the lowest point every frame made it worse
(dragged the swinging heel). Solving the legs to reach the actor's own scaled ankle path gave a planted slide of 9.6 mm on
one clip and 0.3 mm on another. (not re-checked here)
**What to do:** retarget feet by IK to the actor's scaled ankle paths, lowering the pelvis where the leg falls short.
**How it was found:** foot slide measured per frame.

## Actions, keyframes, shape keys, drivers (4.4+)

### keyframe_insert makes a slotted action; F-curves live in a channelbag
**What happens:** since 4.4 an action has slots (one per animated ID), layers and keyframe strips; F-curves sit in the
strip's channelbag for a slot. `action.fcurves` still works in 4.5 as a shortcut to the first slot's channelbag.
**Evidence:** Re-checked here `[exp: experiments/rigging/actions_slotted.py]`: `keyframe_insert('location')` on a cube made
action "CubeAction", layered, one slot `OBCube` (target type OBJECT), one layer, one KEYFRAME strip; the curves
(`location` 0-2, group "Object Transforms") read from `action.layers[0].strips[0].channelbag(slot).fcurves` and equally
from `action.fcurves`. `bpy_extras.anim_utils.action_get_channelbag_for_slot` exists in 4.5;
`action_ensure_channelbag_for_slot` does not. New keys are BEZIER; `fcurve.evaluate(frame)` reads a value without
changing the scene.
**What to do:** read curves through `strip.channelbag(slot)` (or the helper); expect `action.fcurves` to go in 5.0.
**How it was found:** measured here.

### Assigning an action to a second object gives it no slot: it does not move
**What happens:** an action keyed on object A has a slot for A; assigned to object B, B's `action_slot` stays None and B
does not animate, though the slot is listed in `action_suitable_slots`.
**Evidence:** Re-checked here `[exp: experiments/rigging/actions_slotted.py]`: B stayed at (3, 0, 0) with slot None; after
`B.animation_data.action_slot = act.slots['OBA']` it followed A's curves to (0, 0, 2). Keying B afterwards (slot cleared)
added a second slot to the shared action. An action made with `action.fcurves.new()` on an empty action got a slot named
"Legacy Slot" (`OBLegacy Slot` once assigned), and an object assigned it did animate.
**What to do:** after `animation_data.action = act`, set `animation_data.action_slot` explicitly; or build actions with
`act.slots.new(id_type='OBJECT', name=...)`, `act.layers.new(...)`, `layer.strips.new(type='KEYFRAME')`,
`strip.channelbag(slot, ensure=True).fcurves.new(...)`.
**How it was found:** measured here.

### Many keys: keyframe_points.add plus foreach_set is about a hundred times faster
**What happens:** a `keyframe_insert` per key goes through the full keying path.
**Evidence:** Re-checked here `[exp: experiments/rigging/actions_slotted.py]`: 1,000 keys by `keyframe_insert` 0.022 s;
`fcurve.keyframe_points.add(1000)`, `foreach_set('co', ...)`, `fcurve.update()` 0.0002 s, the curve evaluating correctly.
**What to do:** bulk-add for long curves (baked motion), then `fcurve.update()`.
**How it was found:** measured here.

### A shape key's animation lives on the Key datablock, not on the object
**What happens:** keyframing `key_block.value` makes an action on `mesh.shape_keys` (slot `KEKey`), not on the object.
The shape-key mix shows in the evaluated mesh; the mesh's own vertices stay at the basis.
**Evidence:** Re-checked here `[exp: experiments/rigging/shapekeys_drivers.py]`: object had no animation data; the Key's
action held `key_blocks["up"].value`; at value 0.5 the evaluated top was at z = 1.5 and the mesh data's at 1.0.
**What to do:** look for shape-key animation on `obj.data.shape_keys.animation_data`; read shapes from the evaluated mesh.
**How it was found:** measured here.

### Drivers from Python: simple expressions need no Python; others ran here in a fresh background session
**What happens:** a driver expression that Blender's own evaluator understands (`x * 0.5`) is marked
`is_simple_expression` and runs without Python. A Python-only expression ran in a fresh `-b --factory-startup` session;
see `running.md` for files opened headless, where such drivers stay at 0 without `-y`.
**Evidence:** Re-checked here `[exp: experiments/rigging/shapekeys_drivers.py]`: a TRANSFORMS driver `x * 0.5` from an
empty at x = 1 set the key to 0.5 (simple: True); `sum([x, x]) * 0.25` at x = 0.8 gave 0.4 (simple: False), with
`bpy.app.autoexec_fail` False. A corrective key driven by a bone's local X rotation (`transform_type='ROT_X'`,
`transform_space='LOCAL_SPACE'`, `a / 1.5708`) read 0.0, 0.5, 1.0 at 0, 45, 90 degrees.
**What to do:** prefer simple expressions; driven values update after `view_layer.update()`.
**How it was found:** measured here.
