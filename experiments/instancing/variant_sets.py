"""Found by C-005's shot: a Poly Haven model can be a set of variants laid side by side; and does Random Value's sharing
of socket names across data types (Min, Max, Value) catch a script that uses names? Measured: how many parts each model the shot used arrived as; instancing one part
against the whole set through Collection Info (Separate Children, Reset Children) with Pick Instance; and what
node.inputs["Min"] returns on a FLOAT Random Value, what node.inputs["Min_001"] does, and the scales a scatter gets
each way (read back from the depsgraph's instances)."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy
import exp

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "skills", "blender", "scripts"))
import asset_import as ai  # noqa: E402

E = exp.Experiment(__file__)
parts = {}
for key in ("fern_02", "shrub_sorrel_01", "rock_09", "boulder_01", "tree_stump_01", "dead_tree_trunk_02"):
    exp.empty()
    objs, size = ai.import_model(ai.manifest("polyhaven", key))
    meshes = [o for o in objs if o.type == "MESH"]
    one = [round(max(v.co[i] for v in meshes[0].data.vertices) - min(v.co[i] for v in meshes[0].data.vertices), 3) for i in range(3)]
    parts[key] = dict(objects=len(objs), meshes=len(meshes), set_size_m=[round(x, 3) for x in size], first_part_size_m=one)
E.fact("parts each Poly Haven model arrived as from glTF, the size of the whole import and of its first part alone "
       "(fern_02 and shrub_sorrel_01 are sets of variants side by side)", rows=parts)

exp.empty()
objs, _ = ai.import_model(ai.manifest("polyhaven", "fern_02"))
col = bpy.data.collections.new("Ferns")
bpy.context.scene.collection.children.link(col)
for o in objs:
    for c in list(o.users_collection):
        c.objects.unlink(o)
    col.objects.link(o)
bpy.ops.mesh.primitive_plane_add(size=1)
host = bpy.context.object


def sin(node, ident):
    return next(x for x in node.inputs if x.identifier == ident)


def sout(node, ident):
    return next(x for x in node.outputs if x.identifier == ident)


def scatter(by_identifier, n_points=200):
    ng = bpy.data.node_groups.new("S", "GeometryNodeTree")
    ng.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N, L = ng.nodes, ng.links
    grid = N.new("GeometryNodeMeshGrid")
    grid.inputs["Vertices X"].default_value = grid.inputs["Vertices Y"].default_value = int(n_points ** 0.5)
    info = N.new("GeometryNodeCollectionInfo")
    info.inputs["Collection"].default_value = col
    info.inputs["Separate Children"].default_value = True
    info.inputs["Reset Children"].default_value = True
    pick = N.new("FunctionNodeRandomValue")
    pick.data_type = "INT"
    sin(pick, "Min_002").default_value, sin(pick, "Max_002").default_value = 0, 3
    rs = N.new("FunctionNodeRandomValue")
    rs.data_type = "FLOAT"
    if by_identifier:
        sin(rs, "Min_001").default_value, sin(rs, "Max_001").default_value = 1.4, 2.4
        out = sout(rs, "Value_001")
    else:
        rs.inputs["Min"].default_value, rs.inputs["Max"].default_value = 1.4, 2.4   # by name
        out = rs.outputs["Value"]
    inst = N.new("GeometryNodeInstanceOnPoints")
    L.new(grid.outputs["Mesh"], inst.inputs["Points"])
    L.new(info.outputs["Instances"], inst.inputs["Instance"])
    inst.inputs["Pick Instance"].default_value = True
    L.new(sout(pick, "Value_002"), inst.inputs["Instance Index"])
    lk = L.new(out, inst.inputs["Scale"])
    L.new(inst.outputs["Instances"], N.new("NodeGroupOutput").inputs["Geometry"])
    for md in list(host.modifiers):
        host.modifiers.remove(md)
    host.modifiers.new("S", "NODES").node_group = ng
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    sc = [i.matrix_world.to_scale().z for i in dg.object_instances if i.is_instance and i.parent and i.parent.original == host]
    names = {i.object.original.name for i in dg.object_instances if i.is_instance and i.parent and i.parent.original == host}
    return dict(instances=len(sc), scale_min=round(min(sc), 3), scale_max=round(max(sc), 3),
                variants_used=len(names), link_valid=lk.is_valid, socket_linked=out.identifier,
                socket_enabled=out.enabled)


rs = bpy.data.node_groups.new("T", "GeometryNodeTree").nodes.new("FunctionNodeRandomValue")
rs.data_type = "FLOAT"
try:
    rs.inputs["Min_001"]
    by_key = "found"
except KeyError as e:
    by_key = f"KeyError: {e}"
E.fact("on a FLOAT Random Value, node.inputs['Min'] returns the FLOAT socket (Min_001), not the Vector or INT ones "
       "of the same name that this data type leaves unused; node.inputs['Min_001'] raises KeyError (keys are names); "
       "searching the sockets by identifier finds it",
       inputs_Min=dict(identifier=rs.inputs["Min"].identifier, type=rs.inputs["Min"].type, enabled=rs.inputs["Min"].enabled),
       inputs_Min_001=by_key,
       by_identifier=dict(identifier=sin(rs, "Min_001").identifier, type=sin(rs, "Min_001").type))
E.fact("a fern scatter asking for scale 1.4 to 2.4, with Random Value's sockets taken by name and by identifier: the "
       "scales the instances got, how many of the set's 4 variants were used, and whether the scale link is valid",
       by_name=scatter(False), by_identifier=scatter(True))
E.save()
