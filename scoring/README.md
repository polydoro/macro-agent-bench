# Scoring code and outputs

| Folder | Content |
|---|---|
| `visual-rubric-v1/` | Simple tasks (S01–S11): `rubric.py` (questions, options, weights), `aggregate.py` (answers to points), `judge.py` (judge adapter; reads the API key from the environment), `references.py` (blind numeric questions from the keys), `code_check.py` (numbers in the agent's saved tables), `combine_numeric.py`, `build_score100.py`, `legible_recheck.py`, tests, and `results/` |
| `c-rubric-v1/` | Complex tasks (C01–C05): same structure; `keys/` builds the per-run keys, `gold/` holds the gold standard, verdict questions and the 100-point score |
| `answer-keys/` | Keys for S01–S11 built from the official files the agents saved, grouped by publisher stamp; seasonal-adjustment gate (`sa_gate.py`, `resid_seas.py`, `x13.py`) |
| `scoreboard-v1/` | Joins scores with run receipts (time, attempts) into the result tables |
| `dump_rubrics.py` | Writes `docs/rubric-*.md` from the rubric modules |

The code reads the agents' deliveries and run receipts, which are not published, so only `dump_rubrics.py` and the tests run from this repository. Paths in the code point to the private run folder (`execucoes/…`). `NOTES.md` in each folder is the working log kept while scoring: every rule change, pilot and check, in order. Per-question judge transcripts (the raw API responses, which embed the delivery images) are not included; the per-question answers are, in `results/pass-*.json`, `numeric-*.json` and `verdict-*.json`.
