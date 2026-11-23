"""Units and scale: what 1.0 means, object scale vs mesh size, applying scale, and how unapplied scale changes modifier widths."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import numpy as np
import bpy
from mathutils import Matrix
import exp
E = exp.Experiment(__file__)

us = bpy.context.scene.unit_settings
E.fact("a fresh scene is metric, scale_length 1.0, lengths in metres: one Blender unit is one metre",
       system=us.system, scale_length=us.scale_length, length_unit=us.length_unit, mass_unit=us.mass_unit, rotation=us.system_rotation)

bpy.ops.mesh.primitive_cube_add()
c = bpy.context.object
E.fact("primitive_cube_add() default size is 2 (spans -1..1)", dimensions=list(c.dimensions))
c.scale = (2, 1, 1)
stale = list(c.dimensions)
bpy.context.view_layer.update()
fresh = list(c.dimensions)
E.fact("object.dimensions includes object scale but is stale right after setting scale: it reads (2,2,2) until view_layer.update(), then (4,2,2); the mesh coordinates do not change",
       before_update=stale, after_update=fresh, mesh_max_x=max(v.co.x for v in c.data.vertices))

# apply scale: data route vs operator
me = c.data
me.transform(Matrix.Diagonal((*c.scale, 1.0)))
c.scale = (1, 1, 1)
bpy.context.view_layer.update()
E.fact("mesh.transform(Matrix.Diagonal(scale)) then scale=(1,1,1) applies scale with the data API", mesh_max_x=max(v.co.x for v in me.vertices),
       dimensions_after_update=list(c.dimensions))
bpy.ops.mesh.primitive_cube_add(location=(5, 0, 0))
d = bpy.context.object
d.scale = (3, 1, 1)
r = bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
E.fact("bpy.ops.object.transform_apply(scale=True) works headless on the selected objects", result=list(r), scale=list(d.scale),
       mesh_max_x=round(max(v.co.x for v in d.data.vertices), 4))

# shared mesh: transform_apply refuses multi-user data
bpy.ops.mesh.primitive_cube_add(location=(0, 5, 0))
a = bpy.context.object
b = a.copy(); bpy.context.collection.objects.link(b)
a.scale = (2, 2, 2)
bpy.ops.object.select_all(action="DESELECT"); a.select_set(True); bpy.context.view_layer.objects.active = a
try:
    r = bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    res = list(r)
except Exception as e:
    res = f"{type(e).__name__}: {str(e).strip()}"
E.fact("transform_apply on an object whose mesh has 2 users fails", result=res, users=a.data.users)

# modifier widths are in local space: Solidify/Bevel scale with object scale
def solid_thickness(scale):
    bpy.ops.mesh.primitive_plane_add(size=2)
    p = bpy.context.object
    p.scale = (scale, scale, scale)
    m = p.modifiers.new("s", "SOLIDIFY"); m.thickness = 0.1; m.offset = -1
    dg = bpy.context.evaluated_depsgraph_get()
    ev = p.evaluated_get(dg)
    z = np.array([(ev.matrix_world @ v.co).z for v in ev.data.vertices])
    return float(z.max() - z.min())
E.fact("a Solidify of thickness 0.1 on an object scaled 3x is 0.3 thick in the world (modifier values are in object space)",
       world_thickness_scale1=round(solid_thickness(1), 4), world_thickness_scale3=round(solid_thickness(3), 4))

# scale_length: what it changes
us.scale_length = 0.01
bpy.ops.mesh.primitive_cube_add()
bpy.context.view_layer.update()
E.fact("scene unit scale_length 0.01 does not change the size of new primitives (it changes only displayed units)",
       dimensions=list(bpy.context.object.dimensions))
us.scale_length = 1.0
E.save()
