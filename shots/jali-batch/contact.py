"""C-022: every shot's photo beside its render, for the user to judge at a glance, and a table of the measures.

    .venv/bin/python shots/jali-batch/contact.py [--classes] [--tag TAG]
Writes contact_1.jpg, contact_2.jpg, ... (six shots a page: the photo left, the render right, at the same size,
numbered as the shot's folder; a shot that did not reach a render shows its photo and the step it failed at) and
measures.json (the standard's measures and guards from each compare.json, with status.json's outcome). The pages
carry no measures, so the glance is not led by them. With --classes: reading_1.jpg, ... instead, each photo beside
read_photo.py's map of it (out/classes.png: openings white, stone orange, the dark surround black), to see where the
reading went wrong."""
import json
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
CELL_H, GAP, PER_PAGE, COLS = 560, 16, 6, 2


def font(size):
    for p in ("/System/Library/Fonts/Supplemental/Arial.ttf", "/Library/Fonts/Arial.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


CLASSES = __import__("sys").argv[1:].count("--classes") > 0
_argv = __import__("sys").argv[1:]
TAG = _argv[_argv.index("--tag") + 1] if "--tag" in _argv else ""   # C-023: contact_<tag>_N.jpg, measures_<tag>.json


def pair(slug, status):
    folder = os.path.join(HERE, "shots", slug)
    meta = json.load(open(os.path.join(folder, "shot.json")))
    photo = Image.open(os.path.join(folder, "photo", meta["photo"])).convert("RGB")
    w = round(photo.width * CELL_H / photo.height)
    photo = photo.resize((w, CELL_H), Image.LANCZOS)
    render_path = os.path.join(folder, "out", "classes.png" if CLASSES else "render.png")
    st = status.get(slug, {})
    failed = next((n for n in ("normals", "intrinsics", "read_photo", "build", "compare") if n in st and not st[n]["ok"]), None)
    if os.path.exists(render_path) and failed not in (("normals", "intrinsics", "read_photo") if CLASSES else
                                                       ("normals", "intrinsics", "read_photo", "build")):
        right = Image.open(render_path).convert("RGB").resize((w, CELL_H), Image.LANCZOS)
    else:
        right = Image.new("RGB", (w, CELL_H), (30, 30, 30))
        d = ImageDraw.Draw(right)
        d.text((16, CELL_H // 2 - 20), f"no render: {failed or 'not run'}", fill=(255, 120, 120), font=font(26))
    out = Image.new("RGB", (2 * w + 4, CELL_H + 34), (16, 16, 16))
    out.paste(photo, (0, 34))
    out.paste(right, (w + 4, 34))
    d = ImageDraw.Draw(out)
    d.text((6, 4), f"{slug}   photo | {'how it was read' if CLASSES else 'render'}", fill=(255, 230, 120), font=font(22))
    return out


if __name__ == "__main__":
    status = json.load(open(os.path.join(HERE, "status.json"))) if os.path.exists(os.path.join(HERE, "status.json")) else {}
    slugs = sorted(d for d in os.listdir(os.path.join(HERE, "shots")) if os.path.isdir(os.path.join(HERE, "shots", d)))
    for page in range(0, len(slugs), PER_PAGE):
        cells = [pair(s, status) for s in slugs[page:page + PER_PAGE]]
        cw = max(c.width for c in cells)
        rows = (len(cells) + COLS - 1) // COLS
        sheet = Image.new("RGB", (COLS * cw + (COLS + 1) * GAP, rows * (CELL_H + 34) + (rows + 1) * GAP), (40, 40, 40))
        for i, c in enumerate(cells):
            sheet.paste(c, (GAP + (i % COLS) * (cw + GAP), GAP + (i // COLS) * (CELL_H + 34 + GAP)))
        path = os.path.join(HERE, f"{'reading' if CLASSES else 'contact'}_{TAG + '_' if TAG else ''}{page // PER_PAGE + 1}.jpg")
        sheet.save(path, quality=88)
        print("PAGE", path, sheet.size)
    if CLASSES:
        raise SystemExit(0)
    rows = {}
    for s in slugs:
        cp = os.path.join(HERE, "shots", s, "results", "compare.json")
        r = dict(status={k: v["ok"] for k, v in status.get(s, {}).items()})
        if os.path.exists(cp):
            c = json.load(open(cp))
            sc = c.get("scorecard", {})
            r.update(measures={k: dict(value=v.get("value"), ok=v.get("ok")) for k, v in sc.get("measures", {}).items()},
                     guards={k: dict(value=v.get("value"), ok=v.get("ok")) for k, v in sc.get("guards", {}).items()},
                     all_met=sc.get("all_met"), guards_held=sc.get("guards_held"))
        rows[s] = r
    with open(os.path.join(HERE, f"measures{'_' + TAG if TAG else ''}.json"), "w") as f:
        json.dump(rows, f, indent=1)
    print("MEASURES", sum(1 for r in rows.values() if r.get("all_met")), "of", len(rows), "meet every core bar")
