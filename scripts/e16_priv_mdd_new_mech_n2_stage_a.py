#!/usr/bin/env python3
"""民股／四類 × MDD New Mechanism N2 — FinPriv-scoped relocate Stage A.

Charter: research/ops/PRIV_MDD_NEW_MECHANISM_CHARTER.md
Prior STOP: N1 FinPriv regime membership (PRIV_MDD_NEW_MECH_N1_DECISION_PACK).

Under N1-style stress, relocate FinPriv dollars to cash or 0050 (capped),
instead of path-switching to Soft-Frozen pub-only weights (N1).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import e16_priv_mdd_new_mech_n1_stage_a as n1
import e16_pub_priv_coexist_mdd_stage_a as base
import e16_soft_frozen_base as soft
from e45_paper_harness import load_dividends

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/priv-mdd-new-mech-n2-stagea"
RESEARCH = ROOT / "research/ops"
SLEEVE_COLS = n1.SLEEVE_COLS
OFFENSE = n1.OFFENSE
ETF_HI_CAP = float(soft.SOFT_FROZEN_ETF_HI)  # predeclared 0050 cap; overflow → cash

# N1-style triggers (compact — mid/best cells from N1 autopsy; not a new search of N1 grid)
TRIGGERS = (
    ("LOCAL_06", "local", -0.06, None),
    ("LOCAL_08", "local", -0.08, None),
    ("REL_05", "rel", None, -0.05),
    ("DUAL_L08_R05", "dual", -0.08, -0.05),
)
SINKS = ("CASH", "0050")


def apply_n2_relocate(
    offense: pd.DataFrame,
    flag: pd.Series,
    *,
    sink: str,
    etf_hi_cap: float = ETF_HI_CAP,
) -> tuple[pd.DataFrame, pd.Series]:
    """When gate ON: FinPriv → 0; dollars to cash (sum<1) or 0050 (cap; overflow cash).

    Unlike N1, FinPub/Telecom stay at offense weights (no Soft-Frozen pub-only reproject).
    """
    common = offense.index.intersection(flag.index)
    f = flag.reindex(common).fillna(False).astype(bool)
    out = offense.loc[common, SLEEVE_COLS].astype(float).copy()
    if not f.any():
        return out, f

    priv = out.loc[f, "FinPriv"].to_numpy(dtype=float)
    out.loc[f, "FinPriv"] = 0.0
    if sink == "CASH":
        # residual cash = 1 - row sum; leave FinPub/TEL/0050 unchanged
        pass
    elif sink == "0050":
        etf = out.loc[f, "0050"].to_numpy(dtype=float)
        room = (float(etf_hi_cap) - etf).clip(min=0.0)
        move = np_minimum(priv, room)
        out.loc[f, "0050"] = etf + move
        # overflow of priv beyond etf_hi_cap stays cash (not reassigned)
    else:
        raise ValueError(f"unknown sink={sink}")
    # Do not renormalize — cash residual is intentional for N2.
    return out, f


def np_minimum(a, b):
    import numpy as np

    return np.minimum(a, b)


def make_flag(priv_dd, rel_60, kind: str, local_thr, rel_thr) -> pd.Series:
    if kind == "local":
        return (priv_dd <= float(local_thr)).fillna(False)
    if kind == "rel":
        return (rel_60 <= float(rel_thr)).fillna(False)
    if kind == "dual":
        return ((priv_dd <= float(local_thr)) | (rel_60 <= float(rel_thr))).fillna(False)
    raise ValueError(kind)


def _meta(mechanism: str, **extra) -> dict:
    return {
        "mechanism": mechanism,
        "priv_pol": OFFENSE["priv_pol"],
        "fin_pub_clip": [OFFENSE["pub_lo"], OFFENSE["pub_hi"]],
        "fin_priv_clip": [OFFENSE["priv_lo"], OFFENSE["priv_hi"]],
        "prior_priv_frac": OFFENSE["prior_frac"],
        **extra,
    }


def _run_book(market, dividends, target, regime, *, book_id: str, meta_extra: dict):
    row = n1._sim_sf4(
        market, dividends, target, regime, book_id=book_id, meta_extra=meta_extra
    )
    for k in (
        "n2_family",
        "n2_sink",
        "n1_family",
        "n1_local_thr",
        "n1_rel_thr",
        "gate_on_share",
        "etf_hi_cap",
    ):
        if k in meta_extra:
            row[k] = meta_extra[k]
    return row


def _extend_rank(row: dict, src: dict) -> dict:
    row = dict(row)
    for k in (
        "n2_family",
        "n2_sink",
        "n1_local_thr",
        "n1_rel_thr",
        "gate_on_share",
        "etf_hi_cap",
        "n1_family",
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

    print("SF4 offense targets ...", flush=True)
    off_t, off_r = n1.build_sf4_pair(market, OFFENSE)
    def_t, _ = n1.build_sf4_pair(market, n1.DEFENCE_CTRL)
    priv_dd, rel_60, _ = n1.sleeve_nav_features(market)

    print("SF4_OFFENSE ...", flush=True)
    results["SF4_OFFENSE"] = _run_book(
        market,
        dividends,
        off_t,
        off_r,
        book_id="SF4_OFFENSE",
        meta_extra=_meta("SF4_FROZEN", n2_family="CONTROL"),
    )

    # N1 path-switch reference at best-sealed N1 cell (LOCAL_08) — contrast sink vs off
    print("N1_LOCAL_08_OFF_REF ...", flush=True)
    flag_n1 = make_flag(priv_dd, rel_60, "local", -0.08, None)
    n1_t, n1_f = n1.apply_priv_off_path(off_t, def_t, flag_n1)
    results["N1_LOCAL_08_OFF_REF"] = _run_book(
        market,
        dividends,
        n1_t,
        off_r.reindex(n1_t.index).ffill().bfill(),
        book_id="N1_LOCAL_08_OFF_REF",
        meta_extra=_meta(
            "REF_N1_PRIV_OFF_LOCAL_08",
            n2_family="REF_N1",
            n1_family="LOCAL",
            n1_local_thr=-0.08,
            gate_on_share=float(n1_f.mean()) if len(n1_f) else None,
        ),
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
            n2_family="REF_L4",
            gate_on_share=float(l4_f.mean()) if len(l4_f) else None,
        ),
    )

    for tag, kind, loc_thr, rel_thr in TRIGGERS:
        flag = make_flag(priv_dd, rel_60, kind, loc_thr, rel_thr)
        for sink in SINKS:
            bid = f"N2_{sink}_{tag}"
            print(f"{bid} ...", flush=True)
            tgt, f = apply_n2_relocate(off_t, flag, sink=sink)
            results[bid] = _run_book(
                market,
                dividends,
                tgt,
                off_r.reindex(tgt.index).ffill().bfill(),
                book_id=bid,
                meta_extra=_meta(
                    f"N2_TO_{sink}_{tag}",
                    n2_family=sink,
                    n2_sink=sink,
                    n1_family=kind.upper() if kind != "dual" else "DUAL",
                    n1_local_thr=loc_thr,
                    n1_rel_thr=rel_thr,
                    etf_hi_cap=ETF_HI_CAP if sink == "0050" else None,
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
    n2_ranked = [r for r in ranked if str(r.get("id", "")).startswith("N2_")]
    coexist = [r for r in ranked if r["coexist"]]
    n2_coexist = [r for r in coexist if r["id"].startswith("N2_")]

    if n2_coexist:
        status = "STAGE_A_CANDIDATES"
    elif any(r["gates"]["sealed_mdd"] for r in n2_ranked):
        status = "STAGE_A_SEALED_MDD_PASS_OTHER_GATES_FAIL"
    elif any(r["score_mdd"] > 0 for r in n2_ranked):
        status = "STAGE_A_SCORE_POS_GATES_FAIL"
    else:
        status = "STOP_NO_MDD_COEXIST_VS_LIVE_PUB_KD"

    keep = {"LIVE_PUB_KD", "SF4_OFFENSE", "N1_LOCAL_08_OFF_REF", "SF4_L4_08_REF"} | {
        r["id"] for r in n2_coexist
    } | {r["id"] for r in n2_ranked[:5]}
    for bid in keep:
        if bid in results:
            results[bid]["nav"].to_csv(OUT / "outputs" / f"{bid}_daily_nav.csv", index=False)

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "PRIV_MDD_NEW_MECH_N2_STAGE_A",
        "status": status,
        "charter": "research/ops/PRIV_MDD_NEW_MECHANISM_CHARTER.md",
        "prior_n1": "research/ops/PRIV_MDD_NEW_MECH_N1_DECISION_PACK.md",
        "live_wire": False,
        "soft_frozen_clip": list(soft.SOFT_FROZEN_FIN_CLIP),
        "etf_hi_cap": ETF_HI_CAP,
        "baseline": "LIVE_PUB_KD",
        "frozen_offense": OFFENSE["id"],
        "asof": str(pd.Timestamp(asof).date()),
        "n_challengers": len(ranked),
        "n_n2_challengers": len(n2_ranked),
        "ranked_vs_live_pub_kd": ranked,
        "coexist_ids": [r["id"] for r in coexist],
        "n2_coexist_ids": [r["id"] for r in n2_coexist],
        "best": ranked[0] if ranked else None,
        "best_n2": n2_ranked[0] if n2_ranked else None,
    }
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    RESEARCH.joinpath("PRIV_MDD_NEW_MECH_N2_STAGE_A.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    lines = [
        "# 民股／四類 × MDD New Mechanism N2 — Stage A",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Status: **{status}** · baseline **`LIVE_PUB_KD`** · frozen offense **`{OFFENSE['id']}`**",
        "Soft-Frozen **KEEP** · live wire **false** · sealed gate **unchanged**",
        f"Mechanism: FinPriv-scoped relocate → cash / 0050 (ETF hi cap **{ETF_HI_CAP}**)",
        "",
        "## N2 coexist",
        "",
    ]
    if n2_coexist:
        for r in n2_coexist:
            lines.append(f"- `{r['id']}` · score_mdd **{r['score_mdd']}** · `{r['mechanism']}`")
    else:
        lines.append("- **None**")
    lines += [
        "",
        "## Ranked vs LIVE_PUB_KD",
        "",
        "| book | sink | score_mdd | MDD↑ held | MDD↑ sealed | CAGR gb | tip | tipMDD | gate_on% | coexist |",
        "|---|---|---:|---:|---:|---:|---|---|---:|---|",
    ]
    for r in ranked:
        gos = r.get("gate_on_share")
        gos_s = f"{100.0 * float(gos):.1f}" if gos is not None else "—"
        sink = r.get("n2_sink") or r.get("n2_family") or "—"
        lines.append(
            f"| `{r['id']}` | `{sink}` | {r['score_mdd']:.3f} | "
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
        "2. Do not retune FinPriv clips or TAIEX L4 from this N2 Stage A.",
        "3. N2 coexist → Stage B; else STOP N2 / autopsy → N3 or sealed-gate human path.",
        "",
        "Repro: `PYTHONPATH=scripts python3 scripts/e16_priv_mdd_new_mech_n2_stage_a.py`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "STAGE_A.md").write_text(md)
    RESEARCH.joinpath("PRIV_MDD_NEW_MECH_N2_STAGE_A.md").write_text(md)

    decision = {
        "generated_at_utc": payload["generated_at_utc"],
        "label": "PRIV_MDD_NEW_MECH_N2_DECISION",
        "status": status,
        "live_wire": False,
        "soft_frozen_keep": True,
        "n2_coexist_ids": payload["n2_coexist_ids"],
        "best_n2": payload["best_n2"],
        "best_overall": payload["best"],
        "frozen_offense": OFFENSE["id"],
        "etf_hi_cap": ETF_HI_CAP,
        "next": (
            "Open Stage B dual-paper observe on n2_coexist_ids"
            if n2_coexist
            else "STOP N2 — FinPriv relocate did not clear sealed MDD coexist; Soft-Frozen 公股 KEEP; ballot N3 or human sealed-gate"
        ),
        "charter": "research/ops/PRIV_MDD_NEW_MECHANISM_CHARTER.md",
        "stage_a": "research/ops/PRIV_MDD_NEW_MECH_N2_STAGE_A.md",
        "prior_n1": "research/ops/PRIV_MDD_NEW_MECH_N1_DECISION_PACK.md",
    }
    RESEARCH.joinpath("PRIV_MDD_NEW_MECH_N2_DECISION_PACK.json").write_text(
        json.dumps(decision, indent=2, default=str) + "\n"
    )
    dlines = [
        "# 民股／四類 × MDD New Mechanism N2 — Decision Pack",
        "",
        f"Date: 2026-09-19 · `{decision['generated_at_utc']}`",
        f"Status: **{status}** · Soft-Frozen **KEEP** · live wire **false**",
        f"Frozen offense: `{OFFENSE['id']}` · ETF hi cap `{ETF_HI_CAP}`",
        "",
        "## Verdict",
        "",
    ]
    if n2_coexist:
        dlines += [
            "**STAGE A CANDIDATES (N2)**:",
            "",
            *[f"- `{x}`" for x in decision["n2_coexist_ids"]],
        ]
    else:
        best = decision.get("best_n2") or decision.get("best_overall") or {}
        dlines += [
            "**STOP N2** — no FinPriv-scoped relocate book cleared MDD coexist vs `LIVE_PUB_KD`.",
            "",
            f"Best N2: `{best.get('id')}` · score_mdd **{best.get('score_mdd')}** · "
            f"held MDD↑ **{best.get('heldout_mdd_improve_pp')}** · "
            f"sealed MDD↑ **{best.get('sealed_mdd_improve_pp')}**",
            "",
            "Binding: keep Soft-Frozen 公股 · do not Class-D flip · do not retune SF4 clips / TAIEX L4.",
            "Next (optional): N3 three-state machine ballot · or human sealed-gate change.",
        ]
    dlines += [
        "",
        "## Refs",
        "",
        "- Charter: `PRIV_MDD_NEW_MECHANISM_CHARTER.md`",
        "- Stage A: `PRIV_MDD_NEW_MECH_N2_STAGE_A.md`",
        "- Prior N1 STOP: `PRIV_MDD_NEW_MECH_N1_DECISION_PACK.md`",
        "",
        f"Label: `PRIV_MDD_NEW_MECH_N2_DECISION_2026-09-19__{status}`",
        "",
    ]
    RESEARCH.joinpath("PRIV_MDD_NEW_MECH_N2_DECISION_PACK.md").write_text("\n".join(dlines))

    print(
        json.dumps(
            {
                "status": status,
                "n2_coexist": payload["n2_coexist_ids"],
                "best_n2": payload["best_n2"],
            },
            indent=2,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
