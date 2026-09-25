#!/usr/bin/env python3
"""民營 native dual-paper ledgers — thin wrapper (OPERATING OBSERVE).

BASE PRIV_EQUAL ∥ CHAL PRIV_KD_MAY_Klt25_T15 on extended market with PRIV
universe patch via ``sim_context``. Soft-Frozen sleeve weights unchanged.
"""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import pandas as pd

import e16_soft_frozen_base as soft
import e50_early_stack_combined_nav as e50
from e16_fin_priv_native_optimize import (
    ACTIVE_SCORE,
    CAPITAL,
    LOT,
    PRIV_R3R4,
    PUB_R1,
    TEL,
    build_extended_market,
    held_score,
)
from e45_paper_harness import load_dividends
from ops_dual_paper_ledgers import (
    DualPaperLedgerSpec,
    LedgerResult,
    PreparedBooks,
    cli_main,
    live_kd_sim_kwargs,
    utc_now,
    write_json_md_pair,
)
from within_sleeve_alloc import (
    FIN_EQUAL,
    FIN_PRE_EXDIV_KD,
    TEL_EQUAL,
    build_kd_season_tilt_scores,
    build_pre_exdiv_window_buy_ok,
)

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


@contextmanager
def priv_universe() -> Iterator[None]:
    """Temporarily route FIN dollars to PRIV_R3R4 (same as run_book)."""
    old_fin, old_all = list(e50.FIN), list(e50.ALL)
    e50.FIN = list(PRIV_R3R4)
    e50.ALL = list(PRIV_R3R4) + TEL + ["0050"]
    try:
        yield
    finally:
        e50.FIN = old_fin
        e50.ALL = old_all


def _preflight() -> None:
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.8]
    assert soft.FIN == PUB_R1


def prepare(market: pd.DataFrame, dividends: pd.DataFrame) -> PreparedBooks:
    _p, _s, target, regime = e50.e16_features(market)
    cal = pd.to_datetime(market["date"]).drop_duplicates().sort_values()
    codes = list(PRIV_R3R4)
    scores = build_kd_season_tilt_scores(
        market,
        dividends,
        codes,
        k_thresh=float(NATIVE_KD["k_thresh"]),
        season_start=NATIVE_KD["season_start"],
        season_end=NATIVE_KD["season_end"],
        pre_days=int(NATIVE_KD["pre_days"]),
        active_score=ACTIVE_SCORE,
    )
    buy_ok = build_pre_exdiv_window_buy_ok(
        cal, dividends, codes, pre_days=int(NATIVE_KD["pre_days"]), also_stock_ex=True
    )
    return PreparedBooks(
        base_target=target,
        base_regime=regime,
        chal_target=target,
        chal_regime=regime,
        base_kwargs={
            "financial_alloc": FIN_EQUAL,
            "telecom_alloc": TEL_EQUAL,
        },
        chal_kwargs=live_kd_sim_kwargs(scores=scores, buy_ok=buy_ok),
        context={"native_kd": dict(NATIVE_KD)},
    )


def report(result: LedgerResult) -> None:
    from e45_paper_harness import WINDOWS_STANDARD, window_stats

    win_base = {
        w: window_stats(result.nav_base, a, b) for w, (a, b) in WINDOWS_STANDARD.items()
    }
    win_chal = {
        w: window_stats(result.nav_chal, a, b) for w, (a, b) in WINDOWS_STANDARD.items()
    }
    held = held_score(win_base["heldout_2019_plus"], win_chal["heldout_2019_plus"])
    sealed = held_score(win_base["sealed_2023_plus"], win_chal["sealed_2023_plus"])
    payload = {
        "generated_at_utc": utc_now(),
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
            BASE_ID: int(len(result.fills_base)),
            CHAL_ID: int(len(result.fills_chal)),
        },
        "default_status": "KEEP_OBSERVE",
        "posture": "research/ops/FIN_PRIV_NATIVE_OBSERVE_POSTURE.md",
        "runbook": "research/ops/FIN_PRIV_NATIVE_MONTH_END_RUNBOOK.md",
        "status_ballot": "research/ops/FIN_PRIV_NATIVE_OBSERVE_STATUS_BALLOT_DRAFT.md",
        "cutover_blocked": "research/ops/CUTOVER_CHECKLIST_FIN_PRIV_NATIVE.md",
        "next_human": [
            "Run month-end monitor on this dual-paper pair",
            "Default KEEP OBSERVE; status ballot is paper-only (no live wire)",
        ],
    }
    md = f"""# 民營 native dual-paper (OPERATING OBSERVE)

Status: `{STATUS}` · paper only · Soft-Frozen KEEP · live wire false
Default status: **KEEP OBSERVE** · posture `FIN_PRIV_NATIVE_OBSERVE_POSTURE.md`

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
python3 scripts/e16_fin_priv_native_dual_paper_ledgers.py
python3 scripts/e16_fin_priv_native_month_end_monitor.py
```

Runbook: `FIN_PRIV_NATIVE_MONTH_END_RUNBOOK.md` · checklist: `FIN_PRIV_NATIVE_DUAL_PAPER_OBSERVE_CHECKLIST.md`
Status ballot (DRAFT): `FIN_PRIV_NATIVE_OBSERVE_STATUS_BALLOT_DRAFT.md`
Repro: `{OUT.relative_to(ROOT)}/`
"""
    write_json_md_pair(
        out_dir=OUT,
        report_stem="fin_priv_native_dual_paper_observe",
        payload=payload,
        md_lines=md.strip().splitlines(),
        mirror_dirs=(OPS,),
        mirror_stem="FIN_PRIV_NATIVE_DUAL_PAPER_OBSERVE",
    )
    (OUT / "reports" / "FIN_PRIV_NATIVE_DUAL_PAPER_OBSERVE.md").write_text(
        md if md.endswith("\n") else md + "\n", encoding="utf-8"
    )
    (OPS / "FIN_PRIV_NATIVE_DUAL_PAPER_OBSERVE_OPERATING.md").write_text(
        md if md.endswith("\n") else md + "\n", encoding="utf-8"
    )


SPEC = DualPaperLedgerSpec(
    label="FIN_PRIV_NATIVE_DUAL_PAPER_OBSERVE_OPERATING",
    out_dir=OUT,
    base_id=BASE_ID,
    chal_id=CHAL_ID,
    prepare=prepare,
    base_nav_name="priv_equal_daily_nav.csv",
    chal_nav_name="priv_kd_may_klt25_t15_daily_nav.csv",
    write_fills=False,
    base_targets_name=None,
    capital=float(CAPITAL),
    lot_size=int(LOT),
    soft_frozen_clip=(0.6, 0.8),
    load_market_fn=build_extended_market,
    load_dividends_fn=load_dividends,
    preflight=_preflight,
    sim_context=priv_universe,
    report_fn=report,
    status=STATUS,
)


if __name__ == "__main__":
    raise SystemExit(cli_main(SPEC))
