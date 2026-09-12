#!/usr/bin/env python3
"""Stage A paper screen: 0050 ETF ex-calendar timing vs BUY_HOLD_0050 / LIVE_STACK.

Charter: research/ops/ETF_EX_CALENDAR_STAGE_A_CHARTER.md

Mechanism: rules-based long windows from MONTH_PROXY (Jan/Jul post-2016;
Oct pre-2016) or EXACT_EX cash_ex_date [T-N, T-1]. Soft-Frozen / KD_OPT /
TEL_EQUAL / E45 / Soft-assist / sleeve-tilt observes UNCHANGED. No live wire.
No inventing announcement_date.
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
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, load_market, window_stats
from e50_early_stack_combined_nav import FIN, e16_features, simulate_core
from portfolio_capital import DEFAULT_CAPITAL
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp
from soft_assist_helpers import LIVE_KD
from tw_share_lots import BOARD_LOT
from within_sleeve_alloc import (
    FIN_PRE_EXDIV_KD,
    TEL_EQUAL,
    build_kd_season_tilt_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/etf-ex-calendar"
OPS = ROOT / "research/ops"
DIV_EVENTS = ROOT / "data/dividend_events/e22_dividend_events.csv"
YUANTA_0050 = ROOT / "research/ops/yuanta_etf_div_0050.json"
CAPITAL = float(DEFAULT_CAPITAL)
LOT = BOARD_LOT
TRAIL_ALERT_PP = 3.0
TRAIL_PAUSE_PP = 5.0
PROXY_CUTOVER = pd.Timestamp("2016-01-01")
SLEEVE_COLS = ["Financial", "Telecom", "0050"]


def tip_gate(base_nav: pd.DataFrame, chal_nav: pd.DataFrame, asof: pd.Timestamp) -> dict:
    out = {}
    asof = pd.Timestamp(asof)
    b_dates = pd.to_datetime(base_nav["date"])
    c_dates = pd.to_datetime(chal_nav["date"])
    for wname, start in (
        ("ytd", pd.Timestamp(asof.year, 1, 1)),
        ("trailing_1y", asof - pd.Timedelta(days=365)),
    ):
        b = base_nav[(b_dates >= start) & (b_dates <= asof)].reset_index(drop=True)
        c = chal_nav[(c_dates >= start) & (c_dates <= asof)].reset_index(drop=True)
        if len(b) < 20 or len(c) < 20:
            out[wname] = {"giveback_pp": None, "gate": "INSUFFICIENT"}
            continue
        bn = b["nav"] / float(b["nav"].iloc[0])
        cn = c["nav"] / float(c["nav"].iloc[0])
        years = (len(b) - 1) / 252.0
        bc = float(bn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        cc = float(cn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        gb = None if bc is None or cc is None else (bc - cc) * 100
        gate = "PASS"
        if gb is not None and gb > TRAIL_PAUSE_PP:
            gate = "PAUSE_REVIEW"
        elif gb is not None and gb > TRAIL_ALERT_PP:
            gate = "ALERT"
        out[wname] = {
            "giveback_pp": None if gb is None else float(gb),
            "gate": gate,
            "rel_nav": float(cn.iloc[-1] / bn.iloc[-1]),
        }
    return out


def score_vs_base(base_stats: dict, chal_stats: dict) -> dict:
    mdd_pp = mdd_delta_pp(base_stats.get("max_drawdown"), chal_stats.get("max_drawdown"))
    cagr_pp = cagr_delta_pp(
        base_stats.get("cagr"), chal_stats.get("cagr"), missing_as_zero=True
    )
    giveback = abs(float(cagr_pp)) if cagr_pp is not None else 9.0
    return {
        "mdd_improve_pp": float(mdd_pp),
        "cagr_giveback_pp": float(cagr_pp) if cagr_pp is not None else None,
        "score": float(mdd_pp) - 0.5 * giveback,
    }


def tip_is_clean(tip: dict) -> bool:
    return tip["ytd"]["gate"] == "PASS" and tip["trailing_1y"]["gate"] == "PASS"


def sim_book(market, target, regime, dividends, scores, buy_ok, schedule=None):
    return simulate_core(
        market,
        target,
        regime,
        dividends,
        apply_e22=True,
        apply_stock_div=True,
        capital=CAPITAL,
        lot_size=LOT,
        financial_alloc=FIN_PRE_EXDIV_KD,
        telecom_alloc=TEL_EQUAL,
        fin_name_scores=scores,
        fin_buy_ok=buy_ok,
        sleeve_weight_schedule=schedule,
    )


def load_0050_ex_dates() -> pd.DatetimeIndex:
    dates: list[pd.Timestamp] = []
    if DIV_EVENTS.exists():
        ev = pd.read_csv(DIV_EVENTS, dtype={"code": str})
        sub = ev[ev["code"].astype(str).isin(["50", "0050", "0050.TW"])].copy()
        if "cash_ex_date" in sub.columns:
            dates.extend(
                pd.to_datetime(sub["cash_ex_date"], errors="coerce").dropna().tolist()
            )
    if YUANTA_0050.exists():
        payload = json.loads(YUANTA_0050.read_text(encoding="utf-8"))
        rows = payload.get("rows") or payload.get("events") or []
        for row in rows:
            raw = row.get("cash_ex_date") or row.get("ex_date")
            if not raw:
                continue
            ts = pd.to_datetime(raw, errors="coerce")
            if pd.notna(ts):
                dates.append(pd.Timestamp(ts))
    if not dates:
        raise SystemExit("No 0050 cash_ex_date rows found in E22 / Yuanta inputs")
    return pd.DatetimeIndex(sorted({pd.Timestamp(d).normalize() for d in dates}))


def month_proxy_mask(cal: pd.DatetimeIndex, w_days: int) -> pd.Series:
    cal = pd.DatetimeIndex(cal).sort_values()
    flag = pd.Series(False, index=cal)
    for y in sorted({int(ts.year) for ts in cal}):
        months = (1, 7) if y >= PROXY_CUTOVER.year else (10,)
        for m in months:
            month_days = cal[(cal.year == y) & (cal.month == m)]
            if len(month_days) == 0:
                continue
            flag.loc[month_days[: int(w_days)]] = True
    return flag


def exact_ex_mask(
    cal: pd.DatetimeIndex,
    ex_dates: pd.DatetimeIndex,
    n_before: int,
    hold_thru: int = 0,
) -> pd.Series:
    cal = pd.DatetimeIndex(cal).sort_values()
    flag = pd.Series(False, index=cal)
    pos = {ts: i for i, ts in enumerate(cal)}
    for ex in ex_dates:
        ex = pd.Timestamp(ex).normalize()
        if ex in pos:
            i_ex = pos[ex]
        else:
            later = cal[cal >= ex]
            if len(later) == 0:
                continue
            i_ex = pos[pd.Timestamp(later[0])]
        i0 = max(0, i_ex - int(n_before))
        i1 = i_ex - 1
        if hold_thru > 0:
            i1 = min(len(cal) - 1, i_ex + int(hold_thru))
        if i1 < i0:
            continue
        flag.iloc[i0 : i1 + 1] = True
    return flag


def schedule_from_mask(
    index: pd.DatetimeIndex, active: pd.Series, family: str
) -> pd.DataFrame:
    """CAL_LONG_0050: 100% 0050 in window else cash.
    CAL_OVER_BH: 100% 0050 always (≡ BUY_HOLD under long-only Stage A rules).
    """
    active = active.reindex(index).fillna(False).astype(bool)
    rows = []
    for dt in index:
        on = bool(active.loc[dt])
        if family == "CAL_LONG_0050":
            w0050 = 1.0 if on else 0.0
        elif family == "CAL_OVER_BH":
            w0050 = 1.0
        else:
            raise ValueError(family)
        rows.append([0.0, 0.0, float(w0050)])
    return pd.DataFrame(rows, index=index, columns=SLEEVE_COLS)


def bh_0050_schedule(index: pd.DatetimeIndex) -> pd.DataFrame:
    return pd.DataFrame(
        {"Financial": 0.0, "Telecom": 0.0, "0050": 1.0}, index=index
    )


def book_verdict(
    *,
    tip_vs_live_clean: bool,
    tip_vs_bh_clean: bool,
    score_vs_live: float,
    score_vs_bh: float,
) -> str:
    coexist_live = tip_vs_live_clean and score_vs_live > 0
    beat_bh = tip_vs_bh_clean and score_vs_bh > 0
    if coexist_live:
        return "BEATS_LIVE"
    if beat_bh:
        return "BEATS_BH_ONLY"
    if tip_vs_live_clean and score_vs_live > -0.05:
        return "NEAR_NO_BEAT"
    return "NO_LIFT"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(exist_ok=True)
    OPS.mkdir(parents=True, exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.9]

    import e21_forward_pipeline as e21

    for k in ("season_start", "season_end", "k_thresh", "pre_days", "active_score"):
        if LIVE_KD[k] != e21.KD_OPT[k]:
            raise SystemExit(f"LIVE_KD[{k}] drift vs e21.KD_OPT")
    if e21.LIVE_E45_STITCH:
        raise SystemExit("Refuse ETF ex-calendar screen while LIVE_E45_STITCH is True")

    print("loading ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, _s, target, regime = e16_features(market)
    cal = pd.DatetimeIndex(target.index)
    ex_dates = load_0050_ex_dates()
    ex_in_range = ex_dates[(ex_dates >= cal.min()) & (ex_dates <= cal.max())]
    print(
        f"0050 ex dates: {len(ex_dates)} total · {len(ex_in_range)} in market range "
        f"[{cal.min().date()} .. {cal.max().date()}]",
        flush=True,
    )

    kd_scores = build_kd_season_tilt_scores(
        market,
        dividends,
        FIN,
        k_thresh=float(LIVE_KD["k_thresh"]),
        season_start=LIVE_KD["season_start"],
        season_end=LIVE_KD["season_end"],
        pre_days=int(LIVE_KD["pre_days"]),
        active_score=float(LIVE_KD["active_score"]),
    )
    kd_ok = build_pre_exdiv_window_buy_ok(
        cal,
        dividends,
        FIN,
        pre_days=int(LIVE_KD["pre_days"]),
        also_stock_ex=True,
    )

    jobs: list[dict] = [
        {"id": "BUY_HOLD_0050", "source": "BH", "family": "BUY_HOLD_0050"},
        {"id": "LIVE_STACK", "source": "LIVE", "family": "LIVE_STACK"},
    ]
    for w in (10, 15):
        for fam in ("CAL_LONG_0050", "CAL_OVER_BH"):
            jobs.append(
                {
                    "id": f"MONTH_PROXY_W{w}_{fam}",
                    "source": "MONTH_PROXY",
                    "family": fam,
                    "param": int(w),
                    "hold_thru": 0,
                }
            )
    for n in (10, 20, 40):
        for fam in ("CAL_LONG_0050", "CAL_OVER_BH"):
            jobs.append(
                {
                    "id": f"EXACT_EX_N{n}_{fam}",
                    "source": "EXACT_EX",
                    "family": fam,
                    "param": int(n),
                    "hold_thru": 0,
                }
            )
    jobs.append(
        {
            "id": "EXACT_EX_N20_HOLD_THRU_T5_CAL_LONG_0050",
            "source": "EXACT_EX",
            "family": "CAL_LONG_0050",
            "param": 20,
            "hold_thru": 5,
            "stress": True,
        }
    )
    assert len(jobs) <= 14, len(jobs)
    print(f"Stage A books: {len(jobs)}", flush=True)

    nav_cache: dict[str, pd.DataFrame] = {}
    fill_cache: dict[str, int] = {}
    active_frac: dict[str, float] = {}

    for i, job in enumerate(jobs, 1):
        book_id = job["id"]
        print(f"  [{i}/{len(jobs)}] {book_id}", flush=True)
        schedule = None
        frac = 0.0
        if job["family"] == "LIVE_STACK":
            schedule = None
        elif job["family"] == "BUY_HOLD_0050":
            schedule = bh_0050_schedule(cal)
            frac = 1.0
        elif job["source"] == "MONTH_PROXY":
            mask = month_proxy_mask(cal, int(job["param"]))
            schedule = schedule_from_mask(cal, mask, job["family"])
            frac = float(mask.mean()) if job["family"] == "CAL_LONG_0050" else 1.0
        elif job["source"] == "EXACT_EX":
            mask = exact_ex_mask(
                cal,
                ex_dates,
                n_before=int(job["param"]),
                hold_thru=int(job.get("hold_thru") or 0),
            )
            schedule = schedule_from_mask(cal, mask, job["family"])
            frac = float(mask.mean()) if job["family"] == "CAL_LONG_0050" else 1.0
        else:
            raise ValueError(job)

        nav, fills, meta = sim_book(
            market, target, regime, dividends, kd_scores, kd_ok, schedule=schedule
        )
        assert meta.get("exact_t1_ok"), (book_id, meta)
        nav_cache[book_id] = nav
        fill_cache[book_id] = int(len(fills))
        active_frac[book_id] = float(frac)

    asof = max(pd.to_datetime(nav_cache[b]["date"]).max() for b in nav_cache)
    win = {
        bid: {w: window_stats(nav, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
        for bid, nav in nav_cache.items()
    }
    live_id = "LIVE_STACK"
    bh_id = "BUY_HOLD_0050"

    rows = []
    for job in jobs:
        book_id = job["id"]
        tip_live = tip_gate(nav_cache[live_id], nav_cache[book_id], asof)
        tip_bh = tip_gate(nav_cache[bh_id], nav_cache[book_id], asof)
        held_live = score_vs_base(
            win[live_id]["heldout_2019_plus"], win[book_id]["heldout_2019_plus"]
        )
        held_bh = score_vs_base(
            win[bh_id]["heldout_2019_plus"], win[book_id]["heldout_2019_plus"]
        )
        t_live = tip_is_clean(tip_live)
        t_bh = tip_is_clean(tip_bh)
        if book_id in (live_id, bh_id):
            label = "BASELINE"
        else:
            label = book_verdict(
                tip_vs_live_clean=t_live,
                tip_vs_bh_clean=t_bh,
                score_vs_live=float(held_live["score"]),
                score_vs_bh=float(held_bh["score"]),
            )
        rows.append(
            {
                "id": book_id,
                "source": job["source"],
                "family": job["family"],
                "param": job.get("param"),
                "hold_thru": int(job.get("hold_thru") or 0),
                "stress": bool(job.get("stress")),
                "label": label,
                "tip_live_ytd": tip_live["ytd"]["gate"],
                "tip_live_1y": tip_live["trailing_1y"]["gate"],
                "tip_live_clean": t_live,
                "tip_bh_ytd": tip_bh["ytd"]["gate"],
                "tip_bh_1y": tip_bh["trailing_1y"]["gate"],
                "tip_bh_clean": t_bh,
                "heldout_score_vs_live": float(held_live["score"]),
                "heldout_score_vs_bh": float(held_bh["score"]),
                "mdd_improve_pp_vs_live": float(held_live["mdd_improve_pp"]),
                "mdd_improve_pp_vs_bh": float(held_bh["mdd_improve_pp"]),
                "coexist_live": bool(t_live and held_live["score"] > 0),
                "beat_live": bool(t_live and held_live["score"] > 0),
                "beat_bh": bool(t_bh and held_bh["score"] > 0),
                "full_cagr": win[book_id]["full"].get("cagr"),
                "full_mdd": win[book_id]["full"].get("max_drawdown"),
                "heldout_cagr": win[book_id]["heldout_2019_plus"].get("cagr"),
                "heldout_mdd": win[book_id]["heldout_2019_plus"].get("max_drawdown"),
                "sealed_cagr": win[book_id]["sealed_2023_plus"].get("cagr"),
                "sealed_mdd": win[book_id]["sealed_2023_plus"].get("max_drawdown"),
                "n_fills": fill_cache[book_id],
                "active_frac": active_frac[book_id],
            }
        )

    ranked = sorted(
        rows,
        key=lambda r: (
            1 if r["label"] == "BEATS_LIVE" else 0,
            1 if r.get("coexist_live") else 0,
            1 if r.get("beat_bh") else 0,
            1 if r.get("tip_live_clean") else 0,
            float(r["heldout_score_vs_live"]),
        ),
        reverse=True,
    )
    challengers = [r for r in ranked if r["label"] != "BASELINE"]
    n_beat_live = sum(1 for r in challengers if r["label"] == "BEATS_LIVE")
    n_coexist = sum(1 for r in challengers if r.get("coexist_live"))
    n_beat_bh = sum(1 for r in challengers if r.get("beat_bh"))
    n_tip_live = sum(1 for r in challengers if r.get("tip_live_clean"))
    n_bh_only = sum(1 for r in challengers if r["label"] == "BEATS_BH_ONLY")

    if n_beat_live > 0:
        verdict, decision = "BEATS_LIVE", "HUMAN_OBSERVE_BALLOT"
    elif n_coexist > 0:
        verdict, decision = "COEXIST_NO_LIFT", "STOP_ARCHIVE_OR_HUMAN_EXPAND"
    elif n_bh_only > 0 or n_beat_bh > 0:
        verdict, decision = "BEATS_BH_ONLY", "STOP_ARCHIVE"
    elif n_tip_live > 0:
        verdict, decision = "NEAR_NO_BEAT", "STOP_ARCHIVE"
    else:
        verdict, decision = "NO_LIFT", "STOP_ARCHIVE"

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "ETF_EX_CALENDAR_SCREEN_STAGE_A_2026-09-11",
        "charter": "research/ops/ETF_EX_CALENDAR_STAGE_A_CHARTER.md",
        "status": "PAPER_SCREEN_DONE",
        "live_wire": False,
        "asof": str(pd.Timestamp(asof).date()),
        "n_books": len(ranked),
        "n_challengers": len(challengers),
        "n_beat_live": n_beat_live,
        "n_coexist_live": n_coexist,
        "n_beat_bh": n_beat_bh,
        "n_tip_clean_vs_live": n_tip_live,
        "verdict": verdict,
        "decision": decision,
        "ex_dates_total": int(len(ex_dates)),
        "ex_dates_in_range": int(len(ex_in_range)),
        "note_cal_over_bh": (
            "CAL_OVER_BH is 100% 0050 every day under long-only Stage A rules "
            "(≡ BUY_HOLD_0050); informative lift must come from CAL_LONG_*."
        ),
        "stage_a_grid": {
            "month_proxy_w": [10, 15],
            "exact_ex_n": [10, 20, 40],
            "families": ["CAL_LONG_0050", "CAL_OVER_BH"],
            "stress": ["EXACT_EX_N20_HOLD_THRU_T5_CAL_LONG_0050"],
        },
        "beat_live_ids": [r["id"] for r in challengers if r["label"] == "BEATS_LIVE"],
        "coexist_ids": [r["id"] for r in challengers if r.get("coexist_live")],
        "beat_bh_ids": [r["id"] for r in challengers if r.get("beat_bh")],
        "books": ranked,
        "non_actions": [
            "No Soft-Frozen / KD_OPT / TEL / E45 change",
            "No Soft-assist or sleeve-tilt observe retarget / auto-combo",
            "No inventing announcement_date",
            "No live wire",
        ],
    }

    def pct(x):
        return "—" if x is None else f"{100 * float(x):.2f}%"

    lines = [
        "# ETF Ex-Calendar Screen — Stage A (paper only)",
        "",
        f"Generated: `{payload['generated_at_utc']}` · asof **{payload['asof']}**",
        "Charter: `ETF_EX_CALENDAR_STAGE_A_CHARTER.md`",
        f"Verdict: **`{verdict}`** · decision **`{decision}`** · books **{payload['n_books']}** · **no live wire**",
        "",
        "## Question",
        "",
        "Does rules-based 0050 ex-calendar timing tip-clean beat **BUY_HOLD_0050** and/or coexist with **LIVE_STACK** after costs?",
        "",
        "## Summary",
        "",
        f"- Beat live: **{n_beat_live}** → `{payload['beat_live_ids']}`",
        f"- Coexist live: **{n_coexist}** → `{payload['coexist_ids']}`",
        f"- Beat BH: **{n_beat_bh}** → `{payload['beat_bh_ids'][:12]}`",
        f"- Tip-clean vs live: **{n_tip_live}**",
        f"- Ex dates: **{payload['ex_dates_in_range']}** in market range / {payload['ex_dates_total']} ledger",
        f"- Note: {payload['note_cal_over_bh']}",
        "",
        "## Scoreboard",
        "",
        "| ID | Src | Tip live YTD/1y | Tip BH YTD/1y | Held vs live | Held vs BH | Held CAGR | Held MDD | Sealed CAGR | Sealed MDD | Active% | Label |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for r in ranked:
        lines.append(
            f"| `{r['id']}` | {r['source']} | {r['tip_live_ytd']}/{r['tip_live_1y']} | "
            f"{r['tip_bh_ytd']}/{r['tip_bh_1y']} | {r['heldout_score_vs_live']:.3f} | "
            f"{r['heldout_score_vs_bh']:.3f} | {pct(r['heldout_cagr'])} | {pct(r['heldout_mdd'])} | "
            f"{pct(r['sealed_cagr'])} | {pct(r['sealed_mdd'])} | {r['active_frac']:.1%} | `{r['label']}` |"
        )

    live_row = next(r for r in ranked if r["id"] == live_id)
    bh_row = next(r for r in ranked if r["id"] == bh_id)
    lines += [
        "",
        "## Baselines",
        "",
        f"- `LIVE_STACK` heldout CAGR/MDD: {pct(live_row['heldout_cagr'])} / {pct(live_row['heldout_mdd'])}",
        f"- `BUY_HOLD_0050` heldout CAGR/MDD: {pct(bh_row['heldout_cagr'])} / {pct(bh_row['heldout_mdd'])}",
        "",
        "## Reading",
        "",
        "- Held score = MDD↑pp − 0.5·|CAGRΔpp| vs each baseline.",
        "- Sealed is report-only in Stage A.",
        "- `CAL_OVER_BH` under Stage A long-only rules matches `BUY_HOLD_0050` (charter grid retained).",
        "- Announce dates were **not** invented; EXACT_EX uses realized `cash_ex_date` only.",
        "",
        "## Non-actions",
        "",
        "- No Soft-Frozen / live KD / TEL / E45 / Soft-assist / sleeve-tilt wire from this screen",
        "",
        "## Next",
        "",
    ]
    if verdict == "BEATS_LIVE":
        lines.append(
            "- Draft **OPEN observe** ballot only on human ask (`LIVE_STACK` ∥ champion)."
        )
    elif verdict == "BEATS_BH_ONLY":
        lines.append(
            "- Archive as calendar curiosity; **no** live/observe path unless human expands charter."
        )
    else:
        lines.append("- **STOP / archive**; live + observes unchanged.")
    lines += [
        "",
        "## Label",
        "",
        f"`{payload['label']}__{verdict}`",
        "",
    ]
    md = "\n".join(lines)
    zh = "\n".join(
        [
            "# ETF 除息日曆 Screen — Stage A（只測 paper）",
            "",
            f"產生：`{payload['generated_at_utc']}` · asof **{payload['asof']}**",
            f"總評：**`{verdict}`** · 決策 **`{decision}`** · books **{payload['n_books']}** · **不上 live**",
            f"- 勝 live：**{n_beat_live}** · 共存 live：**{n_coexist}** · 勝 BH：**{n_beat_bh}**",
            f"- tip-clean vs live：**{n_tip_live}**",
            "",
            "Soft-Frozen／KD_OPT／TEL／E45／Soft-assist／sleeve observe **不變**。未虛構 announce。",
            "",
            "英文：`ETF_EX_CALENDAR_SCREEN.md`",
            "",
        ]
    )

    pd.DataFrame(ranked).to_csv(OUT / "reports" / "scoreboard.csv", index=False)
    (OUT / "reports" / "etf_ex_calendar_screen.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (OUT / "reports" / "ETF_EX_CALENDAR_SCREEN.md").write_text(md, encoding="utf-8")
    (OPS / "ETF_EX_CALENDAR_SCREEN.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (OPS / "ETF_EX_CALENDAR_SCREEN.md").write_text(md, encoding="utf-8")
    (OPS / "ETF_EX_CALENDAR_SCREEN.zh-TW.md").write_text(zh, encoding="utf-8")

    print(
        json.dumps(
            {
                "verdict": verdict,
                "decision": decision,
                "n_books": payload["n_books"],
                "n_beat_live": n_beat_live,
                "n_coexist_live": n_coexist,
                "n_beat_bh": n_beat_bh,
                "beat_live_ids": payload["beat_live_ids"],
                "top5": [r["id"] for r in ranked[:5]],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
