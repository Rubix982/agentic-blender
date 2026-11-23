# Extensions: the community's most-downloaded add-ons, headless

Blender 4.5.14 LTS. Tags: `[exp: path]` measured here, `[doc: link]` documentation. Experiment:
`experiments/extensions/top_addons.py` (with `probe/addon_probe.py`) in the source repository.

Since 4.2 most add-ons that once shipped with Blender are extensions, installed from extensions.blender.org. It lists
1,062 add-ons (and 184 themes) for Blender 4.5.14 on macOS arm64. The 20 most downloaded were installed
here into a throwaway profile, every one enabled, and each of their operators was called headless with default
settings on a fresh cube. 13 of the 20 had at least one operator that finished and changed the scene.
`[exp: experiments/extensions/top_addons.py]`

## What goes wrong most often

1. **Installing into the user's Blender to try something.** Install into a throwaway profile instead:
   `BLENDER_USER_RESOURCES=<new folder> blender -c extension install-file -r user_default PACKAGE.zip`. A later
   `blender -b --factory-startup` with the same variable still finds the package, and
   `addon_utils.enable("bl_ext.user_default.<id>", default_set=True)` enabled all 20.
   `[exp: experiments/extensions/top_addons.py]`
2. **Taking FINISHED as done.** Many operators finished and changed nothing: 4 of LoopTools' 9 (Bridge, Circle, Curve
   and Space need a loop or a curve selected), and A.N.T. Landscape's `mesh.landscape_add` returned `PASS_THROUGH` and
   made no terrain. Count objects, vertices or data-blocks after the call. `[exp: experiments/extensions/top_addons.py]`
3. **Panel tools in a script.** Bool Tool changed nothing in 20 operators (they need a canvas and a cutter
   selected; 5 failed their poll on one cube), and Copy Attributes Menu failed the poll on 30 of 31 (it needs two
   selected objects). These are built for a person at the screen; give them the selection they expect, or do the
   same with the data API (`modifiers.md` for booleans). `[exp: experiments/extensions/top_addons.py]`
4. **Running third-party code unguarded.** Check the package against the listing's sha256, read its
   `blender_manifest.toml` permissions, and look for network, subprocess and `exec`/`eval` calls before running it.
   Of the 20, Ucupaint imports `requests` (it declares only file access); MPFB declares optional network use for a
   local MakeHuman and calls a subprocess only to open a folder; Extra Mesh Objects evaluates the user's own
   equations (its 3D function surface). `[exp: experiments/extensions/top_addons.py]`

## The twenty

Downloads as listed on extensions.blender.org (sorted by downloads, 2026-11-23). "Declares": the manifest's
permissions. "Scan": lines in the package's Python matching network, subprocess or `exec`/`eval` calls. Operators:
all it registers; then those that finished and changed the scene, finished with no change, failed their poll, raised
an error, and were not run (they take a file path, or their names suggest a browser, preferences or installing).
`[exp: experiments/extensions/top_addons.py]`:

| Add-on | Downloads | Declares | Scan | Operators | Changed | No change | Poll failed | Error | Not run | Worked headless |
|---|---|---|---|---|---|---|---|---|---|---|
| LoopTools | 2,358,445 | none | none | 9 | 3 | 4 | 0 | 0 | 0 | `mesh.looptools_flatten`, `mesh.looptools_gstretch`, `mesh.looptools_relax` |
| Extra Mesh Objects | 1,277,685 | none | exec_eval 10 | 33 | 32 | 0 | 1 | 0 | 0 | `mesh.add_beam`, `mesh.add_equilateral_grid`, `mesh.add_mesh_rock`, `mesh.honeycomb_add` and 28 more |
| Bool Tool | 1,262,775 | none | none | 20 | 0 | 2 | 5 | 0 | 0 | — |
| Extra Curve Objects | 887,151 | none | none | 17 | 9 | 0 | 3 | 1 | 1 | `curve.add_braid`, `curve.celtic_links`, `curve.curveaceous_galore`, `curve.simple` and 5 more |
| 3D Print Toolbox | 699,092 | files | none | 20 | 1 | 14 | 0 | 4 | 1 | `mesh.print3d_bisect` |
| MMD Tools | 638,634 | files | none | 118 | 1 | 16 | 25 | 55 | 16 | `mmd_tools.create_mmd_model_root_object` |
| A.N.T.Landscape | 521,021 | none | none | 6 | 0 | 3 | 0 | 1 | 0 | — |
| F2 | 438,321 | none | none | 1 | 0 | 0 | 0 | 0 | 0 | — |
| Cell Fracture | 386,650 | none | none | 1 | 1 | 0 | 0 | 0 | 0 | `object.add_fracture_cell_objects` |
| VRM format | 348,397 | files | none | 160 | 1 | 10 | 0 | 0 | 14 | `icyp.make_basic_armature` |
| Archimesh | 338,133 | none | none | 20 | 14 | 0 | 0 | 2 | 3 | `mesh.archimesh_books`, `mesh.archimesh_column`, `mesh.archimesh_door`, `mesh.archimesh_japan` and 10 more |
| Ucupaint | 333,051 | files | network 1, subprocess 3 | 143 | 2 | 4 | 108 | 16 | 13 | `wm.y_new_image_atlas_segment_test`, `wm.y_quick_ypaint_node_setup` |
| BoltFactory | 329,307 | none | none | 1 | 1 | 0 | 0 | 0 | 0 | `mesh.bolt_add` |
| MPFB | 327,305 | files; network | subprocess 2 | 145 | 5 | 10 | 63 | 31 | 36 | `mpfb.create_human`, `mpfb.create_makeskin_material`, `mpfb.create_random_human`, `mpfb.create_random_human_batch` and 1 more |
| Mio3 UV | 324,692 | files | none | 48 | 3 | 27 | 0 | 7 | 0 | `mesh.mio3_uvmesh`, `mio3uv.checker_map`, `mio3uv.checker_map_cleanup` |
| Auto Mirror | 322,754 | none | none | 2 | 0 | 0 | 0 | 2 | 0 | — |
| Sapling Tree Gen | 308,526 | none | exec_eval 1 | 3 | 1 | 0 | 0 | 2 | 0 | `curve.tree_add` |
| MeasureIt | 294,318 | none | none | 17 | 0 | 1 | 0 | 16 | 0 | — |
| Copy Attributes Menu | 286,085 | none | none | 31 | 0 | 0 | 30 | 1 | 0 | — |
| Import Autodesk MAX | 270,399 | files | none | 1 | 0 | 0 | 0 | 0 | 1 | — |

For environments the useful ones measured here: Archimesh (14 operators build doors, kitchens, roofs, lamps, books,
columns), Sapling (`curve.tree_add` made a curve tree with default settings), Extra Mesh Objects (32 of 33 add
primitives, `mesh.add_mesh_rock` among them), BoltFactory, Cell Fracture (`object.add_fracture_cell_objects` broke the
cube into 8 pieces), and MPFB (`mpfb.create_human` made a 19,158-vertex human; `mpfb.create_random_human_batch` made 10
humans with armatures). `[exp: experiments/extensions/top_addons.py]`

## Using one in a script

```python
import addon_utils, bpy
addon_utils.enable("bl_ext.user_default.sapling_tree_gen", default_set=True)   # installed into $BLENDER_USER_RESOURCES
before = len(bpy.data.objects)
bpy.ops.curve.tree_add()
assert len(bpy.data.objects) > before, "the operator finished but made nothing"
```

The module name is `bl_ext.<repository>.<id>`: the id is the manifest's, which can differ from the website's slug
(`sapling-tree-gen` is `sapling_tree_gen`, `bool-tool` is `bool_tool`). `[exp: experiments/extensions/top_addons.py]`

## How the twenty were run, and what that leaves out

Each package was checked against the listing's sha256 and scanned before anything ran, then installed into a profile
under `/private/tmp`. Every Blender run was wrapped in macOS `sandbox-exec` with this profile (home folder and paths
filled in at run time):

```
(version 1)
(allow default)
(deny network*)
(deny file-write* (subpath "<home>"))
(allow file-write* (subpath "<throwaway profile>"))
(deny lsopen)
(deny appleevent-send)
(deny process-exec)
(allow process-exec (subpath "<Blender.app>"))
```

Each add-on had its own Blender process; none crashed or hung. All 20 took 73.7 s. Each operator got a fresh 2 m
cube, in object mode, or in edit mode with everything selected if object mode failed its poll, and was called with
its defaults. "Changed" means the object count, vertex count, sum of vertex coordinates or a data-block count moved.
`[exp: experiments/extensions/top_addons.py]`

Not measured: operators given the selection or settings they are made for (Bool Tool with a canvas and a cutter, F2
with a hole's boundary selected, A.N.T. Landscape with its `refresh` flag set, Sapling with leaves). That pass runs
the add-ons' code again and has not been run.
