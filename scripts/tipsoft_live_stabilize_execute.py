#!/usr/bin/env python3
"""STABILIZE live tip Soft stack — human 請穩定 (0kbe).

Freeze LIVE composition; add DD_SWITCH month-end monitor; stop tip Soft
mechanism churn until soak. Soft FIN/TEL OFF · Path4 OFF · broker false ·
year-switch FORBIDDEN · no Soft-refill · no broker promote.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "research" / "ops"
DAY = "2026-10-02"
REGISTER = "0kbe"
BATCH_ID = "TIPSOFT_LIVE_STABILIZE_2026-10-02"
HUMAN = (
    "請穩定\n"
    "(LIVE tip Soft stack KEEP · DD_SWITCH tip apply KEEP · Path3 WITHIN KEEP ·\n"
    " Soft FIN/TEL stay OFF · Path4 OFF · broker false · no new tip Soft mech · soak)"
)


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")


def write_ballot() -> dict:
    payload = {
        "generated_at_utc": _utc(),
        "label": f"{BATCH_ID}__EXECUTED__LIVE_STACK_FREEZE",
        "status": "EXECUTED_STABILIZE",
        "register": REGISTER,
        "human": HUMAN,
        "live_keep": {
            "soft_frozen_clips_0050": True,
            "cool_fuse_sell_a75_conf_tel": True,
            "path3_within_sleeve": True,
            "t0_carve_fill_emit": True,
            "path3_ledger": True,
            "dd_switch_tip_apply": True,
            "dd_switch_policy": "TIPSOFT_P3_TRAIL42_L4_DD_SWITCH",
            "live_override_stamps": True,
            "soft_fin_tel_exact_t1": "OFF",
            "path4_live": False,
            "broker": False,
        },
        "ops_wiring": {
            "month_end_monitor": "scripts/tipsoft_ip3_trail42_l4_switch_month_end_monitor.py",
            "dual_paper_ledgers": "scripts/tipsoft_ip3_trail42_l4_switch_dual_paper_ledgers.py",
            "pack": "scripts/ops_month_end_paper_pack.py",
            "alert_scan": "scripts/ops_alert_scan.py",
        },
        "freeze_rules": [
            "No new tip Soft Exact T+1 mechanism Stage A / observe / tip apply until soak",
            "No year-switch / year-oracle arms",
            "No Soft FIN/TEL Exact T+1 refill",
            "No Path4 live",
            "No broker live write",
            "DD_SWITCH dual-paper observe KEEP as live twin monitor",
            "LIVE_OVERRIDE remains stamps/telemetry only",
        ],
        "reopen_if": [
            "DD_SWITCH month-end PAUSE_REVIEW / tip giveback breach after soak window",
            "Human ACCEPT for Soft FIN/TEL carve or Path4 / broker (separate ballots)",
            "New Stage A clears held/tipY/MDD floors without Soft-refill",
        ],
        "parents": ["0kbd", "0kac", "0kb2"],
    }
    md = "\n".join(
        [
            "# TIPSOFT LIVE STABILIZE — Ballot EXECUTED",
            "",
            f"Date: {DAY}",
            f"Status: **EXECUTED STABILIZE / LIVE STACK FREEZE** · register **{REGISTER}**",
            "",
            "## Human (exact)",
            "",
            "```",
            HUMAN,
            "```",
            "",
            "## LIVE KEEP (frozen)",
            "",
            "| Layer | State |",
            "|---|---|",
            "| Soft clips + Soft 0050 Exact T+1 | **KEEP** |",
            "| COOL / FUSE / SELL_a75 / CONF / TEL | **KEEP** |",
            "| Path3 `WITHIN_SLEEVE_PATH3` + ledger + T0 carve | **KEEP** |",
            "| DD_SWITCH tip apply `path3_gate_ft_cash_apply` | **KEEP** |",
            "| LIVE_OVERRIDE stamps | **KEEP** (stamps only) |",
            "| Soft FIN/TEL Exact T+1 | **OFF** |",
            "| Path4 / broker | **OFF / false** |",
            "",
            "## Ops harden",
            "",
            "- Add DD_SWITCH dual-paper **month-end monitor** + ledger refresh to month-end pack / alert scan",
            "- Mark tip Soft mechanism ladder **frozen** pending soak (no new Stage A churn)",
            "- Year-switch FORBIDDEN · Soft-refill FORBIDDEN",
            "",
            "## Freeze rules",
            "",
            *[f"- {r}" for r in payload["freeze_rules"]],
            "",
            "## Reopen only if",
            "",
            *[f"- {r}" for r in payload["reopen_if"]],
            "",
            f"Label: `{payload['label']}`",
            "",
        ]
    )
    _write(OPS / f"{BATCH_ID}.md", md)
    _write(OPS / f"{BATCH_ID}.json", json.dumps(payload, indent=2) + "\n")
    return payload


def patch_ops_status() -> None:
    path = OPS / "OPS_STATUS.md"
    text = path.read_text(encoding="utf-8")
    # Fix stale OPEN lines for closed tip Soft observes if still present.
    text = text.replace(
        "**tip Soft high-ON×CASH observe (2026-10-01):** **OBSERVE OPEN / OPERATING**",
        "**tip Soft high-ON×CASH observe (2026-10-01):** **OBSERVE CLOSED**",
    )
    text = text.replace(
        "**tip Soft TRAIL42×CASH observe (2026-10-01):** **OBSERVE OPEN / OPERATING**",
        "**tip Soft TRAIL42×CASH observe (2026-10-01):** **OBSERVE CLOSED**",
    )
    stab = (
        "**tip Soft LIVE STABILIZE (2026-10-02):** human `請穩定` · register **0kbe** · "
        "LIVE stack **FREEZE** (Soft殼+COOL/FUSE+Path3 WITHIN+T0+ledger+DD_SWITCH tip apply) · "
        "DD_SWITCH month-end monitor **WIRED** · Soft FIN/TEL OFF · Path4 OFF · broker false · "
        "no new tip Soft mech until soak · `TIPSOFT_LIVE_STABILIZE_2026-10-02.md`  \n"
    )
    anchor = "**TRAIL42⇄L4 DD-switch tip apply (2026-10-01):**"
    if stab.strip() not in text:
        if anchor in text:
            # insert after DD-switch tip apply line
            lines = text.splitlines(keepends=True)
            out = []
            for ln in lines:
                out.append(ln)
                if ln.startswith(anchor):
                    out.append(stab)
            text = "".join(out)
        else:
            text = stab + text
    path.write_text(text, encoding="utf-8")


def patch_register() -> None:
    path = OPS / "HUMAN_DECISION_REGISTER.md"
    text = path.read_text(encoding="utf-8")
    row = (
        "| 0kbe | tip Soft LIVE STABILIZE / freeze stack | "
        "**EXECUTED STABILIZE** (2026-10-02) | Human `請穩定` · LIVE Soft殼+Path3 WITHIN+"
        "DD_SWITCH tip apply **FREEZE** · DD_SWITCH month-end monitor WIRED · "
        "Soft FIN/TEL OFF · Path4 OFF · broker false · no new tip Soft mech until soak · "
        "`TIPSOFT_LIVE_STABILIZE_2026-10-02.md` |\n"
    )
    if "| 0kbe |" not in text:
        text = text.replace(
            "| 0kbd | TRAIL42×CASH ⇄ L4 DD-switch observe / tip apply |",
            row + "| 0kbd | TRAIL42×CASH ⇄ L4 DD-switch observe / tip apply |",
        )
    path.write_text(text, encoding="utf-8")


def patch_checklist() -> None:
    path = OPS / "CUTOVER_CHECKLIST_TIPSOFT_IP3_TRAIL42_L4_SWITCH.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "- [ ] Month-end monitor window",
        "- [x] Month-end monitor window (`TIPSOFT_IP3_TRAIL42_L4_SWITCH_MONTH_END_MONITOR` · stabilize 0kbe)",
    )
    if "STABILIZE" not in text:
        text = text.replace(
            "Soft FIN/TEL stay OFF · Path4 OFF · broker false · year-switch FORBIDDEN",
            "Soft FIN/TEL stay OFF · Path4 OFF · broker false · year-switch FORBIDDEN\n\n"
            "Stabilize: `TIPSOFT_LIVE_STABILIZE_2026-10-02` · live stack FREEZE pending soak",
        )
    path.write_text(text, encoding="utf-8")


def patch_portfolio_archive() -> None:
    path = OPS / "RESEARCH_PORTFOLIO_KEEP_ARCHIVE.md"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    note = (
        "**Live STABILIZE 2026-10-02:** tip Soft LIVE stack FREEZE · DD_SWITCH tip apply KEEP · "
        "month-end monitor WIRED · `TIPSOFT_LIVE_STABILIZE_2026-10-02.md`\n"
    )
    if "Live STABILIZE 2026-10-02" not in text:
        # append near top after title block if possible
        text = re.sub(
            r"(# Research Portfolio[^\n]*\n)",
            r"\1\n" + note,
            text,
            count=1,
        )
        if "Live STABILIZE 2026-10-02" not in text:
            text = note + "\n" + text
    path.write_text(text, encoding="utf-8")


def main() -> int:
    payload = write_ballot()
    patch_ops_status()
    patch_register()
    patch_checklist()
    patch_portfolio_archive()
    print(json.dumps({"ok": True, "label": payload["label"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
