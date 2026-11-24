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
