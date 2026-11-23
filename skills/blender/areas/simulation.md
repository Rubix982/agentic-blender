# Simulation: cloth, rigid bodies, soft bodies, simulation zones

Blender 4.5.14 LTS on Apple Silicon. Tags: `[inv]` read from Blender (`scripts/kb.py`), `[exp: path]` measured here (the
script and its `results/*.json` are in this repository), `[lesson]` from a real project (`kb/lessons/cloth.md`,
`kb/lessons/physics-other.md`), `[doc: link]` Blender's manual or API reference for 4.5.

## What goes wrong most often

1. **Reading a late frame without simulating the frames before it.** Physics in Blender steps one frame at a time. A cloth
   sent from frame 1 straight to frame 60 takes one solver step stretched over 59 frames: the free cloth fell 4.9 m,
   straight through its collider, where stepping left it resting at z = 0.41 `[exp: experiments/simulation/cloth_bake.py]`.
   A second jump simulates nothing at all. Rigid bodies jumped 1 -> 30 did not move
   `[exp: experiments/simulation/rigid_body.py]`; a simulation zone advanced one frame's worth
   `[exp: experiments/simulation/sim_zone.py]`. Step every frame in order, or bake, before reading any frame.
2. **Touching the simulated object after simulating.** An unbaked (memory) cloth cache loses every frame after the current
   one when the cloth object, its modifier settings or a collider is tagged for update, even by setting a property to the
   value it already has: renaming, `quality = quality`, `hide_render = hide_render`, adding a material slot, adding a
   modifier after the cloth, editing a vertex group `[exp: experiments/simulation/cloth_cache_invalidation.py]`. A project
   rendered unsimulated cloth on every frame of its clips for days because a check toggled visibility per frame
   `[lesson]`. Set everything up first; once simulated, bake (below): the bake survived every change tried.
3. **Calling `bpy.ops.ptcache.bake` headless as if a physics panel were open.** Its poll fails ("context is incorrect")
   until the cache is passed: `temp_override(point_cache=mod.point_cache)`. `ptcache.bake_all` needs nothing
   `[exp: experiments/simulation/cloth_bake.py]`.
4. **Trusting `rest_shape_key`.** The cloth ignores it: a 1 m sheet with a half-size rest key stays 1 m wide.
   `shrink_min` and Dynamic Mesh do change the rest `[exp: experiments/simulation/cloth_rest_shape.py]`.
5. **Reading `vertex_group_self_collisions` as "self-collide here".** It excludes the group's triangles (its tooltip says
   so `[inv]`): with every point in the group, a sheet fell 5 m through another part of the same cloth
   `[exp: experiments/simulation/cloth_self_collision.py]`. Hand it the complement.
6. **Expecting pins to be either all hard or all soft.** Weight 1.0 is held exactly and does not collide; below 1.0 a pin
   is a spring of strength `pin_stiffness` (default 1 of a 0-50 range `[inv]`), which sewing springs pull 15 cm off at
   weight 0.99 and only 3.9 cm at stiffness 50 `[exp: experiments/simulation/cloth_pins.py]`.
7. **A self-collision distance chosen for the look.** Above about 0.37 of the edge length, self-collision keeps a resting
   cloth moving forever: 8 mm a frame at 5 mm on a 12 mm grid, 0.02 at 4 mm
   `[exp: experiments/simulation/cloth_self_collision.py]`.
8. **Assuming a rigid body world exists, or that rigid bodies sit on the ground.** A new scene has none
   (`rigidbody.world_add()`); a MESH-shaped body rests 3.7 cm above what it lands on at the default 4 cm margin
   `[exp: experiments/simulation/rigid_body.py]`.
9. **A soft body that will not fall.** Its goal is on at 0.7 by default, holding every point to the mesh
   `[exp: experiments/simulation/soft_body.py]`.

## Cloth

### Make a cloth with a pinned edge and a collider

From `experiments/simulation/cloth_bake.py` (ran headless in 1 s for 60 frames):

```python
import bpy
sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, 60
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=(0, 0, 0.5))
ball = bpy.context.object
ball.modifiers.new("Collision", "COLLISION")                  # a collider is a Collision modifier
bpy.ops.mesh.primitive_grid_add(x_subdivisions=30, y_subdivisions=30, size=1.0, location=(0, 0, 1.0))
g = bpy.context.object
vg = g.vertex_groups.new(name="pin")
ymax = max(v.co.y for v in g.data.vertices)
vg.add([v.index for v in g.data.vertices if v.co.y > ymax - 1e-6], 1.0, "REPLACE")
cm = g.modifiers.new("Cloth", "CLOTH")
cm.settings.vertex_group_mass = "pin"                         # the pin group
cm.point_cache.frame_start, cm.point_cache.frame_end = 1, 60  # the cache's own range (default 1-250)
```

- Every collider in the scene acts on every cloth unless the cloth's `collision_settings.collection` is set; set to a
  collection holding only a lower plane, a cloth fell through an upper one (mean height 0.034 against 0.534 m)
  `[exp: experiments/simulation/cloth_more.py]`.
- Build the collider as one closed, outward-facing surface. A collider with a negative-determinant transform is inside out
  and pulls cloth toward it; a double-shelled skin makes cloth lumpy; cloth that starts inside a collider is shoved out at
  every step and rides up (a 23 cm hem lift on a garment) `[lesson]`. Check
  `obj.matrix_world.determinant() > 0` and that no cloth point starts inside.
- Check the shortest edge before simulating: two points on one spot are an infinitely stiff spring and "random"
  explosions follow; the project merged edges under 0.3 of the grid spacing and refused edges under 0.5 mm `[lesson]`.

### Simulate and read the result

Step every frame, then read the evaluated mesh (the original mesh never moves). From the same experiment:

```python
import numpy as np
for f in range(1, 61):
    sc.frame_set(f)

def coords(o):
    dg = bpy.context.evaluated_depsgraph_get()
    e = o.evaluated_get(dg)
    me = e.to_mesh()
    a = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", a)
    e.to_mesh_clear()
    a = a.reshape(-1, 3)
    return (np.array(o.matrix_world)[:3, :3] @ a.T).T + np.array(o.matrix_world)[:3, 3]
```

Going back to a frame already simulated reads the cache (0.0 s) `[exp: experiments/simulation/cloth_bake.py]`. Read a
drape when it has stopped moving, not at a fixed frame: the project's rule was p95 point speed under 0.5 mm a frame for
10 frames, with a frame cap; a scarf assumed settled at frame 60 still moved 11-16 mm a frame at 87 `[lesson]`.

### Bake headless

Three calls work in background mode; all gave the stepped result exactly (max difference 0.0 m)
`[exp: experiments/simulation/cloth_bake.py]`:

```python
with bpy.context.temp_override(point_cache=cm.point_cache):
    bpy.ops.ptcache.bake(bake=True)            # this cache; FINISHED, 1.05 s for 60 frames of 961 points

bpy.ops.ptcache.bake_all(bake=True)            # every cache in the scene, no override needed
bpy.ops.ptcache.free_bake_all()                # clears them

# after stepping frames yourself: keep what is in memory as a bake
with bpy.context.temp_override(point_cache=cm.point_cache):
    bpy.ops.ptcache.bake_from_cache()          # is_baked becomes True
```

`ptcache.bake` without the override: "Operator bpy.ops.ptcache.bake.poll() failed, context is incorrect". After a bake
the scene's frame is back at the start. A baked cache is protected; "you will be unable to change the simulation settings
until you clear the bake" `[doc: https://docs.blender.org/manual/en/4.5/physics/baking.html]`. The info line
(`point_cache.info`) says what the cache holds: "60 frames in memory (2.0 MiB)." or, after an edit, "10 frames in memory
(156 KiB), cache is outdated!".

### What throws an unbaked cache away

Stepped 40 frames, gone back to frame 10, one change, then frame 30 compared
`[exp: experiments/simulation/cloth_cache_invalidation.py]`:

| change at frame 10 | unbaked cache | baked (`bake_from_cache`) |
|---|---|---|
| `frame_set` to the current frame, `view_layer.update()`, `select_set` | kept (40 frames) | kept |
| an unrelated camera's location, render resolution, a new object added | kept | kept |
| an existing material's Base Color value edited | kept | kept |
| cloth object renamed | lost (10 frames left; frame 30 off by 0.25 m) | kept |
| `settings.quality` or `settings.mass` set to its own value | lost | kept |
| `hide_render` set to its own value; `hide_viewport` toggled | lost | kept |
| the collider's location set to its own value | lost | kept |
| a material slot added to the cloth | lost | kept |
| a Subdivision modifier added after the cloth (even at levels 0) | lost | kept (40 frames) |
| a pin-group weight edited | lost | kept |

So: add render modifiers (Solidify, Subdivision after the cloth), materials and visibility settings before the first
frame. A measure that runs during a clip must not touch the scene; if it must pose points, compute them from bone
matrices (the project matched the Armature modifier to 1.7 mm that way) `[lesson]`.

### Pins

Pin weight 1.0 holds a point exactly; below it the pin is a spring `[exp: experiments/simulation/cloth_pins.py]`:

| test | weight 1.0 | 0.99 | 0.9 | 0.5 |
|---|---|---|---|---|
| sheet pinned everywhere, gravity, sag (stiffness 1) | 0.0 mm | 0.2 mm | 0.2 mm | 2.4 mm |
| seam edge pulled by sewing springs (max 200), stiffness 1 | 0.0 cm | 15.3 cm | 16.1 cm | 19.2 cm |
| the same, stiffness 50 | 0.0 cm | 3.9 cm | 4.9 cm | 12.4 cm |
| lag behind the object's animation at frame 6, stiffness 1 / 50 | 0 / 0 | | 2.3 / 1.4 cm | |

Fully pinned points also ignore colliders: a sphere pushed into a sheet pinned at 1.0 ended with 109 points inside it;
at 0.9, 24; at 0.5, none `[exp: experiments/simulation/cloth_more.py]`. In practice: weight 1.0 where cloth must not
move, `pin_stiffness` near 50 where pins fade out, and below 1.0 where a hand or collider must push the cloth. The project
cut a taut "tent" from 257 to 156 stretched edges with stiffness 50 `[lesson]`.

Pins are read every frame from the modifiers above the cloth, so a keyed Vertex Weight Mix lets them go mid-run (the row
stayed put to frame 19 and fell 3.4 cm by 21) `[exp: experiments/simulation/cloth_pins.py]`:

```python
mix = g.modifiers.new("release", "VERTEX_WEIGHT_MIX")
mix.vertex_group_a = "pin"
mix.default_weight_b = 0.0
mix.mix_mode = "SET"
mix.mix_set = "ALL"
mix.mask_constant = 0.0          # 0: no effect, the pin stays
mix.keyframe_insert("mask_constant", frame=19)
mix.mask_constant = 1.0          # 1: weight a replaced by b (0): the pin is let go
mix.keyframe_insert("mask_constant", frame=20)
# the cloth must come after the weight modifier in the stack
bpy.context.view_layer.objects.active = g
with bpy.context.temp_override(object=g):
    bpy.ops.object.modifier_move_to_index(modifier="release", index=0)
```

### Rest shape

| how | 1 m sheet, no gravity, 60 frames, end width | |
|---|---|---|
| nothing | 1.0 m | |
| `rest_shape_key` = a half-size key | 1.0 m | ignored; also with a third key, a 2x key, or Dynamic Mesh |
| `shrink_min = 0.5` | 0.5 m | |
| `use_dynamic_mesh = True`, the half key's value keyed 0 -> 1 over frames 1-30 | 0.5 m | the rest follows the stack above the cloth |
| the same keyed key without Dynamic Mesh | 1.0 m | |

`[exp: experiments/simulation/cloth_rest_shape.py]`. A mesh with shape keys reports `rest_shape_key` as Basis. Cloth
otherwise rests at the shape it was placed in: a flare placed folded keeps its folds as pleats, and adding girth only
deepens them `[lesson]`.

### Self-collision only where cloth meets itself

```python
g = o.vertex_groups.new(name="g")           # the triangles NOT to self-collide
...
cs = cm.collision_settings
cs.use_collision = False
cs.use_self_collision = True
cs.self_distance_min = 0.005                # keep under ~1/3 of the mesh's edge length (here 27 mm squares)
cs.vertex_group_self_collisions = "g" if mode != "no group" else ""
```

Measured `[exp: experiments/simulation/cloth_self_collision.py]`: two squares 3 cm apart in one cloth, lower pinned: no
group, the upper rests 7.9 mm above; every point, the lower only, or the upper only in the group: it falls through
(-5,035 mm). A folded sheet's p95 speed over its last 20 of 120 frames (at rest under 0.5 mm a frame):

| grid | self distance | ratio | mm a frame | s a frame (2,924 points, quality 12) |
|---|---|---|---|---|
| 12 mm | off | | 0.013 | 0.065 |
| 12 mm | 4 mm | 0.33 | 0.029 | 0.236 |
| 12 mm | 4.5 mm | 0.375 | 4.02 | 0.299 |
| 12 mm | 5 mm | 0.42 | 8.05 | 0.665 |
| 20 mm | 5 mm | 0.25 | 0.016 | 0.039 |

Self-collision cost 10x here. A pooled floor-length hem under whole-cloth self-collision never settled below about
0.6 mm a frame in about 20 settings tried `[lesson]`. Count crossings at frame 1 before simulating: a start that already
crosses itself blows up under self-collision `[lesson]`.

### Sewing

Loose edges (edges with no faces) between pieces become sewing springs. From
`experiments/simulation/cloth_pins.py` (two squares, a seam of 11 loose edges):

```python
for j in range(n):
    edges.append((idx[("A", n - 1, j)], idx[("B", 0, j)]))   # the seam: loose edges, no faces
me = bpy.data.meshes.new("sewn")
me.from_pydata(verts, edges, faces)
...
st = cm.settings
st.vertex_group_mass = "pin"
st.pin_stiffness = stiff
st.effector_weights.gravity = 0.0
st.use_sewing_springs = True
st.sewing_force_max = 200.0      # default 0 = no limit [inv]
```

Springs pull but never join: weld the seam once closed, before posing. A weak force loses to friction against the body
(caps 28 cm off at 6, within 1.4 cm at 200); close seams with gravity off, then let the cloth fall `[lesson]`. Keyframes on
`sewing_force_max` act: keyed 200 -> 1 at frame 2 ended like a constant 1 (19.9 cm gap), keyed 1 -> 200 like a constant
200 (15.2 cm); gravity keys act too (`effector_weights.keyframe_insert("gravity", ...)`)
`[exp: experiments/simulation/cloth_more.py]` (a project note said the sewing force ignored keys; not reproduced).

### Quality, cost and fast colliders

`[exp: experiments/simulation/cloth_quality_time.py]`, a sheet dropped over a sphere, 40 frames:

| points | quality | collision quality | s a frame |
|---|---|---|---|
| 1,681 | 2 / 5 / 10 / 20 | 2 | 0.015 / 0.035 / 0.064 / 0.111 |
| 1,681 | 5 | 1 / 2 / 5 | 0.029 / 0.035 / 0.049 |
| 441 / 1,681 / 6,561 | 5 | 2 | 0.011 / 0.035 / 0.157 |

A sphere driven 1.4 m up through the sheet in 2 frames had up to 171 cloth points inside it at quality 5 (166 with
collision quality 8) and none at quality 20: raise `quality` for fast colliders. Mass is per vertex `[inv]`, so a finer
grid of the same settings droops more (a 12 cm strip: 8.5 vs 10.2 cm at 15 and 7.5 mm); scaling the mass by the cell area
over-corrected here (3.6 cm) `[exp: experiments/simulation/cloth_more.py]`: re-measure a reference strip when the grid
changes.

## Rigid bodies

```python
bpy.ops.rigidbody.world_add()                         # a new scene has none
sc.rigidbody_world.point_cache.frame_end = N
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, -1.0))
ground = bpy.context.object
bpy.ops.rigidbody.object_add(type="PASSIVE")          # acts on the active object
ground.rigid_body.collision_shape = "BOX"
bpy.ops.mesh.primitive_cube_add(size=0.02, location=(0, 0, 0.10))
cube = bpy.context.object
bpy.ops.rigidbody.object_add(type="ACTIVE")
cube.rigid_body.collision_shape = "CONVEX_HULL"
```

From `experiments/simulation/rigid_body.py`. With no active object, `object_add` fails: "Context missing active object";
`with bpy.context.temp_override(object=c, active_object=c, selected_objects=[c]):` is enough. Bake the world's cache with
`temp_override(point_cache=sc.rigidbody_world.point_cache)` and `ptcache.bake(bake=True)`; the bake matched stepping
exactly and read correctly out of order. 100 convex-hull cubes: 0.0033 s a frame.

**The collision margin.** A 2 cm cube dropped on a passive box; gap left under it
`[exp: experiments/simulation/rigid_body.py]`:

| shape | margin | gap |
|---|---|---|
| CONVEX_HULL, BOX, SPHERE | default 0.04, `use_margin` off | 0.0 mm |
| CONVEX_HULL | `use_margin`, 0.001 | 1.0 mm |
| MESH | default 0.04 | 36.6 mm |
| MESH | `use_margin`, 0.001 | 1.0 mm |

This is the manual's rule: the margin is embedded for sphere, box, capsule, cylinder and convex hull, and not for cone
and active triangle mesh `[doc: https://docs.blender.org/manual/en/4.5/physics/rigid_body/properties/collisions.html]`.

**Joints.** `bpy.ops.rigidbody.constraint_add(type="POINT")` on an empty, then set `object1` and `object2`; its
`disable_collisions` is on by default `[exp: experiments/simulation/rigid_chain.py]`. A chain of 2.5-5 cm pieces hanging
from an animated (`kinematic = True`) anchor swung 4.5 degrees at p50 when the anchor moved gently and 35-44 when it was
shaken, whatever the margin or collision collections; calm the anchor before tuning margins. Cloth does not push rigid
bodies (the coupling is one way), and a deforming mesh used as a passive collider kicks small bodies `[lesson]`.

## Soft bodies

```python
sm = s.modifiers.new("Softbody", "SOFT_BODY")
s.soft_body.use_goal = False     # on by default with goal_default 0.7: the body holds its shape in place
sm.point_cache.frame_start, sm.point_cache.frame_end = 1, N
```

An icosphere 0.7 m above a collider: default goal, lowest point 0.70 -> 0.63 m in 48 frames; goal 0 or off, to 0.015 m on
the plane. It bakes like cloth, with `temp_override(point_cache=sm.point_cache)` `[exp: experiments/simulation/soft_body.py]`.
"A Goal value of 1.0 means no soft body simulation" `[doc: https://docs.blender.org/manual/en/4.5/physics/soft_body/forces/exterior.html]`.

## Simulation zones (geometry nodes)

From `experiments/simulation/sim_zone.py`: a cube moved down by Delta Time each frame (1 m/s):

```python
ng = bpy.data.node_groups.new("fall", "GeometryNodeTree")
ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
gi = ng.nodes.new("NodeGroupInput")
go = ng.nodes.new("NodeGroupOutput")
sin = ng.nodes.new("GeometryNodeSimulationInput")
sout = ng.nodes.new("GeometryNodeSimulationOutput")
paired = sin.pair_with_output(sout)
setp = ng.nodes.new("GeometryNodeSetPosition")
comb = ng.nodes.new("ShaderNodeCombineXYZ")
mul = ng.nodes.new("ShaderNodeMath")
mul.operation = "MULTIPLY"
mul.inputs[1].default_value = -1.0            # 1 m per second downward
L = ng.links
L.new(gi.outputs["Geometry"], sin.inputs["Geometry"])
L.new(sin.outputs["Geometry"], setp.inputs["Geometry"])
L.new(sin.outputs["Delta Time"], mul.inputs[0])
L.new(mul.outputs[0], comb.inputs["Z"])
L.new(comb.outputs["Vector"], setp.inputs["Offset"])
L.new(setp.outputs["Geometry"], sout.inputs["Geometry"])
L.new(sout.outputs["Geometry"], go.inputs["Geometry"])
mod = ob.modifiers.new("GN", "NODES")
mod.node_group = ng
```

- Stepped, it carries state: lowest z -0.100 at frame 1 (Delta Time is 0 on the first frame), -0.142 at 2, -1.308 at 30
  (29 steps of 1/24 m). Back at frame 15 it read the cache. A jump 1 -> 30 gave -0.142: one frame's step
  `[exp: experiments/simulation/sim_zone.py]`.
- Inputs linked into the Simulation Input are "evaluated only once, at the beginning of the simulation"; nodes linked in
  from outside are re-evaluated every step `[doc: https://docs.blender.org/manual/en/4.5/modeling/geometry_nodes/simulation/simulation_zone.html]`.
- Baking headless: `bpy.ops.object.simulation_nodes_cache_bake(selected=False)`, the same with `selected=True` inside
  `temp_override(active_object=ob, object=ob, selected_objects=[ob], selected_editable_objects=[ob])`, and
  `bpy.ops.object.geometry_node_bake_single(session_uid=ob.session_uid, modifier_name=mod.name,
  bake_id=mod.bakes[0].bake_id)` all finished on an unsaved file (`bake_target` INHERIT, `bake_directory` empty); the bake
  read correctly out of order `[exp: experiments/simulation/sim_zone.py]`.
- Collisions and constraint iterations (repeat zones) are yours to build; 4.5 ships no node solver `[lesson]`.

## Reference

### Defaults of a new cloth modifier

`[exp: experiments/simulation/defaults.py]`, matching `kb.py struct ClothSettings` `[inv]`:

| setting | default | | setting | default |
|---|---|---|---|---|
| `quality` (steps per frame) | 5 | | `collision_settings.distance_min` | 0.015 m |
| `mass` (per vertex) | 0.3 kg | | `collision_settings.collision_quality` | 2 |
| `air_damping` | 1.0 | | `collision_settings.friction` | 5.0 |
| `tension_stiffness`, `compression_stiffness` | 15 | | `collision_settings.use_self_collision` | False |
| `shear_stiffness` | 5 | | `collision_settings.self_distance_min` | 0.015 m |
| `bending_stiffness` | 0.5 (`bending_model` ANGULAR) | | `collision_settings.impulse_clamp` | 0 (off) |
| `pin_stiffness` | 1.0 (range 0-50) | | `point_cache.frame_start / frame_end` | 1 / 250 |
| `shrink_min`, `shrink_max` | 0, 0 | | `use_dynamic_mesh` | False |
| `sewing_force_max` | 0 (no limit) | | `use_sewing_springs`, `use_internal_springs`, `use_pressure` | False |

A collider (`obj.collision`, from a Collision modifier): `thickness_outer` 0.02, `thickness_inner` 0.2, `cloth_friction`
5, `damping` 0.1, `use_normal` False.

### Defaults of rigid and soft bodies

| | setting | default |
|---|---|---|
| rigid body world | `substeps_per_frame`, `solver_iterations` | 10, 10 |
| rigid body | `type`, `collision_shape` | ACTIVE, CONVEX_HULL |
| | `mass`, `friction`, `restitution` | 1 kg, 0.5, 0 |
| | `collision_margin`, `use_margin` | 0.04 m, False |
| | `linear_damping`, `angular_damping` | 0.04, 0.1 |
| soft body | `use_goal`, `goal_default`, `goal_spring` | True, 0.7, 0.5 |
| | `mass`, `friction`, `use_edges`, `use_self_collision` | 1, 0.5, True, False |

`[exp: experiments/simulation/defaults.py]`

### Baking and caches at a glance

| system | cache | bake headless |
|---|---|---|
| cloth | `cloth_mod.point_cache` | `temp_override(point_cache=...)` + `ptcache.bake(bake=True)`; or `ptcache.bake_all(bake=True)`; or step then `ptcache.bake_from_cache()` |
| soft body | `softbody_mod.point_cache` | as cloth |
| rigid bodies | `scene.rigidbody_world.point_cache` | as cloth |
| simulation zone | the Nodes modifier's `bakes` | `object.simulation_nodes_cache_bake(selected=False)` or `object.geometry_node_bake_single(...)` |

All: frames are simulated in order only; a jump does not fill the gap. Lessons behind this page, with the project's
numbers: `kb/lessons/cloth.md` (40), `kb/lessons/physics-other.md` (10).
