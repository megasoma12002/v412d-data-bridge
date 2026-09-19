#!/usr/bin/env python3
"""Soft-Frozen 四類 + DH／L4 防禦 × MDD Stage A — RESEARCH ONLY.

Charter: research/ops/SF4_DEFENCE_MDD_CHARTER.md
Frozen offense cell from PUB_PRIV_COEXIST_MDD Stage A — do not retune clips.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import e16_pub_priv_coexist_mdd_stage_a as base
import e16_soft_frozen_4sleeve as sf4
import e16_soft_frozen_base as soft
import e45_defend_handoff_helpers as dh
import e45_defend_handoff_stagea_screen as stagea
import e50_early_stack_combined_nav as e50
from e16_private_fin_holdings_rescreen import PRIV_R3R4, PUB_R1, TEL
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, window_stats
from tw_share_lots import BOARD_LOT
from within_sleeve_alloc import FIN_EQUAL, FIN_PRE_EXDIV_KD, TEL_EQUAL

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/sf4-defence-mdd-stagea"
RESEARCH = ROOT / "research/ops"
CAPITAL = float(base.CAPITAL)
LOT = int(BOARD_LOT)
E22_PAPER = base.E22_PAPER
SLEEVE_COLS = ["FinPub", "FinPriv", "Telecom", "0050"]

# Frozen offense (prior Stage A best priv-bearing) — DO NOT RETUNE.
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
L4_THRS = (-0.08, -0.10)


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
            "l4_dd_thr": meta_extra.get("l4_dd_thr"),
            "dh": meta_extra.get("dh"),
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


def apply_l4_path(offense: pd.DataFrame, defence: pd.DataFrame, market: pd.DataFrame, dd_thr: float):
    """Path-switch to defence 四類 weights while TAIEX DD from peak <= dd_thr."""
    prices = (
        market.pivot(index="date", columns="code", values="adj_close")
        .sort_index()
        .ffill()
    )
    taiex = prices["TAIEX"]
    peak = taiex.rolling(252, min_periods=120).max()
    dd = taiex / peak - 1.0
    common = offense.index.intersection(defence.index).intersection(dd.index)
    flag = (dd.reindex(common) <= float(dd_thr)).fillna(False)
    out = offense.loc[common, SLEEVE_COLS].astype(float).copy()
    def_aligned = defence.loc[common, SLEEVE_COLS].astype(float)
    out.loc[flag.values, SLEEVE_COLS] = def_aligned.loc[flag.values, SLEEVE_COLS].to_numpy()
    s = out.sum(axis=1).replace(0.0, 1.0)
    out = out.div(s, axis=0)
    return out, flag


def apply_dh_scale(target: pd.DataFrame, exposure: pd.Series) -> pd.DataFrame:
    """Scale all equity sleeves by DH exposure (residual cash). FinPub/FinPriv cannot use e45_exposure kw."""
    common = target.index.intersection(exposure.index)
    out = target.loc[common, SLEEVE_COLS].astype(float).copy()
    exp = exposure.reindex(common).astype(float).fillna(1.0).clip(0.0, 1.0)
    for c in SLEEVE_COLS:
        out[c] = out[c] * exp
    return out


def dh_exposure_from_nav(market: pd.DataFrame, offense_nav: pd.DataFrame) -> pd.Series:
    nav_s = stagea._nav_series(offense_nav)
    feat = stagea._risk_features(market, nav_s)
    dates = pd.DatetimeIndex(nav_s.index)
    return stagea._build_exposure(dates, feat, float(dh.DD_THRESHOLD), float(dh.VOL_Z_THRESHOLD))


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

    print("SF4_OFFENSE ...", flush=True)
    results["SF4_OFFENSE"] = _sim_sf4(
        market,
        dividends,
        off_t,
        off_r,
        book_id="SF4_OFFENSE",
        meta_extra={
            "mechanism": "SF4_FROZEN",
            "priv_pol": OFFENSE["priv_pol"],
            "fin_pub_clip": [OFFENSE["pub_lo"], OFFENSE["pub_hi"]],
            "fin_priv_clip": [OFFENSE["priv_lo"], OFFENSE["priv_hi"]],
            "prior_priv_frac": OFFENSE["prior_frac"],
            "dh": False,
        },
    )

    print("SF4_DH ...", flush=True)
    exp = dh_exposure_from_nav(market, results["SF4_OFFENSE"]["nav"])
    dh_target = apply_dh_scale(off_t, exp)
    results["SF4_DH"] = _sim_sf4(
        market,
        dividends,
        dh_target,
        off_r.reindex(dh_target.index).ffill().bfill(),
        book_id="SF4_DH",
        meta_extra={
            "mechanism": "SF4+DH_dd06",
            "priv_pol": OFFENSE["priv_pol"],
            "fin_pub_clip": [OFFENSE["pub_lo"], OFFENSE["pub_hi"]],
            "fin_priv_clip": [OFFENSE["priv_lo"], OFFENSE["priv_hi"]],
            "prior_priv_frac": OFFENSE["prior_frac"],
            "dh": True,
        },
    )

    for thr in L4_THRS:
        tag = f"L4_{abs(int(thr * 100)):02d}"
        print(f"SF4_{tag} ...", flush=True)
        l4_t, flag = apply_l4_path(off_t, def_t, market, thr)
        bid = f"SF4_{tag}"
        results[bid] = _sim_sf4(
            market,
            dividends,
            l4_t,
            off_r.reindex(l4_t.index).ffill().bfill(),
            book_id=bid,
            meta_extra={
                "mechanism": f"SF4+{tag}",
                "priv_pol": OFFENSE["priv_pol"],
                "fin_pub_clip": [OFFENSE["pub_lo"], OFFENSE["pub_hi"]],
                "fin_priv_clip": [OFFENSE["priv_lo"], OFFENSE["priv_hi"]],
                "prior_priv_frac": OFFENSE["prior_frac"],
                "l4_dd_thr": thr,
                "dh": False,
                "l4_on_share": float(flag.mean()) if len(flag) else None,
            },
        )
        print(f"SF4_{tag}_DH ...", flush=True)
        # DH exposure from L4 path offense NAV (two-pass).
        exp_l4 = dh_exposure_from_nav(market, results[bid]["nav"])
        l4_dh_t = apply_dh_scale(l4_t, exp_l4)
        results[f"{bid}_DH"] = _sim_sf4(
            market,
            dividends,
            l4_dh_t,
            off_r.reindex(l4_dh_t.index).ffill().bfill(),
            book_id=f"{bid}_DH",
            meta_extra={
                "mechanism": f"SF4+{tag}+DH",
                "priv_pol": OFFENSE["priv_pol"],
                "fin_pub_clip": [OFFENSE["pub_lo"], OFFENSE["pub_hi"]],
                "fin_priv_clip": [OFFENSE["priv_lo"], OFFENSE["priv_hi"]],
                "prior_priv_frac": OFFENSE["prior_frac"],
                "l4_dd_thr": thr,
                "dh": True,
                "l4_on_share": float(flag.mean()) if len(flag) else None,
            },
        )

    asof = pd.to_datetime(live["nav"]["date"]).max()
    ranked = []
    for bid, row in results.items():
        if bid == "LIVE_PUB_KD":
            continue
        ranked.append(base.rank_row(live, row, asof))
    ranked.sort(key=lambda r: r["score_mdd"], reverse=True)
    coexist = [r for r in ranked if r["coexist"]]

    if coexist:
        status = "STAGE_A_CANDIDATES"
    elif any(r["gates"]["sealed_mdd"] for r in ranked):
        status = "STAGE_A_SEALED_MDD_PASS_OTHER_GATES_FAIL"
    elif any(r["score_mdd"] > 0 for r in ranked):
        status = "STAGE_A_SCORE_POS_GATES_FAIL"
    else:
        status = "STOP_NO_MDD_COEXIST_VS_LIVE_PUB_KD"

    keep = {"LIVE_PUB_KD"} | {r["id"] for r in coexist} | {r["id"] for r in ranked[:5]}
    for bid in keep:
        if bid in results:
            results[bid]["nav"].to_csv(OUT / "outputs" / f"{bid}_daily_nav.csv", index=False)

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "SF4_DEFENCE_MDD_STAGE_A",
        "status": status,
        "charter": "research/ops/SF4_DEFENCE_MDD_CHARTER.md",
        "prior_stop": "research/ops/PUB_PRIV_COEXIST_MDD_DECISION_PACK.md",
        "live_wire": False,
        "soft_frozen_clip": list(soft.SOFT_FROZEN_FIN_CLIP),
        "baseline": "LIVE_PUB_KD",
        "frozen_offense": OFFENSE["id"],
        "asof": str(pd.Timestamp(asof).date()),
        "n_challengers": len(ranked),
        "ranked_vs_live_pub_kd": ranked,
        "coexist_ids": [r["id"] for r in coexist],
        "best": ranked[0] if ranked else None,
    }
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    RESEARCH.joinpath("SF4_DEFENCE_MDD_STAGE_A.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    lines = [
        "# Soft-Frozen 四類 + DH／L4 防禦 × MDD — Stage A",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Status: **{status}** · baseline **`LIVE_PUB_KD`** · frozen offense **`{OFFENSE['id']}`**",
        "Soft-Frozen **KEEP** · live wire **false** · sealed gate **unchanged**",
        "",
        "## Coexist",
        "",
    ]
    if coexist:
        for r in coexist:
            lines.append(f"- `{r['id']}` · score_mdd **{r['score_mdd']}** · `{r['mechanism']}`")
    else:
        lines.append("- **None**")
    lines += [
        "",
        "## Ranked vs LIVE_PUB_KD",
        "",
        "| book | mech | score_mdd | MDD↑ held | MDD↑ sealed | CAGR gb | tip | tipMDD | coexist |",
        "|---|---|---:|---:|---:|---:|---|---|---|",
    ]
    for r in ranked:
        lines.append(
            f"| `{r['id']}` | `{r['mechanism']}` | {r['score_mdd']:.3f} | "
            f"{r['heldout_mdd_improve_pp']:+.2f} | {r['sealed_mdd_improve_pp']:+.2f} | "
            f"{r['heldout_cagr_giveback_pp']} | "
            f"{'Y' if r['tip_clean'] else 'N'} | {'Y' if r['tip_mdd_ok'] else 'N'} | "
            f"{'Y' if r['coexist'] else 'N'} |"
        )
    lines += [
        "",
        "## Binding",
        "",
        "1. Soft-Frozen stays 3-sleeve 公股 until Class D ACCEPT.",
        "2. Do not retune FinPriv clips from this defence Stage A.",
        "3. Coexist → Stage B observe; else STOP this defence objective.",
        "",
        "Repro: `PYTHONPATH=scripts python3 scripts/e16_sf4_defence_mdd_stage_a.py`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "STAGE_A.md").write_text(md)
    RESEARCH.joinpath("SF4_DEFENCE_MDD_STAGE_A.md").write_text(md)

    decision = {
        "generated_at_utc": payload["generated_at_utc"],
        "label": "SF4_DEFENCE_MDD_DECISION",
        "status": status,
        "live_wire": False,
        "soft_frozen_keep": True,
        "coexist_ids": payload["coexist_ids"],
        "best": payload["best"],
        "frozen_offense": OFFENSE["id"],
        "next": (
            "Open Stage B dual-paper observe on coexist_ids"
            if coexist
            else "STOP — defence on frozen SF4 did not clear sealed MDD coexist; Soft-Frozen 公股 KEEP"
        ),
        "charter": "research/ops/SF4_DEFENCE_MDD_CHARTER.md",
        "stage_a": "research/ops/SF4_DEFENCE_MDD_STAGE_A.md",
    }
    RESEARCH.joinpath("SF4_DEFENCE_MDD_DECISION_PACK.json").write_text(
        json.dumps(decision, indent=2, default=str) + "\n"
    )
    dlines = [
        "# Soft-Frozen 四類 + DH／L4 防禦 × MDD — Decision Pack",
        "",
        f"Date: 2026-09-19 · `{decision['generated_at_utc']}`",
        f"Status: **{status}** · Soft-Frozen **KEEP** · live wire **false**",
        f"Frozen offense: `{OFFENSE['id']}`",
        "",
        "## Verdict",
        "",
    ]
    if coexist:
        dlines += ["**STAGE A CANDIDATES**:", "", *[f"- `{x}`" for x in decision["coexist_ids"]]]
    else:
        best = decision.get("best") or {}
        dlines += [
            "**STOP** — no defence book cleared MDD coexist vs `LIVE_PUB_KD`.",
            "",
            f"Best: `{best.get('id')}` · score_mdd **{best.get('score_mdd')}** · "
            f"held MDD↑ **{best.get('heldout_mdd_improve_pp')}** · "
            f"sealed MDD↑ **{best.get('sealed_mdd_improve_pp')}**",
            "",
            "Binding: keep Soft-Frozen 公股 · do not Class-D flip to 四類 from this Stage.",
        ]
    dlines += [
        "",
        "## Refs",
        "",
        "- Charter: `SF4_DEFENCE_MDD_CHARTER.md`",
        "- Stage A: `SF4_DEFENCE_MDD_STAGE_A.md`",
        "- Prior raw 四類 STOP: `PUB_PRIV_COEXIST_MDD_DECISION_PACK.md`",
        "",
        f"Label: `SF4_DEFENCE_MDD_DECISION_2026-09-19__{status}`",
        "",
    ]
    RESEARCH.joinpath("SF4_DEFENCE_MDD_DECISION_PACK.md").write_text("\n".join(dlines))

    print(json.dumps({"status": status, "coexist": payload["coexist_ids"], "best": payload["best"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
