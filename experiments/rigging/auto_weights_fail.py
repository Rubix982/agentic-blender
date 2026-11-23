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


def strip_bm(bm):
    """A flat strip beside the bones (x 0.15..0.35, y 0, z 0..2): it does not enclose them."""
    rows = [[bm.verts.new((x, 0.0, 2.0 * k / 20)) for x in (0.15, 0.25, 0.35)] for k in range(21)]
    for k in range(20):
        for i in range(2):
            bm.faces.new((rows[k][i], rows[k][i + 1], rows[k + 1][i + 1], rows[k + 1][i]))
    return rows


def make(s=1.0, edit=None, base="tube"):
    global N_BASE
    exp.empty()
    scene = bpy.context.scene
    me = bpy.data.meshes.new("tube")
    bm = bmesh.new()
    vs = tube_bm(bm, s=s, caps=edit != "open tube") if base == "tube" else strip_bm(bm)
    N_BASE = len(bm.verts)
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
    unw = w.sum(axis=1) == 0
    return dict(result=res, points=len(me.vertices), unweighted=int(unw.sum()),
                unweighted_base=int(unw[:N_BASE].sum()), unweighted_added=int(unw[N_BASE:].sum()),
                groups=[g.name for g in m.vertex_groups], log=lines[:4])


# the edits
def far_cube(dist):
    def f(bm, vs, s):
        for v in bmesh.ops.create_cube(bm, size=0.2)["verts"]:
            v.co.x += dist
    return f


def part(box=True, sphere=True, x=1.5):
    """A closed box shell (8 points) at x 1..2 and/or a small sphere (62 points) at its centre."""
    def f(bm, vs, s):
        if box:
            for v in bmesh.ops.create_cube(bm, size=1.0)["verts"]:
                v.co.x += x; v.co.z += 1.0
        if sphere:
            for v in bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=6, radius=0.2)["verts"]:
                v.co.x += x; v.co.z += 1.0
    return f


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
                  ("loose cube 3 m away", dict(edit=far_cube(3.0))), ("loose cube 10 m away", dict(edit=far_cube(10.0))),
                  ("loose cube 20 m away", dict(edit=far_cube(20.0))), ("loose cube 30 m away", dict(edit=far_cube(30.0))),
                  ("loose cube 50 m away", dict(edit=far_cube(50.0))),
                  ("loose box shell 1-2 m away", dict(edit=part(sphere=False))),
                  ("loose sphere 1.5 m away", dict(edit=part(box=False))),
                  ("sphere enclosed in that box shell", dict(edit=part())),
                  ("open strip beside the bones (no tube), alone", dict(base="strip")),
                  ("open strip + loose sphere 1.5 m away", dict(base="strip", edit=part(box=False))),
                  ("open strip + loose cube 10 m away", dict(base="strip", edit=far_cube(10.0))),
                  ("open strip + loose cube 50 m away", dict(base="strip", edit=far_cube(50.0))),
                  ("all faces split apart (duplicate vertices)", dict(edit=split_faces)),
                  ("a coincident duplicate surface", dict(edit=doubled)),
                  ("a ring collapsed onto the next (zero-area faces)", dict(edit=collapsed_ring))):
    m, r = make(**kw)
    cases[label] = weigh(m, r)
    print("CASE", label, cases[label]["unweighted"], cases[label]["log"][:1], flush=True)

# the capture itself: an operator known to print a report (a Cycles bake into an image prints where it saved)
exp.empty()
bpy.ops.mesh.primitive_plane_add()
pl = bpy.context.object
mat = bpy.data.materials.new("b"); mat.use_nodes = True
pl.data.materials.append(mat)
img = bpy.data.images.new("bake", 8, 8)
tex = mat.node_tree.nodes.new("ShaderNodeTexImage"); tex.image = img
mat.node_tree.nodes.active = tex
bpy.context.scene.render.engine = "CYCLES"
bpy.context.scene.cycles.samples = 1
_, selftest = captured(lambda: bpy.ops.object.bake(type="EMIT"))
selftest = [ln.strip() for ln in selftest.splitlines() if "Baking map" in ln or "Info" in ln or "Warning" in ln][:2]
E.fact("The capture of Blender's console works: a bake run inside it printed its report there", report=selftest)

failed = [k for k, v in cases.items() if any("Bone Heat" in ln for ln in v["log"])]
zero = [k for k, v in cases.items() if v["unweighted"]]
E.fact("None of these classic causes printed 'Bone Heat Weighting: failed to find solution for one or more bones' "
       "on this tube, and parent_set returned FINISHED every time; points were left with no weight, silently, only on "
       "loose parts: a small cube 10 m or more away, and a separate box shell or sphere 1-2 m beside the tube. With an "
       "open strip in place of the tube (nothing between the loose part and the bones) the same loose parts, even "
       "the cube 50 m away, were all weighted: what left them empty was the tube's wall between them and the bones", failed=failed, unweighted_cases=zero,
       all_finished=all(v["result"] == ["FINISHED"] for v in cases.values()), cases=cases)
E.save()
