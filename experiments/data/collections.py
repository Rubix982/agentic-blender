"""Collections: getting new objects into the scene, nesting, multiple membership, and hiding vs excluding."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy
import exp
E = exp.Experiment(__file__)

sc = bpy.context.scene
ob = bpy.data.objects.new("lonely", bpy.data.meshes.new("m"))
E.fact("bpy.data.objects.new does not put the object in any scene", in_scene=ob.name in sc.objects, users_collection=[c.name for c in ob.users_collection])
dg = bpy.context.evaluated_depsgraph_get()
E.fact("an unlinked object is not evaluated (not in the depsgraph)", in_depsgraph=any(o.original == ob for o in dg.objects))
sc.collection.objects.link(ob)
E.fact("scene.collection.objects.link(obj) puts it in the scene's master collection", in_scene=ob.name in sc.objects,
       users_collection=[c.name for c in ob.users_collection])
E.fact("with factory empty startup, bpy.context.collection is the scene collection", context_collection=bpy.context.collection.name,
       is_master=bpy.context.collection == sc.collection)
try:
    sc.collection.objects.link(ob); twice = "accepted"
except Exception as e:
    twice = f"{type(e).__name__}: {e}"
E.fact("linking the same object twice into one collection raises", error=twice)

col = bpy.data.collections.new("Parts")
E.fact("a new collection is not in the scene until linked under scene.collection.children", in_scene=col.name in [c.name for c in sc.collection.children_recursive])
sc.collection.children.link(col)
sub = bpy.data.collections.new("Sub"); col.children.link(sub)
sub.objects.link(ob)
E.fact("an object can be in several collections at once", users_collection=sorted(c.name for c in ob.users_collection))
sc.collection.objects.unlink(ob)
E.fact("unlinking from one collection leaves it in the others", users_collection=[c.name for c in ob.users_collection], in_scene=ob.name in sc.objects)
E.fact("scene.objects lists objects from all nested collections", count=len(sc.objects), all_objects_in_sub=len(sub.all_objects))

# hide vs exclude
lc = bpy.context.view_layer.layer_collection.children["Parts"]
lc.exclude = True
dg = bpy.context.evaluated_depsgraph_get()
excl = any(o.original == ob for o in dg.objects)
lc.exclude = False
col.hide_viewport = True
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
hv = any(o.original == ob for o in dg.objects)
col.hide_viewport = False
col.hide_render = True
dg = bpy.context.evaluated_depsgraph_get()
hr = any(o.original == ob for o in dg.objects)
col.hide_render = False
ob.hide_set(True)
dg = bpy.context.evaluated_depsgraph_get()
hs = any(o.original == ob for o in dg.objects)
ob.hide_set(False)
say = lambda present: "keeps it" if present else "removes it"
E.fact(f"in the viewport depsgraph (what evaluated_depsgraph_get() returns in -b): layer_collection.exclude {say(excl)}, collection.hide_viewport {say(hv)}, collection.hide_render {say(hr)}, obj.hide_set(True) {say(hs)}",
       in_depsgraph_when_excluded=excl, when_hide_viewport=hv, when_hide_render=hr, when_hide_set=hs)
E.fact("obj.hide_get()/hide_set() are per view layer; obj.hide_viewport and obj.hide_render are global flags",
       has=[hasattr(ob, k) for k in ("hide_get", "hide_set", "hide_viewport", "hide_render")])
# moving an object between collections
for c in list(ob.users_collection):
    c.objects.unlink(ob)
col.objects.link(ob)
E.fact("move = unlink from every users_collection, then link to the target", users_collection=[c.name for c in ob.users_collection])
# instancing a collection
inst = bpy.data.objects.new("inst", None); inst.instance_type = "COLLECTION"; inst.instance_collection = col
sc.collection.objects.link(inst)
dg = bpy.context.evaluated_depsgraph_get()
n = sum(1 for i in dg.object_instances if i.is_instance and i.parent and i.parent.original == inst)
E.fact("an Empty with instance_type COLLECTION instances that collection's objects (seen in depsgraph.object_instances)", instances=n)
E.save()
