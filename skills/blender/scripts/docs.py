#!/usr/bin/env python3
"""Search Blender 4.5's own manual and Python API reference offline.

  docs.py fetch                 download both (about 400 MB of zips, once), unpack, and build a text index
  docs.py index --src DIR       build the index from copies already unpacked in DIR (DIR/manual, DIR/api)
  docs.py search TERM [TERM...] [--api|--manual] [-n 10]
                                pages ranked by the terms, each with its public URL and the passage that matched
  docs.py page URL-OR-PATH [--section HEADING]
                                a page as plain text (or one section of it)

The copies and the index live in $AGENTIC_BLENDER_DOCS, else ~/.cache/agentic-blender/docs-4.5. Nothing is bundled with this
skill: the manual is CC-BY-SA 4.0 and the reference is Blender's; cite the public URL this prints.
"""
import gzip
import html
import json
import os
import re
import sys
import urllib.request
import zipfile

VERSION = "4.5"
ZIPS = {"api": f"https://docs.blender.org/api/{VERSION}/blender_python_reference_{VERSION.replace('.', '_')}.zip",
        "manual": f"https://docs.blender.org/manual/en/{VERSION}/blender_manual_html.zip"}
BASES = {"api": f"https://docs.blender.org/api/{VERSION}/", "manual": f"https://docs.blender.org/manual/en/{VERSION}/"}
HOME = os.environ.get("AGENTIC_BLENDER_DOCS") or os.path.expanduser(f"~/.cache/agentic-blender/docs-{VERSION}")
INDEX = os.path.join(HOME, "index.jsonl.gz")


def page_root(kind, src):
    """The folder that holds a kind's HTML pages: the zip has one top folder."""
    base = os.path.join(src, kind)
    entries = [e for e in os.listdir(base) if not e.startswith(".")] if os.path.isdir(base) else []
    if len(entries) == 1 and os.path.isdir(os.path.join(base, entries[0])):
        return os.path.join(base, entries[0])
    return base


TAGS = re.compile(r"<[^>]+>")
SKIP = re.compile(r"<(script|style|nav|footer|header)[^>]*>.*?</\1>", re.S | re.I)
HEAD = re.compile(r"<h([1-4])[^>]*>(.*?)</h\1>", re.S | re.I)


def text_of(fragment):
    return re.sub(r"\s+", " ", html.unescape(TAGS.sub(" ", fragment))).replace("¶", "").strip()


def parse(path):
    raw = open(path, encoding="utf-8", errors="ignore").read()
    m = re.search(r'itemprop="articleBody"[^>]*>(.*?)(<footer|<div class="rst-footer|$)', raw, re.S)
    body = SKIP.sub(" ", m.group(1) if m else raw)
    parts = HEAD.split(body)
    sections = [("", text_of(parts[0]))]
    for i in range(1, len(parts) - 2, 3):
        sections.append((text_of(parts[i + 1]), text_of(parts[i + 2])))
    title = re.search(r"<title>(.*?)</title>", raw, re.S)
    title = text_of(title.group(1)).split(" — ")[0] if title else os.path.basename(path)
    return title, [s for s in sections if s[0] or s[1]]


def build(src):
    os.makedirs(HOME, exist_ok=True)
    n = 0
    with gzip.open(INDEX, "wt", encoding="utf-8") as out:
        for kind in ("api", "manual"):
            root = page_root(kind, src)
            for dirpath, _, files in os.walk(root):
                for f in files:
                    if not f.endswith(".html") or f in ("genindex.html", "search.html", "py-modindex.html"):
                        continue
                    p = os.path.join(dirpath, f)
                    rel = os.path.relpath(p, root).replace(os.sep, "/")
                    title, sections = parse(p)
                    out.write(json.dumps(dict(kind=kind, url=BASES[kind] + rel, title=title,
                                              sections=[dict(h=h, t=t) for h, t in sections]),
                                         ensure_ascii=False) + "\n")
                    n += 1
    print(f"indexed {n} pages into {INDEX}")


def fetch():
    os.makedirs(HOME, exist_ok=True)
    for kind, url in ZIPS.items():
        z = os.path.join(HOME, f"{kind}.zip")
        if not os.path.exists(z):
            print(f"downloading {url}", flush=True)
            req = urllib.request.Request(url, headers={"User-Agent": "python-client"})
            with urllib.request.urlopen(req) as r, open(z + ".part", "wb") as f:
                while chunk := r.read(1 << 20):
                    f.write(chunk)
            os.rename(z + ".part", z)
        dest = os.path.join(HOME, kind)
        if not os.path.isdir(dest):
            with zipfile.ZipFile(z) as zf:
                for m in zf.namelist():   # pages only: the manual's images are most of its size
                    if m.endswith((".html", ".txt")) and ".." not in m and not m.startswith("/"):
                        zf.extract(m, dest)
    build(HOME)


def pages():
    if not os.path.exists(INDEX):
        sys.exit(f"no index at {INDEX}: run `docs.py fetch` (or `docs.py index --src DIR`)")
    with gzip.open(INDEX, "rt", encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)


def search(terms, kind=None, n=10):
    terms = [t.lower() for t in terms]
    hits = []
    for pg in pages():
        if kind and pg["kind"] != kind:
            continue
        title = pg["title"].lower()
        best, score_page = None, 0
        for s in pg["sections"]:
            h, t = s["h"].lower(), s["t"].lower()
            sc = 0
            for term in terms:
                c = t.count(term)
                if not c and term not in h and term not in title:
                    sc = 0
                    break
                sc += min(c, 8) + (6 if term in h else 0) + (4 if term in title else 0)
            if sc > score_page:
                score_page, best = sc, s
        if score_page:
            hits.append((score_page, pg, best))
    hits.sort(key=lambda x: -x[0])
    for sc, pg, s in hits[:n]:
        t = s["t"]
        i = min([t.lower().find(term) for term in terms if term in t.lower()] or [0])
        snippet = t[max(0, i - 120): i + 280]
        anchor = "#" + re.sub(r"[^a-z0-9]+", "-", s["h"].lower()).strip("-") if s["h"] else ""
        print(f"[{pg['kind']}] {pg['title']} > {s['h'] or '(top)'}\n  {pg['url']}{anchor}\n  ...{snippet}...\n")
    if not hits:
        print("no page has all of: " + ", ".join(terms))


def page(ref, section=None):
    ref = ref.split("#")[0]
    for pg in pages():
        if pg["url"] == ref or pg["url"].endswith("/" + ref.lstrip("/")):
            print(f"{pg['title']}  ({pg['url']})\n")
            for s in pg["sections"]:
                if section and section.lower() not in s["h"].lower():
                    continue
                if s["h"]:
                    print(f"## {s['h']}")
                print(s["t"] + "\n")
            return
    sys.exit(f"no page {ref!r}")


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
        return
    if a[0] == "fetch":
        fetch()
    elif a[0] == "index":
        build(os.path.expanduser(a[a.index("--src") + 1]) if "--src" in a else HOME)
    elif a[0] == "search":
        kind = "api" if "--api" in a else ("manual" if "--manual" in a else None)
        n = int(a[a.index("-n") + 1]) if "-n" in a else 10
        terms = [x for i, x in enumerate(a[1:], 1) if not x.startswith("--") and x != "-n" and a[i - 1] != "-n"]
        search(terms, kind, n)
    elif a[0] == "page":
        sec = a[a.index("--section") + 1] if "--section" in a else None
        page(a[1], sec)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
