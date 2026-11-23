"""A geometry-nodes simulation zone built from Python and run headless: does its state carry from frame to frame, what
does a frame jump do, what does Delta Time read, and which operator bakes it in background mode."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy
import exp
E = exp.Experiment(__file__)
N = 30


def build():
    exp.empty()
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, N
    bpy.ops.mesh.primitive_cube_add(size=0.2, location=(0, 0, 0))
    ob = bpy.context.object
    ng = bpy.data.node_groups.new("fall", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    gi = ng.nodes.new("NodeGroupInput")
    go = ng.nodes.new("NodeGroupOutput")
    sin = ng.nodes.new("GeometryNodeSimulationInput")
    sout = ng.nodes.new("GeometryNodeSimulationOutput")
    paired = sin.pair_with_output(sout)
    setp = ng.nodes.new("GeometryNodeSetPosition")
    comb = ng.nodes.new("ShaderNodeCombineXYZ")
    mul = ng.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = -1.0            # 1 m per second downward
    L = ng.links
    L.new(gi.outputs["Geometry"], sin.inputs["Geometry"])
    L.new(sin.outputs["Geometry"], setp.inputs["Geometry"])
    L.new(sin.outputs["Delta Time"], mul.inputs[0])
    L.new(mul.outputs[0], comb.inputs["Z"])
    L.new(comb.outputs["Vector"], setp.inputs["Offset"])
    L.new(setp.outputs["Geometry"], sout.inputs["Geometry"])
    L.new(sout.outputs["Geometry"], go.inputs["Geometry"])
    mod = ob.modifiers.new("GN", "NODES")
    mod.node_group = ng
    return sc, ob, mod, paired


def low(ob):
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me = ev.to_mesh()
    z = min(v.co.z for v in me.vertices)
    ev.to_mesh_clear()
    return round(z, 4)


sc, ob, mod, paired = build()
z = {}
for f in range(1, N + 1):
    sc.frame_set(f)
    if f in (1, 2, 13, 25, 30):
        z[f] = low(ob)
fps = sc.render.fps / sc.render.fps_base
E.fact("a simulation zone made from Python (pair_with_output) carries its state across frames when stepped: "
       "a cube moved by -Delta Time each frame (1 m/s) falls 1/fps a frame", lowest_z_by_frame=z, fps=fps,
       expected_drop_by_30_m=round(29 / fps, 4), paired=paired)

sc.frame_set(15)
back = low(ob)
E.fact("after stepping, going back to an earlier frame reads the zone's cache", z_at_15_after_stepping=back)

sc, ob, mod, paired = build()
sc.frame_set(1)
z1 = low(ob)
sc.frame_set(N)
zj = low(ob)
E.fact("jumping from frame 1 straight to frame 30 with nothing cached: what the zone outputs", z_at_1=z1, z_after_jump=zj)

# baking headless
sc, ob, mod, paired = build()
res = {}
for name, call in (("object.simulation_nodes_cache_bake(selected=False), no override",
                    lambda: bpy.ops.object.simulation_nodes_cache_bake(selected=False)),
                   ("object.simulation_nodes_cache_bake(selected=True), temp_override(selected_objects=[ob], active_object=ob)",
                    lambda: _ov(lambda: bpy.ops.object.simulation_nodes_cache_bake(selected=True)))):
    pass


def _ov(fn):
    with bpy.context.temp_override(active_object=ob, object=ob, selected_objects=[ob], selected_editable_objects=[ob]):
        return fn()


attempts = []
for label, fn in (("simulation_nodes_cache_bake(selected=False)", lambda: bpy.ops.object.simulation_nodes_cache_bake(selected=False)),
                  ("simulation_nodes_cache_bake(selected=True) in temp_override", lambda: _ov(lambda: bpy.ops.object.simulation_nodes_cache_bake(selected=True))),
                  ("geometry_node_bake_single(session_uid, modifier_name, bake_id)",
                   lambda: bpy.ops.object.geometry_node_bake_single(session_uid=ob.session_uid, modifier_name=mod.name,
                                                                     bake_id=mod.bakes[0].bake_id))):
    try:
        r = list(fn())
        err = None
    except Exception as e:
        r, err = None, str(e).strip().splitlines()[0]
    attempts.append(dict(call=label, result=r, error=err, bakes=len(mod.bakes),
                         bake_target=mod.bakes[0].bake_target if len(mod.bakes) else None))
    print("BAKE", attempts[-1], flush=True)
sc.frame_set(25)
z25 = low(ob)
sc.frame_set(5)
z5 = low(ob)
E.fact("baking a simulation zone in background mode: which calls finish, and the baked result read out of order",
       attempts=attempts, z_at_25=z25, z_at_5=z5, bake_directory=mod.bake_directory, blend_saved=bool(bpy.data.filepath))
E.save()
