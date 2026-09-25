#!/usr/bin/env python3
"""FIN within-sleeve multi-paper ledgers — thin wrapper over MultiPaperLedgerSpec."""
from __future__ import annotations

import pandas as pd

from e45_paper_harness import ROOT
from e50_early_stack_combined_nav import FIN, e16_features
from ops_dual_paper_ledgers import (
    MultiChallengerLedgerBook,
    MultiLedgerResult,
    MultiPaperLedgerSpec,
    PreparedMultiBooks,
    cli_main_multi,
    utc_now,
    write_json_md_pair,
)
from within_sleeve_alloc import (
    FIN_EQUAL,
    FIN_MIX_EQUAL_RS_EXDIV,
    FIN_PRE_EXDIV_KD,
    FIN_RS_SOFT_TILT_EXDIV,
    TEL_EQUAL,
    build_exdiv_buy_ok,
    build_kd_season_tilt_scores,
    build_name_scores,
    build_pre_exdiv_window_buy_ok,
)

OUT = ROOT / "repro/fin-within-sleeve-dual-paper-observe"
OPS = ROOT / "research/ops"
BASE_ID = "FIN_EQUAL"
CHAL_RS_ID = "FIN_RS_SOFT_TILT_EXDIV"
CHAL_RS_SLUG = "fin_rs_soft_tilt_exdiv"
CHAL_MIX_LABEL = "MIX_L75"
CHAL_MIX_SLUG = "fin_mix_l75"
MIX_LAMBDA = 0.75
CHAL_KD_LABEL = "KD_OPT"
CHAL_KD_SLUG = "fin_kd_opt"
KD_OPT = {
    "id": "KD_APR15_MAY15_Klt30_T15",
    "season_start": (4, 15),
    "season_end": (5, 15),
    "k_thresh": 30.0,
    "pre_days": 15,
    "active_score": 1.5,
}


def _fin_kw(*, policy: str, scores=None, buy_ok=None, mix_lambda=None) -> dict:
    return {
        "financial_alloc": policy,
        "telecom_alloc": TEL_EQUAL,
        "fin_name_scores": scores,
        "fin_buy_ok": buy_ok,
        "fin_mix_lambda": mix_lambda,
    }


def prepare(market, dividends) -> PreparedMultiBooks:
    _p, _s, target, regime = e16_features(market)
    cal = pd.to_datetime(market["date"]).drop_duplicates().sort_values().to_numpy()
    fin_scores = build_name_scores(market, FIN)
    fin_buy_ok = build_exdiv_buy_ok(cal, dividends, FIN, also_stock_ex=True)
    kd_scores = build_kd_season_tilt_scores(
        market,
        dividends,
        FIN,
        k_thresh=float(KD_OPT["k_thresh"]),
        season_start=KD_OPT["season_start"],
        season_end=KD_OPT["season_end"],
        pre_days=int(KD_OPT["pre_days"]),
        active_score=float(KD_OPT["active_score"]),
    )
    kd_buy_ok = build_pre_exdiv_window_buy_ok(
        cal, dividends, FIN, pre_days=int(KD_OPT["pre_days"]), also_stock_ex=True
    )
    return PreparedMultiBooks(
        base_target=target,
        base_regime=regime,
        base_kwargs=_fin_kw(policy=FIN_EQUAL),
        challengers={
            CHAL_RS_ID: (
                target,
                regime,
                _fin_kw(policy=FIN_RS_SOFT_TILT_EXDIV, scores=fin_scores, buy_ok=fin_buy_ok),
                {},
            ),
            CHAL_MIX_LABEL: (
                target,
                regime,
                _fin_kw(
                    policy=FIN_MIX_EQUAL_RS_EXDIV,
                    scores=fin_scores,
                    buy_ok=fin_buy_ok,
                    mix_lambda=MIX_LAMBDA,
                ),
                {},
            ),
            CHAL_KD_LABEL: (
                target,
                regime,
                _fin_kw(policy=FIN_PRE_EXDIV_KD, scores=kd_scores, buy_ok=kd_buy_ok),
                {},
            ),
        },
        context={"kd_opt_id": KD_OPT["id"]},
    )


def report(result: MultiLedgerResult) -> None:
    payload = {
        "generated_at_utc": utc_now(),
        "label": "FIN_WITHIN_SLEEVE_DUAL_PAPER_OBSERVE",
        "status": "OPERATING_OBSERVE",
        "live_wire": False,
        "soft_frozen_unchanged": True,
        "base_id": BASE_ID,
        "challengers": [c.chal_id for c in SPEC.challengers],
        "kd_optimal_id": KD_OPT["id"],
        "books": result.books,
        "cutover_blocked": True,
    }
    lines = [
        "# FIN within-sleeve multi-paper observe",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Books: `{BASE_ID}` ∥ `{CHAL_RS_ID}` ∥ `{CHAL_MIX_LABEL}` ∥ `{CHAL_KD_LABEL}`",
        "Soft-Frozen KEEP · live FIN equal-split untouched · no live wire",
        "",
        "```bash",
        "python3 scripts/e16_fin_within_sleeve_dual_paper_ledgers.py",
        "```",
        "",
    ]
    write_json_md_pair(
        out_dir=OUT,
        report_stem="fin_within_sleeve_dual_paper_observe",
        payload=payload,
        md_lines=lines,
        mirror_dirs=(OPS,),
        mirror_stem="FIN_WITHIN_SLEEVE_DUAL_PAPER_OBSERVE",
    )


SPEC = MultiPaperLedgerSpec(
    label="FIN_WITHIN_SLEEVE_DUAL_PAPER_OBSERVE",
    out_dir=OUT,
    base_id=BASE_ID,
    base_nav_name="base_fin_equal_daily_nav.csv",
    prepare=prepare,
    challengers=(
        MultiChallengerLedgerBook(
            chal_id=CHAL_RS_ID,
            nav_name=f"{CHAL_RS_SLUG}_daily_nav.csv",
            compare_col=f"nav_{CHAL_RS_SLUG}",
        ),
        MultiChallengerLedgerBook(
            chal_id=CHAL_MIX_LABEL,
            nav_name=f"{CHAL_MIX_SLUG}_daily_nav.csv",
            compare_col=f"nav_{CHAL_MIX_SLUG}",
        ),
        MultiChallengerLedgerBook(
            chal_id=CHAL_KD_LABEL,
            nav_name=f"{CHAL_KD_SLUG}_daily_nav.csv",
            compare_col=f"nav_{CHAL_KD_SLUG}",
        ),
    ),
    base_targets_name=None,
    soft_frozen_clip=(0.6, 0.8),
    report_fn=report,
)

if __name__ == "__main__":
    raise SystemExit(cli_main_multi(SPEC))
