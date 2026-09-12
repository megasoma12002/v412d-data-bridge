#!/usr/bin/env python3
"""Sleeve-tilt dual-paper ledgers — OPERATING OBSERVE (paper only).

Books (500M / board-lot 1000):
  BASE  LIVE_STACK              Soft-Frozen + KD_OPT + TEL_EQUAL
  CHAL  SLEEVE_RSI14_LT30_a0225 same within-sleeve + Soft-Frozen router RSI14 tilt

Human OPEN (2026-09-12 rule-path): OPEN Sleeve-tilt observe: SLEEVE_RSI14_LT30_a0225
Prior seed SLEEVE_BELOW_MA60_a01 superseded (paper archive).
Soft-Frozen clips KEEP · live wire false · Soft-assist observe independent (no fuse)
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e16_soft_frozen_base as soft
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, load_market, window_stats
from e50_early_stack_combined_nav import FIN, e16_features, simulate_core
from portfolio_capital import DEFAULT_CAPITAL
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp
from sleeve_tilt_helpers import (
    ALPHA,
    BASE_ID,
    CHAMPION_ID,
    HUMAN_OPEN,
    LIVE_KD,
    PRIOR_OBSERVE_ID,
    SIGNAL_SHORT,
    build_champion_target,
)
from tw_share_lots import BOARD_LOT
from within_sleeve_alloc import (
    FIN_PRE_EXDIV_KD,
    TEL_EQUAL,
    build_kd_season_tilt_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/sleeve-tilt-dual-paper-observe"
OPS = ROOT / "research/ops"
CAPITAL = float(DEFAULT_CAPITAL)
LOT = BOARD_LOT
STATUS = "OPERATING_OBSERVE"


def held_score(base_stats: dict, chal_stats: dict) -> dict:
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


def run_book(market, target, regime, dividends, *, scores, buy_ok):
    nav, fills, meta = simulate_core(
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
    )
    assert meta.get("exact_t1_ok")
    return {"nav": nav, "n_fills": int(len(fills)), "meta": meta}


def main() -> int:
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    OPS.mkdir(parents=True, exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.9]

    import e21_forward_pipeline as e21

    for k in ("season_start", "season_end", "k_thresh", "pre_days", "active_score"):
        if LIVE_KD[k] != e21.KD_OPT[k]:
            raise SystemExit(f"LIVE_KD[{k}] drift vs e21.KD_OPT")
    if e21.LIVE_E45_STITCH:
        raise SystemExit("Refuse sleeve-tilt observe while LIVE_E45_STITCH is True")

    print("loading ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _prices, sleeve, target_live, regime = e16_features(market)
    cal = pd.DatetimeIndex(pd.to_datetime(market["date"]).drop_duplicates().sort_values())
    target_chal = build_champion_target(market, sleeve, regime)

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
        cal, dividends, FIN, pre_days=int(LIVE_KD["pre_days"]), also_stock_ex=True
    )

    print(f"{BASE_ID} ...", flush=True)
    base = run_book(market, target_live, regime, dividends, scores=kd_scores, buy_ok=kd_ok)
    base["nav"].to_csv(OUT / "outputs" / "live_stack_daily_nav.csv", index=False)

    print(f"{CHAMPION_ID} ...", flush=True)
    chal = run_book(market, target_chal, regime, dividends, scores=kd_scores, buy_ok=kd_ok)
    chal["nav"].to_csv(
        OUT / "outputs" / "sleeve_rsi14_lt30_a0225_daily_nav.csv", index=False
    )

    joined = (
        base["nav"][["date", "nav"]]
        .rename(columns={"nav": "nav_base"})
        .merge(
            chal["nav"][["date", "nav"]].rename(columns={"nav": "nav_chal"}),
            on="date",
            how="inner",
        )
    )
    joined["rel_chal_vs_base"] = joined["nav_chal"] / joined["nav_base"]
    joined.to_csv(OUT / "outputs" / "dual_paper_nav_compare.csv", index=False)

    win_base = {w: window_stats(base["nav"], a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
    win_chal = {w: window_stats(chal["nav"], a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
    held = held_score(win_base["heldout_2019_plus"], win_chal["heldout_2019_plus"])
    sealed = held_score(win_base["sealed_2023_plus"], win_chal["sealed_2023_plus"])

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "SLEEVE_TILT_DUAL_PAPER_OBSERVE_OPERATING",
        "status": STATUS,
        "live_wire": False,
        "soft_frozen_clips_unchanged": True,
        "soft_assist_observe": "INDEPENDENT_NO_FUSE",
        "human_open": HUMAN_OPEN,
        "prior_observe_id": PRIOR_OBSERVE_ID,
        "books": [BASE_ID, CHAMPION_ID],
        "capital": CAPITAL,
        "lot_size": LOT,
        "base_id": BASE_ID,
        "challenger_id": CHAMPION_ID,
        "challenger_policy": {
            "signal": SIGNAL_SHORT,
            "alpha": ALPHA,
            "within_sleeve": "KD_OPT + TEL_EQUAL",
        },
        "heldout_vs_base": held,
        "sealed_vs_base": sealed,
        "windows": {BASE_ID: win_base, CHAMPION_ID: win_chal},
        "fills": {BASE_ID: base["n_fills"], CHAMPION_ID: chal["n_fills"]},
        "default_status": "KEEP_OBSERVE",
        "ballot": "research/ops/SLEEVE_RSI14_A0225_OBSERVE_BALLOT_EXECUTED_OPEN.md",
        "observe_open": "research/ops/SLEEVE_LAYER_TILT_DUAL_PAPER_OBSERVE_OPEN.md",
        "posture": "research/ops/SLEEVE_LAYER_TILT_OBSERVE_POSTURE.md",
        "cutover_blocked": "research/ops/CUTOVER_CHECKLIST_SLEEVE_LAYER_TILT.md",
        "next_human": [
            "Month-end monitor on LIVE_STACK ∥ SLEEVE_RSI14_LT30_a0225",
            "Default KEEP OBSERVE; live cutover needs dedicated ACCEPT",
        ],
    }
    (OUT / "reports" / "sleeve_tilt_dual_paper_observe.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8"
    )
    OPS.joinpath("SLEEVE_LAYER_TILT_DUAL_PAPER_OBSERVE.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8"
    )

    md = f"""# Sleeve-tilt dual-paper (OPERATING OBSERVE)

Status: `{STATUS}` · paper only · Soft-Frozen clips KEEP · live wire false  
Human: `{HUMAN_OPEN}`  
Default: **KEEP OBSERVE** · posture `SLEEVE_LAYER_TILT_OBSERVE_POSTURE.md`

Books: `{BASE_ID}` ∥ `{CHAMPION_ID}`  
Execution: capital **{CAPITAL:,.0f}** · lot **{LOT}**

Held-out vs `{BASE_ID}`:
- MDD↑pp: **{held.get('mdd_improve_pp')}**
- CAGR giveback pp: **{held.get('cagr_giveback_pp')}**
- Score: **{held.get('score')}**

Sealed vs `{BASE_ID}` (report-only):
- MDD↑pp: **{sealed.get('mdd_improve_pp')}**
- CAGR giveback pp: **{sealed.get('cagr_giveback_pp')}**
- Score: **{sealed.get('score')}**

## Reproduce

```bash
python3 scripts/e16_sleeve_tilt_dual_paper_ledgers.py
python3 scripts/e16_sleeve_tilt_month_end_monitor.py
```

Repro: `{OUT.relative_to(ROOT)}/`
"""
    (OUT / "reports" / "SLEEVE_LAYER_TILT_DUAL_PAPER_OBSERVE.md").write_text(md, encoding="utf-8")
    OPS.joinpath("SLEEVE_LAYER_TILT_DUAL_PAPER_OBSERVE_OPERATING.md").write_text(
        md, encoding="utf-8"
    )
    print(json.dumps({"status": STATUS, "heldout": held, "sealed": sealed}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
