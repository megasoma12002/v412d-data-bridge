#!/usr/bin/env python3
"""EXECUTE OPEN tip Soft Exact T+1 ON_UNLESS_MUTE_FT_CASH paper observe (0kba).

Human line (exact):
  OPEN paper observe: TIPSOFT_P3_ON_UNLESS_MUTE_FT_CASH
  (tip Soft Exact T+1 · Path3 ON unless lag63 prem_p3<-0.01 ∧ sat_lead ·
   Path3 OFF → FIN∪TEL→cash · Soft FIN/TEL stay OFF · NOT Soft-refill · NOT hybrid T+0)

Effects:
  - Ballot DRAFT → EXECUTED OPEN
  - Dual-paper OPERATING (frozen Exact T+1 NAVs: L4 ∥ TWIN_ON_UNLESS_MUTE_CASH)
  - Soft KEEP · Soft FIN/TEL stay OFF · Path4 OFF · hybrid T+0 FORBIDDEN
  - live_wire false · apply/cutover BLOCKED · no Soft-Frozen flip
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from e45_paper_harness import WINDOWS_STANDARD, window_stats
from fin_sell_quality_helpers import cagr_lift_pp
from ops_repro_ssot import write_ops_and_repro_pointer, write_repro_pointer
from research_metric_helpers import mdd_delta_pp

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "tipsoft-ip3-highon-cash-paper-observe"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"
TWIN = ROOT / "repro" / "tipsoft-ip3-highon-cash-twin-stageb" / "outputs"
ALIGN = ROOT / "repro" / "research-live-align-gap-stagea" / "outputs"

REGISTER = "0kba"
POLICY_ID = "TIPSOFT_P3_ON_UNLESS_MUTE_FT_CASH"
BASE_ID = "L4_LIVE_P3_WITHIN"
CHAL_ID = "ON_UNLESS_MUTE_FT_CASH"
HUMAN_OPEN = (
    "OPEN paper observe: TIPSOFT_P3_ON_UNLESS_MUTE_FT_CASH\n"
    "(tip Soft Exact T+1 · Path3 ON unless lag63 prem_p3<-0.01 ∧ sat_lead ·\n"
    " Path3 OFF → FIN∪TEL→cash · Soft FIN/TEL stay OFF · NOT Soft-refill · NOT hybrid T+0)"
)

BALLOT_DRAFT_ID = "TIPSOFT_IP3_HIGHON_CASH_OBSERVE_BALLOT_DRAFT"
BALLOT_EXEC_ID = "TIPSOFT_IP3_HIGHON_CASH_OBSERVE_BALLOT_EXECUTED_OPEN"
OPERATING_ID = "TIPSOFT_IP3_HIGHON_CASH_DUAL_PAPER_OBSERVE_OPERATING"
OPEN_ID = "TIPSOFT_IP3_HIGHON_CASH_DUAL_PAPER_OBSERVE_OPEN"
CUTOVER_ID = "CUTOVER_CHECKLIST_TIPSOFT_IP3_HIGHON_CASH"


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
            "gate": "PASS",
        }
    return out


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()

    # Frozen NAVs from Stage B twin
    base_src = TWIN / "nav_REF_L4.csv"
    if not base_src.is_file():
        base_src = ALIGN / "nav_L4_LIVE_P3_WITHIN.csv"
    chal_src = TWIN / "nav_TWIN_ON_UNLESS_MUTE_CASH.csv"
    base = _load(base_src)
    chal = _load(chal_src)
    base.to_csv(OUT / f"nav_{BASE_ID}.csv", index=False)
    chal.to_csv(OUT / f"nav_{CHAL_ID}.csv", index=False)
    base.to_csv(OUT / "l4_live_p3_within_daily_nav.csv", index=False)
    chal.to_csv(OUT / "on_unless_mute_ft_cash_daily_nav.csv", index=False)
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
    }
    b_s, c_s = bw["sealed_2023_plus"], cw["sealed_2023_plus"]
    sealed = {
        "cagr_lift_pp": round(float(cagr_lift_pp(b_s["cagr"], c_s["cagr"])), 4),
        "mdd_improve_pp": round(
            float(mdd_delta_pp(b_s["max_drawdown"], c_s["max_drawdown"])), 4
        ),
    }

    non_actions = [
        "Soft-Frozen KEEP",
        "Soft FIN/TEL Exact T+1 stay OFF (Path3 WITHIN intent KEEP)",
        "Path4 live OFF",
        "hybrid Soft-core T+0 carve FORBIDDEN",
        "year-cut / lookahead promote FORBIDDEN",
        "Return-blend apply on tip order_rows FORBIDDEN",
        "Live −P3T0 apply / cutover BLOCKED until dedicated ACCEPT",
        "broker false",
    ]

    operating = {
        "generated_at_utc": generated,
        "label": OPERATING_ID,
        "status": "OPERATING_OBSERVE",
        "register": REGISTER,
        "human_open": HUMAN_OPEN,
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
            "Path3 ON unless lag63 prem_p3 < -0.01 AND sat_lead; "
            "OFF → FIN∪TEL→cash; Soft FIN/TEL stay OFF; tip Soft Exact T+1 twin stitch"
        ),
        "stitch": "tip_r = L4_r + (SC_ON_UNLESS_MUTE_CASH_r - SC_ALWAYS_WITHIN_r)",
        "base_windows": bw,
        "chal_windows": cw,
        "heldout_delta": held,
        "sealed_delta": sealed,
        "tip": tip,
        "non_actions": non_actions,
        "parents": ["0kba", "0kb9", "0kb8", "0kac"],
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
            f"- human_open: `{HUMAN_OPEN.replace(chr(10), ' / ')}`",
            "- status: **OPERATING_OBSERVE** · live_wire: false · apply/cutover: **BLOCKED** · "
            "Soft KEEP · Soft FIN/TEL OFF · Path4 OFF · hybrid T+0 carve FORBIDDEN",
            f"- books: `{BASE_ID}` ∥ `{CHAL_ID}` (Exact T+1 tip Soft twin)",
            "- gate: Path3 ON unless lag63 prem_p3<-0.01 ∧ sat_lead · OFF→FIN∪TEL→cash",
            f"- held-out: CAGR↑ {held['cagr_lift_pp']} pp · MDD↑ {held['mdd_improve_pp']} pp",
            f"- sealed: CAGR↑ {sealed['cagr_lift_pp']} pp · MDD↑ {sealed['mdd_improve_pp']} pp",
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

    # OPEN summary
    open_payload = {
        "id": OPEN_ID,
        "register": REGISTER,
        "status": "OBSERVE_OPEN",
        "human_open": HUMAN_OPEN,
        "policy_id": POLICY_ID,
        "base_id": BASE_ID,
        "challenger_id": CHAL_ID,
        "heldout_delta": held,
        "sealed_delta": sealed,
        "tip": tip,
        "live_wire": False,
        "cutover_authorized": False,
        "apply_authorized": False,
        "generated_at_utc": generated,
        "label": f"{OPEN_ID}_{generated[:10]}__OBSERVE_OPEN__NO_LIVE",
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
            f"Date: {generated[:10]} · Status: **OBSERVE OPEN / OPERATING**",
            f"Register: **{REGISTER}**",
            "",
            "## Human (exact)",
            "",
            "```",
            HUMAN_OPEN,
            "```",
            "",
            f"- Books: `{BASE_ID}` ∥ `{CHAL_ID}`",
            f"- held **+{held['cagr_lift_pp']}** · tipY **+{(tip.get('ytd') or {}).get('cagr_lift_pp')}** · "
            f"sealed MDD **{sealed['mdd_improve_pp']}**",
            "- Soft FIN/TEL stay OFF · Path4 OFF · broker false · apply **BLOCKED**",
            "",
            f"Label: `{open_payload['label']}`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{OPEN_ID}.md", REP / f"{OPEN_ID}.md", open_md, kind="dual-paper open"
    )

    # Ballot EXECUTED OPEN
    ballot = {
        "id": BALLOT_EXEC_ID,
        "register": REGISTER,
        "status": "EXECUTED_OPEN",
        "human_open": HUMAN_OPEN,
        "supersedes": BALLOT_DRAFT_ID,
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
        "generated_at_utc": generated,
        "label": f"{BALLOT_EXEC_ID}_{generated[:10]}__OPEN__NO_LIVE",
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
            f"Date: {generated[:10]}",
            "Status: **EXECUTED OPEN / OPERATING OBSERVE** · Soft KEEP · Soft FIN/TEL stay **OFF** · "
            "Path4 OFF · broker false · apply/cutover **BLOCKED**",
            "",
            f"Register: **{REGISTER}** · Parent Stage B `TWIN_HIT` · supersedes `{BALLOT_DRAFT_ID}`",
            "",
            "## Human (exact)",
            "",
            "```",
            HUMAN_OPEN,
            "```",
            "",
            "## What changed",
            "",
            "| Item | Before | After OPEN |",
            "|---|---|---|",
            f"| Observe ballot | DRAFT | **EXECUTED OPEN** |",
            f"| Dual-paper | — | **OPERATING** (`{BASE_ID}` ∥ `{CHAL_ID}`) |",
            "| Soft FIN/TEL Exact T+1 | OFF | **stay OFF** |",
            "| Path4 / broker | OFF / false | **OFF / false** |",
            "| Live −P3T0 apply | — | **BLOCKED** (needs ACCEPT) |",
            "",
            "## Evidence",
            "",
            f"- held vs L4 **+{held['cagr_lift_pp']}** · tipY **+{(tip.get('ytd') or {}).get('cagr_lift_pp')}** · "
            f"sealed MDD **{sealed['mdd_improve_pp']}**",
            f"- Operating: `{OPERATING_ID}.md`",
            "- Stage B: `TIPSOFT_IP3_HIGHON_CASH_TWIN_STAGEB_DECISION_PACK.md`",
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

    # Mark draft superseded
    draft_md = OPS / f"{BALLOT_DRAFT_ID}.md"
    if draft_md.is_file():
        text = draft_md.read_text(encoding="utf-8")
        if "SUPERSEDED" not in text.splitlines()[2]:
            text = text.replace(
                "Status: **DRAFT — awaiting human OPEN**",
                f"Status: **SUPERSEDED by `{BALLOT_EXEC_ID}`** (OPEN EXECUTED {generated[:10]})",
            )
            draft_md.write_text(text, encoding="utf-8")
            write_repro_pointer(
                draft_md,
                ROOT
                / "repro/tipsoft-ip3-highon-cash-twin-stageb/reports"
                / f"{BALLOT_DRAFT_ID}.md",
                kind="observe ballot draft",
            )

    # Cutover checklist BLOCKED
    cut_md = "\n".join(
        [
            f"# {CUTOVER_ID}",
            "",
            f"Date: {generated[:10]} · Status: **BLOCKED** (observe OPEN only)",
            "",
            "- [x] Stage B tip Soft twin `TWIN_HIT`",
            "- [x] Human OPEN paper observe EXECUTED",
            "- [x] Dual-paper OPERATING",
            "- [ ] Month-end monitor window",
            "- [ ] ACCEPT −P3T0 apply ballot (separate)",
            "- [ ] Live wire apply (forbidden until ACCEPT)",
            "",
            "Soft FIN/TEL stay OFF · Path4 OFF · broker false",
            "",
            f"Label: `{CUTOVER_ID}_{generated[:10]}__BLOCKED`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{CUTOVER_ID}.md", REP / f"{CUTOVER_ID}.md", cut_md, kind="cutover checklist"
    )

    # Register + OPS
    reg = OPS / "HUMAN_DECISION_REGISTER.md"
    rt = reg.read_text(encoding="utf-8")
    old = (
        "| 0kba | tip Soft high-ON×CASH Exact T+1 twin Stage B | **STAGE B `TWIN_HIT`** (2026-10-01) | "
        "Parents 0kb9/0kb8/0kb7/0kac · champ **`TWIN_ON_UNLESS_MUTE_CASH`** held vs L4 **+0.87** tipY **+2.44** "
        "sealedMDD **+0.02** · TRAIL42 twin MDD_BLOCK · DRAFT observe `TIPSOFT_IP3_HIGHON_CASH_OBSERVE_BALLOT_DRAFT.md` · "
        "Soft FIN/TEL OFF · Path4 OFF · no live · `TIPSOFT_IP3_HIGHON_CASH_TWIN_STAGEB_DECISION_PACK.md` |"
    )
    new = (
        f"| 0kba | tip Soft high-ON×CASH Exact T+1 twin / observe | **OBSERVE OPEN / OPERATING** ({generated[:10]}) | "
        f"Parents 0kb9/0kb8/0kb7/0kac · human OPEN `{POLICY_ID}` · `{BASE_ID}`∥`{CHAL_ID}` held **+{held['cagr_lift_pp']}** "
        f"tipY **+{(tip.get('ytd') or {}).get('cagr_lift_pp')}** sealedMDD **{sealed['mdd_improve_pp']}** · "
        f"Soft FIN/TEL OFF · Path4 OFF · apply **BLOCKED** · `{BALLOT_EXEC_ID}.md` |"
    )
    if old in rt:
        reg.write_text(rt.replace(old, new), encoding="utf-8")
    elif "OBSERVE OPEN / OPERATING" not in rt.split("0kba")[1][:200]:
        # fallback: append note after 0kba line
        pass

    ops = OPS / "OPS_STATUS.md"
    ot = ops.read_text(encoding="utf-8")
    line = (
        f"**tip Soft high-ON×CASH observe (2026-10-01):** **OBSERVE OPEN / OPERATING** · "
        f"human OPEN `{POLICY_ID}` · held **+{held['cagr_lift_pp']}** tipY "
        f"**+{(tip.get('ytd') or {}).get('cagr_lift_pp')}** · Soft FIN/TEL OFF · Path4 OFF · "
        f"apply BLOCKED · `{BALLOT_EXEC_ID}.md`  \n"
    )
    if "high-ON×CASH observe" not in ot:
        needle = (
            "**tip Soft high-ON×CASH twin (2026-10-01):** Stage B **`TWIN_HIT`** · "
            "champ `ON_UNLESS_MUTE×CASH` held **+0.87** tipY **+2.44** sealedMDD **+0.02** · "
            "DRAFT observe · Soft FIN/TEL OFF · Path4 OFF · no live · "
            "`TIPSOFT_IP3_HIGHON_CASH_TWIN_STAGEB_DECISION_PACK.md`  \n"
        )
        if needle in ot:
            ops.write_text(ot.replace(needle, needle + line), encoding="utf-8")
        else:
            idx = ot.find("TIPSOFT_IP3_HIGHON_CASH_TWIN_STAGEB_DECISION_PACK.md")
            if idx > 0:
                end = ot.find("\n", idx) + 1
                ops.write_text(ot[:end] + line + ot[end:], encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "OBSERVE_OPEN",
                "held": held,
                "tipY": (tip.get("ytd") or {}).get("cagr_lift_pp"),
                "sealed_mdd": sealed["mdd_improve_pp"],
                "ballot": BALLOT_EXEC_ID,
                "operating": OPERATING_ID,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
