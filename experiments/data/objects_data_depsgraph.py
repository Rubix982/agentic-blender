"""Objects vs data vs evaluated copies, and when matrix_world (and other derived values) are stale until view_layer.update()."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy
from mathutils import Vector
import exp
E = exp.Experiment(__file__)

me = bpy.data.meshes.new("m")
me.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
a = bpy.data.objects.new("A", me)
bpy.context.scene.collection.objects.link(a)
b = a.copy()
bpy.context.scene.collection.objects.link(b)
E.fact("obj.copy() makes a linked duplicate: a new object sharing the same mesh (users 2)", shared=a.data == b.data, users=me.users)
c = a.copy(); c.data = a.data.copy(); bpy.context.scene.collection.objects.link(c)
E.fact("obj.copy() then obj.data = obj.data.copy() makes an independent duplicate", shared=c.data == a.data, mesh_users=me.users, new_mesh=c.data.name)
E.fact("an object without data is an Empty", type=bpy.data.objects.new("e", None).type)

# matrix_world staleness
a.location = (1, 2, 3)
stale = tuple(a.matrix_world.translation)
bpy.context.view_layer.update()
fresh = tuple(a.matrix_world.translation)
E.fact("after setting location, obj.matrix_world is stale until bpy.context.view_layer.update()", before=stale, after=fresh)

# parent: child world matrix stale too; matrix_parent_inverse
p = bpy.data.objects.new("P", None); bpy.context.scene.collection.objects.link(p)
p.location = (10, 0, 0)
bpy.context.view_layer.update()
k = bpy.data.objects.new("K", None); bpy.context.scene.collection.objects.link(k)
k.location = (1, 0, 0)
k.parent = p
bpy.context.view_layer.update()
E.fact("setting child.parent = P without a parent inverse moves the child: its local location is now relative to P",
       child_world=tuple(round(x, 4) for x in k.matrix_world.translation))
k2 = bpy.data.objects.new("K2", None); bpy.context.scene.collection.objects.link(k2)
k2.location = (1, 0, 0)
bpy.context.view_layer.update()
k2.parent = p
k2.matrix_parent_inverse = p.matrix_world.inverted()
bpy.context.view_layer.update()
E.fact("setting matrix_parent_inverse = parent.matrix_world.inverted() keeps the child where it was (like Ctrl+P)",
       child_world=tuple(round(x, 4) for x in k2.matrix_world.translation))
# setting matrix_world directly
k3 = bpy.data.objects.new("K3", None); bpy.context.scene.collection.objects.link(k3)
k3.parent = p
k3.matrix_world.translation = Vector((5, 5, 5))
E.fact("writing matrix_world on a parented object sets location so the world position is right after update",
       location=tuple(round(x, 4) for x in k3.location), world_after_update=(bpy.context.view_layer.update(), tuple(round(x, 4) for x in k3.matrix_world.translation))[1])

# constraints are evaluated by the depsgraph
t = bpy.data.objects.new("T", None); bpy.context.scene.collection.objects.link(t); t.location = (0, 0, 7)
cons = k3.constraints.new("COPY_LOCATION"); cons.target = t
before = tuple(round(x, 3) for x in k3.matrix_world.translation)
bpy.context.view_layer.update()
after = tuple(round(x, 3) for x in k3.matrix_world.translation)
E.fact("a constraint's effect shows in matrix_world only after the depsgraph updates; obj.location is not changed by it",
       before=before, after=after, location=tuple(round(x, 3) for x in k3.location))

# evaluated vs original
a.modifiers.new("s", "SUBSURF")
dg = bpy.context.evaluated_depsgraph_get()
ea = a.evaluated_get(dg)
E.fact("evaluated objects: is_evaluated True, .original points back, and the evaluated mesh is a different datablock",
       is_evaluated=ea.is_evaluated, original_is_a=ea.original == a, orig_is_evaluated=a.is_evaluated,
       eval_mesh_verts=len(ea.data.vertices), orig_mesh_verts=len(a.data.vertices), same_mesh=ea.data == a.data)
try:
    ea.location.x = 100; w = f"accepted, original x still {a.location.x}"
except Exception as e:
    w = f"{type(e).__name__}: {e}"
E.fact("writing to an evaluated object does not change the original", result=w)
E.fact("bpy.context.evaluated_depsgraph_get() and view_layer.depsgraph are the same depsgraph",
       same=bpy.context.evaluated_depsgraph_get() == bpy.context.view_layer.depsgraph)

# data API changes to mesh: is the evaluated result updated without update()?
a.modifiers.clear()
me.vertices[0].co.z = 5
dg = bpy.context.evaluated_depsgraph_get()
z_eval = a.evaluated_get(dg).data.vertices[0].co.z
me.update()
dg = bpy.context.evaluated_depsgraph_get()
z_eval2 = a.evaluated_get(dg).data.vertices[0].co.z
E.fact("after writing vertex co directly, the evaluated mesh " + ("already shows it" if z_eval == 5 else "still shows the old value until mesh.update()"),
       before_update=z_eval, after_update=z_eval2)
E.save()
