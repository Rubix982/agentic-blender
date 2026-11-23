# Reference solution, task 2: box with weighted bevel on its vertical edges, then an array.
import bpy, sys, bmesh

out = sys.argv[sys.argv.index("--") + 1]

bpy.ops.wm.read_factory_settings(use_empty=True)

me = bpy.data.meshes.new("Block")
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=1.0)
for v in bm.verts:                      # unit cube -> 2 x 2 x 1, base on z = 0
    v.co.x *= 2.0
    v.co.y *= 2.0
    v.co.z += 0.5
bm.to_mesh(me)
bm.free()

ob = bpy.data.objects.new("Block", me)
bpy.context.scene.collection.objects.link(ob)

# Blender 4.0+: bevel weights live in the generic edge attribute "bevel_weight_edge".
attr = me.attributes.new("bevel_weight_edge", 'FLOAT', 'EDGE')
weights = []
for e in me.edges:
    a, b = (me.vertices[i].co for i in e.vertices)
    vertical = abs(a.x - b.x) < 1e-6 and abs(a.y - b.y) < 1e-6
    weights.append(1.0 if vertical else 0.0)
attr.data.foreach_set("value", weights)

bev = ob.modifiers.new("Bevel", 'BEVEL')
bev.limit_method = 'WEIGHT'
bev.width = 0.1
bev.segments = 3

arr = ob.modifiers.new("Array", 'ARRAY')
arr.count = 3
arr.use_relative_offset = False
arr.use_constant_offset = True
arr.constant_offset_displace = (2.5, 0.0, 0.0)   # 2 m box + 0.5 m gap
arr.use_merge_vertices = False

bpy.ops.wm.save_as_mainfile(filepath=out)
