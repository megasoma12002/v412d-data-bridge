#!/usr/bin/env python3
"""民股 MDD V2 S1 — breadth / FinPub–TAIEX sensor Stage A.

Charter: research/ops/PRIV_MDD_SENSOR_MECH_V2_CHARTER.md
≠ N1–N3 FinPriv self-DD. Fire (lag-1) → FinPriv→0050 (N2 sink, ETF hi 0.35).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

import e16_priv_mdd_new_mech_n1_stage_a as n1
import e16_priv_mdd_new_mech_n2_stage_a as n2
import e16_pub_priv_coexist_mdd_stage_a as base
import e16_soft_frozen_base as soft
from e16_private_fin_holdings_rescreen import PUB_R1, TEL
from e45_paper_harness import load_dividends

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/priv-mdd-sensor-s1-stagea"
RESEARCH = ROOT / "research/ops"
OFFENSE = n1.OFFENSE
ETF_HI_CAP = float(n2.ETF_HI_CAP)

# Soft-Frozen FIN∪TEL for breadth (公股+電信 — not FinPriv self-path)
BREADTH_CODES = list(PUB_R1) + list(TEL)
BREADTH_THRS = (0.45, 0.55)  # 1 - breadth
FINREL_Z_THRS = (-1.0, -1.5)


def build_s1_sensors(market: pd.DataFrame) -> pd.DataFrame:
    """Causal sensors; caller must lag-1 before firing."""
    prices = (
        market.pivot(index="date", columns="code", values="adj_close")
        .sort_index()
        .ffill()
    )
    if "TAIEX" not in prices.columns:
        raise SystemExit("TAIEX missing")
    cols = [c for c in BREADTH_CODES if c in prices.columns]
    if len(cols) < 4:
        raise SystemExit(f"breadth codes missing: need Soft-Frozen FIN∪TEL, got {cols}")
    eq = prices[cols].astype(float)
    sma120 = eq.rolling(120, min_periods=60).mean()
    breadth = (eq > sma120).sum(axis=1) / eq.notna().sum(axis=1).replace(0, np.nan)
    stress_breadth = (1.0 - breadth).clip(0.0, 1.0)

    pub_cols = [c for c in PUB_R1 if c in prices.columns]
    fin_ew = prices[pub_cols].mean(axis=1)
    taiex = prices["TAIEX"].astype(float)
    rel = np.log((fin_ew / taiex).replace(0.0, np.nan))
    mu = rel.rolling(60, min_periods=30).mean()
    sd = rel.rolling(60, min_periods=30).std().replace(0.0, np.nan)
    z = (rel - mu) / sd

    return pd.DataFrame(
        {"stress_breadth": stress_breadth, "finpub_taiex_z": z},
        index=prices.index,
    )


def fire_lag1(raw: pd.Series, pred) -> pd.Series:
    """Lag-1 then apply predicate on lagged value."""
    x = raw.shift(1)
    return pred(x).fillna(False).astype(bool)


def _run_book(market, dividends, target, regime, *, book_id: str, meta_extra: dict):
    row = n1._sim_sf4(
        market, dividends, target, regime, book_id=book_id, meta_extra=meta_extra
    )
    for k in (
        "s1_family",
        "s1_thr",
        "gate_on_share",
        "n2_sink",
        "etf_hi_cap",
        "n3_family",
    ):
        if k in meta_extra:
            row[k] = meta_extra[k]
    return row


def _meta(mechanism: str, **extra) -> dict:
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
    for k in ("s1_family", "s1_thr", "gate_on_share", "n2_sink"):
        if k in src and src[k] is not None:
            row[k] = src[k]
    return row


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "outputs").mkdir(exist_ok=True)
    assert list(soft.SOFT_FROZEN_FIN_CLIP) == [0.6, 0.8]

    print("building extended market ...", flush=True)
    market = base.build_extended_market()
    dividends = load_dividends()

    print("baseline LIVE_PUB_KD ...", flush=True)
    live = base.run_live_pub_kd(market, dividends)
    results: dict = {"LIVE_PUB_KD": live}

    print("SF4 offense + S1 sensors ...", flush=True)
    off_t, off_r = n1.build_sf4_pair(market, OFFENSE)
    def_t, _ = n1.build_sf4_pair(market, n1.DEFENCE_CTRL)
    sens = build_s1_sensors(market)

    print("SF4_OFFENSE ...", flush=True)
    results["SF4_OFFENSE"] = _run_book(
        market,
        dividends,
        off_t,
        off_r,
        book_id="SF4_OFFENSE",
        meta_extra=_meta("SF4_FROZEN", s1_family="CONTROL"),
    )

    print("SF4_L4_08_REF ...", flush=True)
    l4_t, l4_f = n1.apply_l4_taiex_ref(off_t, def_t, market, n1.L4_REF_THR)
    results["SF4_L4_08_REF"] = _run_book(
        market,
        dividends,
        l4_t,
        off_r.reindex(l4_t.index).ffill().bfill(),
        book_id="SF4_L4_08_REF",
        meta_extra=_meta(
            "REF_TAIEX_L4_08",
            s1_family="REF_L4",
            gate_on_share=float(l4_f.mean()) if len(l4_f) else None,
        ),
    )

    print("N2_0050_LOCAL_08_REF ...", flush=True)
    priv_dd, _, _ = n1.sleeve_nav_features(market)
    flag_n2 = (priv_dd <= -0.08).fillna(False)
    n2_t, n2_f = n2.apply_n2_relocate(off_t, flag_n2, sink="0050")
    results["N2_0050_LOCAL_08_REF"] = _run_book(
        market,
        dividends,
        n2_t,
        off_r.reindex(n2_t.index).ffill().bfill(),
        book_id="N2_0050_LOCAL_08_REF",
        meta_extra=_meta(
            "REF_N2_0050_LOCAL_08",
            s1_family="REF_N2",
            n2_sink="0050",
            gate_on_share=float(n2_f.mean()) if len(n2_f) else None,
        ),
    )

    specs = []
    for thr in BREADTH_THRS:
        tag = f"BREADTH_{int(round(thr * 100))}"
        specs.append((f"S1_{tag}", "BREADTH", thr, fire_lag1(sens["stress_breadth"], lambda x, t=thr: x >= t)))
    for thr in FINREL_Z_THRS:
        tag = f"FINZ_{abs(int(round(thr * 10)))}"
        specs.append(
            (
                f"S1_{tag}",
                "FINPUB_TAIEX_Z",
                thr,
                fire_lag1(sens["finpub_taiex_z"], lambda x, t=thr: x <= t),
            )
        )
    # OR mid cells only
    flag_or = fire_lag1(sens["stress_breadth"], lambda x: x >= 0.45) | fire_lag1(
        sens["finpub_taiex_z"], lambda x: x <= -1.0
    )
    specs.append(("S1_OR_MID", "OR_MID", "B0.45|Z-1.0", flag_or))

    for bid, family, thr, flag in specs:
        print(f"{bid} ...", flush=True)
        tgt, f = n2.apply_n2_relocate(off_t, flag, sink="0050")
        results[bid] = _run_book(
            market,
            dividends,
            tgt,
            off_r.reindex(tgt.index).ffill().bfill(),
            book_id=bid,
            meta_extra=_meta(
                f"S1_{family}_TO_0050",
                s1_family=family,
                s1_thr=thr,
                n2_sink="0050",
                etf_hi_cap=ETF_HI_CAP,
                gate_on_share=float(f.mean()) if len(f) else None,
            ),
        )

    asof = pd.to_datetime(live["nav"]["date"]).max()
    ranked = []
    for bid, row in results.items():
        if bid == "LIVE_PUB_KD":
            continue
        ranked.append(_extend_rank(base.rank_row(live, row, asof), row))
    ranked.sort(key=lambda r: r["score_mdd"], reverse=True)
    s1_ranked = [r for r in ranked if str(r.get("id", "")).startswith("S1_")]
    coexist = [r for r in ranked if r["coexist"]]
    s1_coexist = [r for r in coexist if r["id"].startswith("S1_")]

    if s1_coexist:
        status = "STAGE_A_CANDIDATES"
    elif any(r["gates"]["sealed_mdd"] for r in s1_ranked):
        status = "STAGE_A_SEALED_MDD_PASS_OTHER_GATES_FAIL"
    elif any(r["score_mdd"] > 0 for r in s1_ranked):
        status = "STAGE_A_SCORE_POS_GATES_FAIL"
    else:
        status = "STOP_NO_MDD_COEXIST_VS_LIVE_PUB_KD"

    keep = {
        "LIVE_PUB_KD",
        "SF4_OFFENSE",
        "SF4_L4_08_REF",
        "N2_0050_LOCAL_08_REF",
    } | {r["id"] for r in s1_coexist} | {r["id"] for r in s1_ranked[:5]}
    for bid in keep:
        if bid in results:
            results[bid]["nav"].to_csv(OUT / "outputs" / f"{bid}_daily_nav.csv", index=False)

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "PRIV_MDD_SENSOR_S1_STAGE_A",
        "status": status,
        "charter": "research/ops/PRIV_MDD_SENSOR_MECH_V2_CHARTER.md",
        "prior_n1_n3": "research/ops/PRIV_MDD_NEW_MECH_N3_DECISION_PACK.md",
        "live_wire": False,
        "soft_frozen_clip": list(soft.SOFT_FROZEN_FIN_CLIP),
        "etf_hi_cap": ETF_HI_CAP,
        "sink": "0050",
        "baseline": "LIVE_PUB_KD",
        "frozen_offense": OFFENSE["id"],
        "asof": str(pd.Timestamp(asof).date()),
        "n_challengers": len(ranked),
        "n_s1_challengers": len(s1_ranked),
        "ranked_vs_live_pub_kd": ranked,
        "coexist_ids": [r["id"] for r in coexist],
        "s1_coexist_ids": [r["id"] for r in s1_coexist],
        "best": ranked[0] if ranked else None,
        "best_s1": s1_ranked[0] if s1_ranked else None,
    }
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    RESEARCH.joinpath("PRIV_MDD_SENSOR_S1_STAGE_A.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    lines = [
        "# 民股 MDD V2 S1 — breadth / FinPub–TAIEX sensor Stage A",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Status: **{status}** · baseline **`LIVE_PUB_KD`** · frozen offense **`{OFFENSE['id']}`**",
        "Soft-Frozen **KEEP** · live wire **false** · sealed gate **unchanged**",
        "Mechanism: lag-1 breadth / FinPub–TAIEX z → FinPriv→0050",
        "",
        "## S1 coexist",
        "",
    ]
    if s1_coexist:
        for r in s1_coexist:
            lines.append(f"- `{r['id']}` · score_mdd **{r['score_mdd']}** · `{r['mechanism']}`")
    else:
        lines.append("- **None**")
    lines += [
        "",
        "## Ranked vs LIVE_PUB_KD",
        "",
        "| book | family | thr | score_mdd | MDD↑ held | MDD↑ sealed | tip | tipMDD | gate_on% | coexist |",
        "|---|---|---|---:|---:|---:|---|---|---:|---|",
    ]
    for r in ranked:
        gos = r.get("gate_on_share")
        gos_s = f"{100.0 * float(gos):.1f}" if gos is not None else "—"
        lines.append(
            f"| `{r['id']}` | `{r.get('s1_family')}` | `{r.get('s1_thr')}` | {r['score_mdd']:.3f} | "
            f"{r['heldout_mdd_improve_pp']:+.2f} | {r['sealed_mdd_improve_pp']:+.2f} | "
            f"{'Y' if r['tip_clean'] else 'N'} | {'Y' if r['tip_mdd_ok'] else 'N'} | "
            f"{gos_s} | {'Y' if r['coexist'] else 'N'} |"
        )
    lines += [
        "",
        "## Binding",
        "",
        "1. Soft-Frozen stays 3-sleeve 公股 until Class D ACCEPT.",
        "2. Do not retune N1–N3 or SF4 clips from this S1 Stage A.",
        "3. S1 coexist → Stage B; else STOP S1 / ballot S2 or Soft-Frozen KEEP.",
        "",
        "Repro: `PYTHONPATH=scripts python3 scripts/e16_priv_mdd_sensor_s1_stage_a.py`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "STAGE_A.md").write_text(md)
    RESEARCH.joinpath("PRIV_MDD_SENSOR_S1_STAGE_A.md").write_text(md)

    decision = {
        "generated_at_utc": payload["generated_at_utc"],
        "label": "PRIV_MDD_SENSOR_S1_DECISION",
        "status": status,
        "live_wire": False,
        "soft_frozen_keep": True,
        "s1_coexist_ids": payload["s1_coexist_ids"],
        "best_s1": payload["best_s1"],
        "best_overall": payload["best"],
        "frozen_offense": OFFENSE["id"],
        "next": (
            "Open Stage B dual-paper observe on s1_coexist_ids"
            if s1_coexist
            else "STOP S1 — breadth/FinPub–TAIEX sensors did not clear sealed MDD; Soft-Frozen KEEP; ballot S2 macro or new charter"
        ),
        "charter": "research/ops/PRIV_MDD_SENSOR_MECH_V2_CHARTER.md",
        "stage_a": "research/ops/PRIV_MDD_SENSOR_S1_STAGE_A.md",
    }
    RESEARCH.joinpath("PRIV_MDD_SENSOR_S1_DECISION_PACK.json").write_text(
        json.dumps(decision, indent=2, default=str) + "\n"
    )
    dlines = [
        "# 民股 MDD V2 S1 — Decision Pack",
        "",
        f"Date: 2026-09-19 · `{decision['generated_at_utc']}`",
        f"Status: **{status}** · Soft-Frozen **KEEP** · live wire **false**",
        f"Frozen offense: `{OFFENSE['id']}` · sink FinPriv→0050",
        "",
        "## Verdict",
        "",
    ]
    if s1_coexist:
        dlines += [
            "**STAGE A CANDIDATES (S1)**:",
            "",
            *[f"- `{x}`" for x in decision["s1_coexist_ids"]],
        ]
    else:
        best = decision.get("best_s1") or decision.get("best_overall") or {}
        dlines += [
            "**STOP S1** — no breadth / FinPub–TAIEX sensor book cleared MDD coexist vs `LIVE_PUB_KD`.",
            "",
            f"Best S1: `{best.get('id')}` · score_mdd **{best.get('score_mdd')}** · "
            f"held MDD↑ **{best.get('heldout_mdd_improve_pp')}** · "
            f"sealed MDD↑ **{best.get('sealed_mdd_improve_pp')}**",
            "",
            "Binding: Soft-Frozen 公股 KEEP · sealed gate unchanged · do not retune N1–N3.",
            "Next (optional): S2 USDTWD/CBC ballot · or Soft-Frozen KEEP / new charter.",
        ]
    dlines += [
        "",
        "## Refs",
        "",
        "- Charter: `PRIV_MDD_SENSOR_MECH_V2_CHARTER.md`",
        "- Stage A: `PRIV_MDD_SENSOR_S1_STAGE_A.md`",
        "- Prior ladder: `PRIV_MDD_NEW_MECH_N3_DECISION_PACK.md`",
        "",
        f"Label: `PRIV_MDD_SENSOR_S1_DECISION_2026-09-19__{status}`",
        "",
    ]
    RESEARCH.joinpath("PRIV_MDD_SENSOR_S1_DECISION_PACK.md").write_text("\n".join(dlines))

    print(
        json.dumps(
            {
                "status": status,
                "s1_coexist": payload["s1_coexist_ids"],
                "best_s1": payload["best_s1"],
            },
            indent=2,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
