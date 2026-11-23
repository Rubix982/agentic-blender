"""Modifier order: where modifiers.new puts a modifier, how to reorder from Python, and how much order changes the result."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy
import exp
E = exp.Experiment(__file__)


def ev_sig(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    me = ob.evaluated_get(dg).data
    return (len(me.vertices), round(sum(abs(v.co.x) + abs(v.co.y) + abs(v.co.z) for v in me.vertices), 3))


def ev_counts(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    me = ob.evaluated_get(dg).data
    return (len(me.vertices), len(me.edges), len(me.polygons))

bpy.ops.mesh.primitive_cube_add()
ob = bpy.context.object
b = ob.modifiers.new("Bevel", "BEVEL"); b.width = 0.2; b.segments = 2
s = ob.modifiers.new("Subdivision", "SUBSURF"); s.levels = 1
E.fact("modifiers.new appends at the end of the stack (evaluated top to bottom)", order=[m.name for m in ob.modifiers])
c1 = ev_sig(ob)
has_move = hasattr(ob.modifiers, "move")
ob.modifiers.move(1, 0)
E.fact("ObjectModifiers.move(from_index, to_index) reorders without an operator", has_move=has_move, order=[m.name for m in ob.modifiers])
c2_stale = ev_sig(ob)
ob.update_tag()
c2 = ev_sig(ob)
sig_moved = ev_sig(ob)
# fresh objects built in each order
def build(order):
    bpy.ops.mesh.primitive_cube_add(location=(5, 0, 0))
    o = bpy.context.object
    for t in order:
        if t == "BEVEL":
            m = o.modifiers.new("Bevel", "BEVEL"); m.width = 0.2; m.segments = 2
        else:
            m = o.modifiers.new("Subdivision", "SUBSURF"); m.levels = 1
    return o
o1, o2 = build(["BEVEL", "SUBSURF"]), build(["SUBSURF", "BEVEL"])
s1, s2 = ev_sig(o1), ev_sig(o2)
E.fact(f"bevel-then-subsurf and subsurf-then-bevel on a cube give (verts, sum|co|) {s1} and {s2}: " + ("different meshes" if s1 != s2 else "the same mesh"),
       bevel_then_subsurf=s1, subsurf_then_bevel=s2, moved_stack=sig_moved, bevel_limit_method=b.limit_method)
E.fact("after modifiers.move(1, 0) the evaluated mesh " + ("already matched the new order without update_tag()" if c2_stale == s2 else "kept the old order until update_tag()"),
       right_after_move=c2_stale, after_update_tag=c2, fresh_subsurf_then_bevel=s2, before_move=c1)
try:
    with bpy.context.temp_override(object=ob, active_object=ob):
        r = list(bpy.ops.object.modifier_move_to_index(modifier="Bevel", index=0))
except Exception as e:
    r = f"{type(e).__name__}: {e}"
E.fact("bpy.ops.object.modifier_move_to_index(modifier=, index=) also works headless", result=r, order=[m.name for m in ob.modifiers])

# name uniqueness and lookup
m2 = ob.modifiers.new("Bevel", "BEVEL")
E.fact("a second modifier given an existing name is renamed with a .001 suffix; look modifiers up by the returned object, not the name you asked for",
       name=m2.name)
ob.modifiers.remove(m2)
# invalid type
try:
    ob.modifiers.new("x", "SUBDIVISION"); bad = "accepted"
except Exception as e:
    bad = f"{type(e).__name__}: {e}"
E.fact("the subdivision modifier's type is SUBSURF; 'SUBDIVISION' raises", error=bad[:200])
# show_viewport vs show_render, and which the depsgraph uses in -b
s = ob.modifiers["Subdivision"]
s.levels = 1; s.render_levels = 3
E.fact("evaluated_depsgraph_get() in background mode evaluates with viewport settings (levels, not render_levels)",
       verts=ev_counts(ob)[0], levels=s.levels, render_levels=s.render_levels)
s.show_viewport = False
E.fact("show_viewport=False removes the modifier from the evaluated mesh in -b", verts=ev_counts(ob)[0])
s.show_viewport = True
# pin to last
E.fact("modifiers have use_pin_to_last (4.2+) to keep one at the end", has=hasattr(s, "use_pin_to_last"))
E.save()
