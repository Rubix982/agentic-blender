# Scatter: a geometry-nodes modifier on a 2 x 2 m plane that scatters exactly 200 points with a 5 cm cube on each.
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from _common import OUT
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_plane_add(size=2)
plane = bpy.context.active_object
ng = bpy.data.node_groups.new("Scatter", "GeometryNodeTree")
ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
N = ng.nodes; L = ng.links
gin = N.new("NodeGroupInput"); gout = N.new("NodeGroupOutput")
pts = N.new("GeometryNodePoints"); pts.inputs["Count"].default_value = 200
rnd = N.new("FunctionNodeRandomValue"); rnd.data_type = "FLOAT_VECTOR"
rnd.inputs["Min"].default_value = (-1, -1, 0); rnd.inputs["Max"].default_value = (1, 1, 0)
cube = N.new("GeometryNodeMeshCube"); cube.inputs["Size"].default_value = (0.05, 0.05, 0.05)
inst = N.new("GeometryNodeInstanceOnPoints")
L.new(rnd.outputs["Value"], pts.inputs["Position"])
L.new(pts.outputs["Points"], inst.inputs["Points"]); L.new(cube.outputs["Mesh"], inst.inputs["Instance"])
L.new(inst.outputs["Instances"], gout.inputs["Geometry"])
mod = plane.modifiers.new("Scatter", "NODES"); mod.node_group = ng
bpy.ops.wm.save_as_mainfile(filepath=OUT)
