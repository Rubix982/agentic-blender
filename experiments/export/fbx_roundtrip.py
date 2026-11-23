"""FBX in 4.5: which operators exist, and what a round trip of a skinned mesh with a material brings back through each
importer (the add-on's import_scene.fbx and the new C++ wm.fbx_import), with the exporter's defaults.

Source: an armature "Rig" at (1, 2, 0), rotated 30 degrees about Z, with two connected bones (root 0..1 m, arm
1..2 m up Z, arm rolled 30 degrees); a tube "Body" (0.2 m radius, 2 m tall, 336 points) skinned to it with automatic
weights; material "Red" (base colour 0.8, 0.05, 0.05, roughness 0.3, metallic 0.5). Compared: object transforms, the
mesh's world-space points (nearest-point distance to the source), bones in world space, weights, the material, and the
deformed mesh after the same pose."""
import math
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bmesh  # noqa: E402
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix, Vector, kdtree  # noqa: E402

import exp  # noqa: E402

E = exp.Experiment(__file__)
TMP = tempfile.mkdtemp(prefix="bfg-fbx-")
FBX = os.path.join(TMP, "rig.fbx")

ops = {}
for mod, op in (("export_scene", "fbx"), ("import_scene", "fbx"), ("wm", "fbx_import"), ("wm", "fbx_export")):
    try:
        getattr(getattr(bpy.ops, mod), op).get_rna_type()
        ops[f"{mod}.{op}"] = True
    except (AttributeError, KeyError):
        ops[f"{mod}.{op}"] = False
label = {}
for name in ("import_scene.fbx", "wm.fbx_import", "export_scene.fbx"):
    if ops[name]:
        mod, op = name.split(".")
        label[name] = getattr(getattr(bpy.ops, mod), op).get_rna_type().name
E.fact("FBX operators in 4.5: export_scene.fbx and import_scene.fbx (the bundled add-on) and wm.fbx_import (labelled "
       "'Import FBX (experimental)'); there is no wm.fbx_export", present=ops, labels=label)


def build():
    exp.empty()
    scene = bpy.context.scene
    arm = bpy.data.armatures.new("Rig")
    rig = bpy.data.objects.new("Rig", arm)
    scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    a = arm.edit_bones.new("root"); a.head = (0, 0, 0); a.tail = (0, 0, 1)
    b = arm.edit_bones.new("arm"); b.head = (0, 0, 1); b.tail = (0, 0, 2); b.parent = a; b.use_connect = True
    b.roll = math.radians(30)
    bpy.ops.object.mode_set(mode="OBJECT")
    rig.location = (1, 2, 0)
    rig.rotation_euler = (0, 0, math.radians(30))
    me = bpy.data.meshes.new("Body")
    bm = bmesh.new()
    rings, seg = 21, 16
    vs = [[bm.verts.new((0.2 * math.cos(2 * math.pi * i / seg), 0.2 * math.sin(2 * math.pi * i / seg), 2.0 * k / (rings - 1)))
           for i in range(seg)] for k in range(rings)]
    for k in range(rings - 1):
        for i in range(seg):
            bm.faces.new((vs[k][i], vs[k][(i + 1) % seg], vs[k + 1][(i + 1) % seg], vs[k + 1][i]))
    bm.faces.new(vs[0][::-1]); bm.faces.new(vs[-1])
    bm.to_mesh(me); bm.free()
    body = bpy.data.objects.new("Body", me)
    scene.collection.objects.link(body)
    body.location = (1, 2, 0)
    body.rotation_euler = (0, 0, math.radians(30))
    m = bpy.data.materials.new("Red")
    m.use_nodes = True
    p = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    p.inputs["Base Color"].default_value = (0.8, 0.05, 0.05, 1)
    p.inputs["Roughness"].default_value = 0.3
    p.inputs["Metallic"].default_value = 0.5
    me.materials.append(m)
    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True); rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    bpy.context.view_layer.update()
    return rig, body


def world_points(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    mw = np.array(ev.matrix_world)
    co = np.zeros(len(ev.data.vertices) * 3, np.float32)
    ev.data.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    return co @ mw[:3, :3].T + mw[:3, 3]


def nearest_max(a, b):
    kd = kdtree.KDTree(len(b))
    for i, p in enumerate(b):
        kd.insert(Vector(p), i)
    kd.balance()
    return round(max(kd.find(Vector(p))[2] for p in a), 5)


def bones_world(rig):
    out = {}
    for bn in rig.data.bones:
        mw = rig.matrix_world @ bn.matrix_local
        out[bn.name] = dict(head=[round(x, 4) for x in rig.matrix_world @ bn.head_local],
                            tail=[round(x, 4) for x in rig.matrix_world @ bn.tail_local],
                            z_axis=[round(x, 3) for x in mw.to_3x3().col[2]])
    return out


def pose_top(rig, body, bone="arm"):
    pb = rig.pose.bones[bone]
    pb.rotation_mode = "XYZ"
    pb.rotation_euler = (math.radians(60), 0, 0)
    bpy.context.view_layer.update()
    pts = world_points(body)
    pb.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()
    return pts


rig, body = build()
src_pts = world_points(body)
src_bones = bones_world(rig)
src_groups = sorted(g.name for g in body.vertex_groups)
src_posed = pose_top(rig, body)
defaults = {k: getattr(bpy.ops.export_scene.fbx.get_rna_type().properties[k], "default", None)
            for k in ("global_scale", "apply_unit_scale", "apply_scale_options", "axis_forward", "axis_up",
                      "add_leaf_bones", "primary_bone_axis", "secondary_bone_axis", "bake_anim", "mesh_smooth_type")}
r = bpy.ops.export_scene.fbx(filepath=FBX)
E.fact("export_scene.fbx with its defaults wrote the file", result=list(r), defaults=defaults,
       size_kb=round(os.path.getsize(FBX) / 1024, 1))


def summary(importer):
    exp.empty()
    try:
        if importer == "import_scene.fbx":
            res = list(bpy.ops.import_scene.fbx(filepath=FBX))
        else:
            res = list(bpy.ops.wm.fbx_import(filepath=FBX))
    except Exception as e:  # noqa: BLE001
        return dict(error=str(e).splitlines()[0][:300])
    bpy.context.view_layer.update()
    objs = {o.name: dict(type=o.type, parent=o.parent.name if o.parent else None,
                         location=[round(x, 4) for x in o.location],
                         rotation_deg=[round(math.degrees(x), 2) for x in o.rotation_euler],
                         scale=[round(x, 4) for x in o.scale]) for o in bpy.data.objects}
    out = dict(result=res, objects=objs)
    rigs = [o for o in bpy.data.objects if o.type == "ARMATURE"]
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    if meshes:
        b = meshes[0]
        pts = world_points(b)
        out["mesh"] = dict(points=len(pts), max_dist_to_source_m=nearest_max(pts, src_pts),
                           vertex_groups=sorted(g.name for g in b.vertex_groups),
                           modifiers=[(md.type, md.object.name if getattr(md, "object", None) else None) for md in b.modifiers],
                           unweighted=int(sum(1 for v in b.data.vertices if not any(g.weight > 0 for g in v.groups))))
        mats = []
        for m in b.data.materials:
            d = dict(name=m.name, use_nodes=m.use_nodes)
            if m.use_nodes:
                p = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
                if p:
                    d.update(base_color=[round(x, 4) for x in p.inputs["Base Color"].default_value[:3]],
                             roughness=round(p.inputs["Roughness"].default_value, 4),
                             metallic=round(p.inputs["Metallic"].default_value, 4))
            mats.append(d)
        out["materials"] = mats
    if rigs:
        rg = rigs[0]
        bw = bones_world(rg)
        out["bones"] = bw
        common = [n for n in src_bones if n in bw]
        out["bone_max_head_tail_error_m"] = round(max(
            max(np.abs(np.array(bw[n]["head"]) - src_bones[n]["head"]).max(),
                np.abs(np.array(bw[n]["tail"]) - src_bones[n]["tail"]).max()) for n in common), 5) if common else None
        out["bone_roll_axis_error_deg"] = {n: round(math.degrees(Vector(bw[n]["z_axis"]).angle(Vector(src_bones[n]["z_axis"]))), 2)
                                           for n in common}
        if meshes and "arm" in rg.pose.bones:
            posed = pose_top(rg, meshes[0])
            out["posed_max_dist_to_source_posed_m"] = nearest_max(posed, src_posed)
    return out


for imp in ("import_scene.fbx", "wm.fbx_import"):
    s = summary(imp)
    E.fact(f"Round trip through export_scene.fbx and {imp} (defaults): what came back", **s)

# leaf bones: off at export, or ignored at import
rig, body = build()
bpy.ops.export_scene.fbx(filepath=FBX, add_leaf_bones=False)
leaf = {}
for imp in ("import_scene.fbx", "wm.fbx_import"):
    exp.empty()
    (bpy.ops.import_scene.fbx if imp == "import_scene.fbx" else bpy.ops.wm.fbx_import)(filepath=FBX)
    leaf[f"add_leaf_bones=False, {imp}"] = sorted(b.name for o in bpy.data.objects if o.type == "ARMATURE" for b in o.data.bones)
rig, body = build()
bpy.ops.export_scene.fbx(filepath=FBX)
for imp in ("import_scene.fbx", "wm.fbx_import"):
    exp.empty()
    (bpy.ops.import_scene.fbx if imp == "import_scene.fbx" else bpy.ops.wm.fbx_import)(filepath=FBX, ignore_leaf_bones=True)
    leaf[f"default export, {imp}(ignore_leaf_bones=True)"] = sorted(
        b.name for o in bpy.data.objects if o.type == "ARMATURE" for b in o.data.bones)
E.fact("The exporter adds a leaf bone ('arm_end') at the end of each chain by default; add_leaf_bones=False at export, "
       "or ignore_leaf_bones=True at import (both importers have it), gives back the two bones", **leaf)

# speed: a 400 x 400 grid (160,801 points) with a material
exp.empty()
bpy.ops.mesh.primitive_grid_add(x_subdivisions=400, y_subdivisions=400, size=4)
g = bpy.context.object
g.data.materials.append(bpy.data.materials.new("M"))
import time  # noqa: E402
t = time.time()
bpy.ops.export_scene.fbx(filepath=FBX)
t_exp = time.time() - t
times = {}
for imp in ("import_scene.fbx", "wm.fbx_import"):
    exp.empty()
    t = time.time()
    (bpy.ops.import_scene.fbx if imp == "import_scene.fbx" else bpy.ops.wm.fbx_import)(filepath=FBX)
    times[imp] = dict(seconds=round(time.time() - t, 3),
                      points=[len(o.data.vertices) for o in bpy.data.objects if o.type == "MESH"])
E.fact("On a 160,801-point grid the C++ importer wm.fbx_import was faster than import_scene.fbx", export_s=round(t_exp, 3),
       file_mb=round(os.path.getsize(FBX) / 2 ** 20, 1), **times)

for f in os.listdir(TMP):
    os.remove(os.path.join(TMP, f))
os.rmdir(TMP)
E.save(source=dict(bones=src_bones, groups=src_groups, points=len(src_pts)), pose_arm_x_deg=60)
