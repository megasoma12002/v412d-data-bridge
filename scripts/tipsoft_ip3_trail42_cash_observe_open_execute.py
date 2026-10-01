#!/usr/bin/env python3
"""Human ACCEPTABLE sealed MDD for TRAIL42×CASH twin + OPEN paper observe (0kbb).

Human (exact):
  Trail42 cash的mdd可接受
  → sealed MDD −0.36pp ACCEPTABLE (abs sealed ≪ held)
  → OPEN paper observe: TIPSOFT_P3_TRAIL42_FT_CASH

Effects:
  - Disposition pack ACCEPTABLE (unlocks Stage B sensitivity from TWIN_MDD_BLOCK for observe)
  - Dual-paper OPERATING (L4 ∥ TWIN_TRAIL42_CASH Exact T+1)
  - Soft KEEP · Soft FIN/TEL stay OFF · Path4 OFF · hybrid T+0 FORBIDDEN
  - live_wire false · apply/cutover BLOCKED · ON_UNLESS_MUTE observe KEEP OPERATING
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from e45_paper_harness import WINDOWS_STANDARD, window_stats
from fin_sell_quality_helpers import cagr_lift_pp
from ops_repro_ssot import write_ops_and_repro_pointer
from research_metric_helpers import mdd_delta_pp

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "tipsoft-ip3-trail42-cash-paper-observe"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"
TWIN = ROOT / "repro" / "tipsoft-ip3-highon-cash-twin-stageb" / "outputs"
ALIGN = ROOT / "repro" / "research-live-align-gap-stagea" / "outputs"

REGISTER = "0kbb"
POLICY_ID = "TIPSOFT_P3_TRAIL42_FT_CASH"
BASE_ID = "L4_LIVE_P3_WITHIN"
CHAL_ID = "TRAIL42_FT_CASH"
HUMAN_MDD = "Trail42 cash的mdd可接受"
HUMAN_OPEN = (
    "OPEN paper observe: TIPSOFT_P3_TRAIL42_FT_CASH\n"
    "(tip Soft Exact T+1 · Path3 ON when trail42d prem_p3≥−0.01 ·\n"
    " Path3 OFF → FIN∪TEL→cash · Soft FIN/TEL stay OFF · sealed MDD −0.36 ACCEPTABLE ·\n"
    " NOT Soft-refill · NOT hybrid T+0)"
)

DISP_ID = "TIPSOFT_IP3_TRAIL42_CASH_SEALED_MDD_DISPOSITION"
BALLOT_EXEC_ID = "TIPSOFT_IP3_TRAIL42_CASH_OBSERVE_BALLOT_EXECUTED_OPEN"
OPERATING_ID = "TIPSOFT_IP3_TRAIL42_CASH_DUAL_PAPER_OBSERVE_OPERATING"
OPEN_ID = "TIPSOFT_IP3_TRAIL42_CASH_DUAL_PAPER_OBSERVE_OPEN"
CUTOVER_ID = "CUTOVER_CHECKLIST_TIPSOFT_IP3_TRAIL42_CASH"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"])
    return (
        df[["date", "nav"]]
        .assign(
            date=lambda x: pd.to_datetime(x["date"]).dt.normalize(),
            nav=lambda x: x["nav"].astype(float),
        )
        .sort_values("date")
        .reset_index(drop=True)
    )


def _pack(nav: pd.DataFrame) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, (a, b) in WINDOWS_STANDARD.items():
        st = window_stats(nav, a, b)
        out[k] = {
            "cagr": None if st.get("cagr") is None else round(float(st["cagr"]), 6),
            "max_drawdown": None
            if st.get("max_drawdown") is None
            else round(float(st["max_drawdown"]), 6),
            "n_days": int(st.get("n_days") or 0),
        }
    return out


def _tip(base_nav: pd.DataFrame, chal_nav: pd.DataFrame) -> dict[str, Any]:
    asof = pd.Timestamp(pd.to_datetime(base_nav["date"]).max())
    b_dates = pd.to_datetime(base_nav["date"])
    c_dates = pd.to_datetime(chal_nav["date"])
    out: dict[str, Any] = {}
    for wname, start in (
        ("ytd", pd.Timestamp(asof.year, 1, 1)),
        ("trailing_1y", asof - pd.Timedelta(days=365)),
    ):
        b = base_nav[(b_dates >= start) & (b_dates <= asof)].reset_index(drop=True)
        c = chal_nav[(c_dates >= start) & (c_dates <= asof)].reset_index(drop=True)
        if len(b) < 20 or len(c) < 20:
            out[wname] = {
                "cagr_lift_pp": None,
                "mdd_improve_pp": None,
                "gate": "INSUFFICIENT",
            }
            continue
        bn = b["nav"].astype(float) / float(b["nav"].iloc[0])
        cn = c["nav"].astype(float) / float(c["nav"].iloc[0])
        b_mdd = float((bn / bn.cummax() - 1.0).min())
        c_mdd = float((cn / cn.cummax() - 1.0).min())
        years = (len(b) - 1) / 252.0
        bc = float(bn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        cc = float(cn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        out[wname] = {
            "cagr_lift_pp": None
            if cagr_lift_pp(bc, cc) is None
            else round(float(cagr_lift_pp(bc, cc)), 4),
            "mdd_improve_pp": round(float(mdd_delta_pp(b_mdd, c_mdd)), 4),
            "base_mdd": round(b_mdd, 6),
            "chal_mdd": round(c_mdd, 6),
            "gate": "PASS",
        }
    return out


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()
    day = generated[:10]

    base_src = TWIN / "nav_REF_L4.csv"
    if not base_src.is_file():
        base_src = ALIGN / "nav_L4_LIVE_P3_WITHIN.csv"
    chal_src = TWIN / "nav_TWIN_TRAIL42_CASH.csv"
    base = _load(base_src)
    chal = _load(chal_src)
    base.to_csv(OUT / f"nav_{BASE_ID}.csv", index=False)
    chal.to_csv(OUT / f"nav_{CHAL_ID}.csv", index=False)
    cmp = base.merge(chal, on="date", suffixes=("_base", "_chal"))
    cmp.to_csv(OUT / "dual_paper_nav_compare.csv", index=False)

    bw, cw = _pack(base), _pack(chal)
    tip = _tip(base, chal)
    b_h, c_h = bw["heldout_2019_plus"], cw["heldout_2019_plus"]
    held = {
        "cagr_lift_pp": round(float(cagr_lift_pp(b_h["cagr"], c_h["cagr"])), 4),
        "mdd_improve_pp": round(
            float(mdd_delta_pp(b_h["max_drawdown"], c_h["max_drawdown"])), 4
        ),
        "base_mdd": b_h["max_drawdown"],
        "chal_mdd": c_h["max_drawdown"],
    }
    b_s, c_s = bw["sealed_2023_plus"], cw["sealed_2023_plus"]
    sealed = {
        "cagr_lift_pp": round(float(cagr_lift_pp(b_s["cagr"], c_s["cagr"])), 4),
        "mdd_improve_pp": round(
            float(mdd_delta_pp(b_s["max_drawdown"], c_s["max_drawdown"])), 4
        ),
        "base_mdd": b_s["max_drawdown"],
        "chal_mdd": c_s["max_drawdown"],
    }
    b_f, c_f = bw["full"], cw["full"]
    full = {
        "cagr_lift_pp": round(float(cagr_lift_pp(b_f["cagr"], c_f["cagr"])), 4),
        "mdd_improve_pp": round(
            float(mdd_delta_pp(b_f["max_drawdown"], c_f["max_drawdown"])), 4
        ),
        "base_mdd": b_f["max_drawdown"],
        "chal_mdd": c_f["max_drawdown"],
    }

    # --- Sealed MDD disposition ACCEPTABLE ---
    disp = {
        "id": DISP_ID,
        "register": REGISTER,
        "status": "HUMAN_DISPOSITION_ACCEPTABLE",
        "human": HUMAN_MDD,
        "policy_id": POLICY_ID,
        "parent_stageb": "0kba",
        "prior_verdict": "TWIN_MDD_BLOCK",
        "sealed_mdd_improve_pp": sealed["mdd_improve_pp"],
        "held_mdd_improve_pp": held["mdd_improve_pp"],
        "rationale": (
            "Absolute sealed |MDD| ≈ 6.7–7.1% ≪ held ≈ 14.4%; "
            "sealed tax −0.36pp ACCEPTABLE for paper observe continuation"
        ),
        "live_wire": False,
        "cutover_authorized": False,
        "apply_authorized": False,
        "generated_at_utc": generated,
        "label": f"{DISP_ID}_{day}__ACCEPTABLE__NO_LIVE",
    }
    write_ops_and_repro_pointer(
        OPS / f"{DISP_ID}.json",
        REP / f"{DISP_ID}.json",
        json.dumps(disp, indent=2) + "\n",
        kind="sealed mdd disposition",
    )
    disp_md = "\n".join(
        [
            f"# {DISP_ID}",
            "",
            f"Date: {day}",
            "Status: **HUMAN DISPOSITION** · sealed MDD **ACCEPTABLE** · observe unlock · "
            "cutover still **BLOCKED** · no live",
            f"Register: **{REGISTER}** · Parent Stage B **0kba** (`TWIN_TRAIL42_CASH` was `TWIN_MDD_BLOCK`)",
            "",
            "## Human",
            "",
            f"> {HUMAN_MDD}",
            "",
            "## Numbers (Exact T+1 tip Soft twin vs L4)",
            "",
            "| Window | base MDD | chal MDD | Δ pp |",
            "|---|---:|---:|---:|",
            f"| held-out 2019+ | {held['base_mdd']:.2%} | {held['chal_mdd']:.2%} | "
            f"**+{held['mdd_improve_pp']:.2f}** (better) |",
            f"| sealed 2023+ | {sealed['base_mdd']:.2%} | {sealed['chal_mdd']:.2%} | "
            f"**{sealed['mdd_improve_pp']:.2f}** (worse) |",
            f"| full | {full['base_mdd']:.2%} | {full['chal_mdd']:.2%} | "
            f"**{full['mdd_improve_pp']:.2f}** |",
            "",
            "Absolute sealed |MDD| ≈ 6.7–7.1% ≪ held ≈ 14.4%.",
            "",
            "## Effect",
            "",
            "- Stage B sensitivity `TWIN_TRAIL42_CASH` sealed MDD tax marked **ACCEPTABLE** for "
            "paper observe (overrides `TWIN_MDD_BLOCK` for observe eligibility only)",
            "- Does **not** authorize live cutover / ACCEPT −P3T0 apply · Soft FIN/TEL stay OFF · "
            "Path4 OFF · broker false",
            f"- Unlocks OPEN observe `{POLICY_ID}`",
            "",
            f"Label: `{disp['label']}`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{DISP_ID}.md", REP / f"{DISP_ID}.md", disp_md, kind="sealed mdd disposition"
    )

    non_actions = [
        "Soft-Frozen KEEP",
        "Soft FIN/TEL Exact T+1 stay OFF (Path3 WITHIN intent KEEP)",
        "Path4 live OFF",
        "hybrid Soft-core T+0 carve FORBIDDEN",
        "year-cut / lookahead promote FORBIDDEN",
        "Return-blend apply on tip order_rows FORBIDDEN",
        "Live −P3T0 apply / cutover BLOCKED until dedicated ACCEPT",
        "ON_UNLESS_MUTE_FT_CASH observe KEEP OPERATING (sibling 0kba)",
        "broker false",
    ]

    operating = {
        "generated_at_utc": generated,
        "label": OPERATING_ID,
        "status": "OPERATING_OBSERVE",
        "register": REGISTER,
        "human_mdd": HUMAN_MDD,
        "human_open": HUMAN_OPEN,
        "sealed_mdd_disposition": "ACCEPTABLE",
        "live_wire": False,
        "cutover_authorized": False,
        "apply_authorized": False,
        "soft_frozen_keep": True,
        "soft_fin_tel": "OFF",
        "path4_live": False,
        "hybrid_t0_carve": False,
        "broker": False,
        "base_id": BASE_ID,
        "challenger_id": CHAL_ID,
        "policy_id": POLICY_ID,
        "gate": (
            "Path3 ON when trail42d prem_p3 ≥ −0.01; "
            "OFF → FIN∪TEL→cash; Soft FIN/TEL stay OFF; tip Soft Exact T+1 twin stitch"
        ),
        "stitch": "tip_r = L4_r + (SC_TRAIL42_CASH_r - SC_ALWAYS_WITHIN_r)",
        "base_windows": bw,
        "chal_windows": cw,
        "heldout_delta": {
            "cagr_lift_pp": held["cagr_lift_pp"],
            "mdd_improve_pp": held["mdd_improve_pp"],
        },
        "sealed_delta": {
            "cagr_lift_pp": sealed["cagr_lift_pp"],
            "mdd_improve_pp": sealed["mdd_improve_pp"],
        },
        "tip": tip,
        "non_actions": non_actions,
        "parents": ["0kbb", "0kba", "0kb9", "0kac"],
        "disposition": DISP_ID,
    }
    (OUT / "dual_paper_operating.json").write_text(
        json.dumps(operating, indent=2) + "\n", encoding="utf-8"
    )
    write_ops_and_repro_pointer(
        OPS / f"{OPERATING_ID}.json",
        REP / f"{OPERATING_ID}.json",
        json.dumps(operating, indent=2) + "\n",
        kind="dual-paper operating",
    )
    op_md = "\n".join(
        [
            f"# {POLICY_ID} dual-paper observe — OPERATING",
            "",
            f"- human_mdd: `{HUMAN_MDD}` → sealed MDD **ACCEPTABLE**",
            f"- human_open: `{HUMAN_OPEN.replace(chr(10), ' / ')}`",
            "- status: **OPERATING_OBSERVE** · live_wire: false · apply/cutover: **BLOCKED** · "
            "Soft KEEP · Soft FIN/TEL OFF · Path4 OFF · hybrid T+0 carve FORBIDDEN",
            f"- books: `{BASE_ID}` ∥ `{CHAL_ID}` (Exact T+1 tip Soft twin)",
            "- gate: Path3 ON when trail42d prem_p3≥−0.01 · OFF→FIN∪TEL→cash",
            f"- held-out: CAGR↑ {held['cagr_lift_pp']} pp · MDD↑ {held['mdd_improve_pp']} pp",
            f"- sealed: CAGR↑ {sealed['cagr_lift_pp']} pp · MDD↑ {sealed['mdd_improve_pp']} pp "
            f"(**ACCEPTABLE**)",
            f"- tip ytd CAGR↑ {(tip.get('ytd') or {}).get('cagr_lift_pp')} · "
            f"tip 1y CAGR↑ {(tip.get('trailing_1y') or {}).get('cagr_lift_pp')}",
            "",
            "## Non-actions",
            "",
        ]
        + [f"- {x}" for x in non_actions]
        + ["", f"Repro: `{REPRO.relative_to(ROOT)}/`", ""]
    )
    write_ops_and_repro_pointer(
        OPS / f"{OPERATING_ID}.md",
        REP / f"{OPERATING_ID}.md",
        op_md,
        kind="dual-paper operating",
    )

    open_payload = {
        "id": OPEN_ID,
        "register": REGISTER,
        "status": "OBSERVE_OPEN",
        "human_mdd": HUMAN_MDD,
        "human_open": HUMAN_OPEN,
        "policy_id": POLICY_ID,
        "base_id": BASE_ID,
        "challenger_id": CHAL_ID,
        "heldout_delta": {
            "cagr_lift_pp": held["cagr_lift_pp"],
            "mdd_improve_pp": held["mdd_improve_pp"],
        },
        "sealed_delta": {
            "cagr_lift_pp": sealed["cagr_lift_pp"],
            "mdd_improve_pp": sealed["mdd_improve_pp"],
        },
        "tip": tip,
        "sealed_mdd_disposition": "ACCEPTABLE",
        "live_wire": False,
        "cutover_authorized": False,
        "apply_authorized": False,
        "generated_at_utc": generated,
        "label": f"{OPEN_ID}_{day}__OBSERVE_OPEN__NO_LIVE",
    }
    write_ops_and_repro_pointer(
        OPS / f"{OPEN_ID}.json",
        REP / f"{OPEN_ID}.json",
        json.dumps(open_payload, indent=2) + "\n",
        kind="dual-paper open",
    )
    open_md = "\n".join(
        [
            f"# {OPEN_ID}",
            "",
            f"Date: {day} · Status: **OBSERVE OPEN / OPERATING**",
            f"Register: **{REGISTER}**",
            "",
            "## Human (exact)",
            "",
            "```",
            HUMAN_MDD,
            "",
            HUMAN_OPEN,
            "```",
            "",
            f"- Books: `{BASE_ID}` ∥ `{CHAL_ID}`",
            f"- held **+{held['cagr_lift_pp']}** · tipY **+{(tip.get('ytd') or {}).get('cagr_lift_pp')}** · "
            f"sealed MDD **{sealed['mdd_improve_pp']} ACCEPTABLE**",
            "- Soft FIN/TEL stay OFF · Path4 OFF · broker false · apply **BLOCKED**",
            f"- Sibling 0kba `ON_UNLESS_MUTE_FT_CASH` observe **KEEP OPERATING**",
            "",
            f"Label: `{open_payload['label']}`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{OPEN_ID}.md", REP / f"{OPEN_ID}.md", open_md, kind="dual-paper open"
    )

    ballot = {
        "id": BALLOT_EXEC_ID,
        "register": REGISTER,
        "status": "EXECUTED_OPEN",
        "human_mdd": HUMAN_MDD,
        "human_open": HUMAN_OPEN,
        "disposition": DISP_ID,
        "policy_id": POLICY_ID,
        "operating": OPERATING_ID,
        "live_wire": False,
        "cutover_authorized": False,
        "apply_authorized": False,
        "soft_fin_tel": "OFF",
        "path4_live": False,
        "broker": False,
        "held_vs_L4_pp": held["cagr_lift_pp"],
        "tipY_vs_L4_pp": (tip.get("ytd") or {}).get("cagr_lift_pp"),
        "sealed_mdd_vs_L4_pp": sealed["mdd_improve_pp"],
        "sealed_mdd_disposition": "ACCEPTABLE",
        "generated_at_utc": generated,
        "label": f"{BALLOT_EXEC_ID}_{day}__OPEN__NO_LIVE",
    }
    write_ops_and_repro_pointer(
        OPS / f"{BALLOT_EXEC_ID}.json",
        REP / f"{BALLOT_EXEC_ID}.json",
        json.dumps(ballot, indent=2) + "\n",
        kind="observe ballot executed",
    )
    ballot_md = "\n".join(
        [
            f"# {BALLOT_EXEC_ID}",
            "",
            f"Date: {day}",
            "Status: **EXECUTED OPEN / OPERATING OBSERVE** · Soft KEEP · Soft FIN/TEL stay **OFF** · "
            "Path4 OFF · broker false · apply/cutover **BLOCKED**",
            "",
            f"Register: **{REGISTER}** · Parent 0kba Stage B sensitivity · "
            f"disposition `{DISP_ID}` **ACCEPTABLE**",
            "",
            "## Human (exact)",
            "",
            "```",
            HUMAN_MDD,
            "",
            HUMAN_OPEN,
            "```",
            "",
            "## What changed",
            "",
            "| Item | Before | After |",
            "|---|---|---|",
            f"| Sealed MDD (−0.36pp) | `TWIN_MDD_BLOCK` | **ACCEPTABLE** |",
            f"| Observe | — | **EXECUTED OPEN** `{POLICY_ID}` |",
            f"| Dual-paper | — | **OPERATING** (`{BASE_ID}` ∥ `{CHAL_ID}`) |",
            "| Soft FIN/TEL Exact T+1 | OFF | **stay OFF** |",
            "| Path4 / broker | OFF / false | **OFF / false** |",
            "| 0kba ON_UNLESS_MUTE observe | OPERATING | **KEEP OPERATING** |",
            "| Live −P3T0 apply | — | **BLOCKED** (needs ACCEPT) |",
            "",
            "## Evidence",
            "",
            f"- held vs L4 **+{held['cagr_lift_pp']}** · tipY **+{(tip.get('ytd') or {}).get('cagr_lift_pp')}** · "
            f"sealed MDD **{sealed['mdd_improve_pp']} ACCEPTABLE**",
            f"- Disposition: `{DISP_ID}.md`",
            f"- Operating: `{OPERATING_ID}.md`",
            "",
            "## Non-actions",
            "",
        ]
        + [f"- {x}" for x in non_actions]
        + ["", f"Label: `{ballot['label']}`", ""]
    )
    write_ops_and_repro_pointer(
        OPS / f"{BALLOT_EXEC_ID}.md",
        REP / f"{BALLOT_EXEC_ID}.md",
        ballot_md,
        kind="observe ballot executed",
    )

    cut_md = "\n".join(
        [
            f"# {CUTOVER_ID}",
            "",
            f"Date: {day} · Status: **BLOCKED** (observe OPEN only · sealed MDD ACCEPTABLE ≠ cutover)",
            "",
            "- [x] Stage B tip Soft twin `TWIN_TRAIL42_CASH` (was MDD_BLOCK)",
            "- [x] Human sealed MDD **ACCEPTABLE**",
            "- [x] Human OPEN paper observe EXECUTED",
            "- [x] Dual-paper OPERATING",
            "- [ ] Month-end monitor window",
            "- [ ] ACCEPT −P3T0 apply ballot (separate)",
            "- [ ] Live wire apply (forbidden until ACCEPT)",
            "",
            "Soft FIN/TEL stay OFF · Path4 OFF · broker false",
            "",
            f"Label: `{CUTOVER_ID}_{day}__BLOCKED`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{CUTOVER_ID}.md", REP / f"{CUTOVER_ID}.md", cut_md, kind="cutover checklist"
    )

    # Register 0kbb row (insert after 0kba)
    reg = OPS / "HUMAN_DECISION_REGISTER.md"
    rt = reg.read_text(encoding="utf-8")
    row_0kba = None
    for line in rt.splitlines():
        if line.startswith("| 0kba |"):
            row_0kba = line
            break
    new_row = (
        f"| 0kbb | tip Soft TRAIL42×CASH Exact T+1 observe | **OBSERVE OPEN / OPERATING** ({day}) | "
        f"Parents 0kba/0kb9/0kac · human `{HUMAN_MDD}` → sealed MDD **{sealed['mdd_improve_pp']} ACCEPTABLE** · "
        f"OPEN `{POLICY_ID}` · `{BASE_ID}`∥`{CHAL_ID}` held **+{held['cagr_lift_pp']}** "
        f"tipY **+{(tip.get('ytd') or {}).get('cagr_lift_pp')}** · Soft FIN/TEL OFF · Path4 OFF · "
        f"apply **BLOCKED** · 0kba ON_UNLESS_MUTE KEEP · `{BALLOT_EXEC_ID}.md` · `{DISP_ID}.md` |"
    )
    if row_0kba and "| 0kbb |" not in rt:
        rt = rt.replace(row_0kba, row_0kba + "\n" + new_row)
        reg.write_text(rt, encoding="utf-8")

    ops = OPS / "OPS_STATUS.md"
    ot = ops.read_text(encoding="utf-8")
    line = (
        f"**tip Soft TRAIL42×CASH observe (2026-10-01):** **OBSERVE OPEN / OPERATING** · "
        f"human `{HUMAN_MDD}` → sealed MDD **{sealed['mdd_improve_pp']} ACCEPTABLE** · "
        f"OPEN `{POLICY_ID}` held **+{held['cagr_lift_pp']}** tipY "
        f"**+{(tip.get('ytd') or {}).get('cagr_lift_pp')}** · Soft FIN/TEL OFF · Path4 OFF · "
        f"apply BLOCKED · 0kba KEEP · `{BALLOT_EXEC_ID}.md`  \n"
    )
    if "TRAIL42×CASH observe" not in ot:
        needle = (
            "**tip Soft high-ON×CASH observe (2026-10-01):** **OBSERVE OPEN / OPERATING** · "
            "human OPEN `TIPSOFT_P3_ON_UNLESS_MUTE_FT_CASH` · held **+0.8735** tipY **+2.4396** · "
            "Soft FIN/TEL OFF · Path4 OFF · apply BLOCKED · "
            "`TIPSOFT_IP3_HIGHON_CASH_OBSERVE_BALLOT_EXECUTED_OPEN.md`  \n"
        )
        if needle in ot:
            ops.write_text(ot.replace(needle, needle + line), encoding="utf-8")
            ot = ops.read_text(encoding="utf-8")
        else:
            idx = ot.find("TIPSOFT_IP3_HIGHON_CASH_OBSERVE_BALLOT_EXECUTED_OPEN.md")
            if idx > 0:
                end = ot.find("\n", idx) + 1
                ops.write_text(ot[:end] + line + ot[end:], encoding="utf-8")
                ot = ops.read_text(encoding="utf-8")

    table_row = (
        f"| tip Soft Exact T+1 `{POLICY_ID}` | **OBSERVE OPEN** ({day}) | "
        f"TRAIL42≥−0.01 × FT→CASH · sealed MDD **ACCEPTABLE** (−0.36) · Soft FIN/TEL stay OFF · "
        f"apply/cutover **BLOCKED** · `{BALLOT_EXEC_ID}.md` |"
    )
    if POLICY_ID not in ot:
        anchor = (
            "| tip Soft Exact T+1 `TIPSOFT_P3_ON_UNLESS_MUTE_FT_CASH` | **OBSERVE OPEN** (2026-10-01) | "
            "Path3 ON unless lag63 prem_p3<-0.01 ∧ sat_lead · OFF→FIN∪TEL→cash · Soft FIN/TEL stay OFF · "
            "Exact T+1 tip Soft twin · apply/cutover **BLOCKED** · "
            "`TIPSOFT_IP3_HIGHON_CASH_OBSERVE_BALLOT_EXECUTED_OPEN.md` |"
        )
        ot = ops.read_text(encoding="utf-8")
        if anchor in ot:
            ops.write_text(ot.replace(anchor, anchor + "\n" + table_row), encoding="utf-8")

    # Annotate Stage B pack sensitivity line
    pack = OPS / "TIPSOFT_IP3_HIGHON_CASH_TWIN_STAGEB_DECISION_PACK.md"
    if pack.is_file():
        pt = pack.read_text(encoding="utf-8")
        old = (
            "- Sensitivity `TWIN_TRAIL42_CASH`: held **+1.45** tipY **+11.34** sealedMDD **−0.36** "
            "→ **MDD_BLOCK** (not observe champ)"
        )
        new = (
            "- Sensitivity `TWIN_TRAIL42_CASH`: held **+1.45** tipY **+11.34** sealedMDD **−0.36** "
            "→ was **MDD_BLOCK**; human **ACCEPTABLE** 2026-10-01 → observe OPEN `TIPSOFT_P3_TRAIL42_FT_CASH` "
            "(0kbb) · see `TIPSOFT_IP3_TRAIL42_CASH_SEALED_MDD_DISPOSITION.md`"
        )
        if old in pt:
            pack.write_text(pt.replace(old, new), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "OBSERVE_OPEN",
                "disposition": "ACCEPTABLE",
                "held": {
                    "cagr_lift_pp": held["cagr_lift_pp"],
                    "mdd_improve_pp": held["mdd_improve_pp"],
                },
                "tipY": (tip.get("ytd") or {}).get("cagr_lift_pp"),
                "sealed_mdd": sealed["mdd_improve_pp"],
                "ballot": BALLOT_EXEC_ID,
                "operating": OPERATING_ID,
                "disposition_id": DISP_ID,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
