"""Text objects with the built-in font against fonts loaded from files (bpy.data.fonts.load): which characters each
draws, whether the .woff2 fonts shipped with Blender load, a system .ttf and .ttc, check_existing, and whether
complex scripts are shaped (a Devanagari conjunct against its parts)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import bpy  # noqa: E402
import numpy as np  # noqa: E402

import exp  # noqa: E402

E = exp.Experiment(__file__)
FDIR = os.path.join(bpy.utils.system_resource("DATAFILES"), "fonts")
SYSTEM = ["/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Helvetica.ttc"]


def measure(text, font=None):
    cu = bpy.data.curves.new("t", "FONT")
    cu.body = text
    if font is not None:
        cu.font = font
    ob = bpy.data.objects.new("t", cu)
    bpy.context.scene.collection.objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    n = len(me.vertices)
    if n:
        co = np.zeros(n * 3, np.float32)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        width = round(float(co[:, 0].max() - co[:, 0].min()), 3)
    else:
        width = 0.0
    bpy.data.objects.remove(ob)
    bpy.data.curves.remove(cu)
    bpy.data.meshes.remove(me)
    return n, width


CHARS = {"H": "H", "e acute": "é", "check mark": "✓", "CJK": "日", "Devanagari ka": "क", "Arabic beh": "ب",
         "emoji": "😀"}
NOTDEF = "\u0378"   # an unassigned code point no font maps: it shows the font's 'missing glyph' shape


def coverage(font):
    """Per character: vertices and width, and whether it differs from the font's missing-glyph shape."""
    nd = measure(NOTDEF, font)
    out = {}
    for k, c in CHARS.items():
        v, w = measure(c, font)
        out[k] = dict(vertices=v, width=w, drawn=v > 0 and (v, w) != nd)
    return out, dict(vertices=nd[0], width=nd[1])


builtin, builtin_nd = coverage(None)
loaded = {}
fonts = {}
for fn in ("DejaVuSansMono.woff2", "Inter.woff2", "Noto Sans CJK Regular.woff2", "NotoSansDevanagari-Regular.woff2",
           "NotoSansArabic-VariableFont_wdth,wght.woff2", "NotoEmoji-VariableFont_wght.woff2"):
    path = os.path.join(FDIR, fn)
    try:
        f = bpy.data.fonts.load(path)
        fonts[fn] = f
        cov, nd = coverage(f)
        loaded[fn] = dict(name=f.name, filepath_is_set=bool(f.filepath), packed=f.packed_file is not None,
                          missing_glyph=nd, chars=cov, hello_width=measure("Hello", f)[1])
    except Exception as e:  # noqa: BLE001
        loaded[fn] = f"{type(e).__name__}: {str(e).splitlines()[0][:200]}"
same_as = {}
for k in CHARS:
    same_as[k] = [dict(font=fn, width_ratio=round(builtin[k]["width"] / d["chars"][k]["width"], 3))
                  for fn, d in loaded.items() if isinstance(d, dict) and d["chars"][k]["drawn"]
                  and d["chars"][k]["vertices"] == builtin[k]["vertices"]]
E.fact("The built-in font (Bfont Regular) draws every character tried, including CJK, Devanagari, Arabic and emoji: "
       "those glyphs have exactly the vertex count of the same character in the matching bundled Noto font (drawn "
       "at a different size), so the built-in font falls back to Blender's bundled fonts", chars=builtin, missing_glyph=builtin_nd,
       identical_to=same_as)
E.fact("The check mark in 'Héllo ✓' has geometry with the built-in font: the string has more vertices than 'Héllo '",
       with_check=measure("Héllo ✓")[0], without=measure("Héllo ")[0], check_alone=measure("✓")[0])
E.fact("bpy.data.fonts.load() reads the .woff2 fonts shipped in Blender's datafiles/fonts. A loaded font draws only "
       "its own glyphs: characters it lacks come out as its missing-glyph shape (no fallback, no error)",
       builtin_hello_width=measure("Hello")[1], **loaded)

system = {}
for path in SYSTEM:
    if not os.path.exists(path):
        system[os.path.basename(path)] = "not on this machine"
        continue
    try:
        f = bpy.data.fonts.load(path)
        cov, nd = coverage(f)
        system[os.path.basename(path)] = dict(name=f.name, missing_glyph=nd, drawn=[k for k in CHARS if cov[k]["drawn"]],
                                              hello_width=measure("Hello", f)[1])
    except Exception as e:  # noqa: BLE001
        system[os.path.basename(path)] = f"{type(e).__name__}: {str(e).splitlines()[0][:200]}"
E.fact("System fonts load the same way: a .ttf, and a .ttc collection (its first face)", **system)

p = os.path.join(FDIR, "Inter.woff2")
n0 = len(bpy.data.fonts)
a = bpy.data.fonts.load(p)
b = bpy.data.fonts.load(p, check_existing=True)
n1 = len(bpy.data.fonts)
c = bpy.data.fonts.load(p, check_existing=False)
E.fact("fonts.load() of a path already loaded makes a new datablock (check_existing defaults to False); "
       "check_existing=True returned the one already loaded", default_check_existing=bpy.data.fonts.bl_rna.functions["load"].parameters["check_existing"].default,
       first=a.name, with_check_existing=b.name, same=(a == fonts.get("Inter.woff2")) or (b == a),
       without=c.name, fonts_before=n0, fonts_after=len(bpy.data.fonts))

dev = fonts.get("NotoSansDevanagari-Regular.woff2")
if dev:
    conj = measure("क्ष", dev)
    parts = [measure(ch, dev) for ch in ("क", "्", "ष")]
    word = measure("नमस्ते", dev)
    E.fact("No shaping: the Devanagari conjunct क्ष (ka + virama + ssa) came out as its three separate glyphs, its "
           "vertices exactly the sum of the three drawn alone: the text was not shaped into a conjunct",
           conjunct=dict(vertices=conj[0], width=conj[1]),
           parts=[dict(vertices=v, width=w) for v, w in parts], sum_part_vertices=sum(v for v, _ in parts),
           namaste=dict(vertices=word[0], width=word[1]))
E.save(fonts_dir_listed=sorted(os.listdir(FDIR))[:5])
