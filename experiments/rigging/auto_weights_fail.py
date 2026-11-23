"""When do automatic weights (bone heat, parent_set ARMATURE_AUTO) fail? The classic causes, each on the same 336-point
tube and two-bone rig (2 m tall) that weights cleanly as it is: size applied to the data (not object scale), open and
non-manifold geometry, intersecting parts, loose parts near and far, a part enclosed in a shell that hides the bones,
split faces and coincident duplicate surfaces, and degenerate faces.

Blender's own messages are caught by pointing file descriptors 1 and 2 at a file around each operator call (they are
written by C code, not Python's print). Counted per case: points with no weight at all, and the warning text."""
import ctypes
import math
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bmesh  # noqa: E402
import bpy  # noqa: E402
import numpy as np  # noqa: E402

import exp  # noqa: E402

E = exp.Experiment(__file__)
libc = ctypes.CDLL(None)


def captured(fn):
    sys.stdout.flush(); sys.stderr.flush(); libc.fflush(None)
    tmp = tempfile.TemporaryFile()
    s1, s2 = os.dup(1), os.dup(2)
    os.dup2(tmp.fileno(), 1); os.dup2(tmp.fileno(), 2)
    try:
        res = fn()
    finally:
        sys.stdout.flush(); sys.stderr.flush(); libc.fflush(None)
        os.dup2(s1, 1); os.dup2(s2, 2); os.close(s1); os.close(s2)
    tmp.seek(0)
    text = tmp.read().decode("utf-8", "replace")
    tmp.close()
    return res, text


def tube_bm(bm, s=1.0, caps=True, x=0.0, axis="z"):
    rings, seg = 21, 16
    vs = []
    for k in range(rings):
        t = 2.0 * k / (rings - 1)
        ring = []
        for i in range(seg):
            a, b = 0.1 * math.cos(2 * math.pi * i / seg), 0.1 * math.sin(2 * math.pi * i / seg)
            co = (a + x, b, t) if axis == "z" else (t - 1.0 + x, a, b + 1.0)
            ring.append(bm.verts.new(tuple(c * s for c in co)))
        vs.append(ring)
    for k in range(rings - 1):
        for i in range(seg):
            bm.faces.new((vs[k][i], vs[k][(i + 1) % seg], vs[k + 1][(i + 1) % seg], vs[k + 1][i]))
    if caps:
        bm.faces.new(vs[0][::-1]); bm.faces.new(vs[-1])
    return vs


def make(s=1.0, edit=None):
    exp.empty()
    scene = bpy.context.scene
    me = bpy.data.meshes.new("tube")
    bm = bmesh.new()
    vs = tube_bm(bm, s=s, caps=edit != "open tube")
    if edit:
        edit(bm, vs, s) if callable(edit) else None
    bm.to_mesh(me); bm.free()
    m = bpy.data.objects.new("tube", me)
    scene.collection.objects.link(m)
    arm = bpy.data.armatures.new("Rig")
    r = bpy.data.objects.new("Rig", arm)
    scene.collection.objects.link(r)
    bpy.context.view_layer.objects.active = r
    bpy.ops.object.mode_set(mode="EDIT")
    a = arm.edit_bones.new("lower"); a.head = (0, 0, 0); a.tail = (0, 0, 1 * s)
    b = arm.edit_bones.new("upper"); b.head = (0, 0, 1 * s); b.tail = (0, 0, 2 * s); b.parent = a; b.use_connect = True
    bpy.ops.object.mode_set(mode="OBJECT")
    return m, r


def weigh(m, r):
    bpy.ops.object.select_all(action="DESELECT")
    m.select_set(True); r.select_set(True)
    bpy.context.view_layer.objects.active = r
    res, log = captured(lambda: list(bpy.ops.object.parent_set(type="ARMATURE_AUTO")))
    me = m.data
    w = np.zeros((len(me.vertices), max(1, len(m.vertex_groups))))
    for v in me.vertices:
        for g in v.groups:
            w[v.index, g.group] = g.weight
    lines = [ln.strip() for ln in log.splitlines() if ln.strip() and not ln.startswith(("Fra:", "Read ", "Blender"))]
    return dict(result=res, points=len(me.vertices), unweighted=int((w.sum(axis=1) == 0).sum()),
                groups=[g.name for g in m.vertex_groups], log=lines[:4])


# the edits
def far_cube(dist):
    def f(bm, vs, s):
        for v in bmesh.ops.create_cube(bm, size=0.2)["verts"]:
            v.co.x += dist
    return f


def enclosed(bm, vs, s):
    """A closed box shell at x 1..2 with a small sphere inside it: the box hides every bone from the sphere."""
    for v in bmesh.ops.create_cube(bm, size=1.0)["verts"]:
        v.co.x += 1.5; v.co.z += 1.0
    for v in bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=6, radius=0.2)["verts"]:
        v.co.x += 1.5; v.co.z += 1.0


def crossing(bm, vs, s):
    """A second tube, horizontal, passing through the first at z = 1 (intersecting, not joined)."""
    tube_bm(bm, s=s, axis="x")


def fin(bm, vs, s):
    """A third face on one edge: non-manifold."""
    v0, v1 = vs[10][0], vs[10][1]
    v2 = bm.verts.new((v1.co.x + 0.3, v1.co.y, v1.co.z))
    v3 = bm.verts.new((v0.co.x + 0.3, v0.co.y, v0.co.z))
    bm.faces.new((v0, v1, v2, v3))


def split_faces(bm, vs, s):
    """Every face its own island: each corner a separate vertex, duplicates at the same place."""
    bmesh.ops.split_edges(bm, edges=bm.edges[:])


def doubled(bm, vs, s):
    """A second copy of the whole surface at exactly the same place, not merged."""
    bmesh.ops.duplicate(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:])


def collapsed_ring(bm, vs, s):
    """Ring 10 moved onto ring 11 without merging: zero-length edges and zero-area faces."""
    for a, b in zip(vs[10], vs[11]):
        a.co = b.co.copy()


cases = {}
for label, kw in (("as built (2 m)", {}),
                  ("size 0.01 applied (2 cm)", dict(s=0.01)), ("size 0.001 applied (2 mm)", dict(s=0.001)),
                  ("size 0.0001 applied (0.2 mm)", dict(s=0.0001)),
                  ("size 100 applied (200 m)", dict(s=100.0)), ("size 1000 applied (2 km)", dict(s=1000.0)),
                  ("open tube (no caps)", dict(edit="open tube")), ("a fin: one edge with 3 faces", dict(edit=fin)),
                  ("a second tube crossing through", dict(edit=crossing)),
                  ("loose cube 3 m away", dict(edit=far_cube(3.0))), ("loose cube 50 m away", dict(edit=far_cube(50.0))),
                  ("sphere enclosed in a box shell", dict(edit=enclosed)),
                  ("all faces split apart (duplicate vertices)", dict(edit=split_faces)),
                  ("a coincident duplicate surface", dict(edit=doubled)),
                  ("a ring collapsed onto the next (zero-area faces)", dict(edit=collapsed_ring))):
    m, r = make(**kw)
    cases[label] = weigh(m, r)
    print("CASE", label, cases[label]["unweighted"], cases[label]["log"][:1], flush=True)

failed = [k for k, v in cases.items() if any("Bone Heat" in ln for ln in v["log"])]
zero = [k for k, v in cases.items() if v["unweighted"]]
E.fact("Which classic causes make bone heat fail on a tube that weights cleanly: the cases that printed 'Bone Heat "
       "Weighting: failed to find solution for one or more bones', and the cases that left points with no weight. "
       "parent_set returned FINISHED in every case", failed=failed, unweighted_cases=zero,
       all_finished=all(v["result"] == ["FINISHED"] for v in cases.values()), cases=cases)
E.save()
