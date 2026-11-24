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
