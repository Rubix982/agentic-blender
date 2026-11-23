"""Parenting a mesh to an armature with automatic weights in background mode: does
bpy.ops.object.parent_set(type='ARMATURE_AUTO') work under -b, with selection or with only a context override; what does
it make; when does bone heat fail; and does posing then move the evaluated mesh."""
import os, sys, math; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy, bmesh
import numpy as np
import exp
E = exp.Experiment(__file__)


def tube(name="tube", scale=1.0):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    rings, seg = 21, 16
    vs = []
    for k in range(rings):
        z = 2.0 * k / (rings - 1)
        vs.append([bm.verts.new((0.1 * math.cos(2 * math.pi * i / seg), 0.1 * math.sin(2 * math.pi * i / seg), z))
                   for i in range(seg)])
    for k in range(rings - 1):
        for i in range(seg):
            bm.faces.new((vs[k][i], vs[k][(i + 1) % seg], vs[k + 1][(i + 1) % seg], vs[k + 1][i]))
    bm.faces.new(vs[0][::-1]); bm.faces.new(vs[-1])
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    o.scale = (scale,) * 3
    return o


def rig(scale=1.0):
    arm = bpy.data.armatures.new("Rig")
    r = bpy.data.objects.new("Rig", arm)
    bpy.context.scene.collection.objects.link(r)
    bpy.context.view_layer.objects.active = r
    bpy.ops.object.mode_set(mode="EDIT")
    a = arm.edit_bones.new("lower"); a.head = (0, 0, 0); a.tail = (0, 0, 1)
    b = arm.edit_bones.new("upper"); b.head = (0, 0, 1); b.tail = (0, 0, 2); b.parent = a; b.use_connect = True
    bpy.ops.object.mode_set(mode="OBJECT")
    r.scale = (scale,) * 3
    return r


def summary(m):
    groups = [g.name for g in m.vertex_groups]
    w = np.zeros((len(m.data.vertices), max(1, len(groups))))
    for v in m.data.vertices:
        for ge in v.groups:
            w[v.index, ge.group] = ge.weight
    unweighted = int((w.sum(axis=1) == 0).sum())
    return dict(groups=groups, unweighted_points=unweighted, points=len(m.data.vertices),
                modifiers=[(md.type, getattr(md, "object", None) and md.object.name) for md in m.modifiers],
                parent=m.parent.name if m.parent else None, parent_type=m.parent_type)


def run_select(scale=1.0, kind="ARMATURE_AUTO"):
    exp.empty()
    m = tube(scale=scale); r = rig(scale=scale)
    bpy.ops.object.select_all(action="DESELECT")
    m.select_set(True); r.select_set(True)
    bpy.context.view_layer.objects.active = r
    err = None
    try:
        res = list(bpy.ops.object.parent_set(type=kind))
    except Exception as e:
        res, err = None, str(e).strip().splitlines()[0]
    return m, r, res, err


m, r, res, err = run_select()
s = summary(m)
E.fact("parent_set(type='ARMATURE_AUTO') works in background mode with the mesh selected and the armature active "
       "and selected: it adds one vertex group per deforming bone, an Armature modifier, and the parent",
       result=res, error=err, **s)

# the posed, evaluated mesh
pb = r.pose.bones["upper"]
top = [v.index for v in m.data.vertices if v.co.z > 1.99]
before = np.array([m.matrix_world @ m.data.vertices[i].co for i in top]).mean(axis=0)
pb.rotation_mode = "XYZ"
pb.rotation_euler = (math.radians(90), 0, 0)
dg = bpy.context.evaluated_depsgraph_get()
ev = m.evaluated_get(dg)
after = np.array([ev.matrix_world @ ev.data.vertices[i].co for i in top]).mean(axis=0)
orig_after = np.array([m.matrix_world @ m.data.vertices[i].co for i in top]).mean(axis=0)
E.fact("posing the upper bone 90 degrees moves the evaluated mesh's top ring; the original mesh data does not move",
       top_before=np.round(before, 3).tolist(), top_evaluated=np.round(after, 3).tolist(),
       top_original_data=np.round(orig_after, 3).tolist())

# only a context override, nothing selected
exp.empty()
m = tube(); r = rig()
bpy.ops.object.select_all(action="DESELECT")
bpy.context.view_layer.objects.active = None
err = None
try:
    with bpy.context.temp_override(active_object=r, object=r, selected_objects=[m, r], selected_editable_objects=[m, r]):
        res = list(bpy.ops.object.parent_set(type="ARMATURE_AUTO"))
except Exception as e:
    res, err = None, str(e).strip().splitlines()[0]
E.fact("with nothing selected, a temp_override(active_object=rig, selected_editable_objects=[mesh, rig]) is enough "
       "for parent_set ARMATURE_AUTO", result=res, error=err, **summary(m))

# no selection, no override: what goes wrong
exp.empty()
m = tube(); r = rig()
bpy.ops.object.select_all(action="DESELECT")
bpy.context.view_layer.objects.active = r
err = None
try:
    res = list(bpy.ops.object.parent_set(type="ARMATURE_AUTO"))
except Exception as e:
    res, err = None, str(e).strip().splitlines()[0]
E.fact("with the armature active but the mesh not selected, parent_set does nothing to the mesh",
       result=res, error=err, **summary(m))

# bone heat at tiny scale
for sc_ in (0.01, 0.001):
    m, r, res, err = run_select(scale=sc_)
    E.fact(f"automatic weights on the same tube and rig scaled to {sc_} (object scale, not applied)",
           result=res, error=err, **summary(m))

# envelope and empty groups
for kind in ("ARMATURE_ENVELOPE", "ARMATURE_NAME"):
    m, r, res, err = run_select(kind=kind)
    E.fact(f"parent_set type {kind}", result=res, error=err, **summary(m))
E.save()
