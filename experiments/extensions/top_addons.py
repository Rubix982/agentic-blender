"""T-002, card C-003: the 20 most-downloaded add-ons on extensions.blender.org, for this Blender on this platform.
What each declares and contains, what it registers, and which of its operators run headless with default settings and
change the scene.

Run with the system Python (network, for the listing and the packages):  python3 experiments/extensions/top_addons.py
Writes experiments/extensions/results/top_addons.json; packages are cached in ~/.cache/agentic-blender/extensions/.

Containment. Each package is checked against the listing's sha256 and scanned before anything runs: declared
permissions, and every network, subprocess, exec/eval and native-library call. It is installed into a throwaway
profile (BLENDER_USER_RESOURCES = a new folder under /private/tmp), never the user's Blender. Every Blender run here is
wrapped in macOS sandbox-exec: no network, no writes under the home folder, no launching other programs (except
Blender's own), no opening URLs or apps, no Apple Events. Each add-on gets its own Blender process; if one crashes or
hangs on an operator, that operator is skipped and the rest are tried again.
"""
import datetime
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from run import blender  # noqa: E402

UA = "agentic-blender/0.4"
TOP = 20
CACHE = os.path.expanduser("~/.cache/agentic-blender/extensions")
PROBE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "probe", "addon_probe.py")
B = os.path.realpath(blender())
APP = B.split("/Contents/MacOS/")[0]
facts = []


def fact(sentence, **numbers):
    facts.append(dict(fact=sentence, **numbers))
    print("FACT", sentence, json.dumps(numbers, default=str)[:300], flush=True)


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=120).read()


version = subprocess.run([B, "-b", "--factory-startup", "--version"], capture_output=True, text=True).stdout.split()[1]
plat = {"Darwin": "macos", "Linux": "linux", "Windows": "windows"}[platform.system()] + \
    ("-arm64" if platform.machine() in ("arm64", "aarch64") else "-x64")
listing = json.loads(get(f"https://extensions.blender.org/api/v1/extensions/?blender_version={version}&platform={plat}"))
addons = {x["website"].rstrip("/").split("/")[-1]: x for x in listing["data"] if x["type"] == "add-on"}

# the website's order by downloads (the API gives no counts)
rank = []
for page in (1, 2):
    html = get(f"https://extensions.blender.org/add-ons/?sort_by=-download_count&page={page}").decode("utf8", "replace")
    for card in html.split('<div class="cards-item">')[1:]:
        m = re.search(r'href="/add-ons/([a-z0-9][a-z0-9_-]*)/"', card)
        n = re.search(r'title="(\d+) downloads"', card)       # each card: <li title="2358438 downloads">
        if m and m.group(1) not in [r[0] for r in rank]:
            rank.append((m.group(1), int(n.group(1)) if n else None))
top = [(s, d) for s, d in rank if s in addons][:TOP]
fact(f"extensions.blender.org lists this many add-ons for Blender {version} on {plat}; the top {TOP} by downloads",
     addons=len(addons), themes=sum(1 for x in listing["data"] if x["type"] == "theme"),
     top=[dict(slug=s, downloads=d) for s, d in top])

# fetch, verify, scan
RISK = {"network": r"^\s*(import (socket|requests|http\.client|urllib\.request)|from (socket|requests|urllib\.request|http) import)|urlopen\(|requests\.(get|post)\(",
        "subprocess": r"\b(subprocess\.|os\.system\(|os\.popen\(|os\.exec\w*\(|os\.spawn\w*\()",
        "exec_eval": r"(?<![\w.])(exec|eval)\s*\(",
        "native": None}
os.makedirs(CACHE, exist_ok=True)
rows = []
for slug, downloads in top:
    x = addons[slug]
    dest = os.path.join(CACHE, os.path.basename(x["archive_url"]))
    if not os.path.exists(dest):
        data = get(x["archive_url"])
        assert len(data) == x["archive_size"] and "sha256:" + hashlib.sha256(data).hexdigest() == x["archive_hash"], slug
        open(dest, "wb").write(data)
    z = zipfile.ZipFile(dest)
    names = z.namelist()
    man = next((n for n in names if n.endswith("blender_manifest.toml")), None)
    mtext = z.read(man).decode("utf8", "replace") if man else ""
    sect = re.search(r"(?ms)^\[permissions\](.*?)(^\[|\Z)", mtext)
    perms = dict(re.findall(r'(?m)^\s*(\w+)\s*=\s*"([^"]*)"', sect.group(1))) if sect else {}
    lines, hits = 0, {k: 0 for k in RISK}
    for n in names:
        if n.endswith(".py"):
            src = z.read(n).decode("utf8", "replace")
            lines += src.count("\n")
            for line in src.splitlines():
                code = line.split("#")[0]
                for k, pat in RISK.items():
                    if pat and re.search(pat, code):
                        hits[k] += 1
    hits["native"] = sum(1 for n in names if re.search(r"\.(so|dylib|dll|pyd)$", n))
    rows.append(dict(slug=slug, id=x["id"], name=x["name"], version=x["version"], downloads=downloads,
                     license=x.get("license"), tags=x.get("tags"), tagline=x.get("tagline"), archive_mb=round(x["archive_size"] / 1e6, 2),
                     permissions=perms, py_lines=lines, wheels=sum(1 for n in names if n.endswith(".whl")), scan=hits,
                     zip=dest))

# a throwaway profile and the sandbox
prof = tempfile.mkdtemp(prefix="bfg-ext-", dir="/private/tmp")
sb = os.path.join(prof, "sandbox.sb")
open(sb, "w").write(f"""(version 1)
(allow default)
(deny network*)
(deny file-write* (subpath "{os.path.expanduser('~')}"))
(allow file-write* (subpath "{prof}"))
(deny lsopen)
(deny appleevent-send)
(deny process-exec)
(allow process-exec (subpath "{APP}"))
""")
env = dict(os.environ, BLENDER_USER_RESOURCES=prof)


def boxed(args, timeout):
    return subprocess.run(["sandbox-exec", "-f", sb, B] + args, env=env, cwd=prof, capture_output=True, text=True,
                          timeout=timeout)


probe_t = time.time()
for r in rows:
    p = boxed(["--factory-startup", "-c", "extension", "install-file", "-r", "user_default", r["zip"]], 300)
    r["installed"] = p.returncode == 0
    r["install_message"] = (p.stdout + p.stderr).strip().splitlines()[-1:] if p.returncode else []
    out, progress = os.path.join(prof, f"{r['id']}.json"), os.path.join(prof, f"{r['id']}.progress")
    skipped, runs = [], 0
    while r["installed"] and runs < 8:
        runs += 1
        for f in (out, progress):
            if os.path.exists(f):
                os.remove(f)
        try:
            p = boxed(["-b", "--factory-startup", "--python-exit-code", "1", "--python", PROBE, "--",
                       f"bl_ext.user_default.{r['id']}", out, progress, ",".join(skipped)], 900)
            status = "ok" if os.path.exists(out) else f"exit {p.returncode}"
        except subprocess.TimeoutExpired:
            status = "timeout"
        if os.path.exists(out):
            r["probe"] = json.load(open(out))
            break
        last = [l[4:].strip() for l in open(progress).read().splitlines() if l.startswith("TRY ")] if os.path.exists(progress) else []
        if not last:
            r["probe"] = dict(error=f"probe failed before any operator ({status})")
            break
        skipped.append(last[-1])
        r.setdefault("crashed_or_hung", []).append(dict(operator=last[-1], how=status))
    r.pop("zip")
fact("probe time for all add-ons, seconds", seconds=round(time.time() - probe_t, 1))

usable = []
for r in rows:
    pr = r.get("probe", {})
    tried = pr.get("operators", [])
    good = [o["id"] for o in tried if o.get("result") == ["FINISHED"] and o.get("changed")]
    r["headless_changed"] = good
    if good:
        usable.append(r["slug"])
    fact(f"{r['name']} ({r['slug']} {r['version']})",
         downloads=r["downloads"], license=r["license"], permissions=r["permissions"], py_lines=r["py_lines"],
         scan=r["scan"], installed=r["installed"], enabled=pr.get("enabled"), enable_error=pr.get("enable_error"),
         registers=pr.get("registers"), new_properties=pr.get("new_properties"),
         operators=len(tried), finished_and_changed=len(good), finished_no_change=sum(1 for o in tried if o.get("result") == ["FINISHED"] and not o.get("changed")),
         poll_failed=sum(1 for o in tried if o.get("result") == "poll failed"),
         errors=sum(1 for o in tried if isinstance(o.get("result"), str) and o["result"] not in ("poll failed", "not run")),
         not_run=sum(1 for o in tried if o.get("result") == "not run"),
         crashed_or_hung=r.get("crashed_or_hung", []), headless_changed=good,
         details=tried)
fact(f"of the top {TOP} add-ons, this many have at least one operator that finished headless with default settings and "
     "changed the scene (C-003)", count=len(usable), of=len(rows), which=usable)

rec = dict(experiment=os.path.relpath(os.path.abspath(__file__), ROOT), blender=version,
           machine=f"{platform.system()} {platform.machine()}", date=datetime.date.today().isoformat(), facts=facts,
           data=dict(platform=plat))
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results"), exist_ok=True)
text = json.dumps(rec, indent=1, default=str).replace(os.path.expanduser("~"), "~")
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "top_addons.json"), "w").write(text)
