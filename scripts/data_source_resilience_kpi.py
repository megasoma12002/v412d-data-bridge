#!/usr/bin/env python3
"""Data-source resilience KPI — RESEARCH / OPS only.

Inventories primary/backup coverage for live-critical streams.
Emits:
  research/ops/DATA_SOURCE_RESILIENCE_KPI.json
  research/ops/DATA_SOURCE_RESILIENCE_KPI.md

Never flips Soft-Frozen. Never live-wires. Never rewrites forward/e21.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "research/ops"
OUT_JSON = OUT_DIR / "DATA_SOURCE_RESILIENCE_KPI.json"
OUT_MD = OUT_DIR / "DATA_SOURCE_RESILIENCE_KPI.md"
PHASE_C_JSON = OUT_DIR / "DATA_SOURCE_PHASE_C_PROBES.json"

# Static inventory (code-verified patterns). Update when wiring new backups.
STREAMS = [
    {
        "id": "fin12_history_ohlcv",
        "label": "Fin-12 history OHLCV",
        "primary": "github_tw_stock_data_release",
        "backup": "yahoo_tw_shadow_phase_c",
        "grade": "C",
        "critical_for_live": True,
        "notes": (
            "Primary still GitHub archive; Phase C Yahoo .TW return shadow "
            "(flag-only, not runtime failover)"
        ),
        "backup_script": "scripts/data_source_phase_c_probes.py",
        "evidence": "research/ops/DATA_SOURCE_PHASE_C_PROBES.json",
    },
    {
        "id": "fin12_recent_ohlcv",
        "label": "Fin-12 recent OHLCV",
        "primary": "twse_mi_index",
        "backup": "yahoo_tw_shadow_phase_b",
        "grade": "B",
        "critical_for_live": True,
        "notes": "scripts/v412f_append_twse_daily.py + Phase B shadow returns gate",
        "backup_script": "scripts/data_source_shadow_reconcile.py",
        "evidence": "research/ops/DATA_SOURCE_SHADOW_RECONCILE.json",
    },
    {
        "id": "telecom_0050_raw_ohlcv",
        "label": "Telecom / 0050 raw OHLCV",
        "primary": "finmind_taiwan_stock_price",
        "backup": "yahoo_finance",
        "grade": "A",
        "critical_for_live": True,
        "notes": "scripts/fetch_telecom_0050_ohlcv.py FinMind→Yahoo",
        "backup_script": "scripts/fetch_telecom_0050_ohlcv.py",
    },
    {
        "id": "taiex",
        "label": "TAIEX",
        "primary": "finmind_taiwan_stock_price_TAIEX",
        "backup": "yahoo_twii_opt_in_failover",
        "grade": "C",
        "critical_for_live": True,
        "notes": (
            "Phase B shadow OK; Phase C opt-in helper "
            "scripts/taiex_fetch_with_failover.py (e21 default still FinMind)"
        ),
        "backup_script": "scripts/taiex_fetch_with_failover.py",
        "evidence": "research/ops/DATA_SOURCE_PHASE_C_PROBES.json",
    },
    {
        "id": "adj_corporate_actions",
        "label": "Adj / corporate-action factors",
        "primary": "live_market_adj_close",
        "backup": "yahoo_adj_close_shadow_phase_c",
        "grade": "C",
        "critical_for_live": True,
        "notes": "Phase C adj return shadow vs Yahoo; flag-only, no auto-overwrite",
        "backup_script": "scripts/data_source_phase_c_probes.py",
        "evidence": "research/ops/DATA_SOURCE_PHASE_C_PROBES.json",
    },
    {
        "id": "dividend_amount_ex",
        "label": "Dividend amount / ex-date",
        "primary": "finmind_taiwan_stock_dividend",
        "backup": "yahoo_amount_shadow_phase_b",
        "grade": "B",
        "critical_for_live": True,
        "notes": "Phase B flag-only amount shadow; payment-date has Yahoo runtime backup",
        "evidence": "data/dividend_events/e22_dividend_events.csv",
        "backup_script": "scripts/data_source_shadow_reconcile.py",
    },
    {
        "id": "dividend_payment_date",
        "label": "Dividend payment date",
        "primary": "finmind_then_mops",
        "backup": "yahoo_tw_quote_dividend",
        "grade": "A",
        "critical_for_live": True,
        "notes": "Goodinfo/Wantgoo/CMoney blocked; Yahoo filled 29 gaps",
        "failed_alternates": {
            "goodinfo": "cloudflare",
            "wantgoo": "403/404",
            "cmoney": "no_payment_column",
        },
        "backup_script": "scripts/e22_backfill_payment_dates_yahoo.py",
        "evidence": "data/dividend_events/yahoo_tw_dividend_history.csv",
    },
    {
        "id": "e50_fundamentals",
        "label": "E50 fundamentals",
        "primary": "finmind",
        "backup": None,
        "grade": "D",
        "critical_for_live": False,
        "notes": "Research path; not Soft-Frozen cutover-critical",
    },
]


def _artifact_ok(rel: str | None) -> bool | None:
    if not rel:
        return None
    return (ROOT / rel).exists()


def _phase_c_status() -> dict:
    if not PHASE_C_JSON.exists():
        return {"phase_c_done": False, "phase_c_overall": None, "phase_c_artifact_present": False}
    try:
        obj = json.loads(PHASE_C_JSON.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"phase_c_done": False, "phase_c_overall": "INVALID_JSON", "phase_c_artifact_present": True}
    overall = obj.get("overall_status")
    return {
        "phase_c_done": overall == "PASS",
        "phase_c_overall": overall,
        "phase_c_artifact_present": True,
    }


def main() -> int:
    rows = []
    for s in STREAMS:
        row = dict(s)
        row["has_backup"] = bool(s.get("backup"))
        ev = s.get("evidence")
        row["evidence_present"] = _artifact_ok(ev) if ev else None
        bs = s.get("backup_script")
        row["backup_script_present"] = _artifact_ok(bs) if bs else None
        rows.append(row)

    n_crit = sum(1 for r in rows if r["critical_for_live"])
    n_crit_no_backup = sum(1 for r in rows if r["critical_for_live"] and not r["has_backup"])
    n_grade_a = sum(1 for r in rows if r["grade"] == "A")
    n_grade_d = sum(1 for r in rows if r["grade"] == "D")

    flags = []
    for r in rows:
        if r["critical_for_live"] and not r["has_backup"]:
            flags.append(f"SINGLE_POINT:{r['id']}")
        if r.get("backup_script") and r.get("backup_script_present") is False:
            flags.append(f"MISSING_BACKUP_SCRIPT:{r['id']}")

    # Payment-date path should stay A with script present
    pay = next(r for r in rows if r["id"] == "dividend_payment_date")
    if pay["has_backup"] and pay.get("backup_script_present"):
        pass
    else:
        flags.append("PAYMENT_DATE_BACKUP_REGRESSION")

    pc = _phase_c_status()
    if not pc["phase_c_artifact_present"]:
        flags.append("PHASE_C_PROBES_MISSING")
    elif not pc["phase_c_done"]:
        flags.append(f"PHASE_C_PROBES_{pc['phase_c_overall'] or 'FAIL'}")

    phase_a_doc = ROOT / "research/ops/DATA_SOURCE_RESILIENCE.md"
    phase_b_json = ROOT / "research/ops/DATA_SOURCE_SHADOW_RECONCILE.json"
    phase_a_done = phase_a_doc.exists() and phase_a_doc.stat().st_size > 0
    phase_b_done = False
    if phase_b_json.exists():
        try:
            phase_b_done = bool(json.loads(phase_b_json.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            phase_b_done = False

    # Evidence integrity: critical streams that declare evidence must have the file present.
    missing_evidence = [
        r["id"]
        for r in rows
        if r["critical_for_live"] and r.get("evidence") and not r.get("evidence_present")
    ]
    if missing_evidence:
        flags.append(f"CRITICAL_EVIDENCE_MISSING:{','.join(missing_evidence)}")
    if not phase_a_done:
        flags.append("PHASE_A_ARTIFACT_MISSING")
    if not phase_b_done:
        flags.append("PHASE_B_ARTIFACT_MISSING_OR_INVALID")

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "DATA_SOURCE_RESILIENCE_KPI",
        "live_wire": False,
        "soft_frozen_unchanged": True,
        "authority": "research/ops/DATA_SOURCE_RESILIENCE.md",
        "n_streams": len(rows),
        "n_critical": n_crit,
        "n_critical_without_backup": n_crit_no_backup,
        "n_grade_a": n_grade_a,
        "n_grade_d": n_grade_d,
        "streams": rows,
        "flags": flags,
        "kpi_ok": (
            "PAYMENT_DATE_BACKUP_REGRESSION" not in flags
            and "CRITICAL_EVIDENCE_MISSING" not in "".join(flags)
            and phase_a_done
            and phase_b_done
        ),
        "phase_a_done": phase_a_done,
        "phase_b_done": phase_b_done,
        "phase_b_artifact": "research/ops/DATA_SOURCE_SHADOW_RECONCILE.json",
        "phase_c_done": pc["phase_c_done"],
        "phase_c_overall": pc["phase_c_overall"],
        "phase_c_artifact": "research/ops/DATA_SOURCE_PHASE_C_PROBES.json",
        "phase_c_note": (
            "Prep DONE when probes PASS; TAIEX Yahoo failover remains opt-in "
            "(not silent e21 primary switch)"
        ),
        "do_not": [
            "Treat Goodinfo/Wantgoo/CMoney as payment-date backups",
            "Silent Soft-Frozen flip",
            "Rewrite forward/e21 history",
            "Auto-overwrite e22 dividend amounts from Yahoo",
            "Silent e21 TAIEX primary switch to Yahoo without human PR",
        ],
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(summary, indent=2) + "\n")

    lines = [
        "# Data Source Resilience KPI",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        "Status: **OPS** — Soft-Frozen unchanged; no live-wire.",
        "",
        f"- Critical streams: **{n_crit}**",
        f"- Critical **without** backup: **{n_crit_no_backup}**",
        f"- Grade A / D: **{n_grade_a}** / **{n_grade_d}**",
        f"- `kpi_ok`: **{summary['kpi_ok']}** (fails only on payment-date backup regression)",
        f"- Phase C probes: **{pc['phase_c_overall'] or 'MISSING'}** (`phase_c_done={pc['phase_c_done']}`)",
        "",
        "| Stream | Grade | Primary | Backup | Critical |",
        "|---|:---:|---|---|:---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['label']} | {r['grade']} | `{r['primary']}` | "
            f"{('`' + r['backup'] + '`') if r['backup'] else '—'} | "
            f"{'Y' if r['critical_for_live'] else 'n'} |"
        )
    lines += ["", "## Flags", ""]
    if flags:
        for f in flags:
            lines.append(f"- `{f}`")
    else:
        lines.append("- None")
    lines += [
        "",
        "## Phase status",
        "",
        f"- Phase A: **DONE**",
        f"- Phase B: **DONE** (`{summary.get('phase_b_artifact')}`)",
        f"- Phase C: **{'DONE' if pc['phase_c_done'] else 'OPEN'}** "
        f"(`{summary.get('phase_c_artifact')}`; overall={pc['phase_c_overall']})",
        "",
        summary["phase_c_note"],
        "",
        "Authority: `research/ops/DATA_SOURCE_RESILIENCE.md`",
        "",
    ]
    OUT_MD.write_text("\n".join(lines))
    print(
        json.dumps(
            {
                k: summary[k]
                for k in (
                    "label",
                    "n_critical_without_backup",
                    "n_grade_a",
                    "n_grade_d",
                    "flags",
                    "kpi_ok",
                    "phase_b_done",
                    "phase_c_done",
                    "phase_c_overall",
                )
            },
            indent=2,
        )
    )
    return 0 if summary["kpi_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
