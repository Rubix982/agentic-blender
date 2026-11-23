"""Build a geometry-nodes group entirely from Python (4.x interface API), put it on an object, set its inputs, read the result."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy
import exp
E = exp.Experiment(__file__)

ng = bpy.data.node_groups.new("Grid Wave", "GeometryNodeTree")
E.fact("a new GeometryNodeTree has no nodes and an empty interface; is_modifier is False", nodes=len(ng.nodes),
       items=len(ng.interface.items_tree), is_modifier=ng.is_modifier)

# the removed 3.x API
gone = {k: hasattr(ng, k) for k in ("inputs", "outputs")}
try:
    ng.inputs.new("NodeSocketFloat", "x"); old = "accepted"
except Exception as e:
    old = f"{type(e).__name__}: {e}"
E.fact("node_group.inputs / .outputs (3.x) are gone in 4.x: ng.inputs.new raises", has=gone, error=old)

# interface: outputs and inputs
geo_out = ng.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
size = ng.interface.new_socket(name="Size", in_out="INPUT", socket_type="NodeSocketFloat")
size.default_value = 2.0; size.min_value = 0.1; size.max_value = 100.0
res = ng.interface.new_socket(name="Resolution", in_out="INPUT", socket_type="NodeSocketInt")
res.default_value = 10; res.min_value = 2
amp = ng.interface.new_socket(name="Amplitude", in_out="INPUT", socket_type="NodeSocketFloat")
amp.default_value = 0.2
mat = ng.interface.new_socket(name="Material", in_out="INPUT", socket_type="NodeSocketMaterial")
E.fact("interface.new_socket(name, in_out, socket_type) adds group sockets; socket_type is the NodeSocket* idname",
       items=[(i.name, i.in_out, i.socket_type, i.identifier) for i in ng.interface.items_tree])
try:
    ng.interface.new_socket(name="Bad", in_out="INPUT", socket_type="FLOAT"); bad = "accepted"
except Exception as e:
    bad = f"{type(e).__name__}: {str(e)[:200]}"
E.fact("socket_type must be an idname like 'NodeSocketFloat'; 'FLOAT' raises", error=bad)

# nodes
N, L = ng.nodes, ng.links
gin = N.new("NodeGroupInput"); gin.location = (-600, 0)
gout = N.new("NodeGroupOutput"); gout.location = (600, 0)
grid = N.new("GeometryNodeMeshGrid")
pos = N.new("GeometryNodeInputPosition")
sep = N.new("ShaderNodeSeparateXYZ")
sin = N.new("ShaderNodeMath"); sin.operation = "SINE"
mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
comb = N.new("ShaderNodeCombineXYZ")
setp = N.new("GeometryNodeSetPosition")
setm = N.new("GeometryNodeSetMaterial")
E.fact("node sockets by name on Mesh Grid and Set Position", grid_inputs=[s.name for s in grid.inputs],
       setpos_inputs=[s.name for s in setp.inputs], math_inputs=[(s.name, s.identifier) for s in mul.inputs])
L.new(gin.outputs["Size"], grid.inputs["Size X"])
L.new(gin.outputs["Size"], grid.inputs["Size Y"])
L.new(gin.outputs["Resolution"], grid.inputs["Vertices X"])
L.new(gin.outputs["Resolution"], grid.inputs["Vertices Y"])
L.new(pos.outputs["Position"], sep.inputs["Vector"])
L.new(sep.outputs["X"], sin.inputs[0])
L.new(sin.outputs["Value"], mul.inputs[0])
L.new(gin.outputs["Amplitude"], mul.inputs[1])
L.new(mul.outputs["Value"], comb.inputs["Z"])
L.new(grid.outputs["Mesh"], setp.inputs["Geometry"])
L.new(comb.outputs["Vector"], setp.inputs["Offset"])
L.new(setp.outputs["Geometry"], setm.inputs["Geometry"])
L.new(gin.outputs["Material"], setm.inputs["Material"])
L.new(setm.outputs["Geometry"], gout.inputs["Geometry"])
E.fact("all links valid", invalid=[(l.from_socket.name, l.to_socket.name) for l in L if not l.is_valid])

# object + modifier
me = bpy.data.meshes.new("host"); ob = bpy.data.objects.new("host", me); bpy.context.scene.collection.objects.link(ob)
mod = ob.modifiers.new("GN", "NODES")
E.fact("a NODES modifier added from Python has no node group (4.x does not auto-create one)", node_group=mod.node_group)
mod.node_group = ng
keys = list(mod.keys())
E.fact("modifier input values are ID properties keyed by the interface socket identifier (Socket_N), not by name",
       keys=keys, ident_by_name={i.name: i.identifier for i in ng.interface.items_tree if i.in_out == "INPUT"})
E.fact("after assigning the group, the modifier holds the interface defaults", values={k: mod[k] for k in keys if not k.endswith(("_use_attribute", "_attribute_name"))})
try:
    mod["Size"] = 3.0; by_name = "accepted (but it is a new unrelated ID property)"
except Exception as e:
    by_name = f"{type(e).__name__}: {e}"
E.fact("mod['Size'] (the socket name) is not the input", result=by_name)
if "Size" in mod.keys():
    del mod["Size"]

ids = {i.name: i.identifier for i in ng.interface.items_tree if i.item_type == "SOCKET" and i.in_out == "INPUT"}
E.fact("name -> identifier map read from ng.interface.items_tree (item_type 'SOCKET', in_out 'INPUT')", ids=ids)
dg = bpy.context.evaluated_depsgraph_get()
v0 = len(ob.evaluated_get(dg).data.vertices)
mod[res.identifier] = 20
dg = bpy.context.evaluated_depsgraph_get()
v1 = len(ob.evaluated_get(dg).data.vertices)
ob.update_tag()
dg = bpy.context.evaluated_depsgraph_get()
v2 = len(ob.evaluated_get(dg).data.vertices)
E.fact("setting mod[identifier] = value " + ("is picked up by the next evaluation without update_tag()" if v1 == 400 else "needs ob.update_tag() before the next evaluation picks it up"),
       verts_default=v0, verts_after_set=v1, verts_after_update_tag=v2)
mod[amp.identifier] = 0.5
ob.update_tag()
dg = bpy.context.evaluated_depsgraph_get()
z = [v.co.z for v in ob.evaluated_get(dg).data.vertices]
E.fact("the evaluated mesh carries the node result (sin wave, amplitude 0.5)", z_min=round(min(z), 4), z_max=round(max(z), 4))
# wrong type value
try:
    mod[res.identifier] = 2.5; ob.update_tag(); dg = bpy.context.evaluated_depsgraph_get(); wt = f"accepted; verts {len(ob.evaluated_get(dg).data.vertices)}"
except Exception as e:
    wt = f"{type(e).__name__}: {e}"
E.fact("assigning a float to an Int input's ID property", result=wt, stored=repr(mod[res.identifier]))
mod[res.identifier] = 20
# material input
m = bpy.data.materials.new("M")
mod[mat.identifier] = m
ob.update_tag(); dg = bpy.context.evaluated_depsgraph_get()
evm = ob.evaluated_get(dg).data
E.fact("a Material input takes a bpy.types.Material; Set Material adds it to the evaluated mesh's materials", materials=[x.name for x in evm.materials if x])
# is_modifier flag
E.fact("a group created by data API is usable on a modifier even with is_modifier False", is_modifier=ng.is_modifier)
ng.is_modifier = True
# use_attribute toggle
E.fact("each input also has <id>_use_attribute and <id>_attribute_name keys to drive it by an attribute",
       keys=[k for k in mod.keys() if k.startswith(size.identifier)])
# idnames listing
E.fact("node idnames used here", idnames=sorted({n.bl_idname for n in N}))
E.save()
