# Threads

Open questions that surfaced while C-001 is open. One card at a time: these wait until C-001 closes.

### T-001 · Which free remote asset sources can a headless script pull from, and how?

**Status:** answered
**Parent:** C-001
**Opened:** 2026-11-23
**Question:** v1 knows only the assets bundled with Blender; it names no remote source. Candidates: Poly Haven and
ambientCG (CC0, no account), Megascans (reported free again in November 2026, needs an Epic account: the user's call).
**Answer:** C-002 (CARD.md): Poly Haven and ambientCG through `scripts/assets.py` and `scripts/asset_import.py`, 10 of
10 test assets right (`areas/remote-assets.md`). Megascans not used (account).

### T-002 · What do the most-used community extensions add, read in a throwaway profile?

**Status:** answered
**Parent:** C-001
**Opened:** 2026-11-23
**Question:** v1 inventoried the 14 bundled add-ons only; 4.5's `BLENDER_USER_RESOURCES` and `BLENDER_USER_EXTENSIONS`
(listed in `--help`) let extensions be installed and inventoried without changing the user's own Blender.
**Answer:** C-003 (CARD.md): the top 20 by downloads, sandboxed; 13 have an operator that works headless with default
settings (`areas/extensions.md`); 15 once four were given the input they are made for (targeted_addons.py).

### T-003 · What separates a contest-level realistic environment from a merely correct one, and can an agent reach it?

**Status:** open
**Parent:** C-001
**Opened:** 2026-11-23
**Question:** the guide checks that a script did what was asked, never whether the image looks real. Proposed test: a
photo match (one real photograph rebuilt in Blender, compared in the same frame, then shuffled pairs judged blind).
**Answer:** in part, C-004 (CARD.md): from 17 published breakdowns, every setting-level technique 4 or more used runs
headless with a measured effect (`areas/realism.md`). Still open: the photo match, which tests the judgement left over.

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

### T-005 · Blender competitions over the years: techniques as settings, procedures (operator steps) and judgement

**Status:** active
**Parent:** T-003
**Opened:** 2026-11-23
**Question:** the user's idea: study winners across years (Best of Blender Artists, Suzanne Awards, CG Boost, Pwnisher,
Blender Studio's open movies) far deeper than click-by-click tutorials, writing each technique so an agent can run it.
A research agent is gathering it (scratchpad competitions_study.md, to become kb/research/).
**Answer:** —

### T-006 · Turning a click-path tutorial into operator calls

**Status:** open
**Parent:** T-005
**Opened:** 2026-11-23
**Question:** YouTube teaches by clicks and hotkeys. Ways in: the user pastes Blender's Info editor log (every click as
its Python call); or a lookup from Blender's own keymap and menu labels to operators (`kb.py keys`), built from the
running Blender like the inventory.
**Answer:** —

