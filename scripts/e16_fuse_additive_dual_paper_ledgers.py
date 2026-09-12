#!/usr/bin/env python3
"""FUSE_ADDITIVE dual-paper ledgers — OPERATING OBSERVE (paper only).

Books (500M / board-lot 1000):
  BASE  LIVE_STACK      Soft-Frozen + KD_OPT + TEL_EQUAL
  CHAL  FUSE_ADDITIVE   Soft observe softs + Sleeve observe RSI14 tilt α=0.225

Human OPEN (2026-09-12): OPEN Soft×Sleeve fuse observe: FUSE_ADDITIVE
Soft-assist observe KEEP · Sleeve-tilt observe KEEP · independent · no live wire
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
from fuse_additive_helpers import (
    BASE_ID,
    FUSE_ID,
    HUMAN_OPEN,
    LIVE_KD,
    SLEEVE_ALPHA,
    SLEEVE_OBSERVE_ID,
    SOFT_OBSERVE_ID,
    STATUS,
    build_champion_target,
    build_observe_buy_scores,
    build_observe_sell_panel,
)
from portfolio_capital import DEFAULT_CAPITAL
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp
from ta_indicator_catalog import build_low_high_catalog
from tw_share_lots import BOARD_LOT
from within_sleeve_alloc import (
    FIN_PRE_EXDIV_KD,
    TEL_EQUAL,
    build_kd_season_tilt_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/fuse-additive-dual-paper-observe"
OPS = ROOT / "research/ops"
CAPITAL = float(DEFAULT_CAPITAL)
LOT = BOARD_LOT


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


def run_book(market, target, regime, dividends, *, scores, buy_ok, sell_scores=None):
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

    import e21_forward_pipeline as e21

    for k in ("season_start", "season_end", "k_thresh", "pre_days", "active_score"):
        if LIVE_KD[k] != e21.KD_OPT[k]:
            raise SystemExit(f"LIVE_KD[{k}] drift vs e21.KD_OPT")
    if e21.LIVE_E45_STITCH:
        raise SystemExit("Refuse FUSE_ADDITIVE observe while LIVE_E45_STITCH is True")

    print("loading ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _prices, sleeve, target_live, regime = e16_features(market)
    cal = pd.DatetimeIndex(pd.to_datetime(market["date"]).drop_duplicates().sort_values())
    lows, highs = build_low_high_catalog(market, cal, list(FIN))

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
    soft_buy = build_observe_buy_scores(kd_scores, lows)
    soft_sell = build_observe_sell_panel(highs)
    target_fuse = build_champion_target(market, sleeve, regime)

    print(f"{BASE_ID} ...", flush=True)
    base = run_book(market, target_live, regime, dividends, scores=kd_scores, buy_ok=kd_ok)
    base["nav"].to_csv(OUT / "outputs" / "live_stack_daily_nav.csv", index=False)

    print(f"{FUSE_ID} ...", flush=True)
    chal = run_book(
        market,
        target_fuse,
        regime,
        dividends,
        scores=soft_buy,
        buy_ok=kd_ok,
        sell_scores=soft_sell,
    )
    chal["nav"].to_csv(OUT / "outputs" / "fuse_additive_daily_nav.csv", index=False)

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
        "label": "FUSE_ADDITIVE_DUAL_PAPER_OBSERVE_OPERATING",
        "status": STATUS,
        "live_wire": False,
        "soft_frozen_clips_unchanged": True,
        "soft_assist_observe": "KEEP_INDEPENDENT",
        "sleeve_tilt_observe": "KEEP_INDEPENDENT",
        "ops_auto_fuse": False,
        "human_open": HUMAN_OPEN,
        "books": [BASE_ID, FUSE_ID],
        "capital": CAPITAL,
        "lot_size": LOT,
        "base_id": BASE_ID,
        "challenger_id": FUSE_ID,
        "challenger_policy": {
            "soft_observe_softs": SOFT_OBSERVE_ID,
            "sleeve_observe_tilt": SLEEVE_OBSERVE_ID,
            "sleeve_alpha": float(SLEEVE_ALPHA),
            "construction": "Soft observe buy+sell softs + Sleeve RSI14 tilt on LIVE_STACK",
        },
        "heldout_vs_base": held,
        "sealed_vs_base": sealed,
        "windows": {BASE_ID: win_base, FUSE_ID: win_chal},
        "fills": {BASE_ID: base["n_fills"], FUSE_ID: chal["n_fills"]},
        "default_status": "KEEP_OBSERVE",
        "ballot": "research/ops/FUSE_ADDITIVE_OBSERVE_BALLOT_EXECUTED_OPEN.md",
        "observe_open": "research/ops/FUSE_ADDITIVE_DUAL_PAPER_OBSERVE_OPEN.md",
        "posture": "research/ops/FUSE_ADDITIVE_OBSERVE_POSTURE.md",
        "cutover_blocked": "research/ops/CUTOVER_CHECKLIST_FUSE_ADDITIVE.md",
        "evidence": "research/ops/SOFT_SLEEVE_PAPER_FUSE_STAGEA_SCREEN.md",
        "next_human": [
            "Month-end monitor on LIVE_STACK ∥ FUSE_ADDITIVE",
            "Default KEEP OBSERVE; live cutover needs dedicated ACCEPT for FUSE_ADDITIVE",
            "Soft-assist and Sleeve-tilt observes remain independent KEEP",
        ],
    }
    (OUT / "reports" / "fuse_additive_dual_paper_observe.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8"
    )
    OPS.joinpath("FUSE_ADDITIVE_DUAL_PAPER_OBSERVE.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8"
    )

    md = f"""# FUSE_ADDITIVE dual-paper (OPERATING OBSERVE)

Status: `{STATUS}` · paper only · Soft-Frozen clips KEEP · live wire **false**  
Human: `{HUMAN_OPEN}`  
Default: **KEEP OBSERVE** · posture `FUSE_ADDITIVE_OBSERVE_POSTURE.md`

Books: `{BASE_ID}` ∥ `{FUSE_ID}`  
Construction: Soft `{SOFT_OBSERVE_ID}` softs + Sleeve `{SLEEVE_OBSERVE_ID}` tilt α={SLEEVE_ALPHA:g}  
Soft-assist observe **KEEP** · Sleeve-tilt observe **KEEP** (independent; not replaced)  
Ops auto-fuse of Soft∥Sleeve observes: **still FORBIDDEN** (this is a dedicated third paper book)

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
python3 scripts/e16_fuse_additive_dual_paper_ledgers.py
python3 scripts/e16_fuse_additive_month_end_monitor.py
```

Repro: `{OUT.relative_to(ROOT)}/`
"""
    (OUT / "reports" / "FUSE_ADDITIVE_DUAL_PAPER_OBSERVE.md").write_text(md, encoding="utf-8")
    OPS.joinpath("FUSE_ADDITIVE_DUAL_PAPER_OBSERVE_OPERATING.md").write_text(md, encoding="utf-8")
    print(json.dumps({"status": STATUS, "heldout": held, "sealed": sealed}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
