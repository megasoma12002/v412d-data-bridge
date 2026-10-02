#!/usr/bin/env python3
"""EXECUTE OPEN tip Soft TRAIL42⇄L4 DD-switch paper observe (0kbd).

Human line (exact):
  OPEN paper observe: TIPSOFT_P3_TRAIL42_L4_DD_SWITCH
  (tip Soft Exact T+1 dual-book · daily TRAIL42 twin if TRAIL DD≥L4 DD else L4 ·
   Soft FIN/TEL stay OFF · NOT year-switch · NOT Path3-gate-only · NOT tip apply)

Effects:
  - Ballot DRAFT → EXECUTED OPEN
  - Dual-paper OPERATING (L4 ∥ TRAIL42_L4_DD_SWITCH)
  - Soft KEEP · Soft FIN/TEL stay OFF · Path4 OFF · tip apply BLOCKED
  - Sibling 0kba/0kbb observes KEEP · no live tip wire
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
REPRO = ROOT / "repro" / "tipsoft-ip3-trail42-l4-switch-paper-observe"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"
STAGEA = ROOT / "repro" / "tipsoft-ip3-trail42-l4-signal-switch-stagea" / "outputs"
ALIGN = ROOT / "repro" / "research-live-align-gap-stagea" / "outputs"

REGISTER = "0kbd"
POLICY_ID = "TIPSOFT_P3_TRAIL42_L4_DD_SWITCH"
BASE_ID = "L4_LIVE_P3_WITHIN"
CHAL_ID = "TRAIL42_L4_DD_SWITCH"
HUMAN_OPEN = (
    "OPEN paper observe: TIPSOFT_P3_TRAIL42_L4_DD_SWITCH\n"
    "(tip Soft Exact T+1 dual-book · daily TRAIL42 twin if TRAIL DD≥L4 DD else L4 ·\n"
    " Soft FIN/TEL stay OFF · NOT year-switch · NOT Path3-gate-only · NOT tip apply)"
)

BALLOT_DRAFT_ID = "TIPSOFT_IP3_TRAIL42_L4_SWITCH_OBSERVE_BALLOT_DRAFT"
BALLOT_EXEC_ID = "TIPSOFT_IP3_TRAIL42_L4_SWITCH_OBSERVE_BALLOT_EXECUTED_OPEN"
OPERATING_ID = "TIPSOFT_IP3_TRAIL42_L4_SWITCH_DUAL_PAPER_OBSERVE_OPERATING"
OPEN_ID = "TIPSOFT_IP3_TRAIL42_L4_SWITCH_DUAL_PAPER_OBSERVE_OPEN"
CUTOVER_ID = "CUTOVER_CHECKLIST_TIPSOFT_IP3_TRAIL42_L4_SWITCH"
CAND_ID = "TIPSOFT_IP3_TRAIL42_L4_SWITCH_PAPER_OBSERVE_CANDIDATE"


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


def _tip_aligned(base_nav: pd.DataFrame, chal_nav: pd.DataFrame) -> dict[str, Any]:
    asof = pd.Timestamp(pd.to_datetime(base_nav["date"]).max())
    out: dict[str, Any] = {}
    for wname, start in (
        ("ytd", pd.Timestamp(asof.year, 1, 1)),
        ("trailing_1y", asof - pd.Timedelta(days=365)),
    ):
        b = base_nav[
            (pd.to_datetime(base_nav["date"]) >= start)
            & (pd.to_datetime(base_nav["date"]) <= asof)
        ]
        c = chal_nav[
            (pd.to_datetime(chal_nav["date"]) >= start)
            & (pd.to_datetime(chal_nav["date"]) <= asof)
        ]
        common = sorted(set(pd.to_datetime(b["date"])) & set(pd.to_datetime(c["date"])))
        if len(common) < 20:
            out[wname] = {
                "cagr_lift_pp": None,
                "mdd_improve_pp": None,
                "gate": "INSUFFICIENT",
            }
            continue
        b = b[pd.to_datetime(b["date"]).isin(common)].sort_values("date")
        c = c[pd.to_datetime(c["date"]).isin(common)].sort_values("date")
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
    day = generated[:10]

    base_src = OUT / f"nav_{BASE_ID}.csv"
    if not base_src.is_file():
        base_src = STAGEA / "nav_REF_L4.csv"
    if not base_src.is_file():
        base_src = ALIGN / "nav_L4_LIVE_P3_WITHIN.csv"
    chal_src = OUT / f"nav_{CHAL_ID}.csv"
    if not chal_src.is_file():
        chal_src = STAGEA / "nav_TRAIL_WHEN_TR_DD_GTE_L4.csv"

    base = _load(base_src)
    chal = _load(chal_src)
    base.to_csv(OUT / f"nav_{BASE_ID}.csv", index=False)
    chal.to_csv(OUT / f"nav_{CHAL_ID}.csv", index=False)
    cmp = base.merge(chal, on="date", suffixes=("_base", "_chal"))
    cmp.to_csv(OUT / "dual_paper_nav_compare.csv", index=False)

    bw, cw = _pack(base), _pack(chal)
    tip = _tip_aligned(base, chal)
    held = {
        "cagr_lift_pp": round(
            float(cagr_lift_pp(bw["heldout_2019_plus"]["cagr"], cw["heldout_2019_plus"]["cagr"])),
            4,
        ),
        "mdd_improve_pp": round(
            float(
                mdd_delta_pp(
                    bw["heldout_2019_plus"]["max_drawdown"],
                    cw["heldout_2019_plus"]["max_drawdown"],
                )
            ),
            4,
        ),
    }
    sealed = {
        "cagr_lift_pp": round(
            float(cagr_lift_pp(bw["sealed_2023_plus"]["cagr"], cw["sealed_2023_plus"]["cagr"])),
            4,
        ),
        "mdd_improve_pp": round(
            float(
                mdd_delta_pp(
                    bw["sealed_2023_plus"]["max_drawdown"],
                    cw["sealed_2023_plus"]["max_drawdown"],
                )
            ),
            4,
        ),
    }

    non_actions = [
        "Soft-Frozen KEEP",
        "Soft FIN/TEL Exact T+1 stay OFF",
        "Path4 live OFF",
        "Calendar-year switch / year-oracle FORBIDDEN",
        "Path3-gate-only switch (without dual-book relative signal) FORBIDDEN",
        "hybrid Soft-core T+0 carve FORBIDDEN",
        "Research return-blend on tip order_rows FORBIDDEN",
        "Live tip apply / cutover BLOCKED until dedicated ACCEPT",
        "Sibling 0kba MUTE×CASH observe KEEP OPERATING",
        "Sibling 0kbb TRAIL42×CASH observe KEEP OPERATING",
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
        "broker": False,
        "base_id": BASE_ID,
        "challenger_id": CHAL_ID,
        "policy_id": POLICY_ID,
        "signal": "TRAIL_WHEN_TR_DD_GTE_L4",
        "gate": "daily TRAIL42 tip Soft twin if TRAIL_DD >= L4_DD else L4 (dual-book)",
        "pct_days_trail": 57.2917,
        "base_windows": bw,
        "chal_windows": cw,
        "heldout_delta": held,
        "sealed_delta": sealed,
        "tip": tip,
        "non_actions": non_actions,
        "parents": ["0kbd", "0kbb", "0kba", "0kac"],
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
            "- status: **OPERATING_OBSERVE** · live_wire: false · tip apply/cutover: **BLOCKED** · "
            "Soft KEEP · Soft FIN/TEL OFF · Path4 OFF",
            f"- books: `{BASE_ID}` ∥ `{CHAL_ID}` (Exact T+1 dual-book DD switch)",
            "- gate: TRAIL42 twin if TRAIL DD≥L4 DD else L4 · ~57% TRAIL days",
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
            HUMAN_OPEN,
            "```",
            "",
            f"- Books: `{BASE_ID}` ∥ `{CHAL_ID}`",
            f"- held **+{held['cagr_lift_pp']}** · tipY **+{(tip.get('ytd') or {}).get('cagr_lift_pp')}** · "
            f"sealed MDD **{sealed['mdd_improve_pp']}**",
            "- Soft FIN/TEL stay OFF · Path4 OFF · broker false · tip apply **BLOCKED**",
            "- Sibling 0kba/0kbb observes **KEEP OPERATING**",
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
            "Path4 OFF · broker false · tip apply/cutover **BLOCKED**",
            "",
            f"Register: **{REGISTER}** · Parent Stage A `SIGNAL_SWITCH_HIT` · supersedes `{BALLOT_DRAFT_ID}`",
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
            "| Observe ballot | DRAFT | **EXECUTED OPEN** |",
            f"| Dual-paper | candidate | **OPERATING** (`{BASE_ID}` ∥ `{CHAL_ID}`) |",
            "| Soft FIN/TEL Exact T+1 | OFF | **stay OFF** |",
            "| Path4 / broker | OFF / false | **OFF / false** |",
            "| Tip apply | — | **BLOCKED** (needs ACCEPT) |",
            "| 0kba / 0kbb | OPERATING | **KEEP OPERATING** |",
            "",
            "## Evidence",
            "",
            f"- held vs L4 **+{held['cagr_lift_pp']}** · tipY **+{(tip.get('ytd') or {}).get('cagr_lift_pp')}** · "
            f"sealed MDD **{sealed['mdd_improve_pp']}**",
            f"- Operating: `{OPERATING_ID}.md`",
            "- Stage A: `TIPSOFT_IP3_TRAIL42_L4_SIGNAL_SWITCH_STAGEA_DECISION_PACK.md`",
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

    draft_md = OPS / f"{BALLOT_DRAFT_ID}.md"
    if draft_md.is_file():
        text = draft_md.read_text(encoding="utf-8")
        text = text.replace(
            "Status: **DRAFT — awaiting human OPEN**",
            f"Status: **SUPERSEDED by `{BALLOT_EXEC_ID}`** (OPEN EXECUTED {day})",
        )
        draft_md.write_text(text, encoding="utf-8")
        write_repro_pointer(
            draft_md, REP / f"{BALLOT_DRAFT_ID}.md", kind="observe ballot draft"
        )

    cand = OPS / f"{CAND_ID}.json"
    if cand.is_file():
        c = json.loads(cand.read_text(encoding="utf-8"))
        c["status"] = "OBSERVE_OPEN_OPERATING"
        c["open_executed"] = BALLOT_EXEC_ID
        c["generated_at_utc"] = generated
        write_ops_and_repro_pointer(
            cand,
            REP / f"{CAND_ID}.json",
            json.dumps(c, indent=2) + "\n",
            kind="paper observe candidate",
        )
    cand_md = OPS / f"{CAND_ID}.md"
    if cand_md.is_file():
        ct = cand_md.read_text(encoding="utf-8")
        ct = ct.replace(
            "Status: **DRAFT candidate** · awaiting human OPEN",
            f"Status: **`OBSERVE_OPEN_OPERATING`** (human OPEN {day})",
        )
        write_ops_and_repro_pointer(
            cand_md, REP / f"{CAND_ID}.md", ct, kind="paper observe candidate"
        )

    cut_md = "\n".join(
        [
            f"# {CUTOVER_ID}",
            "",
            f"Date: {day} · Status: **BLOCKED** (observe OPEN only · dual-book paper)",
            "",
            "- [x] Stage A dual-book signal switch `SIGNAL_SWITCH_HIT`",
            "- [x] Human OPEN paper observe EXECUTED",
            "- [x] Dual-paper OPERATING",
            "- [ ] Month-end monitor window",
            "- [ ] ACCEPT tip apply ballot (separate — not stamps-only)",
            "- [ ] Live tip wire (forbidden until ACCEPT)",
            "",
            "Soft FIN/TEL stay OFF · Path4 OFF · broker false · year-switch FORBIDDEN",
            "",
            f"Label: `{CUTOVER_ID}_{day}__BLOCKED`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{CUTOVER_ID}.md", REP / f"{CUTOVER_ID}.md", cut_md, kind="cutover checklist"
    )

    # Register 0kbd
    reg = OPS / "HUMAN_DECISION_REGISTER.md"
    rt = reg.read_text(encoding="utf-8")
    old = None
    for line in rt.splitlines():
        if line.startswith("| 0kbd |"):
            old = line
            break
    new = (
        f"| 0kbd | TRAIL42×CASH ⇄ L4 DD-switch observe | **OBSERVE OPEN / OPERATING** ({day}) | "
        f"Parents 0kbb/0kba/0kbc/0kac · human OPEN `{POLICY_ID}` · `{BASE_ID}`∥`{CHAL_ID}` "
        f"held **+{held['cagr_lift_pp']}** tipY **+{(tip.get('ytd') or {}).get('cagr_lift_pp')}** "
        f"sealedMDD **{sealed['mdd_improve_pp']}** · Soft FIN/TEL OFF · Path4 OFF · tip apply **BLOCKED** · "
        f"0kba/0kbb KEEP · `{BALLOT_EXEC_ID}.md` |"
    )
    if old:
        reg.write_text(rt.replace(old, new), encoding="utf-8")

    ops = OPS / "OPS_STATUS.md"
    ot = ops.read_text(encoding="utf-8")
    open_line = (
        f"**TRAIL42⇄L4 DD-switch observe (2026-10-01):** **OBSERVE OPEN / OPERATING** · "
        f"human OPEN `{POLICY_ID}` · held **+{held['cagr_lift_pp']}** tipY "
        f"**+{(tip.get('ytd') or {}).get('cagr_lift_pp')}** sealedMDD **{sealed['mdd_improve_pp']}** · "
        f"Soft FIN/TEL OFF · Path4 OFF · tip apply BLOCKED · `{BALLOT_EXEC_ID}.md`  \n"
    )
    draft_needle = (
        "**TRAIL42⇄L4 DD-switch observe (2026-10-01):** **DRAFT** dual-paper · "
        "policy `TIPSOFT_P3_TRAIL42_L4_DD_SWITCH` · held **+3.5275** tipY **+27.5471** "
        "sealedMDD **0.4692** · awaiting OPEN · Soft FIN/TEL OFF · Path4 OFF · "
        "`TIPSOFT_IP3_TRAIL42_L4_SWITCH_OBSERVE_BALLOT_DRAFT.md`  \n"
    )
    if draft_needle in ot:
        ops.write_text(ot.replace(draft_needle, open_line), encoding="utf-8")
        ot = ops.read_text(encoding="utf-8")
    elif "OBSERVE OPEN / OPERATING** · human OPEN `TIPSOFT_P3_TRAIL42_L4_DD_SWITCH`" not in ot:
        idx = ot.find("TIPSOFT_IP3_TRAIL42_L4_SWITCH_OBSERVE_BALLOT_DRAFT.md")
        if idx > 0:
            end = ot.find("\n", idx) + 1
            ops.write_text(ot[:end] + open_line + ot[end:], encoding="utf-8")
            ot = ops.read_text(encoding="utf-8")

    table_row = (
        f"| tip Soft Exact T+1 `{POLICY_ID}` | **OBSERVE OPEN** ({day}) | "
        f"dual-book TRAIL DD≥L4 DD else L4 · Soft FIN/TEL stay OFF · tip apply/cutover **BLOCKED** · "
        f"`{BALLOT_EXEC_ID}.md` |"
    )
    ot = ops.read_text(encoding="utf-8")
    if f"`{POLICY_ID}` |" not in ot:
        for anchor in (
            "| tip Soft Exact T+1 `TIPSOFT_P3_TRAIL42_FT_CASH` | **OBSERVE OPEN** (2026-10-01) |",
            "| tip Soft Exact T+1 `TIPSOFT_P3_ON_UNLESS_MUTE_FT_CASH` | **OBSERVE OPEN** (2026-10-01) |",
        ):
            if anchor in ot:
                # insert after full matching line
                for line in ot.splitlines():
                    if line.startswith(anchor):
                        ot = ot.replace(line, line + "\n" + table_row)
                        ops.write_text(ot, encoding="utf-8")
                        break
                break

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
