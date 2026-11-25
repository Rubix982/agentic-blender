# jali-match

A carved red-sandstone window screen (a jali; Agra area, 1630-50, Louvre Abu Dhabi) rebuilt in Blender from one
frontal photograph, rendered from the photo's viewpoint, and set beside it (cards C-007 to C-011 in `CARD.md`; the
photo and its licence in `photo/CREDIT.md`).

## Run it

```bash
# once: the Python environment for the normals model (Python 3.12; torch, diffusers)
python3.12 -m venv .venv && .venv/bin/pip install -r shots/jali-match/requirements.txt

# every time, from the repo's root
python3 shots/jali-match/make.py
```

`make.py` runs the steps in order (the two models first, since the photo's rule uses the normals) and stops at the first that fails:

| step | runs in | writes |
|---|---|---|
| `read_photo.py` | Blender | the photo sorted into surround, opening and stone: `results/read_photo.json`, `out/classes.png` |
| `normals.py` | `.venv` | Marigold's normals for the photo: `out/normals.npy`, `results/normals.json` (skipped when up to date) |
| `intrinsics.py` | `.venv` | Marigold's albedo for the photo, the stone's colour: `out/albedo.npy` (skipped when up to date) |
| `build.py` | Blender | the screen built, lit and rendered: `out/render.png`, `out/scene.blend`, `results/build.json` |
| `compare.py` | Blender | the measures and the sheet: `results/compare.json`, `sheet.jpg` |

The models (`prs-eth/marigold-normals-v1-1` and `prs-eth/marigold-iid-lighting-v1-1`, CreativeML OpenRAIL++-M) are
read from the local Hugging Face cache. The first time, run `normals.py` and `intrinsics.py` with `HF_HUB_OFFLINE=0`
to download them.

Options after `--` go to `build.py`. The earlier builds are a switch away: `--forms shading --no-normal-map
--photo-detail 0 --thick 0.020` gives C-009's build settings (on today's photo rule). `results/*_c00N.json` and `*_c011_*.json` keep each card's numbers.

Another photo: put it in `<folder>/photo/`, describe it in `<folder>/shot.json` (`shot.py` lists the fields: the file,
its size, the working size, the camera, the screen's width, the credit line), and run with `JALI_SHOT=<folder>`; the
outputs go to that folder's `out/`, `results/` and `sheet.jpg`. Without it, everything is this folder's, as before.
`shots/jali-batch/` runs the chain this way on eighteen other jalis (C-022).

## What comes from the photo

- **The outline** of the stone and every opening, by the rule in `common.classify` (green over red, near the wall's
  local colour, and not much brighter or darker than that wall).
- **Which way the carving faces**, from Marigold's normals: integrated into heights for the forms' shadows, and used
  as the front's normal map for its shading.
- **The weathering**: the photo's own light and dark (its pale specks taken out), tilting those normals.
- **The stone's colour**: Marigold's albedo of the photo, with the photo's pale specks put back into it.
- **The stone's hue, the wall's colour** in ten bands, and **the spotlight's power**, fitted to the stone's median.

Everything else (the solid, the sandstone, the light's direction, the camera from the photo's EXIF) is made in
`build.py`.
