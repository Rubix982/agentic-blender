"""A repeat zone built from Python: pairing the input/output nodes, adding a state item, and checking the iteration count."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy
import exp
E = exp.Experiment(__file__)

ng = bpy.data.node_groups.new("Repeat", "GeometryNodeTree")
ng.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
it = ng.interface.new_socket(name="Iterations", in_out="INPUT", socket_type="NodeSocketInt"); it.default_value = 3
N, L = ng.nodes, ng.links
gi, go = N.new("NodeGroupInput"), N.new("NodeGroupOutput")
cube = N.new("GeometryNodeMeshCube")
rin = N.new("GeometryNodeRepeatInput")
rout = N.new("GeometryNodeRepeatOutput")
paired_before = rin.paired_output
ok = rin.pair_with_output(rout)
E.fact("a repeat zone is two nodes, GeometryNodeRepeatInput and GeometryNodeRepeatOutput, joined by repeat_input.pair_with_output(repeat_output)",
       paired_before=paired_before.name if paired_before else None, pair_returned=ok, paired_after=rin.paired_output.name if rin.paired_output else None,
       default_items=[(i.name, i.socket_type) for i in rout.repeat_items])
# add a float state item: counts iterations
item = rout.repeat_items.new("FLOAT", "Count")
E.fact("repeat_items.new(socket_type, name) on the OUTPUT node adds a state item that appears on both nodes",
       items=[(i.name, i.socket_type) for i in rout.repeat_items], input_sockets=[s.name for s in rin.inputs], output_sockets=[s.name for s in rin.outputs])
sub = N.new("GeometryNodeSubdivideMesh"); sub.inputs["Level"].default_value = 1
add = N.new("ShaderNodeMath"); add.operation = "ADD"; add.inputs[1].default_value = 1.0
store = N.new("GeometryNodeStoreNamedAttribute"); store.data_type = "FLOAT"; store.domain = "POINT"; store.inputs["Name"].default_value = "count"
L.new(gi.outputs["Iterations"], rin.inputs["Iterations"])
L.new(cube.outputs["Mesh"], rin.inputs["Geometry"])
L.new(rin.outputs["Geometry"], sub.inputs["Mesh"])
L.new(sub.outputs["Mesh"], rout.inputs["Geometry"])
L.new(rin.outputs["Count"], add.inputs[0])
L.new(add.outputs["Value"], rout.inputs["Count"])
L.new(rout.outputs["Geometry"], store.inputs["Geometry"])
L.new(rout.outputs["Count"], next(s for s in store.inputs if s.name == "Value" and s.enabled))
L.new(store.outputs["Geometry"], go.inputs["Geometry"])
E.fact("links valid", invalid=[(l.from_node.name, l.from_socket.name, l.to_node.name, l.to_socket.name) for l in L if not l.is_valid])

me = bpy.data.meshes.new("h"); ob = bpy.data.objects.new("h", me); bpy.context.scene.collection.objects.link(ob)
m = ob.modifiers.new("GN", "NODES"); m.node_group = ng
res = {}
ident = next(i.identifier for i in ng.interface.items_tree if i.name == "Iterations")
for n in (0, 1, 3):
    m[ident] = n; ob.update_tag()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg).data
    c = ev.attributes.get("count")
    res[n] = dict(faces=len(ev.polygons), count=c.data[0].value if c else None)
E.fact("subdividing a cube N times in a repeat zone gives 6*4^N faces and the float state item counts N", by_iterations=res)
E.save()
