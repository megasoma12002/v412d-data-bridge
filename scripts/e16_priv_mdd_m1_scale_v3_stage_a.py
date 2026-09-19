#!/usr/bin/env python3
"""民股 MDD V3 — E45 M1 proportional FinPriv scale Stage A.

Charter: research/ops/PRIV_MDD_M1_SCALE_V3_CHARTER.md
FinPriv'_t = FinPriv_t * clip(1 - c * s_{t-1}, 0, 1); residual → 0050 or cash.
Sensor: frozen E45 M1 v0 s_t. Sealed gates unchanged.
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
import e45_m1_state_signal_paper as m1
from e45_paper_harness import load_dividends

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/priv-mdd-m1-scale-v3-stagea"
RESEARCH = ROOT / "research/ops"
OFFENSE = n1.OFFENSE
ETF_HI_CAP = float(n2.ETF_HI_CAP)
SLEEVE_COLS = n1.SLEEVE_COLS

C_GRID = (0.25, 0.50, 0.75, 1.00)
SINKS = ("0050", "CASH")


def apply_v3_scale(
    offense: pd.DataFrame,
    s_t: pd.Series,
    *,
    c: float,
    sink: str,
    etf_hi_cap: float = ETF_HI_CAP,
) -> tuple[pd.DataFrame, pd.Series]:
    """Proportional FinPriv dampener; returns (targets, exposure e_t)."""
    common = offense.index.intersection(s_t.index)
    out = offense.loc[common, SLEEVE_COLS].astype(float).copy()
    s_lag = s_t.reindex(common).shift(1).fillna(0.0).clip(0.0, 1.0)
    e = (1.0 - float(c) * s_lag).clip(0.0, 1.0)
    priv = out["FinPriv"].to_numpy(dtype=float)
    new_priv = priv * e.to_numpy(dtype=float)
    residual = priv - new_priv
    out["FinPriv"] = new_priv
    if sink == "CASH":
        pass
    elif sink == "0050":
        etf = out["0050"].to_numpy(dtype=float)
        room = (float(etf_hi_cap) - etf).clip(min=0.0)
        move = np.minimum(residual, room)
        out["0050"] = etf + move
    else:
        raise ValueError(sink)
    return out, e


def _run_book(market, dividends, target, regime, *, book_id: str, meta_extra: dict):
    row = n1._sim_sf4(
        market, dividends, target, regime, book_id=book_id, meta_extra=meta_extra
    )
    for k in (
        "v3_family",
        "v3_c",
        "v3_sink",
        "mean_exposure",
        "etf_hi_cap",
        "n2_sink",
        "s2_family",
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
    for k in ("v3_family", "v3_c", "v3_sink", "mean_exposure", "n2_sink"):
        if k in src and src[k] is not None:
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
    results: dict = {"LIVE_PUB_KD": live}

    print("SF4 offense + M1 s_t ...", flush=True)
    off_t, off_r = n1.build_sf4_pair(market, OFFENSE)
    def_t, _ = n1.build_sf4_pair(market, n1.DEFENCE_CTRL)
    # M1 uses close; ensure present on extended panel
    state = m1.build_m1_state(market)
    s_t = state["s_t"].astype(float)

    print("SF4_OFFENSE ...", flush=True)
    results["SF4_OFFENSE"] = _run_book(
        market,
        dividends,
        off_t,
        off_r,
        book_id="SF4_OFFENSE",
        meta_extra=_meta("SF4_FROZEN", v3_family="CONTROL"),
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
            v3_family="REF_L4",
            mean_exposure=1.0 - float(l4_f.mean()) if len(l4_f) else None,
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
            v3_family="REF_N2",
            n2_sink="0050",
            mean_exposure=1.0 - float(n2_f.mean()) if len(n2_f) else None,
        ),
    )

    for c in C_GRID:
        for sink in SINKS:
            tag = f"C{int(round(c * 100)):02d}_{sink}"
            bid = f"V3_{tag}"
            print(f"{bid} ...", flush=True)
            tgt, e = apply_v3_scale(off_t, s_t, c=c, sink=sink)
            results[bid] = _run_book(
                market,
                dividends,
                tgt,
                off_r.reindex(tgt.index).ffill().bfill(),
                book_id=bid,
                meta_extra=_meta(
                    f"V3_M1_SCALE_{tag}",
                    v3_family="M1_SCALE",
                    v3_c=c,
                    v3_sink=sink,
                    etf_hi_cap=ETF_HI_CAP if sink == "0050" else None,
                    mean_exposure=float(e.mean()) if len(e) else None,
                ),
            )

    asof = pd.to_datetime(live["nav"]["date"]).max()
    ranked = []
    for bid, row in results.items():
        if bid == "LIVE_PUB_KD":
            continue
        ranked.append(_extend_rank(base.rank_row(live, row, asof), row))
    ranked.sort(key=lambda r: r["score_mdd"], reverse=True)
    v3_ranked = [r for r in ranked if str(r.get("id", "")).startswith("V3_")]
    coexist = [r for r in ranked if r["coexist"]]
    v3_coexist = [r for r in coexist if r["id"].startswith("V3_")]

    if v3_coexist:
        status = "STAGE_A_CANDIDATES"
    elif any(r["gates"]["sealed_mdd"] for r in v3_ranked):
        status = "STAGE_A_SEALED_MDD_PASS_OTHER_GATES_FAIL"
    elif any(r["score_mdd"] > 0 for r in v3_ranked):
        status = "STAGE_A_SCORE_POS_GATES_FAIL"
    else:
        status = "STOP_NO_MDD_COEXIST_VS_LIVE_PUB_KD"

    keep = {
        "LIVE_PUB_KD",
        "SF4_OFFENSE",
        "SF4_L4_08_REF",
        "N2_0050_LOCAL_08_REF",
    } | {r["id"] for r in v3_coexist} | {r["id"] for r in v3_ranked[:5]}
    for bid in keep:
        if bid in results:
            results[bid]["nav"].to_csv(OUT / "outputs" / f"{bid}_daily_nav.csv", index=False)

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "PRIV_MDD_M1_SCALE_V3_STAGE_A",
        "status": status,
        "charter": "research/ops/PRIV_MDD_M1_SCALE_V3_CHARTER.md",
        "m1_state_vector": m1.STATE_VECTOR_LABEL,
        "prior_stops": [
            "research/ops/PRIV_MDD_NEW_MECH_N3_DECISION_PACK.md",
            "research/ops/PRIV_MDD_SENSOR_S2_DECISION_PACK.md",
        ],
        "live_wire": False,
        "soft_frozen_clip": list(soft.SOFT_FROZEN_FIN_CLIP),
        "etf_hi_cap": ETF_HI_CAP,
        "baseline": "LIVE_PUB_KD",
        "frozen_offense": OFFENSE["id"],
        "asof": str(pd.Timestamp(asof).date()),
        "n_challengers": len(ranked),
        "n_v3_challengers": len(v3_ranked),
        "ranked_vs_live_pub_kd": ranked,
        "coexist_ids": [r["id"] for r in coexist],
        "v3_coexist_ids": [r["id"] for r in v3_coexist],
        "best": ranked[0] if ranked else None,
        "best_v3": v3_ranked[0] if v3_ranked else None,
    }
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    RESEARCH.joinpath("PRIV_MDD_M1_SCALE_V3_STAGE_A.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    lines = [
        "# 民股 MDD V3 — M1 proportional FinPriv scale Stage A",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Status: **{status}** · baseline **`LIVE_PUB_KD`** · frozen offense **`{OFFENSE['id']}`**",
        "Soft-Frozen **KEEP** · live wire **false** · sealed gate **unchanged**",
        f"Mechanism: FinPriv × (1 − c · M1 `s_{{t-1}}`) · residual → 0050/cash · `{m1.STATE_VECTOR_LABEL}`",
        "",
        "## V3 coexist",
        "",
    ]
    if v3_coexist:
        for r in v3_coexist:
            lines.append(f"- `{r['id']}` · score_mdd **{r['score_mdd']}** · `{r['mechanism']}`")
    else:
        lines.append("- **None**")
    lines += [
        "",
        "## Ranked vs LIVE_PUB_KD",
        "",
        "| book | c/sink | score_mdd | MDD↑ held | MDD↑ sealed | tip | tipMDD | mean_e | coexist |",
        "|---|---|---:|---:|---:|---|---|---:|---|",
    ]
    for r in ranked:
        if r["id"].startswith("V3_"):
            cs = f"{r.get('v3_c')}/{r.get('v3_sink')}"
            me = r.get("mean_exposure")
            me_s = f"{float(me):.3f}" if me is not None else "—"
        else:
            cs = str(r.get("v3_family") or "—")
            me_s = "—"
        lines.append(
            f"| `{r['id']}` | `{cs}` | {r['score_mdd']:.3f} | "
            f"{r['heldout_mdd_improve_pp']:+.2f} | {r['sealed_mdd_improve_pp']:+.2f} | "
            f"{'Y' if r['tip_clean'] else 'N'} | {'Y' if r['tip_mdd_ok'] else 'N'} | "
            f"{me_s} | {'Y' if r['coexist'] else 'N'} |"
        )
    lines += [
        "",
        "## Binding",
        "",
        "1. Soft-Frozen stays 3-sleeve 公股 until Class D ACCEPT.",
        "2. Do not retune M1 feature maps / N1–N3 / V2 from this Stage A.",
        "3. V3 coexist → Stage B; else STOP V3 · Soft-Frozen KEEP.",
        "",
        "Repro: `PYTHONPATH=scripts python3 scripts/e16_priv_mdd_m1_scale_v3_stage_a.py`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "STAGE_A.md").write_text(md)
    RESEARCH.joinpath("PRIV_MDD_M1_SCALE_V3_STAGE_A.md").write_text(md)

    decision = {
        "generated_at_utc": payload["generated_at_utc"],
        "label": "PRIV_MDD_M1_SCALE_V3_DECISION",
        "status": status,
        "live_wire": False,
        "soft_frozen_keep": True,
        "v3_coexist_ids": payload["v3_coexist_ids"],
        "best_v3": payload["best_v3"],
        "best_overall": payload["best"],
        "frozen_offense": OFFENSE["id"],
        "m1_state_vector": m1.STATE_VECTOR_LABEL,
        "next": (
            "Open Stage B dual-paper observe on v3_coexist_ids"
            if v3_coexist
            else "STOP V3 — M1 proportional FinPriv scale did not clear sealed MDD; Soft-Frozen KEEP; sealed-gate or other new charter"
        ),
        "charter": "research/ops/PRIV_MDD_M1_SCALE_V3_CHARTER.md",
        "stage_a": "research/ops/PRIV_MDD_M1_SCALE_V3_STAGE_A.md",
    }
    RESEARCH.joinpath("PRIV_MDD_M1_SCALE_V3_DECISION_PACK.json").write_text(
        json.dumps(decision, indent=2, default=str) + "\n"
    )
    dlines = [
        "# 民股 MDD V3 — Decision Pack",
        "",
        f"Date: 2026-09-19 · `{decision['generated_at_utc']}`",
        f"Status: **{status}** · Soft-Frozen **KEEP** · live wire **false**",
        f"Frozen offense: `{OFFENSE['id']}` · M1 `{m1.STATE_VECTOR_LABEL}`",
        "",
        "## Verdict",
        "",
    ]
    if v3_coexist:
        dlines += [
            "**STAGE A CANDIDATES (V3)**:",
            "",
            *[f"- `{x}`" for x in decision["v3_coexist_ids"]],
        ]
    else:
        best = decision.get("best_v3") or decision.get("best_overall") or {}
        dlines += [
            "**STOP V3** — no M1-scale book cleared MDD coexist vs `LIVE_PUB_KD`.",
            "",
            f"Best V3: `{best.get('id')}` · score_mdd **{best.get('score_mdd')}** · "
            f"held MDD↑ **{best.get('heldout_mdd_improve_pp')}** · "
            f"sealed MDD↑ **{best.get('sealed_mdd_improve_pp')}**",
            "",
            "Binding: Soft-Frozen 公股 KEEP · N1–N3 + V2 + V3 STOP · sealed unchanged.",
            "Next: Soft-Frozen KEEP · human sealed-gate · or other new charter (≠ retune).",
        ]
    dlines += [
        "",
        "## Refs",
        "",
        "- Charter: `PRIV_MDD_M1_SCALE_V3_CHARTER.md`",
        "- Stage A: `PRIV_MDD_M1_SCALE_V3_STAGE_A.md`",
        "- M1: `research/e45/E45_M1_STATE_VECTOR_V0_FROZEN.md`",
        "",
        f"Label: `PRIV_MDD_M1_SCALE_V3_DECISION_2026-09-19__{status}`",
        "",
    ]
    RESEARCH.joinpath("PRIV_MDD_M1_SCALE_V3_DECISION_PACK.md").write_text("\n".join(dlines))

    print(
        json.dumps(
            {
                "status": status,
                "v3_coexist": payload["v3_coexist_ids"],
                "best_v3": payload["best_v3"],
            },
            indent=2,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
