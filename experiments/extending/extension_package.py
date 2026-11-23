"""Packaging Python code as a Blender 4.5 extension (the 4.2+ replacement for zipped add-ons with bl_info): the
smallest blender_manifest.toml that validates, what validate and build say about common mistakes, and what the built
zip holds. Nothing is installed (installing would change the user's Blender).

Run with the system Python:  python3 experiments/extending/extension_package.py
"""
import datetime
import json
import os
import platform
import subprocess
import sys
import tempfile
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from run import blender  # noqa: E402

B = blender()
facts = []


def fact(sentence, **numbers):
    facts.append(dict(fact=sentence, **numbers))
    print("FACT", sentence, numbers, flush=True)


MANIFEST = '''schema_version = "1.0.0"
id = "bfg_probe"
version = "0.1.0"
name = "Field Guide Probe"
tagline = "A probe extension for the field guide"
maintainer = "Field Guide"
type = "add-on"
blender_version_min = "4.2.0"
license = ["SPDX:GPL-3.0-or-later"]
'''
INIT = '''import bpy


class BFG_OT_probe(bpy.types.Operator):
    bl_idname = "object.bfg_probe"
    bl_label = "Probe"

    def execute(self, context):
        return {"FINISHED"}


def register():
    bpy.utils.register_class(BFG_OT_probe)


def unregister():
    bpy.utils.unregister_class(BFG_OT_probe)
'''


def make(files):
    d = tempfile.mkdtemp(prefix="bfg-ext-")
    for name, text in files.items():
        open(os.path.join(d, name), "w").write(text)
    return d


def cmd(*args, cwd=None):
    r = subprocess.run([B, "--factory-startup", "--command", "extension", *args], capture_output=True, text=True, cwd=cwd)
    out = [l for l in (r.stdout + r.stderr).splitlines() if l.strip() and not l.startswith("[")]
    return r.returncode, out[-6:]


good = make({"blender_manifest.toml": MANIFEST, "__init__.py": INIT})
code, out = cmd("validate", good)
fact("A manifest with schema_version, id, version, name, tagline, maintainer, type, blender_version_min and license "
     "(an SPDX list) validates in 4.5 with `blender --command extension validate DIR` (fields were not removed one by "
     "one, except the tagline below)", exit=code, output=out)

outdir = tempfile.mkdtemp(prefix="bfg-ext-out-")
code, out = cmd("build", "--source-dir", good, "--output-dir", outdir)
zips = [f for f in os.listdir(outdir) if f.endswith(".zip")]
members = zipfile.ZipFile(os.path.join(outdir, zips[0])).namelist() if zips else []
fact("`extension build` writes <id>-<version>.zip holding the source files at the zip's top level", exit=code,
     zips=zips, members=sorted(members))

cases = {
    "bl_info left in __init__.py": {"blender_manifest.toml": MANIFEST, "__init__.py": "bl_info = {'name': 'x'}\n" + INIT},
    "no tagline": {"blender_manifest.toml": MANIFEST.replace('tagline = "A probe extension for the field guide"\n', ""), "__init__.py": INIT},
    "tagline ending with a full stop": {"blender_manifest.toml": MANIFEST.replace('the field guide"', 'the field guide."'), "__init__.py": INIT},
    "id with a hyphen": {"blender_manifest.toml": MANIFEST.replace('id = "bfg_probe"', 'id = "bfg-probe"'), "__init__.py": INIT},
    "licence not SPDX-prefixed": {"blender_manifest.toml": MANIFEST.replace('["SPDX:GPL-3.0-or-later"]', '["GPL-3.0-or-later"]'), "__init__.py": INIT},
    "no __init__.py": {"blender_manifest.toml": MANIFEST},
}
res = {}
for label, files in cases.items():
    code, out = cmd("validate", make(files))
    res[label] = dict(exit=code, message=out[-2:])
fact("What `extension validate` says about common mistakes (exit 0 = accepted): it refuses a missing tagline, a "
     "tagline ending in punctuation, an id with a hyphen and a missing __init__.py, but accepts a leftover bl_info and a "
     "licence without the 'SPDX:' prefix", **res)

rec = dict(experiment=os.path.relpath(os.path.abspath(__file__), ROOT),
           blender=subprocess.run([B, "--version"], capture_output=True, text=True).stdout.splitlines()[0],
           machine=f"{platform.system()} {platform.machine()}", date=datetime.date.today().isoformat(), facts=facts)
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results"), exist_ok=True)
json.dump(rec, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "extension_package.json"), "w"), indent=1)
