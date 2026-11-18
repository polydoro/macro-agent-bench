# C-task rubric v1

Scores the C01–C05 deliveries (question-type tasks: a written answer backed by charts) with closed
questions answered by Jev (`jev-1.14.0`), weights and aggregation in code. Same design as
`visual-rubric-v1/` on PR #1; the full rubric and the author's decisions are in the review doc
(private review document).

Principle (the author, 2026-11-17): a one-shot eval of method, not of reaching one right answer. No
question rewards or penalises the direction of a conclusion.

## Blocks (100 points)

| Block | Points | Request | Scored by |
|---|---:|---|---|
| A identity and conventions (I1, I2) | 20 | images | probability-weighted |
| B coverage of required roles (C_*) | 20 | images | probability-weighted |
| C presentation (P1, P2) | 20 | images | probability-weighted |
| D numeric (N_*), blind value ranges with decoys | 20 | report text + images | the judge's own choice |
| E answer 2, support 0 (asked, not scored), method 12, limits 6 | 20 | report text | probability-weighted |

Each request is stored separately (`responses/<sha256 of what the model sees>/r<repeat>.json`), so
changing one block never invalidates the others. A cell with no report text gets NAO_ATENDE on E
without a call; a cell with no product (A2 C04 Sol) scores 0; verified absences are reported absent.

## Files

- `rubric.py` questions, options, weights (C01, C04). `aggregate.py` copied from PR #1.
- `judge.py` Jev adapter and report-text extraction (`.md`, `.txt`, `.html` under `entrega/`; PDF only if none).
- `references.py` blind numeric questions from `keys/` (the value is never sent to Jev).
- `keys/build_c04.py` → `keys/C04-key.csv`, `keys/C04-cells.csv`. `keys/build_c01.py` → `keys/C01-production.csv`, `keys/C01-orders-A3.csv`;
  `S01-key.csv`, `S02-key.csv`, `S02-extra-yoy.csv`, `jsonstat.py` copied from PR #1 `answer-keys/`.
- `summarize.py` → `results/summary-<version>.csv` (all full passes).
- `run_pass.py` (`--dry-run`, `--cells`, `--shift` for the false-pass test). `test_c_rubric.py` offline tests.

## C04 key

BBKRT `Q.DE.Y.A.AG1.CA010.A.I` from four agent-saved copies (A1 Opus x2, A2 Opus, A3 Sonnet); all
agree on shared vintages; 114 vintages, 2005-05-12 to 2026-10-30. Each cell sees only vintages before
its `submitted_at_utc` (A1: last vintage 2026-09-30; A2/A3: 2026-10-30). Mean revision of q/q and
YoY growth for 3 samples (2005–2019, 2005–latest without 2020–21, 2005–latest) and 9 horizon
definitions in 5 groups. Admitted: any sample and definition in the group; tolerance 0.03 pp
(0.12 annualised). Quarters before 2005-Q1 have no genuine first estimate in BBKRT and are excluded.

Known limit: at the 1-year horizon the pre-2005 trap (+0.024 pp) sits within tolerance of the key,
so only the latest-vintage horizon separates it.

## Pilot, 2026-11-17 (A1–A3, 25 deliveries, 3 repeats, 312 calls, 3.4M input tokens)

Results: `results/pass-A1-A2-A3-C04-c-rubric-v1-pilot-3.json`, summary `results/C04-pilot-3-summary.csv`.

- False-pass test (all keys moved +4 tolerances, 4 cells): pilot-1 let A1 Luna keep 10 of 20 because
  it reports Destatis's YoY revision statistics, read as q/q. Pilot-2 asks q/q and YoY separately:
  3 of 4 cells fell to 0; A2 Fable kept 20, because its YoY figures over 1995–2026 (a sample not in
  the key) happen to sit in the shifted band.
- Pilot-3 changes: E2 asks only about the report's own numbers (the text request has no images);
  D counts the best 1 of 10 numeric questions (A3 Kimi reports one sound horizon only).
- Repeats: L standard deviation 0.1–1.2 points, except A2 Haiku (11.9: its numeric answer flips).
- Hand check of 6 reports against E3 (method): ordering agrees in all 6. A1 and A3 Haiku (no vintages,
  a few anecdotes; A3 also labels Eurostat YoY as q/q) score low; A1 and A3 Luna (quote Destatis's
  official revision statistics, no own vintages) score PARCIAL; A1 Opus and A3 Kimi (BBKRT vintages;
  85 archived Destatis releases with zeros, CIs and sign test) score high.
- E2 (support) does not hold up: long, careful reports (Opus, Fable, Sonnet) get mostly PARCIAL, short
  ones (Luna) ATENDE. E1 and E4 sit near the ceiling for nearly every cell.

## Weights v1-4 (the author, 2026-11-17)

E2 (support) is still asked and stored but weighs 0; its 4 points moved to E3 (method), now 12.
C04 rescored with v1-4: `results/pass-A1-A2-A3-C04-c-rubric-v1-4.json`.

## C01 (German industry recovery), 2026-11-17

Key: production from Eurostat `sts_inpr_m` JSON-stat files saved by S01 and C01 agents, newest stamp
before each arm's runs; latest month 2026-08 in all arms. Totals admitted B-D, B-D_F, B_C and C
(manufacturing): YoY CA 0.36 / 2.26 / -0.36 / -0.36, YoY SCA 0.55 / 2.33 / -0.22 / -0.22, 3m SAAR
0.00 / 1.62 / -2.17 / -2.31. Orders (manufacturing, volume, total): A1/A2 from the S02 key (2026-08:
YoY CA 2.67, SA 2.99, NSA 3.46; 3m SAAR 5.4). A3 ran after the September orders release (2026-11-05
08:00 CET), so its month is 2026-09: YoY CA 3.30, SA 3.32, NSA 3.36, 3m SAAR 0.74 (BBDE1 copies from
two agents, GENESIS 42151-0004 from Kimi). Tolerances as PR #1: rates 0.15, 3m SAAR 0.3.

Rubric: 4 coverage roles (production level, production growth, orders, one breadth or demand
indicator; 24 months each). Numeric: production and orders YoY and 3m SAAR for the reference month,
best 2 of 4 count (10 each). The reference month is stated in the question; a delivery that stops
earlier does not show the value.

Checks before the pass (4 cells, 1 repeat): first try gave A1 Opus NAO_MOSTRADO on production values
that its text states ("YoY −0,4%", "3msaar −2,3%" for manufacturing, "ago/26"); fixed by naming the
month in both formats, decimal commas, "3msaar" as a synonym and saying manufacturing counts as a
total. False-pass test (+4 tolerances): every choice matches the value the delivery shows; two cells
kept one production YoY because their B-D value (+0.4) falls in the shifted band of another admitted
total (C or B_C, -0.36 + 0.6). That is a limit of shifting a set of several admitted totals, not a
judge bias.

Pass (A1–A3, 27 cells, 3 repeats, 243 calls): `results/pass-A1-A2-A3-C01-c-rubric-v1-4.json`.
L ranges 70–97; repeat sd 0.1–0.8. What separates cells is coverage: 11 cells have no orders series of
24 months (Haiku in all arms, A1 Sonnet/Astra/Luna/Kimi, A3 Sonnet/Luna/Sol; A1 Astra and A3 Sol show
only bars or three months), and 7 have no breadth indicator. D is at 20 for 26 of 27 cells (production
alone fills best 2 of 4; A1 Opus 10, since Jev does not read its 3m SAAR). E3 is ATENDE for 25 cells;
Haiku A1/A3 PARCIAL. Hand check: A3 Sonnet (no orders, says so in limits) got ATENDE although the
method question names orders; A1 Haiku with the same gap got PARCIAL. The E block barely separates C01
deliveries.

## C02 (euro-area household consumption), 2026-11-17

Key per cell (`keys/build_c02.py` → `keys/C02-key.csv`), cutoff = the cell's start
(`submitted_at_utc`), from Eurostat JSON-stat files saved by C02 agents, keyed by dataset and stamp.
Consumption 2026-Q2 for every cell (namq_10_gdp P31_S14 or P31_S14_S15, or namq_10_fcs P31_S14,
EA21 or EA20): q/q 0.28–0.42 (annualised 1.13–1.68), YoY 1.10–1.23. Retail volume (G47 or
G47_X_G473): 2026-08 except A3 Fable (ran 2026-11-07, after the 2026-11-06 release): 2026-09. Consumer
confidence 2026-10 (-17.9) for every cell; A1 ran before Eurostat carried October, but two A1 agents
quote the DG ECFIN flash, so the flash counts (the author, question 10). Saving rate 2026-Q2 (14.2).
No A1 agent saved namq_10_fcs; A1 uses the 2026-10-30 copy (flagged in the stamp column).

Rubric: 3 coverage roles (national-accounts consumption 8 quarters, retail 24 months, one of income,
saving, labour market or confidence); 6 numeric questions, best 3 count (6.67 each).

Checks (4 cells, 1 repeat): first try scored A2 Haiku's consumption q/q (1.1% annualised) outside the
key; it uses namq_10_fcs (domestic concept), now admitted. False-pass test (+4 tolerances): A1 Opus,
A3 Fable and A3 Luna fall to 0; A2 Haiku keeps 2 of 3 through the same multi-variant effect as C01
(its true values sit in shifted bands of other admitted variants).

Pass (27 cells, 3 repeats): `results/pass-A1-A2-A3-C02-c-rubric-v1-4.json`. 24 of 27 cells score
89–97. A1 and A3 Luna (65, 68: consumption only, no retail and no other indicator; E3 PARCIAL) and
A1 Sonnet (84.5: identity and presentation) are the only low ones. D is 20 for all but the two Luna
cells (13.3). C02 hardly separates the models.

## C03 (euro-area GDP nowcast), 2026-11-17

No accuracy score (the author, question 11). Key (`keys/build_c03.py` → `keys/C03-key.csv`,
`keys/C03-cells.csv`): last observed GDP per cell from saved namq_10_gdp copies. A1 (28 Oct) sees
2026-Q2 (q/q 0.60–0.64, annualised 2.6, YoY 1.2) and must nowcast Q3; A2 and A3 see the Q3 flash of
2026-10-30 (q/q 0.40–0.42, annualised 1.67, YoY 1.3) and must nowcast Q4.

Block D: last observed GDP (q/q or YoY, best 1 of 2, 10 points) plus a target-quarter question
(10 points, closed options written per arm: correct target separated from data / only another quarter /
target mislabelled or shown as data / no nowcast). The judge's choice counts, as for numeric questions.

Checks: false-pass (+4 tolerances) moved every last-observed answer to a decoy; target answers
unchanged, as they should be. First E3 try marked A1 Opus and A3 Grok PARCIAL although both say their
pseudo out-of-sample test uses revised data; method text now says that disclosure, or projecting a
missing month by AR, is not an error.

Pass (27 cells, 3 repeats): `results/pass-A1-A2-A3-C03-c-rubric-v1-4.json`. Every cell with a nowcast
picks the right target quarter (A1: Q3 as unreleased, A2/A3: Q4 with Q3 as observed). Scores 86–97
except A1 Luna (39: no report text, no nowcast in the images), A2 Fable (76: no report text) and A3
Luna (77: thin). Side column (hand-read from reports), A1 nowcast of 2026-Q3 against the flash +0.42:
`results/C03-A1-nowcast-error.csv`; all eight under-predicted, by 0.10 (Kimi) to 0.46 pp (Grok).

## C05 (energy and euro-area core inflation), 2026-11-17

Key (`keys/build_c05.py` → `keys/C05-key.csv`) reuses the S06 rows of PR #1's `S05-S06-key.csv`
(YoY from Eurostat RCH_A or I25; 3m SAAR on the ECB official SA index; energy SA equals NSA). The
October flash came out 2026-11-04 10:00 UTC: A1 and A2 (except Fable, which started 16:15 that day)
take September (energy YoY 18.9, core 2.5, energy 3m SAAR 45.8, core 2.81); A2 Fable and all A3
take October (20.8, 2.5, 38.6, 2.68). Simplification: the core 3m SAAR admits only the ECB SA value
(tolerance 0.3); the S05/S06 residual-seasonality gate on agents' own SA series is not run here.
Numeric: 4 questions, best 2 count.

Checks: false-pass (+4 tolerances) sends all four test cells to 0 on D. Method text adds "(5) a
conclusion on transmission from a window of a few months" after A3 Haiku (four months of YoY, no
transmission estimate) got E3 ATENDE; it still gets mostly ATENDE (p ≈ 0.63), so E3 stays lenient.

Pass (26 judged cells, A2 Grok verified absence, 3 repeats): `results/pass-A1-A2-A3-C05-c-rubric-v1-4.json`.
The transmission chart is what separates cells: 12 of 26 show none (B ≈ 13). Timeliness bites in D:
A1 Kimi (data only to December 2025) and A3 Sonnet and Haiku (September after the October flash) get
0. Scores: 55 (A3 Haiku) to 97; median 89.

### C05 seasonal-adjustment gate (the author's S05/S06 rule), 2026-11-17

`keys/build_c05_sa.py` -> `keys/C05-sa-gate.csv` (uses `extract_sa.py` and `resid_seas.py` copied read-only from PR #1's
`answer-keys/`). For the core 3m SAAR only (energy is exempt, SA or NSA accepted):

- official ECB SA (agent's saved core SA index within 0.02 pp m/m RMSE of ECB XEF000, last 60 months): full marks;
- otherwise residual-seasonality F-test on the agent's own saved series, full history: p < 0.01 fail, p >= 0.05 pass,
  in between goes to a 1.0 pp RMSE threshold on the 3m SAAR (24 months) against the ECB SA reference;
- fewer than 36 months, or no saved series: fail.

Pass admits the delivery's own 3m SAAR at the reference month as a variant of `N_core_3m`; fail fixes that question to
NAO_ATENDE (`run_pass.py`, override after the judge call). Result: 13 official ECB SA, 9 pass, 4 fail (A1 Sonnet no
saved series, A1 Luna residual seasonality p 0.00, A2 Haiku too short, A3 Haiku no series), 0 inconclusive, so the RMSE
threshold never applied. No cell's L changed: D keeps the best 2 of 4 numeric questions, and every failing cell either
already scored the core 3m SAAR as not shown or had two other numeric questions at full marks.

Flag: A3 Kimi's own SA core index sits near 65 against an NSA level near 103 and its own 3m SAAR at 2026-10 is -0.15
(ECB 2.68), yet the F-test passes (p 1.0). Under the literal rule its value is admitted; Jev placed its shown value in
the ECB band anyway, so the flag changes nothing here.

## Cells with no delivery

`summarize.py` also writes `results/model-means-<VERSION>.csv` with both treatments and the counts behind them.
Two kinds, from the receipts:

- `verified_absence` (Grok A2 C04 and C05): 1.5 s elapsed, 3 telemetry events, exit 1, no model usage. The CLI failed
  before the model did any work; an infrastructure failure, not a model outcome.
- `no_product` (Sol A2 C04): 273 s, 70 events, exit 1, 0 files delivered. The model ran and ended without a delivery;
  arguably a model outcome.

| model | delivered / cells | L, absent as 0 | L, absent excluded |
|---|---|---|---|
| Fable | 15/15 | 93.6 | 93.6 |
| Opus | 15/15 | 93.0 | 93.0 |
| Astra | 15/15 | 91.4 | 91.4 |
| Kimi | 15/15 | 90.7 | 90.7 |
| Sonnet | 15/15 | 89.1 | 89.1 |
| Sol | 14/15 | 85.0 | 91.1 |
| Grok | 13/15 | 80.7 | 93.1 |
| Haiku | 15/15 | 79.2 | 79.2 |
| Luna | 15/15 | 76.3 | 76.3 |

## A4 (revision arms), 2026-11-17

Mapping (`keys/build_a4_cells.py` -> `keys/A4-cells.csv`): every A4 C seed is the A1 final delivery (all 45 seed
trees byte-identical to A1 `work/entrega`). **Before** = the A1 score already in `results/`, no new calls. **After** =
the evaluation snapshot of each revision, two per seed: `A4_self_review` (same model reviews and fixes) and
`A4_external_review` (a reviewer writes notes, same model fixes); 90 revised deliveries. Failed revisions: Grok C05 both
arms (snapshot = seed unchanged) and Grok C04 external (failed partway); scored as left, flagged.

Data release: "seed's release or newer" (confirmed by the author 2026-11-17).
`references._a4` takes the seed's key and adds the key of any release out when the revision ran; the question then names
both months and asks for the latest one the delivery shows. C01: non-Anthropic revisions ran 6 Nov 01-02 UTC (September
orders out, production still August); Anthropic revisions from 7 Nov 18 UTC (Eurostat sts_inpr_m stamp 2026-11-07 has
September production for B-D, B_C and C; `build_c01.py` arms A4-early, A4-late).

### C01 A4 results (3 repeats; before = A1)

| model | before | self | external |
|---|---|---|---|
| Fable | 92.1 | 94.0 | 93.1 |
| Haiku | 82.7 | 87.8 | 87.9 |
| Opus | 85.1 | 96.0 | 85.8 |
| Sonnet | 90.2 | 91.1 | 89.3 |
| Astra | 87.7 | 87.7 | 87.8 |
| Luna | 80.0 | 83.5 | 79.4 |
| Sol | 91.7 | 91.9 | 92.5 |
| Grok | 89.8 | 91.6 | 92.3 |
| Kimi | 89.0 | 88.2 | 88.7 |

Mean change: self +2.6 (5 up by more than 1 point, none down), external +0.9 (3 up, none down). Opus self's +10.8 is
block D (production 3m SAAR now shown); Haiku's +5 is conventions (A) and coverage (B). Every numeric band Jev chose was
an admitted one; no decoy picks.

### C02–C05 A4 and summary

Newer-release keys: C02 September retail (Eurostat stamp 2026-11-06 11:00 CET) for revisions from 7 Nov (build_c02
keys each A4 revision at its own start and also reads its saved files; A1–A3 rows unchanged, checked). C03: Q3 flash
out for every revision, so the last-observed question admits Q2 or Q3 and the target question admits either the seed's
target (Q3 as estimate) or the updated one (Q4 with Q3 observed). C04: last BBKRT vintage 2026-10-30 for every
revision. C05: October flash for every revision; the SA gate runs on the revised delivery's own series
(`C05-sa-gate.csv`, A4 rows; own 3m SAAR admitted at September and October).

`summarize.py` writes `results/a4-before-after-c-rubric-v1-4.csv` (task, model, before_A1, self, external, deltas,
revision state). Mean L, before / self / external: C01 87.6 / 90.2 / 88.5; C02 90.1 / 90.3 / 90.7; C03 85.2 / 89.4 /
86.9; C04 81.8 / 85.7 / 82.3; C05 86.5 / 87.1 / 90.5; all 86.3 / 88.5 / 87.8.

Notes from the review:
- Grok C05 revisions failed in both arms and left the seed unchanged: after = before (95.4). Grok C04 external failed
  partway; scored as left (89.6, same as before).
- Wrong-band picks: C04 `N_qoq_latest` 0.16–0.23 (same gap between admitted bands as in A1–A3, same models); C05
  `N_energy_3m` OUTRO_VALOR for Opus, Astra, Kimi, Haiku (they show about 18.5 against the key's 45.8 point-to-point
  3m SAAR; same picks in A1). Likely a definition difference (3m average over previous 3m average vs point-to-point),
  inherited from PR #1's S06 key; only best 2 of 4 count, so D is rarely affected.
- Race fixed by rerun: identical request bodies from two cells (Grok C05 no-op snapshots) collided on the response
  file; the second run used the cache.

C05 3m SAAR definition: point-to-point only. A short-lived change also admitted the 3-month average over the previous
3-month average; it was reverted because the task's common context defines inflation 3msaar as "a variação do índice
SA em três meses anualizada" (average over average is the convention for monthly activity, as in C01). Agents printing
energy 18.5 used the activity convention for inflation, which the prompt rules out. Results are the earlier pass
(all responses cached; no score had changed either way).
