"""How long does it take to build a grid mesh from arrays: from_pydata (Python lists) vs vertices.add + foreach_set (numpy)?"""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import time
import numpy as np
import bpy
import exp
E = exp.Experiment(__file__)


def grid(n):
    """n x n vertices, (n-1)^2 quads, as numpy arrays."""
    xs, ys = np.meshgrid(np.arange(n, dtype=np.float32), np.arange(n, dtype=np.float32))
    co = np.stack([xs.ravel(), ys.ravel(), np.zeros(n * n, np.float32)], 1)
    i = np.arange(n * n).reshape(n, n)
    quads = np.stack([i[:-1, :-1].ravel(), i[:-1, 1:].ravel(), i[1:, 1:].ravel(), i[1:, :-1].ravel()], 1)
    return co, quads.astype(np.int32)


def by_pydata(co, quads):
    t = time.perf_counter()
    vl, fl = co.tolist(), quads.tolist()
    t_list = time.perf_counter() - t
    me = bpy.data.meshes.new("pydata")
    t = time.perf_counter()
    me.from_pydata(vl, [], fl)
    t_build = time.perf_counter() - t
    t = time.perf_counter()
    me.update()
    t_upd = time.perf_counter() - t
    return me, t_list, t_build, t_upd


def by_foreach(co, quads):
    me = bpy.data.meshes.new("foreach")
    t = time.perf_counter()
    nv, nf = len(co), len(quads)
    me.vertices.add(nv)
    me.vertices.foreach_set("co", co.ravel())
    me.loops.add(nf * 4)
    me.loops.foreach_set("vertex_index", quads.ravel())
    me.polygons.add(nf)
    me.polygons.foreach_set("loop_start", np.arange(0, nf * 4, 4, dtype=np.int32))
    t_set = time.perf_counter() - t
    t = time.perf_counter()
    me.update(calc_edges=True)
    t_upd = time.perf_counter() - t
    return me, t_set, t_upd


def by_attributes(co, quads):
    """Same as by_foreach, but positions and corner vertices written through the attribute API."""
    me = bpy.data.meshes.new("attr")
    t = time.perf_counter()
    nv, nf = len(co), len(quads)
    me.vertices.add(nv)
    me.attributes["position"].data.foreach_set("vector", co.ravel())
    me.loops.add(nf * 4)
    me.attributes[".corner_vert"].data.foreach_set("value", quads.ravel())
    me.polygons.add(nf)
    me.polygons.foreach_set("loop_start", np.arange(0, nf * 4, 4, dtype=np.int32))
    t_set = time.perf_counter() - t
    t = time.perf_counter()
    me.update(calc_edges=True)
    t_upd = time.perf_counter() - t
    return me, t_set, t_upd


rows = []
for n in (100, 317, 1000):          # 10k, ~100k, 1M vertices
    co, quads = grid(n)
    me1, tl, tb, tu1 = by_pydata(co, quads)
    me2, ts, tu2 = by_foreach(co, quads)
    me3, ts3, tu3 = by_attributes(co, quads)
    pa, pb = np.empty(len(co) * 3, np.float32), np.empty(len(co) * 3, np.float32)
    me2.vertices.foreach_get("co", pa); me3.vertices.foreach_get("co", pb)
    same3 = bool(np.array_equal(pa, pb)) and len(me3.edges) == len(me2.edges)
    bpy.data.meshes.remove(me3)
    t = time.perf_counter(); bad1 = me1.validate(verbose=False); tv = time.perf_counter() - t
    bad2 = me2.validate(verbose=False)
    same = (len(me1.vertices), len(me1.edges), len(me1.polygons)) == (len(me2.vertices), len(me2.edges), len(me2.polygons))
    r = dict(verts=len(co), faces=len(quads), edges_pydata=len(me1.edges), edges_foreach=len(me2.edges),
             pydata_tolist_s=round(tl, 4), pydata_build_s=round(tb, 4), pydata_update_s=round(tu1, 4),
             foreach_set_s=round(ts, 4), foreach_update_calc_edges_s=round(tu2, 4), validate_s=round(tv, 4),
             validate_changed_pydata=bad1, validate_changed_foreach=bad2, same_counts=same,
             attr_set_s=round(ts3, 4), attr_update_s=round(tu3, 4), attr_same_mesh=same3)
    rows.append(r)
    print(r)
    bpy.data.meshes.remove(me1); bpy.data.meshes.remove(me2)

for r in rows:
    total_py = r["pydata_tolist_s"] + r["pydata_build_s"]
    total_fe = r["foreach_set_s"] + r["foreach_update_calc_edges_s"]
    E.fact(f"at {r['verts']} vertices, from_pydata (with tolist) takes {total_py:.3f} s and vertices.add+foreach_set+update(calc_edges=True) takes {total_fe:.3f} s",
           ratio=round(total_py / max(total_fe, 1e-9), 1), **r)
for r in rows:
    E.fact(f"at {r['verts']} vertices, writing positions and corner vertices through mesh.attributes ('position', '.corner_vert') takes {r['attr_set_s']+r['attr_update_s']:.3f} s against {r['foreach_set_s']+r['foreach_update_calc_edges_s']:.3f} s through vertices/loops.foreach_set",
           same_mesh=r["attr_same_mesh"])
E.fact("both routes end with the same edge count (from_pydata makes edges itself; the foreach_set route gets them from update())",
       edges_pydata=rows[0]["edges_pydata"], edges_foreach=rows[0]["edges_foreach"])
E.fact("neither route leaves anything for validate() to fix on a clean grid", changed=[(r["validate_changed_pydata"], r["validate_changed_foreach"]) for r in rows])

# foreach route without calc_edges: are edges there before update, after update(), after validate()?
me = bpy.data.meshes.new("noedges")
co, quads = grid(10)
me.vertices.add(len(co)); me.vertices.foreach_set("co", co.ravel())
me.loops.add(quads.size); me.loops.foreach_set("vertex_index", quads.ravel())
me.polygons.add(len(quads)); me.polygons.foreach_set("loop_start", np.arange(0, quads.size, 4, dtype=np.int32))
edges_before_update = len(me.edges)
me.update()
edges_after_plain_update = len(me.edges)
E.fact(f"built by foreach_set, a mesh has {edges_before_update} edges before update() and {edges_after_plain_update} after a plain update() (calc_edges=False); "
       + ("so update() computes missing edges even without calc_edges" if edges_after_plain_update else "so calc_edges=True is required"),
       edges_before_update=edges_before_update, edges_after_plain_update=edges_after_plain_update, expected=180)
# loop_total writable?
before = me.polygons[0].loop_total
try:
    me.polygons.foreach_set("loop_total", np.full(len(quads), 4, np.int32)); lt = "accepted"
except Exception as e:
    lt = f"{type(e).__name__}: {e}"
try:
    me.polygons[0].loop_total = 4; lt1 = "accepted"
except Exception as e:
    lt1 = f"{type(e).__name__}: {e}"
E.fact("loop_start alone defines the faces: loop_total is derived from the next face's loop_start, and is already 4 on a quad built without setting it",
       loop_total_before_setting=before, foreach_set_loop_total=lt, attribute_set_loop_total=lt1)
E.fact("Mesh.update docstring in 4.5", doc=bpy.types.Mesh.bl_rna.functions["update"].description,
       params={p.identifier: p.description for p in bpy.types.Mesh.bl_rna.functions["update"].parameters})
E.save(rows=rows)
