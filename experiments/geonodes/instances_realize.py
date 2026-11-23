"""Instances vs realised geometry out of geometry nodes: what the evaluated mesh contains, and how to read instances."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import time
import bpy
import exp
E = exp.Experiment(__file__)


def group(realize):
    ng = bpy.data.node_groups.new("Scatter", "GeometryNodeTree")
    ng.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N, L = ng.nodes, ng.links
    out = N.new("NodeGroupOutput")
    grid = N.new("GeometryNodeMeshGrid"); grid.inputs["Vertices X"].default_value = 10; grid.inputs["Vertices Y"].default_value = 10
    grid.inputs["Size X"].default_value = 10; grid.inputs["Size Y"].default_value = 10
    pts = N.new("GeometryNodeMeshToPoints")
    ico = N.new("GeometryNodeMeshIcoSphere"); ico.inputs["Radius"].default_value = 0.2; ico.inputs["Subdivisions"].default_value = 2
    inst = N.new("GeometryNodeInstanceOnPoints")
    L.new(grid.outputs["Mesh"], pts.inputs["Mesh"])
    L.new(pts.outputs["Points"], inst.inputs["Points"])
    L.new(ico.outputs["Mesh"], inst.inputs["Instance"])
    last = inst.outputs["Instances"]
    if realize:
        rz = N.new("GeometryNodeRealizeInstances")
        L.new(last, rz.inputs["Geometry"]); last = rz.outputs["Geometry"]
    L.new(last, out.inputs["Geometry"])
    return ng


def host(name, ng, x):
    me = bpy.data.meshes.new(name); ob = bpy.data.objects.new(name, me); ob.location.x = x
    bpy.context.scene.collection.objects.link(ob)
    m = ob.modifiers.new("GN", "NODES"); m.node_group = ng
    return ob

a = host("instanced", group(False), 0)
b = host("realized", group(True), 20)
dg = bpy.context.evaluated_depsgraph_get()
ea, eb = a.evaluated_get(dg), b.evaluated_get(dg)
E.fact("with unrealised instances, the evaluated object's mesh is empty: the 100 icospheres are not in evaluated.data",
       instanced_mesh_verts=len(ea.data.vertices), realized_mesh_verts=len(eb.data.vertices), ico_verts=42)
nm = bpy.data.meshes.new_from_object(ea)
E.fact("new_from_object on the instancing object also gives an empty mesh (instances are dropped)", verts=len(nm.vertices))

# reading instances through depsgraph.object_instances
t = time.perf_counter()
inst = [(i.object.name, i.is_instance, i.parent.name if i.parent else None, tuple(round(x, 3) for x in i.matrix_world.translation))
        for i in dg.object_instances if i.is_instance and i.parent and i.parent.original == a]
dt = time.perf_counter() - t
types = {}
for i in dg.object_instances:
    if i.is_instance and i.parent and i.parent.original == a:
        types[i.object.type] = types.get(i.object.type, 0) + 1
        data_verts = len(i.object.data.vertices) if i.object.type == "MESH" else None
E.fact("depsgraph.object_instances yields one item per instance (is_instance True, parent = the instancer); the instanced object is a MESH of 42 verts, matrix_world places it",
       count=len(inst), types=types, first=inst[0] if inst else None, instanced_mesh_verts=data_verts, ms=round(dt * 1000, 2))
kept_refs, kept_copies = [], []
for i in dg.object_instances:
    if i.is_instance and i.parent and i.parent.original == a:
        kept_refs.append(i.matrix_world); kept_copies.append(i.matrix_world.copy())
try:
    distinct_refs = len({tuple(round(x, 3) for x in m.translation) for m in kept_refs}); ref_err = None
except Exception as e:
    distinct_refs, ref_err = None, f"{type(e).__name__}: {e}"
distinct_copies = len({tuple(round(x, 3) for x in m.translation) for m in kept_copies})
E.fact(f"matrices kept from the object_instances loop: {distinct_copies} distinct positions when copied (.copy()), {distinct_refs} when the matrix_world objects themselves were kept",
       copies=distinct_copies, refs=distinct_refs, error=ref_err)

# geometry set API (4.3+): evaluated_geometry
has_gs = hasattr(ea, "evaluated_geometry")
if has_gs:
    gs = ea.evaluated_geometry()
    ref = gs.instance_references() if hasattr(gs, "instance_references") else None
    E.fact("evaluated_object.evaluated_geometry() returns a GeometrySet exposing instances_pointcloud() and instance_references()",
           members=[m for m in dir(gs) if not m.startswith("_")],
           mesh=gs.mesh is not None and len(gs.mesh.vertices) if gs.mesh else None,
           instances_pointcloud=len(gs.instances_pointcloud().points) if gs.instances_pointcloud() else None,
           references=[type(r).__name__ for r in ref] if ref is not None else None)
else:
    E.fact("this build has no Object.evaluated_geometry()", has=False)

E.fact("with Realize Instances, the evaluated mesh holds all copies: 100 x 42 verts", verts=len(eb.data.vertices), expected=4200)
# applying the modifier with instances
with bpy.context.temp_override(object=a, active_object=a):
    try:
        r = list(bpy.ops.object.modifier_apply(modifier="GN")); err = None
    except Exception as e:
        r, err = None, f"{type(e).__name__}: {str(e).strip()}"
E.fact("modifier_apply on a nodes modifier whose output is instances", result=r, error=err, verts_after=len(a.data.vertices),
       objects=len(bpy.data.objects))
E.save()
