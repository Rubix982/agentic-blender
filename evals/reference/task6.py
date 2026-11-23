# Hanging cloth: a 1 m square (20 x 20 grid) pinned at its two top corners, falling for 60 frames, baked.
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bmesh, bpy
from _common import OUT, link
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.frame_start, sc.frame_end = 1, 60
me = bpy.data.meshes.new("Cloth"); bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=20, y_segments=20, size=0.5)   # size is half the width: 1 m
bm.to_mesh(me); bm.free()
ob = link(bpy.data.objects.new("Cloth", me)); ob.location.z = 1.5
pins = [v.index for v in me.vertices if v.co.y > 0.49 and abs(v.co.x) > 0.49]
vg = ob.vertex_groups.new(name="pin"); vg.add(pins, 1.0, "REPLACE")
cl = ob.modifiers.new("Cloth", "CLOTH")
cl.settings.vertex_group_mass = "pin"
cl.point_cache.frame_start, cl.point_cache.frame_end = 1, 60
with bpy.context.temp_override(object=ob, active_object=ob, point_cache=cl.point_cache):
    bpy.ops.ptcache.bake(bake=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
