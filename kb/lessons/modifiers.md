# Lessons: modifiers

From a project that layered Armature, weight, Cloth, Solidify, Subdivision, Mask, Data Transfer, Surface Deform and Remesh
modifiers on garments and human figures in Blender 4.5.14.

---

### In background mode the evaluated mesh follows show_viewport, so render-only modifiers stay out of what you read
**What happens:** `obj.evaluated_get(depsgraph)` in a `-b` job uses viewport visibility: a modifier with
`show_viewport = False` and `show_render = True` renders but is absent from `evaluated_get(dg).to_mesh()`.
**Evidence:** the project made thickness and smoothing render-only so its measurements read the cloth's own points.
(not re-checked here)
**What to do:** make look-only modifiers render-only; to read only some modifiers, toggle `show_viewport` on the others
and `view_layer.update()`, but only after any cloth is baked (`cloth.md`).
**How it was found:** measurements that disagreed with renders.

### A Mask modifier hides geometry from everything that reads the evaluated mesh
**What happens:** collisions, Data Transfer, BVH trees built from the evaluated mesh and measurements all see the masked
mesh.
**Evidence:** a figure measured with its skin mask on gave sleeves eight times too wide ("giant puffs"); weights copied
from a masked body came only from the hands and neck (sleeves stretched x59 when posed); a masked torso had holes a joint
solve fell through. (not re-checked here)
**What to do:** turn masks off (`show_viewport = False`) on colliders while simulating and while copying weights or
measuring; measure from the rest mesh; place the Mask after Corrective Smooth (which needs every vertex) and before
Subdivision.
**How it was found:** the same trap found three times in different places.

### Data Transfer of weights reads the source's evaluated mesh, armature and mask included
**What happens:** if the source still has its Armature on, weights are matched against the posed body; with its Mask on,
hidden points are missing.
**Evidence:** with the Mask on, only hands and neck were left to copy from. The working setup: create the target groups by
name; `DATA_TRANSFER` with `use_vert_data=True`, `data_types_verts={'VGROUP_WEIGHTS'}`,
`vert_mapping='POLYINTERP_NEAREST'`, `layers_vgroup_select_src='ALL'`, `layers_vgroup_select_dst='NAME'`; the source's
ARMATURE and MASK `show_viewport = False`, `view_layer.update()`, then apply. (not re-checked here)
**What to do:** as above; the same applies to a Shrinkwrap (`wrap_mode='OUTSIDE'`) that pushes cloth out of a body.
**How it was found:** sleeves that stretched when the arm moved.

### Add every modifier the cloth's result needs before simulating
**What happens:** adding a modifier to a simulated object afterwards throws its unbaked cloth cache away (see `cloth.md`).
**Evidence:** render modifiers added after the simulation made every frame render unsimulated cloth. Re-checked here
`[exp: experiments/simulation/cloth_cache_invalidation.py]`: a Subdivision added after the cloth cut the cache from 40 to
10 frames.
**What to do:** build the whole stack (Armature -> Vertex Weight Mix / Hook -> Cloth -> Solidify -> Subdivision) before
the first `frame_set`; reorder with `modifier_move_to_index` inside `temp_override(object=o, active_object=o)`.
**How it was found:** a measure identical on every frame.

### Solidify and Subdivision keep the original vertices first
**What happens:** index i of the evaluated mesh after Solidify or Subdivision is still original vertex i, so points can be
read by index through them.
**Evidence:** relied on in the project's code; it also switched them off before reading, the safer course. (not re-checked
here)
**What to do:** read by index through them only if you must; otherwise switch them off and update first.
**How it was found:** code that read trim positions through the stack.

### Two-sided cloth from one Solidify, with material_offset for the inside
**What happens:** Solidify's shell takes materials at index + `material_offset` (and the rim at `material_offset_rim`); if
the material list changes later, the offsets point at the wrong materials.
**Evidence:** every look render once had the sleeves and back in the front's maps after the material list changed. The
working setup: recalculate normals outward; append a darker "-inner" copy of each of the n materials and shift faces by
+n; `thickness=0.0018`, `offset=1.0`, `use_rim=True`, `material_offset = material_offset_rim = -n`; rebuild the offsets
whenever materials change. The inner copy at 0.82 brightness. (not re-checked here)
**What to do:** as above.
**How it was found:** wrong maps on look renders.

### The Solidify modifier with even offset off has no spikes; bmesh.ops.solidify does
**What happens:** `bmesh.ops.solidify`'s even-thickness offset divides by the fold angle, so where cloth folds back on
itself points shoot far off; the Solidify modifier with `use_even_offset = False` does not.
**Evidence:** on one draped tunic 59 points landed more than 3 cm off the cloth, the farthest 1.08 m; on trousers 107, the
farthest 59 m. A voxel remesh turned them into thin phantom sheets (the shell had 169,508 points; 23,590 without them), and
a scarf hung on them (its front end 13.2 % of the figure's height above the floor; 0.6 % without them). (not re-checked
here)
**What to do:** `SOLIDIFY` with `use_even_offset=False`, `offset=-1.0`, `use_rim=True`, then read the evaluated mesh.
**How it was found:** a scarf hanging in mid-air; a rule that looked for what it hung on found something 1.31 m up.

### A voxel Remesh needs a closed shell; with holes it keeps fragments
**What happens:** with open holes the voxel remesh falls apart and keeps only disconnected pieces.
**Evidence:** a male figure with 56 long-edged faces deleted and left open: the remesh kept only his shins, and every
garment read as "flown off the body"; holes wider than 16 sides left unfilled gave a 1,182-point leg fragment. After
filling, the proxy had 39k points head to foot. (not re-checked here)
**What to do:** `bmesh.ops.holes_fill(bm, edges=boundary_edges, sides=N)` before remeshing; check the result's height span
against the source and, if short, fill every hole (`sides=0`) and remesh again.
**How it was found:** every garment flagged as flown off.

### A voxel Remesh drops a slab thinner than one voxel, and shrinks thin sheets
**What happens:** a single-sided sheet has no inside; a thin slab narrower than the voxel size drops out where it stands
off the body, and the remesh's smoothing shrinks thin layers.
**Evidence:** a 6 mm slab under 12 mm voxels dropped out and let a scarf through a tunic at the waist and hip (75-152
crossing faces against 0); at 15 mm, 0-1. Garments worn under another were fused as a 12 mm slab after the remesh's
smoothing had shrunk them inside the real cloth (cream trousers showed through a hole). (not re-checked here)
**What to do:** thicken sheets into a slab at least one voxel thick before remeshing (15 mm for 12 mm voxels).
**How it was found:** crossings counted with `BVHTree.overlap` after a render showed grey through the scarf.

### Surface Deform carries a garment to another body in about a second, as a grading
**What happens:** bound to one body's surface, a garment follows when that surface is moved point by point onto another
body; it is resized with the body (graded), not re-draped.
**Evidence:** garments carried from a 1.609 m figure onto a 1.753 m one in 1.2 s against about 6 min for a drape; 1 and 0
points inside the new body; edges 1.06-1.07x their length at the median, 1.22-1.30x at p95. A scarf's free end, bound to
far parts of the body, tore (p95 4.9x, 96 points inside). (not re-checked here)
**What to do:** use it for fitted garments; re-drape loose parts. `surfacedeform_bind` needs
`temp_override(object=o, active_object=o, selected_objects=[o])`; check `mod.is_bound` afterwards: the bind fails on
crumpled quads or a hem spread on the floor (see `geometry-nodes.md` for a node follower that always binds).
**How it was found:** carrying a library of garments between figures.

### correctivesmooth_bind toggles: on a bound modifier it unbinds
**What happens:** after the rest mesh changes, one call removes the old bind instead of rebinding.
**Evidence:** relied on in the project's re-rest code. (not re-checked here)
**What to do:** call `bpy.ops.object.correctivesmooth_bind(modifier=name)` twice (unbind, then bind) when
`rest_source == 'BIND'`; `rest_source = 'ORCO'` needs no bind.
**How it was found:** a stale bind after re-resting a figure.

### Line Art is cheaper than Freestyle but jitters more between frames and fills fine strands
**What happens:** the Line Art modifier and Freestyle both ink contours; they differ in cost, stability and what they do
with fine detail.
**Evidence:** at 480 x 600, three frames orbiting: Line Art 5.0 s a frame against Freestyle 6.4 (no lines 2.6); frame to
frame jitter 25.3 % vs 16.3 % of line pixels, chamfer 1.52 vs 1.15 px, line-pixel count varying 3.2 % vs 0.4 %. Line Art
filled hair strands into a dark mass and drew a thinner, broken body line. Line Art's radius is in world units (metres),
not pixels; Freestyle's crease edges ink every wrinkle of cloth. (not re-checked here)
**What to do:** Freestyle for stable lines on a turn; Line Art where speed matters (4.5: `bpy.data.grease_pencils_v3.new`, a `LINEART` modifier with `source_type='SCENE'`,
`use_contour=True`) with `radius = 0.5 * px * m_per_px`, `m_per_px = 2 * dist * tan(fov / 2) / width`; exclude collections
with `collection.lineart_usage = 'EXCLUDE'`. Freestyle: `select_crease = False`.
**How it was found:** an ink-style look, compared on the same turn.
