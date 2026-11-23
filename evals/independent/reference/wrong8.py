# Wrong solution, task 8: sets the modifier input by its name instead of its identifier.
import bpy, sys

out = sys.argv[sys.argv.index("--") + 1]

bpy.ops.wm.read_factory_settings(use_empty=True)

me = bpy.data.meshes.new("Base")
ob = bpy.data.objects.new("Scatter", me)
bpy.context.scene.collection.objects.link(ob)

ng = bpy.data.node_groups.new("SphereGrid", 'GeometryNodeTree')
ng.is_modifier = True
# Blender 4.0+: sockets are declared on the tree's interface.
ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
scale_sock = ng.interface.new_socket("Scale", in_out='INPUT', socket_type='NodeSocketFloat')
scale_sock.default_value = 1.0
ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

N = ng.nodes
gin = N.new("NodeGroupInput")
gout = N.new("NodeGroupOutput")
grid = N.new("GeometryNodeMeshGrid")
grid.inputs["Size X"].default_value = 5.0
grid.inputs["Size Y"].default_value = 5.0
grid.inputs["Vertices X"].default_value = 6
grid.inputs["Vertices Y"].default_value = 6
ico = N.new("GeometryNodeMeshIcoSphere")
ico.inputs["Radius"].default_value = 0.2
ico.inputs["Subdivisions"].default_value = 1
inst = N.new("GeometryNodeInstanceOnPoints")
real = N.new("GeometryNodeRealizeInstances")

L = ng.links
L.new(grid.outputs["Mesh"], inst.inputs["Points"])
L.new(ico.outputs["Mesh"], inst.inputs["Instance"])
L.new(gin.outputs["Scale"], inst.inputs["Scale"])
L.new(inst.outputs["Instances"], real.inputs["Geometry"])
L.new(real.outputs["Geometry"], gout.inputs["Geometry"])

mod = ob.modifiers.new("SphereGrid", 'NODES')
mod.node_group = ng
mod["Scale"] = 0.5

bpy.ops.wm.save_as_mainfile(filepath=out)
