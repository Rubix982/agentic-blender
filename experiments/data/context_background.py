"""What bpy.context holds in background (-b) mode, which operators run there, and how temp_override changes that."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy
import exp
E = exp.Experiment(__file__)

ctx = bpy.context
E.fact("in -b mode there is a window manager and a window, but screen/area/region availability is what matters",
       window=str(ctx.window), screen=str(ctx.screen), area=str(ctx.area), region=str(ctx.region),
       windows=len(ctx.window_manager.windows), background=bpy.app.background)
E.fact("in -b mode the data context is there", scene=ctx.scene.name, view_layer=ctx.view_layer.name, collection=ctx.collection.name,
       active_object=str(ctx.active_object), object=str(ctx.object), mode=ctx.mode, selected_objects=len(ctx.selected_objects))

def run(label, fn):
    try:
        r = fn(); return list(r) if isinstance(r, set) else r
    except Exception as e:
        return f"{type(e).__name__}: {str(e).strip()[:200]}"

res = {}
res["mesh.primitive_cube_add"] = run("", lambda: bpy.ops.mesh.primitive_cube_add())
E.fact("primitive add operators work headless; the new object is active and selected", result=res["mesh.primitive_cube_add"],
       active=ctx.active_object.name, selected=[o.name for o in ctx.selected_objects])
cube = ctx.active_object
res["object.select_all"] = run("", lambda: bpy.ops.object.select_all(action="DESELECT"))
res["object.mode_set EDIT"] = run("", lambda: bpy.ops.object.mode_set(mode="EDIT"))
res["mesh.select_all"] = run("", lambda: bpy.ops.mesh.select_all(action="SELECT"))
res["mesh.subdivide"] = run("", lambda: bpy.ops.mesh.subdivide(number_cuts=1))
res["mesh.extrude_region_move"] = run("", lambda: bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value": (0, 0, 1)}))
res["object.mode_set OBJECT"] = run("", lambda: bpy.ops.object.mode_set(mode="OBJECT"))
res["selected after mode round trip"] = [o.name for o in ctx.selected_objects]
cube.select_set(True); ctx.view_layer.objects.active = cube
res["view3d.snap_cursor_to_center"] = run("", lambda: bpy.ops.view3d.snap_cursor_to_center())
res["view3d.view_all"] = run("", lambda: bpy.ops.view3d.view_all())
res["transform.translate"] = run("", lambda: bpy.ops.transform.translate(value=(1, 0, 0)))
res["object.origin_set"] = run("", lambda: bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY"))
res["object.join (one selected)"] = run("", lambda: bpy.ops.object.join())
res["object.duplicate"] = run("", lambda: bpy.ops.object.duplicate())
res["object.delete"] = run("", lambda: bpy.ops.object.delete())
res["mesh.primitive_uv_sphere_add"] = run("", lambda: bpy.ops.mesh.primitive_uv_sphere_add())
res["uv.smart_project (object mode)"] = run("", lambda: bpy.ops.uv.smart_project())
E.fact("which common operators run in -b without any override, with the cube selected and active (FINISHED / CANCELLED / error)", results=res)
bpy.ops.object.select_all(action="DESELECT")
E.fact("with nothing selected, object operators return CANCELLED rather than raising", delete=run("", lambda: bpy.ops.object.delete()),
       translate=run("", lambda: bpy.ops.transform.translate(value=(1, 0, 0))))

# temp_override: what keys work, and screen-based ops
o = ctx.active_object
override_res = {}
override_res["object.join with selected_editable_objects"] = None
bpy.ops.mesh.primitive_cube_add(location=(3, 0, 0)); c2 = ctx.active_object
with ctx.temp_override(active_object=o, object=o, selected_objects=[o, c2], selected_editable_objects=[o, c2]):
    override_res["object.join with selected_editable_objects"] = run("", lambda: bpy.ops.object.join())
E.fact("object.join with temp_override(active_object, selected_editable_objects) joins the listed objects", result=override_res, objects=len(bpy.data.objects))
# view3d needs an area: can we fake one?
win = ctx.window_manager.windows[0] if ctx.window_manager.windows else None
areas = [a.type for a in win.screen.areas] if win and win.screen else None
E.fact("the background window's screen areas", areas=areas)
if win and win.screen:
    area = next(a for a in win.screen.areas if a.type == "VIEW_3D")
    region = next((r for r in area.regions if r.type == "WINDOW"), None)
    ctx.scene.cursor.location = (1, 2, 3)
    with ctx.temp_override(window=win, area=area, region=region):
        vr = run("", lambda: bpy.ops.view3d.snap_cursor_to_center())
        va = run("", lambda: bpy.ops.view3d.view_all())
    E.fact("the -b window's screen ('Layout') has a VIEW_3D area; passing it (window, area, region) to temp_override lets view3d operators run",
           snap_cursor_to_center=vr, cursor_after=tuple(ctx.scene.cursor.location), view_all=va)

# temp_override with an unknown key, and with a dict
try:
    with ctx.temp_override(not_a_member=1):
        pass
    unk = "accepted"
except Exception as e:
    unk = f"{type(e).__name__}: {e}"
E.fact("temp_override with an unknown keyword", result=unk)
E.fact("bpy.context.copy() still exists (returns a dict) but passing it to an operator positionally fails (see modifiers/evaluate_and_apply)",
       copy_type=type(ctx.copy()).__name__)
# restricted context in register-time / handlers is not covered here
E.save()
