"""What fluid.free_all and a second fluid.bake_all do in background mode (4.5): after a bake, does free_all delete the
files and clear the baked flag at once, does bake_all on an already-baked domain bake again, and does pointing the
domain at a new cache directory make it bake again."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import shutil
import tempfile
import time

import bmesh
import bpy
import exp

E = exp.Experiment(__file__)
scene = bpy.context.scene
TMP = tempfile.mkdtemp(prefix="bfg-fluidfree-")
os.chdir(TMP)


def mesh(name, build, loc=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new(); build(bm); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); ob.location = loc
    scene.collection.objects.link(ob)
    return ob


def count(d):
    return sum(len(fs) for _, _, fs in os.walk(d)) if os.path.isdir(d) else 0


dom = mesh("Domain", lambda bm: bmesh.ops.create_cube(bm, size=2.0))
md = dom.modifiers.new("Fluid", "FLUID"); md.fluid_type = "DOMAIN"
ds = md.domain_settings
ds.resolution_max = 16; ds.cache_frame_start, ds.cache_frame_end = 1, 10; ds.cache_type = "ALL"
flow = mesh("Flow", lambda bm: bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.25), loc=(0, 0, -0.6))
fm = flow.modifiers.new("Fluid", "FLUID"); fm.fluid_type = "FLOW"
fm.flow_settings.flow_type = "SMOKE"; fm.flow_settings.flow_behavior = "INFLOW"
scene.frame_start, scene.frame_end = 1, 10
a = os.path.join(TMP, "a"); b = os.path.join(TMP, "b")
ds.cache_directory = a


def op(name):
    t = time.time()
    with bpy.context.temp_override(object=dom, active_object=dom):
        r = getattr(bpy.ops.fluid, name)()
    return dict(ret=str(r), seconds=round(time.time() - t, 3), baked=ds.has_cache_baked_data,
                baking=ds.is_cache_baking_any, files_a=count(a), files_b=count(b))


steps = {}
steps["1 bake_all"] = op("bake_all")
steps["2 bake_all again"] = op("bake_all")
steps["3 free_all"] = op("free_all")
scene.frame_set(2); scene.frame_set(1)
steps["4 after frame_set"] = dict(baked=ds.has_cache_baked_data, files_a=count(a))
steps["5 bake_all after free"] = op("bake_all")
ds.cache_directory = b
steps["6 bake_all with a new cache_directory"] = op("bake_all")
for k, v in steps.items():
    print(k, v, flush=True)
E.fact("in background mode: a first bake_all writes 20 files; bake_all on an already-baked domain returns FINISHED "
       "without baking again; free_all returns at once while has_cache_baked_data still reads True and the files are "
       "still on disk (19 or 20 of them in two runs), and both had settled (False, 0 files) after a frame_set; a "
       "bake_all then bakes all 20 again; "
       "pointing a baked domain at a new cache_directory and calling bake_all writes only 2 files there", **steps)
shutil.rmtree(TMP, ignore_errors=True)
E.save()
