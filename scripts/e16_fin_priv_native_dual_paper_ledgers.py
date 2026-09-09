#!/usr/bin/env python3
"""民營 native dual-paper ledgers — OPERATING OBSERVE (paper only).

Books (500M / board-lot 1000):
  BASE  PRIV_EQUAL
  CHAL  PRIV_KD_MAY_Klt25_T15  (native winner)

Soft-Frozen sleeve weights are unchanged (from live FINBAND features).
Financial dollars are routed to PRIV_R3R4 only for this paper observe.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e16_soft_frozen_base as soft
from e16_fin_priv_native_optimize import (
    CAPITAL,
    LOT,
    PRIV_R3R4,
    PUB_R1,
    TEL,
    build_extended_market,
    held_score,
    kd_book,
    run_book,
)
import e50_early_stack_combined_nav as e50
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, window_stats
from within_sleeve_alloc import FIN_EQUAL, FIN_PRE_EXDIV_KD

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/fin-priv-native-dual-paper-observe"
OPS = ROOT / "research/ops"

BASE_ID = "PRIV_EQUAL"
CHAL_ID = "PRIV_KD_MAY_Klt25_T15"
STATUS = "OPERATING_OBSERVE"

NATIVE_KD = {
    "season": "MAY",
    "season_start": (5, 1),
    "season_end": (5, 31),
    "k_thresh": 25.0,
    "pre_days": 15,
}


def main() -> None:
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    OPS.mkdir(parents=True, exist_ok=True)

    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.9]
    assert soft.FIN == PUB_R1

    print("loading extended market + dividends ...", flush=True)
    market = build_extended_market()
    dividends = load_dividends()
    _p, _s, target, regime = e50.e16_features(market)

    print(f"{BASE_ID} sim @ {CAPITAL:,.0f}/{LOT} ...", flush=True)
    base = run_book(
        market,
        dividends,
        target,
        regime,
        book_id=BASE_ID,
        financial_alloc=FIN_EQUAL,
    )
    base["nav"].to_csv(OUT / "outputs" / "priv_equal_daily_nav.csv", index=False)
    base["n_fills"] = int(base["n_fills"])

    print(f"{CHAL_ID} sim @ {CAPITAL:,.0f}/{LOT} ...", flush=True)
    chal = kd_book(
        market,
        dividends,
        target,
        regime,
        season=NATIVE_KD["season"],
        s0=NATIVE_KD["season_start"],
        s1=NATIVE_KD["season_end"],
        k_thresh=NATIVE_KD["k_thresh"],
        pre_days=NATIVE_KD["pre_days"],
    )
    chal["nav"].to_csv(OUT / "outputs" / "priv_kd_may_klt25_t15_daily_nav.csv", index=False)
    chal["n_fills"] = int(chal["n_fills"])

    joined = base["nav"][["date", "nav"]].rename(columns={"nav": "nav_base"}).merge(
        chal["nav"][["date", "nav"]].rename(columns={"nav": "nav_chal"}),
        on="date",
        how="inner",
    )
    joined["rel_chal_vs_base"] = joined["nav_chal"] / joined["nav_base"]
    joined.to_csv(OUT / "outputs" / "dual_paper_nav_compare.csv", index=False)

    win_base = {w: window_stats(base["nav"], a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
    win_chal = {w: window_stats(chal["nav"], a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
    held = held_score(win_base["heldout_2019_plus"], win_chal["heldout_2019_plus"])
    sealed = held_score(win_base["sealed_2023_plus"], win_chal["sealed_2023_plus"])

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "FIN_PRIV_NATIVE_DUAL_PAPER_OBSERVE_OPERATING",
        "status": STATUS,
        "live_wire": False,
        "soft_frozen_unchanged": True,
        "books": [BASE_ID, CHAL_ID],
        "capital": CAPITAL,
        "lot_size": LOT,
        "base_id": BASE_ID,
        "challenger_id": CHAL_ID,
        "challenger_policy": FIN_PRE_EXDIV_KD,
        "native_kd": {
            "season_start": list(NATIVE_KD["season_start"]),
            "season_end": list(NATIVE_KD["season_end"]),
            "k_thresh": NATIVE_KD["k_thresh"],
            "pre_days": NATIVE_KD["pre_days"],
        },
        "heldout_vs_base": held,
        "sealed_vs_base": sealed,
        "windows": {
            BASE_ID: win_base,
            CHAL_ID: win_chal,
        },
        "fills": {
            BASE_ID: base["n_fills"],
            CHAL_ID: chal["n_fills"],
        },
        "next_human": [
            "Run month-end monitor on this dual-paper pair",
            "Keep observe-only; no live wiring without dedicated ACCEPT",
        ],
    }
    (OUT / "reports" / "fin_priv_native_dual_paper_observe.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    OPS.joinpath("FIN_PRIV_NATIVE_DUAL_PAPER_OBSERVE.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n",
        encoding="utf-8",
    )

    md = f"""# 民營 native dual-paper (OPERATING OBSERVE)

Status: `{STATUS}` · paper only · Soft-Frozen KEEP · live wire false

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

Repro: `{OUT.relative_to(ROOT)}/`
"""
    (OUT / "reports" / "FIN_PRIV_NATIVE_DUAL_PAPER_OBSERVE.md").write_text(md, encoding="utf-8")
    OPS.joinpath("FIN_PRIV_NATIVE_DUAL_PAPER_OBSERVE_OPERATING.md").write_text(md, encoding="utf-8")
    print(json.dumps({"status": STATUS, "heldout": held, "sealed": sealed}, indent=2, default=str))


if __name__ == "__main__":
    main()
