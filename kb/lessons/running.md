# Lessons: running Blender from scripts

From a project that ran Blender 4.5.14 headless in batches of many jobs on a 16 GB Apple Silicon laptop (cloth drapes,
renders, exports), and kept one Blender open as a live server for quick looks.

---

### A background job's printed output arrives only when it exits, unless you flush
**What happens:** read through a pipe, Python's stdout inside Blender is block-buffered; a running job cannot be watched.
**Evidence:** a drape job's progress could not be followed until each line was flushed. (not re-checked here; the
`running` area page measured the same and found `PYTHONUNBUFFERED` alone does not help)
**What to do:** `sys.stdout.reconfigure(line_buffering=True)` at the top of every `-b` script, or `print(..., flush=True)`.
**How it was found:** a running job could not be watched.

### Records written in an atexit hook were lost from batch jobs
**What happens:** the project lost records it wrote in an `atexit` hook. A clean exit does run the hook, so the loss
probably came from jobs that crashed or were killed, where no hook runs.
**Evidence:** records written at exit went missing. Not reproduced in a simple test
`[exp: experiments/running/lesson_checks.py]`: the hook ran both when a `-b` script ended and on `sys.exit(0)`; the
loss probably came from crashed or killed jobs.
**What to do:** write records as they happen (append at each event), never at exit.
**How it was found:** missing records.

### Without --factory-startup, a background job loads the user's add-ons, including ones that start servers
**What happens:** `Blender -b` registers every enabled add-on; an add-on that starts something on load (a socket server
that runs any Python it receives) starts inside every pipeline job too.
**Evidence:** found reading a third-party live-link add-on before installing it. (not re-checked here)
**What to do:** run checks and batch jobs with `--factory-startup`; in an add-on's `register()`, return early when
`bpy.app.background` is true, and default any auto-start to off.
**How it was found:** a code review of the add-on.

### One long-lived Blender that runs code sent to it turns a 30-60 s look into about a second
**What happens:** starting Blender and rebuilding the scene for every look costs far more than the change being looked at.
A Blender kept open (`Blender -b file.blend --python server.py`, a blocking socket loop on the main thread, so bpy calls
are safe) answers in a fraction of a second.
**Evidence:** a query 0.2 s and a preview about 3 s per view, against 30-60 s per look when each rebuilt the scene (about
15x). Previews used the viewport subdivision level for render (`render_levels = levels`) and EEVEE at about 12 samples;
full-detail subdivision was most of the cost. A whole garment fitting took 5 s (measuring 0.04 s, cutting 0.5 s, weights
0.9 s, a scarf settling 4 s); the 60-90 s rounds before were Blender start-up, full-detail renders and file saves.
(not re-checked here)
**What to do:** bind to 127.0.0.1 only; `exec(compile(code, '<live>', 'exec'), NS)` into a namespace that persists between
sends; return prints through `contextlib.redirect_stdout`. Measure where time goes before optimising.
**How it was found:** the head and neck took about 20 render rounds at a minute each.

### In a persistent session, module state does not survive a reload: tag what you create
**What happens:** reloading a module (`importlib.reload`) between runs forgets module-level lists, so objects made by
earlier runs stay in the scene and render on top of new ones.
**Evidence:** 32 meshes from earlier tries were in the scene, rendering over every new try; a parameter seemed to change
nothing because of them. (not re-checked here)
**What to do:** mark each created object with a custom property (`o["made_by"] = "fit"`) and clean up by scanning
`bpy.data.objects` for the tag.
**How it was found:** a sensitivity check found a parameter no measure could see.

### Each batch job reads your scripts when it starts, so edits mid-batch mix code versions
**What happens:** `Blender -b --python` imports the files as they are at that job's start; edits made while a batch runs
reach later jobs only.
**Evidence:** happened three times; a study mixed results from two code versions. (not re-checked here)
**What to do:** copy the script tree to a snapshot directory at batch start and run every job from it; never move or swap
files (textures, caches) a running batch reads.
**How it was found:** mixed results within one study.

### Rendering, not simulation, sets a job's peak memory
**What happens:** a cloth job holds little; rendering the full scene (cloth at render subdivision, hair, a dense collision
shell) is the peak. Blender loads image textures only when it renders.
**Evidence:** resident memory sampled every 0.5 s with one job alone: a drape job 0.5-1.4 GB (15 mm to 7 mm grid); a pose
job with its own render at the end 3.25 GB (simulation 0.44-0.85 GB); an id-pass render 3.09 GB; a look render 2.60 GB.
Dropping the render from the pose job: 3.25 -> 0.88 GB, 184 -> 173 s, the saved result bit-identical. A long clip holding
its whole baked simulation took about 5 GB. (not re-checked here)
**What to do:** split simulation (save a .blend) and rendering into separate jobs; gate each job start on its kind's peak
against free memory, not on a fixed count.
**How it was found:** four jobs that each started with more than 25 % free reached their renders together: 4 x 3.6 GB on a
16 GB machine crashed; five clips at once with a browser filled swap and stalled everything.

### Parallel jobs slow each other more than their count suggests
**What happens:** Blender jobs share cores; renders and simulations slow down sharply when several run at once.
**Evidence:** an id pass took 7 s alone and about 3 min with four jobs sharing 12 cores; a look render 9 s alone, about
3 min in the batch. (not re-checked here)
**What to do:** time a job alone before planning a batch; prefer fewer, sequential jobs for renders.
**How it was found:** a timing breakdown of a slow batch.

### Counting Blender processes also counts the user's window and a live server
**What happens:** `pgrep -x Blender` matches the interactive app and any live server as well as background jobs.
**Evidence:** an open window took one of two job slots and stalled a batch. (not re-checked here)
**What to do:** count only processes whose command line (`ps -o args= -p PID`) contains ` -b ` and not your server script.
**How it was found:** a batch waiting on a phantom slot.

### Cycles on Metal sometimes dies compiling kernels; check the output exists
**What happens:** a Cycles render on the Apple GPU can abort (SIGABRT in `ccl::path_cache_get`) while compiling Metal
kernels; the log stops at "Updating Meshes". Renders also crashed with about five GPU renders running at once.
**Evidence:** three macOS crash reports on one day; a render that died in the kernel compile was kept as made because the
step's other output file had been written. (not re-checked here)
**What to do:** after every render, check the expected image exists and is not empty; retry (the project retried up to 3
times, keeping each try's log). For emission bakes, use the CPU (`scene.cycles.device = 'CPU'`): no light transport to
speed up and no Metal compile.
**How it was found:** macOS crash reports and missing frames.

### Re-runs are bit-identical at the same thread count; a different thread count changed a drape
**What happens:** the same cloth job, same inputs, same thread count, gives identical vertices. Changing `-t` changed one
drape's result; and the voxel remesh returns the same surface with its points in a different order from run to run, which
changes how a cloth collides with it.
**Evidence:** a pose job re-run: 57 objects, 251,320 evaluated vertices, max difference 0.0 m; settle records
byte-identical. One drape at the default thread count matched its earlier run point for point; at `-t 3` its tunic
differed by up to 0.10 m and the remeshed collision proxy had a different point count. On another design a whole chain at
`-t 3` reproduced every measured number. Separately, a remeshed proxy had 15,184 of 41,244 points at other indices between
runs, even at `-t 1`, and two drapes of the same inputs differed by 2-6 cm until the remesh output was re-sorted into a
canonical order. (Not reproduced here with identical input: the remesh returned the identical point array in every
run, at 1 and 12 threads, `experiments/modifiers/remesh_order.py`; a 1e-6 m change in the input reordered most points,
so the project's input probably differed slightly between runs.)
**What to do:** fix the thread count per stage and record it with any cached result; re-sort freshly remeshed meshes by
position (points by x, y, z; faces by their points) before simulating against them.
**How it was found:** a thread-determinism test.

### Blender's bundled Python has no Pillow
**What happens:** image drawing written with PIL cannot run inside Blender.
**Evidence:** label drawing for a sheet had to move out of Blender. Re-checked
`[exp: experiments/running/lesson_checks.py]`: no PIL in 4.5.14's Python; numpy 1.26.4, OpenImageIO, MaterialX 1.39.2 and
requests are bundled.
**What to do:** write a sidecar JSON from Blender (positions projected through the camera) and draw in an outside Python;
or use numpy with `Image.pixels`, or the bundled OpenImageIO.
**How it was found:** an import error.

### Read what this Blender can do from Blender itself
**What happens:** modifiers, nodes, cloth and rigid-body settings, bake types, passes, operators, bundled add-ons and
node-group assets differ by version and build.
**Evidence:** the project's inventory of 4.5.14 (headless, factory settings): 83 modifiers, 28 constraints, 222 geometry
nodes and 47 function nodes, 104 shader nodes, 107 compositor nodes, 57 cloth settings, 12 bake types, 30 render passes,
8 rigid-body joint types, 15 bundled add-ons. (not re-checked here; this guide's own inventory is `[inv]`)
**What to do:** dump `bl_rna` and operators from a `-b --factory-startup` run to JSON and look names up there.
**How it was found:** surveying Blender's features before building a pipeline stage.
