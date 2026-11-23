# Lessons: geometry nodes

From a project that placed embroidery motifs on simulated garments and built hair with Blender 4.5.14's geometry nodes.

---

### Sample UV Surface finds nothing where a UV is covered by two faces
**What happens:** the node looks a UV coordinate up on the (deformed) surface; where two faces share that UV region
(overlapping UV islands, or faces whose UVs were copied from two pieces), it returns no valid sample.
**Evidence:** a row of nine domes placed by their pattern UV on a garment after its cloth modifier: on every walk frame
(61-129) the domes that landed sat 0.0 mm from the cloth and the row kept its 33.5 cm across the front while the figure
walked 1.3 m. But only 2 of 9 landed at first: 59 faces that bridged welded seams carried UVs from two pieces over the
pieces' own; moved aside, 8 of 9 landed. (not re-checked here)
**What to do:** make the UV map non-overlapping where you sample (check for faces whose UVs overlap another island), and
read the node's "Is Valid" output.
**How it was found:** most domes missing on the first try.

### Socket names cost runs: look them up for the exact version
**What happens:** node socket names change between versions and are not always what memory suggests.
**Evidence:** scripts written from memory failed on Sample UV Surface's UV input. In 4.5 its inputs are Mesh, Value,
"UV Map" (identifier `Source UV Map`) and "Sample UV"; its outputs Value and "Is Valid" `[inv]`.
**What to do:** read the node's sockets from Blender (`skills/blender/scripts/kb.py node "Sample UV Surface"`) before
linking by name; link by identifier where names are ambiguous.
**How it was found:** failed runs, fixed by reading the node's sockets.

### Instancing small details in nodes is not faster than building them in Python
**What happens:** for a few thousand to tens of thousands of small pieces, a Python/bmesh build is already fast; nodes
(Distribute Points on Faces + Instance on Points) save memory and file size when the details are kept as instances, not
build time.
**Evidence:** building sequins and beads in Python took 2.5 s for one garment (12 objects, about 13,000 pieces, 199,596
points). (not re-checked here)
**What to do:** choose instancing for file size and memory (an asset carrying its embellishment), not for speed.
**How it was found:** timing before deciding whether to port the build to nodes.

### Blender's bundled hair node groups shape hair; none simulates it
**What happens:** the 27 procedural hair node-group assets bundled with 4.5 (clump, curl, frizz, braid, interpolate, ...)
are shaping tools; there is no hair or cloth solver among them in 4.5.
**Evidence:** read from the bundled asset library on Blender 4.5.14. (not re-checked here)
**What to do:** a solver in nodes means writing one (simulation zone plus repeat zone); 4.5 has no node solver to reuse.
**How it was found:** surveying what could replace the cloth solver.

### The bundled procedural hair node groups load from a .blend inside Blender's install
**What happens:** the hair node-group assets ship in Blender's own datafiles, not in `bpy.data`; they need loading, and
hair needs a UV-mapped surface to attach to.
**Evidence:** loaded from `bpy.utils.resource_path('LOCAL') + '/datafiles/assets/geometry_nodes/procedural_hair_node_assets.blend'`
with `bpy.data.libraries.load`; guides built with `bpy.data.hair_curves.new()`, `curves.add_curves(...)`,
`attributes['position']`, with `curves.surface` and `curves.surface_uv_map` set; "Attach Hair Curves to Surface" first in
the stack; `uv.smart_project` in edit mode ran headless to give the scalp its UVs. Modifier inputs set by
`mod[item.identifier]`; attribute inputs through `mod[identifier + '_use_attribute'] = True` and
`mod[identifier + '_attribute_name']`. (not re-checked here)
**What to do:** as above; read the group's interface items for identifiers rather than guessing `Socket_N`.
**How it was found:** building a figure's hair from Blender's own assets.

### Closing grooves narrower than r: two SDF round trips
**What happens:** a morphological closing (fill inside corners and grooves narrower than r) can be done with the 4.5 grid
nodes: mesh to SDF, offset out, mesh, back to SDF, offset in.
**Evidence:** chain `GeometryNodeMeshToSDFGrid` -> `GeometryNodeGridToMesh` (threshold +r) -> `MeshToSDFGrid` ->
`GridToMesh` (threshold -r), with the band width at least r / voxel size + 4 so the field reaches past the offset
surfaces; then apply the modifier. (not re-checked here)
**What to do:** as above; too narrow a band leaves holes where the offset surface leaves the field.
**How it was found:** smoothing a scanned surface for sculpting.

### A geometry-nodes "follower" works where Surface Deform refuses to bind
**What happens:** Surface Deform's bind fails on concave or crumpled polygons; a node setup that rebuilds each point from
three stored triangle corners on the moving surface does the same job and always binds.
**Evidence:** per point, store the nearest triangle's three vertex indices (INT attributes), barycentric weights and an
offset in the triangle's frame (FLOAT_VECTOR); in nodes, Object Info (`transform_space='RELATIVE'`) of the moving surface
-> three Sample Index (FLOAT_VECTOR, POINT domain) of Position -> rebuild the frame -> Set Position. The object input is
set with `mod[group.interface.items_tree['Cloth'].identifier] = cloth`. (not re-checked here)
**What to do:** use it for trims that must ride a draped cloth whose faces fold or crumple.
**How it was found:** binds failing on draped cloth.
