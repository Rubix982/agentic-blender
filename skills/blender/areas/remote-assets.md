# Remote assets: free HDRIs, textures and models from Poly Haven and ambientCG

Blender 4.5.14 LTS. Tags: `[exp: path]` measured here, `[doc: link]` documentation. Two scripts next to this page's
folder: `scripts/assets.py` searches and fetches (any Python, outside Blender), `scripts/asset_import.py` builds with
what was fetched (inside Blender). Experiments: `experiments/assets/remote_assets.py` (ten assets end to end) and
`experiments/assets/api_probe.py` (what the two APIs return) in the source repository.

Both sources are CC0: free for any use, commercial included, with no account and no credit needed for the assets.
Poly Haven's API terms ask that software calling the live API send its own User-Agent and say where the content comes
from; `assets.py` sends `agentic-blender/<version>` and prints the source with every result and in every manifest.
ambientCG is run by one person, so `assets.py` caches searches for a day and never fetches a file twice.
`[doc: https://github.com/Poly-Haven/Public-API/blob/master/ToS.md]` `[doc: https://docs.ambientcg.com/license/]`

## What goes wrong most often

1. **Opening a downloaded `.blend`.** ambientCG's zips hold a `.blend` beside the OBJ or USD (4 of the 4 ambientCG
   downloads here). A `.blend` can carry Python that runs once scripts are trusted. Import glTF, OBJ, FBX or USD
   instead; `asset_import.import_model` refuses `.blend`. `[exp: experiments/assets/api_probe.py]`
   `[doc: https://docs.blender.org/manual/en/4.5/advanced/scripting/security.html]`
2. **Reading `has_data` to see whether an imported texture loaded.** Every one of the 8 textures of the three imported
   models read `has_data = False` straight after import, although each file was there; after touching the pixels
   (`img.pixels[0]`) all 8 read True, and the renders were textured. Images load lazily: check the file
   (`os.path.exists(bpy.path.abspath(img.filepath))`) and touch the pixels. `[exp: experiments/assets/remote_assets.py]`
3. **A texture stretched over the whole object.** A 4 m plane's own UVs put one tile across 4 m.
   `uvs_to_real_size(obj, size_m)` measures metres per UV unit on the object and rescales the UVs; then a 1.4 m brick
   tile repeated every 179.16 px in a 512 px render of the 4 m plane, against 179.2 predicted.
   `[exp: experiments/assets/remote_assets.py]`
4. **Data maps in sRGB.** Roughness, metal, normal, displacement and opacity maps must be Non-Color and the colour map
   sRGB (`materials.md`). `material_from_maps` sets each; all four textures came out so.
   `[exp: experiments/assets/remote_assets.py]`
5. **The DirectX normal map.** Both sources ship an OpenGL and a DirectX normal map (Poly Haven `nor_gl` and `nor_dx`,
   ambientCG `NormalGL` and `NormalDX`); `assets.py` takes the GL one. `[exp: experiments/assets/api_probe.py]`
6. **ambientCG's v2 API for anything but materials.** Its `type` filter is ignored: `type=3DModel&q=rock` returned
   82 results, all materials. v3 applies it (0 rock models, 34 models in all); `assets.py` uses v3.
   `[exp: experiments/assets/api_probe.py]`
7. **Trusting ambientCG's sizes as metres.** It states no unit; the values (105 for Bricks060, 130 x 65 for
   WoodFloor043) read as centimetres, and the tiles then repeated at the right size in the render. Many assets give 0,
   meaning unknown. Poly Haven gives millimetres for every texture and model. `[exp: experiments/assets/api_probe.py]`
   `[exp: experiments/assets/remote_assets.py]`

## Fetch

```sh
python3 scripts/assets.py search texture brick wall        # both sources; --source polyhaven|ambientcg; -n 10
python3 scripts/assets.py search hdri sunny field
python3 scripts/assets.py search model chair --source polyhaven
python3 scripts/assets.py get polyhaven red_brick          # --res 1k|2k|4k|8k, --format jpg|png|exr|hdr
python3 scripts/assets.py get ambientcg 3DTreeStump001 --quality LQ   # an ambientCG model's mesh: LQ, SQ or HQ
python3 scripts/assets.py cache                            # what has been fetched
```

`get` prints a manifest (also `manifest.json` in the asset's folder): the maps by role (`color`, `normal`,
`roughness`, `metallic`, `displacement`, `ao`, `arm`, `opacity`), or the `hdri`, or the `model` path; `size_m` and where
it came from; the credit. Each Poly Haven file is checked against the size and md5 the API lists, each ambientCG zip
against its size, and zip members that would land outside the asset's folder are refused. Downloads live in
`~/.cache/agentic-blender/assets/` (`$AGENTIC_BLENDER_ASSET_CACHE` moves it); the ten assets below took 38.9 MB at 1k.
`[exp: experiments/assets/api_probe.py]`

Sizes at 1k: a Poly Haven HDRI 1.44 MB as `.hdr` (5.5 MB as `.exr`; 20.67 MB at 4k); an ambientCG material 7.9 MB
(Bricks060, JPG zip); an ambientCG model 7.4 MB at LQ, 19.9 MB at SQ. `[exp: experiments/assets/api_probe.py]`

## Build, inside Blender

```python
import sys; sys.path.insert(0, "<skill>/scripts")
import asset_import as ai

sky = ai.manifest("polyhaven", "kloofendal_48d_partly_cloudy_puresky")
ai.world_from_hdri(sky, strength=1.0, rotation_deg=90)
elevation, bearing = ai.hdri_sun(sky, rotation_deg=90)      # where the HDRI's sun is, after the turn
sun.rotation_euler = (math.radians(90 - elevation), 0, math.radians(180 - bearing))   # a Sun light on it

brick = ai.manifest("polyhaven", "red_brick")
wall.data.materials.append(ai.material_from_maps(brick))    # displacement as bump, 0.01 m; AO left out
ai.uvs_to_real_size(wall, brick["size_m"])                  # one tile = 1.4 m x 1.4 m on the wall

chair, size = ai.import_model(ai.manifest("polyhaven", "ArmChair_01"))   # new objects, and their size in metres
```

`material_from_maps` uses an ARM map (AO, roughness, metal in R, G and B) only for what has no map of its own: for
red_brick (no metal map) it supplied metal; for metal_plate, which has both, it was left out. AO is never connected:
Cycles and EEVEE compute occlusion. The material keeps the unused maps' names in `mat["unused_maps"]`.
`[exp: experiments/assets/remote_assets.py]`

## The ten assets, end to end (C-002)

Each checked as `CARD.md` set out before the run; 10 of the 10 passed, in 9.23 s for the whole experiment.
`[exp: experiments/assets/remote_assets.py]`

**HDRIs.** A grey sphere lit by each, mean brightness of its left and right halves, then with the world turned 180
degrees `[exp: experiments/assets/remote_assets.py]`:

| HDRI | Left, right | Turned 180: left, right | Brightest point found in a render | `hdri_sun` said |
|---|---|---|---|---|
| polyhaven kloofendal_48d_partly_cloudy_puresky | 0.3297, 0.6359 | 0.2828, 0.1415 | 47.5 up, bearing 124.5 | 48.0 up, 124.3 |
| polyhaven brown_photostudio_02 | 0.4067, 0.6917 | 0.2413, 0.1507 | 42.5 up, 130.5 | 43.1 up, 130.6 |
| ambientcg DaySkyHDRI072B | 0.1658, 0.2488 | 0.246, 0.1663 | 5.5 up, 89.5 | 5.1 up, 90.2 |

Turning the world by +90 degrees (`rotation_deg=90`, the Mapping node's Z) moved each brightest point's bearing by
+90 (clockwise seen from above, +Y north). Pixel (u, v) of an equirectangular HDRI sits at bearing 360 u - 90 and
elevation 180 (v - 0.5): the image's centre faces +X. `hdri_sun` uses that, within 0.8 degrees of the render.
`[exp: experiments/assets/remote_assets.py]`

**Textures.** On a 4 m plane after `uvs_to_real_size`, rendered from above at 128 px a metre; tile period from the
autocorrelation of the render `[exp: experiments/assets/remote_assets.py]`:

| Texture | Stated size | UVs reach | Tile, predicted | Tile, measured |
|---|---|---|---|---|
| polyhaven red_brick | 1.4 x 1.4 m | 2.8571, 2.8571 | 179.2 px | 179.16 px |
| polyhaven metal_plate | 0.5 x 0.5 m | 8.0, 8.0 | 64.0 px | 64.0 px |
| ambientcg Bricks060 | 1.05 x 1.05 m | 3.8095, 3.8095 | 134.4 px | 134.27 px |
| ambientcg WoodFloor043 | 1.3 x 0.65 m | 3.0769, 6.1538 | 166.4 x 83.2 px | 166.37 x 83.12 px |

**Models.** Imported size against the size the source states `[exp: experiments/assets/remote_assets.py]`:

| Model | File | Imported size (m) | Stated (m) | Triangles (stated polycount) |
|---|---|---|---|---|
| polyhaven ArmChair_01 | glTF | 0.8484 x 0.7658 x 1.0651 | 0.8484 x 0.7658 x 1.0651 | 5626 (5626) |
| polyhaven potted_plant_04 | glTF | 0.1679 x 0.1848 x 0.2675 | 0.1703 x 0.1859 x 0.2676 | 8929 (6097) |
| ambientcg 3DTreeStump001 | OBJ (LQ) | 0.9732 x 1.3983 x 0.2178 | none stated | 4999 |

Poly Haven's glTF models arrive in metres (the plant within 1.42 %); its "polycount" matched the triangle count for
the chair and not for the plant. The OBJ kept its own material (`3DTreeStump001_LQ-1K-JPG`, from its `.mtl`) with its textures, so no maps were
applied over it.
`[exp: experiments/assets/remote_assets.py]`

The contact sheet of all ten (HDRIs on spheres, textures from above, models on a floor) is
`experiments/assets/results/remote_assets-sheet.png`.

## Not covered

Megascans (behind an Epic account; reported free again in November 2026
`[doc: https://cgchannel.com/2026/11/epic-has-made-megascans-free-again-for-good-this-time]`), BlenderKit and Sketchfab
(accounts) are left out: no account is used here. Poly Haven's `.blend` and ambientCG's `.blend` and `.usdc` files are
not used.
