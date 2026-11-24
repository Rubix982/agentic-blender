#!/usr/bin/env python3
"""Check the area pages against the evidence they cite.

  python3 tools/audit_pages.py [PAGE.md ...] [-v]

For every `[exp: path]` tag: the experiment exists and has a result. For every number in the same paragraph or list
item as that tag: it appears in one of the cited results (to the precision written, as a value or within a string), or
is listed as not found (card and thread ids, like C-011, and references to numbered items are not numbers). Also
counts paragraphs that state numbers with no tag at all. Prints a line per page and the
totals; -v lists every number not found. Numbers below 10 with no decimal point are skipped (counts like "3 islands"
are checked only when they have a decimal or are 10 or more), as are years and version numbers.
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
TAG = re.compile(r"\[exp: ([^\]]+)\]")
NUM = re.compile(r"(?<![\w.])-?\d[\d,]*(?:\.\d+)?(?![\w])")
VERSION = re.compile(r"\b\d+\.\d+(?:\.\d+)?\s*(?:LTS)?\b(?=[^\n]{0,0})")


def numbers_in(obj, out):
    if isinstance(obj, bool) or obj is None:
        return
    if isinstance(obj, (int, float)):
        out.append(float(obj))
    elif isinstance(obj, str):
        for m in NUM.findall(obj):
            try:
                out.append(float(m.replace(",", "")))
            except ValueError:
                pass
    elif isinstance(obj, dict):
        for k, v in obj.items():
            numbers_in(k, out)
            numbers_in(v, out)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            numbers_in(v, out)


def result_numbers(exp_path):
    script = os.path.join(ROOT, exp_path.strip())
    name = os.path.splitext(os.path.basename(script))[0]
    files = glob.glob(os.path.join(os.path.dirname(script), "results", f"{name}*.json"))
    nums = []
    for f in files:
        try:
            numbers_in(json.load(open(f)), nums)
        except (OSError, ValueError):
            pass
    return os.path.exists(script), files, nums


def matches(written, values, kind=None):
    s = written.replace(",", "")
    x = float(s)
    if kind in ("time", "ms"):   # timings vary run to run and with load: within a factor of 2, as tools/recheck.py does
        scale = (1, 1000) if kind == "ms" else (1, 0.001)
        return any(v > 0 and x > 0 and max(v * k, x) / min(v * k, x) <= 2 for v in values for k in scale)
    if kind == "mem":
        return any(v > 0 and x > 0 and abs(v - x) <= 0.1 * max(v, x) for v in values)
    dec = len(s.split(".")[1]) if "." in s else 0
    tol = 0.5 * 10 ** (-dec) + 1e-12
    for v in values:
        for cand in (v, v * 100, v / 100, v / 1000, v * 1000, v / 2**20 * 2**20):
            if abs(cand - x) <= tol or abs(round(cand, dec) - x) <= tol:
                return True
    return False


def blocks(text):
    """Paragraphs and list items: the unit a tag vouches for."""
    out, cur = [], []
    for line in text.splitlines():
        starts_item = re.match(r"\s*(?:[-*]|\d+\.)\s", line) and not line.startswith("    ")
        if not line.strip() or line.startswith("#") or line.startswith("```") or (starts_item and cur):
            if cur:
                out.append("\n".join(cur))
            cur = [] if not line.strip() or line.startswith(("#", "```")) else [line]
            continue
        cur.append(line)
    if cur:
        out.append("\n".join(cur))
    merged = []   # a table is vouched for by a tag line right under it, or by one right above it that ends in ':'
    for blk in out:
        is_table = blk.lstrip().startswith("|")
        prev = merged[-1] if merged else ""
        if prev.lstrip().startswith("|") and TAG.search(blk) and not is_table:
            merged[-1] += "\n" + blk
        elif is_table and TAG.search(prev) and prev.rstrip().endswith(":"):
            merged[-1] += "\n" + blk
        else:
            merged.append(blk)
    return merged


def audit(page, verbose):
    text = open(page).read()
    text = re.sub(r"```.*?```", "", text, flags=re.S)   # code is not a claim
    found = missing = untagged = tags = bad_tags = 0
    notes = []
    for b in blocks(text):
        cites = [c for c in TAG.findall(re.sub(r"`\[exp: path\]`", "", b)) if c.strip() != "path"]
        claim = re.sub(r"(?m)^\s*\d+\.\s", "", TAG.sub("", b))   # a list item's own number is not a claim
        claim = re.sub(r"`[^`]*`", "", claim)               # identifiers and code spans
        claim = re.sub(r"\[(?:inv|lesson|doc:[^\]]*|study:[^\]]*)\]", "", claim)
        claim = re.sub(r"https?://\S+", "", claim)
        claim = re.sub(r"\b[CT]-\d{3}\b", "", claim)                    # card and thread ids are names, not claims
        claim = re.sub(r"\bitems? \d+(?:\s*(?:to|and|,)\s*\d+)*", "", claim)   # cross-references to list items
        claim = re.sub(r"\b[234]\.\d+(?:\.\d+)?\b(?:\s*LTS)?", "", claim)   # Blender versions
        nums = [n for n in NUM.findall(claim) if "." in n or float(n.replace(",", "")) >= 10]
        nums = [n for n in nums if not (1900 <= float(n.replace(",", "")) <= 2100 and "." not in n)]
        if not cites:
            if nums and not re.search(r"\[(?:inv|lesson|doc|study)", b):
                untagged += 1
                if verbose:
                    notes.append(f"    untagged numbers {nums[:5]}: {b.strip()[:100]}")
            continue
        values = []
        for c in cites:
            tags += 1
            exists, files, vals = result_numbers(c)
            if not exists or not files:
                bad_tags += 1
                notes.append(f"    missing experiment or result: {c}")
            values += vals
        for n in nums:
            unit = re.search(re.escape(n) + r"(?:\s?(?:to|-|–|and|,)\s?[\d.,]+)*\s?(s|ms|seconds|MB|GB)\b", claim)
            kind = None if not unit else ("mem" if unit.group(1) in ("MB", "GB") else "ms" if unit.group(1) == "ms" else "time")
            if matches(n, values, kind):
                found += 1
            else:
                missing += 1
                if verbose:
                    notes.append(f"    not in results: {n}  ({b.strip()[:90]})")
    return dict(found=found, missing=missing, untagged=untagged, tags=tags, bad_tags=bad_tags), notes


def main():
    verbose = "-v" in sys.argv
    pages = [a for a in sys.argv[1:] if a != "-v"] or sorted(glob.glob(os.path.join(ROOT, "skills", "blender", "areas", "*.md")))
    tot = dict(found=0, missing=0, untagged=0, tags=0, bad_tags=0)
    for p in pages:
        r, notes = audit(p, verbose)
        for k in tot:
            tot[k] += r[k]
        n = r["found"] + r["missing"]
        print(f"{os.path.basename(p):26s} exp tags {r['tags']:3d} (broken {r['bad_tags']}), numbers checked {n:3d}, "
              f"found {r['found']:3d}, not found {r['missing']:3d}, untagged paragraphs with numbers {r['untagged']}")
        for line in notes:
            print(line)
    n = tot["found"] + tot["missing"]
    print(f"\nTOTAL: {tot['tags']} [exp] tags ({tot['bad_tags']} broken); {tot['found']} of {n} cited numbers found in "
          f"their results; {tot['untagged']} paragraphs state numbers with no tag")


if __name__ == "__main__":
    main()
