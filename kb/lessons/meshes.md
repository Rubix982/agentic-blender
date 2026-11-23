# Lessons: meshes

From a project that built garment meshes from flat pattern pieces, cleaned downloaded human figures, and made collision
proxies, in Blender 4.5.14.

---

### Measure the mesh before blaming the physics
**What happens:** faults that look random or physical (explosions, lumps, a hem riding up) often come from the mesh:
zero-length edges, stray faces, doubled shells, inward normals.
**Evidence:** a day of "random" cloth explosions was two points on one spot; a 23 cm ride-up was 117 stray "webbing"
faces with edges up to 27 cm; lumpy cloth was a skin made of two shells 4 mm apart. (not re-checked here)
**What to do:** before any simulation report the shortest and longest edge, the number of loose parts, non-manifold edges
and whether normals are consistent; fail on edges under 0.5 mm.
**How it was found:** each fault, after several cloth settings had been tried in vain.

### Cut a mesh with a plane, not by deleting vertices
**What happens:** deleting vertices below a height leaves a jagged edge with spikes and slivers that confuse inside tests
and catch cloth.
**Evidence:** a sliver made sleeve points 13-14 cm away read as inside. (not re-checked here)
**What to do:** `bmesh.ops.bisect_plane(bm, geom=region, plane_co=..., plane_no=..., clear_outer=True)`, limited to the
region so the plane cannot cut elsewhere.
**How it was found:** a pre-simulation check flagged the sleeve.

### Filled holes are big non-flat ngons with arbitrary normals
**What happens:** `bmesh.ops.holes_fill` caps a hole with one polygon; if the hole is not planar the cap is a warped ngon,
and it faces whichever way the fill left it.
**Evidence:** a warped cap in a collider blew up every 1.5 cm drape (seams 15 m apart) at every quality; an inward cap made
a cuff 13 cm away read as 13 cm "inside". (not re-checked here)
**What to do:** `bmesh.ops.triangulate(bm, faces=caps, quad_method='BEAUTY', ngon_method='BEAUTY')`, then
`bmesh.ops.recalc_face_normals(bm, faces=bm.faces)`.
**How it was found:** pre-simulation checks on every variant.

### Faces wound against their neighbours put a Solidify shell on the wrong side
**What happens:** a face whose winding disagrees with its neighbours has its normal flipped; Solidify then offsets it the
other way and the cloth's inside shows there. Generated small faces (sequins, tiles) wound clockwise render dark.
**Evidence:** 41 of 3,836 faces on a garment (20 of them bridges across welded seams) showed pale wedges along the shoulder
seams in a 5x close-up. (not re-checked here)
**What to do:** before solidifying, flip each face whose normal opposes its neighbours' mean (`bmesh.ops.reverse_faces`),
or `recalc_face_normals` on closed parts; wind generated faces counter-clockwise about their outward normal.
**How it was found:** a close-up render.

### A 2D curve flattens its profile into its local XY plane
**What happens:** a curve with `dimensions = '2D'` keeps its points in its own XY plane; a profile drawn in Y-Z collapses
into a flat sheet.
**Evidence:** a studio backdrop (floor curving up to a wall) built as a 2D curve became one vertical plane through the
middle of the subject; in Cycles it hid everything behind the subject's centre line (a trailing leg with its trouser leg
and shoe vanished; Workbench showed both legs). (not re-checked here)
**What to do:** build such profiles as a mesh, or set the curve to 3D; render a side view once to check.
**How it was found:** bisecting the render (Workbench vs Cycles, objects hidden in turn).

### Constrained Delaunay meshing of pattern pieces gives seams matching point counts
**What happens:** `mathutils.geometry.delaunay_2d_cdt` triangulates a 2D outline with holes and inner edges kept, so a
piece's boundary can carry exactly the points you give it.
**Evidence:** pieces meshed as a 1.5 cm grid snapped to the outline gave the two sides of a seam different point counts
(66 and 132 skipped seam points on two garments; 80 bridge faces at the weld); keeping the grid inside, giving every seam
exactly its pair's count and triangulating the strip along the outline with `delaunay_2d_cdt` cut skipped points to 0,
bridges to 2 and 6, and a drape from 324 to 249 s. (not re-checked here)
**What to do:** mesh flat pieces with the outline as constraint edges; merge edges shorter than a tolerance afterwards.
**How it was found:** holes at welded seams.

### Shape keys block destructive edits
**What happens:** a mesh with shape keys cannot be cut, subdivided or have modifiers applied the usual way.
**Evidence:** MPFB figures keep their shape in shape keys. (not re-checked here)
**What to do:** `bpy.ops.object.shape_key_remove(all=True, apply_mix=True)` to bake the mix into the mesh first.
**How it was found:** preparing figures for cutting.

### Rebuilding a figure's skin with a voxel remesh needs preparation
**What happens:** a voxel remesh copies flat facets, takes hidden inner walls for surface, melts fingers together in a
closing, leaves stair-steps and loses vertex groups.
**Evidence:** the working sequence at voxel 3 mm (shell) and 2.6 mm (skin): apply Subdivision (levels 2), split the hands
off, pre-remesh to one shell, close, re-join the hands and remesh, Laplacian Smooth (14 iterations, `lambda_factor` 1,
`use_volume_preserve`), transfer weights back. (not re-checked here)
**What to do:** as above.
**How it was found:** a faceless mannequin head built from a scan.
