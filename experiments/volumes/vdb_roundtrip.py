"""OpenVDB files in and out of 4.5: saving an evaluated volume with VolumeGrids.save, reading the file with the bundled
openvdb module, importing it back with bpy.ops.object.volume_import headless or through the data API (volume.filepath),
writing a VDB from scratch with openvdb and meshing it (the grid-name trap), and a numbered file sequence."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import shutil

import bmesh
import bpy
import numpy as np
import openvdb
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene
d = E.out("vdb")
shutil.rmtree(d, ignore_errors=True)
os.makedirs(d)


def err(fn):
    try:
        return "ok", fn()
    except Exception as e:  # noqa: BLE001
        return "error", f"{type(e).__name__}: {str(e).strip()[:200]}"


me = bpy.data.meshes.new("Src")
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=1.0); bm.to_mesh(me); bm.free()
src = bpy.data.objects.new("Src", me); scene.collection.objects.link(src)
vol = bpy.data.volumes.new("Vol"); vo = bpy.data.objects.new("Vol", vol); scene.collection.objects.link(vo)
m2v = vo.modifiers.new("M2V", "MESH_TO_VOLUME"); m2v.object = src

# 1. Save the evaluated volume.
path = os.path.join(d, "sphere.vdb")
orig = err(lambda: vol.grids.save(os.path.join(d, "orig.vdb")))
dg = bpy.context.evaluated_depsgraph_get()
ve = vo.evaluated_get(dg).data
saved = err(lambda: ve.grids.save(path))
orig_grids = len(openvdb.readAll(os.path.join(d, "orig.vdb"))[0]) if os.path.exists(os.path.join(d, "orig.vdb")) else None
E.fact("VolumeGrids.save(filepath) writes a .vdb from the evaluated volume (the modifier's result); on the original "
       "data-block it also returns True and writes a file, but one with no grids in it",
       evaluated=saved, evaluated_bytes=os.path.getsize(path) if os.path.exists(path) else 0,
       original=orig, original_file=os.path.exists(os.path.join(d, "orig.vdb")), original_file_grids=orig_grids)

# 2. Read it with openvdb.
grids, meta = openvdb.readAll(path)
g = grids[0]
acc = g.getConstAccessor()
centre_ijk = tuple(int(round(x)) for x in g.transform.worldToIndex((0.0, 0.0, 0.0)))
E.fact("the bundled openvdb module reads the saved file: one FloatGrid 'density', its active voxel count, value range, "
       "voxel size, and 1.0 at the sphere's centre",
       grids=[(x.name, type(x).__name__) for x in grids], active_voxels=g.activeVoxelCount(),
       min_max=[round(float(v), 4) for v in g.evalMinMax()], voxel_size=[round(v, 5) for v in g.transform.voxelSize()],
       centre_value=round(float(acc.getValue(centre_ijk)), 4), grid_class=str(g.gridClass),
       file_metadata=sorted(meta.keys()) if hasattr(meta, "keys") else str(meta))

# 3. Import it back: the operator, headless.
n0 = len(bpy.data.objects)
imp = err(lambda: bpy.ops.object.volume_import(filepath=path, directory=d + os.sep, files=[{"name": "sphere.vdb"}]))
new = [o for o in bpy.data.objects if o.type == "VOLUME" and o.name not in ("Vol",)]
iv = new[0].data if new else None
if iv:
    iv.grids.load()
E.fact("bpy.ops.object.volume_import runs headless (no override) and makes a Volume object whose grids load from the "
       "file", result=imp, objects_added=len(bpy.data.objects) - n0,
       grids=[(x.name, x.data_type) for x in iv.grids] if iv else None,
       is_sequence=iv.is_sequence if iv else None, filepath=os.path.basename(iv.filepath) if iv else None)

# The data API route.
v2 = bpy.data.volumes.new("ByPath")
v2.filepath = path
before_load = (v2.grids.is_loaded, len(v2.grids))
ok = v2.grids.load()
E.fact("the data API route: volumes.new + volume.filepath; the grids are listed only after grids.load(); grid.load() "
       "returns True, yet that grid's is_loaded still reads False on the original data-block", before_load=before_load, load_ok=ok,
       after=[(x.name, x.data_type, x.is_loaded) for x in v2.grids],
       grid_load=err(lambda: v2.grids[0].load()), grid_loaded_after=v2.grids[0].is_loaded,
       error_message=v2.grids.error_message)
bad = bpy.data.volumes.new("Bad"); bad.filepath = os.path.join(d, "missing.vdb")
E.fact("a missing file does not raise: grids.load() returns False and grids.error_message says why",
       load=bad.grids.load(), error_message=bad.grids.error_message)

# 4. A level set written from scratch with openvdb, then meshed in Blender.
ls = openvdb.createLevelSetSphere(radius=0.8, center=(0, 0, 0), voxelSize=0.04, halfWidth=3.0)
ls.name = "surface"
ls_path = os.path.join(d, "ls.vdb")
openvdb.write(ls_path, grids=[ls])
lv = bpy.data.volumes.new("LS"); lv.filepath = ls_path
lo = bpy.data.objects.new("LS", lv); scene.collection.objects.link(lo)
mm = bpy.data.objects.new("LSMesh", bpy.data.meshes.new("LSMesh")); scene.collection.objects.link(mm)
v2m = mm.modifiers.new("V2M", "VOLUME_TO_MESH"); v2m.object = lo


def stats():
    dg = bpy.context.evaluated_depsgraph_get()
    m = mm.evaluated_get(dg).data
    if not len(m.vertices):
        return dict(verts=0)
    c = np.empty(len(m.vertices) * 3, np.float32); m.vertices.foreach_get("co", c)
    r = np.linalg.norm(c.reshape(-1, 3), axis=1)
    return dict(verts=len(m.vertices), r_mean=round(float(r.mean()), 4))


default_name = v2m.grid_name
s_default = stats()
v2m.grid_name = "surface"
s_named = stats()
v2m.threshold = 0.0
s_zero = stats()
E.fact("a level set written with openvdb (grid 'surface', radius 0.8) loads in Blender; Volume to Mesh reads the grid "
       "named in grid_name ('density' by default), so it returns nothing until grid_name is set; at threshold 0 the "
       "surface sits at the level set's radius (0.800), at the default 0.1 it sits 0.1 m further out (0.900)",
       grid_names=[(x.name, x.data_type) for x in lv.grids], default_grid_name=default_name, default=s_default,
       named_threshold_0_1=s_named, named_threshold_0=s_zero)

# 5. A numbered sequence.
for i in (1, 2, 3):
    shutil.copy(path, os.path.join(d, f"seq_{i:04d}.vdb"))
n0 = set(o.name for o in bpy.data.objects)
r = err(lambda: bpy.ops.object.volume_import(filepath=os.path.join(d, "seq_0001.vdb"), directory=d + os.sep,
                                             files=[{"name": f"seq_{i:04d}.vdb"} for i in (1, 2, 3)]))
so = [o for o in bpy.data.objects if o.name not in n0]
sv = so[0].data if so else None
frames = {}
if sv:
    for f in (1, 2, 3, 5):
        scene.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        frames[f] = os.path.basename(so[0].evaluated_get(dg).data.grids.frame_filepath)
E.fact("importing numbered files (seq_0001..0003.vdb) as one selection makes one Volume object that is a sequence of "
       "3 frames; each frame loads its own file, and past the end (frame 5) none loads (sequence_mode CLIP)",
       result=r, objects=len(so), is_sequence=sv.is_sequence if sv else None,
       frame_duration=sv.frame_duration if sv else None, sequence_mode=sv.sequence_mode if sv else None,
       frame_files=frames)
shutil.rmtree(d)
E.save()
