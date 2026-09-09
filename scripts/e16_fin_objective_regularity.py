#!/usr/bin/env python3
"""Objective FIN regularity discovery (RESEARCH ONLY) — no presupposed May–Jun story.

Scans:
  A) Cash-ex relative day effects (T-40..T+10)
  B) Calendar half-month forward returns
  C) Yahoo K9 threshold crossings → forward return (any month)
  D) Interaction grid: entry month × K thresh × exit at T-k before ex
     with train (≤2019) / test (≥2020) split

Soft-Frozen KEEP · live e21 untouched · discovery ≠ cutover.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e16_soft_frozen_base as soft
from e45_paper_harness import load_dividends, load_market
from e50_early_stack_combined_nav import FIN
from tw_yahoo_kd import yahoo_kd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/fin-objective-regularity-20260909"
RESEARCH = ROOT / "research/ops"

TRAIN_END_YEAR = 2019
TEST_START_YEAR = 2020


def _prep(market: pd.DataFrame, dividends: pd.DataFrame):
    m = market[market["code"].astype(str).isin(FIN)].copy()
    m["date"] = pd.to_datetime(m["date"])
    m["code"] = m["code"].astype(str)
    for c in ("high", "low", "close"):
        m[c] = pd.to_numeric(m[c], errors="coerce")
    d = dividends.copy()
    d["code"] = d["code"].astype(str)
    d["cash_ex_date"] = pd.to_datetime(d["cash_ex_date"], errors="coerce")
    d = d[d["code"].isin(FIN) & d["cash_ex_date"].notna()]
    return m, d


def scan_exdiv_relative(m: pd.DataFrame, d: pd.DataFrame) -> pd.DataFrame:
    """Mean forward return from offset t to ex-1, and share of local max in bins."""
    rows = []
    local_rows = []
    for code, g in m.groupby("code"):
        g = g.sort_values("date").set_index("date")
        px = g["close"]
        cal = list(px.index)
        pos = {dt: i for i, dt in enumerate(cal)}
        for ex0 in sorted(d.loc[d["code"] == code, "cash_ex_date"].unique()):
            later = [dt for dt in cal if dt >= pd.Timestamp(ex0)]
            if not later:
                continue
            ex = later[0]
            i = pos[ex]
            if i < 40 or i + 5 >= len(cal):
                continue
            year = ex.year
            # local max in [T-40,T+5]
            w = px.iloc[i - 40 : i + 6]
            dist = (i - 40 + int(np.nanargmax(w.to_numpy(dtype=float)))) - i
            local_rows.append({"code": code, "year": year, "dist": int(dist)})
            for t in range(-40, 6):
                j = i + t
                if j < 0 or j >= i:  # only pre-ex entries for path-to-ex-1
                    if t > 0:
                        # post-ex: forward 5d from t
                        j2 = min(len(cal) - 1, j + 5)
                        ret = float(px.iloc[j2] / px.iloc[j] - 1)
                        rows.append(
                            {
                                "code": code,
                                "year": year,
                                "t": t,
                                "metric": "fwd_5d",
                                "ret": ret,
                            }
                        )
                    continue
                # return from t to ex-1
                ret = float(px.iloc[i - 1] / px.iloc[j] - 1)
                rows.append(
                    {
                        "code": code,
                        "year": year,
                        "t": t,
                        "metric": "to_ex_minus_1",
                        "ret": ret,
                    }
                )
    path = pd.DataFrame(rows)
    loc = pd.DataFrame(local_rows)
    # aggregate path
    agg = (
        path.groupby(["metric", "t"])["ret"]
        .agg(["count", "mean", "median"])
        .reset_index()
    )
    # local max histogram
    bins = [(-40, -21), (-20, -11), (-10, -1), (0, 0), (1, 5)]
    hist = []
    for a, b in bins:
        hist.append(
            {
                "bin": f"[{a},{b}]",
                "share": float(loc["dist"].between(a, b).mean()) if len(loc) else None,
                "n": int(len(loc)),
                "expected": (b - a + 1) / 46.0,
            }
        )
    return agg, pd.DataFrame(hist), loc


def scan_calendar(m: pd.DataFrame, horizons=(20, 40, 60)) -> pd.DataFrame:
    """Half-month bucket → forward median return (equal-weight FIN)."""
    wide = (
        m.pivot_table(index="date", columns="code", values="close", aggfunc="last")
        .sort_index()
        .ffill()
    )
    ew = wide[FIN].mean(axis=1)
    rows = []
    for dt, px0 in ew.items():
        month = dt.month
        half = "H1" if dt.day <= 15 else "H2"
        bucket = f"{month:02d}-{half}"
        i = ew.index.get_loc(dt)
        if isinstance(i, slice):
            continue
        for h in horizons:
            if i + h >= len(ew):
                continue
            ret = float(ew.iloc[i + h] / px0 - 1)
            rows.append(
                {
                    "bucket": bucket,
                    "month": month,
                    "half": half,
                    "horizon": h,
                    "year": dt.year,
                    "ret": ret,
                }
            )
    df = pd.DataFrame(rows)
    # train/test
    out = []
    for (bucket, h), sub in df.groupby(["bucket", "horizon"]):
        tr = sub[sub["year"] <= TRAIN_END_YEAR]["ret"]
        te = sub[sub["year"] >= TEST_START_YEAR]["ret"]
        out.append(
            {
                "bucket": bucket,
                "horizon": int(h),
                "train_n": int(len(tr)),
                "train_med": float(tr.median()) if len(tr) else None,
                "test_n": int(len(te)),
                "test_med": float(te.median()) if len(te) else None,
                "all_med": float(sub["ret"].median()),
            }
        )
    return pd.DataFrame(out)


def scan_kd_crossings(m: pd.DataFrame, d: pd.DataFrame) -> pd.DataFrame:
    """Any-month first K cross below thresh each year-half → fwd to next cash ex-1."""
    rows = []
    for code, g in m.groupby("code"):
        g = g.sort_values("date").set_index("date")
        kd = yahoo_kd(g["high"], g["low"], g["close"], n=9)
        px = g["close"]
        cal = list(px.index)
        pos = {dt: i for i, dt in enumerate(cal)}
        exs = sorted(d.loc[d["code"] == code, "cash_ex_date"].dropna().unique())
        ex_aligned = []
        for ex0 in exs:
            later = [dt for dt in cal if dt >= pd.Timestamp(ex0)]
            if later:
                ex_aligned.append(later[0])
        k = kd["k"]
        for thr in (20.0, 25.0, 30.0):
            below = k < thr
            # crossing: today below, yesterday not
            cross = below & (~below.shift(1).fillna(False))
            for dt in cross[cross].index:
                i = pos[dt]
                # next ex after dt
                nxt = [ex for ex in ex_aligned if ex > dt]
                if not nxt:
                    continue
                ex = nxt[0]
                i_ex = pos[ex]
                if i_ex <= i + 5:
                    continue
                ret_ex1 = float(px.iloc[i_ex - 1] / px.iloc[i] - 1)
                # also fixed 40d
                j40 = min(len(cal) - 1, i + 40)
                ret40 = float(px.iloc[j40] / px.iloc[i] - 1)
                rows.append(
                    {
                        "code": code,
                        "year": dt.year,
                        "month": dt.month,
                        "thresh": thr,
                        "signal_dt": str(dt.date()),
                        "days_to_ex": int(i_ex - i),
                        "ret_to_ex_minus_1": ret_ex1,
                        "ret_40d": ret40,
                    }
                )
    return pd.DataFrame(rows)


def interaction_grid(m: pd.DataFrame, d: pd.DataFrame) -> pd.DataFrame:
    """Entry: first K<thresh in calendar month M; exit: max in [T-k,T-1] before next cash ex.
    Score train/test median ret and hit rate."""
    rows = []
    for code, g in m.groupby("code"):
        g = g.sort_values("date").set_index("date")
        kd = yahoo_kd(g["high"], g["low"], g["close"], n=9)
        px = g["close"]
        cal = list(px.index)
        pos = {dt: i for i, dt in enumerate(cal)}
        k = kd["k"]
        exs = []
        for ex0 in sorted(d.loc[d["code"] == code, "cash_ex_date"].dropna().unique()):
            later = [dt for dt in cal if dt >= pd.Timestamp(ex0)]
            if later:
                exs.append(later[0])
        for year in sorted({dt.year for dt in cal}):
            for month in range(1, 13):
                start = pd.Timestamp(year, month, 1)
                if month == 12:
                    end = pd.Timestamp(year, 12, 31)
                else:
                    end = pd.Timestamp(year, month + 1, 1) - pd.Timedelta(days=1)
                # next ex after month start
                nxt = [ex for ex in exs if ex > start]
                if not nxt:
                    continue
                ex = nxt[0]
                i_ex = pos[ex]
                if i_ex < 15:
                    continue
                mask = (k.index >= start) & (k.index <= end) & (k.index < ex)
                if not bool(mask.any()):
                    continue
                seg = k.loc[mask]
                for thr in (20.0, 25.0, 30.0):
                    hit = seg[seg < thr].dropna()
                    if hit.empty:
                        rows.append(
                            {
                                "code": code,
                                "year": year,
                                "month": month,
                                "thresh": thr,
                                "hit": False,
                                "ret": None,
                                "exit_k": None,
                            }
                        )
                        continue
                    sdt = hit.index[0]
                    i_sig = pos[sdt]
                    for exit_k in (5, 10, 15):
                        if i_ex <= exit_k:
                            continue
                        pre = px.iloc[i_ex - exit_k : i_ex]
                        if len(pre) < 2 or i_sig >= i_ex - exit_k:
                            continue
                        ret = float(pre.max() / px.iloc[i_sig] - 1)
                        rows.append(
                            {
                                "code": code,
                                "year": year,
                                "month": month,
                                "thresh": thr,
                                "exit_k": exit_k,
                                "hit": True,
                                "ret": ret,
                            }
                        )
    raw = pd.DataFrame(rows)
    # only hit rows with exit_k for scoring grid
    hit = raw[raw["hit"] == True].dropna(subset=["ret", "exit_k"])
    grid = []
    for (month, thr, exit_k), sub in hit.groupby(["month", "thresh", "exit_k"]):
        tr = sub[sub["year"] <= TRAIN_END_YEAR]
        te = sub[sub["year"] >= TEST_START_YEAR]
        # hit rate needs all events including misses — approximate from raw
        all_m = raw[(raw["month"] == month) & (raw["thresh"] == thr)]
        # unique code-year hit rate
        keys_all = all_m.drop_duplicates(["code", "year"])
        keys_hit = keys_all[keys_all["hit"] == True]
        tr_hr = keys_hit[keys_hit["year"] <= TRAIN_END_YEAR]
        te_hr = keys_hit[keys_hit["year"] >= TEST_START_YEAR]
        tr_all = keys_all[keys_all["year"] <= TRAIN_END_YEAR]
        te_all = keys_all[keys_all["year"] >= TEST_START_YEAR]
        grid.append(
            {
                "month": int(month),
                "thresh": float(thr),
                "exit_k": int(exit_k),
                "train_hit_rate": float(len(tr_hr) / len(tr_all)) if len(tr_all) else None,
                "test_hit_rate": float(len(te_hr) / len(te_all)) if len(te_all) else None,
                "train_med_ret": float(tr["ret"].median()) if len(tr) else None,
                "test_med_ret": float(te["ret"].median()) if len(te) else None,
                "train_n": int(len(tr)),
                "test_n": int(len(te)),
                "names_train": int(tr["code"].nunique()) if len(tr) else 0,
                "names_test": int(te["code"].nunique()) if len(te) else 0,
            }
        )
    return pd.DataFrame(grid), hit


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "outputs").mkdir(exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.9]

    print("loading ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    m, d = _prep(market, dividends)

    print("A) ex-div relative ...", flush=True)
    path_agg, local_hist, local_raw = scan_exdiv_relative(m, d)
    path_agg.to_csv(OUT / "outputs" / "exdiv_path_agg.csv", index=False)
    local_hist.to_csv(OUT / "outputs" / "exdiv_local_high_hist.csv", index=False)

    print("B) calendar half-months ...", flush=True)
    cal = scan_calendar(m)
    cal.to_csv(OUT / "outputs" / "calendar_halfmonth.csv", index=False)
    # top train+test consistent for h=40
    cal40 = cal[cal["horizon"] == 40].copy()
    cal40["ok"] = (
        cal40["train_med"].notna()
        & cal40["test_med"].notna()
        & (cal40["train_med"] > 0)
        & (cal40["test_med"] > 0)
        & (cal40["train_n"] >= 30)
        & (cal40["test_n"] >= 20)
    )
    top_cal = cal40[cal40["ok"]].sort_values("test_med", ascending=False).head(8)

    print("C) KD crossings any month ...", flush=True)
    crosses = scan_kd_crossings(m, d)
    crosses.to_csv(OUT / "outputs" / "kd_crossings.csv", index=False)
    cross_sum = []
    for thr, sub in crosses.groupby("thresh"):
        for month, s2 in sub.groupby("month"):
            tr = s2[s2["year"] <= TRAIN_END_YEAR]["ret_to_ex_minus_1"]
            te = s2[s2["year"] >= TEST_START_YEAR]["ret_to_ex_minus_1"]
            if len(tr) < 5 or len(te) < 3:
                continue
            cross_sum.append(
                {
                    "thresh": float(thr),
                    "month": int(month),
                    "train_n": int(len(tr)),
                    "train_med": float(tr.median()),
                    "test_n": int(len(te)),
                    "test_med": float(te.median()),
                }
            )
    cross_df = pd.DataFrame(cross_sum)
    if len(cross_df):
        cross_df.to_csv(OUT / "outputs" / "kd_cross_by_month.csv", index=False)
        top_cross = cross_df[
            (cross_df["train_med"] > 0) & (cross_df["test_med"] > 0)
        ].sort_values("test_med", ascending=False).head(10)
    else:
        top_cross = pd.DataFrame()

    print("D) interaction grid ...", flush=True)
    grid, hit_detail = interaction_grid(m, d)
    grid.to_csv(OUT / "outputs" / "interaction_grid.csv", index=False)
    # objective survivors: train & test med>0, hit_rate train>=0.3, test_n>=8, names>=3
    surv = grid[
        (grid["train_med_ret"] > 0.03)
        & (grid["test_med_ret"] > 0.03)
        & (grid["train_hit_rate"] >= 0.25)
        & (grid["test_n"] >= 8)
        & (grid["names_test"] >= 3)
    ].copy()
    surv["score"] = surv["test_med_ret"] * surv["test_hit_rate"].fillna(0)
    surv = surv.sort_values("score", ascending=False)
    top_surv = surv.head(15)

    # path-to-ex: best entry offsets by median to_ex_minus_1 on train/test
    path = path_agg[path_agg["metric"] == "to_ex_minus_1"].copy()
    # need year split — recompute quickly
    # use local_raw years via re-scan lite: from path file we only have agg; skip detailed
    best_t = path.sort_values("median", ascending=False).head(5)

    # Compare human May hypothesis vs top objective month for K<25 exit_k=10
    human = grid[(grid["month"] == 5) & (grid["thresh"] == 25) & (grid["exit_k"] == 10)]
    human6 = grid[(grid["month"] == 6) & (grid["thresh"] == 25) & (grid["exit_k"] == 10)]

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "FIN_OBJECTIVE_REGULARITY",
        "status": "DISCOVERY_SCREEN",
        "live_wire": False,
        "soft_frozen_keep": True,
        "split": {"train_years": f"≤{TRAIN_END_YEAR}", "test_years": f"≥{TEST_START_YEAR}"},
        "universe": FIN,
        "kd": "Yahoo K9/D9",
        "findings": {
            "exdiv_local_high_hist": local_hist.to_dict(orient="records"),
            "exdiv_best_entry_offsets_allsample": best_t.to_dict(orient="records"),
            "calendar_top_consistent_h40": top_cal.to_dict(orient="records"),
            "kd_cross_top_month_consistent": top_cross.to_dict(orient="records")
            if len(top_cross)
            else [],
            "interaction_survivors_top": top_surv.to_dict(orient="records"),
            "human_may_klt25_exit10": human.to_dict(orient="records"),
            "human_jun_klt25_exit10": human6.to_dict(orient="records"),
        },
        "verdict_bullets": [],
        "non_actions": [
            "Discovery ≠ live wire",
            "Multiple testing — survivors are hypotheses for paper NAV, not proven alpha",
            "Does not replace MIX_L75 OPERATING observe",
        ],
    }

    # craft verdict from data
    bullets = []
    # local high
    pre10 = next((x for x in local_hist.to_dict("records") if x["bin"] == "[-10,-1]"), None)
    if pre10 and pre10["share"] and pre10["share"] > 2 * pre10["expected"]:
        bullets.append(
            f"OBJECTIVE: cash-ex local highs cluster in T-10..T-1 "
            f"({pre10['share']:.0%} vs ~{pre10['expected']:.0%} expected) — supports pre-ex skip window"
        )
    if len(top_surv):
        best = top_surv.iloc[0]
        bullets.append(
            f"OBJECTIVE survivor #1: month={int(best['month'])} K<{best['thresh']:g} "
            f"exit T-{int(best['exit_k'])} · train med {best['train_med_ret']:.1%} / "
            f"test med {best['test_med_ret']:.1%} · test n={int(best['test_n'])}"
        )
        # is May in top?
        may_rank = None
        for i, (_, r) in enumerate(top_surv.iterrows(), 1):
            if int(r["month"]) in (5, 6) and float(r["thresh"]) == 25 and int(r["exit_k"]) == 10:
                may_rank = i
                break
        if may_rank:
            bullets.append(
                f"Human May/Jun K<25 exit-10 appears in survivors (rank ~{may_rank}) — not unique but not contradicted"
            )
        else:
            # check if any May in top 15
            may_any = top_surv[top_surv["month"].isin([5, 6])]
            if len(may_any):
                r = may_any.iloc[0]
                bullets.append(
                    f"Human season nearby: month={int(r['month'])} K<{r['thresh']:g} "
                    f"exit T-{int(r['exit_k'])} test med {r['test_med_ret']:.1%} (among survivors)"
                )
            else:
                bullets.append(
                    "Human May–Jun K<25 / exit-10 is NOT among top train∩test survivors — "
                    "other month×threshold combos score higher out-of-sample"
                )
    if len(top_cal):
        b0 = top_cal.iloc[0]
        bullets.append(
            f"Calendar: strongest consistent 40d bucket {b0['bucket']} "
            f"(train med {b0['train_med']:.1%} / test {b0['test_med']:.1%})"
        )
    bullets.append(
        "Caution: grid search overfits; treat survivors as paper hypotheses only"
    )
    payload["verdict_bullets"] = bullets

    (OUT / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    RESEARCH.joinpath("FIN_OBJECTIVE_REGULARITY.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    lines = [
        "# FIN objective regularity discovery",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Status: **DISCOVERY_SCREEN** · Soft-Frozen **KEEP** · live wire **false**",
        f"Split: train ≤{TRAIN_END_YEAR} · test ≥{TEST_START_YEAR} · Yahoo K9/D9 · FIN `{', '.join(FIN)}`",
        "",
        "## What this is",
        "",
        "Data-driven scan **without** presupposing May–Jun. Your observation is checked against survivors.",
        "",
        "## A) Ex-div local high",
        "",
        "| bin | share | expected |",
        "|---|---:|---:|",
    ]
    for r in local_hist.to_dict("records"):
        lines.append(f"| `{r['bin']}` | {r['share']:.1%} | {r['expected']:.1%} |")
    lines += [
        "",
        "## B) Calendar half-months (40d fwd, train&test both >0)",
        "",
        "| bucket | train med | test med |",
        "|---|---:|---:|",
    ]
    for r in top_cal.to_dict("records")[:6]:
        lines.append(
            f"| `{r['bucket']}` | {r['train_med']:.2%} | {r['test_med']:.2%} |"
        )
    lines += [
        "",
        "## C–D) Interaction survivors (month × K×thresh × exit T-k)",
        "",
        "Filter: train&test med ret >3%, train hit≥25%, test n≥8, ≥3 names.",
        "",
        "| month | K< | exit | train med | test med | test n |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for r in top_surv.to_dict("records")[:12]:
        lines.append(
            f"| {int(r['month'])} | {r['thresh']:g} | T-{int(r['exit_k'])} | "
            f"{r['train_med_ret']:.1%} | {r['test_med_ret']:.1%} | {int(r['test_n'])} |"
        )
    lines += ["", "## vs your observation", ""]
    if len(human):
        r = human.iloc[0]
        lines.append(
            f"- May × K<25 × exit T-10: train med **{r['train_med_ret']:.1%}** "
            f"(n={int(r['train_n'])}) · test **{r['test_med_ret']:.1%}** (n={int(r['test_n'])}) · "
            f"hit train {r['train_hit_rate']:.0%} / test {r['test_hit_rate']:.0%}"
        )
    if len(human6):
        r = human6.iloc[0]
        lines.append(
            f"- Jun × K<25 × exit T-10: train med **{r['train_med_ret']:.1%}** · "
            f"test **{r['test_med_ret']:.1%}**"
        )
    lines += ["", "## Verdict", ""]
    lines.extend(f"- {b}" for b in bullets)
    lines += [
        "",
        "## Hard rules",
        "",
        "- Soft-Frozen KEEP · no live wire · discovery ≠ observe OPEN",
        "",
        f"Repro: `{OUT.relative_to(ROOT)}/`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "REPORT.md").write_text(md)
    RESEARCH.joinpath("FIN_OBJECTIVE_REGULARITY.md").write_text(md)
    print(json.dumps({"status": payload["status"], "bullets": bullets, "n_survivors": int(len(surv))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
