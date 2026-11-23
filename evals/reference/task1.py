# Pierced slab: 300 x 400 x 60 mm, a 5 x 6 grid of 40 mm square holes right through, exported as a GLB in metres.
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bmesh, bpy
from _common import OUT, link

bpy.ops.wm.read_factory_settings(use_empty=True)
def box(name, sx, sy, sz, loc=(0, 0, 0)):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    bm.to_mesh(me); bm.free()
    return me
slab = link(bpy.data.objects.new("Slab", box("Slab", 0.3, 0.4, 0.06)))
cut_bm = bmesh.new()
for i in range(5):
    for j in range(6):
        tmp = bmesh.new(); bmesh.ops.create_cube(tmp, size=1.0)
        bmesh.ops.scale(tmp, vec=(0.04, 0.04, 0.1), verts=tmp.verts)
        bmesh.ops.translate(tmp, vec=(-0.12 + 0.06 * i, -0.15 + 0.06 * j, 0), verts=tmp.verts)
        me_t = bpy.data.meshes.new("t"); tmp.to_mesh(me_t); tmp.free(); cut_bm.from_mesh(me_t); bpy.data.meshes.remove(me_t)
cut_me = bpy.data.meshes.new("Cutter"); cut_bm.to_mesh(cut_me); cut_bm.free()
cutter = link(bpy.data.objects.new("Cutter", cut_me))
mod = slab.modifiers.new("Holes", "BOOLEAN"); mod.operation = "DIFFERENCE"; mod.object = cutter; mod.solver = "EXACT"
dg = bpy.context.evaluated_depsgraph_get()
new = bpy.data.meshes.new_from_object(slab.evaluated_get(dg))
slab.modifiers.clear(); old = slab.data; slab.data = new; bpy.data.meshes.remove(old)
bpy.data.objects.remove(cutter)
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB")
