"""Solidify and Bevel modifiers: what thickness/offset and width/segments/profile/clamp/limit actually do, measured."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import math
import numpy as np
import bpy, bmesh
import exp
E = exp.Experiment(__file__)


def evm(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    return ob.evaluated_get(dg).data


def zrange(me):
    z = [v.co.z for v in me.vertices]; return round(min(z), 4), round(max(z), 4)


def manifold(me):
    bm = bmesh.new(); bm.from_mesh(me); ok = all(e.is_manifold for e in bm.edges); bm.free(); return ok

# --- Solidify on a plane (normal +Z)
bpy.ops.mesh.primitive_plane_add(size=2)
p = bpy.context.object
s = p.modifiers.new("Solidify", "SOLIDIFY")
E.fact("a new Solidify modifier has thickness 0.01, offset -1, rim on, even thickness off", thickness=s.thickness, offset=s.offset,
       use_rim=s.use_rim, use_even_offset=s.use_even_offset, mode=s.solidify_mode)
s.thickness = 0.1
res = {}
for off in (-1.0, 0.0, 1.0):
    s.offset = off
    res[off] = zrange(evm(p))
E.fact("Solidify offset -1 grows the shell behind the normal (z from -0.1 to 0), 0 centres it, +1 grows along the normal", z_ranges=res)
s.offset = -1
me = evm(p)
E.fact("a solidified plane is closed and manifold with the rim on", verts=len(me.vertices), faces=len(me.polygons), manifold=manifold(me))
s.use_rim = False
me = evm(p)
E.fact("with use_rim off, the two shells are not joined (open boundary)", faces=len(me.polygons), manifold=manifold(me))
s.use_rim = True

# even thickness on a 90-degree fold
bpy.ops.mesh.primitive_cube_add()
c = bpy.context.object
bm = bmesh.new(); bm.from_mesh(c.data)
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z > 0.5], context="FACES_ONLY")   # open box
bm.to_mesh(c.data); bm.free()
s2 = c.modifiers.new("Solidify", "SOLIDIFY"); s2.thickness = 0.2
def wall(me):
    # inner x extent of the box's +X wall at mid-height: thickness measured along x
    xs = sorted({round(v.co.x, 4) for v in me.vertices if abs(v.co.z) < 0.99 and abs(v.co.y) < 0.99 and v.co.x > 0})
    return xs
plain = wall(evm(c))
s2.use_even_offset = True
even = wall(evm(c))
E.fact("on a box corner, Solidify's corner vertices move by thickness*sqrt(2) along the averaged normal without even thickness; use_even_offset keeps the walls at the set thickness",
       distinct_x_plain=plain, distinct_x_even=even)

# --- Bevel on a cube
bpy.ops.mesh.primitive_cube_add(location=(5, 0, 0))
cb = bpy.context.object
b = cb.modifiers.new("Bevel", "BEVEL")
E.fact("a new Bevel modifier: width 0.1, segments 1, affect EDGES, limit_method ANGLE at 30 deg, clamp overlap on",
       width=b.width, segments=b.segments, affect=b.affect, limit_method=b.limit_method, angle_deg=round(math.degrees(b.angle_limit), 2),
       use_clamp_overlap=b.use_clamp_overlap, offset_type=b.offset_type, profile=b.profile)
seg = {}
for n in (1, 2, 3, 4, 8):
    b.segments = n; me = evm(cb); seg[n] = (len(me.vertices), len(me.polygons))
E.fact("Bevel on a cube: (verts, faces) by segments", by_segments=seg)
b.segments = 4
prof = {}
for pr in (0.0, 0.25, 0.5, 0.75, 1.0):
    b.profile = pr
    me = evm(cb)
    # distance from cube corner (1,1,1) to nearest vertex: small for profile 1 (sharp/square), large for 0 (concave)
    d = min((v.co - __import__("mathutils").Vector((1, 1, 1))).length for v in me.vertices)
    prof[pr] = round(d, 4)
E.fact("Bevel profile 0.5 is round, 1.0 pushes the profile out to the original corner (square), 0.0 pulls it in (concave): nearest-vertex distance to the original corner",
       by_profile=prof)
b.profile = 0.5
# clamp overlap: width larger than half the edge
b.segments = 1
cl = {}
for w in (0.5, 1.5):
    for clamp in (True, False):
        b.width = w; b.use_clamp_overlap = clamp
        me = evm(cb)
        inverted = sum(1 for f in me.polygons if f.normal.dot(f.center) < 0)
        top = max((f for f in me.polygons if f.normal.z > 0.99), key=lambda f: f.center.z)
        cl[f"width={w},clamp={clamp}"] = dict(inverted_faces=inverted, top_face_area=round(top.area, 4))
E.fact("on a size-2 cube, Bevel width 1.5 (more than half an edge): with use_clamp_overlap the width is clamped and no face turns inside out; without it, faces invert",
       results=cl)
b.width = 0.1; b.use_clamp_overlap = True

# limit method on a cylinder: ANGLE bevels only the rim, NONE bevels every edge
bpy.ops.mesh.primitive_cylinder_add(vertices=32, location=(10, 0, 0))
cy = bpy.context.object
b2 = cy.modifiers.new("Bevel", "BEVEL"); b2.width = 0.05
lim = {}
for lm in ("ANGLE", "NONE"):
    b2.limit_method = lm; me = evm(cy); lim[lm] = (len(me.vertices), len(me.polygons))
E.fact("on a 32-sided cylinder, Bevel's default ANGLE limit bevels only the two rims; limit_method NONE also bevels the 32 side edges",
       base=(len(cy.data.vertices), len(cy.data.polygons)), by_limit=lim)
# weight limit uses the bevel_weight_edge attribute
b2.limit_method = "WEIGHT"
n_no_weights = len(evm(cy).vertices)          # copy numbers out: the evaluated mesh is freed on the next evaluation
me0 = evm(cy)
cy.data.attributes.new("bevel_weight_edge", "FLOAT", "EDGE")
w = np.zeros(len(cy.data.edges), np.float32); w[0] = 1.0
cy.data.attributes["bevel_weight_edge"].data.foreach_set("value", w); cy.data.update()
me1 = evm(cy)
try:
    len(me0.vertices); stale = "still valid"
except ReferenceError as e:
    stale = f"ReferenceError: {e}"
E.fact("an evaluated mesh obtained before a change is freed when the depsgraph re-evaluates: touching it raises ReferenceError", error=stale)
E.fact("limit_method WEIGHT bevels only edges with a bevel_weight_edge attribute value > 0",
       verts_no_weights=n_no_weights, verts_one_weighted_edge=len(me1.vertices), edge_weight_prop=b2.edge_weight)
E.save()
