# Results

- `deliveries.csv`: one row per model × task × method (720). Columns: `suite` (S simple, C complex), `task`, `model`, `cli`, `method` (`low_effort`, `high_effort`, `examples`, `self_review`, `external_review`) and `arm` (A1, A2, A3, A4s, A4e), `status` (`delivered` or `no delivery`), `total` (0–100; blank for no delivery, counted as 0 in the analysis); simple-task parts `visual_60`, `correct_30`, `legible_10`; complex-task parts `method_50`, `numbers_30`, `shown_10`, `answer_10` (`pending Q4 flash` for C03 nowcasts of Q4); `minutes` (to final delivery; review methods include the first run), `revision_minutes`, `attempts`, `timed_out`, `output_ktokens` (as each CLI reports it; Kimi Code reports none), `judge_sd` (SD of the judge score across 3 repeats), `before_review_total` (review methods: score of the low-effort delivery they started from).
- `model-method-summary.csv`: mean per model and method with 90% bootstrap intervals and ranks, by suite (`simple`, `complex`, `all`), metric (total or part) and treatment of no-delivery runs (`zero` or `delivered`). `method = all_A1_A3` pools the first three methods.
- `frontier-en.png`, `frontier-pt.png`: the figure, made by `analysis/figure.py`.

Built from the score files under `scoring/` by `scoring/scoreboard-v1/build_scoreboard.py` (its JSON output is in `scoring/scoreboard-v1/data/`).
