"""What throws an unbaked cloth cache away, and does a bake protect it?

Each case: build the scene, step frames 1..40 (memory cache, not baked), record the cloth at frame 30, go back to frame 10,
make one change there, then go to frame 30 again and compare. A kept cache gives the same points; a lost one does not,
and its info line says how many frames are left."""
import re
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy
import numpy as np
import exp
E = exp.Experiment(__file__)
N = 40


def build():
    exp.empty()
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, N
    bpy.ops.object.camera_add(location=(0, -3, 1))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=(0, 0, 0.5))
    ball = bpy.context.object
    ball.modifiers.new("Collision", "COLLISION")
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=20, y_subdivisions=20, size=1.0, location=(0, 0, 1.0))
    g = bpy.context.object
    g.name = "cloth"
    vg = g.vertex_groups.new(name="pin")
    vg.add([v.index for v in g.data.vertices if v.co.y > 0.5 - 1e-6], 1.0, "REPLACE")
    cm = g.modifiers.new("Cloth", "CLOTH")
    cm.settings.vertex_group_mass = "pin"
    cm.point_cache.frame_start, cm.point_cache.frame_end = 1, N
    return g, cm


def coords(o):
    dg = bpy.context.evaluated_depsgraph_get()
    e = o.evaluated_get(dg)
    me = e.to_mesh()
    a = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", a)
    n = len(me.vertices)
    e.to_mesh_clear()
    return a.reshape(-1, 3), n


def mat(g):
    m = bpy.data.materials.new("m")
    m.use_nodes = True
    g.data.materials.append(m)


def mat_color(g):
    m = g.active_material
    bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (1, 0, 0, 1)


CASES = {
    "nothing (control)": lambda g, cm: None,
    "frame_set to the frame already current": lambda g, cm: bpy.context.scene.frame_set(bpy.context.scene.frame_current),
    "view_layer.update()": lambda g, cm: bpy.context.view_layer.update(),
    "select_set on the cloth": lambda g, cm: g.select_set(True),
    "rename the cloth object": lambda g, cm: setattr(g, "name", "cloth2"),
    "cloth quality set to its own value": lambda g, cm: setattr(cm.settings, "quality", cm.settings.quality),
    "cloth mass set to its own value": lambda g, cm: setattr(cm.settings, "mass", cm.settings.mass),
    "cloth object's hide_render set to its own value": lambda g, cm: setattr(g, "hide_render", g.hide_render),
    "cloth object's hide_viewport toggled off and on": lambda g, cm: (setattr(g, "hide_viewport", True), setattr(g, "hide_viewport", False)),
    "camera (unrelated object) location set to its own value": lambda g, cm: setattr(bpy.data.objects["Camera"], "location", bpy.data.objects["Camera"].location.copy()),
    "collider's location set to its own value": lambda g, cm: setattr(bpy.data.objects["Sphere"], "location", bpy.data.objects["Sphere"].location.copy()),
    "scene render resolution changed": lambda g, cm: setattr(bpy.context.scene.render, "resolution_x", 640),
    "material added to the cloth": lambda g, cm: mat(g),
    "Subdivision modifier added after the cloth": lambda g, cm: g.modifiers.new("Sub", "SUBSURF"),
    "Subdivision added after the cloth, levels 0 and render levels 0": lambda g, cm: (lambda m: (setattr(m, "levels", 0), setattr(m, "render_levels", 0)))(g.modifiers.new("Sub", "SUBSURF")),
    "a vertex group weight edited": lambda g, cm: g.vertex_groups["pin"].add([0], 1.0, "REPLACE"),
    "a new object added to the scene": lambda g, cm: bpy.ops.object.empty_add(),
}

rows = []


def nframes(info):
    m = re.match(r"(\d+) frames", info)
    return int(m.group(1)) if m else None


def run_case(name, touch, baked, before=None):
    g, cm = build()
    sc = bpy.context.scene
    if before:
        before(g)
    for f in range(1, N + 1):
        sc.frame_set(f)
    if baked:
        with bpy.context.temp_override(point_cache=cm.point_cache):
            bpy.ops.ptcache.bake_from_cache()
    sc.frame_set(30)
    A30, nA = coords(g)
    sc.frame_set(10)
    touch(g, cm)
    sc.frame_set(10)  # evaluate the change at frame 10
    info_at_10 = cm.point_cache.info
    sc.frame_set(30)
    B30, nB = coords(g)
    info_after = cm.point_cache.info
    d = float(np.abs(A30 - B30).max()) if nA == nB else None
    left = nframes(info_after)
    kept = (d == 0.0) if d is not None else (left == N)  # point count changed (Subdivision): judge by frames left
    rows.append(dict(case=name, baked=baked, kept=kept, max_diff_at_30_m=d, points=(nA, nB),
                     info_after_change=info_at_10, info_at_30=info_after, frames_left=left))
    print("ROW", baked, name, kept, d, "|", info_at_10, "|", info_after, flush=True)


for baked in (False, True):
    for name, touch in CASES.items():
        run_case(name, touch, baked)
    run_case("material's Base Color edited (material made before the simulation)", lambda g, cm: mat_color(g),
             baked, before=mat)

lost_unbaked = [r["case"] for r in rows if not r["baked"] and not r["kept"]]
kept_unbaked = [r["case"] for r in rows if not r["baked"] and r["kept"]]
lost_baked = [r["case"] for r in rows if r["baked"] and not r["kept"]]
E.fact("an unbaked (memory) cloth cache is thrown away by these changes", cases=lost_unbaked)
E.fact("an unbaked cloth cache survives these", cases=kept_unbaked)
E.fact("a baked cloth cache (bake_from_cache) survives every change tried except these", cases=lost_baked)
E.save(rows=rows, frames=N)
