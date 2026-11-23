"""Cloth self-collision: does vertex_group_self_collisions select or exclude its points, and does a self distance large
against the edge length keep a resting cloth moving?

1. One cloth object of two 0.4 m squares 3 cm apart, the lower pinned, self-collision on (5 mm), object collision off.
   Where does the upper square end after 40 frames, with no group, every point in the group, the lower square only,
   the upper square only?
2. A 50 x 80 cm sheet pinned along its top, 12 cm too long for its height above a floor, so it buckles and folds onto
   itself; self-collision on at several self distances on a 12 mm and a 20 mm grid. The p95 point speed over the last
   20 of 120 frames (mm a frame); under 0.5 counts as at rest. Also the time per frame, self-collision on and off."""
import os, sys, time; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy, bmesh
import numpy as np
import exp
E = exp.Experiment(__file__)


def two_squares(mode):
    exp.empty()
    me = bpy.data.meshes.new("c")
    bm = bmesh.new()
    n = 16
    for z in (0.0, 0.03):
        vs = [[bm.verts.new(((i / (n - 1) - 0.5) * 0.4, (j / (n - 1) - 0.5) * 0.4, z)) for j in range(n)] for i in range(n)]
        for i in range(n - 1):
            for j in range(n - 1):
                bm.faces.new((vs[i][j], vs[i + 1][j], vs[i + 1][j + 1], vs[i][j + 1]))
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("c", me)
    bpy.context.scene.collection.objects.link(o)
    low = [v.index for v in me.vertices if v.co.z < 0.01]
    up = [v.index for v in me.vertices if v.co.z > 0.01]
    o.vertex_groups.new(name="pin").add(low, 1.0, "REPLACE")
    g = o.vertex_groups.new(name="g")
    if mode == "every point":
        g.add(list(range(len(me.vertices))), 1.0, "REPLACE")
    elif mode == "lower square only":
        g.add(low, 1.0, "REPLACE")
    elif mode == "upper square only":
        g.add(up, 1.0, "REPLACE")
    cm = o.modifiers.new("cloth", "CLOTH")
    cm.settings.vertex_group_mass = "pin"
    cs = cm.collision_settings
    cs.use_collision = False
    cs.use_self_collision = True
    cs.self_distance_min = 0.005
    cs.vertex_group_self_collisions = "g" if mode != "no group" else ""
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, 40
    cm.point_cache.frame_start, cm.point_cache.frame_end = 1, 40
    for f in range(1, 41):
        sc.frame_set(f)
    ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me2 = ev.to_mesh()
    z = min(me2.vertices[i].co.z for i in up)
    ev.to_mesh_clear()
    return round(z * 1000, 1)


groups = {m: two_squares(m) for m in ("no group", "every point", "lower square only", "upper square only")}
print("GROUPS", groups, flush=True)
E.fact("vertex_group_self_collisions EXCLUDES its points from self-collision: with no group the upper square rests on "
       "the lower; with every point in the group it falls through",
       upper_square_lowest_mm=groups, tooltip=bpy.types.ClothCollisionSettings.bl_rna.properties["vertex_group_self_collisions"].description)

FR = 120


def buckle(self_on, dist, res, quality=12):
    exp.empty()
    W, H, TOP = 0.5, 0.8, 0.7
    nx, nz = int(round(W / res)) + 1, int(round(H / res)) + 1
    me = bpy.data.meshes.new("c")
    bm = bmesh.new()
    vs = []
    for i in range(nx):
        col = []
        for j in range(nz):
            t = j / (nz - 1)                    # 0 at the hem, 1 at the top
            col.append(bm.verts.new(((i / (nx - 1) - 0.5) * W, 0.02 * (1 - t), 0.02 + (TOP - 0.02) * t)))
        vs.append(col)
    for i in range(nx - 1):
        for j in range(nz - 1):
            bm.faces.new((vs[i][j], vs[i + 1][j], vs[i + 1][j + 1], vs[i][j + 1]))
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("c", me)
    bpy.context.scene.collection.objects.link(o)
    top = [v.index for v in me.vertices if v.co.z > TOP - 1e-4]
    o.vertex_groups.new(name="pin").add(top, 1.0, "REPLACE")
    bpy.ops.mesh.primitive_plane_add(size=3, location=(0, 0, 0))
    bpy.context.active_object.modifiers.new("col", "COLLISION")
    cm = o.modifiers.new("cloth", "CLOTH")
    s = cm.settings
    s.vertex_group_mass = "pin"
    s.quality = quality
    s.mass = 0.15
    cs = cm.collision_settings
    cs.collision_quality = 8
    cs.distance_min = 0.003
    cs.use_self_collision = self_on
    cs.self_distance_min = dist
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, FR
    cm.point_cache.frame_start, cm.point_cache.frame_end = 1, FR
    prev, speeds = None, []
    t0 = time.time()
    dg = bpy.context.evaluated_depsgraph_get()
    for f in range(1, FR + 1):
        sc.frame_set(f)
        ev = o.evaluated_get(dg)
        p = np.empty(len(ev.data.vertices) * 3)
        ev.data.vertices.foreach_get("co", p)
        p = p.reshape(-1, 3)
        if prev is not None and f > FR - 20:
            speeds.append(np.percentile(np.linalg.norm(p - prev, axis=1), 95))
        prev = p
    secs = time.time() - t0
    return dict(self_collision=self_on, self_distance_mm=dist * 1000, grid_mm=res * 1000, points=nx * nz,
                p95_speed_mm_per_frame=round(float(np.mean(speeds)) * 1000, 3), seconds_per_frame=round(secs / FR, 3),
                ratio_distance_to_edge=round(dist / res, 3))


rows = []
for args in ((False, 0.005, 0.012), (True, 0.004, 0.012), (True, 0.0045, 0.012), (True, 0.005, 0.012),
             (True, 0.005, 0.020)):
    r = buckle(*args)
    rows.append(r)
    print("BUCKLE", r, flush=True)
E.fact("self-collision keeps a folded sheet moving once the self distance passes about 0.37 of the edge length: "
       "p95 speed in mm a frame over the last 20 of 120 frames, settled under 0.5",
       rows=[(r["grid_mm"], r["self_distance_mm"], r["self_collision"], r["p95_speed_mm_per_frame"]) for r in rows])
off = rows[0]["seconds_per_frame"]
on = rows[3]["seconds_per_frame"]
E.fact("self-collision's cost on a ~2,800-point sheet at quality 12, collision quality 8",
       seconds_per_frame_off=off, seconds_per_frame_on_5mm=on, factor=round(on / off, 1))
E.save(groups_mm=groups, buckle=rows)
