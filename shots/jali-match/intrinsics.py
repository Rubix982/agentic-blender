"""C-015: the photo split into the stone's own colour (albedo) and the light on it, by Marigold's intrinsic
decomposition (prs-eth/marigold-iid-lighting-v1-1, CreativeML OpenRAIL++-M; diffusers' MarigoldIntrinsicsPipeline, no
remote code).

    .venv/bin/python shots/jali-match/intrinsics.py [--ensemble N] [--steps N]
Runs in the repo's .venv (make.py runs it), offline from the local model cache (HF_HUB_OFFLINE=0 to download it).
Like normals.py: the photo at the working size (1230 x 1402) in overlapping tiles of the model's processing size
(768 px), blended with weights that fall to 0 towards a tile's inner edges. The model gives three linear maps: albedo
(at its true scale), shading and a residual (each up to a scale of its own, per tile); only the albedo is kept, since
the shading's scale changes from tile to tile. Writes out/albedo.npy (H x W x 3, linear), out/albedo.png (sRGB, to
look at) and results/intrinsics.json: the tiles, the time, how far tiles disagree where they overlap (the median
absolute difference of their albedos), and the albedo's luminance inside the screen's box (percentiles)."""
import json
import math
import os
import sys
import time

os.environ.setdefault("HF_HUB_OFFLINE", "1")
import numpy as np  # noqa: E402
import torch  # noqa: E402
from diffusers import MarigoldIntrinsicsPipeline  # noqa: E402
from PIL import Image  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from normals import TILE, OVERLAP, W, H, positions, feather  # noqa: E402
import shot  # noqa: E402  (C-022)

MODEL = "prs-eth/marigold-iid-lighting-v1-1"
argv = sys.argv[1:]
ENSEMBLE = int(argv[argv.index("--ensemble") + 1]) if "--ensemble" in argv else 3
STEPS = int(argv[argv.index("--steps") + 1]) if "--steps" in argv else None


def to_srgb(v):
    v = np.clip(v, 0, 1)
    return np.where(v <= 0.0031308, 12.92 * v, 1.055 * v ** (1 / 2.4) - 0.055)


if __name__ == "__main__":
    t0 = time.time()
    rgb = np.asarray(Image.open(shot.PHOTO).convert("RGB").resize((W, H), Image.LANCZOS))
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    try:
        pipe = MarigoldIntrinsicsPipeline.from_pretrained(MODEL, variant="fp16", torch_dtype=torch.float16).to(device)
    except OSError as e:
        raise SystemExit(f"{MODEL} is not in the local model cache ({e.__class__.__name__}); run once with "
                         "HF_HUB_OFFLINE=0 to download it (several GB), then again offline")
    pipe.set_progress_bar_config(disable=True)
    names = pipe.target_properties["target_names"]
    ia = names.index("albedo")
    acc = np.zeros((H, W, 3), np.float32)
    wsum = np.zeros((H, W), np.float32)
    tiles, preds = [], []
    for y0 in positions(H, TILE, OVERLAP):
        for x0 in positions(W, TILE, OVERLAP):
            t = time.time()
            out = pipe(Image.fromarray(rgb[y0:y0 + TILE, x0:x0 + TILE]), num_inference_steps=STEPS,
                       ensemble_size=ENSEMBLE, processing_resolution=TILE, match_input_resolution=True,
                       generator=torch.Generator(device="cpu").manual_seed(0), output_type="np")
            alb = np.asarray(out.prediction[ia], np.float32)            # TILE x TILE x 3, linear
            w = feather(x0, y0)
            acc[y0:y0 + TILE, x0:x0 + TILE] += alb * w[:, :, None]
            wsum[y0:y0 + TILE, x0:x0 + TILE] += w
            preds.append((x0, y0, alb))
            tiles.append(dict(x=x0, y=y0, seconds=round(time.time() - t, 1)))
            print("TILE", tiles[-1], flush=True)
    albedo = acc / np.maximum(wsum, 1e-6)[:, :, None]
    count = np.zeros((H, W), np.int32)
    for x0, y0, _ in preds:
        count[y0:y0 + TILE, x0:x0 + TILE] += 1
    dis = np.concatenate([np.abs(a - albedo[y0:y0 + TILE, x0:x0 + TILE])[count[y0:y0 + TILE, x0:x0 + TILE] > 1].ravel()
                          for x0, y0, a in preds])
    os.makedirs(shot.OUT, exist_ok=True)
    np.save(os.path.join(shot.OUT, "albedo.npy"), albedo)
    Image.fromarray((to_srgb(albedo) * 255).astype(np.uint8)).save(os.path.join(shot.OUT, "albedo.png"))
    rp = os.path.join(shot.RESULTS, "read_photo.json")
    bx0, by0, bx1, by1 = json.load(open(rp))["box"] if os.path.exists(rp) else (0, 0, W - 1, H - 1)
    lum = albedo[by0:by1 + 1, bx0:bx1 + 1] @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    res = dict(model=MODEL, licence="CreativeML OpenRAIL++-M", device=device, dtype="float16", size=[W, H], tile=TILE,
               overlap=OVERLAP, ensemble=ENSEMBLE, steps=STEPS or 4, seed=0, tiles=tiles, seconds=round(time.time() - t0, 1),
               overlap_albedo_abs_diff_median=round(float(np.median(dis)), 4),
               albedo_luminance_in_box_p10_p50_p90=[round(float(np.percentile(lum, q)), 4) for q in (10, 50, 90)])
    os.makedirs(shot.RESULTS, exist_ok=True)
    with open(os.path.join(shot.RESULTS, "intrinsics.json"), "w") as f:
        json.dump(res, f, indent=1)
    print("INTRINSICS", json.dumps({k: v for k, v in res.items() if k != "tiles"}), flush=True)
