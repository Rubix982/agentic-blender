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
