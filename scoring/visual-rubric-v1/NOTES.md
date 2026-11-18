# Visual rubric v1 (provisional pilot)

Scores the **final images** of one delivery with closed questions answered by Jev
(TypeSafe System One, `jev-1.14.0`). The model only picks an option per question.
Weights and aggregation are fixed code in `aggregate.py`.

This is a separate product score. It does not read or change the code-based scores in
`deterministic-scoring-full-v1/`, and it does not certify provenance, seasonal
adjustment or method.

## Files

- `rubric.py`: prompt, options, questions and weights for S01–S03.
- `judge.py`: Jev adapter. Each raw response is stored under the SHA-256 of what the
  model sees, plus a repeat index. A stored response is never fetched again.
- `aggregate.py`: pure function from answers to `L` (supported points) and `U`
  (`L` plus undetermined mass).
- `run_pilot.py`: runs a folder of packets and writes `results/`.
- `test_visual_rubric.py`: offline tests (`python -m pytest`).

## Points

| Block | Points | Needs a reference sheet |
|---|---:|---|
| Identity and conventions (I1, I2) | 20 | no |
| Numeric values at the latest period | 40 | yes |
| Coverage of trajectories | 20 | no |
| Presentation (P1, P2) | 20 | no |

Without a reference sheet the numeric questions are not sent. They are reported as
`pending_points`, never as a candidate failure, and nothing is renormalised.

## Provisional defaults (not yet decided by the author)

1. A value the delivery does not show scores zero (`NAO_MOSTRADO`); only a value that
   is shown but unreadable is undetermined.
2. No timeliness test: coverage is judged up to the latest period the delivery shows.
3. Breakdowns: best K of an admissible list (S01 K=4 of 5, S02 K=2 of 2, S03 K=2 of 8).
4. YoY is the calendar-adjusted rate; S01 total is the delivery's headline aggregate.
5. Coverage window is "at least 24 months" until the original common context is recovered.

Numeric questions currently hand the reference value to the model. Before the numeric
block is used, measure false passes with deliberately wrong references.

## Pilot, 2026-11-16 (A2, S01 and S02, 18 packets, 3 repeats, `jev-1.14.0`)

Results: `results/pilot-A2-S0*-visual-rubric-v1-provisional-3.json`. Raw responses:
`responses/`. Only the 60 points without a reference sheet were asked.

- Repeats differ: the standard deviation of L across 3 calls was 0.07–1.17 points out
  of 60. Identical payloads do not return identical probabilities.
- Version -1 defined YoY as calendar-adjusted, so a YoY trajectory computed on the SA
  series was marked missing (Sonnet S02). Version -2 accepts any adjustment variant
  for coverage.
- Version -2 still missed Sonnet's total YoY, labelled "a/a". Version -3 lists the
  usual labels (a/a, interanual, 12m, y/y); Sonnet S02 went from 43.9 to 52.9 and no
  other packet moved by more than about 1.5.
- Spot checks against the images agreed with the low calls for Haiku, Fable, Luna,
  Kimi and Grok S02.
- Known weak spot: foreign-orders YoY drawn in small multiples (Opus S02 as bars,
  Sonnet S02) gets only 0.46–0.57, although the trajectory is there.
- Not yet checked by hand: Haiku S01 I2 (0.40) and Astra S02 P2 (0.41).

## Running

```
python run_pilot.py --packets ../qa-preview/A2-S01 --task S01 --dry-run
python run_pilot.py --packets ../qa-preview/A2-S01 --task S01 --repeats 3
```

The call needs network access to `api.typesafe.ai` and either `JEV_API_KEY` in the
environment or a network secret that adds the `Authorization: Bearer …` header for that
host. Images outside TypeSafe's size limits are downscaled with a fixed filter; both the
original and the sent hashes are recorded.

## Numeric 40 points (2026-11-17)

`run_numeric.py` sends one extra request per delivery that holds only the numeric
questions. The 60-point requests do not change, so their stored responses stay valid.
References come from `references.py`, which reads `../answer-keys/*-key.csv`.

**The reference is never shown to the model.** Each numeric question is a blind
reading question. The options are value ranges: the tolerance band of each admitted
value, two decoy ranges of the same width on each side, a catch-all for other values,
`NAO_MOSTRADO` and `NAO_VERIFICAVEL`. A choice inside an admitted band maps to
`ATENDE` and any other range maps to `NAO_ATENDE` (`references.to_options`).

- **Period.** The question names the latest period available on the arm's run date. A
  delivery that stops earlier does not show the value and scores zero (the author, 2026-11-17).
- **Admitted variants.** Each question lists the admitted series by name, never by value.
  Examples: B-D, B-D_F and B_C for the S01 total; NIC or HICP for S05; with or without
  the sport adjustment for S08.
- **Tolerances.** 0.15 pp for one-decimal rates and pp changes. 0.3 pp for 3m/3m SAAR,
  3m SAAR and annualised q/q. 0.6 for survey balances and indices published as integers.
- **S05/S06 3m SAAR.** The SA criterion (`../answer-keys/sa_gate.py`) settles these in code.
  - A non-energy series that failed the criterion gets `NAO_ATENDE` with no call.
  - A series that passed also admits the delivery's own latest value.
  - For energy, both SA and unadjusted values are admitted.
- **Shown.** A value counts as shown only if it is printed, in a table or in a label. This
  is the rubric's original definition. Reading a line's end point off the axis does not count.

**False-pass test** (`results/false-pass-test/`). Four deliveries (A2 S01 Fable, A3 S06
Opus, A1 S08 Astra, A2 S11 Sonnet), one call each, run with correct references and
with every admitted value moved by +4 tolerances.

| Design | Correct references | Wrong references (false-pass points) |
|---|---|---|
| Reference shown, "does it match?" | 35.6 / 31.5 / 8.3 / 5.9 | 7.6 / 9.8 / 6.3 / 4.7 |
| Blind ranges (adopted) | 32.9 / 26.8 / 11.1 / 3.0 | 1.4 / 2.3 / 5.3 / 1.0 |

The S08 leak came from reading unlabelled line ends. The stricter definition of "shown"
above addresses it.

**Crop test.** Adding 2×2 zoomed tiles of every image cost 2.7–4.7 times the input
tokens. It moved S06 Opus from 26.8 to 31.2 and did not change S11 Sonnet. The remaining
misses are overlapping end labels, not resolution. Tiles are not used.

**Scoring rule for the numeric block: the judge's own choice.** Each repeat scores the
option the judge picked (`N_choice`), averaged over 3 repeats. The probability-weighted
score (`N_prob`, the 60-point convention) is also recorded. It is not used for this block,
because blind range questions spread 10–25% of the probability over the admitted bands
even when nothing is printed. In S01, deliveries that print no value got 4–8 of 40 under
`N_prob` and 0 under `N_choice`.

## Numeric 40 points split: correct (code) + legible (Jev)

the author's decision, 2026-11-17: the 40 numeric points are split into a part for the value being correct,
checked in code, and a part for it being readable on the chart, checked by Jev. Default weight 30 + 10
(`W_CODE = 0.75` in `combine_numeric.py`; weights 30/10 confirmed by the author 2026-11-17); both parts are stored separately, so changing the weight needs no API call.

Per question: `value = 0.75 * correct + 0.25 * legible`; best-K groups pick on the combined value.

- **correct** (`code_check.py`, `run_code_check.py`): looks in the delivery's own saved tables (csv/xlsx in
  `dados/` and `entrega/`, raw downloads excluded) for the admitted value at the reference period.
  Labels come from the column header, the row text and the file name; per-task regexes pick the role
  and the transform. Status per question: `auto` (one clean match), `ambiguous` (a match plus
  conflicting candidates; accepted), `fail` (candidates, none admitted), `none` (no candidate table).
- **Hybrid path**: every `fail` and `none` is reviewed by hand (`review.py` prints the latest-period
  rows). Where the saved table shows an admitted value the automatic check missed, the mapping goes in
  `results/manual-overrides-<task>.json` with file, period and value; `combine_numeric.py` applies it
  and marks the question `manual`.
- **Ambiguous matches** (1,076 values in A1–A3) are accepted on the automatic match, without a full
  hand mapping (the author, 2026-11-17: skip it). Audit by strict mapping of random samples of 30: first
  sample 1 wrong (about 3%), which led to the label and period fixes; second sample after the fixes,
  0 wrong. Values the fixes would have dropped wrongly were kept as manual mappings.
- **legible**: share of the Jev repeats of the numeric pass whose chosen range contains an admitted
  value of the current key (`band_ok`; a later key correction is applied without a new call). Shown
  means printed on the chart, in a table or a label. Caveat: a delivery whose chart prints a value that
  was admitted only after the Jev pass (e.g. S02 NSA YoY) got OUTRO_VALOR then and is not recovered,
  so its legible part can be undercounted (S02: 4 of 312 answers).
- S05/S06 3m SAAR questions failed by the SA gate score 0 on both parts.

Output: `results/numeric-combined-<task>.csv` (N_total, N_correct, N_legible, non-auto paths).

Key additions made during the review, consistent with the rubric:
- S01: energy also admitted as Bundesbank MIG energy (A2P500000, calendar- and seasonally adjusted);
  consumer goods counted when the delivery shows durables and non-durables (MIG_DCOG, MIG_NDCOG) instead.
- S02: components also admit calendar-adjusted and original-series YoY; the total admits original-series
  YoY 3.46 (`answer-keys/S02-extra-yoy.csv`, Destatis GENESIS 42151-0004).

### Hybrid check, S03–S11 notes (2026-11-17)

- Label fixes found in the manual review, applied to every task and re-checked against the earlier
  tasks (no earlier result changed): Portuguese retail-mode names (S03); misses capped at 50 per question
  but hits never dropped (a long BDM table had crowded out the INSEE values, S04); underscore codes
  (`TOT_X_NRG_FOOD`, `IGD_NNRG`, `P3_S13`); accented `famílias`, `Inv.`, `t_t`/`var_trim` for q/q,
  `Transformadora` (S08); a leading NACE code cell such as `47.9` labels its row (S09).
- Manual overrides (each with file, period and value): S02 4, S03 4, S05 3, S08 1, S11 14.
  S05's three admit ISTAT NIC component aggregates (NIC "altri beni" 1.0 for non-energy goods,
  NIC "beni alimentari" 2.7 for food in October) by analogy with the NIC headline, core and services
  already in the key; flagged for the author.
- Kept as fails: deliveries whose latest period is older than the run-date release (S06 A1 Fable and
  Sonnet show December 2025; S05 A1 Luna and Sonnet likewise), narrower or different aggregates (S09
  NACE 47.91 for 47.9; S11 large firms only; S03 activity classes for product groups), and two 3m SAAR
  values just outside the band whose saved SA series was not the one the SA gate tested (S05 A1 Kimi
  6.22 vs 5.7/5.82; S06 A2 Sonnet non-energy goods 1.95 vs 2.28).
- `paths.py <tasks>` prints how each delivery went through the check.

## A4 revisions (2026-11-17)

Same rubric (60 visual + 30 correct + 10 legible) on the A4 self-review (A4s) and external-review (A4e) arms;
the after-revision score is the one that counts, the before score is only a check.

- Cells (`a4_cells.py`): 9 models x 11 tasks x 2 arms = 198; a completed timeout-retry replaces a timed-out
  primary. 194 scored, 4 verified absences (S05 Grok A4e, S10 Kimi A4e and A4s, S11 Haiku A4e). C tasks ignored.
- Key (`references.py`, `A4_SOURCES`, `A4_NEWER`), decided by the author 2026-11-17 ("seed's release or newer"): a value counts if it matches the
  seed's release (A1 key), the A3 release, or a release published after A3 and before the A4 runs. The only
  such release is Destatis orders for September (press release 385, 2026-11-05), added as arm A4 of
  `answer-keys/S02-key.csv` by `answer-keys/build_s02_a4.py` (levels from Fable A4s's saved conversion; the raw
  download was not kept). The S02 numeric Jev pass was rerun with it (`numeric-A4-S02-*.json`).
  `run_code_check.py <task> A4` checks each release at its own period and keeps the best.
- SA gate for S05/S06: `answer-keys/a4_sa_gate.py` -> `S05-S06-sa-gate-A4.csv`, same rule as A1-A3.
- Manual mappings: `results/manual-overrides-A4-<task>.json` (8). Every other A4 residual repeats a
  not-correct A1 finding already reviewed (stale data, narrower aggregates, missing components).
- Scores: `results/score-100-A4-S01-S11-provisional-7.csv` (`build_score100.py A4`).
- Before/after: `results/a4-before-after-provisional-7.csv` (`build_a4_compare.py`). 94 of 99 seeds are the
  scored A1 delivery and keep its score. Five differ: S10 Fable and Grok seeds were scored here
  (`run_pass.py`/`run_numeric.py --phases A4seed`, `run_code_check.py S10 A4seed`, `combine_numeric.py --a4seed`);
  S02 Kimi, S05 Grok and S10 Kimi seeds have no charts (the A1 primary never delivered) and score 0.

## Judge check against hand labels, and the legibility recheck (2026-11-17)

**Hand labels** (`hand-labels/`): the author labelled 15 deliveries blind (S01 A3, S02 A1, S09 A3; the top 5 models;
265 questions; flag problems only, unflagged = Atende). Agreement with Jev: I1/I2 100%, coverage 97%, P1 93%,
numeric "printed" 82%, P2 53%. P2: Jev stricter for every model (lenient P2 adds 1.2-1.4 to each top model, order
unchanged). Numeric legibility: Jev credits values read off unlabelled bars and line ends, against the printed-only rule.

**Legibility recheck** (`legible_recheck.py`, `results/legible-recheck/`): blind Sonnet readers (prompt in
`reader-prompt.md`; calibrated on the 15 hand-labelled deliveries, 95/95 correct) re-read (a) all 975 questions where
Jev gave legibility credit: 733 printed and admitted, 242 not; (b) all 860 questions where Jev gave none but the code
check found the value in saved tables: 85 printed and admitted. Legible = 1 only for a printed admitted value.
Result: `results/score-100-A1-A2-A3-S01-S11-provisional-7-legible-recheck.csv`. The published score files are untouched.
Means (before -> after): Astra 90.9 -> 90.5, Fable 90.9 -> 90.4, Sol 89.5 -> 88.6, Opus 89.4 -> 88.3,
Grok 87.6 -> 86.4, Sonnet 86.5 -> 84.4, Kimi 82.4 -> 80.4, Luna 76.5 -> 76.0, Haiku 71.6 -> 70.1.

**A4 recheck** (same readers and rule): the A4 revisions (A4s, A4e) and the five A4 seeds that differ from A1.
Of 473 Jev-credited questions, 232 printed and admitted, 240 not, 1 unclear; of 804 uncredited with the value in saved
tables, 56 printed and admitted. A4 after-revision means fall 0.5-2.7 (e.g. Astra A4e 89.6 -> 88.5, Fable A4e 90.0 -> 88.2,
Sonnet A4e 88.7 -> 86.0).

**These corrected files replace the published scores** (the author, 2026-11-17); the originals stay for the record:
- `results/score-100-A1-A2-A3-S01-S11-provisional-7-legible-recheck.csv` (S, A1-A3)
- `results/score-100-A4-S01-S11-provisional-7-legible-recheck.csv` (S, A4 after revision)
- `results/a4-before-after-provisional-7-legible-recheck.csv` (A4 before/after check)
Visual 60 and the pass files are unchanged. Rebuild all three with `python legible_recheck.py`.
