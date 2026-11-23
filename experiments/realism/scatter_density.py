"""C-004, scattering by painted density (4 of the 17 realistic scenes painted where things grow): a vertex group's
weights driving Geometry Nodes' Distribute Points on Faces, random and Poisson-disk, read back as counts per region,
and instances placed on the points."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy
from mathutils import kdtree
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene
bpy.ops.mesh.primitive_grid_add(x_subdivisions=50, y_subdivisions=50, size=10)
ground = bpy.context.object
vg = ground.vertex_groups.new(name="density")
for v in ground.data.vertices:
    vg.add([v.index], 1.0 if v.co.x < 0 else 0.25, "REPLACE")   # left half 1.0, right half 0.25


def tree(method, instance=False):
    ng = bpy.data.node_groups.new(f"Scatter_{method}", "GeometryNodeTree")
    ng.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N, L = ng.nodes, ng.links
    gi, go = N.new("NodeGroupInput"), N.new("NodeGroupOutput")
    dist = N.new("GeometryNodeDistributePointsOnFaces")
    dist.distribute_method = method
    w = N.new("GeometryNodeInputNamedAttribute")
    w.data_type = "FLOAT"
    w.inputs["Name"].default_value = "density"
    L.new(gi.outputs["Geometry"], dist.inputs["Mesh"])
    if method == "RANDOM":
        mul = N.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        mul.inputs[1].default_value = 20.0                  # points per square metre where the weight is 1
        L.new(w.outputs["Attribute"], mul.inputs[0])
        L.new(mul.outputs[0], dist.inputs["Density"])
    else:
        dist.inputs["Distance Min"].default_value = 0.15
        dist.inputs["Density Max"].default_value = 20.0
        L.new(w.outputs["Attribute"], dist.inputs["Density Factor"])
    if instance:
        ico = N.new("GeometryNodeMeshIcoSphere")
        ico.inputs["Radius"].default_value = 0.05
        inst = N.new("GeometryNodeInstanceOnPoints")
        L.new(dist.outputs["Points"], inst.inputs["Points"])
        L.new(ico.outputs["Mesh"], inst.inputs["Instance"])
        L.new(inst.outputs["Instances"], go.inputs["Geometry"])
    else:
        pv = N.new("GeometryNodePointsToVertices")
        L.new(dist.outputs["Points"], pv.inputs["Points"])
        L.new(pv.outputs["Mesh"], go.inputs["Geometry"])
    return ng


rows = {}
for method in ("RANDOM", "POISSON"):
    mod = ground.modifiers.new("Scatter", "NODES")
    mod.node_group = tree(method)
    bpy.context.view_layer.update()
    me = ground.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
    xs = [v.co for v in me.vertices]
    left = sum(1 for c in xs if c.x < 0)
    right = len(xs) - left
    kd = kdtree.KDTree(len(xs))
    for i, c in enumerate(xs):
        kd.insert(c, i)
    kd.balance()
    nearest = min(kd.find_n(c, 2)[1][2] for c in xs) if len(xs) > 1 else None
    rows[method] = dict(points=len(xs), left_weight_1=left, right_weight_0_25=right,
                        left_over_right=round(left / right, 3) if right else None,
                        closest_pair_m=round(nearest, 4) if nearest is not None else None)
    ground.modifiers.remove(mod)
E.fact("points from Distribute Points on Faces on a 10 x 10 m grid whose vertex group 'density' is 1.0 on the left "
       "half and 0.25 on the right: RANDOM with Density = 20 x weight, POISSON with Density Max 20, Distance Min "
       "0.15 m and Density Factor = weight (the vertex group read with a Named Attribute node)", rows=rows)

mod = ground.modifiers.new("Scatter", "NODES")
mod.node_group = tree("RANDOM", instance=True)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
inst = sum(1 for i in dg.object_instances if i.is_instance and i.parent and i.parent.original == ground)
E.fact("Instance on Points with an ico sphere on the RANDOM points: instances the depsgraph lists for the grid",
       instances=inst, points=rows["RANDOM"]["points"])
E.save()
