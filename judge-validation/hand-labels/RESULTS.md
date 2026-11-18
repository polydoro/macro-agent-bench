# Jev vs the author's hand labels (2026-11-17)

Sample: 15 deliveries (S01 A3, S02 A1, S09 A3 x top 5 models), 265 questions, the author flagged problems only (unflagged = Atende). Jev = stored majority of 3 repeats; Partial counts as a problem. Rows: compare-rows.csv. Labels: labels-20261117/.

| Kind | n | agree |
|---|---:|---:|
| identity (I1) | 15 | 1.00 |
| conventions (I2) | 15 | 1.00 |
| coverage | 110 | 0.97 |
| legibility (P1) | 15 | 0.93 |
| numeric "printed" | 95 | 0.84 |
| identification (P2) | 15 | 0.53 |

Clusters:
1. P2: Jev says Parcial in 7 of 15 where the author says Atende, across all 5 models. Making P2 lenient (Parcial -> Atende) on all 280 deliveries adds 1.2-1.4 pts to each top model (Luna +2.7); order among top models unchanged except Astra 92.3 vs Fable 92.0 (was tied 90.9).
2. Numeric legibility: Jev reads values off unlabelled bars / line ends (D10 Fable S02 bar chart "Taxas por abertura", D12 Sonnet S09 "Último mês" bars, D14 Opus, D09, D06) against the printed-only rule. False legible credit in sample: Sonnet ~9 pts over 3 deliveries, Fable 5, Opus 2.5, Astra 0.
   D02 (Sol S01): the author flagged total YoY/3m as not printed, but the bar chart prints +2.30% / +1.62%. the author approved correcting both labels to Atende on 2026-11-18 (originals kept in labels/D02.json "corrections"); tables here use the corrected labels.
3. Coverage: 3 disagreements; D08 Sonnet S02 'externo' is the known euro-area subset (Jev right); D10 domestic/foreign YoY panels exist (Jev looks right).


## Chance-corrected agreement (Cohen's kappa), 2026-11-18

Script: `kappa.py` (run from `visual-rubric-v1/`: `PYTHONPATH=. python hand-labels/kappa.py`). No new judge calls.
Same 15 deliveries and 265 questions; D02 total YoY / 3m labels corrected as approved by the author on 2026-11-18.
Binary labels: Jev ok = majority of 3 repeats Atende (Parcial = problem); Sonnet ok = value printed and inside an
admitted band. 95% CI = percentile bootstrap over the 15 deliveries (5,000 draws). Error columns are counts:
"credits what the author rejected" = judge ok / the author not ok; "rejects what the author credited" = the reverse.
⚠ = one rater puts more than 90% of labels in one class; kappa is undefined or degenerate there, read raw agreement and the error counts instead.

**Jev vs the author**

| Item kind | n | Raw agreement | Cohen's kappa | 95% CI | Judge credits what the author rejected | Judge rejects what the author credited | the author ok rate | Judge ok rate |
|---|---:|---:|---:|---|---:|---:|---:|---:|
| identity (I1) ⚠ | 15 | 1.00 | undef. | n/a | 0/0 | 0/15 | 1.00 | 1.00 |
| conventions (I2) ⚠ | 15 | 1.00 | undef. | n/a | 0/0 | 0/15 | 1.00 | 1.00 |
| coverage | 110 | 0.97 | 0.92 | [0.74, 1.00] | 2/25 | 1/85 | 0.77 | 0.78 |
| legibility (P1) ⚠ | 15 | 0.93 | 0 (by construction: one rater constant) | n/a | 1/1 | 0/14 | 0.93 | 1.00 |
| identification (P2) ⚠ | 15 | 0.53 | 0 (by construction: one rater constant) | n/a | 0/0 | 7/15 | 1.00 | 0.53 |
| numeric "printed" | 95 | 0.84 | 0.60 | [0.00, 0.94] | 15/78 | 0/17 | 0.18 | 0.34 |
| **all questions** | 265 | 0.90 | 0.79 | [0.59, 0.93] | 18/104 | 8/161 | 0.61 | 0.65 |
| all excl. numeric | 170 | 0.94 | 0.77 | [0.49, 0.91] | 3/26 | 8/144 | 0.85 | 0.82 |

**Blind Sonnet readers vs the author (numeric questions only; Sonnet read nothing else)**

| Item kind | n | Raw agreement | Cohen's kappa | 95% CI | Judge credits what the author rejected | Judge rejects what the author credited | the author ok rate | Judge ok rate |
|---|---:|---:|---:|---|---:|---:|---:|---:|
| numeric "printed" | 95 | 1.00 | 1.00 | [1.00, 1.00] | 0/78 | 0/17 | 0.18 | 0.18 |
| numeric, Jev on the same rows | 95 | 0.84 | 0.60 | [0.00, 0.94] | 15/78 | 0/17 | 0.18 | 0.34 |

**Sensitivity: the two D02 labels as originally entered**

| Item kind | n | Raw agreement | Cohen's kappa | 95% CI | Judge credits what the author rejected | Judge rejects what the author credited | the author ok rate | Judge ok rate |
|---|---:|---:|---:|---|---:|---:|---:|---:|
| Jev, numeric "printed" | 95 | 0.82 | 0.54 | [0.00, 0.89] | 17/80 | 0/15 | 0.16 | 0.34 |
| Jev, all questions | 265 | 0.89 | 0.78 | [0.58, 0.92] | 20/106 | 8/159 | 0.60 | 0.65 |
| Sonnet, numeric "printed" | 95 | 0.98 | 0.92 | [0.00, 1.00] | 2/80 | 0/15 | 0.16 | 0.18 |

Evidence:
- Coverage: kappa 0.92 [0.74, 1.00] on 110 questions.
- Numeric "printed": kappa 0.60. Every disagreement is Jev crediting a value the author says is not printed (15 of 78).
- P2: the author said Atende on all 15 deliveries; Jev said Parcial on 7.
- The numeric CIs reach 0 because only 3 deliveries have any printed value, so resampling deliveries often drops them all.
- Sonnet matches the author on all 95 numeric questions.

Interpretation: on these 15 deliveries, Jev's structural judgements (identity, coverage) agree with a human almost perfectly. Its numeric legibility errs one way, giving credit too easily, which the Sonnet recheck removes. The P2 gap is Jev being stricter than the author, not noise. With 15 deliveries the intervals are wide, so these results are indicative.
