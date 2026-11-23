"""Displace with a texture, and Shrinkwrap's wrap methods: measured displacement and distance to the target."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import numpy as np
import bpy
from mathutils.bvhtree import BVHTree
import exp
E = exp.Experiment(__file__)


def zs(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    me = ob.evaluated_get(dg).data
    a = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", a)
    return a.reshape(-1, 3)[:, 2]

bpy.ops.mesh.primitive_grid_add(x_subdivisions=64, y_subdivisions=64, size=2)
g = bpy.context.object
d = g.modifiers.new("Displace", "DISPLACE")
E.fact("a new Displace modifier: strength 1, mid_level 0.5, direction NORMAL, no texture", strength=d.strength, mid_level=d.mid_level,
       direction=d.direction, texture=d.texture, texture_coords=d.texture_coords, space=d.space)
z = zs(g)
E.fact("with no texture, Displace moves every vertex by (1 - mid_level) * strength along the normal", z_min=float(z.min()), z_max=float(z.max()))
tex = bpy.data.textures.new("clouds", "CLOUDS")
tex.noise_scale = 0.5
d.texture = tex
z = zs(g)
E.fact("with a CLOUDS texture (bpy.data.textures.new(name, 'CLOUDS')), displacement = (value - mid_level) * strength", z_min=round(float(z.min()), 4),
       z_max=round(float(z.max()), 4), z_std=round(float(z.std()), 4), texture_types=[e.identifier for e in bpy.types.BlendDataTextures.bl_rna.functions["new"].parameters["type"].enum_items])
d.mid_level = 0.0; d.strength = 0.2
z = zs(g)
E.fact("mid_level 0, strength 0.2: all displacement is outward, 0..0.2", z_min=round(float(z.min()), 4), z_max=round(float(z.max()), 4))
d.direction = "Z"; d.texture_coords = "GLOBAL"
z2 = zs(g)
E.fact("direction 'Z' and texture_coords 'GLOBAL' are accepted (texture_coords: LOCAL, GLOBAL, OBJECT, UV)", z_max=round(float(z2.max()), 4),
       coords=[e.identifier for e in d.bl_rna.properties["texture_coords"].enum_items])
# image texture route
img = bpy.data.images.new("ramp", 8, 8)
px = np.zeros((8, 8, 4), np.float32); px[..., 3] = 1; px[:, :, 0:3] = np.linspace(0, 1, 8)[None, :, None]
img.pixels.foreach_set(px.ravel())
it = bpy.data.textures.new("img", "IMAGE"); it.image = img
d.texture = it; d.texture_coords = "UV"; d.mid_level = 0; d.strength = 1; d.direction = "NORMAL"
z3 = zs(g)
E.fact("an IMAGE texture (a ramp 0..1 along x) with UV coords displaces from about 0 to 1 across the grid", z_min=round(float(z3.min()), 3), z_max=round(float(z3.max()), 3))

# Shrinkwrap: a subdivided cube onto a sphere of radius 1
bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=1.0, location=(5, 0, 0))
target = bpy.context.object
bpy.ops.mesh.primitive_cube_add(size=3, location=(5, 0, 0))
c = bpy.context.object
sub = c.modifiers.new("s", "SUBSURF"); sub.levels = 3; sub.subdivision_type = "SIMPLE"
sw = c.modifiers.new("Shrinkwrap", "SHRINKWRAP")
sw.target = target
E.fact("a new Shrinkwrap: wrap_method NEAREST_SURFACEPOINT, wrap_mode ON_SURFACE, offset 0",
       wrap_method=sw.wrap_method, wrap_mode=sw.wrap_mode, offset=sw.offset,
       methods=[e.identifier for e in sw.bl_rna.properties["wrap_method"].enum_items],
       modes=[e.identifier for e in sw.bl_rna.properties["wrap_mode"].enum_items])
dg = bpy.context.evaluated_depsgraph_get()
bvh = BVHTree.FromObject(target, dg)
def dist_stats():
    dg = bpy.context.evaluated_depsgraph_get()
    ev = c.evaluated_get(dg)
    mw = ev.matrix_world; tmi = target.matrix_world.inverted()
    ds = []
    for v in ev.data.vertices:
        p = tmi @ (mw @ v.co)
        loc, n, i, dist = bvh.find_nearest(p)
        ds.append(dist)
    ds = np.array(ds)
    r = np.array([(tmi @ (mw @ v.co)).length for v in ev.data.vertices])
    return dict(max_dist_to_surface=round(float(ds.max()), 5), radius_min=round(float(r.min()), 4), radius_max=round(float(r.max()), 4))
res = {}
for meth in ("NEAREST_SURFACEPOINT", "PROJECT", "NEAREST_VERTEX", "TARGET_PROJECT"):
    sw.wrap_method = meth
    if meth == "PROJECT":
        sw.use_negative_direction = True; sw.use_positive_direction = True; sw.use_project_z = False
    res[meth] = dist_stats()
E.fact("Shrinkwrap of a subdivided cube (size 3) onto a unit sphere: NEAREST_SURFACEPOINT, NEAREST_VERTEX and TARGET_PROJECT put every vertex on the target; PROJECT (no axis, both directions) casts along each vertex normal and leaves the vertices whose ray misses where they were",
       by_method=res)
sw.wrap_method = "NEAREST_SURFACEPOINT"; sw.offset = 0.1
E.fact("Shrinkwrap offset 0.1 keeps vertices 0.1 off the surface", **dist_stats())
E.save()
