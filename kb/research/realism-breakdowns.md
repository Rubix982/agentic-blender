# How photoreal Blender environments are built: 17 published breakdowns

_Compiled 2026-11-23 by a research agent from generic web searches (nothing downloaded, no sign-ups). Checked
afterwards against the pages themselves: six quotes (S9, S10, S12, S14, S15, S17) and five numbers (S5's 512 samples
and hand placement, S14's 64 samples and 5200 K, S15's 16-25 minutes) were found word for word; the agent had
re-checked S4 to S7. Used by `skills/blender/areas/realism.md` (card C-004)._

## How this was gathered, and what to check before citing

- About 60 pages were opened, counting contest winner lists and re-checks. **17 are kept** (below). 12 more were read but are too thin to count, and 27 were excluded. Both groups are listed at the end with the reason for each.
- A source was kept when it met three tests. It gives the artist's own account (first person, an interview, or the artist's forum replies). Blender is the main tool and, as far as the source says, the renderer. And it depicts a realistic environment that the source does not describe as painterly or stylized.
- **Photoreal aim.** Several kept sources never use the word "photoreal" or "realistic". Each entry has a *Photoreal aim* line that says what the source itself states, so a reader can drop the uncertain ones.
- **Extraction method.** Pages were read through a fetch tool that answers questions about the page. I asked it for verbatim quotes and for "not stated" whenever a field is absent. The quotes behind the surprising findings (S4, S5, S6, S7) were fetched a second time and checked word for word. Spot-check the other quotes against the page before publishing them.
- "—" means the source does not state it. Nothing here is inferred. Where a fact is ambiguous, the entry says "uncertain".
- Benjamin Roman appears twice (S1, S3). These are two different pieces, two contests and two accounts.

Source IDs: contest-placed pieces come first (S1–S3), then editor-featured breakdowns.

---

## S1. Galerie Vivienne — Benjamin Roman ("Arethyu")

- **URL:** https://blenderartists.org/t/galerie-vivienne/1309855 (artist's thread). Placement: https://blenderartists.org/t/these-are-the-winners-of-the-best-of-blender-artists-2021/1350993
- **Year:** 2021 (first post 11 Jun 2021)
- **Contest / feature:** Best of Blender Artists 2021, Interior architecture, **Grand winner**. Also on the Blender Artists featured row.
- **Photoreal aim:** a recreation of a real place (Galerie Vivienne, Paris). The artist wanted "to capture the unique feeling of this passage." The word photoreal is not used.
- **Blender version:** —
- **Engine / settings:** Cycles (the artist says the floor node tree "hit the cycles' limit of complexity"). Samples, denoiser, resolution, render time and hardware: —
- **Assets:** some Quixel textures and assets; Chocofur assets (teapot, mugs); the rest hand-modelled, sculpted and shaded by the artist; **own photogrammetry** of the detail around the "25" number, scanned at the real location.
- **Scattering / vegetation:** The Grove 3D (trees); Thomas Luft's Ivy generator.
- **Lighting:** the Nishita sky node "completely carrying the lighting of the render." HDRI, volumetrics: —
- **Materials:** fully procedural floor (about 150 hours). Bump and saturation were lowered on the final floor shader. Channel maps were made by rendering each channel with an orthographic camera.
- **Camera:** —
- **Reference:** the real location (scanned on site). Reference photos: —
- **Post:** — (some preview images are labelled "post processed", with no detail given)
- **Time:** floor alone about 150 h; total —
- **Quote (Benjamin Roman):** "the Nishita sky node that is completely carrying the lighting of the render."

## S2. Stranded — Akhil Alukkaran (Akhil_A_B)

- **URLs:** https://www.blendernation.com/2022/08/17/behind-the-scenes-stranded/ (artist's own account, BlenderNation Behind the Scenes); https://blenderartists.org/t/stranded/1393322 (thread); https://foxrenderfarm.com/news/how-to-create-overgrown-cityscape-environment-with-last-of-us-vibe (interview). Placement: https://blenderartists.org/t/these-are-the-winners-of-the-best-of-blender-artists-2022/1441381
- **Year:** 2022
- **Contest / feature:** Best of Blender Artists 2022, Landscapes, **Grand winner** (per the 2022 winners thread). **FGT Art August 2022 winner** (per Fox Renderfarm). The Fox interview also mentions a Top-100 placing in Pwnisher's *Moving Meditations*; which piece that refers to is unclear. Also featured on BlenderNation.
- **Photoreal aim:** — (the artist calls it "a quick environment setup in Blender"; post-apocalyptic overgrown city)
- **Blender version / engine / settings / hardware:** —
- **Assets:** a **third-party photo-scanned model** of the former Royal Doulton offices (Sketchfab, by artflech), broken into portions and kitbashed. Trees from The Grove 3D, sometimes Maxtree models. Ivy leaf model customised by the artist.
- **Scattering / vegetation:** Blenderesse's ivy generator, built on geometry nodes ("I generated ivy using geometry nodes and it was a bit heavy"). Trees placed on the ground and on rooftops.
- **Lighting:** the Fox interview gives an overcast HDRI from Poly Haven. Uncertain whether this refers to *Stranded* or to his Pwnisher piece.
- **Materials:** the building texture mixed with a moss texture, using an ambient occlusion node as the mask.
- **Camera:** —
- **Reference:** none. The artist says there were "not any references as such."
- **Post:** "basic composition corrections"; software —
- **Time:** "around 2 days" (scope unclear)
- **Quote (Akhil Alukkaran, forum reply):** "Building models are not perfect for closeups since those are 3d scanned"

## S3. Discovered in Ice — Benjamin Roman

- **URL:** https://www.foxrenderfarm.com/news/telling-a-mysterious-ice-adventure-story-in-blender
- **Year:** 2020 (22 Apr 2020)
- **Contest / feature:** CG Boost 13th challenge, "Discovered in Ice", **1st place**
- **Photoreal aim:** — (Nordic church in a glacier cave with a lone explorer)
- **Blender version:** 2.81
- **Engine / settings:** —. The background was rendered separately from the main scene. Hardware: a "good gaming laptop".
- **Assets:** BlenderKit ice and snow materials; HDRI from hdrihaven.com
- **Scattering:** —
- **Lighting:** a uniform HDRI, tinted blue and sharply reduced for ambient light. A strong spotlight stands in for sunlight through a hole in the ice, its intensity varied with noise so no circular shape shows. A very large area light in the background gives diffuse light from the far end of the cave. Fog was added in Photoshop, not in Blender.
- **Materials:** low-poly, roughly sculpted snow; micro-polygon displacement on the roof so the wooden tiles interact with the snow
- **Camera / composition:** cave forms make a spiral that leads the eye to the church on a high place. Focal length, DoF: —
- **Reference:** photos taken by the artist's brother in Norway; PureRef moodboard
- **Post:** Photoshop for composition, colour correction, curves/levels, fog and light rays
- **Time:** about 70 h (a little over a week at 7 h a day)
- **Quote (Benjamin Roman):** "Is this texture resolution necessary?"

## S4. Windowsill — Rayan Zomorodi

- **URL:** https://80.lv/articles/how-to-make-scene-so-realistic-that-no-one-believes-it-was-made-in-blender
- **Year:** 2024 (80.lv interview, 5 Feb 2024)
- **Contest / feature:** — (80.lv editorial interview)
- **Photoreal aim:** stated (title; the artist aimed for the look of "a mirrorless camera or a cinema camera")
- **Blender version:** —
- **Engine / settings:** engine not named. Noise threshold 0.0360, max samples 2600, light bounces 0–10 (volume 0). Per-object denoising in the compositor was tried and dropped. Resolution, render time, hardware: —
- **Assets:** hand-modelled (Subdivision Surface), candle sculpted. **Own 3D scans**: "I even 3D-scanned every other large object in the room as well, like the sofa, desk, kitchen". High-res PBR maps. A free rainy-window shader (Blue Inversion, Gumroad). The Physics Dropper add-on for the pencils.
- **Scattering:** Blender particle systems for dust and hair stuck to objects, placed with weight painting
- **Lighting:** HDRI for the exterior light, plus a **light portal** next to the windows; an emissive bulb with a Blackbody node
- **Materials:** masked fingerprints, dust, dirt and spillage, placed where they make physical sense
- **Camera:** aimed for a super-wide-angle look (no focal length given); keyframed focus distance (DoF); motion blur. Camera motion was recorded from an iPhone with VirtuCamera. A cutout photo of a person was parented to the camera to create reflections and shadows.
- **Reference:** the real room, referenced "mostly by eye"
- **Post:** chose *not* to add "lots of chromatic aberration, to lower the dynamic range or to shift the exposure". Photoshop for sticker designs.
- **Time:** about two months, part-time
- **Quotes (Rayan Zomorodi):** "putting the fingerprints on the glass where someone would actually hold the glass" / "I wanted it to look like it was shot on a mirrorless camera or a cinema camera with a super wide-angle lens."

## S5. Korean street — Gaurav ("World of Gaurav")

- **URL:** https://80.lv/articles/look-how-you-can-create-a-photoreal-korean-street-using-blender
- **Year:** 2023 (80.lv interview, 11 Dec 2023)
- **Contest / feature:** — (80.lv editorial interview)
- **Photoreal aim:** stated (title; inspired by Steffen Hampel's photoreal alley course)
- **Blender version:** —
- **Engine / settings:** Cycles, 512 samples, noise threshold 0.05, OpenImageDenoise, tile 256, default light paths. Rendered on a laptop's CPU because the GPU ran out of VRAM.
- **Assets:** low-poly buildings modelled by hand (extrude, inset, booleans, mirror/array); props and details from Sketchfab and Megascans; botaniq plants; textures from Textures.com and Megascans
- **Scattering:** none. "I didn't use any scattering techniques or add-ons to scatter things around. I placed everything manually"
- **Lighting:** HDRI, desaturated with a Hue/Saturation node "to get a realistic look" and rotated with a Mapping node; the look was changed from sunset to overcast
- **Materials:** 2–3 PBR/image textures mixed for variation; UVs plus triplanar (box) projection; decals "like dirt and leaks for buildings"
- **Camera:** set to match the reference image; focal length, DoF: —
- **Reference:** two photos (a Korean and a Japanese street) blended in Photoshop, then imported as image planes to guide the layout
- **Post:** Photoshop to add the sky, colour-correct, and add small wall cracks. Camera Raw filter "to add some grain, as well as a touch of chromatic aberration and vignetting".
- **Time:** —
- **Quotes (Gaurav):** "textures and lighting play the most important role in bringing photorealism to any scene" / "You can learn a lot by studying how things look in real life."

## S6. Mountain monastery — Maarten Nauta

- **URL:** https://80.lv/articles/making-a-mountain-monastery-environment-with-blender-gaea-speedtree. Supplementary (same artist, news piece with his quotes): https://80.lv/articles/a-large-scale-mountain-castle-environment-made-in-blender
- **Year:** 2023 (interview 25 May 2023; castle news 2 May 2023)
- **Contest / feature:** — (80.lv editorial interview)
- **Photoreal aim:** —
- **Blender version:** —
- **Engine / settings:** not named anywhere in the interview (checked). Output to multilayer EXR. Hardware: an "average rig". For the castle: a 3060 Ti with 8 GB VRAM, four days to render.
- **Assets:** monastery modelled in Blender; mountains from Gaea (his Classic Mountain Pack); Megascans small vegetation, rocks and twigs; SpeedTree Cinema 9 conifers with a Quixel spruce trunk; Geo-Scatter "Moss Biome"
- **Scattering:** Geo-Scatter, both manual scatter (including the chain tool for fences) and biome scatter; weight painting for the grass field; Bezier-curve masks to keep areas near the monastery clear
- **Lighting:** a single HDRI (Pro-Lighting Skies) with the sun boosted by 1000 via EasyHDRI; a gobo plane for animated cloud shadows. "The atmosphere is a huge cube with a principled volume node as material" (very low density, anisotropy 0.9, slight blue emission). VDB clouds.
- **Materials:** displacement on the foreground cliffs; "I deleted the adaptive subdiv modifier in the foreground and scattered small rocks and twigs instead." Mostly 2K/1K textures. Castle: "the small rocks and twigs scattered on the road look more convincing than the displaced texture!"
- **Camera:** an animated pan revealing the valley; focal length, DoF: —
- **Reference:** Lorenzo Lanfranconi's painting "Walk to San Donato" (composition); southern Swiss Alps near the Matterhorn (biome); iNaturalist (local flora); alpine peaks in France and Switzerland
- **Post:** After Effects with the filmic transform reapplied; "comping in imperfections such as grain, glow, and chromatic aberration"
- **Time:** —
- **Quotes (Maarten Nauta):** "don't be scared to go 2K or even 1K." / "I try to use references of the trees in the biome that I am trying to create."

## S7. Cathedral at the end of day — Stan (Stanislaw) Kazimiraw

- **URL:** https://www.blendernation.com/2024/11/11/behind-the-scenes-cathedral-at-the-end-of-day/
- **Year:** 2024 (11 Nov 2024)
- **Contest / feature:** BlenderNation "Behind the Scenes" (the editor's byline, with the artist's first-person text)
- **Photoreal aim:** — (a medieval Rotterdam scene based on the real Grote of Sint-Laurenskerk)
- **Blender version:** — (no add-ons used; Substance Designer, Substance Painter and Photoshop alongside)
- **Engine / settings:** "Cycles with approximately 650 samples without denoising". NLM and OptiX were tried and dropped because they made the image look faded. Resolution, time, hardware: —
- **Assets:** everything modelled from scratch at real-world scale; trees made with the Skin modifier and baked to transparent textures
- **Scattering:** —
- **Lighting:** "HDRI in combination with the position of the sun on January 15, 1480, at 16:00 in Rotterdam". The angles came from an external solar-position calculator (azimuth about 232.5°, elevation about 9°) and the sun was placed by eye to match its angular diameter. A 6 km skydome.
- **Atmosphere:** "created using an emission shader instead of principled volume", for less noise and better performance. Chimney smoke, ground mist and haze were first simulated with fluid physics, then baked into black-and-white textures combined through the RGB channels.
- **Materials:** Diffuse and Glossy BSDFs mixed with the specular map as mask; procedural noise and Musgrave for variation; dirt and soil masks from Substance Designer. **Textures 256, 512 and 1024 px.**
- **Camera:** —
- **Reference:** the church's plans and measurements; photos taken by his mother in the Netherlands; internet photos of the Archeon museum park
- **Post:** Blender Compositor (colour, effects, detail)
- **Time:** —
- **Quote (Kazimiraw):** "This allows the models to be lightweight while still appearing visually rich."

## S8. Misty Mountains — Jaspreet Singh Matharoo

- **URL:** https://www.blendernation.com/2023/08/14/behind-the-scenes-misty-mountains/
- **Year:** 2023 (14 Aug 2023)
- **Contest / feature:** BlenderNation "Behind the Scenes" (artist's first-person account)
- **Photoreal aim:** —
- **Blender version / engine / settings / hardware:** —
- **Assets:** base terrain from A.N.T. Landscape (River preset), then sculpted; mountains from Gaea; vegetation from PRO Forest Bundle, Botaniq, Tree Vegetation, Forestation and Moss Biome Ground Scatter; CloudScapes clouds; Alpha Trees; a foam texture from "texture.com" (as published)
- **Scattering:** Geo-Scatter
- **Lighting:** a sky-only HDRI from AmbientCG; a sun lamp at strength 10, angle 2, slightly orange; a volumetric cube over the scene; fog cards behind parts of the scene
- **Materials:** a custom mountain node setup blending grass, rock and gravel with Gaea masks (slope, flow); the foam texture edited in Photoshop and placed with Images-as-Planes
- **Camera:** —
- **Reference:** a Luca Bravo photo on Unsplash; Bob Ross paintings
- **Post:** Photoshop Camera Raw for colour; dark areas brightened; a man in a boat added
- **Time:** —
- **Quote:** none on realism

## S9. Bird House — Adarsh Gowda

- **URL:** https://www.blendernation.com/2022/09/19/behind-the-scenes-bird-house/
- **Year:** 2022 (19 Sep 2022)
- **Contest / feature:** BlenderNation "Behind the Scenes" (artist's first-person account). Commissioned for BProduction's CAM-FX add-on.
- **Photoreal aim:** the artist describes "a realistic approach"
- **Blender version:** —
- **Engine / settings:** engine not named. A test example used noise threshold 0.05, 1000 samples, a 4-minute limit and 4K. Final settings and hardware: —
- **Assets:** Megascans wood, moss, lichen and small branches; Shagbark hickory trees from the ArtStation marketplace, upscaled with an AI upscaler; free Maxtree foreground trees; free Graswald plants and moss; grassblade add-on (mushrooms, dead leaves); moths from Ian Hubert's Patreon; birdhouse hand-modelled with rusty screws
- **Scattering:** Scatter5 driving particle systems, with density from weight-painted vertex groups; mushrooms and feathers placed by hand
- **Lighting:** Poly Haven HDRI "Spaichingen Hill", sun brightness raised with the Easy-HDRI add-on
- **Materials:** Megascans wood with a noise-driven darker hue variant; geometry made irregular with bevels, irregular scaling and proportional editing
- **Camera:** CAM-FX (bokeh shape, lens dirt). Whether those were used in the final image is uncertain. Focal length: —
- **Reference:** an Unsplash photo for the birdhouse shape
- **Post:** After Effects colour correction, chromatic aberration, vignette, "a little glow", hue-vs-hue curves shifting greens toward yellow, film grain
- **Time:** —
- **Quotes (Adarsh Gowda):** "I added a little amount of film grain to break the smooth render." / "making the birdhouse look irregular by scaling in beveled edges"

## S10. Forest Creature — Arnaud Imobersteg

- **URL:** https://garagefarm.net/making-of-forest-creature-by-arnaud-imoberstegusing-blender-and-graswald (the artist's ArtStation making-of, republished by GarageFarm)
- **Year:** 2019 (28 Oct 2019)
- **Contest / feature:** GarageFarm blog republication
- **Photoreal aim:** — (a fantasy creature in a realistic forest; the references are paintings)
- **Blender version:** — (2.80 mentioned as context)
- **Engine / settings:** engine not named explicitly (uncertain). Rendered on the GarageFarm render farm.
- **Assets:** Graswald presets (grass, moss, flowers); Megascans photoscanned rock and fern; CMV textures; creature sculpted with rock brushes; ground and bubbles hand-modelled
- **Scattering:** Graswald particle systems; density painted with vertex groups; hand placement by instancing (Alt+D); particle systems for the farthest trees, bushes and rocks
- **Lighting:** HDRI with a sun from the left (uncertain whether a separate lamp); a row of instanced trees used only to cast shadows; a low-density volume-scatter cube for forest humidity and god rays
- **Materials:** micro-displacement (adaptive subdivision, "true" displacement) on a photoscanned forest-ground texture; moss vertex-painted onto trees and rocks
- **Camera:** **24 mm (APS-C)**, frontal view with a clear foreground; the tree row gives a vignette-like frame
- **Reference:** Ivan Shishkin, *Forest Cemetery* (1893); Guillem H. Pongiluppi's Cthulhu illustration (2017)
- **Post:** Photoshop layering and grading; a Z-depth fog pass with a normalize node; painted smoke; black-and-white and colour-checker passes
- **Time:** —
- **Quotes (Arnaud Imobersteg):** "it's quite important you use at least 4 or 5 different species." / "check your image in black and white, ensuring you have right values!"

## S11. Half-Life-inspired basement — Ivan Novikov

- **URL:** https://80.lv/articles/half-life-inspired-enviroment-using-eeeve-and-megascans-library
- **Year:** 2020 (80.lv interview, 6 Aug 2020)
- **Contest / feature:** — (80.lv editorial interview)
- **Photoreal aim:** the artist says "it's totally possible to get realistic results with Eevee."
- **Blender version:** —
- **Engine / settings:** **EEVEE**: AO and Screen Space Reflections on; shadow cube and cascade sizes raised; Bloom on; Contact Shadows on lamps
- **Assets:** Megascans decals, materials and models; the Piperator add-on; a Blendswap triplanar material modified for PBR; hand-modelled walls subdivided for vertex painting
- **Scattering:** —
- **Lighting:** one static area lamp; Irradiance Volume probes; Reflection Cubemaps; Reflection Planes on the water and floor; fake caustics on the walls near the water
- **Materials:** procedural animated water; Voronoi-based puddles; vertex-paint blending between two texture sets; layered decals for cracks, leaks and graffiti; Megascans roughness and colour retuned
- **Camera:** —
- **Reference:** Half-Life 2; a photo pack of abandoned buildings; Gleb Alexandrov's work
- **Post:** Bloom only
- **Time:** started two weeks before its ArtStation release
- **Quotes (Ivan Novikov):** "By layering decals, you can tell a story of surface decay." / "I always try to improve the materials that I get from Megascans."

## S12. Photoreal mountain and salt-flat landscape — Rickhard Norberg

- **URL:** https://80.lv/articles/atmospheric-photorealistic-landscape-made-with-gaea-blender
- **Year:** 2025 (80.lv interview, 16 Jun 2025)
- **Contest / feature:** — (80.lv editorial interview)
- **Photoreal aim:** stated (title)
- **Blender version:** —
- **Engine / settings:** engine not named; 500 samples, "standard settings". Hardware: —
- **Assets:** Gaea terrain with an erosion node; Quixel rock textures; custom grass patches; grass pods and mud hand-modelled, subdivided and sculpted
- **Scattering:** grass patches scattered onto the pods with geometry nodes
- **Lighting:** the Physical Starlight and Atmosphere add-on for the sky; fog over the water (method —)
- **Materials:** rock and soil textures blended with a noise texture; Gaea's colour output layered on top; water as a plane with a water texture
- **Camera:** —
- **Reference:** a Pinterest image of salt flats (spelled "Northon Salt Flats" in the article) for composition and the look of the pods
- **Post:** DaVinci Resolve grading, glow and grain
- **Time:** one day
- **Quotes (Rickhard Norberg):** "so that they wouldn't look perfectly flat, as that quickly breaks the realism." / "add some glow and grain to get that film camera feeling"

## S13. Amboseli National Park recreation — Yash Jain

- **URL:** https://80.lv/articles/how-to-recreate-a-scene-from-the-amboselli-national-park-in-kenya
- **Year:** 2026 (80.lv interview, 3 Jul 2026)
- **Contest / feature:** — for this piece (the article mentions an unrelated earlier 5th place)
- **Photoreal aim:** "I wanted it to feel accurate to reality" (said of the mountain)
- **Blender version / engine / settings:** —
- **Assets:** terrain from the A.N.T. Landscape add-on plus sculpting; a real heightmap refined in Gaea; Botaniq foliage; an elephant bought on CGTrader
- **Scattering:** — (Botaniq named, no scatter tool)
- **Lighting:** "built from scratch"; no details
- **Materials:** textures mixed with noise textures and position values
- **Camera:** his own vacation footage set as the camera background at low opacity, with the camera movement matched to it; the scene split into foreground, midground and background
- **Reference:** his own footage of Amboseli
- **Post:** DaVinci Resolve Fusion compositing, matched to the footage
- **Time:** about 1.5 months
- **Quote (Yash Jain):** "The biggest lesson I took away was to stop chasing perfection."

## S14. Japan old alley — Joe Siu

- **URL:** https://blenderartists.org/t/japan-old-alley/1243293
- **Year:** 2020 (25 Jul 2020)
- **Contest / feature:** Blender Artists featured row
- **Photoreal aim:** — (based on a real Kyoto alley; commenters praise the realism)
- **Blender version:** 2.83
- **Engine / settings:** Cycles, **64 samples**, Intel denoiser. Resolution, time, hardware: —
- **Assets:** everything except the plants modelled in Blender; textures from cc0textures.com and textures.com plus custom Photoshop textures; Substance Painter for large objects. Plant source: —
- **Scattering:** —
- **Lighting:** sun at strength about 50 at noon, set "by eye". A Blackbody node on every light: sun about 5200 K at noon and 2250 K at sunrise; signs 6500 K; lamps about 2500 K. Exposure kept fixed while light strengths were adjusted.
- **Materials:** PBR materials chosen by comparing against reference photos; roughness tuned with ColorRamp or Math nodes; procedural yellow walls; separate puddle and wall shaders
- **Camera:** the Photographer add-on
- **Reference:** Google Maps view of the Kyoto alley; reference photos for materials
- **Post:** Premiere Pro colour grading
- **Time:** —
- **Quote (Joe Siu):** "For the material look, I usually just look at the reference photos and finds a suitable pbr material for that."

## S15. Scandinavian living room — Kristian Santoso

- **URL:** https://www.blender3darchitect.com/architectural-visualization/scandinavian-style-living-room-with-cycles-profile
- **Year:** 2020 (28 May 2020)
- **Contest / feature:** Blender 3D Architect profile (an interview)
- **Photoreal aim:** — (archviz)
- **Blender version:** —
- **Engine / settings:** Cycles, 600–1000 samples. The Intel and Cycles native denoisers were blended in the compositor with Cryptomatte as the factor. 16–25 min per render on an RTX 2080 Ti (OptiX), i7-6700K and 32 GB RAM.
- **Assets:** his own library of mostly free assets; Chocofur Model Manager; the Floor Generator add-on; walls, windows, tables, frames and lamps modelled by him
- **Scattering:** —
- **Lighting:** HDRI plus area lights used as **portals**; Filmic, Very High Contrast
- **Materials:** — ("the hard part" was adding materials to every asset)
- **Camera:** tried fSpy for camera matching; the Photographer add-on
- **Reference:** a reference photo as the starting point for the layout; an Angelo Ferretti artwork for modelling
- **Post:** the compositor denoiser blend
- **Time:** about 10 h for the first pass plus about 16 h of improvements, over roughly three days
- **Quote (Kristian Santoso):** "I prefer using HDRI because it resembles real-world lighting."

## S16. Bathroom — Dhananjay Sharma

- **URL:** https://www.blendernation.com/2020/11/16/behind-the-scenes-bathroom/
- **Year:** 2020 (16 Nov 2020)
- **Contest / feature:** BlenderNation "Behind the Scenes" (first-person text under an editor's byline)
- **Photoreal aim:** — (archviz)
- **Blender version:** 2.81
- **Engine / settings:** Cycles, GPU, 1000 samples, denoised. Hardware: an NVIDIA "GTX 2080" (as published) and a Ryzen Threadripper.
- **Assets:** plants, towel, bottles, shower and WC accessories from 3dmili (made for 3ds Max, converted via FBX); window from the Archipack add-on; structure, bricks, floor, cabinet, mirror, door and wall light hand-modelled; textures from textures.com
- **Scattering:** —
- **Lighting:** HDRI from HDRI Haven, plus a plane light used as a **light portal** on the windows
- **Materials:** glass shader rebuilt after transmission alone blocked the light; towel given a flat colour plus bump
- **Camera:** angle matched to a single reference image
- **Reference:** one reference image
- **Post:** denoised beauty and wire-colour passes
- **Time:** —
- **Quote (Dhananjay Sharma):** "the glass was not letting light through itself." (a problem he hit, not advice)

## S17. Mountain environments — Jonathan Lampel

- **URL:** https://80.lv/articles/mountain-environments-with-blender
- **Year:** 2017 (80.lv interview, 12 Apr 2017)
- **Contest / feature:** — (80.lv editorial interview)
- **Photoreal aim:** —
- **Blender version:** —
- **Engine / settings:** Cycles (named for the procedural mountain shader). Settings: —
- **Assets:** a procedural mountain, not from a height map (he would use satellite or scan height maps next time); pines from Blender's built-in tree generator; background trees simplified using Zacharias Reinhardt's fake-forest technique
- **Scattering:** a sparse tree's branches instanced 4–5 times at random rotations
- **Lighting:** —
- **Materials:** procedural snow on upward-facing faces, removed from sharp peaks using Pointiness; snow, rock and grass separated by height with noise softening the transitions; noise-based displacement
- **Camera / composition:** foreground, middle ground and background layers to convey depth
- **Reference / Post / Time:** —
- **Quotes (Jonathan Lampel):** "Nature scenes are notorious for looking flat if the lighting and composition are not focused on" / "there needs to be layers of detail"

---

## Tally (N = 17 kept sources)

A count means the source *states* the technique. An absence means it was not mentioned, not that it was not used. Every row has the same denominator, so rows can be compared.

### Render

| Technique | Count | Sources |
|---|---|---|
| Engine named: Cycles | 7 | S1, S5, S7, S14, S15, S16, S17 |
| Engine named: EEVEE | 1 | S11 |
| Engine not named anywhere | 9 | S2, S3, S4, S6, S8, S9, S10, S12, S13 |
| Sample count stated | 8 | S4 (max 2600), S5 (512), S7 (650), S9 (1000, test), S12 (500), S14 (64), S15 (600–1000), S16 (1000) |
| Denoiser used | 4 | S5 (OIDN), S14 (Intel), S15 (Intel + native, blended), S16 |
| Denoising tried and rejected | 2 | S7 (NLM, OptiX looked faded), S4 (per-object denoise dropped) |
| Hardware stated | 6 | S3, S5, S6 (castle), S10 (render farm), S15, S16 |
| Filmic view transform stated | 2 | S6, S15 |

### Assets

| Technique | Count | Sources |
|---|---|---|
| Hero elements modelled or sculpted by the artist | 13 (+4 partial) | S1, S4, S5, S6, S7, S9, S10, S11, S12, S14, S15, S16, S17; partial: S2 (ivy leaf only), S3 (snow sculpt), S8, S13 (terrain sculpt) |
| Third-party models or packs other than Megascans (Sketchfab, CGTrader, Chocofur, 3dmili, Maxtree, vegetation packs, marketplace) | 8 | S1, S2, S5, S8, S9, S13, S15, S16 |
| Megascans / Quixel | 7 | S1, S5, S6, S9, S10, S11, S12 |
| Poly Haven / HDRI Haven (all for HDRIs) | 4 | S2 (uncertain), S3, S9, S16 |
| Textures.com | 4 | S5, S8, S14, S16 |
| ambientCG / cc0textures | 2 | S8 (HDRI), S14 (textures) |
| BlenderKit | 1 | S3 |
| Own photogrammetry or 3D scans | 2 | S1, S4 |
| Third-party scan as the main asset | 1 | S2 |

### Scattering and vegetation

| Technique | Count | Sources |
|---|---|---|
| Density painted with weight or vertex groups | 4 | S4, S6, S9, S10 |
| Explicit hand placement | 4 | S5 (everything), S6 (Manual Scatter), S9, S10 |
| Geo-Scatter / Scatter5 | 3 | S6, S8, S9 |
| botaniq | 3 | S5, S8, S13 |
| Particle systems | 3 | S4, S9, S10 |
| Graswald | 2 | S9, S10 |
| The Grove 3D | 2 | S1, S2 |
| Maxtree | 2 | S2, S9 |
| Ivy generator | 2 | S1 (Thomas Luft), S2 (Blenderesse, geometry nodes) |
| Geometry nodes for scatter or generation | 2 | S2, S12 |
| Card or alpha trees | 2 | S7 (Skin modifier baked to cards), S8 (Alpha Trees) |
| SpeedTree | 1 | S6 |

### Lighting and atmosphere

| Technique | Count | Sources |
|---|---|---|
| HDRI | 11 | S2 (uncertain), S3, S4, S5, S6, S7, S8, S9, S10, S15, S16 |
| Sun: a sun lamp, a boosted HDRI sun, or a spot standing in for the sun | 7 | S7, S8, S14 (lamps); S6, S9 (HDRI sun boosted with EasyHDRI); S3 (spot); S10 (uncertain) |
| Fog, haze or atmosphere by any method | 6 | S3, S6, S7, S8, S10, S12 |
| Volume shader in the render (cube or volume scatter) | 3 | S6, S8, S10 |
| Fog by other means (emission atmosphere, baked sim textures, fog cards, Photoshop, Z-depth pass) | 4 | S7, S8, S3, S10 |
| Light portals at windows | 3 | S4, S15, S16 (all interiors) |
| Area light as a main or fill source | 2 | S3, S11 |
| Sky texture or atmosphere add-on (Nishita, Physical Starlight and Atmosphere) | 2 | S1, S12 |
| Blackbody colour temperature on lights | 2 | S4, S14 |
| Off-screen shadow casters (gobo plane, row of trees) | 2 | S6, S10 |
| Sun placed from a computed real solar position | 1 | S7 |

### Materials

| Technique | Count | Sources |
|---|---|---|
| Two or more materials blended with noise, masks or vertex paint | 10 | S2, S5, S7, S8, S9, S10, S11, S12, S13, S17 |
| Weathering or imperfection layers (dirt, dust, fingerprints, leaks, rust, moss) | 6 | S2, S4, S5, S7, S9, S11 |
| Procedural shader for a main surface | 5 | S1, S7, S11, S14, S17 |
| Displacement (true, adaptive or micro) | 4 | S3, S6, S10, S17 |
| Texture resolution deliberately kept low | 3 | S3, S6, S7 |
| High-resolution textures stated | 2 | S4, S9 (AI-upscaled) |
| Decals | 2 | S5, S11 |
| Vertex painting | 2 | S10, S11 |
| Triplanar or box projection | 2 | S5, S11 |
| Substance Painter or Designer | 2 | S7, S14 |
| Displacement replaced by scattered small debris | 1 | S6 |

### Camera

| Technique | Count | Sources |
|---|---|---|
| Composition discussed (layering, leading lines, framing) | 4 | S3, S10, S13, S17 |
| Camera matched to a reference photo or footage | 4 | S5, S13, S15 (fSpy), S16 |
| Camera or photography add-ons and tools (Photographer, CAM-FX, VirtuCamera) | 4 | S4, S9, S14, S15 |
| Animated camera | 3 | S4, S6, S13 |
| Depth of field stated as used | 1 | S4 (S9 uncertain) |
| Focal length stated | 1 | S10 (24 mm APS-C) |
| Motion blur | 1 | S4 |

### Reference

| Technique | Count | Sources |
|---|---|---|
| Photographic real-world reference (photos, footage, maps, the real place) | 14 | S1, S3, S4, S5, S6, S7, S8, S9, S11, S12, S13, S14, S15, S16 |
| Built from one specific photo or real place | 10 | S1, S4, S5, S7, S8, S12, S13, S14, S15, S16 |
| Paintings or illustration as reference | 3 | S6, S8, S10 |
| Explicitly no reference | 1 | S2 |

### Post-processing

| Technique | Count | Sources |
|---|---|---|
| External grading or compositing app (Photoshop, After Effects, Resolve, Premiere) | 9 (+1 unnamed) | S3, S5, S6, S8, S9, S10, S12, S13, S14; S2 unnamed |
| Grain | 4 | S5, S6, S9, S12 |
| Glow or bloom | 4 | S6, S9, S11, S12 |
| 2D elements added in post (sky, fog, light rays, figure, smoke) | 4 | S3, S5, S8, S10 |
| Chromatic aberration | 3 | S5, S6, S9 (S4 chose not to add "lots of" it) |
| Render passes used in compositing (EXR layers, Z-depth, wire colour) | 3 | S6, S10, S16 |
| Blender compositor in the final image | 2 | S7, S15 |
| Vignette | 2 | S5, S9 |
| Lens distortion | 0 | (S9's CAM-FX section shows examples; final use uncertain) |

### Time spent (where stated)

8 sources state time: one day (S12), about 2 days (S2), about 26 h over three days (S15), about two weeks (S11), about 70 h (S3), a 150 h floor alone (S1), about 1.5 months (S13), about two months part-time (S4).

### Recurring realism advice (paraphrased themes, each tied to the quotes above)

- **Study the real thing.** S5 ("studying how things look in real life"), S6 (trees from the specific biome), S4 (referenced the real room by eye), S14 (materials picked against reference photos).
- **Break perfection.** S4 (fingerprints where a hand would hold the glass), S9 (grain "to break the smooth render"), S12 (pods not "perfectly flat"), S11 (decals tell "a story of surface decay").
- **Composition and layered depth.** S17 ("layers of detail"), S13 (foreground/midground/background), S10 (check the values in black and white).
- **Spend detail where the camera looks.** S6 (4K only for close-ups), S3 ("Is this texture resolution necessary?"), S7 (low-resolution maps that still look "visually rich").

---

## Read but too thin to count

Each is a real Blender piece, but the source states only one to three techniques, or has no artist account. They are listed so the facts are not lost.

| Piece / artist | URL | Contest / feature | What it states |
|---|---|---|---|
| Forest — Shai Nefer | https://blenderartists.org/t/forest/1285466 | BOBA 2021 Landscapes 2nd; featured | god rays from a Principled Volume in a cube over the whole scene; density and anisotropy tuned |
| Driving Hills at Sunset — Radu Mitroi | https://blenderartists.org/t/driving-hills-at-sunset/1332271 | BOBA 2021 Landscapes 3rd; featured | 3–4 Megascans cliffs duplicated; botaniq; particle-system foliage; trees hand-placed for composition; Quixel Mixer; a BlenderKit car; two days |
| Traces of the past – Old alley — Kim (oo_1942) | https://blenderartists.org/t/traces-of-the-past-old-alley/1340482 | BOBA 2021 Exterior 4th; featured | Blender 3.0, Cycles X |
| Old Middle Eastern Neighborhood — Fadhel | https://blenderartists.org/t/old-middle-eastern-neighborhood/1323411 | BOBA 2021 Exterior 2nd; featured | Photoshop tweaks on the final render |
| Hazy Rainforest — GurjasStudios (Jaspreet Singh; possibly the S8 artist, uncertain) | https://blenderartists.org/t/hazy-rainforest/1474395 | BOBA 2023 Plants 3rd | packs (botaniq, vegetation, forestation, graswald); Geo-Scatter; Photoshop; 6 h over 2 days |
| Abandoned house — Heber Villalta | https://blenderartists.org/t/abandoned-house/1480813 | BlenderNation "Best of Blender Artists 2023-35" | Blender 3.6, Cycles; botaniq, Baga Ivy Generator, Geo-Scatter, Quixel Bridge |
| Three environments — Hrishikesh Bedre | https://80.lv/articles/highly-realistic-3d-environments-set-up-in-blender | 80.lv news | Blender 3.5/3.6; GTX 1650; botaniq, Graswald, Gscatter; NoEmotion HDRI; displaced ground; reference images |
| Antique — George Turmanidze | https://80.lv/articles/step-into-this-gorgeous-blender-made-interior-inspired-by-classical-architecture | 80.lv news (paraphrase only) | Blender 4.3, Cycles; RTX 3090, about 8 h render; "all the models used are interior 3D scans"; motion blur; two weeks |
| Soheil Mahmoudi interview | https://www.blendkit.com/articles/interviewwithsoheilmahmoudi/ | BlenderKit (now "Blendkit") interview | real places recreated from photos; about 95% hand-modelled; SpeedTree; Substance Painter; adds grass, rocks and trash "to show the presence of humans" |
| Short forest scenes — Dimitris Sakkas | https://80.lv/articles/studying-short-forest-scenes-with-dimitris-sakkas | 80.lv interview | sun plus a high-contrast HDRI; AO, Shadow and Mist passes blended in Multiply/Overlay; fog and smoke stock footage; a dirt texture driving roughness. Photoreal aim not stated. |
| God's Valley castle — Maarten Nauta | https://80.lv/articles/a-large-scale-mountain-castle-environment-made-in-blender | 80.lv news | merged into S6 |
| Swamp biome — Jesse Miettinen | https://80.lv/articles/finland-inspired-procedural-swamp-biome-made-with-blender/ | 80.lv news | custom geometry-nodes biome that also shapes the ground; Geo-Scatter assets; Camera Shakify |

## Excluded

| Piece / page | URL | Reason |
|---|---|---|
| Last of Us fan art — Anton Syrvachev | https://80.lv/articles/working-on-the-last-of-us-fan-art-environment/ | assembled, lit and rendered in Unreal Engine (Blender for modelling only) |
| Woodland — Chris Lambert | https://80.lv/articles/001agt-003qxl-crafting-a-natural-scene-with-blender-quixel | final scene built and rendered in UE4 |
| Back alleys of Vietnam — Lenz Monath | https://80.lv/articles/creating-an-environment-to-capture-the-atmosphere-of-the-back-alleys-of-vietnam | lit and rendered in Unreal Engine 5 |
| Photoreal scene recreated from a photo — Steffen Hampel | https://80.lv/articles/003qxl-004adk-making-a-photorealistic-3d-scene-with-megascans | Maya and V-Ray; Blender not mentioned |
| Photoreal forest — William Fiorentini | https://80.lv/articles/setting-up-a-photorealistic-forest-scene-with-megascans | V-Ray; Blender not mentioned |
| Evermotion Challenge 2021 1st — Shabeer MV | https://www.foxrenderfarm.com/jp/news/interview-with-shabeer-mv-a-versatile-3d-professional-who-won-the-1st-award-in-the-evermotion-challenge | 3ds Max and Corona |
| Lost Temple — Andrii Stadnyk | https://80.lv/articles/lost-temple-creating-a-scene-with-blender-and-megascans-assets/ | final render in OctaneRender, then Photoshop paint-over toward a concept-art look |
| Pwnisher *Moving Meditations* entry — Igor Witkowski | https://80.lv/articles/fuelling-a-pwnisher-contest-submission-with-3d-modeling-and-photogrammetry | stylized cyberpunk, not described as realistic |
| Sci-fi shot — Karl Poyzer | https://80.lv/articles/breakdown-creating-realistic-sci-fi-shot-fully-in-blender | a spaceship shot, not an environment of the requested kind |
| Blitter interview | https://80.lv/articles/blitter-dicsusses-creating-those-photoreal-renders-in-blender/ | photoreal character portraits, not environments |
| Zacharias Reinhardt interview | https://80.lv/articles/reinventing-reality-with-blender | vehicle and robot concepts |
| The Greenhouse — Laura Ganis (BOBA 2021 Exterior grand winner) | https://blenderartists.org/t/the-greenhouse/1326130 | painterly look from 16 samples plus the AI denoiser |
| Through the Pines — ASMU (BOBA 2022 Landscapes 2nd) | https://blenderartists.org/t/through-the-pines-by-asmu/1356306 | painterly Topaz "Impression" filter |
| Millbeck Farm — Lazlo Woodbine (BOBA 2022 Landscapes 4th) | https://blenderartists.org/t/millbeck-farm-the-lake-district/1381076 | the artist describes "degrees of painterly-ness". It has a notable technique for another guide: real 1 m Environment Agency height data via QGIS and Gaea. |
| Five Corners — Anton Syrvachev | https://80.lv/articles/beautiful-post-apocalyptic-city-environment-made-in-blender | news post; only "Blender, Megascans, Cycles" |
| Desolate mine — Shamanishka | https://80.lv/articles/this-realistic-desolate-mine-scene-was-set-up-in-blender | news post; the article says the creator shared little |
| Vintage interior — Vladimir Leleiva | https://80.lv/articles/photorealistic-vintage-style-interior-created-with-blender-substance-3d | news post; no artist account |
| Abandoned toilet — DeaVenom | https://80.lv/articles/highly-realistic-abandoned-toilet-scene-made-with-blender | news post; no process |
| Ze Forest — Piotr Krynski | https://80.lv/articles/a-stunning-forest-scene-made-in-blender | news post; asset packs only |
| Subway car — Taira Kakeru | https://80.lv/articles/this-photorealistic-subway-car-is-actually-a-3d-render | news post; no process |
| Rainy Japanese streets — Difffuse Studio | https://80.lv/articles/rainy-streets-of-a-japanese-city-imagined-with-blender-cycles | product promotion; no artist |
| 30-million-tri scene — Blendist3D | https://80.lv/articles/see-how-this-blender-scene-with-30-million-tris-was-made-from-scratch | news post; photoreal aim not stated |
| The Art of Carl Roe | https://www.blendernation.com/2018/08/18/the-art-of-carl-roe/ | gallery; no process text |
| Forest in Fog — Adrian Kulawik | https://www.blendernation.com/2023/05/05/making-of-forest-in-fog/ | video only; no written breakdown |
| GarageFarm interior contest — Robert Paprotny | https://garagefarm.net/interview-with-blender-contest-winner-robert-paprotny | no technique stated; photoreal not stated |
| Archviz interview 2019 — George Turmanidze; Blendkit interviews with Alejandro Zorrilla and Paweł Wałasiewicz | https://80.lv/articles/a-look-into-archviz-in-blender ; https://www.blendkit.com/articles/interview_with_alejandro_zorrilla/ ; https://www.blendkit.com/articles/interview_with_paweł_wałasiewicz/ | no specific piece broken down (Wałasiewicz is about HDRI capture) |

## Tried and could not read, or found but not opened

- **BlenderNation "Behind the Scenes" listing pages** (`/behind-the-scenes/`, `/page/2/`, `/page/3/`): the article list is loaded by script, and the fetched pages had no listings. The category RSS feed returned only the latest 10 posts (2026), none clearly a photoreal environment. Posts were found by search instead, so the series is under-sampled.
- **blenderkit.com/articles/…** pages redirect to **blendkit.com**. I read them after following the redirect, which the server issued itself. Noted in case links need updating.
- **No Blender Guru / Poliigon competition write-up with process detail was found.** The 2011 underwater competition post on BlenderNation is an announcement (search snippet only, not opened).
- **The Rookies Summer Photorealism Blender Contest (2019):** only a headline was found, with no winners page.
- **Found in search, not opened (time):** BlenderNation Behind the Scenes "White Interior" (2019), "Interior Kitchen" (2020), "Bed and Bathroom" (2021), "Atmospheric scene in B3.0 CyclesX" (2021); the BOBA 2023 placed threads (Coming Home; Small island beneath an overcast sky; Parisian Apartment; Recreating St Paul's cathedral; The Shambles); Blender Artists "Travelers from an antique land"; BlenderNation "Infinite Journeys Challenge Process Breakdown" (Brian Resco, 2022); 80.lv "Japanese street under fog" (Malek Mansour) and "Medieval interior in ruins" (Adam Knight), whose software was unclear from snippets; FGT3D "The Ruins" challenge winners.
- **Pwnisher challenges:** the placed breakdowns found were stylized (Witkowski), mixed with Unreal, or Cinema 4D/Redshift (per search snippets). No photoreal Blender environment winner breakdown was found.
