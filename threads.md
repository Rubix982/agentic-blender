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

### T-007 · How much frame-to-frame change does the compositor grain add to a moving shot?

**Status:** open
**Parent:** T-005
**Opened:** 2026-11-24
**Question:** C-006 found the render's noise adds 0.00018 to a forest dolly's flicker at 128 samples; C-005's grain
(Overlay 0.06, a new pattern every frame) was measured only as graded against clean on one frame (0.0088), so its own
flicker is unknown.
**Answer:** —

### T-008 · Which enums read from `bl_rna` list only a placeholder, like the view's `look`?

**Status:** open
**Parent:** T-005
**Opened:** 2026-11-24
**Question:** C-008 found `ColorManagedViewSettings.bl_rna.properties["look"].enum_items` lists only NONE, while the
Standard view takes eight looks; the guide's enum lookups (`kb.py enums`) may miss every enum filled in at run time.
**Answer:** —


### T-009 · How can one photograph give a carving's fine relief: crisp edges, incised rims, raised forms?

**Status:** answered
**Parent:** T-005
**Opened:** 2026-11-24
**Question:** C-007 to C-009 got the jali's openings and symmetry from its photo but not its relief: one top-lit photo
gives only the up-down slope of the surface, and our shading-to-height step rounds every step into a soft slope.
**Answer:** C-011 (CARD.md; `areas/production.md`, items 13 to 18): a learned normal map of the photo, used as the
front's normals with heights from it for the shadows, and the photo's own light and dark for the weathering; judged
"at a glance, yes". The light is still off (T-015).

### T-010 · Does a free, local normal-map model, run on the averaged motif, give crisp carving?

**Status:** answered
**Parent:** T-009
**Opened:** 2026-11-24
**Question:** Models trained on many images (Marigold, DSINE, Depth Anything V2) predict which way each bit of surface
faces; which runs on this laptop, under a licence we can use, and keeps the rims and edges?
**Answer:** yes, for Marigold normals v1.1 (CreativeML OpenRAIL++-M; diffusers, in the repo's .venv), run on the photo
itself, not the averaged motif: 8.3 s a 768 px tile on this laptop's GPU, and the forms band 0.549 against C-009's
0.399 once used as a normal map (C-011). DSINE and Depth Anything V2 were not tried. It flattens plain weathered stone.

### T-011 · Can the relief be fitted so that its render matches the photo (inverse rendering)?

**Status:** open
**Parent:** T-009
**Opened:** 2026-11-24
**Question:** Adjust the height map until a render of it under the fitted light matches the averaged motif, with the
symmetry and "edges are steps" as constraints (SIRFS-style, or Mitsuba 3's differentiable renderer).
**Answer:** —

### T-012 · Are there other photos of the same screen, from other angles or under other light?

**Status:** open
**Parent:** T-009
**Opened:** 2026-11-24
**Question:** Two or more views give real depth (photogrammetry: COLMAP, Meshroom); one view can only give what looks
right under its own light.
**Answer:** —

### T-013 · What number says "the detail is there", so the bar is not the judge's eye alone?

**Status:** open
**Parent:** T-009
**Opened:** 2026-11-24
**Question:** The lines measure fell from C-008 to C-009 while the forms got better; a measure that rewards crisp,
correctly placed relief (the render's local structure against the photo's, under the same light) is missing.
**Answer:** — (C-011 tried a forms band, luminance blurred over 5 px less over 21 px, on stone: it rose as the user's
judgement did, 0.399 to 0.549, with a ceiling of 0.557 at a 2 px misregistration; once the photo's own detail went into
the normals it partly measures the photo against itself, so it is a candidate, not an answer.)

### T-014 · Why does a 2D curve's fill break at 0.92 mm a point, when the same outlines in pixels fill?

**Status:** open
**Parent:** T-005
**Opened:** 2026-11-24
**Question:** C-009's trace (420 outlines) filled 0.3116 m2 of front face built in metres and 1.0485 m2 built in pixels;
one smoothed 15 x 4 px island did it. Is it the fill merging points closer than a fixed distance (Blender's scanfill),
and at what spacing does it start? C-011 found it is not the scale alone: at 15 mm the same island (about 981, 141),
smoothed, broke the fill in pixels too, and filled unsmoothed; at 5 mm several holes near (884, 440) and (922, 441)
broke it either way. The build now finds and repairs such a loop by halving; the cause is still open.
**Answer:** —

### T-015 · What light does the museum's photo have, and can the render's be fitted to it?

**Status:** answered
**Parent:** T-009
**Opened:** 2026-11-24
**Question:** C-011 closed "yes, at a glance" with the light named as what would make it better: the photo's spot pools
on the centre and leaves the frame dark, and lights the rims cream; the render's is even and dim (the stone's bright
end 0.478 against 0.669, the forms band's amplitude 0.53 of the photo's). Fit the spot's direction, cone and falloff,
not only its power, to the photo, now that the normals make the shading comparable.
**Answer:** for the pool, C-012: one spot 4.69 m out, a 13.1 degree cone slightly wider than round, fitted to a light
map of the photo, takes the map's error from 0.443 to 0.198; judged "it reads better". What is left inside the pool
(the bright end, the contrast) is T-016.

### T-016 · What tone curve did the photo's processing apply, and can the render go through the same one?

**Status:** active
**Parent:** T-015
**Opened:** 2026-11-24
**Question:** After C-012's fitted pool the stone's dark end is close (0.159 against 0.129) but the bright end is short
(0.514 against 0.674) about the same median, the shape an S-curve gives; the photo was edited in Polarr. C-008 found
Blender's contrast looks brighten the wall too, which is set exactly; a curve with the wall set through its inverse
would not.
**Answer:** —
