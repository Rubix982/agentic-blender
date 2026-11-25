"""C-022: one shot folder per kept photo (selection.json), for make.py's chain (JALI_SHOT=<folder>).

    python3 shots/jali-batch/setup_shots.py
For each: shots/<slug>/photo/<flickr id>.jpg, the 2048 px size Flickr serves (its largest when smaller; downloaded
when missing), and shots/<slug>/shot.json (shot.py reads it). The chain works at the size where the photo's long side
is 1,402 px, as ours (1230 x 1402). The camera: Prof. Mortel's photos are the same phone as ours, 24 mm equivalent,
cropped from a 3000 px wide frame (the originals' EXIF); for the rest Flickr's resized files carry no EXIF, so 28 mm
equivalent is assumed, uncropped (the sensor width across the photo from the 43.27 mm diagonal). The screen's width is
assumed 1.05 m, as ours, for all: the relief, the thickness and the camera's distance scale with it."""
import json
import math
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
LONG = 1402


def sizes(page):
    h = subprocess.run(["curl", "-s", "-m", "40", "-A", "Mozilla/5.0", page], capture_output=True).stdout.decode("utf-8", "ignore")
    return {k: dict(url="https:" + u.replace("\\/", "/"), w=int(w), h=int(hh))
            for k, u, w, hh in re.findall(r'"(\w{1,2})":\{"displayUrl":"([^"]+)","width":(\d+),"height":(\d+)', h)}


def jpeg_size(path):
    """Width and height from a JPEG's SOF marker (no imaging library in the system Python)."""
    with open(path, "rb") as f:
        data = f.read()
    i = 2
    while i < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker, length = data[i + 1], int.from_bytes(data[i + 2:i + 4], "big")
        if marker in (0xC0, 0xC1, 0xC2):
            return int.from_bytes(data[i + 7:i + 9], "big"), int.from_bytes(data[i + 5:i + 7], "big")
        i += 2 + length
    raise ValueError(path)


if __name__ == "__main__":
    sel = json.load(open(os.path.join(HERE, "selection.json")))
    for p in sel["kept"]:
        folder = os.path.join(HERE, "shots", p["slug"])
        os.makedirs(os.path.join(folder, "photo"), exist_ok=True)
        name = f"{p['flickr_id']}.jpg"
        path = os.path.join(folder, "photo", name)
        szs = None
        if not os.path.exists(path):
            szs = sizes(p["page"])
            pick = szs.get("k") or max(szs.values(), key=lambda s: s["w"] * s["h"])
            subprocess.run(["curl", "-s", "-m", "120", "-o", path, pick["url"]], check=True)
        w, h = jpeg_size(path)
        s = LONG / max(w, h)
        work = [round(w * s), round(h * s)]
        if p["author"] == "Prof. Mortel":
            orig_w = {"51975487525": 2918, "51973919577": 2513}[p["flickr_id"]]
            lens, sensor, cam = 24.0, 25.96 * orig_w / 3000, "SM-G998B, 24 mm equivalent (the original's EXIF)"
        else:
            lens, sensor, cam = 28.0, 43.27 * w / math.hypot(w, h), "assumed: 28 mm equivalent, uncropped"
        meta = dict(photo=name, size=[w, h], work=work, lens_mm=lens, sensor_mm=round(sensor, 4), width_m=1.05,
                    credit=f"photograph ({p['author']}, {p['licence']})", camera=cam, source=p["page"],
                    title=p["title"], licence=p["licence"], author=p["author"], monument=p["monument"])
        json.dump(meta, open(os.path.join(folder, "shot.json"), "w"), indent=1)
        print(p["slug"], [w, h], work, lens, round(sensor, 2))
