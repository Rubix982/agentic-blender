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

---

### C-009 · The jali rebuilt from one motif, averaged over its repeats and mirror halves, judged beside the photo

**Opened:** 2026-11-24

1. **WHERE WE ARE.** C-008's jali was judged "little incisions [...] they don't capture the symmetrical alignment and
   pertuberance". Its openings agree with the photo's at an IoU of 0.725, but 39 % of the photo's cut lines have a
   render line within 2 px, and the stone's bright end is 0.466 against 0.656: each pixel's shadow was traced on its
   own, and every bar got the same rounded rise.
2. **WHAT WE ARE DOING.** Rebuild the carved field from the photo's own symmetry (`shots/jali-match/`).
   - Find the lattice's two repeat vectors (the peaks of the openings' autocorrelation) and the screen's vertical
     mirror axis (where the field best matches its own mirror image).
   - Average the photo over every repeat that falls in the lattice, and the result with its mirror image, after
     dividing out the light's slow change across the screen. Outside the lattice (the arch and its scrolls at the
     top) only the mirror is averaged.
   - From that average: the openings (the averaged opening mask at 0.5), and the raised forms, as heights read from
     the averaged shading with the light from above. A surface lit brighter than its surroundings faces up, so the
     height is the shading integrated down each column of stone, brought back to 0 at the openings.
   - Build, light and render as in C-008, from the same camera.
3. **WHY.** Unknown now: whether the photo's motif, cleaned of noise and of the light's gradient by averaging its
   repeats, carries the carving's order and its raised forms well enough to read heights from, or whether the
   repeats differ too much (it is carved by hand) for an average to stand for them.
4. **WHAT IS AFFECTED.**
   - `shots/jali-match/`: a new `symmetry.py` (the repeat, the axis, the averaged field), `build.py` building from it,
     `compare.py` with the measures below. Its `results/` files are overwritten; C-008's are kept as `*_c008.json`.
   - `areas/production.md`'s photo section: the averaging step and what it measured.
5. **CONCLUSION.**
   - The repeat first: each repeat's opening mask against the average's, as a correlation. If the median is below
     0.5, the lattice is not one repeated motif in this photo; the card stops there with that number, and the next
     card works from the mirror alone.
   - Then the measures, as C-008 set them: the cut lines within 2 px both ways at least 0.6; the stone's 90th
     percentile within 15 % of the photo's 0.656 and its contrast within 0.8 to 1.2 of the photo's; and a guard, the
     openings' IoU at least 0.68 (an average smooths each repeat's own edges, so some loss is expected).
   - Then the judge, the same question. If yes, the guide gets the photo-to-model recipe for carved repeating work
     (find the repeat, average it, read the relief, build it once and repeat it). If no, the user's reason in their
     words is the next card, and the measures say whether it was the motif (the repeat's correlation, the lines) or
     its relief (the light).
6. **CONSEQUENCE OF NOT DOING IT.** The guide's photo method stops at outlines and one rounded rise, and any carved,
   repeating subject renders as incisions on a board.

**Known limits, stated before the run:**
- Heights from shading assume one light from above and stone of one colour; dark weathering reads as a hollow.
- An average is regular where the hand-carved original is not. A render more perfect than the stone may itself read
  as false.
- The arch and scrolls at the top are averaged only with their mirror, so they keep more of the photo's noise.

**The repeat (2026-11-24): the stop rule fired, and was recorded as mis-specified on the user's choice.** The lattice's
repeat vectors are (141.2, -176.9) and (146.3, 173.0) px, a staggered lattice whose sum (286.4, -3.6) is the strongest
autocorrelation peak (0.354); the mirror axis is x = 612, 3 px left of centre (mirror correlation 0.355). (A first pick
took a weak short peak, 0.18 at 29 px, an echo inside each motif; the vectors now come from the strong peaks only.)
Each repeat's openings against the average's, median 0.485, under the card's 0.5. Split by how far apart the copies
are, the rule mixed two things: one step 0.61, two 0.63, three 0.55, four 0.42, five 0.44, six 0.17. Neighbours agree;
far copies, which were most of the pool, do not, which fits effects that change across the screen (the light, the depth
narrowing the openings, a fraction of a pixel of error in the vectors growing with each step). The user chose to record
the rule as mis-specified and continue with repeats up to 3 steps away: median 0.586 over those as first
averaged, 0.502 once each copy was registered (0.64, 0.50, 0.48 at one, two and three steps).

**Measures (2026-11-24, before the judge): lines and light fail, the guard holds.** `results/compare.json`,
`results/symmetry.json`, `sheet.jpg`.
- Lines: 49 % of the render's within 2 px of the photo's, 30 % the other way (bar 60 %); C-008 had 57 and 39.
- Light: the stone's 90th percentile 0.457 against 0.656 (bar 0.557 to 0.754); contrast 0.44 of the photo's (bar 0.8).
- Guard: openings IoU 0.726 (bar 0.68).

Changed before showing, in order:
1. The average first blurred and ghosted the motif: 37 copies a few pixels out of register (the lattice is not exact
   across a hand-carved screen seen in perspective). Each copy is now registered per pixel, the best match of its
   15 x 15 neighbourhood within 3 px, and weighted more sharply. The averaged shading then shows the motif cleanly: the
   flower, the bars' incised rims, the leaves, with the photo's specks gone (`out/symmetry.png`).
2. Heights integrated down each column alone came out in vertical streaks; they are now one least-squares solve over
   all the stone (conjugate gradients, 288 iterations), the slope down the picture following the shading and
   neighbouring columns asked to agree.
3. The averaged openings, used first, smoothed every repeat's edges and in the arch mixed in copies that do not belong
   (IoU 0.55, 0.29 in the top third). The openings are the photo's own again; the average gives only the heights.
4. The forms at 6 mm (99th percentile) reached 17 mm and read as melted; now 4 mm, clipped at 6.

How it looks to me, before the judge: sculpted, with raised forms where C-008 had pits, but soft, like melted wax. The
averaged shading has the crisp edges and rims; the step from shading to height loses them.

**The user's first look (2026-11-24):** "The sheet is much better than before, though i see missing pieces in between
like this example" (a thin connecting stem broken, wall showing where the photo has stone). Measured before changing
anything, on the photo's thin stone (strips about 4 px wide or less, 2.3 % of the field's stone): the widening for depth
kept 61.5 % of it, the one-pixel shrink kept for C-007's bevel left 6.8 %, the trace's blur 2.4 %, and the render
showed 39 % of it as stone. The shrink is gone (the bevel is 0.5 mm and nothing makes up for it): the render now shows
89 % of the thin stone as stone, the openings' IoU is 0.725, the lines 49 % and 32 %, the bright end 0.457.
`--thin-protect` also keeps the widening off thin stone (94 % shown) but costs the openings 0.05 (0.678); it is off.
Still broken: the finest stems, a pixel or two wide at the half resolution this works at.

**The user's second look (2026-11-24):** "better, but rough around the edges" (a close-up of stepped, notched opening
edges). What it was, found by zooming 6x on one edge, photo beside render:
1. The carved skin overhung the smooth outline. It was built from the stone mask after a closing (dilate 2, erode 2)
   meant to fill pin-prick holes, which also bridged every opening under ~4 px wide; there the skin's pixel-stepped
   edge stood out against the wall. Now only holes the stone nearly closes over are filled, and the skin stays 2 px
   inside the stone, its relief faded to 0 over its last ~4 px, so the visible edge is the body's outline.
2. The outlines followed the mask's pixel noise; they are now smoothed without shrinking (Taubin, 20 passes). Six
   passes made no visible change.
3. The render's edges were crisper than the photo's, which a lens and a phone soften over about two pixels: the
   gradient on the openings' edges was 1.072 x the photo's. `render.filter_size` did nothing (Cycles ignores it,
   `experiments/rendering/cycles_pixel_filter.py`); `cycles.filter_width` at 1.8 px makes it 1.001 x.
Now: openings IoU 0.735, thin stone shown 88 %, lines 41 % and 25 %, the bright end 0.454.

**The user's third look (2026-11-24):** "one interesting case here -- it assumed that the line shown onto the original
was actually a gap, but if we look at it carefully, it is just a highly shown part of the frame, it is not empty space"
(a close-up of a bar's pale, lit edge, open in the render). What it was, and what it led to:
1. The rule that sorts the photo called the lit edge wall. Lit sandstone is pale enough to pass the green-over-red cut
   (0.87 to 0.92 against the cut's 0.86), and that cut never asked whether a pixel looked like the wall around it. It
   is brighter than the wall: of the pixels the cut was sure of, the middle half lie between 0.98 and 1.05 of the
   local wall's luminance and the top tenth above 1.27. Now a pixel more than 12 % (plus 0.03) above the local wall is
   lit stone, and the wall's colour field is worked again without those pixels (`common.classify`). It takes 9.6 % of
   what was called opening: 17.5 % in the top half, where the light catches the bars' upper edges against a dim wall,
   and 2.0 % in the bottom. The same close-ups showed some thin pale stems in the top half going the same way, so
   this is probably part of the first look's "missing pieces" too.
2. The first rebuild came out inside out (openings IoU 0.03). Halving the outlines down to one, a smoothed island of
   15 x 4 px (at 983, 138) broke the fill of the whole curve at 0.92 mm a pixel (front face 0.31 m2 of 1.15), and the
   same pair filled correctly at 1 and at 0.01 units a pixel, and unsmoothed. Probably the fill merges points closer
   than a fixed distance; that is not checked. The same outlines fill correctly in pixels, so
   the curve is now built in pixels and its mesh scaled to metres; the build stops if the front face falls below
   85 % of what the outlines enclose. The fill had been losing a little stone before too: its front face is 1.048 m2
   now against 1.028. (Rasterised, the fill in pixels covers every pixel of the traced solid; the 8 % gap to "what
   the outlines enclose" is that sum over-counting, not missing stone.)
Now: openings IoU 0.764 (thirds 0.668, 0.812, 0.777), thin stone shown 89 %, lines 42 % and 25 %, the bright end
0.465 against the photo's 0.667 (the photo's own bright end rose, as its lit edges joined the stone). The render's
edges are stone there now, but not lit cream as the photo's are: the bright end is the open miss.

**The judge (2026-11-24):** "It has vastly improved even further." The user closed the card there, to take up the
research threads opened today (T-009 to T-013). The card's question was not answered yes.

**Result (2026-11-24, closed): not a yes, but judged much improved; the measures still fail on the lines and the
light.** The motif averaged over its near repeats and its mirror half, the heights solved from its shading, and the
fixes the user's three looks led to (thin pieces kept, edges smoothed and softened, lit edges made stone) give openings
at an IoU of 0.764 (guard 0.68), 89 % of the photo's thin pieces shown, and edges 1.04 times as soft as the photo's.
What fails is what C-008 failed on: 42 % of the render's lines lie within 2 px of the photo's and 25 % the other way
(bar 60 %), and the stone's bright end is 0.465 against 0.667 (bar 0.567 to 0.767), its contrast 0.43 of the photo's.
The relief is still soft and the lit rims are not lit: that is T-009. On the final classification the symmetry
re-ran to repeat vectors (141.1, -177.1) and (146.2, 173.3) px, the mirror axis at x = 613 (0.360), and registered
repeats at a median 0.491 against the average (0.64, 0.49, 0.47 at one, two and three steps;
`results/symmetry.json`). The guide's photo section has the findings (`areas/production.md`, items 8 to 12), and
`areas/curves-text.md` the fill that broke at millimetre scale (item 9).

### C-011 · The jali's relief from a learned normal map of its photo, judged beside the photo

**Opened:** 2026-11-24 (C-010 stays reserved for the interface test)

1. **WHERE WE ARE.** C-009 closed not a yes: openings at an IoU of 0.764, but the relief soft and the lit rims unlit.
   Its forms are heights summed from the shading's up-down slope, which rounds every carved step (`production.md`,
   item 9). A new detail measure, taken on C-009's render before this card's build: in a forms band (luminance blurred
   over 5 px minus over 21 px, on stone at least 3 px from any opening), the render correlates with the photo at
   0.399 with 0.495 of its amplitude. The photo against itself shifted 2 px diagonally gives 0.549, 1 px gives 0.858.
2. **WHAT WE ARE DOING.** Predict which way the carving's surface faces at every pixel of the photo with Marigold
   normals v1.1 (`prs-eth/marigold-normals-v1-1`, in `diffusers`, already in this laptop's model cache), integrate
   those normals into heights, and build, light and render the jali with them in place of C-009's forms.
   - The model runs on the photo at the working size (1230 x 1402) in overlapping tiles at its own processing size, so
     the detail is not shrunk to fit one pass; the tiles are blended with feathered weights.
   - Heights: least squares on the slopes the normals give, over the stone, 0 at the openings, in pixels of height per
     pixel, so in metres with no scale fitted. If their 99th percentile falls outside 2 to 12 mm, they are scaled to
     C-009's 4 mm instead, and that is recorded.
   - The openings stay the photo's own, and the bars' rounded profile is dropped: the normals carry it.
   - Built, lit (the spot fitted to the stone's median, as before) and rendered from the same camera.
3. **WHY.** Unknown now: whether a model trained on many images gives this carving's steps and rims from one top-lit
   photo, at this scale and on this laptop, or rounds them as the shading integration does.
4. **WHAT IS AFFECTED.**
   - New: `shots/jali-match/normals.py` (run in the repo's own `.venv`, not Blender; its requirements pinned beside it)
     and `.venv/` in `.gitignore`. `build.py` takes `--forms normals` (C-009's stays as `--forms shading`, the default
     until this card closes). `compare.py`'s detail measure, added before the run.
   - `results/` overwritten; C-009's kept as `*_c009.json`. `sheet.jpg`.
   - `areas/production.md`'s photo section, either way; T-010's answer; T-013 gets the forms band as a first candidate.
5. **CONCLUSION.** The measures first, then the judge.
   - Measures: the forms band's correlation at least 0.50 and its amplitude 0.8 to 1.2 of the photo's; the stone's
     90th percentile within 15 % of the photo's (0.567 to 0.767). Reported, not judged: the fine band (the photo
     against itself 1 px off gives 0.128 there, so it is grain), the lines, and the openings' IoU, which should stay
     within 0.01 of 0.764 as a check that only the relief changed.
   - The judge: *at a glance, could the render be a photograph of the same screen?*
   - If the measures pass and the answer is yes, the guide gets the recipe (relief from one photo by a learned normal
     map, integrated), and T-010 is answered yes.
   - If the forms band rises to 0.50 but the answer is no, the user's reason is the next card.
   - If the forms band does not rise above 0.399, this model at this scale does not give this carving's relief:
     T-010 is answered no for Marigold, and the next card tries another model or T-011.
6. **CONSEQUENCE OF NOT DOING IT.** The relief stays soft, and the guide's photo method can place a carving's openings
   but not carve it.

**Known limits, stated before the run:**
- The normals are what the model believes, not measured. It was trained mostly on synthetic scenes, and a weathered
  carving lit from above may be outside them.
- Tiles can disagree where they meet; the feathering hides a small disagreement, not a large one.
- The photo's own normals are used, not averaged over the repeats: its irregularities come back with its detail.

**The normals (2026-11-24).** Six tiles of 768 px, 3-member ensembles, 4 steps, fp16 on the laptop's GPU: 9 s a tile,
56 s in all (`results/normals.json`). Where tiles overlap they disagree by a median 6.2 degrees (90th percentile 16).
The up-facing part correlates with the photo's forms band at 0.34 (the light is from above, so the sign is right).
Seen as an image they carry the carving: bars, petals, flower centres, scrolls, the incised lines along the bars.

**Measures (2026-11-24), in the order they were taken.** C-009's render: forms band 0.399, amplitude 0.495, the
bright end 0.465.
1. As the card specified (`results/*_c011_first.json`): the heights' 99th percentile came out 14.8 mm, outside the
   2 to 12 mm window, so they were scaled to 4 mm (x 0.27). The forms band fell to 0.280 (amplitude 0.272), under
   C-009's 0.399: by the card's third branch, a no. Looking before taking it: the heights were broad bulges about a
   hundred pixels across, slope errors summed over the wide stone, and they set the 99th percentile; scaled to fit,
   the carving under them was flattened to a quarter.
2. Changed: the solve screened at 30 px (each height also pulled towards 0 with weight 1/30^2, so slope errors cannot
   add up over more than about that). The heights' 99th percentile 8.85 mm, inside the window, so no scale
   (`results/*_c011_screened.json`). The forms band 0.380, amplitude 0.374: about C-009's, not above it. Looking
   again: the normals, and the shading they imply under a light from above and in front, carry the carving almost
   exactly; the heights made from them do not. The solve smooths it, and the skin's edge fade takes all the relief
   off any bar under about 12 px wide.
3. Changed, past what the card said it would do: the normals also shade the front, as an object-space normal map
   (`--normal-map`), used only where the surface faces the camera; the screened heights still give the forms their
   shadows. The forms band **0.549** (the photo against itself 2 px off gives 0.549), amplitude **0.417**; the fine
   band 0.097 (C-009 0.066); the bright end **0.470** against 0.667; contrast 0.46 of the photo's; lines 49 % and 25 %;
   openings IoU 0.761 (C-009 0.764, so only the relief changed).
So: the forms band passes (0.50), its amplitude fails (0.8 to 1.2), and the bright end fails (0.567 to 0.767). The
carving's light and dark now fall where the photo's do, at less than half the strength. Both failures are the light:
the photo's spot pools on the centre and leaves the frame dark, and lights the rims cream; the render's is even and
dim. Seen on the sheet: the flower, its petals and centre, the fleur, the scrolls read; the frame is as bright as the
centre, and nothing catches the light as the photo's rims do.

**The user's first look (2026-11-24):** "this is really nice now! can we work on the bottom part? [...] still some
remants of the missing arches" (a close-up of the bottom row: stubs where the photo has small arches and lobes).
1. The rule that sorts the photo called that stone wall, the mirror of C-009's lit edges. At the bottom the wall
   behind is lit almost white, and the stone in front of it is pale and greyish, so it passed the green-over-red cut;
   but it is darker than the wall around it. Of what the cut called opening, 47 % lay more than 15 % below the local
   wall's luminance in the bottom band, against 0.8 % in the top half, where smooth wall pixels never went below
   0.95 of it (5th percentile). Now a pixel more than 15 % (less 0.03) below the local wall is stone too
   (`common.classify`): it takes 10.9 % of what C-009's rule called opening, 0.3 %, 2.3 % and 28.8 % by thirds from
   the top. Zoomed in, what it takes are the pale lobes and arches; the openings left are the photo's bright gaps.
2. The openings' IoU fell to 0.735, in the bottom third most (0.774 to 0.729). In the render the same rule now calls
   the darkened inner walls of every hole stone, which they are, and the render showed more of them than the photo
   does: 22 % of the photo's openings were stone in the render, against 16 %. The field's thickness, fitted in C-008
   under the old rule, was swept again: openings IoU 0.7596 at 10 mm, 0.7501 at 15, 0.7354 at 20, 0.715 at 25
   (`results/compare_c011_t*.json`). It is now 10 mm (`--thick 0.010`). At 5 mm the fill broke at several holes and
   could not be repaired, so the sweep stops at 10.
3. At 15 mm the curve's fill broke again, in pixels this time, at the same small smoothed island as in C-009 (about
   981, 141), so building in pixels was not the cure C-009 took it for. The build now repairs it: halving the
   outlines finds the one that breaks the fill, which is swapped for its unsmoothed outline (dropped if that breaks
   it too), and the repair is logged (`results/build_c011_t015.json`). Why it breaks is still T-014.
Now (10 mm): openings IoU 0.760 (thirds 0.684, 0.802, 0.772), thin stone shown 96 % (89 % before), the forms band
0.548 with 0.44 of the photo's amplitude, the bright end 0.478 against 0.669, lines 50 % and 22 %. The bottom row's
arches and lobes now run along the frame as in the photo.

**The user's second look (2026-11-24):** "It is really better now! Great stuff! One last thing to add further ... the
original has this kind of "scratches" all around, like the sides have these uneven indentations [...] but ours is VERY
smooth" (close-ups of the frame's lower band).
1. Marigold's normals are flat on the frame: their up-down part varies 0.07 there against 0.28 in the carved field; the
   model sees a plain band and gives it a smooth surface. A new measure, the frame's texture (each band's spread on the
   frame's stone, render over photo): 0.26 in the fine band, 0.56 in the forms band (that one includes the mouldings).
2. Tried first: the photo's own light and dark as a bump, dark as low. At 5 mm per unit the frame's fine texture came to
   0.81 of the photo's, but the fine band's correlation went to -0.20 and the forms band's fell to 0.485: a bump's
   shading follows its slope, not its height, so each scratch's light and dark landed half a feature off the photo's
   (`results/*_c011_bump005.json`).
3. Instead the normals are tilted towards the light from above by A x the photo's light and dark (`--photo-detail A`):
   its fine band on all stone, its forms band only where the normals are flat. Swept: at A = 2, 4, 8, 12 the frame's
   fine texture came to 0.36, 0.55, 0.94, 1.25 of the photo's and its forms texture to 0.63, 0.76, 1.05, 1.30
   (`results/*_c011_tilt*.json`). At 8, on the carving, the photo's pale specks became bumps and it read as crusted;
   so the fine band is used at 0.3 of A where the normals are not flat.
Now (A = 8, 0.3 on the carving): the frame's texture 0.75 and 0.99 of the photo's; openings IoU 0.760; thin stone
96 %; the bright end 0.478 against 0.669. The detail measure is no longer independent of the photo: its light and dark
are now partly built in, so the forms band (0.653) and the fine band (0.352, where the photo against itself 1 px off
gives 0.128) partly measure the photo against itself. The frame and the bars now carry pits and scratches.

**Integrated (2026-11-24).** These settings are now `build.py`'s defaults (normals' forms screened at 30 px, the normal
map, the photo's detail at 8 and 0.3 on the carving, 10 mm), each earlier build a switch away; the build skips the
symmetry pass the normals do not use (32 s against 85) and stops with a message if the normals are missing.
`make.py` runs the chain (read_photo, normals, build, compare; the normals only when out of date), and
`shots/jali-match/README.md` says how. Run from scratch with the normals recomputed, it gave the same numbers to four
decimals (the normals identical to the last bit); `-- --forms shading --no-normal-map --photo-detail 0 --thick 0.020`
still builds C-009's version (openings 0.735, forms band 0.421, frame texture 0.30 and 0.55).

**The judge (2026-11-24):** "At a glance, yes, it seems like, it would become better if we worked on the lighting part,
but that is already documented."

**Result (2026-11-24, closed): yes, at a glance, with the light as its limit.** A learned normal map of the photo
(Marigold normals v1.1, run locally) gives the carving that one top-lit photo's shading could not: used as the front's
normals, with heights integrated from them (screened at 30 px) for the forms' shadows, the forms band rose from C-009's
0.399 to 0.549 before the photo's own detail was added, where the photo against itself 2 px off gives 0.557. Then,
from the user's two looks: the dim test in the photo's rule (the bottom row's arches), the thickness re-fitted to
10 mm, the fill repaired by halving, and the weathering from the photo's own light and dark tilting the normals (the
frame's texture 0.75 and 0.99 of the photo's, from 0.26 and 0.56). Final: openings IoU 0.760, thin stone 96 %, the
forms band 0.653 (partly the photo against itself now). Of the card's measures the forms band passed and the light
failed: the forms band's amplitude 0.53 (bar 0.8 to 1.2) and the stone's bright end 0.478 against 0.669 (bar 0.567 to
0.767). So the guide gets the recipe, with the light as its stated limit (`areas/production.md`, items 13 to 18), and
T-010 is answered yes for Marigold. The light, which the user names as what would make it better, is T-015.

### C-012 · The museum's light fitted: where the spot pools, not only how bright it is

**Opened:** 2026-11-24

1. **WHERE WE ARE.** C-011 closed "at a glance, yes", the light named as what would make it better. Measured before
   this card's work, on C-011's render: the stone's bright end 0.478 against the photo's 0.669, its contrast 0.51 of
   the photo's. A new light map (the stone's median in 6 x 7 cells over the screen, each over the median cell) shows
   why: the photo's light pools in the upper middle (1.19 to 1.51) and falls to 0.36 to 0.79 at the sides and 0.39
   to 0.82 along the bottom; the render's falls evenly from top (1.26 to 1.35) to bottom (0.69 to 0.76) and not at all
   from side to side. The error, the RMS of log(render / photo) over the cells, is 0.443. The light's direction is not
   the problem: the shading Marigold's normals give under each direction matches the photo's best at 55 to 60 degrees
   up and 0 to 10 degrees to the right (0.598), and the spot's own (59 degrees up, straight on) gives 0.596.
2. **WHAT WE ARE DOING.** Fit the spotlight's aim on the screen, its distance, its cone and its blend so the render's
   light map matches the photo's, keeping its direction, then its power to the stone's median as before.
   - Each candidate rendered at 25 % size and 32 samples; its light map from the photo's stone mask at that size; a
     coordinate search over the four (two rounds, a handful of values each), the error as above.
   - In `build.py`, in place of the fixed spot (which stays as `--fixed-light`); the final render as before.
3. **WHY.** Unknown now: whether one spot can make this photo's pool, and if it does, how much of the missing bright
   end and contrast was the pool and how much is left for the phone's tone curve or a second light.
4. **WHAT IS AFFECTED.**
   - `build.py`'s light (`--fixed-light` keeps C-011's); `compare.py`'s light map (added before the work).
   - `results/` overwritten; C-011's kept as `*_c011.json`. `sheet.jpg`. `areas/production.md`'s photo section either
     way; `areas/lighting.md` if the fit is a recipe a script can reuse. T-015's answer.
5. **CONCLUSION.** The measures first, then the judge.
   - Measures: the light map's error at most 0.15; then, reported against the bars C-009 set and C-011 kept: the bright
     end within 15 % of the photo's (0.567 to 0.767), the contrast 0.8 to 1.2 of the photo's, and the forms band's
     amplitude 0.8 to 1.2.
   - The judge: *at a glance, could the render be a photograph of the same screen?*, and whether the light now reads
     as the photo's.
   - If the map fits and the bright end and contrast come within their bars, the guide gets the recipe (fit where a
     light pools by a light map, not only its power), and T-015 is answered.
   - If the map fits but the bright end or contrast does not, the pool was only part of it: what is left (the tone
     curve, a second light, the stone's albedo) is the next card, with the numbers that say which.
   - If the map's error stays above 0.15, one spot cannot make this light, and the next card tries two lights or a
     textured one.
6. **CONSEQUENCE OF NOT DOING IT.** The screen stays lit evenly from the top, its frame as bright as its centre, and
   the guide's photo method fits a light's power but never where it falls.

**Known limits, stated before the run:**
- The light map is read from 42 cells; it says where the light pools, not how sharp its edge is.
- The search is coarse and the renders at 25 % are noisy; a fit within the noise is reported as such.
- The photo's processing (the phone's and an editor's tone curve) is not modelled here; the bright end may need it.

**Measures (2026-11-24), in the order they were taken.** C-011's light: map error 0.443, bright end 0.478, contrast
0.51 of the photo's, the forms band's amplitude 0.53. Errors are at the fit's 25 % size, then at full size.
1. As the card said (aim, distance, cone angle, blend; 31 renders): 0.327, 0.322. It aimed lower and softened the
   edge (blend 1.0), and never narrowed the cone. The beam meets the upright screen 59 degrees off its face, which
   stretches a round pool to about twice as tall as wide, and the photo's pool is about as wide as tall; and with the
   cone set by its angle, distance and pool size fought.
2. Changed: the candidates set by the pool's half-height on the screen and its width over a round pool's (the spot
   object scaled sideways), with the aim, distance and blend (53 renders): 0.275, 0.263 (`results/*_c012_grid.json`).
3. Changed: then all six together by Nelder-Mead from that best (126 renders in all, 2.5 minutes): 0.206, **0.198**.
   The spot 4.69 m out, a 13.1 degree cone 1.11 times as wide as round, its edge fully soft, aimed 0.09 m above the
   centre. Kept in `results/light_fit.json`; later builds reuse it (`--refit-light` searches again), 34 s a build.
Against the bars: the map's error 0.198 (bar 0.15) fails; the bright end 0.514 against 0.669 (bar 0.567 to 0.767)
fails; the contrast 0.66 of the photo's (bar 0.8) fails; the forms band's amplitude 0.58 (bar 0.8) fails. All four
moved the right way, and the dark end came close (0.159 against 0.129). What is left of the map is the frame's sides
(the photo's 0.39 to 0.59 against the render's 0.45 to 0.71 on the right) and the top left; inside the pool the bright
end is still short, a darker bottom and a brighter top around the same median, which is what an S-shaped tone curve
does (the photo was edited in Polarr; C-008's contrast looks raised the stone's contrast but brightened the wall,
which is set exactly through the plain sRGB curve). Seen on the sheet: the frame falls into shadow at its corners and
sides and the light gathers on the carved field, as in the photo; the photo's frame is darker still, and its carving
brighter in the centre.

**The judge (2026-11-24):** "yes, it reads better; let's do the tone curve next. also, the light is exposing some
missing portions we failed to capture through the pipeline" (a close-up of white flecks on the bars, lower middle).

**The flecks.** They were holes: small fragments of lit rim along the upper edges of openings that the photo's rule
still called wall (in the lit middle the wall is bright, and lit stone only 7 to 13 % brighter than it, under the lit
test's 12 % plus 0.03). Marigold sees the wall through an opening as one flat surface facing the camera, and these
fragments sit on bars that face up: of the openings of 400 px or more, the median one's normals lean 5.1 degrees from
the wall's (the 99th percentile 10.4). Now an opening under 400 px whose normals lean more than 15 degrees on average
is stone (`common.classify`, given the photo's normals; the normals step now runs first). It takes 6.2 % of what was
called opening. In the close-up the render is open where the photo is stone on 415 px in all, in pieces of 30 px or
less, every one at an opening's edge. Openings IoU 0.762 to 0.791; thin stone 95.9 % to 97.5 %. Not done: the wall's
normal is taken over the whole photo, and real openings in the lower part lean 10 to 15 degrees from it (Marigold's
wall drifts), so a local wall normal would be safer; and the labelling adds about 14 s to each step that reads the
photo.

**Result (2026-11-24, closed): judged better, the bars not met.** One spot, fitted to where the photo's light pools (a
light map of 6 x 7 cells) by a search over its aim, distance, pool size, pool width and edge, the six together at the
end: 4.69 m out, a 13.1 degree cone 1.11 times as wide as round, fully soft, aimed 0.09 m above the centre. The map's
error from 0.443 to 0.198 (bar 0.15); the bright end 0.514 against 0.674 (bar 0.573 to 0.776); the contrast 0.65 of
the photo's and the forms band's amplitude 0.56 (bars 0.8). By the card the map's miss says one spot cannot make all of
this light and the next card would try two lights; the user chose the tone curve, which is what the misses inside the
pool point to (a darker bottom and brighter top about the same median). That is C-013. Found on the way: a spot's
pool stretches when its object is scaled (`experiments/light/spot_scale.py`), and the normals can veto the photo's
rule. Guide: `areas/production.md` items 19 and 20, `areas/light-world-camera.md` (spot scale). T-015 answered for the
pool; the tone curve is T-016.

### C-013 · The photo's tone curve: the render through the same S-curve, the wall set through its inverse

**Opened:** 2026-11-24

1. **WHERE WE ARE.** C-012 closed "it reads better" with the spot fitted to where the photo's light pools. The stone's
   median matches (0.342 against 0.347) and its dark end is close (10th percentile 0.159 against 0.129), but its bright
   end is short (90th 0.514 against 0.674): a darker bottom and a brighter top about the same median, the shape an
   S-shaped tone curve gives. The photo was edited (Polarr, by its metadata). C-008 tried Blender's contrast looks: the
   stone's contrast rose, but so did the wall seen through the openings, which is set exactly through the plain sRGB
   curve.
2. **WHAT WE ARE DOING.** Put the render through a tone curve fitted to the photo, with the wall set through the
   curve's inverse so the openings stay as the photo has them.
   - The curve: per channel, through 0, 1 and the photo's stone median (so the light's power fit stands), a power curve
     below that point and a mirrored one above it, two numbers fitted so the stone's 10th and 90th percentiles match
     the photo's. Applied to the finished render in `build.py`.
   - The wall's ten colour bands decoded through the curve's inverse before the sRGB decoding; then the spot's power
     fitted again, and the render made again.
3. **WHY.** Unknown now: whether the stone's missing bright end and contrast are the photo's processing (one curve
   fixes them) or the scene (the light, the stone), and whether a curve the wall passes through unchanged reads as
   the photo or as an edit.
4. **WHAT IS AFFECTED.**
   - `build.py` (`--no-tone` keeps C-012's); `results/` overwritten, C-012's kept as `*_c012.json`; `sheet.jpg`.
   - `areas/production.md`'s photo section, and `areas/rendering.md` or `compositing.md` if the curve is a recipe a
     script can reuse; T-016's answer.
5. **CONCLUSION.** The measures first, then the judge.
   - Measures: the bright end within 15 % of the photo's (0.573 to 0.776), the contrast 0.8 to 1.2 of the photo's, the
     forms band's amplitude 0.8 to 1.2. Guards: the openings' median luminance within 0.02 of the photo's in both
     halves, and the light map's error no worse than 0.218 (C-012's 0.198 and 0.02).
   - The judge: *at a glance, could the render be a photograph of the same screen?*
   - If the measures pass and the answer is yes, the guide gets the recipe (a photo's tone curve fitted, the emitters
     set through its inverse), and T-016 is answered.
   - If the bright end and contrast pass but the forms band's amplitude does not, the curve was the global part and
     the local contrast is the scene's (the stone's albedo, its specks, the light's softness): that is the next card.
   - If the curve cannot bring the bright end within its bar without breaking a guard, the missing light is in the
     scene, not the processing.
6. **CONSEQUENCE OF NOT DOING IT.** The render stays flatter than the photo it is set beside, and the guide's photo
   method matches a photo's light but not the processing every photo has been through.

**Known limits, stated before the run:**
- The curve is fitted to the stone's percentiles, so the bright end and contrast are partly fitted; the forms band's
  amplitude and the guards are the checks it cannot fit.
- One curve for the whole picture, the same for each channel; a phone's processing is local and may differ by channel.

**Measures (2026-11-24), in the order they were taken.** C-012: the bright end 0.514, the contrast 0.65 of the
photo's, the forms band's amplitude 0.56, the light map's error 0.198.
1. As the card said, the curve fitted once and the wall set through it (`results/*_c013_once.json`): the bright end
   0.659, the contrast 0.92, the amplitude 0.814, all within their bars; but the openings came out 0.05 too bright in
   both halves (guard 0.02). The wall set through the curve's inverse lights the stone's sides and backs less, so the
   stone's percentiles moved and the curve fitted after it was stronger (its upper exponent 3.0 against 2.42) than
   the one the wall had been set through.
2. Changed: render, fit the curve, set the wall, fit the power, until the curve holds still. Per channel it crept and
   did not settle in five rounds (the upper exponent 2.42, 3.00, 3.23, 3.32, 3.35); the openings came within the guard
   (0.017 and 0.012 over), but the openings' IoU fell from 0.791 to 0.758, and it was 0.795 on the same render before
   the curve (`results/*_c013_perchannel.json`). Per channel, a colour that straddles the pivot changes hue: the dim
   grey wall turned warmer and failed the green-over-red cut.
3. Changed: the curve on luminance, R, G and B scaled together. It settles in three rounds: a = 1.020 (the dark end
   barely moves), b = 2.374 (a strong lift above the median, 0.347). Now: the bright end **0.674** against 0.674 (bar
   0.573 to 0.776), the contrast **0.95** (bar 0.8 to 1.2), the forms band's amplitude **0.828** (bar 0.8 to 1.2);
   guards: the openings 0.467 against 0.448 above and 0.848 against 0.843 below (within 0.02), the light map 0.201
   (at most 0.218). The openings' IoU 0.782 (C-012 0.791).
All three measures pass and both guards hold; the bright end and the contrast are partly fitted (the curve is fitted
to the stone's 10th and 90th percentiles), the amplitude and the guards are not. Seen on the sheet: the lit tops of the
carving come up to a pale cream as in the photo, the centre is brighter; the frame is still a little lighter at the
sides than the photo's.

**The judge (2026-11-24):** "This is really amazing!!!! Looks almost very realistic in a passing glance! what gives it
away, and maybe it is opioanted and not, [...] that this looks VERY fresh, like it was just created. another thing is
disapating edges (top left), [...] so vanishing borders is one thing."

**Result (2026-11-24, closed): "almost very realistic in a passing glance", the measures met.** A tone curve fitted
to the photo (on luminance, through the stone's median; the dark end's exponent 1.020, the bright end's 2.374), the
render put through it and the wall set through its inverse, iterated with the wall and the light's power until the
curve held still: the bright end 0.674 against 0.674, the contrast 0.95 of the photo's, the forms band's amplitude
0.83, the openings within 0.02 of the photo's in both halves, the light map unchanged. By the card, the guide gets
the recipe (`areas/production.md`, item 21) and T-016 is answered. What gives it away, in the user's words: the stone
looks "VERY fresh", and the borders vanish at the top left. Those are the next two cards: the borders C-014, the
stone's age C-015.

### C-014 · The screen's borders: shadowed frame stone kept, not cut away as the museum's dark

**Opened:** 2026-11-24

1. **WHERE WE ARE.** C-013 closed "almost very realistic in a passing glance"; one give-away the user named is
   "disapating edges (top left) [...] vanishing borders". The build cuts from the screen's box every dark pixel
   (luminance under 0.08) joined to the box's edge, taking it for the museum's dark surround: 2.56 % of the box, 23.6 %
   of its left 60 columns, 10.1 % of its top 60 rows. In the photo much of that is the frame's stone in shadow (since
   C-012 the light pools in the centre and leaves the corners dark): its green over red has a median of 0.667 (10th
   percentile 0.424), where the real surround outside the box is neutral (median 1.000, 10th percentile 0.857). Where
   the frame was cut, the glowing wall behind shows through.
2. **WHAT WE ARE DOING.** Count a dark pixel as surround only if it is also neutral in colour (green over red above
   0.8) or too dark for its colour to tell (luminance under 0.02); the rest of the dark inside the box is stone.
3. **WHY.** Unknown now: whether colour alone separates the shadowed frame from the museum's dark along every edge, or
   whether some of the edge needs the frame's shape (a rectangle) instead.
4. **WHAT IS AFFECTED.** `build.py`'s surround (the old rule kept as `--surround-dark`); `results/` (C-013's kept as
   `*_c013.json`), `sheet.jpg`; `areas/production.md`'s item 2, which says dark pixels joined to the edge are the
   surround.
5. **CONCLUSION.** The measures first, then the judge.
   - Measures: the surround cut from the box falls below 1 %, and none of it is stone-coloured; the openings' IoU and
     the light map no worse than C-013's (0.782, 0.201) by more than 0.01 and 0.02.
   - The judge: whether the borders still vanish, and the card's question.
   - If the cut falls and the borders hold, the guide's item 2 gets the colour condition. If colour leaves a ragged
     edge, the frame's outline is drawn as the box's rectangle instead, and that is recorded.
6. **CONSEQUENCE OF NOT DOING IT.** The frame's corners stay eaten wherever the photo's light falls off, and the wall
   glows through them: a give-away at a glance.

**Measures (2026-11-24).** The surround cut from the box 38,321 px to 17,270, 2.56 % to 1.15 % of the box (bar 1 %,
missed); none of what is left is stone-coloured, by the rule, so it is the museum's dark inside the box. The openings'
IoU 0.782 to 0.787, the light map 0.201 to 0.202 (guards held). Seen: the frame's top-left corner is whole, its left
edge straight to the top, and no wall shows through; the other corners hold too.

**The user's look (2026-11-24):** "some parts are still funky" (a close-up of the frame's top edge, bitten and lumpy).
The bites were not the surround (in the photo it took only a hairline there) but holes: the frame's top edge catches
the light, pale and greyish, and the colour rule called 5,055 px of its top 60 rows opening; over the whole frame 1.8 %,
in 973 pieces. The normals could not veto them: Marigold sees the plain frame as flat as a wall. A jali's frame has no
openings, so now the openings are kept only inside the carved field: the box around every opening of 400 px or more
that does not reach within 20 px of the box's edge, padded 6 px (`common.field_box`, found by `read_photo.py` and used
by the build and the comparison; `--frame-openings` keeps the old). Two first tries were wrong and are recorded: the
pale band along the top was itself one opening of 2,739 px and stretched the field to the top; and turning everything
outside the field to stone took in the lit floor below the screen too, so the screen's box grew to the image's bottom.
The field is [160, 148, 1057, 1221]: by the share of opening per row and column, the carved field ends at about rows
150 and 1220 and columns 172 and 1048, so the bottom row's small arches are inside it. It takes 8,824 px of frame
"openings". Openings IoU 0.787 to 0.839, partly because those were false openings in the photo's rule that the render,
solid there, could never match; thin stone 97.8 %; the light map 0.207 (guard 0.221 held). Seen: the top edge is
straight and whole; the bottom row unchanged. Left: the frame's surface reads crumbly beside the photo's speckled
stone, because the detail tilt reads the photo's specks (its colour) as relief; separating the colour from the shading
is C-015's question.

**The judge (2026-11-24):** "Thanks. This is amazing! I really love it."

**Result (2026-11-24, closed): the borders hold.** Two rules in the photo's reading: the surround is dark and neutral
(not dark alone), and the frame has no openings (openings only inside the carved field, found from the openings
themselves). The surround cut from the box 2.56 % to 1.15 % (the 1 % bar missed; what is left is neutral), 8,824 px of
false openings taken out of the frame; the openings' IoU 0.782 to 0.839, the light map 0.201 to 0.207. The guide's
item 2 has the colour condition and item 22 the field (`areas/production.md`).

### C-015 · The stone's age from the photo: a learned albedo as its colour, the specks out of its relief

**Opened:** 2026-11-24

1. **WHERE WE ARE.** C-013's judge named what gives the render away: it "looks VERY fresh, like it was just created".
   Its stone is one colour, the photo's median brought to an albedo, with procedural noise and specks; the photo's has
   stains, darker patches and grime. Measured on C-014's render before this card's work: the stone's colour varies
   0.29 as much as the photo's (the spread of log(R/G) and log(B/G) over a 5 px blur, 0.037 against 0.127). The frame's
   brightness against the field's already matches (0.50 against 0.50: the light does that). And the frame reads
   crumbly (C-014's look): the detail tilt reads the photo's pale specks, which are colour, as relief (the frame's
   texture 1.22 of the photo's in the forms band).
2. **WHAT WE ARE DOING.** Run Marigold's intrinsic decomposition (`prs-eth/marigold-iid-lighting-v1-1`, cached;
   CreativeML OpenRAIL++-M) on the photo, and use its albedo twice.
   - As the stone's base colour: the albedo map, linear, scaled so its median over the stone matches the present
     albedo (so the light and the tone curve keep their level), projected like the normal map where the surface faces
     the camera; the present colour elsewhere.
   - To take the specks out of the relief: the detail tilt reads the photo's luminance divided by the albedo's
     relative luminance (the shading, in the photo's own scale), not the photo's luminance.
   - Run in tiles like the normals, in the repo's `.venv` (`intrinsics.py`, a step in `make.py`); the light refitted
     once, since a darker-stained frame changes where the light seems to pool.
3. **WHY.** Unknown now: whether a learned albedo of this photo carries the stone's age (its stains, grime, discolour)
   or only noise, and whether dividing it out leaves weathering on the frame without the crumble.
4. **WHAT IS AFFECTED.** New `intrinsics.py`; `build.py` (`--no-albedo` keeps C-014's colour and tilt), `make.py`,
   `compare.py`'s colour measure (added before the work); `results/` (C-014's kept as `*_c014.json`), `light_fit.json`,
   `sheet.jpg`; `areas/production.md`; T-017.
5. **CONCLUSION.** The measures first, then the judge.
   - Measures: the stone's colour spread 0.8 to 1.2 of the photo's; the frame's forms-band texture back within 0.8 to
     1.2. Guards: the bright end and contrast within their bars (the curve is refitted), the forms band's amplitude at
     least 0.8, the openings within 0.02 of the photo's, the light map at most 0.23.
   - The judge: whether the stone still looks new, and the card's question.
   - If the colour comes within its bar and the judge no longer sees fresh stone, the guide gets the recipe (a
     photo's learned albedo as a projected base colour, and divided out of the detail) and T-017 is answered.
   - If the colour passes but the stone still looks new, age is more than colour (worn edges, grime in the hollows,
     a duller sheen): the user's reason is the next card.
   - If the albedo map is noise, not stains (the colour spread overshoots, or the stains do not line up with the
     photo's), a learned albedo is not the route here, and the next card tries procedural ageing guided by the photo.
6. **CONSEQUENCE OF NOT DOING IT.** The screen stays a new copy of an old object, the give-away the user named first.

**Known limits, stated before the run:**
- The colour spread is partly built in: the albedo comes from the photo, so a match is expected; what it cannot fit is
  whether the stains read as age, which is the judge's.
- Projected from the front, the albedo smears on surfaces that face away; those keep the even colour.

**The albedo (2026-11-24).** Six tiles, 3-member ensembles, 4 steps: 14 s a tile, 90.5 s in all; tiles differ by a
median 0.011 where they overlap (`results/intrinsics.json`). Seen beside the photo: the light's pool is gone from it
(the frame no longer dark) and the frame keeps a mottled texture, but the carving comes out almost one peach colour.
Measured on the stone, its colour varies 0.070 against the photo's 0.145 and the render's 0.037. And the pale specks
are not in it: the model put them with the shading, so dividing the photo by the albedo would not take them out of
the relief. That part of the plan was changed (below).

**Measures (2026-11-24), in the order they were taken.** C-014: the colour spread 0.29 of the photo's, the frame's
texture 0.92 (fine) and 1.22 (forms), the light map 0.207.
1. The albedo as the base colour; for the specks, the detail tilt reads the photo's luminance through a 5 x 5
   grey-scale opening (bright dots narrower than the square go, dark scratches and pits stay) instead of dividing by
   the albedo; the light refitted (`results/*_c015_nospecks.json`). The colour spread 0.47; the frame's texture 0.52
   and 1.11; the light map 0.148, under C-012's bar of 0.15 for the first time (the stained albedo now does some of
   what the pool was stretched to do: a spot 3.89 m out, the pool's half-height 0.72 m), and the tone curve milder
   (its upper exponent 1.87 against 2.37). But the carving read as clean clay, smoother than C-014's: the albedo had
   replaced the procedural specks with near-uniform colour, and the opening took the grit out of the relief.
2. Changed: the photo's specks put into the albedo, each bright dot narrower than about 2 px (the photo's luminance
   over its 3 x 3 opening) brightening it by its own contrast. At up to 2.5 times (display) some went white, the
   render's rule took them for wall, the openings' IoU fell to 0.795 and the lower openings came out 0.024 off
   (`results/*_c015_speck25.json`).
3. Changed: capped at 1.6 times. Now the colour spread **0.49** of the photo's (bar 0.8, missed); the frame's forms
   texture **1.17** (bar 0.8 to 1.2, met; fine 0.73); guards: the bright end 0.673 against 0.674, the contrast 0.96,
   the forms band's amplitude 0.807, the openings 0.011 and 0.006 off, the light map 0.150: all held. The openings'
   IoU 0.822 (C-014 0.839). `make.py` reproduces it to four decimals.
What the colour measure misses, looked at: in the photo a third of the colour's variation goes with brightness (35 %
of log(R/G)'s variance, 29 % of log(B/G)'s; lit faces paler, shadows redder, at three times the render's slope),
which is the light's colour or the phone's processing, not the stone's; with that taken out the photo still varies
0.106 against the render's 0.059, some of it stains the albedo does not carry and some the photo's colour noise in
its darks, in a split not measured. Seen on the sheet: the frame mottled, lighter and darker in patches as in the
photo, no longer crinkled; the carving speckled pale like the photo's, but more even in colour than the photo's.

**The judge (2026-11-24):** "this looks so real! Oh My Allah!"

**Result (2026-11-24, closed): it no longer reads as new; the colour measure missed.** Marigold's intrinsic
decomposition of the photo gives the stone its colour: its albedo as the base colour where the surface faces the
camera, the photo's pale specks put back into it (they are colour, and the model left them out), and taken out of the
relief by a grey-scale opening. The frame went from crinkled to mottled (its texture 1.22 to 1.17 of the photo's),
the light map's error fell to 0.150 once the light was refitted over the stained albedo, and the guards held. The
stone's colour spread rose from 0.29 to 0.49 of the photo's, short of the 0.8 bar; about a third of the photo's colour
variation goes with brightness (the light's colour or its processing, not the stone's) and some is noise, so the bar
was set on a measure that was partly the wrong thing. None of the card's branches fits exactly (the colour missed, the
judge saw real stone); written as it fell. The guide gets the recipe with that limit (`areas/production.md`, item 23),
and T-017 is answered for this photo.

### C-016 · A standard for photo matches: which measures follow the judge's verdicts from C-007 to C-015

**Opened:** 2026-11-24

1. **WHERE WE ARE.** The jali went from "no" (C-007, C-008) to "this looks so real!" (C-015) over eight judged
   sheets, each measured along the way, but by measures added one card at a time: the lines (C-008) fell as the user's
   verdicts rose, and the forms band (C-011) became partly the photo against itself once its detail went into the
   normals (C-011). Nothing yet says which numbers a new asset should be held to (T-013), and the user asked for a
   standard before going on to other assets.
2. **WHAT WE ARE DOING.** Recompute every candidate measure on the same patch of all eight committed sheets (the
   detail crop, photo and render at full size, unchanged since C-007), and rank each against the judge's ladder.
   - The ladder, from the verdicts in this file: C-007 and C-008 "no" (0), C-009 "much improved" (1), C-011 "yes at a
     glance" (2), C-012 "it reads better" (3), C-013 "almost very realistic" (4), C-014 "I really love it" (5), C-015
     "this looks so real" (6).
   - The measures, on the crop: the openings' IoU, the forms band (correlation, amplitude), the fine band, the stone's
     bright end and contrast against the photo's, its colour spread, the lines, the edge gradient, and SSIM (a
     standard structural similarity, which none of the cards used).
   - For each, Spearman's rank correlation with the ladder (for a ratio, its distance from 1, smaller is better).
   - `shots/jali-match/measure_history.py`, `results/measure_history.json`.
3. **WHY.** Unknown now: which numbers rose with the judge's eye across all eight verdicts, and which only looked
   good on the card that added them, so a standard can name the first and drop the second.
4. **WHAT IS AFFECTED.** New `measure_history.py`; `compare.py` gets a scorecard (the measures that track, with their
   bars); `areas/production.md` a section on the standard; T-013's answer.
5. **CONCLUSION.**
   - If some measures follow the ladder (Spearman 0.8 or more), they are the standard, each with a bar from the
     accepted state (C-015) and the photo's own ceiling, and T-013 is answered with them.
   - If none does, the judge stays the standard and the numbers are guards only (each says what it cannot see), and
     T-013 stays open with that finding.
   - Either way, the lines measure's fate is recorded with its number.
6. **CONSEQUENCE OF NOT DOING IT.** Every new asset would be judged by measures chosen afresh, some of which (C-008's
   lines) moved against the judge, and the generalising cards (T-018) would have no standard to report against.

**Known limits, stated before the run:**
- Eight sheets, two of them tied, from one photo and one judge: a correlation is a pattern to keep testing, not proof.
- The sheets are JPEGs and the crop is one patch (the carved field's middle); the frame and the borders (C-014) are
  outside it, so C-014's rise cannot show there.
- The ladder is ordinal and each verdict was against the one before; the steps are not equal.

**Measures (2026-11-24).** `results/measure_history.json`. Spearman with the ladder, on the detail patch (full size)
and the whole screen (half size, the frame included): SSIM 0.898 and 0.922; the render's lines near the photo's 0.886
and 0.826; the bright end 0.874 and 0.838; the forms band's correlation 0.731 and 0.898; the colour spread 0.527 and
0.922; the fine band's amplitude 0.766 and 0.707; the contrast 0.755 and 0.778; the forms band's amplitude 0.683 and
0.695; the edge gradient 0.06 and 0.335; the openings' IoU -0.205 and -0.263 on the sheets, but 0.922 from the cards'
own full-size comparisons (0.565 to 0.822: the sheets are JPEGs at half size, and the render's later tones move what
the rule calls opening there). None rose at every step: at C-015, the highest verdict, SSIM and the forms band dipped
a little while the colour spread jumped; shape won the early verdicts, light the middle ones, age the last. A second
mistake caught on the way: the photo against itself 2 px off is not a ceiling for SSIM (the render scores 0.554, the
shifted photo 0.374, since SSIM weighs fine grain that a shift destroys and the render never had).

**Result (2026-11-24, closed): a standard of four measures and two candidates.** Following the verdicts in both views
(0.8 or more): SSIM, the openings' IoU at full size, the stone's bright end, and the render's cut lines near the
photo's (the measure C-009 set aside when it fell for one card). In one view only: the forms band's correlation and
the colour spread. `compare.py` now prints them as a `scorecard` with bars from this asset's accepted state, and the
guards that catch a break; the accepted render meets all of it. The guide's photo section has the standard
(`areas/production.md`); T-013 is answered, as a pattern on eight sheets of one photo, for a second asset to test.

### C-017 · The light's colour: a cooler spot, the stone's colour kept, against the photo's paler lit faces

**Opened:** 2026-11-24

1. **WHERE WE ARE.** C-015 judged "this looks so real!" with the stone's colour spread at 0.49 of the photo's, and a
   third of the photo's colour variation going with brightness (T-019). Measured on C-015's render before this card's
   work: regressed on log luminance over the stone, the photo's log(R/G) falls with slope -0.100 (explaining 34.7 % of
   its variance) and its log(B/G) rises with slope 0.113 (28.8 %): lit faces paler, shadows redder. The render's
   slopes are -0.031 and 0.022. Its spot is white; the shadows are lit by the glowing wall and by light bounced inside
   the red stone.
2. **WHAT WE ARE DOING.** Give the spot a colour temperature and fit it to the photo's two slopes, with the stone's
   colour divided by the spot's (channel by channel) so the lit stone keeps the photo's median colour.
   - Candidates from 2,700 K to 10,000 K, the spot's colour from Planck's law (linear, normalised); each rendered at
     25 % before the tone curve, its slopes measured on the photo's stone; the temperature whose slopes are nearest
     the photo's, then the rest of the build as before.
   - `build.py` (`--spot-white` keeps the white spot).
3. **WHY.** Unknown now: whether the photo's paler highlights and redder shadows are the light's colour (a cool spot
   over warm light bounced in red stone), which one number can give, or the phone's processing, which it cannot.
4. **WHAT IS AFFECTED.** `build.py`; `compare.py`'s colour-against-brightness measure (added before the work);
   `results/` (C-015's kept as `*_c015.json`), `sheet.jpg`; `areas/production.md`; T-019 (the light's half).
5. **CONCLUSION.** The measures first, then the judge.
   - Measures: both slopes within 30 % of the photo's (R/G -0.070 to -0.130, B/G 0.079 to 0.147). The scorecard
     (C-016) still met, and the colour spread no lower than C-015's 0.49.
   - If a temperature brings both slopes within 30 % and the judge sees no loss, the light's colour is the light's,
     the guide gets it, and the light's half of T-019 is answered.
   - If no temperature does, or it bends one slope and not the other, the paler highlights are the processing (a
     saturation curve on luminance, C-013's kind), and that is the next card.
6. **CONSEQUENCE OF NOT DOING IT.** The render's highlights stay as saturated as its shadows, a difference from the
   photo the colour spread measures but the user has not named; T-019 stays open.

**Known limits, stated before the run:**
- One colour for the spot and one compensation for the whole stone; a museum's light may mix sources.
- The slopes come from the stone's own colour variation as well, so a perfect match is not expected.

**Measures (2026-11-24).** `results/*_c017_spotcolour.json`. At the fit's 25 % size the photo's slopes are -0.067
(R/G) and 0.077 (B/G). The render's, by the spot's temperature: white -0.034 and 0.015; 2,700 K -0.028 and -0.016;
3,500 K -0.025 and 0.010; 4,500 K -0.029 and 0.015; 5,500 K -0.032 and 0.016 (the nearest); 6,500 K -0.034 and
0.015; 8,000 K -0.036 and 0.012; 10,000 K -0.037 and 0.010. At full size with 5,500 K: -0.031 and 0.025 against the
photo's -0.100 and 0.113. No temperature brings either slope within 30 %; across the whole range they move less than
0.03. Why, looked at: with the stone's colour divided by the spot's, the lit faces keep their colour by design, and
the shadows are lit mostly by light bounced off that same stone, so they keep theirs too; only what the glowing wall
lights changes, and that is little. The scorecard held throughout (the build changes almost nothing).

**Result (2026-11-24, closed): no; the photo's paler highlights are not the light's colour.** One spot temperature,
with the stone's colour kept, moves neither slope by more than 0.03 between 2,700 and 10,000 K, against a gap of 0.07
and 0.09. By the card, the paler highlights are the processing, and a saturation curve on luminance is the next card
(C-018). The search is kept, off by default (`--fit-spot-colour`). No change was shipped, so no sheet was judged.

### C-018 · The photo's processing, its colour: saturation falling with brightness, fitted to the photo's slopes

**Opened:** 2026-11-24

1. **WHERE WE ARE.** C-017 found the photo's paler highlights and redder shadows are not the light's colour: one spot
   temperature, the stone's colour kept, moved the colour-against-brightness slopes by under 0.03, against gaps of
   0.07 (R/G: photo -0.100, render -0.031) and 0.09 (B/G: 0.113 against 0.025). C-013 found the photo's processing in
   its luminance (an S-curve); a phone's processing also takes colour out of highlights.
2. **WHAT WE ARE DOING.** After the tone curve, scale each pixel's colour (its distance from grey at the same
   luminance) by (Y / m)^-k, m the stone's median (above it less colour, below it more), with k fitted so the stone's
   two slopes come nearest the photo's; luminance unchanged.
   - Fitted on the finished render, no renders added; in `build.py` (`--no-saturation` keeps C-017's).
3. **WHY.** Unknown now: whether one number for the processing's colour gives both slopes (so the paler highlights
   are the processing), and whether it reads as the photo or as an edit.
4. **WHAT IS AFFECTED.** `build.py`; `results/` (C-017's kept as `*_c017_spotcolour.json`), `sheet.jpg`;
   `areas/production.md` item 25; T-019's light half.
5. **CONCLUSION.** The measures first, then the judge.
   - Measures: both slopes within 30 % of the photo's; the colour spread up from 0.48; the scorecard met and its guards
     held (the openings' brightness is untouched: the curve keeps luminance).
   - If both slopes come within 30 % and the judge sees no loss, the paler highlights are the processing, the guide
     gets it (item 25), and T-019's colour half is answered.
   - If one number cannot give both slopes, the colour is in the stone after all (or a mixed light), and that is
     written as the next card's question.
6. **CONSEQUENCE OF NOT DOING IT.** The highlights stay as saturated as the shadows, unlike the photo.

**Known limits, stated before the run:**
- k is fitted to the slopes, so meeting them is partly by construction; the colour spread and the judge are the
  checks it cannot fit.
- One curve for the whole picture; a phone's colour processing is local.

**Measures (2026-11-24), in the order they were taken.** C-017: the slopes -0.031 and 0.025 against the photo's
-0.100 and 0.113, the colour spread 0.48.
1. As the card said, k fitted on the photo's stone (`results/*_c018_photomask.json`): k = 0.10, and the build measured
   the slopes within 12 % of the photo's; but `compare.py`, on stone in both images, measured -0.056 and 0.055, half.
   The photo's stone takes in the render's wall at the openings' edges, bright and grey, which steepened the build's
   slopes by itself. The lower openings came out 0.0202 off (guard 0.02).
2. Changed: k fitted on stone in both images, as `compare.py` measures: k = 0.25; the slopes -0.094 and 0.108 against
   -0.099 and 0.113 (within 6 %); the colour spread 0.48 to **0.75**; the scorecard met. But the openings' brightness
   came out 0.027 and 0.032 off and their IoU fell from 0.824 to 0.770 (`results/compare_c018_noveto.json`): the
   render's lit faces, now paler and greyer like the photo's, were taken for wall by the colour rule, as the photo's
   had been before the normals' veto (C-012).
3. Changed: `compare.py` applies the photo's normals' veto to the render's rule too (the render shares the photo's
   geometry and camera). Now: the slopes -0.095 and 0.108, the colour spread **0.757**; the scorecard met (SSIM 0.554,
   openings' IoU 0.809, bright end 0.999, lines 0.607, forms band 0.642); guards held but one: the upper openings'
   brightness 0.022 off (bar 0.02), the lower 0.011. The curve keeps luminance, so the miss is the rule's: some paler
   lit stone joined to real openings is now counted as opening. `make.py` reproduces it.
Seen on the sheet: the lit faces paler and a little greyer, the shadows redder, the whole a touch more muted, nearer
the photo's pinkish grey.

**The user's look (2026-11-24):** "there is a bit of bluriness around these edges" (a close-up of the frame's top
band). The edge itself is not soft (its rise takes about 6 rows against the photo's 10); the surface is. On that band
the photo's fine texture is 0.735 of its mid-scale texture, the render's 0.421, its mid-scale texture 0.041 against
the photo's 0.022: soft blobs where the photo has fine grain and small sharp specks. In the order tried:
1. The albedo blurred over 9 px: no change (0.429). Read wrongly then as "the blobs are not the albedo's".
2. The mid-scale tilt halved: 0.459; the blobs stayed.
3. Taken apart layer by layer: Marigold's albedo on the frame is soft round blobs 8 to 15 px across (larger than
   the 9 px blur, which is why step 1 did nothing); the speck map lifted 38 % of the band's pixels, noise included;
   and the tilt, read through a square grey opening, had square plateaus.
4. All three fixed at once (the albedo blurred over 41 px, a 0.05 noise floor for the specks, the tilt reading the
   photo's own pixels wherever darker than the smoothed opening): the blobs went (mid-scale 0.024), but the albedo's
   blur spread the wall's pale grey from the openings into the stone around them, and the openings' IoU fell to
   0.778 with both openings' brightness 0.03 off (`results/*_c018_blur41.json`).
5. The blur kept within the stone (a masked blur): IoU 0.789, the openings still 0.026 and 0.025 off
   (`results/*_c018_threefixes.json`). Four changes at once, and the saturation refitted after each: no telling which
   cost what.
6. Isolated: only the masked albedo blur, C-015's tilt and specks restored (the floor and the darker-pixels tilt kept
   as switches, off). The blobs are gone: the band's fine texture 0.0159 against the photo's 0.0164, fine over mid
   0.509 (0.421 before, the photo's 0.735). The scorecard met (SSIM 0.543, openings' IoU 0.796, bright end 0.999,
   lines 0.621, forms band 0.624, colour spread 0.746); the slopes -0.100 and 0.120 against -0.100 and 0.114 (k now
   0.30). Two guards missed: the forms band's amplitude 0.772 (bar 0.8; the blobs had been adding mid-scale contrast to
   the carving too), the upper openings' brightness 0.025 off (bar 0.02; with less colour left in the albedo the
   saturation fitted stronger and paled a little more lit stone into "wall"); the lower 0.014.
A crispness measure added to `compare.py` for the record (the frame's top band, fine band over forms band): the photo
0.683; C-015 and C-018's first build 0.392; the 9 px blur 0.383; the masked 41 px blur 0.467
(`results/compare_c018_crispness.json`). `make.py` reproduces the final build.

**The judge (2026-11-24):** "This is so realistic! Oh My! I feel actual progress! It is much better, thank you."

**Result (2026-11-24, closed): yes; the paler highlights are the processing.** One saturation curve on luminance,
fitted on stone in both images (k = 0.30), gives both colour-against-brightness slopes within 6 % of the photo's and
lifts the stone's colour spread from 0.48 to 0.75 of the photo's; the scorecard met. The user's look found blur on the
frame, which was Marigold's albedo blobs; the albedo is now blurred over 41 px within the stone, the fine detail the
photo's own specks (crispness 0.392 to 0.467, the photo 0.683). Two guards missed narrowly and are left, not tuned:
the forms band's amplitude 0.772 (bar 0.8) and the upper openings' brightness 0.025 off (bar 0.02). Guide items 25 and
26 (`areas/production.md`); T-019's colour half is answered, its grime half open.

### C-019 · Grime in the hollows: are the render's recesses lighter than the photo's?

**Opened and closed:** 2026-11-24

1. **WHERE WE ARE.** C-018 closed "so realistic". T-019's other half was untested: dirt gathers in a carving's hollows,
   and the albedo, projected from the front and blurred over 41 px, may not carry it.
2. **WHAT WE ARE DOING.** Before adding anything, measure the render's brightness against the photo's from raised stone
   to the deepest recesses, away from the openings; add grime only if the render's recesses are lighter than the
   photo's.
3. **WHY.** Unknown: whether the photo's hollows hold dirt the render lacks, or the render's shadows already darken
   them as much as the photo's do.
4. **WHAT IS AFFECTED.** `compare.py` (the recess and edge measures, kept); `build.py` only if grime is added;
   `areas/production.md`; T-019.
5. **CONCLUSION.** If the deepest recesses are clearly lighter in the render than its stone overall (against the
   photo), grime is added and fitted to that gap; if not, none is, and T-019 is answered without it.
6. **CONSEQUENCE OF NOT DOING IT.** Grime would be added on a guess, darkening hollows the photo may not darken.

Written after the first measurement (a spike, as the cards' baselines were), so no bar was set in advance; the numbers
are stated as they fell and the decision follows them.

**Measures (2026-11-24).** `results/compare_c019.json`. A first probe took the hollows from where Marigold's normals
converge: its deepest 3 % were 13 % lighter in the render, but those pixels lay along the openings' edges, where the
normals turn in towards the holes, not in the carving's recesses. Then, from heights integrated from the normals
(screened at 30 px), each pixel's depth below its surroundings, on stone 6 px or more from any opening in the carved
field: the median log(render / photo) is -0.037 over all of it; on the deepest 3 % of the recesses it is 0.010 at an
11 px scale (the render 4.8 % lighter there) and -0.029 at 21 px (0.8 %). On the stone's band 1 to 4 px from an
opening it is -0.004 (3.3 % lighter than inside).

**Result (2026-11-24, closed): no grime added; the photo's hollows are not measurably dirtier than the render's.** The
render's shadows darken its recesses about as much as the photo's darken its own: at most 4.8 % lighter, on the
deepest 3 % of the smallest recesses, and nothing at the larger scale. The openings' edges are 3.3 % lighter in the
render. Both are small; nothing was changed, so no sheet was judged. If the user sees grime missing, this card is the
place to reopen. T-019 is answered (the colour by the processing, C-018; no grime needed here).

### C-020 · Why a 2D curve's fill breaks on a few traced outlines, and a fill that does not

**Opened and closed:** 2026-11-24

1. **WHERE WE ARE.** T-014: C-009's traced outlines filled to 0.3116 m2 of front face built in metres and 1.0485 in
   pixels; at 15 mm (C-011) the same small smoothed island broke the fill in pixels too. The build repairs it by
   halving to the outline and swapping in its unsmoothed version, which C-011 found does not always work (at 5 mm it
   failed). The guide said the fill "merges points closer than a fixed distance" would fit; that was never checked.
2. **WHAT WE ARE DOING.** Read Blender's fill (4.5's scan-fill source), reproduce the break from C-009's own code, and
   find what turns it on and off; then a repair that does not depend on luck.
3. **WHY.** Unknown: the cause, and so whether any repair short of another fill can be trusted on a new asset.
4. **WHAT IS AFFECTED.** `curves-text.md` item 9 (its "probably" replaced by what was measured); a new experiment
   `experiments/curves/curve_fill_knife_edge.py` with the outlines it needs as data; `build.py`'s repair;
   `production.md` item 18; T-014.
5. **CONCLUSION.** If the break is a tolerance merging close points, a scale-aware repair fits; if it is the exact
   arithmetic of the fill, only a different fill is dependable, and the build should use one when the curve's fails.
6. **CONSEQUENCE OF NOT DOING IT.** A new asset's trace can come out inside out, and the repair is a guess.

As with C-019, measured before the card was written; the numbers are stated as they fell.

**Measures (2026-11-24).** The source (`blenlib/intern/scanfill.cc`, 4.5): its only tolerance, `SF_EPSILON` 0.00003
in the curve's own units, joins a vertex to an edge only for vertices with a single edge, which closed outlines do not
have; outlines whose bounding boxes overlap are merged into one polygon; the triangles are found by exact arithmetic
(which side of an edge a point lies on), and the loop has two silent exits, a cap at twice as many triangles as
vertices ("Fill error: endless loop") and a skip for "a serial of overlapping edges". C-009's code, rebuilt from its
commit: its 420 outlines fill 0.2718 of their area in metres and 0.9146 in pixels; the island and the outline around it
alone break at 0.000924 and at 0.1 units a pixel and fill at 0.0001, 0.0003, 0.0006, 0.002, 0.005, 0.01 and 1; moving
the island 0.0005 px either way makes them fill; the broken fill stops at 7,352 triangles, under the cap of 22,464, so
it is not the cap; no coordinate of the island equals one of the outline's exactly. Moving the whole set did not
help, and giving each outline its own random offset up to 0.001 px fixed it for 3 seeds of 4. The experiment, on the
pair saved to a millionth of a pixel: broken at 0.1 a pixel and with the island moved 0.0005 px either way, whole
otherwise; rounded to 1e-5 px, broken at 0.005, 0.01 and 0.1 instead. Geometry Nodes' Fill Curve (constrained Delaunay)
filled every case whole, the full 420 too (0.9146 at every scale). The build forced through Fill Curve caps on today's
outlines: front face 1.1248 m2 both ways, the render's measures the same to the third decimal (997,284 faces against
549,170).

**Result (2026-11-24, closed): the fill's own exact arithmetic, not a tolerance.** Whether Blender's curve fill breaks
on these outlines turns on the points' exact floating-point values: a scale, a shift of 0.0005 px or a rounding to
1e-5 px switches it on or off, and no tolerance is involved for closed outlines. The dependable fill is Geometry Nodes'
Fill Curve, which never broke here. The build now repairs a short fill by keeping the curve's bevelled walls with its
fill off and taking the front and back from Fill Curve (the halving search kept as a last resort). T-014 is answered;
`curves-text.md` item 9 and `production.md` item 18 say so.
### C-021 · Other photos of the same screen: is there a second view to test the relief against?

**Opened and closed:** 2026-11-25

1. **WHERE WE ARE.** T-012: the jali is rebuilt from one frontal photo, its relief taken from a learned normal map, and
   every number in the standard (C-016) is measured on that same photo, the one the build was tuned to. Its title ends
   "Louvre Abu Dhabi (2)", so the photographer took at least one more of this screen.
2. **WHAT WE ARE DOING.** Search the photographer's Flickr photostream, Wikimedia Commons and the museum's own pages for
   other photos of this screen, and record for each its angle, light, size and licence.
3. **WHY.** Unknown: whether a second view exists that we may use. A photo from another angle would be the first test
   of the relief that the build was not fitted to; one under other light, a test of the albedo and the light fit.
4. **WHAT IS AFFECTED.** T-012's answer; `production.md`, "Rebuilding a pierced object from one photograph" (what one
   view leaves unchecked); `photo/CREDIT.md` if a photo is added. Nothing in the build or the measures.
5. **CONCLUSION.** If at least one openly licensed photo shows this screen from an angle well off frontal, or under
   clearly different light, the next card renders the build from that view as a held-out check and T-012 stays open
   for it. If there is none (only near-duplicates of our view, or licences that forbid reuse), T-012 is answered no,
   and the guide says the relief's depth is untested beyond looking right under its one light.
6. **CONSEQUENCE OF NOT DOING IT.** The standard rests on in-sample numbers only, and a second asset would inherit that
   without anyone having checked whether a held-out view was there for the taking.

**Measures (2026-11-25).** The photographer's Flickr photostream holds three photos with this title, numbered (1) to
(3), all CC BY 2.0, all taken on the same phone within 37 seconds (12:33:11 to 12:33:48), all frontal, at 1/25 or 1/27
s, f/1.8. They are three different screens. (3) is another design: upright flowering plants in the lattice, another
arch and frame. (1) is a sibling of ours, the same arch and lattice, but the flower under the crown has notched,
heart-shaped petals where ours are round, a plain ring of stems around it where ours cross in loops, and its stone has
none of the white specks that cover ours (`photo/c021_sibling_vs_ours.jpg`). Flickr searched across all users ("louvre
abu dhabi" with jali, window screen, agra, mughal, lattice; "jali abu dhabi"): no photo of a jali by anyone else.
Wikimedia Commons did not answer from this machine; its search index, through a web search limited to the site, has no
jali at the Louvre Abu Dhabi. The museum's site refused the request. Record: `results/other_photos_c021.json`.

**Result (2026-11-25, closed): no second view of this screen where we could look.** Of the three photos taken in that
gallery, one is ours and the other two are other screens, each also from the front. So the second branch holds: T-012
is answered no, and the guide says the relief's depth has not been checked from any other angle; every number in the
standard is measured on the photo the build was fitted to. Commons itself and the museum's archive were not read, so a
view there is not ruled out. What the search turned up instead is for T-018: two more screens photographed on the same
phone, in the same gallery and light, under the same licence, one of them a near sibling of ours.

### C-022 · The chain on a few dozen other jalis: where it holds and where it breaks, at a glance

**Opened:** 2026-11-25

1. **WHERE WE ARE.** T-018, un-parked on the user's word (T-011 set aside): one screen, one photo, judged "this looks so
   real!" (C-015) with the standard's four core measures inside their bars (C-016). Nothing in the chain has run on any
   other photo, and C-021 found the standard is in-sample.
2. **WHAT WE ARE DOING.** Run `make.py`'s chain, its method unchanged, on 24 to 36 openly licensed photos of other jalis
   chosen by rules written before any is run, and lay each render beside its photo for the user to judge at a glance.
   The only code change is to read what is this photo's (its path, size, camera, and where the outputs go) from a
   per-photo file instead of constants, with today's values as the defaults so the jali-match shot reproduces.
3. **WHY.** Unknown: which of the 27 findings in `areas/production.md` are about pierced stone in photos and which are
   about this one photo. After: for each photo, at which step the chain breaks (reading the photo, the build, the light,
   the colour) or that it does not, and whether the standard's measures agree with the user's glance on screens they
   were not fitted to.
4. **WHAT IS AFFECTED.** `areas/production.md` items 1 to 27 and the standard's bars (each could turn out this photo's
   own); `shots/jali-match/*.py` (paths and the photo's constants only); T-018. The jali-match shot's own results must
   not move: its build is rerun after the change and compared to four decimals.
5. **CONCLUSION.** If the user takes at least half of the renders for their photos at a glance, the recipe holds for
   frontal photos of jalis and the failures are its limits, named by step. If fewer than half, the recipe is this
   photo's, and the failures, sorted by the step where each broke, are the order to generalise it in. Either way, the
   standard's measures are checked against the user's glance on photos it was not fitted to: if they rank the renders
   as the user does, they stand; if not, they are this photo's too.
6. **CONSEQUENCE OF NOT DOING IT.** The guide's 27 findings stay one photo's, stated as if general, and the next
   asset finds out which are not by failing.

**Rules for choosing the photos (written before any was run).** A single carved, pierced screen (stone or marble),
seen from roughly the front (its outline foreshortened by no more than about a fifth), its whole carved field in the
frame; licensed CC0, public domain, "no known copyright restrictions", CC BY or CC BY-SA; at least 1,000 px on the
short side. Taken in the order the searches return them, at most four from one monument, until 30 are kept; every
candidate looked at and left out is recorded with its reason.

**Amendment (2026-11-25, before any run):** four rounds of searching (391 candidates, `shots/jali-batch/candidates_round*.json`)
gave 18 photos that meet every rule, short of the 24 the card set: Flickr's openly licensed photos of jalis ran out
(round 4 found 6 new candidates, none a single screen), and Wikimedia Commons does not answer from this machine. The
rules were not loosened to make up the number. Every candidate left out has its reason in `selection.json`; the size
floor took 6 and the cap of four on one monument took 4 (Humayun's Tomb and Sidi Saiyyed reached it).

**Measures (2026-11-25).** The chain's code: the photo, its size, camera, screen width and output folder now come from
`shot.py` (a folder's `shot.json`, or this photo's constants when none is given). The jali-match shot rebuilt after the
change: its 234 compared numbers within 0.0001 of the committed ones; after the guards below, one pixel of 851,095 in a
mask and two numbers by 0.0001 (`results/` restored to the committed files). Assumed for the 18: the screen 1.05 m
wide, as ours; a 28 mm equivalent lens, uncropped (Flickr's resized files carry no EXIF), except the two Louvre Abu
Dhabi photos (the same phone as ours, 24 mm); worked at a long side of 1,402 px, as ours.

The first pass: 10 of 18 reached a render and its comparison. Four of the failures were crashes in this repository's
code, not the method, each fixed by a guard that leaves the jali-match shot as it was: the tone curve took a log of 0
when a percentile was pure white (05, the render's sunlit stone; 09, sunlight on the floor taken for stone); C-020's
repair entry has no `loop` and the older repair looked it up (15); the grime measure took a percentile of nothing
where no stone lies 6 px from any opening in both (15). After them, 13 of 18 reach a render. The other five stop in
reading the photo, and now say why:

| shot | where it stops | measured |
|---|---|---|
| 08-humayun-mihrab | no screen box | 80 % of the image darker than the surround's 0.08: the backlit stone reads as the dark surround |
| 10-humayun-d | no carved field | the box found, its largest opening 11 px (the field rule needs one of 400 px away from the box's edge) |
| 13-jaali-window-a | no carved field | largest 390 px; the scan's white border one opening of 288,160 px, touching the box's edge |
| 14-jaali-window-b | no carved field | largest 337 px; the white border 424,830 px |
| 18-fatehpur-sikri-b | no carved field | largest 211 px, median 26 px: the marble lattice's holes are smaller than the rule's floor |

Of the 13 renders, none meets the standard's four core bars (set on our photo): SSIM at least 0.50 in 2 (02, 04);
openings' IoU at least 0.75 in none (0.176 to 0.713); the bright end within 0.85 to 1.15 in 5; the lines at least 0.60
in 3; the forms band at least 0.50 in 7. The colour spread passes in 12 and says nothing: its bar has no upper end
(16 passes at 2.087), and where the photo's stone has almost no colour the ratio runs away (09: 39,700,000). One cause
measured on a render (01, the museum's third screen): its frame's top band has a grey-green patina, green over red
0.833 at the median and 0.894 at the 90th percentile against ours 0.771 and 0.812, so the colour rule (wall above 0.86,
near the wall's colour above 0.80) called 33.5 % of the band opening, and the field rule, which places the carved
field from the openings, was stretched by them into the frame (its top at y 68 against the box's 52).

My reading of the sheets, before the user's (the user's glance decides field 5): 01, 02 and 11 read as their photos;
04 keeps the tree but loses the screen's fine holes; 05 and 17 in part; 03, 06, 07, 09, 12, 15 and 16 do not. The
reading sheets (`reading_1.jpg` to `reading_3.jpg`: each photo beside how `read_photo.py` sorted it) place most of the
failures in that first step, and say how. The rule expects red stone in front of a lit, neutral wall, and the photos
break it in four ways: a pale stone or patina is taken for wall (01's frame, 06's columns, 11's inlay); with a dim room
behind, the reading inverts, the pale bars called wall and the dark holes stone (12, 15, 16); holes that show sunlight
are brighter than any wall and are taken for lit stone (09); a backdrop of red sandstone cannot be told from the screen
(17). Two read about right and still render poorly, 03 and 05 (the tree of life from outside, in sun), so theirs is
later; I first put 03 down to the colour rule, and its reading sheet says otherwise. Their build logs place it in the
light: the tone curve ran into its limits both ways, 03's upper exponent at its cap of 4.0 with the render's stone
spread 0.39 of the photo's (flat), 05's at its floor of 0.3 with the untoned stone clipping at white (spread 1.21).
One spot and a lit wall behind the holes, a museum's arrangement, does not make a sunlit facade's range; and the
stone's albedo is scaled so its brightest channel is 0.45 (`build.py`, from our sandstone), which a pale limestone or
marble is not. 02 reads right and renders right. The contact sheets: `shots/jali-batch/contact_1.jpg`
to `contact_3.jpg` (no measures on them); the measures: `measures.json`.

**After the measures (2026-11-25): a fault in our code behind five renders, and two of my readings wrong.** The
runs' logs show it. The fit of the light's power measures each fit render's stone by the colour rule with the wall
found by green over red alone (`build.py`, `medians`), and grey or pale stone passes that as wall. So the fit saw 4 %
of the photo's stone in 03, 4 to 6 % in 05, 4 to 14 % in 16 and none in 09 and 15, against 102 to 106 % in every fit
render of ours. In 09 and 15 the median was nan, and each such round cut the power tenfold. Fixed: when the render's
reading holds under half the photo's stone, the fit (and the saturation fit, which had the same mask) measures the
render where the photo's stone is; the two share one camera and one outline. Ours never comes near that and rebuilt
with only its timings changed. Rebuilt, the five fits reach their stone (05: 0.437 against 0.427, where it was 0.634
and clipped white at 32,160 W; 15: 0.574 against 0.558, where it was 0.292), but at a glance 03, 05 and 09 look as
they did (`shots/jali-batch/fitfix_before_after.jpg`).

The user, on 03: "there are patches where the pathways go missing". Its reading is the photo's negative: of the
carved field's pale pixels (luminance above 0.45) 82 % were read as opening, and of its dark ones (below 0.2) 82 % as
the surround, which the build counts as stone inside the box (`shots/jali-batch/03_read_patch.jpg`). So my reading
above, that 03 and 05 "read about right" and fail in the light, was wrong twice: they fail in reading, as 12 and 15
do, because their holes look into a dark interior and the colour rule expects a lit wall. The reading sheets did not
show it to me because a lattice drawn in white on black looks like a lattice either way.

**Result:** waiting on the user's glance at the contact sheets.

---

### C-023 · The faults the 18 runs show, fixed one at a time where the jali-match shot does not move

**Opened:** 2026-11-25, with C-022's result still waiting on the user's glance, on the user's word ("keep checking
the current runs for errors and building on top of that")

1. **WHERE WE ARE.** C-022: 13 of 18 photos reach a render, none meets the four core bars, and the five that stop all
   stop in reading the photo. Reading the runs' logs after it found a fault in our code (the fit's reading of the
   render: C-022's measures) and two constants set by our photo that the others break: the field rule's 400 px floor
   on an opening (four of the five stops), and the tone curve's upper exponent held at 4.0 at most (8 of the 13
   renders at that limit; ours 2.12).
2. **WHAT WE ARE DOING.** Fix the batch's faults one at a time, the one touching most shots first, each changed only
   where the jali-match shot's results stay as committed (its steps rerun and compared), and rerun the shots each fix
   touches. A fault whose fix would move the jali-match shot is not fixed here; it goes to the user.
3. **WHY.** Unknown: how much of C-022's failure is our photo's constants, and how much is the method (the reading by
   colour; one spot and a lit wall for the light). After: the count of renders that read as their photos at a glance
   (mine, then the user's), and of core bars met, before and after the constants are each photo's own.
4. **WHAT IS AFFECTED.** `common.field_box`, `build.py`'s tone fit, and whatever the next fault touches; C-022's table
   of where each shot stops, and its reading of 03 and 05. The jali-match shot must not move.
5. **CONCLUSION.** If the fixes take the renders that read as their photos at a glance from 3 of 18 (my count at
   C-022) to at least 9, the recipe's limits were constants fitted to one photo. If not, they are in the method, and
   the next card is the reading or the light.
6. **CONSEQUENCE OF NOT DOING IT.** The batch's renders stay judged with our photo's constants in them, and the
   method's own limits cannot be told apart from those.

**Measures.**

*Fix 1, the field rule's floor (2026-11-25).* An opening had to be 400 px to place the carved field: our photo's
size, and four of the five stops (10, 13, 14, 18). The floor is now half the area of the screen's 20th-largest opening
away from the box's edge, if that is smaller, and never under 20 px (`common.field_box`; `read_photo.json`'s
`field_rule` when it moved). Ours keeps 400: its read step reran to an identical `read_photo.json`. 13 got a floor of
139 px, 14 of 78, and the three now reach a render (16 of 18 do); 10 still stops, its largest opening 11 px, because
its backlit stone reads as the dark room. 18 renders with the highest SSIM of the batch, 0.704. At a glance 13 and 14
keep their mullions, arch and lattice but their holes come out dim pink where the photo's are lit white, and 18 loses
the lattice in patches in its top panels and smears its bottom panels' holes into slanted strokes
(`shots/jali-batch/new_renders_13_14_18.jpg`).

*Fix 2, which side the openings are on (2026-11-25).* The colour rule expects the holes brighter than the stone. Now
`read_photo.py` splits the photo at its luminance's Otsu threshold (the dark surround that reaches the image's border
left out) and keeps the side that makes the more screen-like structure: the stone mostly one piece, the openings
mostly enclosed pieces of 20 px or more, 30 or more of them (`common.decide_side`). A photo whose openings are dark is
read by `common.classify_dark`: the surround is the dark that reaches the border, the rest splits at the threshold.
The bright side keeps the colour rule, untouched. Ours comes out bright, 0.753 against 0.160, and its read step reran
to an identical `read_photo.json`. Dark: 03 (0.511 against 0.006), 05 (0.072 against 0.024, the narrowest margin), 12
(0.913 against 0.001) and 15 (0.747 against 0.000); the other fourteen bright, as the first probe had them. The four
rebuilt with their saved light fits set aside (`results/light_fit_c022.json`), since those were fitted over the
inverted stone.

*After fix 2, on the user's look at 03's first rebuild:* the wall around the arch reads as stone again, its blocks,
rosettes and frieze, and the trunk and branches are pale stone the right way round; but the lattice inside the arch
was gone, one large opening, and what showed through came out in bands of red, purple and blue where the photo's
interior is near black (`shots/jali-batch/dark_holes_03_05.jpg`). Both were faults further down, now fixed (4 and 5).

*Fix 3, grey stone on the bright side (2026-11-25).* 10 stopped with no opening over 11 px. Its backlit stone is dark
and grey, and the colour rule calls any grey pixel wall, so bars and holes read as one opening that touched the box's
edge. The colour rule can only tell stone from wall where the stone has a colour the wall has not: the gap between
the two brightness sides' median green over red is 0.101 in ours, 0.067 or more in every photo with coloured stone,
and 0.000 (08), 0.000 (09, a black-and-white photo) and 0.020 (10). Below 0.04 the bright side is read by brightness
(`common.classify_backlit`), the screen placed by its holes, since its stone can be as dark as the room (08: 0.064
against 0.004). 08, 09 and 10 now pass the read step, so all 18 do; 08's and 10's readings keep their lattice and
inner arched panel, and 09's takes the sunlight the screen throws on the floor for holes too, so its box runs down
over the floor. Ours keeps the colour rule.

*Fix 4, the parallax widening (2026-11-25).* The user, on 18: "I see distortions on the top left, top right, bottom
right, and bottom left jalis however, like simmering kind of wave patterns". The build widens each hole by its back
face's offset, which grows from the picture's centre (C-008's straight-through holes). With the batch's assumed camera
the offset at the field's corners is 7.6 px in 18, against bars about 6 px wide, so the widening cut through bars and
joined neighbouring holes into streaks pointing at the centre. Counted directly, the share of holes (10 px or more,
in the field) whose widened outline holds another: ours 4.1 %, 13 6.1 %, 14 0.8 %, and 24.6 % (15) to 87.7 % (12, whose
fill then failed: front face 0.627 m2 of 0.763) in the rest. Now the offset is the camera's unless that merges over
10 % of the holes; then the largest that merges no more, by halving (`--no-merge-cap` for the camera's always). Ours
keeps the camera's.

*Fix 5, the colour step through dark holes (2026-11-25).* C-018's step scales each pixel's colour by (luminance over
the stone's median) to the power -k, fitted on the stone and applied to every pixel. In 03 and 05 the stone's median
is 0.86 and k came out 1.05 and 1.2, so the interior's faint tint, at luminance near 0.02, was made 50 to 90 times as
strong. 03's fit had also failed by its own measure (error 5.0: no k matched the sign of both colour slopes). First
form of the fix: no pixel's factor worked out below the stone's 1st percentile. That moved ours: its stone's 1st
percentile is 0.118, so the dark surround and deep shadows changed, and the colour spread went from 0.7457 to 0.7232
(SSIM 0.5429 to 0.5427). Fixes 3 and 4 had left ours exactly as committed. So the floor applies only where the
openings are dark, and ours runs the step as before; and a fit that matches neither slope's sign gives k = 0.

*The user's look at fixes 1 to 5 (2026-11-25).* On 03 (`shots/jali-batch/03_now.jpg`): "such a powerful render! I
think if we could somehow narrow down on the SHARPNESS of the details and edges, it would make it more fantastic";
on 01, "still disappearing edges" (its frame's top band and right side); on 02, "colors and spaces mixing together"
(its upper holes as grey as the stone); on 04, "symptom of the same problem over and over again ... we are having a
hard time getting the small details correctly". Measured, in each carved field: holes under the build's 30 px floor
(`MIN_AREA_PX`, set on ours in C-007) are 1.6 % of our hole area, specks, but 20.7 % of 04's, whose median hole is 21
px: the tree's pinpricks of light are dropped by design. And every photo is worked at 1,402 px on its long side, 03's
from 1,928 x 2,048. Of 06 and 07 the user said "I don't understand the results ... at all": in both the screen is a
small part of a deep space (a porch under a vault, a doorway in a dark hall), and the chain builds the whole picture
as one flat carved slab. They passed the C-022 rules ("its whole carved field in the frame"), which should also have
required the screen to fill the frame; they say nothing about detail and are left out of what follows.

*Fix 7, the build's size floors (2026-11-25).* Each floor is the smaller of its 30 px and a twelfth of the hole size
that holds half the screen's hole area, never under 4 px: ours 43, so 30 (`--fixed-floors` keeps 30 always); 04 7;
13, 14, 17, 18 between 6 and 9. *A test, not a fix: 03 worked at its full size* (`shots/jali-batch/variants/03-full`,
1,928 x 2,048, its method otherwise unchanged), against the same 03 at 1,402.

*Fix 6, the user's look at 13 and 14 (2026-11-25).* On 13: "some disappearing sides"; on 14: "color is changing too
drastically". 13's reading was inverted inside the screen: the pink light through its holes (a red sandstone
courtyard beyond) is under the colour rule's 0.86, so the holes read as stone, the dark lattice and frame as the
surround, and only the scan's white margin as opening; the render was close to a slab with the photo's colours on it
(openings 6.9 % of the box), which is why it passed a glance, and its frame's sides were cut away as dark surround.
The colour gap did not catch it (0.336, the white margin on the bright side; 0.249 without it), nor the holes' green
over red (13's 0.882 against ours 0.814, whose bright side holds its lit stone). What did: how cleanly brightness
alone splits the photo, the dark surround and a bright margin touching the border left out (Otsu's separability: the
between-class share of the variance). Ours 0.724, 01 0.712, 02 0.737; the backlit 08 0.913, 10 0.902, 09 0.846, 13
0.831, 14 0.820; the room interiors 16 0.833, 17 0.810, 18 0.825. Above 0.80 brightness reads the photo, and the
backlit rule's surround is a bright margin at the border and what lies beyond 15 % around the holes (2 % cut 13's
frame away). Ours stays on the colour rule, its read step rerun to an identical `read_photo.json`. 14's colour change
is the wall: ten flat bands from the photo's openings, from 0.92 (linear) to 0.047 within a tenth of the screen's
height, where the photo shows a red arcade with dark arches; bands cannot draw arches. Not fixed.

*The batch after fixes 1 to 6 (2026-11-25; contact sheets `contact_c023_1.jpg` to `_3.jpg`, readings
`reading_c023_*.jpg`, measures `measures_c023.json`).* 17 of 18 reach a render, against 13 at C-022; 08 and 10 for the
first time. 12 fails in the mesh: with the merge cap its merging fell from 87.7 % to 7.3 %, but its 4,686 outlines
fill to a front face of 0.700 m2 of 1.079 and the build stops itself. My glance, before the user's: read as their
photos, 01, 02, 03, 05, 08, 09, 10 and 13 (8, against 3 at C-022); the structure right and the light or the detail
not, 04, 11, 14, 15, 16, 17 and 18 (in 17 and 18 the holes dim where the photos show a bright courtyard); not, 06 and
07 (outside the method) and 12 (no render). None meets the four core bars.

*The denoiser, a test that did not run.* Rendering 03's saved scene with Cycles' denoiser on and off gave the stone
dark with only its edges lit, unlike the build's render: the scene file does not keep the images the build makes in
memory (the stone's colour, its normal map), so the comparison was void. `build.py --no-denoise` now makes it in a
real build.

*Fix 7 on 04 (2026-11-25).* Its floor came out 7.4 px (half its hole area in holes of 89 px or more). Bright spots in
the carved field: the photo 3,261 (2,832 under 30 px), the render with the 30 px floor 1,685 (1,473), with its own
floor 2,371 (2,151): 73 % of the photo's count, against 52 % (`shots/jali-batch/04_floor.jpg`). The holes are still
blobbier than the photo's, and one pale green where the photo's light is green, blue and yellow (the wall's bands).

*Sharpness, measured (2026-11-25).* On the edges between stone and opening in the carved field, an edge's width as
the luminance step over 7 px divided by its steepest gradient: ours 4.9 px in the photo, 5.1 in the render; 13 3.4
and 3.5; 03 3.7 and 6.5. Not the denoiser: 03 built with `--no-denoise` (`variants/03-nodenoise`) has edges 6.5 px
wide too, SSIM 0.4686 against 0.4689. Not mainly the parallax: by distance from the picture's centre (thirds of the
farthest edge's), 03's render is 6.0, 6.8 and 6.4 px against the photo's 3.3, 3.7 and 4.2, wide at the centre where
there is no parallax; 18's is 7.3, 8.5 and 9.2 against 3.2, 3.5 and 3.3, so there the parallax adds to it; ours 5.7,
4.8 and 5.0 against 5.4, 4.5 and 4.8. The render's edges are about 5 to 6 px wide whatever the photo's are, which
matches ours (a phone photo at half size, carving rounded) and not a crisp photo of square-cut tracery. Next suspect,
the normal map (Marigold's normals, smooth at this scale, shade every bar as if rounded): 03 with `--no-normal-map`.

*Sharpness, continued.* Not the normal map: 03 with `--no-normal-map` (`variants/03-nonormal`) has edges 7.1 px wide,
and everything else worse (SSIM 0.319 against 0.469, fine detail correlation -0.006 against 0.297). Seen beside the
photo, the render's tracery is fatter and the fine black gaps between near bars have closed. The openings the build
cuts against those the render shows: ours 11.0 % of the box cut, 8.6 % shown (the photo's reading 9.1 %); 03 32.8 %
and 27.7 % (32.4 %); 18 21.0 % and 9.3 % (18.5 %). 18's loss is the same at the centre as at the corners (about
half), so it is not the side walls seen at an angle; part of it may be the measure, which reads a dim hole as stone.
Untested suspect: the edge bevel, 0.5 mm, which widens the outline by its radius: at the batch's assumed scale about
0.6 px a side, a fifth of a 5 to 8 px hole, against nothing on ours' 20 px holes. `build.py --bevel` now takes another
radius; run on 03 when the laptop is on power. The full-size 03 is paused there too, its normals done.

*`--wall photo` (a switch; the bands stay the default).* The wall's colour taken from the photo's own openings, filled
in across the stone and seen through window coordinates, set through the tone curve's inverse each round. On a copy of
18 (`variants/18-wallphoto`, `shots/jali-batch/18_wallphoto.jpg`) it changed almost nothing: SSIM 0.5453 either way,
openings shown 8.9 % of the box against 9.3 %. The render is too dark for the wall's colour to show: 18's photo stone
sits at a median of 0.103 between 0.054 and 0.127 (backlit, in its own shadow), the spot lights the render's stone from
the front, and the tone curve squeezing that into the photo's range ends at both limits (4.0 and 0.3), which takes the
holes down to a dim grey with it. A backlit screen needs light from behind and from the room, not a front spot.

*What fix 6 cost.* Before it (13, 14 and 18 after fix 1; 16 and 17 at C-022) and after: 13 SSIM 0.556 to 0.727,
openings IoU 0.704 to 0.813, bright end 0.789 to 0.632, lines 0.108 to 0.247; 14 0.605 to 0.686, 0.577 to 0.615,
0.807 to 0.615, 0.499 to 0.602; 16 0.234 to 0.445, 0.496 to 0.607, 0.404 to 0.880, 0.654 to 0.804; 17 0.377 to 0.428,
0.447 to 0.191, 0.636 to 0.606, 0.680 to 0.688; 18 0.704 to 0.545, 0.617 to 0.461, 0.685 to 0.522, 0.686 to 0.561,
worse on all four (the user had called 18, before it, "really beautiful"). The openings IoU compares two readings by
one rule, so across a change of rule it is not like for like; SSIM and the bright end are. Fix 6 stays: it reads the
structure the user saw was wrong (13's sides, its holes), and 18's loss is in the light that follows.

*Fix 8, the user on 03 and 05 (2026-11-25): "it seems the further we go from the main jali, the further distortions
become apparent".* Under the dark rule a pale wall's joints, cracks and weathering are darker than the threshold too,
and they sat inside the carved field's box, which the frieze's gaps had stretched over nearly the whole picture (03:
28 to 1,300 by 18 to 1,226 of 1,320 by 1,402). A jali's holes are packed and a wall's dark lines are scattered. So the
dark rule keeps an opening only where the share of openings around it (a Gaussian of 20 px) is at least half the
median share at the openings: 03 keeps 87.6 % of its openings, 05 83.3 %, 12 92.0 %, 15 89.7 %, and on the reading
sheets the wall goes back to stone while the arch keeps its lattice (05's dark ledge shadows stay: they are dense).
Worked at a quarter of the size in numpy; against scipy's Gaussian at full size it keeps the same openings to 99.9 %.
Ours is on the colour rule and cannot move. Not yet run: the battery reached the 30 % at which runs stop.

*The user's look at the contact sheets (2026-11-26).* On 03 and 05 (`contact_c023_1.jpg`): "still that furthness
issue"; on 06: "a strange blueish affect is occuring here"; on 15 (`contact_c023_3.jpg`): "the lines are thicker than
in the original"; on 17: "unable to narrowly decipher what belongs to the background and what belongs to the
foreground". On the first of the numbers below: "improvements!"

*Fix 8, run (2026-11-26).* 03's reading went from 32.4 % of the picture open to 28.7 %, and its wall reads as stone on
the reading sheet. But its render kept a speckled wall (fix 15), and 15's build stopped at the fill's check (fix 13).

*Fix 9, the tunnels aimed at the camera (2026-11-26).* Fix 4's cap held 14 of the 18 shots to a tenth of the camera's
offset or less (merged at the camera's: 15.7 % of the holes in 09 to 91.1 % in 16), which left every hole a straight
1 cm tunnel seen at an angle; towards the picture's edges its far wall covered part of the hole. That is 15's thicker
bars (its render read back 13.5 % open against its reading's 17.7 %), 17's dark holes where its photo shows a lit
courtyard, and a share of 03's and 05's damage growing away from the centre. Now, when the widening would merge more
than 10 % of the holes, the holes are cut as the reading has them and every point of the screen is moved back along
the camera's ray through it (the back face scaled by (dist + thickness) / dist about the camera's axis), so each
tunnel's walls lie along the rays and every hole is seen whole. `--tunnels straight` keeps fix 4 and `--tunnels
camera` forces this; ours merges 4.1 % and keeps its straight, widened tunnels (compare.json identical). Before and
after, SSIM and openings IoU: 01 0.450 to 0.536 and 0.321 to 0.475; 02 0.507 to 0.582, 0.474 to 0.611; 04 0.471 to
0.559, 0.405 to 0.655; 06 0.456 to 0.475, 0.482 to 0.571; 07 0.386 to 0.383, 0.141 to 0.160; 09 0.579 to 0.575, 0.824
to 0.859; 11 0.325 to 0.403, 0.223 to 0.300; 14 0.686 to 0.781, 0.615 to 0.769; 16 0.445 to 0.563, 0.607 to 0.801;
18 0.545 to 0.769, 0.461 to 0.770 (before fix 6, when the user called it "really beautiful", 0.704). With fix 8, 03
0.469 to 0.497 and 05 0.418 to 0.462 (their IoU is across a change of reading). 12, 15 and 17 stopped at the fill's
check.

*Fix 10, on a wrong premise.* 15's failed fill after fix 8: the halving's culprits sat on one row, the carved field's
bottom edge, where `keep_field` cuts openings with a straight line, and I took that line for what breaks the fill. On a
failed fill those openings are now made stone. It did not let 15 build, and 12's and 17's culprits were off the edge;
fix 13 found the cause. It stays as a repair that runs only after a failed check.

*Fix 13, the outlines' turning (2026-11-26).* The outlines dumped before the fill (`--dump-loops`) and filled in a
separate script: 15's 1,632 filled to 831,855 px2 by scanfill and by Fill Curve alike, as dumped or with a 0.001 or
0.01 px jitter, exactly their even-odd area; no two cross, none share a point. The check compares the fill with the sum
of the outlines' signed areas, 1,099,762 px2, because 1,453 outlines were turned against their nesting (12: 628 of
5,543; 17: 6,660 of 6,973; ours 72 of 353, its check passing at 0.953 only because its holes are large).
`common.contours` turns each outline by one sample, the pixel nearest a point 0.35 px to its left, which can lie
across a thin bar or a small hole, and fix 9's uncut fine holes made those common. The fill reads no turning; the build
did: the check failed on fills that were right, the halving then dropped outlines that were never broken (03 lost a
115,719 px opening, rendered as a grey haze over its lower arch), and the size floors told holes from pieces by the
sign. Now every outline is turned by its nesting depth, as the fill counts (`--sample-turning`: as before). Ours:
compare.json identical, its build.json now recording 72 turned and its outlines' area 1.1248 m2 (its front face's).
12, 15 and 17 build: 12 SSIM 0.383 (C-022's inverted reading) to 0.667; 15 0.549 (before fix 8) to 0.597; 17 0.428
to 0.684, openings IoU 0.191 to 0.711, the courtyard through every hole. C-020's knife edge (T-014) stands; it was not
what stopped these.

*Fix 11, fix 12 (first form), fix 14, fix 15, and fix 12 revised (2026-11-26).* Fix 11: under the dark rule the colour
step fades to none below the stone's darkest. Fix 12: 03 without its bevel, SSIM 0.497 to 0.529, IoU 0.612 to 0.671
(the bevel widens the stone by its radius: 11.7 % of ours's holes' half-width, up to 37 % on the batch); first form,
the bevel at most 12.5 % of the half-width. Then 15 kept a pale ring at each hole's edge (0.675 against the photo's
0.32): with no bevel and the outline blurred over 1 px, 0.576, SSIM 0.597 to 0.625, IoU 0.530 to 0.595 (the blur
alone 0.602 and 0.540). Revised: where the holes' half-width is under 4.2 px (ours 4.64) no bevel and the blur 3 px
times the half-width over ours's, at least 1 (`--fixed-bevel`: 0.5 mm and 3 px). Fix 14: with fix 11, 03's colour fit
landed at k 1.05 with the red slope matched and the blue 30 times too small, and a pixel at 0.1 had its colour made
ten times as strong: the ledge's shadow and the rosettes' holes red. A k is kept only when both slopes are within a
factor of two of the photo's (`--sat-any-fit`). Fix 15, 03's speckled wall: not the speck step (without it SSIM 0.470
against 0.497), not the square opening in the tilt (`--tilt-min`: 0.502, the squares unchanged), not Marigold's
normals (spread under 0.02 on the wall); without the detail tilt the squares went but so did the joints (SSIM 0.372).
The tilt's 8 per unit was set on ours, whose detail spreads 0.0171; 03's spreads 0.0793 and its normals were tilted
past where the shading saturates. With 1.7 the squares went: SSIM 0.541 to 0.547, lines near the photo's 0.450 to
0.618. So the tilt is scaled so the detail's spread is at most 0.018 (`--fixed-detail`). Ours, rebuilt with all of
these: every measure identical (one pixel of one mask's count differed, 851,095 against 851,094: render noise).

*The batch with fixes 1 to 15 (2026-11-26; `shots/jali-batch/c023_fixes_9_15.jpg` and `_crops.jpg`, photo | the render
the user last saw | now).* All 18 reach a render (12 since C-022; its round-3 build aborted in Cycles and its results
are from fix 13's round). SSIM, last seen to now: 01 0.450 to 0.548, 02 0.507 to 0.588, 03 0.469 to 0.555, 04 0.471
to 0.546, 05 0.418 to 0.467, 06 0.456 to 0.469, 07 0.386 to 0.389, 08 0.798 to 0.793, 09 0.579 to 0.553, 10 0.825 to
0.824, 11 0.325 to 0.397, 12 0.383 to 0.667, 13 0.727 to 0.696, 14 0.686 to 0.782, 15 0.549 to 0.673, 16 0.445 to
0.551, 17 0.428 to 0.680, 18 0.545 to 0.783: up in 13, down in 4 (08, 09, 10, 13, all in the round of fixes 12 revised,
14 and 15). By my glance: 03's wall is stone again, 15's bars are the photo's width (the render reads back 15.4 %
open against the reading's 16.2 %), 17's and 18's courtyards show through every hole; 05's interior is purple, 06 is
unchanged. Two of the round's changes were then taken apart on 09 (SSIM 0.553): with its bevel 0.566, with the detail
unscaled 0.563 and fine detail's correlation 0.31 against 0.15.

*Round 4, written and not yet run (2026-11-26).* Fix 15 by the tilt's median (at most 0.06; ours 0.055), not its
spread; fix 12's cut at a half-width of 3.0 px, not 4.2; fix 16, under the dark rule the colour factor at most 3 (05:
refitted at k 1.2 with both slopes within a factor of two, its factor 29 at the stone's darkest). None reaches ours by
its rule; its rebuild has not run. The batch's run of it stopped: the laptop went on battery mid-run and each fit
render took about 420 s against 1.7, so the builds ran out their 30 minutes (01, 02, 03, ours) and the rest were
stopped. Cycles also aborted 3 builds in about 50 in its Metal shader cache (`ccl::path_cache_get`, a pointer freed that
was never allocated, as a render starts); `run_batch.py` now runs such a step once more.

*Fix 17, the user on 03's sheet (2026-11-26): "the actual graving/stone isn't uniform in color all the way. sometimes
it decreases ... most probably due to the moss affecting it from the rain".* Measured, it holds. The dark rule's one cut
is the whole photo's Otsu threshold, set in 03 by the pale wall against the dark lattice (0.48). In a patch of the
lattice's lower left, 37 % of the pixels are near black (under 0.05, the holes) and the rest spread evenly from 0.05 to
1.0 with no second peak, so at that cut 59 % of the patch read as hole: stained stone, darker than the cut. Not the
working size: at the photo's full 1,928 px the same cut reads 59.7 % against 59.4 %. Three local cuts tried in scratch
code: the pixel over a bright envelope (a 9 px max, smoothed), which barely moved (33.3 % open to 32.6 %), since bright
branches lie within a few pixels of every stained strand; Otsu tile by tile (64 px), its cuts about 0.43, little better;
and the one kept, the cut halfway between the local mean of the dark pixels (under 0.1) and the local mean of the
rest, Gaussians of 8 px, where a tenth of the neighbourhood is dark, never above the global cut. In the chain
(`common.classify_dark`): 03's patch 51.5 % hole, the whole picture 25.2 % open after fix 8 (28.7 % before), the
lattice's cut about 0.32; 05 24.8 % to 24.1 %, 12 44.7 % to 40.1 %, 15 16.2 % to 14.7 % (its fine panel's reading had
been more open than the photo's halfway edge, 30.8 % against 27.7 %). shot.json `"dark_cut": "global"` keeps the one
cut. Ours is on the colour rule. Written, not yet rendered (on battery): their reading, build and comparison are queued.

*Round 4 and fix 17, run (2026-11-26, on AC; `shots/jali-batch/c023_round4.jpg`, photo | last seen | now, and
`c023_round4_stain.jpg`, 03's and 05's stained lattice, photo | round 3 | now; contact pages `contact_c023r4_*.jpg`).*
The first try at it on AC stalled like the battery run: four jobs of about 3.2 GB each with 9.1 GB of swap already in
use, and every render crawled at once; with two workers the fit renders took 1.2 to 1.9 s again. SSIM, last seen to
now (round 3 between): 01 0.450 to 0.548 (0.548), 02 0.507 to 0.582 (0.588), 03 0.469 to 0.581 (0.555), 04 0.471 to
0.550 (0.546), 05 0.418 to 0.549 (0.467), 06 0.456 to 0.475, 07 0.386 to 0.385, 08 0.798 to 0.799 (0.793), 09 0.579
to 0.575 (0.553), 10 0.825 to 0.826, 11 0.325 to 0.398, 12 0.383 to 0.690 (0.667), 13 0.727 to 0.716 (0.696), 14
0.686 to 0.783, 15 0.549 to 0.670 (0.673), 16 0.445 to 0.564 (0.551), 17 0.428 to 0.690 (0.680), 18 0.545 to 0.798
(0.783): up in 13, down in 2 (09 by 0.004, 13 by 0.011), 3 flat. 16 meets the four core bars, the first of the batch
to. Round 4 gave back what round 3 took from 08, 09 and 10, and cost 02 (half-width 3.12 px, just over the new cut:
0.588 to 0.582). By my glance 03's stained tracery is back between its branches, 05's purple is gone and its lattice
is dense and grey as in the photo, and 12's lattice and frame read as its photo; 13 of 18 read as their photos (01,
02, 03, 04, 05, 08, 09, 10, 12, 13, 14, 15, 17), 3 have the structure right and the light or colour not (11, 16, 18),
and 06 and 07 are outside the method. Ours, rebuilt with all of it: every measure as committed but two at ±0.0001 and
one mask's count by a pixel (render noise).

*Fix 12, third and fourth forms (2026-11-26).* Taken apart on two backlit shots: 13 (half-width 2.995 px) with its
bevel 0.725 against 0.716 without (IoU 0.817 against 0.791), 10 (3.48) without it 0.810 against 0.826, as 09 (3.92):
every loss from removing the bevel had been on a screen lit from behind, every gain on lit stone (03, 15 under the
dark rule; 01, 02 under the colour rule). Lit from the front, the rim catches the light as a pale ring inside each
dark hole; lit from behind it lies on the bright edge, like the glow at a backlit hole's edge. Third form, the bevel
off only where not backlit (and under 4.2 px): 02 0.582 to 0.588, 13 0.716 to 0.725, but the finest backlit lattices
lost, where the bevel also takes a large share of each hole: 17 (1.81 px) 0.690 to 0.647, its render 12.4 % open
against the reading's 14.7 %; 14 (2.58) 0.783 to 0.755; 18 (2.57) 0.798 to 0.769; 16 (2.72) 0.564 to 0.563. In order of
half-width the backlit seven are hurt at 1.81, 2.57 and 2.58, level at 2.72, helped at 2.995, 3.48 and 3.92. Fourth
form, kept: no bevel under 4.2 px lit from the front, under 2.8 px backlit; 14, 16, 17 and 18 back to their round-4
values exactly. A threshold placed between seven points, monotone in them; recorded as that.

*Fixes 18 to 20, on the user's look at 03 and 05's lattice crops (2026-11-27; `c023_fine.jpg`, photo | what the user
saw | now).* The user: "on the top left corners, the areas look a bit grainy ... there are still gaps, some minute
details are lost, and the color is a bit darkened than expected." Measured on those crops, three causes. Dark: the
intrinsic model reads a thin bar with the dark holes beside it, so 03's raw albedo on the lattice's stone was 0.114
against 0.224 over all its stone (0.153, 0.177, 0.194 at 1, 2, 3 px from a hole), while the photo shows that stone as
bright as the wall; the render's lattice came out at the albedo's ratio, half the wall. Fix 18: where the albedo on
the stone's edges is under 1/1.1 of its cores' (2 px in), its slow change comes from the cores (03 0.871, 05 0.843,
04 0.909, 07 0.763, 12 0.817, 16 0.826, 17 0.878; ours 0.98). Grain: the pale-speck step brightens any bright dot
narrower than its 3 x 3 square, and against dark holes every thin bar is one: 87 % of 05's corner stone brightened,
69 % by the most (2.8 times), the wider parts of the same tracery not at all. Fix 19: with fix 18, the holes are
filled with the stone's level around them first, so only a dot paler than its stone counts: in 05's corner 87 % of
the stone brightened to 54 %, by the most 69 % to 15 % (03's: 66 % to 49 %, 32 % to 8 %). Gaps: none of the lost stone was read as opening; where the outline is not blurred,
two stone pixels touching only at a corner were always cut apart, a thin diagonal strand broke into pieces of a pixel
or two, and the pieces under 30 px were dropped (74 % of 05's lost bright stone, 47 % of 03's). Fix 20: a corner
contact joins the class that is the minority in its 9 x 9 neighbourhood (03: 2,628 of 7,188 such contacts joined as
stone, 05: 3,773 of 7,297), only on unblurred outlines; ours's 3 px outline had 6 exact ties by chance, and is left out.
Switches: `--albedo-edges`, `--speck-holes`, `--saddle-split`. On the crops: 03's stone 0.622 to 0.730 (photo
0.826), 05's 0.572 to 0.653 (photo 0.773); bright stone shown dark 03 5.2 % (unchanged), 05 10.2 % to 8.0 %. SSIM
over the 14 shots the fixes reach (the other four have none of them): 03 0.581 to 0.604, 04, 05 and 16 +0.003, 07, 12
and 17 +0.002, the rest within 0.001; none down. By eye: 03's lattice brighter and its coiled column back, 05's palm
fronds and more of its tracery back; 05's lower left still darker than its photo, and both still under the photo's
brightness. Ours, rebuilt: its measures as committed; its log gains two fields that fix 13 corrected (`turned`, and the
enclosed area now equal to the front face).

*Fix 21, the tone curve checked pixel by pixel (2026-11-27; written, off by default, waiting on the user;
`c023_tonecheck.jpg`).* The user, on `c023_fine.jpg`: "better! but the tone is still a bit darker than the original".
Before the tone curve the render's lattice already matches the photo: 03's stone next to the holes 0.689 against
0.686, further in 0.80 to 0.81 against 0.80 to 0.82. The curve took it to 0.484 and 0.75, its lower exponent 2.82
(05: 2.27), because the photo's darkest tenth of stone (0.556) is far darker than the render's (0.723); mapped, those
pixels are the shadows of the wall's mouldings and the stains, which the render does not have at any scale up to 10 px
(fitted on both smoothed: 2.59), and the percentile match darkens every mid-tone in their place. Three other fits tried
in scratch code and not kept: on the carved field only (03's field is 94 % of its box: 2.71), on the stone near the
openings (worse: 3.08 to 3.73), pixel by pixel (03 1.42, but backlit 09 and 16 run to the limit, 0.30). Kept, behind
`--tone-check`: each half of the curve stays only where it brings the render's stone nearer the photo's, pixel by pixel,
than no curve. 03 and 05 lose their lower half (03: 0.187 against 0.175 with none), keep their upper. On the crops the
stone comes to the photo's: 03 0.611 to 0.747 (photo 0.755), its edges 0.484 to 0.686 (0.686); 05 0.494 to 0.644
(0.694). But the curve's lower half had also crushed the grey in the holes (the pixel filter's spill of the stone's
light, lit tunnel walls), and the holes go from 0.017 to 0.048 (03; photo 0.013) and 0.060 (05; 0.016): the openings'
IoU falls 0.696 to 0.653 and 0.670 to 0.629, 03's SSIM 0.604 to 0.590, 05's 0.552 to 0.570. Ours loses its lower half
too (0.0718 against 0.0702; a 1.06 to 1.00): SSIM 0.5429 to 0.5427, openings IoU 0.7956 to 0.7953, by eye the same.

*Open, not yet fixed.* The tone curve's upper exponent sits at its limit of 4.0 in 8 of the 13 renders that C-022
measured (ours 2.12), and with the fit's stone corrected 03, 05, 09 and 15 end at both limits (0.3 and 4.0); the
cause is not found. The 25 % fit renders are not it: their stone's median is within about 10 % of the full render's
(09: 0.149 at 337 W against 0.116 at 273 W; 13: 0.319 against 0.343 at one power). 13 and 14's holes render dim pink
where the photos' are lit white: the light behind a backlit screen is not yet the photo's.

**Result (2026-11-27, after fixes 1 to 20):** as below, with 03's and 05's lattices brighter and fuller on the user's four points
(fixes 18 to 20; SSIM up on 7 of the 14 shots they reach, none down); still darker than the photos there. Waiting on
the user's glance at `c023_fine.jpg`.

*After fixes 1 to 17, fix 12 in its fourth form (2026-11-26):* 18 of 18 photos reach a render; by my glance 13 read as their photos
(01, 02, 03, 04, 05, 08, 09, 10, 12, 13, 14, 15, 17), 3 have the structure right and the light or colour not (11, 16,
18), 06 and 07 are outside the method; 16 meets the four core bars. The user named the cause of fix 17 (stained
stone); the rest of what is said under the first result below holds. Waiting on the user's glance at
`c023_round4.jpg` and `c023_round4_stain.jpg`.

*After fixes 1 to 15 (round 4 written, not run):* 18 of 18 photos reach a render, and by my
glance, before the user's, 11 read as their photos: 01, 02, 03, 04, 08, 09, 10, 13, 14, 15 and 17 (8 before fixes 9 to
15, 3 at C-022). Five have the structure right and the colour or light not: 05 (its interior purple), 11 (its centre
muddled), 12 (its central opening red where the photo's is dark), 16 (its floor), 18 (grey where the photo's light is
warm). 06 and 07 are outside the method (T-022). So field 5's count is met, but not as its first branch put it: most
of the gain came from two faults in the build, not from constants fitted to our photo (the cap's straight tunnels,
fix 9; the outlines' turning, fix 13), and the rest from constants that were (the floors, the bevel and blur, the
detail tilt's strength, the colour step). None of the 18 meets the four core bars. Waiting on the user's glance at
`c023_fixes_9_15.jpg`.

*Before fixes 9 to 15:* waiting on the user's glance at `contact_c023_1.jpg` to `_3.jpg`. Measured: 17 of 18 photos reach a render
(13 at C-022), and by my glance 8 read as their photos (3 at C-022), one short of field 5's 9. The faults left are in
the method, as field 5's second branch says, and in this order of how many shots they touch: the light for a screen
lit from behind or by its room (08, 09, 10, 13, 14, 16, 17, 18: a front spot and a tone curve at its limits); the
wall seen through the holes (ten flat bands, where 04, 14, 17 and 18 look onto a scene); the edges' sharpness (03 and
18's twice the photo's width; the bevel untested); 12's fill (4,686 outlines); 06 and 07 outside what the method does.

### C-024 · Each screen's structure from its traced openings: its repeat, its mirror, and how much one motif rebuilds

**Opened:** 2026-11-27, on the user's word ("we should start working on extracting the structural aspects, the motifs,
repetition, symmetry, grid"), with C-023's last batch (fixes 18 to 20) still running; its result is written when the
batch lands. From T-023.

1. **WHERE WE ARE.** 19 screens are rebuilt from their photos (ours and C-023's 18), each as a traced opening mask, a
   relief and a stone colour; 13 of the 18 read as their photos. Only ours has had its structure measured: C-009 found
   its repeat vectors (141.2, −177.3) and (146.3, 173.4) px at the working size and its mirror axis at x = 613
   (`shots/jali-match/results/symmetry.json`), with its field's rows hard-coded.
2. **WHAT WE ARE DOING.** For each of the 19 traced opening masks, inside its carved field
   (`results/read_photo.json`'s `field_box`): find the two repeat vectors (the strongest peaks of the mask's
   autocorrelation, as `symmetry.py` does) and the best vertical mirror axis, then predict every pixel of the mask
   from its copies one lattice step away and from its mirror image, leaving the pixel's own value out, and score the
   prediction against the mask by IoU of the openings. The same prediction from the same number of copies at random
   shifts is the baseline. A new `shots/jali-batch/structure.py`, run in the repo's `.venv`; `symmetry.py` is not
   touched (ours's build imports it).
3. **WHY.** Unknown: whether the traced masks carry their design's structure at all. They hold reading errors, wear,
   and the camera's slant, and some designs are not lattices (03 and 05's trees). Finding a lattice in a real photo is
   studied (Liu, Collins and Tsin 2004 on wallpaper groups; Hays et al. 2006 and Park et al. 2009 on lattices bent by
   perspective), and making new star patterns from a motif and its symmetry group is too (Kaplan and Salesin 2004); not
   known is whether our masks, as traced, are good enough to start from. After: for each screen, a number for how much
   of it one motif and its mirror rebuild.
4. **WHAT IS AFFECTED.** Nothing that exists changes: a new script and a `results/structure.json` per shot. The check
   on the script itself: on ours it must find C-009's vectors within 2 px. T-023's question (what a generator would
   learn from) waits on this card's answer.
5. **CONCLUSION.** A screen counts as a motif on a lattice when its leave-one-out prediction reaches an openings IoU of
   0.70 (about what our own render reaches against the photo; a motif that describes the screen worse than our render
   does is no description) and beats the random-shift baseline by 0.15. If at least half of the 19 count, the library's
   form is motif, lattice and mirror, and the next card cuts each counted screen's motif out as one clean tile. If
   fewer, the failures are sorted by their autocorrelation: peaks that drift across the field (the camera's slant) go
   to a card that straightens the photo first; no peaks at all (no lattice) means that design needs another
   description, such as a branching one for the trees.
6. **CONSEQUENCE OF NOT DOING IT.** The rebuilt screens stay photo-matched surfaces with no design in them, and T-023
   (new designs from the library) has nothing to learn from.

**Measures (2026-11-27; `shots/jali-batch/structure.py`, `c024_masks.jpg`, `c024_panels.jpg`).** The check holds: on
ours the finder gives (141.8, −177.7) and (146.4, 174.1) px, within 0.7 px of C-009's. Whole fields, the openings IoU
of the prediction from one lattice step and the mirror (baseline in brackets): ours 0.344 (0.071), 02 0.396 (0.213),
08 0.460 (0.107), 10 0.472 (0.157), 12 0.462 (0.316), 13 0.395 (0.122), 16 0.318 (0.172), 17 0.324 (0.150); eleven
have no peak of 0.25 and are predicted by the mirror alone, from 0.000 (07, whose reading is not of a screen) to
0.387 (05). In 02, 08, 16 and 17 the strongest repeat is a panel's (281, 555, 180 and 94 px), not a motif's. The
masks show why: most fields are not one design. 13 to 18 are mullioned windows whose panels carry different
patterns (15 a grid of square panels, each its own star), 08 and 10 a lattice round an inner arched panel, and the
fields of 03 to 07 and 09 take in wall, porch, room or the sunlit floor. On seven panels cut by hand from the masks
(fractions of the field in `results/structure_panels.json`) every score rises and none reaches the bar: ours's lower
field 0.454 (0.074), 08's side strip 0.435 (0.237), 10's 0.446 (0.256), 12's lattice 0.570 (0.375), 13's lower left
panel 0.638 (0.164), 16's 0.517 (0.276), 18's 0.460 (0.303). The drift is not what keeps 13's panel under: its vectors
move under 1.2 px between its quarters (ours's lower field 2.5 to 5.9 px).

**Result (2026-11-27, closed): no, as traced.** Laid over itself one repeat away, a screen's traced openings match at
most 47 % of themselves over a whole field (10) and 64 % within one panel (13), against 0.70 asked; none of the 19
counts. Field 5 named two causes and found a third, the larger: a field holds several designs (panels, frames,
surroundings), and cutting one panel out raised every score, by 0.10 to 0.24. Within a panel, unaligned copies of a
hand-carved motif, traced at a few pixels to a hole, still differ by a third. Not tested here: whether copies each
moved by one shift onto the others' median give a motif that clears the bar (the next card, if chosen), and finding the
panels without a hand.

### C-025 · One motif per panel from its copies, each moved by one shift onto the others: does it rebuild the panel?

**Opened:** 2026-11-27, on the user's word ("continue with c-025 next"), C-023's last batch still running.

1. **WHERE WE ARE.** C-024: laid over itself one repeat away, a traced panel matches at most 64 % of its openings (13's
   lower left panel; baseline 16 %), against 0.70 asked; over whole fields at most 47 %. Within 13's panel the lattice
   moves under 1.2 px across it, ours's lower field 2.5 to 5.9 px.
2. **WHAT WE ARE DOING.** On seven panels, each one design, cut by hand as fractions of the field (`c025_panels.jpg`:
   ours's lower field 0,0.35,1,1; 08's inner arched panel 0.35,0.52,0.65,0.80; 10's 0.36,0.55,0.64,0.82; 12's lattice
   below its window 0.05,0.55,0.95,0.92; 13's lower left panel 0.01,0.74,0.44,0.99; 16's central lower panel
   0.43,0.55,0.62,0.78; 18's second lower panel 0.23,0.76,0.48,0.99): cut a square patch 1.2 repeats wide at every
   lattice point, and four times over move each patch by the one whole-pixel shift (within a tenth of the repeat) that
   best matches the mean of all the other patches. Then predict each patch from the others' mean, its own pixels left
   out, and score the openings by IoU. The baseline is the same, from patches at random places, with the same shifts
   allowed. `shots/jali-batch/motif.py`, beside C-024's `structure.py` (whose functions it uses).
3. **WHY.** Unknown: whether the traces hold a clean motif once each copy may sit a few pixels off its ideal place
   (hand carving, the camera's slant), or whether the copies differ in shape, beyond any shift, by too much for one
   motif to stand for them. After: for each panel, how much of it one motif rebuilds, and the motif itself, as an image.
4. **WHAT IS AFFECTED.** Nothing that exists: a new script, `results/motif_panels.json` per shot, a sheet of the seven
   motifs. One shift per copy is two numbers fitted to each patch of thousands of pixels; the baseline gets the same
   freedom, so it is the difference that counts.
5. **CONCLUSION.** The bar is C-024's: IoU 0.70 or more, and 0.15 over the baseline. If 4 or more of the 7 panels
   count, a clean motif comes out of the traces with one shift per copy, and the next card finds the panels without a
   hand. If 3 or fewer, the copies differ in shape at the trace's scale (a few pixels to a hole), and the motif should be
   read from the photo's brightness averaged over aligned copies, not from the traced openings.
6. **CONSEQUENCE OF NOT DOING IT.** C-024's no stands for the traces as they are, and it stays unknown whether the
   rebuilt screens hold their motifs at all; T-023 has nothing to start from.

**Measures (2026-11-27; `shots/jali-batch/motif.py`, `c025_motifs.jpg`: one patch | the motif's mean | the motif at
0.5).** Openings IoU from the other patches' mean, aligned (unshifted; random places, aligned the same): 13 0.830
(0.817; 0.326), 18 0.803 (0.780; 0.697), 12 0.674 (0.447; 0.558), 16 0.658 (0.621; 0.474), ours 0.562 (0.540;
0.119), 10 0.400 (0.284; 0.389), 08 0.302 (0.146; 0.314). Copies per panel: 13 in 13's, 81 in 18's, 2,229 in 12's, 7 in 16's and ours's, 25 in 10's, 29 in 08's.
Most of the gain over C-024 is from the mean of all the copies rather than the four nearest and the mirror (13's
panel 0.638 to 0.817 unshifted); the shifts add 0.01 to 0.04, except on 12 (0.22), whose many copies sit up to 4 px
off a lattice fitted over 815 px. On 08 and 10 the finder took a 21 to 26 px echo inside the motif for the repeat:
the motif's mean is one blurred hole, the shifts ran to their limit, and the score is the baseline's. Their inner
panels hold too few copies of the true repeat for its peak; that is the instrument failing, not the copies. 18's motif
is clean to the eye (a lattice of rounded squares) and misses the bar only by its margin over the baseline: its panel
is so open that patches anywhere predict 70 % of it. Ours's and 16's motifs, from 7 copies each of a large motif, come
out blotched, the copies' shapes differing.

**Result (2026-11-27, closed): 1 of 7, so no by the bar, but not for field 5's one reason.** Built from the mean of a
panel's copies, each moved by one shift, a motif rebuilds 83 % of 13's panel (random places 33 %): a clean star and
its ring of holes, the first motif drawn out of a trace. The other six fail for three different reasons, and field 5
named one: copies that differ in shape (ours, 16: seven copies each of a large motif). The others are the measure's:
the repeat not found on two small panels (08, 10), and a bar the densest patterns cannot clear over their own
openness (18 at 0.80, 12 at 0.67, against baselines of 0.70 and 0.56). So field 5's second branch, the motif read
from the photo's brightness, is supported only for the large motifs.

### C-026 · The motif measure fixed: a repeat that the whole lattice agrees on, and a score a flat guess cannot pass

**Opened:** 2026-11-27, on the user's word ("commit, push, then perform the next"; the next was this, my first choice).

1. **WHERE WE ARE.** C-025: 1 of 7 panels gives a motif that clears the bar (13, 0.83 against 0.33). Two of the six
   failures were the measure's: on 08 and 10 the repeat finder took a 21 to 26 px echo inside the motif for the repeat
   (it takes the shortest strong peak), and on 18 and 12 a score of openings alone lets copies from anywhere reach 70 %
   and 56 %, since an open panel is mostly opening.
2. **WHAT WE ARE DOING.** Change the measure in two ways and rerun it on C-025's seven panels as cut, nothing else
   changed. The repeat: of the pairs among the strongest autocorrelation peaks, the one whose lattice points (every
   sum of up to two steps of each vector) have the highest mean autocorrelation, the smallest cell among those within a
   tenth of the best; an echo's lattice puts points where the pattern does not repeat. The score: the mean of the
   openings' IoU and the stone's (a prediction of all opening scores half the open share). Both as switches in
   `structure.py` and `motif.py`; C-025's way stays reproducible.
3. **WHY.** Unknown: how many of the seven panels hold a motif once the measure stops failing on its own, which is
   what C-025's count could not say. After: that count, and a measure the next cards (finding panels without a hand,
   reading the motif from the photo's brightness) can be judged by.
4. **WHAT IS AFFECTED.** C-025's count (kept as measured, under its own measure); `results/motif_panels.json` gains
   entries under the new method. Checks on the new repeat finder: on ours's whole field it must still give C-009's
   vectors within 2 px, and on 13's panel the same lattice as C-025's.
5. **CONCLUSION.** The bar: a balanced IoU of 0.80 or more (ours's render scores 0.84 against its photo, openings
   0.80 and stone 0.89; a motif describing its panel worse than our render describes the photo is no description) and
   0.15 over the random-place baseline. If 4 or more of the 7 count, the traces give a motif for most single-design
   panels, and the next card finds the panels without a hand. If 3 or fewer, the ones still failing are those whose
   copies differ in shape, and their motifs should be read from the photo's brightness.
6. **CONSEQUENCE OF NOT DOING IT.** Every later card about motifs is judged by a measure that fails on small panels
   and on open patterns, and C-025's 1 of 7 cannot be told apart from the measure's own faults.

**Measures (2026-11-27; `motif.py --finder consistent --score balanced`, `c026_motifs.jpg`).** The checks: on ours's
whole field the new finder gives (139.3, −177.4) and (147.8, 173.6) px, within 2.0 px of C-009's (the old finder 0.7
px; inside the limit, at its edge); on 13's panel the same lattice as C-025's; on 12's the same lattice in its shortest
basis. Where C-025's finder took echoes it now finds 08's repeat at (78.7, 78.1) and (79.2, −77.7) px and 10's at
(63.5, 61.4) and (62.2, −62.9), and 18's at a square 38 to 39 px where C-025 had a finer pair. Balanced IoU, aligned
(unshifted; random places): 13 0.867 (0.841; 0.484), 18 0.811 (0.772; 0.669), ours 0.723 (0.703; 0.448), 12 0.700
(0.503; 0.568), 16 0.636 (0.605; 0.419). 08's and 10's inner panels (140 x 235 and 105 x 184 px) hold fewer than
four copies of their true repeat at 1.2 repeats a patch: not measured. On 12 the shifts run to their limit (3 px) over
a panel 64 repeats wide; a larger limit would let a copy jump to its neighbour, a quarter of a repeat away. 16's motif
is two motifs: a fine net that repeats at the lattice found, and larger shapes over it that do not (`c026_motifs.jpg`).

**Result (2026-11-27, closed): still 1 of 7.** With a repeat the whole lattice agrees on and a score that judges stone
and openings alike, 13 counts (0.87 against 0.48), 18 misses the margin by 0.008 (0.81 against 0.67), ours, 12 and 16
miss the bar (0.72, 0.70, 0.64), and 08 and 10 cannot be measured on panels that small. The measure's two faults are
gone: no echo is taken for a repeat, and no open panel passes by being open. What fails now is not one thing, as field
5's second branch put it: ours's seven copies differ (shape, or the reading); 12's lattice bends further than one shift
per copy can follow; 16 is a design of two levels. To the eye 13's, 18's and 12's motifs are clean.
