#!/usr/bin/env python3
"""FIN within-sleeve dual-paper ledgers — OPERATING OBSERVE (paper only).

Side-by-side Exact T+1 paper books @ charter capital 500M / board-lot 1000:
  BASE  FIN_EQUAL
  CHAL  FIN_RS_SOFT_TILT_EXDIV  (Stage C locked top)

Human: 各檔各做各的 — open dual-paper observe beside equal-split.
Soft-Frozen KEEP · live e21 FIN equal-split untouched · no live wire.
Telecom held at TEL_EQUAL (isolate FIN within-sleeve).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e16_soft_frozen_base as soft
from e45_paper_harness import WINDOWS_STANDARD, deltas_vs_base, load_dividends, load_market, window_stats
from e50_early_stack_combined_nav import FIN, e16_features, simulate_core
from tw_share_lots import BOARD_LOT
from within_sleeve_alloc import (
    FIN_EQUAL,
    FIN_RS_SOFT_TILT_EXDIV,
    TEL_EQUAL,
    build_exdiv_buy_ok,
    build_name_scores,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/fin-within-sleeve-dual-paper-observe"
OPS = ROOT / "research/ops"

BASE_ID = "FIN_EQUAL"
CHAL_ID = "FIN_RS_SOFT_TILT_EXDIV"
CHAL_SLUG = "fin_rs_soft_tilt_exdiv"
STATUS = "OPERATING_OBSERVE"
CHARTER_CAPITAL = 500_000_000.0
CHARTER_LOT = BOARD_LOT


def _run(market, dividends, target, regime, *, policy: str, fin_scores, fin_buy_ok):
    return simulate_core(
        market,
        target,
        regime,
        dividends,
        apply_e22=True,
        apply_stock_div=True,
        capital=CHARTER_CAPITAL,
        lot_size=CHARTER_LOT,
        financial_alloc=policy,
        telecom_alloc=TEL_EQUAL,
        fin_name_scores=fin_scores if policy == FIN_RS_SOFT_TILT_EXDIV else None,
        fin_buy_ok=fin_buy_ok if policy == FIN_RS_SOFT_TILT_EXDIV else None,
    )


def main() -> None:
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    OPS.mkdir(parents=True, exist_ok=True)

    assert soft.SOFT_FROZEN_FIN_CLIP == [0.5, 0.95]

    print("loading market + dividends ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, _s, target, regime = e16_features(market)
    cal = pd.to_datetime(market["date"]).drop_duplicates().sort_values().to_numpy()
    fin_scores = build_name_scores(market, FIN)
    fin_buy_ok = build_exdiv_buy_ok(cal, dividends, FIN, also_stock_ex=True)

    print(f"{BASE_ID} sim @ 500M/1000 ...", flush=True)
    nav_b, fills_b, meta_b = _run(
        market, dividends, target, regime, policy=FIN_EQUAL, fin_scores=fin_scores, fin_buy_ok=fin_buy_ok
    )

    print(f"{CHAL_ID} sim @ 500M/1000 ...", flush=True)
    nav_c, fills_c, meta_c = _run(
        market,
        dividends,
        target,
        regime,
        policy=FIN_RS_SOFT_TILT_EXDIV,
        fin_scores=fin_scores,
        fin_buy_ok=fin_buy_ok,
    )

    nav_b.to_csv(OUT / "outputs" / "base_fin_equal_daily_nav.csv", index=False)
    nav_c.to_csv(OUT / "outputs" / f"{CHAL_SLUG}_daily_nav.csv", index=False)
    fills_b.to_csv(OUT / "outputs" / "base_fin_equal_fills.csv", index=False)
    fills_c.to_csv(OUT / "outputs" / f"{CHAL_SLUG}_fills.csv", index=False)

    jb = nav_b[["date", "nav"]].rename(columns={"nav": "nav_base"})
    jc = nav_c[["date", "nav"]].rename(columns={"nav": f"nav_{CHAL_SLUG}"})
    joined = jb.merge(jc, on="date", how="inner")
    joined["rel_chal_vs_base"] = joined[f"nav_{CHAL_SLUG}"] / joined["nav_base"]
    joined.to_csv(OUT / "outputs" / "dual_paper_nav_compare.csv", index=False)

    books: dict = {}
    for name, nav, meta in [(BASE_ID, nav_b, meta_b), (CHAL_ID, nav_c, meta_c)]:
        win = {w: window_stats(nav, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
        end_pos = meta.get("end_positions") or {}
        fin_held = {c: float(end_pos.get(c, 0.0)) for c in FIN}
        books[name] = {
            "exact_t1_ok": bool(meta.get("exact_t1_ok")),
            "lot_size": int(meta.get("lot_size", CHARTER_LOT)),
            "capital": CHARTER_CAPITAL,
            "tip_fin_positions": fin_held,
            "tip_fin_names_with_board_lot": int(
                sum(1 for v in fin_held.values() if abs(v) >= CHARTER_LOT - 1e-9)
            ),
            "windows": win,
        }

    held = deltas_vs_base(
        books[BASE_ID]["windows"]["heldout_2019_plus"],
        books[CHAL_ID]["windows"]["heldout_2019_plus"],
    )
    sealed = deltas_vs_base(
        books[BASE_ID]["windows"]["sealed_2023_plus"],
        books[CHAL_ID]["windows"]["sealed_2023_plus"],
    )

    proposal = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "FIN_WITHIN_SLEEVE_DUAL_PAPER_OBSERVE_OPERATING",
        "status": STATUS,
        "operating_observe": True,
        "live_wire": False,
        "soft_frozen_default_unchanged": True,
        "cutover_authorized": False,
        "ballot": "dual-paper 觀察 FIN_RS_SOFT_TILT_EXDIV 並排 FIN_EQUAL",
        "human_rationale": "各檔各做各的 — ex-div dates + RS timing differ",
        "stage_c": "STAGE_C_CANDIDATES_LOCKED",
        "base_id": BASE_ID,
        "locked_challenger": CHAL_ID,
        "execution_context": {
            "capital": CHARTER_CAPITAL,
            "board_lot": CHARTER_LOT,
            "e22_books": "E22_v2s_tw",
            "telecom_held_at": TEL_EQUAL,
        },
        "exact_t1": {
            "base": books[BASE_ID]["exact_t1_ok"],
            "chal": books[CHAL_ID]["exact_t1_ok"],
        },
        "heldout_vs_base": held,
        "sealed_vs_base": sealed,
        "windows": books,
        "next_human": [
            "Month-end cadence via ops_month_end_paper_pack.py --refresh-ledgers",
            "Live FIN within-sleeve cutover still requires dedicated ACCEPT ballot",
        ],
        "non_actions": [
            "Paper-only; Soft-Frozen KEEP; live e21 FIN equal-split untouched",
            "Do not wire FIN_RS_SOFT_TILT_EXDIV into e21 without cutover ACCEPT",
            "Stage B hard policies remain STOP",
        ],
    }
    (OUT / "reports" / "fin_within_sleeve_dual_paper_observe.json").write_text(
        json.dumps(proposal, indent=2, default=str) + "\n", encoding="utf-8"
    )
    OPS.joinpath("FIN_WITHIN_SLEEVE_DUAL_PAPER_OBSERVE.json").write_text(
        json.dumps(proposal, indent=2, default=str) + "\n", encoding="utf-8"
    )

    md = f"""# FIN within-sleeve dual-paper (OPERATING OBSERVE)

**Status:** `{STATUS}` — **paper only** · Soft-Frozen **KEEP** · live wire **false**

| Book | Role |
|---|---|
| `{BASE_ID}` | Equal-split Financial sleeve (control) |
| `{CHAL_ID}` | Stage C locked: RS soft-tilt + ex-div skip-buy |

Execution: capital **{CHARTER_CAPITAL:,.0f}** · lot **{CHARTER_LOT}** · Telecom=`TEL_EQUAL`

## Held-out vs BASE

- MDD improve pp: {held.get('mdd_improve_pp')}
- CAGR giveback pp: {held.get('cagr_giveback_pp')}
- Score: {held.get('score')}

## Sealed vs BASE

- MDD improve pp: {sealed.get('mdd_improve_pp')}
- CAGR giveback pp: {sealed.get('cagr_giveback_pp')}
- Score: {sealed.get('score')}

## Tip FIN names

- BASE names w/ 張: {books[BASE_ID]['tip_fin_names_with_board_lot']}
- CHAL names w/ 張: {books[CHAL_ID]['tip_fin_names_with_board_lot']}

## Reproduce

```bash
python3 scripts/e16_fin_within_sleeve_dual_paper_ledgers.py
python3 scripts/e16_fin_within_sleeve_month_end_monitor.py
```

Repro: `{OUT.relative_to(ROOT)}/`
"""
    (OUT / "reports" / "FIN_WITHIN_SLEEVE_DUAL_PAPER_OBSERVE.md").write_text(md, encoding="utf-8")
    OPS.joinpath("FIN_WITHIN_SLEEVE_DUAL_PAPER_OBSERVE_OPERATING.md").write_text(md, encoding="utf-8")
    print(json.dumps({"status": STATUS, "chal": CHAL_ID, "held": held, "sealed": sealed}, indent=2, default=str))


if __name__ == "__main__":
    main()
