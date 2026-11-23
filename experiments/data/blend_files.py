"""Saving and loading .blend files from a script: save_as_mainfile, libraries.load (append and link), and open_mainfile mid-script."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy
import exp
E = exp.Experiment(__file__)

lib_path = E.out("library.blend")
main_path = E.out("main.blend")
# build a library file: an object with a material, in a collection
bpy.ops.mesh.primitive_monkey_add()
suz = bpy.context.object; suz.name = "Suzanne"
mat = bpy.data.materials.new("Skin"); suz.data.materials.append(mat)
col = bpy.data.collections.new("Heads"); bpy.context.scene.collection.children.link(col)
col.objects.link(suz)
E.fact("a fresh session has no file path", filepath=repr(bpy.data.filepath))
r = bpy.ops.wm.save_as_mainfile(filepath=lib_path, copy=True)
E.fact("save_as_mainfile(copy=True) writes the file but keeps the session's own file path unchanged", result=list(r), filepath=repr(bpy.data.filepath),
       size_kb=round(os.path.getsize(lib_path) / 1024, 1))
r = bpy.ops.wm.save_as_mainfile(filepath=main_path)
E.fact("save_as_mainfile without copy makes the saved file the current one (bpy.data.filepath)", filepath=os.path.basename(bpy.data.filepath), is_dirty_after_save=bpy.data.is_dirty)
props = [p.identifier for p in bpy.ops.wm.save_as_mainfile.get_rna_type().properties if p.identifier != "rna_type"]
E.fact("save_as_mainfile options", props=props)

# append and link
exp.empty()
with bpy.data.libraries.load(lib_path, link=False) as (src, dst):
    listing = dict(objects=list(src.objects), meshes=list(src.meshes), materials=list(src.materials), collections=list(src.collections))
    dst.objects = ["Suzanne"]
ob = bpy.data.objects["Suzanne"]
E.fact("libraries.load lists names in the source file inside the with block; assigning names to dst appends them", listing=listing)
E.fact("an appended object comes with its mesh and material but is NOT linked into the scene", in_scene=ob.name in bpy.context.scene.objects,
       mesh=ob.data.name, materials=[m.name for m in ob.data.materials], library=ob.library)
bpy.context.scene.collection.objects.link(ob)
with bpy.data.libraries.load(lib_path, link=False) as (src, dst):
    dst.objects = ["Suzanne"]
E.fact("appending the same object again makes a second copy with a .001 name", objects=sorted(o.name for o in bpy.data.objects))
# the dst list holds the new datablocks after the with block
with bpy.data.libraries.load(lib_path, link=False) as (src, dst):
    dst.materials = ["Skin"]
E.fact("after the with block, dst.<type> holds the loaded datablocks (not names)", loaded=[type(m).__name__ + ":" + m.name for m in dst.materials])

exp.empty()
with bpy.data.libraries.load(lib_path, link=True) as (src, dst):
    dst.collections = ["Heads"]
c = dst.collections[0]
inst = bpy.data.objects.new("Heads_instance", None); inst.instance_type = "COLLECTION"; inst.instance_collection = c
bpy.context.scene.collection.objects.link(inst)
E.fact("link=True gives library data (its .library is set); a linked collection is placed in the scene through an Empty that instances it",
       library=os.path.basename(c.library.filepath), objects_in_linked=[o.name for o in c.objects],
       linked_object_library=bool(bpy.data.objects["Suzanne"].library))
try:
    bpy.data.objects["Suzanne"].location.x = 3; w = "accepted"
except Exception as e:
    w = f"{type(e).__name__}: {e}"
E.fact("writing a linked object's property from Python " + ("raises no error (is_editable is " + str(bpy.data.objects["Suzanne"].is_editable) + ")" if w == "accepted" else "raises"),
       result=w, is_editable=bpy.data.objects["Suzanne"].is_editable)
# relative path
E.fact("the library's filepath is stored as given to libraries.load (absolute here)", is_abs=os.path.isabs(bpy.data.libraries[0].filepath))

# open_mainfile mid-script
keep = bpy.data.objects["Heads_instance"]
r = bpy.ops.wm.open_mainfile(filepath=main_path)
try:
    keep.name; alive = "still valid"
except ReferenceError as e:
    alive = f"ReferenceError: {e}"
E.fact("wm.open_mainfile works inside a running -b script, the script keeps running, and every old Python reference to data is invalid",
       result=list(r), old_reference=alive, objects_now=sorted(o.name for o in bpy.data.objects), filepath=os.path.basename(bpy.data.filepath))
E.fact("after open_mainfile, re-fetch through bpy.context/bpy.data: context.scene is the loaded scene", scene=bpy.context.scene.name,
       objects=len(bpy.context.scene.objects))
# load_ui and use_scripts
E.fact("open_mainfile options", props=[p.identifier for p in bpy.ops.wm.open_mainfile.get_rna_type().properties if p.identifier != "rna_type"])
for pth in (lib_path, main_path):
    os.remove(pth)
    if os.path.exists(pth + "1"):
        os.remove(pth + "1")
E.save()
