"""Build the data behind the model scoreboard: score by model, task and arm; Pareto against time to completion.

Two suites, S (S01-S11, 100-point S rubric) and C (C01-C05, 100-point C rubric), plus "SC", which pools
the 16 tasks on the total score only (each task weighs the same, so S carries 11/16 of the mean).

Inputs (read only):
  --s-scores   visual-rubric-v1/results/score-100-A1-A2-A3-S01-S11-<rubric>.csv (PR #1): one row per delivery,
               visual_60, numeric_correct_30, numeric_legible_10, total_100
  --s-pass     visual-rubric-v1/results/ dir with pass-A1-A2-A3-S??-<rubric>.json (attempt ids, judge SD)
  --c-scores   c-rubric-v1/results/summary-c-rubric-v1-4.csv (PR #3): L_mean (0-100) and blocks A-E (old, method-only)
  --c-gold     c-rubric-v1/results/score-100-C-c-gold-provisional-1.csv (PR #3): gold-standard 100 points, one row per
               delivery for A1-A3 and both A4 arms (result 50 = numbers 30 + shown 10 + answer 10, method 50).
               Replaces --c-scores and the A4 C scores. A C task with any blank total (C03 A2-A4, waiting for the
               Q4 flash) is left out of every arm, so all arms are compared on the same tasks.
  --c-pass     c-rubric-v1/results/ dir with pass-A1-A2-A3-C0?-c-rubric-v1-4.json (attempt ids)
  --repo       repo root, for execucoes/<campaign>/attempts/<attempt>/receipt.json
  --a4-s-scores, --a4-s-pass, --a4-s-before   A4 S files (score-100-A4-S01-S11-*.csv, pass-A4-S01-...-*.json,
               a4-before-after-*.csv), PR #1
  --a4-c-pass, --a4-c-before   A4 C files (dir with pass-A4_external_review-A4_self_review-C0?-*.json,
               a4-before-after-c-rubric-*.csv), PR #3
Outputs (in --out): cells.json, summary.json and a4.json, each {rows, meta}; meta carries this script's text.

Rules:
  - Arms: A1, A2, A3, A4s (self-review) and A4e (external review). A4 scores are the after-revision scores;
    the A4 seed (before revision) is the A1 primary delivery and appears only in a4.json as a check.
    "All" pools A1-A3 only: A4 starts from A1 seeds, so pooling it with A1 would count A1 work twice.
  - A4 time to final delivery = seed attempt time (its A1 primary receipt) + revision time (active seconds of
    every A4 role receipt in the branch, primary and timeout retry, reviewer included for A4e). A4 output
    tokens = seed + executor roles (the A4e reviewer is GPT-6 Astra, another model, and is left out).
  - A verified absence, or a run with no usable product, scores 0 on every metric ("no delivery").
  - Two treatments of no-delivery runs: "zero" (counted as 0, every model on all tasks) and "delivered"
    (dropped, so means use different task sets).
  - Time to completion = elapsed_seconds of the final attempt plus its primary attempt when the final one is a
    timeout retry or an access resumption (the protocol sums both). A run stopped at the limit counts the time
    it used. Blank when a receipt has no elapsed time (one infrastructure failure: A3 S10 Kimi).
  - Output tokens = usage_reported.output_tokens (reasoning included, as each CLI reports it), summed the
    same way; blank unless every summed attempt reports it. Kimi Code reports no usage. Context only.
  - Cost is not used: every run used a CLI subscription.
  - Uncertainty: bootstrap over the suite's tasks (resampled jointly for all models, so comparisons stay
    paired), B draws, fixed seed; 90% percentile intervals for the mean and for the rank. With 5 C tasks
    these intervals are coarse.
"""
import argparse
import csv
import glob
import json
import os
import random
import statistics

LABELS = {
    "claude-opus-5-5": "Opus 5.5", "claude-sonnet-5-5": "Sonnet 5.5", "claude-haiku-5-5": "Haiku 5.5",
    "claude-fable-5-1": "Fable 5.1", "gpt-6-astra": "GPT-6 Astra", "gpt-6-luna": "GPT-6 Luna",
    "gpt-6.1-sol": "GPT-6.1 Sol", "grok-4.7": "Grok 4.7", "kimi-code/k3.1-pro": "Kimi k3.1-pro",
}
CLI = {"claude": "Claude Code", "gpt": "Codex", "grok": "Grok CLI", "kimi": "Kimi Code"}
ARMS = ["A1", "A2", "A3"]
ALL_ARMS = ARMS + ["A4s", "A4e"]
C_PHASE = {"A4_self_review": "A4s", "A4_external_review": "A4e"}
METRICS = {
    "S": {"total": "total_100", "visual": "visual_60", "correct": "numeric_correct_30", "legible": "numeric_legible_10"},
    "C": {"total": "L_mean", "A": "A", "B": "B", "C": "C", "D": "D", "E": "E"},
    "Cgold": {"total": "total_100", "method": "method_50", "numbers": "numbers_30", "shown": "shown_10", "answer": "answer_10"},
    "SC": {"total": None},
}
SUITES = {"S": ("S",), "C": ("C",), "SC": ("S", "C")}
METRICS_OF = {"S": list(METRICS["S"]), "C": list(METRICS["C"]), "SC": ["total"]}
DELIVERED = {"scored", "judged"}


def score(v, ok):
    """0 for a run with no delivery; None for a part not scored yet (e.g. C03 answer "pending Q4 flash"), left out of means."""
    if not ok:
        return 0.0
    try:
        return round(float(v), 2)
    except (TypeError, ValueError):
        return None if v else 0.0


def load_receipts(repo):
    rec = {}
    for f in glob.glob(os.path.join(repo, "execucoes/*/attempts/*/receipt.json")):
        r = json.load(open(f))
        rec[(f.split(os.sep)[-4], r["attempt_id"])] = r
    return rec


def run_attempts(camp, final_id, rec):
    ids = [final_id]
    for tag in ("-timeout-retry1", "-access-resumption1"):
        if final_id.endswith(tag):
            ids.append(final_id[: -len(tag)] + "-primary")
    return [rec[(camp, i)] for i in ids if (camp, i) in rec]


def cell_rows(suite, scores_csv, pass_glob, rec, metrics=None):
    metrics = metrics or METRICS[suite]
    passes = {}
    for f in sorted(glob.glob(pass_glob)):
        for r in json.load(open(f))["rows"]:
            passes[(r["task"], r["phase"], r["model"])] = r
    rows = []
    for s in csv.DictReader(open(scores_csv)):
        if s["phase"] not in ARMS:
            continue
        p = passes[(s["task"], s["phase"], s["model"])]
        atts = run_attempts(p["source_campaign_id"], p["final_attempt_id"], rec)
        outs = [((a.get("telemetry") or {}).get("usage_reported") or {}).get("output_tokens") for a in atts]
        ok = s["status"] in DELIVERED
        row = {
            "suite": suite, "arm": s["phase"], "task": s["task"], "model": LABELS[s["model"]],
            "cli": CLI[s["model"].split("-")[0]], "status": "delivered" if ok else "no delivery",
            "judge_sd": round(p["L_sd"], 2) if ok and p.get("L_sd") is not None else None,
            "minutes": round(sum(a["elapsed_seconds"] for a in atts) / 60, 2)
            if atts and all(a.get("elapsed_seconds") is not None for a in atts) else None,
            "attempts": len(atts), "timed_out": any(a.get("timed_out") for a in atts),
            "output_ktokens": round(sum(outs) / 1000, 1) if atts and all(o is not None for o in outs) else None,
            "attempt_id": p["final_attempt_id"],
        }
        for k, col in metrics.items():
            row[k] = score(s[col], ok)
        rows.append(row)
    return rows


def a4_time_tokens(repo, camp, attempt, rec):
    f = os.path.join(repo, "execucoes", camp, "evaluation-snapshots", attempt, "evaluation-source.json")
    if not os.path.exists(f):
        return None, None, None
    d = json.load(open(f))
    seed = rec.get((d["source_A1_campaign_id"], d["source_A1_primary_attempt_id"]))
    pair = os.path.join(repo, "execucoes", d["pair_directory"].split("/srv/benchmark/")[1])
    roles = [json.load(open(r)) for r in glob.glob(os.path.join(pair, "arms", d["experimental_arm"], "*", "roles", "*", "receipt.json"))]
    rev = [r.get("active_elapsed_seconds") or r.get("elapsed_seconds") for r in roles]
    if not seed or seed.get("elapsed_seconds") is None or not roles or any(x is None for x in rev):
        return None, None, None
    outs = [((seed.get("telemetry") or {}).get("usage_reported") or {}).get("output_tokens")]
    outs += [((r.get("telemetry") or {}).get("usage_reported") or {}).get("output_tokens") for r in roles if r.get("role") != "reviewer"]
    tok = round(sum(outs) / 1000, 1) if all(o is not None for o in outs) else None
    return round((seed["elapsed_seconds"] + sum(rev)) / 60, 2), round(sum(rev) / 60, 2), tok


def a4_rows(suite, repo, rec, pass_rows, scores, before, metrics=None):
    metrics = metrics or METRICS[suite]
    """pass_rows: A4 pass rows; scores: {(task, arm, model_id): {metric: value}} or None to read L_mean/blocks."""
    rows = []
    for p in pass_rows:
        arm = C_PHASE.get(p["phase"], p["phase"])
        ok = p["status"] in DELIVERED
        minutes, rev, tok = a4_time_tokens(repo, p["source_campaign_id"], p["final_attempt_id"], rec)
        row = {
            "suite": suite, "arm": arm, "task": p["task"], "model": LABELS[p["model"]],
            "cli": CLI[p["model"].split("-")[0]], "status": "delivered" if ok else "no delivery",
            "judge_sd": round(p["L_sd"], 2) if ok and p.get("L_sd") is not None else None,
            "minutes": minutes, "revision_minutes": rev, "attempts": None, "timed_out": None,
            "output_ktokens": tok, "attempt_id": p["final_attempt_id"],
            "before_total": before.get((p["task"], arm, p["model"])),
        }
        if scores is not None:
            sc = scores[(p["task"], arm, p["model"])]
            for k, col in metrics.items():
                row[k] = score(sc[col], ok)
        else:
            row["total"] = round(p["L_mean"], 2) if ok else 0.0
            for k in "ABCDE":
                row[k] = round(p["blocks_mean"][k], 2) if ok and p.get("blocks_mean") else 0.0
        rows.append(row)
    return rows


def a4_summary(cells):
    out = []
    for suite in ("S", "C", "SC"):
        for m in sorted({c["model"] for c in cells if c["suite"] in SUITES[suite]}):
            r = {"suite": suite, "model": m}
            for arm in ("A4s", "A4e"):
                cs = [c for c in cells if c["suite"] in SUITES[suite] and c["model"] == m and c["arm"] == arm and c["before_total"] is not None]
                if not cs:
                    continue
                r["n"] = len(cs)
                r["before"] = round(statistics.fmean(c["before_total"] for c in cs), 2)
                r[f"{arm}_after"] = round(statistics.fmean(c["total"] for c in cs), 2)
                r[f"{arm}_up"] = sum(c["total"] > c["before_total"] + 0.5 for c in cs)
                r[f"{arm}_down"] = sum(c["total"] < c["before_total"] - 0.5 for c in cs)
            if "n" in r:
                out.append(r)
    return out


def pct(xs, p):
    xs = sorted(xs)
    k = (len(xs) - 1) * p
    lo, hi = int(k), min(int(k) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def summarise(cells, suite, B, seed):
    cells = [c for c in cells if c["suite"] in SUITES[suite]]
    tasks = sorted({c["task"] for c in cells})
    models = sorted({c["model"] for c in cells})
    by = {(c["arm"], c["task"], c["model"]): c for c in cells}
    rng = random.Random(seed)
    strata = [sorted({c["task"] for c in cells if c["suite"] == u}) for u in SUITES[suite]]
    # resample within each suite, so the pooled mean keeps the 11 S / 5 C mix in every draw
    draws = [[rng.choice(st) for st in strata for _ in st] for _ in range(B)]
    out = []
    for view in [v for v in ALL_ARMS if any(c["arm"] == v for c in cells)] + ["All"]:
        arms = ARMS if view == "All" else [view]
        for treat in ("zero", "delivered"):
            for metric in METRICS_OF[suite]:
                def mean(model, ts):
                    xs = [by[(a, t, model)] for t in ts for a in arms]
                    xs = [c[metric] for c in xs if (treat == "zero" or c["status"] == "delivered") and c[metric] is not None]
                    return statistics.fmean(xs) if xs else None
                full = {m: mean(m, tasks) for m in models}
                boot = {m: [] for m in models}
                ranks = {m: [] for m in models}
                for ts in draws:
                    ms = {m: mean(m, ts) for m in models}
                    order = sorted([m for m in models if ms[m] is not None], key=lambda m: -ms[m])
                    for m in order:
                        boot[m].append(ms[m])
                        ranks[m].append(order.index(m) + 1)
                ranked = sorted([m for m in models if full[m] is not None], key=lambda m: -full[m])
                for m in models:
                    cs = [by[(a, t, m)] for t in tasks for a in arms]
                    minutes = [c["minutes"] for c in cs if c["minutes"] is not None]
                    toks = [c["output_ktokens"] for c in cs if c["output_ktokens"] is not None]
                    sds = [c["judge_sd"] for c in cs if c["judge_sd"] is not None]
                    has = full[m] is not None
                    out.append({
                        "suite": suite, "view": view, "treatment": treat, "metric": metric, "model": m,
                        "cli": cs[0]["cli"], "cells": len(cs), "delivered": sum(c["status"] == "delivered" for c in cs),
                        "mean": round(full[m], 2) if has else None,
                        "lo90": round(pct(boot[m], 0.05), 2) if boot[m] else None,
                        "hi90": round(pct(boot[m], 0.95), 2) if boot[m] else None,
                        "rank": ranked.index(m) + 1 if has else None,
                        "rank_lo90": round(pct(ranks[m], 0.05)) if ranks[m] else None,
                        "rank_hi90": round(pct(ranks[m], 0.95)) if ranks[m] else None,
                        "mean_minutes": round(statistics.fmean(minutes), 2),
                        "median_minutes": round(statistics.median(minutes), 2),
                        "mean_output_ktokens": round(statistics.fmean(toks), 1) if toks else None,
                        "token_cells": len(toks),
                        "mean_judge_sd": round(statistics.fmean(sds), 2) if sds else None,
                    })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--s-scores", required=True)
    ap.add_argument("--s-pass", required=True)
    ap.add_argument("--s-rubric", default="visual-rubric-v1-provisional-7")
    ap.add_argument("--c-scores")
    ap.add_argument("--c-pass")
    ap.add_argument("--c-gold")
    ap.add_argument("--c-rubric", default="c-rubric-v1-4")
    ap.add_argument("--a4-s-scores")
    ap.add_argument("--a4-s-pass")
    ap.add_argument("--a4-s-before")
    ap.add_argument("--a4-c-pass")
    ap.add_argument("--a4-c-before")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--out", default="scoreboard-v1/data")
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20261117)
    a = ap.parse_args()
    rec = load_receipts(a.repo)
    cells = cell_rows("S", a.s_scores, os.path.join(a.s_pass, f"pass-A1-A2-A3-S??-{a.s_rubric}.json"), rec)
    if a.a4_s_scores:
        prs = json.load(open(a.a4_s_pass))["rows"]
        sc = {(r["task"], r["phase"], r["model"]): r for r in csv.DictReader(open(a.a4_s_scores))}
        bf = {(r["task"], r["arm"], r["model"]): float(r["before_100"]) for r in csv.DictReader(open(a.a4_s_before))}
        cells += a4_rows("S", a.repo, rec, prs, sc, bf)
    summary = summarise(cells, "S", a.boot, a.seed)
    c_note = "not included"
    if a.c_gold:
        METRICS_OF["C"] = list(METRICS["Cgold"])
        gold = list(csv.DictReader(open(a.c_gold)))
        pending = sorted({g["task"] for g in gold if g["total_100"] == ""})
        cc = cell_rows("C", a.c_gold, os.path.join(a.c_pass, f"pass-A1-A2-A3-C0?-{a.c_rubric}.json"), rec, METRICS["Cgold"])
        prs = [r for f in sorted(glob.glob(os.path.join(a.a4_c_pass, f"pass-A4_external_review-A4_self_review-C0?-{a.c_rubric}.json")))
               for r in json.load(open(f))["rows"]]
        sc = {(g["task"], C_PHASE.get(g["phase"], g["phase"]), g["model"]): g for g in gold}
        # A4 seeds are byte-identical to the A1 deliveries, so "before" is the A1 gold total
        bf = {(g["task"], arm, g["model"]): float(g["total_100"]) for g in gold if g["phase"] == "A1" and g["total_100"] != "" for arm in ("A4s", "A4e")}
        cc += a4_rows("C", a.repo, rec, prs, sc, bf, METRICS["Cgold"])
        for c in cc:
            c["judge_sd"] = None  # the pass-file SD belongs to the old method-only score
        cells += [c for c in cc if c["task"] not in pending]
        summary += summarise(cells, "C", a.boot, a.seed)
        summary += summarise(cells, "SC", a.boot, a.seed)
        c_note = f"{os.path.basename(a.c_gold)} (PR #3), gold standard, 100 points, provisional; left out until every arm has a total: {', '.join(pending) or 'none'}"
    elif a.c_scores:
        cells += cell_rows("C", a.c_scores, os.path.join(a.c_pass, f"pass-A1-A2-A3-C0?-{a.c_rubric}.json"), rec)
        if a.a4_c_pass:
            prs = [r for f in sorted(glob.glob(os.path.join(a.a4_c_pass, f"pass-A4_external_review-A4_self_review-C0?-{a.c_rubric}.json")))
                   for r in json.load(open(f))["rows"]]
            bf = {}
            for r in csv.DictReader(open(a.a4_c_before)):
                for arm in ("A4s", "A4e"):
                    bf[(r["task"], arm, r["model"])] = float(r["before_A1"])
            cells += a4_rows("C", a.repo, rec, prs, None, bf)
        summary += summarise(cells, "C", a.boot, a.seed)
        summary += summarise(cells, "SC", a.boot, a.seed)
        c_note = os.path.basename(a.c_scores) + " (PR #3), 100 points, method-only rubric, provisional"
    meta = [{"label": "build_scoreboard.py", "value": open(__file__).read(), "type": "code", "lang": "python"},
            {"label": "S scores", "value": os.path.basename(a.s_scores) + " (PR #1), 100 points, provisional"},
            {"label": "C scores", "value": c_note},
            {"label": "Run receipts", "value": "execucoes/<campaign>/attempts/<attempt>/receipt.json"},
            {"label": "Bootstrap", "value": f"B={a.boot}, seed={a.seed}, tasks resampled jointly within a suite (within S and within C for the pooled view)"}]
    os.makedirs(a.out, exist_ok=True)
    json.dump({"rows": cells, "meta": meta}, open(os.path.join(a.out, "cells.json"), "w"), indent=0)
    json.dump({"rows": summary, "meta": meta}, open(os.path.join(a.out, "summary.json"), "w"), indent=0)
    json.dump({"rows": a4_summary(cells), "meta": meta}, open(os.path.join(a.out, "a4.json"), "w"), indent=0)
    print(len(cells), "cells,", len(summary), "summary rows")


if __name__ == "__main__":
    main()
