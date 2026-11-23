"""Cloth pins: is a pinned point fixed or sprung, and what does pin stiffness change?

1. A 1 m sheet (21 x 21 points), every point in the pin group at one weight w, gravity only, 48 frames: how far does it
   sag, for w in 1.0 / 0.999 / 0.99 / 0.9 / 0.5 and pin stiffness 1 / 10 / 50?
2. The same sheet, only its back row pinned (w = 1, or w = 0.9), the object keyframed 0.5 m along x over frames 1-12:
   do the pinned points follow the animation, and by how much do they lag?
4. Pins against sewing springs: two 0.5 m squares 20 cm apart joined by loose edges (sewing springs, max force 200,
   no gravity); one square pinned at weight 1, the other everywhere at weight w: how far is the second pulled off its pins?
3. The pin weight changed mid-simulation by a Vertex Weight Mix modifier above the cloth (its strength keyframed 1 -> 0
   at frame 20): does the cloth read the new weights while it runs?"""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy
import numpy as np
import exp
E = exp.Experiment(__file__)
N = 48


def sheet(weight=None, back_row=None):
    exp.empty()
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, N
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=20, y_subdivisions=20, size=1.0, location=(0, 0, 1.0))
    g = bpy.context.object
    vg = g.vertex_groups.new(name="pin")
    if weight is not None:
        vg.add(list(range(len(g.data.vertices))), weight, "REPLACE")
    if back_row is not None:
        vg.add([v.index for v in g.data.vertices if v.co.y > 0.5 - 1e-6], back_row, "REPLACE")
    cm = g.modifiers.new("Cloth", "CLOTH")
    cm.settings.vertex_group_mass = "pin"
    cm.point_cache.frame_start, cm.point_cache.frame_end = 1, N
    return g, cm


def world(o):
    dg = bpy.context.evaluated_depsgraph_get()
    e = o.evaluated_get(dg)
    me = e.to_mesh()
    a = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", a)
    e.to_mesh_clear()
    a = a.reshape(-1, 3)
    M = np.array(e.matrix_world)
    return a @ M[:3, :3].T + M[:3, 3]


# 1. uniform pin weight, sag
sag = []
for stiff in (1.0, 10.0, 50.0):
    for w in (1.0, 0.999, 0.99, 0.9, 0.5):
        g, cm = sheet(weight=w)
        cm.settings.pin_stiffness = stiff
        sc = bpy.context.scene
        sc.frame_set(1)
        P0 = world(g)
        for f in range(2, N + 1):
            sc.frame_set(f)
        P = world(g)
        drop = P0[:, 2] - P[:, 2]
        sag.append(dict(pin_stiffness=stiff, weight=w, mean_drop_m=round(float(drop.mean()), 4),
                        max_drop_m=round(float(drop.max()), 4)))
        print("SAG", stiff, w, round(float(drop.mean()), 4), flush=True)


def get(stiff, w):
    return next(r["mean_drop_m"] for r in sag if r["pin_stiffness"] == stiff and r["weight"] == w)


E.fact("a point pinned at weight 1.0 is held exactly: the sheet does not drop at all, at any pin stiffness",
       drop_m={s: get(s, 1.0) for s in (1.0, 10.0, 50.0)})
E.fact("below weight 1.0 a pin is a spring: at the default stiffness (1) a sheet pinned everywhere at 0.99 sags, "
       "and stiffness 50 holds it much closer",
       drop_w099_m={s: get(s, 0.99) for s in (1.0, 10.0, 50.0)},
       drop_w0999_m={s: get(s, 0.999) for s in (1.0, 10.0, 50.0)},
       drop_w05_m={s: get(s, 0.5) for s in (1.0, 10.0, 50.0)})

# 2. animated object, back row pinned
follow = []
for w in (1.0, 0.9):
    for stiff in (1.0, 50.0):
        g, cm = sheet(back_row=w)
        cm.settings.pin_stiffness = stiff
        back = [v.index for v in g.data.vertices if v.co.y > 0.5 - 1e-6]
        g.location = (0, 0, 1)
        g.keyframe_insert("location", frame=1)
        g.location = (0.5, 0, 1)
        g.keyframe_insert("location", frame=12)
        sc = bpy.context.scene
        sc.frame_set(1)
        R = world(g)[back]
        lag = []
        for f in range(2, N + 1):
            sc.frame_set(f)
            if f in (6, 12, 24, 48):
                P = world(g)[back]
                target_x = g.matrix_world.translation.x
                lag.append((f, round(float(np.abs(P[:, 0] - (R[:, 0] - 0 + target_x)).max()), 4)))
        follow.append(dict(weight=w, pin_stiffness=stiff, max_x_lag_m_by_frame=lag))
        print("FOLLOW", w, stiff, lag, flush=True)
E.fact("pinned points (weight 1) follow the object's animation exactly; at weight 0.9 they lag behind it, "
       "less at pin stiffness 50", rows=follow)

# 3. pin weight changed mid-run by a Vertex Weight Mix modifier above the cloth
g, cm = sheet(back_row=1.0)
back = [v.index for v in g.data.vertices if v.co.y > 0.5 - 1e-6]
mix = g.modifiers.new("release", "VERTEX_WEIGHT_MIX")
mix.vertex_group_a = "pin"
mix.default_weight_b = 0.0
mix.mix_mode = "SET"
mix.mix_set = "ALL"
mix.mask_constant = 0.0          # 0: no effect, the pin stays
mix.keyframe_insert("mask_constant", frame=19)
mix.mask_constant = 1.0          # 1: weight a replaced by b (0): the pin is let go
mix.keyframe_insert("mask_constant", frame=20)
# the cloth must come after the weight modifier in the stack
bpy.context.view_layer.objects.active = g
with bpy.context.temp_override(object=g):
    bpy.ops.object.modifier_move_to_index(modifier="release", index=0)
order = [m.type for m in g.modifiers]
sc = bpy.context.scene
sc.frame_set(1)
R = world(g)[back]
zs = {}
for f in range(2, N + 1):
    sc.frame_set(f)
    if f in (10, 19, 21, 30, 48):
        zs[f] = round(float((R[:, 2] - world(g)[back][:, 2]).max()), 4)
E.fact("the cloth reads the pin weights every frame from the modifiers above it: a pin let go by a keyframed "
       "Vertex Weight Mix at frame 20 holds before and drops after", stack=order, back_row_drop_m_by_frame=zs)

# 4. pins against sewing springs
def sewn(w, stiff):
    exp.empty()
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, N
    verts, faces, edges, idx = [], [], [], {}
    n = 11
    for side, x0 in (("A", -0.6), ("B", 0.1)):
        for i in range(n):
            for j in range(n):
                idx[(side, i, j)] = len(verts)
                verts.append((x0 + 0.5 * i / (n - 1), 0.5 * j / (n - 1) - 0.25, 1.0))
        for i in range(n - 1):
            for j in range(n - 1):
                faces.append((idx[(side, i, j)], idx[(side, i + 1, j)], idx[(side, i + 1, j + 1)], idx[(side, i, j + 1)]))
    for j in range(n):
        edges.append((idx[("A", n - 1, j)], idx[("B", 0, j)]))   # the seam: loose edges, no faces
    me = bpy.data.meshes.new("sewn")
    me.from_pydata(verts, edges, faces)
    o = bpy.data.objects.new("sewn", me)
    sc.collection.objects.link(o)
    vg = o.vertex_groups.new(name="pin")
    vg.add([idx[("A", i, j)] for i in range(n) for j in range(n)], w, "REPLACE")
    vg.add([idx[("B", i, j)] for i in range(n) for j in range(n)], 1.0, "REPLACE")
    cm = o.modifiers.new("Cloth", "CLOTH")
    st = cm.settings
    st.vertex_group_mass = "pin"
    st.pin_stiffness = stiff
    st.effector_weights.gravity = 0.0
    st.use_sewing_springs = True
    st.sewing_force_max = 200.0
    cm.point_cache.frame_start, cm.point_cache.frame_end = 1, N
    seamA = [idx[("A", n - 1, j)] for j in range(n)]
    sc.frame_set(1)
    R = world(o)[seamA]
    for f in range(2, N + 1):
        sc.frame_set(f)
    P = world(o)[seamA]
    return round(float(np.abs(P - R).max()), 4), round(float(np.median(np.linalg.norm(P - R, axis=1))), 4)


sewing = []
for w in (1.0, 0.99, 0.9, 0.5):
    for stiff in (1.0, 50.0):
        mx, med = sewn(w, stiff)
        sewing.append(dict(weight=w, pin_stiffness=stiff, seam_edge_moved_max_m=mx, median_m=med))
        print("SEW", w, stiff, mx, med, flush=True)
E.fact("pins below weight 1 give way to sewing springs (max force 200) at the default pin stiffness 1; "
       "stiffness 50 holds them far better; weight 1 does not move", rows=sewing)
E.save(sag=sag, follow=follow, sewing=sewing)
