# Judge validation

## Why this judge

The goal was to remove judge variance and make the score as deterministic as possible. The closed questions go to Jev (TypeSafe, model `jev-1.14.0`), a decision model that can only pick one of the options defined in the rubric and returns a probability per option; everything else is code. A second reason: Jev is not one of the nine models tested and does not come from any of their labs. There is no evidence here that Jev is more accurate than a chat-model judge; that was not tested.

## 1. Repeat variance (identical requests)

Every judged delivery was sent three times, word for word. 4,479 question triples, 13,437 answers ([`judge-validation/repeat-variance/`](../judge-validation/repeat-variance/)).

- The chosen option changed in 2.1% of questions (coverage 0.7%, identity 1.5%, presentation 4.1%, numeric 4.6%).
- Flips are confined to close calls: 44% when the top-two probability margin is under 0.1, 0% above 0.6.
- On the 60 judge points of the simple tasks, the pooled SD across repeats is 0.46 points. Judge noise is 0.6% of the variance of scores across deliveries (single-call reliability 0.994).
- The TypeSafe API exposes no seed or temperature, so this noise cannot be switched off; averaging three repeats reduces it.

## 2. Agreement with my own blind labels

I labelled 15 deliveries blind (three simple tasks × the top five models; no model names shown): 265 questions, flagging problems only. Files: [`judge-validation/hand-labels/`](../judge-validation/hand-labels/) (`RESULTS.md`, labels, `kappa.py`; `sample-key.json` maps the anonymised deliveries D01–D15 to models).

| Question kind | n | Raw agreement | Cohen's κ (95% CI) |
|---|---:|---:|---|
| Identity, conventions | 30 | 1.00 | undefined (all positive) |
| Coverage | 110 | 0.97 | 0.92 (0.74–1.00) |
| Legibility (P1) | 15 | 0.93 | n/a, one rater constant |
| Identification (P2) | 15 | 0.53 | n/a, one rater constant |
| Numeric "printed" | 95 | 0.84 | 0.60 (0.00–0.94) |
| **All questions** | 265 | 0.90 | **0.79 (0.59–0.93)** |

CIs are a percentile bootstrap over the 15 deliveries. Two labels I had entered for one delivery were corrected after the comparison showed the chart did print those values (originals kept in `labels/D02.json`); with the original labels κ is 0.78 (0.58–0.92).

What the comparison found:

- **Structure is reliable.** Identity and coverage agree almost perfectly.
- **P2 is stricter than me**, for every model alike (7 of 15 "partial" where I said "meets"). Making it lenient adds 1.2–1.4 points to each top model and does not change their order. Left as is.
- **A real bias in numeric legibility.** Every numeric disagreement went one way: the judge credited values that a chart did not print, read off unlabelled bars and line ends (15 of 78 questions), against the rule that a value counts only if printed.

## 3. Blind recheck of numeric legibility

To remove that bias, blind Sonnet 5.5 readers (no model names; instructions in `scoring/visual-rubric-v1/results/legible-recheck/reader-prompt.md`) re-read every numeric question where the judge gave legibility credit, and every one where it gave none but the code check found the value in the saved tables. The readers matched my labels on all 95 numeric questions of the hand-labelled sample before being used.

| | Credited by the judge | of which printed and admitted | Not credited but in saved tables | of which printed |
|---|---:|---:|---:|---:|
| Simple tasks, first three methods | 975 | 733 | 860 | 85 |
| Simple tasks, review methods | 473 | 232 | 804 | 56 |
| Complex tasks | 745 | 703 (+7 on adjudication) | 63 | 25 |

Model means on the simple tasks fell by 0.4–2.1 points; the ranking at the top and the frontier did not change. The corrected files replace the originals in every result; the originals are kept.

Caveat: the readers are from one of the tested labs (Sonnet 5.5). They only decided whether a number is printed, with no model names, and were checked against my labels first.

## 4. Earlier judge, for context

Before Jev, a chat model (Opus 5.5) graded each delivery once on a 0–20 scale. It had no repeat data and was in the tested pool. Its rank correlation with the Jev score on 279 matched deliveries was 0.38 (different rubrics, so this measures agreement, not noise). Its scores are not used here.
