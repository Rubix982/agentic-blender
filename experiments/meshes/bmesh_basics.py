"""bmesh round trip: from_mesh / to_mesh, index lookups, selection state, edit-mode meshes, and what errors look like."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import time
import bpy, bmesh
import exp
E = exp.Experiment(__file__)

bpy.ops.mesh.primitive_cube_add()
ob = bpy.context.object
me = ob.data

bm = bmesh.new()
bm.from_mesh(me)
# index access without lookup table
try:
    v = bm.verts[0]; idx = "ok"
except Exception as e:
    idx = f"{type(e).__name__}: {e}"
bm.verts.new((2, 2, 2))
try:
    v = bm.verts[0]; idx2 = "ok"
except Exception as e:
    idx2 = f"{type(e).__name__}: {e}"
bm.verts.ensure_lookup_table()
E.fact("bm.verts[i] raises IndexError ('outdated internal index table') even right after from_mesh, and again after adding a vertex, until bm.verts.ensure_lookup_table()",
       after_from_mesh=idx, after_add=idx2, after_ensure=bm.verts[0].index)
newv = bm.verts[-1]
E.fact("a vertex made with bm.verts.new has index -1 until bm.verts.index_update()", before=newv.index)
bm.verts.index_update()
E.fact("index_update gives it its position", after=newv.index)

# selection state round-trip
for f in bm.faces:
    f.select = False
bm.faces.ensure_lookup_table()
bm.faces[0].select_set(True)
sel_verts = sum(v.select for v in bm.verts)
bm.to_mesh(me)
me.update()
E.fact("face.select_set(True) also selects the face's 4 vertices", verts_selected_via_select_set=sel_verts)
bm.faces[1].select = True
n_after_attr = sum(v.select for v in bm.verts)
E.fact(f"setting face.select = True on a second face (sharing an edge) gives {n_after_attr} selected vertices: " +
       ("the .select setter also selects the face's vertices, like select_set" if n_after_attr == 6 else "the .select setter does not flush to vertices"),
       verts_selected=n_after_attr)
bm.select_flush_mode()
E.fact("bm.select_flush_mode() flushes face selection down to vertices", verts_selected=sum(v.select for v in bm.verts))
E.fact("selection written by to_mesh is in mesh.polygons[i].select / .select_vert attribute",
       polys_selected=sum(p.select for p in me.polygons), verts_selected=sum(v.select for v in me.vertices))
bm.free()

# to_mesh needs a mesh not in edit mode; from_edit_mesh needs edit mode
bpy.ops.object.mode_set(mode="EDIT")
try:
    bme = bmesh.from_edit_mesh(me)
    n = len(bme.verts)
    bmesh.ops.subdivide_edges(bme, edges=bme.edges[:], cuts=1)
    bmesh.update_edit_mesh(me)
    edit = f"ok, {n} verts -> {len(bme.verts)}"
except Exception as e:
    edit = f"{type(e).__name__}: {e}"
bpy.ops.object.mode_set(mode="OBJECT")
E.fact("bmesh.from_edit_mesh + update_edit_mesh work headless after object.mode_set(mode='EDIT'); the change lands in mesh data on leaving edit mode",
       result=edit, verts_after_object_mode=len(me.vertices))
try:
    bmesh.from_edit_mesh(me); fe = "ok"
except Exception as e:
    fe = f"{type(e).__name__}: {e}"
E.fact("bmesh.from_edit_mesh on a mesh not in edit mode raises", error=fe)

# using a freed bmesh
bm = bmesh.new(); bm.from_mesh(me); bm.free()
try:
    len(bm.verts); fr = "ok"
except Exception as e:
    fr = f"{type(e).__name__}: {e}"
E.fact("touching a freed BMesh raises ReferenceError rather than crashing", error=fr)

# to_mesh on a mesh used by an object in edit mode? and normals after to_mesh
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.translate(bm, verts=bm.verts[:], vec=(0, 0, 1))
bm.to_mesh(me); bm.free()
E.fact("bmesh.ops.translate moves the given verts; written back by to_mesh, the cube's lowest z is now 0",
       min_z=round(min(v.co.z for v in me.vertices), 4))

# from_object with depsgraph (evaluated, modifiers applied)
ob.modifiers.new("s", "SUBSURF").levels = 1
dg = bpy.context.evaluated_depsgraph_get()
bm = bmesh.new()
bm.from_object(ob, dg)
E.fact("bm.from_object(obj, depsgraph) reads the evaluated mesh (modifiers applied); from_mesh reads the base mesh",
       from_object_verts=len(bm.verts), base_verts=len(me.vertices))
bm.free()

# speed: bmesh round trip on 1M-vert grid
bpy.ops.mesh.primitive_grid_add(x_subdivisions=999, y_subdivisions=999)
g = bpy.context.object.data
t = time.perf_counter(); bm = bmesh.new(); bm.from_mesh(g); t1 = time.perf_counter() - t
t = time.perf_counter(); bm.to_mesh(g); t2 = time.perf_counter() - t
bm.free()
E.fact(f"a bmesh round trip of a 1M-vertex grid costs {t1:.2f} s from_mesh and {t2:.2f} s to_mesh", from_mesh_s=round(t1, 3), to_mesh_s=round(t2, 3), verts=len(g.vertices))

# custom layers
bm = bmesh.new(); bm.from_mesh(me)
lay = bm.verts.layers.float.new("weight_x")
for v in bm.verts:
    v[lay] = v.co.x
bm.to_mesh(me); bm.free()
E.fact("a bmesh float layer written with v[layer] = value becomes a FLOAT POINT mesh attribute",
       attr=(me.attributes["weight_x"].domain, me.attributes["weight_x"].data_type) if "weight_x" in me.attributes else None)
bm = bmesh.new(); bm.from_mesh(me)
E.fact("bmesh layer collections available in 4.5", vert_layer_kinds=[k for k in dir(bm.verts.layers) if not k.startswith("_")],
       uv_layers=list(bm.loops.layers.uv.keys()), float_layers=list(bm.verts.layers.float.keys()))
bm.free()
E.save()
