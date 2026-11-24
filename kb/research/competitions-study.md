# Blender competitions and showcase work, 2014–2026: techniques, methods and tricks for an agent that works through Python

_Checked after collection against the pages themselves (2026-11-23): A-01 (6x samples; constant seed; tripling the
samples did little), A-06 (median render time around 3 minutes), C-02 (the vegetation-flicker quote; 750 samples),
B-08 (32-bit ACES), C-12 (~36 hours for 220 frames; the self-improvement quote) were found word for word. One quote in
A-01 was a paraphrase inside quotation marks and is corrected to the page's words. Spot-check the rest before citing._

_Compiled 2026-11-23. 49 sources counted: part A 15, part B 15, part C 20 (Flow, covered by A-07 and B-06, counts once). Each technique is labelled [Setting], [Procedure] or [Judgement]; "not stated" means the source did not say it._

## Method notes

**How the work was split.** Three readers worked in parallel, each with the same extraction rules and the same entry format. Part A covers Blender Studio's open movies and other Blender-made films (Flow, Next Gen). Part B covers Suzanne Award winners, Pwnisher challenge entries, and character breakdowns. Part C covers still-image and short-animation contests and featured work: Best of Blender Artists (BoBA), CG Boost, Blender Guru, GarageFarm and Fox Renderfarm contest interviews, BlenderNation Behind the Scenes, 80.lv, an ArtStation challenge entry, and one Ronen Bekerman making-of. Entry IDs carry the part letter (A-, B-, C-). Each part's own method notes follow its heading below.

**What was searched (part C).** WebSearch in standard mode throughout; extended mode was never needed, because the limit was depth of the pages, not the search. Queries were generic: "Best of Blender Artists winners", "CG Boost challenge winners", "Blender Guru competition results", "Poliigon render competition", "blendernation behind the scenes" with year and subject terms, "80.lv Blender breakdown" with subject terms (car, food, interior, sci-fi, AgX), "foxrenderfarm interview Blender winner", "ronenbekerman making of Blender Cycles", "Evermotion making of Blender", "Hum3D car render challenge winners". The BoBA winners threads for 2021, 2023 and 2024 were read in full, and ten winners' entry threads were opened from them. The BlenderNation Behind the Scenes archive was sampled at listing pages 1, 40, 70, 88 and 95 (2016–2026).

**How sources were judged.** A source was kept only if the page itself (not a video) states at least one setting, procedure or judgement with enough detail to act on. Artist-written or interview pages were preferred over news rewrites. Pages that only point to a video were excluded however famous the work. Four CG Boost / Blender Guru pages are kept for their jury commentary, which is the only direct evidence on what judges reward. One entry (C-20) groups ten thin BoBA winner threads, because the thinness is itself the finding. Every "not stated" means the page did not say it. Where I inferred (for example, "engine not named but sampling implies Cycles"), the entry says so.

**What the sources could not give.** Most pages state procedures and judgements, few state numbers. Colour management, sample counts and bounce settings are the most often missing. Video breakdowns (most Pwnisher entries, most recent BlenderNation posts, Ian Hubert's) could not be used. blender.org, Evermotion, CG Cookie's blog and 3dmodels.org (Hum3D) refused automated fetches (HTTP 403), which removed the blender.org user stories, including the primary Flow interview.

**Counting.** Each technique line carries tags. The tally in the analysis counts distinct sources per technique, never mentions; one source that states a technique three times counts once. Tags were grouped by hand into techniques where readers used different words for the same thing.

### Method notes, part A (open movies and films)

- **Queries run (WebSearch, standard mode only; extended was not needed because the limit was access, not search depth):** Charge render settings / render times / production log; Sprite Fright lighting, rendering, denoising; Flow + Gints Zilbalodis + EEVEE interview; "Making Flow" blender.org; Blender Studio pipeline docs (shot builder, render review, lighting overrides, Flamenco); Agent 327 Barbershop Cycles render times; Spring 2019 rendering / lighting / BCON19 talk; Coffee Run EEVEE lighting; Wing It! EEVEE rendering; Singularity 2025 rendering; Singularity / Gold painterly brushstrokes; Cosmos Laundromat / Gooseberry render farm and render times; Next Gen Tangent Cycles pipeline / Embree; Hero Grease Pencil workflow; Caminandes 3 render settings / fur; Sprite Fright rigging / pose library / CloudRig.
- **How sources were judged:** kept only pages I could read in full with WebFetch, preferring the production's own text (studio.blender.org blog posts, Blender Studio pipeline docs, gooseberry.blender.org posts, a developer mailing-list post). One feature-press interview (VFX Voice, original reporting with direct quotes from the Flow crew) was kept. One 80.lv page was kept as a flagged *secondary* summary, because the primary blender.org Flow interview returned HTTP 403 and it is the only readable carrier of the render-time and file-management facts.
- **Access limits that shaped the set:** www.blender.org returned 403 for every page tried; web.archive.org could not be fetched; several of the deepest Blender Studio posts (Charge FX, Charge lens-dust compositing, parts of Wing It! shading) are login-walled; production logs are mostly titles over subscription-walled video. Nothing here comes from watching video.
- **Where one entry lists several URLs**, they are pages from the same producer on the same film or the same documentation set; each technique names its page when it matters.
- **Count:** 15 kept. Four (A-06 Charge, A-13 Singularity, A-14 Cosmos Laundromat, A-15 Next Gen) are thin-to-medium and are kept only because the brief names those films and they carry concrete numbers or methods found nowhere else; their depth notes say so.
- "not stated" means the source did not say it. Where I inferred something, it is marked as such.

### Method notes, part B (Suzanne Awards, Pwnisher, characters)

- Queries run (WebSearch, standard mode unless noted): "Suzanne Awards winners Blender Conference best animation short film list"; "blendernation Suzanne Awards winners 2023" (restricted to blendernation.com / blender.org); "Suzanne Awards 2019 / 2025 winners"; "Pwnisher challenge winner Blender breakdown 80.lv"; "Pwnisher Moving Meditations Blender breakdown"; "Pwnisher Infinite Journeys Blender entry breakdown"; "80.lv Pwnisher Endless Engines Blender breakdown geometry nodes"; "Toni Mortero Mundo Canibal Blender 2D look pipeline"; "Milo Chiavarino Singularity short film Blender breakdown"; "The Box Dušan Kastelic Blender making of"; "Remove Hind Legs Before Consumption Blender making of"; "Samurai Blue Afterimage Goo Engine making of"; "La Vida de una Piñata Blender making of"; "Katsu Cats Blender"; "Suzanne Awards 2015 / 2017 / 2020 / 2022 winners"; "blendernation Behind the Scenes pwnisher challenge animation" (blendernation.com only); "foxrenderfarm interview Pwnisher challenge top winner Blender"; "Pwnisher Kinetic Rush parkour Blender breakdown cloth"; "80.lv Blender realistic character hair curves skin breakdown"; "80.lv Blender character animation Auto-Rig Pro OR Rigify breakdown"; "Blender short film breakdown Cycles animation flicker denoiser"; "pwnisher challenge entry Blender flicker denoising". Extended mode was not needed.
- Winners list: the conference.blender.org `/<year>/festival/finals/` pages mark the winner of each category with an `is-winner` CSS class; I read the raw HTML with curl to see that class (WebFetch's text conversion drops it). Entry detail pages (`/<year>/festival/entries/<id>/`) carry the makers' own synopsis, "Making-of" field and credits. For 2014, 2016, 2018 and 2019 I used BlenderNation / 3DVF / the 2019 festival page.
- Reading: every kept page was read with WebFetch (asked for exact settings, numbers, ordered steps, verbatim quotes); I then pulled the raw HTML with curl for every kept page (80.lv, BlenderNation, Blender Artists, Fox Renderfarm) and grepped the article text to check that quotes are verbatim and to look for engine / version / denoise / motion-blur words the extraction might have missed; the 80.lv animation page in B-06 (director quotes) was checked only through WebFetch. Where a field says "not stated" I grepped for it and found nothing.
- Judging: kept only pages where the artist speaks in their own words (interview, own post, own entry text) and gives at least some concrete method. Pages that are a video embed with two lines of text, or a news rewrite listing winners, are in "Excluded". Placement is recorded as the page gives it.
- Scope: Blender Studio open movies, still-image environment/product/interior contests and Best of Blender Artists (BoBA) entries are covered by other researchers and skipped here.
- What the search found, before the sources: Suzanne Award winners almost never publish a written making-of. For 2014–2025 the text that exists is the entry page's one-paragraph "Making-of" field, a talk abstract, or a forum post listing tools; the real breakdowns are videos or BCON talks I could not read as text. So only one Suzanne winner (B-09, 2022 Best Short) is kept as a full source, one finalist (B-04) is kept through an earlier teaser write-up, and the rest are summarised in the winners table at the end. The depth in this part comes from Pwnisher placed entries (B-01–B-03, B-07, B-08, B-10–B-13) and character work (B-05, B-06, B-14, B-15).
- Year spread of kept sources: 2019 (B-04), 2022 (B-02, B-07, B-09), 2024 (B-05, B-08, B-10, B-12, B-13, B-15), 2025 (B-01, B-03, B-06), 2026 (B-11, B-14). Nothing earlier than 2019 had enough text.

## Sources — part A: Blender Studio open movies and other Blender-made films

### A-01 · Denoising Sprite Fright
- **URL:** https://studio.blender.org/blog/denoising-sprite-fright
- **Artist/studio:** Simon Thommes, 3D Artist, Blender Studio
- **Year:** 2021 (post dated 26 Nov 2021)
- **Contest & placement:** none — open movie / production
- **Blender version:** not stated
- **Engine & render settings:** Cycles; Open Image Denoise (OIDN) used from early in production "to get noise-free frames with a relatively low sample count"; constant (non-animated) seed. Final sample count, noise threshold and denoiser passes not stated. Test renders compared at 800 and 5000 samples.
- **Render time & hardware:** not stated, beyond "6x samples = 6x render time, still not noise-free"
- **Techniques:**
  - [Setting] Seed held constant across frames, so the noise pattern is fixed on screen and the denoiser reads consecutive frames consistently — principle: holds only while the camera is static; when the camera moves, the fixed pattern slides across the image {tags: cycles, oidn, seed, flicker, temporal-denoise}
  - [Judgement] More samples rejected as the fix: tripling samples did little, and 6x samples (6x time) was still not noise-free — reason: at low samples the denoiser fills in missing information with guesses that differ from frame to frame, which shows as flicker; brute force does not remove it at acceptable cost {tags: cycles, oidn, flicker, render-time}
  - [Setting] Temporal denoising not available — the author notes neither OIDN nor NVIDIA's denoiser had a temporal mode at the time — principle: not stated beyond the fact {tags: temporal-denoise, oidn, optix-denoise}
  - [Procedure] Super-resolution trial: render at double the pixel count with half the samples (same cost per frame), denoise, downscale by an integer ratio with bilinear or bicubic filtering (author unsure which) (steps stated in outline) — principle: extra pixels give the denoiser more normal and detail information; helped fine detail (bark, mushrooms) but was not temporally stable where transparency or volume passes were involved, and did not fix jitter on moving moss {tags: oidn, flicker, resolution}
  - [Procedure] Border rendering of the noisy regions only, at higher samples (steps not stated) {tags: cycles, render-time}
  - [Procedure] Proxy projection trial: hand-built proxy meshes approximating the noisy background; one clean frame projected onto them and rendered over the sequence (steps stated in outline) — principle: reusing one clean frame removes frame-to-frame variation; rejected as cumbersome, and it loses parallax {tags: flicker, projection, compositor}
  - [Procedure] Final method, Z-depth projection: 1. output the depth pass and the camera data (position, rotation, focal length, aspect ratio); 2. reconstruct each pixel's 3D position and build a mesh dynamically with Geometry Nodes; 3. project one clean, denoised frame (lighting baked in) onto that mesh; 4. render the projection from the moving shot camera and composite it with the original shot; 5. mask back in the lighting that is not baked (moving character shadows, occlusion) — those areas lose the denoising benefit (steps stated) — principle: needs a fully static background; fails with view-dependent reflections, moving shadows or moving lights; one viewpoint leaves gaps, so the shot needs a well-chosen projection viewpoint and limited camera movement (multiple projection cameras suggested as a fix) {tags: geometry-nodes, compositor, flicker, projection, cycles}
  - [Judgement] Avoided moving foliage in day shots, except the opening and closing shots — reason: the projection method requires static backgrounds {tags: flicker, layout}
  - Further ideas listed by the author, not used: average colours across all frames mapped into 3D; solve a 3D model from the whole sequence; mask characters and shadows procedurally from pixel deviation; reconstruct occluded layers by skipping early camera-ray bounces {tags: flicker}
- **Quotes:** "It is only possible to utilize this method with fully static backgrounds." — Simon Thommes
- **Depth note:** deep; the most detailed public account found of frame-to-frame noise and flicker on a Blender Studio film. It gives no final sample count or noise threshold.

### A-02 · Sprite Fright Master Class: Lighting & Rendering
- **URL:** https://studio.blender.org/blog/Sprite-Fright-Master-Class-Lighting-Rendering/ (companion: https://studio.blender.org/blog/lighting-big-picture-beautiful-pictures)
- **Artist/studio:** Andy Goralczyk (Art Director), Blender Studio; companion post is an interview with him by Christian Bunyan
- **Year:** 2021 (1 Mar 2021; companion 3 May 2021)
- **Contest & placement:** none — open movie / production (lighting of one key image, which became a 3D World cover)
- **Blender version:** not stated
- **Engine & render settings:** Cycles. Light Paths: Max Bounces 3, Transparency 32; Clamping Direct 0.00, Indirect 10.00; Reflective and Refractive Caustics off; Filter Glossy 1.00. Sampling: Render 200, Viewport 100, Start Sample 1. Denoising: OpenImageDenoise for Render and Viewport. Colour management: Filmic view transform.
- **Render time & hardware:** not stated
- **Techniques:**
  - [Setting] Max Bounces 3, Transparency 32, Clamp Indirect 10 (Direct 0), caustics off, Filter Glossy 1.0, 200 render samples — principle: not stated (they are the article's base settings) {tags: cycles, light-paths, clamping, render-settings}
  - [Setting] OpenImageDenoise on the viewport as well as the render — principle: "to get a clearer image while adjusting light" {tags: oidn, viewport}
  - [Setting] Filmic view transform {tags: filmic, colour-management}
  - [Procedure] Lighting workspace: split the viewport, camera view with overlays off, Border Render, viewport shading Rendered (steps stated) {tags: workflow, viewport}
  - [Procedure] Camera-only background swap: World = forest HDRI mixed with a flat dark blue; a Mix Shader driven by Light Path "Is Camera Ray" so the camera sees a stylised background while the HDRI still lights the scene (steps stated) — principle: use an HDRI with no sharp details or recognisable figures; it is there for subtle diffuse and glossy variation {tags: world, hdri, light-path-node}
  - [Procedure] Key sun: lit from the front at an angle, never from the camera position; colour (1.0, 0.5, 0.08), strength 20, angle 8°, Cast Shadow and Multiple Importance on (stated) — principle: 8° and tweaked values chosen because they look better than physically accurate settings {tags: lighting, sun-light}
  - [Procedure] Dappled-shadow blocker: plane subdivided 5 times, delete a random 30% of faces, Subsurf modifier at render level 2; material = black Diffuse mixed with Transparent by Is Camera Ray, so it casts shadow but is invisible to camera and does not bounce light (steps stated) {tags: blockers, lighting, light-path-node}
  - [Procedure] Character lights (all Disk area lights): warm key 0.7 m 55 W, placed about 30–40° off the sun on Z; cool fill 1.4 m 45 W colour (0.10, 0.35, 1.00); rim 0.7 m 43 W from behind; ground-bounce rim 0.7 m 10 W colour (1.0, 0.4, 0.03) angled up from behind the head; face softener 0.1 m 100 mW near the jaw to soften the cheekbone terminator; small-character key 0.05 m 180 mW skin-toned (0.47, 0.30, 0.15) plus a 40 mW purple-blue fill from camera direction; hair accent 0.8 m 45 W light blue above and behind the head with Diffuse ray visibility off, so it only adds specular (steps stated) {tags: lighting, area-light, ray-visibility}
  - [Procedure] Light shafts: cube aligned to the sun, Emission shader in the Volume socket, density from 2D Noise → ColorRamp → Multiply 0.070, light blue, to lift the character off the background (stated) {tags: volumetrics, lighting}
  - [Procedure] Foreground blockers: two planes between the feet and camera, 0.2 m above ground (to avoid overly sharp shadows), to darken corners (stated) {tags: blockers, lighting}
  - [Procedure] Put lights in a "Lights" collection and blockers in a "Blockers" collection, then F12 (stated) {tags: collections, organisation}
  - [Judgement] Darken frame corners with in-scene blockers rather than a post vignette — reason: a post vignette can look fake in the highlights {tags: lighting, blockers, compositor}
  - [Judgement] Light the character and the environment separately — reason: independent control of angles while keeping colours in sync {tags: lighting}
  - [Judgement] Make the face the highest-contrast area; keep the background behind the head lower in contrast; avoid sharp shadows and very dark areas mid-face; keep the terminator and core shadow off the centre of the face — reason: appeal and readability {tags: lighting, composition}
  - [Judgement] Find light values by halving or doubling, then refine in quarters and thirds — reason: not stated beyond speed {tags: lighting, workflow}
  - [Judgement] (companion post) In EEVEE "you have to cut some settings down", so compensate with extra lights, e.g. at the back of the shot or on the floor; fake effects when the on-screen result needs it — reason: EEVEE does not represent bounce light the way Cycles, "a path tracer", does {tags: eevee, lighting}
- **Quotes:** "The lighting should feel motivated by the scenery, but above all it's the emotion that counts." — Andy Goralczyk; "For maximum appeal, avoid sharp shadows and extremely dark parts in the middle of the face." — Andy Goralczyk
- **Depth note:** very deep, with exact values. It is one key frame lit for a magazine cover, so these are the production's still-image settings, not stated per-shot animation settings.

### A-03 · Sprite Fright Workflow: Lighting & Set Dressing
- **URL:** https://studio.blender.org/blog/sprite-fright-workflow-lighting-set-dressing
- **Artist/studio:** Beau Gerbrands (lighter), interviewed by Christian Bunyan, Blender Studio
- **Year:** 2021 (17 Aug 2021)
- **Contest & placement:** none — open movie / production
- **Blender version:** not stated
- **Engine & render settings:** Cycles (per the production). "Samples are increased and EXRs output for compositing" once a shot is approved; values not stated.
- **Render time & hardware:** not stated
- **Techniques:**
  - [Procedure] 1. the art director builds the lighting file with the shotbuilder add-on, which links set, characters and props and adds a lighting collection; 2. the first lighting pass is rendered and sequenced in Kitsu with notes and drawovers, then discussed in a briefing; 3. the lighter refines lights, adds set changes, coordinates shading and layout fixes with the 3D team, and sometimes asks for small animation changes; 4. on approval, raise samples and output EXR for compositing (steps stated, values not stated) {tags: shot-builder, kitsu, linking, exr, lighting}
  - [Procedure] Continuity check: a contact sheet of all shots (studio-built tool) showing light values, consistency and angles per shot; the Kitsu add-on compares versions (steps not stated) — principle: shots in a sequence must match {tags: contact-sheet, continuity, kitsu, review}
  - [Procedure] Shadow caster: add a 3D object and disable its Camera and Diffuse ray visibility (stated) {tags: ray-visibility, blockers, lighting}
  - [Setting] Keep light strengths and distances consistent between shots; name lights; build up from simple setups — principle: continuity and speed {tags: continuity, lighting}
  - [Judgement] Squint and desaturate to judge values; compare renders with render slots (J / Alt+J) — reason: faster value judgement {tags: lighting, review}
- **Quotes:** "Add a 3D object and disable both the camera and diffuse ray visibility checkboxes." — Beau Gerbrands
- **Depth note:** medium; workflow-level, few numbers.

### A-04 · Blender Studio Tools — pipeline documentation (shot assembly, animation, lighting, rigging, Lighting Overrider, CloudRig, Flamenco render, render review, final render) + "One Thing I've Learned: Sprite Fright Rigging Edition"
- **URL:** https://studio.blender.org/pipeline/pipeline-overview/shot-production/shot-assembly ; https://studio.blender.org/tools/pipeline-overview/shot-production/animation ; https://studio.blender.org/tools/pipeline-overview/shot-production/lighting ; https://studio.blender.org/tools/pipeline-overview/rigging ; https://studio.blender.org/tools/addons/lighting_overrider ; https://studio.blender.org/tools/addons/cloudrig/introduction ; https://studio.blender.org/tools/user-guide/project_tools/usage-render-flamenco ; https://studio.blender.org/tools/user-guide/project_tools/usage-render-review ; https://studio.blender.org/tools/user-guide/project_tools/usage-final-render ; https://studio.blender.org/blog/one-thing-ive-learned-sprite-fright-rigging-edition
- **Artist/studio:** Blender Studio (docs, no single author); the blog post is by Christian Bunyan quoting rigger Demeter Dzadik
- **Year:** docs 2023–2025 (the Rendering page is a stub dated 6 Oct 2023); blog 15 Mar 2021
- **Contest & placement:** none — studio pipeline documentation (used from Sprite Fright onward; CloudRig on Coffee Run, Sprite Fright, Wing It! per the studio)
- **Blender version:** not stated
- **Engine & render settings:** the engine "depends on the production's style" and must be chosen in pre-production. Final renders go to OpenEXR with Previews on, through a Flamenco "Simple Blender Render" job. No sample or denoiser values; the Rendering page says its content "is currently being edited/updated".
- **Render time & hardware:** not stated (Flamenco farm)
- **Techniques:**
  - [Procedure] Shot assembly: 1. build Metadata Strips from the previz in the Video Sequence Editor (strip length sets shot in/out); push to Kitsu; 2. author each asset as a collection marked as an asset (Asset Pipeline add-on), saved under `assets/<type>`; 3. cast assets to shots in Kitsu Breakdown; 4. run Set Kitsu Asset (sends file path and collection); 5. save and edit Shot Builder hooks per project (`hooks.py`); 6. File > New > Shot File, pick sequence and shot → saved as `shots/{seq}/{shot}/{shot}.blend`; 7. when the editor retimes a shot, the Kitsu add-on warns and the user pulls the new frame range (steps stated) — principle: "rely on Blender's linking system"; tasks derive from the edit {tags: shot-builder, kitsu, linking, pipeline, vse}
  - [Procedure] Per-shot files: `shot.anim` (rigged assets + linked set; anything going downstream sits in its output collection); `shot.fx` (links anim and lighting); `shot.lighting` (lights, shadow catchers; links anim and fx); compositing file (links anim, fx and lighting, plus a Compositing Node Group used for the final render) (stated) — principle: departments work in parallel on linked data; animator updates reach lighting automatically through the output collection; new helpers or props must be added to that output {tags: linking, library-overrides, shot-files, pipeline}
  - [Procedure] Animation stage: 1. director briefing on performance and acting beats; 2. check the built shot (assets present, framerate, camera) and plan technical setup (e.g. parent constraints for riding a vehicle); 3. blocking pass for quick director feedback; 4. keep rigs and props updated throughout; 5. after approval, polish: inbetweens, secondary motion (earrings, tails, fingers), contact with the environment, no visible intersections; 6. delivery checks: framerate, latest render in Kitsu, linked assets current in the output collection, motion-blur readiness (start and end frames, parent switches) (steps stated) {tags: blocking, animation-workflow, motion-blur, kitsu}
  - [Procedure] Lighting stage: start "as soon as there is a first blocking pass"; needs basic shading on in-frame assets and a colour script, colour key or lighting guidelines; light the key shots of each sequence first; light the establishing or wide shot first and derive close-ups and inserts from it; match intensity, colour and style with adjacent shots, and keep light direction consistent where spatial continuity matters (use a top-down sketch or a light-direction chart); before submitting, switch quality settings from preview to final (stated) — principle: continuity across a sequence {tags: lighting, continuity, light-rig, blocking}
  - [Setting] Reduce light types to four — key, key-soft, fill, rim — each with a per-scene RGB value stored in a library file; for Cycles the values can live in a linked node group so updates propagate on the next render — principle: one source of truth for sequence lighting values {tags: light-rig, linking, node-group, continuity}
  - [Procedure] Changing linked data in the lighting file: visibility by view-layer exclusion (render and viewport visibility are read from the source file); recent productions prefer Geometry Nodes rig switches; Python text blocks (names ending `.py`) set linked values and must be re-run; the Lighting Overrider add-on stores overrides as JSON (`<sequence>.settings.json` applied first, then `<shot>.settings.json`) and re-applies them on file load; hover a property and press O to add an RNA override (stated) — principle: overrides on library data must be re-applied after every load {tags: library-overrides, lighting-overrider, python, linking}
  - [Setting] Lighting Overrider categories: variable settings (a `VAR-settings` node group in `variables.blend`), motion blur settings (disable deformation motion blur on objects in a named collection, cameras excluded), shader settings (custom properties on `HLP-` objects), rig settings (custom properties on a `Properties_Character_<name>` bone in `RIG-` armatures), RNA overrides — principle: not stated {tags: lighting-overrider, motion-blur, library-overrides}
  - [Judgement] Animating a linked value is hard: either a Python-driven driver on a dummy object, or animate it locally in the anim file after telling that shot's animator — reason: both are awkward (quoted below) {tags: library-overrides, animation-workflow}
  - [Procedure] Motion-blur debugging: constraint switches (e.g. a hand picking up a prop) produce long blur streaks; set those switch keys to Constant interpolation (may cause other issues); enable Subframe in the Timeline Playback popover to scrub between frames and see what the renderer samples (stated; "not a universal fix") {tags: motion-blur, constraints, interpolation}
  - [Judgement] Eye highlights get extra care: either real reflections plus hand-placed highlight lights, or highlights placed by the animator through the rig — reason: highlights make characters appealing {tags: lighting, eyes, rig}
  - [Procedure] Rigging: generate the control rig with CloudRig (the studio's extension of Rigify), weight-paint by hand (Easy Weight add-on), then author corrective shape keys; Pose Shape Keys add-on lets rig and weights change later while keeping correctives (stated) — principle: deformation from bones and corrective shape keys only, no muscle or physics systems, because of technical constraints and the art styles pursued {tags: cloudrig, rigify, rigging, shape-keys, weight-painting}
  - [Procedure] CloudRig: place a Metarig matching the character's proportions; assign Rig Component types (spine, arm, leg) to bones; set parameters; Generate the Control Rig (regenerate as often as needed); fix problems from the Generation Log; refine with Single Control, Bone Tweak or a post-generation script (stated) {tags: cloudrig, rigging}
  - [Judgement] (blog) Limbs fully procedural, faces mostly rigged by hand — reason: limbs are simple and similar across characters; faces are unique and demanding, and "Procedural rigging is a trade-off between convenience and control" (Dzadik) {tags: cloudrig, rigify, rigging, face-rig}
  - [Procedure] Flamenco render: Output tab → OpenEXR, Previews on; Flamenco panel → Fetch Job Types → Simple Blender Render; Render Output Directory = project `render/`; Add Path Components 3; Submit to Flamenco (stated) {tags: flamenco, exr, render-farm}
  - [Procedure] Render review: File > New > Render Review (Render Review + Blender Kitsu add-ons), choose the sequence, select the render's strip, Push to Edit & Approve Render (copies the mp4 to `editorial/shots` and the image sequence to `editorial/frames`); in the edit file, load approved image sequences (EXR or JPG) onto a new VSE channel (stated) — what is checked during review not stated {tags: review, vse, kitsu, flamenco}
  - [Procedure] Final delivery: from the edit .blend, render PNG frames and a WAV audio file to `editorial/deliver/`, then encode and mux with the studio's delivery script (stated; codec and bitrate not stated) {tags: vse, delivery}
- **Quotes:** "We can start lighting a shot as soon as there is a first blocking pass available." — Blender Studio docs; "A significant drawback of both methods is that animation is very hard to do." — Blender Studio docs (on animating linked values)
- **Depth note:** medium-deep on structure, linking, lighting order and override mechanics; no numeric render settings anywhere (the Rendering page is a stub).

### A-05 · Cycles Turbocharged: how we made rendering 10x faster (Agent 327: Operation Barbershop)
- **URL:** https://studio.blender.org/blog/cycles-turbocharged-how-we-made-rendering-10x-faster
- **Artist/studio:** Francesco Siddi, Blender Institute (the optimisation by Sergey Sharybin)
- **Year:** 2017 (20 Jan 2017)
- **Contest & placement:** none — open movie / production
- **Blender version:** not stated on the page (secondary coverage ties the fix to 2.78b)
- **Engine & render settings:** Cycles with high-quality rendered motion blur; advanced shaders, hair, indoor environments, complex lighting, many mirrors. Samples, bounces, denoising not stated.
- **Render time & hardware:** "some frames were taking over 100 hours to render" before the fix; farm at IT4Innovations (VSB – Technical University of Ostrava): 24-core nodes (2x Xeon E5-2680v3, 2.5 GHz), and an Intel-compiler build using a Xeon Phi coprocessor
- **Techniques:**
  - [Judgement] Production goal of high-quality motion blur in render — reason: quality (not elaborated). Cost: motion blur, especially on hair, made some frames up to 100x slower {tags: motion-blur, hair-curves, render-time, cycles}
  - [Procedure] Fix made in Cycles itself: better layout of hair bounding boxes in the BVH (~10x), the same applied to triangles (up to 8x more on full frames), ~15% more memory for that shot (stated) — principle: motion-blurred hair was the dominant cost; tighter BVH bounds cut it (the BVH explanation was promised for a later post) {tags: cycles, bvh, motion-blur, hair-curves}
- **Quotes:** "some frames were taking over 100 hours to render." — Francesco Siddi
- **Depth note:** medium; names the cause (motion-blurred hair in the BVH) and the hardware, gives no scene settings.

### A-06 · Charge Render Times Overview (+ Charge Premiere post)
- **URL:** https://studio.blender.org/blog/charge-render-times-overview ; https://studio.blender.org/blog/charge-premiere/
- **Artist/studio:** Francesco Siddi (Producer), Blender Studio
- **Year:** 2023 (4 Jan 2023); premiere post 15 Dec 2022
- **Contest & placement:** none — open movie / production
- **Blender version:** an in-development build (number not stated)
- **Engine & render settings:** "EEVEE as render engine for the entire production" (premiere post); 4K final frames; working in Blender's linear space with the Filmic view transform (Siddi, comment reply on the premiere post, 17 Dec 2022). Samples, soft shadows, volumetrics, motion-blur steps not stated.
- **Render time & hardware:** ~3,200 frames charted (titles and credits excluded); median ≈3 minutes per frame at 4K; wide variation even within one shot, attributed to rendering hardware, shader compilation time, scene complexity and the number of motion-blur samples; rendered fully in-house on NVIDIA cards ("RTX 3XXX, Quadro, etc") managed by Flamenco, "within a few weeks"
- **Techniques:**
  - [Judgement] EEVEE for a realism-oriented film — reason: project goal "to challenge Blender and the creative team to pursue heightened realism" in the interactive PBR workflow {tags: eevee, realism}
  - [Setting] Number of motion-blur samples named as one of four drivers of per-frame time (value not stated) — principle: not stated {tags: eevee, motion-blur, render-time}
  - [Setting] Filmic view transform, linear working space — principle: not stated {tags: filmic, colour-management}
  - [Procedure] Final frames rendered with Flamenco on in-house GPUs (steps not stated) {tags: flamenco, render-farm}
- **Quotes:** "The rendering of the film was performed fully in-house, using the Flamenco render manager." — Francesco Siddi
- **Depth note:** thin-to-medium. The numbers are useful; the deeper Charge posts (Smoke and Mirrors FX, lens-dust compositing) are login-walled, and the production logs only say the team worked to "render every shot with little to no glitches" before the conference screening.

### A-07 · Flow (2024) — "Charting a New Course for Flow" (VFX Voice), with the 80.lv summary of the blender.org "Making Flow" interview and an 80.lv piece quoting the director's posts
- **URL:** https://vfxvoice.com/?p=13143691 (primary) ; https://80.lv/articles/award-winning-flow-s-director-breaks-down-how-blender-made-the-film-possible (SECONDARY summary of blender.org; original returned 403) ; https://80.lv/articles/see-how-animation-for-the-award-winning-movie-flow-was-created/
- **Artist/studio:** Trevor Hogg (VFX Voice) interviewing Gints Zilbalodis (director), Léo Silly-Pélissier (animation director), Mārtiņš Upītis (simulation artist); Dream Well Studio (Latvia) with Sacrebleu (France) and Take Five (Belgium). 80.lv pages by Amber Rutherford.
- **Year:** film 2024; VFX Voice 7 Jan 2025; 80.lv 2025
- **Contest & placement:** none — feature film (outside Blender Studio)
- **Blender version:** director learned on 2.8 alpha; team used 2.9 or 3.0 when they joined (80.lv summary, sources disagree on dates)
- **Engine & render settings:** EEVEE throughout, from the animatic to final; 4K output (80.lv summary). Settings not stated.
- **Render time & hardware:** 0.5 to 10 seconds per frame at 4K; no render farm — final render on the director's PC (80.lv summary of blender.org)
- **Techniques:**
  - [Procedure] No storyboards: build a rough set in 3D, place characters, explore it with a virtual camera to find shots; adjust the camera after the first animation pass so it responds to the action; EEVEE previews of lighting and fog in the animatic shaped framing and shadow placement (steps stated in outline) — principle: long 360° takes moving in depth could not be drawn on boards {tags: eevee, previz, layout, camera}
  - [Judgement] Camera given slight response delays — reason: to suggest an operator reacting to events; an "organic, handmade feel" over clean perfection {tags: camera, animation}
  - [Procedure] Animation guided by written per-character behaviour rules (ears turn to check sounds, head turns toward interesting sounds, tail may move independently), built from reference video and photos shared on a website; naturalistic, not copied (stated) — principle: frame-by-frame checking was impossible on shots of ~6,000 frames, so rules kept the animals consistent {tags: animation-workflow, reference, long-take}
  - [Procedure] Longest shot 6,606 frames: eight animators worked on separate scenes that were merged into one file; the merged file was very heavy; the shot was started early and finished near the end (stated) {tags: long-take, shot-files}
  - [Procedure] Water: a Geometry Nodes tool (Upītis) that adds water, submerges objects, and has lighting and physics respond by rules; the camera can pass above and below the surface without switching modes; two stages — key effects before animation, small splashes and ripples after; dense simulations in the foreground, sparse in the background, previs simulations kept where they looked better; splashes layered over cut-out sections of water (stated) {tags: geometry-nodes, water, simulation-cache}
  - [Procedure] Each shot is a separate file (original total 160, more added); water checked for colour and movement against adjacent shots (stated) {tags: continuity, shot-files, water}
  - [Judgement] Water colour arc across the film: green at the start, dull and muddy in the middle, bluer and oceanic at the end — reason: not stated {tags: colour-script, water}
  - [Judgement] Characters stylised and flat-shaded, environments realistic and detailed — reason: keeps the animals from looking cold or synthetic {tags: look-dev, stylisation}
  - [Judgement] (80.lv summary) No compositing; all colour adjustment done in shaders — reason: not stated {tags: compositor, colour-management, eevee}
  - [Judgement] (80.lv summary) Large single files with everything appended rather than linked; no library overrides — reason: linked assets broke when moving between desktop and laptop; single files allowed per-shot material and lighting tweaks {tags: library-overrides, linking, shot-files}
  - [Setting] (80.lv summary) Add-ons named: GeoScatter, Animation Layers, FLIP Fluids, Cell Fluids, Baga Pie, Baga Rain Generator, Copy Global Transform — principle: not stated {tags: add-ons, animation-layers, simulation-cache}
- **Quotes:** "Some shots are 6,000 frames, so I wrote some rules for animators" — Léo Silly-Pélissier; "Blender has this great real-time render engine called Eevee that helped us to do the animatic" — Gints Zilbalodis
- **Depth note:** medium-deep on animation and water workflow (VFX Voice); render-time and file-management facts are second-hand (80.lv paraphrase of a page I could not open) and should be cited as such.

### A-08 · Shading and Rendering of "Wing It!"
- **URL:** https://studio.blender.org/blog/shading-and-rendering-of-wing-it
- **Artist/studio:** Simon Thommes (Shading and FX), Blender Studio
- **Year:** 2023 (5 Oct 2023)
- **Contest & placement:** none — open movie / production
- **Blender version:** not stated (a custom Kuwahara-like filter was used before Blender 4.0 added one natively)
- **Engine & render settings:** EEVEE. Exact SSS, sample, shadow and film values not stated; sections on normal faceting, outlines and character shading are partly login-walled.
- **Render time & hardware:** not stated
- **Techniques:**
  - [Judgement] EEVEE over Cycles — reason: faster previews for quick turnaround, and more direct control of light response and normals; SSS on everything "rules out" Cycles, where SSS behaves very differently at high settings {tags: eevee, cycles, sss, npr}
  - [Setting] Subsurface scattering applied to essentially every object (carried over from Coffee Run) — principle: flattens dimensional detail toward a graphic look {tags: sss, eevee, npr}
  - [Judgement] Shadows mostly removed; kept only for simple shapes (e.g. the rocket hull); other shadows replaced by simplified proxy geometry casting transparent, distance-faded shadows — reason: simplified graphic look {tags: shadows, npr}
  - [Procedure] Normal faceting: normals snapped to discrete directions, in the shader with a Voronoi texture or in Geometry Nodes from edge-angle boundaries or hand-set boundary attributes (stated in outline; node graphs gated) {tags: geometry-nodes, normals, npr}
  - [Procedure] Environment outlines: mesh strips generated from the camera view with Geometry Nodes; per-object colour from a "Line Properties" modifier; outlines on their own render layer so they can be lit separately for rim light; character outlines built into the shader (stated in outline) {tags: geometry-nodes, outlines, view-layers, npr}
  - [Setting] Paper texture applied in the shader, not in compositing — principle: it stays anchored to moving objects and a moving camera instead of sitting on the screen {tags: npr, texture, flicker}
  - [Procedure] Character shading: normals blurred with Geometry Nodes on top of the SSS shader; fake rim light and toon shading built into the shader (stated in outline) {tags: geometry-nodes, sss, npr}
  - [Judgement] Compositing ended up playing a smaller role than planned; a custom painterly filter approximated a Kuwahara filter — reason: not stated {tags: compositor, npr}
  - [Procedure] Outline/silhouette failures for certain poses fixed frame by frame in a handful of shots (steps not stated) {tags: outlines, flicker}
- **Quotes:** "fast render times, especially for previews, allow for a quick turnaround during production." — Simon Thommes; "some unfortunate, obvious hiccups with the outline/silhouette tech" — Simon Thommes
- **Depth note:** medium; clear reasons and methods in outline, no numeric settings, some sections gated.

### A-09 · Wing It! Lighting: From Concept to Render
- **URL:** https://studio.blender.org/blog/wing-it-from-concept-to-render/
- **Artist/studio:** Andy Goralczyk (Lighting and Compositing), Blender Studio
- **Year:** 2025 (27 Jan 2025); film 2023
- **Contest & placement:** none — open movie / production
- **Blender version:** not stated
- **Engine & render settings:** EEVEE (per A-08); no settings stated in this post
- **Render time & hardware:** not stated
- **Techniques:**
  - [Procedure] 1. quick pre-light of the blocked animation; 2. hand it to concept art for a 2D paint-over; 3. adjust the lighting to match; 4. iterate (the example shot 020_0040_A went through 12 iterations); 5. break the concept art into parameters that can be exposed and reused per shot, and transfer value sets between shots as the look matures (stated) {tags: lighting, paint-over, review, continuity}
  - [Setting] One World environment per major sequence for the base colour tint; a preset barn-interior light rig linked into every interior shot — principle: continuity across a sequence {tags: light-rig, linking, world, continuity}
  - [Procedure] Global key lights first (a simple sun for exteriors; the barn rig has its own sun), because they most affect shot-to-shot continuity (stated) {tags: lighting, continuity, sun-light}
  - [Setting] Characters decoupled from environment lights: each character's rig has a controller with a Tilt property (key angle) plus shadow and highlight colour controls; two colourable rim lights per character, opposite or alongside the key — principle: independent control of character and set {tags: rig, lighting, npr}
  - [Setting] The sun key is the only shadow caster; most props and set pieces excluded from casting; characters use shadow proxies with controllable gradients — principle: deliberately simplified, cartoony shadows {tags: shadows, npr}
  - [Procedure] Environment accents (area, spot, point) for colour casts, gradients and fake bounces (stated) {tags: lighting, area-light}
  - [Setting] View layers: Base (foreground beauty); Outlines (whole scene as holdout to isolate the line work, with its own lighting pass for stylised edge highlights); Grease Pencil (animation smears); Preview (excluded from final). The shot builder add-on splits collections into view layers and links them in the compositor — principle: separate control of line, beauty and 2D elements {tags: view-layers, outlines, grease-pencil, shot-builder}
  - [Procedure] Compositing inside each lighting file: node groups combine beauty and outline passes; a depth-based colour gradient fades in a uniform colour for character separation (stated) {tags: compositor, node-group}
  - [Judgement] Rim light kept subtle in the example shot — reason: the shot was already strongly backlit {tags: lighting}
  - [Judgement] A 2D mindset over any single technique — reason: avoids over-detailing; 2D feedback from people who know 2D is the key asset {tags: lighting, npr, review}
- **Quotes:** "I've found that putting in lights and tweaking them is about 20% of the job." — Andy Goralczyk; "Having people who know what they are doing in 2D is an enormous asset to get good feedback." — Andy Goralczyk
- **Depth note:** medium-deep on lighting structure and per-sequence reuse; no numeric settings.

### A-10 · Rendering Snow Parkour Animation with EEVEE
- **URL:** https://studio.blender.org/blog/rendering-snow-parkour-animation-with-eevee
- **Artist/studio:** Beau Gerbrands, Blender Studio (with Pablico Fournier, Hjalti Hjálmarsson; supervised by Andy Goralczyk)
- **Year:** 2022 (29 Jun 2022); a 13-shot promotional animation made Nov 2021 – Feb 2022 as a production test of EEVEE (not one of the open movies; kept as the only detailed EEVEE animation-rendering retrospective found)
- **Contest & placement:** none — studio production test
- **Blender version:** not stated
- **Engine & render settings:** EEVEE; 1920×1080, 24 fps; cube and cascade shadow size "almost always 1024 px"; viewport 2 samples with a scaled-down viewport and Simplify; motion blur with zero steps = vector blur. Render samples not stated.
- **Render time & hardware:** ~3 minutes per frame average; workstations: Xeon E5-2697 v3 (56 threads) + RTX 3080 10 GB + 64 GB RAM, and Ryzen 7 3800X + RX 590 + 32 GB RAM
- **Techniques:**
  - [Judgement] Scenes built "as if for Cycles" (no LODs, no baked normals, no retopology) — outcome: this cost performance; the conclusion recommends game-style scene building for EEVEE {tags: eevee, optimisation}
  - [Setting] Avoid Subdivision Surface modifiers; retopologise or decimate — principle: EEVEE triangulates (doubling triangles) and subdivision level 2 multiplies the base count by 16; single-thread CPU object evaluation (characters with subdivision) dominated render time, so Simplify helped {tags: eevee, subdivision, simplify, render-time}
  - [Setting] Bake normal maps instead of Bump/Displacement nodes — principle: each adds two extra shader graphs {tags: eevee, shading}
  - [Setting] Limit each light's influence distance; prefer spot lights under 90° — principle: shadow cost per light: point 6 projections, area 5, spot 1 under 90° (area cost above 90°), sun cascades always update {tags: eevee, lighting, shadows}
  - [Setting] Shadow cube/cascade size 1024 px, raised carefully only in very detailed scenes — principle: higher sizes lengthen renders and slow the viewport {tags: eevee, shadows}
  - [Procedure] Overlapping volumetrics fixed by lowering volumetric tile size and raising samples (values not stated) {tags: eevee, volumetrics}
  - [Procedure] Light probes re-baked for each shot (steps not stated) — principle: baked probe lighting cannot be shared between scenes {tags: eevee, light-probes, shot-files}
  - [Setting] Motion blur steps: use only as many as needed; 0 steps falls back to vector blur (faster, less accurate) {tags: eevee, motion-blur}
  - [Judgement] Get the scene right before rendering instead of fixing in compositing — reason: EEVEE passes lack the sample refinement of the Combined pass (lower-fidelity DOF and motion blur, Alpha Blend materials missing), so Combined cannot be rebuilt from passes; Alpha Hashed materials appear in passes but add noise that only more samples remove {tags: eevee, compositor, alpha-hashed, render-passes}
  - [Setting] Replace overlapping Alpha Blend glass with an opaque material using a refraction shader; remove SSS where it bleeds or glows (e.g. inside the mouth) {tags: eevee, sss, shading}
  - [Procedure] Drone spot lights: small shadow-caster objects close to the light for an uneven flashlight look; two spots per drone, one lighting the scene and one affecting only volumes (via the light's Diffuse/Glossy/Volume sliders, which can exceed 1.0) (stated) {tags: eevee, lighting, volumetrics}
  - [Setting] Lighting kept in the shared set file — principle: consistency between shots, at some performance cost {tags: continuity, linking, light-rig}
- **Quotes:** "Strongly suggest not using any subdivision surface modifiers." — Beau Gerbrands; "Eevee and Cycles have their own strengths and weaknesses when rendering animations." — Beau Gerbrands
- **Depth note:** deep, with numbers and reasons; the best source found on EEVEE cost structure for animation.

### A-11 · Color Scripting – Intro & Coffee Run
- **URL:** https://studio.blender.org/blog/color-scripting/
- **Artist/studio:** Vivien Lulkowski (Concept Artist) and Julien Kaspar (CG Artist), Blender Studio
- **Year:** 2024 (31 Dec 2024); film 2020
- **Contest & placement:** none — open movie / production
- **Blender version:** not stated (Coffee Run was made in Blender 2.8 with EEVEE, per search-result text from blender.org; not read directly)
- **Engine & render settings:** not stated in this post
- **Render time & hardware:** not stated
- **Techniques:**
  - [Procedure] 1. ask story questions about how characters and environments change; 2. translate the beats into colour questions (screen coverage, colour recurrence, light influence); 3. write the intended audience reaction as plain statements and check them with the team; 4. list fixed constraints (character hair colours, white set pieces, time of day) and build around them; 5. sketch the whole film as one strip, or a shape such as a wheel for a looping story (Coffee Run used a wheel); 6. refine sections and paint each scene over stitched screenshots, adding textures, props and lighting effects; 7. match the paintings in 3D (stated) {tags: colour-script, lighting, previz}
  - [Judgement] Soft gradient "slidy ramps" between scenes; "colour bridges" carrying a colour from one scene to the next — reason: smooth the film's intense mood swings and keep the story flowing {tags: colour-script, continuity}
  - [Judgement] Pure white reserved for interactable elements; unimportant background characters as silhouettes — reason: "an obvious visual hierarchy" {tags: colour-script, composition}
  - [Judgement] A watercolour bloom marks each entry into a memory; the restaurant scene moved from night to sunset but kept its stark reds — reason: story signalling (stated in outline) {tags: colour-script}
  - [Judgement] Colour cheats allowed when they raise no questions (e.g. a lighter tone through a dark barn's window); most scenes skipped a colour-comp pass — reason: readability; time {tags: colour-script, lighting}
- **Quotes:** "Color can expose another facet of a story" — Vivien Lulkowski and Julien Kaspar; "It was important to create an obvious visual hierarchy" — Vivien Lulkowski and Julien Kaspar
- **Depth note:** medium-deep on judgement and procedure for planning colour across shots; no render settings.

### A-12 · Brushstroke Tools (Blender Studio add-on from Project Gold) + Gold production logs #59–#62
- **URL:** https://studio.blender.org/tools/addons/brushstroke_tools ; https://studio.blender.org/projects/gold/production-logs/
- **Artist/studio:** Blender Studio (docs); logs by Andy Goralczyk, Simon Thommes, Vivien Lulkowski
- **Year:** logs Jul 2024; docs current
- **Contest & placement:** none — open movie / production (Gold, painterly short)
- **Blender version:** not stated
- **Engine & render settings:** engine for Gold not stated in readable text. Docs: Cycles needs many transparent bounces for the overlapping stroke planes (black spots otherwise; a Render Setup operator in the Advanced panel sets this up); in EEVEE reduce viewport Pixel Size for navigation.
- **Render time & hardware:** not stated
- **Techniques:**
  - [Procedure] Brushstrokes are procedural textured mesh strips generated from curves with Geometry Nodes; every layer (Fill or Draw) belongs to a surface mesh; Fill layers follow drawn flow curves and need a valid UV map (run an Auto-UV unwrap if they ignore the curves) and enough mesh resolution (stated) {tags: geometry-nodes, brushstrokes, npr}
  - [Setting] "Deforming Surface" on a layer for stable strokes on a deforming mesh; requires the object's `add_rest_position_attribute` flag (works with linked data) — principle: not stated (the docs give only the requirement; that it stops strokes sliding on a deforming mesh is my inference, unverified) {tags: brushstrokes, deforming-surface, flicker, rest-position}
  - [Setting] "Animated Strokes" (experimental): strokes appear by the frame they were drawn, like Grease Pencil; needs auto-keying {tags: brushstrokes, grease-pencil}
  - [Setting] Cycles: raise transparent bounces (via Render Setup) — principle: many overlapping transparent planes {tags: cycles, transparency-bounces, brushstrokes}
  - [Judgement] (log #59) Andy's main concern near the end was "Adjusting the brush stroke jittering in certain sequences" — reason: not stated; method not stated {tags: brushstrokes, flicker}
  - [Procedure] (logs #59–#61) Motion trails split into separate render passes and merged in compositing; hand-painted Grease Pencil smudge and smear effects over fast movements; Geometry Nodes particle emission from cracks; brightness tweaks in compositing "to make Mikassa more readable" (steps not stated) {tags: compositor, grease-pencil, geometry-nodes, render-passes}
- **Quotes:** "All brushstroke layers created with the add-on are associated to a surface mesh object." — Blender Studio docs; "Adjusting the brush stroke jittering in certain sequences." — Andy Goralczyk (Gold log #59)
- **Depth note:** medium for the add-on; the logs are thin (titles over gated video) but name stroke jitter as a late-production problem.

### A-13 · Blender Development: Singularity and Beyond (+ Singularity production logs #347–#350)
- **URL:** https://studio.blender.org/blog/blender-development-singularity-and-beyond/ ; https://studio.blender.org/projects/singularity/production-logs/
- **Artist/studio:** Anastasia Rudina (blog), Blender Studio; logs by the studio team (Andy Goralczyk, Simon Thommes)
- **Year:** blog 29 June (year not shown; logs date the end of production to Feb–Mar 2026, so 2026 is likely — uncertain); film premiered 11 May
- **Contest & placement:** none — open movie / production (painterly, watercolour look)
- **Blender version:** production shaped Blender 5.x; 5.2 LTS (beta) features listed
- **Engine & render settings:** engine not stated in readable text. Delivery: 4K HDR. The Cycles texture cache (tiled `.tx` files beside the sources; only the tiles and mip levels each render tile needs are loaded) is described as a feature that came out of this work; render tiles of 1024 or 512 instead of 2048 reduce RAM on slower machines at a small speed cost.
- **Render time & hardware:** not stated (render farm, per logs)
- **Techniques:**
  - [Procedure] Colour grade done in the Video Sequence Editor: HDR video read with PQ or HLG from file metadata, each strip's input colour space set; export H.265 or AV1 with PQ or HLG at 100 nits reference white, full-range YUV; HDR-capable scopes (histogram, waveform, vectorscope; P3 and Rec.2020) (stated as features; their use on the film stated by the post) {tags: vse, hdr, colour-management, grading}
  - [Procedure] (log #349) First grading pass in the VSE with a proxy + HDR workflow; shots conformed to look right in both SDR and HDR (steps not stated) {tags: vse, hdr, grading}
  - [Procedure] Compositor node groups can drive VSE strip modifiers and effect strips (feature, stated) {tags: compositor, vse}
  - [Procedure] (log #348) After all shots were rendered, compositing effects added across sequences "for drama and consistency", plus a painterly lens flare; then grading, render-error fixing and export (steps not stated) {tags: compositor, continuity}
  - [Setting] Simplify panel Texture Resolution percentage for viewport work with the texture cache — principle: keep memory stable per render tile at 4K and above {tags: cycles, texture-cache, simplify}
- **Quotes:** "It is also our first film mastered in 4K HDR with a full color grade done in Blender's Video Sequence Editor." — Anastasia Rudina
- **Depth note:** thin-to-medium for production methods; mostly a features post. Kept for the HDR grade-in-VSE workflow and the texture-cache memory method; nothing on its render settings or noise.

### A-14 · Cosmos Laundromat (Gooseberry): "Gooseberry Production Benchmark file" + "Qarnot Computing renders Gooseberry"
- **URL:** http://gooseberry.blender.org/gooseberry-production-benchmark-file/ ; http://gooseberry.blender.org/qarnot-computing-renders-gooseberry/
- **Artist/studio:** Ton Roosendaal, Blender Institute
- **Year:** 2015 (20 Mar 2015; 5 May 2015)
- **Contest & placement:** none — open movie / production
- **Blender version:** 2.73a era (from the benchmark context; not stated in the body)
- **Engine & render settings:** Cycles; large environments, heavy grass, fur. The benchmark file is at "intermediate" quality without motion blur; final quality was planned to add more bounces and motion blur. Samples and bounces not stated.
- **Render time & hardware:** benchmark frame: 1133 s (19 min) on a Xeon E5-2697 v3, 56 threads; 2916 s on 16 threads; 7985 s on an 8-thread i7 930; 8–12 GB memory. Production estimate: about 3 hours per frame or more on fast i7 CPUs; a ~10-minute film would need ~60 systems full time for over 3 weeks, before tests and re-renders. Qarnot Computing supplied up to 64 systems on average (peaks of 100) for final frames; the studio's own farm took tests and previews.
- **Techniques:**
  - [Procedure] Split the farm by purpose: external farm for final frames, in-house farm for tests and previews (stated) — principle: final-frame demand far exceeded in-house capacity {tags: render-farm, render-time}
  - [Procedure] Command-line render of a frame: `blender -b -y -f 1` (stated) {tags: command-line, render-farm}
  - [Judgement] Quality planned to be switched by script between intermediate and final settings (script "later"; steps not stated) — reason: not stated {tags: render-settings, python}
- **Quotes:** "expecting render times of 3 hours per frame or more (on regular fast i7 cpus)" — Ton Roosendaal; "something nice and heavy, taking 8-12 GB memory and requiring an hour to render in a minimal quality!" — Ton Roosendaal
- **Depth note:** thin-to-medium; real numbers on cost and farm sizing, nothing on how noise or hair were handled. Production logs are titles over gated media.

### A-15 · Next Gen (Tangent Animation, 2018): studio posts on Blender Artists + Stefan Werner's Cycles Embree branch post
- **URL:** https://blenderartists.org/t/new-from-tangent-animation-next-gen-is-this-bender/1116159/38 ; https://blenderartists.org/t/new-from-tangent-animation-next-gen-is-this-bender/1116159/72 ; https://archive.blender.org/lists/bf-committers/2017-November/048936.html
- **Artist/studio:** forum user "twitchmedia" writing as the studio ("we", "our feature"; affiliation not confirmed on the page); Stefan Werner (bf-committers, 27 Nov 2017)
- **Year:** 2018 (forum, July 2018); 2017 (mailing list)
- **Contest & placement:** none — feature film (outside Blender Studio)
- **Blender version:** not stated (custom build with Embree in Cycles)
- **Engine & render settings:** "Cycles for all rendering"; Embree as Cycles' ray-tracing core (switchable on/off); full 3D motion blur on every shot
- **Render time & hardware:** "extremely reasonable and manageable, even with full 3D blur" — no numbers; farm not stated in readable sources (an AWS case-study page did not load)
- **Techniques:**
  - [Setting] 3D (rendered) motion blur on every shot — principle: not stated {tags: motion-blur, cycles}
  - [Procedure] Embree integrated into Cycles, CPU only (Embree 2.16.1+, built with `EMBREE_RAY_MASK=ON`, slightly patched) (stated) — principle: gains come mainly in scenes with deformation motion blur; small or static scenes gain little; also credited with volumetric rendering efficiency {tags: embree, cycles, motion-blur, volumetrics}
  - [Judgement] Accept Embree's differences from stock Cycles: object motion blur is straight linear motion, not arc interpolation; curves render with a slightly different shape; a patched Embree needed to avoid hair self-shadowing — reason: not stated (the stated benefit of Embree is speed with deformation motion blur) {tags: embree, motion-blur, hair-curves}
  - [Judgement] Render everything in camera and use Cryptomatte for compositing — reason: not stated {tags: cryptomatte, compositor}
  - [Procedure] Houdini and FumeFX generate VDB and Alembic data for import and render in Cycles; Alembic attributes exposed to Cycles material networks; Substance Painter and Photoshop for texturing; Blender cloth simulation improved and used heavily (stated, no steps) {tags: volumetrics, alembic, simulation-cache, cloth}
- **Quotes:** "There are no shots in the movie that do not have 3D blur in it." — twitchmedia (Blender Artists); "Object motion blur in Embree does not do arc interpolation but only straight linear motion." — Stefan Werner
- **Depth note:** thin-to-medium and informal; the only readable first-hand technical statements found for Next Gen.

## Sources — part B: Suzanne Awards, Pwnisher challenges, character work

### B-01 · A Winner of Pwnisher's Latest Challenge Breaks Down His Submission (Rampage Rally)
- **URL:** https://80.lv/articles/a-winner-of-pwnisher-s-latest-challenge-breaks-down-his-submission
- **Artist/studio:** Ted Heemskerk, 3D animator (Netherlands); interview by Theodore McKenzie, 80.lv
- **Year:** 2025 (article dated 3 October 2025)
- **Contest & placement:** Pwnisher "Rampage Rally" 3D challenge (11th community challenge) — 2nd place
- **Blender version:** not stated
- **Engine & render settings:** not stated (engine not named)
- **Render time & hardware:** render about 30 hours; total work about 170 hours; hardware not stated
- **Techniques:**
  - [Procedure] Characters: motorcycle sourced online; human rider is an iPhone 3D scan (Scaniverse app); dense, heavily moving body parts remodelled and retextured (steps not stated beyond this) — principle: not stated {tags: photogrammetry, scan-cleanup, character}
  - [Procedure] Dog texture: photos projected onto a matching model with a UV Project modifier (steps not stated) {tags: uv-project, photo-texture}
  - [Setting/Procedure] Clothing simulated in Marvelous Designer (the only non-Blender step); wind strength pushed "to the point where the clothes almost flew away", wind direction tuned to sell speed — principle: rider looked stiff after animation; cloth motion carries the speed {tags: cloth-sim, marvelous-designer, wind}
  - [Procedure] Tornado without a fluid/smoke sim: 1. volumetric cube; 2. shaped into a cone with Math and Map Range nodes; 3. animated Noise Texture added; 4. three particle systems for debris at three sizes — large debris near the tornado, small debris spread farther (steps stated) — principle: avoid a full sim "to reduce time"; the tornado reads as a big dark silhouette, "so it didn't need a lot of detail" {tags: volumetrics, shader-nodes, particles, sim-avoidance, silhouette}
  - [Procedure] Foliage: tree photos shot on overcast days against white sky, inverted, used as alpha mattes on cut-out cards; materials from photos plus some PBR sets; shaders combined with Mix Shader nodes driven by masks and blend modes; dirt and wet spots hand-painted (steps not stated in detail) {tags: photo-texture, alpha-cards, mix-shader, texture-painting}
  - [Judgement] Lighting kept to two main sources (bright sky corner, village light); extra lights on buildings to reinforce them; rim lights attached to the characters so they read against the tornado's shadow; dog's head given extra light; bridge brightened — reason: readability {tags: lighting, rim-light, readability}
  - [Judgement] Post-production planned early around a strong fish-eye lens effect; ground curved to push the fish-eye — reason: the lens decided which objects would be visible, so unseen work could be skipped {tags: compositing, lens-distortion, plan-from-camera}
  - [Judgement] Building photos taken at sunset or on overcast days — reason: no hard shadows baked into the wall textures {tags: photo-texture, reference}
- **Quotes:** "I turned the wind simulation to the point where the clothes almost flew away from the body." — Ted Heemskerk; "I ended up using a volumetric cube to reduce time." — Ted Heemskerk
- **Depth note:** medium; clear on sim-avoidance and photo texturing, silent on animation method, engine and render settings.

### B-02 · Fuelling a Pwnisher Contest Submission with 3D Modeling and Photogrammetry (Moving Meditations)
- **URL:** https://80.lv/articles/fuelling-a-pwnisher-contest-submission-with-3d-modeling-and-photogrammetry
- **Artist/studio:** Igor Witkowski, 3D artist (80.lv interview)
- **Year:** 2022 (article dated 17 October 2022)
- **Contest & placement:** Pwnisher "Moving Meditations" — article says the work was selected and mentions the top 100; exact placement not stated
- **Blender version:** not stated
- **Engine & render settings:** engine not named; rendered as an image sequence with "Filmic sRGB" view settings; samples/denoiser not stated
- **Render time & hardware:** 35 hours of rendering (plus about 32 hours of work); laptop with 6 GB VRAM; no farm
- **Techniques:**
  - [Procedure] Challenge animation: 1. Pwnisher supplied 27 mocap files (performed with a Tai-Chi master), all starting and ending on the same pose; 2. one file imported into the provided Blender template; 3. retargeted to the robot (tool/add-on not named); 4. because the robot is made of separate rigid parts, weight problems were fixed by manually parenting each limb and segment to the animation skeleton (steps stated, retarget tool not stated) — principle: rigid mechanical parts can be parented to bones instead of skinned {tags: mocap, retargeting, rigid-parenting, rigging}
  - [Judgement] Clipping frames hidden by timing a passing car to cross the frame at that moment — reason: cover an animation fault cheaply {tags: cover-up, staging}
  - [Procedure] Photogrammetry with KIRI Engine (Android): at least 20 photos walking around the object at varied heights, steady hand; even lighting to avoid baked shadows; avoid reflective surfaces; process on KIRI's servers and export; clean in Blender by deleting faces and smoothing with sculpt tools (steps stated) {tags: photogrammetry, scan-cleanup, sculpt}
  - [Procedure] Background passer-by: friend scanned twice (full body in T-pose, then a detailed head pass), merged, sent to Mixamo for auto-rig by placing pins, Mixamo animation applied (steps stated) {tags: photogrammetry, mixamo, auto-rig, character}
  - [Setting] Pillars displaced with Adaptive Subdivision (value not stated) — principle: realistic displacement "while maintaining optimal and smooth viewport and rendering" {tags: displacement, adaptive-subdivision}
  - [Procedure] Rain: 1. one droplet object used as the particle system's instance object, about 80,000 particles; 2. droplet decimated from about 80 faces to 12 (total rain geometry about 6.4M → 960k faces); 3. a wind force field angles the rain; 4. particle sim baked to cache (steps stated) — principle: "A baked simulation will play smoother as it uses cache data"; particle count kept down because dense rain eats VRAM on a 6 GB card; with motion blur and rain movement nobody can tell low-poly droplets — "It looked quite bad as a still object, but you can't see that once it's all in movement" {tags: particles, sim-cache, bake, decimate, motion-blur, vram, optimisation}
  - [Procedure] Ground splashes: fluid splash simulated in a separate file, two variants made, used as splash particle objects at a much lower count than the drops; the rain's image sequence used to guide splash placement; technique from a CG Geek tutorial (steps partly stated) {tags: fluid-sim, particles, instancing}
  - [Judgement] Lighting changed from two spot lights (daylight) to a dark alley: orange/pink lanterns, neon signs, fog from a cube with a volume texture — reason: not stated beyond mood {tags: lighting, volumetrics, mood}
  - [Procedure] Comp: sharpening in a video editor (not named); a faint car-splash layer; a black void on the back wall masked out (steps not stated) {tags: compositing, cleanup}
- **Quotes:** "A baked simulation will play smoother as it uses cache data to store it" — Igor Witkowski; "I just manually parented each limb and other segments of the body to the animation skeleton" — Igor Witkowski
- **Depth note:** good on rain particles, baking and scan workflow; nothing on samples, denoising or motion-blur settings.

### B-03 · Breakdown: LEGO-Style Construction Site with a Collapsing Crane Made with Blender ("Trouble in LEGO Town")
- **URL:** https://80.lv/articles/breakdown-lego-style-construction-site-with-a-collapsing-crane-made-with-blender
- **Artist/studio:** Tino Klein, 3D artist and video editor (Germany); interview by Gloria Levine, 80.lv
- **Year:** 2025 (article dated 23 April 2025); covers two entries — his first, a collapsing crane on a LEGO construction site for Pwnisher "Endless Engines" (2023), and "Trouble in LEGO Town" for "Chasm's Call"
- **Contest & placement:** Pwnisher "Chasm's Call" — 5th place (Endless Engines placement not stated)
- **Blender version:** not stated
- **Engine & render settings:** engine not named; 4K, 450 samples per frame, output as EXR; denoiser and motion blur not stated
- **Render time & hardware:** about 5 minutes per frame on his PC (specs not given); 120 frames overnight; no farm; 90–100 hours of work
- **Techniques:**
  - [Procedure] Layout: blockout with cubes/cylinders and placeholders; the chasm moved from the right half of frame to the left during production (steps stated) {tags: blockout, layout}
  - [Procedure] Assets: bricks and sets from Mecabricks, exported with the Mecabricks add-on (arrive UV-unwrapped and textured; paid add-on has sliders for scratches, fingerprints, colour deviation); custom LEGO material with his own add-on UI (glow, aged prints, wear stripes on joints); Dustify add-on for dust and hairs on foreground bricks (steps not stated in detail) {tags: kitbash, addon, shader, wear}
  - [Procedure] Viewport performance: a Geometry Nodes switch with an Is Viewport node merges objects only in the viewport — one building went from ~27,000 objects / 320,000 verts at 10–12 FPS to 6 objects / 25M verts at 60 FPS; repeated bricks are instances (steps stated) — principle: in the viewport the object count is the bottleneck, but merging multiplies vertices and "more vertices means more render time", so instances are kept for the render and merging is a switch, not permanent {tags: geometry-nodes, instancing, viewport-performance, is-viewport}
  - [Procedure] Bricks sucked into the chasm: 1. in Geometry Nodes, an effector sphere that can be slowly grown; 2. any object the sphere touches is moved to a new location set by the artist; 3. minor clipping accepted because it is in the background and in blur. Tried and dropped first: manual keyframes, constraints, the Commotion add-on; the working setup came from a Cartesian Caramel tutorial (steps stated) — principle: an effector lets him adjust without re-running a sim or re-keying many objects; a physics sim of thousands of bricks judged not worth it {tags: geometry-nodes, effector, sim-avoidance, procedural-animation}
  - [Procedure] Characters and cars keyframed by hand (cars slow down or get pulled in); the background placeholders from the blockout stayed in while animating the characters; crowd ("crowd simulation" in his words) = one to three walk cycles with very small variations, people following paths drawn on the floor; smear frames made in camera with LEGO bricks (steps not stated beyond this) {tags: keyframe, walk-cycle, crowd, path-drawn, smear-frames}
  - [Judgement] Bricks placed loose and crooked — reason: so the city looks less computer-built {tags: imperfection, realism}
  - [Judgement] Bright, colourful look on a Poly Haven HDRI base; off-camera objects to shape light and shadow; volume-scatter cube over the scene; blue point lights for brake lights, traffic lights, buildings and the chasm light (which grows and moves down) — reason: stand out from the many dark entries {tags: hdri, lighting, volumetrics, colour}
  - [Procedure] Grade inside Blender: 1. render 4K EXR with all render layers; 2. import EXRs into a new Blender project; 3. colour correction and grade with the Colorist Pro add-on; 4. Cryptomatte to brighten the yellow of the main character's face; 5. glow, lens dirt, grain, camera distortion (Colorist Pro), vignette, blur on outer edges; 6. export MP4 from Blender (steps stated) — principle: do as much as possible in camera / in Blender, less in After Effects or Premiere {tags: compositing, exr, cryptomatte, glare, grain, vignette}
- **Quotes:** "I almost immediately rejected the idea of doing the whole thing with physics-based simulations." — Tino Klein; "I was able to create an effector, a sphere, that I can slowly grow." — Tino Klein
- **Depth note:** good; one of the clearer accounts of choosing a procedural effector over simulation for an animated shot, plus exact sample count and per-frame time.

### B-04 · Behind the Scenes: Heroes of Bronze "Before the Storm" EEVEE Trailer
- **URL:** https://www.blendernation.com/2019/04/24/behind-the-scenes-heroes-of-bronze-before-the-storm-eevee-trailer/ (companion, for the finished short: https://3dvf.com/heroes-of-bronze-the-memory-4-ans-de-travail-sous-blender/, French, 23 Jan 2023, paraphrase only)
- **Artist/studio:** Martin Klekner (first-person BlenderNation "Behind the Scenes" article)
- **Year:** 2019 (teaser); the finished short "Heroes of Bronze: The Memory" (2023) was a Suzanne Awards 2023 Best Short finalist (conference.blender.org/2023/festival/finals/, entry 543) — not a winner
- **Contest & placement:** teaser itself: none stated; short film: Suzanne 2023 Best Short nominee
- **Blender version:** 2.8 (he calls it "B3D 2.8")
- **Engine & render settings:** EEVEE (switched from Cycles); no EEVEE settings given
- **Render time & hardware:** "final image sequences in a manner of minutes"; hardware not stated; no render farm
- **Techniques:**
  - [Judgement] Chose EEVEE over Cycles — reason: to speed up the workflow, remove long render hours and the need to hire render farms {tags: eevee, render-time, engine-choice}
  - [Procedure] Moving scenes from Cycles to EEVEE: 1. switch the render engine in the menu; 2. wait for everything to bake (steps stated; what is baked not stated) {tags: eevee, bake, engine-switch}
  - [Procedure] EEVEE lighting: build it from the ground up in EEVEE; Point and Spot lights to highlight objects; HDRI for overall light; Sun lamps dropped (steps stated) — reason: "Sun lamps somehow don't produce nice results for me" {tags: eevee, lighting, hdri}
  - [Judgement] Keep scenes light for real-time editing: low polycount, fake as much as possible with images (sky, some soldiers), delete everything not in the shot, limit the number of materials and image textures — reason: too many models/materials slow the process {tags: eevee, optimisation, matte-cards, cull-offscreen}
  - [Procedure] Human characters: 1. base mesh made in Adobe Fuse (Beta); 2. sent to Mixamo for automatic rigging; 3. pick animations in Mixamo; 4. download as .obj/.fbx/Collada; 5. edit animations and poses in Blender (steps stated) {tags: mixamo, auto-rig, character, crowd}
  - [Procedure] Texturing: in 2.8 select many models, edit all UVs together (multi-object UV editing), assign one material, export .obj, texture in Substance Painter with Smart Materials (steps stated) {tags: uv, substance, multi-object-editing}
  - [Judgement] Teaser shots chosen so each tests a technique he was unsure of (trireme sails in wind, marching army, Megascans rocky foreground) — reason: de-risk the film's techniques before the film {tags: test-shots, megascans, planning}
  - [Note, from the 3DVF 2023 article — paraphrase, not quotes] for the finished short: characters and animation from Reallusion Character Creator and iClone, his own mocap with a Rokoko suit, clothing in Marvelous Designer, Substance Painter textures, Blender for scene assembly and rendering, post in Photoshop/Premiere/After Effects {tags: mocap, rokoko, iclone, marvelous-designer}
- **Quotes:** "I also decided to choose the new EEVEE renderer instead of Cycles, to speed up my workflow." — Martin Klekner; "Sun lamps somehow don't produce nice results for me" — Martin Klekner
- **Depth note:** medium; clear reasons for EEVEE and for scene economy, no numeric settings.

### B-05 · Grooming Fur for Gremlins' Gizmo with Blender's Hair System ("11:58")
- **URL:** https://80.lv/articles/grooming-fur-for-gremlins-gizmo-with-blender-s-hair-system
- **Artist/studio:** Stefan Mayr, Senior Visual Development Artist at Framestore (interview by Gloria Levine, 80.lv)
- **Year:** 2024 (article dated 15 November 2024)
- **Contest & placement:** none; personal cinematic short "11:58", about a year of weekend work
- **Blender version:** not stated (mentions features of 4.0 retopology overlay and 4.2 EEVEE-next)
- **Engine & render settings:** EEVEE (EEVEE-next, 4.2) for previs and look feedback; Cycles for final render; samples not stated
- **Render time & hardware:** not stated
- **Techniques:**
  - [Procedure] Body: generic human base → proportions shifted to a toddler; dynamic topology for early shapes → retopology → ZBrush detail; areas under fur given only broad anatomy (steps stated) {tags: sculpt, dyntopo, retopology, character}
  - [Procedure] Eye meniscus generated by Geometry Nodes so it follows the eyelid shape keys without its own rig or deformer (steps not stated) — principle: a hand-placed meniscus is tedious to keep attached when the face is driven by shape keys {tags: geometry-nodes, eyes, shape-keys}
  - [Procedure] Fur with the new curves (geometry-based) hair system: 1. guides placed by hand over the whole body for flow; 2. guides split into head / torso / lower body inside one node tree, combined into one output (one hair system, per-region control); 3. head node setup reused on the body with little change; 4. property masks for density, length, clumping; an RGB clump_size_mask (black smallest → blue large) sets how many clump guides are generated — more guides = tighter clumps (face); 5. one probability mask for shading (red = white-hair probability, green = yellowish tint in the whites); base hair brown with per-hair hue/saturation/value variation (steps stated; node names not given) — principle: split regions because the hair system "can become rather slow rather quickly" {tags: hair-curves, geometry-nodes, groom, clumping, masks, performance}
  - [Procedure] UVs: symmetrical layout, overlapped eye UVs, higher texel density on face and hands; groom on a single UDIM; textures in Mari from a tileable skin base + ZBrush displacement + added redness (steps stated) {tags: uv, udim, mari, skin, displacement}
  - [Procedure] Shot design: sketches on paper → animated 3D blockout → iterate camera and pacing (steps stated) {tags: blockout, previs, camera}
  - [Setting/Procedure] Rig: Auto-Rig Pro for the body; face by shape keys with his own "shape network" add-on (steps not stated) — reason: shape keys are more art-directable than bones, though a lot of setup {tags: auto-rig-pro, shape-keys, facial-rig}
  - [Procedure] Comp entirely in Blender's compositor: passes main_pass, dust_pass, volume_pass; each main light rendered as its own Light Group in a multilayer EXR; light strengths rebalanced per pass in comp; lightning flashes timed in post instead of animating a light (steps stated) — principle: rebalance lighting after render without re-rendering {tags: compositor, light-groups, exr, multilayer, cycles}
  - [Judgement] Reference from pygmy monkeys, cats and toddlers; cartoon head roundness removed; cool moonlight with warm string-light accents per shot — reason: lifelike rather than puppet-like; a cool moody interior {tags: reference, design, lighting}
- **Quotes:** "I separated the fur into three parts: the head, the torso, and the lower body." — Stefan Mayr; "the outcome is more artdirectable than working with bones." — Stefan Mayr
- **Depth note:** good on groom structure, face rig choice and light-group comp; no hair node names, counts or Principled Hair BSDF values.

### B-06 · Flow (Gints Zilbalodis, Dream Well Studio) — three short accounts read together
- **URL:** https://80.lv/articles/award-winning-flow-s-director-breaks-down-how-blender-made-the-film-possible (80.lv news, 28 Jan 2025, reported speech); https://80.lv/articles/see-how-animation-for-the-award-winning-movie-flow-was-created/ (17 Jan 2025, director's own words on layout/animation); https://www.foxrenderfarm.com/news/inside-flow-a-conversation-with-the-film-s-technical-artists-konstantins-and-martins/ (interview with technical artists Konstantins Visnevskis and Mārtiņš Upītis)
- **Artist/studio:** Gints Zilbalodis (writer/director, sole lighter), Dream Well Studio (Latvia); about 15–20 people, 3–5 at a time
- **Year:** 2024 film; articles 2025
- **Contest & placement:** feature film, "over 60 awards" (80.lv); not a Suzanne / Pwnisher entry — kept as stylised animal-character animation made entirely in Blender
- **Blender version:** started on 2.8 alpha; team on 2.9 or 3.0 when it joined (80.lv); final production version not stated in these pages (a search snippet of the blender.org interview says 3.6 — not read, the page is behind a bot check)
- **Engine & render settings:** EEVEE, 4K; no compositing — "all color adjustments were made using shaders"
- **Render time & hardware:** 0.5 to 10 seconds per 4K frame; final render on the director's own PC; no render farm
- **Techniques:**
  - [Judgement] EEVEE over Cycles — reason: speed and instant feedback, faster and cheaper delivery; the technical artist says the choice also defined the film's look {tags: eevee, engine-choice, render-time}
  - [Procedure] Layout instead of storyboards: 1. design scenes directly in 3D; 2. explore a rough set with a virtual camera; 3. animators do a first pass; 4. camera adjusted after the first animation pass so it reacts to the action (steps stated) — principle: long camera-led shots, "almost like on a live-action film set" {tags: layout, previs, camera, long-take}
  - [Procedure] Concept-to-shot: director's rough Blender sketches → concept artist rebuilds in Blender keeping proportions (paint-over or model) → assets returned in place → director imports them into large single shot files and sets materials and lighting per shot (steps stated) {tags: previs, layout, file-management}
  - [Judgement] One big file per shot instead of linked libraries / library overrides — reason: switching between desktop and MacBook broke linked assets {tags: file-management, linking, library-overrides}
  - [Procedure] Water: a procedural toolset by Mārtiņš Upītis that adapts to the camera view and to what characters do; big water views made and tuned by hand; later generalised into a commercial add-on; some water with the Physical Open Waters add-on (steps not stated) — principle: "more control than you usually have with standard simulations" while keeping some randomness {tags: water, procedural, addon, sim-avoidance}
  - [Setting] Add-ons named: GeoScatter, Animation Layers, Cell Fluids, FLIP Fluids, Baga Pie, Baga Rain Generator, Copy Global Transform (which shot used which not stated) {tags: addon, animation-layers, flip-fluids, scatter-addon}
  - [Judgement] Colour graded in shaders, not in a compositor — reason: not stated {tags: grading, shader, no-compositing}
- **Quotes:** "Instead of using storyboards, I design the scenes directly in 3D." — Gints Zilbalodis; "We chose to use real-time rendering (Eevee) instead of a path tracer (Cycles)." — Konstantins Visnevskis
- **Counting note:** same film as A-07; A-07 and B-06 are counted as ONE source in every tally. B-06 adds the Fox Renderfarm technical-artists interview and the concept-to-shot procedure.
- **Depth note:** each page is short; together they give the engine, per-frame time, hardware and layout method, but nothing on rigs, EEVEE settings or how flicker was handled. The first 80.lv page is reported speech, not the director's words.

### B-07 · Behind the Scenes: Breaking Boundaries (Moving Meditations)
- **URL:** https://www.blendernation.com/2022/10/14/behind-the-scenes-breaking-boundaries/
- **Artist/studio:** Robert Kouts, 17, self-taught (Australia); first-person BlenderNation BTS (posted by Alina Khan)
- **Year:** 2022 (14 October 2022)
- **Contest & placement:** Pwnisher "Moving Meditations" — top 100
- **Blender version:** not stated
- **Engine & render settings:** not stated (he says he focuses on effects and animation)
- **Render time & hardware:** laptop GTX 1060 6 GB, i7-7700HQ, 16 GB RAM crashed on a single frame; final frames rendered on GarageFarm (render farm); times not stated
- **Techniques:**
  - [Setting] Challenge rules: template scene, camera may not be touched (camera shake allowed), mannequin replaced with one of 27 provided animations {tags: template, mocap}
  - [Procedure] Growing glass cracks: 1. simplified copy of the room; 2. each of 4 walls broken with the bundled Cell Fracture add-on; 3. vine holes cut with a Boolean modifier; 4. each wall rendered once at 4K from a matching camera, plus a UV Project from that view so UVs line up with the image; 5. crack objects' visibility animated to render a black-and-white growth mask; 6. cracks applied in comp through the UV pass (Nuke) (steps stated) — principle: "The easiest way to apply a texture onto an object in compositing is using the UV pass" {tags: cell-fracture, boolean, uv-pass, compositing, nuke, render-once}
  - [Setting] Glass shader: surface imperfections plus a slightly different IOR for R, G and B to fake chromatic aberration {tags: shader, glass, dispersion-fake}
  - [Procedure] Glass smash: 1. reuse the Cell Fracture pieces; 2. add Rigid Body (shards burst without extra steps); 3. bake the simulation; 4. Geometry Nodes scales the instances down over time; rendered as a separate pass with a near-default glass shader (steps stated) {tags: rigid-body, bake, sim-cache, geometry-nodes, render-passes}
  - [Procedure] Flower: shell animated with keyframed Simple Deform Bend and Twist; petals deformed by a Lattice and animated with shape keys with "Relative" turned off so keys blend in sequence driven by one "Evaluation Time" value; flower centre built and animated in Geometry Nodes (steps stated) — principle: absolute shape keys give a one-slider growth sequence {tags: shape-keys, evaluation-time, simple-deform, lattice, geometry-nodes}
  - [Procedure] Stems: point scatter with random rotation and scale; bounce by rotating with a sine function (steps stated) — principle: sine is the easiest smooth back-and-forth {tags: scatter, sine, procedural-animation}
  - [Procedure] Water ripples in Geometry Nodes: Geometry Proximity distance → Subtract/Add (animated, moves waves outward) → Multiply (wave density) → Sine → Multiply by the proximity value (fade with distance); setup duplicated for other water areas (steps stated) {tags: geometry-nodes, ripples, procedural-animation}
  - [Procedure] Lily pads on moving water: 1. disable all water deformations so it is flat; 2. bind pads with a Surface Deform modifier; 3. re-enable deformations — pads ride the waves; 4. add position/rotation keyframes (steps stated) {tags: surface-deform, modifier-order, keyframe}
  - [Procedure] Vines: curves processed in Geometry Nodes, radius scaled by distance to curve end, UVs generated by a node group before Curve to Mesh; jiggle from shape keys on the splines plus a Sine wave F-curve modifier in the Graph Editor (steps stated) {tags: curves, geometry-nodes, shape-keys, graph-editor, fcurve-modifier}
  - [Procedure] Final composite in Nuke combining glass, crack and main render passes (steps not stated in detail); clothes from Marvelous Designer; Quixel assets for props and foliage; Substance Painter plus Blender procedural materials {tags: nuke, compositing, marvelous-designer, megascans, substance}
- **Quotes:** "The easiest way to use shape keys in this manner is to disable "relative" in the settings." — Robert Kouts; "The final frames were rendered using Garage Farm, as my laptop was definitely not powerful enough" — Robert Kouts
- **Depth note:** good; node-by-node for several procedural animation tricks, nothing on render settings.

### B-08 · Winning the Kinetic Rush Challenge: How Jonas Bentzen Brought a 1920s Dystopia to Life in 3D
- **URL:** https://www.foxrenderfarm.com/news/winning-the-kinetic-rush-challenge-how-jonas-bentzen-brought-a-1920s-dystopia-to-life-in-3d
- **Artist/studio:** Jonas Bentzen, freelance 3D artist (Copenhagen), architecture background; Q&A on Fox Renderfarm's site
- **Year:** 2024 challenge; page last edited 27 February 2025
- **Contest & placement:** Pwnisher "Kinetic Rush" — top 100 (first submission)
- **Blender version:** not stated
- **Engine & render settings:** engine not named; rendered "in 32-bit ACES"; all passes with 10 % overscan; seven view layers plus a Z-depth pass; samples/denoise/motion blur not stated
- **Render time & hardware:** laptop with 12 GB VRAM; times and farm not stated
- **Techniques:**
  - [Procedure] Scene assembly: 1. build parts (foreground, midground, character, simulations…) in separate files; 2. instance/link them into the main file (viewport performance, file size, render speed); 3. split into seven view layers — foreground, foreground FX (papers), airships, midground, midground FX (distant papers), background, atmosphere/volumetrics; 4. render layers separately; 5. composite in Fusion Studio (per-layer light balance, extra smoke and volume layers); 6. convert to black and white and grade in DaVinci Resolve (steps stated) — principle: the 12 GB VRAM limit forced layers, and layers allow targeted re-renders {tags: view-layers, linking, vram, compositing, fusion, render-passes}
  - [Setting] 10 % overscan on all passes — principle: room for slight camera shake and lens distortion in comp {tags: overscan, camera-shake, lens-distortion}
  - [Setting] 32-bit ACES output — principle: exposure flexibility per layer afterwards {tags: aces, exr, colour-management}
  - [Judgement] Look built mainly through lighting; with many lights, exposure balanced per layer in comp to build depth and clarity; theme "Kinetic Rush" answered with layered motion (falling flyers from airships) instead of the first idea, rain — reason: flyers suggest announcements or war {tags: lighting, depth, story}
- **Quotes:** "Everything was rendered in 32-bit ACES to get the most flexibility afterwards" — Jonas Bentzen; "Rendering everything in separate layers also ensured that I could easily make re-renders" — Jonas Bentzen
- **Depth note:** medium; strong on layer/comp structure for an animated shot on limited VRAM, silent on the provided parkour animation and render settings.

### B-09 · Short Film: La Vida de una Piñata (Blender Artists thread, team's own replies)
- **URL:** https://blenderartists.org/t/short-film-la-vida-de-una-pinata/1376370 and page 2: https://blenderartists.org/t/short-film-la-vida-de-una-pinata/1376370?page=2
- **Artist/studio:** Kai Müri (art/technical direction, modelling, texturing, 3D/2D animation, lighting, compositing), Elena Heller (storyboard, rigging, 3D animation, backgrounds), Marina Kunz, Raphael Pfyffer — graduation film, Lucerne University of Applied Sciences and Arts
- **Year:** film 2021 (SIGGRAPH 2021 animation listing); thread 2022
- **Contest & placement:** Suzanne Awards 2022 — Best Short (BlenderNation BCON 2022 day-2 recap quoting the conference tweet: "BEST SHORT: La Vida de una Piñata"). Also nominated for BoBA 2022 animation (part C does not hold this thread, so it is kept here)
- **Blender version:** not stated
- **Engine & render settings:** EEVEE for beauty renders; Cryptomatte passes rendered from Cycles because EEVEE "didn't support them at that time"; settings not stated
- **Render time & hardware:** not stated
- **Techniques:**
  - [Procedure] Mask passes from the other engine: beauty in EEVEE, Cryptomatte passes from Cycles, used in comp to place hand-painted Krita textures over parts of the image — notably masking volumetric light with brushstrokes (steps stated) — principle: give the CG image a hand-painted look where it matters {tags: eevee, cycles, cryptomatte, compositing, painted-overlay, volumetrics}
  - [Procedure] Break the "perfect CG look": two stacked "Turbulent Displace" effect layers per object in After Effects to break up straight edges (steps stated) {tags: compositing, after-effects, edge-breakup, npr}
  - [Judgement] Heavy grade, colours pushed for saturation and "pop" — reason: cartoons typically have very saturated colours {tags: grading, colour, cartoon}
  - [Judgement] In hindsight, would not composite in After Effects again; recommends Nuke or Blender — reason: layer-based, "quickly reaches its limits, even in small projects", old and slow {tags: compositing, tool-choice}
  - [Setting] "We did all the 3D work in Blender. For the rest, we mostly used Open-Source Software." Rig: a free monster-truck rig was shared on BlendSwap (whether it is the film's rig not confirmed); rig system for characters not stated {tags: pipeline, rigging}
- **Quotes:** "we used the Cryptomatte Passes from Cycles, since Eevee didn't support them at that time." — Kai Müri; "The idea was to break up the straight edges of all objects." — Kai Müri
- **Depth note:** thin on animation and render settings; useful and specific on comp tricks that make an EEVEE film read as painted. The only Suzanne Best Short winner in this set with a text account of method beyond tool lists.

### B-10 · Interview with Koala OK, 2nd Place Winner in Pwnisher's Boss Fight 3D Render Challenge ("MEOW~")
- **URL:** https://www.foxrenderfarm.com/news/interview-with-koala-ok-2nd-place-winner-in-pwnisher-boss-fight-3d-render-challenge
- **Artist/studio:** Koala OK, freelance CG artist (9+ years in film, animation, games); Q&A on Fox Renderfarm
- **Year:** 2024 (page last edited 28 October 2024)
- **Contest & placement:** Pwnisher "Boss Fight" (7th community challenge, 2,880 submissions) — 2nd place
- **Blender version:** not stated
- **Engine & render settings:** EEVEE ("mostly use Eevee and probably less than 1% of the time I would use Cycles"); explosion rendered with motion blur on; other settings not stated
- **Render time & hardware:** not stated; whole piece made in about one week
- **Techniques:**
  - [Procedure] Story blocking: plot poses drawn with the Grease Pencil ("Blender crayon tool") directly over the official camera reference file — basic poses must be readable, drawing quality does not matter (steps stated) {tags: grease-pencil, storyboard, blocking}
  - [Procedure] Pose-to-pose: 1. key poses of the hero set first with interpolation changed to constant ("no transition, snap!") so timing is clear at a glance; 2. then transitions and anticipation/buffers added; 3. supporting characters animated to the hero's rhythm, first as low-poly stand-ins (steps stated) — principle: the hero's rhythm "basically determines everything"; accurate key poses and timing first, borrowing from Japanese anime timing {tags: blocking, constant-interpolation, stepped, pose-to-pose, timing}
  - [Procedure] Large fabric posed with bones plus a modifier he calls "replace" (exact modifier not identifiable from the text); character effects made with models and modifiers (steps not stated) {tags: cloth-fake, bones, modifiers}
  - [Procedure] Secondary action added last: robot structural vibration, camera shake, small deformation "drawing" on models (steps not stated) {tags: secondary-motion, camera-shake}
  - [Procedure] Stylised FX: live/realistic effect footage processed in DaVinci with a post node — flatter, fewer details, sharpened edges, fewer transitions, lower frame rate — exported as a frame sequence and brought back into Blender (steps stated at this level) — reason: models looked too stiff, fluid sims too hard, hand-drawing beyond him, raw footage too realistic for the style {tags: fx, stylised, reduced-frame-rate, image-sequence}
  - [Procedure] Explosion: a sphere with a procedural texture and a scale animation, rendered with motion blur, no layering; glow from Blender's real-time compositor, then colour/light correction in DaVinci (steps stated) {tags: procedural-fx, motion-blur, realtime-compositor, glare}
  - [Judgement] 24 lights but only 3–4 matter: main backlight + volume fog for a night silhouette, then 3–4 fill/layer lights; spotlights on the robot parented to its bones; cool tones first then warm; dark foreground, bright background — reason: the hero's silhouette must read {tags: lighting, silhouette, volumetrics, light-parenting}
  - [Judgement] Background built in under half a day from cubes plus one 4K texture collage assembled from Midjourney images (his words: "pure laziness", energy saved for the hero) — reason: everything serves the main character {tags: background, matte-texture, prioritisation}
  - [Judgement] EEVEE for nearly everything — reason: fast for mild realism, atmosphere and stylisation; realistic glass is harder; for beginners the engine "doesn't change the quality of the work" {tags: eevee, engine-choice}
- **Quotes:** "first I made the key action of the little boy, but changed the animation interpolation to no transition, snap!" — Koala OK; "I counted 24 lights, but only three or four actually matter" — Koala OK
- **Depth note:** good on animation order (constant-interpolation blocking) and lighting priorities; machine-translated feel in places; no settings numbers.

### B-11 · DRÆM SEQUENCE Top 3: Inside the Squirrel's House That Ted Heemskerk Built with Blender
- **URL:** https://www.foxrenderfarm.com/news/draem-sequence-top-3-inside-the-squirrel-s-house-that-ted-heemskerk-built-with-blender/
- **Artist/studio:** Ted Heemskerk (Netherlands) — same artist as B-01, different challenge
- **Year:** 2026 (page last edited 20 April 2026)
- **Contest & placement:** Pwnisher "DRÆM SEQUENCE" (12th challenge; visualise a 120 BPM beat with on-beat keyframes) — 3rd place
- **Blender version:** not stated
- **Engine & render settings:** not stated
- **Render time & hardware:** rendered on Fox Renderfarm because his own PC "would have taken many hours"; times not stated
- **Techniques:**
  - [Procedure] 1. about five days on the idea; 2. blockout in Blender with few references; 3. lumberjack clothing designed in Marvelous Designer with photos of his own clothes as textures on the patterns; 4. face recorded with a Rokoko face rig — tested on a basic head (unconvincing), then on a 3D scan of his own head with the moving face texture on top; 5. axe swing animated on the 120 BPM beat; 6. small light blink on the axe at the exact moment of impact (steps stated; beat-sync method in Blender — markers, keys — not stated) {tags: blockout, marvelous-designer, facial-mocap, rokoko, beat-sync, photogrammetry}
  - [Judgement] Other motions exaggerated to match the fast axe swing — reason: so the whole performance feels cohesive {tags: animation, exaggeration, timing}
  - [Judgement] Hitting every beat made the lumberjack look robotic and repetitive; breaking up the repetition made the beat hits unreadable, so he broke the repetition and added the light blink on impact to restore the hit — reason: keep natural motion and a readable beat at once {tags: beat-sync, repetition, accent-light}
  - [Judgement] Keep the character's face constantly moving — reason: so viewers do not notice its uncanny details {tags: facial-animation, uncanny-valley}
  - [Judgement] Real-world small props (matchbox table, tin-can pot, napkin rug) fill the tree interior — reason: lived-in and plausible at squirrel scale; he judges lighting and colour first, then animation and motion, then story {tags: set-dressing, scale, priorities}
- **Quotes:** "What really helped was to make the character constantly moving." — Ted Heemskerk; "I added a small light blink on top of the axe at the exact moment when the beat hits." — Ted Heemskerk
- **Depth note:** medium-thin; worthwhile for three animation judgements and the face-scan trick; no settings.

### B-12 · Kinetic Rush Mastery: Aiman Samat's 'Mother' Conquers Pwnisher's Internet-Breaking 3D Challenge
- **URL:** https://www.foxrenderfarm.com/news/kinetic-rush-mastery-aiman-samat-mother-conquers-pwnisher-internet-breaking-3d-challenge
- **Artist/studio:** Aiman Samat, VFX artist at Ingenuity Studios (Los Angeles); Q&A on Fox Renderfarm
- **Year:** 2024 (page last edited 15 October 2024)
- **Contest & placement:** Pwnisher "Kinetic Rush" — top spot (1st)
- **Blender version:** not stated
- **Engine & render settings:** engine not named; final output 2–3 PNG passes; settings not stated
- **Render time & hardware:** about one hour per frame on his home PC (RTX 3070), scene not optimised; 2 days left before the deadline, so moved to Fox Renderfarm (sponsor coupon)
- **Techniques:**
  - [Procedure] His usual pipeline (stated as contrast): gather references → animated previs until movement and environment blocking are right → model/structure the environment → animate with a partner → simulation in Houdini with a roommate → render 15+ passes (AOVs, light trees, depth) as Multilayer EXR from Blender → proxies of the passes → composite in After Effects (steps stated) {tags: previs, multilayer-exr, light-groups, render-passes, compositing}
  - [Procedure] For this entry (solo rule, time pressure): little reference or blocking; environment from a purchased Unreal game asset rearranged into three rooms; look "nailed" in Blender so only 2–3 PNG passes were needed and comp was short (steps stated) — principle: spend the time on animation; get the look in-render to save comp time {tags: kitbash, look-in-camera, render-passes, prioritisation}
  - [Judgement] Three rooms staged for varied movement: a deep large room, a medium room with stairs along the Y axis, a tight final corridor for the climax — reason: vary spatial movement through the shot {tags: staging, layout, camera}
  - [Judgement] Rule: the character must start and end at the same spot (loop) — he staged the chaos around that constraint {tags: loop, template, staging}
  - [Judgement] Sprint animated without a reference shoot; trusted viewers pointed out parts that did not feel real throughout; movement exaggerated — reason: the character is portrayed as super-powered and "crazy" {tags: keyframe, feedback, exaggeration}
  - [Judgement] Colour arc: starts cool and warms to orange, inspired by "Arrival" — reason: the child brings literal "warmth" {tags: colour-script, grading, lighting}
- **Quotes:** "tried nailing the look in Blender as much as I could so I only had to render out 2 or 3 passes in PNG" — Aiman Samat; "it would take my PC an hour to render a frame (I am using RTX 3070)" — Aiman Samat
- **Depth note:** medium; the winner of the challenge, useful for render-time reality and the in-camera vs. multi-pass trade-off; no settings.

### B-13 · Outrunning Bears, Chasing Dreams: Pavle's Award-Winning Kinetic Rush Journey
- **URL:** https://www.foxrenderfarm.com/news/outrunning-bears-chasing-dreams-pavles-award-winning-kinetic-rush-journey
- **Artist/studio:** Pavle Crnobrnja ("Crnovision"), Belgrade; music-video 3D/VFX background
- **Year:** 2024 (page last edited 30 September 2024)
- **Contest & placement:** Pwnisher "Kinetic Rush" — 3rd place
- **Blender version:** not stated
- **Engine & render settings:** not stated ("The whole scene was created using Blender")
- **Render time & hardware:** not stated
- **Techniques:**
  - [Procedure] Environment: 1. rough blocking; 2. many 3D rock scans for realism; 3. vegetation from the Botaniq add-on, scattered with Geometry Nodes and particle systems; 4. lights added for drama; water simulated in Blender with the FLIP Fluids add-on (steps stated, settings not) {tags: blockout, photogrammetry, scatter-addon, geometry-nodes, particles, flip-fluids, fluid-sim}
  - [Procedure] Animation reference: hundreds of videos of bears running, fighting and playing; parkour and javelin-throw videos for the character's jump and spear throw (keyframing method not stated) {tags: reference, animal-animation, keyframe}
  - [Judgement] Loop and timing rules overrode realism: after a 4–5 m jump into shallow water the character keeps running "to fit the loop"; the first bear stops faster than a real bear could — reason: the challenge's fixed timing and loop {tags: loop, template, realism-tradeoff}
- **Quotes:** "in order to fit the loop, I had to make him keep running." — Pavle Crnobrnja; "I found hundreds of videos of bears running, fighting, and playing." — Pavle Crnobrnja
- **Depth note:** thin-to-medium; kept for the placed-entry account of loop constraints and the scan + scatter + FLIP stack; no settings.

### B-14 · Making a Stop Motion Video with a 3D Animation of Toy Story's Sid
- **URL:** https://80.lv/articles/creating-a-stop-motion-video-with-a-3d-animation-of-toy-story-s-sid
- **Artist/studio:** JuanCarlos CR, Spanish 3D artist based in Tokyo (80.lv interview)
- **Year:** 2026 (article dated 26 March 2026)
- **Contest & placement:** none; personal character piece
- **Blender version:** not stated
- **Engine & render settings:** not stated
- **Render time & hardware:** not stated
- **Techniques:**
  - [Setting] Rig: Rigify for all three characters (Duck, Legs, Sid) — "allows all sorts of custom rigs" (customisation steps not stated) {tags: rigify, character}
  - [Procedure] Texturing in Substance 3D Painter: solid base colour → gradients → surface detail to break up specular highlights; toy plastic and human skin given distinct material looks; models kept in exploded view while baking to avoid projection artifacts (steps stated) {tags: substance, baking, exploded-bake, materials}
  - [Judgement] Look-dev scale test — reason: the toys must read as small objects in a large room, "not just scaled-down characters" {tags: scale, lookdev}
  - [Procedure] Digital stop motion: 1. model and rig a stop-motion character holder ("a rig for the rig"); 2. make the toy the master object and attach the holder and Sid's hands to the toy's hip; 3. move the toy and let the others follow; 4. animate the toy on twos; 5. cycle through 10 hand poses in a loop to mimic an animator's frame-by-frame touches; 6. motion blur on some frames only; 7. slow camera zoom into the scene (steps stated; how "on twos" was set — constant interpolation or keys every 2 frames — not stated) — principle: imitate the physical artifacts of real stop motion {tags: stop-motion, on-twos, stepped, parenting, hierarchy, motion-blur}
- **Quotes:** "I attached the character holder and Sid's hands to the toy's hip." — JuanCarlos CR; "Switching between 10 hand poses in a loop to mimic the frame-by-frame adjustment of a real stop motion animator" — JuanCarlos CR
- **Depth note:** short but procedural on the stop-motion look; no render data.

### B-15 · Kotte Animation Talks Art Style, Blender & the 'Squid Game' Parody
- **URL:** https://80.lv/articles/we-spoke-to-kotte-animation-about-blender-art-style-creating-the-squid-game-parody-video
- **Artist/studio:** Kotte Animation, solo 3D animator and YouTuber, self-taught since 2018 (80.lv interview by Theodore McKenzie)
- **Year:** 2024 (12 November 2024)
- **Contest & placement:** none; widely viewed stylised character parodies
- **Blender version:** not stated
- **Engine & render settings:** not stated
- **Render time & hardware:** not stated
- **Techniques:**
  - [Setting] Rigify for every character since he started; tools named: Dope Sheet, Graph Editor, Motion Paths, Geometry Nodes, modifiers, constraints {tags: rigify, graph-editor, motion-paths, dope-sheet}
  - [Setting] Reusable base characters: Squid Game model (2020) 11,012 polygons; current general human model (early 2022) 18,600 polygons; variants made by editing the same mesh {tags: character, reuse, low-poly}
  - [Procedure] Pose-to-pose: key poses → in-betweens → adjust timing (from The Animator's Survival Kit and the 12 principles) (steps stated) {tags: pose-to-pose, keyframe, timing}
  - [Procedure] Walk cycle: 1. base pose with one foot forward; 2. weight-shift up/down key pose; 3. in-betweens; 4. duplicate the keyframes to continue the cycle; 5. apply them to each character for synchronised group motion; dances adapted onto the walk by keeping the hip sway (steps stated; he duplicates keys rather than naming a Cycles F-curve modifier) {tags: walk-cycle, duplicate-keys, crowd}
  - [Procedure] Shot order: no storyboard; each scene finished in 3–10 s segments; 1. animate characters/objects first; 2. then the camera (rarely static); 3. then tweak the character animation so key movements read within the frame (steps stated) — principle: what the camera sees takes priority {tags: camera, layout, per-shot-polish}
  - [Judgement] Nearly every video synced to the music's tempo — reason: without music he struggles to decide camera transitions and the timing of key poses {tags: music-sync, timing}
- **Quotes:** "I animate characters or objects first, followed by the camera." — Kotte Animation; "Nearly all of my videos are synced with the tempo of the music." — Kotte Animation
- **Depth note:** medium on animation order and walk-cycle construction; nothing on rendering.

## Sources — part C: still-image contests, BoBA, contest interviews, featured work

_C-16 was drafted and then demoted to the excluded list; the number is left unused._

### C-01 · Behind the Scenes: Coming Home
- **URL:** https://www.blendernation.com/2023/11/20/behind-the-scenes-coming-home/ ; forum thread https://blenderartists.org/t/coming-home/1477966
- **Artist/studio:** Thijs de Bruin (bureaubruin)
- **Year:** 2023
- **Contest & placement:** Made for CGMood's "Home" render challenge (placement there not stated); Best of Blender Artists 2023, Landscapes, 1st (grand winner, community vote)
- **Blender version:** 3.5 (forum thread)
- **Engine & render settings:** Cycles (forum thread). Raw image rendered at 4K. Samples, denoiser, light paths, colour management: not stated.
- **Render time & hardware:** not stated
- **Techniques:**
  - [Procedure] 1. Reference board for each aspect of the project. 2. Add a plane, subdivide heavily, sculpt a basic landscape from the camera's viewpoint. 3. Scatter ground vegetation with the Geo-Scatter add-on, Graswald library plants. 4. Place cabin; tree scatters with Forestation add-on trees (scanned trunks, optimised branches). 5. Water = Quixel texture plus "a few bump nodes combined" for ripples. 6. HDRI from Textures.com, brightness slightly reduced. 7. Iterate lighting/composition; add fallen trees and branches via Quixel Bridge. 8. Rebuild cabin in a separate file with photo-scanned materials. (steps stated; node values not stated) — principle: "This scene study proved that I was headed in the right direction" — a study render confirms direction before detailing. {tags: reference, sculpt-terrain, scatter-addon, geo-scatter, graswald, megascans, hdri, study-render}
  - [Setting] Render > Simplify used to cap texture size; "2k will do just fine most of the time" unless close-up. — principle: texture resolution should match framing; saves VRAM. {tags: simplify, texture-resolution, optimisation}
  - [Setting] Camera culling on scatter systems. — principle: remove geometry the camera cannot see. {tags: camera-culling, scatter-addon, optimisation}
  - [Judgement] High-detail meshes in the foreground, low-res in the background. — reason: detail only where the viewer looks; VRAM. {tags: lod, optimisation}
  - [Judgement] Reverted to the original HDRI after trying others — reason: it "gave the preferred look" (by eye). {tags: hdri}
  - [Procedure] Post in Photoshop: PNG cut-outs of animals and a campfire for story; Realpaint FX action; upscale 4× in Topaz Gigapixel, rerun script; vignette and Camera Raw colour/contrast. Animated version composited in DaVinci Resolve. (steps stated, values not stated) {tags: photoshop-post, upscale, vignette}
- **Quotes:** "Use high detail, high resolution meshes in the foreground, but lower resolution meshes in the background." — Thijs de Bruin. "It is not necessary to have 4k textures on each and every model, 2k will do just fine most of the time" — Thijs de Bruin.
- **Depth note:** good on workflow order and optimisation; no render numbers.

### C-02 · Simulating long drips and how to eliminate denoise flicker on vegetation in Blender
- **URL:** https://blenderartists.org/t/simulating-long-drips-and-how-to-eliminate-denoise-flicker-on-vegetation-in-blender/1471832
- **Artist/studio:** Adam (Skovran)
- **Year:** 2023 (posted 4 July 2023)
- **Contest & placement:** Best of Blender Artists 2023, Product Design, 3rd (community vote)
- **Blender version:** not stated
- **Engine & render settings:** 750 samples; Blender's built-in denoiser switched OFF for the final render. Engine not named (sampling + denoiser suggests Cycles; not confirmed).
- **Render time & hardware:** not stated
- **Techniques:**
  - [Procedure] Flicker removal: 1. Final render without Blender denoise. 2. 750 samples. 3. Multi-frame (temporal) Neat Video denoiser. 4. On the final animation in After Effects: Topaz Labs AI denoise. 5. Lumetri Color sharpening in After Effects. (steps stated; per-step values not stated) — principle: flicker comes from "the Blender internal denoiser denoising frame by frame and not looking at multiple frames at once." {tags: flicker, temporal-denoise, denoise-off, post-denoise, animation-consistency}
  - [Judgement] Kept the translucency channel on vegetation despite flicker. — reason: without it flicker is weaker "but then it will look incredibly fake." {tags: translucency, vegetation, flicker}
  - [Setting] Drips simulated with the paid FLIP Fluids add-on; no settings given. {tags: fluid-sim, flip-fluids}
  - (Reply from another user, not the artist: suggests Blender's own Temporal Denoise; the artist had not tried it.)
- **Quotes:** "Vegetation is almost impossible to render out without noise and flicker." — Skovran. "the Blender internal denoiser denoising frame by frame and not looking at multiple frames at once" — Skovran.
- **Depth note:** short post but the only placed entry found that names a flicker workflow; settings for the post tools not given.

### C-03 · Blender Beasts 2017 winner: Eternum Rek'Sai (case study)
- **URL:** https://garagefarm.net/case-studies/interview-blender-beast-winner-jesse-gayanilo
- **Artist/studio:** Jesse Amiel D. Gayanilo
- **Year:** 2017 contest, case study published 31 Jan 2018
- **Contest & placement:** Blender Beasts 2017 (GarageFarm.NET), 1st
- **Blender version:** not stated (article discusses 2.79 features)
- **Engine & render settings:** denoiser and Principled BSDF used (implies Cycles; engine not named). Samples not stated.
- **Render time & hardware:** rendered on GarageFarm render farm; numbers not stated. Sponsor-hosted article.
- **Techniques:**
  - [Judgement] Dropped a furry character and a fully sculpted body — reason: fur sculpting and full-body sculpting too slow for the deadline. Chose a design mixing organic and hard-surface parts. {tags: scope}
  - [Procedure] 1. Sculpt only exposed organic parts (torso, some arm). 2. Box-model armour, tail, head and other hard-surface parts. 3. Retopologise and UV-unwrap the sculpted torso. 4. Muscle-fibre detail only where armour does not cover. 5. Bake normals and AO in xNormal. 6. Texture hard-surface parts with procedural materials. (steps stated) — principle: procedural materials on hard-surface parts save time. {tags: sculpt, box-modeling, retopology, baking, procedural-materials, scope}
  - [Setting] Denoiser on — principle (artist's estimate): output looks like ~1.5× the samples. {tags: denoise}
  - [Judgement] Low camera looking up so the beast reads large; rule of thirds, head near top-right intersection; arms/body as leading lines to the head. — reason: dominance and focus. {tags: composition, camera-height, leading-lines}
  - [Judgement] Backlight from above so the wall behind the head is brightest, fading downward; moved the light after previs showed the left wall pulling the eye to a hand. — reason: "her head is supposed to be the focus." {tags: lighting-for-focus, separation, iteration}
  - [Judgement] Human figures (from BlendSwap) added for scale and emotion. — reason: "show how big the beast is." {tags: scale-figures, storytelling}
- **Quotes:** "This is not ideal because her head is supposed to be the focus." — Jesse Gayanilo. "The scientists and soldiers also show how big the beast is." — Jesse Gayanilo.
- **Depth note:** strong on judgement and scope; render settings absent.

### C-04 · Sky Ship Challenge winners (CG Boost challenge #1)
- **URL:** https://cgboost.com/sky-ship-challenge-winners/
- **Artist/studio:** Jakob Scheidt (1st), Júlio Cargnin Pereira (2nd), Rafael Comino Matas (3rd); jury incl. Zacharias Reinhardt, Aidy Burrows, Julien Kaspar, Gregory Smith, Lukas Walzer, Chris Plush
- **Year:** 2019 (March)
- **Contest & placement:** CG Boost Sky Ship Challenge, 127 submissions; placements as above
- **Blender version:** 3rd place: Blender 2.80; others not stated
- **Engine & render settings:** 2nd place: EEVEE; others not stated
- **Render time & hardware:** 2nd and 3rd: about two weeks of work each; no render times
- **Techniques:**
  - [Procedure] Clouds (1st): paint and composite photos, project onto alpha planes, add volumetrics. (steps stated, values not stated) {tags: cloud-cards, alpha-planes, volumetrics}
  - [Procedure] Clouds (3rd): transparent cloud images on planes, colour management and curves, minimal post. (steps stated) {tags: cloud-cards, alpha-planes, minimal-post}
  - [Setting] 2nd place chose EEVEE "for fast PBR feedback and cloud volume shading", though Cycles would have been preferred "for light consistency". — principle: speed of iteration vs lighting accuracy. {tags: eevee, eevee-vs-cycles}
  - [Procedure] 2nd place split the scene into render passes so unchanged objects did not need re-rendering. (steps not stated) {tags: render-layers, compositor}
  - [Judgement] Jury reasons for winners (verbatim fragments): "calm two-tone color palette" (1st); "great composition and the pleasing use of color and light" (2nd); "a well-chosen and limited color palette" and "subject is nicely separated from the background" (3rd), with criticism of "rough details, shadows, and noise". {tags: jury, limited-palette, separation, story, silhouette}
- **Quotes:** "The calm two-tone color palette helps selling the eccentric design of the ships." — Lukas Walzer (juror). "The great composition and the pleasing use of color and light makes this rendering a winner for me." — Zacharias Reinhardt (juror).
- **Depth note:** jury commentary is the value; artist notes are a few lines each.

### C-05 · Little Traveler Challenge (CG Boost challenge #36)
- **URL:** https://cgboost.com/challenges/little-traveler-challenge
- **Artist/studio:** Dylan Atkins (1st Pro), Leo Semmelmann (2nd), Yaroslav Kovalenok (3rd), Steffen Knothe and Yeremey Moskalev (honourable mentions); jury incl. Zacharias Reinhardt, Daniel Nees, Masha Bazueva, Martin Klekner
- **Year:** 2022 (winners 9 Nov 2022); 259 submissions
- **Contest & placement:** as above
- **Blender version:** Knothe: Blender 3.4; others not stated
- **Engine & render settings:** 1st: EEVEE, comped in After Effects. 2nd: Houdini set dressing + Blender characters + Redshift (not a pure-Blender render). Training-arena entry (Fuhrmann): Cycles.
- **Render time & hardware:** not stated
- **Techniques:**
  - [Setting] Botaniq add-on for trees and grass (Knothe). {tags: scatter-addon, botaniq}
  - [Setting] Stable Diffusion-generated image textures for outfits, banners, carvings (Knothe). {tags: ai-textures}
  - [Judgement] 1:1 aspect ratio, triangular composition; real objects as modelling reference (Simonella, training arena). {tags: composition, aspect-ratio, reference}
  - [Judgement] Jury reasons: 1st "combine great visuals with an interesting story"; 2nd "great mood and atmosphere" (god rays, depth of field); criticisms that recur: "wonky deformations" on a character leg, character looking "like a puppet", image "noisy" (suggests more samples or denoising), water/flatness, missing story. {tags: jury, story, mood, deformation, noise}
- **Quotes:** "What strikes most in this artwork is the great mood and atmosphere." — Zacharias Reinhardt (juror). "Technical wise, this artwork is almost perfect" — Zacharias Reinhardt (juror), on an entry that did not place top-3 because story was missing.
- **Depth note:** jury commentary; artist process notes are one line each.

### C-06 · Rock Buddha
- **URL:** https://www.blendernation.com/2016/05/26/rock-buddha/
- **Artist/studio:** Rence (posted as K1FF)
- **Year:** 2016
- **Contest & placement:** none — BlenderNation featured
- **Blender version:** not stated
- **Engine & render settings:** Cycles, 500 samples. Colour Management: "film emulation" (pre-Filmic film looks), Exposure and Gamma tweaked (values not stated).
- **Render time & hardware:** not stated
- **Techniques:**
  - [Procedure] Material: Diffuse BSDF + Glossy BSDF into a Mix Shader. Poliigon rock maps: Color → Diffuse colour; Gloss → Glossy roughness; Normal → normal of both; Reflection map → Mix Shader Factor. (steps stated) — principle: "The material is as basic as a Diffuse mixed with a Glossy." {tags: shader-mix, pbr-maps, poliigon}
  - [Setting] One mesh light; solid black background; camera 55 mm, full sensor; DoF distance set far as needed, radius tuned by eye. {tags: single-light, dof, camera}
  - [Procedure] Film grain in the compositor: Lens Distortion node with only Jitter enabled → Mix RGB with the pre-jitter image at 0.333 (favouring the clean render). Chromatic aberration: Lens Distortion with Fit enabled, Dispersion ≈ 0.02. Colour Balance after (values not stated). (steps stated) {tags: compositor, film-grain, chromatic-aberration, lens-distortion}
  - [Judgement] "found the sweet spot on the lighting/coloring ... after quite a while of tweaking" — by eye. {tags: iteration}
- **Quotes:** "The material is as basic as a Diffuse mixed with a Glossy." — Rence.
- **Depth note:** short but every value given is concrete; pre-Principled BSDF era.

### C-07 · Behind the Scenes: Corvette C7 Stingray
- **URL:** https://www.blendernation.com/2019/02/15/behind-the-scenes-corvette-c7-stingray/
- **Artist/studio:** Saksham Kumar
- **Year:** 2019
- **Contest & placement:** none — BlenderNation Behind the Scenes feature
- **Blender version:** 2.79 (kept because GPU unsupported by 2.80 and UI unfamiliar)
- **Engine & render settings:** 4K, 2000 samples, denoising on (because of fireflies). Engine not named in text.
- **Render time & hardware:** ~20–30 min per image on GarageFarm render farm; local machine Core 2 Duo E4500, GT430 1 GB, 2 GB RAM (could not render it).
- **Techniques:**
  - [Procedure] 1. Build guide meshes for body panels (smooth surfaces, cut-outs ignored). 2. Model the real panel with cut-outs. 3. Shrinkwrap modifier on the panel targeting the guide mesh so the panel inherits the guide's smooth reflections. 4. Supplementary meshes to smooth or bulge reflections in specific areas (front bumper). (steps stated; subdivision levels not stated) — principle: the guide mesh is "the most helpful technique" for smooth reflections without fussing over cut-out topology. {tags: hard-surface, guide-mesh, shrinkwrap, car, reflections}
  - [Setting] Car paint: Chris Plush's material (orange peel, micro-scratches, metallic flakes, clear coat, base colour controls); no values. HDRI: "Warehouse" from the sIBL archive. {tags: car-paint, hdri}
  - [Judgement] Interior kept bare; shadow planes hide the unmodelled underside. — reason: tedious, and not seen. {tags: model-only-what-camera-sees}
  - [Procedure] Post in Lightroom; lens overlays; dust overlay removed (scaling issues). {tags: lightroom-post, lens-overlay}
- **Quotes:** "using a guide mesh and shrink-wrapping the actual panel to it" — Saksham Kumar (as reported). "The interior was a really bare bones basic one because it is really tedious and tiring to model it." — Saksham Kumar.
- **Depth note:** one clear procedure (guide-mesh shrinkwrap) with reason; render settings partly in screenshots only.

### C-08 · Behind the Scenes: Chocolate Truffles
- **URL:** https://www.blendernation.com/2019/05/24/behind-the-scenes-chocolate-truffles/
- **Artist/studio:** Ioanna Papadopoulou (Studio Clip, advertising illustration)
- **Year:** 2019
- **Contest & placement:** none — BlenderNation Behind the Scenes feature
- **Blender version:** not stated
- **Engine & render settings:** Cycles; 1600 samples ("too many"); camera 35 mm, 1920×1080 at 200 % resolution scale. Bounces, colour management: not stated.
- **Render time & hardware:** not stated
- **Techniques:**
  - [Procedure] Chocolate bar: cube with extra loops → Array modifier to final size → apply Array so the joins work with Subdivision Surface. (steps stated) {tags: array, apply-before-subsurf, subdivision}
  - [Procedure] Chocolate lines on a truffle: draw curves flat over the truffle → Knife Project with Cut Through to create loops → convert loops to curves → extrude. Crossing lines: extrude each direction separately, join, Bridge Edge Loops + Subdivision to smooth joints. (steps stated) {tags: knife-project, curves, bridge}
  - [Procedure] Sprinkles: displaced cube base → hair particle system rendering a Group of line objects of varied size → make real → Shrinkwrap onto the cube with slight offset → convert to curve, bevel → back to mesh → fill holes → Bevel (angle limit) + Subdivision + Smooth modifiers. (steps stated) {tags: particles, shrinkwrap, bevel}
  - [Procedure] Drops: paint a density texture on a plane → hair particles emit drop objects → convert to real objects → active Rigid Body, passive rigid floor, low-res obstacle objects → simulate, then adjust positions by hand. (steps stated) — principle not stated beyond natural placement. {tags: rigid-body, physics-placement, particles}
  - [Setting] Chocolate shader: Principled BSDF with BlenderDiplom "Scale SSS" setup; Pointiness mixed into subsurface colour to define subsurface at bar edges; marbling by distorted Noise with its own Mapping; cocoa via Noise "labyrinth" + Voronoi into Colour, Roughness/Specular and Bump. (values not stated) {tags: sss, pointiness, procedural-materials}
  - [Setting] Key light: a softbox HDR image plugged into a light's Colour input. Back/top light: plain Emission shader with Light Falloff (Quadratic) into Strength — "adds fill and reveals subsurface" while falloff keeps parts dark. (values not stated) {tags: textured-light, light-falloff, backlight-for-sss}
  - [Procedure] Post outside Blender: raise exposure/gamma slightly; Photoshop denoise only on selected areas; blur background in Photoshop. {tags: photoshop-post, selective-denoise}
- **Quotes:** "Search for the similarities, not the differences!" — Ioanna Papadopoulou (on moving from Maxwell to Cycles). "I used 1600 samples (too many) but, even at that number, some denoising in selected areas had to be done inside Photoshop." — Ioanna Papadopoulou.
- **Depth note:** rich modelling procedures; shading named but no values.

### C-09 · Hardcore Henry – using Blender for VFX
- **URL:** https://www.blendernation.com/2016/05/05/hardcore-henry-using-blender-vfx/ (repost of a blender.org user story; original blender.org page refused automated fetch)
- **Artist/studio:** Yaroslav Kemnits, Division LLC (Moscow), on-set VFX supervisor
- **Year:** 2016 (film released 2015/16)
- **Contest & placement:** none — feature-film showcase
- **Blender version:** not stated
- **Engine & render settings:** not stated (Sun + Hemi lamps imply the pre-2.8 era; engine not confirmed)
- **Render time & hardware:** not stated
- **Techniques:**
  - [Procedure] Free-fall through clouds: 1. Build a cloud with the Cloud Generator add-on. 2. Animate a six-camera unit descending to the cloud's edge. 3. Add turbulence on entry; carve cave-like hollows inside the cloud "to make the fall more visually interesting". (steps stated, values not stated) {tags: volumetrics, clouds, camera-rig}
  - [Judgement] Lighting = Sun + Hemi (sky) only; renders compared against real GoPro footage. — reason: match the real camera's look. {tags: reference-footage, two-light-sky}
  - [Procedure] On set: a "white room" with programmed luminaires around the pod moved sunlight across the actor's face during rotation, matching the CG. (steps not stated) {tags: lighting-match, vfx}
  - [Procedure] City plate: drone with a six-GoPro rig → footage synchronised and laid onto a cube → camera mapping to fake greater height than the drone could fly (374 m limit). (steps stated) — principle: camera projection buys height the plate does not have. {tags: camera-mapping, projection, vfx}
  - [Setting] Parachute: Round Canopy model enlarged slightly "so it would not look too small"; Cloth simulation with a Wind force; needed on screen ~1 s. {tags: cloth-sim, wind, scale-cheat}
  - [Setting] Destruction with the Fracture Modifier (custom Blender branch). {tags: destruction, fracture-modifier}
- **Quotes:** "It is a very flexible tool." — Yaroslav Kemnits. "The scene was illuminated by two sources of light – Sun and Hemi (sky)." — Yaroslav Kemnits.
- **Depth note:** good procedure outlines, no numbers; old-engine era.

### C-10 · Making of House 59
- **URL:** https://www.ronenbekerman.com/making-of-house-59/
- **Artist/studio:** 77 Studio (Medellín)
- **Year:** 2020
- **Contest & placement:** none — Ronen Bekerman blog making-of (professional archviz showcase)
- **Blender version:** not stated
- **Engine & render settings:** Cycles; settings not stated. Compositing mainly in Blender; minimal Photoshop colour correction.
- **Render time & hardware:** not stated
- **Techniques:**
  - [Judgement] Re-modelled the whole SketchUp import in Blender — reason: "the mesh did not give us the results we wanted" (topology). {tags: remodel-imports, topology}
  - [Procedure] Wood slats as geometry: one slat → Array modifier → move UVs per slat to remove visible repetition; same for floors. (steps stated) — "we decided to model the wood slats and not use a texture". {tags: array, uv-offset, anti-repetition, model-dont-texture}
  - [Setting] Bevel modifier on planes/cubes to soften edges. {tags: bevel}
  - [Procedure] Vegetation: particles first; scenes too heavy; linking vegetation files gave a repeating pattern; manual placement looked poor → bought the Scatter add-on (proxies + grass biomes) for trees/bushes/grass. A plane with a photo of the real site closes the view behind the trees. (steps stated) — principle: memory optimisation was "one of the biggest lessons". {tags: scatter-addon, proxies, backdrop-photo-plane, optimisation}
  - [Setting] Interior: very pale HDRI for a cool atmosphere plus IES lights. Exterior: several HDRIs tested (PG Skies, Poliigon, HDRI Haven). {tags: hdri, ies}
  - [Judgement] Photo-scanned PBR materials preferred "for realism"; colour/fit adjusted in Cycles. {tags: scanned-materials, megascans}
- **Quotes:** "we decided to model the wood slats and not use a texture" — 77 Studio. "One of our goals with this project was to demonstrate all the capabilities that Blender has" — 77 Studio.
- **Depth note:** solid procedures and reasons; no render numbers.

### C-11 · Interview with Ben White, top winner in the Ultimate Race Track Challenge
- **URL:** https://www.foxrenderfarm.com/news/interview-with-ben-white-top-winner-in-the-ultimate-race-track-challenge
- **Artist/studio:** Ben White (hobbyist)
- **Year:** challenge year not stated; page last edited 2024-12-13
- **Contest & placement:** polygoniq Ultimate Race Track Challenge, 1st (animation under one minute, one-month deadline)
- **Blender version:** not stated
- **Engine & render settings:** Cycles, output as EXR sequences; colour grading in DaVinci Resolve instead of Blender compositing. Samples/motion blur/fps not stated.
- **Render time & hardware:** not stated (Fox Renderfarm used)
- **Techniques:**
  - [Procedure] 1. Storyboards and gray-box layouts first. 2. Model each racer as far as time allows (HardOps add-on). 3. Kitbash to fill gaps (Ian Hubert greebles, Big Medium Small industrial kit, Botaniq trees). 4. Crowd with the Population add-on. 5. Textures.com bases + procedural dirt and edge wear in Blender; procedural team liveries. 6. Render Cycles to EXR sequence. 7. Grade in Resolve. (steps stated) — principle: storyboards and gray-box layouts prevent wasted effort on details irrelevant to the shot. {tags: storyboard, grey-box, kitbash, hardops, population-addon, exr-sequence, resolve-grade, procedural-wear}
  - [Judgement] Modelled only the first quarter of the track — reason: the animation covers the race start; scope to the shot. {tags: model-only-what-camera-sees, scope}
  - [Judgement] Worked at accurate real-world scale — reason: faking scale "would not produce believable results"; but viewport control at that scale was his biggest difficulty. {tags: real-scale}
  - [Judgement] Details "placed with intention, have a function, and be explainable by the narrative of your world"; avoid garish lights on futuristic designs. {tags: purposeful-detail, design}
- **Quotes:** "Details should be placed with intention, have a function, and be explainable by the narrative of your world." — Ben White. "Always keep references at the forefront of your designs." — Ben White.
- **Depth note:** good on method and judgement; render numbers absent.

### C-12 · The Ruins Challenge, 1st place: "Anuket" (interview)
- **URL:** https://www.foxrenderfarm.com/news/unveiling-the-architect-of-ruins-dylan-1st-place-winner-of-the-ruins-challenge/
- **Artist/studio:** Dylan Donaldson
- **Year:** 2024 (page date 2024-09-27)
- **Contest & placement:** FGT3D The Ruins Challenge (Fox Renderfarm), 1st, professional category
- **Blender version:** not stated
- **Engine & render settings:** Cycles; samples, denoiser, motion blur not stated. 220 frames.
- **Render time & hardware:** ~36 hours locally for 220 frames (~10 min/frame) on one RTX 4090, i9-12900K, 64 GB DDR5; scene "quite unoptimised".
- **Techniques:**
  - [Setting] Albedo map reused as a Bump map on top of the normal map for micro-detail. {tags: albedo-as-bump, micro-detail}
  - [Procedure] Simulations (including a fat/muscle sim on the camel) done in Houdini and exported into Blender; all rendering in Blender. Terrain tools listed: Gaea, Liquigen (uses not stated). (steps not stated) {tags: houdini-to-blender, sim-cache, muscle-sim}
  - [Procedure] Camel walk: trace a reference video of a walking camel; simple FK rig (which he felt "did not help"). {tags: reference-video, fk-rig, animal-animation}
  - [Judgement] Characters in shadow, city lit as focal point — reason: the viewer feels like a traveller, interested in the city not each other. Slow waterfall and haze to sell scale. Handheld-like camera shake kept though not physically consistent — "felt right compositionally". {tags: lighting-for-focus, scale-cues, haze, camera-shake}
  - [Setting] Texture blending and painting for sand on the road. {tags: texture-blending}
- **Quotes:** "I think it's a good idea to treat a render challenge as a personal project too for self-improvement." — Dylan Donaldson. "The most challenging part of the project for me was making the camel animation feel real." — Dylan Donaldson.
- **Depth note:** moderate; one of few sources with frame count, render time and hardware for an animation.

### C-13 · Enes Aksakal's beat-synced kitchen ("Octo Beat"), 2nd place in DRÆM SEQUENCE
- **URL:** https://www.foxrenderfarm.com/news/enes-aksakal-s-beat-synced-kitchen-cooks-up-2nd-place-in-draem-sequence/
- **Artist/studio:** Enes Aksakal (Mantaframe)
- **Year:** challenge year not stated (page edited 2026-05-19); DRÆM SEQUENCE is Pwnisher's 12th community challenge, visualising a 120 BPM beat (per B-11)
- **Contest & placement:** Pwnisher DRÆM SEQUENCE, 2nd
- **Blender version:** not stated
- **Engine & render settings:** EEVEE (his first use; previously only Cycles). Settings not stated.
- **Render time & hardware:** not stated
- **Techniques:**
  - [Procedure] Four-week plan: wk 1 ideation, references, initial blockouts for composition and timing; wk 2 refine blockouts, camera movement, pacing; wk 3 animation and simulation, syncing to the beat; wk 4 texturing, lighting, rendering. (stated) — principle: look-dev comes last, timing first. {tags: blocking, animatic, schedule, timing-first}
  - [Judgement] Hold certain poses for a few frames on the beat — reason: "reinforce the rhythm and clarity"; 2D timing conventions (WarioWare, Rhythm Heaven) translated to 3D. {tags: holds, timing, readability}
  - [Setting] Cloth and stove flames simulated in Marvelous Designer (flames for a stop-motion feel); texturing in 3DCoat. {tags: cloth-sim, external-sim}
  - Beat-sync method in Blender (drivers, sound baking, keyframes): not stated.
- **Quotes:** "Using techniques like holding certain poses for a few frames helped reinforce the rhythm and clarity." — Enes Aksakal.
- **Depth note:** schedule and timing judgement only; no settings. Same challenge as B-11 (3rd place), different entry.

### C-14 · Fox's Got Talent February winner: astronauts' escape
- **URL:** https://foxrenderfarm.com/news/foxs-got-talent-february-winner-revealed-3d-astronauts-escape-story-made-in-blender
- **Artist/studio:** Sai Dinesh Komanduri
- **Year:** 2022 (article 2022-07-04); idea from the CG Boost "Space Carrier" theme
- **Contest & placement:** Fox's Got Talent, monthly winner (February)
- **Blender version:** 2.82 (modelling)
- **Engine & render settings:** Cycles, 300 samples, an AI denoise add-on applied in compositing (name not stated).
- **Render time & hardware:** not stated; 4 days total work
- **Techniques:**
  - [Setting] Rigify basic rig used only to pose the characters for a still. {tags: rigify, posing}
  - [Setting] Lighting = HDRI + reflection planes + emission planes for soft light. {tags: hdri, emission-planes, reflection-planes}
  - [Judgement] Orange rocket where references were white — reason: cartoon style; colour by instinct, no preset palette. {tags: colour-choice}
  - [Procedure] Build each asset individually, then assemble "as a puzzle". (stated) {tags: asset-first}
- **Quotes:** "I always think to keep the artwork simple but it has to also tell a story." — Sai Dinesh Komanduri.
- **Depth note:** moderate-thin; stylised still.

### C-15 · Architecture Academy Contest results (Blender Guru)
- **URL:** https://www.blenderguru.com/posts/internal-architecture-academy-contest
- **Artist/studio:** winners Ross Franks (Interiors), Marcus Pinto and Luca Buono (Exteriors, joint); judge commentary unattributed (Blender Guru)
- **Year:** late 2013 / early 2014 (post dated 15 Nov; academy reopening April 2014)
- **Contest & placement:** Blender Guru Architecture Academy members' contest; winners above
- **Blender version / engine / settings / time:** not stated
- **Techniques:**
  - [Judgement] Jury reasons: interiors winner — "Everything from the lighting, modelling and materials are excellent", central stairwell as focal point; exteriors — "realism and great control over the lighting and palette"; "subtle grunge, individual wood planks and perfect grass". {tags: jury, palette, focal-point, subtle-grunge, model-dont-texture}
- **Quotes:** "The subtle grunge, individual wood planks and perfect grass push this scene over the edge." — Blender Guru judges. "The realism and great control over the lighting and palette really makes this stand out." — Blender Guru judges.
- **Depth note:** jury commentary only; kept for year coverage and the winners-vs-others question.

### C-17 · Blitter discusses creating those photoreal renders in Blender
- **URL:** https://80.lv/articles/blitter-dicsusses-creating-those-photoreal-renders-in-blender/ (forum thread: https://blenderartists.org/t/newest-photoreal-renders/1290285)
- **Artist/studio:** Blitter
- **Year:** 2021 (interview 6 April 2021)
- **Contest & placement:** Best of Blender Artists 2021, Characters, 2nd (community vote)
- **Blender version:** started on 2.80; version for these renders not stated
- **Engine & render settings:** Cycles, ~600–1200 samples, some grain kept on purpose. Bounces, denoiser, colour management: not stated.
- **Render time & hardware:** 1080×1200 in ≤10 min at ~1000 samples; Ryzen 3900X, RTX 2080 Ti 11 GB (VRAM-limited; Render > Simplify needed to fit two characters).
- **Techniques:**
  - [Procedure] Characters: 1. Modify a Daz Genesis 8.1 base in Daz Studio. 2. Import to Blender with the Diffeomorphic Daz importer. 3. Sculpt tweaks in Blender, including deliberate asymmetry. 4. Bring in the Daz/TexturingXYZ texture set and hand-paint bump, specular and reflectivity variation, blemishes, colour patches, moles. 5. One UDIM material for the whole body (eyes, teeth apart). (steps stated) {tags: daz-import, sculpt, asymmetry, texture-painting, udim}
  - [Judgement] Faint non-obvious colour blotches (blues, greens) on chest, head and legs; tan lines; saturation variety. Skin spec and reflectivity "very subtle". — reason: "in real life, people just are not that shiny". {tags: skin, colour-variation, low-spec}
  - [Judgement] Clutter, variety, imperfection: never exact 90°/180° rotations on furniture (e.g. 93.32°, 175.4°); cables, socks, bottles, laundry. — reason: lived-in look. {tags: imperfection, rotation-jitter, clutter}
  - [Setting] Lighting = a single spot or area light with transforms matched to the camera (an on-camera flash). — reason: mimics selfie/amateur photos, even light with no hard shadows on face/body; downside: shadows hide directly behind objects; outdoor light harder. {tags: camera-flash-light, single-light}
  - [Procedure] Framing with View > Align View > Camera to View (frame through the viewport); low, selfie-like angles, slight tilt, odd crops, subtle foreground DoF. (stated; values not stated) {tags: camera-imperfection, tilt, crop, dof}
  - [Procedure] Post: Photoshop Selective Color to tint blacks blue; for "low-quality photo" looks, save a low-quality JPEG. {tags: photoshop-post, jpeg-degrade, photo-mimicry}
- **Quotes:** "I think that composition is key." — Blitter. "Don’t overdo it though, in real life, people just are not that shiny." — Blitter.
- **Depth note:** rich on judgement and lighting principle; shading values absent.

### C-18 · Solstice-5: designing environments for a sci-fi movie in Blender
- **URL:** https://80.lv/articles/solstice-5-designing-environments-for-a-sci-fi-movie-in-blender
- **Artist/studio:** Paul Chadeisson (with Lambert Grand, co-writer; Alban Kasikci, compositing; Pierre Lazarevic, two shots + UI)
- **Year:** 2024 (interview 2 Jan 2024)
- **Contest & placement:** none — short film showcase
- **Blender version:** not stated
- **Engine & render settings:** Cycles, 4K; post and edit in After Effects. Samples etc. not stated.
- **Render time & hardware:** one or two 4K scenes per day while doing other work; workstation with three RTX 4090.
- **Techniques:**
  - [Procedure] 1. Animate a test (aircraft carriers) to check Blender gives interesting results. 2. Write the story. 3. Build a kit of 3D assets to kitbash "like Lego parts". 4. Ships: 2D line sketches first, model once settled. 5. Per environment, work "like a photographer": camera angle, lens, lighting, mood per shot. 6. Later add live-action interviews (green screen + matte painting). (steps stated) {tags: kitbash, sketch-first, shot-by-shot-framing, green-screen}
  - [Setting] Sky Texture node in Cycles for light and atmosphere in most scenes; the sun can be keyframed (e.g. timelapse). Values not stated. {tags: sky-texture, nishita, animated-sun}
  - [Setting] Fog in most scenes — "Blender renders fog quickly" (artist's claim). {tags: volumetrics, fog}
  - [Judgement] Future should look bigger than today — reason: humans build that way; scale drives drama. Little lighting work beyond the sky — focus on believable designs. {tags: scale, design}
- **Quotes:** "For most of the scene, I used the sky texture node within Blender Cycles to set up the light and atmosphere." — Paul Chadeisson. "Having three 4090 GPUs made it much easier to render scenes." — Paul Chadeisson.
- **Depth note:** good production outline; no settings.

### C-19 · Behind the Scenes: Lukas Walzer – Khalau
- **URL:** https://www.blendernation.com/2017/09/28/behind-scenes-lukas-walzer-khalau/
- **Artist/studio:** Lukas Walzer
- **Year:** 2017
- **Contest & placement:** ArtStation challenge "Beyond Human" entry; placement not stated
- **Blender version / engine / settings / time / hardware:** not stated
- **Techniques:**
  - [Procedure] 1. References on Pinterest. 2. Block out basic shapes in Blender and render them. 3. Photobash and overpaint the blockout render in Photoshop to explore the look. 4. Refine the blockout following the paint-over. 5. Fix the final camera and a basic environment early. 6. Paint further details in Photoshop, then model them. 7. Model "one part after the other", HardOps for quick details. (steps stated) — principle: fixing camera and environment early "gives me the certainty that my work will look good in the end" (an earlier project lost weeks searching for lighting late). {tags: blockout, paint-over, camera-first, hardops}
  - [Judgement] Chose an organic, Giger-like biomech instead of a hard-surface mech — reason: his hard-surface skills were weaker than competitors'. {tags: scope, play-to-strengths}
- **Quotes:** "I think, art challenges are a great way (if not the greatest) to improve." — Lukas Walzer. "it gives me the certainty that my work will look good in the end" — Lukas Walzer.
- **Depth note:** good order of work; no technical values.

### C-20 · Best of Blender Artists winner threads, sampled (2021–2024)
- **URLs:** https://blenderartists.org/t/these-are-the-winners-of-the-best-of-blender-artists-2021/1350993 ; https://blenderartists.org/t/these-are-the-winners-of-the-best-of-blender-artists-2023/1509638 ; https://blenderartists.org/t/these-are-the-winners-of-the-best-of-blender-artists-2024/1578497 ; plus the ten entry threads below
- **Artist/studio:** various; organiser Bart Veldhuizen (BlenderNation / Blender Artists)
- **Year:** 2021–2024
- **Contest & placement:** BoBA, top 5 per category by community vote (12 categories; votes boosted from social media removed in 2023; ties cut by likes in 2021)
- **What the threads state (all the process text there is):**
  - BoBA 2024 Product, 1st — Leica M2 (sempervirent, Jan 2024): Blender 4.0 + Substance Painter + Photoshop; "I'm just using high contrast in AgX and exporting my renders in png, nothing fancy." {tags: agx, agx-high-contrast, substance}
  - BoBA 2024 Interior, 1st — Kitchen 3d render (Gidiman, Jan 2024): "I used volumetrics but it's a small cube close to the window"; the cube covers the whole window and is "extruded ... to follow the sun direction"; render "Around two to three days" (unclear whether that means render or project time). {tags: volume-cube, local-volume, god-rays}
  - BoBA 2023 Landscapes, 1st — Coming Home: see C-01 (Blender 3.5, Cycles).
  - BoBA 2023 Product, 3rd — denoise flicker thread: see C-02.
  - BoBA 2023 Characters, 1st — The Barbershop Project (aendom, June 2023): Blender 3.5 + Substance Painter 2022; "Hair Particles using Medusa Nodes, Geometry Nodes, Render Passes, and Light Groups". {tags: medusa-nodes, hair-curves, light-groups}
  - BoBA 2021 Characters, 3rd — Macro facial renders (Kent Trammell, Nov 2021): "I only used Blender to create everything from scratch"; only change from his course head was "the amount of vellus hairs"; macro views chosen to "stress-test the details up close". {tags: vellus-hair, macro-test}
  - BoBA 2021 Characters, 2nd — Blitter: see C-17.
  - BoBA 2023 Animation, 1st (Nick Is Playin' Video Games), BoBA 2024 Animation, 1st (Drive: "all done entirely in blender"), BoBA 2023 Animation, 4th (commercial, "100% done on Blender"), BoBA 2023 VFX, 2nd (Detritus: "rough digital double and a complete digital recreation of the set"), BoBA 2024 Vehicles, 1st (Toyota Corolla: "the look of a bygone era"): no settings or steps.
- **Finding:** the animation winners' threads carry no process text at all. The vote rewards the finished image or film, and the threads are a gallery.
- **Depth note:** thin per thread; kept as one source because the sample itself is the evidence for the winners-vs-others question.

### C-21 · Breakdown: creating a realistic sci-fi shot fully in Blender
- **URL:** https://80.lv/articles/breakdown-creating-realistic-sci-fi-shot-fully-in-blender
- **Artist/studio:** Karl Poyzer (former live-action cinematographer)
- **Year:** 2025 (6 Aug 2025)
- **Contest & placement:** none — featured work
- **Blender version:** not stated
- **Engine & render settings:** Cycles, 4K; render split into View Layers. Samples, colour management: not stated.
- **Render time & hardware:** animation took about an afternoon; rendering the passes "most of the following day"; hardware not stated.
- **Techniques:**
  - [Procedure] 1. Build the ships' lower section first, leave it a few hours, add a larger top shape; design from the low camera view that looked best. 2. Kitbash from his own asset library. 3. Place ships as collection instances, not duplicates, to cut render load. 4. Light while building to see where shadows fall and where detail is worth adding. 5. Cube-project image textures (collage of metal photos) with colour tweaks in nodes + AO; low reflectivity. 6. Split into View Layers: ground, background, orb, ships, fog. 7. HDRI key + orange lights rising from trenches; one volumetric cube over the whole scene on its own pass. 8. Render 4K Cycles. 9. Assemble passes and grade in DaVinci Resolve. (steps stated, values not stated) — principle: no detail where it won't be seen; "if it looks right there, leave it there". {tags: collection-instances, light-while-modelling, box-projection, view-layers, volume-cube, fog-pass, resolve-grade, kitbash}
  - [Judgement] 20+ lighting setups tried per scene; ships placed to balance the frame with sky visible through the formation, by feel. {tags: lighting-iteration, composition}
  - [Judgement] Simple textures and shadows carry large objects; close-ups would need more detail. {tags: detail-by-distance}
- **Quotes:** "Lighting is probably the place I feel most comfortable, so I will often experiment with 20+ lighting setups per scene." — Karl Poyzer. "Artistically, the principle was, if it looks right there, leave it there." — Karl Poyzer.
- **Depth note:** clear ordered procedure for a fast animated shot; no numeric settings.

## Analysis

### 0. What the set is

There are 49 sources counted. Part A has 15, part B has 15 with Flow counted once across A-07 and B-06, and part C has 20 after C-16 was demoted. By kind:

- **Productions and films (17):** A-01 to A-15, C-09 (Hardcore Henry), C-18 (Solstice-5).
- **Placed or winning contest entries in the artist's own words (15):** B-01, B-03, B-09, B-10, B-11, B-12, B-13, C-01, C-02, C-03, C-11, C-12, C-13, C-14, C-17.
- **Entries that took part but did not place, or were finalists only (5):** B-02, B-04, B-07, B-08, C-19.
- **Featured, non-contest work (8):** B-05, B-14, B-15, C-06, C-07, C-08, C-10, C-21.
- **Jury or thread evidence (4):** C-04, C-05, C-15, C-20.

The years run from late 2013/early 2014 (C-15) to 2026. The spread is uneven: 8 sources come from before 2019, 5 from 2019–2020, and 36 from 2021–2026. This matters for every trend below. The early years are thin because written making-ofs from that period are mostly gone, moved behind logins, or were always video (see the excluded lists).

Most sources state procedures and judgements, and few state numbers. Only 8 of 49 give a sample count, 7 name a denoiser choice, and 7 name a colour-management setting. For an agent, the guide can lean on these sources for *what to do in what order*. It cannot lean on them for *what value to type*, except in a handful of deep sources: A-02, A-10, C-06, C-08, and A-01 for method.

### 1. Tally: how many sources state each technique

Counts are distinct sources, never mentions. Years are those of the sources, which are not always the year a technique arrived in Blender.

**Engine and render settings**

| Technique | n | Sources (year) |
|---|---|---|
| Cycles named as the final engine | 17 | A-14 (2015), C-06 (2016), A-05 (2017), A-15 (2018), C-08 (2019), C-10 (2020), A-01, A-02, A-03, C-17 (2021), C-14 (2022), C-01 (2023), B-05, C-11, C-12, C-18 (2024), C-21 (2025) |
| EEVEE named as the final engine | 11 | B-04, C-04 (2019), B-09 (2021/22), A-06, A-10, C-05 (2022), A-08 (2023), A-07/B-06, B-10 (2024), A-09 (2025 post on the 2023 film), C-13 (≈2026) |
| EEVEE for blocking/previs, Cycles for the final | 1 | B-05 (2024); also Ian Hubert's Dynamo Dream in an excluded news post |
| Engine not named at all | ≈15 | most placed Pwnisher entries (B-01, B-02, B-03, B-07, B-08, B-11, B-12, B-13), B-14, B-15, C-07, C-15, C-19, and others |
| Sample count stated | 8 | C-06 500 (2016); C-08 1600, C-07 2000 (2019); A-02 200, C-17 600–1200 (2021); C-14 300 (2022); C-02 750 (2023); B-03 450 (2025) |
| Denoiser choice stated | 7 | C-03 2.79 denoiser (2017); C-07 denoise for fireflies, C-08 Photoshop on selected areas (2019); A-01, A-02 OIDN (2021); C-14 AI add-on in compositing (2022); C-02 built-in denoiser off, temporal denoise in post (2023) |
| Colour management stated | 7 | C-06 film-emulation looks (2016); A-02 Filmic (2021); B-02 Filmic sRGB, A-06 Filmic + linear (2022); C-20 AgX High Contrast (2024); B-08 32-bit ACES (2024); A-13 HDR PQ/HLG grade in the VSE (2026) |
| Motion blur rendered, with a stated cost or setting | 8 | A-05 (2017), A-15 (2018), A-06, A-10, B-02 (2022), A-04 (2023), B-10 (2024), B-14 (2026) |
| Per-frame or total render time for an animation | 13 | A-14 (2015), A-05 (2017), B-04 (2019), A-06, A-10, B-02 (2022), A-07, B-12, C-12, C-18 (2024), B-01, B-03, C-21 (2025) |
| Render farm used | 10 | A-14 (2015), A-05, C-03 (2017), C-07 (2019), B-07 (2022), A-04, A-06 (2022–23), B-12, C-11 (2024), B-11 (2026) |

**Building the scene**

| Technique | n | Sources (year) |
|---|---|---|
| Block out first and fix the camera/composition before detail | 12 | C-19 (2017), C-01 (2023), A-07, B-05, B-12, B-13, C-11 (2024), B-01, B-03, C-21 (2025), B-11, C-13 (≈2026) |
| Detail or model only what the camera sees; cull the rest | 7 | C-03 (2017), C-07, B-04 (2019), C-01 (2023), C-11 (2024), B-01, C-21 (2025) |
| Scanned material/asset libraries (Megascans, Poliigon, Textures.com, rock scans) | 7 | C-06 (2016), B-04 (2019), C-10 (2020), B-07 (2022), C-01 (2023), B-13, C-11 (2024) |
| Scatter add-on (Scatter/Geo-Scatter, Botaniq, Forestation, Graswald, Population) | 6 | C-10 (2020), C-05 (2022), C-01 (2023), A-07, B-13, C-11 (2024) |
| Particle system for scatter, rain or debris | 5 | C-08 (2019), C-10 (2020, then replaced), B-02 (2022), B-13 (2024), B-01 (2025) |
| Geometry Nodes used for anything | 10 | A-01 (2021), B-07 (2022), A-04, A-08, C-20 (2023), A-07, A-12, B-05, B-13 (2024), B-03 (2025). None before 2021. |
| Kitbash from a personal or bought kit | 5 | B-12, C-11, C-18 (2024), B-03, C-21 (2025) |
| Instancing (collection or GN instances) to keep scenes light | 4 | B-02 (2022), B-08 (2024), B-03, C-21 (2025) |
| Own photogrammetry with a phone | 3 | B-02 KIRI Engine (2022), B-01 Scaniverse (2025), B-11 head scan (2026) |
| Photo projection (camera mapping, UV Project, box projection) | 5 | C-09 (2016), A-01 (2021), B-07 (2022), B-01, C-21 (2025) |
| Imperfection placed on purpose (rotation jitter, crooked parts, grunge) | 3 | C-15 (2013/14, jury), C-17 (2021), B-03 (2025) |

**Lighting**

| Technique | n | Sources (year) |
|---|---|---|
| HDRI as the base light | 8 | C-07, B-04 (2019), C-10 (2020), A-02 (2021), C-14 (2022), C-01 (2023), B-03, C-21 (2025) |
| Volumetrics of any kind | 11 | C-09 (2016), C-04 (2019), A-02 (2021), A-10, B-02 (2022), B-10, C-18, C-20 (2024), B-01, B-03, C-21 (2025) |
| …of which a *cube with a volume shader* is named | 6 | A-02 (2021), B-02 (2022), C-20 Kitchen (2024), B-01, B-03, C-21 (2025) |
| Character lit separately from the set (own key/rim, lights parented to the character) | 5 | C-03 (2017), A-02 (2021), B-10 (2024), B-01, A-09 (2025) |
| Shared light rig or stored light values per sequence | 4 | A-03 (2021), A-10 (2022), A-04 (2023), A-09 (2025) |
| Ray-visibility / Light Path tricks (shadow casters invisible to camera; camera-only background) | 2 | A-02, A-03 (2021) |
| Many lighting setups tried, few kept | 5 | C-06 (2016), C-03 (2017), A-02 (2021), B-10 (2024), C-21 (2025) |

**Splitting the image and finishing it**

| Technique | n | Sources (year) |
|---|---|---|
| View layers or passes rendered separately for compositing | 9 | C-04 (2019), B-07 (2022), A-08 (2023), A-12, B-05, B-08, B-12 (2024), A-09, C-21 (2025) |
| EXR / multilayer EXR output | 7 | A-03 (2021), A-04 (2023), B-05, B-08, B-12, C-11 (2024), B-03 (2025) |
| Light Groups to rebalance lights after render | 3 | C-20 (2023), B-05, B-12 (2024) |
| Cryptomatte | 3 | A-15 (2018), B-09 (2021/22), B-03 (2025) |
| Grade/composite outside Blender (Resolve, After Effects, Nuke, Fusion) | 10 | B-09 (2021/22), B-07, C-05 (2022), C-01 (2023), B-08, B-10, B-12, C-11, C-18 (2024), C-21 (2025) |
| Grade/composite inside Blender (compositor or VSE) | 7 | C-06 (2016), C-10 (2020), A-09 (2023 film), B-05, B-10 (real-time compositor glow) (2024), B-03 (2025), A-13 (2026) |
| Look finished in the render, little or no compositing | 3 | A-10 (2022), A-07, B-12 (2024) |
| Still finished in Photoshop or Lightroom | 6 | C-19 (2017, paint-over), C-04, C-07, C-08 (2019), C-17 (2021), C-01 (2023) |
| Lens artefacts added on purpose (grain, CA, distortion, vignette, overscan) | 6 | C-06 (2016), C-07 (2019), C-01 (2023), B-08 (2024), B-01, B-03 (2025) |

**Simulation**

| Technique | n | Sources (year) |
|---|---|---|
| Cloth done in Marvelous Designer | 5 | B-04 (2019), B-07 (2022), B-01 (2025), B-11 (2026), C-13 (≈2026) |
| Cloth done in Blender | 2 | C-09 (2016), A-15 (2018) |
| Effects faked instead of simulated (volume cube, GN effector, scaled sphere, procedural water) | 4 | A-07, B-10 (2024), B-01, B-03 (2025) |
| FLIP Fluids add-on | 3 | C-02 (2023), A-07, B-13 (2024) |
| Simulations made in Houdini and brought into Blender | 3 | A-15 (2018), B-12, C-12 (2024) |
| Simulation baked to cache before render | 3 | B-02, B-07 (2022), A-07 (2024) |

**Animation**

| Technique | n | Sources (year) |
|---|---|---|
| Rig system named (CloudRig, Rigify, Auto-Rig Pro, Mixamo, simple FK) | 8 | B-04 Mixamo (2019), B-02 Mixamo, C-14 Rigify (2022), A-04 CloudRig (2023), B-05 Auto-Rig Pro, B-15 Rigify, C-12 FK (2024), B-14 Rigify (2026) |
| Mocap (body or face) | 4 | B-04 (2019), B-02, B-07 (2022 template), B-11 (2026 face) |
| Reference video for motion | 3 | A-07, B-13, C-12 (2024) |
| Key poses first (constant/stepped interpolation), then in-betweens and polish | 4 | A-04 (2023), B-10, B-15 (2024), C-13 (≈2026) |
| Camera adjusted after the first animation pass | 2 | A-07, B-15 (2024) |
| Holds and timing set to a beat | 3 | B-15 (2024), B-11, C-13 (≈2026) |
| Procedural motion (sine F-curve modifier, Evaluation Time shape keys, GN) | 2 | B-07 (2022), B-03 (2025) |

**Frame-to-frame consistency**

| Technique | n | Sources (year) |
|---|---|---|
| Flicker or jitter named as a production problem | 4 | A-01 (2021), C-02, A-08 (2023), A-12 (2024) |
| Continuity checked across shots (contact sheet, light values, water colour) | 5 | A-03 (2021), A-04 (2023), A-07, A-11 (2024), A-09 (2025) |
| Fixed seed | 1 | A-01 |
| Temporal (multi-frame) denoising | 1 | C-02 (outside Blender) |

### 2. How things changed over time

Each change is dated by the sources, so it lags the Blender release that made it possible.

**EEVEE moved from preview to final render, first for stylised work and then for a feature film.** The 2015–2018 animation sources that name an engine (A-14, A-05, A-15) all rendered in Cycles on CPUs. Cosmos Laundromat (A-14, 2015) estimated about 3 hours per frame. Agent 327 (A-05, 2017) had frames over 100 hours until a fix in Cycles' handling of motion-blurred hair. EEVEE first appears as a final engine in 2019, the year 2.80 shipped: a placed CG Boost entry (C-04) and the Heroes of Bronze teaser (B-04). The stated reasons were speed and not needing a farm. By 2022 Blender Studio rendered Charge in EEVEE at 4K, at a median of about 3 minutes a frame (A-06), with the stated aim of "heightened realism". In 2024 Flow rendered every frame in EEVEE at 0.5–10 seconds per 4K frame on one PC (A-07/B-06). Cycles did not go away. It stays the choice for realistic stills (C-01, C-08, C-17) and for realistic animation, where it now runs on single consumer GPUs: about 10 minutes a frame on one RTX 4090 (C-12, 2024), about 5 minutes at 450 samples (B-03, 2025), about 1 hour on an RTX 3070 for an unoptimised scene (B-12, 2024). In this set, 11 sources render the final in EEVEE and 17 in Cycles. All 11 EEVEE sources date from 2019 onward, and 9 of them are animations.

**Geometry Nodes replaced particles and some simulation.** No source before 2021 mentions Geometry Nodes. Ten sources from 2021 to 2025 use it, and for more than scatter:
- the anti-flicker projection rig (A-01, 2021);
- procedural ripples, vines and a growing flower (B-07, 2022);
- outlines and normal faceting (A-08, 2023);
- the water toolset of a feature film (A-07, 2024);
- a hair groom (B-05, 2024);
- an effector that replaced a physics simulation of thousands of bricks (B-03, 2025).

Particles have not vanished. They still carry rain and debris (B-02, 2022; B-01, 2025). Scatter add-ons sit between the two eras, from 2020 to 2024: Scatter/Geo-Scatter, Botaniq, Forestation, Graswald, Population (6 sources). The clearest sign of the change is in what artists choose *not* to simulate. Four sources from 2024–2025 fake an effect that earlier work would have simulated: a tornado from a volume cube (B-01), bricks pulled by a GN effector (B-03), an explosion from a scaled sphere with motion blur (B-10), and water from a procedural toolset (A-07).

**Denoising made low sample counts normal and moved the problem to flicker.** The stills tell the sample story. 500 samples with no denoiser mentioned (C-06, 2016). Then 1600 and 2000 samples in 2019, with denoising still needed on fireflies or selected areas (C-07, C-08). Then 200 samples with OIDN on both viewport and render at Blender Studio (A-02, 2021), and 300–750 in later entries. With only eight data points this is a direction, not a measured trend. The cost showed up in animation. Blender Studio found that OIDN at low samples guesses differently on every frame. More samples did not fix it, and neither OIDN nor OptiX had a temporal mode then (A-01, 2021). In 2023 a BoBA-placed artist turned Blender's denoiser off and denoised the sequence in post with multi-frame tools (C-02). No source in the set shows a Blender-native fix in use.

**Colour management changed, but the showcase write-ups barely record it.** Only 7 of 49 sources name a view transform or delivery space. The sequence they show runs from film-emulation looks (C-06, 2016), to Filmic (A-02 2021, B-02 2022, A-06 2022), to AgX High Contrast (C-20, 2024; the only AgX mention in the set), to 32-bit ACES output for compositing (B-08, 2024), to an HDR PQ/HLG master graded in Blender's VSE (A-13, 2026). Flow did all its colour in shaders and used no compositing (A-07). For the guide, this is a gap to fill from the manual and release notes. The sources show which transforms were in use, but not how they were set.

**Simulation moved out of Blender, then partly back in as procedural fakes.** Cloth was done in Blender in 2016 (C-09) and 2018 (A-15). In the contest entries from 2019 to 2026 it is done in Marvelous Designer (5 sources). Heavy simulations come in from Houdini (A-15, B-12, C-12). Fluids use the FLIP Fluids add-on (C-02, B-13, A-07). The 2024–2025 fakes listed above are the reverse movement.

**Photogrammetry went from bought libraries to the artist's own phone.** Scanned libraries appear from 2016 onward (Poliigon maps in C-06; Megascans/Quixel in B-04, B-07, C-01, C-10). From 2022 solo entrants scan their own props and people: KIRI Engine (B-02), an iPhone with Scaniverse (B-01), and their own head as a face-mocap carrier (B-11).

**Where finishing happens moved out of Blender and partly back.** The 2016 still (C-06) did grain and chromatic aberration in Blender's compositor. From 2019 to 2025 most animations graded outside Blender, in Resolve, After Effects, Nuke or Fusion (10 sources). From 2024 several did it inside Blender again:
- Colorist Pro grading of EXR passes (B-03);
- Light Groups rebalanced in Blender's compositor (B-05);
- the real-time compositor for glow (B-10);
- Singularity's HDR grade in the VSE (A-13).

### 3. What separates winners from other featured work

The sources do not allow a technique-by-technique comparison, and it is better to say so plainly. Non-placing entries almost never publish breakdowns. Most winners don't either: the BoBA winner threads carry one line of process or none (C-20), and Suzanne Award winners almost never publish a written making-of (part B's winners table). The 15 placed entries kept here use the same techniques as the 5 unplaced entries and the 8 featured pieces. There is no technique that only winners use.

Two kinds of evidence do speak to the question.

1. **What juries wrote (C-04, C-05, C-15).** In all three, the stated reasons for winning were story or concept, mood and atmosphere, a limited or controlled palette, the subject separated from the background, and a readable design silhouette. Technique comes up as praise in two places only: "individual wood planks" and "subtle grunge" (C-15). The faults that held entries back were technical: noise, "wonky deformations" on a character, a character that looks "like a puppet", flat water, rough details and shadows (C-04, C-05). One entry was called "Technical wise ... almost perfect" and still did not place in the top three, because its story was missing (C-05). Read together, the comments suggest technique works as a floor. Noise or bad deformation can lose an entry, but clean technique does not win one by itself. This rests on three pages of jury comments, so treat it as a pattern in judges' words, not a measured effect.
2. **What placed artists say they prioritised.** These accounts repeatedly put effort into the hero subject and cut corners everywhere else:
   - "everything serves the main character" (B-10, 2nd);
   - a background built from cubes and a texture collage in under half a day (B-10);
   - the look "nailed" in render so that only 2–3 passes were needed and the time went to animation (B-12, 1st);
   - only the first quarter of a race track modelled (C-11, 1st);
   - only exposed organic parts sculpted, with procedural materials on the rest (C-03, 1st).

   The unplaced Kinetic Rush entry (B-08) built a heavier seven-layer pipeline. One case does not make a rule, and this point is no more than suggestive.

### 4. Recurring procedures, in Blender terms

Each procedure is the common core of the sources listed with it. Steps a source did not state are not filled in. Where sources differ, the variants are noted.

**P1. Block out to the camera, then light early, then detail what the camera sees** — 12 sources (C-01, C-11, C-13, C-19, C-21, A-07/B-06, B-01, B-03, B-05, B-11, B-12, B-13)
1. Collect references; one board per aspect of the scene (C-01, C-11, C-19).
2. Block out with primitives and placeholders: cubes, cylinders, a subdivided plane sculpted into terrain *from the camera's viewpoint* (C-01, B-03).
3. Place and lock the camera (angle, lens, rough framing) before modelling detail (C-19, C-21, B-01). For animation, either explore the rough set with a virtual camera (A-07) or make an animated blockout for timing and camera (B-05, C-13).
4. Put in the key light and a basic environment, render, and check the image. C-19 also over-painted the blockout render in Photoshop to explore the look. C-21 lights while modelling, to see where shadows fall and where detail is worth adding.
5. Model and detail only what the camera sees; leave the rest at blockout level or delete it (C-07, C-11, B-04, C-21).
6. Scene study render to confirm direction (C-01), then finish.

**P2. Split the render, output EXR, rebalance and grade afterwards** — 9 sources split the render (C-04, B-07, A-08, A-12, B-05, B-08, B-12, A-09, C-21); 7 output EXR
1. Separate the scene into view layers by depth or role: for example foreground / foreground FX / midground / background / atmosphere (B-08), or ground / background / hero object / ships / fog (C-21). For stylised work, beauty / outlines / Grease Pencil (A-09).
2. Optionally assign each main light to its own Light Group (B-05, B-12) and add Cryptomatte for masks (A-15, B-03, B-09).
3. Render to (multilayer) EXR. B-08 rendered 32-bit ACES with 10% overscan "for slight camera shake and lens distortion in comp".
4. Rebalance lights and exposure per layer, add glow, grain, lens distortion and vignette. This happens in Blender's compositor (B-03, B-05) or outside it (Resolve, After Effects, Nuke, Fusion).
5. Grade last (B-03, B-08, C-11, C-21).

The counter-variant: get the look right in the render and output 2–3 passes (B-12, A-10, A-07). A-10 gives the reason for EEVEE: its passes lack the Combined pass's sample refinement, so the Combined pass cannot be rebuilt from them.

**P3. Fog, god rays or a large effect from a volume cube** — 6 sources name a cube with a volume shader (A-02, B-02, C-20, B-01, B-03, C-21); 5 more use volumetrics without saying how (C-09, C-04, A-10, B-10, C-18)
1. Add a cube around the region that needs atmosphere. It can cover the whole scene (B-03, C-21), cover only the window and be stretched along the sun direction (C-20), or be aligned to the sun as a light shaft (A-02).
2. Put a volume shader in the material's Volume socket. A-02 used an Emission shader there, with density from a 2D Noise → ColorRamp → Multiply 0.070. B-02 used "a volume texture".
3. Shape it with nodes if it is an effect: B-01 made a tornado by shaping the density into a cone with Math and Map Range nodes, adding an animated Noise Texture, and adding three particle systems of debris at three sizes.
4. Optionally render it on its own view layer (C-21).

**P4. Scatter vegetation or clutter, then keep it light** — 9 sources (C-01, C-05, C-10, C-11, B-13, A-07, B-02, B-03, C-21)
1. Bring in assets: a scatter add-on's library (Botaniq, Graswald, Forestation) or scanned assets.
2. Scatter with an add-on (Geo-Scatter / Scatter, Botaniq), Geometry Nodes, or a particle system with weight-painted density.
3. Make the copies instances: collection instances (C-21), particle instances (B-02), GN instances (B-03).
4. Reduce cost: camera culling on the scatter (C-01); Render > Simplify to cap texture size, "2k will do just fine most of the time" (C-01); proxies (C-10); decimate small repeated objects, from 80 faces to 12 per raindrop (B-02); low-res meshes in the background (C-01). For viewport speed only, B-03 used a GN switch on Is Viewport that merges objects in the viewport and keeps instances for the render.
5. Close the view behind the scatter with a photo on a plane (C-10).

**P5. Animate: key poses first, then in-betweens, then the camera, then polish** — 7 sources (A-04, B-10, B-15, C-13, A-07/B-06, B-12, B-14)
1. Plan the action: Grease Pencil drawn over the shot camera (B-10), an animated previs (B-12), or a blockout for timing (C-13).
2. Key the hero's poses with interpolation set to Constant, so timing reads at a glance (B-10). A-04 calls this the "blocking pass for quick director feedback".
3. Get feedback, then add in-betweens, anticipation and transitions (B-10, B-15).
4. Animate secondary characters to the hero's rhythm, first as low-poly stand-ins (B-10).
5. Adjust the camera after the first animation pass so it responds to the action (A-07, B-15).
6. Polish: secondary motion (earrings, tails, fingers), contact with the environment, no intersections (A-04).
7. Delivery checks: frame rate, current linked assets, and motion-blur readiness on start and end frames and parent switches (A-04).

**P6. One light rig per sequence, checked across shots** — 4 sources (A-03, A-04, A-09, A-10)
1. Make one World per sequence for the base tint (A-09), and a light rig linked into every shot of that sequence (A-09, A-10).
2. Reduce lights to a few roles, each with stored values. A-04 uses key, key-soft, fill and rim, with RGB values in a linked node group so changes propagate.
3. Light the wide or establishing shot first and derive close-ups from it. Light the key shots of each sequence first (A-04).
4. Keep character lights separate from set lights. In A-09 a rig controller exposes key tilt, shadow colour and highlight colour.
5. Check continuity on a contact sheet of all shots (A-03), and keep light direction consistent with a top-down chart (A-04).

**P7. Fake the effect instead of simulating it** — 4 sources (B-01, B-03, B-10, A-07), plus B-07's Geometry Nodes scale-down of rigid-body shards
1. Decide what the effect must read as on screen. B-01: "a big dark silhouette, so it didn't need a lot of detail".
2. Build it from shader or Geometry Nodes primitives. A volume cube with a noise-driven cone (B-01). A GN effector sphere that moves any object it touches to a set location (B-03). A sphere with a procedural texture, scaled up and rendered with motion blur (B-10).
3. Animate one or two parameters instead of a simulation: effector radius, noise offset, scale.
4. The reason given: it can be adjusted without re-running a sim or re-keying many objects (B-03), and it is faster (B-01).

**P8. Scan it yourself, clean it, rig it** — 4 sources (B-01, B-02, B-11, B-13)
1. Shoot at least 20 photos around the object at varied heights, in even light, avoiding reflective surfaces (B-02). B-01 shot building photos at sunset or under overcast skies so no hard shadows are baked in.
2. Process with a phone app (KIRI Engine, Scaniverse).
3. Clean in Blender: delete faces, smooth with sculpt tools, remodel dense moving parts (B-01, B-02).
4. For a person: auto-rig in Mixamo by placing pins and apply a Mixamo animation (B-02). B-11 drove a facial-capture texture on a scan of the artist's own head.

**P9. Simulate, bake to cache, then render** — 3 sources state it (B-02, B-07, A-07). Another 3 import finished simulations from Houdini (A-15, B-12, C-12).
1. Set up the simulation: a rigid body on Cell Fracture pieces (B-07), particles with a wind force field (B-02).
2. Bake to cache before rendering. B-02: "A baked simulation will play smoother as it uses cache data".
3. Post-process the cached result if needed. B-07 scaled the shards down over time in Geometry Nodes.

### 5. Tricks a beginner would not think of

Each is stated in the source named. "Why" is the source's reason where one is given.

- **Project one clean frame over a moving camera to kill background flicker.** Render a depth pass, rebuild a mesh from it with Geometry Nodes, project one denoised frame onto it, and render that from the shot camera. It only works on static backgrounds. (A-01)
- **Turn the built-in denoiser off for animation and denoise the sequence temporally in post.** Blender's denoiser works one frame at a time; vegetation translucency makes the flicker worse. (C-02)
- **Put screen textures in the shader.** A paper texture applied in compositing sits on the screen; in the shader it stays attached to moving objects. (A-08)
- **A volume cube only at the window, stretched along the sun direction**, instead of filling the room with volume. (C-20, BoBA 2024 interior winner)
- **Shadow blockers the camera cannot see.** Disable Camera and Diffuse ray visibility (A-03), or mix black Diffuse with Transparent by Light Path *Is Camera Ray* (A-02). Darken frame corners with in-scene blockers instead of a post vignette, which "can look fake in the highlights". (A-02)
- **A camera-only background.** Mix the World by Is Camera Ray, so the HDRI lights the scene while the camera sees something else. (A-02)
- **A hair accent light with Diffuse ray visibility off**, so it adds only specular. (A-02)
- **The on-camera flash.** For photo-like character realism, use one spot or area light transform-matched to the camera; it gives even, amateur-photo lighting. (C-17)
- **Never rotate furniture by exactly 90° or 180°.** Use values like 93.32° or 175.4°. (C-17)
- **Guide mesh + Shrinkwrap for smooth reflections on car panels.** Model a smooth guide surface, then shrinkwrap the cut-up panel onto it. (C-07)
- **Albedo map reused as a bump map**, on top of the normal map, for micro-detail. (C-12)
- **Model repeated slats instead of texturing them.** Use an Array modifier and shift UVs per slat so the wood does not repeat. (C-10)
- **Drop objects with rigid bodies to place them naturally.** Chocolate drops onto a passive floor (C-08); pencils with the Physics Dropper add-on (Windowsill, collected earlier).
- **An Emission light with Light Falloff (Quadratic) behind a subsurface subject** to reveal SSS while keeping the rest dark. (C-08)
- **Film grain from a Lens Distortion node with only Jitter on**, mixed back at 0.333; chromatic aberration from Dispersion ≈ 0.02 with Fit on. (C-06)
- **Absolute shape keys.** Turn Relative off and drive a whole growth sequence from one Evaluation Time value. (B-07)
- **Bind objects to deforming water with Surface Deform**: switch the water's deformation off, bind, then switch it back on. (B-07)
- **Cracks applied in compositing through the UV pass**, with a growth mask rendered from animated crack visibility. (B-07)
- **Hide an animation fault behind timed staging.** A passing car crosses the frame at the clipping frames. (B-02)
- **Low-poly raindrops are invisible in motion.** Decimating drops from 80 to 12 faces "looked quite bad as a still object, but you can't see that once it's all in movement". (B-02)
- **A Geometry Nodes Is Viewport switch** that merges objects only in the viewport: 27,000 objects at 10–12 FPS became 6 objects at 60 FPS, with instances kept for the render. (B-03)
- **10% overscan on every pass**, so camera shake and lens distortion can be added in comp. (B-08)
- **A light blink on the beat.** When the motion stopped hitting every beat (hitting all of them looked robotic), a small light blink on the axe at impact restored the beat. (B-11)
- **Keep a scanned face constantly moving** so viewers do not notice its uncanny details. (B-11)
- **Constraint switches make long motion-blur streaks.** Set the switch keys to Constant interpolation and scrub with Subframe on to see what the renderer samples. (A-04)
- **In EEVEE, avoid Subdivision Surface modifiers.** EEVEE triangulates, and subdivision level 2 multiplies the base count by 16. CPU evaluation of subdivided characters dominated render time. (A-10)
- **Build the city around the path the car happened to take**, driven live with a vehicle-rig add-on on a gamepad. (Ian Hubert, Dynamo Dream; secondhand news post, not counted)

### 6. Animation: production methods that recur, and keeping a sequence consistent

**Methods that recur**
- **Previs in 3D instead of boards, then the camera responds to the animation.** Flow had no storyboards: a rough set, a virtual camera, and the camera adjusted after the first animation pass (A-07/B-06). B-15 animates characters first and the camera second, then retimes key moves so they read in frame. B-05 and B-12 build animated blockouts.
- **Blocking with constant interpolation, then splines.** B-10 states it outright ("no transition, snap!"). A-04 makes the blocking pass the trigger for lighting to start. B-15 works pose-to-pose. B-14 animates on twos with ten looping hand poses to imitate stop motion.
- **Light from blocking, not from final animation.** A-04: "We can start lighting a shot as soon as there is a first blocking pass available". A-09 pre-lights blocked shots and hands them to a 2D paint-over, which the lighting is then matched to.
- **One file per shot with linked assets in studios, or one big appended file when linking fails.** Blender Studio splits anim / fx / lighting / comp files per shot, all linked, with overrides re-applied on load (A-04). Flow used one big file per shot with everything appended, because linked assets broke between machines (A-07/B-06). Both are workable. The choice depends on whether the library paths can be kept stable.
- **Rigs.** Blender Studio generates limbs procedurally with CloudRig (built on Rigify) and rigs faces by hand (A-04). Contest entrants use Rigify (B-14, B-15, C-14), Auto-Rig Pro with a shape-key face (B-05), Mixamo auto-rigs (B-02, B-04), or a simple FK rig (C-12, who said it "did not help"). Rigid mechanical parts can be parented straight to bones instead of being skinned (B-02).
- **Behaviour rules for long shots.** On shots of about 6,000 frames, Flow's animators worked from written rules per character instead of checking frame by frame: ears turn to sounds, the tail moves independently (A-07).
- **Timing to an external clock.** Beat-synced work holds poses for a few frames on the beat (C-13). It breaks repetition and restores the beat with a light accent (B-11). Nearly all of one animator's work is cut to music tempo (B-15).
- **Loop constraints shape staging.** In template challenges, the character must start and end on the same spot. Staging and even physics bend to fit the loop (B-12, B-13).
- **Render cost for animation in practice.**
  - EEVEE: seconds to about 3 minutes per 4K or HD frame (A-06, A-07, A-10).
  - Cycles on one consumer GPU: about 5–10 minutes per frame (B-03, C-12), up to an hour unoptimised (B-12).
  - Before 2018: hours per frame on CPU farms (A-05, A-14).

  Several solo entrants moved to a farm days before the deadline (B-07, B-11, B-12).

**Keeping a sequence consistent frame to frame.** Only 4 of 49 sources talk about flicker directly, and only one (A-01) does so in depth. What they establish:
1. **Low-sample denoising flickers in animation.** The denoiser invents different detail on each frame. Raising samples 6× did not remove it (A-01).
2. **A fixed seed helps only while the camera is still.** With a moving camera the fixed noise pattern slides across the image (A-01).
3. **Temporal denoising has to come from outside Blender in these sources.** A-01 notes no temporal mode in OIDN or OptiX at the time. C-02 used Neat Video's multi-frame denoiser and Topaz in post.
4. **Some content flickers more than others.** Vegetation with translucency (C-02), moving moss, and transparency or volume passes (A-01). Blender Studio avoided moving foliage in day shots for this reason (A-01).
5. **Anything procedural must stick to the surface.** Paper texture in the shader, not in comp (A-08). Brushstrokes on a deforming mesh need a rest-position attribute (A-12; the docs give only the requirement). Outlines still broke on some poses and were fixed frame by frame (A-08). Gold flagged "brush stroke jittering" as a late problem (A-12).
6. **EEVEE needs per-shot light probes.** Baked probe lighting cannot be shared between scenes (A-10).
7. **Motion blur is where frame-sampling bugs show.** Constraint switches streak (A-04). Motion-blurred hair dominated Agent 327's render time (A-05). Next Gen used rendered 3D blur on every shot, and accepted that Embree's object blur is linear, not arced (A-15).
8. **Shot-to-shot consistency is managed with shared rigs and review.** Shared light values, a contact sheet, and water checked against adjacent shots (A-03, A-04, A-07, A-09). Simulations baked to cache play back the same each time (B-02).

**Measured afterwards on this laptop** (card C-006, `experiments/animation/flicker.py`): 25 frames of a forest dolly at 1280 x 720, Cycles on Metal, each variant's flicker set against a 1,024-sample render of the same frames.
- Claim 1: at 128 samples with OpenImageDenoise the noise was 2.5 % of the flicker (0.00018 of 0.00725). Tripling the samples moved the total by 1 %. That matches A-01's observation that more samples did not cure it, but here there was little noise flicker to cure. A-01 does not say how much of its flicker was noise.
- Claim 2: animating the seed raised flicker by 21 % in this moving shot. The measure undercounts a pattern that stays fixed in the picture, so it does not test whether a fixed pattern visibly slides.
- Claim 3: Blender 4.5 has `bpy.ops.cycles.denoise_animation`, and it runs headless, but with OpenImageDenoise it changed flicker by +0.14 %. The claim stands on this Mac; OptiX was not tested.
- Claim 4 was not tested. The foreground plants changed more than the whole frame (0.00872 against 0.00725), but they are also nearest the camera, so they move most.

The gap is plain. None of the placed contest entries in part B states its denoiser, seed or any flicker handling. Several of them rendered 120–220 frames on a single GPU. Either their scenes did not show flicker at their sample counts, or they did not report how they handled it. The sources cannot tell these apart.

### 7. Limits of this study

- **Year spread.** Eight sources predate 2019. The trends in section 2 are anchored at the early end by a handful of pages, and a different early handful could shift the dates.
- **Survivorship.** Written breakdowns exist mostly for work whose authors chose to explain it. The set says what those artists did, not what all good Blender work does.
- **Numbers are rare.** 8 sample counts, 7 denoiser choices and 7 colour-management settings across 49 sources. Values for colour management, light bounces and denoiser passes should come from the manual, not from this study.
- **Secondhand material.** The Flow render times come through an 80.lv paraphrase of a blender.org page that could not be fetched (A-07). B-06's first page is reported speech. Both are marked as such in the entries.
- **Same-film clusters.** A-01, A-02 and A-03 are all Sprite Fright; A-08 and A-09 are both Wing It!. Counts treat each write-up as a source, so Blender Studio practice is weighted more heavily than a single studio usually would be.

## Sources tried and excluded

### Part A

- https://www.blender.org/?p=93732 and https://www.blender.org/user-stories/making-flow-interview-with-director-gints-zilbalodis/ — the primary "Making Flow" interview; HTTP 403 to fetch. Its facts enter only second-hand through A-07.
- https://web.archive.org/... (Flow interview) — the fetch tool cannot reach web.archive.org.
- https://conference.blender.org/2024/presentations/3929/ ("The animation of Flow") and https://conference.blender.org/2025/presentations/4110/ ("A glimpse into 'Flow'") — abstracts only; the talks are video.
- https://80.lv/articles/behind-the-scenes-blender-water-development-in-animated-movie-flow — thin news piece; names a paid add-on, no method.
- https://studio.blender.org/blog/smoke-mirrors-and-explosions/ (Charge FX) — login-walled; only the intro says the FX used EEVEE's real-time interactivity.
- https://studio.blender.org/blog/compositing-lens-dust-fx/ (Charge) — login-walled.
- https://studio.blender.org/films/charge/production-logs/ and https://studio.blender.org/projects/charge/production-log/205/ — summaries over subscription video; the only usable line ("render every shot with little to no glitches") is noted in A-06.
- https://studio.blender.org/tools/pipeline-overview/shot-production/rendering — stub page ("currently being edited/updated").
- https://studio.blender.org/blog/the-blender-studio-pipeline — history of production-tracking tools (Attract, Kitsu); no production method.
- https://studio.blender.org/blog/spring-spring-open-content-overview/, https://studio.blender.org/projects/spring/pages/about/, https://conference.blender.org/2019/presentations/595/ — Spring: no readable technical content beyond "development build of Blender 2.80" and "Blender, GIMP and Krita". https://digitalproduction.com/2019/05/05/making-of-spring/ — paywalled after the intro.
- https://studio.blender.org/blog/hero-presenting-hero-blender-grease-pencil-showcase and https://studio.blender.org/blog/hero-hero-a-blender-2d-open-movie-project — Hero: announcements only (Blender 2.8 Grease Pencil 2.0, about 3 minutes, made remotely); no workflow.
- https://studio.blender.org/blog/caminandes-3-blender-development-during-llamigos — a development changelog. The one production method in it: a texture driving hair clump and other particle settings through drivers, used for moving fur in action shots and to switch hair on and off on linked characters; also a per-render-layer "Use Ambient Occlusion" option. Too little on methods to stand as a source.
- https://studio.blender.org/projects/cosmos-laundromat/production-log/22 and /28 — titles over gated video; mention hair render tests, wind in grass, Qarnot benchmarks, no settings.
- https://code.blender.org/?p=1825 — the 2016 Cycles benchmark post; not about production method (contains Ton Roosendaal's general line that fast GPUs suit previewing and lighting while fast CPUs suit production rendering).
- https://80.lv/articles/next-gen-a-netflix-film-made-with-blender — a rewrite of the Blender Artists post used in A-15.
- https://aws.amazon.com/blogs/media/aws-does-the-heavy-lifting-for-tangent-animation-on-netflix-film-next-gen — article body did not load (navigation only). Search snippets claim about 2.5 versions of the film rendered on AWS in 36 days and a 600-node local farm; not verified, not used.
- https://studio.blender.org/blog/singularity-premiere/ — announcement only (first 4K HDR release).
- Coffee Run "Rendering Coffee Run" video series (studio.blender.org/projects/coffee-run/...) — subscription video; not used.
- YouTube and other video pages — not used; nothing here is claimed from watching video.

### Part B

Suzanne Awards winners and finalists (the main gap: winners rarely publish a text making-of; most of what exists is a video, a talk page abstract, or a one-line tool list):
- https://conference.blender.org/2023/festival/entries/547/ and https://sturmstudio.org/rhlbc.html — "Remove Hind Legs Before Consumption" (Best Short 2023). Thin: everything in Blender except edit/grade in DaVinci Resolve; rough character animation in TVPaint, clean-up and all FX animation in Grease Pencil. No settings. Kept only as a winners-table note.
- https://conference.blender.org/2023/festival/entries/556/ and https://www.blendernation.com/2023/10/24/space-tales-episode-02/ — "Space Tales, Episode 02", M74 (Best Animation 2023). Thin: "Our 3D Department uses Blender, and sometimes Houdini for some simulations."
- https://conference.blender.org/2024/festival/entries/577/, https://blendernation.com/2024/09/16/anime-short-film-samurai-blue-afterimage, https://blenderartists.org/t/samurai-blue-afterimage-anime-short-film/1549188 — "Samurai Blue: Afterimage" (Best Short 2024). Thin: made in the Goo Engine fork of Blender 3.6, comp in After Effects, edit/mix in DaVinci Resolve. BCON 2024 talk (https://conference.blender.org/2024/presentations/3870/) is an abstract only.
- https://conference.blender.org/2024/festival/entries/606/ and https://conference.blender.org/2024/presentations/3864/ — "SOLO – Mundo Canibal", Toni Mortero (Best Animation 2024). Entry text: a 3-year project to test a pipeline for "the most 2D-like finish possible"; talk page is an abstract with no method; no slides linked.
- https://conference.blender.org/2024/festival/entries/595/ — "CATWALK" (Best Design 2024). Entry text only: modelling, animation and VFX in Quill VR; shading, rendering, compositing, animatic (Story Pencil) and edit in Blender.
- https://conference.blender.org/2025/festival/entries/676/, https://blenderartists.org/t/spent-3-months-on-a-short-film/1606875, https://sandwich.vision/newsletter/restraint-in-relief-with-milo-chiavarino-annaud — "SINGULARITY", Milo Chiavarino (Best Design 2025). Thin: Blender 4.2 and 4.5 plus "a bit of Marvelous Designer", one person, three months; interview is about direction, not method.
- https://conference.blender.org/2025/festival/entries/685/ (The Ballad of Pale Blue Dot, Best Short 2025) and /662/ (Phởnomenal Battle, Best Animation 2025) — synopsis and credits only.
- https://blenderartists.org/t/another-animated-short-film/1135053 — "ANOTHER" (Best Short 2018). Thin: three-day kick-off with a team, six months, "Made with Blender. Edited in DaVinci Resolve. Rendered in Cycles." https://linolafett.artstation.com/projects/3oo0JD (team member's page, said to describe a texture-based raindrop effect) returned 403.
- https://www.blendernation.com/2019/10/02/devin-townsend-why-grease-pencil-music-video/ — "Devin Townsend: Why?", DC Turner (Best Animation 2019). Video embed; "Created entirely in Blender 2.8", Grease Pencil.
- https://stashmedia.tv/?p=64282 — "The Box", Dušan Kastelic (Best Short 2019). Interview about story; visuals "mostly by myself" in Blender over two years; no method.
- https://www.blendernation.com/2016/03/23/short-action-film-katsu-cats/ — "Katsu Cats", Dillon Gu (Best Animation 2016). Video plus two lines: six weeks, everything modelled/rigged/animated/shaded/rendered in Blender.
- https://animationxpress.com/?p=620479 — "Muskaan", Girgit Studios (Best Short 2017). News piece; first use of cloth physics and fire/rain dynamics in Blender; no settings.
- https://3dvf.com/heroes-of-bronze-the-memory-4-ans-de-travail-sous-blender/ — used only as a companion note in B-04 (paraphrase, no quotes).

Pwnisher entries:
- https://www.blendernation.com/2022/03/08/infinite-journeys-challenge-process-breakdown-blender-3-0/ — video embed; text says Blender 3.0 and first time using Blender for final output.
- https://www.blendernation.com/2021/05/31/how-i-mixed-2d-and-3d-animation-for-alternate-realities-challenge/ — video embed; text: Grease Pencil + 3D, "Rendered in Eevee", chapter list only.
- https://www.blendernation.com/2023/07/18/how-i-created-my-entry-for-the-endless-engines-challenge/ — video pointer only.
- https://80.lv/articles/fascinating-anime-fight-made-for-pwnisher-s-challenge — DRÆM SEQUENCE entry; news rewrite, only "outlines were made with Grease Pencil".
- https://80.lv/articles/creating-story-in-cyberpunk-animation-for-chasm-s-call-challenge — Chasm's Call 4th place, detailed, but final render in Unreal Engine 5 (Movie Render Queue); Blender used for blockout, modelling and keyframe animation only. Out of scope for a Blender render guide; could be reused for Blender-side rigging notes (twist bone, 0/1 weights for rigid parts).
- https://www.foxrenderfarm.com/news/how-david-sujono-won-2nd-place-in-chasm-call-with-offside/ — Cinema 4D + Redshift, not Blender.
- https://blenderartists.org/t/miles-nyc/1546414 and https://www.blendernation.com/2024/10/23/behind-the-scenes-miles-nyc/ — Kinetic Rush entry, but featured in BoBA; skipped at the coordinator's request (BoBA covered elsewhere).
- https://80.lv/articles/breakdown-creating-realistic-sci-fi-shot-fully-in-blender — not a challenge entry, an environment shot (out of slice); Cycles 4K, view layers rendered separately, comp in Resolve.

Character / other:
- https://80.lv/articles/check-out-how-this-stylized-animated-short-film-was-created-in-blender — NOXIOUS (Kay Hilman); news rewrite of a video; projection mapping + Grease Pencil, Outline modifier, geo-node lines stuck to surfaces; no detail.
- https://garagefarm.net/case-studies/charles-lang-follains-debut-animated-film-gardener — "The Gardener" (2017): render-farm case study; 300 samples at 1280×720 with the denoiser; otherwise thin and outside the slice.
- https://www.blender.org/?p=93732 — "Making Flow" interview on blender.org: blocked by a bot check (Cloudflare) for both WebFetch and curl; not read.
- https://www.blendernation.com/2021/11/03/behind-the-scenes-dynamic-magic-dynamic-machines/ — not read (same artist as B-07, a non-Pwnisher challenge; budget).

Search notes: no kept source states samples + denoiser + seed choices for an animation, and none describes fixing flicker. Generic guides on flicker (render-farm blogs, iRendering) and Blender Studio's "Denoising Sprite Fright" turned up but are outside this slice (open movie / vendor guides).

### Part C

- https://blenderartists.org/t/nick-is-playin-video-games/1489764 — BoBA 2023 Animation winner; no process text from the artist.
- https://blenderartists.org/t/drive/1542528 — BoBA 2024 Animation winner; one sentence of process ("all done entirely in blender").
- https://blenderartists.org/t/the-barbershop-project/1467888 — BoBA 2023 Characters winner; lists Medusa Nodes, light groups, Blender 3.5 + Substance only; the linked guide not found.
- https://garagefarm.net/case-studies/interview-with-blender-contest-winner-robert-paprotny — placement and all technical detail not stated.
- https://www.blendernation.com/2015/06/08/stillness-breakdown/ — teaser; linked artist page 404.
- https://www.blendernation.com/2023/06/18/photorealistic-car-animation-with-vfx-breakdown/ — two sentences; breakdown only in video.
- https://80.lv/articles/a-hyperrealistic-3d-render-stylized-as-a-mobile-phone-photo — short news post, two quoted lines (Lightroom noise reduction, clipped darks).
- https://80.lv/articles/how-to-make-scene-so-realistic-that-no-one-believes-it-was-made-in-blender — this is the Windowsill interview (already collected).
- https://www.blendernation.com/2026/04/27/inside-sjor-a-two-person-pipeline-for-a-17-minute-cinematic-short/ — final frames apparently real-time (UE5); no Blender settings.
- https://www.blendernation.com/2026/08/23/behind-the-scenes-stormy-weather/ ; https://www.blendernation.com/2025/11/15/the-making-of-au-revoir/ ; https://www.blendernation.com/2021/09/08/animation-stages-on-a-short-film-samurai-sushi/ — teasers pointing to videos.
- https://www.blendernation.com/2021/08/31/cyberpunk-apartment-motion-tracking-breakdown/ — short; one usable trick (paper markers), no tracking settings.
- Hum3D Car Render Challenge winners pages (3dmodels.org) — HTTP 403; 80.lv summaries name no software.
- https://www.blendernation.com/2019/09/16/product-render-break-down/ ; https://www.blendernation.com/2017/11/07/gravity-fragrance-packshot-breakdown/ ; https://www.blendernation.com/2016/06/11/blender-glassicebubbles-render-breakdown/ ; https://www.blendernation.com/2016/06/15/mr-elephant-glenn-melenhorst/ ; https://www.blendernation.com/2017/10/04/umi-no-ha-blade-sea-post-mortem-02/ ; https://www.blendernation.com/2014/07/17/sector-9-vfx-breakdowns/ ; https://www.blendernation.com/2021/08/29/breakdown-pemberton-station/ — teasers; the content is in a video or image, or on another site.
- https://www.blendernation.com/2019/09/23/behind-the-scenes-thai-island-life/ — full article, but Blender Internal low-poly (2.79b); outside the realism/animation priority. Worth noting: Mist pass for distance fade, a second shadowless sun in a complementary colour.
- https://80.lv/articles/a-look-into-archviz-in-blender (George Turmanidze, 2019) — principles only (four maps per material); no settings.
- https://80.lv/articles/highway-scene-using-blender-for-modeling-and-vegetation-workflow/ — final render in Unreal Engine 4, not Blender.
- https://80.lv/articles/animating-a-chaotic-taxi-ride-sequence-in-blender-with-an-xbox-gamepad ; https://80.lv/articles/breakdown-making-a-digital-train-car-environment-in-blender (Ian Hubert, Dynamo Dream) — secondhand news posts. Not counted, but two facts are worth recording: EEVEE was used to block timing and lighting and Cycles for everything else; the city was built around the path the car happened to take (driven with the RBC vehicle add-on on an Xbox gamepad).
- https://cgcookie.com/posts/worldbuilding-with-ludicrous-energy-ft-ian-hubert — 403.
- https://www.blender.org/features/user-stories/ and every blender.org page — 403 to automated fetch.
- Evermotion making-ofs (evermotion.org/tutorials/...) — 403; the Evermotion 2015 winner write-ups found were 3ds Max/V-Ray anyway.
- https://www.ronenbekerman.com/showcase-by-software/cycles/ — gallery listing, not making-ofs.
- https://conference.blender.org/2024/presentations/1965/ — talk abstract only.
- https://www.foxrenderfarm.com/news/interview-with-blender-artist-whatheheckgg-winner-of-cyber-city-challenge — Kaizen's Cyber City Challenge, 3rd place. Drafted as C-16 and then demoted as too thin: no version, engine or settings. Its stated order of work is camera angle and mood first, then modelling, then a volumetric fog cube. One judgement: an over-pushed Color Ramp made wet concrete very reflective, and the artist kept it because it bounced the neon.
- BoBA 2025 — voting threads exist (https://blenderartists.org/t/best-of-blender-artists-2025-is-here/1623370), but no winners announcement was found or indexed as of 2026-11-23. BoBA 2022 winners thread (https://blenderartists.org/t/these-are-the-winners-of-the-best-of-blender-artists-2022/1441381) was found but not opened, because 2021, 2023 and 2024 already showed that the entry threads carry little process text.
- CG Boost per-challenge pages beyond the two kept (treehouse, mushroom house, science lab, etc.) — same one-line-per-entry format; two kept as representative of the jury commentary.

## Appendix: Suzanne Award winners by year (2014–2025), from part B

Source per row. Winners for 2023–2025 read from the `is-winner` CSS class on conference.blender.org `/<year>/festival/finals/`. "—" = not found.

| Year | Best Animation | Best Design | Best Short Film | Source / note |
|---|---|---|---|---|
| 2014 | Télécelebrité — Arnaud Travert | Jonas — Gaël Labousse & Clément Ducarteron | 11 Paper Place — Daniel Houghton | https://www.blendernation.com/2014/10/28/the-winners-of-the-suzanne-awards-2014-are/ |
| 2015 | Vlad & Louise trailer — In Efecto | Sintik — Manuel Grad, Timo Socher | the parking lot — flojoART | Wikipedia "Suzanne Award" mirror (bold = winner): https://bafybeiemxf5abjwjbikoz4mc3a3dla6ual3jsgpdr4cjr3oz3evfyavhwq.ipfs.4everland.io/wiki/Suzanne_Award.html — medium confidence |
| 2016 | Katsu Cats — Dillon Gu | Subsurface — (artist not given) | The Collinwood Fire — (artist not given) | https://www.blendernation.com/2016/10/30/suzanne-awards-winners-2/ |
| 2017 | — | — | Muskaan — Girgit Studios | https://animationxpress.com/?p=620479 (categories that year: Character Animation, Design, Short Film) |
| 2018 | Un día de suerte / A Lucky Day — Fernando Enrique González (student project) | The Hunter — Jari Vaara | Another — Manuel Lüllau and team | https://3dvf.com/actualite-24672-suzanne-awards-decouvrez-projets-primes-a-blender-conference-html/ ; team names from https://blenderartists.org/t/another-animated-short-film/1135053 |
| 2019 | Devin Townsend: Why? — DC Turner | HeartFuel — (artist not given) | The Box — Dušan Kastelic | https://conference.blender.org/2019/festival/ ; directors from https://skwigly.co.uk/showcase/why and https://stashmedia.tv/?p=64282 |
| 2020 | — | — | — | not found (online edition; festival pages 404) |
| 2021 | — | — | — | 3DVF reports no 2021 Blender Conference: https://3dvf.com/thematique/blender-conference/ |
| 2022 | KITTEH KITTEH Fatal Danger — (artist not given) | Fértil — (artist not given) | La Vida de una Piñata — Kai Müri, Elena Heller, Marina Kunz, Raphael Pfyffer (HSLU) | https://www.blendernation.com/2022/10/29/blender-conference-2022-recap-day-2/ (quotes the conference tweet) — see B-09 |
| 2023 | Space Tales, Episode 02 — M74 (dir. Andrea Battistoni) | Secret Moon — orencloud | Remove Hind Legs Before Consumption — Finn Meisner, Lukas Wind, Leslie Herzig (HSLU) | https://conference.blender.org/2023/festival/finals/ ; method note: rough animation in TVPaint, clean-up and FX in Grease Pencil, all else in Blender except Resolve grade |
| 2024 | SOLO – Mundo Canibal — Toni Mortero | CATWALK — Lidia Luna, Toni Mortero, Omayra González | Samurai Blue: Afterimage — Winterstellar Studios (dir. Wyatt Hall) | https://conference.blender.org/2024/festival/finals/ ; method notes: SOLO a test of a 2D-like 3D pipeline; CATWALK animated in Quill VR, shaded/rendered/composited in Blender; Samurai Blue made in Goo Engine (Blender 3.6 fork) |
| 2025 | Phởnomenal Battle — Animation Lucerne students (ident for Adult Swim Europe) | SINGULARITY — Milo Chiavarino | The Ballad of Pale Blue Dot — Duncan Rudd (3DR Studio) | https://conference.blender.org/2025/festival/finals/ ; method note: Singularity made in Blender 4.2 and 4.5 + Marvelous Designer, one person, three months |

Rule worth knowing for reading these winners: the festival requires that "the 3D graphics (models, animation, rendering) in the films have to be created entirely in Blender, rendered in Blender or any other free and open source render engine"; 2D paint and outside compositing/editing are allowed if declared (https://conference.blender.org/2019/festival/; same rule, with Grease Pencil added, on the 2022 page). So every winner is a Blender-rendered film, even when its comp is in After Effects or Resolve.
