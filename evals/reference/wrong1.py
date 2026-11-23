# Wrong: the boolean left as a modifier and glTF's default export_apply=False, so the slab is exported uncut.
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bmesh, bpy
from _common import OUT, link
bpy.ops.wm.read_factory_settings(use_empty=True)
def boxme(name, sx, sy, sz, loc=(0, 0, 0)):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts); bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    bm.to_mesh(me); bm.free(); return me
slab = link(bpy.data.objects.new("Slab", boxme("Slab", 0.3, 0.4, 0.06)))
cut = bmesh.new()
for i in range(5):
    for j in range(6):
        bmesh.ops.create_cube(cut, size=1.0, matrix=__import__("mathutils").Matrix.Translation((-0.12 + 0.06 * i, -0.15 + 0.06 * j, 0)) @ __import__("mathutils").Matrix.Diagonal((0.04, 0.04, 0.1, 1)))
cm = bpy.data.meshes.new("Cutter"); cut.to_mesh(cm); cut.free()
cutter = link(bpy.data.objects.new("Cutter", cm)); cutter.hide_render = True
mod = slab.modifiers.new("Holes", "BOOLEAN"); mod.operation = "DIFFERENCE"; mod.object = cutter
slab.select_set(True); cutter.select_set(False)
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", use_selection=True)
