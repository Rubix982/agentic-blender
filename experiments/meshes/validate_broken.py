"""What does mesh.validate() fix on broken input, and what does it leave?"""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy
import exp
E = exp.Experiment(__file__)

cases = {
    "duplicate_face": ([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)], [(0, 1, 2, 3), (0, 1, 2, 3)]),
    "repeated_vertex_in_face": ([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)], [(0, 1, 1, 2)]),
    "two_vertex_face": ([(0, 0, 0), (1, 0, 0), (1, 1, 0)], [(0, 1)]),
    "coincident_vertices": ([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 0, 0)], [(0, 1, 2), (3, 1, 2)]),
}
res = {}
for name, (v, f) in cases.items():
    me = bpy.data.meshes.new(name)
    try:
        me.from_pydata(v, [], f)
        built = "ok"
    except Exception as e:
        built = f"{type(e).__name__}: {e}"
    before = (len(me.vertices), len(me.edges), len(me.polygons))
    changed = me.validate(verbose=True)
    after = (len(me.vertices), len(me.edges), len(me.polygons))
    res[name] = dict(built=built, before=before, validate_changed=changed, after=after)
    print(name, res[name])

# out of range index: from_pydata raises?
me = bpy.data.meshes.new("oob")
try:
    me.from_pydata([(0, 0, 0), (1, 0, 0), (1, 1, 0)], [], [(0, 1, 7)])
    oob = "accepted"
except Exception as e:
    oob = f"{type(e).__name__}: {e}"
oob_counts = (len(me.vertices), len(me.edges), len(me.polygons))
oob_changed = me.validate(verbose=True)
res["out_of_range_index"] = dict(built=oob, before=oob_counts, validate_changed=oob_changed,
                                 after=(len(me.vertices), len(me.edges), len(me.polygons)))

for k, r in res.items():
    E.fact(f"validate() on a mesh with a {k.replace('_', ' ')}: counts (v,e,f) {r['before']} -> {r['after']}, returned {r['validate_changed']}", **r)
E.fact("validate() does not merge coincident vertices (that is bmesh.ops.remove_doubles or the Weld modifier)",
       before=res["coincident_vertices"]["before"], after=res["coincident_vertices"]["after"])
E.save(cases=res)
