#!/usr/bin/env python3
"""Find and fetch free (CC0) assets from Poly Haven and ambientCG for headless Blender scripts.

  assets.py search KIND TERM... [--source polyhaven|ambientcg|all] [-n 10]
  assets.py get SOURCE ID [--res 1k|2k|4k|8k] [--format jpg|png|exr|hdr] [--quality LQ|SQ|HQ]
  assets.py cache                     where downloads are kept, and what is there

KIND is hdri, texture or model. `get` downloads once into ~/.cache/agentic-blender/assets/<source>/<id>/<res>/
(later calls reuse it; $AGENTIC_BLENDER_ASSET_CACHE moves it), checks each file against the size (and md5, for Poly Haven) the
source lists, and prints a manifest, also saved there as manifest.json. Inside Blender, asset_import.py turns a manifest
into a world, a material or imported objects.

Licence: everything on both sites is CC0 1.0, free for any use, no account; the assets need no credit. Poly Haven's API
terms (github.com/Poly-Haven/Public-API/blob/master/ToS.md) ask software using the live API to send its own
User-Agent and to say where the content comes from: this script sends "agentic-blender/<version>" and names the
source in every line and manifest ("Powered by Poly Haven"). ambientCG (its v3 API) is run by one person: the
script caches search results for a day and never downloads the same file twice. --quality picks an ambientCG model's
mesh (LQ, SQ or HQ: 7, 20 and 133 MB for one tree stump at 1K).

Sizes: Poly Haven gives real-world dimensions in millimetres; ambientCG gives numbers without a unit, which fit
centimetres (floors and ground 120 to 280), and 0 when unknown. The manifest's size_m is in metres either way, with
size_note saying which.
Runs on Python 3.9+ with the standard library only (system Python or Blender's).
"""
import hashlib
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import zipfile

VERSION = "0.4"
UA = f"agentic-blender/{VERSION}"
CACHE = os.path.expanduser(os.environ.get("AGENTIC_BLENDER_ASSET_CACHE", "~/.cache/agentic-blender/assets"))
CREDIT = {"polyhaven": "Powered by Poly Haven (polyhaven.com), CC0", "ambientcg": "ambientCG (ambientcg.com), CC0"}
PH_TYPES = {"hdri": "hdris", "texture": "textures", "model": "models"}
ACG_TYPES = {"hdri": "hdri", "texture": "material", "model": "3d-model"}
# Poly Haven map keys -> roles (nor_gl: OpenGL normals, what Blender's Normal Map node expects)
PH_MAPS = {"Diffuse": "color", "nor_gl": "normal", "Rough": "roughness", "AO": "ao", "Displacement": "displacement",
           "Metal": "metallic", "arm": "arm", "Opacity": "opacity", "Alpha": "opacity", "Translucent": "translucency",
           "Emission": "emission"}
# ambientCG file-name suffixes -> roles
ACG_MAPS = {"Color": "color", "NormalGL": "normal", "Roughness": "roughness", "AmbientOcclusion": "ao",
            "Displacement": "displacement", "Metalness": "metallic", "Opacity": "opacity", "Emission": "emission"}


def fetch(url, dest=None, expect_size=None, expect_md5=None):
    """GET url; return the bytes, or write them to dest (atomically) and return dest."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
            break
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))
    if expect_size is not None and len(data) != expect_size:
        raise RuntimeError(f"{url}: got {len(data)} bytes, the source lists {expect_size}")
    if expect_md5 and hashlib.md5(data).hexdigest() != expect_md5:
        raise RuntimeError(f"{url}: md5 does not match the source's")
    if dest is None:
        return data
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest + ".part", "wb") as f:
        f.write(data)
    os.replace(dest + ".part", dest)
    return dest


def cached_json(url, max_age_s=86400):
    path = os.path.join(CACHE, "_api", hashlib.sha1(url.encode()).hexdigest() + ".json")
    if os.path.exists(path) and time.time() - os.path.getmtime(path) < max_age_s:
        return json.load(open(path))
    data = json.loads(fetch(url))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(data, open(path, "w"))
    return data


def words(text):
    return set(re.findall(r"[a-z0-9]+", str(text).lower().replace("_", " ")))


def safe_rel(path):
    """A relative path from a download list, refused if it could escape the asset folder."""
    p = os.path.normpath(path)
    if os.path.isabs(p) or p.startswith("..") or ":" in p:
        raise RuntimeError(f"refusing unsafe path in a download list: {path!r}")
    return p


# ---------------------------------------------------------------- search

def search_polyhaven(kind, terms, n):
    assets = cached_json(f"https://api.polyhaven.com/assets?type={PH_TYPES[kind]}")
    want = set(t.lower() for t in terms)
    rows = []
    for aid, a in assets.items():
        have = words(aid) | words(a.get("name", "")) | set(x.lower() for x in a.get("tags", [])) | \
            set(w for c in a.get("categories", []) for w in words(c))
        score = len(want & have)
        if score:
            dims = a.get("dimensions")
            rows.append(dict(source="polyhaven", id=aid, name=a.get("name"), score=score,
                             downloads=a.get("download_count", 0), categories=a.get("categories", [])[:5],
                             size_m=[round(d / 1000, 3) for d in dims] if dims else None,
                             polycount=a.get("polycount"), page=f"https://polyhaven.com/a/{aid}"))
    rows.sort(key=lambda r: (-r["score"], -r["downloads"]))
    return rows[:n]


def search_ambientcg(kind, terms, n):
    q = urllib.parse.urlencode(dict(type=ACG_TYPES[kind], q=" ".join(terms), sort="popular", limit=n,
                                    include="title,tags,dimensions,url,downloadStatistics"))
    d = cached_json(f"https://ambientcg.com/api/v3/assets?{q}")
    rows = []
    for a in d.get("assets", []):
        dm = a.get("dimensions") or {}
        dims = [dm.get("width", 0), dm.get("height", 0)]
        rows.append(dict(source="ambientcg", id=a["id"], name=a.get("title"), score=None, downloads=None,
                         categories=a.get("tags", [])[:5], size_m=[x / 100 for x in dims] if all(dims) else None,
                         polycount=None, page=a.get("url") or f"https://ambientcg.com/a/{a['id']}"))
    return rows


# ---------------------------------------------------------------- get

def get_polyhaven(aid, res, fmt):
    info = cached_json(f"https://api.polyhaven.com/info/{aid}")
    files = cached_json(f"https://api.polyhaven.com/files/{aid}")
    kind = {0: "hdri", 1: "texture", 2: "model"}[info["type"]]
    folder = os.path.join(CACHE, "polyhaven", aid, res)
    dims = info.get("dimensions")
    m = dict(source="polyhaven", id=aid, name=info.get("name"), kind=kind, res=res, licence="CC0 1.0",
             credit=CREDIT["polyhaven"], page=f"https://polyhaven.com/a/{aid}", folder=folder,
             size_m=[round(d / 1000, 4) for d in dims] if dims else None,
             size_note="Poly Haven dimensions, millimetres in the source" if dims else "no size given",
             polycount=info.get("polycount"), maps={}, hdri=None, model=None)

    def pick(tree, prefer):
        for f in prefer:
            if f in tree:
                return f, tree[f]
        f = next(iter(tree))
        return f, tree[f]

    if kind == "hdri":
        if res not in files["hdri"]:
            raise SystemExit(f"{aid}: no {res}; has {sorted(files['hdri'])}")
        f, entry = pick(files["hdri"][res], [fmt or "hdr", "hdr", "exr"])
        m["hdri"] = fetch_once(entry, os.path.join(folder, os.path.basename(entry["url"])))
    elif kind == "texture":
        for key, role in PH_MAPS.items():
            if key in files and res in files[key]:
                f, entry = pick(files[key][res], [fmt or "jpg", "jpg", "png", "exr"])
                m["maps"][role] = fetch_once(entry, os.path.join(folder, os.path.basename(entry["url"])))
    else:
        if res not in files["gltf"]:
            raise SystemExit(f"{aid}: no {res} glTF; has {sorted(files['gltf'])}")
        main = files["gltf"][res]["gltf"]
        m["model"] = fetch_once(main, os.path.join(folder, os.path.basename(main["url"])))
        for rel, entry in main.get("include", {}).items():
            fetch_once(entry, os.path.join(folder, safe_rel(rel)))
    return m


def fetch_once(entry, dest):
    if os.path.exists(dest) and os.path.getsize(dest) == entry.get("size", os.path.getsize(dest)):
        return dest
    return fetch(entry["url"], dest, expect_size=entry.get("size"), expect_md5=entry.get("md5"))


def get_ambientcg(aid, res, fmt, quality="LQ"):
    q = urllib.parse.urlencode(dict(id=aid, include="downloads,dimensions,title,type,url,tags"))
    d = cached_json(f"https://ambientcg.com/api/v3/assets?{q}")
    if not d.get("assets"):
        raise SystemExit(f"ambientCG has no asset {aid}")
    a = d["assets"][0]
    kind = {v: k for k, v in ACG_TYPES.items()}.get(a.get("type"), a.get("type"))
    downloads = a.get("downloads", [])
    attrs = [x["attributes"] for x in downloads]
    fmt = (fmt or "jpg").upper()
    want = {"hdri": [res.upper()], "texture": [f"{res.upper()}-{fmt}"],
            "model": [f"{quality.upper()}-{res.upper()}-{fmt}"]}.get(kind, [])
    entry = next((x for w in want for x in downloads if x["attributes"] == w), None)
    if entry is None:
        raise SystemExit(f"{aid}: no {want}; has {attrs}")
    folder = os.path.join(CACHE, "ambientcg", aid, entry["attributes"])
    dm = a.get("dimensions") or {}
    dims = [dm.get("width", 0), dm.get("height", 0)]
    m = dict(source="ambientcg", id=aid, name=a.get("title"), kind=kind, res=entry["attributes"],
             licence="CC0 1.0", credit=CREDIT["ambientcg"], page=a.get("url"), folder=folder,
             size_m=[x / 100 for x in dims] if all(dims) else None,
             size_note="ambientCG dimensions, unit not stated, read as centimetres" if all(dims) else "no size given",
             polycount=None, maps={}, hdri=None, model=None)
    if not os.path.isdir(folder) or not [f for f in os.listdir(folder) if f != "manifest.json"]:
        blob = fetch(entry["url"], expect_size=entry.get("size"))
        os.makedirs(folder, exist_ok=True)
        if entry.get("extension") == "zip":
            tmp = os.path.join(folder, "_download.zip")
            open(tmp, "wb").write(blob)
            with zipfile.ZipFile(tmp) as z:
                for member in z.infolist():
                    if member.is_dir():
                        continue
                    out = os.path.join(folder, safe_rel(member.filename))
                    os.makedirs(os.path.dirname(out), exist_ok=True)
                    with z.open(member) as src, open(out, "wb") as dst:
                        dst.write(src.read())
            os.remove(tmp)
        else:
            open(os.path.join(folder, f"{aid}.{entry.get('extension', 'bin')}"), "wb").write(blob)
    for root, _, fs in os.walk(folder):
        for f in sorted(fs):
            p = os.path.join(root, f)
            stem, ext = os.path.splitext(f)
            ext = ext.lower()
            if kind == "hdri" and ext in (".hdr", ".exr"):
                m["hdri"] = p
            elif kind == "model" and ext in (".gltf", ".glb", ".obj", ".fbx", ".usdc", ".usda", ".usdz", ".blend"):
                rank = [".gltf", ".glb", ".obj", ".fbx", ".usdc", ".usda", ".usdz", ".blend"]
                if m["model"] is None or rank.index(ext) < rank.index(os.path.splitext(m["model"])[1].lower()):
                    m["model"] = p
            elif ext in (".jpg", ".jpeg", ".png", ".exr", ".tif", ".tiff"):
                for suffix, role in ACG_MAPS.items():
                    if stem.endswith("_" + suffix):
                        m["maps"][role] = p
    return m


def get(source, aid, res="1k", fmt=None, quality="LQ"):
    m = get_polyhaven(aid, res, fmt) if source == "polyhaven" else get_ambientcg(aid, res, fmt, quality)
    os.makedirs(m["folder"], exist_ok=True)
    json.dump(m, open(os.path.join(m["folder"], "manifest.json"), "w"), indent=1)
    return m


# ---------------------------------------------------------------- cli

def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd, rest = argv[0], argv[1:]
    opt = lambda k, d=None: rest[rest.index(k) + 1] if k in rest else d
    flags = {"--source", "-n", "--res", "--format", "--quality"}
    plain = [x for i, x in enumerate(rest) if x not in flags and (i == 0 or rest[i - 1] not in flags)]
    if cmd == "search":
        kind, terms = plain[0], plain[1:]
        if kind not in PH_TYPES:
            raise SystemExit("KIND is hdri, texture or model")
        n = int(opt("-n", 10))
        src = opt("--source", "all")
        rows = []
        if src in ("all", "polyhaven"):
            rows += search_polyhaven(kind, terms, n)
        if src in ("all", "ambientcg"):
            rows += search_ambientcg(kind, terms, n)
        if not rows:
            print("nothing matches")
        for r in rows:
            size = "x".join(f"{s:g}" for s in r["size_m"]) + " m" if r["size_m"] else "size ?"
            poly = f", {r['polycount']:,} polys" if r.get("polycount") else ""
            print(f"{r['source']:9}  {r['id']:32}  {r['name']}  ({size}{poly})  {r['page']}")
        print(f"-- {CREDIT['polyhaven']}; {CREDIT['ambientcg']}")
    elif cmd == "get":
        source, aid = plain[0], plain[1]
        if source not in CREDIT:
            raise SystemExit("SOURCE is polyhaven or ambientcg")
        print(json.dumps(get(source, aid, opt("--res", "1k"), opt("--format"), opt("--quality", "LQ")), indent=1))
    elif cmd == "cache":
        print(CACHE)
        for source in ("polyhaven", "ambientcg"):
            d = os.path.join(CACHE, source)
            for aid in sorted(os.listdir(d)) if os.path.isdir(d) else []:
                print(f"  {source}/{aid}: {', '.join(sorted(os.listdir(os.path.join(d, aid))))}")
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
