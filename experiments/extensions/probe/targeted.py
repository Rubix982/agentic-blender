"""Inside Blender, run by ../top_addons.py in the same sandbox: the add-ons whose operators did nothing with default
settings on one cube, given the input each is made for. Arguments after --: OUT_JSON."""
import json
import sys
import traceback

import addon_utils
import bmesh
import bpy

out_path = sys.argv[sys.argv.index("--") + 1]
cases = []


def empty():
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.data.batch_remove(list(bpy.data.objects))
    bpy.data.orphans_purge(do_recursive=True)
    bpy.context.view_layer.update()


def counts():
    """Measured in object mode (edit-mode changes reach the mesh, and the evaluated copy exists, only then); the
    mode is restored afterwards."""
    ob = bpy.context.object
    edit = bool(ob and ob.mode == "EDIT")
    if edit:
        bpy.ops.object.mode_set(mode="OBJECT")
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    dg = bpy.context.evaluated_depsgraph_get()
    out = dict(objects=len(bpy.data.objects), verts=sum(len(o.data.vertices) for o in meshes),
               faces=sum(len(o.data.polygons) for o in meshes),
               evaluated_verts=sum(len(o.evaluated_get(dg).data.vertices) for o in meshes),
               co=round(sum(abs(c) for o in meshes for v in o.data.vertices for c in v.co), 3),
               modifiers=sum(len(o.modifiers) for o in bpy.data.objects))
    if edit:
        bpy.ops.object.mode_set(mode="EDIT")
    return out


def case(addon, what, setup, call):
    rec = dict(addon=addon, what=what)
    try:
        addon_utils.enable(f"bl_ext.user_default.{addon}", default_set=True)
        empty()
        setup()
        before = counts()
        rec["result"] = sorted(call())
        if bpy.context.object and bpy.context.object.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        bpy.context.view_layer.update()
        after = counts()
        rec.update(before=before, after=after, changed=before != after,
                   new_objects=sorted(o.name for o in bpy.data.objects)[:12])
    except Exception:
        rec.update(result="error", error=traceback.format_exc().strip().splitlines()[-1][:300])
    cases.append(rec)
    print("CASE", rec["addon"], rec["what"], rec.get("result"), rec.get("changed"), flush=True)


# A.N.T. Landscape: its add operator generates only when its `refresh` flag is set (the panel sets it)
case("antlandscape", "mesh.landscape_add(refresh=True) in an empty scene", lambda: None,
     lambda: bpy.ops.mesh.landscape_add(refresh=True))


def plane_grid():
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=64, y_subdivisions=64, size=4)


case("antlandscape", "mesh.ant_displace(refresh=True) on a 64 x 64 grid, edit mode", plane_grid,
     lambda: (bpy.ops.object.mode_set(mode="EDIT"), bpy.ops.mesh.select_all(action="SELECT"),
              bpy.ops.mesh.ant_displace(refresh=True))[-1])


# Bool Tool: a canvas and a cutter, both selected, the canvas active
def two_cubes():
    bpy.ops.mesh.primitive_cube_add(size=2)
    canvas = bpy.context.object
    bpy.ops.mesh.primitive_cube_add(size=1, location=(1, 1, 1))
    cutter = bpy.context.object
    canvas.select_set(True)
    cutter.select_set(True)
    bpy.context.view_layer.objects.active = canvas


case("bool_tool", "object.boolean_auto_difference() with canvas active and cutter selected", two_cubes,
     lambda: bpy.ops.object.boolean_auto_difference())
case("bool_tool", "object.boolean_brush_difference() with canvas active and cutter selected", two_cubes,
     lambda: bpy.ops.object.boolean_brush_difference())


# F2: fill a hole from a selected boundary
def cube_with_hole():
    bpy.ops.mesh.primitive_cube_add(size=2)
    ob = bpy.context.object
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.faces.ensure_lookup_table()
    top = max(bm.faces, key=lambda f: f.calc_center_median().z)
    bmesh.ops.delete(bm, geom=[top], context="FACES_ONLY")
    bm.to_mesh(ob.data)
    bm.free()
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.mesh.select_non_manifold()


case("f2", "mesh.f2() with a hole's boundary selected", cube_with_hole, lambda: bpy.ops.mesh.f2())

# Sapling: a tree with leaves
case("sapling_tree_gen", "curve.tree_add(do_update=True, showLeaves=True)", lambda: None,
     lambda: bpy.ops.curve.tree_add(do_update=True, showLeaves=True))

json.dump(cases, open(out_path, "w"), indent=1, default=str)
