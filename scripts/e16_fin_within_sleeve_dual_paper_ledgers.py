#!/usr/bin/env python3
"""FIN within-sleeve multi-paper ledgers — OPERATING OBSERVE (paper only).

Side-by-side Exact T+1 paper books @ charter capital 500M / board-lot 1000:
  BASE     FIN_EQUAL
  CHAL_RS  FIN_RS_SOFT_TILT_EXDIV          (Stage C locked top)
  CHAL_MIX FIN_MIX_EQUAL_RS_EXDIV λ=0.75   (MIX_L75 coexist candidate)

Human: 各檔各做各的 — open observe beside equal-split; mix tip-clean coexist.
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
    FIN_RS_SOFT_TILT_EXDIV,
    TEL_EQUAL,
    build_exdiv_buy_ok,
    build_name_scores,
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
    need_scores = policy in (FIN_RS_SOFT_TILT_EXDIV, FIN_MIX_EQUAL_RS_EXDIV)
    need_ok = need_scores
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
        fin_name_scores=fin_scores if need_scores else None,
        fin_buy_ok=fin_buy_ok if need_ok else None,
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

    runs = [
        ("base", BASE_ID, FIN_EQUAL, None, "base_fin_equal"),
        ("chal_rs", CHAL_RS_ID, FIN_RS_SOFT_TILT_EXDIV, None, CHAL_RS_SLUG),
        ("chal_mix", CHAL_MIX_LABEL, FIN_MIX_EQUAL_RS_EXDIV, MIX_LAMBDA, CHAL_MIX_SLUG),
    ]
    navs: dict[str, pd.DataFrame] = {}
    metas: dict[str, dict] = {}
    for key, label, policy, mix_lam, slug in runs:
        print(f"{label} sim @ 500M/1000 ...", flush=True)
        nav, fills, meta = _run(
            market,
            dividends,
            target,
            regime,
            policy=policy,
            fin_scores=fin_scores,
            fin_buy_ok=fin_buy_ok,
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
    joined = jb.merge(jrs, on="date", how="inner").merge(jmx, on="date", how="inner")
    joined[f"rel_{CHAL_RS_SLUG}_vs_base"] = joined[f"nav_{CHAL_RS_SLUG}"] / joined["nav_base"]
    joined[f"rel_{CHAL_MIX_SLUG}_vs_base"] = joined[f"nav_{CHAL_MIX_SLUG}"] / joined["nav_base"]
    joined.to_csv(OUT / "outputs" / "dual_paper_nav_compare.csv", index=False)

    books: dict = {}
    id_by_key = {
        "base": BASE_ID,
        "chal_rs": CHAL_RS_ID,
        "chal_mix": CHAL_MIX_LABEL,
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
            "加進 MIX_L75 (λ=0.75 EQUAL×RS_EXDIV) 第三本"
        ),
        "human_rationale": (
            "各檔各做各的 — ex-div dates + RS timing differ; "
            "MIX_L75 tip-clean coexist candidate from λ-grid"
        ),
        "stage_c": "STAGE_C_CANDIDATES_LOCKED",
        "mix_probe": "COEXIST_CANDIDATE_FOUND",
        "base_id": BASE_ID,
        "locked_challenger": CHAL_RS_ID,
        "mix_challenger": {
            "id": CHAL_MIX_LABEL,
            "financial_alloc": CHAL_MIX_ID,
            "fin_mix_lambda": MIX_LAMBDA,
            "definition": f"λ·FIN_EQUAL + (1−λ)·FIN_RS_SOFT_TILT_EXDIV with λ={MIX_LAMBDA}",
        },
        "books": [BASE_ID, CHAL_RS_ID, CHAL_MIX_LABEL],
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
        },
        "heldout_vs_base": {
            CHAL_RS_ID: held_rs,
            CHAL_MIX_LABEL: held_mx,
        },
        "sealed_vs_base": {
            CHAL_RS_ID: sealed_rs,
            CHAL_MIX_LABEL: sealed_mx,
        },
        "windows": books,
        "next_human": [
            "Month-end cadence via ops_month_end_paper_pack.py --refresh-ledgers",
            "Live FIN within-sleeve cutover still requires dedicated ACCEPT ballot",
        ],
        "non_actions": [
            "Paper-only; Soft-Frozen KEEP; live e21 FIN equal-split untouched",
            "Do not wire FIN_RS_SOFT_TILT_EXDIV or MIX_L75 into e21 without cutover ACCEPT",
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

Execution: capital **{CHARTER_CAPITAL:,.0f}** · lot **{CHARTER_LOT}** · Telecom=`TEL_EQUAL`

## Held-out vs BASE

| Challenger | MDD↑pp | CAGR giveback | Score |
|---|---:|---:|---:|
| `{CHAL_RS_ID}` | {held_rs.get('mdd_improve_pp')} | {held_rs.get('cagr_giveback_pp')} | {held_rs.get('score')} |
| `{CHAL_MIX_LABEL}` | {held_mx.get('mdd_improve_pp')} | {held_mx.get('cagr_giveback_pp')} | {held_mx.get('score')} |

## Sealed vs BASE

| Challenger | MDD↑pp | CAGR giveback | Score |
|---|---:|---:|---:|
| `{CHAL_RS_ID}` | {sealed_rs.get('mdd_improve_pp')} | {sealed_rs.get('cagr_giveback_pp')} | {sealed_rs.get('score')} |
| `{CHAL_MIX_LABEL}` | {sealed_mx.get('mdd_improve_pp')} | {sealed_mx.get('cagr_giveback_pp')} | {sealed_mx.get('score')} |

## Tip FIN names (張)

- BASE: {books[BASE_ID]['tip_fin_names_with_board_lot']}
- RS_EXDIV: {books[CHAL_RS_ID]['tip_fin_names_with_board_lot']}
- MIX_L75: {books[CHAL_MIX_LABEL]['tip_fin_names_with_board_lot']}

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
                "books": [BASE_ID, CHAL_RS_ID, CHAL_MIX_LABEL],
                "held_rs": held_rs,
                "held_mix": held_mx,
            },
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    main()
