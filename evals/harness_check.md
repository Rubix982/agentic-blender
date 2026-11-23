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

## Change before the first agent run (2026-11-23)

Until now no agent session had run. Before the first one, the sessions were moved out of the repository: an agent
working in `evals/runs/` could have found the guide, the checks and the reference solutions in the folders above it,
and Claude Code puts the repository's git status (whose commit messages name the guide) in every session's context.
Each session now works in a new folder under `/private/tmp` and is copied back into `evals/runs/` when done. Sessions
also load no MCP servers (`--strict-mcp-config`), because one configured on this machine drives a live Blender. A
probe session in such a folder listed no MCP tools and no Blender skill. The with arm's plugin is now taken from git tag
`v1` (`git archive`), not the working tree. Each record now notes the session's model, whether the skill was listed,
any MCP tools, whether a tool call touched the repository, and a session error (such as the usage limit), which stops
the run and is counted as not run rather than as a failure. After the change, `--set independent --arms
reference,wrong --tasks 1-2` gave reference 2 of 2 and wrong 0 of 2.
