# Scoring

Every delivery gets 100 points. The judge never gives an overall grade: it only picks one option per closed question, and the weights and aggregation are fixed code. Numbers are checked in code against keys computed from the official data. Neither the model nor the method is an input to any scoring function.

Full question text, options and weights: [rubric-simple-tasks.md](rubric-simple-tasks.md) and [rubric-complex-tasks.md](rubric-complex-tasks.md) (Portuguese, as sent to the judge).

## Simple tasks (S01–S11)

| Block | Points | Checked by | What it asks |
|---|---:|---|---|
| Identity (I1) | 10 | judge, on the final images | right country, indicator and scope |
| Conventions (I2) | 10 | judge, images | units, adjustment, frequency and annualisation as declared are admissible |
| Coverage | 20 | judge, images | each required trajectory (level, YoY, 3m SAAR of the total; YoY of components) is drawn over at least 24 months up to the latest period shown |
| Presentation (P1 legibility, P2 identification) | 20 | judge, images | readable; title, units, legends, source and final period identifiable |
| Numbers correct | 30 | code | the latest-period values in the agent's own saved tables match the answer key |
| Numbers legible | 10 | judge, then a blind recheck | those values are printed on a chart, table or label, readable without estimating from an axis |

Judge-scored blocks use the judge's option probabilities, averaged over 3 identical requests. Numeric legibility uses the judge's chosen option (probabilities spread too much over value ranges when nothing is printed). Components use best-K: only the K best components of an admissible list count (for example S01 counts the best 4 of 5 industrial groupings).

**Rules decided before scoring**

- **Latest data.** A delivery must reach the latest period available on its run date. If it stops earlier, latest-value questions score zero.
- **Admitted variants.** Every defensible series counts: for German industrial production, B-D, B-D_F or Destatis "Industrie"; for Italian inflation, HICP or NIC; for Swiss GDP, with or without the sport-events adjustment; calendar-adjusted, seasonally adjusted or original YoY where the release offers them.
- **Tolerances.** 0.15 pp for one-decimal rates; 0.3 pp for 3m/3m SAAR and annualised q/q; 0.6 for survey balances and integer indices.
- **Seasonal adjustment for inflation 3m SAAR** (Italy, euro area, and the energy-core question C05). The ECB's official SA series gets full marks. Otherwise the agent's own SA series is tested for residual seasonality on its full saved history (F-test on monthly dummies); a clear failure scores zero; inconclusive cases go to a 1.0 pp RMSE threshold against a reference (ECB SA, or X-13 for Italy). No saved series, or too short, is a fail. Energy may be adjusted or not. Code: `scoring/answer-keys/sa_gate.py`, `resid_seas.py`, `x13.py`.
- **Blind numeric questions.** The judge never sees the reference value. Each numeric question offers value ranges: the tolerance band of each admitted value, two decoy bands of the same width on each side, "other value", "not shown" and "cannot verify". A false-pass test with every reference moved by four tolerances gave 1.0–5.3 false points per delivery (of 40) with this design, against 4.7–9.8 when the reference was shown and the judge asked whether it matched (`scoring/visual-rubric-v1/results/false-pass-test/`).
- **Correct in code.** `code_check.py` searches the delivery's own saved CSV and Excel tables for the admitted value at the reference period. Every `fail` or `none` was reviewed by hand; mappings the automatic check missed are in `results/manual-overrides-*.json` with file, period and value. About 1,076 values matched with competing candidates were accepted on the automatic match; two random audits of 30 found 1 and then 0 errors.

## Complex tasks (C01–C05)

| Part | Points | Checked by |
|---|---:|---|
| **Result** | **50** | |
| Numbers | 30 | code: headline values in the agent's saved tables, or in the report text after a manual check, against the key |
| Shown | 10 | judge, blind value ranges with decoys, then the blind recheck; report text and images |
| Answer | 10 | judge, report text only: does the conclusion match the gold category? For C03, nowcast accuracy in code: full marks within 0.1 pp of the realised value, zero at 0.5 pp |
| **Method** | **50** | judge: identity and conventions, coverage of the required evidence, presentation, method (12 of 20 in the text block, with task-specific errors listed in the question) and limits, rescaled from 80 to 50 |

Gold answers and their evidence are in [tasks.md](tasks.md) and [`scoring/c-rubric-v1/gold/NOTES.md`](../scoring/c-rubric-v1/gold/NOTES.md). C04's gold (significant upward revisions) comes from Newey-West tests on Bundesbank real-time vintages (`gold/c04_significance.py`); C05's gold (small but positive pass-through) from a distributed-lag regression of core on energy inflation (`gold/c05_passthrough.py`).

C03 nowcasts that target Q4 2026 cannot be scored yet; their total is the other 90 points rescaled to 100, which flatters them by the average accuracy loss of the Q3 nowcasts (about 4 points). They can be rescored after Eurostat's Q4 flash (around 30 January 2027).

## Aggregation

- Model × method mean: plain mean over tasks, each task weighing the same. A run with no delivery counts as 0 (the "zero" treatment); the "delivered" treatment drops it instead.
- Uncertainty: bootstrap over tasks, resampled jointly for every model so comparisons stay paired; 90% percentile intervals for means and ranks (`results/model-method-summary.csv`).
- Time: wall-clock minutes of the final attempt, plus the first attempt when the final one is a timeout retry; for review methods, the low-effort run plus every review role. The frontier uses the median minutes per task.

## Score files

| File | Content |
|---|---|
| `results/deliveries.csv` | one row per delivery: total and parts, minutes, attempts |
| `scoring/visual-rubric-v1/results/score-100-A1-A2-A3-S01-S11-provisional-7-legible-recheck.csv` | simple tasks, low/high effort and examples |
| `scoring/visual-rubric-v1/results/score-100-A4-S01-S11-provisional-7-legible-recheck.csv` | simple tasks, review methods (after revision) |
| `scoring/c-rubric-v1/results/score-100-C-c-gold-provisional-2-legible-recheck.csv` | complex tasks, all methods |
| files without `-legible-recheck` | the same scores before the blind legibility recheck, kept for the record |
| `pass-*.json`, `numeric-*.json`, `verdict-*.json` | per-question judge answers (probabilities per repeat) |
| `numeric-combined-*.csv`, `code-check-*.json` | per-question numeric results: correct, legible, path through the check |

"Provisional" in a file name is the rubric version label; these are the final scores used in the results.
