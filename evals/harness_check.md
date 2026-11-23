# The harness, checked before any agent ran (2026-11-23)

`evals/run_eval.py` was run on the independent set with its own solutions in place of an agent (no Claude session):
each script run once, headless, by the harness, then graded by `evals/independent/checks.py` through `tools/run.py`.

| Run | Right first time |
|---|---|
| `--set independent --arms reference` (the set writer's correct solutions) | 10 of 10 |
| `--set independent --arms wrong` (its deliberately wrong solutions: a removed API, a wrong unit, an unbaked simulation...) | 0 of 10 |

So the harness and the checks tell a right answer from a wrong one on every task of the independent set. The writer's
own set gets its reference solutions after the guide is frozen (`evals/tasks.md`, order of work).

## The writer's set (evals/tasks.md), after the guide's content was frozen

Reference and deliberately wrong solutions written by the guide's writer (`evals/reference/`), run through the same
harness:

| Run | Right first time |
|---|---|
| `--set writer --arms reference` | 10 of 10 |
| `--set writer --arms wrong` | 0 of 10 |

Each wrong solution failed on the intended reason: an unapplied boolean exported uncut (1), a sun tilted by its
elevation (2), smoothing with no angle rule (3), hex colours taken as linear (4), cubes left at 1 m (5), a cloth
stepped but not baked (6), MESH collision shapes resting on their margin (7), the frame left at 1920 x 1080 (8), a
single-layer EXR (9), the mesh left unselected for automatic weights (10). Task 5's first wrong solution (Distribute
Points on Faces at density 50 on the 4 m² plane, meant to give "about 200") gave exactly 200, so the check rightly
passed it; it was replaced by the 1 m cubes.
