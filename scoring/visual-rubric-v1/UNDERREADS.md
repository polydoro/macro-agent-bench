# Known judge under-reads (candidates for a targeted fix, not yet applied)

Deliveries where Jev under-reads a trajectory that is visibly present, usually in a dense
multi-panel image or small multiples. Collected during the provisional-5 pass, 2026-11-17.

| Task | Cell | Question(s) | Score given | What the chart shows |
|---|---|---|---|---|
| S01 | A3 claude-opus-5-5 | C_total_yoy, C_total_3m | ~0.4-0.6 | one 2210x1235 six-panel image; B-D YoY and 3m panel 2019-2026 |
| S02 | A2 claude-opus-5-5 | C_externo_yoy | 0.43 | foreign orders YoY in small multiples |
| S02 | A1 claude-sonnet-5-5 | C_externo_yoy | 0.11 | foreign orders YoY in small multiples (not hand-checked) |
| S02 | A1 gpt-6-astra | C_total_3m | 0.60 | 3m SAAR line 2023-2026 in a single clean chart |

## Other judge errors (not dense-panel)

| Task | Cell | Question(s) | Score given | What the chart shows |
|---|---|---|---|---|
| S08 | A2 gpt-6-luna | C_total_level, I1, I2 | 0.03, 0.54, 0.16 | clean real SA level 1980-2026 (CHF bn, chained 2020), YoY and q/q annualised; no source line on images. Cause unclear. |

## S10 conventions (I2) under-read, cause unknown

| Cell | I2 | What the images show |
|---|---|---|
| A1 Opus | 0.57 | p.p. changes (12m, 3m vs 3m), SA+smoothed SCB series, 15–74, source line |
| A1 Sol | 0.54 | same, "p.p. (sem anualização)", 15–74 |
| A1/A2 Luna, A3 Haiku | 0.39–0.54 | declared NSA and SA+smoothed rates |

Adding explicit admission of SCB "SA + suavizada" and of growth rates of levels (provisional-6) did not move I2. Candidate causes for the targeted fix: the judge wants every declared attribute (age band, frequency, adjustment) on every image, or it reads "média 3m − média 3m anterior" as a non-admitted transform.

## Diagnosis and fixes (provisional-7, 2026-11-17)

Diagnosed with single calls and Jev probe questions on the logged cells (about 30 calls, kept outside the repo store).

| Issue | Cause found | Fix in provisional-7 | Test result (ATENDE) |
|---|---|---|---|
| "Dense multi-panel" S01 A3 Opus | Not density: the coverage question named "produção industrial total", the chart says "Indústria (B-D, ex-construção)". Probes: Jev sees the YoY panel (1.00), accepts B-D as total (0.89), but answers the composite question at 0.41 | Admitted label inside the S01 total name | YoY 0.41 → 0.96, 3m 0.46 → 0.93 |
| S02 A2 Opus `externo` | Same label matching ("Exterior") | S02 component names carry synonyms (Inland/Ausland) | 0.43 → 0.65 |
| S02 A1 Sonnet `externo` | Genuine: the panel is "Zona do euro (externo)", a subset of foreign orders | none (negative control) | 0.11 → 0.07 |
| S02 A1 Astra `C_total_3m` | Unexplained; the chart shows 44 months of 3m SAAR titled "Total" | none | 0.60 → 0.50, residual |
| S08 A2 Luna (I1, I2, level) | Jev does not read the word "dessazonalizado" in the chart as seasonally adjusted (probe: "declared SA?" 0.40). Retitling the image to "SA (ajustado sazonalmente)" gives level 0.93. Text instructions (synonym lists, no-plausibility rule, label rule) do not override it | Level coverage no longer requires SA; I2 still judges adjustment | level 0.03 → 0.63; I1/I2 stay low (Jev limitation) |
| S10 and S04 conventions | Missing mass went to NAO_VERIFICAVEL because the conventions questions list items (age band, frequency) that charts rarely state | Conventions options: undeclared items are not errors; NAO_VERIFICAVEL only when nothing relevant is declared | S10 0.39–0.54 → 0.80–0.98; S04 0.44–0.52 → 0.71–0.96; S06/S07 controls move but stay below clean deliveries |

Known residual: any chart that labels SA only as "dessazonalizado" may still lose I1/I2 points.
