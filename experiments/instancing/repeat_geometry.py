"""Repeating geometry in 4.5: full copies, linked duplicates (shared mesh), collection instances, vertex instancing and
a legacy particle system; what each costs to create, what the depsgraph reports, the .blend size, and how instances are
made real headless. Also hair curves from Python, point clouds, and assets (marking, and Blender's bundled ones)."""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bmesh  # noqa: E402
import bpy  # noqa: E402
import numpy as np  # noqa: E402

import exp  # noqa: E402

E = exp.Experiment(__file__)
N = 2000


def unit_mesh(name, segments=32):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=segments // 2, radius=0.1)
    bm.to_mesh(me)
    bm.free()
    return me


def blend_size(label):
    path = E.out(f"{label}.blend")
    bpy.ops.wm.save_as_mainfile(filepath=path, compress=False)
    size = os.path.getsize(path)
    os.remove(path)
    return round(size / 2**20, 2)


def instance_count():
    dg = bpy.context.evaluated_depsgraph_get()
    return sum(1 for i in dg.object_instances if i.is_instance), sum(1 for i in dg.object_instances if not i.is_instance)


rows = {}
sc = bpy.context.scene
grid = [((i % 50) * 0.3, (i // 50) * 0.3, 0.0) for i in range(N)]

# a) full copies: every object its own mesh
src = unit_mesh("ball")
t = time.time()
for p in grid:
    o = bpy.data.objects.new("full", src.copy())
    o.location = p
    sc.collection.objects.link(o)
bpy.context.view_layer.update()
rows["full copies"] = dict(create_s=round(time.time() - t, 3), meshes=len(bpy.data.meshes), mb=blend_size("full"))
exp.empty()

# b) linked duplicates: objects share one mesh
src = unit_mesh("ball")
t = time.time()
for p in grid:
    o = bpy.data.objects.new("linked", src)
    o.location = p
    sc = bpy.context.scene
    sc.collection.objects.link(o)
bpy.context.view_layer.update()
rows["linked duplicates (shared mesh)"] = dict(create_s=round(time.time() - t, 3), meshes=len(bpy.data.meshes),
                                               mb=blend_size("linked"))
exp.empty()

# c) collection instances: empties that instance a collection
sc = bpy.context.scene
src = unit_mesh("ball")
coll = bpy.data.collections.new("Ball")
ball = bpy.data.objects.new("Ball", src)
coll.objects.link(ball)          # a collection not linked to the scene: its objects are not drawn themselves
t = time.time()
for p in grid:
    e = bpy.data.objects.new("inst", None)
    e.instance_type = "COLLECTION"
    e.instance_collection = coll
    e.location = p
    sc.collection.objects.link(e)
bpy.context.view_layer.update()
inst, real = instance_count()
rows["collection instances (empties)"] = dict(create_s=round(time.time() - t, 3), meshes=len(bpy.data.meshes),
                                              mb=blend_size("coll"), depsgraph_instances=inst, depsgraph_objects=real)

# make them real, headless
for o in sc.objects:
    o.select_set(o.name.startswith("inst"))
bpy.context.view_layer.objects.active = next(o for o in sc.objects if o.name.startswith("inst"))
t = time.time()
r = bpy.ops.object.duplicates_make_real()
made = sum(1 for o in sc.objects if o.type == "MESH")
E.fact("object.duplicates_make_real works headless on the selected instancers; the objects it makes share one mesh "
       "(linked duplicates)", result=str(r), seconds=round(time.time() - t, 3), mesh_objects=made,
       meshes=len(bpy.data.meshes))
exp.empty()

# d) vertex instancing: a mesh's vertices carry a child object
sc = bpy.context.scene
pts = bpy.data.meshes.new("points")
pts.from_pydata(grid, [], [])
parent = bpy.data.objects.new("Points", pts)
sc.collection.objects.link(parent)
child = bpy.data.objects.new("Ball", unit_mesh("ball"))
sc.collection.objects.link(child)
child.parent = parent
t = time.time()
parent.instance_type = "VERTS"
bpy.context.view_layer.update()
inst, real = instance_count()
rows["vertex instancing (one parent mesh)"] = dict(create_s=round(time.time() - t, 3), meshes=len(bpy.data.meshes),
                                                    mb=blend_size("verts"), depsgraph_instances=inst,
                                                    depsgraph_objects=real, child_drawn_itself=child.visible_get())
exp.empty()

# e) a legacy particle system rendering an object
sc = bpy.context.scene
me = bpy.data.meshes.new("plane")
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=10, y_segments=10, size=7.5)
bm.to_mesh(me)
bm.free()
emitter = bpy.data.objects.new("Emitter", me)
sc.collection.objects.link(emitter)
ball = bpy.data.objects.new("Ball", unit_mesh("ball"))
sc.collection.objects.link(ball)
t = time.time()
mod = emitter.modifiers.new("Scatter", "PARTICLE_SYSTEM")
ps = mod.particle_system.settings
ps.type = "HAIR"           # hair particles are placed at once; emitter particles need the frames to run
ps.count = N
ps.hair_length = 1.0
ps.render_type = "OBJECT"
ps.instance_object = ball
bpy.context.view_layer.update()
inst, real = instance_count()
dg = bpy.context.evaluated_depsgraph_get()
ev = emitter.evaluated_get(dg)
parts = ev.particle_systems[0].particles
locs = [tuple(p.location) for p in parts][:3]
roots = [tuple(p.hair_keys[0].co) for p in parts][:3] if len(parts[0].hair_keys) else None
tips = [tuple(p.hair_keys[-1].co) for p in parts][:3] if len(parts[0].hair_keys) else None
rows["particle system (hair, render as object)"] = dict(create_s=round(time.time() - t, 3), meshes=len(bpy.data.meshes),
                                                        mb=blend_size("particles"), depsgraph_instances=inst,
                                                        depsgraph_objects=real, particles=len(ev.particle_systems[0].particles))
E.fact("Five ways to put 2000 copies of a 32 x 16 sphere in a scene: creation time from Python, meshes in the file, "
       "uncompressed .blend size, and what the depsgraph reports (instances are not objects)", **rows)
E.fact("A legacy particle system's particles are read from the evaluated object "
       "(obj.evaluated_get(depsgraph).particle_systems[0].particles). For hair, particle.location is the strand's tip "
       "(z = 1.0 on a plane at z = 0, hair_length 1.0); hair_keys[0].co is its root and hair_keys[-1].co the tip",
       location=[[round(v, 3) for v in l] for l in locs],
       hair_key_root=[[round(v, 3) for v in l] for l in roots] if roots else None,
       hair_key_tip=[[round(v, 3) for v in l] for l in tips] if tips else None)
exp.empty()

# f) hair curves (the Curves object) from Python
sc = bpy.context.scene
hc = bpy.data.hair_curves.new("Hair")
try:
    hc.add_curves([4] * 100)    # 100 curves of 4 points
    pos = np.zeros((400, 3), dtype=np.float32)
    pos[:, 0] = np.repeat(np.arange(100) * 0.01, 4)
    pos[:, 2] = np.tile(np.arange(4) * 0.05, 100)
    hc.attributes["position"].data.foreach_set("vector", pos.ravel())
    obj = bpy.data.objects.new("Hair", hc)
    sc.collection.objects.link(obj)
    hair = dict(curves=len(hc.curves), points=len(hc.points), object_type=obj.type,
                attributes=sorted(a.name for a in hc.attributes))
except Exception as e:  # noqa: BLE001
    hair = "ERROR " + repr(e)[:200]
E.fact("Hair curves (the Curves object type) can be built from Python: hair_curves.new, add_curves(sizes), then the "
       "'position' attribute set with foreach_set", result=hair)

# g) point clouds
try:
    pc = bpy.data.pointclouds.new("Cloud")
    pc_res = dict(created=True, points=len(pc.points), has_add=hasattr(pc, "add_points") or hasattr(pc.points, "add"))
except Exception as e:  # noqa: BLE001
    pc_res = "ERROR " + repr(e)[:200]
E.fact("Point cloud data-blocks in 4.5 from Python", result=pc_res)

# h) assets: marking, and the bundled node-group assets
sc = bpy.context.scene
o = bpy.data.objects.new("Asset", unit_mesh("ball"))
sc.collection.objects.link(o)
o.asset_mark()
o.asset_data.tags.new("stone")
o.asset_data.description = "a test asset"
path = E.out("assets.blend")
bpy.ops.wm.save_as_mainfile(filepath=path)
try:
    with bpy.data.libraries.load(path, assets_only=True) as (src_, _):
        list(src_.objects)
    self_load = "loaded"
except ValueError as e:
    self_load = "ERROR " + str(e)
E.fact("save_as_mainfile makes the saved file the open one, and libraries.load refuses to load from the open file; "
       "save_as_mainfile(filepath=..., copy=True) writes a copy and leaves the open file as it was", result=self_load)
path2 = E.out("assets_copy.blend")
bpy.ops.wm.save_as_mainfile(filepath=path2, copy=True)
with bpy.data.libraries.load(path2, assets_only=True) as (src_, _):
    found = list(src_.objects)
os.remove(path2)
os.remove(path)
bundled = os.path.join(bpy.utils.system_resource("DATAFILES"), "assets", "geometry_nodes", "smooth_by_angle.blend")
with bpy.data.libraries.load(bundled, assets_only=True) as (src_, dst):
    names = list(src_.node_groups)
    dst.node_groups = names
ng = bpy.data.node_groups.get("Smooth by Angle")
E.fact("ID.asset_mark() marks a data-block as an asset (tags and description in asset_data), and "
       "libraries.load(path, assets_only=True) lists only assets. Blender's own node-group assets live in "
       "<datafiles>/assets/geometry_nodes/ (smooth_by_angle.blend, procedural_hair_node_assets.blend) and are appended "
       "the same way. After the with-block, the list given to data_to holds the loaded data-blocks, not names",
       marked_found=found, bundled_node_groups=[getattr(n, "name", n) for n in names],
       smooth_by_angle_inputs=[(i.name, i.socket_type) for i in ng.interface.items_tree if getattr(i, "in_out", "") == "INPUT"] if ng else None)
E.save()
