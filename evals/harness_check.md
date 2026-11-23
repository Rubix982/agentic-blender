# The harness, checked before any agent ran (2026-11-23)

`evals/run_eval.py` was run on the independent set with its own solutions in place of an agent (no Claude session):
each script run once, headless, by the harness, then graded by `evals/independent/checks.py` through `tools/run.py`.

| Run | Right first time |
|---|---|
| `--set independent --arms reference` (the set writer's correct solutions) | 10 of 10 |
| `--set independent --arms wrong` (its deliberately wrong solutions: a removed API, a wrong unit, an unbaked simulation...) | 0 of 10 |

So the harness and the checks tell a right answer from a wrong one on every task of the independent set. The writer's
own set gets its reference solutions after the guide is frozen (`evals/tasks.md`, order of work).
