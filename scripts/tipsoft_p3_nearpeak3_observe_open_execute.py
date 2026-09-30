#!/usr/bin/env python3
"""EXECUTE OPEN tip Soft Exact T+1 P3_THETA_NEARPEAK3 paper observe (0kaw).

Human line (exact):
  OPEN paper observe: TIPSOFT_P3_THETA_NEARPEAK3
  (tip Soft Exact T+1 · meta-detect Path3 near-peak3 · NOT hybrid T+0 carve)

Effects:
  - Ballot DRAFT → EXECUTED OPEN
  - Dual-paper PREP → OPERATING (frozen Exact T+1 NAVs)
  - Soft KEEP · Path4 OFF · hybrid T+0 carve FORBIDDEN
  - live_wire false · cutover BLOCKED · no Soft-Frozen flip
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from e45_paper_harness import WINDOWS_STANDARD, window_stats
from fin_sell_quality_helpers import cagr_lift_pp
from ops_repro_ssot import write_ops_and_repro_pointer, write_repro_pointer
from research_metric_helpers import mdd_delta_pp

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "tipsoft-p3-nearpeak3-paper-observe"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"
ME_DIR = REPRO / "month_end"

REGISTER = "0kaw"
POLICY_ID = "P3_THETA_NEARPEAK3"
BASE_ID = "BASE_LIVE_FUSE_COOL"
HUMAN_OPEN = (
    "OPEN paper observe: TIPSOFT_P3_THETA_NEARPEAK3 "
    "(tip Soft Exact T+1 · meta-detect Path3 near-peak3 · NOT hybrid T+0 carve)"
)

BALLOT_DRAFT_ID = "TIPSOFT_P3_NEARPEAK3_OBSERVE_BALLOT_DRAFT"
BALLOT_EXEC_ID = "TIPSOFT_P3_NEARPEAK3_OBSERVE_BALLOT_EXECUTED_OPEN"
OPERATING_ID = "TIPSOFT_P3_NEARPEAK3_DUAL_PAPER_OBSERVE_OPERATING"
OPEN_ID = "TIPSOFT_P3_NEARPEAK3_DUAL_PAPER_OBSERVE_OPEN"
CANDIDATE_ID = "TIPSOFT_P3_NEARPEAK3_PAPER_OBSERVE_CANDIDATE"
CUTOVER_ID = "CUTOVER_CHECKLIST_TIPSOFT_P3_NEARPEAK3"
HELPERS_NOTE = "Exact T+1 frozen NAV dual-paper; hybrid T+0 carve forbidden"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_nav(path: Path) -> pd.DataFrame:
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


def _delta_win(base_w: dict, chal_w: dict, key: str) -> dict[str, Any]:
    b, c = base_w.get(key) or {}, chal_w.get(key) or {}
    return {
        "cagr_lift_pp": None
        if cagr_lift_pp(b.get("cagr"), c.get("cagr")) is None
        else round(float(cagr_lift_pp(b.get("cagr"), c.get("cagr"))), 4),
        "mdd_improve_pp": None
        if b.get("max_drawdown") is None or c.get("max_drawdown") is None
        else round(float(mdd_delta_pp(b["max_drawdown"], c["max_drawdown"])), 4),
    }


def main() -> int:
    for d in (OUT, REP, OPS, ME_DIR):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()
    day = generated[:10]

    base = _load_nav(OUT / f"nav_{BASE_ID}.csv")
    chal = _load_nav(OUT / f"nav_{POLICY_ID}.csv")
    # Canonical daily names for monitor
    base.to_csv(OUT / "base_live_fuse_cool_daily_nav.csv", index=False)
    chal.to_csv(OUT / "p3_theta_nearpeak3_daily_nav.csv", index=False)
    cmp = base.merge(chal, on="date", suffixes=("_base", "_chal"))
    cmp["nav_lift"] = cmp["nav_chal"] / cmp["nav_base"] - 1.0
    cmp.to_csv(OUT / "dual_paper_nav_compare.csv", index=False)

    bw, cw = _pack(base), _pack(chal)
    tip = _tip(base, chal)
    held = _delta_win(bw, cw, "heldout_2019_plus")
    sealed = _delta_win(bw, cw, "sealed_2023_plus")
    full = _delta_win(bw, cw, "full")

    non_actions = [
        "Soft-Frozen KEEP",
        "Path4 live OFF",
        "hybrid Soft-core T+0 carve FORBIDDEN for this observe",
        "Do not live-wire Path3 near-peak gate from this ballot",
        "Cutover BLOCKED until dedicated ACCEPT",
    ]

    # --- Ballot EXECUTED OPEN ---
    ballot = {
        "id": BALLOT_EXEC_ID,
        "status": "EXECUTED_OPEN",
        "date": day,
        "generated_at_utc": generated,
        "register": REGISTER,
        "human_open": HUMAN_OPEN,
        "policy_id": POLICY_ID,
        "clock": "exact_t1",
        "hybrid_t0_carve": False,
        "live_wire": False,
        "cutover_blocked": True,
        "soft_keep": True,
        "path4_live": False,
        "broker": False,
        "draft_superseded": BALLOT_DRAFT_ID,
        "heldout_delta": held,
        "sealed_delta": sealed,
        "tip": tip,
        "label": f"{BALLOT_EXEC_ID}_{day}__OPEN__NO_LIVE",
    }
    ballot_md = "\n".join(
        [
            "# TIPSOFT_P3_NEARPEAK3 — Ballot EXECUTED (OPEN observe)",
            "",
            f"Date: {day}",
            "Status: **EXECUTED** · Soft KEEP · Path4 OFF · hybrid T+0 carve **FORBIDDEN** · "
            "live wire **false** · cutover **BLOCKED**",
            "Human (exact):",
            "",
            "```",
            HUMAN_OPEN,
            "```",
            "",
            "## Evidence",
            "",
            f"- 0kau Stage A **HIT** · policy `{POLICY_ID}` tip Soft Exact T+1",
            f"- held CAGR↑ **{held.get('cagr_lift_pp')}** · sealed MDD↑ **{sealed.get('mdd_improve_pp')}**",
            f"- tip YTD CAGR↑ **{(tip.get('ytd') or {}).get('cagr_lift_pp')}** · "
            f"1y **{(tip.get('trailing_1y') or {}).get('cagr_lift_pp')}**",
            "- 0kav hybrid T+0 NEARPEAK3 **MDD_BLOCK** — not opened",
            f"- Draft superseded: `{BALLOT_DRAFT_ID}.md`",
            "",
            "## Effect",
            "",
            f"- Dual-paper **OPERATING**: `{BASE_ID}` ∥ `{POLICY_ID}` (Exact T+1)",
            "- Month-end monitor wired (frozen NAV)",
            "- Cutover **BLOCKED** — do **not** live-wire near-peak Path3 from this ballot",
            "",
            "## Artifacts",
            "",
            f"- Operating: `{OPERATING_ID}.md`",
            "- Ledgers: `scripts/tipsoft_p3_nearpeak3_dual_paper_ledgers.py`",
            "- Monitor: `scripts/tipsoft_p3_nearpeak3_month_end_monitor.py`",
            "- Repro: `repro/tipsoft-p3-nearpeak3-paper-observe/`",
            f"- Cutover: `{CUTOVER_ID}.md` (**BLOCKED**)",
            "",
            f"Label: `{ballot['label']}`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{BALLOT_EXEC_ID}.md",
        REP / f"{BALLOT_EXEC_ID}.md",
        ballot_md,
        kind="ballot executed open",
    )
    (OPS / f"{BALLOT_EXEC_ID}.json").write_text(
        json.dumps(ballot, indent=2) + "\n", encoding="utf-8"
    )
    write_repro_pointer(
        OPS / f"{BALLOT_EXEC_ID}.json",
        REP / f"{BALLOT_EXEC_ID}.json",
        kind="ballot executed open",
    )

    # Mark draft superseded (append note; keep file)
    draft_path = OPS / f"{BALLOT_DRAFT_ID}.md"
    if draft_path.exists():
        body = draft_path.read_text(encoding="utf-8")
        if "SUPERSEDED" not in body[:400]:
            draft_path.write_text(
                body.replace(
                    "Status: **DRAFT — awaiting human OPEN**",
                    f"Status note: **SUPERSEDED {day}** by `{BALLOT_EXEC_ID}.md`\n"
                    "Status (historical): **DRAFT — awaiting human OPEN**",
                    1,
                ),
                encoding="utf-8",
            )
    draft_json = OPS / f"{BALLOT_DRAFT_ID}.json"
    if draft_json.exists():
        dj = json.loads(draft_json.read_text(encoding="utf-8"))
        dj["status"] = "SUPERSEDED"
        dj["superseded_by"] = BALLOT_EXEC_ID
        draft_json.write_text(json.dumps(dj, indent=2) + "\n", encoding="utf-8")

    # --- Dual-paper OPEN + OPERATING ---
    operating = {
        "generated_at_utc": generated,
        "schema_version": "tipsoft_p3_nearpeak3_dual_paper_observe_v1",
        "label": OPERATING_ID,
        "status": "OPERATING_OBSERVE",
        "human_open": HUMAN_OPEN,
        "register": REGISTER,
        "live_wire": False,
        "cutover_authorized": False,
        "soft_frozen_keep": True,
        "path4_live": False,
        "hybrid_t0_carve": False,
        "broker": False,
        "base_id": BASE_ID,
        "challenger_id": POLICY_ID,
        "clock": "exact_t1",
        "stage_a_verdict": "SEALED_MDD_HARDEN_HIT",
        "base_windows": bw,
        "chal_windows": cw,
        "heldout_delta": held,
        "sealed_delta": sealed,
        "full_delta": full,
        "tip": tip,
        "helpers_note": HELPERS_NOTE,
        "non_actions": non_actions,
    }
    (OPS / f"{OPERATING_ID}.json").write_text(
        json.dumps(operating, indent=2) + "\n", encoding="utf-8"
    )
    write_repro_pointer(
        OPS / f"{OPERATING_ID}.json", REP / f"{OPERATING_ID}.json", kind="dual-paper operating"
    )
    (OUT / "dual_paper_operating.json").write_text(
        json.dumps(operating, indent=2) + "\n", encoding="utf-8"
    )

    operating_md = "\n".join(
        [
            f"# {OPERATING_ID.replace('TIPSOFT_P3_NEARPEAK3_DUAL_PAPER_OBSERVE_OPERATING', 'TIPSOFT_P3_NEARPEAK3 dual-paper observe — OPERATING')}",
            "",
            f"- human_open: `{HUMAN_OPEN}`",
            "- status: **OPERATING_OBSERVE** · live_wire: false · cutover: **BLOCKED** · "
            "Soft KEEP · Path4 OFF · hybrid T+0 carve FORBIDDEN",
            f"- books: `{BASE_ID}` ∥ `{POLICY_ID}` (Exact T+1)",
            "- Stage A: `SEALED_MDD_HARDEN_HIT` (0kau) · Stage B hybrid BLOCK (0kav) not in scope",
            f"- held-out: CAGR↑ {held.get('cagr_lift_pp')} pp · MDD↑ {held.get('mdd_improve_pp')} pp",
            f"- sealed: CAGR↑ {sealed.get('cagr_lift_pp')} · MDD↑ {sealed.get('mdd_improve_pp')}",
            f"- tip ytd CAGR↑ {(tip.get('ytd') or {}).get('cagr_lift_pp')} · "
            f"tip 1y CAGR↑ {(tip.get('trailing_1y') or {}).get('cagr_lift_pp')}",
            "",
            "## Non-actions",
            "",
            *[f"- {x}" for x in non_actions],
            "",
            "Repro: `repro/tipsoft-p3-nearpeak3-paper-observe/`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{OPERATING_ID}.md",
        REP / f"{OPERATING_ID}.md",
        operating_md,
        kind="dual-paper operating",
    )

    open_md = "\n".join(
        [
            "# tip Soft Exact T+1 NEARPEAK3 Dual-Paper Observe — OPEN",
            "",
            f"Date: {day}",
            "Status: **OPEN → OPERATING**",
            f"Human: `{HUMAN_OPEN}`",
            "",
            "| Book | ID | Role |",
            "|---|---|---|",
            f"| Base | `{BASE_ID}` | tip Soft Exact T+1 Soft+FUSE+COOL |",
            f"| Challenger | `{POLICY_ID}` | same shell + Path3 near-peak3 gate |",
            "",
            "## Gates",
            "",
            "- Exact T+1 only · hybrid Soft-core T+0 carve **FORBIDDEN**",
            "- live_wire=false · cutover_authorized=false · Path4 OFF · broker false",
            "",
            "## Cadence",
            "",
            "- Ledgers: `scripts/tipsoft_p3_nearpeak3_dual_paper_ledgers.py`",
            "- Month-end: `scripts/tipsoft_p3_nearpeak3_month_end_monitor.py`",
            "",
            "## Non-actions",
            "",
            *[f"- {x}" for x in non_actions],
            "",
            f"Label: `{OPEN_ID}_{day}__OPERATING__NO_LIVE_WIRE`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{OPEN_ID}.md", REP / f"{OPEN_ID}.md", open_md, kind="dual-paper open"
    )
    (OPS / f"{OPEN_ID}.json").write_text(
        json.dumps(
            {
                "id": OPEN_ID,
                "status": "OPEN_OPERATING",
                "date": day,
                "human_open": HUMAN_OPEN,
                "live_wire": False,
                "cutover_authorized": False,
                "base_id": BASE_ID,
                "challenger_id": POLICY_ID,
                "label": f"{OPEN_ID}_{day}__OPERATING__NO_LIVE_WIRE",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    write_repro_pointer(OPS / f"{OPEN_ID}.json", REP / f"{OPEN_ID}.json", kind="dual-paper open")

    # Update candidate status
    cand_path = OPS / f"{CANDIDATE_ID}.json"
    if cand_path.exists():
        cand = json.loads(cand_path.read_text(encoding="utf-8"))
        cand["status"] = "OBSERVE_OPEN_OPERATING"
        cand["human_open"] = HUMAN_OPEN
        cand["opened_at_utc"] = generated
        cand_path.write_text(json.dumps(cand, indent=2) + "\n", encoding="utf-8")
        write_repro_pointer(cand_path, REP / f"{CANDIDATE_ID}.json", kind="candidate")
    cand_md = OPS / f"{CANDIDATE_ID}.md"
    if cand_md.exists():
        write_ops_and_repro_pointer(
            cand_md,
            REP / f"{CANDIDATE_ID}.md",
            cand_md.read_text(encoding="utf-8").replace(
                "Status: **`PAPER_OBSERVE_CANDIDATE_DRAFT`**",
                f"Status: **`OBSERVE_OPEN_OPERATING`** (human OPEN {day})",
                1,
            ),
            kind="candidate",
        )

    # Cutover remains BLOCKED but note OPEN happened
    cutover_md = "\n".join(
        [
            f"# {CUTOVER_ID}",
            "",
            f"Date: {day}",
            "Status: **BLOCKED** (observe OPEN does not authorize cutover)",
            "",
            "## Why blocked",
            "",
            "- Paper observe OPERATING only — no live wire ACCEPT",
            "- Soft-Frozen / FUSE / COOL KEEP; Path4 OFF",
            "- Hybrid T+0 carve path remains rejected (0kav)",
            "",
            "## Opened",
            "",
            f"- Human: `{HUMAN_OPEN}`",
            f"- Operating: `{OPERATING_ID}.md`",
            "",
            "## Required before any cutover PR",
            "",
            "1. Dual-paper OPERATING tip/sealed gates remain green forward",
            "2. Separate ACCEPT live wire ballot (not this OPEN)",
            "3. Soft KEEP unchanged unless dedicated Soft ballot",
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

    # Mark PREP superseded
    prep = OPS / "TIPSOFT_P3_NEARPEAK3_DUAL_PAPER_OBSERVE_PREP.md"
    if prep.exists():
        body = prep.read_text(encoding="utf-8")
        if "SUPERSEDED" not in body[:300]:
            prep.write_text(
                body.replace(
                    "Status: **PREP — not OPERATING**",
                    f"Status note: **SUPERSEDED {day}** by `{OPERATING_ID}.md`\n"
                    "Status (historical): **PREP — not OPERATING**",
                    1,
                ),
                encoding="utf-8",
            )

    summary = {
        "register": REGISTER,
        "status": "OBSERVE_OPEN_OPERATING",
        "human_open": HUMAN_OPEN,
        "policy_id": POLICY_ID,
        "held_cagr_lift_pp": held.get("cagr_lift_pp"),
        "sealed_mdd_improve_pp": sealed.get("mdd_improve_pp"),
        "tip_ytd_cagr_lift_pp": (tip.get("ytd") or {}).get("cagr_lift_pp"),
        "live_wire": False,
        "cutover_blocked": True,
        "hybrid_t0_carve": False,
    }
    (OUT / "open_execute_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
