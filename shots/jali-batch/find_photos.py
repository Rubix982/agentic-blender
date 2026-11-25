"""C-022: candidate photos of jalis, openly licensed, in the order the searches return them.

    python3 shots/jali-batch/find_photos.py
Flickr's public search pages (no key; the first page of each query, about 25 photos) filtered to the licences the card
allows: CC BY and CC BY-SA (2.0 and 4.0), CC0, the public domain mark, "no known copyright restrictions" and US
government works (Flickr licence ids 4, 5, 7, 8, 9, 10, 11, 12). Writes candidates_round1.json (or with --round2, candidates_round2.json): for each photo its id, owner,
title, licence, the largest size the page lists and its URL, and the queries that found it, in first-found order."""
import json
import os
import re
import subprocess
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
LICENCES = {4: "CC BY 2.0", 5: "CC BY-SA 2.0", 7: "no known copyright restrictions", 8: "US government work",
            9: "CC0 1.0", 10: "public domain mark", 11: "CC BY 4.0", 12: "CC BY-SA 4.0"}
QUERIES = ["jali", "jaali", "jali screen", "jali window", "stone jali", "marble jali", "sandstone jali",
           "pierced stone screen", "stone lattice window india", "jali fatehpur sikri", "sidi saiyyed jali",
           "jali mughal", "jali tomb", "jali mosque", "jali red fort", "jali humayun"]
# Round 2, after round 1's 130 gave 14 that met the rules: more places and words, and the second and third pages of the
# queries that gave most jalis. Only photos round 1 did not already list are added.
ROUND2 = [(q, 1) for q in ["jali agra fort", "jali taj mahal", "jali salim chishti", "jali delhi", "jali lahore",
                           "jali ahmedabad", "jali amber fort", "jali gwalior", "jali mandu", "jali bidar",
                           "marble screen mughal", "pierced window screen", "carved stone window lattice",
                           "jaali window", "jaali screen", "jali museum", "sandstone screen carved", "jharokha jali"]] + \
         [(q, p) for q in ["jali", "jaali", "jali window", "jali tomb", "jali mosque", "pierced stone screen"]
          for p in (2, 3)]
# Round 3, after round 2's 203 gave 5 more: words that name the screens rather than the place.
ROUND3 = [(q, 1) for q in ["jali work", "jaali work", "jali marble", "jali carving", "jali design", "mughal lattice",
                           "stone screen india", "pierced screen india", "lattice screen india", "fatehpur sikri screen",
                           "salim chishti screen", "humayun tomb screen", "itimad ud daulah jali", "sarkhej roza jali",
                           "jama masjid jali", "jali panel", "jaali marble", "jali sandstone"]] + \
         [(q, p) for q in ["jaali", "jali screen", "jaali window"] for p in (2,)]
# Round 4, after round 3's 55 left 19 that met every rule (the size floor and the cap on one monument took 10): more
# monuments with screens, and second pages of round 3's best queries.
ROUND4 = [(q, 1) for q in ["chausath khamba jali", "nizamuddin jali", "alai darwaza jali", "isa khan tomb jali",
                           "safdarjung tomb jali", "akbar tomb sikandra jali", "lodi jali", "golconda jali",
                           "champaner jali", "jahaz mahal jali", "city palace jali", "jaipur jali", "agra jali",
                           "delhi jaali", "marble jaali", "stone jaali", "jaali design", "jali gujarat"]] + \
         [(q, p) for q in ["jali panel", "stone screen india", "jali design", "humayun tomb screen",
                           "fatehpur sikri screen", "jaali work"] for p in (2,)]


def fetch(url):
    return subprocess.run(["curl", "-s", "-m", "40", "-A", "Mozilla/5.0", url], capture_output=True, check=True).stdout.decode("utf-8", "ignore")


def photos(html):
    out = []
    chunks = html.split('"_flickrModelRegistry":"photo-lite-models"')[1:]
    for seg in chunks:
        seg = seg[:20000]
        g = lambda k: (re.search(r'"' + k + r'":"?([^",]*)"?[,}]', seg) or [None, None])[1]
        lic = g("license")
        sizes = re.findall(r'"(\w{1,2})":\{"data":\{"displayUrl":"([^"]+)","width":(\d+),"height":(\d+)', seg)
        if not sizes or lic is None:
            continue
        big = max(sizes, key=lambda s: int(s[2]) * int(s[3]))
        pid = re.search(r'/(\d+)_\w+(?:_\w)?\.jpg', big[1].replace("\\/", "/"))
        title = re.search(r'"title":"((?:[^"\\]|\\.)*)"', seg)
        try:
            t = json.loads('"' + title.group(1) + '"') if title else ""
        except ValueError:
            t = title.group(1)
        user = re.sub(r"@[A-Za-z0-9.-]+\.[a-z]{2,}$", "", g("username") or "")   # an email as a display name: its name part
        out.append(dict(id=pid.group(1) if pid else None, owner=g("ownerNsid"), username=user,
                        title=t, licence_id=int(lic),
                        largest=dict(key=big[0], w=int(big[2]), h=int(big[3]), url="https:" + big[1].replace("\\/", "/"))))
    return out


if __name__ == "__main__":
    import sys
    r2, r3, r4 = "--round2" in sys.argv, "--round3" in sys.argv, "--round4" in sys.argv
    known = set()
    for r in (["candidates_round1.json"] if r2 else []) + (["candidates_round1.json", "candidates_round2.json"] if r3 else []) + \
             (["candidates_round1.json", "candidates_round2.json", "candidates_round3.json"] if r4 else []):
        known |= {p["id"] for p in json.load(open(os.path.join(HERE, r)))}
    found, order = {}, []
    lic = urllib.parse.quote(",".join(str(k) for k in LICENCES))
    for q, page in (ROUND4 if r4 else ROUND3 if r3 else ROUND2 if r2 else [(q, 1) for q in QUERIES]):
        html = fetch(f"https://www.flickr.com/search/?text={urllib.parse.quote(q)}&license={lic}" + (f"&page={page}" if page > 1 else ""))
        ps = photos(html)
        print("QUERY", q, page, len(ps), flush=True)
        for p in ps:
            if p["id"] is None or p["licence_id"] not in LICENCES or p["id"] in known:
                continue
            if p["id"] not in found:
                p["licence"] = LICENCES[p["licence_id"]]
                p["page"] = f"https://www.flickr.com/photos/{p['owner']}/{p['id']}/"
                p["queries"] = []
                found[p["id"]] = p
                order.append(p["id"])
            found[p["id"]]["queries"].append(q if page == 1 else f"{q} (page {page})")
    name = "candidates_round4.json" if r4 else "candidates_round3.json" if r3 else "candidates_round2.json" if r2 else "candidates_round1.json"
    with open(os.path.join(HERE, name), "w") as f:
        json.dump([found[i] for i in order], f, indent=1)
    print("CANDIDATES", len(order))
