"""The common bmesh.ops, run on small inputs with their real argument names: what each one returns and does to the counts."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import math
import bpy, bmesh
from mathutils import Vector, Matrix
import exp
E = exp.Experiment(__file__)


def counts(bm):
    return (len(bm.verts), len(bm.edges), len(bm.faces))


def cube():
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2.0)
    return bm


def is_manifold(bm):
    return all(e.is_manifold for e in bm.edges)


R = {}

# create_* : size vs radius conventions
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=2.0)
R["create_cube"] = dict(args="size=2.0", counts=counts(bm), max_x=max(v.co.x for v in bm.verts)); bm.free()
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=4, y_segments=4, size=1.0)
R["create_grid"] = dict(args="x_segments=4, y_segments=4, size=1.0", counts=counts(bm), max_x=max(v.co.x for v in bm.verts)); bm.free()
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=1.0)
R["create_uvsphere"] = dict(args="u_segments=16, v_segments=8, radius=1.0", counts=counts(bm)); bm.free()
bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
R["create_icosphere"] = dict(args="subdivisions=2, radius=1.0", counts=counts(bm)); bm.free()
bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=True, segments=12, radius=1.0)
R["create_circle"] = dict(args="cap_ends=True, segments=12, radius=1.0", counts=counts(bm)); bm.free()
bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=1.0, radius2=0.0, depth=2.0)
R["create_cone"] = dict(args="cap_ends=True, segments=12, radius1=1.0, radius2=0.0, depth=2.0", counts=counts(bm)); bm.free()

# extrude_face_region: returns geom; new verts must be moved separately
bm = cube(); top = [f for f in bm.faces if f.normal.z > 0.5]
r = bmesh.ops.extrude_face_region(bm, geom=top)
newv = [g for g in r["geom"] if isinstance(g, bmesh.types.BMVert)]
bmesh.ops.translate(bm, verts=newv, vec=(0, 0, 1))
R["extrude_face_region"] = dict(args="geom=[top face]; then translate(verts=new verts, vec=(0,0,1))", counts=counts(bm),
                                returned_keys=list(r.keys()), new_verts=len(newv), max_z=max(v.co.z for v in bm.verts),
                                manifold=is_manifold(bm), original_face_kept=top[0].is_valid)
bm.free()

# extrude_face_region with the old face deleted
bm = cube(); top = [f for f in bm.faces if f.normal.z > 0.5]
r = bmesh.ops.extrude_face_region(bm, geom=top)
bmesh.ops.delete(bm, geom=top, context="FACES")
newv = [g for g in r["geom"] if isinstance(g, bmesh.types.BMVert)]
bmesh.ops.translate(bm, verts=newv, vec=(0, 0, 1))
R["extrude_face_region+delete_old"] = dict(counts=counts(bm), manifold=is_manifold(bm))
bm.free()

# extrude_discrete_faces
bm = cube(); r = bmesh.ops.extrude_discrete_faces(bm, faces=bm.faces[:])
R["extrude_discrete_faces"] = dict(args="faces=all 6", counts=counts(bm), returned_keys=list(r.keys()), new_faces=len(r["faces"])); bm.free()

# inset_region / inset_individual
bm = cube(); top = [f for f in bm.faces if f.normal.z > 0.5]
r = bmesh.ops.inset_region(bm, faces=top, thickness=0.2, depth=0.0)
R["inset_region"] = dict(args="faces=[top], thickness=0.2, depth=0.0", counts=counts(bm), returned_faces=len(r["faces"])); bm.free()
bm = cube(); r = bmesh.ops.inset_individual(bm, faces=bm.faces[:], thickness=0.2, depth=-0.1)
R["inset_individual"] = dict(args="faces=all, thickness=0.2, depth=-0.1", counts=counts(bm), returned_faces=len(r["faces"])); bm.free()

# bevel: affect EDGES vs VERTICES (default), geom with and without verts; same offset and segments throughout
for label, geom_fn, kw in [("bevel_edges_geom_edges_affect_EDGES", lambda bm: bm.edges[:], dict(affect="EDGES")),
                           ("bevel_edges_geom_edges+verts_affect_EDGES", lambda bm: bm.edges[:] + bm.verts[:], dict(affect="EDGES")),
                           ("bevel_edges_geom_edges_default_affect", lambda bm: bm.edges[:], dict()),
                           ("bevel_verts_geom_verts_affect_VERTICES", lambda bm: bm.verts[:], dict(affect="VERTICES"))]:
    bm = cube()
    r = bmesh.ops.bevel(bm, geom=geom_fn(bm), offset=0.1, segments=3, profile=0.5, clamp_overlap=True, **kw)
    R[label] = dict(args=f"offset=0.1, segments=3, profile=0.5, clamp_overlap=True, {kw}", counts=counts(bm), manifold=is_manifold(bm),
                    returned={k: len(v) for k, v in r.items()})
    bm.free()

# bisect_plane
bm = cube()
r = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0.3), plane_no=(0, 0, 1), clear_outer=True)
R["bisect_plane"] = dict(args="geom=all, plane_co=(0,0,0.3), plane_no=(0,0,1), clear_outer=True", counts=counts(bm),
                         max_z=round(max(v.co.z for v in bm.verts), 4), cut=len(r["geom_cut"]), manifold=is_manifold(bm))
# fill the cut
edges = [e for e in bm.edges if e.is_boundary]
r2 = bmesh.ops.holes_fill(bm, edges=edges, sides=0)
R["holes_fill_after_bisect"] = dict(args="edges=boundary edges, sides=0", new_faces=len(r2["faces"]), counts=counts(bm), manifold=is_manifold(bm))
bm.free()
bm = cube()
r2 = bmesh.ops.holes_fill(bm, edges=bm.edges[:], sides=4)
R["holes_fill_closed"] = dict(new_faces=len(r2["faces"]))
bm.free()

# triangulate
bm = cube(); r = bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="BEAUTY", ngon_method="BEAUTY")
R["triangulate"] = dict(args="faces=all, quad_method='BEAUTY', ngon_method='BEAUTY'", counts=counts(bm), returned=list(r.keys()),
                        quad_methods=None); bm.free()

# remove_doubles: two overlapping cubes
bm = cube()
bmesh.ops.create_cube(bm, size=2.0)
before = counts(bm)
bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-4)
R["remove_doubles"] = dict(args="verts=all, dist=1e-4", before=before, after=counts(bm))
bm.free()
bm = cube()
bmesh.ops.create_cube(bm, size=2.0)
r = bmesh.ops.find_doubles(bm, verts=bm.verts[:], dist=1e-4)
n_pairs = len(r["targetmap"])
bmesh.ops.weld_verts(bm, targetmap=r["targetmap"])
R["find_doubles+weld_verts"] = dict(pairs=n_pairs, after=counts(bm))
bm.free()

# convex_hull from random points
import random
random.seed(1)
bm = bmesh.new()
for _ in range(200):
    bm.verts.new((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)))
r = bmesh.ops.convex_hull(bm, input=bm.verts[:], use_existing_faces=False)
interior = [g for g in r["geom_interior"] if isinstance(g, bmesh.types.BMVert)]
R["convex_hull"] = dict(args="input=verts", counts_with_interior=counts(bm), interior_verts=len(interior),
                        returned=list(r.keys()))
bmesh.ops.delete(bm, geom=interior, context="VERTS")
R["convex_hull"]["after_deleting_interior"] = counts(bm)
R["convex_hull"]["manifold"] = is_manifold(bm)
bm.free()

# delete contexts
ctxs = [e.identifier for e in []]
bm = cube()
bm.faces.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[bm.faces[0]], context="FACES_ONLY")
R["delete_FACES_ONLY"] = dict(counts=counts(bm)); bm.free()
bm = cube(); bm.faces.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[bm.faces[0]], context="FACES")
R["delete_FACES"] = dict(counts=counts(bm)); bm.free()
bm = cube(); bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[bm.verts[0]], context="VERTS")
R["delete_VERTS"] = dict(counts=counts(bm)); bm.free()
try:
    bm = cube(); bmesh.ops.delete(bm, geom=bm.faces[:1], context="FACE")
except Exception as e:
    R["delete_bad_context"] = f"{type(e).__name__}: {e}"

# subdivide_edges, dissolve_limit, recalc_face_normals, reverse_faces, solidify, spin, bridge_loops
bm = cube(); r = bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=2, use_grid_fill=True)
R["subdivide_edges"] = dict(args="edges=all, cuts=2, use_grid_fill=True", counts=counts(bm)); 
bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(5), verts=bm.verts[:], edges=bm.edges[:])
R["dissolve_limit_after"] = dict(args="angle_limit=radians(5), verts=all, edges=all", counts=counts(bm)); bm.free()
bm = cube(); bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
inward = sum(1 for f in bm.faces if f.normal.dot(f.calc_center_median()) < 0)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
outward = sum(1 for f in bm.faces if f.normal.dot(f.calc_center_median()) > 0)
R["reverse_then_recalc_normals"] = dict(inward_after_reverse=inward, outward_after_recalc=outward); bm.free()
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=2, y_segments=2, size=1.0)
r = bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.1)
R["solidify"] = dict(args="geom=faces, thickness=0.1", counts=counts(bm), manifold=is_manifold(bm)); bm.free()
bm = bmesh.new(); v1 = bm.verts.new((1, 0, 0)); v2 = bm.verts.new((1, 0, 1)); bm.edges.new((v1, v2))
r = bmesh.ops.spin(bm, geom=bm.verts[:] + bm.edges[:], cent=(0, 0, 0), axis=(0, 0, 1), angle=math.radians(360), steps=12, use_merge=True)
R["spin"] = dict(args="geom=verts+edges, cent=(0,0,0), axis=(0,0,1), angle=2pi, steps=12, use_merge=True", counts=counts(bm)); bm.free()
bm = bmesh.new()
bmesh.ops.create_circle(bm, segments=8, radius=1.0)
bmesh.ops.create_circle(bm, segments=8, radius=1.0, matrix=Matrix.Translation((0, 0, 2)))
r = bmesh.ops.bridge_loops(bm, edges=bm.edges[:])
R["bridge_loops"] = dict(args="edges=both circles' edges", counts=counts(bm), new_faces=len(r["faces"])); bm.free()

# poke, wireframe, beautify, join_triangles
bm = cube(); r = bmesh.ops.poke(bm, faces=bm.faces[:]); R["poke"] = dict(counts=counts(bm)); 
bm.free()
bm = cube(); r = bmesh.ops.wireframe(bm, faces=bm.faces[:], thickness=0.05, use_replace=True)
R["wireframe"] = dict(args="faces=all, thickness=0.05, use_replace=True", counts=counts(bm)); bm.free()

E.fact("create_cube(size=2) spans -1..1 (size is the edge length) but create_grid(size=1) also spans -1..1 (size is half the width)",
       cube_max_x=R["create_cube"]["max_x"], grid_max_x=R["create_grid"]["max_x"])
E.fact("extrude_face_region leaves the original face in place; deleting it (context='FACES') is what makes the result manifold",
       kept=R["extrude_face_region"]["manifold"], deleted=R["extrude_face_region+delete_old"]["manifold"])
# Enum values for a few ops, read from the docstring of the op
for k, v in R.items():
    E.fact(f"bmesh.ops.{k}", **(v if isinstance(v, dict) else dict(result=v)))
E.save(results=R)
