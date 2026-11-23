"""The Mesh Boolean node vs the Boolean modifier: enum names and defaults differ; does the node's Manifold solver give the same result?"""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy, bmesh
import exp
E = exp.Experiment(__file__)

ng = bpy.data.node_groups.new("Cut", "GeometryNodeTree")
ng.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
ng.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
N, L = ng.nodes, ng.links
gi, go = N.new("NodeGroupInput"), N.new("NodeGroupOutput")
b = N.new("GeometryNodeMeshBoolean")
mod_enum = [e.identifier for e in bpy.types.BooleanModifier.bl_rna.properties["solver"].enum_items]
E.fact("node and modifier use different identifiers and defaults for the same solvers",
       node_solvers=[e.identifier for e in b.bl_rna.properties["solver"].enum_items], node_default=b.solver, node_operation=b.operation,
       modifier_solvers=mod_enum, modifier_default=bpy.types.BooleanModifier.bl_rna.properties["solver"].default,
       modifier_operation_default=bpy.types.BooleanModifier.bl_rna.properties["operation"].default)
try:
    b.solver = "FAST"; r = "accepted"
except Exception as e:
    r = f"{type(e).__name__}: {str(e)[:160]}"
E.fact("setting the node's solver to 'FAST' (the modifier's name) raises", error=r)
b.operation = "DIFFERENCE"; b.solver = "MANIFOLD"
cyl = N.new("GeometryNodeMeshCylinder"); cyl.inputs["Radius"].default_value = 0.5; cyl.inputs["Depth"].default_value = 4
L.new(gi.outputs[0], b.inputs["Mesh 1"]); L.new(cyl.outputs["Mesh"], b.inputs["Mesh 2"]); L.new(b.outputs["Mesh"], go.inputs[0])
bpy.ops.mesh.primitive_cube_add()
ob = bpy.context.object
m = ob.modifiers.new("GN", "NODES"); m.node_group = ng
out = {}
for solver in ("FLOAT", "EXACT", "MANIFOLD"):
    b.solver = solver
    dg = bpy.context.evaluated_depsgraph_get(); me = ob.evaluated_get(dg).data
    bm = bmesh.new(); bm.from_mesh(me)
    out[solver] = dict(verts=len(bm.verts), non_manifold=sum(1 for e in bm.edges if not e.is_manifold), volume=round(bm.calc_volume(), 4),
                       genus=(2 - (len(bm.verts) - len(bm.edges) + len(bm.faces))) / 2)
    bm.free()
E.fact("a cube minus a cylinder (32 sides, r 0.5) with each node solver: one through-hole (genus 1), manifold, same volume", by_solver=out)
E.save()
