"""Subdivision Surface, Array and Mirror: counts per setting, and the merge/clip options."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy, bmesh
import exp
E = exp.Experiment(__file__)


def ev(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    me = ob.evaluated_get(dg).data
    xs = [v.co.x for v in me.vertices]
    return dict(verts=len(me.vertices), faces=len(me.polygons), x_min=round(min(xs), 4), x_max=round(max(xs), 4))

bpy.ops.mesh.primitive_cube_add()
c = bpy.context.object
s = c.modifiers.new("Subdivision", "SUBSURF")
E.fact("a new Subdivision Surface modifier: levels 1 (viewport), render_levels 2, Catmull-Clark, quality 3",
       levels=s.levels, render_levels=s.render_levels, subdivision_type=s.subdivision_type, quality=s.quality,
       uv_smooth=s.uv_smooth, boundary_smooth=s.boundary_smooth, use_limit_surface=s.use_limit_surface)
lv = {}
for l in range(0, 5):
    s.levels = l; lv[l] = ev(c)
E.fact(f"Catmull-Clark on a size-2 cube: faces x4 per level (6, 24, 96, 384, 1536); with use_limit_surface on, x_max is {lv[1]['x_max']} at every level 1-4 (vertices sit on the limit surface)", by_level=lv)
s.levels = 2
s.subdivision_type = "SIMPLE"
E.fact("SIMPLE subdivision keeps the cube's shape (x_max stays 1)", **ev(c))
s.subdivision_type = "CATMULL_CLARK"
c.data.attributes.new("crease_edge", "FLOAT", "EDGE")
import numpy as np
c.data.attributes["crease_edge"].data.foreach_set("value", np.ones(12, np.float32)); c.data.update()
E.fact("with crease_edge = 1.0 on every edge, Catmull-Clark keeps the cube's corners (x_max back to 1)", **ev(c))
c.modifiers.clear()

# Array
bpy.ops.mesh.primitive_cube_add(location=(0, 5, 0))
a = bpy.context.object
arr = a.modifiers.new("Array", "ARRAY")
E.fact("a new Array modifier: count 2, fit_type FIXED_COUNT, relative offset (1,0,0), merge off",
       count=arr.count, fit_type=arr.fit_type, use_relative_offset=arr.use_relative_offset, relative_offset=list(arr.relative_offset_displace),
       use_constant_offset=arr.use_constant_offset, use_merge_vertices=arr.use_merge_vertices, merge_threshold=arr.merge_threshold)
arr.count = 5
E.fact("Array count 5 with relative offset 1: copies touch, 5x the verts (no merge)", **ev(a))
arr.use_merge_vertices = True
E.fact("with use_merge_vertices, touching copies share their faces' vertices", **ev(a))
arr.use_merge_vertices = False
arr.use_relative_offset = False; arr.use_constant_offset = True; arr.constant_offset_displace = (3, 0, 0)
E.fact("constant offset 3 on a size-2 cube leaves gaps of 1", **ev(a))
arr.fit_type = "FIT_LENGTH"; arr.fit_length = 20
E.fact("fit_type FIT_LENGTH 20 with constant offset 3 picks the count that fits", count_used=ev(a)["verts"] // 8, **ev(a))
arr.fit_type = "FIT_CURVE"
E.fact("FIT_CURVE with no curve set", **ev(a))
a.modifiers.clear()

# Mirror
bpy.ops.mesh.primitive_cube_add(location=(0, 10, 0))
m = bpy.context.object
bm = bmesh.new(); bm.from_mesh(m.data)
bmesh.ops.translate(bm, verts=bm.verts[:], vec=(1.0, 0, 0))   # mesh now spans x 0..2, touching the mirror plane
bm.to_mesh(m.data); bm.free()
mi = m.modifiers.new("Mirror", "MIRROR")
E.fact("a new Mirror modifier mirrors X across the object's origin, merge on (0.001), clipping off",
       use_axis=list(mi.use_axis), use_bisect_axis=list(mi.use_bisect_axis), use_mirror_merge=mi.use_mirror_merge,
       merge_threshold=mi.merge_threshold, use_clip=mi.use_clip, mirror_object=mi.mirror_object)
E.fact("mirroring a cube that touches the plane at x=0 merges the seam vertices (16 -> 12)", **ev(m))
mi.use_mirror_merge = False
E.fact("with use_mirror_merge off, the seam keeps duplicate vertices", **ev(m))
mi.use_mirror_merge = True
bm = bmesh.new(); bm.from_mesh(m.data)
bmesh.ops.translate(bm, verts=bm.verts[:], vec=(-1.5, 0, 0))   # now crosses the plane: x -0.5..1.5
bm.to_mesh(m.data); bm.free()
E.fact("a mesh crossing the mirror plane overlaps its mirror copy unless use_bisect_axis is on", **ev(m))
mi.use_bisect_axis[0] = True
r1 = ev(m)
mi.use_bisect_flip_axis[0] = True
r2 = ev(m)
E.fact(f"on a mesh spanning x -0.5..1.5, use_bisect_axis[0] keeps the NEGATIVE side and mirrors it (x {r1['x_min']}..{r1['x_max']}); use_bisect_flip_axis[0] keeps the positive side instead (x {r2['x_min']}..{r2['x_max']})",
       bisect=r1, bisect_flip=r2)
E.save()
