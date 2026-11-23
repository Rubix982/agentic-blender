"""The Curve to Mesh geometry node in 4.5: what it makes from a classic Curve object with no profile, a circle profile
with and without Fill Caps, a closed path, a line profile, and the Scale input and point radius; whether the result is
manifold and which way its normals face (signed volume > 0 = outward).

The path is a 4-point open Bezier curve (resolution_u 12, 37 evaluated points) carried in through a geometry-nodes
modifier on the Curve object; the profile is a Curve Circle (8 points, radius 0.1 m)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bmesh  # noqa: E402
import bpy  # noqa: E402
import numpy as np  # noqa: E402

import exp  # noqa: E402

E = exp.Experiment(__file__)
scene = bpy.context.scene

cu = bpy.data.curves.new("path", "CURVE")
cu.dimensions = "3D"
sp = cu.splines.new("BEZIER")
sp.bezier_points.add(3)
for p, co in zip(sp.bezier_points, ((0, 0, 0), (1, 0.5, 0), (2, -0.5, 0.3), (3, 0, 0))):
    p.co = co
    p.handle_left_type = p.handle_right_type = "AUTO"
ob = bpy.data.objects.new("path", cu)
scene.collection.objects.link(ob)

ng = bpy.data.node_groups.new("ToMesh", "GeometryNodeTree")
ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
gi = ng.nodes.new("NodeGroupInput")
go = ng.nodes.new("NodeGroupOutput")
c2m = ng.nodes.new("GeometryNodeCurveToMesh")
circle = ng.nodes.new("GeometryNodeCurvePrimitiveCircle")
circle.inputs["Resolution"].default_value = 8
circle.inputs["Radius"].default_value = 0.1
line = ng.nodes.new("GeometryNodeCurvePrimitiveLine")
line.inputs["Start"].default_value = (-0.1, 0, 0)
line.inputs["End"].default_value = (0.1, 0, 0)
radius = ng.nodes.new("GeometryNodeInputRadius")
ng.links.new(gi.outputs[0], c2m.inputs["Curve"])
ng.links.new(c2m.outputs["Mesh"], go.inputs[0])
md = ob.modifiers.new("GN", "NODES")
md.node_group = ng
new_node = dict(inputs={s.name: (s.default_value if hasattr(s, "default_value") else None) for s in c2m.inputs},
                outputs=[s.name for s in c2m.outputs])


def link_profile(kind):
    for l in list(c2m.inputs["Profile Curve"].links):
        ng.links.remove(l)
    if kind == "circle":
        ng.links.new(circle.outputs["Curve"], c2m.inputs["Profile Curve"])
    elif kind == "line":
        ng.links.new(line.outputs["Curve"], c2m.inputs["Profile Curve"])


def measure():
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bm = bmesh.new()
    bm.from_mesh(me)
    nonman = sum(1 for e in bm.edges if not e.is_manifold)
    boundary = sum(1 for e in bm.edges if e.is_boundary)
    vol = bm.calc_volume(signed=True) if len(bm.faces) else 0.0
    ngons = sum(1 for f in bm.faces if len(f.verts) > 4)
    co = np.array([v.co[:] for v in bm.verts]) if len(bm.verts) else np.zeros((0, 3))
    out = dict(vertices=len(bm.verts), edges=len(bm.edges), faces=len(bm.faces), non_manifold_edges=nonman,
               boundary_edges=boundary, ngons=ngons, signed_volume=round(vol, 5),
               manifold=bool(len(bm.faces)) and nonman == 0)
    if len(co):
        out["max_abs_z"] = round(float(np.abs(co[:, 2]).max()), 4)
    bm.free()
    bpy.data.meshes.remove(me)
    return out


rows = {}
link_profile(None)
rows["no profile"] = measure()
link_profile("circle")
rows["circle profile"] = measure()
c2m.inputs["Fill Caps"].default_value = True
rows["circle profile, Fill Caps"] = measure()
sp.use_cyclic_u = True
rows["closed path, circle, Fill Caps"] = measure()
c2m.inputs["Fill Caps"].default_value = False
rows["closed path, circle"] = measure()
sp.use_cyclic_u = False
link_profile("line")
rows["line profile"] = measure()
E.fact("Curve to Mesh from a 37-point open path: with no profile it gives a polyline (edges, no faces); with an "
       "8-point circle profile an open tube, 37 x 8 points, not manifold; Fill Caps adds two 8-sided faces and makes it "
       "manifold with outward normals (positive signed volume); a closed path needs no caps; a line profile makes a "
       "ribbon", new_node=new_node, **rows)

# size: the Scale input and the curve's point radius
link_profile("circle")
c2m.inputs["Fill Caps"].default_value = True
def tube_radius():
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    co = np.zeros(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    bpy.data.meshes.remove(me)
    ring = co[:8]                            # the first ring sits at the path's first point (0, 0, 0)
    return round(float(np.linalg.norm(ring, axis=1).max()), 4)


sizes = {"default": tube_radius()}
c2m.inputs["Scale"].default_value = 2.0
sizes["Scale 2"] = tube_radius()
c2m.inputs["Scale"].default_value = 1.0
for p in sp.bezier_points:
    p.radius = 3.0
sizes["point radius 3, Scale 1"] = tube_radius()
ng.links.new(radius.outputs["Radius"], c2m.inputs["Scale"])
sizes["point radius 3, Radius -> Scale"] = tube_radius()
E.fact("The tube's size: profile radius 0.1 x the Scale input (default 1.0). The curve's own point radius is not "
       "applied unless it is wired into Scale (a Radius node -> Scale)", **sizes)
E.save(path_points=37, profile_points=8)
