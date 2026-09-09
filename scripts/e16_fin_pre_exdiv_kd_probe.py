#!/usr/bin/env python3
"""FIN pre-exdiv + Yahoo K9/D9 seasonal paper probe (RESEARCH ONLY).

Human pattern:
  1) Local highs cluster in cash-ex T-10..T-1 trading days
  2) Mid-May..early-Jun Yahoo K9 near/below oversold → local low, then
     rally into (1) until pre-exdiv

KD params match Yahoo TW chart labels K9/D9 (RSV n=9, recursive 1/3 K/D)
— not SMA(9,9). Soft-Frozen KEEP · live e21 untouched · no cutover.
"""
from __future__ import annotations

import argparse
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
OUT = ROOT / "repro/fin-pre-exdiv-kd-probe-20260909"
RESEARCH = ROOT / "research/ops"

SEASON_START = (5, 15)  # May 15
SEASON_END = (6, 10)  # Jun 10
PRE_EX_LO, PRE_EX_HI = -10, -1  # T-10..T-1
LOCAL_WIN = (-60, 20)  # [T-60, T+20] for local-high study


def _cash_ex_events(div: pd.DataFrame, codes: list[str]) -> pd.DataFrame:
    d = div.copy()
    d["code"] = d["code"].astype(str)
    d["cash_ex_date"] = pd.to_datetime(d["cash_ex_date"], errors="coerce")
    d = d[d["code"].isin(codes) & d["cash_ex_date"].notna()]
    return d[["code", "cash_ex_date"]].drop_duplicates()


def _align_ex_on_calendar(cal: list[pd.Timestamp], ex0: pd.Timestamp) -> pd.Timestamp | None:
    later = [dt for dt in cal if dt >= pd.Timestamp(ex0)]
    return later[0] if later else None


def local_high_study(market: pd.DataFrame, events: pd.DataFrame) -> dict:
    """Share of local close/high maxima in [T-60,T+20] that fall in T-10..T-1."""
    rows = []
    pre, post = LOCAL_WIN
    for code, g in market.groupby("code"):
        g = g.sort_values("date").set_index("date")
        px = g["close"]
        hi = g["high"]
        cal = list(px.index)
        pos = {dt: i for i, dt in enumerate(cal)}
        for ex0 in events.loc[events["code"] == code, "cash_ex_date"]:
            ex = _align_ex_on_calendar(cal, ex0)
            if ex is None:
                continue
            i = pos[ex]
            lo_i, hi_i = i + pre, i + post
            if lo_i < 0 or hi_i >= len(cal):
                continue
            for kind, series in (("close", px), ("high", hi)):
                window = series.iloc[lo_i : hi_i + 1]
                dist = (lo_i + int(np.nanargmax(window.to_numpy(dtype=float)))) - i
                rows.append(
                    {
                        "code": code,
                        "ex": str(ex.date()),
                        "kind": kind,
                        "dist": int(dist),
                        "in_pre_ex": PRE_EX_LO <= dist <= PRE_EX_HI,
                    }
                )
    df = pd.DataFrame(rows)
    baseline = (PRE_EX_HI - PRE_EX_LO + 1) / (post - pre + 1)
    out = {"baseline_share": baseline, "n": int(len(df) // 2), "by_kind": {}}
    for kind, sub in df.groupby("kind"):
        out["by_kind"][kind] = {
            "n": int(len(sub)),
            "share_T10_T1": float(sub["in_pre_ex"].mean()),
            "lift_vs_baseline": float(sub["in_pre_ex"].mean() / baseline) if baseline else None,
            "share_T20_T1": float(sub["dist"].between(-20, -1).mean()),
            "share_after_1_10": float(sub["dist"].between(1, 10).mean()),
            "by_code": {
                c: float(s["in_pre_ex"].mean()) for c, s in sub.groupby("code")
            },
        }
    return out, df


def seasonal_kd_study(
    market: pd.DataFrame,
    events: pd.DataFrame,
    *,
    rule: str,
    thresh: float,
) -> tuple[dict, pd.DataFrame]:
    """May15–Jun10 Yahoo K9 signal → return to pre-ex [T-10,T-1] high."""
    rng = np.random.default_rng(0)
    hits: list[dict] = []
    misses = 0
    base_rets: list[float] = []

    for code, g in market.groupby("code"):
        g = g.sort_values("date").set_index("date")
        kd = yahoo_kd(g["high"], g["low"], g["close"], n=9)
        px = g["close"]
        cal = list(px.index)
        pos = {dt: i for i, dt in enumerate(cal)}
        for ex0 in events.loc[events["code"] == code, "cash_ex_date"]:
            ex = _align_ex_on_calendar(cal, ex0)
            if ex is None:
                continue
            i_ex = pos[ex]
            year = ex.year
            start = pd.Timestamp(year, SEASON_START[0], SEASON_START[1])
            end = pd.Timestamp(year, SEASON_END[0], SEASON_END[1])
            if ex < start:
                continue
            mask = (px.index >= start) & (px.index <= end) & (px.index < ex)
            if int(mask.sum()) < 5 or i_ex < 10:
                continue
            seg_k = kd["k"].loc[mask]
            days = list(px.loc[mask].index)
            pre = px.iloc[i_ex - 10 : i_ex]
            pre_high = float(pre.max())
            pre_high_dt = pre.idxmax()
            for _ in range(15):
                sdt = days[int(rng.integers(0, len(days)))]
                base_rets.append(pre_high / float(px.loc[sdt]) - 1.0)

            if rule == "le":
                hit = seg_k <= thresh
            else:
                hit = seg_k < thresh
            hit = hit.fillna(False)
            if not bool(hit.any()):
                misses += 1
                continue
            sdt = hit[hit].index[0]
            deep = seg_k.loc[hit].idxmin()
            i_sig = pos[sdt]
            neigh = px.iloc[max(0, i_sig - 5) : min(len(cal) - 1, i_sig + 5) + 1]
            local_ok = float(px.loc[sdt]) <= float(neigh.min()) * 1.005
            ret = pre_high / float(px.loc[sdt]) - 1.0
            ret_ex1 = float(px.iloc[i_ex - 1]) / float(px.loc[sdt]) - 1.0
            hits.append(
                {
                    "code": code,
                    "year": int(year),
                    "ex": str(ex.date()),
                    "signal_dt": str(sdt.date()),
                    "signal_k": float(kd["k"].loc[sdt]),
                    "signal_d": float(kd["d"].loc[sdt]),
                    "signal_rsv": float(kd["rsv"].loc[sdt]) if pd.notna(kd["rsv"].loc[sdt]) else None,
                    "deep_dt": str(deep.date()),
                    "deep_k": float(kd["k"].loc[deep]),
                    "is_local_low_ok": bool(local_ok),
                    "pre_ex_high_dt": str(pre_high_dt.date()),
                    "ret_to_pre_ex_high": float(ret),
                    "ret_to_ex_minus_1": float(ret_ex1),
                    "days_sig_to_ex": int(i_ex - i_sig),
                }
            )

    H = pd.DataFrame(hits)
    n = len(H) + misses
    B = pd.Series(base_rets, dtype=float)
    summary = {
        "rule": f"K{rule}{thresh:g}",
        "kd": "Yahoo K9/D9 recursive (RSV n=9, α=1/3)",
        "season_window": f"{SEASON_START[0]}/{SEASON_START[1]}–{SEASON_END[0]}/{SEASON_END[1]}",
        "exit_measure": "max close in cash-ex T-10..T-1",
        "n_events": int(n),
        "n_hits": int(len(H)),
        "hit_rate": float(len(H) / n) if n else None,
        "median_ret_to_pre_ex_high": float(H["ret_to_pre_ex_high"].median()) if len(H) else None,
        "mean_ret_to_pre_ex_high": float(H["ret_to_pre_ex_high"].mean()) if len(H) else None,
        "median_ret_to_ex_minus_1": float(H["ret_to_ex_minus_1"].median()) if len(H) else None,
        "share_ret_gt_0": float((H["ret_to_pre_ex_high"] > 0).mean()) if len(H) else None,
        "share_ret_gt_10pct": float((H["ret_to_pre_ex_high"] > 0.10).mean()) if len(H) else None,
        "share_ret_gt_20pct": float((H["ret_to_pre_ex_high"] > 0.20).mean()) if len(H) else None,
        "share_local_low_ok": float(H["is_local_low_ok"].mean()) if len(H) else None,
        "baseline_random_same_window_median": float(B.median()) if len(B) else None,
        "edge_vs_random_median_pp": (
            float((H["ret_to_pre_ex_high"].median() - B.median()) * 100)
            if len(H) and len(B)
            else None
        ),
        "by_code_median_ret": (
            {c: float(s["ret_to_pre_ex_high"].median()) for c, s in H.groupby("code")}
            if len(H)
            else {}
        ),
    }
    return summary, H


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--thresh-primary", type=float, default=25.0, help="primary K threshold (default K<25)")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "outputs").mkdir(exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.9]

    print("loading market + dividends ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    m = market[market["code"].astype(str).isin(FIN)].copy()
    m["date"] = pd.to_datetime(m["date"])
    m["code"] = m["code"].astype(str)
    for c in ("open", "high", "low", "close"):
        m[c] = pd.to_numeric(m[c], errors="coerce")
    events = _cash_ex_events(dividends, FIN)

    print("local-high study ...", flush=True)
    local_sum, local_df = local_high_study(m, events)
    local_df.to_csv(OUT / "outputs" / "local_high_dist.csv", index=False)

    print("seasonal Yahoo K9/D9 study ...", flush=True)
    grids = []
    hit_tables = {}
    for rule, thr in (("le", 20.0), ("lt", 20.0), ("lt", float(args.thresh_primary))):
        summary, hits = seasonal_kd_study(m, events, rule=rule, thresh=thr)
        grids.append(summary)
        key = summary["rule"]
        hit_tables[key] = hits
        hits.to_csv(OUT / "outputs" / f"hits_{key}.csv", index=False)

    # primary = K<thresh (default K<25)
    primary = next(g for g in grids if g["rule"] == f"Klt{args.thresh_primary:g}")
    primary_hits = hit_tables[primary["rule"]]

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "FIN_PRE_EXDIV_KD_PROBE",
        "status": "PAPER_PROBE",
        "live_wire": False,
        "soft_frozen_keep": True,
        "cutover_authorized": False,
        "universe": FIN,
        "kd_spec": {
            "source": "Yahoo Finance Taiwan chart labels K9/D9",
            "rsv_n": 9,
            "k": "K_t = (2/3)*K_{t-1} + (1/3)*RSV_t",
            "d": "D_t = (2/3)*D_{t-1} + (1/3)*K_t",
            "j": "J = 3K - 2D (Yahoo often shows as K3D2)",
            "not": "SMA(9) of RSV / SMA(9,9,9)",
        },
        "pattern": {
            "season": "May 15 – Jun 10 Yahoo K9 oversold",
            "pre_exdiv_high": "cash-ex T-10..T-1 trading days",
            "note": "Current FIN_RS_SOFT_TILT_EXDIV skip-buy is ex-date only — later than this window",
        },
        "local_high": local_sum,
        "kd_grid": grids,
        "primary": primary,
        "implications": [
            "Pre-exdiv high clustering is strong on FIN names — skip-buy on ex-date alone is too late/narrow",
            "Yahoo K9 seasonal signal has modest edge vs random same-window day; useful as observe probe not live knife",
            "Next paper option: PRE_EXDIV_T10 reduce/skip buy, optional May–Jun K9<25 add bias — still Soft-Frozen KEEP",
        ],
        "non_actions": [
            "No Soft-Frozen flip",
            "No live e21 within-sleeve wire",
            "Does not replace MIX_L75 / RS_EXDIV OPERATING observe",
        ],
    }

    (OUT / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    RESEARCH.joinpath("FIN_PRE_EXDIV_KD_PROBE.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    lh = local_sum["by_kind"]["close"]
    lines = [
        "# FIN pre-exdiv + Yahoo K9/D9 — paper probe",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Status: **PAPER_PROBE** · Soft-Frozen **KEEP** · live wire **false**",
        "",
        "## KD spec (match Yahoo TW chart)",
        "",
        "- Labels: **K9 / D9** (RSV lookback **9**)",
        "- `K = ⅔·Kprev + ⅓·RSV` · `D = ⅔·Dprev + ⅓·K` · `J = 3K − 2D`",
        "- **Not** SMA(9)/SMA(9,9)",
        "",
        "## Pattern A — local high near cash ex-div",
        "",
        f"Window `[T{LOCAL_WIN[0]}, T+{LOCAL_WIN[1]}]` close argmax → share in **T{PRE_EX_LO}..T{PRE_EX_HI}**:",
        f"**{lh['share_T10_T1']:.1%}** (baseline ~{local_sum['baseline_share']:.1%}, lift ×{lh['lift_vs_baseline']:.1f})",
        "",
        "## Pattern B — May15–Jun10 Yahoo K9 → pre-ex high",
        "",
        "| rule | hit rate | med ret→pre-ex high | vs random med | local-low OK |",
        "|---|---:|---:|---:|---:|",
    ]
    for g in grids:
        lines.append(
            f"| `{g['rule']}` | {g['hit_rate']:.1%} | {g['median_ret_to_pre_ex_high']:.1%} | "
            f"{g['edge_vs_random_median_pp']:+.2f}pp | {g['share_local_low_ok']:.1%} |"
        )
    lines += [
        "",
        f"### Primary observe line: `{primary['rule']}`",
        "",
        f"- Hits: **{primary['n_hits']}** / {primary['n_events']} events",
        f"- Median ret to pre-ex high: **{primary['median_ret_to_pre_ex_high']:.1%}**",
        f"- Edge vs random same window: **{primary['edge_vs_random_median_pp']:+.2f}pp**",
        "",
        "## Implications",
        "",
    ]
    lines.extend(f"- {x}" for x in payload["implications"])
    lines += [
        "",
        "## Hard rules",
        "",
        "- Soft-Frozen KEEP · no live wire · no cutover from this probe",
        "- Does not replace OPERATING FIN triad (`EQUAL` ∥ `RS_EXDIV` ∥ `MIX_L75`)",
        "",
        f"Repro: `{OUT.relative_to(ROOT)}/`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "REPORT.md").write_text(md)
    RESEARCH.joinpath("FIN_PRE_EXDIV_KD_PROBE.md").write_text(md)

    # short primary hits preview
    if len(primary_hits):
        preview = primary_hits.sort_values("ret_to_pre_ex_high", ascending=False).head(12)
        preview.to_csv(OUT / "outputs" / "primary_hits_top.csv", index=False)

    print(
        json.dumps(
            {
                "status": payload["status"],
                "primary": {
                    "rule": primary["rule"],
                    "hit_rate": primary["hit_rate"],
                    "med_ret": primary["median_ret_to_pre_ex_high"],
                    "edge_pp": primary["edge_vs_random_median_pp"],
                },
                "local_high_share_T10_T1": lh["share_T10_T1"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
