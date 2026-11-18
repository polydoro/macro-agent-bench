# Answer keys for the numeric 40 points

One key per task and arm (A1, A2, A3 ran on different dates). There is no independent data
source: the key is computed here from the official downloads the agents saved during their own
runs (in Git, or in release `raw-archive-20261116`). Agent calculations are only used as checks.

## Rules decided by the author (2026-11-17)
- A trajectory must cover at least 24 months.
- Timeliness: a delivery must reach the latest period in the release available on its run date.
  If its last observation is older, the latest-value questions score zero (not undetermined).
  This applies inside the numeric 40 points only; the visual 60 points are not rerun.

## Method
1. Parse every saved official file for the task (S01: Eurostat JSON-stat `sts_inpr_m`, `sts_copr_m`).
2. Group by the publisher's `updated` stamp. Within one stamp all agents' copies must agree cell by
   cell, or the build stops.
3. For each arm, use the newest stamp not after the arm's run date. The latest period in that stamp
   is the latest period available to the arm, which also serves a timeliness rule if one is adopted.
4. Compute the transforms here: YoY on the calendar-adjusted (CA) and on the seasonally and
   calendar-adjusted (SCA) series, and 3m/3m SAAR on SCA as
   `100*((mean(t,t-1,t-2)/mean(t-3,t-4,t-5))^4-1)`.

## S01 (`build_s01.py`, `S01-key.csv`)
- 179 Eurostat files across 4 stamps (2026-10-15, 10-23, 10-29, 11-04); 440,368 cells; 0 disagreements.
- Latest period is 2026-08 for all three arms (Destatis published September on 2026-11-07, after A3).
- Cross-check with the Destatis press release of 2026-10-07 saved by A3 Sol: headline (B-D_F) YoY
  +2.3 % (key 2.26), three-month comparison +0.4 % (key 3m SAAR 1.62 = 1.004^4), "Industrie"
  YoY -0.4 % (key B_C -0.36). A2 Sonnet's own YoY file: B-D 0.362 (key 0.36).
- Decided by the author 2026-11-17: `D` (electricity, gas) counts as "energia" (`MIG_NRG` was downloaded
  by no agent), and Destatis's "Industrie" (B_C, without energy and construction) is an admitted
  total alongside B-D and B-D_F.

## S02 (`bbk.py`, `build_s02.py`, `S02-key.csv`)
- Bundesbank BBDE1 (Destatis data) as saved by agents in all three arms, SDMX-CSV and web CSV;
  102,147 cells, 0 disagreements within or across arms. Web CSVs carry `last update 2026-10-06`.
- Latest period 2026-08 for all arms (September orders were published after A3 ran).
- Codes from the series titles: AEA1 total, AEB1 domestic, AEB5 foreign. AED1 is foreign orders
  from euro-area countries only (AED5 non-euro area); they do not stand for total foreign.
- Cross-check with Destatis press release 354 of 2026-10-06 (saved by A3 Astra/Sol/Haiku):
  m/m SA total -10.6, domestic -17.3, foreign -5.4, euro area -5.4, non-euro area -5.5 and
  3m/3m +1.3 all reproduced exactly; total YoY calendar-adjusted 2.67 vs release +2.7.
- Domestic and foreign have no calendar-adjusted-only series in the downloads; their key YoY is on
  the SA series (what agents could compute from what they had).

## S03 (`ine.py`, `build_s03.py`, `S03-key.csv`)
- Timeliness matters here: INE published September on 2026-10-29. A1 (run 2026-10-27) had August
  as the latest month; A2 and A3 had September.
- A2/A3: INE tempus3 index series saved by agents, constant prices, original / calendar-adjusted /
  seasonally and calendar adjusted; all copies agree. September YoY reproduces INE's own rate series
  (general SA -1.4, CA -1.6; without service stations SA 0.1, CA 0.0).
- A1: rates from the INE August release annex (`ICM0826.xlsx`, 2026-09-29, constant-price columns),
  which A1 agents saved. Using A2's September-release series for August would be wrong: August was
  revised by up to 1 point (e.g. personal equipment SA YoY 2.5 → 1.5).
- A1 total 3m SAAR comes from Eurostat `sts_trtu_m` ES G47 SCA (stamp 2026-10-27, A1's own
  download; its August SA level 111.6 equals the annex). A1 has no keyed 3m SAAR for the total
  without service stations: no A1 agent saved that monthly series.

## S04 (`build_s04.py`, `S04-key.csv`)
- INSEE release annex `260_IR_Camme.xlsx` (SA history), saved in all three arms; every French
  copy of the latest edition agrees. All arms had the October 2026 survey (published 2026-10-27,
  the morning A1 ran). One agent also saved an older edition (last month 2022-07); it is ignored.
- Native values: confidence indicator 80.32 (release text: "À 80, l'indicateur ... baisse de cinq
  points"). Saving capacity admits current or future; prices admit past or expected.

## S05 and S06 (`build_s05_s06.py`, `S05-S06-key.csv`, `S05-NIC-key.csv`)
- HICP from Eurostat JSON-stat (`coicop18`, I25 index and RCH_A) saved by the agents; all copies of
  a stamp agree. Stamp 2026-10-16 for A1/A2 (latest 2026-09), 2026-11-04 for A3 (October flash).
  The separate flash-versus-final table (`release` dimension) is skipped.
- YoY: Eurostat RCH_A (1 dp); the rate recomputed from I25 agrees to rounding everywhere.
- 3m SAAR end to end, `100*((SA_t/SA_t-3)^4-1)`:
  - S06: ECB official SA index `HICP.M.U2.Y.<item>.4F0.INX`, the arm's own downloads. Matches
    agents that used it (e.g. Fable A3 total 5.83, core 2.68).
  - S05: no official SA exists. X13 under the old evaluator's policy (`x13.py`, which reproduces
    52 of 54 cached fits exactly) on Eurostat I25 from 2010-01.
  - Energy: SA or unadjusted both admitted (the author, 2026-11-17); the ECB SA energy equals NSA.
- S05 headline may be ISTAT's NIC (rubric admits NIC or HICP). `S05-NIC-key.csv`: YoY quoted from
  ISTAT (A1/A2: `serie09_2026.xlsx` Tabella_6 and September rates; A3: preliminary October release of
  30 Oct, 5.4%). NIC total 3m SAAR: X13 on ISTAT M.IT.39.4.00 (2016–2025, linked with ISTAT's
  coefficient 1.226) plus M.IT.85.4.00 (2026); checked against Tabella_6 for every month it shows.
  ISTAT core ("inflazione di fondo", ex energy and fresh food) and services are quoted from the
  release text only.

### Seasonal-adjustment criterion (the author, 2026-11-17)
- First a residual-seasonality test on the agent's own saved SA series, full saved history
  (`resid_seas.py`, `extract_sa.py`, `run_resid_seasonality.py`): F-test on month dummies of the
  m/m change; pass p >= 0.05, fail p < 0.01, otherwise inconclusive. Validated on ECB SA and X13
  (pass) versus unadjusted series (fail): `S05-S06-residual-seasonality-validation.txt`.
- Inconclusive series and the five borderline Italian non-energy-goods failures go to a threshold:
  RMSE of the 3m SAAR over the last 24 months against the reference above, pass <= 1.0 pp
  (`run_sa_threshold.py`, `S05-S06-sa-threshold.csv`).
- Too short (< 36 months saved; none had 24–35) or no saved series: fail. Energy is not tested.
- Agents' series that equal the ECB official SA pass outright.

## S07 (`build_s07.py`, `S07-key.csv`)
- ONS MGDP CSV, release 15-10-2026 (August 2026), saved in all three arms; 68 copies (full dataset
  and single-series downloads) agree cell by cell. The 12 November release came after A3, so every
  arm keys August. An older September-release copy (one A2 agent) is ignored.
- Codes: total ECY2 (GVA, CVM SA), services ECYC, production ECY4, construction ECY9, manufacturing
  ECY6 (admitted subdivision).
- YoY: ONS published rate (e.g. total 2.1) and the rate from the 1-dp index (1.98); both admitted.
- 3m/3m SAAR: from the index, 2.63 for the total, and ONS's unannualised 3m/3m (0.7) annualised,
  2.83. Agents used both (checked in A3 delivery tables), so both are keyed.

## S08 (`build_s08.py`, `S08-key.csv`)
- SECO quarterly accounts workbooks (`qna_p_csa/cssa`, `qna_e_csa/cssa`, sheet `real_q`), saved in
  all three arms; every copy of each file is byte-identical. Latest quarter 2026 Q2 for all arms
  (release of 3 September 2026; Q3 came after A3).
- Both GDP totals admitted: sport-event adjusted q/q 1.54 (release: "grew by 1.5%"), YoY 2.15;
  without sport adjustment q/q 1.88, YoY 2.63.
- Components keyed by SECO code: household and government consumption, GFCF (total, construction,
  equipment and software), exports and imports (total, goods, goods ex gold, services),
  manufacturing, and each services section. Release-text aggregates added: services sector +0.7,
  industrial sector +3.9 (q/q). Cross-checked against the release: manufacturing +4.5, transport
  +1.9, communications +1.1.
- Transforms: YoY on chained levels, SECO's published q/q, and q/q annualised.

## S09 (`build_s09.py`, `S09-key.csv`)
- SSB table 07129 JSON-stat saved in all arms; copies agree within each stamp. A1 has the release
  stamped 2026-09-28 (latest August); A2/A3 have 2026-10-28 (latest September; SSB published it
  the day after A1 ran).
- Totals: 47 (retail) and 47_ub (excluding automotive fuel), both admitted. Components by NACE:
  food 47.1/47.2, fuel 47.3, household/ICT equipment 47.4/47.5, culture 47.6, other goods 47.7,
  internet/mail order 47.9.
- YoY on calendar-adjusted, unadjusted and SA volume (any declared variant admitted); 3m/3m SAAR on
  SA volume. Cross-check with the SSB September release table: 12-month change (calendar adjusted)
  47 -1.4, 47.9 3.0; 3-month change 47 0.0. All reproduced.

## S10 (`build_s10.py`, `S10-key.csv`)
- SCB AKU JSON-stat (population 15-74 by labour status and type of data), 39 copies across all
  arms, all stamped 2026-10-16 and agreeing; latest September 2026 for every arm. Tables with an
  extra breakdown (e.g. born in Sweden/abroad) are skipped.
- Unemployment rate 15-74, September 2026: unadjusted 8.1, SA 8.6, SA and smoothed 8.7. Changes
  in percentage points keyed (1 month and 12 months). Eurostat `une_rt_m` for Sweden (stamp
  2026-10-30, saved in A2/A3) gives the same three values.

## S11 (ECB bank lending survey)

`build_s11.py` → `S11-key.csv`. Source: ECB data portal CSVs (`BLS.Q.U2.ALL.*.WFNET`) saved by the agents in all three arms; all copies agree cell by cell (Grok A3 `bls_series_long.csv` has no TIME_PERIOD and is skipped).

- All arms have the October 2026 round. The ECB report calls it the survey for the third quarter of 2026; the ECB data portal stores it under TIME_PERIOD `2026-Q4`. Both labels are admitted.
- Keyed values are realised changes (B3), native net percentages. Expected changes for the next quarter (F3) are listed separately and are not interchangeable with B3.
- Realised: firms' credit standards 8.55 (previous 7.29), firms' demand -6.39, housing standards -0.27, housing demand -26.92, consumer standards 14.04, consumer demand -2.44.
- Cross-check against the ECB report (rounded): 9, -6, 0, -27, 14, -2 realised; 7, -1, 10, -36, 16, -14 expected. All match.

## 3m SAAR definition by task (checked 2026-11-17)

- S01, S02, S03, S07, S09 (activity): 3-month average over the previous 3-month average, annualised,
  the publishers' own three-month comparison (Destatis Dreimonatsvergleich, ONS 3m-on-3m).
- S05, S06 (inflation): point to point, `(I_t/I_t-3)^4`, on the SA index; the SA threshold and the
  own-series value in the SA gate use the same formula on both sides.
- Counterfactual (scratch, nothing changed): admitting the average-over-average definition as well for
  S05/S06 (reference and own series, A1-A4) flips 4 values, all coincidences: Luna S05 A1 and A4s services
  2.31 is its own point-to-point value for 2025-12 (stale); Sonnet S06 A2 NEIG 1.95 is point to point on its
  own STL series; Luna S05 A4e core 1.90 is the same under both formulas. No S05/S06 agent computes a
  3-month average (no `rolling(3).mean` in their code); the 18.5 energy figure seen in C05 does not occur in S06.
