# Lessons: cloth simulation

Learned on a project that sewed garments from flat pattern pieces and draped them with Blender 4.5.14's cloth solver on
animated human figures (standing, posed from photos, walking, sitting). Numbers are from that project unless a line says
"Re-checked here", which points at an experiment in this repository that measured it again.

---

### A pin at weight 1.0 is fixed; a pin below 1.0 is a spring, and at the default stiffness it gives way
**What happens:** points whose pin-group weight is 1.0 are held exactly where the mesh above the cloth puts them. Below
1.0 the pin is a goal spring whose strength is the weight times `pin_stiffness` (default 1, range 0 to 50). Against
gravity alone a soft pin barely moves; against stronger springs (sewing springs, a stretched panel) it is pulled away.
**Evidence:** a raised sleeve's seam pulled the back panel taut "like a tent" while the arm was still: the pinned
bodice (partly weighted) gave way to sewing springs with force up to 200. Pin stiffness 50 cut the taut edges on that
pose from 257 to 156 and the tent was gone by eye; on a walk clip stiff pins kept the hem within 1.6 cm instead of
5.6 cm, and the most taut frame had 144 stretched edges instead of 324. Separately, a band pinned at full weight did
not move at all while a thigh pushed the cloth below it out 5-8 cm. Re-checked here
`[exp: experiments/simulation/cloth_pins.py]`: weight 1.0 moved 0.0 m at stiffness 1, 10 and 50; two squares 20 cm apart
joined by sewing springs (max force 200, no gravity), one pinned at 1.0 and the other everywhere at 0.99, pulled the
0.99 square's seam edge 15.3 cm at stiffness 1 and 3.9 cm at stiffness 50 (weight 0.9: 16.1 and 4.9 cm; weight 0.5:
19.2 and 12.4 cm). A whole sheet pinned at 0.5 sagged only 2.4 mm under gravity at stiffness 1.
**What to do:** use weight 1.0 where the cloth must not move; where a pin fades out (a ramp), raise `pin_stiffness`
toward 50 so the partial pins hold against seams. Check each stage's pin settings separately: settings right for a
static drape (free sleeves, soft pins) were wrong for motion.
**How it was found:** twenty isolating runs ruled out the torso turn, legs, hand colliders, self-collision, cuff pins and
the arm's path; a per-frame trace then showed the panel going taut during a hold with the arm still.

### The cloth reads its pin weights from the modifier stack above it every frame
**What happens:** `vertex_group_mass` is evaluated each step from the mesh as the modifiers above the cloth leave it, so
a Vertex Weight Mix (or Edit/Proximity) modifier with a keyframed strength can release or add pins mid-simulation.
**Evidence:** a pinned band was faded out as a seated figure's thighs rose, by a weight mix keyed per frame; it acted on
the running simulation. Re-checked here `[exp: experiments/simulation/cloth_pins.py]`: a back row pinned at 1.0, its
weight replaced by 0 through a Vertex Weight Mix whose `mask_constant` is keyed 0 -> 1 at frame 19 -> 20: the row moved
0.0 m up to frame 19, 3.4 cm by frame 21 and 3.9 m by frame 48.
**What to do:** put the weight modifier above the cloth (`bpy.ops.object.modifier_move_to_index(..., index=0)` with the
object in a context override) and key its strength.
**How it was found:** needed to let a pinned waistband go while a figure sat down.

### Points pinned at full weight follow the object's animation exactly; soft pins lag
**What happens:** pins follow the mesh above the cloth, object transform included. At weight 1 they are exact; at
partial weight they trail the motion and catch up.
**Evidence:** Re-checked here `[exp: experiments/simulation/cloth_pins.py]`: the object keyed 0.5 m along x over 11
frames; the weight-1 row lagged 0.0 m at every frame; a weight-0.9 row lagged 2.3 cm at frame 6 (stiffness 1) or 1.4 cm
(stiffness 50), and under 0.5 cm by frame 12.
**What to do:** carry fitted parts (a bodice, a band) on full-weight pins following the armature; give partial weights
only where the cloth should be free to lag.
**How it was found:** measured here while re-checking the pin lessons.

### Pinned cloth does not collide
**What happens:** points held by pins follow their target and are not pushed by colliders, so a hand placed on the body
passes straight through a pinned bodice.
**Evidence:** a hand posed on the stomach sank into the garment; 16 hand-through-cloth triangle crossings on one pose,
170 on another, until the cloth was pressed under the palm after the simulation (16 -> 0, 170 -> 0). Freeing the pins
where a hand would rest made it worse: the arriving hand bunched the freed cloth (taut edges 288 -> 385-524).
(not re-checked here)
**What to do:** keep hands off the body far enough for cloth to lie between, or fix the cloth after the simulation; do not
expect collision on pinned points.
**How it was found:** a reviewer saw a hand inside the cloth on renders that had passed every automatic check.

### Any edit to the cloth object or its colliders throws away the unbaked cache after the current frame
**What happens:** a cloth simulated by stepping `scene.frame_set` keeps its frames in a memory cache that is not baked.
Tagging the cloth object, its modifier settings or a collider for an update (even setting a property to the value it
already has) marks the cache outdated and frees every frame after the current one. Going to a later frame then cannot
simulate (it is not the next frame), so the cloth shows a stale state.
**Evidence:** every frame of several motion clips rendered the unsimulated drape (hem height 0.372 on every frame) because
a per-frame check hid objects, added a copy and unhid them on each sampled frame; a bisection over commits found it.
Re-checked here `[exp: experiments/simulation/cloth_cache_invalidation.py]`: 40 frames stepped, back to frame 10, one
change, then frame 30: the cache fell from 40 to 10 frames ("cache is outdated!") and frame 30 differed by 0.25 m after
renaming the cloth object, setting `quality` or `mass` to their own values, setting `hide_render` to its own value,
toggling `hide_viewport`, setting the collider's location to its own value, adding a material slot, adding a Subdivision
modifier after the cloth (even at levels 0), or editing a vertex group weight. Kept (40 frames, identical): `frame_set`
to the current frame, `view_layer.update()`, `select_set`, moving an unrelated camera, changing render resolution, adding
a new object, editing a material's Base Color value.
**What to do:** set everything (materials, render modifiers, visibility) before simulating; once simulated, bake it:
`with bpy.context.temp_override(point_cache=cloth_mod.point_cache): bpy.ops.ptcache.bake_from_cache()` turns the memory
cache into a bake, which survived every change tried here. Measures that run during a clip must not touch the scene;
compute them from data instead (project triangles, pose points from bone matrices).
**How it was found:** short clips on past commits bisected the freeze to a check that toggled visibility per frame.

### A frame jump with nothing cached takes one giant step, or none
**What happens:** cloth simulates only from the last simulated frame to the next. Jumping from the start frame to a
later one takes a single solver step stretched over the whole gap (no collisions resolved in between); a further jump
does not simulate at all and shows the last state.
**Evidence:** Re-checked here `[exp: experiments/simulation/cloth_bake.py]`: from frame 1 straight to frame 60 the free
cloth fell 4.9 m, through a sphere collider (lowest point z = -3.9 against 0.41 when stepped); 1 -> 3 moved it 2.3 cm in
one step, and 3 -> 60 then moved it 0.0 m.
**What to do:** step every frame in order (`for f in range(start, end + 1): scene.frame_set(f)`) or bake, before reading
any frame.
**How it was found:** measured here.

### Baking headless: ptcache.bake needs the point cache in the context; bake_all does not
**What happens:** in background mode `bpy.ops.ptcache.bake` has no physics panel to take the cache from, so its poll fails;
given `point_cache` through `temp_override` it bakes. `ptcache.bake_all` needs nothing. A bake equals stepping exactly.
**Evidence:** Re-checked here `[exp: experiments/simulation/cloth_bake.py]`: without the override "Operator
bpy.ops.ptcache.bake.poll() failed, context is incorrect"; with it FINISHED in 1.05 s for 60 frames of a 961-point sheet,
max difference from stepping 0.0 m; `bake_all` 1.04 s, 0.0 m; the scene's frame was back at 1 after the bake.
**What to do:** `with bpy.context.temp_override(point_cache=mod.point_cache): bpy.ops.ptcache.bake(bake=True)`.
**How it was found:** measured here; the project baked with `bake_from_cache` after stepping.

### rest_shape_key does not set the springs' rest lengths; shrink_min and Dynamic Mesh do
**What happens:** a cloth whose `rest_shape_key` points at a smaller shape key still rests at the mesh as placed. The
springs take their rest lengths from the mesh at the first frame. `shrink_min` scales the rest; with `use_dynamic_mesh`
the rest follows the modifier stack above the cloth each frame (so an animated shape key or modifier does change it).
**Evidence:** a 1 m square with a half-size rest key, no gravity, 60 frames: still 1.0 m wide with the key added before or
after the modifier, with Dynamic Mesh and with soft springs; `shrink_min` 0.5 gave 0.5 m. Every construction the project
had built on a rest key (a flat rest for a flared skirt, a gathered rest, a cone) had never acted. Re-checked here
`[exp: experiments/simulation/cloth_rest_shape.py]`: rest key "half" -> 1.0 m wide; with a third key after it 1.0;
pointing at a 2x key 1.0; with Dynamic Mesh 1.0; `shrink_min` 0.5 -> 0.5; Dynamic Mesh with the half key's value keyed
0 -> 1 over frames 1-30 -> 0.5 m; the same keyed key without Dynamic Mesh -> 1.0 m. A mesh with shape keys reports
`rest_shape_key` as Basis by default.
**What to do:** shape the rest by placing the mesh in that shape before the first frame, by `shrink_min`/`shrink_max`
(with a vertex group for part of it), or by Dynamic Mesh with the shape driven above the cloth.
**How it was found:** a staged-rest experiment changed nothing to the unit; a minimal square then showed the key ignored.

### Cloth rests in the shape it was placed in
**What happens:** because the springs rest at the placed mesh, a full skirt or flare keeps whatever shape it started in:
placed as an open cone it pools in stiff fins; placed folded round a small core, the folds come back as regular pleats.
Adding girth only deepens the remembered folds, and gravity alone hangs a flare in vertical folds.
**Evidence:** a floor-length flared trouser placed in folds: adding girth (3.4 -> 5.0 m a leg) moved its floor spread from
0.40 to 0.45 of the figure's height against the photo's 0.75; bending stiffness x4 to x100 kept it a column. Laying the
lower part out on the floor with a shape key as the pose began raised the spread to 0.54 (median of 3 drapes; a second
design 0.30 -> 0.47 against 0.66). (not re-checked here)
**What to do:** place cloth in the shape it should rest in; lay out a sweep on the floor rather than expecting it to fall
into one; for a standing flare, give it something to stand on (next lesson).
**How it was found:** a dozen rounds on one flared garment, judged by eye and by the outline's widths.

### A flare stands only on a support that grips it
**What happens:** a full flare hangs straight down however wide it is cut; a collider under it (a petticoat cone) holds
the spread, but only if the cloth's friction on it is high enough not to creep.
**Evidence:** a cone collider sized from the photo's flare widened the standing shape 21-30 cm between 10 and 50 cm up; at
the collider's default friction 5 the cloth crept over it and never settled (58 mm p95 movement in 240 frames); at
friction 40, with the floor at 40, it settled by frame 115 and kept the width. (not re-checked here)
**What to do:** an invisible support collider with friction around 40.
**How it was found:** the flare's settle measure never passed at the default grip.

### vertex_group_self_collisions excludes its points
**What happens:** Blender's own tooltip says it: "Triangles with all vertices in this group are not used during self
collisions". A group meant to say "self-collide only here" does the opposite.
**Evidence:** two squares 3 cm apart in one cloth, the lower pinned, self-collision 5 mm: no group, the upper rests 7.9 mm
above the lower; every point in the group, it falls 5 m through. Five groups in the project had been set the wrong way
round. Re-checked here `[exp: experiments/simulation/cloth_self_collision.py]`: no group 7.9 mm; every point, the lower
square only, or the upper square only in the group: -5,035 mm (through).
**What to do:** to self-collide only on part of a cloth, put the complement of that part in the group.
**How it was found:** reading the property's description while debugging a blow-up, then a three-square probe.

### Self-collision keeps cloth moving when its distance passes about 0.37 of the edge length
**What happens:** with `self_distance_min` large against the mesh's edges, neighbouring points sit inside each other's
self-collision distance and the solver keeps pushing them: the cloth never comes to rest, with no second layer anywhere.
**Evidence:** a buckling hung sheet, p95 point speed at the end (at rest means under 0.5 mm a frame): on a 12 mm grid
4 mm gave 0.02, 4.5 mm 0.69, 5 mm 7.87; on a 20 mm grid 5 mm gave 0.01. Friction 0 or 40, air damping 5, impulse clamp 0.2
and quality 24 did not stop it. Re-checked here `[exp: experiments/simulation/cloth_self_collision.py]`, 120 frames:
12 mm grid 4 mm 0.029, 4.5 mm 4.02, 5 mm 8.05; 20 mm grid 5 mm 0.016; self-collision off 0.013.
**What to do:** set the self distance from the mesh's shortest edges (under about a third of them), not from how thick the
cloth should look.
**How it was found:** a garment under whole-cloth self-collision never met the settle rule; a minimal sheet isolated it.

### A pooled hem under whole-cloth self-collision never quite settles
**What happens:** floor-length cloth folded onto itself on the floor creeps without end; every setting lowers the creep and
none removes it.
**Evidence:** about 20 variants (air damping 5-10, floor friction 40-80, self distance 2-4 mm, bending x2-3, shear x5, grid
20-28 mm, floor thickness 4-20 mm, 200-700 frames) all levelled off near 0.6 mm a frame; net movement grew without bound
but slowing (p95 3.6 mm at frame 220, 20.5 mm at 740). Self friction 80 made it worse. Without self-collision the same
drape had 174,912 crossing triangle pairs against 32 with it. (not re-checked here)
**What to do:** accept a looser settle rule for pooled cloth, or keep the pooled part out of self-collision and check
crossings separately.
**How it was found:** a settle rule (p95 under 0.5 mm a frame for 10 frames) that one garment never met.

### Whole-cloth self-collision is expensive
**What happens:** self-collision tests every triangle pair near each other each step.
**Evidence:** a full flared garment: about 34 s a frame, 853 s for a 25-frame stage; a drape hit a 90-minute limit.
Re-checked here `[exp: experiments/simulation/cloth_self_collision.py]`: a 2,924-point sheet at quality 12 and collision
quality 8 took 0.065 s a frame without and 0.665 s with self-collision at 5 mm (10x).
**What to do:** turn it on only where cloth meets itself (slits, folded sleeves, pooled hems), via the group's complement.
**How it was found:** timing; a drape hitting its time limit.

### A start state that already crosses itself explodes under self-collision
**What happens:** if the first frame has cloth through cloth, self-collision tries to push the layers apart from the wrong
side and the simulation blows up; springs pulling a placed shape toward a different rest also drag it through itself.
**Evidence:** a shape key added at the start moved points up to 270 mm at frame 1; the cloth had 7,787 crossing triangle
pairs before anything moved (the saved drape: 109), and the drape blew up (p95 675 mm a frame). With no gravity a cloth
pulled 6-12 cm toward its rest gained crossings in proportion to how far it travelled. (not re-checked here)
**What to do:** count crossings at frame 1 (`BVHTree.overlap` of the cloth with itself) before simulating.
**How it was found:** a per-frame trace from frame 1 showed the crossings were there before the solver ran.

### Zero-length edges make cloth explode, and the trigger looks random
**What happens:** two points on one spot are an infinitely stiff spring. Whether it blows up depends on tiny geometric
differences, so the failures look random.
**Evidence:** every drape of one run exploded at every solver quality; 0.03 mm in a hem decided whether a test exploded.
Five theories (sewing force, impulse clamping, collision passes, pre-closing seams, wrist caps) were tested and dropped
before the shortest edge was measured. A collar meshed at 8 mm inside a 15 mm garment also blew a drape up (seams 15 m
apart). (not re-checked here)
**What to do:** before simulating, report the shortest edge and merge edges shorter than about 0.3 of the mesh
resolution; fail a mesh with an edge under 0.5 mm; keep one resolution per garment.
**How it was found:** after the five theories failed, the mesh itself was measured.

### Cloth that starts inside a collider is shoved, and no cloth setting fixes it
**What happens:** points that begin inside a collision surface are pushed out with a steady force at every step, lifting
or dragging the whole cloth.
**Evidence:** a garment's hem rose 23 cm above where it was cut; its back started 2.5 cm inside the collider at the hip
and 5 cm at the shoulders, because the body had stray faces (a 27 cm "rod" at each hip). After cleaning, the lift fell to
about 7 cm. Pushing points clear one by one made the drape blow up; heavy damping barely changed anything (the force was
steady, not momentum). Sleeves placed 4 cm deep in the shoulder shrank from the wrist to 0.37 m while seams closed.
(not re-checked here)
**What to do:** before any drape, check every point is outside every collider (the body, the proxy, every garment
underneath), by ray parity or a closed proxy's signed distance; place sleeves by where a ray leaves the body.
**How it was found:** hem height traced after each stage, then collision and sewing switched off one at a time.

### A collider with a mirrored transform is inside out and pulls cloth in
**What happens:** an object whose matrix has a negative determinant has its normals flipped; the cloth solver then treats
the inside as outside and draws cloth toward it.
**Evidence:** an ellipsoid hand collider built from a left-handed basis (determinant -1) hitched a skirt up at both hands,
with friction 15 or 0.5; two studies were void. An x-ray render looked right. (not re-checked here)
**What to do:** assert `matrix_world.determinant() > 0` for every collider you build.
**How it was found:** printing the collider's matrix.

### A double-shelled or open collider makes lumpy cloth; collide against a clean closed proxy
**What happens:** a figure whose skin is two surfaces a few millimetres apart (as some downloaded bodies are) gives the
cloth two collision layers; cloth on it comes out crumpled. Separate colliders for each under-layer are slow.
**Evidence:** three fabric settings changed nothing; draping against a voxel-remeshed proxy of the body fixed the lumps
and ran 4x faster. A garment draped over the body plus the trousers as one remeshed closed surface took 205 s against
1,114 s with the trousers as a separate collider. (not re-checked here)
**What to do:** make the collider a voxel-remeshed, closed copy of the body (and of every garment worn under), with holes
closed before remeshing; see the Remesh lessons in `modifiers.md`.
**How it was found:** fabric settings exhausted, then the collider measured.

### Sewing springs pull but never join, and weak ones lose to friction
**What happens:** `use_sewing_springs` pulls loose edges together up to `sewing_force_max`; below some force, friction
against the body wins and seams stay open. Closed seams are still springs: posing stretches them open again.
**Evidence:** at sewing force 6 sleeve caps stayed up to 28 cm from their armholes (damping and more frames changed
nothing); at 200 every seam closed within 1.4 cm. Seams held by springs at a median gap of 1.6 mm in a drape stretched to
2-13 cm when the arms lowered; welding before posing closed them (open seam length 120 cm -> 0.7 cm on one garment).
(not re-checked here)
**What to do:** sewing force around 200; weld the seams (merge the stitched points) once closed, before posing or motion.
**How it was found:** seam gaps traced per stage and per pair of pieces.

### Let seams close before gravity acts
**What happens:** with gravity on from the first frame the pieces fall before the seams have drawn them together.
**Evidence:** a garment slid off the shoulders; two stages fixed it: seams close with gravity off
(`settings.effector_weights.gravity = 0`), then it falls. (not re-checked here)
**What to do:** stage the simulation: a seam-closing stage without gravity, then the fall.
**How it was found:** by eye, then fixed by staging.

### Thin collision distances lose ground over long clips
**What happens:** small per-frame losses accumulate; over hundreds of frames cloth sinks into a body whose collision
distance is small.
**Evidence:** a 4 mm collision distance over 335 frames let 663 points sink into the body; 6 mm was used for motion.
(not re-checked here)
**What to do:** raise the collision distance for long motion, and measure points inside the body at several frames, not
only the last.
**How it was found:** frames measured through a long clip showed the drift starting at the second pose.

### A fast collider passes through cloth at the default steps; more steps fix it, collision quality does not
**What happens:** a collider that moves far in one frame can carry cloth points inside it between steps.
**Evidence:** Re-checked here `[exp: experiments/simulation/cloth_quality_time.py]`: a 0.3 m sphere driven 1.4 m up
through a 1,681-point sheet in 2 frames: at quality 5 up to 171 points were inside it on frames 1-8 (collision quality 2)
and 166 (collision quality 8); at quality 20, none. No points were left inside by frame 40 in any case.
**What to do:** raise `quality` (steps per frame) for fast motion; collision quality alone did not help here.
**How it was found:** measured here.

### Cloth cost: steps, collision quality and point count
**What happens:** time per frame rises with quality and point count, less than in proportion at low quality.
**Evidence:** Re-checked here `[exp: experiments/simulation/cloth_quality_time.py]`, a sheet over a sphere, 40 frames:
1,681 points at quality 2 / 5 / 10 / 20: 0.015 / 0.035 / 0.064 / 0.111 s a frame; at quality 5, 441 / 1,681 / 6,561
points: 0.011 / 0.035 / 0.157 s; collision quality 1 / 2 / 5: 0.029 / 0.035 / 0.049 s. In the project a garment drape at a
1.5 cm grid took about 200 s, and a drape job peaked at 0.5-1.4 GB from a 15 mm to a 7 mm grid.
**What to do:** budget from these; the default quality is 5 and collision quality 2 `[inv]`.
**How it was found:** timing.

### Cloth needs time to stop moving; damping after the fall settles it without moving where it lands
**What happens:** a draped piece can still be moving well after the frame a script assumes it has settled; raising air
damping during the fall changes where it lands, raising it after the fall only calms it.
**Evidence:** a scarf-like strip read at frame 87 was still moving 11-16 mm a frame (assumed settled by 60), and a 1 %
nudge of its placement swung its lean between 6 and 16 degrees. Read at frame 170 with air damping raised five times
after the fall, it moved 1-2 mm a frame and the same nudges left the lean at 1.9-4.7 degrees. Damping raised during the
fall let a long end land far behind the figure, held by friction as a taut sheet at 42 degrees. (not re-checked here)
**What to do:** measure the p95 point speed before reading a result (the project used under 0.5 mm a frame for 10
frames); raise `air_damping` (key it) after the cloth has landed.
**How it was found:** small placement changes gave large, inconsistent shape changes.

### Two drapes of the same cut differ; judge cloth on several
**What happens:** folds land differently with tiny changes in start or timing.
**Evidence:** two drapes of the same garment differed by 2.1 % median and 12.5 % at p90 per landmark measurement, from
folds alone; the project judged on the median of 3. Re-runs with identical inputs were bit-identical (see
`running.md`), so the spread comes from changed inputs, not from the solver. (not re-checked here)
**What to do:** compare garment settings on the median of several drapes with small perturbations.
**How it was found:** a noise table before setting tolerances.

### Drape in an A-pose, then bring the figure into its pose with the cloth simulated
**What happens:** arms hanging where side seams go catch the cloth; draping with arms raised and then lowering them over
many frames lets underarms and sleeves fold.
**Evidence:** cloth caught along the arms until the drape used an A-pose (arms raised 40 degrees); easing into a fitted
pose over 80 frames instead of 60 (120 in all) was adopted. Blender's manual gives the same advice for character cloth:
put the cloth on before the motion starts and bring it into the start pose over several frames. (not re-checked here)
**What to do:** drape in a rest pose that keeps limbs clear, then animate into the pose with the cloth running.
**How it was found:** garments caught on arms in the first sewn drapes.

### Long motion drifts when everything is simulated; skin the fitted parts
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
**What happens:** cloth at its simulation spacing renders as hard facets; a Solidify and Subdivision after the cloth fix
it, but adding them after simulating throws the unbaked cache away (lesson above).
**Evidence:** folds at a 1.5 cm spacing rendered as shards until motion renders got the same thickness and smoothing as
stills; adding them after simulating rendered unsimulated cloth on every frame. Re-checked here
`[exp: experiments/simulation/cloth_cache_invalidation.py]`: a Subdivision added after the cloth cut the cache from 40 to
10 frames, even at levels 0.
**What to do:** add Solidify/Subdivision after the cloth in the stack before the first frame, or bake first.
**How it was found:** every frame measured alike ("a measure identical in every frame is broken, not good news").
