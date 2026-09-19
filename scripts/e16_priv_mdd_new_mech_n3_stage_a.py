#!/usr/bin/env python3
"""民股／四類 × MDD New Mechanism N3 — three-state risk machine Stage A.

Charter: research/ops/PRIV_MDD_NEW_MECHANISM_CHARTER.md
Prior STOP: N1 membership · N2 relocate.

States (FinPriv sleeve-local DD level machine — no hysteresis latch):
  OFFENSE         : priv_dd > mid_thr          → frozen SF4 weights
  COEXIST_DEFEND  : high_thr < priv_dd ≤ mid   → N2 relocate (cash or 0050)
  PUB_ONLY        : priv_dd ≤ high_thr         → Soft-Frozen pub-only path (N1 off)
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
from e45_paper_harness import load_dividends

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/priv-mdd-new-mech-n3-stagea"
RESEARCH = ROOT / "research/ops"
SLEEVE_COLS = n1.SLEEVE_COLS
OFFENSE = n1.OFFENSE
ETF_HI_CAP = float(n2.ETF_HI_CAP)

# Predeclared (mid_thr, high_thr, mid_sink) — high more negative than mid.
# Thresholds from N1/N2 autopsy cells; not a FinPriv clip / TAIEX L4 retune.
N3_SPECS = (
    ("L06_L10_0050", -0.06, -0.10, "0050"),
    ("L06_L10_CASH", -0.06, -0.10, "CASH"),
    ("L08_L12_0050", -0.08, -0.12, "0050"),
    ("L08_L12_CASH", -0.08, -0.12, "CASH"),
    ("L06_L08_0050", -0.06, -0.08, "0050"),
    ("L08_L10_0050", -0.08, -0.10, "0050"),
)


def apply_n3_three_state(
    offense: pd.DataFrame,
    defence: pd.DataFrame,
    priv_dd: pd.Series,
    *,
    mid_thr: float,
    high_thr: float,
    mid_sink: str,
    etf_hi_cap: float = ETF_HI_CAP,
) -> tuple[pd.DataFrame, pd.Series]:
    """Map FinPriv DD → three-state target weights.

    Returns (targets, state_code) where state_code is 0=OFFENSE, 1=DEFEND, 2=PUB_ONLY.
    """
    if float(high_thr) >= float(mid_thr):
        raise ValueError("high_thr must be < mid_thr (more negative)")
    common = offense.index.intersection(defence.index).intersection(priv_dd.index)
    dd = priv_dd.reindex(common).astype(float)
    out = offense.loc[common, SLEEVE_COLS].astype(float).copy()
    def_aligned = defence.loc[common, SLEEVE_COLS].astype(float)

    state = pd.Series(0, index=common, dtype=int)  # OFFENSE
    mid = (dd <= float(mid_thr)) & (dd > float(high_thr))
    high = dd <= float(high_thr)
    state.loc[mid.fillna(False)] = 1
    state.loc[high.fillna(False)] = 2

    # COEXIST_DEFEND: FinPriv → cash/0050 (N2 actuator); FinPub/TEL unchanged
    if mid.any():
        priv = out.loc[mid, "FinPriv"].to_numpy(dtype=float)
        out.loc[mid, "FinPriv"] = 0.0
        if mid_sink == "0050":
            etf = out.loc[mid, "0050"].to_numpy(dtype=float)
            room = (float(etf_hi_cap) - etf).clip(min=0.0)
            out.loc[mid, "0050"] = etf + np.minimum(priv, room)
        elif mid_sink != "CASH":
            raise ValueError(mid_sink)

    # PUB_ONLY: full Soft-Frozen pub-only path (N1 off)
    if high.any():
        out.loc[high.values, SLEEVE_COLS] = def_aligned.loc[high.values, SLEEVE_COLS].to_numpy()
        s = out.loc[high].sum(axis=1).replace(0.0, 1.0)
        out.loc[high] = out.loc[high].div(s, axis=0)

    return out, state


def _run_book(market, dividends, target, regime, *, book_id: str, meta_extra: dict):
    row = n1._sim_sf4(
        market, dividends, target, regime, book_id=book_id, meta_extra=meta_extra
    )
    for k in (
        "n3_family",
        "n3_mid_thr",
        "n3_high_thr",
        "n3_mid_sink",
        "share_offense",
        "share_defend",
        "share_pub_only",
        "etf_hi_cap",
        "n2_family",
        "n1_family",
        "gate_on_share",
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
    for k in (
        "n3_family",
        "n3_mid_thr",
        "n3_high_thr",
        "n3_mid_sink",
        "share_offense",
        "share_defend",
        "share_pub_only",
        "n2_family",
        "n1_family",
        "gate_on_share",
    ):
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

    print("SF4 offense + defence targets ...", flush=True)
    off_t, off_r = n1.build_sf4_pair(market, OFFENSE)
    def_t, _ = n1.build_sf4_pair(market, n1.DEFENCE_CTRL)
    priv_dd, _rel_60, _ = n1.sleeve_nav_features(market)

    print("SF4_OFFENSE ...", flush=True)
    results["SF4_OFFENSE"] = _run_book(
        market,
        dividends,
        off_t,
        off_r,
        book_id="SF4_OFFENSE",
        meta_extra=_meta("SF4_FROZEN", n3_family="CONTROL"),
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
            n3_family="REF_L4",
            gate_on_share=float(l4_f.mean()) if len(l4_f) else None,
        ),
    )

    print("N2_0050_LOCAL_08_REF ...", flush=True)
    flag = (priv_dd <= -0.08).fillna(False)
    n2_t, n2_f = n2.apply_n2_relocate(off_t, flag, sink="0050")
    results["N2_0050_LOCAL_08_REF"] = _run_book(
        market,
        dividends,
        n2_t,
        off_r.reindex(n2_t.index).ffill().bfill(),
        book_id="N2_0050_LOCAL_08_REF",
        meta_extra=_meta(
            "REF_N2_0050_LOCAL_08",
            n3_family="REF_N2",
            n2_family="0050",
            gate_on_share=float(n2_f.mean()) if len(n2_f) else None,
        ),
    )

    for tag, mid_thr, high_thr, sink in N3_SPECS:
        bid = f"N3_{tag}"
        print(f"{bid} ...", flush=True)
        tgt, state = apply_n3_three_state(
            off_t, def_t, priv_dd, mid_thr=mid_thr, high_thr=high_thr, mid_sink=sink
        )
        n = max(len(state), 1)
        results[bid] = _run_book(
            market,
            dividends,
            tgt,
            off_r.reindex(tgt.index).ffill().bfill(),
            book_id=bid,
            meta_extra=_meta(
                f"N3_THREE_STATE_{tag}",
                n3_family="THREE_STATE",
                n3_mid_thr=mid_thr,
                n3_high_thr=high_thr,
                n3_mid_sink=sink,
                etf_hi_cap=ETF_HI_CAP if sink == "0050" else None,
                share_offense=float((state == 0).mean()),
                share_defend=float((state == 1).mean()),
                share_pub_only=float((state == 2).mean()),
            ),
        )
        print(
            f"  shares offense/defend/pub_only = "
            f"{results[bid]['share_offense']:.3f}/"
            f"{results[bid]['share_defend']:.3f}/"
            f"{results[bid]['share_pub_only']:.3f}",
            flush=True,
        )

    asof = pd.to_datetime(live["nav"]["date"]).max()
    ranked = []
    for bid, row in results.items():
        if bid == "LIVE_PUB_KD":
            continue
        ranked.append(_extend_rank(base.rank_row(live, row, asof), row))
    ranked.sort(key=lambda r: r["score_mdd"], reverse=True)
    n3_ranked = [r for r in ranked if str(r.get("id", "")).startswith("N3_")]
    coexist = [r for r in ranked if r["coexist"]]
    n3_coexist = [r for r in coexist if r["id"].startswith("N3_")]

    if n3_coexist:
        status = "STAGE_A_CANDIDATES"
    elif any(r["gates"]["sealed_mdd"] for r in n3_ranked):
        status = "STAGE_A_SEALED_MDD_PASS_OTHER_GATES_FAIL"
    elif any(r["score_mdd"] > 0 for r in n3_ranked):
        status = "STAGE_A_SCORE_POS_GATES_FAIL"
    else:
        status = "STOP_NO_MDD_COEXIST_VS_LIVE_PUB_KD"

    keep = {
        "LIVE_PUB_KD",
        "SF4_OFFENSE",
        "SF4_L4_08_REF",
        "N2_0050_LOCAL_08_REF",
    } | {r["id"] for r in n3_coexist} | {r["id"] for r in n3_ranked[:5]}
    for bid in keep:
        if bid in results:
            results[bid]["nav"].to_csv(OUT / "outputs" / f"{bid}_daily_nav.csv", index=False)

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "PRIV_MDD_NEW_MECH_N3_STAGE_A",
        "status": status,
        "charter": "research/ops/PRIV_MDD_NEW_MECHANISM_CHARTER.md",
        "prior_n1": "research/ops/PRIV_MDD_NEW_MECH_N1_DECISION_PACK.md",
        "prior_n2": "research/ops/PRIV_MDD_NEW_MECH_N2_DECISION_PACK.md",
        "live_wire": False,
        "soft_frozen_clip": list(soft.SOFT_FROZEN_FIN_CLIP),
        "etf_hi_cap": ETF_HI_CAP,
        "baseline": "LIVE_PUB_KD",
        "frozen_offense": OFFENSE["id"],
        "asof": str(pd.Timestamp(asof).date()),
        "n_challengers": len(ranked),
        "n_n3_challengers": len(n3_ranked),
        "ranked_vs_live_pub_kd": ranked,
        "coexist_ids": [r["id"] for r in coexist],
        "n3_coexist_ids": [r["id"] for r in n3_coexist],
        "best": ranked[0] if ranked else None,
        "best_n3": n3_ranked[0] if n3_ranked else None,
    }
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    RESEARCH.joinpath("PRIV_MDD_NEW_MECH_N3_STAGE_A.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    lines = [
        "# 民股／四類 × MDD New Mechanism N3 — Stage A",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Status: **{status}** · baseline **`LIVE_PUB_KD`** · frozen offense **`{OFFENSE['id']}`**",
        "Soft-Frozen **KEEP** · live wire **false** · sealed gate **unchanged**",
        "Mechanism: three-state (OFFENSE / COEXIST_DEFEND+N2 / PUB_ONLY) on FinPriv sleeve DD",
        "",
        "## N3 coexist",
        "",
    ]
    if n3_coexist:
        for r in n3_coexist:
            lines.append(f"- `{r['id']}` · score_mdd **{r['score_mdd']}** · `{r['mechanism']}`")
    else:
        lines.append("- **None**")
    lines += [
        "",
        "## Ranked vs LIVE_PUB_KD",
        "",
        "| book | mid/high/sink | score_mdd | MDD↑ held | MDD↑ sealed | tip | tipMDD | %off/%def/%pub | coexist |",
        "|---|---|---:|---:|---:|---|---|---|---|",
    ]
    for r in ranked:
        if r["id"].startswith("N3_"):
            mh = (
                f"{r.get('n3_mid_thr')}/{r.get('n3_high_thr')}/{r.get('n3_mid_sink')}"
            )
            sh = (
                f"{100*float(r.get('share_offense') or 0):.0f}/"
                f"{100*float(r.get('share_defend') or 0):.0f}/"
                f"{100*float(r.get('share_pub_only') or 0):.0f}"
            )
        else:
            mh = str(r.get("n3_family") or "—")
            sh = "—"
        lines.append(
            f"| `{r['id']}` | `{mh}` | {r['score_mdd']:.3f} | "
            f"{r['heldout_mdd_improve_pp']:+.2f} | {r['sealed_mdd_improve_pp']:+.2f} | "
            f"{'Y' if r['tip_clean'] else 'N'} | {'Y' if r['tip_mdd_ok'] else 'N'} | "
            f"{sh} | {'Y' if r['coexist'] else 'N'} |"
        )
    lines += [
        "",
        "## Binding",
        "",
        "1. Soft-Frozen stays 3-sleeve 公股 until Class D ACCEPT.",
        "2. Do not retune FinPriv clips or TAIEX L4 from this N3 Stage A.",
        "3. N3 coexist → Stage B; else STOP new-mechanism ladder / human sealed-gate path.",
        "",
        "Repro: `PYTHONPATH=scripts python3 scripts/e16_priv_mdd_new_mech_n3_stage_a.py`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "STAGE_A.md").write_text(md)
    RESEARCH.joinpath("PRIV_MDD_NEW_MECH_N3_STAGE_A.md").write_text(md)

    decision = {
        "generated_at_utc": payload["generated_at_utc"],
        "label": "PRIV_MDD_NEW_MECH_N3_DECISION",
        "status": status,
        "live_wire": False,
        "soft_frozen_keep": True,
        "n3_coexist_ids": payload["n3_coexist_ids"],
        "best_n3": payload["best_n3"],
        "best_overall": payload["best"],
        "frozen_offense": OFFENSE["id"],
        "next": (
            "Open Stage B dual-paper observe on n3_coexist_ids"
            if n3_coexist
            else "STOP N3 — three-state machine did not clear sealed MDD coexist; Soft-Frozen 公股 KEEP; human sealed-gate or new charter"
        ),
        "charter": "research/ops/PRIV_MDD_NEW_MECHANISM_CHARTER.md",
        "stage_a": "research/ops/PRIV_MDD_NEW_MECH_N3_STAGE_A.md",
        "prior_n1": "research/ops/PRIV_MDD_NEW_MECH_N1_DECISION_PACK.md",
        "prior_n2": "research/ops/PRIV_MDD_NEW_MECH_N2_DECISION_PACK.md",
    }
    RESEARCH.joinpath("PRIV_MDD_NEW_MECH_N3_DECISION_PACK.json").write_text(
        json.dumps(decision, indent=2, default=str) + "\n"
    )
    dlines = [
        "# 民股／四類 × MDD New Mechanism N3 — Decision Pack",
        "",
        f"Date: 2026-09-19 · `{decision['generated_at_utc']}`",
        f"Status: **{status}** · Soft-Frozen **KEEP** · live wire **false**",
        f"Frozen offense: `{OFFENSE['id']}`",
        "",
        "## Verdict",
        "",
    ]
    if n3_coexist:
        dlines += [
            "**STAGE A CANDIDATES (N3)**:",
            "",
            *[f"- `{x}`" for x in decision["n3_coexist_ids"]],
        ]
    else:
        best = decision.get("best_n3") or decision.get("best_overall") or {}
        dlines += [
            "**STOP N3** — no three-state book cleared MDD coexist vs `LIVE_PUB_KD`.",
            "",
            f"Best N3: `{best.get('id')}` · score_mdd **{best.get('score_mdd')}** · "
            f"held MDD↑ **{best.get('heldout_mdd_improve_pp')}** · "
            f"sealed MDD↑ **{best.get('sealed_mdd_improve_pp')}**",
            "",
            "Binding: keep Soft-Frozen 公股 · do not Class-D flip · N1–N3 ladder exhausted under sealed gate.",
            "Next: human sealed-gate change · or a **new** charter (≠ N1–N3 retune).",
        ]
    dlines += [
        "",
        "## Refs",
        "",
        "- Charter: `PRIV_MDD_NEW_MECHANISM_CHARTER.md`",
        "- Stage A: `PRIV_MDD_NEW_MECH_N3_STAGE_A.md`",
        "- Prior: `PRIV_MDD_NEW_MECH_N1_DECISION_PACK.md` · `PRIV_MDD_NEW_MECH_N2_DECISION_PACK.md`",
        "",
        f"Label: `PRIV_MDD_NEW_MECH_N3_DECISION_2026-09-19__{status}`",
        "",
    ]
    RESEARCH.joinpath("PRIV_MDD_NEW_MECH_N3_DECISION_PACK.md").write_text("\n".join(dlines))

    print(
        json.dumps(
            {
                "status": status,
                "n3_coexist": payload["n3_coexist_ids"],
                "best_n3": payload["best_n3"],
            },
            indent=2,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
