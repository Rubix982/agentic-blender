"""Operators vs the data API for the same job: making 1000 cubes, and moving 1000 objects. Speed and what each leaves behind."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import time
import bpy, bmesh
import exp
E = exp.Experiment(__file__)
N = 1000

t = time.perf_counter()
for i in range(N):
    bpy.ops.mesh.primitive_cube_add(size=0.5, location=(i % 32, i // 32, 0))
t_ops = time.perf_counter() - t
meshes_ops = len(bpy.data.meshes)
E.fact(f"{N} x bpy.ops.mesh.primitive_cube_add takes {t_ops:.2f} s and makes {meshes_ops} separate meshes", seconds=round(t_ops, 3), meshes=meshes_ops)
# how the per-call time grows
exp.empty()
lap = []
t = time.perf_counter()
for i in range(N):
    bpy.ops.mesh.primitive_cube_add(size=0.5, location=(i % 32, i // 32, 0))
    if (i + 1) % 250 == 0:
        lap.append(round(time.perf_counter() - t, 3)); t = time.perf_counter()
E.fact("operator cost per 250 cubes as the scene fills", laps_s=lap)

exp.empty()
t = time.perf_counter()
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=0.5)
me = bpy.data.meshes.new("cube"); bm.to_mesh(me); bm.free()
col = bpy.context.scene.collection
for i in range(N):
    o = bpy.data.objects.new(f"c{i}", me); o.location = (i % 32, i // 32, 0)
    col.objects.link(o)
t_data_shared = time.perf_counter() - t
E.fact(f"{N} objects sharing one mesh via bpy.data.objects.new + link takes {t_data_shared:.3f} s", seconds=round(t_data_shared, 4))

exp.empty()
t = time.perf_counter()
col = bpy.context.scene.collection
for i in range(N):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=0.5)
    me = bpy.data.meshes.new(f"m{i}"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(f"c{i}", me); o.location = (i % 32, i // 32, 0)
    col.objects.link(o)
t_data_own = time.perf_counter() - t
E.fact(f"{N} objects each with its own bmesh-built mesh takes {t_data_own:.3f} s", seconds=round(t_data_own, 4),
       speedup_vs_ops=round(t_ops / t_data_own, 1))

# moving: operator on selection vs setting location
objs = list(bpy.context.scene.objects)
for o in objs:
    o.select_set(True)
t = time.perf_counter(); bpy.ops.transform.translate(value=(0, 0, 1)); t_tr = time.perf_counter() - t
t = time.perf_counter()
for o in objs:
    o.location.z += 1
t_loc = time.perf_counter() - t
E.fact(f"moving {N} selected objects: one transform.translate call {t_tr*1000:.1f} ms, a Python loop over location {t_loc*1000:.1f} ms",
       translate_ms=round(t_tr * 1000, 2), loop_ms=round(t_loc * 1000, 2), z=objs[0].location.z)
# foreach_set on objects' locations? (collection of objects in bpy.data supports foreach)
import numpy as np
locs = np.zeros(len(objs) * 3, np.float32)
try:
    t = time.perf_counter(); bpy.data.objects.foreach_get("location", locs); t_fe = time.perf_counter() - t
    fe = f"works, {t_fe*1000:.2f} ms"
except Exception as e:
    fe = f"{type(e).__name__}: {e}"
E.fact("bpy.data.objects.foreach_get('location', array) reads all object locations in one call", result=fe)
E.save()
