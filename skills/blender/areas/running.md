# Running Blender from a script

Blender 4.5.14 LTS on Apple Silicon. Tags: `[inv]` read from Blender, `[exp: path]` measured here, `[lesson]` from a
real project, `[doc: link]` Blender's own documentation. Command-line reference:
[manual: command line arguments](https://docs.blender.org/manual/en/4.5/advanced/command_line/arguments.html).

## What goes wrong most often

1. **A failed script reports success.** A script that raises leaves Blender's exit code at 0. Only
   `--python-exit-code 1` turns a Python error into a failed run. `sys.exit(N)` inside the script does end Blender with
   code N. `[exp: experiments/running/cli_behaviour.py]`
2. **Nothing prints until the end.** Read through a pipe (a subprocess, a log, a tool call), a plain `print()` inside
   Blender is held until the script finishes: a line printed 3 s before the end arrived with the end.
   `PYTHONUNBUFFERED=1` does nothing, because Blender's Python ignores `PYTHON*` environment variables unless
   `--python-use-system-env` is given. What works: `print(..., flush=True)`, or once at the top
   `sys.stdout.reconfigure(line_buffering=True)` (what `scripts/run.py` does for you), or `--python-use-system-env`
   with `PYTHONUNBUFFERED=1`. `[exp: experiments/running/cli_behaviour.py]`
3. **Reading `sys.argv` as if it were the script's own.** It holds Blender's arguments too (10 entries for a 4-argument
   call). The script's arguments are the ones after `--`, and Blender does not act on anything after `--` (a `-f 3`
   there rendered nothing). `[exp: experiments/running/cli_behaviour.py]`

   ```python
   import sys, argparse
   argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
   args = argparse.ArgumentParser().parse_args(argv)   # careful: argparse calls sys.exit on bad arguments, which
                                                        # closes Blender at once [doc: info_gotchas_crashes, sys.exit]
   ```
4. **Assuming background mode has no context at all, or a full one.** In `-b` mode `bpy.context` has a window and a
   screen (from the file), the scene, view layer, active object and selection, but **no area, region or space**.
   Object, mesh and edit-mode operators work (`object.select_all`, `mesh.primitive_uv_sphere_add`,
   `object.shade_smooth`, `object.mode_set`, `mesh.subdivide` all returned FINISHED); operators that need a 3D view
   or a screen area fail their poll (`view3d.snap_cursor_to_center`, `screen.screenshot`: "poll() failed, context is
   incorrect"). Prefer the data API; see `data-model.md` for `bpy.context.temp_override`.
   `[exp: experiments/running/cli_behaviour.py]`
5. **Python drivers silently stay at 0.** A driver whose expression needs Python (`__import__("math").pi`) is not
   evaluated in a file opened headless: it read 0.0. With `-y` (allow auto-run of scripts) it read 3.1416. A simple
   expression (`frame * 2`) is evaluated either way, by Blender's own evaluator. `[exp: experiments/running/cli_behaviour.py]`
6. **Holding on to Blender data across a change that re-allocates it.** References to a mesh's vertices, polygons or
   UVs, an armature's bones or a curve's points die when the mode switches (`object.mode_set`) or when elements are
   added; using them can crash Blender. Re-fetch after the change. Removed data must not be touched again.
   `[doc: https://docs.blender.org/api/4.5/info_gotchas_crashes.html]`
7. **Looking data up by the name you asked for.** A new data-block may get another name (`.001` when the name is
   taken; names are cut at 63 bytes). Keep the Python reference you were given, not the name.
   `[doc: https://docs.blender.org/api/4.5/info_gotchas_internal_data_and_python_objects.html]`
8. **Threads.** Python threads that touch `bpy` crash Blender in ways that are hard to trace (the docs name Cycles
   renders and Python drivers). Do work in the main thread; in a live Blender, schedule it with `bpy.app.timers`.
   `[doc: https://docs.blender.org/api/4.5/info_gotchas_threading.html]`

## Running a script

```bash
python3 scripts/run.py my_script.py -- --out /tmp/x.png        # this skill's runner
# what it runs:
Blender -b --factory-startup --python-exit-code 1 \
        --python-expr "import sys; sys.stdout.reconfigure(line_buffering=True)" \
        --python my_script.py -- --out /tmp/x.png
```

- `-b` first. A `.blend` to open goes before `--python` (`Blender -b scene.blend --python s.py`).
- `--factory-startup` ignores the user's preferences and add-ons: the run is the same on every machine. Without it,
  user add-ons and extensions load (startup 0.66 to 0.80 s instead of 0.37 to 0.40 s here).
  `[exp: experiments/running/cli_behaviour.py]`
- Arguments are applied in order. `--python-expr` placed before `-f 1` changed the scene before the frame rendered
  (the PNG came out at the size the expression set). `[exp: experiments/running/cli_behaviour.py]`
- Which Blender, and its version: `python3 scripts/run.py --which`. Everything in this guide is for 4.5.14 LTS with
  Python 3.11.15 inside (`kb.py meta`). `[inv]`

## Rendering from the command line

```bash
Blender -b scene.blend -E CYCLES -o /tmp/frame_ -F PNG -x 1 -f 1 -- --cycles-device METAL
#        engine        output prefix, format, add extension, frame;   Cycles' device, after '--'
```

- `-E` takes the engine id: in 4.5 these are `BLENDER_EEVEE_NEXT`, `BLENDER_WORKBENCH`, `CYCLES`, `HYDRA_STORM`
  (`kb.py enums`). The EEVEE id changed in 4.2; code written for older versions that sets `'BLENDER_EEVEE'` fails. `[inv]`
- `-- --cycles-device METAL` renders on the GPU without changing `scene.cycles.device` (it still read `CPU`): the same
  320 px, 512-sample frame took 1.8 s on the CPU and 1.1 s with the flag. To choose the device inside a script instead,
  see `rendering.md`. `[exp: experiments/running/cli_behaviour.py]`
- `-a` renders the animation; `-s`/`-e` set the frame range; `-o` takes `#` as frame-number placeholders.
  [doc: https://docs.blender.org/manual/en/4.5/advanced/command_line/render.html]

## Cost: time and memory

| Job, headless | Peak memory |
|---|---|
| an empty script, factory file | 175 to 177 MB |
| a 1,000,000-vertex grid | 1,041 to 1,059 MB |
| a Cycles render, 512 px, 64 samples, CPU | 422 to 482 MB |

`[exp: experiments/running/process.py]`. Starting Blender costs about 0.4 s, so many small headless runs are cheap; a
heavy scene rebuilt on every run is what costs. A cloth simulation on a figure took about 2 GB a job, and more than four
such jobs at once on 16 GB swapped and slowed every job. `[lesson]`

## When Blender crashes

A segmentation fault ends Blender with a negative return code (−11 here), with no Python traceback. Blender prints
`Writing: <path>` and leaves a backtrace in the system temp folder: `$TMPDIR/blender.crash.txt` with no file open
(named after the `.blend` otherwise). Read its first lines: the top frames name the Blender function that crashed.
`[exp: experiments/running/process.py]` Common causes are in item 6 and 8 above and on
[info_gotchas_crashes](https://docs.blender.org/api/4.5/info_gotchas_crashes.html).

## Add-ons and extensions

- In a fresh 4.5 these add-ons are on: `io_anim_bvh`, `bl_pkg` (the extensions system), `cycles`, `io_scene_fbx`,
  `io_scene_gltf2`, `pose_library`, `io_curve_svg`, `io_mesh_uv_layout`. Bundled but off: `copy_global_transform`,
  `hydra_storm`, `ui_translate`, `node_wrangler`, `rigify`, `viewport_vr_preview`. `[inv]`
- Turning one on from a script: `addon_utils.enable("rigify", default_set=True)`. With `default_set=False`, Rigify's
  own registration failed (`KeyError: 'bpy_prop_collection[key]: key "rigify" not found'`), since it reads its
  preferences entry. Set `bpy.context.preferences.use_preferences_save = False` first so nothing is written to the
  user's preferences. (Seen while writing `tools/inventory.py`.)
- Since 4.2 most add-ons are extensions, managed with `blender --command extension {list, sync, install,
  install-file, remove, update, repo-list, repo-add, repo-remove, build, validate, server-generate}`. `--command` is
  the only subcommand family 4.5 lists. `[exp: experiments/running/process.py]`

## Blender as a Python module

`pip install bpy` gives Blender without its app. Its 4.5 wheels (newest 4.5.9) are built for Python 3.11 only
(`bpy-4.5.9-cp311-cp311-macosx_11_0_arm64.whl`), so it needs a Python 3.11 environment. `[exp:
experiments/running/process.py]` Untested here: whether it renders on Metal and how it differs from the app.

## A live Blender

A Blender left open with a small server add-on can run code sent to it, which saves startup and keeps a heavy scene
loaded between changes. Code must run on Blender's main thread: the server queues it and runs it from a
`bpy.app.timers` callback (item 8). An earlier project kept one Blender open this way and sent it only the changed
garments each round, instead of starting Blender for every look (10 to 60 s each). `[lesson]` An MCP connector for
Blender works the same way (`execute_blender_code`, and a `look` tool that returns a viewport image); it drives the
user's own Blender and needs them to have it open with the add-on running. Untested in this guide.
