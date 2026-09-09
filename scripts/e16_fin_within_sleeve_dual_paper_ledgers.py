#!/usr/bin/env python3
"""FIN within-sleeve multi-paper ledgers — OPERATING OBSERVE (paper only).

Side-by-side Exact T+1 paper books @ charter capital 500M / board-lot 1000:
  BASE     FIN_EQUAL
  CHAL_RS  FIN_RS_SOFT_TILT_EXDIV          (Stage C locked top)
  CHAL_MIX FIN_MIX_EQUAL_RS_EXDIV λ=0.75   (MIX_L75 coexist candidate)
  CHAL_KD  FIN_PRE_EXDIV_KD                (KD_OPT = KD_APR15_MAY15_Klt30_T15)

Human: 各檔各做各的 — open observe beside equal-split; mix tip-clean coexist;
       KD optimal as 4th OPERATING observe (paper only).
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
    FIN_MIX_EQUAL_RS_EXDIV,
    FIN_PRE_EXDIV_KD,
    FIN_RS_SOFT_TILT_EXDIV,
    TEL_EQUAL,
    build_exdiv_buy_ok,
    build_kd_season_tilt_scores,
    build_name_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/fin-within-sleeve-dual-paper-observe"
OPS = ROOT / "research/ops"

BASE_ID = "FIN_EQUAL"
CHAL_RS_ID = "FIN_RS_SOFT_TILT_EXDIV"
CHAL_RS_SLUG = "fin_rs_soft_tilt_exdiv"
CHAL_MIX_ID = "FIN_MIX_EQUAL_RS_EXDIV"
CHAL_MIX_LABEL = "MIX_L75"
CHAL_MIX_SLUG = "fin_mix_l75"
MIX_LAMBDA = 0.75
CHAL_KD_ID = FIN_PRE_EXDIV_KD
CHAL_KD_LABEL = "KD_OPT"
CHAL_KD_SLUG = "fin_kd_opt"
# Paper optimal from FIN_PRE_EXDIV_KD_OPTIMIZE (KD_APR15_MAY15_Klt30_T15)
KD_OPT = {
    "id": "KD_APR15_MAY15_Klt30_T15",
    "season_start": (4, 15),
    "season_end": (5, 15),
    "k_thresh": 30.0,
    "pre_days": 15,
    "active_score": 1.5,
}
STATUS = "OPERATING_OBSERVE"
CHARTER_CAPITAL = 500_000_000.0
CHARTER_LOT = BOARD_LOT


def _run(
    market,
    dividends,
    target,
    regime,
    *,
    policy: str,
    fin_scores,
    fin_buy_ok,
    fin_mix_lambda: float | None = None,
):
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
        fin_name_scores=fin_scores,
        fin_buy_ok=fin_buy_ok,
        fin_mix_lambda=fin_mix_lambda,
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

    print(
        f"building KD_OPT scores ({KD_OPT['id']}: "
        f"season {KD_OPT['season_start']}–{KD_OPT['season_end']} "
        f"K<{KD_OPT['k_thresh']} T−{KD_OPT['pre_days']}) ...",
        flush=True,
    )
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
        cal,
        dividends,
        FIN,
        pre_days=int(KD_OPT["pre_days"]),
        also_stock_ex=True,
    )

    runs = [
        ("base", BASE_ID, FIN_EQUAL, None, None, None, "base_fin_equal"),
        ("chal_rs", CHAL_RS_ID, FIN_RS_SOFT_TILT_EXDIV, fin_scores, fin_buy_ok, None, CHAL_RS_SLUG),
        (
            "chal_mix",
            CHAL_MIX_LABEL,
            FIN_MIX_EQUAL_RS_EXDIV,
            fin_scores,
            fin_buy_ok,
            MIX_LAMBDA,
            CHAL_MIX_SLUG,
        ),
        (
            "chal_kd",
            CHAL_KD_LABEL,
            CHAL_KD_ID,
            kd_scores,
            kd_buy_ok,
            None,
            CHAL_KD_SLUG,
        ),
    ]
    navs: dict[str, pd.DataFrame] = {}
    metas: dict[str, dict] = {}
    for key, label, policy, scores, buy_ok, mix_lam, slug in runs:
        print(f"{label} sim @ 500M/1000 ...", flush=True)
        nav, fills, meta = _run(
            market,
            dividends,
            target,
            regime,
            policy=policy,
            fin_scores=scores,
            fin_buy_ok=buy_ok,
            fin_mix_lambda=mix_lam,
        )
        assert meta.get("exact_t1_ok"), label
        nav.to_csv(OUT / "outputs" / f"{slug}_daily_nav.csv", index=False)
        fills.to_csv(OUT / "outputs" / f"{slug}_fills.csv", index=False)
        navs[key] = nav
        metas[key] = meta

    jb = navs["base"][["date", "nav"]].rename(columns={"nav": "nav_base"})
    jrs = navs["chal_rs"][["date", "nav"]].rename(columns={"nav": f"nav_{CHAL_RS_SLUG}"})
    jmx = navs["chal_mix"][["date", "nav"]].rename(columns={"nav": f"nav_{CHAL_MIX_SLUG}"})
    jkd = navs["chal_kd"][["date", "nav"]].rename(columns={"nav": f"nav_{CHAL_KD_SLUG}"})
    joined = (
        jb.merge(jrs, on="date", how="inner")
        .merge(jmx, on="date", how="inner")
        .merge(jkd, on="date", how="inner")
    )
    joined[f"rel_{CHAL_RS_SLUG}_vs_base"] = joined[f"nav_{CHAL_RS_SLUG}"] / joined["nav_base"]
    joined[f"rel_{CHAL_MIX_SLUG}_vs_base"] = joined[f"nav_{CHAL_MIX_SLUG}"] / joined["nav_base"]
    joined[f"rel_{CHAL_KD_SLUG}_vs_base"] = joined[f"nav_{CHAL_KD_SLUG}"] / joined["nav_base"]
    joined.to_csv(OUT / "outputs" / "dual_paper_nav_compare.csv", index=False)

    books: dict = {}
    id_by_key = {
        "base": BASE_ID,
        "chal_rs": CHAL_RS_ID,
        "chal_mix": CHAL_MIX_LABEL,
        "chal_kd": CHAL_KD_LABEL,
    }
    for key, book_id in id_by_key.items():
        nav = navs[key]
        meta = metas[key]
        win = {w: window_stats(nav, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
        end_pos = meta.get("end_positions") or {}
        fin_held = {c: float(end_pos.get(c, 0.0)) for c in FIN}
        books[book_id] = {
            "exact_t1_ok": bool(meta.get("exact_t1_ok")),
            "lot_size": int(meta.get("lot_size", CHARTER_LOT)),
            "capital": CHARTER_CAPITAL,
            "financial_alloc": meta.get("financial_alloc"),
            "fin_mix_lambda": meta.get("fin_mix_lambda"),
            "tip_fin_positions": fin_held,
            "tip_fin_names_with_board_lot": int(
                sum(1 for v in fin_held.values() if abs(v) >= CHARTER_LOT - 1e-9)
            ),
            "windows": win,
        }

    held_rs = deltas_vs_base(
        books[BASE_ID]["windows"]["heldout_2019_plus"],
        books[CHAL_RS_ID]["windows"]["heldout_2019_plus"],
    )
    sealed_rs = deltas_vs_base(
        books[BASE_ID]["windows"]["sealed_2023_plus"],
        books[CHAL_RS_ID]["windows"]["sealed_2023_plus"],
    )
    held_mx = deltas_vs_base(
        books[BASE_ID]["windows"]["heldout_2019_plus"],
        books[CHAL_MIX_LABEL]["windows"]["heldout_2019_plus"],
    )
    sealed_mx = deltas_vs_base(
        books[BASE_ID]["windows"]["sealed_2023_plus"],
        books[CHAL_MIX_LABEL]["windows"]["sealed_2023_plus"],
    )
    held_kd = deltas_vs_base(
        books[BASE_ID]["windows"]["heldout_2019_plus"],
        books[CHAL_KD_LABEL]["windows"]["heldout_2019_plus"],
    )
    sealed_kd = deltas_vs_base(
        books[BASE_ID]["windows"]["sealed_2023_plus"],
        books[CHAL_KD_LABEL]["windows"]["sealed_2023_plus"],
    )

    proposal = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "FIN_WITHIN_SLEEVE_DUAL_PAPER_OBSERVE_OPERATING",
        "status": STATUS,
        "operating_observe": True,
        "live_wire": False,
        "soft_frozen_default_unchanged": True,
        "cutover_authorized": False,
        "ballot": (
            "dual-paper 觀察 FIN_RS_SOFT_TILT_EXDIV 並排 FIN_EQUAL；"
            "加進 MIX_L75 (λ=0.75 EQUAL×RS_EXDIV) 第三本；"
            "加進 KD_OPT (KD_APR15_MAY15_Klt30_T15) 第四本"
        ),
        "human_rationale": (
            "各檔各做各的 — ex-div dates + RS timing differ; "
            "MIX_L75 tip-clean coexist candidate from λ-grid; "
            "KD_OPT paper optimal (tip PASS + max held-out) from PRE_EXDIV_KD optimize"
        ),
        "stage_c": "STAGE_C_CANDIDATES_LOCKED",
        "mix_probe": "COEXIST_CANDIDATE_FOUND",
        "kd_probe": "OPTIMAL_SELECTED_OBSERVE",
        "base_id": BASE_ID,
        "locked_challenger": CHAL_RS_ID,
        "mix_challenger": {
            "id": CHAL_MIX_LABEL,
            "financial_alloc": CHAL_MIX_ID,
            "fin_mix_lambda": MIX_LAMBDA,
            "definition": f"λ·FIN_EQUAL + (1−λ)·FIN_RS_SOFT_TILT_EXDIV with λ={MIX_LAMBDA}",
        },
        "kd_challenger": {
            "id": CHAL_KD_LABEL,
            "financial_alloc": CHAL_KD_ID,
            "optimal_id": KD_OPT["id"],
            "params": {
                "season_start": list(KD_OPT["season_start"]),
                "season_end": list(KD_OPT["season_end"]),
                "k_thresh": KD_OPT["k_thresh"],
                "pre_days": KD_OPT["pre_days"],
                "active_score": KD_OPT["active_score"],
            },
            "definition": (
                f"FIN_PRE_EXDIV_KD season {KD_OPT['season_start']}–{KD_OPT['season_end']} "
                f"first Yahoo K9 < {KD_OPT['k_thresh']} soft-tilt; "
                f"skip buy cash-ex T−{KD_OPT['pre_days']}…T0 (+ stock ex)"
            ),
        },
        "books": [BASE_ID, CHAL_RS_ID, CHAL_MIX_LABEL, CHAL_KD_LABEL],
        "execution_context": {
            "capital": CHARTER_CAPITAL,
            "board_lot": CHARTER_LOT,
            "e22_books": "E22_v2s_tw",
            "telecom_held_at": TEL_EQUAL,
        },
        "exact_t1": {
            "base": books[BASE_ID]["exact_t1_ok"],
            "chal_rs": books[CHAL_RS_ID]["exact_t1_ok"],
            "chal_mix": books[CHAL_MIX_LABEL]["exact_t1_ok"],
            "chal_kd": books[CHAL_KD_LABEL]["exact_t1_ok"],
        },
        "heldout_vs_base": {
            CHAL_RS_ID: held_rs,
            CHAL_MIX_LABEL: held_mx,
            CHAL_KD_LABEL: held_kd,
        },
        "sealed_vs_base": {
            CHAL_RS_ID: sealed_rs,
            CHAL_MIX_LABEL: sealed_mx,
            CHAL_KD_LABEL: sealed_kd,
        },
        "windows": books,
        "next_human": [
            "Month-end cadence via ops_month_end_paper_pack.py --refresh-ledgers",
            "Live FIN within-sleeve cutover still requires dedicated ACCEPT ballot",
            "Optional later: λ·EQUAL+(1−λ)·KD_OPT mix (not required now)",
        ],
        "non_actions": [
            "Paper-only; Soft-Frozen KEEP; live e21 FIN equal-split untouched",
            "Do not wire FIN_RS_SOFT_TILT_EXDIV, MIX_L75, or KD_OPT into e21 without cutover ACCEPT",
            "Stage B hard policies remain STOP",
        ],
    }
    (OUT / "reports" / "fin_within_sleeve_dual_paper_observe.json").write_text(
        json.dumps(proposal, indent=2, default=str) + "\n", encoding="utf-8"
    )
    OPS.joinpath("FIN_WITHIN_SLEEVE_DUAL_PAPER_OBSERVE.json").write_text(
        json.dumps(proposal, indent=2, default=str) + "\n", encoding="utf-8"
    )

    md = f"""# FIN within-sleeve multi-paper (OPERATING OBSERVE)

**Status:** `{STATUS}` — **paper only** · Soft-Frozen **KEEP** · live wire **false**

| Book | Role |
|---|---|
| `{BASE_ID}` | Equal-split Financial sleeve (control) |
| `{CHAL_RS_ID}` | Stage C locked: RS soft-tilt + ex-div skip-buy |
| `{CHAL_MIX_LABEL}` | Mix coexist: λ={MIX_LAMBDA} EQUAL + (1−λ) RS_EXDIV |
| `{CHAL_KD_LABEL}` | KD optimal: `{KD_OPT['id']}` (Apr15–May15 K&lt;{KD_OPT['k_thresh']} · T−{KD_OPT['pre_days']}) |

Execution: capital **{CHARTER_CAPITAL:,.0f}** · lot **{CHARTER_LOT}** · Telecom=`TEL_EQUAL`

## Held-out vs BASE

| Challenger | MDD↑pp | CAGR giveback | Score |
|---|---:|---:|---:|
| `{CHAL_RS_ID}` | {held_rs.get('mdd_improve_pp')} | {held_rs.get('cagr_giveback_pp')} | {held_rs.get('score')} |
| `{CHAL_MIX_LABEL}` | {held_mx.get('mdd_improve_pp')} | {held_mx.get('cagr_giveback_pp')} | {held_mx.get('score')} |
| `{CHAL_KD_LABEL}` | {held_kd.get('mdd_improve_pp')} | {held_kd.get('cagr_giveback_pp')} | {held_kd.get('score')} |

## Sealed vs BASE

| Challenger | MDD↑pp | CAGR giveback | Score |
|---|---:|---:|---:|
| `{CHAL_RS_ID}` | {sealed_rs.get('mdd_improve_pp')} | {sealed_rs.get('cagr_giveback_pp')} | {sealed_rs.get('score')} |
| `{CHAL_MIX_LABEL}` | {sealed_mx.get('mdd_improve_pp')} | {sealed_mx.get('cagr_giveback_pp')} | {sealed_mx.get('score')} |
| `{CHAL_KD_LABEL}` | {sealed_kd.get('mdd_improve_pp')} | {sealed_kd.get('cagr_giveback_pp')} | {sealed_kd.get('score')} |

## Tip FIN names (張)

- BASE: {books[BASE_ID]['tip_fin_names_with_board_lot']}
- RS_EXDIV: {books[CHAL_RS_ID]['tip_fin_names_with_board_lot']}
- MIX_L75: {books[CHAL_MIX_LABEL]['tip_fin_names_with_board_lot']}
- KD_OPT: {books[CHAL_KD_LABEL]['tip_fin_names_with_board_lot']}

## Reproduce

```bash
python3 scripts/e16_fin_within_sleeve_dual_paper_ledgers.py
python3 scripts/e16_fin_within_sleeve_month_end_monitor.py
```

Repro: `{OUT.relative_to(ROOT)}/`
"""
    (OUT / "reports" / "FIN_WITHIN_SLEEVE_DUAL_PAPER_OBSERVE.md").write_text(md, encoding="utf-8")
    OPS.joinpath("FIN_WITHIN_SLEEVE_DUAL_PAPER_OBSERVE_OPERATING.md").write_text(md, encoding="utf-8")
    print(
        json.dumps(
            {
                "status": STATUS,
                "books": [BASE_ID, CHAL_RS_ID, CHAL_MIX_LABEL, CHAL_KD_LABEL],
                "held_rs": held_rs,
                "held_mix": held_mx,
                "held_kd": held_kd,
            },
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    main()
