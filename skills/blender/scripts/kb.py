#!/usr/bin/env python3
"""Look things up in Blender 4.5's own description of itself (the inventory next to this script).

  kb.py find TERM [TERM...] [--kind struct|prop|op|node|py] [-n 25]   search types, properties, functions (also those
                                   Blender defines in Python, like Mesh.from_pydata), operators, nodes, sockets, modules
  kb.py struct NAME [--all]        a type: its properties (type, default, range, enum items), functions, base, and
                                   the paths that reach it from bpy.context / bpy.data (--all: inherited ones too)
  kb.py prop STRUCT.NAME           one property in full (every enum item), or a function or Python-defined member
  kb.py op NAME                    an operator (bpy.ops.mesh.bevel, mesh.bevel or MESH_OT_bevel): its parameters
  kb.py node NAME                  a node (ShaderNodeBsdfPrincipled, or its label "Principled BSDF"): the trees it
                                   goes in, its sockets (name, identifier, type, default), its own properties
  kb.py nodes [shader|geometry|compositor|texture] [TERM]   list node types
  kb.py py NAME                    a Python function or class (bmesh.ops.bevel, mathutils.geometry.delaunay_2d_cdt,
                                   bpy_extras.object_utils.world_to_camera_view) with its docstring
  kb.py path STRUCT                how to reach a type from bpy.context or bpy.data (e.g. CyclesRenderSettings);
                                   <T> marks a place that holds a more general type, where a T can be found
  kb.py enums                      enums whose values depend on the machine or file (engines, view transforms,
                                   colour spaces, GPU devices)
  kb.py factory [SECTION]          a fresh file's values (render, cycles, eevee, view_settings, ...)
  kb.py meta                       version, build, libraries, add-ons, counts
  kb.py keys KEYS [--map NAME]     what a key press does in the default keymap ("shift a", "ctrl r", "alt click",
                                   "numpad 1", "g"), in every editor and mode, with the operator call and, for a key
                                   that opens a menu, the menu
  kb.py keys --op OPERATOR         which keys run an operator;  kb.py keys --map NAME  everything in one keymap
  kb.py menu "Add > Mesh > Cylinder" [--in VIEW3D]   follow a menu path as a tutorial gives it, to the call it makes
  kb.py menu MENU_ID               one menu's entries (VIEW3D_MT_add);  kb.py menu --op OPERATOR  where an operator
                                   sits in the menus, with the key that opens each top menu

Everything printed was read from Blender 4.5.14 LTS by inventory.py; nothing is from memory. "default" is the value
Blender registers; "(a new one starts at X)" is what a node, modifier or constraint made from Python really starts with.
"""
import gzip
import json
import os
import re
import sys
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
INV = os.path.join(HERE, "..", "inventory")
_cache = {}


def load(name):
    if name not in _cache:
        path = os.path.join(INV, name)
        if name.endswith(".jsonl.gz"):
            with gzip.open(path, "rt", encoding="utf-8") as f:
                _cache[name] = [json.loads(line) for line in f]
        else:
            with open(path, encoding="utf-8") as f:
                _cache[name] = json.load(f)
    return _cache[name]


def structs():
    if "S" not in _cache:
        _cache["S"] = {s["id"]: s for s in load("structs.jsonl.gz")}
    return _cache["S"]


def wrap(text, indent, width=118):
    words, lines, cur = (text or "").split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width - indent and cur:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}" if cur else w
    if cur:
        lines.append(cur)
    return ("\n" + " " * indent).join(lines)


def made_values():
    """struct id -> the values a newly made modifier or constraint of that type starts with (typed.json)."""
    if "MADE" not in _cache:
        made = {}
        try:
            t = load("typed.json")
            for group in ("modifiers", "constraints"):
                for rec in t[group].values():
                    if rec.get("struct"):
                        made[rec["struct"]] = rec.get("new_values", {})
        except (OSError, KeyError):
            pass
        _cache["MADE"] = made
    return _cache["MADE"]


def fmt_prop(p, full=False, indent=2, new=None):
    t = p["type"].lower()
    if p.get("array"):
        t += f"[{p['array']}]"
    if p.get("subtype"):
        t += f" {p['subtype'].lower()}"
    if p.get("unit"):
        t += f" ({p['unit'].lower()})"
    if p.get("to"):
        t += f" -> {p['to']}"
    bits = [f"{p['id']}: {t}"]
    if "default" in p and p["type"] not in ("POINTER", "COLLECTION"):
        bits.append(f"= {json.dumps(p['default'])}")
    if p.get("range") and p["range"] != [None, None]:
        r = p["range"]
        if p.get("soft"):
            bits.append(f"[{p['soft'][0]} .. {p['soft'][1]}; hard {r[0]} .. {r[1]}]")
        else:
            bits.append(f"[{r[0]} .. {r[1]}]")
    if new is not None and p["id"] in new and p["type"] not in ("POINTER", "COLLECTION"):
        nv = new[p["id"]]
        if nv != p.get("default") and not (isinstance(nv, str) and nv.startswith("<")):
            bits.append(f"(a new one starts at {json.dumps(nv)})")
    flags = [f for f in ("readonly", "required", "flag", "dynamic") if p.get(f)]
    if flags:
        bits.append("{" + ",".join(flags) + "}")
    line = " " * indent + " ".join(bits)
    if p.get("name") and p["name"] != p["id"]:
        line += f"  \"{p['name']}\""
    if p.get("desc"):
        line += "\n" + " " * (indent + 4) + wrap(p["desc"], indent + 4)
    if p.get("items"):
        if full or len(p["items"]) <= 12:
            for i in p["items"]:
                d = f"  {i['desc']}" if full and i.get("desc") else ""
                line += "\n" + " " * (indent + 4) + f"- {i['id']}" + (f" ({i['name']})" if i["name"] != i["id"] else "") + d
        else:
            line += "\n" + " " * (indent + 4) + "one of: " + wrap(", ".join(i["id"] for i in p["items"]), indent + 12)
    return line


def resolve_struct(name):
    S = structs()
    if name in S:
        return S[name]
    low = name.lower()
    for key in ("id", "alias", "name"):   # an identifier match wins over a display-name match
        hits = [s for s in S.values() if (s.get(key) or "").lower() == low]
        hits.sort(key=lambda s: (bool(s.get("ui")), "Node" in s["id"], len(s["id"])))
        if hits:
            return hits[0]
    cands = [s["id"] for s in S.values() if low in s["id"].lower() and not s.get("ui")]
    sys.exit(f"no type {name!r}" + (f"; close: {', '.join(sorted(cands)[:15])}" if cands else ""))


def chain(s):
    """The struct and its bases, nearest first."""
    S, out = structs(), []
    while s:
        out.append(s)
        s = S.get(s.get("base"))
    return out


GENERIC = {"PropertyGroup", "ID", "Struct", "AnyType", "bpy_struct"}


def paths_to(target, limit=6):
    """Shortest attribute paths from bpy.context / bpy.data to a type, breadth first over pointers and collections.
    A collection of a base type (Object.modifiers holds Modifier) is followed into each kind of it, written
    modifiers[...]<ClothModifier>."""
    S = structs()
    edges, subs = {}, {}
    for s in S.values():
        if s.get("ui"):
            continue
        edges[s["id"]] = [(p["id"] + ("[...]" if p["type"] == "COLLECTION" else ""), p["to"])
                          for c in chain(s) for p in c["props"]
                          if p.get("to") and p["type"] in ("POINTER", "COLLECTION")
                          and p["id"] not in ("rna_type", "bl_rna", "id_data", "original", "evaluated_get")]
        for c in chain(s)[1:]:
            if c["id"] not in GENERIC:
                subs.setdefault(c["id"], []).append(s["id"])
    found, seen = [], {"Context", "BlendData"}
    q = deque([("bpy.context", "Context"), ("bpy.data", "BlendData")])
    while q and len(found) < limit:
        path, t = q.popleft()
        if path.replace("[...]", "").count(".") > 7:
            continue
        moves = [(f"{path}.{a}", to) for a, to in edges.get(t, [])]
        for sub in subs.get(t, []):
            moves += [(f"{path}<{sub}>.{a}", to) for a, to in edges.get(sub, []) if (a, to) not in edges.get(t, [])]
        for np_, to in moves:
            if to == target or (target in subs.get(to, []) and to not in GENERIC):
                found.append(np_ if to == target else f"{np_}<{target}>")
                if len(found) >= limit:
                    break
            elif to not in seen:
                seen.add(to)
                q.append((np_, to))
    return found


def cmd_struct(args):
    s = resolve_struct(args[0])
    show_all = "--all" in args
    print(f"{s['id']}  \"{s['name']}\"" + (f"  (bpy.types.{s['alias']})" if s.get("alias") else "")
          + (f"  [add-on: {s['module']}]" if s.get("module") else ""))
    if s.get("desc"):
        print("  " + wrap(s["desc"], 2))
    bases = [c["id"] for c in chain(s)[1:]]
    if bases:
        print("  base: " + " < ".join(bases))
    ps = paths_to(s["id"], 4)
    if ps:
        print("  reached by: " + ("\n             ".join(ps)))
    for c in (chain(s) if show_all else [s]):
        if c is not s:
            print(f"\n  -- inherited from {c['id']} --")
        print(f"\n  properties ({len(c['props'])}):" if c is s else "")
        for p in c["props"]:
            print(fmt_prop(p, new=made_values().get(s["id"])))
        if c["funcs"]:
            print(f"\n  functions ({len(c['funcs'])}):")
            for f in c["funcs"]:
                args_ = ", ".join(p["id"] + ("" if p.get("required") else "=" + json.dumps(p.get("default")))
                                  for p in f["params"])
                ret = ", ".join(f"{r['id']}: {r['type'].lower()}" + (f"->{r['to']}" if r.get("to") else "") for r in f["returns"])
                print(f"  {'@static ' if f.get('static') else ''}{f['id']}({args_})" + (f" -> {ret}" if ret else ""))
                if f.get("desc"):
                    print("      " + wrap(f["desc"], 6))
    pys = [(c["id"], m) for c in (chain(s) if show_all else [s]) for m in c.get("py", [])]
    if pys:
        print(f"\n  defined in Python (bpy_types; not in the RNA, so not in the API's property lists) ({len(pys)}):")
        for owner, m in pys:
            sig = m.get("signature", "") if m["kind"] != "property" else ""
            first = (m.get("desc") or "").split("\n")[0][:110]
            print(f"  {m['kind'][:4]} {m['id']}{sig}" + (f"  — {first}" if first else "") + (f"  [{owner}]" if owner != s["id"] else ""))
    if not show_all and len(bases) > 0:
        n = sum(len(c["props"]) for c in chain(s)[1:])
        print(f"\n  (+{n} inherited properties: --all)")


def cmd_prop(args):
    sname, _, pname = args[0].rpartition(".")
    s = resolve_struct(sname)
    for c in chain(s):
        for p in c["props"]:
            if p["id"] == pname:
                print(f"{s['id']}.{pname}" + (f"  (from {c['id']})" if c is not s else ""))
                print(fmt_prop(p, full=True, new=made_values().get(s["id"])))
                return
    for c in chain(s):
        for f in c["funcs"]:
            if f["id"] == pname:
                args_ = ", ".join(p["id"] + ("" if p.get("required") else "=" + json.dumps(p.get("default"))) for p in f["params"])
                print(f"{s['id']}.{pname}({args_})  (a function" + (f" of {c['id']}" if c is not s else "") + ")")
                if f.get("desc"):
                    print("  " + wrap(f["desc"], 2))
                for p in f["params"] + f["returns"]:
                    print(fmt_prop(p))
                return
        for m in c.get("py", []):
            if m["id"] == pname:
                print(f"{s['id']}.{pname}{m.get('signature', '')}  ({m['kind']} defined in Python on {m['defined_on']})")
                if m.get("desc"):
                    print(m["desc"])
                return
    sys.exit(f"{s['id']} has no property, function or Python member {pname!r}; properties: "
             + ", ".join(p["id"] for c in chain(s) for p in c["props"]))


def cmd_op(args):
    name = args[0].removeprefix("bpy.ops.")
    ops = load("operators.jsonl.gz")
    hit = [o for o in ops if o["id"] == name or o.get("idname") == name or o.get("idname", "").lower() == name.lower()]
    if not hit:
        hit = [o for o in ops if o["id"].split(".", 1)[-1].lower() == name.lower()]
    if not hit:
        hit = [o for o in ops if name.lower() in o["id"].lower()]
        if len(hit) != 1:
            sys.exit(f"no operator {name!r}" + (f"; close: {', '.join(o['id'] for o in hit[:20])}" if hit else ""))
    o = hit[0]
    print(f"bpy.ops.{o['id']}  ({o.get('idname')})  \"{o.get('name')}\"" + (f"  [python: {o['module']}]" if o.get("module") else ""))
    if o.get("desc"):
        print("  " + wrap(o["desc"], 2))
    for p in o.get("params", []):
        print(fmt_prop(p))


def node_by(name):
    nodes = load("nodes.jsonl.gz")
    low = name.lower()
    for n in nodes:
        if n["id"] == name or n["id"].lower() == low:
            return n
    hit = [n for n in nodes if (n.get("label") or n["name"]).lower() == low]
    if len(hit) == 1:
        return hit[0]
    if hit:
        return hit
    hit = [n for n in nodes if low in n["id"].lower() or low in (n.get("label") or n["name"]).lower()]
    return hit[0] if len(hit) == 1 else hit


def cmd_node(args):
    n = node_by(" ".join(args))
    if isinstance(n, list):
        print("several match:")
        for x in n[:40]:
            print(f"  {x['id']:42s} {x.get('label') or x['name']:32s} {','.join(t.replace('NodeTree', '') for t in x['trees'])}")
        return
    print(f"{n['id']}  \"{n.get('label') or n['name']}\"  in: {', '.join(n['trees']) or 'none (abstract)'}"
          + (f"  type={n['type']}" if n.get("type") else ""))
    if n.get("desc"):
        print("  " + wrap(n["desc"], 2))
    for side in ("inputs", "outputs"):
        socks = n.get(side, [])
        if not socks:
            continue
        print(f"\n  {side} ({len(socks)}; '*' = hidden until a setting shows it):")
        for i, s in enumerate(socks):
            t = s["type"].replace("NodeSocket", "")
            dflt = f" = {json.dumps(s['default'])}" if "default" in s else ""
            rng = f" [{s['range'][0]} .. {s['range'][1]}]" if s.get("range") else ""
            ident = f"  id={s['id']!r}" if s["id"] != s["name"] else ""
            print(f"  {'*' if s.get('hidden_by_default') else ' '}[{i}] {s['name']!r}: {t}{dflt}{rng}{ident}"
                  + (" multi-input" if s.get("multi_input") else ""))
    if n.get("props"):
        print("\n  node properties:")
        for p in n["props"]:
            print(fmt_prop(p, new=n.get("new_values", {})))


def cmd_nodes(args):
    kinds = dict(shader="ShaderNodeTree", geometry="GeometryNodeTree", compositor="CompositorNodeTree", texture="TextureNodeTree")
    tree = kinds.get(args[0]) if args else None
    term = (args[1] if tree and len(args) > 1 else (args[0] if args and not tree else "")).lower()
    for n in load("nodes.jsonl.gz"):
        if not n["trees"] or (tree and tree not in n["trees"]):
            continue
        lab = n.get("label") or n["name"]
        if term and term not in n["id"].lower() and term not in lab.lower():
            continue
        print(f"  {n['id']:44s} {lab:34s} {len(n.get('inputs', []))} in / {len(n.get('outputs', []))} out")


def cmd_py(args):
    name = args[0]
    mods = load("modules.jsonl.gz")
    best = None
    for m in sorted(mods, key=lambda m: -len(m["module"])):
        if name == m["module"]:
            print(f"module {m['module']}\n  " + wrap(m.get("doc", ""), 2))
            for e in m.get("members", []):
                first = (e.get("doc") or "").split("\n")[0]
                print(f"  {e['kind']:8s} {e['name']}{e.get('signature', '')}  {first[:90]}")
            return
        if name.startswith(m["module"] + "."):
            rest = name[len(m["module"]) + 1:]
            head, _, member = rest.partition(".")
            for e in m.get("members", []):
                if e["name"] == head:
                    best = (m, e, member)
                    break
            if best:
                break
    if not best:
        hits = [f"{m['module']}.{e['name']}" for m in mods for e in m.get("members", []) if name.lower() in e["name"].lower()]
        sys.exit(f"not found: {name}" + (f"; close: {', '.join(hits[:20])}" if hits else ""))
    m, e, member = best
    if member:
        for mm in e.get("members", []):
            if mm["name"] == member:
                print(f"{m['module']}.{e['name']}.{member}\n\n{mm['doc']}")
                return
        sys.exit(f"{e['name']} has no documented member {member!r}: " + ", ".join(x["name"] for x in e.get("members", [])))
    print(f"{m['module']}.{e['name']}  ({e['kind']}){e.get('signature', '')}\n")
    if e.get("doc"):
        print(e["doc"])
    if e.get("value") is not None:
        print(f"value: {e['value']}")
    if e.get("members"):
        print("\nmembers: " + ", ".join(x["name"] for x in e["members"]))


def cmd_find(args):
    kind, n, terms = None, 25, []
    i = 0
    while i < len(args):
        if args[i] == "--kind":
            kind, i = args[i + 1], i + 2
        elif args[i] == "-n":
            n, i = int(args[i + 1]), i + 2
        else:
            terms.append(args[i].lower())
            i += 1
    if not terms:
        sys.exit("find what?")
    rows = []

    def words(text):
        text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text or "")
        return [w for w in re.split(r"[^A-Za-z0-9]+", text.lower()) if w]

    def score(ident, name, desc, ui=False):
        iw, nw, dw = words(ident), words(name), set(words((desc or "")[:400]))
        last = ident.rsplit(".", 1)[-1].lower()
        total = 0
        for t in terms:
            if t == last or t == (name or "").lower():
                total += 10
            elif t in iw:
                total += 6
            elif t in nw:
                total += 5
            elif any(w.startswith(t) for w in iw + nw):
                total += 3
            elif t in dw or any(w.startswith(t) for w in dw):
                total += 1
            else:
                return 0
        return total - (4 if ui else 0)

    if kind in (None, "struct", "prop"):
        for s in structs().values():
            if kind in (None, "struct"):
                sc = score(s["id"], s["name"], s.get("desc"), s.get("ui"))
                if sc:
                    rows.append((sc + 1, "type", s["id"], s.get("desc", "")))
            if kind in (None, "prop") and not s.get("ui"):
                for p in s["props"]:
                    sc = score(f"{s['id']}.{p['id']}", p.get("name"), p.get("desc"))
                    if sc:
                        rows.append((sc, "prop", f"{s['id']}.{p['id']} ({p['type'].lower()})", p.get("desc", "")))
                for f in s["funcs"]:
                    sc = score(f"{s['id']}.{f['id']}", f["id"], f.get("desc"))
                    if sc:
                        rows.append((sc, "func", f"{s['id']}.{f['id']}()", f.get("desc", "")))
                for m in s.get("py", []):
                    sc = score(f"{s['id']}.{m['id']}", m["id"], (m.get("desc") or "")[:300])
                    if sc:
                        rows.append((sc, "pydef", f"{s['id']}.{m['id']}" + ("" if m["kind"] == "property" else "()"),
                                     (m.get("desc") or "").split("\n")[0]))
    if kind in (None, "op"):
        for o in load("operators.jsonl.gz"):
            sc = score(o["id"], o.get("name"), o.get("desc"))
            if sc:
                rows.append((sc, "op", "bpy.ops." + o["id"], o.get("desc", "")))
    if kind in (None, "node"):
        for nd in load("nodes.jsonl.gz"):
            if not nd["trees"]:
                continue
            sc = score(nd["id"], nd.get("label") or nd["name"], nd.get("desc"))
            if sc:
                rows.append((sc + 1, "node", f"{nd['id']} \"{nd.get('label') or nd['name']}\"", nd.get("desc", "")))
            for s in nd.get("inputs", []) + nd.get("outputs", []):
                sc = score(f"{nd['id']}.{s['name']}", s["name"], "")
                if sc and len(terms) > 1:
                    rows.append((sc - 1, "socket", f"{nd['id']} socket {s['name']!r}", ""))
    if kind in (None, "py"):
        for m in load("modules.jsonl.gz"):
            for e in m.get("members", []):
                sc = score(f"{m['module']}.{e['name']}", e["name"], (e.get("doc") or "")[:300])
                if sc:
                    rows.append((sc, "py", f"{m['module']}.{e['name']}", (e.get("doc") or "").split("\n")[0]))
    rows.sort(key=lambda r: (-r[0], len(r[2])))
    for sc, k, ident, desc in rows[:n]:
        print(f"  {k:6s} {ident}" + (f"\n         {desc[:150]}" if desc else ""))
    if len(rows) > n:
        print(f"  ... {len(rows) - n} more (-n {len(rows)})")
    if not rows:
        print("  nothing matches all of: " + " ".join(terms) + "  (try fewer or shorter terms, or docs.py search)")
        if len(terms) > 1:                  # e.g. "overwrite placeholder": two settings, no entry has both words
            for t in terms:
                print(f"\n  {t} alone:")
                cmd_find([t, "-n", "5"] + (["--kind", kind] if kind else []))


def cmd_path(args):
    s = resolve_struct(args[0])
    ps = paths_to(s["id"], 12)
    print("\n".join(ps) if ps else f"no path found to {s['id']} from bpy.context or bpy.data")


def cmd_enums(_):
    for k, v in load("dynamic_enums.json").items():
        print(f"{k}:\n    {v}")


def cmd_factory(args):
    f = load("factory.json")
    if not args:
        print("sections: " + ", ".join(f))
        return
    print(json.dumps(f.get(args[0]), indent=1))


def cmd_meta(_):
    m = load("meta.json")
    print(json.dumps({k: m[k] for k in ("blender", "python", "platform", "libraries", "counts")}, indent=1))
    a = m["addons"]
    print("add-ons on in a fresh Blender:", ", ".join(a["on_by_default"]))
    print("bundled, off by default:", ", ".join(a["enabled_for_this_read"]))


# --- the interface: keys and menus (inventory_ui.py) ----------------------------------------------------------------

KEYNAMES = {
    **{c: c.upper() for c in "abcdefghijklmnopqrstuvwxyz"},
    **{str(i): w for i, w in enumerate("ZERO ONE TWO THREE FOUR FIVE SIX SEVEN EIGHT NINE".split())},
    **{f"f{i}": f"F{i}" for i in range(1, 25)},
    **{f"numpad_{i}": f"NUMPAD_{i}" for i in range(10)},
    "numpad_plus": "NUMPAD_PLUS", "numpad_minus": "NUMPAD_MINUS", "numpad_period": "NUMPAD_PERIOD",
    "numpad_slash": "NUMPAD_SLASH", "numpad_asterisk": "NUMPAD_ASTERIX", "numpad_enter": "NUMPAD_ENTER",
    "tab": "TAB", "space": "SPACE", "spacebar": "SPACE", "esc": "ESC", "escape": "ESC", "enter": "RET",
    "return": "RET", "del": "DEL", "delete": "DEL", "backspace": "BACK_SPACE", "home": "HOME", "end": "END",
    "page_up": "PAGE_UP", "pgup": "PAGE_UP", "page_down": "PAGE_DOWN", "pgdn": "PAGE_DOWN", "insert": "INSERT",
    "up": "UP_ARROW", "down": "DOWN_ARROW", "left": "LEFT_ARROW", "right": "RIGHT_ARROW",
    ".": "PERIOD", "period": "PERIOD", ",": "COMMA", "comma": "COMMA", "/": "SLASH", "slash": "SLASH",
    "\\": "BACK_SLASH", "-": "MINUS", "minus": "MINUS", "=": "EQUAL", "equal": "EQUAL", "plus": "PLUS",
    "`": "ACCENT_GRAVE", "~": "ACCENT_GRAVE", "grave": "ACCENT_GRAVE", "tilde": "ACCENT_GRAVE",
    "[": "LEFT_BRACKET", "]": "RIGHT_BRACKET", ";": "SEMI_COLON", "'": "QUOTE",
    "lmb": "LEFTMOUSE", "click": "LEFTMOUSE", "rmb": "RIGHTMOUSE", "mmb": "MIDDLEMOUSE",
    "wheel_up": "WHEELUPMOUSE", "wheel_down": "WHEELDOWNMOUSE", "wheel_in": "WHEELINMOUSE", "wheel_out": "WHEELOUTMOUSE",
}
PHRASES = [  # longest first: words a tutorial uses, turned into one token
    (r"num(?:ber)?\s*pad\s*\+|numpad\s*plus", "numpad_plus"), (r"num(?:ber)?\s*pad\s*-|numpad\s*minus", "numpad_minus"),
    (r"num(?:ber)?\s*pad\s*(?:\.|period|del(?:ete)?)", "numpad_period"), (r"num(?:ber)?\s*pad\s*/", "numpad_slash"),
    (r"num(?:ber)?\s*pad\s*\*", "numpad_asterisk"), (r"num(?:ber)?\s*pad\s*enter", "numpad_enter"),
    (r"(?:num(?:ber)?\s*pad|numpad|num|np)\s*([0-9])", r"numpad_\1"),
    (r"double[\s-]*click", "click double"), (r"left[\s-]*click|left\s*mouse(?:\s*button)?", "lmb"),
    (r"right[\s-]*click|right\s*mouse(?:\s*button)?", "rmb"), (r"middle[\s-]*(?:click|mouse(?:\s*button)?)", "mmb"),
    (r"(?:scroll|wheel|mouse\s*wheel)\s*up", "wheel_up"), (r"(?:scroll|wheel|mouse\s*wheel)\s*down", "wheel_down"),
    (r"page\s*up", "page_up"), (r"page\s*down", "page_down"), (r"(?:up|down|left|right)\s*arrow", None),
]
MODS = {"shift": "shift", "ctrl": "ctrl", "control": "ctrl", "ctl": "ctrl", "alt": "alt", "option": "alt", "opt": "alt",
        "cmd": "oskey", "command": "oskey", "oskey": "oskey", "super": "oskey", "win": "oskey", "meta": "oskey"}
EDIT_HINT = {"Mesh": "edit mode, mesh", "Curve": "edit mode, curve", "Curves": "edit mode, hair curves",
             "Armature": "edit mode, armature", "Lattice": "edit mode, lattice", "Font": "edit mode, text",
             "Metaball": "edit mode, metaball", "Point Cloud": "edit mode, point cloud", "Object Mode": "object mode",
             "Grease Pencil Edit Mode": "edit mode, grease pencil"}
EDITORS = {"VIEW3D": "3D Viewport", "NODE": "Node Editor", "IMAGE": "Image / UV Editor", "SEQUENCER": "Video Sequencer",
           "GRAPH": "Graph Editor", "DOPESHEET": "Dope Sheet", "NLA": "NLA Editor", "CLIP": "Movie Clip Editor",
           "TEXT": "Text Editor", "OUTLINER": "Outliner", "TOPBAR": "top bar", "PROPERTIES": "Properties",
           "INFO": "Info", "CONSOLE": "Python Console", "FILEBROWSER": "File Browser", "USERPREF": "Preferences",
           "ASSETBROWSER": "Asset Browser", "SPREADSHEET": "Spreadsheet", "TIME": "Timeline", "MASK": "Mask",
           "GREASE_PENCIL": "Grease Pencil", "CURVES": "hair curves", "POINTCLOUD": "point cloud", "WM": "any editor",
           "SCREEN": "any editor", "RENDER": "render settings", "ANIM": "animation editors"}


def parse_keys(text):
    t = " " + text.lower().replace("+", " + ") + " "
    t = re.sub(r"num(?:ber)?\s*pad\s*\+\s*\+?", " numpad_plus ", t)        # "numpad +" before + becomes a separator
    for pat, rep in PHRASES:
        if rep is None:
            t = re.sub(r"\b(up|down|left|right)\s*arrow\b", r"\1", t)
        else:
            t = re.sub(pat, f" {rep} ", t)
    mods, keys, value = set(), [], None
    for tok in t.replace("+", " ").split():
        if tok in MODS:
            mods.add(MODS[tok])
        elif tok == "double":
            value = "DOUBLE_CLICK"
        elif tok in ("drag", "tweak"):
            value = "CLICK_DRAG"
        elif tok in ("hold", "press"):
            continue
        elif tok in KEYNAMES:
            keys.append(KEYNAMES[tok])
        elif tok.upper() in {r["type"] for r in load("keymap.jsonl.gz")}:
            keys.append(tok.upper())
        else:
            sys.exit(f"unknown key {tok!r} in {text!r}: use names like a, 1, f2, tab, numpad 1, click, rmb, wheel up")
    return mods, keys, value


def key_text(r):
    m = [n for n, k in (("Ctrl", "ctrl"), ("Shift", "shift"), ("Alt", "alt"), ("Cmd", "oskey")) if r.get(k) is True]
    if r.get("any"):
        m = ["(any modifiers)"]
    if r.get("key_modifier"):
        m.append(f"{r['key_modifier']} held")
    v = r.get("value")
    tail = "" if v in (None, "PRESS") else f" ({v.lower().replace('_', ' ')})"
    return " ".join(m + [r["type"]]) + tail


def call_text(r):
    props = r.get("props") or {}
    if r.get("modal"):
        return f"modal action {r['op']} (while the operator that owns this map runs)"
    args = ", ".join(f"{k}={v!r}" for k, v in props.items())
    out = f"bpy.ops.{r['op']}({args})"
    if r["op"] in ("wm.call_menu", "wm.call_menu_pie", "wm.call_panel") and props.get("name"):
        m = menus_by_id().get(props["name"])
        if m:
            out += f"   opens \"{m['label']}\" ({props['name']}; kb.py menu {props['name']})"
    return out


def menus_by_id():
    if "M" not in _cache:
        _cache["M"] = {m["id"]: m for m in load("menus.jsonl.gz")}
    return _cache["M"]


def print_key_rows(rows):
    last = None
    for r in sorted(rows, key=lambda r: (r["keymap"], r["type"], key_text(r))):
        if r["keymap"] != last:
            last = r["keymap"]
            where = ", ".join(x for x in (r.get("space") if r.get("space") not in (None, "EMPTY") else "",
                                          EDIT_HINT.get(last, ""), "modal map" if r.get("modal") else "") if x)
            print(f"{last}" + (f"  [{where}]" if where else ""))
        flag = "" if r.get("active", True) else "  (inactive by default)"
        mac = "  (Cmd also, on macOS)" if r.get("mac_cmd") else ""
        print(f"  {key_text(r):<26} {call_text(r)}{mac}{flag}")


def cmd_keys(args):
    km_filter = op_filter = None
    rest = []
    it = iter(args)
    for a in it:
        if a == "--map":
            km_filter = next(it, "").lower()
        elif a == "--op":
            op_filter = next(it, "").removeprefix("bpy.ops.")
        else:
            rest.append(a)
    rows = load("keymap.jsonl.gz")
    if km_filter:
        exact = [r for r in rows if r["keymap"].lower() == km_filter]
        rows = exact or [r for r in rows if km_filter in r["keymap"].lower()]
    if op_filter:
        o = op_filter.lower()
        if "_ot_" in o:
            o = o.replace("_ot_", ".")
        rows = [r for r in rows if r["op"].lower() == o or (r["op"] in ("wm.call_menu", "wm.call_menu_pie", "wm.call_panel")
                                                          and (r.get("props") or {}).get("name", "").lower() == o)]
    if rest:
        mods, keys, value = parse_keys(" ".join(rest))
        if len(keys) != 1:
            sys.exit(f"give one key with its modifiers (got {keys or 'none'}); for a sequence, look each key up in turn")
        k = keys[0]
        want = {m: m in mods for m in ("shift", "ctrl", "alt", "oskey")}

        def match(r, w):
            if r["type"] != k or (value and r.get("value") != value) or r.get("any"):
                return False
            return all(bool(r.get(m) is True) == w[m] for m in w)
        hit = [r for r in rows if match(r, want)]
        if want["oskey"]:                                               # Cmd on a Mac stands for Ctrl in most items
            w2 = dict(want, oskey=False, ctrl=True)
            hit += [r for r in rows if match(r, w2) and r.get("mac_cmd")]
        anyk = [r for r in rows if r.get("any") and r["type"] == k and (not value or r.get("value") == value)]
        if not mods or not hit:                                         # "any modifiers" items, when they can apply
            hit += anyk
        rows = hit
    if not rows:
        sys.exit("nothing in the default keymap matches" + (" (try without --map)" if km_filter else ""))
    plain_rows = [r for r in rows if not r.get("modal")]
    modal_rows = [r for r in rows if r.get("modal")]
    print_key_rows(plain_rows)
    if modal_rows:
        print("\nWhile an operator runs (its modal map; e.g. X after G constrains the move to X):" if plain_rows else
              "Only inside a running operator (modal maps):")
        print_key_rows(modal_rows)
    print("\n(the default keymap, left-click select, as Blender 4.5 builds it; a user's own keymap may differ)")


def norm(label):
    return re.sub(r"[\s.…]+$", "", (label or "")).strip().lower()


def entries_of(mid, depth=0):
    """A menu's entries with inline menus expanded."""
    m = menus_by_id().get(mid)
    if not m or depth > 4:
        return []
    out = []
    for e in m["entries"]:
        out += entries_of(e["menu"], depth + 1) if e["kind"] == "inline" else [e]
    return out


def entry_call(e, item=None):
    if e["kind"] == "op":
        args = ", ".join(f"{k}={v!r}" for k, v in (e.get("props") or {}).items())
        return f"bpy.ops.{e['op']}({args})"
    if e["kind"] == "enum_menu" and item:
        return f"bpy.ops.{e['op']}({e['prop']}={item!r})"
    if e["kind"] in ("prop", "prop_menu", "prop_value"):
        v = f" = {e['value']!r}" if e["kind"] == "prop_value" else ""
        return f"a property: {e['struct']}.{e['prop']}{v}"
    if e["kind"] == "menu":
        return f"opens menu {e['menu']}"
    return e["kind"]


def follow(mid, parts, trail):
    """Every way the labels in parts lead through menu mid. Yields (trail, entry, enum item)."""
    if not parts:
        return
    want, rest = norm(parts[0]), parts[1:]
    for e in entries_of(mid):
        if e["kind"] == "enum_menu" and norm(e.get("label")) == want:
            if not rest:
                yield trail + [e["label"]], e, None
            else:
                for ident, name in e.get("items", []):
                    if norm(name) == norm(rest[0]) and len(rest) == 1:
                        yield trail + [e["label"], name], e, ident
        elif norm(e.get("label")) == want:
            if e["kind"] == "menu" and rest:
                yield from follow(e["menu"], rest, trail + [e["label"]])
            elif not rest:
                yield trail + [e["label"]], e, None


def openers():
    """menu id -> the keys that open it."""
    if "O" not in _cache:
        o = {}
        for r in load("keymap.jsonl.gz"):
            if r["op"] in ("wm.call_menu", "wm.call_menu_pie") and (r.get("props") or {}).get("name"):
                o.setdefault(r["props"]["name"], []).append(f"{key_text(r)} in {r['keymap']}")
        _cache["O"] = o
    return _cache["O"]


def editor_of(mid):
    pre = mid.split("_MT_")[0] if "_MT_" in mid else mid.split("_")[0]
    return EDITORS.get(pre, pre)


def print_menu(m):
    print(f"{m['id']}  \"{m['label']}\"  [{editor_of(m['id'])}]")
    keys = openers().get(m["id"])
    if keys:
        print("  opened by: " + "; ".join(keys[:6]))
    for e in m["entries"]:
        if e["kind"] == "label":
            print(f"  -- {e['label']} --")
        elif e["kind"] == "inline":
            print(f"  (the entries of {e['menu']} appear here)")
        elif e["kind"] == "enum_menu":
            print(f"  {e.get('label') or '?':<28} > a list: " + ", ".join(n for _, n in e.get("items", [])[:12])
                  + f"   -> bpy.ops.{e['op']}({e['prop']}=...)")
        else:
            print(f"  {(e.get('label') or '?') + (' >' if e['kind'] == 'menu' else ''):<28} {entry_call(e)}")
    if m.get("error"):
        print(f"  (read only this far headless: {m['error']})")


def cmd_menu(args):
    where = op = None
    rest = []
    it = iter(args)
    for a in it:
        if a == "--in":
            where = next(it, "").upper()
        elif a == "--op":
            op = next(it, "").removeprefix("bpy.ops.").lower()
        else:
            rest.append(a)
    M = menus_by_id()
    if op:
        parents = {}
        for m in M.values():
            for e in m["entries"]:
                if e["kind"] in ("menu", "inline"):
                    parents.setdefault(e["menu"], []).append((m["id"], e.get("label") if e["kind"] == "menu" else None))
        paths = []

        def up(mid, path, seen):
            ps = parents.get(mid, [])
            if not ps or len(path) > 6:
                top = M[mid]["label"] if M.get(mid) else ""
                paths.append((mid, ([top] if top else ["(header)"] if mid.endswith("_MT_editor_menus") else []) + path))
                return
            for pid, lab in ps:
                if pid in seen:
                    continue
                up(pid, ([lab] if lab else []) + path, seen | {pid})
        for m in M.values():
            for e in m["entries"]:
                if e.get("op", "").lower() == op and e["kind"] in ("op", "enum_menu"):
                    up(m["id"], [e.get("label") or "?"], {m["id"]})
        if where:
            paths = [p for p in paths if p[0].startswith(where)]
        if not paths:
            sys.exit(f"{op} is in no menu" + (f" of {where}" if where else ""))
        for root, path in sorted(set((r, tuple(p)) for r, p in paths)):
            keys = openers().get(root)
            print(f"{' > '.join(path)}   [{editor_of(root)}: {root}]" + (f"  opened by {keys[0]}" if keys else ""))
        return
    text = " ".join(rest)
    if text in M:
        print_menu(M[text])
        return
    parts = [p for p in re.split(r"\s*(?:>|›|→|/)\s*", text) if p]
    if len(parts) == 1:
        hits = [m for m in M.values() if norm(m["label"]) == norm(parts[0]) and (not where or m["id"].startswith(where))]
        if not hits:
            sys.exit(f"no menu called {parts[0]!r}; give a path like \"Add > Mesh > Cylinder\" or a menu id")
        for m in hits:
            print_menu(m)
            print()
        return
    found = 0
    for m in M.values():
        if norm(m["label"]) != norm(parts[0]) or (where and not m["id"].startswith(where)):
            continue
        for trail, e, item in follow(m["id"], parts[1:], [m["label"]]):
            found += 1
            keys = openers().get(m["id"])
            print(f"{' > '.join(trail)}   [{editor_of(m['id'])}: {m['id']}" + (f"; opened by {keys[0]}" if keys else "") + "]")
            print(f"    {entry_call(e, item)}")
            if e["kind"] == "menu":
                print_menu(M[e["menu"]])
    if not found:
        sys.exit(f"no menu path {' > '.join(parts)}" + (f" in {where}" if where else "")
                 + f"; see the top menu's entries with: kb.py menu \"{parts[0]}\"")


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print(__doc__)
        return
    cmd, args = sys.argv[1], sys.argv[2:]
    fn = globals().get(f"cmd_{cmd}")
    if not fn:
        sys.exit(f"unknown command {cmd!r}\n{__doc__}")
    if cmd not in ("enums", "meta", "factory", "nodes") and not args:
        sys.exit(f"{cmd} needs an argument\n{__doc__}")
    fn(args)


if __name__ == "__main__":
    main()
