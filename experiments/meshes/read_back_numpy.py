"""Reading mesh data into numpy with foreach_get: does the array dtype matter, and how fast is it against a Python loop?"""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import time
import numpy as np
import bpy
import exp
E = exp.Experiment(__file__)

bpy.ops.mesh.primitive_grid_add(x_subdivisions=999, y_subdivisions=999, size=2)   # 1000 x 1000 = 1M verts
ob = bpy.context.object
me = ob.data
n = len(me.vertices)

def timed(fn, reps=3):
    best = 1e9
    for _ in range(reps):
        t = time.perf_counter(); fn(); best = min(best, time.perf_counter() - t)
    return best

a32 = np.empty(n * 3, np.float32)
a64 = np.empty(n * 3, np.float64)
t32 = timed(lambda: me.vertices.foreach_get("co", a32))
t64 = timed(lambda: me.vertices.foreach_get("co", a64))
ap = np.empty(n * 3, np.float32)
tattr = timed(lambda: me.attributes["position"].data.foreach_get("vector", ap))
tloop = timed(lambda: [v.co[:] for v in me.vertices], reps=1)
E.fact(f"reading positions through mesh.attributes['position'].data.foreach_get('vector', float32 array) takes {tattr*1000:.2f} ms for 1M vertices, against {t32*1000:.1f} ms through vertices.foreach_get('co')",
       same_values=bool(np.array_equal(ap, a32)))
E.fact(f"foreach_get of 1M vertex positions takes {t32*1000:.1f} ms into float32, {t64*1000:.1f} ms into float64, and a Python loop over vertices takes {tloop*1000:.0f} ms",
       verts=n, float32_ms=round(t32 * 1000, 2), float64_ms=round(t64 * 1000, 2), attribute_position_ms=round(tattr * 1000, 2),
       python_loop_ms=round(tloop * 1000, 1), same_values=bool(np.allclose(a32, a64)))

# a list works but is slow; a wrong-size array raises
try:
    me.vertices.foreach_get("co", np.empty(10, np.float32)); wrong = "accepted"
except Exception as e:
    wrong = f"{type(e).__name__}: {e}"
E.fact("foreach_get into an array of the wrong size raises instead of truncating", error=wrong)

# 2D array accepted?
try:
    a2 = np.empty((n, 3), np.float32); me.vertices.foreach_get("co", a2); two_d = "accepted"
    two_d_ok = bool(np.allclose(a2.ravel(), a32))
except Exception as e:
    two_d = f"{type(e).__name__}: {e}"; two_d_ok = None
E.fact("foreach_get " + ("accepts" if two_d == "accepted" else "rejects") + " a 2D (n,3) float32 array; pass a flat array (or a.ravel() view) of length 3n", result=two_d, values_match=two_d_ok)

# indices: loops vertex_index into int32 vs int64
nl = len(me.loops)
i32 = np.empty(nl, np.int32); i64 = np.empty(nl, np.int64)
ti32 = timed(lambda: me.loops.foreach_get("vertex_index", i32))
ti64 = timed(lambda: me.loops.foreach_get("vertex_index", i64))
ic = np.empty(nl, np.int32)
tic = timed(lambda: me.attributes[".corner_vert"].data.foreach_get("value", ic))
E.fact(f"corner (loop) vertex indices read through attributes['.corner_vert'] take {tic*1000:.1f} ms against {ti32*1000:.1f} ms through loops.foreach_get('vertex_index')",
       same_values=bool(np.array_equal(ic, i32)), internal_names=[a.name for a in me.attributes if a.name.startswith('.')])
E.fact(f"loop vertex_index foreach_get: int32 {ti32*1000:.1f} ms vs int64 {ti64*1000:.1f} ms for {nl} loops",
       loops=nl, int32_ms=round(ti32 * 1000, 2), int64_ms=round(ti64 * 1000, 2))

# world-space positions
mw = np.array(ob.matrix_world)
co = a32.reshape(-1, 3)
world = co @ mw[:3, :3].T + mw[:3, 3]
E.fact("world-space positions are co @ M[:3,:3].T + M[:3,3] with M = np.array(obj.matrix_world)", first=world[0].tolist())

# polygon normals and centers
pn = np.empty(len(me.polygons) * 3, np.float32)
tpn = timed(lambda: me.polygons.foreach_get("normal", pn))
E.fact(f"polygon normals for {len(me.polygons)} faces via foreach_get take {tpn*1000:.1f} ms", ms=round(tpn * 1000, 2), first=pn[:3].tolist())
E.save()
