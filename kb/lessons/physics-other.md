# Lessons: rigid bodies, soft bodies, simulation zones

From a project that tried Blender 4.5.14's rigid-body solver (Bullet) for small accessories hanging from a garment on a
walking figure (a tassel on short cords), and from experiments in this repository. Numbers are the project's unless a
line says "Re-checked here".

---

### A small hanging chain on point constraints is thrown about by a jerky anchor; the collision margin is not what calms it
**What happens:** the project's first tassel (three 2.5 cm cord pieces on point constraints and a 5 cm tassel, its anchor
riding one vertex of a walking garment) flew up; it attributed this to Bullet's 4 cm default collision margin, larger than
the pieces, and found it calm after setting a 1 mm margin and putting each piece in its own collision group. Re-checked
here, the margin did not reproduce as the cause: what throws such a chain is the anchor's motion.
**Evidence:** project: swing from straight down p50 75 degrees, p95 139 at default settings; p50 18.4, p95 36.3, max 39.5
with a 1 mm margin and a collision group each, the chain within 0.19 mm of its anchor. Re-checked here
`[exp: experiments/simulation/rigid_chain.py]`: the same shapes on POINT constraints from an animated passive anchor.
Swung gently (10 cm over 19 frames): p50 4.3-4.5, max 8.8-9.0 degrees at the default margin, a 1 mm margin, separate
collision collections, both, and with MESH shapes alike. Shaken (5 cm every 3 frames): p50 35.5, p95 70.5 degrees at the
default margin; 44.4 / 82.5 with a 1 mm margin; 39.0 / 90.6 with 1 mm and separate collections. A POINT constraint's
`disable_collisions` is on by default, so joined pieces never collide with each other. What in the project's scene the
fix actually acted on is not known.
**What to do:** smooth the anchor's motion (or hang the chain from a point that moves smoothly) before tuning margins;
check `disable_collisions` on each joint.
**How it was found:** project: tried in a walk; here: rebuilt in a minimal scene with the anchor's motion varied.

### The default collision margin shows as a gap only for MESH shapes
**What happens:** a new rigid body has `collision_margin` 0.04 m with `use_margin` off `[inv]`. For a convex hull, box or
sphere the margin does not show as a gap at the default; a MESH (triangle mesh) shape rests the margin's width above
what it lands on. With `use_margin` on, the set margin is used as a gap.
**Evidence:** Re-checked here `[exp: experiments/simulation/rigid_body.py]`: a 2 cm cube dropped on a passive box, gap
between its bottom and the box top: CONVEX_HULL default 0.0 mm; CONVEX_HULL with `use_margin` and 1 mm, 1.0 mm; BOX
default or 0.04 with `use_margin`, 0.0; SPHERE default 0.0; MESH default 36.6 mm; MESH with 1 mm, 1.0 mm.
**What to do:** for small parts use convex hull or primitive shapes; if a MESH shape is needed, set `use_margin = True`
and a margin of a millimetre or so.
**How it was found:** measured here while re-checking the margin lesson above.

### Rigid bodies are not pushed by cloth, and a deforming collider kicks them
**What happens:** cloth collides with rigid bodies, but the coupling is one way: nothing the cloth does moves a rigid
body. A garment used as Bullet's passive, animated, deforming collider is rebuilt every frame, and cloth moving into a
body kicks it.
**Evidence:** a tassel hung 1.5 cm outside a garment that was Bullet's moving deforming collider was thrown about again
(p50 41 degrees, p95 147). Without the garment as a collider it hung inside the neckline, through the cloth.
(not re-checked here)
**What to do:** for something that rests on cloth, use the cloth solver instead (a short strand pinned at its anchor), or
give the anchor a standoff clear of the cloth.
**How it was found:** six tries in two solvers on one accessory.

### A cloth strand pinned inside another cloth's collision zone is squeezed
**What happens:** a small cloth pinned right at a point on a garment that is its collider starts inside the garment's
collision distance; it is pushed behind the garment or flung about.
**Evidence:** a 14 cm cord and a tapered tassel as cloth, pinned to a garment point, the garment a collider: steady (swing
p50 27-31 degrees, pin exact) but behind the garment's front on every checked frame, even started 1 cm outside; with
three times the steps and stronger collision it was flung about (p50 47, max 90 degrees). (not re-checked here)
**What to do:** anchor small hanging cloth to a point held clear of the collider (a standoff).
**How it was found:** the same accessory study.

### A rigid body world and rigid bodies can be made headless; object_add needs an active object
**What happens:** a new scene has no rigid body world; `bpy.ops.rigidbody.world_add()` makes one in background mode.
`bpy.ops.rigidbody.object_add()` acts on the active object and fails its poll without one; a `temp_override(object=...)`
is enough.
**Evidence:** Re-checked here `[exp: experiments/simulation/rigid_body.py]`: `world_add` FINISHED; `object_add` with no
active object: "Operator bpy.ops.rigidbody.object_add.poll() Context missing active object"; with
`temp_override(object=c, active_object=c, selected_objects=[c])` FINISHED. Defaults `[exp: experiments/simulation/defaults.py]`:
ACTIVE, CONVEX_HULL, mass 1 kg, friction 0.5, restitution 0; the world 10 substeps per frame, 10 solver iterations.
**What to do:** create the world first; add bodies with the object active or overridden.
**How it was found:** measured here.

### Rigid bodies simulate only frame by frame; a bake can be read in any order
**What happens:** like cloth, the rigid body world steps one frame at a time; a jump with nothing cached does not simulate.
Its cache (`scene.rigidbody_world.point_cache`) bakes headless with `ptcache.bake` given the cache in the context.
**Evidence:** Re-checked here `[exp: experiments/simulation/rigid_body.py]`: a box at z = 1 stayed at 1.0 after a jump
from frame 1 to 30 (stepped: 0.1); the bake matched stepping to 0.0 m and read correctly at frames 30, 10, 60, 45 in that
order; 100 convex-hull cubes took 0.0033 s a frame.
**What to do:** step or bake before reading any frame.
**How it was found:** measured here.

### A new soft body holds its shape: its goal is on at 0.7
**What happens:** `use_goal` is on and `goal_default` 0.7 with no goal group, so every point is pulled back to where the
mesh is; a "falling soft body" needs the goal off (or goal 0).
**Evidence:** Re-checked here `[exp: experiments/simulation/soft_body.py]`: an icosphere 0.7 m above a collider plane,
48 frames: default goal, lowest point 0.70 -> 0.63 m; goal 0 or goal off, 0.70 -> 0.015 m (on the plane). It bakes like
cloth: `ptcache.bake` fails its poll without the cache in the context and bakes with `temp_override(point_cache=...)`.
**What to do:** set `obj.soft_body.use_goal = False` for free soft bodies; use a goal vertex group to hold part of one.
**How it was found:** measured here. (The project judged soft body unnecessary for garments: the cloth solver does it better.)

### A simulation zone carries state between frames; jumps advance it by one frame
**What happens:** a geometry-nodes simulation zone built from Python (`GeometryNodeSimulationInput.pair_with_output`)
keeps its geometry from frame to frame when frames are stepped. At the start frame it passes its input through (Delta
Time 0). A jump with nothing cached advances it by only one frame's step.
**Evidence:** Re-checked here `[exp: experiments/simulation/sim_zone.py]`: a cube moved by -Delta Time each frame (1 m/s,
24 fps): lowest z -0.100 at frame 1, -0.142 at 2, -0.600 at 13, -1.308 at 30 (29 steps of 1/24 m); stepping back to 15
read -0.683 from the cache; a jump 1 -> 30 gave -0.142. `object.simulation_nodes_cache_bake(selected=False)`,
the same with `selected=True` in a context override, and `object.geometry_node_bake_single(session_uid=...,
modifier_name=..., bake_id=...)` all finished headless on an unsaved file; the bake read correctly out of order.
**What to do:** step or bake before reading; collisions and solver iterations are yours to build (repeat zones); the
project judged a node solver worth it only for a constraint Blender's cloth lacks.
**How it was found:** measured here.
