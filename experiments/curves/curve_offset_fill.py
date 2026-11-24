"""A 2D curve with holes: what the curve's Offset does to its fill, and how far the bevel widens the outline.

C-007 traced a carved screen into 600 to 800 nested outlines on one 2D curve. With offset -3 mm the front face came out
0.24 m2 against 1.10 at offset 0, and the render was inside out: the openings solid, the stone empty. This rebuilds the
question on squares: a 1 m square, a grid of square holes, the gaps between holes either wide (50 mm) or narrower than
twice the offset (4 mm), holes wound against the outer square or with it. For each, the front face's area and the solid's
width, at offset 0 and +/-3 mm, with extrude 20 mm and bevel 3 mm."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy
import exp
E = exp.Experiment(__file__)

BEVEL = 0.003


def square(cu, x0, y0, side, ccw):
    pts = [(x0, y0), (x0 + side, y0), (x0 + side, y0 + side), (x0, y0 + side)]
    if not ccw:
        pts = pts[::-1]
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for p, (x, y) in zip(sp.points, pts):
        p.co = (x, y, 0.0, 1.0)
    sp.use_cyclic_u = True


def build(gap, holes_ccw, n=8):
    cu = bpy.data.curves.new("screen", "CURVE")
    cu.dimensions = "2D"
    cu.fill_mode = "BOTH"
    cu.extrude = 0.02
    cu.bevel_depth = BEVEL
    cu.bevel_resolution = 2
    square(cu, -0.5, -0.5, 1.0, True)
    margin = 0.1
    side = (1.0 - 2 * margin - (n - 1) * gap) / n
    for i in range(n):
        for j in range(n):
            square(cu, -0.5 + margin + i * (side + gap), -0.5 + margin + j * (side + gap), side, holes_ccw)
    ob = bpy.data.objects.new("screen", cu)
    bpy.context.scene.collection.objects.link(ob)
    return ob, 1.0 - n * n * side * side


def measure(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    front = sum(f.area for f in me.polygons if f.normal.z > 0.99)
    xs = [v.co.x for v in me.vertices]
    r = dict(front_m2=round(front, 4), width_m=round(max(xs) - min(xs), 4), faces=len(me.polygons))
    ev.to_mesh_clear()
    return r


rows = {}
for gap in (0.05, 0.004):
    for holes_ccw in (False, True):
        ob, stone = build(gap, holes_ccw)
        key = f"gap {gap * 1000:.0f} mm, holes {'with' if holes_ccw else 'against'} the outer square"
        rows[key] = dict(stone_m2=round(stone, 4))
        for off in (0.0, -BEVEL, BEVEL):
            ob.data.offset = off
            rows[key][f"offset {off * 1000:+.0f} mm"] = measure(ob)
        bpy.data.objects.remove(ob)
        print("ROW", key, rows[key], flush=True)

w = rows["gap 50 mm, holes against the outer square"]
n = rows["gap 4 mm, holes against the outer square"]
E.fact("At offset 0 the front face is the outlines' own area with the holes cut, whichever way the holes wind; the "
       "bevel widens the solid by its radius on each side", stone_m2=w["stone_m2"], front_m2=w["offset +0 mm"]["front_m2"],
       width_m=w["offset +0 mm"]["width_m"])
E.fact("A negative offset moves every outline into the solid: the outer edge in, each hole out (the bevelled width is "
       "back to 1 m at offset -3 mm with bevel 3 mm)", front_m2=w["offset -3 mm"]["front_m2"],
       width_m=w["offset -3 mm"]["width_m"])
E.fact("Where holes grow into each other (gaps 4 mm, offset -3 mm) the overlaps fill in: the front face roughly doubles "
       "instead of shrinking", stone_m2=n["stone_m2"], front_m2=n["offset -3 mm"]["front_m2"])
E.save(rows=rows, bevel_m=BEVEL, extrude_m=0.02)
