# Lessons: sculpt mode from a script

From a project that wanted small folds on draped garments and tried Blender 4.5.14's sculpt filters from a background
job.

---

### Sculpt filters crash a background job until an undo step is pushed
**What happens:** calling `bpy.ops.sculpt.mesh_filter` or `bpy.ops.sculpt.cloth_filter` from a script under `-b`
segfaults inside sculpt's undo push (`sculpt_mesh_filter_start`). Pushing one undo step first stops the crash.
**Evidence:** Blender 4.5.14 with `-b`: segfault on both filters; with `bpy.ops.ed.undo_push()` before and after entering
sculpt mode, the mesh filter returned FINISHED and the points moved (its `RANDOM` kind; relax, sharpen, enhance details,
surface smooth and inflate are the same operator). (not re-checked here)
**What to do:** `bpy.ops.ed.undo_push()`, `bpy.ops.object.mode_set(mode='SCULPT')`, `bpy.ops.ed.undo_push()`, then the
filter.
**How it was found:** a headless probe script, one operator at a time.

### The sculpt cloth filter does nothing from a script: it is modal only
**What happens:** `bpy.ops.sculpt.cloth_filter` needs interactive mouse events; called from a script it returns
`{'PASS_THROUGH'}` and moves nothing, even after the undo push that stops the crash.
**Evidence:** Blender 4.5.14 `-b`: PASS_THROUGH, no point moved. So sculpt mode's local cloth simulation (gravity,
inflate, pinch over a mask) cannot be scripted headless; it needs Blender with a window. The mesh filter's enhance-details
kind can deepen folds a mesh already has, not make new ones. (not re-checked here)
**What to do:** for folds the solver leaves out, use the cloth solver itself, displacement, or Multires detail; or drive
a windowed Blender.
**How it was found:** the same probe.
