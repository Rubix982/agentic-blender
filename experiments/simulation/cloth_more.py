"""Four more cloth lessons re-checked: do keyframes on sewing_force_max act; do fully pinned points collide; does
collision_settings.collection limit the colliders; is mass per vertex (so a finer grid of the same cloth is heavier)?"""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy
import numpy as np
import exp
E = exp.Experiment(__file__)


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


def step(n):
    sc = bpy.context.scene
    for f in range(1, n + 1):
        sc.frame_set(f)


# 1. keyframes on sewing_force_max (and, as a control, on gravity)
def sewn(force=None, keys=None, gravity_keys=None, N=40, pins=True):
    exp.empty()
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, N
    verts, faces, edges, idx = [], [], [], {}
    n = 9
    for side, x0 in (("A", -0.5), ("B", 0.1)):
        for i in range(n):
            for j in range(n):
                idx[(side, i, j)] = len(verts)
                verts.append((x0 + 0.4 * i / (n - 1), 0.4 * j / (n - 1) - 0.2, 1.0))
        for i in range(n - 1):
            for j in range(n - 1):
                faces.append((idx[(side, i, j)], idx[(side, i + 1, j)], idx[(side, i + 1, j + 1)], idx[(side, i, j + 1)]))
    for j in range(n):
        edges.append((idx[("A", n - 1, j)], idx[("B", 0, j)]))
    me = bpy.data.meshes.new("s"); me.from_pydata(verts, edges, faces)
    o = bpy.data.objects.new("s", me); sc.collection.objects.link(o)
    vg = o.vertex_groups.new(name="pin")      # A held by soft pins (0.9, stiffness 50), B fixed: the seam must pull A
    if pins:
        vg.add([idx[("A", i, j)] for i in range(n) for j in range(n)], 0.9, "REPLACE")
        vg.add([idx[("B", i, j)] for i in range(n) for j in range(n)], 1.0, "REPLACE")
    cm = o.modifiers.new("Cloth", "CLOTH")
    st = cm.settings
    st.vertex_group_mass = "pin"
    st.pin_stiffness = 50.0
    st.effector_weights.gravity = 0.0
    st.use_sewing_springs = True
    st.sewing_force_max = force if force is not None else 0.0
    if keys:
        for f, v in keys:
            st.sewing_force_max = v
            st.keyframe_insert("sewing_force_max", frame=f)
    if gravity_keys:
        for f, v in gravity_keys:
            st.effector_weights.gravity = v
            st.effector_weights.keyframe_insert("gravity", frame=f)
    cm.point_cache.frame_start, cm.point_cache.frame_end = 1, N
    a = [idx[("A", n - 1, j)] for j in range(n)]
    b = [idx[("B", 0, j)] for j in range(n)]
    step(N)
    P = world(o)
    return dict(gap_m=round(float(np.median(np.linalg.norm(P[a] - P[b], axis=1))), 4),
                mean_z=round(float(P[:, 2].mean()), 4), fcurve_count=len(o.animation_data.action.fcurves) if o.animation_data and o.animation_data.action else 0)


sew = {
    "sewing_force_max 0 (no limit)": sewn(0.0),
    "sewing_force_max 1": sewn(1.0),
    "sewing_force_max 200": sewn(200.0),
    "keyed 1 at frame 1 -> 200 at frame 10": sewn(keys=[(1, 1.0), (10, 200.0)]),
    "keyed 200 at frame 1 -> 1 at frame 2": sewn(keys=[(1, 200.0), (2, 1.0)]),
}
grav = {
    "gravity 0": sewn(1.0, pins=False),
    "gravity keyed 0 -> 1 at frame 20": sewn(1.0, gravity_keys=[(19, 0.0), (20, 1.0)], pins=False),
}
print("SEW", sew, grav, flush=True)
E.fact("sewing springs 20 cm long against soft pins (0.9, stiffness 50), no gravity, 40 frames: the seam gap left at "
       "each sewing_force_max, and with the force keyframed up or down. Keyed values act: each keyed run ends where a "
       "constant run at its later value ends", gaps=sew)
E.fact("control: a keyframed gravity weight does act mid-simulation (mean height after 40 frames, no pins)",
       mean_z={k: v["mean_z"] for k, v in grav.items()})

# 2. do fully pinned points collide?
def pinned_vs_ball(w, stiff=1.0, N=30):
    exp.empty()
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, N
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(0, 0, 0.5))
    ball = bpy.context.object
    ball.modifiers.new("Collision", "COLLISION")
    ball.keyframe_insert("location", frame=1)
    ball.location.z = 1.0
    ball.keyframe_insert("location", frame=20)
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=30, y_subdivisions=30, size=1.0, location=(0, 0, 1.0))
    g = bpy.context.object
    g.vertex_groups.new(name="pin").add(list(range(len(g.data.vertices))), w, "REPLACE")
    cm = g.modifiers.new("Cloth", "CLOTH")
    cm.settings.vertex_group_mass = "pin"
    cm.settings.pin_stiffness = stiff
    cm.point_cache.frame_start, cm.point_cache.frame_end = 1, N
    step(20)
    P = world(g)
    c = np.array(ball.matrix_world.translation)
    inside = int((np.linalg.norm(P - c, axis=1) < 0.2 - 0.002).sum())
    lifted = round(float(P[:, 2].max() - 1.0), 4)
    return dict(points_inside_ball=inside, highest_lift_m=lifted)


pins = {f"weight {w}, stiffness {s}": pinned_vs_ball(w, s) for w, s in ((1.0, 1.0), (0.9, 1.0), (0.9, 50.0), (0.5, 1.0))}
print("PINCOLL", pins, flush=True)
E.fact("a sheet pinned everywhere, a sphere pushed up into it from below (its top 20 cm past the sheet): points left "
       "inside the sphere and how far the sheet was lifted, by pin weight", rows=pins)

# 3. collision collection
def coll_limit(use_collection):
    exp.empty()
    sc = bpy.context.scene
    N = 30
    sc.frame_start, sc.frame_end = 1, N
    bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, 0.5))
    a = bpy.context.object; a.name = "upper"; a.modifiers.new("Collision", "COLLISION")
    bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, 0.0))
    b = bpy.context.object; b.name = "lower"; b.modifiers.new("Collision", "COLLISION")
    col = bpy.data.collections.new("only_lower")
    sc.collection.children.link(col)
    col.objects.link(b)
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=10, y_subdivisions=10, size=0.5, location=(0, 0, 1.0))
    g = bpy.context.object
    cm = g.modifiers.new("Cloth", "CLOTH")
    if use_collection:
        cm.collision_settings.collection = col
    cm.point_cache.frame_start, cm.point_cache.frame_end = 1, N
    step(N)
    return round(float(world(g)[:, 2].mean()), 3)


cl = {"no collection (both planes collide)": coll_limit(False), "collection holding only the lower plane": coll_limit(True)}
E.fact("collision_settings.collection limits a cloth's colliders: with it set to a collection holding only the lower "
       "plane, the cloth falls through the upper one (mean height after 30 frames)", mean_z=cl)

# 4. mass per vertex: a strip clamped at one end, at two grid spacings, same settings
def strip(res, scale_mass=False, bending=0.5, mass=0.3):
    exp.empty()
    sc = bpy.context.scene
    N = 120
    sc.frame_start, sc.frame_end = 1, N
    L, W = 0.12, 0.03
    nx, ny = int(round(L / res)) + 1, int(round(W / res)) + 1
    verts = [(L * i / (nx - 1), W * j / (ny - 1) - W / 2, 1.0) for i in range(nx) for j in range(ny)]
    faces = [(i * ny + j, (i + 1) * ny + j, (i + 1) * ny + j + 1, i * ny + j + 1) for i in range(nx - 1) for j in range(ny - 1)]
    me = bpy.data.meshes.new("strip"); me.from_pydata(verts, [], faces)
    o = bpy.data.objects.new("strip", me); sc.collection.objects.link(o)
    clamp = [i * ny + j for i in range(2) for j in range(ny)]
    o.vertex_groups.new(name="pin").add(clamp, 1.0, "REPLACE")
    cm = o.modifiers.new("Cloth", "CLOTH")
    cm.settings.vertex_group_mass = "pin"
    cm.settings.bending_model = "ANGULAR"
    cm.settings.bending_stiffness = bending
    cm.settings.mass = mass * ((res / 0.015) ** 2 if scale_mass else 1.0)
    cm.collision_settings.use_collision = False
    cm.point_cache.frame_start, cm.point_cache.frame_end = 1, N
    step(N)
    P = world(o)
    tip = P[[(nx - 1) * ny + j for j in range(ny)]].mean(axis=0)
    return dict(points=nx * ny, tip_reach_m=round(float(tip[0]), 4), tip_drop_m=round(float(1.0 - tip[2]), 4))


strips = {}
for b, m in ((0.5, 0.3), (200.0, 0.3), (0.5, 0.0012), (0.5, 0.003)):
    strips[f"bending {b}, mass {m}: 15 mm grid"] = strip(0.015, bending=b, mass=m)
    strips[f"bending {b}, mass {m}: 7.5 mm grid"] = strip(0.0075, bending=b, mass=m)
    strips[f"bending {b}, mass {m}: 7.5 mm grid, mass x (7.5/15)^2"] = strip(0.0075, scale_mass=True, bending=b, mass=m)
print("STRIP", strips, flush=True)
E.fact("a 12 cm strip clamped at one end, at a 15 mm and a 7.5 mm grid with the same settings, and the fine grid with "
       "its mass scaled by the square of the spacing: where its tip ends (reach along the strip, drop below the clamp)",
       rows=strips)
E.save(sewing=sew, gravity=grav, pins=pins, collection=cl, strips=strips)
