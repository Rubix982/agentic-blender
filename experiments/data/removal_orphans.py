"""Removing data: what bpy.data.*.remove leaves behind, orphans, purge, fake users, and the cost of removing many."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import time
import bpy
import exp
E = exp.Experiment(__file__)

bpy.ops.mesh.primitive_cube_add()
ob = bpy.context.object
me = ob.data
mat = bpy.data.materials.new("Mat"); me.materials.append(mat)
name = me.name
bpy.data.objects.remove(ob)
E.fact("removing an object leaves its mesh (and the mesh's material) in bpy.data with 0 users: an orphan",
       mesh_left=name in bpy.data.meshes, mesh_users=bpy.data.meshes[name].users, mat_users=mat.users)
try:
    ob.name; ref = "still usable"
except ReferenceError as e:
    ref = f"ReferenceError: {e}"
E.fact("a Python reference to a removed object raises ReferenceError when touched", error=ref)

# removing a mesh that an object uses
bpy.ops.mesh.primitive_cube_add()
ob2 = bpy.context.object
m2 = ob2.data
oname = ob2.name
n_obj = len(bpy.data.objects)
bpy.data.meshes.remove(m2)
try:
    ob2.name; alive = True
except ReferenceError:
    alive = False
E.fact("bpy.data.meshes.remove(mesh) on a mesh an object uses also deletes that object (objects without their obdata cannot exist)",
       object_reference_alive=alive, object_in_data=oname in bpy.data.objects, objects_before=n_obj, objects_after=len(bpy.data.objects))
params = [(p.identifier, getattr(p, "default", None)) for p in bpy.types.BlendDataMeshes.bl_rna.functions["remove"].parameters]
E.fact("BlendDataMeshes.remove parameters", params=params)

# orphans_purge
for i in range(5):
    bpy.data.meshes.new(f"orphan{i}")
n_before = len(bpy.data.meshes)
mat_before = len(bpy.data.materials)
r = bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=False)
n_mid = (len(bpy.data.meshes), len(bpy.data.materials))
r2 = bpy.data.orphans_purge(do_recursive=True)
E.fact("bpy.data.orphans_purge() removes 0-user data; with do_recursive=False a material used only by an orphan mesh survives the first pass; do_recursive=True gets it",
       meshes_before=n_before, materials_before=mat_before, after_non_recursive=n_mid, removed_first=r,
       after_recursive=(len(bpy.data.meshes), len(bpy.data.materials)), removed_second=r2)

# fake user
keep = bpy.data.meshes.new("keep"); keep.use_fake_user = True
bpy.data.orphans_purge(do_recursive=True)
E.fact("use_fake_user = True protects a 0-user datablock from purge (and from not being saved)", kept="keep" in bpy.data.meshes, users=keep.users)

# orphans are not saved
nm = bpy.data.meshes.new("unsaved_orphan")
path = E.out("orphans.blend")
bpy.ops.wm.save_as_mainfile(filepath=path, copy=True)
with bpy.data.libraries.load(path) as (src, dst):
    names = list(src.meshes)
os.remove(path)
E.fact("a 0-user datablock is not written when the file is saved", saved_meshes=names)

# batch_remove vs loop
def make(n):
    return [bpy.data.objects.new(f"o{i}", None) for i in range(n)]
for o in make(2000):
    bpy.context.scene.collection.objects.link(o)
objs = [o for o in bpy.data.objects if o.name.startswith("o")]
t = time.perf_counter()
for o in objs:
    bpy.data.objects.remove(o)
t_loop = time.perf_counter() - t
for o in make(2000):
    bpy.context.scene.collection.objects.link(o)
objs = [o for o in bpy.data.objects if o.name.startswith("o")]
t = time.perf_counter()
bpy.data.batch_remove(objs)
t_batch = time.perf_counter() - t
E.fact(f"removing 2000 linked empties: a loop of objects.remove takes {t_loop:.2f} s, bpy.data.batch_remove takes {t_batch:.3f} s",
       loop_s=round(t_loop, 3), batch_s=round(t_batch, 4))
# user_clear, users count for an object
bpy.ops.mesh.primitive_cube_add()
o = bpy.context.object
E.fact("a linked object's users count: 1 per collection it is in", users=o.users, collections=len(o.users_collection))
E.save()
