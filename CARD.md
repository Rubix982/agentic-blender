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
Limits: one cube and default settings for every operator, so these are lower bounds; a second pass giving those
add-ons the input they are made for was written and not run, because it runs their code again. The run's download
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

**Result:** —

