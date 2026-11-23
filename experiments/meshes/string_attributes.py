"""STRING attributes on a mesh in 4.5: can they be written and read with foreach_set / foreach_get, one element at a
time, through bmesh; how long and which characters they hold; whether they survive a save and reload and a modifier."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bmesh  # noqa: E402
import bpy  # noqa: E402
import numpy as np  # noqa: E402

import exp  # noqa: E402

E = exp.Experiment(__file__)
TMP = tempfile.mkdtemp(prefix="bfg-str-")


def cube(name="Cube"):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


ob = cube()
me = ob.data
domains = {}
for dom in ("POINT", "EDGE", "FACE", "CORNER"):
    try:
        a = me.attributes.new(f"s_{dom}", "STRING", dom)
        domains[dom] = dict(ok=True, length=len(a.data), item_type=type(a.data[0]).__name__,
                            value_type=type(a.data[0].value).__name__, default=a.data[0].value)
    except Exception as e:  # noqa: BLE001
        domains[dom] = str(e).splitlines()[0]
E.fact("attributes.new(name, 'STRING', domain) works on every mesh domain; each element's .value is bytes (not "
       "str), b'' to start", **domains)

a = me.attributes["s_POINT"]
names = [f"v{i}" for i in range(8)]
tries = {}
for label, arr in (("list of str", names), ("list of bytes", [n.encode() for n in names]),
                   ("numpy object array", np.array(names, dtype=object)), ("numpy bytes array", np.array(names, dtype="S8"))):
    try:
        a.data.foreach_set("value", arr)
        tries[label] = "accepted: " + repr([d.value for d in a.data][:3])
    except Exception as e:  # noqa: BLE001
        tries[label] = f"{type(e).__name__}: {str(e).splitlines()[0][:160]}"
gets = {}
for label, arr in (("list", [""] * 8), ("list of None", [None] * 8), ("numpy object", np.empty(8, dtype=object))):
    try:
        a.data.foreach_get("value", arr)
        gets[label] = "filled: " + repr(list(arr)[:3])
    except Exception as e:  # noqa: BLE001
        gets[label] = f"{type(e).__name__}: {str(e).splitlines()[0][:160]}"
E.fact("foreach_set and foreach_get do not work on a STRING attribute: every form raised RuntimeError 'internal error "
       "setting the array', and the log says 'Only boolean, int, float, and enum properties supported'",
       foreach_set=tries, foreach_get=gets)

try:
    a.data[0].value = "text"
    str_set = "accepted"
except TypeError as e:
    str_set = str(e).splitlines()[0]
for d, n in zip(a.data, names):
    d.value = n.encode()
loop_read = [d.value for d in a.data]
uni = "héllo ✓ 日本"
a.data[0].value = uni.encode("utf-8")
long = "x" * 1000
a.data[1].value = long.encode()
E.fact("Element by element works with bytes: data[i].value = 'text'.encode() and data[i].value.decode(); assigning a "
       "str raises TypeError. UTF-8 text came back as written; a 1,000-byte string came back shortened",
       str_assignment=str_set, loop_read=[x.decode() for x in loop_read],
       unicode_back=a.data[0].value.decode("utf-8"), unicode_equal=a.data[0].value.decode("utf-8") == uni,
       long_written=len(long), long_read=len(a.data[1].value))

# bmesh
a.data[1].value = b"v1"
bm = bmesh.new()
bm.from_mesh(me)
lay = bm.verts.layers.string.get("s_POINT")
bm.verts.ensure_lookup_table()
bm_val = bm.verts[0][lay] if lay else None
bm.verts[3][lay] = b"from bmesh"
try:
    bm.verts[4][lay] = "str into bmesh"
    bm_str = "accepted"
except Exception as e:  # noqa: BLE001
    bm_str = f"{type(e).__name__}: {str(e).splitlines()[0][:160]}"
bm.to_mesh(me)
bm.free()
E.fact("bmesh sees the attribute as bm.verts.layers.string['s_POINT'], its values bytes too; writing bytes "
       "through bmesh reaches the mesh; writing a str", layer_found=lay is not None,
       bmesh_value=repr(bm_val), after_to_mesh=me.attributes["s_POINT"].data[3].value, bmesh_str_assignment=bm_str)

# save and reload
path = os.path.join(TMP, "s.blend")
bpy.ops.wm.save_as_mainfile(filepath=path)
bpy.ops.wm.open_mainfile(filepath=path)
me = bpy.data.meshes["Cube"]
back = [d.value for d in me.attributes["s_POINT"].data]
E.fact("STRING attributes are saved in the .blend and read back", values_after_reload=[x.decode() for x in back],
       unicode_after_reload=back[0].decode("utf-8") == uni)

# a modifier: what reaches the evaluated mesh
ob = bpy.data.objects["Cube"]
mods = {}
for mtype in ("SUBSURF", "TRIANGULATE", "MIRROR"):
    md = ob.modifiers.new("m", mtype)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg).data
    at = ev.attributes.get("s_POINT")
    vals = [d.value.decode() for d in at.data] if at else None
    mods[mtype] = dict(present=at is not None, data_type=at.data_type if at else None, points=len(ev.vertices),
                       first_values=vals[:10] if vals else None, empty=sum(1 for v in vals if v == "") if vals else None)
    ob.modifiers.remove(md)
E.fact("A STRING attribute reaches the evaluated mesh through modifiers: the original points keep their text, the 18 "
       "points a level-1 Subdivision adds to a cube get an empty string (no interpolation), and Mirror copies the text "
       "to the mirrored points", **mods)

os.remove(path)
for f in os.listdir(TMP):
    os.remove(os.path.join(TMP, f))
os.rmdir(TMP)
E.save()
