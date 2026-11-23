"""Is an attribute reference still safe to use after more attributes are added to the mesh?

Run: python3 tools/run.py experiments/meshes/attribute_stale_ref.py -- N   (N attributes added; default 100)
The result file is saved BEFORE the old reference is touched, with status 'touching'. If the file still says 'touching'
after the run, Blender died while using the stale reference (run.py prints the exit code, -11 is a segfault).
"""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy
import exp
E = exp.Experiment(__file__)
n = int(sys.argv[sys.argv.index("--") + 1]) if "--" in sys.argv and len(sys.argv) > sys.argv.index("--") + 1 else 100
E.name = f"attribute_stale_ref-{n}"
bpy.ops.mesh.primitive_cube_add()
me = bpy.context.object.data
a1 = me.attributes.new("w", "FLOAT", "POINT")
for k in range(n):
    me.attributes.new(f"extra{k}", "FLOAT", "POINT")
E.save(status="touching", added=n)
try:
    a1.data[0].value = 5.0
    err = None
except Exception as e:
    err = f"{type(e).__name__}: {e}"
got = me.attributes["w"].data[0].value
E.fact(f"after {n} more attributes.new calls, writing through the old reference " + ("reached the right layer" if got == 5.0 else f"did not reach the layer named 'w' ({err})"),
       added=n, value_read_by_name=got, error=err)
E.save(status="survived", added=n)
