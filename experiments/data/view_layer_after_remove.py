"""What does view_layer.objects hold after objects are removed with bpy.data.objects.remove, and what brings it back
in line? Found by the C-001 comparison: 3 of the 10 scripts written without the skill deleted the factory scene's
objects this way, then crashed on `None` in the usual deselect loop (evals/results.md)."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy
import exp

E = exp.Experiment(__file__, keep_scene=True)          # the factory scene: Cube, Light, Camera


def names(vl):
    return [None if o is None else o.name for o in vl.objects]


def try_deselect(vl):
    try:
        for o in vl.objects:
            o.select_set(False)
        return None
    except AttributeError as e:
        return str(e)


vl = bpy.context.view_layer
E.fact("the factory scene's view layer lists the cube, the light and the camera", objects=names(vl))

for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
E.fact("after bpy.data.objects.remove on all three, view_layer.objects still has three entries, each None, while "
       "scene.objects is empty", objects=names(vl), length=len(vl.objects),
       scene_objects=[o.name for o in bpy.context.scene.objects])

ob = bpy.data.objects.new("New", bpy.data.meshes.new("New"))
bpy.context.scene.collection.objects.link(ob)
E.fact("linking a new object does not refresh it: the three None entries stay and the new object is missing",
       objects=names(vl), scene_objects=[o.name for o in bpy.context.scene.objects])
E.fact("the usual deselect loop over view_layer.objects then raises AttributeError", error=try_deselect(vl))
E.fact("view_layer.objects.active is None and selecting the new object still works",
       active=None if vl.objects.active is None else vl.objects.active.name,
       select_ok=(ob.select_set(True) is None) and ob.select_get())
vl.update()
E.fact("after view_layer.update() it lists only the new object, and the loop runs", objects=names(vl),
       error=try_deselect(vl))

# one object removed out of several
bpy.ops.wm.read_factory_settings()
vl = bpy.context.view_layer
bpy.data.objects.remove(bpy.data.objects["Cube"], do_unlink=True)
E.fact("removing only the cube leaves None in its place and the others listed", objects=names(vl))

# bpy.data.batch_remove
bpy.ops.wm.read_factory_settings()
vl = bpy.context.view_layer
bpy.data.batch_remove(list(bpy.data.objects))
E.fact("bpy.data.batch_remove leaves the same None entries", objects=names(vl))

# the operator way, in background mode
bpy.ops.wm.read_factory_settings()
vl = bpy.context.view_layer
for o in vl.objects:
    o.select_set(True)
r = bpy.ops.object.delete()
E.fact("bpy.ops.object.delete() on the selected objects works headless and leaves no None entries",
       result=sorted(r), objects=names(vl), data_objects=[o.name for o in bpy.data.objects])

# the clean start
bpy.ops.wm.read_factory_settings(use_empty=True)
vl = bpy.context.view_layer
ob = bpy.data.objects.new("New", bpy.data.meshes.new("New"))
bpy.context.scene.collection.objects.link(ob)
E.fact("starting from read_factory_settings(use_empty=True) there is nothing to remove, and a linked object is listed "
       "at once", objects=names(vl), error=try_deselect(vl))
E.save()
