# Geometry nodes from Python

Blender 4.5.14 LTS on Apple Silicon. Tags: `[inv]` read from Blender (`scripts/kb.py`), `[exp: path]` measured here
(paths relative to the source repository), `[lesson]` from a real project, `[doc: link]` Blender's documentation.

## What goes wrong most often

1. **The 3.x group-socket API.** `node_group.inputs.new(...)` and `node_group.outputs` do not exist in 4.x
   (`AttributeError: 'GeometryNodeTree' object has no attribute 'inputs'`). Sockets are declared on the interface:
   `ng.interface.new_socket(name=, in_out='INPUT'|'OUTPUT', socket_type='NodeSocketFloat')`. `socket_type` is a
   socket idname; `'FLOAT'` raises a TypeError listing the valid ones. `[exp: experiments/geonodes/build_group.py]`
2. **Setting a modifier input by its name.** Inputs are ID properties keyed by the interface identifier
   (`Socket_1`, `Socket_2`, ...), not the name. `mod["Size"] = 3.0` raised nothing and changed nothing: it made a new,
   unrelated property. Map names to identifiers from `ng.interface.items_tree`.
   `[exp: experiments/geonodes/build_group.py]`
3. **Expecting the change to show.** After `mod[identifier] = 20` the next `evaluated_depsgraph_get()` still returned
   the old result (100 vertices); after `ob.update_tag()` it returned 400. Tag the object after setting inputs.
   `[exp: experiments/geonodes/build_group.py]`
4. **A wrong type for an input.** A float assigned to an Int input's property raised
   `TypeError: Cannot assign a 'float' value to the existing 'Socket_2' Int IDProperty`; convert with `int()`.
   `[exp: experiments/geonodes/build_group.py]`
5. **Expecting a new group or a new modifier to come with anything.** `node_groups.new(name, "GeometryNodeTree")` has no
   nodes and no sockets, and `modifiers.new(name, "NODES")` has no node group. Add Group Input / Group Output nodes,
   a Geometry output socket, and assign the group. `[exp: experiments/geonodes/build_group.py]`
6. **Looking for instances in the evaluated mesh.** With Instance on Points and no Realize Instances, the evaluated
   object's mesh had 0 vertices, `new_from_object` gave 0 vertices, and `modifier_apply` raised "Evaluated geometry
   from modifier does not contain a mesh". Realize them in the tree (4,200 vertices), or read them through
   `depsgraph.object_instances`. `[exp: experiments/geonodes/instances_realize.py]`
7. **Keeping `matrix_world` from the instance iterator.** The iterator reuses its object: 100 kept `matrix_world`
   references all held the last instance's matrix (1 distinct position); `.copy()` kept 100.
   `[exp: experiments/geonodes/instances_realize.py]`
8. **Linking by a socket name that is not unique.** Math's three inputs are all named "Value" (identifiers `Value`,
   `Value_001`, `Value_002`), and Store Named Attribute has one "Value" input per data type, only one enabled. Link by
   index or identifier, and pick the enabled socket. `[exp: experiments/geonodes/build_group.py]` On a FLOAT Random
   Value, `node.inputs["Min"]` returned the enabled FLOAT socket (`Min_001`), not the Vector or INT ones
   of that name; an identifier is not a key (`node.inputs["Min_001"]` raised `KeyError`): find it with
   `next(s for s in node.inputs if s.identifier == "Min_001")`. `[exp: experiments/instancing/variant_sets.py]`
   `[exp: experiments/geonodes/named_attribute_to_shader.py]` Socket names change between versions and cost runs
   when written from memory; look them up. `[lesson: kb/lessons/geometry-nodes.md]`
9. **Mesh Boolean node's enum names.** Its solvers are `EXACT`, `FLOAT`, `MANIFOLD` (default `FLOAT`); the Boolean
   modifier's are `FAST`, `EXACT`, `MANIFOLD`. `node.solver = "FAST"` raises. `[exp: experiments/geonodes/mesh_boolean_node.py]`
10. **Adding a bundled node-group asset with an operator, headless.** `object.modifier_add_node_group` and
    `object.shade_auto_smooth` return CANCELLED with "Asset loading is unfinished". Append from the asset file instead.
    `[exp: experiments/geonodes/bundled_assets.py]`
11. **A misspelt attribute name in a shader.** The Attribute node rendered black with no error. Read the evaluated
    mesh's `attributes` to check the name. `[exp: experiments/geonodes/named_attribute_to_shader.py]`
12. **The Closure zone from Python crashes Blender.** In 4.5.14, reading `paired_output` on an unpaired Closure Input
    node, and calling `pair_with_output` on one, both ended Blender with a segfault (exit -11). The Repeat, Simulation
    and For Each Element inputs behave: `paired_output` is `None` until paired, then the output node.
    `[exp: experiments/geonodes/zone_paired_output.py]`

## Build a node group

Copied from `experiments/geonodes/build_group.py` (a grid displaced by a sine wave, with a material input):

```python
ng = bpy.data.node_groups.new("Grid Wave", "GeometryNodeTree")
ng.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
size = ng.interface.new_socket(name="Size", in_out="INPUT", socket_type="NodeSocketFloat")
size.default_value = 2.0; size.min_value = 0.1; size.max_value = 100.0
res = ng.interface.new_socket(name="Resolution", in_out="INPUT", socket_type="NodeSocketInt")
res.default_value = 10; res.min_value = 2
amp = ng.interface.new_socket(name="Amplitude", in_out="INPUT", socket_type="NodeSocketFloat")
amp.default_value = 0.2
mat = ng.interface.new_socket(name="Material", in_out="INPUT", socket_type="NodeSocketMaterial")

N, L = ng.nodes, ng.links
gin = N.new("NodeGroupInput"); gout = N.new("NodeGroupOutput")
grid = N.new("GeometryNodeMeshGrid")
pos = N.new("GeometryNodeInputPosition")
sep = N.new("ShaderNodeSeparateXYZ")
sin = N.new("ShaderNodeMath"); sin.operation = "SINE"
mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
comb = N.new("ShaderNodeCombineXYZ")
setp = N.new("GeometryNodeSetPosition")
setm = N.new("GeometryNodeSetMaterial")
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
```

- Group Input exposes the interface's inputs as outputs, by name. All 14 links were valid (`link.is_valid`).
- Identifiers are given in creation order across inputs and outputs: here the output got `Socket_0` and the inputs
  `Socket_1` to `Socket_4`. Another group (the bundled Smooth by Angle) has `Input_0`, `Input_1`, `Socket_1`. Never
  assume them; read them.
- A group made this way has `is_modifier` False and still works on a modifier. The flag probably only decides whether
  the UI offers it in the modifier's group menu (untested).

All: `[exp: experiments/geonodes/build_group.py]`. Node idnames used: `NodeGroupInput`, `NodeGroupOutput`,
`GeometryNodeMeshGrid`, `GeometryNodeInputPosition`, `GeometryNodeSetPosition`, `GeometryNodeSetMaterial`,
`ShaderNodeMath`, `ShaderNodeSeparateXYZ`, `ShaderNodeCombineXYZ` (math and vector nodes keep their `ShaderNode`
idnames inside geometry trees). Find others with `python3 scripts/kb.py nodes geometry TERM` and the sockets with
`kb.py node "Label"`. `[inv]`

## Put it on an object and set its inputs

```python
me = bpy.data.meshes.new("host"); ob = bpy.data.objects.new("host", me)
bpy.context.scene.collection.objects.link(ob)
mod = ob.modifiers.new("GN", "NODES")
mod.node_group = ng
ids = {i.name: i.identifier for i in ng.interface.items_tree if i.item_type == "SOCKET" and i.in_out == "INPUT"}
mod[ids["Resolution"]] = 20
mod[ids["Amplitude"]] = 0.5
mod[ids["Material"]] = bpy.data.materials.new("M")
ob.update_tag()                                        # or the next evaluation may not see the change
dg = bpy.context.evaluated_depsgraph_get()
ev = ob.evaluated_get(dg).data                         # 400 vertices, z from -0.42 to 0.42
```

Assigning the group fills the modifier with the interface defaults (`Socket_1` 2.0, `Socket_2` 10, ...). Each input
`X` also gets `X_use_attribute` and `X_attribute_name`, to drive it from a named attribute instead of a value. The
Material input took a `bpy.types.Material`, and Set Material put it in the evaluated mesh's materials.
`[exp: experiments/geonodes/build_group.py]` The `item_type == "SOCKET"` test skips panels, which have no `in_out`.

## Instances and realised geometry

```python
inst = N.new("GeometryNodeInstanceOnPoints")
L.new(pts.outputs["Points"], inst.inputs["Points"])
L.new(ico.outputs["Mesh"], inst.inputs["Instance"])
rz = N.new("GeometryNodeRealizeInstances")              # without this, the evaluated mesh is empty
L.new(inst.outputs["Instances"], rz.inputs["Geometry"])
```

Reading instances without realising them, copied from `experiments/geonodes/instances_realize.py`:

```python
dg = bpy.context.evaluated_depsgraph_get()
for i in dg.object_instances:
    if i.is_instance and i.parent and i.parent.original == a:
        m = i.matrix_world.copy()                      # copy: the iterator reuses the object
        verts = len(i.object.data.vertices)            # the instanced mesh (42 for an icosphere)
```

100 points gave 100 instances of type MESH; the loop took 0.3 ms. `ev.evaluated_geometry()` returns a GeometrySet
(`mesh`, `pointcloud`, `curves`, `volume`, `grease_pencil`, `instances_pointcloud()`, `instance_references()`); its
`instances_pointcloud()` had 100 points. `[exp: experiments/geonodes/instances_realize.py]` Kept as instances, small
details save memory and file size but are not faster to build than Python/bmesh (about 13,000 pieces took 2.5 s in
Python). `[lesson: kb/lessons/geometry-nodes.md]`

## Named attributes from nodes into a shader

Copied from `experiments/geonodes/named_attribute_to_shader.py`:

```python
st = N.new("GeometryNodeStoreNamedAttribute")
st.data_type = "FLOAT_COLOR"; st.domain = "POINT"
st.inputs["Name"].default_value = "tint"
val = next(s for s in st.inputs if s.name == "Value" and s.enabled)   # the input for the chosen data_type
val.default_value = (1.0, 0.2, 0.0, 1.0)

an = nt.nodes.new("ShaderNodeAttribute")               # in the material
an.attribute_name = "tint"; an.attribute_type = "GEOMETRY"
nt.links.new(an.outputs["Color"], em.inputs["Color"])
```

The evaluated mesh had `tint` (POINT, FLOAT_COLOR); the original did not. A 32 px Cycles render of the plane read
(0.996, 0.482, 0.0) at the centre: 0.2 linear is 0.48 in sRGB. With the name misspelt it read (0, 0, 0).
`[exp: experiments/geonodes/named_attribute_to_shader.py]` `attribute_type` can be GEOMETRY, OBJECT, INSTANCER or
VIEW_LAYER; INSTANCER reads attributes stored on instances (untested here). `[inv]`

## Repeat zones

A zone is two nodes joined in Python. Copied from `experiments/geonodes/repeat_zone.py`:

```python
rin = N.new("GeometryNodeRepeatInput")
rout = N.new("GeometryNodeRepeatOutput")
rin.pair_with_output(rout)                             # returns True; rin.paired_output is now rout
item = rout.repeat_items.new("FLOAT", "Count")         # state items are added on the OUTPUT node
L.new(gi.outputs["Iterations"], rin.inputs["Iterations"])
L.new(cube.outputs["Mesh"], rin.inputs["Geometry"])
L.new(rin.outputs["Geometry"], sub.inputs["Mesh"])     # the loop body
L.new(sub.outputs["Mesh"], rout.inputs["Geometry"])
L.new(rin.outputs["Count"], add.inputs[0])
L.new(add.outputs["Value"], rout.inputs["Count"])
```

The zone starts with one Geometry item; a new item appears on both nodes (Repeat Input: Iterations, Geometry, Count;
its outputs: Iteration, Geometry, Count). Subdividing a cube N times gave 6, 24 and 384 faces for N = 0, 1, 3, and the
Count item read 0, 1, 3. `[exp: experiments/geonodes/repeat_zone.py]` Simulation zones (state carried between frames)
are in `simulation.md`.

## Bundled node-group assets

`datafiles/assets/geometry_nodes/` holds two files: `smooth_by_angle.blend` (1 asset, Smooth by Angle) and
`procedural_hair_node_assets.blend` (26 assets: Trim, Straighten, Smooth, Shrinkwrap, Set Hair Curve Profile, Rotate,
Roll, Restore Curve Segment Length, Redistribute Curve Points, Interpolate, Noise, Hair Attachment Info, Generate,
Frizz, Duplicate, Displace, Curve Tip, Curve Segment, Curve Root, Curve Info, Curl, Create Guide Index Map, Clump,
Braid, Blend, Attach Hair Curves to Surface). Appending all 26 brought 27 groups (one dependency), 21 of them modifier
groups. `[exp: experiments/geonodes/bundled_assets.py]` None of them simulates hair. `[lesson: kb/lessons/geometry-nodes.md]`

```python
root = os.path.join(bpy.utils.system_resource("DATAFILES"), "assets", "geometry_nodes")
with bpy.data.libraries.load(os.path.join(root, "smooth_by_angle.blend"), link=True) as (src, dst):
    dst.node_groups = ["Smooth by Angle"]               # link=False appends an editable copy
g = bpy.data.node_groups["Smooth by Angle"]
m = ob.modifiers.new("Smooth by Angle", "NODES"); m.node_group = g
```

`assets_only=True` in `libraries.load` lists only the groups marked as assets. A linked group is not editable
(`is_editable` False) but evaluates: 64 rim edges sharp on a smoothed 32-sided cylinder.
`[exp: experiments/geonodes/bundled_assets.py]`

## Mesh Boolean node

| | Mesh Boolean node | Boolean modifier |
|---|---|---|
| solver identifiers | `EXACT`, `FLOAT`, `MANIFOLD` | `FAST`, `EXACT`, `MANIFOLD` |
| default solver | `FLOAT` | `EXACT` |
| a new one's operation | `DIFFERENCE` | `DIFFERENCE` |

`[exp: experiments/geonodes/mesh_boolean_node.py]` (`kb.py node "Mesh Boolean"` lists the RNA default of operation as
INTERSECT `[inv]`; a node made with `nodes.new` had DIFFERENCE.) Its inputs are "Mesh 1" and a multi-input
"Mesh 2", plus hidden Self Intersection and Hole Tolerant `[inv]`. A cube minus a 32-sided cylinder came out the same
with all three solvers: 72 vertices, genus 1, manifold, volume 6.4393. `[exp: experiments/geonodes/mesh_boolean_node.py]`
For many cutters and the cases where solvers differ, see the Boolean section of `modifiers.md`.

## Reference: 3.x to 4.5

| 3.x | 4.5 |
|---|---|
| `ng.inputs.new("NodeSocketFloat", "Size")` | `ng.interface.new_socket(name="Size", in_out="INPUT", socket_type="NodeSocketFloat")` |
| `ng.outputs.new("NodeSocketGeometry", "Geometry")` | `ng.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")` |
| `ng.inputs["Size"].default_value` | the interface socket's `default_value`, `min_value`, `max_value` |
| `mod["Input_2"]` | `mod["Socket_N"]` for sockets made in 4.x (`Input_N` survives in older files and assets) |
| a NODES modifier creating its own group | none: assign `mod.node_group` |
| `object.shade_auto_smooth` toggling a mesh flag | it adds the Smooth by Angle NODES modifier (UI only) |

Interface functions: `new_socket`, `new_panel`, `copy`, `remove`, `clear`, `move`, `move_to_parent` `[inv]`.
