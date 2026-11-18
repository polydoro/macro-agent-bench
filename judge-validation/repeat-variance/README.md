# Jev repeat variance (identical requests), 2026-11-17

Inputs (stored responses only, no new calls): PR #1 branch claude/project-thread-x7r67z @ b25ebafa
(visual 60-pt provisional-7, A1–A3 S01–S11, 280 deliveries; numeric pass S01–S03, 78 deliveries) and
PR #3 branch claude/project-thread-90vag2 @ 23ddead8 (C04 pilot-3, 25 deliveries). Every set of 3
repeats shares one request hash. 4,479 question-repeat triples, 13,437 answers.
Scripts: analyse.py (all numbers in summary.json), paired.py (paired model gaps). flips.json lists every flipped question.

## Evidence
- Choice flips between identical requests: 2.1% of questions overall (visual 1.4%, numeric 5.5%, C04 2–4%).
  By block: coverage 0.7%, identity 1.5%, presentation 4.1%, numeric 4.6%, C04 text 4.0%.
- Chosen option = argmax of probabilities in 13,437 / 13,437 answers. Flip rate by mean top-2 margin:
  <0.1: 44%; 0.1–0.2: 13%; 0.2–0.4: 3%; 0.4–0.6: 0.6%; >0.6: 0% (3,639 questions).
- Probabilities: median absolute move per option 0.01, p95 0.07, max 0.66. Identical probability
  vectors across all 3 repeats in 20% of questions; no delivery got 3 identical responses (0/280).
- Visual 60 total (probability scoring): per-delivery SD median 0.30, p90 0.71, max 1.82; pooled SD 0.46.
  Range of 3 calls median 0.57, max 3.6. Blocks (of 20): identity 0.28, coverage 0.26, presentation 0.18 pooled SD.
  By task pooled SD 0.21 (S10) to 0.57 (S02). By image count: 1 img 0.64 (n=11), 2–3 0.47, 4–6 0.48, 7+ 0.36.
- Same 280 deliveries scored by chosen option: pooled SD 1.11 (median 0, p90 2.9, max range 11.7).
- Numeric Jev-only (scored by choice, 40 pts): pooled SD 2.07, median 0, max 5.8 (e.g. 0/10/0). Prob-scored: 0.49.
  In the combined numeric score Jev carries 10 of 40 points (legible), so this is about a quarter as large.
- C04 (100 pts): pooled SD 2.44 but median 0.45, p90 1.19; one outlier A2 Haiku 61.6/62.8/82.8 (block D 0/0/20).
- Judge noise = 0.6% of the variance of visual-60 scores across deliveries (single-call reliability 0.994).
- Model means (visual 60, judged deliveries only, absences excluded, so not the scoreboard): SE from judge
  noise 0.04–0.06; SE from task/arm spread 0.4–1.3. Paired top-6 gaps 0.1–1.1 pts, cell SE 0.5–1.0, judge SE 0.06–0.08.
- 247 adjacent pairs within task×arm cells: 88 have gap < 2 judge SEs.

## TypeSafe API (docs.typesafe.ai, read 2026-11-17)
No seed, temperature, top_p or sample count. Body: model, state, questions, assets. Headers: Authorization,
TypeSafe-Danger-Zone-Images, TypeSafe-Danger-Zone-Long-Context. No determinism, caching or idempotency statement.
Confidence is a formula on the probabilities; how probabilities are generated is not documented. Long context is
documented as "slower and less accurate"; images page says accuracy will change between releases. Pin jev-1.14.0.

## Opus judge (added 2026-11-17)
avaliacao/juiz-opus on main: 751 grades, 750 distinct deliveries by material hash; the one duplicate had different prompts (16, 16).
No repeat data. Agreement with Jev visual 60 on 279 matched A1–A3 S01–S11 deliveries: Spearman 0.38; within task×arm
median 0.45 (33 cells, −0.37 to 0.86). Different rubrics; agreement, not noise. Script: opus_rep.py.
