#!/usr/bin/env python3
"""Fail if anything about to be committed holds a machine's home path or a name that must not appear here.

  python3 tools/check_private.py          checks every tracked or staged file (gzip files decompressed)
Names come from $BFG_PRIVATE_WORDS (comma-separated, kept out of the repository) plus the home folder's path.
"""
import gzip
import os
import subprocess
import sys

words = [os.path.expanduser("~")] + [w for w in os.environ.get("BFG_PRIVATE_WORDS", "").split(",") if w]
files = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], capture_output=True,
                       text=True).stdout.split()
bad = 0
for f in files:
    try:
        raw = gzip.open(f).read() if f.endswith(".gz") else open(f, "rb").read()
    except OSError:
        continue
    text = raw.decode("utf-8", "ignore").lower()
    for w in words:
        if w.lower() in text:
            print(f"{f}: contains a private word ({len(w)} chars)")
            bad += 1
sys.exit(1 if bad else 0)
