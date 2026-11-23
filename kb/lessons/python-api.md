# Lessons: bmesh, mathutils, BVH trees and the data API

From a project that measured garments and bodies in Blender 4.5.14 with BVH trees, KD-trees and bmesh: crossings, points
inside a body, distances, visibility.

---

### BVHTree.overlap is the exact crossing test; a nearest-face signed distance is not
**What happens:** counting cloth "inside" another cloth by each point's signed distance to the nearest face misreads points
near open edges (hems, slits) as inside; `BVHTree.overlap` between two trees lists the triangle pairs that actually cross.
**Evidence:** the nearest-face proxy reported 21-24 crossings on a garment that crossed nowhere; the overlap test found the
real 75-152 crossing faces that a render had shown. Points with non-finite coordinates cross nothing in a BVH, silently.
(not re-checked here)
**What to do:** `BVHTree.FromPolygons(points, tris, epsilon=0.0)` and `tree.overlap(other)`; for self-crossings drop pairs
that share a vertex; check every coordinate with `math.isfinite` first. Test a new measure where its answer is known (an
asset that crosses nowhere must count 0).
**How it was found:** a measure that disagreed with a render.

### A nearest face's normal is not a reliable inside test; count ray crossings
**What happens:** `find_nearest`'s normal misjudges points near convex edges and behind open sheets, and inconsistent
winding flips the sign outright.
**Evidence:** sleeve points 13 cm from any surface read as 4-14 cm "inside" (14 % of a bell sleeve); "behind" an open sheet
read 43 cm inside; on a head whose faces half pointed inward, hair sunk 5 cm into the skull read as outside and coverage
read 0.5 on a full head of hair. A thin double-shell skin made rays hit twice, 4 mm apart. (not re-checked here)
**What to do:** count `ray_cast` crossings along three directions and take the majority; treat hits within the shell
thickness as one; against open meshes count only shallow, real crossings (the project used 3 cm); recalculate normals
(`bmesh.ops.recalc_face_normals`, then `BVHTree.FromBMesh`) before any signed test on a mesh you did not build.
**How it was found:** checks tested with a fault injected on purpose: two of the first four passed obvious faults.

### bmesh.ops.solidify's even offset spikes at folds
**What happens:** where a surface folds back on itself the even-thickness offset divides by a small angle and throws points
far off.
**Evidence:** points up to 59 m off a draped garment (see `modifiers.md` for the numbers and the Solidify modifier that
does not). (not re-checked here)
**What to do:** use the Solidify modifier with `use_even_offset = False` and read the evaluated mesh.
**How it was found:** a scarf hanging on phantom sheets.

### Removing from a bpy collection while iterating over it skips entries
**What happens:** removing vertex groups (or other collection items) inside a loop over the same collection skips some.
**Evidence:** some weights survived a removal loop. (not re-checked here)
**What to do:** collect first (`for g in list(obj.vertex_groups): ...`), then remove.
**How it was found:** leftover weights found by a check.

### Index ranges do not survive welding; tag points with an attribute
**What happens:** merging points (welding seams, `remove_doubles`) renumbers vertices; code that knew a piece by its index
range then reads other points.
**Evidence:** welding renumbered garment points three times under code that used index ranges. (not re-checked here)
**What to do:** store a per-point attribute (the piece it belongs to) and select by it; do anything keyed by index before
welding.
**How it was found:** measures reading the wrong piece.

### meshes.new_from_object drops shape keys
**What happens:** a mesh made from an evaluated object has no shape keys.
**Evidence:** stages that replaced a mesh with its evaluated result lost their rest keys. (not re-checked here)
**What to do:** `new_from_object(ev, preserve_all_data_layers=True, depsgraph=dg)` keeps attributes and UVs; keep keys
yourself (as arrays) across stages.
**How it was found:** missing keys after a stage.

### foreach_get/foreach_set with numpy, not per-element loops
**What happens:** per-element Python loops over large meshes are slow.
**Evidence:** loose parts of a 65k-vertex mesh found in a fraction of a second by label propagation over
`edges.foreach_get('vertices', ...)`, where a face walk took minutes. (not re-checked here)
**What to do:** `me.vertices.foreach_get('co', arr)`, `polygons.foreach_get('material_index', ...)`,
`uv_layers[...].data.foreach_set('uv', ...)`.
**How it was found:** a slow check.

### There is no one-call "copy this modifier": walk its RNA properties
**What happens:** the API has no direct modifier copy between objects.
**Evidence:** working approach: `m2 = new.modifiers.new(m.name, m.type)`; for each `p` in `m.bl_rna.properties` not
`p.is_readonly` (skipping name and type), `setattr(m2, p.identifier, getattr(m, p.identifier))` in a try. (not re-checked
here)
**What to do:** as above, and re-bind modifiers that need it (Surface Deform, Corrective Smooth).
**How it was found:** copying a garment's stack to a frozen copy.

### A new datablock may take a .001 name
**What happens:** a second datablock with a taken name gets a suffix.
**Evidence:** materials became "trousers.001" and lookups by name missed them. (not re-checked here)
**What to do:** keep the Python reference; match by base name (strip `.NNN`) or tag datablocks with custom properties.
**How it was found:** missing materials.

### box_pack_2d packs rectangles into a square
**What happens:** `mathutils.geometry.box_pack_2d` packs rectangles (for example texture canvases) into one square.
**Evidence:** five garment maps packed into 3180 x 3120 (90 % filled), another set into 3240 x 3720 (70 %). (not re-checked
here)
**What to do:** use it to lay out an atlas; it packs into a square, not into a fixed width.
**How it was found:** sizing a texture atlas.

### A BVH distance replaces Dynamic Paint for contact maps
**What happens:** where cloth lies on a body can be measured exactly per frame with a BVH tree in Python, with no paint
simulation to set up.
**Evidence:** the project's visibility and contact measures used `find_nearest`/`ray_cast` per frame instead of Dynamic
Paint. (not re-checked here)
**What to do:** `BVHTree.FromObject(body, depsgraph)` per frame and `find_nearest` for each cloth point.
**How it was found:** deciding whether Dynamic Paint was needed.
