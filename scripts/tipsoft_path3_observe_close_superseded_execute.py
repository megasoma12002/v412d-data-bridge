#!/usr/bin/env python3
"""CLOSE superseded paper observes — tip Soft old stack + Path3 paper shadows.

Human (exact):

```
CLOSE paper observe: TIPSOFT_P3_THETA_NEARPEAK3 + TIPSOFT_P3_ON_UNLESS_MUTE_FT_CASH + TIPSOFT_P3_TRAIL42_FT_CASH
(superseded by TIPSOFT_P3_TRAIL42_L4_DD_SWITCH tip apply LIVE · Soft FIN/TEL stay OFF · Path3 WITHIN KEEP)

CLOSE paper observe: COMP_H150_x_A20 + SAT_A20_RELAX + P3_T0_STATE
(Path3 WITHIN + T0 carve + ledger already LIVE · Soft KEEP · DD_SWITCH tip apply KEEP)
```

CLOSE ≠ delete evidence/scripts · only remove from operating month-end/alert queue.
Live KEEP: Path3 WITHIN · T0 carve · ledger · DD_SWITCH tip apply · Soft clips+0050.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "research" / "ops"
DAY = "2026-10-01"

HUMAN_TIPSOFT = (
    "CLOSE paper observe: TIPSOFT_P3_THETA_NEARPEAK3 + TIPSOFT_P3_ON_UNLESS_MUTE_FT_CASH + "
    "TIPSOFT_P3_TRAIL42_FT_CASH\n"
    "(superseded by TIPSOFT_P3_TRAIL42_L4_DD_SWITCH tip apply LIVE · Soft FIN/TEL stay OFF · "
    "Path3 WITHIN KEEP)"
)
HUMAN_PATH3 = (
    "CLOSE paper observe: COMP_H150_x_A20 + SAT_A20_RELAX + P3_T0_STATE\n"
    "(Path3 WITHIN + T0 carve + ledger already LIVE · Soft KEEP · DD_SWITCH tip apply KEEP)"
)

BATCH_ID = "OBSERVE_CLOSE_SUPERSEDED_2026-10-01"
BATCH_LABEL = f"{BATCH_ID}__TIPSOFT_OLDSTACK__PATH3_SHADOW"


TIPSOFT_CLOSES = [
    {
        "reg": "0kaw",
        "policy": "TIPSOFT_P3_THETA_NEARPEAK3",
        "why": "superseded by DD_SWITCH tip apply LIVE (via OVERRIDE→MUTE/TRAIL chain)",
        "operating": "TIPSOFT_P3_NEARPEAK3_DUAL_PAPER_OBSERVE_OPERATING",
        "ballot_open": "TIPSOFT_P3_NEARPEAK3_OBSERVE_BALLOT_EXECUTED_OPEN",
        "cutover": "CUTOVER_CHECKLIST_TIPSOFT_P3_NEARPEAK3",
    },
    {
        "reg": "0kba",
        "policy": "TIPSOFT_P3_ON_UNLESS_MUTE_FT_CASH",
        "why": "superseded by DD_SWITCH tip apply LIVE (KEEPBOTH already NO)",
        "operating": "TIPSOFT_IP3_HIGHON_CASH_DUAL_PAPER_OBSERVE_OPERATING",
        "ballot_open": "TIPSOFT_IP3_HIGHON_CASH_OBSERVE_BALLOT_EXECUTED_OPEN",
        "cutover": "CUTOVER_CHECKLIST_TIPSOFT_IP3_HIGHON_CASH",
    },
    {
        "reg": "0kbb",
        "policy": "TIPSOFT_P3_TRAIL42_FT_CASH",
        "why": "twin leg absorbed into DD_SWITCH tip apply LIVE",
        "operating": "TIPSOFT_IP3_TRAIL42_CASH_DUAL_PAPER_OBSERVE_OPERATING",
        "ballot_open": "TIPSOFT_IP3_TRAIL42_CASH_OBSERVE_BALLOT_EXECUTED_OPEN",
        "cutover": "CUTOVER_CHECKLIST_TIPSOFT_IP3_TRAIL42_CASH",
    },
]

PATH3_CLOSES = [
    {
        "reg": "0k9b",
        "policy": "COMP_H150_x_A20",
        "why": "Path3 WITHIN + ledger already LIVE (paper COMPOSITE shadow)",
        "operating": "FIN_SAT_COMPOSITE_DUAL_PAPER_OBSERVE_OPERATING",
        "ballot_open": "FIN_SAT_COMPOSITE_OBSERVE_BALLOT_EXECUTED_OPEN",
        "cutover": None,
    },
    {
        "reg": "0k9d",
        "policy": "SAT_A20_RELAX",
        "why": "Path3 WITHIN + ledger already LIVE (paper SAT shadow)",
        "operating": "SAT_A20_RELAX_DUAL_PAPER_OBSERVE_OPERATING",
        "ballot_open": "SAT_A20_RELAX_OBSERVE_BALLOT_EXECUTED_OPEN",
        "cutover": None,
    },
    {
        "reg": "0k9r",
        "policy": "P3_T0_STATE",
        "why": "T0 carve + Path3 cutover already LIVE (paper observe shadow)",
        "operating": "FIN_SAT_PATH3_T0_DUAL_PAPER_OBSERVE_OPERATING",
        "ballot_open": "FIN_SAT_PATH3_T0_STATE_OBSERVE_BALLOT_EXECUTED_OPEN",
        "cutover": None,
    },
]


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _close_operating_json(stem: str, *, policy: str, why: str) -> None:
    path = OPS / f"{stem}.json"
    if not path.is_file():
        raise FileNotFoundError(path)
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["status"] = "OBSERVE_CLOSED"
    doc["closed_at"] = DAY
    doc["close_batch"] = BATCH_ID
    doc["close_why"] = why
    doc["month_end_queue"] = "SKIP"
    doc["alert_scan"] = "SKIP"
    doc["reopen"] = "new human OPEN ballot required"
    doc["live_wire"] = bool(doc.get("live_wire", False))  # unchanged; close is paper-only
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")


def _close_operating_md(stem: str, *, policy: str, why: str) -> None:
    path = OPS / f"{stem}.md"
    if not path.is_file():
        raise FileNotFoundError(path)
    text = path.read_text(encoding="utf-8")
    # Flip OPERATING status line
    text2 = re.sub(
        r"status:\s*\*\*OPERATING_OBSERVE\*\*",
        "status: **OBSERVE_CLOSED**",
        text,
        count=1,
    )
    if "OBSERVE_CLOSED" not in text2:
        # insert after title
        lines = text2.splitlines()
        insert_at = 1 if lines else 0
        lines.insert(
            insert_at,
            f"\nStatus: **OBSERVE_CLOSED** ({DAY}) · `{policy}` · {why} · batch `{BATCH_ID}`\n",
        )
        text2 = "\n".join(lines) + ("\n" if not text2.endswith("\n") else "")
    banner = (
        f"\n## CLOSED ({DAY})\n\n"
        f"- Policy `{policy}` removed from month-end / alert queue\n"
        f"- Why: {why}\n"
        f"- Batch: `{BATCH_ID}`\n"
        f"- Evidence/scripts **KEEP** · reopen needs new human OPEN ballot\n"
        f"- Live Path3 WITHIN / T0 carve / ledger / DD_SWITCH tip apply **KEEP**\n"
    )
    if f"## CLOSED ({DAY})" not in text2:
        text2 = text2.rstrip() + "\n" + banner + "\n"
    path.write_text(text2, encoding="utf-8")


def _banner_open_ballot(stem: str, *, policy: str, why: str) -> None:
    md = OPS / f"{stem}.md"
    js = OPS / f"{stem}.json"
    if md.is_file():
        text = md.read_text(encoding="utf-8")
        note = (
            f"\n> **SUPERSEDED / OBSERVE CLOSED ({DAY})** — `{policy}` · {why} · "
            f"`{BATCH_ID}.md`\n"
        )
        if "OBSERVE CLOSED" not in text[:400]:
            # after first heading line
            parts = text.split("\n", 1)
            if len(parts) == 2:
                text = parts[0] + "\n" + note + parts[1]
            else:
                text = text + note
            # also flip Status OPEN → CLOSED if present
            text = re.sub(
                r"(Status:\s*\*\*)EXECUTED[^*]*OPEN[^*]*(\*\*)",
                r"\1OBSERVE CLOSED\2",
                text,
                count=1,
            )
            text = re.sub(
                r"\*\*OBSERVE OPEN[^*]*\*\*",
                "**OBSERVE CLOSED**",
                text,
                count=1,
            )
            md.write_text(text, encoding="utf-8")
    if js.is_file():
        raw = js.read_text(encoding="utf-8").lstrip()
        if raw.startswith("{"):
            doc = json.loads(raw)
            doc["status"] = "OBSERVE_CLOSED"
            doc["closed_at"] = DAY
            doc["close_batch"] = BATCH_ID
            doc["close_why"] = why
            js.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")


def _close_cutover(stem: str | None, *, policy: str) -> None:
    if not stem:
        return
    path = OPS / f"{stem}.md"
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    text = re.sub(
        r"Status:\s*\*\*[^*]+\*\*",
        f"Status: **OBSERVE CLOSED** ({DAY}) · paper queue off · `{policy}`",
        text,
        count=1,
    )
    if "OBSERVE CLOSED" not in text:
        text = (
            f"# {stem}\n\nStatus: **OBSERVE CLOSED** ({DAY}) · `{policy}` · batch `{BATCH_ID}`\n"
        )
    path.write_text(text, encoding="utf-8")


def _write_batch() -> None:
    rows_t = "\n".join(
        f"| `{c['reg']}` | `{c['policy']}` | {c['why']} |" for c in TIPSOFT_CLOSES
    )
    rows_p = "\n".join(
        f"| `{c['reg']}` | `{c['policy']}` | {c['why']} |" for c in PATH3_CLOSES
    )
    md = "\n".join(
        [
            f"# {BATCH_ID}",
            "",
            f"Date: {DAY}",
            "Status: **EXECUTED** · Soft KEEP · Path3 WITHIN KEEP · T0 carve KEEP · "
            "ledger KEEP · DD_SWITCH tip apply KEEP · broker false · no live undo",
            "",
            "## Human (exact)",
            "",
            "```",
            HUMAN_TIPSOFT,
            "",
            HUMAN_PATH3,
            "```",
            "",
            "## DOWN — tip Soft old stack",
            "",
            "| Reg | Policy | Why |",
            "|---|---|---|",
            rows_t,
            "",
            "## DOWN — Path3 paper shadows",
            "",
            "| Reg | Policy | Why |",
            "|---|---|---|",
            rows_p,
            "",
            "## KEEP (unchanged)",
            "",
            "- Live: Path3 `WITHIN_SLEEVE_PATH3` · T0 carve fill/emit · ledger · "
            "**DD_SWITCH tip apply** · Soft clips+0050 · COOL/FUSE/SELL_a75/CONF/TEL",
            "- Observe KEEP: `TIPSOFT_P3_TRAIL42_L4_DD_SWITCH` dual-paper (live twin monitor)",
            "- LIVE_OVERRIDE stamps (0kb2) unchanged this ballot",
            "",
            "## Binding",
            "",
            "1. CLOSE ≠ delete evidence/scripts; month-end + alert queue **SKIP** only.",
            "2. Re-open any CLOSED observe needs **new human OPEN** ballot.",
            "3. Do **not** unwind Path3 WITHIN / T0 carve / ledger / DD_SWITCH tip apply.",
            "4. Soft FIN/TEL Exact T+1 stay OFF.",
            "",
            "## Wiring",
            "",
            "- `scripts/ops_month_end_paper_pack.py` — COMPOSITE / SAT_RELAX / P3_T0 monitors+ledgers commented",
            "- `scripts/ops_alert_scan.py` — COMPOSITE / SAT_RELAX / P3_T0 alert sources commented",
            "- Register / OPS_STATUS / portfolio archive updated",
            "",
            f"Label: `{BATCH_LABEL}`",
            "",
        ]
    )
    (OPS / f"{BATCH_ID}.md").write_text(md + "\n", encoding="utf-8")
    payload = {
        "id": BATCH_ID,
        "date": DAY,
        "generated_at_utc": _utc(),
        "status": "EXECUTED",
        "human_tipsoft": HUMAN_TIPSOFT,
        "human_path3": HUMAN_PATH3,
        "close_tipsoft": TIPSOFT_CLOSES,
        "close_path3": PATH3_CLOSES,
        "keep_live": [
            "PATH3_WITHIN_SLEEVE",
            "T0_CARVE_FIN_SAT_SWITCH",
            "P3_COMP_SAT_DAILY_POS_LEDGER_A",
            "TIPSOFT_P3_TRAIL42_L4_DD_SWITCH",
        ],
        "keep_observe": ["TIPSOFT_P3_TRAIL42_L4_DD_SWITCH"],
        "label": BATCH_LABEL,
    }
    (OPS / f"{BATCH_ID}.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )


def _patch_register() -> None:
    path = OPS / "HUMAN_DECISION_REGISTER.md"
    text = path.read_text(encoding="utf-8")
    replacements = [
        (
            "| 0k9b | FIN×SAT COMPOSITE (HARD150 × SAT densify) | **OBSERVE OPEN** (2026-09-28) | Champion `COMP_H150_x_A20` · `FIN_SAT_COMPOSITE_OBSERVE_BALLOT_EXECUTED_OPEN.md` · parents both-quality+SAT_A20 **CLOSED** · Soft-Frozen KEEP · live CONF α=0.10 KEEP · cutover **BLOCKED** · no live |",
            "| 0k9b | FIN×SAT COMPOSITE (HARD150 × SAT densify) | **OBSERVE CLOSED** (2026-10-01) | Superseded by Path3 WITHIN + ledger LIVE · batch `OBSERVE_CLOSE_SUPERSEDED_2026-10-01.md` · Soft KEEP · live CONF α KEEP · `FIN_SAT_COMPOSITE_OBSERVE_BALLOT_EXECUTED_OPEN.md` |",
        ),
        (
            "| 0k9d | FIN×SAT tip new-mech (COOL HARD / SAT_RELAX) | **OBSERVE OPEN** `SAT_A20_RELAX` (2026-09-28) | Stage A `SAT_RELAX_HIT` · `SAT_A20_RELAX_OBSERVE_BALLOT_EXECUTED_OPEN.md` · COMPOSITE observe **KEEP** · Soft-Frozen KEEP · live CONF α=0.10 KEEP · cutover **BLOCKED** · no live |",
            "| 0k9d | FIN×SAT tip new-mech (COOL HARD / SAT_RELAX) | **OBSERVE CLOSED** (2026-10-01) | Superseded by Path3 WITHIN + ledger LIVE · batch `OBSERVE_CLOSE_SUPERSEDED_2026-10-01.md` · Soft KEEP · `SAT_A20_RELAX_OBSERVE_BALLOT_EXECUTED_OPEN.md` |",
        ),
        (
            "| 0k9r | Path3 + Exact T+0 carve-out + paper observe | **EXECUTED ACCEPT + OBSERVE OPEN** (2026-09-28) | Human `ACCEPT T+0 carve-out + OPEN paper observe: P3_T0_STATE (FIN×SAT Path3 · T0_CARVE_FIN_SAT_SWITCH)` · carve `T0_CARVE_FIN_SAT_SWITCH` · dual-paper OPERATING · sealed MDD −0.17pp **ACCEPTABLE** (abs sealed≪full/held) · Soft-Frozen clips KEEP · cutover **BLOCKED** · no live · `FIN_SAT_T0_CARVEOUT_POLICY_BALLOT_EXECUTED_ACCEPT.md` · `FIN_SAT_PATH3_T0_STATE_OBSERVE_BALLOT_EXECUTED_OPEN.md` · `FIN_SAT_PATH3_T0_SEALED_MDD_DISPOSITION.md` |",
            "| 0k9r | Path3 + Exact T+0 carve-out + paper observe | **EXECUTED ACCEPT + OBSERVE CLOSED** (2026-10-01) | Carve/fill/emit KEEP LIVE · paper `P3_T0_STATE` observe CLOSED (shadow) · batch `OBSERVE_CLOSE_SUPERSEDED_2026-10-01.md` · Soft KEEP · `FIN_SAT_T0_CARVEOUT_POLICY_BALLOT_EXECUTED_ACCEPT.md` · `FIN_SAT_PATH3_T0_STATE_OBSERVE_BALLOT_EXECUTED_OPEN.md` |",
        ),
        (
            "| 0kaw | tip Soft Exact T+1 NEARPEAK3 paper/observe | **OBSERVE OPEN / OPERATING** (2026-09-30) | Parents 0kav/0kau/0kat · human `OPEN paper observe: TIPSOFT_P3_THETA_NEARPEAK3 (tip Soft Exact T+1 · meta-detect Path3 near-peak3 · NOT hybrid T+0 carve)` · Exact T+1 only · hybrid T+0 carve **FORBIDDEN** · held **+1.45** tipY **+5.68** sealed MDD **−0.04** · Soft KEEP · Path4 OFF · broker false · cutover **BLOCKED** · `TIPSOFT_P3_NEARPEAK3_OBSERVE_BALLOT_EXECUTED_OPEN.md` |",
            "| 0kaw | tip Soft Exact T+1 NEARPEAK3 paper/observe | **OBSERVE CLOSED** (2026-10-01) | Superseded by DD_SWITCH tip apply LIVE · batch `OBSERVE_CLOSE_SUPERSEDED_2026-10-01.md` · Soft KEEP · Path4 OFF · `TIPSOFT_P3_NEARPEAK3_OBSERVE_BALLOT_EXECUTED_OPEN.md` |",
        ),
        (
            "| 0kba | tip Soft high-ON×CASH Exact T+1 twin / observe | **OBSERVE OPEN / OPERATING** (2026-10-01) | Parents 0kb9/0kb8/0kb7/0kac · human OPEN `TIPSOFT_P3_ON_UNLESS_MUTE_FT_CASH` · `L4_LIVE_P3_WITHIN`∥`ON_UNLESS_MUTE_FT_CASH` held **+0.8735** tipY **+2.4396** sealedMDD **0.0173** · Soft FIN/TEL OFF · Path4 OFF · apply **BLOCKED** · `TIPSOFT_IP3_HIGHON_CASH_OBSERVE_BALLOT_EXECUTED_OPEN.md` |",
            "| 0kba | tip Soft high-ON×CASH Exact T+1 twin / observe | **OBSERVE CLOSED** (2026-10-01) | Superseded by DD_SWITCH tip apply LIVE · batch `OBSERVE_CLOSE_SUPERSEDED_2026-10-01.md` · Soft FIN/TEL OFF · `TIPSOFT_IP3_HIGHON_CASH_OBSERVE_BALLOT_EXECUTED_OPEN.md` |",
        ),
        (
            "| 0kbb | tip Soft TRAIL42×CASH Exact T+1 observe | **OBSERVE OPEN / OPERATING** (2026-10-01) | Parents 0kba/0kb9/0kac · human `Trail42 cash的mdd可接受` → sealed MDD **-0.3632 ACCEPTABLE** · OPEN `TIPSOFT_P3_TRAIL42_FT_CASH` · `L4_LIVE_P3_WITHIN`∥`TRAIL42_FT_CASH` held **+1.4549** tipY **+11.3364** · Soft FIN/TEL OFF · Path4 OFF · apply **BLOCKED** · 0kba ON_UNLESS_MUTE KEEP · `TIPSOFT_IP3_TRAIL42_CASH_OBSERVE_BALLOT_EXECUTED_OPEN.md` · `TIPSOFT_IP3_TRAIL42_CASH_SEALED_MDD_DISPOSITION.md` |",
            "| 0kbb | tip Soft TRAIL42×CASH Exact T+1 observe | **OBSERVE CLOSED** (2026-10-01) | Twin absorbed into DD_SWITCH tip apply LIVE · batch `OBSERVE_CLOSE_SUPERSEDED_2026-10-01.md` · Soft FIN/TEL OFF · `TIPSOFT_IP3_TRAIL42_CASH_OBSERVE_BALLOT_EXECUTED_OPEN.md` |",
        ),
        (
            "· dual-paper observe KEEP · 0kba/0kbb KEEP · `TIPSOFT_IP3_TRAIL42_L4_SWITCH_BALLOT_EXECUTED_ACCEPT.md`",
            "· dual-paper observe KEEP · 0kba/0kbb **OBSERVE CLOSED** (2026-10-01) · `TIPSOFT_IP3_TRAIL42_L4_SWITCH_BALLOT_EXECUTED_ACCEPT.md`",
        ),
    ]
    for old, new in replacements:
        if old not in text:
            raise SystemExit(f"register pattern missing:\n{old[:120]}...")
        text = text.replace(old, new, 1)
    # Append timeline bullet near tip Soft / Path3 section if possible
    bullet = (
        f"- Observe CLOSE superseded batch **{DAY}** — tip Soft NEARPEAK3+MUTE×CASH+TRAIL42×CASH "
        f"+ Path3 COMPOSITE/SAT_RELAX/P3_T0 paper shadows **CLOSED** · DD_SWITCH tip apply KEEP · "
        f"Path3 WITHIN/T0/ledger KEEP · Soft KEEP · `{BATCH_ID}.md`\n"
    )
    if BATCH_ID not in text:
        # insert after 0kbd register line block in timeline if present, else append near end of Path3 timeline
        anchor = "Path3 strategy cutover **EXECUTED ACCEPT / LIVE WIRED** 2026-09-30"
        idx = text.find(anchor)
        if idx >= 0:
            # find end of that bullet line
            nl = text.find("\n", idx)
            text = text[: nl + 1] + bullet + text[nl + 1 :]
        else:
            text = text.rstrip() + "\n" + bullet
    path.write_text(text, encoding="utf-8")


def _patch_ops_status() -> None:
    path = OPS / "OPS_STATUS.md"
    text = path.read_text(encoding="utf-8")
    # narrative lines
    narr = (
        f"**Observe CLOSE superseded ({DAY}):** tip Soft `NEARPEAK3`+`MUTE×CASH`+`TRAIL42×CASH` "
        f"+ Path3 paper `COMPOSITE`/`SAT_RELAX`/`P3_T0_STATE` **CLOSED** · DD_SWITCH tip apply KEEP · "
        f"Path3 WITHIN/T0/ledger KEEP · Soft KEEP · `{BATCH_ID}.md`  \n"
    )
    if BATCH_ID not in text:
        # after DD-switch tip apply line if present
        key = "**TRAIL42⇄L4 DD-switch tip apply"
        idx = text.find(key)
        if idx < 0:
            key = "**TRAIL42⇄L4 DD-switch observe"
            idx = text.find(key)
        if idx >= 0:
            nl = text.find("\n", idx)
            text = text[: nl + 1] + narr + text[nl + 1 :]
        else:
            text = narr + text

    table_reps = [
        (
            "| FIN×SAT COMPOSITE `COMP_H150_x_A20` | **OBSERVE OPEN** (2026-09-28) | Stage A HIT · cutover **BLOCKED** · `FIN_SAT_COMPOSITE_OBSERVE_BALLOT_EXECUTED_OPEN.md` |",
            "| FIN×SAT COMPOSITE `COMP_H150_x_A20` | **OBSERVE CLOSED** (2026-10-01) | Superseded by Path3 WITHIN LIVE · batch `OBSERVE_CLOSE_SUPERSEDED_2026-10-01.md` |",
        ),
        (
            "| `SAT_A20_RELAX` tip-first densify | **OBSERVE OPEN** (2026-09-28) | Stage A `SAT_RELAX_HIT` · cutover **BLOCKED** · `SAT_A20_RELAX_OBSERVE_BALLOT_EXECUTED_OPEN.md` |",
            "| `SAT_A20_RELAX` tip-first densify | **OBSERVE CLOSED** (2026-10-01) | Superseded by Path3 WITHIN LIVE · batch `OBSERVE_CLOSE_SUPERSEDED_2026-10-01.md` |",
        ),
        (
            "| FIN×SAT Path3 `P3_T0_STATE` | **OBSERVE OPEN** (2026-09-28) | Exact T+0 carve `T0_CARVE_FIN_SAT_SWITCH` · cutover **BLOCKED** · `FIN_SAT_PATH3_T0_STATE_OBSERVE_BALLOT_EXECUTED_OPEN.md` |",
            "| FIN×SAT Path3 `P3_T0_STATE` | **OBSERVE CLOSED** (2026-10-01) | Carve LIVE KEEP · paper observe CLOSED · batch `OBSERVE_CLOSE_SUPERSEDED_2026-10-01.md` |",
        ),
        (
            "| tip Soft Exact T+1 `P3_THETA_NEARPEAK3` | **OBSERVE OPEN** (2026-09-30) | meta-detect Path3 near-peak3 · Exact T+1 only · hybrid T+0 **FORBIDDEN** · cutover **BLOCKED** · `TIPSOFT_P3_NEARPEAK3_OBSERVE_BALLOT_EXECUTED_OPEN.md` |",
            "| tip Soft Exact T+1 `P3_THETA_NEARPEAK3` | **OBSERVE CLOSED** (2026-10-01) | Superseded by DD_SWITCH tip apply · batch `OBSERVE_CLOSE_SUPERSEDED_2026-10-01.md` |",
        ),
        (
            "| tip Soft Exact T+1 `TIPSOFT_P3_ON_UNLESS_MUTE_FT_CASH` | **OBSERVE OPEN** (2026-10-01) | Path3 ON unless lag63 prem_p3<-0.01 ∧ sat_lead · OFF→FIN∪TEL→cash · Soft FIN/TEL stay OFF · Exact T+1 tip Soft twin · apply/cutover **BLOCKED** · `TIPSOFT_IP3_HIGHON_CASH_OBSERVE_BALLOT_EXECUTED_OPEN.md` |",
            "| tip Soft Exact T+1 `TIPSOFT_P3_ON_UNLESS_MUTE_FT_CASH` | **OBSERVE CLOSED** (2026-10-01) | Superseded by DD_SWITCH tip apply · batch `OBSERVE_CLOSE_SUPERSEDED_2026-10-01.md` |",
        ),
        (
            "| tip Soft Exact T+1 `TIPSOFT_P3_TRAIL42_FT_CASH` | **OBSERVE OPEN** (2026-10-01) | TRAIL42≥−0.01 × FT→CASH · sealed MDD **ACCEPTABLE** (−0.36) · Soft FIN/TEL stay OFF · apply/cutover **BLOCKED** · `TIPSOFT_IP3_TRAIL42_CASH_OBSERVE_BALLOT_EXECUTED_OPEN.md` |",
            "| tip Soft Exact T+1 `TIPSOFT_P3_TRAIL42_FT_CASH` | **OBSERVE CLOSED** (2026-10-01) | Absorbed into DD_SWITCH tip apply · batch `OBSERVE_CLOSE_SUPERSEDED_2026-10-01.md` |",
        ),
    ]
    for old, new in table_reps:
        if old not in text:
            raise SystemExit(f"OPS_STATUS table row missing:\n{old[:100]}")
        text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")


def _patch_portfolio() -> None:
    path = OPS / "RESEARCH_PORTFOLIO_KEEP_ARCHIVE.md"
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    note = (
        f"\n**Observe CLOSE superseded {DAY}:** tip Soft NEARPEAK3+MUTE×CASH+TRAIL42×CASH + "
        f"Path3 COMPOSITE/SAT_RELAX/P3_T0 paper shadows **CLOSED** · DD_SWITCH tip apply KEEP · "
        f"Path3 WITHIN/T0/ledger KEEP · `{BATCH_ID}.md`\n"
    )
    if BATCH_ID not in text:
        text = text.rstrip() + "\n" + note
        path.write_text(text + "\n", encoding="utf-8")


def _patch_month_end_pack() -> None:
    path = ROOT / "scripts" / "ops_month_end_paper_pack.py"
    text = path.read_text(encoding="utf-8")
    old_mon = '''    (
        "fin_sat_composite_month_end",
        ["python3", "scripts/fin_sat_composite_month_end_monitor.py"],
    ),
    (
        "sat_a20_relax_month_end",
        ["python3", "scripts/sat_a20_relax_month_end_monitor.py"],
    ),
    (
        "fin_sat_path3_t0_month_end",
        ["python3", "scripts/fin_sat_path3_t0_month_end_monitor.py"],
    ),'''
    new_mon = '''    # OBSERVE_CLOSE_SUPERSEDED_2026-10-01 — COMPOSITE/SAT_RELAX/P3_T0 paper shadows CLOSED
    # (
    #     "fin_sat_composite_month_end",
    #     ["python3", "scripts/fin_sat_composite_month_end_monitor.py"],
    # ),
    # (
    #     "sat_a20_relax_month_end",
    #     ["python3", "scripts/sat_a20_relax_month_end_monitor.py"],
    # ),
    # (
    #     "fin_sat_path3_t0_month_end",
    #     ["python3", "scripts/fin_sat_path3_t0_month_end_monitor.py"],
    # ),'''
    if old_mon not in text:
        raise SystemExit("month_end STEPS monitor block missing")
    text = text.replace(old_mon, new_mon, 1)
    old_led = '''    (
        "fin_sat_composite_dual_paper_ledgers",
        ["python3", "scripts/fin_sat_composite_dual_paper_ledgers.py"],
    ),
    (
        "sat_a20_relax_dual_paper_ledgers",
        ["python3", "scripts/sat_a20_relax_dual_paper_ledgers.py"],
    ),'''
    new_led = '''    # OBSERVE_CLOSE_SUPERSEDED_2026-10-01 — COMPOSITE/SAT_RELAX paper shadows CLOSED
    # (
    #     "fin_sat_composite_dual_paper_ledgers",
    #     ["python3", "scripts/fin_sat_composite_dual_paper_ledgers.py"],
    # ),
    # (
    #     "sat_a20_relax_dual_paper_ledgers",
    #     ["python3", "scripts/sat_a20_relax_dual_paper_ledgers.py"],
    # ),'''
    if old_led not in text:
        raise SystemExit("month_end STEPS_REFRESH ledger block missing")
    text = text.replace(old_led, new_led, 1)
    path.write_text(text, encoding="utf-8")


def _patch_alert_scan() -> None:
    path = ROOT / "scripts" / "ops_alert_scan.py"
    text = path.read_text(encoding="utf-8")
    old = '''        ("fin_sat_composite_month_end", FIN_SAT_COMPOSITE_JSON),
        ("sat_a20_relax_month_end", SAT_A20_RELAX_JSON),
        ("fin_sat_path3_t0_month_end", FIN_SAT_PATH3_T0_JSON),'''
    new = '''        # OBSERVE_CLOSE_SUPERSEDED_2026-10-01 — COMPOSITE/SAT_RELAX/P3_T0 CLOSED
        # ("fin_sat_composite_month_end", FIN_SAT_COMPOSITE_JSON),
        # ("sat_a20_relax_month_end", SAT_A20_RELAX_JSON),
        # ("fin_sat_path3_t0_month_end", FIN_SAT_PATH3_T0_JSON),'''
    if old not in text:
        raise SystemExit("alert_scan monitor_sources block missing")
    text = text.replace(old, new, 1)
    # update comment block near constants
    text = text.replace(
        "# SAT_A20_RELAX re-OPEN tip-first 2026-09-28 (parallel COMPOSITE)\n"
        "# Path3 P3_T0_STATE OPEN 2026-09-28 (Exact T+0 carve T0_CARVE_FIN_SAT_SWITCH)\n",
        "# SAT_A20_RELAX / Path3 P3_T0_STATE / COMPOSITE paper observes CLOSED 2026-10-01 "
        "(OBSERVE_CLOSE_SUPERSEDED; Path3 WITHIN+T0+ledger LIVE KEEP)\n",
        1,
    )
    path.write_text(text, encoding="utf-8")


def main() -> int:
    generated = _utc()
    for c in TIPSOFT_CLOSES + PATH3_CLOSES:
        _close_operating_json(c["operating"], policy=c["policy"], why=c["why"])
        _close_operating_md(c["operating"], policy=c["policy"], why=c["why"])
        _banner_open_ballot(c["ballot_open"], policy=c["policy"], why=c["why"])
        _close_cutover(c.get("cutover"), policy=c["policy"])
    _write_batch()
    _patch_register()
    _patch_ops_status()
    _patch_portfolio()
    _patch_month_end_pack()
    _patch_alert_scan()
    print(
        json.dumps(
            {
                "ok": True,
                "batch": BATCH_ID,
                "generated_at_utc": generated,
                "closed": [c["policy"] for c in TIPSOFT_CLOSES + PATH3_CLOSES],
                "keep_dd_switch": True,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
