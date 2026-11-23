# Threads

Open questions that surfaced while C-001 is open. One card at a time: these wait until C-001 closes.

### T-001 · Which free remote asset sources can a headless script pull from, and how?

**Status:** open
**Parent:** C-001
**Opened:** 2026-11-23
**Question:** v1 knows only the assets bundled with Blender; it names no remote source. Candidates: Poly Haven and
ambientCG (CC0, no account), Megascans (reported free again in November 2026, needs an Epic account: the user's call).
**Answer:** —

### T-002 · What do the most-used community extensions add, read in a throwaway profile?

**Status:** open
**Parent:** C-001
**Opened:** 2026-11-23
**Question:** v1 inventoried the 14 bundled add-ons only; 4.5's `BLENDER_USER_RESOURCES` and `BLENDER_USER_EXTENSIONS`
(listed in `--help`) let extensions be installed and inventoried without changing the user's own Blender.
**Answer:** —

### T-003 · What separates a contest-level realistic environment from a merely correct one, and can an agent reach it?

**Status:** open
**Parent:** C-001
**Opened:** 2026-11-23
**Question:** the guide checks that a script did what was asked, never whether the image looks real. Proposed test: a
photo match (one real photograph rebuilt in Blender, compared in the same frame, then shuffled pairs judged blind).
**Answer:** —

### T-004 · v2: the lessons the comparison found

**Parent:** C-001
**Opened:** 2026-11-23
**Question:** add to the guide the view-layer trap (`None` in `view_layer.objects` after `bpy.data.objects.remove`,
until `view_layer.update()`; `evals/results/stale_view_layer.py`), which crashed 3 of the 10 scripts written without
it, and the sun-elevation rule held back from v1.
**Answer:** in v2 (git tag `v2`): the view-layer trap (`data-model.md`, `errors.md`), the sun from elevation and
bearing with the sky's `sun_rotation` (`light-world-camera.md`), light and shadow linking, and looping keys and keyed
node inputs (`animation-video.md`), each from a new experiment.
**Status:** answered
