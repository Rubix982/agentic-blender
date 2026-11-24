# CARD

The live card is below the template. One card open at a time; a card closes with a number, or a sentence that could
have come out the other way.

```
### C-xxx · title
**Opened / Closed:**
1. WHERE WE ARE      the last thing established, as a number or a fact
2. WHAT WE ARE DOING one action a second person could carry out
3. WHY               what is not known now that will be known after
4. WHAT IS AFFECTED  which claims, files or numbers change either way (written before the work)
5. CONCLUSION        if X, we claim A; if not-X, we claim B
6. CONSEQUENCE OF NOT DOING IT
**Result:**
```

---

### C-001 · A field guide to Blender 4.5, read from Blender itself, and a skill made from it

**Opened:** 2026-11-23 · **Closed:** 2026-11-23

1. **WHERE WE ARE.** Blender has come up in two projects. What we learned is spread over one 371-line feature map and
   dozens of lessons scattered through another project's logs, and none of it reaches an agent working somewhere else.
   This machine runs Blender 4.5.14 LTS (Apple Silicon, 16 GB).
2. **WHAT WE ARE DOING.** Build a knowledge base of Blender 4.5 from three sources: an inventory read from Blender
   itself (every type, property, operator and node, with node sockets), experiments run headless on this machine, and
   lessons from earlier projects, rewritten as general lessons. Document it by area, and package it as a skill
   (`skills/blender/`) with a lookup tool over the inventory.
3. **WHY.** Unknown now: whether a written guide changes how often an agent's Blender script does the right thing the
   first time. After: a count, on ten tasks set aside before any of the guide was written (`evals/tasks.md`), done by a
   fresh agent with the skill and without it.
4. **WHAT IS AFFECTED.** Nothing that exists yet; this repository is new. The earlier projects' own Blender notes stay
   where they are; they may later point here.
5. **CONCLUSION.** If the agent with the skill gets at least 3 more of the 10 tasks right first time than without it, the
   skill is where Blender work starts in every project, and new Blender lessons are written here. If not, the guide is
   reference only, and the failures say what the gap is instead (knowledge, or checking the result).
6. **CONSEQUENCE OF NOT DOING IT.** Each project rediscovers Blender from an agent's memory, which mixes versions 2.7 to
   4.x; the next one (a pierced stone screen to be lit and rendered) starts from zero.

**Amendment (2026-11-23, before any run):** the ten tasks in `evals/tasks.md` were written by the guide's writer, who
then briefed the guide's workers knowing them, so the guide's coverage leans toward them (details in `evals/tasks.md`).
The claim in field 5 is tested on an independent set of ten tasks written by a fresh agent that had not seen the guide
(`evals/independent/`); the writer's set is reported beside it.

**Status (2026-11-23, end of the build):** the guide is frozen as git tag `v1`: 22 area pages, a generated reference
(every node, modifier, constraint and setting of 4.5), 121 experiments with 884 recorded facts, 168 lessons, and the
audit finding 1,812 of 1,859 cited numbers in the results they cite. Both task sets and the harness are validated
(`evals/harness_check.md`: right solutions 10 of 10 and wrong ones 0 of 10, in each set). Not run yet: the with and
without comparison itself, 20 Claude sessions per set on the user's account, which waits for the user's yes.

**Result:** with the skill, 10 of the 10 independent tasks were right the first time; without it, 6 of 10 (one
session per task and arm, claude-opus-5-5; `evals/results.md`). The gap of 4 meets the bar of 3 in field 5, so the
first branch holds: Blender work starts from this skill, and new Blender lessons are written here.

What the 4 is made of: every script without the skill that ran was right (6 of 6), and all four failures crashed
before saving anything. Three hit one trap the guide does not describe (deleting the default objects with
`bpy.data.objects.remove` leaves `None` in `view_layer.objects` until `view_layer.update()`); the skill's sessions
avoided it by starting from the empty file in its skeleton (9 of 10). The fourth guessed a light-linking name that
the skill's session looked up with `kb.py`. Limits: one session per task and arm (the four differing tasks all going
one way would happen about one time in 16 if the skill made no difference); the agents wrote blind, so this measures
first attempts, not finished work; the skill's sessions took 12.5 turns on average against 2.8 and cost about a
quarter more; the writer's set was not run.

---

### C-002 · Free remote assets into a headless scene

**Opened:** 2026-11-23

1. **WHERE WE ARE.** v2 knows only the assets that ship with Blender; it names no outside source. Poly Haven and
   ambientCG are free (CC0) and need no account; both have APIs (Poly Haven's terms: a User-Agent naming the software,
   and a credit).
2. **WHAT WE ARE DOING.** Write `scripts/assets.py` (search and fetch, cached and checked) and `scripts/asset_import.py`
   (inside Blender: a world from an HDRI, a material from texture maps at real-world size, a model imported), then run
   ten assets through them headless: three HDRIs, four textures, three models, from both sources.
3. **WHY.** Unknown now: whether a script can go from a search word to a correctly lit, textured, correctly sized scene
   element with no person in the loop, or where that breaks.
4. **WHAT IS AFFECTED.** New files only (the two scripts, an area page, an experiment); `SKILL.md`'s areas table and
   `instancing-assets.md` gain a pointer.
5. **CONCLUSION.** An asset passes if it arrives checked against the source's size (and md5), builds without error,
   and passes its kind's check: an HDRI lights a grey sphere and rotating it by 180 degrees moves the lit side; a
   texture's maps are all connected in the right colour space and repeat at the stated real-world size; a model's
   imported size is within 2 % of the stated one (or is reported, where the source states none). If at least 9 of 10
   pass, `assets.py` is how the skill gets assets; if fewer, the page records what fails, by source and kind.
6. **CONSEQUENCE OF NOT DOING IT.** Every realism task (T-003) starts with grey boxes, or an agent hand-rolls downloads
   each time, unchecked.

**Closed:** 2026-11-23

**Result:** 10 of the 10 assets passed (`experiments/assets/remote_assets.py`), so `assets.py` is how the skill gets
assets (`areas/remote-assets.md`). The three HDRIs lit the sphere and their lit side moved when turned; the four
textures repeated within 0.1 % of their stated size (179.16 px against 179.2 for a 1.4 m brick); the two Poly Haven
models came in within 1.42 % of their stated size, and the ambientCG model, which states none, at 0.97 x 1.40 x 0.22 m.
The first run scored the models 0 of 3: its check read `has_data`, which is False on every freshly imported texture
until its pixels are used, so the check was wrong, not the models; it now looks at the file and touches the pixels,
and that trap is on the page. Found on the way: where an HDRI's sun is (`asset_import.hdri_sun`, within 0.8 degrees),
and that ambientCG's v2 API ignores its type filter.

---

### C-003 · The community's most-downloaded add-ons, headless

**Opened:** 2026-11-23

1. **WHERE WE ARE.** The guide catalogues the 14 add-ons that ship with Blender 4.5. extensions.blender.org lists 1,062
   add-ons for 4.5 on this Mac; the most downloaded are mostly ones that shipped with Blender before 4.2 (LoopTools,
   2.36 million downloads). None is catalogued.
2. **WHAT WE ARE DOING.** Install the top 20 by downloads into a throwaway profile inside a macOS sandbox (no network,
   no writes under the home folder, no launching programs), record what each declares, contains and registers, and
   call each of its operators headless with default settings on a fresh cube.
3. **WHY.** Unknown now: which of the community's everyday add-ons a headless script can use at all, and which are
   tools for a person at the screen.
4. **WHAT IS AFFECTED.** New files (an experiment, an area page); `running.md`'s extensions section and `SKILL.md`'s
   areas table gain a pointer.
5. **CONCLUSION.** If at least 10 of the 20 have an operator that finishes headless with default settings and changes
   the scene, the page lists them as tools a script can call, with those operators; if fewer, the page says the
   popular add-ons are mostly interactive tools and names the few that work.
6. **CONSEQUENCE OF NOT DOING IT.** Agents rebuild what an add-on already does, or reach for an add-on that only works
   with a person at the screen.

**Closed:** 2026-11-23

**Result:** 13 of the 20 had an operator that finished headless with default settings and changed the scene
(`experiments/extensions/top_addons.py`), so `areas/extensions.md` lists them as tools a script can call, with those
operators. All 20 installed and enabled in the throwaway profile; none crashed or hung; the whole probe took 73.7 s.
The seven with none are mostly built for a selection a person makes (Bool Tool, F2, Copy Attributes Menu, Auto
Mirror, MeasureIt) or a flag their panel sets (A.N.T. Landscape returned `PASS_THROUGH`); the importer takes a file.
Limits: one cube and default settings for every operator, so these are lower bounds. A second pass, run on the
user's go-ahead (`experiments/extensions/targeted_addons.py`), gave four of them the input they are made for: A.N.T.
Landscape (with `refresh=True`) and Bool Tool (with a canvas and a cutter selected) then worked, making it 15 of 20;
F2 and A.N.T.'s Displace still did nothing headless. The run's download
counts were wrong (an icon's width, 100, read as the count) and were re-read from the website afterwards; the parser
is fixed.

---

### C-004 · What realistic Blender environments are made of, as settings a script can make

**Opened:** 2026-11-23

1. **WHERE WE ARE.** The guide makes a script do what it is asked (C-001: 10 of 10), fetches free assets (C-002) and
   knows which add-ons run headless (C-003). It says nothing about what makes an image look real. 17 published
   breakdowns of realistic Blender environments (three contest winners) are collected and checked
   (`kb/research/realism-breakdowns.md`).
2. **WHAT WE ARE DOING.** For each technique that at least 4 of the 17 used and that is a setting in Blender rather than
   judgement or hand-modelling (twelve: HDRI lighting, a sun with it, materials blended through masks, weathering
   layers, procedural main surfaces, displacement, fog, density-painted scattering, grain, glow, grading, denoising),
   find the Blender 4.5 recipe, run it headless, and measure what it changes in the render. Write `areas/realism.md`.
3. **WHY.** Unknown now: whether everything those artists did with settings can be done from a script on this
   machine, and what each step changes, in numbers; and so what is left that is judgement.
4. **WHAT IS AFFECTED.** New files (experiments under `experiments/realism/`, the page); `SKILL.md`'s areas table. The
   photo match (the next card) is designed from this page.
5. **CONCLUSION.** If all twelve have a recipe that runs headless with a measured effect, the photo match is built
   from this page alone and tests the judgement left over; for each that does not, the page names the gap, and the
   photo match either works around it or tests it.
6. **CONSEQUENCE OF NOT DOING IT.** A realism attempt starts from an agent's guesses about grain and fog values, and
   any failure cannot be told apart from a missing technique.

**Closed:** 2026-11-23

**Result:** all twelve have a recipe that runs headless with a measured effect, so the photo match is built from
`areas/realism.md` alone and tests the judgement left over. Five were measured before (HDRI lighting and its sun in
`remote-assets.md` and `light-world-camera.md`; procedural surfaces and displacement in `materials.md`; denoising in
`rendering.md`); seven here (`experiments/realism/`): masks through noise, ambient occlusion, pointiness, facing up,
height and painted attributes; fog as a ground layer and as the Mist pass; scattering whose density follows a painted
vertex group (left over right 3.758 random, 3.801 Poisson, for weights 1.0 and 0.25); glow, chromatic aberration,
vignette, grain and a grade in the compositor. The first runs had two faulty tests (an edge at the frame's centre,
where radial dispersion moves nothing; a fog volume 150 m tall that dimmed the sun) and one guessed pointiness ramp;
each was redone, and the traps they exposed are on the page: a world volume blacks out a sunlit scene, EEVEE volumes
end at 100 m and do not shadow the sun by default, pointiness is Cycles only and narrow, EEVEE's AO is about half of
Cycles'. What the settings leave out is what 14 and 13 of the 17 artists did: work from photographs of a real place,
and model the main objects themselves.

---

### C-005 · A ten-second realistic shot from a brief, by script, overnight on this laptop

**Opened:** 2026-11-23 (night, unattended) · **Closed:** 2026-11-24

**The brief (fixed before the work):** early morning in a forest clearing. A mossy boulder beside a fallen trunk,
ferns and small stones around it on a leaf-litter floor, light ground haze, a low sun through the trees casting
dappled light. The camera dollies slowly towards the boulder, focused on it. 10 seconds at 24 fps (240 frames),
1280 x 720.

1. **WHERE WE ARE.** The guide has each piece measured separately: free scanned assets at real size (C-002),
   add-ons (C-003), and the twelve realism settings (C-004). Nothing has yet been made with all of them at once, or
   moved, or rendered as a sequence.
2. **WHAT WE ARE DOING.** Build the brief's scene by script using only the guide (Poly Haven assets through
   `assets.py`, scattering by painted density, a ground fog layer, a sun on the HDRI's own, a hidden plane casting the
   dappled light, depth of field, the compositor finish with per-frame grain), render all 240 frames headless, and
   check them by numbers.
3. **WHY.** Unknown now: whether the measured pieces combine into an animated shot on 16 GB and an M2 Pro within one
   night, and what breaks when they do (time, memory, flicker, a recipe that does not hold up in motion).
4. **WHAT IS AFFECTED.** New files under `shots/morning-clearing/` (scripts committed; renders git-ignored); any gap
   becomes an experiment and a page line in the next version.
5. **CONCLUSION.** If all 240 frames render within 9 hours, the boulder arrives within 2 % of its stated size, and the
   frame-to-frame flicker (each frame against the mean of its neighbours, before grain) stays at or below 0.01 on
   average, the guide supports a realistic animated shot on this laptop, and its gaps are polish. If not, the failure
   names the gap (time, memory, flicker, or a recipe), and that is the next experiment.
6. **CONSEQUENCE OF NOT DOING IT.** Every measured piece stays a still, and the first real animation request finds out
   at once whether they combine.

**Result (2026-11-24, closed): the bar is met.** All 240 frames rendered (graded and clean), at 22.6 s a frame on
the Metal GPU (max 23.4), 1.51 hours in all against the 9 allowed; Cycles' peak memory was 3.6 GB. The boulder arrived
within 0.044 % of its stated size. Flicker before grain averaged 0.0076 (max 0.0099; no frame above 0.01). The grain
adds 0.0088 on average. The 7.1 MB H.264 video was joined by the Video Sequencer
(`shots/morning-clearing/results.json`, `sheet.png`).

The flicker number is an upper bound, not flicker alone. A frame against the mean of its neighbours also catches the
camera's motion, since the dolly is straight but its image motion is not, and the haze drifts. C-006 separates the two
by comparing render variants over the same frames.

Five gaps found on the way, each now an experiment and a page line (commit 6670fde):
- Poly Haven's plants come as variant sets, and the first build instanced one variant of four.
- Socket identifiers are not keys.
- Resuming a sequence: an empty placeholder counts as done.
- The GPU choice saved in a .blend survives `--factory-startup` on this Mac.
- `kb.py find` with no full match now lists each term.

Two of my diagnoses on the way were wrong (a glTF rotation; socket names) and are recorded as such in the commit.

Seen on the sheet, not measured. These are polish for the next shot, not failures of the bar:
- The boulder, the shot's subject, sits mostly behind the sorrel the density ring put around it.
- The moss barely reads at this distance.
- The trees beyond the clearing are the HDRI, so they show no parallax as the camera moves.


---

### C-006 · What lowers flicker in a moving-camera shot on this laptop, and at what cost

**Opened:** 2026-11-24 (night, unattended) · **Closed:** 2026-11-24

1. **WHERE WE ARE.** C-005's forest shot measured 0.0076 of flicker before grain (each frame against the mean of its
   neighbours, mean over pixels). That figure also contains the camera's motion. The competitions study (section 6)
   reports four claims about flicker, none measured here:
   - low-sample denoised animation flickers;
   - a fixed seed helps only with a still camera;
   - more samples did not cure it in one production (A-01);
   - temporal denoising came from outside Blender.
2. **WHAT WE ARE DOING.** Render frames 101–125 of the shot in seven variants with `experiments/animation/flicker.py`:
   - baseline: 128 samples with OpenImageDenoise and a constant seed;
   - an animated seed;
   - no denoising;
   - 141 % resolution at 64 samples, downscaled;
   - 384 samples;
   - the raw frames run through `bpy.ops.cycles.denoise_animation`;
   - 1,024 samples as the floor.

   Every variant's noise threshold scales with its samples. For each, measure seconds per frame, flicker (mean, 99th
   percentile, and the foreground plants' quarter), detail (neighbouring-pixel difference) and the difference from
   the baseline's frames.
3. **WHY.** Three things are unknown now and will be known after:
   - which of the study's fixes lowers flicker on this machine, by how much, and at what cost in time;
   - how much of C-005's 0.0076 is noise rather than motion;
   - whether `denoise_animation` does anything temporal here. It demands motion-vector passes, so it is built to be
     temporal, but on a Mac it can only use OpenImageDenoise.
4. **WHAT IS AFFECTED.**
   - `areas/animation-video.md`: a flicker section saying which setting to use for a moving camera.
   - `areas/realism.md`: the denoising and grain lines.
   - C-005's flicker figure, which gets re-read as motion plus noise.
   - The bar in the next shot's card.
   - `kb/research/competitions-study.md` section 6: each claim gains a measured line for this machine.
5. **CONCLUSION.** "Excess" means a variant's flicker minus the floor's (1,024 samples).
   - **A fix that works.** If a variant at most 1.5x the baseline's time halves the baseline's excess, and keeps at
     least 90 % of the floor's detail, the guide recommends it for moving shots. If none does, the guide says the only
     cure measured here is samples, and gives the cost curve (128 / 384 / 1,024).
   - **`denoise_animation`.** If its frames differ from the baseline's by less than a tenth of the baseline's excess,
     it is per-frame denoising on this Mac and the guide says so. If its flicker is lower than the baseline's by at
     least a quarter, it is a temporal cure available headless, and the study's "outside Blender" claim gets a
     correction for 4.5.
   - **C-005's figure.** If the floor's flicker is at least half the baseline's, C-005's 0.0076 was mostly motion, and
     future bars are set as excess over a floor. If it is less than half, the figure was mostly noise and stands as a
     flicker figure.
6. **CONSEQUENCE OF NOT DOING IT.** The guide's animation page carries the study's flicker advice unmeasured, one source
   of it says samples did not help, and every shot's flicker figure stays mixed with its motion.

**Known limit, stated before the run:** the measure counts change between frames. Noise that stays fixed in the
picture while the scene moves under it (the constant seed's "dirty lens") changes little from frame to frame and is
undercounted, so the animated seed may score worse here than it looks.

**Result (2026-11-24, closed): no variant is a fix, because at 128 samples there was almost nothing left to fix.**
The 1,024-sample floor flickered 0.00707, which is 97.5 % of the baseline's 0.00725. So the noise left in this moving
shot at 128 samples, denoised, with a constant seed, adds 0.00018 to its flicker, and the rest is the camera and the
haze moving. Numbers: `experiments/animation/results/flicker.json`, `flicker_times.json`, `flicker_verdict.json`;
the change between frames 113 and 114 of every variant is on `flicker_sheet.jpg`.

| Variant | flicker | excess over the floor | seconds a frame | detail, against the floor |
|---|---|---|---|---|
| baseline: 128 samples, denoised, constant seed | 0.00725 | 0.00018 | 22.5 | 0.98 |
| animated seed | 0.00878 | 0.00171 | 22.1 | 0.98 |
| no denoising | 0.01206 | 0.00499 | 20.4 | 2.93 (the noise) |
| 141 % at 64 samples, scaled down | 0.00788 | 0.00081 | 27.1 | 1.07 |
| 384 samples | 0.00718 | 0.00011 | 62.8 | 0.99 |
| raw frames through `denoise_animation` | 0.00726 | 0.00019 | 22.7 | 0.98 |
| 1,024 samples (the floor) | 0.00707 | 0 | 155.5 | 1.00 |

The three clauses, as `flicker_verdict.py` applies them:
- **A fix that works: none.** Only samples lowered the excess: 384 samples to 0.61 of the baseline's at 2.8x the
  time. Everything else raised flicker: the animated seed by 21 %, 141 % at 64 samples by 9 %, no denoising by 66 %.
  So the guide gives the branch the card named: the only cure measured is samples, at 22.5 / 62.8 / 155.5 s a frame
  for 128 / 384 / 1,024. It adds what the card did not foresee, that in a shot like this one 128 samples leave
  little to cure.
- **`denoise_animation`: not temporal here.** Its flicker was the baseline's within 0.14 %, so the study's claim
  that temporal denoising comes from outside Blender stands for 4.5 on this Mac (OpenImageDenoise; OptiX not tested).
  The per-frame clause came out false, but the clause was wrong before the run. It asked the frames to differ from
  the baseline's by less than a tenth of the baseline's excess (0.000018), and any two renders of the same frame
  differ by about 0.005 whatever the setting: a reseeded render by 0.0052, 384 samples by 0.0050, the floor by
  0.0049. `denoise_animation`'s frames differ by 0.0054, inside that band. That is consistent with per-frame
  denoising; the clause as written cannot confirm it.
- **C-005's figure: mostly motion.** The floor is 0.975 of the baseline, above the half the card set. Future bars
  are set as excess over a floor rendered over the same frames.

In the foreground plants the floor flickered more than the baseline (0.00882 against 0.00872). At 128 samples the
denoiser smooths away a little of the leaves' real change between frames; the baseline's detail, 0.98 of the floor's,
says the same.

The known limit held in the direction it warned of: the animated seed scored worst of the denoised variants, and
this measure cannot say whether the constant seed's fixed pattern reads as dirt on the lens. The change maps on the
sheet show the same leaf edges and ground texture for the baseline, 384 samples, `denoise_animation` and the floor,
and speckle across the ground without denoising, but a fixed pattern would not show in a change map either. It was
not judged in motion.

The run was on battery, which I had not checked. From the 92nd frame rendered on, macOS slowed the GPU about
threefold and then slept the machine for 5.7 hours in the middle of the 384-sample variant. Seconds a frame are the
median of the frames rendered on mains power (16 of 25 for those two variants, all 25 for the rest;
`flicker_times.py`). The per-variant means in `flicker.json` (46.5 and 920.3 s) include the slow frames and are not
used. Flicker and detail do not depend on time.


---

### C-007 · A carved jali rebuilt from one museum photograph, judged beside it

**Opened:** 2026-11-24

1. **WHERE WE ARE.** C-005 passed every number on its card, yet on the sheet its subject was hidden and its moss
   unreadable. The competitions study (section 3) finds the same split in juries' words: technique is a floor, and
   what wins is judged by eye. Nothing in the guide has yet been set beside a real photograph, or judged by a person.
2. **WHAT WE ARE DOING.** Rebuild one carved red-sandstone window screen (jali; Agra area, 1630–50, Louvre Abu Dhabi)
   from one frontal photograph of it (Prof. Mortel, Flickr, CC BY 2.0; `shots/jali-match/photo/`), by script, and
   render it from the photo's viewpoint (`read_photo.py`, `build.py`, `compare.py`).
   - Only three things come from the photo: the outline of the stone and its openings (traced), the stone's hue (its
     median colour), and two light powers fitted so the stone's and the openings' median brightness match.
   - Made here: the solid (the traced outline extruded to 6.1 cm, edges rounded 3 mm), a rounded profile on the bars
     (a height made by blurring the outline, not from the photo's shading), a procedural sandstone with pale specks, a
     pale wall behind, a spotlight from above and in front, and a camera from the photo's EXIF (24 mm equivalent).
   - The size is an estimate from comparable screens (1.05 m wide; `photo/CREDIT.md`).
3. **WHY.** Unknown now: whether the guide's pieces make an object a person takes for the photographed one, and if
   not, which part gives it away. Only a judge can answer the first; C-005 showed the numbers alone do not.
4. **WHAT IS AFFECTED.**
   - New: `shots/jali-match/` (scripts, the photo and its credit, `results.json`, `sheet.jpg`).
   - A section on matching a photograph in `areas/production.md`, with whatever the build found that the guide lacked.
   - The next card: the user's reason, if the answer is no.
5. **CONCLUSION.** The measures come first, then the judge.
   - Measures, inside the screen: the openings agree with the photo's at an IoU of at least 0.90, and the stone's
     contrast (90th minus 10th percentile of luminance, which nothing is fitted to) is within 20 % of the photo's. If
     either fails, that is fixed before the user sees the sheet, and the failure is recorded.
   - The judge: the user sees `sheet.jpg` and answers one question: *at a glance, could the render be a photograph of
     the same screen?*
   - If yes, the guide gets a photo-to-model recipe for pierced work (screens, grilles, fretwork), and the next shot's
     hero subject is built that way.
   - If no, the user's reason is written here in their words (carving depth, stone, light, edges, or something else),
     and it becomes the next card. The measures say whether the miss is in the shape or the tone.
6. **CONSEQUENCE OF NOT DOING IT.** The guide's realism stays judged by numbers that C-005 showed pass shots a viewer
   would not take for real, and the photo match stays the one check nobody has run.

**Known limits, stated before the run:**
- The openings come from the photo, so the IoU measures the build (thickness, rounding, camera), not the ability to
  design a jali. Designing one from rules is a different question.
- The carving on the bars' faces (incised lines, petals) is not traced; only the silhouette is. A "no" is most likely to
  come from there.
- The stone's and openings' median brightness are fitted, so they cannot fail; they are reported, not judged.

**Measures (2026-11-24, before the judge): both fail.** `shots/jali-match/results/compare.json`, `sheet.jpg`.
- Openings IoU 0.565 against the bar of 0.90: 0.40 in the top third, 0.69 in the middle, 0.53 at the bottom. Of the
  photo's opening pixels the render shows 67 % as opening, 21 % as stone and 12 % as dark; 19 % of the render's
  openings fall on the photo's stone, in slivers along the edges.
- Stone contrast 0.315 against the photo's 0.529, a ratio of 0.59 against the bar of 0.8 to 1.2.
- Fitted, reported only: the stone's median luminance 0.347 (photo 0.339); the openings' 0.856 (photo 0.702), brighter
  because the fit counts dim wall by colour and the measure does not.

Fixed before showing, in order, each found by looking at the sheet or the numbers:
1. The rule for openings. Saturation below 0.22 and luminance at least 0.30 found 6.9 % openings (3.5 % in the top
   half, against 10.9 % by the rule that replaced it), where the wall behind is dim and warm. Green over red separates them everywhere in
   this photo (stone 0.70 to 0.80, wall 0.86 to 0.99); at 0.86 the solid frame reads 0.01 % open (`common.py`).
2. The trace kept the plinth and the stand behind the screen. It is now cut to the screen's box. Dark pixels inside it
   are stone, not holes: their green over red is below 0.6, the stone's colour in shadow, not the wall's.
3. The wall was a 4 m plane, lit around the screen where the photo is dark. It is now a lit panel hidden behind the
   screen, brighter at the bottom, its two ends fitted to the photo's openings in each half.
4. The fill came out inside out (openings IoU 0.028). The curve's Offset broke the fill of these 600 to 800 nested
   outlines: the front face was 0.24 m2 at -3 mm and 0.09 at +3 mm, against 1.10 at 0 (the outlines enclose 1.15).
   Offset is 0; the traced stone is shrunk one pixel instead, and the edges rounded 1 mm. IoU 0.27.
   `experiments/curves/curve_offset_fill.py` found why: a negative offset grows every hole, and where holes grow into
   each other the overlaps fill in.
5. Every opening was narrowed twice. The photo shows what can be seen through each hole, which is already narrowed by
   the stone's depth (at 6.1 cm and 1.28 m, by up to 23 mm at the edges); extruding that narrowed it again. Each
   traced opening is now joined with itself scaled out by the back face's projection (1 / 0.9546). IoU 0.53.
6. The panel behind covered only 75 % of the screen as the camera sees it, so the top and bottom openings looked past
   it into black. It now covers 95 %. IoU 0.565.

Why the bars still fail:
- The openings' bar was set without working out what one pixel costs at this scale. An opening 10 px wide shifted by
  one pixel scores 9 / 11 = 0.82 on its own, and the photo's edges are soft over about two pixels. The misses left
  are edge slivers on every opening, plus dark inner walls and a dim wall in the top third.
- The photo's contrast comes from relief carving inside the stone: raised flowers and leaves over a recessed ground.
  The build has none of it (the known limit above), so its stone is a flat slab with a rounded bump.

Blender aborted once 4 s into a build (exit -6, before rendering) and ran clean on the rerun; not reproduced.

**The judge (2026-11-24): no.** In the user's words, looking at the sheet: "it is looks very surreal. Bits are popping
in and out like layers out of sand. The individual small tracing of lining on the individual pieces being connected
are not there, and so our render renders it as something plain but it is not. It does not capture the lighting in the
original picture, and gives us a darker muddier look."

**Result (2026-11-24, closed): no. The build places the openings to within a few pixels and gets the stone's average
colour right, and has none of the carving.** What the measures say about each of the three reasons:
- *Plain; the lines on the individual pieces are missing.* Shape, inside the stone. In the photo each leaf, petal and
  bar is outlined by a cut line and stands over a recessed ground. Nothing traced that (the known limit above): the
  build's stone is one flat slab with a rounded bump.
- *Darker and muddier.* Tone, from the same cause. The stone's median colour matched (photo 0.435, 0.322, 0.239;
  render 0.439, 0.329, 0.251) and its median luminance was fitted equal (0.339 and 0.347). The bright end did not:
  the photo's carving reaches 0.657 at the 90th percentile and 0.795 at the 99th, the render 0.493 and 0.575. With no
  raised surfaces facing the light, nothing in the render catches it.
- *Bits popping in and out like layers out of sand.* Shape, at the openings' edges: 21 % of the photo's opening pixels
  are stone in the render, and 19 % of the render's openings are stone in the photo, in slivers along every edge.
  Through a 6.1 cm slab each opening's inner walls also show as bands. Not checked: whether the half-resolution trace,
  and the union with the scaled-out copy (which can give an opening a stepped double edge), make the slivers.

The "no" branch applies: these reasons are the next card. The guide gains, whatever the verdict, what the build found
on the way: `areas/production.md` ("Rebuilding a pierced object from one photograph") and `areas/curves-text.md`
(item 8, the Offset).

---

### C-008 · The jali's carved lines traced from the photo and cut into its stone, judged beside it again

**Opened:** 2026-11-24

1. **WHERE WE ARE.** C-007's jali was judged "plain", "darker muddier" and "like layers out of sand". Its openings
   agree with the photo's at an IoU of 0.565 and its stone's median colour matches, but its bright end is 0.493 at the
   90th percentile against the photo's 0.657: one flat slab, with nothing raised to catch the light.
2. **WHAT WE ARE DOING.** Give the screen a carved front, traced from the photo the way its openings were, and
   render it again from the same camera (`shots/jali-match/`).
   - The cut lines: thin dark lines inside the stone, found by one rule (darker than their surroundings at a small
     scale, and thin) applied alike to the photo and the render.
   - The relief: every piece between cut lines and openings rises with a rounded profile, 6 mm at most, falling to
     0 at its edges, so each line becomes a groove. All pieces rise alike: which are raised and which are ground is
     not traced.
   - The geometry: a grid at the photo's pixel spacing (0.92 mm) laid on the front face and lifted by that height,
     over the extruded body from C-007, whose side walls stay. Outlines smaller than 30 px are dropped, against 12
     before, for the slivers.
3. **WHY.** Unknown now: whether the lines and the light the judge missed come back from traced grooves on rounded
   pieces, or whether the look also needs the levels of the carving (raised flowers over a recessed ground), which
   lines alone cannot give.
4. **WHAT IS AFFECTED.**
   - `shots/jali-match/`: `read_photo.py` traces the lines, `build.py` builds the relief, `compare.py` measures lines
     and the bright end. Its `results/` files are overwritten; C-007's numbers stay in its card and commit (19d86a3).
   - `areas/production.md`, "Rebuilding a pierced object from one photograph": the relief step and what it measured.
5. **CONCLUSION.** The measures first, set by arithmetic this time, then the judge.
   - Lines: the render's lines found within 2 px of the photo's, and the photo's within 2 px of the render's, both
     at least 0.6. A 2 px allowance because a line is 2 to 4 px wide here, and C-007 showed a one-pixel slip costs a
     thin shape most of an exact-overlap score.
   - Light: the stone's 90th percentile of luminance within 15 % of the photo's 0.657 (0.56 to 0.76), and its
     contrast (90th minus 10th percentile) within C-007's bar, 0.8 to 1.2 of the photo's.
   - A guard: the openings' IoU stays at least 0.52, so the relief has not broken what C-007 got right.
   - The judge: the user sees `sheet.jpg` and answers the same question, *at a glance, could the render be a
     photograph of the same screen?* If yes, the guide gets the photo-to-model recipe for carved and pierced work
     (trace the openings, trace the lines, rise the pieces). If no, the reason in the user's words is the next card,
     and the measures say whether it is the lines, the light, or something they do not measure (the levels are the
     likeliest).
6. **CONSEQUENCE OF NOT DOING IT.** The guide can trace a carved object's silhouette and nothing inside it, so any
   carved subject (screens, panels, reliefs, furniture) renders as a flat board with holes.

**Known limits, stated before the run:**
- The lines come from the photo's shading at a threshold, as the openings came from its colour; a groove the light
  does not show is not traced.
- Every piece rises the same 6 mm; the carving's levels are not modelled.

**Measures (2026-11-24, before the judge): lines and light fail, the guard holds.**
`shots/jali-match/results/compare.json`, `sheet.jpg`.
- Lines: 57 % of the render's lines lie within 2 px of the photo's, and 39 % of the photo's within 2 px of the
  render's, against 60 % both ways.
- Light: the stone's 90th percentile is 0.466 against the photo's 0.656 (bar 0.557 to 0.754), and its contrast 0.51
  of the photo's (bar 0.8 to 1.2). The median was fitted (0.344 against 0.337).
- Guard: the openings' IoU is 0.725, above 0.52, and up from C-007's 0.565 (0.64, 0.76, 0.76 by thirds). The render
  shows 83 % of the photo's see-through pixels as see-through; 14 % of its own fall on the photo's stone.
- Reported: the openings' median luminance 0.680 against the photo's 0.686, now set, not fitted.

Changed before showing, in order, each from the sheet or the numbers:
1. The relief as the card wrote it (every piece between the lines rising 6 mm on its own) read as crumbled rock: the
   lines, 6 % of the stone, cut it into hundreds of small humps. The bars now round across their width by distance
   from the nearest opening, and the lines are cut into that surface.
2. Distance counted by erosions stepped in blocks; it is now the stone mask blurred, eased (smoothstep).
3. The field's thickness is fitted. Widening each opening for 6.1 cm swallowed front stone (a whole four-petal flower
   became a hole), and the openings agree best when the field is thin: IoU 0.564 at 61 mm, 0.685 at 40, 0.721 at 30,
   0.737 at 20, 0.746 at 15, 0.754 at 10. Either the pierced field is thinner than the catalogue's overall depth or
   its holes splay; neither is checked. 20 mm is taken, within 0.02 of the best.
4. The opening rule missed about half the wall in the middle of the screen, where it is dim and warm (green over red
   0.82 to 0.85, under the 0.86 cut). A second rule now joins it: a pixel close in colour to the wall's local colour
   (a field estimated from the sure pixels) and smooth. Smoothness alone let the render's stone in, which is smooth
   everywhere, so the second rule also needs green over red above 0.80. Openings 12.8 % of the screen against 11.7.
5. The wall is set from the photo in ten bands from top to bottom, not fitted: it only emits and is seen straight
   through the openings, so its colour is its emission through the sRGB curve. C-007's two-number fit kept dimming
   the panel's top.
6. The carving deepened: bars 10 mm, reached 18 mm in; grooves 3 mm and wider; the spot's shadows crisper (0.02 m).
7. Short dashes dropped from the lines (fewer than 8 line pixels in a 9 x 9 window): cut as grooves they read as pits.
8. Tried and not kept: Blender's contrast looks, since the photo was edited (Polarr). Medium High Contrast and High
   Contrast raised the stone's contrast to 0.56 and 0.61 of the photo's but pushed the wall to 0.73 and 0.83.
   Reading the `look` enum from `bl_rna` lists only NONE; the eight looks appear once the view is Standard.

How it looks to me, before the judge: smooth clay with pockmarks. The line rule finds the shadowed sides of shapes, in
pieces, not their outlines, and the carved forms (domed petals and leaves over a recessed ground) are still not built.

**The judge (2026-11-24): no.** In the user's words, looking at the sheet and at one junction of the lattice in each:
"it is another no. We are not capturing that fine line of details and carvings in the stone. [...] there are little
incisions across the model, but they don't capture the symmetrical alignment and pertuberance from the original
picture."

**Result (2026-11-24, closed): no. Traced lines cut as grooves give scattered incisions; the carving's order and its
raised forms are not there.** The two things the judge named are both outside what the card built:
- *Symmetrical alignment.* The photo's motifs are mirror-symmetric (the lotus at each junction of the bars, the leaves
  either side of it) and the lattice repeats. The line rule traces each pixel's shadow on its own, so whatever symmetry
  the stone has, the trace has only where the light happens to show it, and the lines measure says as much: 39 % of
  the photo's lines have a render line within 2 px.
- *Protuberance.* The photo's petals, leaves and the bars' raised rims bulge out as forms. The build has one height
  rule for all of it (bars rounded by distance from the openings), so no form rises on its own, and the stone's
  bright end stays low: 0.466 at the 90th percentile against 0.656.
What did improve, and stays: the openings (IoU 0.725 against 0.565) and the wall's light, now set from the photo.

The "no" branch applies again: the judge's reasons are the next card.
