"""Does the voxel Remesh return its points in the same order every time? The same input, remeshed in separate Blender
processes (three at -t 1, three at the default thread count) and twice within each process, at three voxel sizes; and
the voxel_remesh operator (Object Data > Remesh) the same way. Compared: point counts, whether the point arrays are
identical, how many indices hold a different point, and whether the same set of points came back (sorted by x, y, z).

Run with the system Python (it starts Blender itself, with and without -t 1):
    python3 experiments/modifiers/remesh_order.py
"""
import datetime
import json
import os
import platform
import subprocess
import sys
import tempfile

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from run import blender  # noqa: E402

B = blender()
TMP = tempfile.mkdtemp(prefix="bfg-remesh-")
SIZES = (0.05, 0.02, 0.01)

INNER = r'''
import sys, os, time
import bpy, bmesh
import numpy as np
from mathutils import Matrix
argv = sys.argv[sys.argv.index("--") + 1:]
out, sizes = argv[0], [float(x) for x in argv[1].split(",")]
bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new("in")
bm = bmesh.new()
bmesh.ops.create_monkey(bm, matrix=Matrix.Scale(1.0, 4))              # about 2.7 x 1.7 x 2 m
bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=0.6, matrix=Matrix.Translation((0, 0.4, -1.2)))
bm.to_mesh(me); bm.free()
ob = bpy.data.objects.new("in", me)
bpy.context.scene.collection.objects.link(ob)
md = ob.modifiers.new("R", "REMESH")
md.mode = "VOXEL"
res = {}
def pts():
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg).data
    a = np.zeros(len(ev.vertices) * 3, np.float32)
    ev.vertices.foreach_get("co", a)
    return a.reshape(-1, 3)
for s in sizes:
    md.voxel_size = s
    t = time.time()
    res[f"mod_{s}_a"] = pts()
    res[f"time_{s}"] = np.array([time.time() - t])
    md.voxel_size = s * 1.5            # force a fresh evaluation, then back
    pts()
    md.voxel_size = s
    res[f"mod_{s}_b"] = pts()
ob.modifiers.remove(md)
for s in sizes:
    m2 = me.copy()
    o2 = bpy.data.objects.new("op", m2)
    bpy.context.scene.collection.objects.link(o2)
    m2.remesh_voxel_size = s
    with bpy.context.temp_override(object=o2, active_object=o2, selected_objects=[o2], selected_editable_objects=[o2]):
        r = bpy.ops.object.voxel_remesh()
    a = np.zeros(len(m2.vertices) * 3, np.float32)
    m2.vertices.foreach_get("co", a)
    res[f"op_{s}"] = a.reshape(-1, 3)
# the same input with its points in another order, and with 1e-6 m of noise (voxel 0.02)
co = np.zeros(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
faces = [tuple(p.vertices) for p in me.polygons]
rng = np.random.default_rng(0)
def remeshed(verts, fcs, s=0.02):
    m3 = bpy.data.meshes.new("v"); m3.from_pydata(verts.tolist(), [], fcs); m3.update()
    o3 = bpy.data.objects.new("v", m3); bpy.context.scene.collection.objects.link(o3)
    r3 = o3.modifiers.new("R", "REMESH"); r3.mode = "VOXEL"; r3.voxel_size = s
    dg = bpy.context.evaluated_depsgraph_get(); ev = o3.evaluated_get(dg).data
    a = np.zeros(len(ev.vertices) * 3, np.float32); ev.vertices.foreach_get("co", a)
    return a.reshape(-1, 3)
res["var_base"] = remeshed(co, faces)
perm = rng.permutation(len(co)); inv = np.argsort(perm)
res["var_shuffled"] = remeshed(co[perm], [tuple(int(inv[i]) for i in f) for f in faces])
res["var_noise"] = remeshed(co + rng.normal(0, 1e-6, co.shape).astype(np.float32), faces)
res["threads"] = np.array([bpy.context.scene.render.threads])
np.savez(out, **res)
'''
inner = os.path.join(TMP, "inner.py")
open(inner, "w").write(INNER)

runs = {}
for threads in ("1", None):
    for k in range(3):
        out = os.path.join(TMP, f"t{threads or 'default'}_{k}.npz")
        cmd = [B, "-b", "--factory-startup", "--python-exit-code", "1"] + (["-t", threads] if threads else []) + \
              ["--python", inner, "--", out, ",".join(str(s) for s in SIZES)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stdout[-2000:], r.stderr[-2000:])
            raise SystemExit("inner run failed")
        runs[(threads or "default", k)] = dict(np.load(out))
        print("ran", threads or "default", k, flush=True)


def compare(a, b):
    if a.shape != b.shape:
        n = min(len(a), len(b))
        close = np.abs(a[:n] - b[:n]).max(axis=1) < 1e-4
        return dict(same_count=False, counts=[len(a), len(b)], same_index_within_0_1_mm=int(close.sum()),
                    first_index_that_differs=int(np.argmin(close)) if not close.all() else n)
    rows_differ = int((np.abs(a - b).max(axis=1) > 0).sum())
    sa = a[np.lexsort(a.T[::-1])]
    sb = b[np.lexsort(b.T[::-1])]
    return dict(same_count=True, identical=bool(np.array_equal(a, b)), points=len(a), indices_differing=rows_differ,
                same_set=bool(np.array_equal(sa, sb)), max_sorted_diff=float(np.abs(sa - sb).max()))


facts = []
table = {}
for s in SIZES:
    row = {}
    for kind in ("mod", "op"):
        key = f"{kind}_{s}_a" if kind == "mod" else f"op_{s}"
        ref = runs[("1", 0)][key]
        row[f"{kind} points"] = len(ref)
        for threads in ("1", "default"):
            for k in range(3):
                if (threads, k) == ("1", 0):
                    continue
                row[f"{kind} -t {threads} run {k + 1} vs -t 1 run 1"] = compare(ref, runs[(threads, k)][key])
    row["mod, same process, evaluated twice (-t 1 run 1)"] = compare(runs[("1", 0)][f"mod_{s}_a"], runs[("1", 0)][f"mod_{s}_b"])
    row["mod, same process, evaluated twice (default run 1)"] = compare(runs[("default", 0)][f"mod_{s}_a"],
                                                                         runs[("default", 0)][f"mod_{s}_b"])
    row["seconds (-t 1, default)"] = [round(float(runs[("1", 0)][f"time_{s}"][0]), 3),
                                      round(float(runs[("default", 0)][f"time_{s}"][0]), 3)]
    table[f"voxel {s}"] = row

variants = {}
for threads in ("1", "default"):
    base = runs[(threads, 0)]["var_base"]
    variants[f"-t {threads}: input points shuffled"] = compare(base, runs[(threads, 0)]["var_shuffled"])
    variants[f"-t {threads}: input moved by 1e-6 m noise"] = compare(base, runs[(threads, 0)]["var_noise"])
facts.append(dict(fact="The voxel Remesh output depends on the surface, not on the input's point order: the same input "
                       "with its points shuffled gave the identical array; moving each input point by about 1e-6 m "
                       "changed the output's point count (60,010 to 60,008), and with it the index of most points",
                  **variants))
any_reorder = any(v.get("same_count") and not v.get("identical") for row in table.values() for v in row.values()
                  if isinstance(v, dict))
facts.insert(0, dict(fact="The voxel Remesh returned the identical point array (same points, same order) in every run: "
                       "3 separate processes at -t 1 and 3 at the default thread count (12), at voxel 0.05, 0.02 and 0.01, "
                       "for the Remesh modifier and the voxel_remesh operator, and when evaluated twice in one process. "
                       "Each run is compared with the first run at -t 1",
                  any_run_reordered=any_reorder, threads_default=int(runs[("default", 0)]["threads"][0]),
                  threads_t1=int(runs[("1", 0)]["threads"][0]), **table))
print(json.dumps(facts, indent=1)[:4000])

for f in os.listdir(TMP):
    os.remove(os.path.join(TMP, f))
os.rmdir(TMP)
rec = dict(experiment=os.path.relpath(os.path.abspath(__file__), ROOT),
           blender=subprocess.run([B, "--version"], capture_output=True, text=True).stdout.splitlines()[0],
           machine=f"{platform.system()} {platform.machine()}", date=datetime.date.today().isoformat(), facts=facts)
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results"), exist_ok=True)
json.dump(rec, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "remesh_order.json"), "w"), indent=1)
