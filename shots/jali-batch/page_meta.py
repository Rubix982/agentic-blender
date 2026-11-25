"""C-022: for chosen Flickr photos, what their pages say: title, description, tags, date taken, and every size offered
(the original's when the owner allows it). Used to apply the card's rules (the monument cap, the size floor).

    python3 shots/jali-batch/page_meta.py ID [ID ...]   -> prints one JSON line per photo"""
import json
import re
import subprocess
import sys


def meta(pid, owner):
    h = subprocess.run(["curl", "-s", "-m", "40", "-A", "Mozilla/5.0", f"https://www.flickr.com/photos/{owner}/{pid}/"],
                       capture_output=True).stdout.decode("utf-8", "ignore")
    sizes = {}
    for k, u, w, hh in re.findall(r'"(\w{1,2})":\{"displayUrl":"([^"]+)","width":(\d+),"height":(\d+)', h):
        sizes[k] = dict(url="https:" + u.replace("\\/", "/"), w=int(w), h=int(hh))
    title = re.search(r'<meta property="og:title" content="([^"]*)"', h)
    desc = re.search(r'<meta property="og:description" content="([^"]*)"', h)
    tags = sorted(set(re.findall(r'"(?:raw|_content)":"([^"]{2,40})","(?:author|authorname|machine_tag)', h)))
    taken = re.search(r'"dateTaken":"?([^",]+)', h)
    lic = re.findall(r'creativecommons\.org/(?:licenses|publicdomain)/([a-z\-]+/[\d.]+)', h)
    big = max(sizes.items(), key=lambda kv: kv[1]["w"] * kv[1]["h"]) if sizes else (None, {})
    return dict(id=pid, title=title.group(1) if title else None, description=(desc.group(1) if desc else "")[:400],
                tags=tags[:30], taken=taken.group(1) if taken else None, licence_link=sorted(set(lic)),
                largest_key=big[0], largest=big[1], has_original="o" in sizes)


if __name__ == "__main__":
    known = {}
    for r in ("candidates_round1.json", "candidates_round2.json", "candidates_round3.json"):
        for p in json.load(open(r)):
            known[p["id"]] = p["owner"]
    for pid in sys.argv[1:]:
        print(json.dumps(meta(pid, known[pid])), flush=True)
