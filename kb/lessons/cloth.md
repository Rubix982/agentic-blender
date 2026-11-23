# Lessons: cloth simulation

Learned on a project that sewed garments from flat pattern pieces and draped them with Blender 4.5.14's cloth solver on
animated human figures (standing, posed from photos, walking, sitting): a long tunic (kameez), trousers, flared skirts,
a long scarf. Numbers are from that project unless a line says "Re-checked here", which points at an experiment in this
repository that measured it again.

## Pins

### A pin at weight 1.0 is fixed; a pin below 1.0 is a spring, and at the default stiffness it gives way
**What happens:** points whose pin-group weight is 1.0 are held exactly where the mesh above the cloth puts them. Below
1.0 the pin is a goal spring whose strength scales with the weight and `pin_stiffness` (default 1, range 0 to 50 `[inv]`).
Against gravity alone a soft pin barely moves; against stronger springs (sewing springs, a stretched panel) it is pulled
away.
**Evidence:** a raised sleeve's seam pulled the back panel taut "like a tent" while the arm was still: the partly
weighted bodice pins gave way to sewing springs (force up to 200), taut edges creeping 157 -> 237 during the hold. Pin
stiffness 50 cut the taut edges on that pose from 257 to 156-160 and the tent was gone by eye; on a walk clip stiff pins
kept the hem within 1.6 cm instead of 5.6 cm, and the most taut frame had 144 stretched edges instead of 324. Stiff pins
also out-pull the fabric: at 50 they beat a tension of 40 and stretched cloth 1.6x where a collision pushed against them.
A band pinned at full weight did not move while a thigh pushed the cloth below it out 5-8 cm. Re-checked here
`[exp: experiments/simulation/cloth_pins.py]`: weight 1.0 moved 0.0 m at stiffness 1, 10 and 50; two squares 20 cm apart
joined by sewing springs (max force 200, no gravity), one pinned at 1.0 and the other everywhere at 0.99, pulled the
0.99 square's seam edge 15.3 cm at stiffness 1 and 3.9 cm at stiffness 50 (weight 0.9: 16.1 and 4.9 cm; weight 0.5: 19.2
and 12.4 cm). A whole sheet pinned at 0.5 sagged only 2.4 mm under gravity at stiffness 1.
**What to do:** weight 1.0 where the cloth must not move; where a pin fades out, raise `pin_stiffness` toward 50 so partial
pins hold against seams, and fade pins out where collisions push. Set pins per stage: settings right for a static drape
(free sleeves, soft pins) were wrong for motion.
**How it was found:** twenty isolating runs ruled out the torso turn, legs, hand colliders, self-collision, cuff pins and
the arm's path; a per-frame trace then showed the panel going taut during a hold with the arm still.

### Points pinned at weight 1.0 do not collide; at 0.9 they mostly do
**What happens:** a fully pinned point follows its goal and ignores colliders, so a hand placed on a pinned bodice sinks
through it. A partly weighted pin is pushed by colliders.
**Evidence:** a hand posed on the stomach sank into the garment (16 hand-through-cloth triangle crossings on one pose,
170 on another) until the cloth was pressed under the palm after the simulation (16 -> 0, 170 -> 0). Freeing the pins
where a hand would rest made it worse: the arriving hand bunched the freed cloth (taut edges 288 -> 385-524). Re-checked
here `[exp: experiments/simulation/cloth_more.py]`: a sheet pinned everywhere with a 0.2 m sphere pushed 20 cm up into it:
weight 1.0 left 109 points inside the sphere and lifted nothing; weight 0.9 left 24 inside and lifted the sheet 8.5 cm
(stiffness 50: 41 inside, 4.6 cm); weight 0.5 left none inside (lifted 23 cm).
**What to do:** where contact matters, pin below 1.0 (the project used 0.9 at the centre of a small pinned patch); keep
hands off the body far enough for cloth to lie between; or fix a render copy after the simulation.
**How it was found:** a reviewer saw a hand inside the cloth on renders that had passed every automatic check.

### Keep a pin's goal outside the collider's contact zone
**What happens:** if a pinned point's goal lies inside a collider's skin (its `thickness_outer` plus the cloth's
`distance_min`), pin and collision fight every step and the whole cloth buzzes.
**Evidence:** a 25 cm pinned disk on a curved shoulder: 110 % stretch and buzzing at rest; a goal 9 mm above a collider
pushed out 3 mm sat inside its skin. A small patch (2.5 cm, fading to nothing by 5.5 cm) with its goal lifted 12 mm
(4 mm thickness + 4 mm cloth distance + margin) was calm. (not re-checked here)
**What to do:** keep pinned patches small and lift their goal past the collider's thickness plus the cloth's collision
distance.
**How it was found:** the first smoke run of a scarf pinned at the shoulder.

### The cloth reads its pin weights from the modifier stack above it every frame
**What happens:** `vertex_group_mass` is evaluated each step from the mesh as the modifiers above the cloth leave it, so
a Vertex Weight Mix (or Edit/Proximity) modifier with a keyframed strength can release or add pins mid-simulation.
**Evidence:** a pinned band was faded out as a seated figure's thighs rose, by a weight mix keyed per frame, and it acted
on the running simulation. Re-checked here `[exp: experiments/simulation/cloth_pins.py]`: a back row pinned at 1.0, its
weight replaced by 0 through a Vertex Weight Mix (`mix_mode='SET'`, `mix_set='ALL'`, `default_weight_b=0`) whose
`mask_constant` is keyed 0 -> 1 at frames 19 -> 20: the row moved 0.0 m up to frame 19, 3.4 cm by frame 21 and 3.9 m by 48.
**What to do:** order the stack Armature -> Vertex Weight Mix (or Hook) -> Cloth -> Solidify -> Subdivision, all made
before the first `frame_set`; reorder with `bpy.ops.object.modifier_move_to_index` inside
`temp_override(object=o, active_object=o)`; key `mask_constant` or `default_weight_b`.
**How it was found:** needed to let a pinned waistband go while a figure sat down.

### Points pinned at full weight follow the object's animation exactly; soft pins lag
**What happens:** pins follow the mesh above the cloth, object transform included. At weight 1 they are exact; at
partial weight they trail the motion and catch up.
**Evidence:** Re-checked here `[exp: experiments/simulation/cloth_pins.py]`: the object keyed 0.5 m along x over 11
frames; the weight-1 row lagged 0.0 m at every frame; a weight-0.9 row lagged 2.3 cm at frame 6 (stiffness 1) or 1.4 cm
(stiffness 50), and under 0.5 cm by frame 12.
**What to do:** carry fitted parts (a bodice, a band) on full-weight pins following an armature; use partial weights only
where the cloth should be free to lag.
**How it was found:** measured here while re-checking the pin lessons.

### Carry cloth into place with a Hook before letting it go
**What happens:** a Hook modifier above the cloth, driven by a keyed empty, moves its vertex group as a pin goal; keying a
weight mix to 0 then releases it.
**Evidence:** used to carry a long scarf onto a shoulder from beside the figure. Setup: `HOOK` with `falloff_type='NONE'`
on a vertex group, at the bind frame `hook.matrix_inverse = (obj.matrix_world.inverted() @ empty.matrix_world).inverted()`
and `hook.center`; to follow a bone afterwards, a Child Of constraint on the empty with
`inverse_matrix = (rig.matrix_world @ pose_bone.matrix).inverted()` and influence keyed 0 -> 1. (not re-checked here)
**What to do:** as above; the empty's path is the cloth's path to its start pose.
**How it was found:** a scarf put on by wrap-and-pin.

## The cache, baking and frames

### Any edit to the cloth object or its colliders throws away the unbaked cache after the current frame
**What happens:** a cloth simulated by stepping `scene.frame_set` keeps its frames in a memory cache that is not baked.
Tagging the cloth object, its modifier settings or a collider for an update (even setting a property to the value it
already has) marks the cache outdated and frees every frame after the current one. Going to a later frame then cannot
simulate (it is not the next frame), so the cloth shows a stale or unsimulated state.
**Evidence:** every frame of several motion clips rendered the unsimulated drape (hem height 0.372 on every frame) because
a per-frame check hid objects, added a copy and unhid them on each sampled frame; a bisection over commits found it. Other
triggers seen: changing materials, writing a colour attribute to the simulating mesh, adding modifiers after the cloth,
toggling a Mask on another object. Re-checked here `[exp: experiments/simulation/cloth_cache_invalidation.py]`: 40 frames
stepped, back to frame 10, one change, then frame 30: the cache fell from 40 to 10 frames ("cache is outdated!") and frame
30 differed by 0.25 m after renaming the cloth object, setting `quality` or `mass` to their own values, setting
`hide_render` to its own value, toggling `hide_viewport`, setting the collider's location to its own value, adding a
material slot, adding a Subdivision modifier after the cloth (even at levels 0), or editing a vertex group weight. Kept (40
frames, identical): `frame_set` to the current frame, `view_layer.update()`, `select_set`, moving an unrelated camera,
changing render resolution, adding a new object, editing an existing material's Base Color value.
**What to do:** set everything (materials, render modifiers, visibility) before simulating; once simulated, bake:
`with bpy.context.temp_override(point_cache=mod.point_cache, object=o, active_object=o): bpy.ops.ptcache.bake_from_cache()`
and check `point_cache.is_baked`. The bake survived every change tried here. Measures that run during a clip must not touch
the scene; compute them from data (project triangles, pose points from bone matrices). Settings that must change mid-run
are keyframed before simulating.
**How it was found:** short clips on past commits bisected the freeze to a check that toggled visibility per frame.

### A frame jump with nothing cached takes one giant step, or none
**What happens:** cloth simulates only from the last simulated frame to the next. Jumping from the start frame to a later
one takes a single solver step stretched over the whole gap (no collisions resolved in between); a further jump does not
simulate at all and shows the last state.
**Evidence:** Re-checked here `[exp: experiments/simulation/cloth_bake.py]`: from frame 1 straight to frame 60 the free
cloth fell 4.9 m, through a sphere collider (lowest point z = -3.9 against 0.41 when stepped); 1 -> 3 moved it 2.3 cm in
one step, and 3 -> 60 then moved it 0.0 m. Going back to an already simulated frame is a cache read (0.0 s).
**What to do:** step every frame in order (`for f in range(start, end + 1): scene.frame_set(f)`) or bake, before reading
any frame.
**How it was found:** measured here.

### Baking headless: ptcache.bake needs the point cache in the context; bake_all does not
**What happens:** in background mode `bpy.ops.ptcache.bake` has no physics panel to take the cache from, so its poll fails;
given `point_cache` through `temp_override` it bakes. `ptcache.bake_all` needs nothing. A bake equals stepping exactly.
**Evidence:** Re-checked here `[exp: experiments/simulation/cloth_bake.py]`: without the override "Operator
bpy.ops.ptcache.bake.poll() failed, context is incorrect"; with it FINISHED in 1.05 s for 60 frames of a 961-point sheet,
max difference from stepping 0.0 m; `bake_all(bake=True)` 1.04 s, 0.0 m; `free_bake_all()` cleared it; the scene's frame
was back at 1 after the bake.
**What to do:** `with bpy.context.temp_override(point_cache=mod.point_cache): bpy.ops.ptcache.bake(bake=True)`.
**How it was found:** measured here; the project baked with `bake_from_cache` after stepping.

### Freeze a settled simulation into the mesh before removing the cloth
**What happens:** the settled shape exists only as the modifier's output; it must be written into a mesh before the cloth
modifier goes. If an Armature stays under it, the pose is applied a second time to a mesh that already holds it.
**Evidence:** after a simulation run on top of an Armature was frozen, the remaining Armature applied the pose again:
sleeves flew back up and part of the front fell to the floor. (not re-checked here)
**What to do:** step frames in order, then `me = bpy.data.meshes.new_from_object(o.evaluated_get(dg),
preserve_all_data_layers=True, depsgraph=dg)`, remove the CLOTH (and the Armature, unless the mesh is re-bound in rest
space), set `o.data = me`, remove the old mesh. `new_from_object` drops shape keys: keep rest keys as arrays across stages.
**How it was found:** staged drapes that replaced the mesh between stages.

### An exploded simulation can render as a black frame with no error
**What happens:** nothing fails; a frame whose cloth went to huge or non-finite coordinates just comes out black or empty.
**Evidence:** a black render from a blown-up drape. (not re-checked here)
**What to do:** measure the result (extents, finite coordinates, a known height such as the hem) before trusting any
render.
**How it was found:** a black render.

## Rest shape

### rest_shape_key does not set the springs' rest lengths; shrink_min and Dynamic Mesh do
**What happens:** a cloth whose `rest_shape_key` points at another shape key still rests at the mesh as placed. The
springs take their rest lengths from the mesh at the first frame. `shrink_min` scales the rest; with `use_dynamic_mesh`
the rest follows the modifier stack above the cloth each frame (an animated shape key or modifier does change it). Under
Dynamic Mesh an unpinned cloth is not moved to the base mesh (only its rest follows it); pinned points follow it as goals.
**Evidence:** a 1 m square with a half-size rest key, no gravity, 60 frames: still 1.0 m wide with the key added before or
after the modifier, with Dynamic Mesh and with soft springs; `shrink_min` 0.5 gave 0.5 m. A 20 cm strip whose rest key was
10 % shorter, or rolled into a half-cylinder, kept its length and stayed flat whatever was tried; with Dynamic Mesh and the
key's value keyed 0 -> 1 it shrank to 18.0 cm and the half-cylinder curled. Every construction the project had built on a
rest key had never acted. Re-checked here `[exp: experiments/simulation/cloth_rest_shape.py]`: rest key "half" -> 1.0 m
wide; with a third key after it 1.0; pointing at a 2x key 1.0; with Dynamic Mesh 1.0; `shrink_min` 0.5 -> 0.5; Dynamic
Mesh with the half key's value keyed 0 -> 1 over frames 1-30 -> 0.5 m; the same keyed key without Dynamic Mesh -> 1.0 m.
A mesh with shape keys reports `rest_shape_key` as Basis by default.
**What to do:** shape the rest by placing the mesh in that shape before the first frame, by `shrink_min`/`shrink_max`
(with a vertex group for part of it), or by Dynamic Mesh with the shape driven above the cloth. Re-check after a Blender
upgrade (a small strip test is enough).
**How it was found:** a staged-rest experiment changed nothing to the unit; a minimal square then showed the key ignored.

### Cloth rests in the shape it was placed in
**What happens:** because the springs rest at the placed mesh, a full skirt or flare keeps whatever shape it started in:
placed as an open cone it pools in stiff fins; placed folded round a small core, the folds come back as regular pleats.
Adding girth only deepens the remembered folds, and gravity alone hangs a flare in vertical folds.
**Evidence:** a floor-length flared trouser placed in folds: adding girth (3.4 -> 5.0 m a leg) moved its floor spread from
0.40 to 0.45 of the figure's height against the photo's 0.75; bending stiffness x4 to x100 kept it a column (x4: the
flutes hung straight and stood off the floor). Laying the lower part out on the floor with a shape key as the pose began
raised the spread to 0.54 (median of 3 drapes; a second design 0.30 -> 0.47 against 0.66). (not re-checked here)
**What to do:** place cloth in the shape it should rest in; lay out a sweep on the floor rather than expecting it to fall
into one; for a standing flare, give it something to stand on (next lesson).
**How it was found:** a dozen rounds on one flared garment, judged by eye and by the outline's widths.

### A flare stands only on a support that grips it
**What happens:** a full flare hangs straight down however wide it is cut; a collider under it (a petticoat cone) holds
the spread, but only if the cloth's friction on it is high enough not to creep.
**Evidence:** a cone collider sized from the photo's flare widened the standing shape 21-30 cm between 10 and 50 cm up; at
the collider's default friction 5 the cloth crept over it and never settled (58 mm p95 movement in 240 frames); at
friction 40, with the floor at 40, it settled by frame 115 and kept the width. (not re-checked here)
**What to do:** an invisible support collider with `collision.cloth_friction` around 40.
**How it was found:** the flare's settle measure never passed at the default grip.

## Self-collision

### vertex_group_self_collisions excludes its points
**What happens:** Blender's own tooltip says it: "Triangles with all vertices in this group are not used during self
collisions" `[inv]`. A group meant to say "self-collide only here" does the opposite.
**Evidence:** two squares 3 cm apart in one cloth, the lower pinned, self-collision 5 mm: no group, the upper rests 7.9 mm
above the lower; every point in the group, it falls 5 m through. Five groups in the project had been set the wrong way
round. Re-checked here `[exp: experiments/simulation/cloth_self_collision.py]`: no group 7.9 mm; every point, the lower
square only, or the upper square only in the group: -5,035 mm (through).
**What to do:** to self-collide only on part of a cloth, put the complement of that part in the group (or `""` for all).
**How it was found:** reading the property's description while debugging a blow-up, then a three-square probe.

### Self-collision keeps cloth moving when its distance passes about 0.37 of the edge length
**What happens:** with `self_distance_min` large against the mesh's edges, neighbouring points sit inside each other's
self-collision distance and the solver keeps pushing them: the cloth never comes to rest, with no second layer anywhere.
**Evidence:** a buckling hung sheet, p95 point speed at the end (at rest means under 0.5 mm a frame): on a 12 mm grid 4 mm
gave 0.02, 4.5 mm 0.69, 5 mm 7.87; 3 mm 0.85 in another setup; on a 20 mm grid 5 mm gave 0.01 and 4 mm 0.32. Friction 0 or
40, air damping 5, impulse clamp 0.2 and quality 24 did not stop it. On a garment, self-collision at the slits kept it
moving 1-4 mm a frame for 400 frames; with it off it was still by frame 45-64. Re-checked here
`[exp: experiments/simulation/cloth_self_collision.py]`, 120 frames: 12 mm grid 4 mm 0.029, 4.5 mm 4.02, 5 mm 8.05; 20 mm
grid 5 mm 0.016; self-collision off 0.013.
**What to do:** set the self distance from the mesh's shortest edges (under about a third of them), not from how thick the
cloth should look; enable self-collision only where needed; settle by a speed rule with a frame cap.
**How it was found:** a garment under whole-cloth self-collision never met the settle rule; a minimal sheet isolated it.

### A pooled hem under whole-cloth self-collision never quite settles
**What happens:** floor-length cloth folded onto itself on the floor creeps without end; every setting lowers the creep and
none removes it.
**Evidence:** about 20 variants (air damping 5-10, floor friction 40-80, self distance 2-4 mm, bending x2-3, shear x5, grid
20-28 mm, floor thickness 4-20 mm, 200-700 frames) all levelled off near 0.6 mm a frame; net movement grew without bound
but slowing (p95 3.6 mm at frame 220, 20.5 mm at 740). Self friction 80 made it worse. Without self-collision the same
drape had 174,912 crossing triangle pairs against 32 with it. Raising collision quality cut crossings 1,459 -> 599 on
another case. (not re-checked here)
**What to do:** accept a looser settle rule for pooled cloth (judge the speed above the floor band), or keep the pooled
part out of self-collision and count crossings separately.
**How it was found:** a settle rule (p95 under 0.5 mm a frame for 10 frames) that one garment never met.

### Whole-cloth self-collision is expensive
**What happens:** self-collision tests every nearby triangle pair each step.
**Evidence:** a full flared garment: about 34 s a frame, 853 s for a 25-frame stage; a drape hit a 90-minute limit.
Re-checked here `[exp: experiments/simulation/cloth_self_collision.py]`: a 2,924-point sheet at quality 12 and collision
quality 8 took 0.065 s a frame without and 0.665 s with self-collision at 5 mm (10x).
**What to do:** turn it on only where cloth meets itself (slits, folded sleeves, pooled hems), via the group's complement.
**How it was found:** timing; a drape hitting its time limit.

### A start that already crosses itself, or coincident layers, explode under self-collision
**What happens:** if the first frame has cloth through cloth, self-collision pushes the layers apart from the wrong side
and the simulation blows up. Two layers placed on the same spot are pulled together by sewing springs and pushed apart by
self-collision at once. Springs pulling a placed shape toward a different rest in one step drag it through itself.
**Evidence:** a shape key added at the start moved points up to 270 mm at frame 1; the cloth had 7,787 crossing triangle
pairs before anything moved (the saved drape: 109), and the drape blew up (p95 675 mm a frame). A rest changed in one
step moved cloth 64-162 mm in 25 frames and made 11,688 self-crossings. 644 point pairs at 0 mm apart made flares move
80 mm in a no-gravity step (12 mm with self-collision off). Two trouser legs meeting under self-collision blew up into a
heap. (not re-checked here)
**What to do:** count crossings at frame 1 (`BVHTree.overlap` of the cloth with itself) before simulating; make placements
crossing-free; weld springs shorter than 0.5 mm; morph a rest over staged steps with gravity off.
**How it was found:** a per-frame trace from frame 1 showed the crossings were there before the solver ran.

## Mesh and collider preparation

### Zero-length edges make cloth explode, and the trigger looks random
**What happens:** two points on one spot are an infinitely stiff spring. Whether it blows up depends on tiny geometric
differences, so the failures look random.
**Evidence:** every drape of one run exploded at every solver quality; 0.03 mm in a hem decided whether a test exploded;
edges of 0.12-0.2 mm came from pushing neighbours onto one spot. Five theories (sewing force, impulse clamping, collision
passes, pre-closing seams, wrist caps) were tested and dropped before the shortest edge was measured. A collar meshed at
8 mm inside a 15 mm garment also blew a drape up (seams 15 m apart). (not re-checked here)
**What to do:** before simulating, report the shortest edge, merge edges shorter than about 0.3 of the mesh resolution and
fail a mesh with an edge under 0.5 mm; keep one resolution per garment; when pushing points out of a collider, move each
along the normal by its own depth (and both ends of an edge alike) rather than snapping to the nearest surface point.
**How it was found:** after the five theories failed, the mesh itself was measured.

### Cloth that starts inside a collider is shoved, and no cloth setting fixes it
**What happens:** points that begin inside a collision surface are pushed out with a steady force at every step, lifting
or dragging the whole cloth.
**Evidence:** a garment's hem rose 23 cm above where it was cut; its back started 2.5 cm inside the collider at the hip and
5 cm at the shoulders, because the body had stray faces (a 27 cm "rod" at each hip). After cleaning, the lift fell to about
7 cm. Pushing points clear one by one made the drape blow up; heavy damping barely changed anything (the force was steady,
not momentum). Sleeves placed 4 cm deep in the shoulder shrank from the wrist to 0.37 m while seams closed; 12 % of a
sleeve starting about 2 cm inside made a garment ride 20 cm up. (not re-checked here)
**What to do:** before any drape, test every placed point against every collider (the body, the proxy, every garment
underneath) by ray parity, push it out along the normal plus a gap, and refuse a run where more than about 2 % of a piece
starts inside; place sleeves by where a ray leaves the body. When no setting fixes a symptom, look for something in the
scene every variant shares.
**How it was found:** hem height traced after each stage, then collision and sewing switched off one at a time.

### A collider with a mirrored transform is inside out and pulls cloth in
**What happens:** an object whose matrix has a negative determinant has its normals flipped; the cloth solver then treats
the inside as outside and draws cloth toward it. Inward-facing caps on a collider do the same locally.
**Evidence:** an ellipsoid hand collider built from a left-handed basis (`(x, y, y × x)`, determinant -1) hitched a skirt
up at both hands, with friction 15 or 0.5; two studies were void. An x-ray render looked right. (not re-checked here)
**What to do:** assert `matrix_world.determinant() > 0` for every collider you build; run `bmesh.ops.recalc_face_normals`
on colliders; `obj.collision.use_normal = True` makes impulses follow the collider's normals `[inv]`.
**How it was found:** printing the collider's matrix.

### Collide against one clean, closed proxy, not a double-shelled body or a stack of garments
**What happens:** a figure whose skin is two surfaces a few millimetres apart (as some downloaded bodies are) gives the
cloth two collision layers; open, thin or layered colliders (a skinned garment, hair cards) snag and jitter the cloth and
slow it down.
**Evidence:** three fabric settings changed nothing on a lumpy drape; draping against a voxel-remeshed proxy of the body
fixed the lumps and ran 4x faster. Over a closed proxy, stretch p99 0.14 and 116 of 3,267 points shaking more than 2 mm a
frame², against 1.03 and 2,576 over the layered colliders. A garment draped over body plus trousers as one remeshed closed
surface took 205 s against 1,114 s with the trousers as a separate collider; a drape over dense open cloth took 18 min
instead of 3. (not re-checked here)
**What to do:** fuse the body and every garment worn under into one closed collider: thicken sheets into a slab, voxel
remesh (8-12 mm), smooth, displace out about 3 mm, apply; bind it to the body (Surface Deform or weights). Close holes
before remeshing; see `kb/lessons/modifiers.md` ("A voxel Remesh needs a closed shell" and "A voxel Remesh drops a slab
thinner than one voxel").
**How it was found:** fabric settings exhausted, then the collider measured.

### collision_settings.collection limits which colliders a cloth sees
**What happens:** by default every collider in the scene acts on every cloth; extra colliders change the drape. Setting
the cloth's collision collection limits it to the colliders in that collection.
**Evidence:** adding the plain body and floor as colliders made a garment hang 4 % longer. Re-checked here
`[exp: experiments/simulation/cloth_more.py]`: a cloth over two planes (0.5 m and 0 m): mean height after 30 frames 0.534 m
with no collection, 0.034 m with the collection holding only the lower plane.
**What to do:** put the intended colliders in a collection and set `cloth_mod.collision_settings.collection = coll`.
**How it was found:** a drape that changed when unrelated colliders were added.

## Sewing

### Sewing springs pull but never join, and weak ones lose to friction
**What happens:** `use_sewing_springs` pulls loose edges (edges with no faces) together up to `sewing_force_max`; below
some force, friction against the body wins and seams stay open. Closed seams are still springs: posing stretches them
open again and the last gap renders as a dark slit.
**Evidence:** at sewing force 6 sleeve caps stayed up to 28 cm from their armholes (damping and more frames changed
nothing); at 200 every seam closed within 1.4 cm. Springs 16 cm long, or full force from frame 1, dragged cloth through
the collider and blew drapes up at random. Seams held by springs at a median gap of 1.6 mm stretched to 2-13 cm when the
arms lowered; welding before posing closed them (open seam length 120 cm -> 0.7 cm on one garment). (not re-checked here)
**What to do:** `sewing_force_max` around 200; bring each seam's ends most of the way together before simulating (the
project moved them 80 % toward their midpoint); close seams with gravity off; weld the stitched points once closed, before
posing. Welding renumbers vertices: do anything keyed by index first.
**How it was found:** seam gaps traced per stage and per pair of pieces.

### Keyframes on sewing_force_max act (contradicting an earlier note)
**What happens:** the project recorded that a keyframed ramp on the sewing force "made no difference" and concluded Blender
ignores keyframes on it. Re-checked here, keyed values do act.
**Evidence:** Re-checked here `[exp: experiments/simulation/cloth_more.py]`: sewing springs 20 cm long against soft pins
(0.9, stiffness 50), no gravity, 40 frames: constant force 1 left a 19.9 cm gap, 200 (or 0, no limit) 15.2 cm; keyed 1 at
frame 1 -> 200 at frame 10 ended at 15.2 cm; keyed 200 at frame 1 -> 1 at frame 2 ended at 19.9 cm. A keyed gravity weight
also acts (0 -> 1 at frame 20: mean height 1.0 -> -0.75 m). Why the project's ramp changed nothing is not known (its seams
may have closed either way).
**What to do:** staging by keyframes is available for the sewing force as for gravity (`effector_weights.gravity`),
`air_damping`, field strength and weight-mix values.
**How it was found:** re-checking the project's note.

### Removing the sewing springs between stages lets the pieces fall apart
**What happens:** if more simulation follows, deleting the loose edges unjoins the garment.
**Evidence:** the front fell to the floor. (not re-checked here)
**What to do:** keep loose edges until the last simulated stage (or weld first); then
`bmesh.ops.delete(bm, geom=[e for e in bm.edges if not e.link_faces], context='EDGES')`.
**How it was found:** a staged drape.

### Let seams close before gravity acts, and damp the gravity-off stage
**What happens:** with gravity on from the first frame the pieces fall before the seams have drawn them together. With
gravity off, nothing slows cloth that a collision has pushed, so it drifts.
**Evidence:** a garment slid off the shoulders until the drape was staged (seams close with gravity off, then it falls);
in a gravity-off stage a hem rose 20 cm until `air_damping` was raised to 20 (default 1). (not re-checked here)
**What to do:** stage it: `settings.effector_weights.gravity = 0` and high `air_damping` while seams close, then gravity
on and damping back.
**How it was found:** by eye, then fixed by staging.

## Settings and their effects

### Cloth mass is per vertex, so the same settings on a finer grid make a heavier cloth
**What happens:** `mass` is the mass of each vertex `[inv]`, so a finer grid of the same cloth weighs more per area and
droops more. Scaling the mass by the square of the spacing compensates in direction; how exactly depends on the setup.
**Evidence:** a 12 cm strip clamped at one end, the tip's (reach, drop) at 15 / 10 / 7 mm grids: (0.108, 0.048) /
(0.085, 0.073) / (0.062, 0.092) m at one mass; (0.108, 0.048) / (0.108, 0.045) / (0.115, 0.031) with the mass scaled by
the cell area. Re-checked here `[exp: experiments/simulation/cloth_more.py]`, same strip, 15 vs 7.5 mm grid, bending 0.5:
at mass 0.0012 the tip dropped 8.5 vs 10.2 cm (finer droops more, confirmed), but with the fine grid's mass scaled by
(7.5/15)² it dropped only 3.6 cm (over-corrected); at mass 0.003, 10.1 vs 11.2, scaled 8.1; at mass 0.3 and bending 200,
9.0 vs 11.0, scaled 10.6. So the direction holds; scaling by area did not reproduce the coarse grid's droop here.
**What to do:** when changing resolution, re-measure a reference strip (a cantilever: clamp one end, read reach and drop
after the tip stops) rather than trusting a formula. When mass changes, scale `air_damping` and force-field strengths with
it (both act as forces, not per mass): at a quarter of the mass, cloth crept below the settle speed still packed round a
leg, and a flat turbulence force made the lightest fabric flutter like a flag.
**How it was found:** a resolution option that changed how the same fabric hung.

### Woven cloth needs high tension, with stiffness varied by region through vertex groups
**What happens:** at the default tension (15 `[inv]`) a hanging garment stretches under its own weight over many frames.
Structural, shear and bending stiffness can vary across the cloth: a vertex group gives `lo + w * (max - lo)`.
**Evidence:** at tension 15 cloth stretched over 115 frames and bunched at the hem; a free-hanging skirt at tension 55
still hung 12.8 cm longer than cut. Scarf presets used tension 40-50 with compression 2-6. (not re-checked here)
**What to do:** high tension, low compression for woven cloth; stiffen facings, hems and embroidered regions with
`vertex_group_bending` and `bending_stiffness_max` (and the structural group with its max).
**How it was found:** hem lengths against the cut.

### Impulse clamping and more collision passes stop cloth being thrown out of tight places
**What happens:** cloth squeezed in a wedge (an underarm) can be ejected by its own collision response.
**Evidence:** the project set `collision_settings.impulse_clamp = 1.0` (default 0, no clamp `[inv]`) and the self-collision
clamp alike, and `collision_quality = 4` (default 2), and raised `quality` to retry a run that blew up. (not re-checked
here)
**What to do:** as above, for cloth in tight places.
**How it was found:** random ejections at the underarm.

### A fast collider passes through cloth at the default steps; more steps fix it, collision quality does not
**What happens:** a collider that moves far in one frame can carry cloth points inside it between steps.
**Evidence:** Re-checked here `[exp: experiments/simulation/cloth_quality_time.py]`: a 0.3 m sphere driven 1.4 m up
through a 1,681-point sheet in 2 frames: at quality 5 up to 171 points were inside it on frames 1-8 (collision quality 2)
and 166 (collision quality 8); at quality 20, none. No points were left inside by frame 40 in any case.
**What to do:** raise `quality` (steps per frame) for fast motion; collision quality alone did not help here.
**How it was found:** measured here.

### Cloth cost: steps, collision quality, point count, memory
**What happens:** time per frame rises with quality and point count, less than in proportion at low quality.
**Evidence:** Re-checked here `[exp: experiments/simulation/cloth_quality_time.py]`, a sheet over a sphere, 40 frames:
1,681 points at quality 2 / 5 / 10 / 20: 0.015 / 0.035 / 0.064 / 0.111 s a frame; at quality 5, 441 / 1,681 / 6,561
points: 0.011 / 0.035 / 0.157 s; collision quality 1 / 2 / 5: 0.029 / 0.035 / 0.049 s. In the project a garment drape at a
1.5 cm grid took about 200 s, and a drape job peaked at 0.5-1.4 GB from a 15 mm to a 7 mm grid.
**What to do:** budget from these; defaults are quality 5 and collision quality 2 `[inv]`.
**How it was found:** timing.

### Thin collision distances lose ground over long clips
**What happens:** small per-frame losses accumulate; over hundreds of frames cloth sinks into a body whose collision
distance is small.
**Evidence:** a 4 mm collision distance over 335 frames let 663 points sink into the body; 6 mm was used for motion.
(not re-checked here)
**What to do:** raise the collision distance for long motion, and measure points inside the body at several frames.
**How it was found:** frames measured through a long clip showed the drift starting at the second pose.

## Settling and motion

### Read a drape at rest, not at a fixed frame; damp after the fall, not during it
**What happens:** a draped piece can still be moving well after the frame a script assumes it has settled; raising air
damping during the fall changes where it lands, raising it after the fall only calms it.
**Evidence:** a scarf read at frame 87 was still moving 11-16 mm a frame (assumed settled by 60), and a 1 % nudge of its
placement swung its lean between 6 and 16 degrees. Read at frame 170 with air damping raised five times after the fall, it
moved 1-2 mm a frame and the same nudges left the lean at 1.9-4.7 degrees. Damping raised during the fall let a long end
land far behind the figure, held by friction as a taut sheet at 42 degrees. (not re-checked here)
**What to do:** step until the p95 point speed stays under 0.5 mm a frame for 10 frames, with a frame cap; key
`air_damping` up after the cloth has landed.
**How it was found:** small placement changes gave large, inconsistent shape changes.

### Two drapes of the same cut differ; judge cloth on several
**What happens:** folds land differently with tiny changes in start or timing.
**Evidence:** two drapes of the same garment differed by 2.1 % median and 12.5 % at p90 per landmark measurement, from
folds alone; the project judged on the median of 3. Identical inputs re-run were bit-identical (`running.md`), so the
spread comes from changed inputs. (not re-checked here)
**What to do:** compare garment settings on the median of several drapes with small perturbations.
**How it was found:** a noise table before setting tolerances.

### Drape in an A-pose, then bring the figure into its pose with the cloth simulated
**What happens:** arms hanging where side seams go pinch and catch the cloth; draping with arms raised and then lowering
them over many frames lets underarms and sleeves fold.
**Evidence:** cloth caught along the arms until the drape used an A-pose (arms raised 40 degrees); easing into a fitted
pose over 80 frames instead of 60 (120 in all) was adopted. Blender's manual gives the same advice for character cloth.
(not re-checked here)
**What to do:** re-rest the figure with limbs clear, drape, then key the limbs into the pose while the same simulation
keeps running (re-binding a static result between stages applied a rotation twice).
**How it was found:** garments caught on arms in the first sewn drapes.

### Long motion drifts when everything is simulated; carry the fitted parts on the skeleton
**What happens:** simulating a whole garment through a long clip accumulates error (rides up, sinks, bunches).
**Evidence:** a hem climbed 44 cm up the thighs when everything below the armpits was unpinned; a later three-pose clip
with the bodice and sleeves carried on pins held the hem within 3.6 cm, and stiff pins within 1.6 cm. (not re-checked
here)
**What to do:** as games and film do, carry fitted parts on the skeleton (full-weight pins following an armature) and
simulate only loose parts (skirts, hems, cuffs).
**How it was found:** hem traces over long clips.

### Colliders inside a skirt drag it; hands are the usual cause
**What happens:** a hand collider resting inside a flared skirt, or pressing on its slope, drags the cloth up as it moves.
**Evidence:** a hem trace showed the climb starting as the hands arrived (frame ~78): without hand colliders the hem held
(+0.8 cm), with them it rose 4 cm; one clip's third move dragged the skirt 29 cm. Moving the arm out until the hand rested
on the drape (4 degrees each side) held the hem to 0.5 cm. Less friction made it worse (7.9 cm). (not re-checked here)
**What to do:** keep hands outside the cloth's rest shape in held poses; trace the hem every few frames to find which
collider moves it.
**How it was found:** a hem trace every 5 frames, after three full clips had not settled it.

### Render-only modifiers belong in the stack before the simulation runs
**What happens:** cloth at its simulation spacing renders as hard facets; Solidify and Subdivision after the cloth fix it,
but adding them after simulating throws the unbaked cache away (lesson above).
**Evidence:** folds at a 1.5 cm spacing rendered as shards until motion renders got the same thickness and smoothing as
stills (Solidify 1.8 mm, offset 1; Subdivision levels 1, render levels 2; smooth shading); adding them after simulating
rendered unsimulated cloth on every frame. Re-checked here `[exp: experiments/simulation/cloth_cache_invalidation.py]`: a
Subdivision added after the cloth cut the cache from 40 to 10 frames, even at levels 0.
**What to do:** add them after the cloth in the stack before the first frame (render-only with `show_viewport = False` if
measurements read the evaluated mesh, see `modifiers.md`), or bake first.
**How it was found:** every frame measured alike ("a measure identical in every frame is broken, not good news").
