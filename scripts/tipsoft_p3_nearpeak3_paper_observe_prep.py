#!/usr/bin/env python3
"""Tip Soft Exact T+1 P3_THETA_NEARPEAK3 paper/observe candidate (0kaw).

Disposition from 0kav: hybrid Soft-core T+0 carve NEARPEAK3 = MDD_BLOCK;
tip Soft Exact T+1 ``P3_THETA_NEARPEAK3`` dual-track = HIT KEEP.

This pack freezes the paper/observe candidate path:
  Soft Exact T+1 FUSE+COOL shell + Path3 WITHIN premium only when
  |trail_rel_63|≥θ AND Soft within 3% of 63d peak.

NOT hybrid T+0 carve. Soft KEEP · Path4 OFF · broker false · live flag OFF
· cutover BLOCKED · DRAFT ballot awaiting human OPEN.
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from ops_repro_ssot import write_ops_and_repro_pointer, write_repro_pointer

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "tipsoft-p3-nearpeak3-paper-observe"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

HARDEN = ROOT / "repro" / "meta-detect-sealed-mdd-harden-stagea" / "outputs"
ALIGN = ROOT / "repro" / "research-live-align-gap-stagea" / "outputs"

CHARTER_ID = "TIPSOFT_P3_NEARPEAK3_PAPER_OBSERVE_CHARTER"
CANDIDATE_ID = "TIPSOFT_P3_NEARPEAK3_PAPER_OBSERVE_CANDIDATE"
BALLOT_ID = "TIPSOFT_P3_NEARPEAK3_OBSERVE_BALLOT_DRAFT"
DUAL_ID = "TIPSOFT_P3_NEARPEAK3_DUAL_PAPER_OBSERVE_PREP"
CUTOVER_ID = "CUTOVER_CHECKLIST_TIPSOFT_P3_NEARPEAK3"
REGISTER = "0kaw"
PARENTS = ("0kav", "0kau", "0kat")

POLICY_ID = "P3_THETA_NEARPEAK3"
CLOCK = "exact_t1"
FILL_TIMING = "exact_t1"
P3_THETA = 0.005
NEAR_PEAK_PCT = 0.03


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()
    day = generated[:10]

    # Freeze SSOT NAVs into this repro (base live + challenger tip Soft NEARPEAK3)
    src_chal = HARDEN / "nav_P3_THETA_NEARPEAK3.csv"
    src_base = ALIGN / "nav_L3_LIVE_FUSE_COOL.csv"
    if not src_chal.exists():
        raise SystemExit(f"missing challenger NAV: {src_chal}")
    if not src_base.exists():
        raise SystemExit(f"missing base NAV: {src_base}")

    dst_chal = OUT / f"nav_{POLICY_ID}.csv"
    dst_base = OUT / "nav_BASE_LIVE_FUSE_COOL.csv"
    shutil.copy2(src_chal, dst_chal)
    shutil.copy2(src_base, dst_base)

    # Duty cycle from harden panel if present
    duty: dict[str, Any] = {
        "policy_id": POLICY_ID,
        "clock": CLOCK,
        "fill_timing": FILL_TIMING,
        "p3_theta": P3_THETA,
        "near_peak_pct": NEAR_PEAK_PCT,
        "gate": "|trail_rel_63|≥θ AND Soft DD63_peak ≥ −3%",
        "hybrid_t0_carve": False,
        "path4": False,
    }
    panel = HARDEN / "detector_panel.csv"
    if panel.exists():
        det = pd.read_csv(panel, parse_dates=["date"])
        if "near_peak_3" in det.columns and "p3_theta" in det.columns:
            g = (det["p3_theta"].astype(int) == 1) & (det["near_peak_3"].astype(int) == 1)
            duty["pct_gate_on"] = round(float(g.mean()) * 100, 2)
            duty["n_days"] = int(len(det))
    arms = HARDEN / "arms_vs_live.csv"
    metrics: dict[str, Any] = {}
    if arms.exists():
        df = pd.read_csv(arms)
        row = df[df["arm"] == "P3_THETA_NEARPEAK3"]
        if not row.empty:
            r = row.iloc[0]
            metrics = {
                "verdict_vs_live": str(r.get("verdict")),
                "held_cagr_lift_pp": float(r["held"]) if pd.notna(r.get("held")) else None,
                "full_cagr_lift_pp": float(r["full"]) if pd.notna(r.get("full")) else None,
                "sealed_mdd_improve_pp": float(r["sealed_mdd"])
                if pd.notna(r.get("sealed_mdd"))
                else None,
                "tip_ytd_cagr_lift_pp": float(r["tipY"]) if pd.notna(r.get("tipY")) else None,
                "tip_1y_cagr_lift_pp": float(r["tip1y"]) if pd.notna(r.get("tip1y")) else None,
                "pct_p3_on": float(r["pct_p3"]) if pd.notna(r.get("pct_p3")) else None,
            }

    candidate = {
        "id": CANDIDATE_ID,
        "register": REGISTER,
        "parents": list(PARENTS),
        "generated_at_utc": generated,
        "status": "PAPER_OBSERVE_CANDIDATE_DRAFT",
        "policy_id": POLICY_ID,
        "clock": CLOCK,
        "fill_timing": FILL_TIMING,
        "hybrid_t0_carve": False,
        "path4_live": False,
        "soft_keep": True,
        "broker": False,
        "live_wire": False,
        "cutover_blocked": True,
        "base_book": "BASE_LIVE_FUSE_COOL",
        "challenger_book": POLICY_ID,
        "duty": duty,
        "stage_a_metrics_0kau": metrics,
        "stage_b_hybrid_0kav": {
            "verdict": "HYBRID_NEARPEAK3_MDD_BLOCK",
            "disposition": "Do NOT use Soft-core T+0 carve hybrid for this candidate",
        },
        "nav_challenger": str(dst_chal.relative_to(ROOT)),
        "nav_base": str(dst_base.relative_to(ROOT)),
        "label": f"{CANDIDATE_ID}_{day}__TIPSOFT_EXACT_T1__NO_HYBRID_T0",
    }
    (OUT / "candidate.json").write_text(
        json.dumps(candidate, indent=2) + "\n", encoding="utf-8"
    )
    (OPS / f"{CANDIDATE_ID}.json").write_text(
        json.dumps(candidate, indent=2) + "\n", encoding="utf-8"
    )
    write_repro_pointer(
        OPS / f"{CANDIDATE_ID}.json", REP / f"{CANDIDATE_ID}.json", kind="candidate"
    )

    candidate_md = "\n".join(
        [
            f"# {CANDIDATE_ID}",
            "",
            f"Date: {day} · Status: **`PAPER_OBSERVE_CANDIDATE_DRAFT`**",
            f"Register: **{REGISTER}** · Parents: {', '.join(PARENTS)}",
            f"Policy: **`{POLICY_ID}`** · clock **Exact T+1** · hybrid T+0 carve **FORBIDDEN**",
            "",
            "## Candidate rule",
            "",
            "- Base: tip Soft Exact T+1 Soft+FUSE+COOL (`BASE_LIVE_FUSE_COOL`)",
            "- Challenger: same shell + Path3 WITHIN premium only when",
            f"  `|trail_rel_63|≥{P3_THETA}` AND Soft within {int(NEAR_PEAK_PCT*100)}% of 63d peak",
            "- Soft KEEP · Path4 OFF · broker false · live wire false · cutover BLOCKED",
            "",
            "## Evidence",
            "",
            f"- 0kau Stage A **HIT**: held **{metrics.get('held_cagr_lift_pp')}** "
            f"tipY **{metrics.get('tip_ytd_cagr_lift_pp')}** "
            f"sealed MDD **{metrics.get('sealed_mdd_improve_pp')}**",
            "- 0kav Stage B hybrid T+0 NEARPEAK3 **MDD_BLOCK** → not this path",
            "",
            "## Ballot",
            "",
            f"- Draft: `{BALLOT_ID}.md` (awaiting human OPEN)",
            f"- Dual-paper prep: `{DUAL_ID}.md` (not OPERATING until OPEN)",
            f"- Cutover: `{CUTOVER_ID}.md` (**BLOCKED**)",
            "",
            f"Label: `{candidate['label']}`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{CANDIDATE_ID}.md",
        REP / f"{CANDIDATE_ID}.md",
        candidate_md,
        kind="candidate",
    )

    charter_md = "\n".join(
        [
            f"# {CHARTER_ID}",
            "",
            f"Date: {day}",
            "Status: **Paper/observe candidate — tip Soft Exact T+1 NEARPEAK3**",
            f"Register: **{REGISTER}** · Parents: {', '.join(PARENTS)}",
            "",
            "## Scope",
            "",
            f"- Policy `{POLICY_ID}` on tip Soft Exact T+1 live stack",
            "- Meta-detect selects Path3 block only near Soft peaks",
            "- Explicitly **excludes** Soft-core T+0 carve / hybrid twin promote path (0kav BLOCK)",
            "",
            "## Non-goals",
            "",
            "- Live wire / Soft-Frozen flip / Path4 / broker / cutover",
            "- Hybrid `TIP_SOFT_HYBRID_T1_OVERLAY_T0_CARVE` promote of this policy",
            "",
            f"Label: `{CHARTER_ID}_{day}__TIPSOFT_EXACT_T1`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{CHARTER_ID}.md", REP / f"{CHARTER_ID}.md", charter_md, kind="charter"
    )
    (OPS / f"{CHARTER_ID}.json").write_text(
        json.dumps(
            {
                "id": CHARTER_ID,
                "register": REGISTER,
                "parents": list(PARENTS),
                "policy_id": POLICY_ID,
                "clock": CLOCK,
                "hybrid_t0_carve": False,
                "soft_keep": True,
                "path4_live": False,
                "live_wire": False,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    write_repro_pointer(OPS / f"{CHARTER_ID}.json", REP / f"{CHARTER_ID}.json", kind="charter")

    open_line = (
        "OPEN paper observe: TIPSOFT_P3_THETA_NEARPEAK3 "
        "(tip Soft Exact T+1 · meta-detect Path3 near-peak3 · NOT hybrid T+0 carve)"
    )
    ballot = {
        "id": BALLOT_ID,
        "status": "DRAFT",
        "date": day,
        "register": REGISTER,
        "parents": list(PARENTS),
        "policy_id": POLICY_ID,
        "clock": CLOCK,
        "hybrid_t0_carve": False,
        "live_wire": False,
        "cutover_blocked": True,
        "soft_keep": True,
        "path4_live": False,
        "broker": False,
        "open_line": open_line,
        "label": f"{BALLOT_ID}_{day}__AWAITING_OPEN__NO_LIVE",
    }
    ballot_md = "\n".join(
        [
            f"# {BALLOT_ID}",
            "",
            f"Date: {day}",
            "Status: **DRAFT — awaiting human OPEN** · Soft KEEP · Path4 OFF · "
            "hybrid T+0 carve **FORBIDDEN** · live wire **false** · cutover **BLOCKED**",
            "",
            "## Proposed human line",
            "",
            "```",
            open_line,
            "```",
            "",
            "## Champion",
            "",
            f"- `{POLICY_ID}` — tip Soft Exact T+1 Soft+FUSE+COOL + Path3 WITHIN",
            f"  gated by `|trail|≥{P3_THETA}` AND Soft within 3% of 63d peak",
            f"- 0kau HIT: held **{metrics.get('held_cagr_lift_pp')}** · "
            f"tipY **{metrics.get('tip_ytd_cagr_lift_pp')}** · "
            f"sealed MDD **{metrics.get('sealed_mdd_improve_pp')}**",
            "- 0kav: Soft-core T+0 hybrid NEARPEAK3 **MDD_BLOCK** — do not open that path",
            "",
            "## Non-goals",
            "",
            "- Live wire / Soft-Frozen clip flip / Path4 / broker",
            "- Hybrid Soft-core T+0 carve promote (`TIP_SOFT_HYBRID_T1_OVERLAY_T0_CARVE`)",
            "- Always-on tip Soft Path3 (ungated L4)",
            "",
            "## Evidence",
            "",
            "- `META_DETECT_SEALED_MDD_HARDEN_STAGEA_DECISION_PACK.md` (0kau HIT)",
            "- `META_DETECT_HYBRID_NEARPEAK3_STAGEB_DECISION_PACK.md` (0kav hybrid BLOCK)",
            f"- Candidate: `{CANDIDATE_ID}.md`",
            f"- Repro NAV: `repro/tipsoft-p3-nearpeak3-paper-observe/outputs/nav_{POLICY_ID}.csv`",
            "",
            f"Label: `{ballot['label']}`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{BALLOT_ID}.md", REP / f"{BALLOT_ID}.md", ballot_md, kind="ballot draft"
    )
    (OPS / f"{BALLOT_ID}.json").write_text(
        json.dumps(ballot, indent=2) + "\n", encoding="utf-8"
    )
    write_repro_pointer(OPS / f"{BALLOT_ID}.json", REP / f"{BALLOT_ID}.json", kind="ballot draft")

    dual = {
        "id": DUAL_ID,
        "status": "PREP_NOT_OPERATING",
        "date": day,
        "register": REGISTER,
        "base_book": "BASE_LIVE_FUSE_COOL",
        "challenger_book": POLICY_ID,
        "clock": CLOCK,
        "live_wire": False,
        "operating": False,
        "awaiting": open_line,
        "label": f"{DUAL_ID}_{day}__PREP__NO_LIVE_WIRE",
    }
    dual_md = "\n".join(
        [
            f"# {DUAL_ID}",
            "",
            f"Date: {day}",
            "Status: **PREP — not OPERATING** (awaits human OPEN on draft ballot)",
            "",
            "| Book | ID | Role |",
            "|---|---|---|",
            "| Base | `BASE_LIVE_FUSE_COOL` | tip Soft Exact T+1 Soft+FUSE+COOL |",
            f"| Challenger | `{POLICY_ID}` | same shell + Path3 near-peak3 gate |",
            "",
            "## Gates",
            "",
            "- Exact T+1 only · no Soft-core T+0 carve premium",
            "- live_wire=false · cutover_authorized=false · Path4 OFF · broker false",
            "",
            "## Cadence (after OPEN)",
            "",
            "- Freeze NAVs already in `repro/tipsoft-p3-nearpeak3-paper-observe/outputs/`",
            "- Month-end monitor: wire only after EXECUTED OPEN (not this pack)",
            "",
            "## Non-actions",
            "",
            "- No live Soft clip flip · no hybrid T+0 carve · no tip history rewrite",
            "",
            f"Label: `{dual['label']}`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{DUAL_ID}.md", REP / f"{DUAL_ID}.md", dual_md, kind="dual-paper prep"
    )
    (OPS / f"{DUAL_ID}.json").write_text(json.dumps(dual, indent=2) + "\n", encoding="utf-8")
    write_repro_pointer(OPS / f"{DUAL_ID}.json", REP / f"{DUAL_ID}.json", kind="dual-paper prep")

    cutover_md = "\n".join(
        [
            f"# {CUTOVER_ID}",
            "",
            f"Date: {day}",
            "Status: **BLOCKED**",
            "",
            "## Why blocked",
            "",
            "- Paper/observe candidate only (DRAFT ballot, not OPEN)",
            "- No live wire authorization",
            "- Soft-Frozen / FUSE / COOL KEEP; Path4 OFF",
            "- Hybrid T+0 carve path explicitly rejected for this policy (0kav)",
            "",
            "## Required before any cutover PR",
            "",
            "1. Human OPEN paper observe on draft ballot",
            "2. Dual-paper OPERATING with tip/sealed gates green",
            "3. Separate ACCEPT live wire ballot (not this pack)",
            "",
            f"Label: `{CUTOVER_ID}_{day}__BLOCKED`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{CUTOVER_ID}.md",
        REP / f"{CUTOVER_ID}.md",
        cutover_md,
        kind="cutover checklist",
    )

    summary = {
        "register": REGISTER,
        "status": "PAPER_OBSERVE_CANDIDATE_DRAFT",
        "policy_id": POLICY_ID,
        "clock": CLOCK,
        "hybrid_t0_carve": False,
        "open_line": open_line,
        "metrics_0kau": metrics,
        "live_wire": False,
        "cutover_blocked": True,
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
