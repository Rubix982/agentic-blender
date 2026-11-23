"""What the two free asset APIs return, as scripts/assets.py relies on it: Poly Haven's types, sizes and file tree,
ambientCG's v2 and v3 type filters, the map files each source ships, and download sizes at 1k.

Run with the system Python (network):  python3 experiments/assets/api_probe.py
Writes experiments/assets/results/api_probe.json. Requests carry the User-Agent assets.py uses.
"""
import datetime
import json
import os
import platform
import sys
import urllib.parse

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "skills", "blender", "scripts"))
import assets  # noqa: E402

facts = []


def fact(sentence, **numbers):
    facts.append(dict(fact=sentence, **numbers))
    print("FACT", sentence, numbers, flush=True)


def j(url):
    return json.loads(assets.fetch(url))


fact("Poly Haven's API lists three asset types", types=j("https://api.polyhaven.com/types"))
tex = j("https://api.polyhaven.com/assets?type=textures")
mod = j("https://api.polyhaven.com/assets?type=models")
hdr = j("https://api.polyhaven.com/assets?type=hdris")
fact("Poly Haven asset counts, and how many state real-world dimensions (millimetres)",
     hdris=len(hdr), textures=len(tex), models=len(mod),
     textures_with_dimensions=sum(1 for a in tex.values() if a.get("dimensions")),
     models_with_dimensions=sum(1 for a in mod.values() if a.get("dimensions")),
     red_brick_dimensions=tex["red_brick"]["dimensions"], armchair_dimensions=mod["ArmChair_01"]["dimensions"])
f = j("https://api.polyhaven.com/files/red_brick")
fact("a Poly Haven texture's file tree: one key per map, then resolution, then format, each file with size and md5",
     keys=sorted(f), resolutions=sorted(f["Diffuse"]), formats_1k=sorted(f["Diffuse"]["1k"]),
     entry_fields=sorted(f["Diffuse"]["1k"]["jpg"]), normal_keys=[k for k in f if k.startswith("nor")])
h = j("https://api.polyhaven.com/files/kloofendal_48d_partly_cloudy_puresky")
fact("a Poly Haven HDRI's sizes (MB) by resolution and format",
     sizes={r: {k: round(v["size"] / 1e6, 2) for k, v in h["hdri"][r].items()} for r in ("1k", "2k", "4k", "8k")})

q = lambda v, **kw: j(f"https://ambientcg.com/api/{v}/" + ("full_json?" if v == "v2" else "assets?") + urllib.parse.urlencode(kw))
v2 = q("v2", type="3DModel", q="rock", limit=4, sort="Popular")
v3 = q("v3", type="3d-model", q="rock", limit=4)
v3all = q("v3", type="3d-model", limit=1)
fact("ambientCG's v2 API ignores its type filter (type=3DModel returns materials); v3 applies it (no rock models)",
     v2_results=v2.get("numberOfResults"), v2_types=sorted({a["dataType"] for a in v2["foundAssets"]}),
     v3_results=v3.get("totalResults"), v3_models_in_total=v3all.get("totalResults"))
a = q("v3", id="Bricks060,DaySkyHDRI072B,3DTreeStump001", include="downloads,dimensions,type")
fact("ambientCG v3 downloads are zips named by attributes: resolution and format for materials, resolution for HDRIs, "
     "mesh quality (LQ, SQ, HQ), resolution and format for models",
     **{x["id"]: dict(type=x["type"], dimensions=x["dimensions"],
                      downloads_mb={d["attributes"]: round(d["size"] / 1e6, 1) for d in x["downloads"]
                                    if "1K" in d["attributes"]}) for x in a["assets"]})

cache = assets.CACHE
listing = {}
for src in ("polyhaven", "ambientcg"):
    for aid in sorted(os.listdir(os.path.join(cache, src))) if os.path.isdir(os.path.join(cache, src)) else []:
        for res in os.listdir(os.path.join(cache, src, aid)):
            d = os.path.join(cache, src, aid, res)
            listing[f"{src}/{aid}"] = sorted(os.listdir(d))
fact("files in the cache after `assets.py get` on the C-002 assets: both sources ship an OpenGL and a DirectX normal "
     "map (assets.py takes the GL one), and ambientCG's zips also hold .blend files",
     normal_files=sorted(f for v in listing.values() for f in v if "nor" in f.lower()),
     blend_files=sorted(f for v in listing.values() for f in v if f.endswith(".blend")),
     cache_mb=round(sum(os.path.getsize(os.path.join(r, x)) for r, _, fs in os.walk(cache) for x in fs) / 1e6, 1))

rec = dict(experiment=os.path.relpath(os.path.abspath(__file__), ROOT), blender=None, user_agent=assets.UA,
           machine=f"{platform.system()} {platform.machine()}", date=datetime.date.today().isoformat(), facts=facts,
           data={})
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results"), exist_ok=True)
text = json.dumps(rec, indent=1).replace(os.path.expanduser("~"), "~")
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "api_probe.json"), "w").write(text)
