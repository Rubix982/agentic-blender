"""Cloth cost: seconds per frame against quality (steps), collision quality and point count, and whether the cloth goes
into the collider at low settings.

A 1 m sheet dropped onto a sphere (r 0.3 m); 40 frames; points that end inside the sphere (deeper than 1 mm) counted."""
import os, sys, time; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy
import numpy as np
import exp
E = exp.Experiment(__file__)
N = 40
R = 0.3


def run(sub, quality, coll_q, fast_ball=False):
    exp.empty()
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, N
    bpy.ops.mesh.primitive_uv_sphere_add(radius=R, location=(0, 0, 0.5), segments=48, ring_count=24)
    ball = bpy.context.object
    ball.modifiers.new("Collision", "COLLISION")
    if fast_ball:   # the ball rises through the cloth's rest place quickly: a fast collider
        ball.location.z = 0.0
        ball.keyframe_insert("location", frame=1)
        ball.location.z = 1.4
        ball.keyframe_insert("location", frame=3)
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=sub, y_subdivisions=sub, size=1.0, location=(0, 0, 1.0))
    g = bpy.context.object
    cm = g.modifiers.new("Cloth", "CLOTH")
    cm.settings.quality = quality
    cm.collision_settings.collision_quality = coll_q
    cm.point_cache.frame_start, cm.point_cache.frame_end = 1, N
    t = time.time()
    max_inside = 0
    for f in range(1, N + 1):
        sc.frame_set(f)
        if fast_ball and f <= 8:
            max_inside = max(max_inside, count_inside(g, ball))
    secs = time.time() - t
    e = g.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me = e.to_mesh()
    P = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", P)
    e.to_mesh_clear()
    P = P.reshape(-1, 3) + np.array(g.location)
    c = np.array(ball.matrix_world.translation)
    inside = int((np.linalg.norm(P - c, axis=1) < R - 0.001).sum())
    return dict(points=(sub + 1) ** 2, quality=quality, collision_quality=coll_q, fast_ball=fast_ball,
                seconds_per_frame=round(secs / N, 4), points_inside_ball=inside, max_inside_frames_1_8=max_inside)


def count_inside(g, ball):
    e = g.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me = e.to_mesh()
    P = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", P)
    e.to_mesh_clear()
    P = P.reshape(-1, 3) + np.array(g.location)
    c = np.array(ball.matrix_world.translation)
    return int((np.linalg.norm(P - c, axis=1) < R - 0.001).sum())


rows = []
for q in (2, 5, 10, 20):
    rows.append(run(40, q, 2)); print("ROW", rows[-1], flush=True)
for cq in (1, 5):
    rows.append(run(40, 5, cq)); print("ROW", rows[-1], flush=True)
for sub in (20, 80):
    rows.append(run(sub, 5, 2)); print("ROW", rows[-1], flush=True)
for q, cq in ((5, 2), (5, 8), (20, 2)):
    rows.append(run(40, q, cq, fast_ball=True)); print("ROW", rows[-1], flush=True)


def pick(**k):
    return next(r for r in rows if all(r[a] == b for a, b in k.items()))


E.fact("cloth time per frame rises with quality (steps per frame) but less than in proportion: 1,681 points over a sphere",
       sec_per_frame={q: pick(points=1681, quality=q, collision_quality=2, fast_ball=False)["seconds_per_frame"] for q in (2, 5, 10, 20)})
E.fact("cloth time per frame against point count at quality 5",
       sec_per_frame={p: pick(points=p, quality=5, collision_quality=2, fast_ball=False)["seconds_per_frame"] for p in (441, 1681, 6561)})
E.fact("collision quality's cost on a drape over a still sphere; no points end inside at 1, 2 or 5",
       rows=[(r["collision_quality"], r["seconds_per_frame"], r["points_inside_ball"]) for r in rows
             if r["points"] == 1681 and r["quality"] == 5 and not r["fast_ball"]])
E.fact("a collider driven up through the cloth fast (1.4 m in 2 frames): the most cloth points inside it on any of "
       "frames 1-8, and at the end, by quality and collision quality",
       rows=[(r["quality"], r["collision_quality"], r["max_inside_frames_1_8"], r["points_inside_ball"]) for r in rows if r["fast_ball"]])
E.save(rows=rows, frames=N)
