"""mathutils.geometry: delaunay_2d_cdt (with a hole), tessellate_polygon, and the intersect_* helpers, with their real return values."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import math
import bpy
from mathutils import Vector, geometry as G
import exp
E = exp.Experiment(__file__)

# square with a square hole: constrained edges, output types
outer = [(0, 0), (4, 0), (4, 4), (0, 4)]
inner = [(1, 1), (3, 1), (3, 3), (1, 3)]
verts = [Vector(p) for p in outer + inner]
edges = [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4)]
res = {}
for ot in range(6):
    vs, es, fs, ov, oe, of = G.delaunay_2d_cdt(verts, edges, [], ot, 1e-6)
    area = 0.0
    for f in fs:
        pts = [vs[i] for i in f]
        area += 0.5 * abs(sum(pts[i].x * pts[(i + 1) % len(pts)].y - pts[(i + 1) % len(pts)].x * pts[i].y for i in range(len(pts))))
    res[ot] = dict(verts=len(vs), edges=len(es), faces=len(fs), area=round(area, 4), max_face_size=max((len(f) for f in fs), default=0))
omitted = [k for k, v in res.items() if abs(v["area"] - 12.0) < 1e-6]
E.fact("delaunay_2d_cdt(verts, edges, faces, output_type, epsilon) on a 4x4 square with a 2x2 square hole given as EDGES only: output types that leave the hole out: " + (str(omitted) if omitted else "none (pass the loops as faces to get holes)"),
       by_output_type=res, expected_area_without_hole=12.0)
# faces given as input
def poly_area(vs, f):
    return 0.5 * abs(sum(vs[f[i]].x * vs[f[(i + 1) % len(f)]].y - vs[f[(i + 1) % len(f)]].x * vs[f[i]].y for i in range(len(f))))
res_f = {}
for ot in range(6):
    vs, es, fs, ov, oe, of = G.delaunay_2d_cdt(verts, [], [[0, 1, 2, 3], [4, 5, 6, 7]], ot, 1e-6)
    res_f[ot] = dict(faces=len(fs), area=round(sum(poly_area(vs, f) for f in fs), 4), max_face_size=max((len(f) for f in fs), default=0))
E.fact("the same square-with-hole passed as two FACES (outer, inner): output types 0-5 (area 12 means the hole was left out, 16 filled, 20 = both loops as overlapping faces)",
       by_output_type=res_f)
# reversed inner winding
res_r = {}
for ot in (3, 5):
    vs, es, fs, ov, oe, of = G.delaunay_2d_cdt(verts, [], [[0, 1, 2, 3], [7, 6, 5, 4]], ot, 1e-6)
    res_r[ot] = dict(faces=len(fs), area=round(sum(poly_area(vs, f) for f in fs), 4))
E.fact("the same with the inner loop wound clockwise", by_output_type=res_r)
try:
    G.delaunay_2d_cdt([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [], 0, 1e-6); d3 = "accepted (z ignored?)"
except Exception as e:
    d3 = f"{type(e).__name__}: {e}"
E.fact("delaunay_2d_cdt with 3D vertex tuples", result=d3)

# tessellate_polygon: list of loops; the second loop is a hole
tris = G.tessellate_polygon([[Vector((x, y, 0)) for x, y in outer], [Vector((x, y, 0)) for x, y in inner]])
E.fact("tessellate_polygon([outer, inner]) triangulates with the inner loop as a hole; indices refer to the concatenated loops",
       tris=len(tris), max_index=max(max(t) for t in tris))

# intersections
tri = (Vector((0, 0, 0)), Vector((1, 0, 0)), Vector((0, 1, 0)))
h = G.intersect_ray_tri(*tri, Vector((0, 0, -1)), Vector((0.2, 0.2, 1)))
E.fact("intersect_ray_tri(v1, v2, v3, ray_direction, ray_origin) -- direction BEFORE origin -- returns the hit point or None",
       hit=tuple(h) if h else None, behind=G.intersect_ray_tri(*tri, Vector((0, 0, 1)), Vector((0.2, 0.2, 1)), True))
p = G.intersect_line_plane(Vector((0, 0, 5)), Vector((0, 0, 4)), Vector((0, 0, 1)), Vector((0, 0, 1)))
E.fact("intersect_line_plane(line_a, line_b, plane_co, plane_no) treats the line as infinite", point=tuple(p) if p else None)
cp, pct = G.intersect_point_line(Vector((0.5, 1, 0)), Vector((0, 0, 0)), Vector((2, 0, 0)))
E.fact("intersect_point_line(pt, line_a, line_b) returns (closest point, factor along a->b)", closest=tuple(cp), factor=pct)
ll = G.intersect_line_line(Vector((0, 0, 0)), Vector((1, 0, 0)), Vector((0.5, -1, 1)), Vector((0.5, 1, 1)))
E.fact("intersect_line_line returns the two closest points between skew lines", points=[tuple(x) for x in ll])
ll2 = G.intersect_line_line_2d(Vector((0, 0)), Vector((2, 2)), Vector((0, 2)), Vector((2, 0)))
E.fact("intersect_line_line_2d works on segments and returns the crossing point or None", point=tuple(ll2) if ll2 else None,
       none_case=G.intersect_line_line_2d(Vector((0, 0)), Vector((1, 1)), Vector((5, 0)), Vector((6, 1))))
ss = G.intersect_sphere_sphere_2d(Vector((0, 0)), 1.0, Vector((1, 0)), 1.0)
E.fact("intersect_sphere_sphere_2d", points=[tuple(round(c, 4) for c in x) for x in ss])
E.fact("other helpers present", names=[n for n in dir(G) if not n.startswith("_")])
hull = G.convex_hull_2d([(0, 0), (1, 0), (0.5, 0.2), (1, 1), (0, 1)])
E.fact("convex_hull_2d returns hull vertex indices", hull=list(hull))
E.fact("area_tri and normal", area=G.area_tri(*tri), normal=tuple(G.normal(*tri)))
E.save()
