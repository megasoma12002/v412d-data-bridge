#!/usr/bin/env python3
"""E45 M2 BIL_FX dual-paper ledgers — PREP only (AWAITING_HUMAN_ACCEPT).

Side-by-side Exact T+1 paper books:
  BASE (Soft-Frozen early-stack)
  M2_RELOC_BIL_FX_C50 (same stack + relocate to BIL×USDTWD mid @ c=0.50)

Status: AWAITING_HUMAN_ACCEPT — NOT OPERATING OBSERVE.
Does NOT cast ACCEPT OPEN. Does NOT edit Soft-Frozen / DEFAULT / stitch.
Does NOT add to ops_month_end_paper_pack.py until human ACCEPT.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from e45_crisis_core import build_m2_sleeve_schedule
from e45_m1_state_signal_paper import build_m1_state
from e45_m2_true_def_relocate_paper import CODE_BIL_FX, build_def_bars
from e45_paper_harness import (
    BOOK_BASE,
    CLAIM_STATUS,
    ROOT,
    WINDOWS_STANDARD,
    deltas_vs_base,
    e16_features,
    load_dividends,
    load_market,
    run_early_stack,
    window_stats,
)

OUT = ROOT / "repro/e45-m2-bil-fx-dual-paper-observe"
RESEARCH = ROOT / "research/e45"
OPS = ROOT / "research/ops"

BASE_ID = BOOK_BASE
CHAL_ID = "M2_RELOC_BIL_FX_C50"
CUT = 0.50
MODE = "RELOC_BIL_FX"
STATUS = "AWAITING_HUMAN_ACCEPT"


def main() -> None:
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)
    OPS.mkdir(parents=True, exist_ok=True)

    print("loading market + dividends ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, _s, target, regime = e16_features(market)

    print("building M1 intensity + BIL_FX bars ...", flush=True)
    state = build_m1_state(market)
    intensity_lag1 = state["s_t"].shift(1).fillna(0.0)
    def_bars = build_def_bars(pd.DatetimeIndex(sorted(market["date"].unique())))
    bil_bars = def_bars[def_bars["code"] == CODE_BIL_FX].copy()
    market_aug = pd.concat([market, bil_bars], ignore_index=True)
    sched = build_m2_sleeve_schedule(target, intensity_lag1, CUT, MODE)
    sched.to_csv(OUT / "outputs" / "m2_reloc_bil_fx_c50_sleeve_schedule.csv")

    print(f"{BASE_ID} sim ...", flush=True)
    nav_b, fills_b, meta_b = run_early_stack(
        market, target, regime, dividends, e45_exposure=None
    )

    print(f"{CHAL_ID} sim (DEF={CODE_BIL_FX}) ...", flush=True)
    nav_c, fills_c, meta_c = run_early_stack(
        market_aug,
        target,
        regime,
        dividends,
        e45_exposure=None,
        sleeve_weight_schedule=sched,
        def_code=CODE_BIL_FX,
        cost_multiple=1.0,
    )

    nav_b.to_csv(OUT / "outputs" / "base_e16_e18_e22_v2s_daily_nav.csv", index=False)
    nav_c.to_csv(OUT / "outputs" / "m2_reloc_bil_fx_c50_daily_nav.csv", index=False)
    fills_b.to_csv(OUT / "outputs" / "base_e16_e18_e22_v2s_fills.csv", index=False)
    fills_c.to_csv(OUT / "outputs" / "m2_reloc_bil_fx_c50_fills.csv", index=False)

    jb = nav_b[["date", "nav"]].rename(columns={"nav": "nav_base"})
    jc = nav_c[["date", "nav"]].rename(columns={"nav": "nav_m2_reloc_bil_fx_c50"})
    joined = jb.merge(jc, on="date", how="inner")
    joined["rel_chal_vs_base"] = joined["nav_m2_reloc_bil_fx_c50"] / joined["nav_base"]
    joined.to_csv(OUT / "outputs" / "dual_paper_nav_compare.csv", index=False)

    books: dict = {}
    for name, nav, meta in [(BASE_ID, nav_b, meta_b), (CHAL_ID, nav_c, meta_c)]:
        win = {w: window_stats(nav, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
        books[name] = {
            "exact_t1_ok": bool(meta.get("exact_t1_ok")),
            "mean_e45_exposure": meta.get("mean_e45_exposure"),
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
        "label": "E45_M2_BIL_FX_DUAL_PAPER_OBSERVE_PREP",
        "status": STATUS,
        "operating_observe": False,
        "live_wire": False,
        "soft_frozen_default_unchanged": True,
        "stitch_authorized": False,
        "cutover_authorized": False,
        "ballot": "E45_M2_RELOC_OBSERVE_OPEN_BALLOT_DRAFT (NOT ACCEPTED)",
        "base_id": BASE_ID,
        "locked_challenger": CHAL_ID,
        "mode": MODE,
        "cut": CUT,
        "def_code": CODE_BIL_FX,
        "def_honesty": "BIL × USDTWD mid — FX risk; mid optimistic; not TWD cash",
        "claim_status": CLAIM_STATUS,
        "exact_t1": {
            "base": books[BASE_ID]["exact_t1_ok"],
            "m2_reloc_bil_fx_c50": books[CHAL_ID]["exact_t1_ok"],
        },
        "heldout_vs_base": held,
        "sealed_vs_base": sealed,
        "windows": books,
        "next_human": [
            "Cast HOLD / ACCEPT OPEN / REJECT on draft observe ballot",
            "Only after ACCEPT OPEN: mark OPERATING and add to ops month-end pack",
        ],
        "non_actions": [
            "Do not treat AWAITING as OPERATING observe",
            "Do not Soft-Frozen / DEFAULT / stitch",
            "Do not merge DEF into live_market.csv",
        ],
    }
    (OUT / "reports" / "e45_m2_bil_fx_dual_paper_observe.json").write_text(
        json.dumps(proposal, indent=2, default=str) + "\n", encoding="utf-8"
    )

    md = f"""# E45 M2 BIL_FX dual-paper ledgers (PREP)

**Status:** `{STATUS}` — **NOT OPERATING**

| Book | Role |
|---|---|
| `{BASE_ID}` | Soft-Frozen early-stack ref |
| `{CHAL_ID}` | M2 relocate → `{CODE_BIL_FX}` @ c={CUT} |

**Honesty:** BIL × USDTWD mid — FX risk; mid optimistic; **not** TWD cash.

## Held-out vs BASE

- MDD improve pp: {held.get('mdd_improve_pp')}
- CAGR giveback pp: {held.get('cagr_giveback_pp')}
- Score: {held.get('score')}

## Sealed vs BASE

- MDD improve pp: {sealed.get('mdd_improve_pp')}
- CAGR giveback pp: {sealed.get('cagr_giveback_pp')}
- Score: {sealed.get('score')}

## Reproduce

```bash
python3 scripts/e45_m2_bil_fx_dual_paper_ledgers.py
python3 scripts/e45_m2_bil_fx_month_end_monitor.py
```

Repro: `{OUT.relative_to(ROOT)}/`
"""
    (OUT / "reports" / "E45_M2_BIL_FX_DUAL_PAPER_OBSERVE.md").write_text(md, encoding="utf-8")
    (OPS / "E45_M2_BIL_FX_DUAL_PAPER_OBSERVE_PREP.md").write_text(md, encoding="utf-8")
    print(json.dumps({"status": STATUS, "chal": CHAL_ID, "held": held}, indent=2, default=str))


if __name__ == "__main__":
    main()
