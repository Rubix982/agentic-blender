"""A tiny Mantaflow smoke and liquid baked headless in 4.5: what bpy.ops.fluid.bake_all needs in -b, where the cache
goes (the default cache directory, an unsaved file), the files a bake writes, time against resolution, reading the baked
smoke back (openvdb and volume_import), what a REPLAY (default) cache does when frames are stepped, and which changes
invalidate a baked cache."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import shutil
import tempfile
import time

import bmesh
import bpy
import numpy as np
import openvdb
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene
TMP = tempfile.mkdtemp(prefix="bfg-fluid-")
os.chdir(TMP)                   # anything written relative to the working directory lands here


def err(fn):
    try:
        return "ok", fn()
    except Exception as e:  # noqa: BLE001
        return "error", f"{type(e).__name__}: {str(e).strip()[:200]}"


def mesh(name, build, loc=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new(); build(bm); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); ob.location = loc
    scene.collection.objects.link(ob)
    return ob


def files_under(d):
    out = []
    for dp, _, fs in os.walk(d):
        for f in fs:
            out.append(os.path.relpath(os.path.join(dp, f), d))
    return sorted(out)


def size_under(d):
    return sum(os.path.getsize(os.path.join(d, f)) for f in files_under(d))


def scene_setup(kind, res, cache_dir, frames=10):
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    dom = mesh("Domain", lambda bm: bmesh.ops.create_cube(bm, size=2.0))
    md = dom.modifiers.new("Fluid", "FLUID"); md.fluid_type = "DOMAIN"
    ds = md.domain_settings
    defaults = dict(domain_type=ds.domain_type, cache_type=ds.cache_type, cache_directory=ds.cache_directory,
                    data_format=ds.cache_data_format, mesh_format=ds.cache_mesh_format,
                    resolution_max=ds.resolution_max, frame_start=ds.cache_frame_start, frame_end=ds.cache_frame_end,
                    use_mesh=ds.use_mesh)
    ds.domain_type = kind
    ds.resolution_max = res
    ds.cache_frame_start, ds.cache_frame_end = 1, frames
    if cache_dir is not None:
        ds.cache_directory = cache_dir
    if kind == "GAS":
        flow = mesh("Flow", lambda bm: bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.25), loc=(0, 0, -0.6))
        fm = flow.modifiers.new("Fluid", "FLUID"); fm.fluid_type = "FLOW"
        fm.flow_settings.flow_type = "SMOKE"; fm.flow_settings.flow_behavior = "INFLOW"
    else:
        flow = mesh("Flow", lambda bm: bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.4), loc=(0, 0, 0.3))
        fm = flow.modifiers.new("Fluid", "FLUID"); fm.fluid_type = "FLOW"
        fm.flow_settings.flow_type = "LIQUID"; fm.flow_settings.flow_behavior = "GEOMETRY"
    scene.frame_start, scene.frame_end = 1, frames
    scene.frame_set(1)
    return dom, ds, flow, defaults


def bake(dom):
    bpy.context.view_layer.objects.active = dom
    dom.select_set(True)
    t = time.time()
    with bpy.context.temp_override(object=dom, active_object=dom):
        r = err(lambda: bpy.ops.fluid.bake_all())
    return r, round(time.time() - t, 2)


# 1. Defaults, and the bake operator without context.
c1 = os.path.join(TMP, "c1")
dom, ds, flow, defaults = scene_setup("GAS", 16, None)
in_app_tempdir = defaults["cache_directory"].startswith(bpy.app.tempdir)
defaults["cache_directory"] = defaults["cache_directory"].replace(bpy.app.tempdir, "<bpy.app.tempdir>/")
E.fact("a new fluid domain in an unsaved file: GAS, cache type REPLAY, data cached as OpenVDB, resolution 32, frames "
       "1-250; its cache directory is cache_fluid_<hash> inside bpy.app.tempdir (Blender's session temp folder)",
       **defaults, in_app_tempdir=in_app_tempdir, blend_saved=bool(bpy.data.filepath))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(TMP, "scene.blend"))
d2 = mesh("Domain2", lambda bm: bmesh.ops.create_cube(bm, size=1.0))
m2 = d2.modifiers.new("Fluid", "FLUID"); m2.fluid_type = "DOMAIN"
E.fact("in a saved file a new domain's cache directory is relative to the .blend: //cache_fluid_<hash>",
       cache_directory=m2.domain_settings.cache_directory)
bpy.data.objects.remove(d2)
for o in bpy.context.view_layer.objects:
    o.select_set(False)
bpy.context.view_layer.objects.active = None
plain = err(lambda: bpy.ops.fluid.bake_all())
ds.cache_type = "ALL"
c0 = os.path.join(TMP, "c0")
ds.cache_directory = c0
with bpy.context.temp_override(object=dom, active_object=dom):
    only_override = err(lambda: bpy.ops.fluid.bake_all())
only_override_files = len(files_under(c0))
dom, ds, flow, _ = scene_setup("GAS", 16, c1)      # a fresh domain: a baked one does not bake again (fluid_free.py)
ds.cache_type = "ALL"
r, dt = bake(dom)
E.fact("fluid.bake_all fails its poll with no active object; with the domain active (and in a temp_override) it bakes "
       "headless and blocks until done; the override alone (nothing active in the view layer) is enough",
       no_context=plain, override_only=only_override, override_only_files=only_override_files, with_domain=r, seconds=dt,
       has_cache_baked_data=ds.has_cache_baked_data, files=len(files_under(c1)))
tree = files_under(c1)
E.fact("an ALL bake of 10 smoke frames writes a config file (.uni) and an OpenVDB data file per frame, under "
       "<cache>/config and <cache>/data", folders=sorted({f.split(os.sep)[0] for f in tree}),
       examples=tree[:3] + tree[-2:], count=len(tree), bytes=size_under(c1))

# 2. Read the baked smoke back.
vdbs = [os.path.join(c1, f) for f in tree if f.endswith(".vdb") and "data" in f]
last = sorted(vdbs)[-1]
grids, _ = openvdb.readAll(last)
dens = next((g for g in grids if g.name == "density"), None)
E.fact("the last baked frame's .vdb holds the smoke's grids; density has active voxels and a positive maximum",
       file=os.path.relpath(last, c1), grids=sorted(g.name for g in grids),
       density_active=dens.activeVoxelCount() if dens else None,
       density_max=round(float(dens.evalMinMax()[1]), 4) if dens else None)
n0 = set(o.name for o in bpy.data.objects)
imp = err(lambda: bpy.ops.object.volume_import(filepath=last, directory=os.path.dirname(last) + os.sep,
                                               files=[{"name": os.path.basename(last)}]))
new = [o for o in bpy.data.objects if o.name not in n0]
if new:
    new[0].data.grids.load()
E.fact("a baked fluid .vdb imports as a Volume object with volume_import", result=imp,
       grids=sorted(g.name for g in new[0].data.grids) if new else None)

# 3. Time against resolution (smoke and liquid, 10 frames, ALL).
timing = {}
for kind in ("GAS", "LIQUID"):
    for res in (16, 32, 48, 96):
        d = os.path.join(TMP, f"{kind}{res}")
        dom, ds, flow, _ = scene_setup(kind, res, d)
        ds.cache_type = "ALL"
        r, dt = bake(dom)
        info = dict(result=r[1] if r[0] == "ok" else r, seconds=dt, files=len(files_under(d)), bytes=size_under(d))
        if kind == "LIQUID":
            scene.frame_set(10)
            dg = bpy.context.evaluated_depsgraph_get()
            m = dom.evaluated_get(dg).data
            info["liquid_mesh_verts_frame10"] = len(m.vertices)
            info["mesh_files"] = len([f for f in files_under(d) if f.startswith("mesh")])
        timing[f"{kind} {res}"] = info
        print(kind, res, info, flush=True)
        shutil.rmtree(d, ignore_errors=True)
E.fact("bake time and cache size for 10 frames, by resolution_max (smoke inflow; a liquid sphere falling): both grow "
       "with resolution", **timing)
E.fact("after a liquid ALL bake, the domain's evaluated mesh at frame 10 is the liquid surface (with use_mesh on, the "
       "default), not the domain cube's 8 points", liquid32=timing["LIQUID 32"].get("liquid_mesh_verts_frame10"),
       mesh_files=timing["LIQUID 32"].get("mesh_files"))

# 4. REPLAY: stepping frames simulates and caches.
d = os.path.join(TMP, "replay")
dom, ds, flow, _ = scene_setup("GAS", 16, d)
t = time.time()
for f in range(1, 11):
    scene.frame_set(f)
step_s = time.time() - t
replay_files = len(files_under(d))
dom2_jump = None
E.fact("with the default REPLAY cache, stepping frames 1-10 simulates and writes cache files as it goes, with no bake "
       "call", seconds=round(step_s, 2), files=replay_files, has_cache_baked_data=ds.has_cache_baked_data)

# 5. What invalidates a baked (ALL) cache: bake afresh before each change, then read the flag and the files.
d = os.path.join(TMP, "inval")
dom, ds, flow, _ = scene_setup("GAS", 16, d)
ds.cache_type = "ALL"
fs = flow.modifiers["Fluid"].flow_settings


def after(change):
    bake(dom)
    before = (ds.has_cache_baked_data, len(files_under(d)))
    change()
    scene.frame_set(5); scene.frame_set(1)
    return dict(before=before, after=(ds.has_cache_baked_data, len(files_under(d))))


def move_flow():
    flow.location.x += 0.1


def free_all():
    with bpy.context.temp_override(object=dom, active_object=dom):
        bpy.ops.fluid.free_all()


checks = {
    "move the flow object": after(move_flow),
    "flow density": after(lambda: setattr(fs, "density", fs.density * 0.5)),
    "domain vorticity": after(lambda: setattr(ds, "vorticity", ds.vorticity + 0.1)),
    "domain resolution_max": after(lambda: setattr(ds, "resolution_max", ds.resolution_max + 2)),
    "domain cache_frame_end": after(lambda: setattr(ds, "cache_frame_end", ds.cache_frame_end + 1)),
    "fluid.free_all": after(free_all),
}
E.fact("after an ALL bake ((has_cache_baked_data, file count) before and after each change, baked afresh each time): "
       "moving the flow object, changing its density or the domain's cache_frame_end keeps the bake; setting the "
       "domain's vorticity or resolution_max from Python clears the flag and deletes the cache files, as does free_all",
       **checks)
shutil.rmtree(TMP, ignore_errors=True)
E.save(timing=timing)
