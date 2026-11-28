"""C-010: do kb.py's key and menu lookups reach the operator Blender's own manual names?

The 4.5 manual opens most tool pages with a Reference box: the mode, a menu path ("Edge ‣ Bevel Edges") and a shortcut
("Ctrl-B"), under a section whose anchor names the operator (id="bpy-ops-mesh-bevel"). People wrote those boxes; the
lookup reads Blender's keymap and menus. For every box whose section names an operator:
  menu      kb.py's menu walk from every menu with the path's first label: does some path end on the named operator?
  shortcut  kb.py's key parser and keymap: does some binding of that key run the named operator, or open a menu (or a
            menu inside it) that has it?
Misses are classed by reading them (results list each one).

Run with the system Python (no Blender; needs the manual, fetched by skills/blender/scripts/docs.py fetch):
    python3 experiments/interface/manual_refbox.py
Writes experiments/interface/results/manual_refbox.json."""
import datetime
import glob
import html
import json
import os
import platform
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "skills", "blender", "scripts"))
import kb  # noqa: E402

MANUAL = os.path.join(os.environ.get("AGENTIC_BLENDER_DOCS") or os.path.expanduser("~/.cache/agentic-blender/docs-4.5"),
                      "manual")
TAG = re.compile(r"<[^>]+>")
TOKEN = re.compile(r'<span id="(bpy-ops-[a-z0-9_-]+)"></span>|<h[1-6][ >]|<div class="refbox admonition"')
FIELD = re.compile(r'<dt class="field-\w+">(\w[\w ]*)<span class="colon">:</span></dt>\s*<dd class="field-\w+">(.*?)</dd>', re.S)
MANUAL_KEYS = {"lmb": "click", "rmb": "rmb", "mmb": "mmb", "return": "enter", "spacebar": "space", "pageup": "page up",
               "pagedown": "page down", "numpadperiod": "numpad period", "numpadplus": "numpad plus",
               "numpadminus": "numpad minus", "numpadslash": "numpad /", "numpadasterisk": "numpad *",
               "numpadenter": "numpad enter", "oskey": "cmd", "cmd": "cmd", "wheelup": "wheel up",
               "wheeldown": "wheel down", "backspace": "backspace", "delete": "delete", "del": "delete"}


def text(fragment):
    return re.sub(r"\s+", " ", html.unescape(TAG.sub(" ", fragment))).strip()


OPS = {o["id"] for o in kb.load("operators.jsonl.gz")}


def op_of(anchor):
    """bpy-ops-mesh-bevel -> mesh.bevel. Underscores became hyphens in both parts (grease_pencil), so the split is the
    one that names a real operator."""
    parts = anchor.removeprefix("bpy-ops-").split("-")
    for i in range(1, len(parts)):
        cand = "_".join(parts[:i]) + "." + "_".join(parts[i:])
        if cand in OPS:
            return cand
    return parts[0] + "." + "_".join(parts[1:])


def boxes():
    for path in sorted(glob.glob(os.path.join(MANUAL, "**", "*.html"), recursive=True)):
        if not os.path.isfile(path):
            continue
        t = open(path, encoding="utf-8", errors="replace").read()
        pending, section = [], []
        for m in TOKEN.finditer(t):
            if m.group(1):
                pending.append(op_of(m.group(1)))
            elif m.group(0).startswith("<h"):
                section, pending = pending, []
            else:
                end = t.find("</div>", m.end())
                body = t[m.end():end]
                fields = [(k.strip(), v) for k, v in FIELD.findall(body)]
                yield os.path.relpath(path, MANUAL), list(section), fields


def keys_from(dd):
    """The shortcuts in one Shortcut field: each <kbd class="... compound"> or lone <kbd>, as text like 'Ctrl-B'."""
    out = []
    for comp in re.findall(r'<kbd class="kbd compound[^"]*">(.*?)</kbd></kbd>', dd, re.S):
        out.append(text(comp + "</kbd>").replace(" ", ""))
    if not out:
        out = [text(k) for k in re.findall(r"<kbd[^>]*>(.*?)</kbd>", dd, re.S)]
    return [k for k in out if k]


def manual_key_to_query(k):
    parts = [p for p in re.split(r"-(?=.)", k) if p]
    q = []
    for p in parts:
        lp = p.lower()
        if lp in MANUAL_KEYS:
            q.append(MANUAL_KEYS[lp])
        elif re.fullmatch(r"numpad\d", lp):
            q.append("numpad " + lp[-1])
        else:
            q.append(lp)
    return " ".join(q)


def ops_in_menu(mid, depth=0):
    if depth > 2:
        return set()
    out = set()
    for e in kb.entries_of(mid):
        if e.get("op"):
            out.add(e["op"])
        if e["kind"] == "menu":
            out |= ops_in_menu(e["menu"], depth + 1)
    return out


def key_ops(query):
    """Operators a key runs anywhere in the default keymap, directly or through the menu it opens."""
    try:
        mods, keys, value = kb.parse_keys(query)
    except SystemExit as e:
        return None, str(e)
    if len(keys) != 1:
        return None, f"{len(keys)} keys"
    k = keys[0]
    want = {m: m in mods for m in ("shift", "ctrl", "alt", "oskey")}
    ops = set()
    for r in kb.load("keymap.jsonl.gz"):
        if r["type"] != k or r.get("modal") or r.get("any"):
            continue
        if not all(bool(r.get(m) is True) == want[m] for m in want):
            continue
        ops.add(r["op"])
        name = (r.get("props") or {}).get("name")
        if r["op"] in ("wm.call_menu", "wm.call_menu_pie") and name:
            ops |= ops_in_menu(name)
    return ops, None


def menu_ops(path):
    parts = [p.strip() for p in path.split("‣") if p.strip()]
    found, ops = False, set()
    for m in kb.menus_by_id().values():
        if kb.norm(m["label"]) != kb.norm(parts[0]):
            continue
        if len(parts) == 1:
            found = True
            ops |= ops_in_menu(m["id"])
            continue
        for trail, e, item in kb.follow(m["id"], parts[1:], [m["label"]]):
            found = True
            if e.get("op"):
                ops.add(e["op"])
            if e["kind"] == "menu":
                ops |= ops_in_menu(e["menu"])
    return found, ops


rows = dict(menu=[], shortcut=[])
counts = dict(pages=0, boxes=0, boxes_with_operator=0, boxes_without_operator=0)
pages = set()
for page, ops, fields in boxes():
    counts["boxes"] += 1
    pages.add(page)
    if not ops:
        counts["boxes_without_operator"] += 1
        continue
    counts["boxes_with_operator"] += 1
    mode = "; ".join(text(v) for k, v in fields if k == "Mode")
    for k, v in fields:
        if k == "Menu":
            for path in re.findall(r'<span class="menuselection">(.*?)</span>', v, re.S) or [v]:
                path = text(path)
                found, got = menu_ops(path)
                rows["menu"].append(dict(page=page, operators=ops, mode=mode, path=path, found=found,
                                         hit=bool(set(ops) & got), reached=sorted(got)[:8]))
        elif k == "Shortcut":
            for key in keys_from(v):
                q = manual_key_to_query(key)
                got, err = key_ops(q)
                rows["shortcut"].append(dict(page=page, operators=ops, mode=mode, key=key, query=q, error=err,
                                             hit=bool(got and set(ops) & got), reached=sorted(got or [])[:8]))
counts["pages"] = len(pages)


def share(rs):
    n = len(rs)
    h = sum(r["hit"] for r in rs)
    return dict(n=n, hits=h, share=round(h / n, 4) if n else None)


summary = dict(counts=counts, menu=share(rows["menu"]), shortcut=share(rows["shortcut"]),
               menu_path_not_found=sum(not r["found"] for r in rows["menu"]),
               shortcut_unparsed=sum(bool(r["error"]) for r in rows["shortcut"]))
rec = dict(experiment=os.path.relpath(os.path.abspath(__file__), ROOT), blender=kb.load("ui_meta.json")["blender"],
           machine=f"{platform.system()} {platform.machine()}", date=datetime.date.today().isoformat(),
           facts=[dict(fact="of the 4.5 manual's Reference boxes whose section names an operator, the share of menu paths "
                            "and of shortcuts that kb.py's lookup takes to that operator", **summary)],
           data=dict(misses=dict(menu=[r for r in rows["menu"] if not r["hit"]],
                                 shortcut=[r for r in rows["shortcut"] if not r["hit"]])))
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results"), exist_ok=True)
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "manual_refbox.json"), "w") as f:
    json.dump(rec, f, indent=1, ensure_ascii=False)
print(json.dumps(summary, indent=1))
