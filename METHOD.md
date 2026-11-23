# Method

Everything in this guide is about one Blender: 4.5.14 LTS, on Apple Silicon with 16 GB. A fact about another version is
marked with that version. Every fact carries its evidence, as one of four tags:

| Tag | Meaning | Where it comes from |
|---|---|---|
| `[inv]` | read from Blender itself: a type, property, default, range, enum, operator or node socket | `skills/blender/scripts/inventory.py`, run headless; the output is `skills/blender/inventory/` and `skills/blender/scripts/kb.py` searches it |
| `[exp: path]` | measured here, by a script anyone can run again | `experiments/<area>/<name>.py`, result in `experiments/<area>/results/<name>.json` |
| `[lesson]` | learned on a real project, with what was measured there | `kb/lessons/`; the projects are described, not named |
| `[doc: link]` | from Blender's manual or Python reference for 4.5 | `docs.blender.org/manual/en/4.5/`, `docs.blender.org/api/4.5/` (local copies in `docs-local/`, not committed) |

A fact with no tag is a guess and is written as one ("probably", "untested").

## Experiments

One question per script. A script runs inside Blender (`python3 tools/run.py experiments/<area>/<name>.py`), starts from
an empty scene, and records its result with `tools/exp.py`: each fact is one plain sentence that could come out false,
with the numbers behind it. Images saved by an experiment stay at most 512 px; `.blend` files are not committed unless
small and needed. At most one Blender process per worker at a time, and four on the machine (16 GB; a Blender job takes
about 2 GB).

A failed attempt is a result too: when something errors, the error and what fixed it are the fact.

## Area pages

`skills/blender/areas/<area>.md`: how to do things in that area in 4.5, with code that was run. Each page opens with what
an agent most often gets wrong there, then the tasks in the order they come up, then the reference tables. Code snippets
are copied from experiments that ran, not written fresh.

## What this guide never contains

The names of the projects its lessons came from, their clients, brands, product or design identifiers, or any person.
A lesson says what was being built in general words ("a cloth garment on an animated figure").
