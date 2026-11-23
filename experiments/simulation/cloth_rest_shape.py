"""Does cloth's rest_shape_key set the springs' rest lengths? Against shrink_min and Dynamic Mesh.

A 1 m grid (21 x 21) with no gravity, simulated 60 frames; its width at the end tells which rest it used.
Shape keys: Basis (1 m), "half" (0.5x), and in some cases a third key "double" (2x) after it, to catch the key being
read by the wrong index."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy
import numpy as np
import exp
E = exp.Experiment(__file__)
N = 60


def run(name, setup, third_key=False, animate_half=False):
    exp.empty()
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, N
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=20, y_subdivisions=20, size=1.0)
    o = bpy.context.object
    o.shape_key_add(name="Basis", from_mix=False)
    half = o.shape_key_add(name="half", from_mix=False)
    for i, v in enumerate(o.data.vertices):
        half.data[i].co = v.co * 0.5
    half.value = 0.0
    keys = {"half": half}
    if third_key:
        dbl = o.shape_key_add(name="double", from_mix=False)
        for i, v in enumerate(o.data.vertices):
            dbl.data[i].co = v.co * 2.0
        dbl.value = 0.0
        keys["double"] = dbl
    if animate_half:
        half.value = 0.0
        half.keyframe_insert("value", frame=1)
        half.value = 1.0
        half.keyframe_insert("value", frame=30)
    cm = o.modifiers.new("cloth", "CLOTH")
    cm.settings.effector_weights.gravity = 0.0
    cm.point_cache.frame_start, cm.point_cache.frame_end = 1, N
    setup(cm, keys)
    for f in range(1, N + 1):
        sc.frame_set(f)
    e = o.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me = e.to_mesh()
    P = np.array([v.co[:] for v in me.vertices])
    e.to_mesh_clear()
    width = round(float(P[:, 0].max() - P[:, 0].min()), 3)
    rk = cm.settings.rest_shape_key
    print("RK", name, width, rk.name if rk else None, flush=True)
    return dict(case=name, width_m=width, rest_shape_key=rk.name if rk else None)


rows = [
    run("control: nothing set", lambda cm, k: None),
    run("shrink_min 0.5", lambda cm, k: setattr(cm.settings, "shrink_min", 0.5)),
    run("rest_shape_key = half", lambda cm, k: setattr(cm.settings, "rest_shape_key", k["half"])),
    run("rest_shape_key = half, a third key 'double' after it", lambda cm, k: setattr(cm.settings, "rest_shape_key", k["half"]), third_key=True),
    run("rest_shape_key = double (the third key)", lambda cm, k: setattr(cm.settings, "rest_shape_key", k["double"]), third_key=True),
    run("rest_shape_key = half + use_dynamic_mesh", lambda cm, k: (setattr(cm.settings, "rest_shape_key", k["half"]), setattr(cm.settings, "use_dynamic_mesh", True))),
    run("use_dynamic_mesh, 'half' keyed 0 -> 1 over frames 1-30", lambda cm, k: setattr(cm.settings, "use_dynamic_mesh", True), animate_half=True),
    run("no dynamic mesh, 'half' keyed 0 -> 1 over frames 1-30", lambda cm, k: None, animate_half=True),
]
by = {r["case"]: r["width_m"] for r in rows}
E.fact("shrink_min 0.5 halves the cloth's rest: a 1 m sheet with no gravity ends 0.5 m wide",
       width_m=by["shrink_min 0.5"], control_m=by["control: nothing set"])
E.fact("rest_shape_key pointing at a half-size key does not change the rest: the sheet stays 1 m wide, with or without a third key or Dynamic Mesh (and a mesh with keys reports Basis as its rest key by default)",
       width_m=by["rest_shape_key = half"],
       with_third_key_m=by["rest_shape_key = half, a third key 'double' after it"],
       rest_key_double_m=by["rest_shape_key = double (the third key)"],
       with_dynamic_mesh_m=by["rest_shape_key = half + use_dynamic_mesh"])
E.fact("with use_dynamic_mesh the rest follows the shape-key mix as it is animated (the stack above the cloth); "
       "without it the animated key does not change the rest",
       dynamic_m=by["use_dynamic_mesh, 'half' keyed 0 -> 1 over frames 1-30"],
       not_dynamic_m=by["no dynamic mesh, 'half' keyed 0 -> 1 over frames 1-30"])
E.save(rows=rows)
