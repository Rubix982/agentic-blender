"""When does a 2D curve's own fill break, and does Geometry Nodes' Fill Curve break with it?

C-009 and C-011 (shots/jali-match) saw a curve of traced outlines fill to a fraction of its area, and each time one
small smoothed island was enough to break it. data/fill_knife_edge_pair.json keeps that island and the outline around
it, in pixels. This builds the pair as a 2D curve (fill BOTH, no extrude or bevel) at several scales, with the island
moved by fractions of a pixel, and measures the filled area against the area the outlines enclose; then the same
outlines with the curve's fill off and a Geometry Nodes Fill Curve modifier (constrained Delaunay triangulation)
instead. Blender's curve fill is its scan-fill (blenlib scanfill.cc), which decides sides by exact arithmetic."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import json
import bpy
import numpy as np
import exp
E = exp.Experiment(__file__)

D = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "fill_knife_edge_pair.json")))
W, H = D["image_size"]
OUTER, ISLAND = np.array(D["outer"]), np.array(D["island"])
S = D["metres_per_px"]


def area(p):
    x, y = p[:, 0], p[:, 1]
    return 0.5 * float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))


ENC = abs(area(OUTER) + area(ISLAND))
ng = bpy.data.node_groups.new("fill", "GeometryNodeTree")
ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
gi, go, fc = ng.nodes.new("NodeGroupInput"), ng.nodes.new("NodeGroupOutput"), ng.nodes.new("GeometryNodeFillCurve")
ng.links.new(gi.outputs[0], fc.inputs[0])
ng.links.new(fc.outputs[0], go.inputs[0])


def filled(scale, shift=0.0, nodes=False):
    cu = bpy.data.curves.new("pair", "CURVE")
    cu.dimensions, cu.resolution_u = "2D", 1
    cu.fill_mode = "NONE" if nodes else "BOTH"
    for q in (OUTER, ISLAND + np.array([shift, 0.0])):
        sp = cu.splines.new("POLY")
        sp.points.add(len(q) - 1)
        co = np.zeros((len(q), 4), np.float32)
        co[:, 0], co[:, 1], co[:, 3] = (q[:, 0] - W / 2) * scale, (H / 2 - q[:, 1]) * scale, 1.0
        sp.points.foreach_set("co", co.ravel())
        sp.use_cyclic_u = True
    ob = bpy.data.objects.new("pair", cu)
    bpy.context.scene.collection.objects.link(ob)
    if nodes:
        ob.modifiers.new("fill", "NODES").node_group = ng
    me = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
    share = sum(f.area for f in me.polygons) / scale ** 2 / ENC
    faces = len(me.polygons)
    bpy.data.objects.remove(ob)
    bpy.data.curves.remove(cu)
    return round(share, 4), faces


def run(outer, island):
    global OUTER, ISLAND
    OUTER, ISLAND = outer, island
    rows = {}
    for sc in (1e-4, 3e-4, 6e-4, S, 2e-3, 5e-3, 0.01, 0.1, 1.0):
        (cs, cf), (ns_, nf) = filled(sc), filled(sc, nodes=True)
        rows[f"scale {sc:g} per px"] = dict(curve_fill=cs, curve_faces=cf, fill_curve_node=ns_, node_faces=nf)
    shifts = {f"{dx:+g} px": filled(S, dx)[0] for dx in (-2e-3, -1e-3, -5e-4, 0.0, 5e-4, 1e-3, 2e-3)}
    return rows, shifts


O0, I0 = OUTER.copy(), ISLAND.copy()
rows, shifts = run(O0, I0)                                             # as saved: to a millionth of a pixel
rows5, shifts5 = run(np.round(O0, 5), np.round(I0, 5))                  # the same, rounded to a hundred-thousandth
for name, r in (("as saved", rows), ("rounded to 1e-5 px", rows5)):
    print("ROWS", name, {k: v["curve_fill"] for k, v in r.items()}, flush=True)
print("SHIFTS", shifts, shifts5, flush=True)


def broken(r):
    return ", ".join(k for k, v in r.items() if v["curve_fill"] < 0.9) or "none"


E.fact("A 2D curve's fill broke on these two outlines at some scales and not others, not by size; the curve faces it "
       "made also changed with scale", broken_scales=broken(rows),
       faces_range=f"{min(v['curve_faces'] for v in rows.values())} to {max(v['curve_faces'] for v in rows.values())}")
E.fact("Moving the island by fractions of a thousandth of a pixel turned the break on and off",
       broken_shifts=", ".join(k for k, v in shifts.items() if v < 0.9) or "none",
       whole_shifts=", ".join(k for k, v in shifts.items() if v >= 0.9))
E.fact("Rounding the same coordinates one decimal coarser (to 1e-5 px) moved which scales and shifts break: the break "
       "turns on the points' exact floating-point values", broken_scales_rounded=broken(rows5),
       broken_shifts_rounded=", ".join(k for k, v in shifts5.items() if v < 0.9) or "none")
E.fact("Geometry Nodes' Fill Curve filled the same outlines whole every time",
       node_share_min=min(v["fill_curve_node"] for r in (rows, rows5) for v in r.values()))
E.save(rows=rows, island_shifts_at_build_scale=shifts, rows_rounded_1e5=rows5, island_shifts_rounded_1e5=shifts5,
       enclosed_px=round(ENC, 1), points=[len(O0), len(I0)])
