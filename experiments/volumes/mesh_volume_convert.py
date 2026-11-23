"""Mesh to volume and back in 4.5, two ways: the Mesh to Volume modifier (on a Volume object) and the Volume to Mesh
modifier (on a mesh object), and the geometry-nodes Mesh to Volume / Volume to Mesh nodes; also the newer SDF grid
nodes (Mesh to SDF Grid, Grid to Mesh). What a new modifier starts with (it differs from the registered defaults kb.py
shows), what the evaluated volume holds (grid names, types, voxel size), how close the round trip comes to the sphere,
and the time and size against resolution. Also whether Blender's Python can read voxels at all (pyopenvdb/openvdb)."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import importlib
import time

import bmesh
import bpy
import numpy as np
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene


def err(fn):
    try:
        return "ok", fn()
    except Exception as e:  # noqa: BLE001
        return "error", f"{type(e).__name__}: {str(e).strip()[:200]}"


me = bpy.data.meshes.new("Src")
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=64, v_segments=32, radius=1.0); bm.to_mesh(me); bm.free()
src = bpy.data.objects.new("Src", me)
scene.collection.objects.link(src)

vol = bpy.data.volumes.new("Vol")
vo = bpy.data.objects.new("Vol", vol)
scene.collection.objects.link(vo)
m2v = vo.modifiers.new("M2V", "MESH_TO_VOLUME")
E.fact("a new Mesh to Volume modifier starts at VOXEL_AMOUNT 32 (voxel size 0.1 unused), density 1, interior band "
       "0.2; kb.py's registered defaults read 0 for all four",
       resolution_mode=m2v.resolution_mode, voxel_amount=m2v.voxel_amount, voxel_size=m2v.voxel_size,
       density=m2v.density, interior_band_width=m2v.interior_band_width)
m2v.object = src


def grids(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    v = obj.evaluated_get(dg).data
    out = []
    for g in v.grids:
        m = np.array(g.matrix_object).reshape(4, 4) if len(g.matrix_object) == 16 else np.array(g.matrix_object)
        out.append(dict(name=g.name, data_type=g.data_type, channels=g.channels, is_loaded=g.is_loaded,
                        voxel=round(float(np.linalg.norm(np.array(m)[:3, 0])), 5)))
    return out


t = time.time()
g = grids(vo)
dt = time.time() - t
E.fact("the evaluated Volume object holds one FLOAT grid named 'density'; at amount 32 on a 2 m sphere the voxel is "
       "0.108 m, the bounding box's diagonal (3.46 m) / 32", grids=g, seconds=round(dt, 3))
E.fact("the Volume data-block itself (not evaluated) has no grids: the modifier's result lives on the evaluated copy",
       original_grids=len(vol.grids), evaluated_grids=len(g))

back_me = bpy.data.meshes.new("Back")
back = bpy.data.objects.new("Back", back_me)
scene.collection.objects.link(back)
v2m = back.modifiers.new("V2M", "VOLUME_TO_MESH")
E.fact("a new Volume to Mesh modifier starts at resolution GRID (the volume's own voxels), threshold 0.1, adaptivity 0",
       resolution_mode=v2m.resolution_mode, threshold=v2m.threshold, adaptivity=v2m.adaptivity,
       grid_name=v2m.grid_name, voxel_amount=v2m.voxel_amount)
v2m.object = vo


def mesh_stats(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    m = obj.evaluated_get(dg).data
    n = len(m.vertices)
    if n == 0:
        return dict(verts=0)
    c = np.empty(n * 3, np.float32); m.vertices.foreach_get("co", c); c = c.reshape(-1, 3)
    r = np.linalg.norm(c, axis=1)
    return dict(verts=n, faces=len(m.polygons), r_mean=round(float(r.mean()), 4), r_min=round(float(r.min()), 4),
                r_max=round(float(r.max()), 4))


res = {}
for amount in (16, 32, 64, 128):
    m2v.voxel_amount = amount
    t = time.time()
    st = mesh_stats(back)
    res[amount] = dict(seconds=round(time.time() - t, 3), voxel=grids(vo)[0]["voxel"], **st)
    print("amount", amount, res[amount], flush=True)
E.fact("modifier round trip sphere -> volume -> mesh, by voxel amount: the voxel is the bounding-box diagonal / amount; "
       "points out grow about 4x per doubling; the result's radius settles near 0.979 (the sphere's is 1)", by_amount=res)

m2v.voxel_amount = 64
for th in (0.1, 0.5, 0.9):
    v2m.threshold = th
    res[f"threshold {th}"] = mesh_stats(back)
E.fact("the surface Volume to Mesh returns sits about threshold x interior band width inside the mesh (band 0.2: "
       "radius 0.979, 0.898, 0.817 at threshold 0.1, 0.5, 0.9)", **{k: v for k, v in res.items() if str(k).startswith("threshold")})
v2m.threshold = 0.1
m2v.interior_band_width = 0.05
thin = mesh_stats(back)
m2v.interior_band_width = 0.2
E.fact("a narrower interior band moves the returned surface out to the mesh's: band 0.05 gives radius 1.000 against "
       "0.979 at band 0.2 (threshold 0.1, amount 64)",
       band_0_05=thin, band_0_2=res[64])
for o in (vo, back):
    o.hide_viewport = True

# ---- geometry nodes: the same round trip in one node tree, and with the SDF grid nodes.
def gn_object(name, build):
    m = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, m)
    scene.collection.objects.link(ob)
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    out = ng.nodes.new("NodeGroupOutput")
    oi = ng.nodes.new("GeometryNodeObjectInfo")
    oi.inputs["Object"].default_value = src
    last = build(ng, oi.outputs["Geometry"])
    ng.links.new(last, out.inputs[0])
    md = ob.modifiers.new("GN", "NODES"); md.node_group = ng
    return ob, ng


def nodes_roundtrip(ng, geo):
    a = ng.nodes.new("GeometryNodeMeshToVolume")
    b = ng.nodes.new("GeometryNodeVolumeToMesh")
    ng.links.new(geo, a.inputs["Mesh"]); ng.links.new(a.outputs["Volume"], b.inputs["Volume"])
    return b.outputs["Mesh"]


ob1, ng1 = gn_object("GNRound", nodes_roundtrip)
t = time.time(); gn = mesh_stats(ob1); gn_s = time.time() - t
m2v_node = next(n for n in ng1.nodes if n.bl_idname == "GeometryNodeMeshToVolume")
E.fact("geometry nodes Mesh to Volume -> Volume to Mesh (node defaults: amount 64, density 1, band 0.2, threshold 0.1) "
       "gives the same round trip as the two modifiers", seconds=round(gn_s, 3), mode=m2v_node.resolution_mode, **gn)


def sdf_roundtrip(ng, geo):
    a = ng.nodes.new("GeometryNodeMeshToSDFGrid")
    a.inputs["Voxel Size"].default_value = 2 / 64
    b = ng.nodes.new("GeometryNodeGridToMesh")
    b.inputs["Threshold"].default_value = 0.0
    ng.links.new(geo, a.inputs["Mesh"]); ng.links.new(a.outputs["SDF Grid"], b.inputs["Grid"])
    return b.outputs["Mesh"]


made = err(lambda: gn_object("GNSdf", sdf_roundtrip))
sdf = mesh_stats(made[1][0]) if made[0] == "ok" else None
E.fact("the SDF grid nodes (Mesh to SDF Grid, voxel 2/64 m -> Grid to Mesh at threshold 0) build and evaluate headless "
       "in 4.5, and the surface they return sits on the sphere", made=made[0] if made[0] == "ok" else made, sdf=sdf)

# Volume object with a geometry-nodes Volume Cube: grids on the evaluated volume.
vol2 = bpy.data.volumes.new("Cube"); vo2 = bpy.data.objects.new("Cube", vol2); scene.collection.objects.link(vo2)
ng = bpy.data.node_groups.new("VC", "GeometryNodeTree")
ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
vc = ng.nodes.new("GeometryNodeVolumeCube"); o = ng.nodes.new("NodeGroupOutput")
ng.links.new(vc.outputs["Volume"], o.inputs[0])
md = vo2.modifiers.new("GN", "NODES"); md.node_group = ng
E.fact("a Volume object whose geometry nodes output a Volume Cube evaluates to one FLOAT grid named 'density' at the "
       "node's resolution (32 -> voxel 2/31 m across -1..1)", grids=grids(vo2))

# Can Python read voxels? openvdb / pyopenvdb modules.
mods = {}
for name in ("openvdb", "pyopenvdb"):
    try:
        m = importlib.import_module(name)
        mods[name] = dict(ok=True, file=os.path.basename(getattr(m, "__file__", "") or ""),
                          has_read=hasattr(m, "read"), has_write=hasattr(m, "write"),
                          version=str(getattr(m, "LIBRARY_VERSION", getattr(m, "__version__", ""))))
    except Exception as e:  # noqa: BLE001
        mods[name] = dict(ok=False, error=f"{type(e).__name__}: {str(e)[:120]}")
E.fact("Blender 4.5's Python can import the OpenVDB module (openvdb), so voxel values can be read and written from a "
       "script; bpy itself exposes only grid metadata", **mods)
E.save(results=res)
