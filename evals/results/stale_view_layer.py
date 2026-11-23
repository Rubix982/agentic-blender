import bpy
vl = bpy.context.view_layer
def show(label):
    print(label, [None if o is None else o.name for o in vl.objects])
show("factory:")
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
show("after data.objects.remove:")
me = bpy.data.meshes.new("M"); ob = bpy.data.objects.new("New", me)
bpy.context.scene.collection.objects.link(ob)
show("after linking a new object:")
vl.update()
show("after view_layer.update():")
