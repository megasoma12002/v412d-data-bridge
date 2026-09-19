#!/usr/bin/env python3
"""民股／四類 × MDD New Mechanism N1 — FinPriv regime membership Stage A.

Charter: research/ops/PRIV_MDD_NEW_MECHANISM_CHARTER.md
Frozen offense cell SF4_P60-90_V0-15_F10_KD — do not retune clips.
Triggers: FinPriv sleeve-local DD and/or FinPriv vs FinPub relative 60d return
(NOT TAIEX DD ∈ {−8%, −10%} search — that pairing is exhausted).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import e16_pub_priv_coexist_mdd_stage_a as base
import e16_soft_frozen_4sleeve as sf4
import e16_soft_frozen_base as soft
import e50_early_stack_combined_nav as e50
from e16_private_fin_holdings_rescreen import PRIV_R3R4, PUB_R1, TEL
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, window_stats
from tw_share_lots import BOARD_LOT
from within_sleeve_alloc import FIN_EQUAL, FIN_PRE_EXDIV_KD, TEL_EQUAL

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/priv-mdd-new-mech-n1-stagea"
RESEARCH = ROOT / "research/ops"
CAPITAL = float(base.CAPITAL)
LOT = int(BOARD_LOT)
E22_PAPER = base.E22_PAPER
SLEEVE_COLS = ["FinPub", "FinPriv", "Telecom", "0050"]

OFFENSE = {
    "pub_lo": 0.60,
    "pub_hi": 0.90,
    "priv_lo": 0.00,
    "priv_hi": 0.15,
    "prior_frac": 0.10,
    "priv_pol": FIN_PRE_EXDIV_KD,
    "id": "SF4_P60-90_V0-15_F10_KD",
}
DEFENCE_CTRL = {
    "pub_lo": 0.60,
    "pub_hi": 0.90,
    "priv_lo": 0.00,
    "priv_hi": 0.00,
    "prior_frac": 0.00,
    "priv_pol": FIN_EQUAL,
    "id": "SF4_CTRL_PUB_ONLY",
}

# N1 predeclared grids (charter §5)
LOCAL_THRS = (-0.06, -0.08, -0.10)
REL_THRS = (-0.03, -0.05, -0.08)
# Mid-cell OR only
DUAL_LOCAL = -0.08
DUAL_REL = -0.05
L4_REF_THR = -0.08  # reference only — not a search axis


def _sim_sf4(market, dividends, target4, regime, *, book_id: str, meta_extra: dict):
    old_fin, old_all = list(e50.FIN), list(e50.ALL)
    fin_codes = list(PUB_R1) + list(PRIV_R3R4)
    e50.FIN = fin_codes
    e50.ALL = fin_codes + list(TEL) + ["0050"]
    try:
        scores, buy_ok = base._kd_panels(market, dividends, fin_codes)
        nav, fills, meta = e50.simulate_core(
            market,
            target4,
            regime,
            dividends,
            apply_e22=True,
            apply_stock_div=True,
            e22_version=E22_PAPER,
            capital=CAPITAL,
            lot_size=LOT,
            financial_alloc=FIN_PRE_EXDIV_KD,
            telecom_alloc=TEL_EQUAL,
            fin_name_scores=scores,
            fin_buy_ok=buy_ok,
            fin_pub_codes=PUB_R1,
            fin_priv_codes=PRIV_R3R4,
            fin_pub_alloc=FIN_PRE_EXDIV_KD,
            fin_priv_alloc=meta_extra.get("priv_pol", FIN_PRE_EXDIV_KD),
        )
        assert meta.get("exact_t1_ok"), book_id
        win = {w: window_stats(nav, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
        end_pos = meta.get("end_positions") or {}
        return {
            "id": book_id,
            "nav": nav,
            "windows": win,
            "n_fills": int(len(fills)),
            "meta": meta,
            "mechanism": meta_extra.get("mechanism"),
            "priv_policy": meta_extra.get("priv_pol"),
            "fin_pub_clip": meta_extra.get("fin_pub_clip"),
            "fin_priv_clip": meta_extra.get("fin_priv_clip"),
            "prior_priv_frac": meta_extra.get("prior_priv_frac"),
            "n1_family": meta_extra.get("n1_family"),
            "n1_local_thr": meta_extra.get("n1_local_thr"),
            "n1_rel_thr": meta_extra.get("n1_rel_thr"),
            "gate_on_share": meta_extra.get("gate_on_share"),
            "tip_pub": sum(1 for c in PUB_R1 if abs(float(end_pos.get(c, 0.0))) >= LOT - 1e-9),
            "tip_priv": sum(1 for c in PRIV_R3R4 if abs(float(end_pos.get(c, 0.0))) >= LOT - 1e-9),
        }
    finally:
        e50.FIN = old_fin
        e50.ALL = old_all


def build_sf4_pair(market, cfg: dict):
    _prices, _sleeve, target, regime, _score = sf4.build_4sleeve_targets(
        market,
        fin_pub_lo=cfg["pub_lo"],
        fin_pub_hi=cfg["pub_hi"],
        fin_priv_lo=cfg["priv_lo"],
        fin_priv_hi=cfg["priv_hi"],
        prior_priv_frac=cfg["prior_frac"],
    )
    return target, regime


def sleeve_nav_features(market: pd.DataFrame) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Equal-weight FinPub/FinPriv sleeve NAV + relative 60d return (pp as fraction)."""
    prices = (
        market.pivot(index="date", columns="code", values="adj_close")
        .sort_index()
        .ffill()
    )
    rets = prices.pct_change(fill_method=None).fillna(0.0)
    pub_r = rets[list(PUB_R1)].mean(axis=1)
    priv_r = rets[list(PRIV_R3R4)].mean(axis=1)
    pub_nav = (1.0 + pub_r).cumprod()
    priv_nav = (1.0 + priv_r).cumprod()
    priv_dd = priv_nav / priv_nav.rolling(252, min_periods=60).max() - 1.0
    # 60d cumulative relative return: FinPriv − FinPub
    rel_60 = (priv_nav / priv_nav.shift(60) - 1.0) - (pub_nav / pub_nav.shift(60) - 1.0)
    return priv_dd, rel_60, pub_nav


def apply_priv_off_path(
    offense: pd.DataFrame,
    defence: pd.DataFrame,
    flag: pd.Series,
) -> tuple[pd.DataFrame, pd.Series]:
    """Path-switch to pub-only 四類 weights while FinPriv gate is ON (OFF membership)."""
    common = offense.index.intersection(defence.index).intersection(flag.index)
    f = flag.reindex(common).fillna(False).astype(bool)
    out = offense.loc[common, SLEEVE_COLS].astype(float).copy()
    def_aligned = defence.loc[common, SLEEVE_COLS].astype(float)
    out.loc[f.values, SLEEVE_COLS] = def_aligned.loc[f.values, SLEEVE_COLS].to_numpy()
    s = out.sum(axis=1).replace(0.0, 1.0)
    out = out.div(s, axis=0)
    return out, f


def apply_l4_taiex_ref(offense, defence, market, dd_thr: float):
    """Reference-only prior closest (TAIEX DD) — not an N1 search axis."""
    prices = (
        market.pivot(index="date", columns="code", values="adj_close")
        .sort_index()
        .ffill()
    )
    taiex = prices["TAIEX"]
    peak = taiex.rolling(252, min_periods=120).max()
    dd = taiex / peak - 1.0
    flag = (dd <= float(dd_thr)).fillna(False)
    return apply_priv_off_path(offense, defence, flag)


def _meta_base(mechanism: str, **extra) -> dict:
    return {
        "mechanism": mechanism,
        "priv_pol": OFFENSE["priv_pol"],
        "fin_pub_clip": [OFFENSE["pub_lo"], OFFENSE["pub_hi"]],
        "fin_priv_clip": [OFFENSE["priv_lo"], OFFENSE["priv_hi"]],
        "prior_priv_frac": OFFENSE["prior_frac"],
        **extra,
    }


def _extend_rank(row: dict, src: dict) -> dict:
    row = dict(row)
    for k in ("n1_family", "n1_local_thr", "n1_rel_thr", "gate_on_share"):
        if k in src:
            row[k] = src[k]
    return row


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "outputs").mkdir(exist_ok=True)
    assert list(soft.SOFT_FROZEN_FIN_CLIP) == [0.6, 0.9]

    print("building extended market ...", flush=True)
    market = base.build_extended_market()
    dividends = load_dividends()

    print("baseline LIVE_PUB_KD ...", flush=True)
    live = base.run_live_pub_kd(market, dividends)
    results = {"LIVE_PUB_KD": live}

    print("SF4 offense + defence targets ...", flush=True)
    off_t, off_r = build_sf4_pair(market, OFFENSE)
    def_t, _def_r = build_sf4_pair(market, DEFENCE_CTRL)
    priv_dd, rel_60, _pub_nav = sleeve_nav_features(market)

    print("SF4_OFFENSE ...", flush=True)
    results["SF4_OFFENSE"] = _sim_sf4(
        market,
        dividends,
        off_t,
        off_r,
        book_id="SF4_OFFENSE",
        meta_extra=_meta_base("SF4_FROZEN", n1_family="CONTROL"),
    )

    print("SF4_L4_08_REF (reference only) ...", flush=True)
    l4_t, l4_flag = apply_l4_taiex_ref(off_t, def_t, market, L4_REF_THR)
    results["SF4_L4_08_REF"] = _sim_sf4(
        market,
        dividends,
        l4_t,
        off_r.reindex(l4_t.index).ffill().bfill(),
        book_id="SF4_L4_08_REF",
        meta_extra=_meta_base(
            "REF_TAIEX_L4_08",
            n1_family="REF_L4",
            gate_on_share=float(l4_flag.mean()) if len(l4_flag) else None,
        ),
    )

    for thr in LOCAL_THRS:
        tag = f"LOCAL_{abs(int(round(thr * 100))):02d}"
        bid = f"N1_{tag}"
        print(f"{bid} ...", flush=True)
        flag = (priv_dd <= float(thr)).fillna(False)
        tgt, f = apply_priv_off_path(off_t, def_t, flag)
        results[bid] = _sim_sf4(
            market,
            dividends,
            tgt,
            off_r.reindex(tgt.index).ffill().bfill(),
            book_id=bid,
            meta_extra=_meta_base(
                f"N1_PRIV_OFF_{tag}",
                n1_family="LOCAL",
                n1_local_thr=thr,
                gate_on_share=float(f.mean()) if len(f) else None,
            ),
        )

    for thr in REL_THRS:
        tag = f"REL_{abs(int(round(thr * 100))):02d}"
        bid = f"N1_{tag}"
        print(f"{bid} ...", flush=True)
        flag = (rel_60 <= float(thr)).fillna(False)
        tgt, f = apply_priv_off_path(off_t, def_t, flag)
        results[bid] = _sim_sf4(
            market,
            dividends,
            tgt,
            off_r.reindex(tgt.index).ffill().bfill(),
            book_id=bid,
            meta_extra=_meta_base(
                f"N1_PRIV_OFF_{tag}",
                n1_family="REL",
                n1_rel_thr=thr,
                gate_on_share=float(f.mean()) if len(f) else None,
            ),
        )

    bid = "N1_DUAL_L08_R05"
    print(f"{bid} ...", flush=True)
    flag = ((priv_dd <= float(DUAL_LOCAL)) | (rel_60 <= float(DUAL_REL))).fillna(False)
    tgt, f = apply_priv_off_path(off_t, def_t, flag)
    results[bid] = _sim_sf4(
        market,
        dividends,
        tgt,
        off_r.reindex(tgt.index).ffill().bfill(),
        book_id=bid,
        meta_extra=_meta_base(
            "N1_PRIV_OFF_DUAL_L08_R05",
            n1_family="DUAL",
            n1_local_thr=DUAL_LOCAL,
            n1_rel_thr=DUAL_REL,
            gate_on_share=float(f.mean()) if len(f) else None,
        ),
    )

    asof = pd.to_datetime(live["nav"]["date"]).max()
    ranked = []
    for bid, row in results.items():
        if bid == "LIVE_PUB_KD":
            continue
        rr = base.rank_row(live, row, asof)
        ranked.append(_extend_rank(rr, row))
    ranked.sort(key=lambda r: r["score_mdd"], reverse=True)
    n1_ranked = [r for r in ranked if str(r.get("n1_family") or "").startswith(("LOCAL", "REL", "DUAL"))]
    coexist = [r for r in ranked if r["coexist"]]
    n1_coexist = [r for r in coexist if r["id"].startswith("N1_")]

    if n1_coexist:
        status = "STAGE_A_CANDIDATES"
    elif any(r["gates"]["sealed_mdd"] for r in n1_ranked):
        status = "STAGE_A_SEALED_MDD_PASS_OTHER_GATES_FAIL"
    elif any(r["score_mdd"] > 0 for r in n1_ranked):
        status = "STAGE_A_SCORE_POS_GATES_FAIL"
    else:
        status = "STOP_NO_MDD_COEXIST_VS_LIVE_PUB_KD"

    keep = {"LIVE_PUB_KD", "SF4_OFFENSE", "SF4_L4_08_REF"} | {
        r["id"] for r in n1_coexist
    } | {r["id"] for r in n1_ranked[:5]}
    for bid in keep:
        if bid in results:
            results[bid]["nav"].to_csv(OUT / "outputs" / f"{bid}_daily_nav.csv", index=False)

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "PRIV_MDD_NEW_MECH_N1_STAGE_A",
        "status": status,
        "charter": "research/ops/PRIV_MDD_NEW_MECHANISM_CHARTER.md",
        "prior_stops": [
            "research/ops/PUB_PRIV_COEXIST_MDD_DECISION_PACK.md",
            "research/ops/SF4_DEFENCE_MDD_DECISION_PACK.md",
        ],
        "live_wire": False,
        "soft_frozen_clip": list(soft.SOFT_FROZEN_FIN_CLIP),
        "baseline": "LIVE_PUB_KD",
        "frozen_offense": OFFENSE["id"],
        "asof": str(pd.Timestamp(asof).date()),
        "n_challengers": len(ranked),
        "n_n1_challengers": len(n1_ranked),
        "ranked_vs_live_pub_kd": ranked,
        "coexist_ids": [r["id"] for r in coexist],
        "n1_coexist_ids": [r["id"] for r in n1_coexist],
        "best": ranked[0] if ranked else None,
        "best_n1": n1_ranked[0] if n1_ranked else None,
    }
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    RESEARCH.joinpath("PRIV_MDD_NEW_MECH_N1_STAGE_A.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    lines = [
        "# 民股／四類 × MDD New Mechanism N1 — Stage A",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Status: **{status}** · baseline **`LIVE_PUB_KD`** · frozen offense **`{OFFENSE['id']}`**",
        "Soft-Frozen **KEEP** · live wire **false** · sealed gate **unchanged**",
        "Mechanism: FinPriv regime membership (LOCAL sleeve DD / REL vs FinPub / DUAL)",
        "",
        "## N1 coexist",
        "",
    ]
    if n1_coexist:
        for r in n1_coexist:
            lines.append(f"- `{r['id']}` · score_mdd **{r['score_mdd']}** · `{r['mechanism']}`")
    else:
        lines.append("- **None**")
    lines += [
        "",
        "## Ranked vs LIVE_PUB_KD",
        "",
        "| book | family | score_mdd | MDD↑ held | MDD↑ sealed | CAGR gb | tip | tipMDD | gate_on% | coexist |",
        "|---|---|---:|---:|---:|---:|---|---|---:|---|",
    ]
    for r in ranked:
        gos = r.get("gate_on_share")
        gos_s = f"{100.0 * float(gos):.1f}" if gos is not None else "—"
        lines.append(
            f"| `{r['id']}` | `{r.get('n1_family')}` | {r['score_mdd']:.3f} | "
            f"{r['heldout_mdd_improve_pp']:+.2f} | {r['sealed_mdd_improve_pp']:+.2f} | "
            f"{r['heldout_cagr_giveback_pp']} | "
            f"{'Y' if r['tip_clean'] else 'N'} | {'Y' if r['tip_mdd_ok'] else 'N'} | "
            f"{gos_s} | {'Y' if r['coexist'] else 'N'} |"
        )
    lines += [
        "",
        "## Binding",
        "",
        "1. Soft-Frozen stays 3-sleeve 公股 until Class D ACCEPT.",
        "2. Do not retune FinPriv clips or TAIEX L4 −8/−10 from this N1 Stage A.",
        "3. N1 coexist → Stage B observe ballot; else STOP N1 / autopsy → N2 or sealed-gate human path.",
        "",
        "Repro: `PYTHONPATH=scripts python3 scripts/e16_priv_mdd_new_mech_n1_stage_a.py`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "STAGE_A.md").write_text(md)
    RESEARCH.joinpath("PRIV_MDD_NEW_MECH_N1_STAGE_A.md").write_text(md)

    decision = {
        "generated_at_utc": payload["generated_at_utc"],
        "label": "PRIV_MDD_NEW_MECH_N1_DECISION",
        "status": status,
        "live_wire": False,
        "soft_frozen_keep": True,
        "n1_coexist_ids": payload["n1_coexist_ids"],
        "best_n1": payload["best_n1"],
        "best_overall": payload["best"],
        "frozen_offense": OFFENSE["id"],
        "next": (
            "Open Stage B dual-paper observe on n1_coexist_ids"
            if n1_coexist
            else "STOP N1 — FinPriv regime membership did not clear sealed MDD coexist; Soft-Frozen 公股 KEEP; ballot N2 relocate or human sealed-gate"
        ),
        "charter": "research/ops/PRIV_MDD_NEW_MECHANISM_CHARTER.md",
        "stage_a": "research/ops/PRIV_MDD_NEW_MECH_N1_STAGE_A.md",
    }
    RESEARCH.joinpath("PRIV_MDD_NEW_MECH_N1_DECISION_PACK.json").write_text(
        json.dumps(decision, indent=2, default=str) + "\n"
    )
    dlines = [
        "# 民股／四類 × MDD New Mechanism N1 — Decision Pack",
        "",
        f"Date: 2026-09-19 · `{decision['generated_at_utc']}`",
        f"Status: **{status}** · Soft-Frozen **KEEP** · live wire **false**",
        f"Frozen offense: `{OFFENSE['id']}`",
        "",
        "## Verdict",
        "",
    ]
    if n1_coexist:
        dlines += [
            "**STAGE A CANDIDATES (N1)**:",
            "",
            *[f"- `{x}`" for x in decision["n1_coexist_ids"]],
        ]
    else:
        best = decision.get("best_n1") or decision.get("best_overall") or {}
        dlines += [
            "**STOP N1** — no FinPriv regime-membership book cleared MDD coexist vs `LIVE_PUB_KD`.",
            "",
            f"Best N1: `{best.get('id')}` · score_mdd **{best.get('score_mdd')}** · "
            f"held MDD↑ **{best.get('heldout_mdd_improve_pp')}** · "
            f"sealed MDD↑ **{best.get('sealed_mdd_improve_pp')}**",
            "",
            "Binding: keep Soft-Frozen 公股 · do not Class-D flip · do not retune SF4 clips / TAIEX L4.",
            "Next (optional): N2 FinPriv-scoped relocate charter ballot · or human sealed-gate change.",
        ]
    dlines += [
        "",
        "## Refs",
        "",
        "- Charter: `PRIV_MDD_NEW_MECHANISM_CHARTER.md`",
        "- Stage A: `PRIV_MDD_NEW_MECH_N1_STAGE_A.md`",
        "- Prior STOP: `PUB_PRIV_COEXIST_MDD_DECISION_PACK.md` · `SF4_DEFENCE_MDD_DECISION_PACK.md`",
        "",
        f"Label: `PRIV_MDD_NEW_MECH_N1_DECISION_2026-09-19__{status}`",
        "",
    ]
    RESEARCH.joinpath("PRIV_MDD_NEW_MECH_N1_DECISION_PACK.md").write_text("\n".join(dlines))

    print(
        json.dumps(
            {
                "status": status,
                "n1_coexist": payload["n1_coexist_ids"],
                "best_n1": payload["best_n1"],
            },
            indent=2,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
