# C-task gold standard (result block)

Design: Claude Doc (private review document) the author's decisions 2026-11-17: verdict about 10 of
100 points, result/method 50/50, Jev for legibility (homogeneity), C04 "no clear bias" admitted only if not
significant, C05 distributed-lag reference estimate, same gold for A4 (after counts). No Jev call without his go.

Files (no Jev calls):
- `c04_significance.py` -> `C04-significance.csv`: mean revisions with Newey-West SE. Last vintage 2026-10-30: q/q
  positive and significant at one year or more in every sample (t 1.9-2.9); next release and 92 days not
  significant (t 0.2-1.5). Gold: SIM (upward), PEQUENA (q/q mean 0.04-0.13 pp). "No clear bias" is not admitted.
- `c05_passthrough.py` -> `C05-passthrough.csv`: core m/m on energy m/m lags 0-12 plus 2 core lags, 2005-2026, ECB SA
  indices the agents saved. Long-run pass-through 0.08 (95% CI 0.03-0.13); the 2026 energy upturn (energy YoY -4.0 in
  January to 18.9/20.8) adds about 0.37/0.45 pp to core YoY by September/October; core went 2.19 -> 2.51/2.55.
  Gold: small but positive indirect effect (EFEITO_PEQUENO_OU_LIMITADO). This revises the doc's first label
  ("limited so far"): the effect is already visible, of a few tenths.
- `code_check.py` (copied from PR #1, C roles added) and `run_code_check.py` -> `results/code-check-<task>.json`:
  numbers in the agents' own saved tables vs the key (A4: seed's release or newer).
- `verdict.py`: closed questions on the delivery's conclusion, text only, separate request (`c-gold-verdict-v1`);
  gold categories in `gold()`. C03 has no verdict request: its result is the nowcast error (code).

## Code check audit (first pass, 2026-11-17)

Status counts: C01 ambiguous 129 / auto 23 / none 20 / fail 8; C02 131 / 82 / 56 / 1; C03 21 / 46 / 20 / 3; C05 67 / 67 / 11 / 23 (+8 sa_rule).
Random sample of 20 ambiguous matches (seed 7): 16 correct, 4 wrong. Wrong ones: a sub-sector row matched the total
(C01 Fable A4 N_prod_3m), a nowcast scenario row matched last observed GDP (C03 Haiku A4), a food sub-index matched
G47 (C02 Kimi A4 N_ret_3m), and an out-of-period quarterly row matched (C01 Sonnet A2, row 1995-Q3).
About 20% error on ambiguous matches, so they need row/period filters and a manual pass before they count. Not scored yet.

## Verdict pass (Jev, c-gold-verdict-v1, 2026-11-17)

the author approved the pilot and full pass on 2026-11-17 20:24 UTC. 531 calls (12 pilot + 519), 3 repeats per delivery.
Results: `results/verdict-C0{1,2,4,5}-c-gold-verdict-v1.json`, logs `results/verdict-C0?.log`.

| Task | Deliveries | Mean of 10 | Cells with unstable repeats |
|---|---|---|---|
| C01 | 45 | 9.78 | 0 (only A3 Sonnet says "no recovery") |
| C02 | 45 | 7.26 | 2 |
| C04 | 43 | 6.98 | 2 |
| C05 | 44 | 10.00 | 0 |

C01 and C05 do not separate models. C02: 12 deliveries that saw only August retail say "weak or losing momentum"
against a gold of "moderate"; their data are the same as the cells that say "moderate", so this is an interpretive
split. C04: 36 of 129 answers say "no clear bias" (gold: yes, small); 15 say "large" or do not quantify.

## Code check filters (second pass, 2026-11-17)

After the first audit, `code_check.py` skips rows that cannot hold the headline number: C01 export/domestic orders, sub-sectors
(NACE codes in brackets, "equip"), ex-large-order series; C02 retail sub-aggregates (food, fuel, G47x, online);
C03 nowcast, forecast, scenario and shock rows (and files named for scenarios); and, for monthly references, rows that
state only a quarter. `\bip\b` replaces `ip\b` (it matched "Equip.").
New counts: C01 ambiguous 118 / auto 34 / none 23 / fail 5; C02 80 / 127 / 62 / 1; C03 17 / 48 / 22 / 3; C05 unchanged.
Hits lost against the first pass: 8, all checked: 6 were out-of-period Grok C02 rows (2016–2018, false hits), 2 are
Luna A4 self C03 values on a nowcast row (now 'none', left for the manual pass).
Second audit: 25 random accepted matches (auto + ambiguous, seed 11), 25 correct.

## 100-point file (provisional, 2026-11-17)

`gold/score100.py` → `results/score-100-C-c-gold-provisional-1.csv`: result 50 (numbers 30 from the code check,
shown 10 = block D / 2, answer 10 = verdict or C03 nowcast accuracy) + method 50 (A, B, C, E rescaled from 80).
C03 accuracy: 10 within 0.1 pp, linear to 0 at 0.5 pp; the naive-relative variant is a separate column.
Empty totals: C04 (numbers checked by hand later) and C03 A2–A4 (Q4 flash, about 2027-01-30).
Provisional because 'none' and 'fail' in the code check count as not matched until the manual pass.
Means, new vs old L: C01 88.3 vs 89.0, C02 84.8 vs 91.2, C05 83.7 vs 86.0; the spread across deliveries widens on every task.

## Manual pass on numbers (2026-11-17)

`gold/report_search.py` looks for the reference value in the report text for each 'none' question (no candidate in
the saved tables). 56 hits were checked by hand: 29 accepted (in `results/manual-overrides-C.json`), the rest were
other numbers near the keyword (GDP for consumption, Irish GDP, chart file names, per-capita consumption).
The 9 'fail' cases on C01–C03 and the non-energy C05 fails were read: all are wrong concepts or wrong periods
(order backlog for orders, unannualised 3m/3m, annualised q/q labelled YoY, older months, own SA core off the gate).
Values on charts only are not counted here; they score in "shown" (block D).

## C04 numbers (2026-11-17)

`gold/c04_check.py` → `results/code-check-C04.json`: mean revisions read from each delivery's summary tables (mean column,
row label naming a horizon; Destatis quality-report rows "revisão trimestral/anual" are YoY). A question is correct if
the value is within tolerance of any admitted BBKRT variant (samples 2005–2019, 2005–latest, ex 2020–21; q/q also annualised).
Report-text candidates for the remaining 'none' questions were read by hand: 30 accepted (Destatis quality-report YoY
means in Luna's reports, Sonnet A2's report tables, Opus A2, Grok A3/A4 self, Kimi A3), the rest were single episodes,
mean absolute revisions (0.55) or YoY values offered as q/q. Overrides in `results/manual-overrides-C.json`.
C04 100-point mean 66.4 (old L 80.6): numbers 11.5 of 30, because most deliveries give only some of the 10 horizon × measure means.

## Legibility recheck, "value shown" (2026-11-17, no Jev)

Same method as the S tasks (PR #4): blind Sonnet readers (no model names; 8 readers, 213 deliveries) re-read every
N_ question where Jev gave legibility credit (745) and every uncredited one where the code check found the value (63).
The C rubric's block D also counts a value written in the report, so each question carried the report lines that hold a
number within an admitted tolerance (table rows with their header). Shown = printed as digits (chart label, table,
annotation or report text) and within an admitted variant's tolerance. Steps: `gold/legible_prep.py` (folders, key),
readers (`results/legible-recheck-C/reader-prompt.md`), `gold/legible_collect.py` (reads.json, reads-detail.json),
`python gold/score100.py results/legible-recheck-C/reads.json`.
Result: of 745 credited, 703 shown, 42 not; 7 of the 42 were adjudicated back to shown (`adjudications.json`: a printed
-0.4 for manufacturing within the B_C tolerance, where the reader judged identity rather than legibility; "+0.32/+0.26
after the 4th annual revision" read as the latest horizon, as other readers did). Of 63 uncredited, 25 shown (added).
Readers sometimes skipped images when the text already settled a question; every removal cites unlabelled charts.
Because block D takes only the best 1–3 values, only 5 deliveries change (C01 Opus A1 and A4 external +5.0;
C02 Haiku A1 -3.3, C02 Luna A3 -3.3, C04 Haiku A2 -3.3). File: `results/score-100-C-c-gold-provisional-1-legible-recheck.csv`;
the earlier file is unchanged.

## C03 scored on the Q3 flash (c-gold-provisional-2, 2026-11-17)

the author asked to score C03 now against the latest Q3 estimate instead of waiting for the Q4 flash.
`results/C03-nowcast-q3.csv` records, per delivery, the quarter nowcast and the Q3 value read from the report:
A1 (all 9 nowcast Q3; Luna gave none), A2 and A3 (all 18 nowcast Q4 only), A4 external review (8 kept the 28 Oct
cut and a Q3 nowcast; Luna withdrew it), A4 self review (Astra and Sol Q3; Luna none; six moved to Q4).
Realised value: Eurostat Q3 flash 0.42 q/q (the files' rounding of 0.415); the author confirmed on 2026-11-18 that Eurostat's second estimate left Q3 unrevised at +0.4% q/q, so no rescore.
Accuracy 10 points as before (full within 0.1 pp, zero at 0.5 pp; no Q3 nowcast scores 0). Q4-only deliveries
keep `answer_10 = pending Q4 flash` and total = (method + numbers + shown) x 100/90, so they are not penalised
for a value that does not exist yet; this flatters them relative to Q3 deliveries by the average accuracy loss.
Provisional-1 files are kept. No Jev calls.
