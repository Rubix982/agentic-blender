---
name: blender
description: Use whenever a task touches Blender or its Python API (bpy) — writing, running or debugging a Blender script; building meshes from data; modifiers and booleans; geometry nodes; materials and shader nodes; lights, world and camera; rendering with Cycles or EEVEE (headless or not); compositing and render passes; cloth, rigid-body and other simulation; armatures, skinning, poses, keyframes and actions; importing or exporting glTF, OBJ, USD, FBX, STL or PLY; or driving a live Blender. Written for Blender 4.5 LTS from what Blender reports about itself (every type, property, operator and node socket, searchable with kb.py), experiments run headless, and lessons from real projects.
---

# Blender 4.5, for an agent

Your memory of Blender mixes versions 2.7 to 4.x. Much of what you remember was renamed, moved or removed (auto smooth,
the EEVEE engine id, Principled BSDF's inputs, node-group sockets, context overrides, actions). This skill replaces
memory with things that can be checked. Paths below are relative to this file's folder.

## Before writing any Blender code

1. **Know the version.** `python3 scripts/run.py --which`. This guide is for 4.5.14 LTS. On another version, regenerate
   the inventory first (`scripts/run.py scripts/inventory.py`) and trust `kb.py` over the area pages.
2. **Look names up; don't recall them.** Every property, enum value, operator parameter and node socket name you are
   about to use: check it with `kb.py`. It answers in a fraction of a second, from Blender itself:

   ```bash
   python3 scripts/kb.py find smooth angle             # anything: types, properties, operators, nodes, Python
   python3 scripts/kb.py struct BooleanModifier        # properties with types, defaults, ranges, enum items
   python3 scripts/kb.py prop SceneEEVEE.use_shadows   # one property in full
   python3 scripts/kb.py path ClothSettings            # how to reach it: bpy.data.objects[...].modifiers[...]<ClothModifier>.settings
   python3 scripts/kb.py op object.modifier_apply      # an operator's parameters
   python3 scripts/kb.py node "Principled BSDF"        # sockets: name, identifier, type, default; * = hidden by default
   python3 scripts/kb.py nodes geometry curve          # node types of one tree, filtered
   python3 scripts/kb.py py bmesh.ops.bevel            # Python helpers with their real argument names
   python3 scripts/kb.py enums                         # machine-dependent enums: engines, view transforms, colour spaces, GPU
   python3 scripts/kb.py factory render                # what a fresh file starts with
   ```
3. **Read the area page** for the task (below). Each opens with what agents most often get wrong there.
4. **For anything the pages don't cover**, search Blender's own manual and Python reference offline:
   `python3 scripts/docs.py search TERM...` (run `docs.py fetch` once; it prints public URLs to cite).

## How to work

- **Headless by default**, through `python3 scripts/run.py SCRIPT.py -- ARGS`. It uses factory settings, makes a
  Python error fail the run (without `--python-exit-code 1` Blender exits 0 after a traceback), and streams printed
  lines (a plain `print()` inside Blender is otherwise held until the end). See `areas/running.md`.
- **Data API first, operators second.** Most operators assume a window, an area or a selection; in background mode
  there is no area, so view-dependent operators fail their poll. Where an operator is the only way, give it the context
  it needs with `bpy.context.temp_override(...)` (`areas/data-model.md`).
- **Check with numbers, not by eye.** Read back what you made: vertex and face counts, bounding boxes, the evaluated
  mesh (`obj.evaluated_get(depsgraph)`), distances with `mathutils.bvhtree`, a light's rotation, a node's links.
  Save the `.blend`, open it again, and read the values from the file.
- **Then look.** Render small (256 to 512 px, few samples), save a PNG, and view it. One change at a time.
- **Keep references, not names.** A new data-block can get `.001`; references to vertices, bones or points die when the
  mode changes or elements are added (`areas/running.md`).
- **Mind the machine.** An empty headless Blender takes about 175 MB, a 1M-vertex mesh about 1 GB, a cloth
  simulation on a figure about 2 GB. Run at most four Blender jobs at once on 16 GB.

## Areas

| Page | What it covers |
|---|---|
| `areas/running.md` | running headless, exit codes, output, arguments, background context, drivers, command-line rendering, memory, crashes, add-ons and extensions, bpy as a module, a live Blender |
| `areas/data-model.md` | objects, data and the evaluated depsgraph; context and `temp_override`; collections; files, append and link; `mathutils` |
| `areas/meshes.md` | meshes from arrays, reading them back, normals and smooth shading in 4.1+, attributes, `bmesh` |
| `areas/modifiers.md` | adding, ordering, evaluating and applying modifiers; Boolean solvers; the common modifiers |
| `areas/geometry-nodes.md` | node groups built from Python with the 4.x interface API, modifier inputs, reading results |
| `areas/curves-text.md` | Bezier and poly curves, bevels, curve to mesh, text |
| `areas/instancing-assets.md` | full copies, linked duplicates, collection and vertex instancing, particle systems (costs measured); hair curves; assets and Blender's bundled ones |
| `areas/uv-images.md` | UV maps (from arrays, bmesh, unwrap operators headless, packing); images: colour spaces, pixels, saving, packing |
| `areas/materials.md` | Principled BSDF in 4.5, textures, bump and normal maps, displacement, colour spaces |
| `areas/light-world-camera.md` | light types and units, sky and HDRI worlds, shadow catcher, camera lens and framing |
| `areas/rendering.md` | Cycles on Metal and CPU, samples, denoising, EEVEE in 4.5, view transforms, output |
| `areas/lines.md` | Grease Pencil strokes from Python (the 4.3+ data), its materials and rendering, Line Art, Freestyle |
| `areas/compositing.md` | render passes, the compositor in background mode, multilayer EXR |
| `areas/export-baking.md` | glTF, OBJ, USD, FBX, STL, PLY: what survives; baking textures |
| `areas/simulation.md` | cloth, rigid bodies, soft bodies, simulation zones; baking headless; caches |
| `areas/python-extending.md` | custom properties, property groups, operators, handlers (and @persistent), timers and msgbus (not in background mode) |
| `areas/rigging-animation.md` | armatures from Python, automatic weights, poses, keyframes and 4.4+ actions, shape keys, drivers |

Lessons from real projects, by area, with what was measured: `../../kb/lessons/` in the source repository.

## Version traps

<!-- filled from the area pages -->
