#!/usr/bin/env python3
"""FIN post-exdiv autumn low + Yahoo K9 paper probe (RESEARCH ONLY).

Human pattern: ~late Oct → early Dec may see post-ex-div local lows on FIN.
Contrasts live KD_OPT (Apr–May pre-ex accumulation).

Soft-Frozen KEEP · live e21 KD_OPT untouched · no cutover from this probe.
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
OUT = ROOT / "repro/fin-post-exdiv-autumn-probe-20260909"
RESEARCH = ROOT / "research/ops"

# Autumn window (human: 10月底–12月初)
SEASON_START = (10, 20)
SEASON_END = (12, 10)
POST_WIN = (1, 100)  # trading days after ex for local-low study


def _cash_ex_events(div: pd.DataFrame, codes: list[str]) -> pd.DataFrame:
    d = div.copy()
    d["code"] = d["code"].astype(str)
    d["cash_ex_date"] = pd.to_datetime(d["cash_ex_date"], errors="coerce")
    d = d[d["code"].isin(codes) & d["cash_ex_date"].notna()]
    return d[["code", "cash_ex_date"]].drop_duplicates()


def _align_ex_on_calendar(cal: list[pd.Timestamp], ex0: pd.Timestamp) -> pd.Timestamp | None:
    later = [dt for dt in cal if dt >= pd.Timestamp(ex0)]
    return later[0] if later else None


def _in_autumn(dt: pd.Timestamp) -> bool:
    start = pd.Timestamp(dt.year, SEASON_START[0], SEASON_START[1])
    end = pd.Timestamp(dt.year, SEASON_END[0], SEASON_END[1])
    return start <= dt <= end


def local_low_study(market: pd.DataFrame, events: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    """Share of post-ex local close/low minima that fall in Oct20–Dec10."""
    rows = []
    lo_d, hi_d = POST_WIN
    for code, g in market.groupby("code"):
        g = g.sort_values("date").set_index("date")
        px = g["close"]
        lo = g["low"]
        cal = list(px.index)
        pos = {dt: i for i, dt in enumerate(cal)}
        for ex0 in events.loc[events["code"] == code, "cash_ex_date"]:
            ex = _align_ex_on_calendar(cal, ex0)
            if ex is None:
                continue
            i = pos[ex]
            a, b = i + lo_d, i + hi_d
            if a >= len(cal) or b >= len(cal):
                continue
            for kind, series in (("close", px), ("low", lo)):
                window = series.iloc[a : b + 1]
                j = a + int(np.nanargmin(window.to_numpy(dtype=float)))
                dt = cal[j]
                dist = j - i
                rows.append(
                    {
                        "code": code,
                        "ex": str(ex.date()),
                        "kind": kind,
                        "low_date": str(dt.date()),
                        "dist": int(dist),
                        "in_autumn": bool(_in_autumn(dt)),
                        "month": int(dt.month),
                    }
                )
    df = pd.DataFrame(rows)
    # baseline: autumn trading-day share within post window is calendar-dependent;
    # use empirical share of all post-window days that land in autumn.
    baseline_rows = []
    for code, g in market.groupby("code"):
        g = g.sort_values("date").set_index("date")
        cal = list(g.index)
        pos = {dt: i for i, dt in enumerate(cal)}
        for ex0 in events.loc[events["code"] == code, "cash_ex_date"]:
            ex = _align_ex_on_calendar(cal, ex0)
            if ex is None:
                continue
            i = pos[ex]
            a, b = i + lo_d, i + hi_d
            if b >= len(cal):
                continue
            for dt in cal[a : b + 1]:
                baseline_rows.append(_in_autumn(dt))
    baseline = float(np.mean(baseline_rows)) if baseline_rows else None
    out = {"baseline_share_autumn_in_post_window": baseline, "n_events": int(len(df) // 2), "by_kind": {}}
    for kind, sub in df.groupby("kind"):
        share = float(sub["in_autumn"].mean())
        out["by_kind"][kind] = {
            "n": int(len(sub)),
            "share_in_autumn_Oct20_Dec10": share,
            "lift_vs_baseline": (share / baseline) if baseline else None,
            "median_dist_to_low": float(sub["dist"].median()),
            "by_code": {c: float(s["in_autumn"].mean()) for c, s in sub.groupby("code")},
            "by_month": {int(m): int(n) for m, n in sub["month"].value_counts().sort_index().items()},
        }
    return out, df


def autumn_kd_study(
    market: pd.DataFrame,
    events: pd.DataFrame,
    *,
    thresh: float,
    hold_days: int = 40,
) -> tuple[dict, pd.DataFrame]:
    """After cash-ex, first autumn K9 < thresh → forward hold_days return vs random."""
    rng = np.random.default_rng(1)
    hits: list[dict] = []
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
            year = ex.year
            start = pd.Timestamp(year, SEASON_START[0], SEASON_START[1])
            end = pd.Timestamp(year, SEASON_END[0], SEASON_END[1])
            win_start = max(start, ex + pd.Timedelta(days=1))
            later = [dt for dt in cal if dt >= win_start]
            if not later or later[0] > end:
                continue
            win_start = later[0]
            season_days = [dt for dt in cal if win_start <= dt <= end]
            if len(season_days) < 5:
                continue
            k = kd["k"].reindex(cal)
            seg = k.loc[season_days]
            hit = seg[seg < float(thresh)].dropna()
            if hit.empty:
                continue
            sig = hit.index[0]
            i_sig = pos[sig]
            i_end = min(i_sig + hold_days, len(cal) - 1)
            if i_end <= i_sig:
                continue
            ret = float(px.iloc[i_end] / px.iloc[i_sig] - 1.0)
            # random same-window day
            rnd = rng.choice(season_days)
            i_r = pos[rnd]
            i_re = min(i_r + hold_days, len(cal) - 1)
            rnd_ret = float(px.iloc[i_re] / px.iloc[i_r] - 1.0) if i_re > i_r else None
            # local-low OK: signal within 10 days of window close argmin
            wpx = px.loc[season_days]
            low_dt = wpx.idxmin()
            near_low = abs(pos[sig] - pos[low_dt]) <= 10
            hits.append(
                {
                    "code": code,
                    "ex": str(ex.date()),
                    "sig": str(sig.date()),
                    "ret_hold": ret,
                    "rnd_ret": rnd_ret,
                    "near_season_low": bool(near_low),
                    "k_at_sig": float(k.loc[sig]),
                }
            )
    df = pd.DataFrame(hits)
    if df.empty:
        return {"n_hits": 0, "hit_rate_note": "no K triggers in autumn post-ex"}, df
    # event count with season after ex
    n_eligible = 0
    for code, g in market.groupby("code"):
        g = g.sort_values("date").set_index("date")
        cal = list(g.index)
        for ex0 in events.loc[events["code"] == code, "cash_ex_date"]:
            ex = _align_ex_on_calendar(cal, ex0)
            if ex is None:
                continue
            year = ex.year
            start = pd.Timestamp(year, SEASON_START[0], SEASON_START[1])
            end = pd.Timestamp(year, SEASON_END[0], SEASON_END[1])
            if any(max(start, ex + pd.Timedelta(days=1)) <= dt <= end for dt in cal):
                n_eligible += 1
    out = {
        "thresh": thresh,
        "hold_days": hold_days,
        "n_hits": int(len(df)),
        "n_eligible_events": int(n_eligible),
        "hit_rate": float(len(df) / n_eligible) if n_eligible else None,
        "med_ret_hold": float(df["ret_hold"].median()),
        "med_rnd_ret": float(df["rnd_ret"].dropna().median()) if df["rnd_ret"].notna().any() else None,
        "edge_vs_random_pp": None,
        "share_near_season_low": float(df["near_season_low"].mean()),
        "by_code": {
            c: {"n": int(len(s)), "med_ret": float(s["ret_hold"].median())}
            for c, s in df.groupby("code")
        },
    }
    if out["med_rnd_ret"] is not None:
        out["edge_vs_random_pp"] = (out["med_ret_hold"] - out["med_rnd_ret"]) * 100
    return out, df


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "outputs").mkdir(exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.5, 0.95]

    print("loading market + dividends ...", flush=True)
    market = load_market()
    market = market[market["code"].isin(FIN)].copy()
    dividends = load_dividends()
    events = _cash_ex_events(dividends, FIN)

    print("local-low autumn clustering ...", flush=True)
    local, local_df = local_low_study(market, events)
    local_df.to_csv(OUT / "outputs/local_low_dist.csv", index=False)

    kd_rules = {}
    for thresh in (20.0, 25.0, 30.0):
        print(f"autumn KD K<{thresh} ...", flush=True)
        summary, hits = autumn_kd_study(market, events, thresh=thresh, hold_days=40)
        kd_rules[f"Klt{int(thresh)}"] = summary
        hits.to_csv(OUT / "outputs" / f"hits_Klt{int(thresh)}.csv", index=False)

    primary = "Klt25"
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "FIN_POST_EXDIV_AUTUMN_PROBE",
        "status": "PAPER_PROBE",
        "live_wire": False,
        "soft_frozen_keep": True,
        "live_kd_opt_unchanged": True,
        "season": {"start": list(SEASON_START), "end": list(SEASON_END)},
        "kd": "Yahoo K9/D9",
        "local_low_post_ex": local,
        "autumn_kd": kd_rules,
        "primary_observe": primary,
        "verdict": (
            f"Post-ex local-low autumn share (close)="
            f"{local['by_kind'].get('close', {}).get('share_in_autumn_Oct20_Dec10')}; "
            f"primary {primary} med hold ret="
            f"{kd_rules.get(primary, {}).get('med_ret_hold')} "
            f"edge_pp={kd_rules.get(primary, {}).get('edge_vs_random_pp')}. "
            "Soft-Frozen KEEP · live KD_OPT untouched · no cutover."
        ),
    }
    # fix accidental
    payload["soft_frozen_keep"] = True

    (OUT / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    RESEARCH.joinpath("FIN_POST_EXDIV_AUTUMN_PROBE.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    close = local["by_kind"].get("close", {})
    lines = [
        "# FIN post-exdiv autumn low — paper probe",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Status: **PAPER_PROBE** · Soft-Frozen **KEEP** · live wire **false** · live **KD_OPT untouched**",
        "",
        "## Season",
        "",
        f"- Window: **{SEASON_START[0]}/{SEASON_START[1]} – {SEASON_END[0]}/{SEASON_END[1]}** (after cash-ex)",
        "- KD: Yahoo **K9/D9**",
        "",
        "## Pattern A — post-ex local low in autumn?",
        "",
        f"Window trading days **T+{POST_WIN[0]}..T+{POST_WIN[1]}** close argmin → share in Oct20–Dec10:",
        f"**{100 * close.get('share_in_autumn_Oct20_Dec10', 0):.1f}%** "
        f"(baseline ~{100 * (local.get('baseline_share_autumn_in_post_window') or 0):.1f}%, "
        f"lift ×{close.get('lift_vs_baseline')})",
        "",
        f"Median dist ex→low: **{close.get('median_dist_to_low')}** sessions",
        "",
        "## Pattern B — autumn Yahoo K9 → +40d hold",
        "",
        "| rule | hit rate | med ret | vs random med | near season low |",
        "|---|---:|---:|---:|---:|",
    ]
    for rid, s in kd_rules.items():
        edge = s.get("edge_vs_random_pp")
        lines.append(
            f"| `{rid}` | {100 * (s.get('hit_rate') or 0):.1f}% | "
            f"{100 * (s.get('med_ret_hold') or 0):.2f}% | "
            f"{edge if edge is None else f'{edge:+.2f}pp'} | "
            f"{100 * (s.get('share_near_season_low') or 0):.1f}% |"
        )
    p = kd_rules.get(primary, {})
    lines += [
        "",
        f"### Primary line: `{primary}`",
        "",
        f"- Hits: **{p.get('n_hits')}** / {p.get('n_eligible_events')} eligible post-ex seasons",
        f"- Median +40d ret: **{100 * (p.get('med_ret_hold') or 0):.2f}%**",
        f"- Edge vs random same window: **{p.get('edge_vs_random_pp')} pp**",
        "",
        "## Implications",
        "",
        "- Distinct from live **KD_OPT** (Apr–May pre-ex)",
        "- Follow-up NAV: `FIN_POST_EXDIV_AUTUMN_NAV.md` if edge warrants",
        "",
        "## Hard rules",
        "",
        "- Soft-Frozen KEEP · no live wire · no cutover from this probe",
        "- Does not change live `KD_OPT`",
        "",
        f"Repro: `{OUT.relative_to(ROOT)}/`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "REPORT.md").write_text(md)
    RESEARCH.joinpath("FIN_POST_EXDIV_AUTUMN_PROBE.md").write_text(md)
    print(json.dumps({"status": "PAPER_PROBE", "primary": primary, "local_close": close, "kd": kd_rules.get(primary)}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
