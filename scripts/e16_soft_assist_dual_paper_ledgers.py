#!/usr/bin/env python3
"""Soft-assist dual-paper ledgers — OPERATING OBSERVE (paper only).

Books (500M / board-lot 1000):
  BASE  LIVE_KD_OPT
  CHAL  SOFT_BOTH__BELOW_MA120__RSI6_GT80

Human OPEN: OPEN Soft-assist observe: SOFT_BOTH__BELOW_MA120__RSI6_GT80
Soft-Frozen KEEP · live wire false · TEL_EQUAL KEEP
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
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp
from soft_assist_helpers import (
    BUY_LOW_ID,
    CHAMPION_ID,
    LIVE_KD,
    SELL_HIGH_ID,
    SOFT_BOOST,
    soft_boost_scores,
    soft_sell_panel,
)
from ta_indicator_catalog import build_low_high_catalog
from tw_share_lots import BOARD_LOT
from within_sleeve_alloc import (
    FIN_PRE_EXDIV_KD,
    TEL_EQUAL,
    build_kd_season_tilt_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/soft-assist-dual-paper-observe"
OPS = ROOT / "research/ops"
CAPITAL = 500_000_000.0
LOT = BOARD_LOT
BASE_ID = "LIVE_KD_OPT"
CHAL_ID = CHAMPION_ID
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


def run_kd(market, target, regime, dividends, *, scores, buy_ok, sell_scores=None):
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
        fin_sell_scores=sell_scores,
    )
    assert meta.get("exact_t1_ok")
    return {"nav": nav, "n_fills": int(len(fills)), "meta": meta}


def main() -> int:
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    OPS.mkdir(parents=True, exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.9]

    print("loading ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, _s, target, regime = e16_features(market)
    cal = pd.DatetimeIndex(pd.to_datetime(market["date"]).drop_duplicates().sort_values())

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
    lows, highs = build_low_high_catalog(market, cal, list(FIN))
    soft_scores = soft_boost_scores(kd_scores, lows[BUY_LOW_ID], SOFT_BOOST)
    soft_sell = soft_sell_panel(highs[SELL_HIGH_ID], boost=SOFT_BOOST)

    print(f"{BASE_ID} ...", flush=True)
    base = run_kd(market, target, regime, dividends, scores=kd_scores, buy_ok=kd_ok)
    base["nav"].to_csv(OUT / "outputs" / "live_kd_opt_daily_nav.csv", index=False)

    print(f"{CHAL_ID} ...", flush=True)
    chal = run_kd(
        market,
        target,
        regime,
        dividends,
        scores=soft_scores,
        buy_ok=kd_ok,
        sell_scores=soft_sell,
    )
    chal["nav"].to_csv(
        OUT / "outputs" / "soft_both_below_ma120_rsi6_gt80_daily_nav.csv", index=False
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
        "label": "SOFT_ASSIST_DUAL_PAPER_OBSERVE_OPERATING",
        "status": STATUS,
        "live_wire": False,
        "soft_frozen_unchanged": True,
        "human_open": "OPEN Soft-assist observe: SOFT_BOTH__BELOW_MA120__RSI6_GT80",
        "books": [BASE_ID, CHAL_ID],
        "capital": CAPITAL,
        "lot_size": LOT,
        "base_id": BASE_ID,
        "challenger_id": CHAL_ID,
        "challenger_policy": FIN_PRE_EXDIV_KD,
        "soft_assist": {
            "buy_low_id": BUY_LOW_ID,
            "sell_high_id": SELL_HIGH_ID,
            "boost": SOFT_BOOST,
            "live_kd": {
                "season_start": list(LIVE_KD["season_start"]),
                "season_end": list(LIVE_KD["season_end"]),
                "k_thresh": LIVE_KD["k_thresh"],
                "pre_days": LIVE_KD["pre_days"],
                "active_score": LIVE_KD["active_score"],
            },
        },
        "heldout_vs_base": held,
        "sealed_vs_base": sealed,
        "windows": {BASE_ID: win_base, CHAL_ID: win_chal},
        "fills": {BASE_ID: base["n_fills"], CHAL_ID: chal["n_fills"]},
        "default_status": "KEEP_OBSERVE",
        "ballot": "research/ops/SOFT_ASSIST_PROMOTE_BALLOT_EXECUTED_OPEN_OBSERVE.md",
        "observe_open": "research/ops/SOFT_ASSIST_DUAL_PAPER_OBSERVE_OPEN.md",
        "posture": "research/ops/SOFT_ASSIST_OBSERVE_POSTURE.md",
        "cutover_blocked": "research/ops/CUTOVER_CHECKLIST_SOFT_ASSIST.md",
        "next_human": [
            "Month-end monitor on LIVE_KD_OPT ∥ soft champion",
            "Default KEEP OBSERVE; live cutover needs dedicated ACCEPT",
        ],
    }
    (OUT / "reports" / "soft_assist_dual_paper_observe.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8"
    )
    OPS.joinpath("SOFT_ASSIST_DUAL_PAPER_OBSERVE.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8"
    )

    md = f"""# Soft-assist dual-paper (OPERATING OBSERVE)

Status: `{STATUS}` · paper only · Soft-Frozen KEEP · live wire false  
Human: `OPEN Soft-assist observe: SOFT_BOTH__BELOW_MA120__RSI6_GT80`  
Default: **KEEP OBSERVE** · posture `SOFT_ASSIST_OBSERVE_POSTURE.md`

Books: `{BASE_ID}` ∥ `{CHAL_ID}`  
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
python3 scripts/e16_soft_assist_dual_paper_ledgers.py
python3 scripts/e16_soft_assist_month_end_monitor.py
```

Repro: `{OUT.relative_to(ROOT)}/`
"""
    (OUT / "reports" / "SOFT_ASSIST_DUAL_PAPER_OBSERVE.md").write_text(md, encoding="utf-8")
    OPS.joinpath("SOFT_ASSIST_DUAL_PAPER_OBSERVE_OPERATING.md").write_text(md, encoding="utf-8")
    print(json.dumps({"status": STATUS, "heldout": held, "sealed": sealed}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
