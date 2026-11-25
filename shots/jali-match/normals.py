"""C-011: which way the jali's surface faces at every pixel of the photo, by Marigold normals v1.1.

    .venv/bin/python shots/jali-match/normals.py [--ensemble N] [--steps N]
Runs outside Blender, in the repo's .venv (requirements.txt beside this file; make.py runs it), offline from the local
model cache (prs-eth/marigold-normals-v1-1, CreativeML OpenRAIL++-M; diffusers' MarigoldNormalsPipeline, no remote
code; HF_HUB_OFFLINE=0 lets it download the model the first time). The photo
at the working size (common.SCALE: 1230 x 1402) is cut into overlapping tiles of the model's processing size (768 px),
so nothing is shrunk to fit one pass. Each tile's normals (x right, y up, z towards the viewer, unit length, as
diffusers documents them) are blended with weights that fall to 0 towards a tile's inner edges. Writes
out/normals.npy (H x W x 3, float32), out/normals.png (coloured 0.5 + 0.5 n), and results/normals.json: the tiles, the
time, how far neighbouring tiles disagree where they overlap, and a first check with no mask: inside the screen's box,
the correlation of the up-facing part (y) with a band like compare.py's forms band (two Gaussian blurs apart;
the light is from above, so it should be clearly positive)."""
import json
import math
import os
import sys
import time

os.environ.setdefault("HF_HUB_OFFLINE", "1")                           # from the local cache; HF_HUB_OFFLINE=0 to download
import numpy as np  # noqa: E402
import torch  # noqa: E402
from diffusers import MarigoldNormalsPipeline  # noqa: E402
from PIL import Image  # noqa: E402
from scipy.ndimage import gaussian_filter  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = "prs-eth/marigold-normals-v1-1"
TILE = 768                                                              # the model's own processing size
OVERLAP = 192
FEATHER = 96
sys.path.insert(0, HERE)
import shot  # noqa: E402  (C-022: which photo, and where the outputs go)
W, H = shot.WORK                                                        # common.size(): ours at half size, 1230 x 1402
argv = sys.argv[1:]
ENSEMBLE = int(argv[argv.index("--ensemble") + 1]) if "--ensemble" in argv else 3
STEPS = int(argv[argv.index("--steps") + 1]) if "--steps" in argv else None   # None: the model's default (4)


def positions(n, t, over):
    k = max(1, math.ceil((n - t) / (t - over)) + 1)
    return [round(i * (n - t) / (k - 1)) for i in range(k)] if k > 1 else [0]


def feather(x0, y0):
    """A tile's weight: 1 inside, falling to 0 over FEATHER px towards each edge that is not the photo's own edge."""
    xs, ys = np.arange(TILE, dtype=np.float32), np.arange(TILE, dtype=np.float32)
    wx = np.ones(TILE, np.float32)
    wy = np.ones(TILE, np.float32)
    if x0 > 0:
        wx = np.minimum(wx, (xs + 1) / FEATHER)
    if x0 + TILE < W:
        wx = np.minimum(wx, (TILE - xs) / FEATHER)
    if y0 > 0:
        wy = np.minimum(wy, (ys + 1) / FEATHER)
    if y0 + TILE < H:
        wy = np.minimum(wy, (TILE - ys) / FEATHER)
    return np.clip(wy[:, None] * wx[None, :], 1e-4, 1.0)


def blur(a, sigma):
    return gaussian_filter(a.astype(np.float32), sigma)


if __name__ == "__main__":
    t0 = time.time()
    photo = Image.open(shot.PHOTO).convert("RGB").resize((W, H), Image.LANCZOS)
    rgb = np.asarray(photo)
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    try:
        pipe = MarigoldNormalsPipeline.from_pretrained(MODEL, variant="fp16", torch_dtype=torch.float16).to(device)
    except OSError as e:
        raise SystemExit(f"{MODEL} is not in the local model cache ({e.__class__.__name__}); run once with "
                         "HF_HUB_OFFLINE=0 to download it (several GB), then again offline")
    pipe.set_progress_bar_config(disable=True)
    acc = np.zeros((H, W, 3), np.float32)
    wsum = np.zeros((H, W), np.float32)
    tiles, preds = [], []
    for y0 in positions(H, TILE, OVERLAP):
        for x0 in positions(W, TILE, OVERLAP):
            t = time.time()
            crop = Image.fromarray(rgb[y0:y0 + TILE, x0:x0 + TILE])
            out = pipe(crop, num_inference_steps=STEPS, ensemble_size=ENSEMBLE, processing_resolution=TILE,
                       match_input_resolution=True, generator=torch.Generator(device="cpu").manual_seed(0),
                       output_type="np")
            n = np.asarray(out.prediction[0], np.float32)                 # TILE x TILE x 3
            n /= np.maximum(np.linalg.norm(n, axis=2, keepdims=True), 1e-6)
            w = feather(x0, y0)
            acc[y0:y0 + TILE, x0:x0 + TILE] += n * w[:, :, None]
            wsum[y0:y0 + TILE, x0:x0 + TILE] += w
            preds.append((x0, y0, n))
            tiles.append(dict(x=x0, y=y0, seconds=round(time.time() - t, 1)))
            print("TILE", tiles[-1], flush=True)
    normals = acc / np.maximum(wsum, 1e-6)[:, :, None]
    normals /= np.maximum(np.linalg.norm(normals, axis=2, keepdims=True), 1e-6)
    # Where tiles overlap: each tile's angle from the blend, in degrees, at the pixels it shares with another tile.
    count = np.zeros((H, W), np.int32)
    for x0, y0, _ in preds:
        count[y0:y0 + TILE, x0:x0 + TILE] += 1
    dis = []
    for x0, y0, n in preds:
        shared = count[y0:y0 + TILE, x0:x0 + TILE] > 1
        cos = np.clip((n * normals[y0:y0 + TILE, x0:x0 + TILE]).sum(2), -1, 1)
        dis.append(np.degrees(np.arccos(cos[shared])))
    dis = np.concatenate(dis) if dis else np.zeros(1)
    os.makedirs(shot.OUT, exist_ok=True)
    np.save(os.path.join(shot.OUT, "normals.npy"), normals)
    Image.fromarray(np.clip((normals * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)).save(os.path.join(shot.OUT, "normals.png"))
    # The first check: up-facing against the forms band, inside the screen's box.
    y = (rgb.astype(np.float32) / 255) @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    forms = blur(y, 1.0) - blur(y, 3.5)                                 # sigmas near common.blur's 5 and 21 px widths
    rp = os.path.join(shot.RESULTS, "read_photo.json")                 # a new shot: the whole photo until it is read
    bx0, by0, bx1, by1 = json.load(open(rp))["box"] if os.path.exists(rp) else (0, 0, W - 1, H - 1)
    sl = (slice(by0, by1 + 1), slice(bx0, bx1 + 1))
    up_forms = float(np.corrcoef(normals[:, :, 1][sl].ravel(), forms[sl].ravel())[0, 1])
    res = dict(model=MODEL, licence="CreativeML OpenRAIL++-M", device=device, dtype="float16", size=[W, H],
               tile=TILE, overlap=OVERLAP, feather=FEATHER, ensemble=ENSEMBLE, steps=STEPS or 4, seed=0, tiles=tiles,
               seconds=round(time.time() - t0, 1),
               overlap_disagreement_deg=dict(median=round(float(np.median(dis)), 2),
                                             p90=round(float(np.percentile(dis, 90)), 2)),
               up_vs_forms_band_correlation=round(up_forms, 4),
               mean_normal=[round(float(v), 4) for v in normals[sl].reshape(-1, 3).mean(0)])
    os.makedirs(shot.RESULTS, exist_ok=True)
    with open(os.path.join(shot.RESULTS, "normals.json"), "w") as f:
        json.dump(res, f, indent=1)
    print("NORMALS", json.dumps({k: v for k, v in res.items() if k != "tiles"}), flush=True)
