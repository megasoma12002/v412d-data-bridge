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

# Static inventory (code-verified patterns). Update when wiring new backups.
STREAMS = [
    {
        "id": "fin12_history_ohlcv",
        "label": "Fin-12 history OHLCV",
        "primary": "github_tw_stock_data_release",
        "backup": None,
        "grade": "D",
        "critical_for_live": True,
        "notes": "TWSE covers recent append only (~14d), not full history backup",
    },
    {
        "id": "fin12_recent_ohlcv",
        "label": "Fin-12 recent OHLCV",
        "primary": "twse_mi_index",
        "backup": None,
        "grade": "B",
        "critical_for_live": True,
        "notes": "scripts/v412f_append_twse_daily.py + scripts/v412d_twse_spotcheck.py",
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
        "backup": None,
        "grade": "D",
        "critical_for_live": True,
        "notes": "Regime / L4 DD path depends on TAIEX; no second vendor wired",
    },
    {
        "id": "adj_corporate_actions",
        "label": "Adj / corporate-action factors",
        "primary": "finmind_div_result_capred_split",
        "backup": None,
        "grade": "D",
        "critical_for_live": True,
        "notes": "Single-vendor adjusted layer",
    },
    {
        "id": "dividend_amount_ex",
        "label": "Dividend amount / ex-date",
        "primary": "finmind_taiwan_stock_dividend",
        "backup": None,
        "grade": "C",
        "critical_for_live": True,
        "notes": "Payment-date has Yahoo backup; amounts do not",
        "evidence": "data/dividend_events/e22_dividend_events.csv",
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
        "kpi_ok": "PAYMENT_DATE_BACKUP_REGRESSION" not in flags,
        "phase_a_done": True,
        "phase_b_done": True,
        "phase_b_artifact": "research/ops/DATA_SOURCE_SHADOW_RECONCILE.json",
        "phase_c_next": [
            "Second vendor for full Fin-12 history (charter)",
            "Corporate-action factor dual source (research)",
            "Optional runtime TAIEX failover (today shadow-only)",
        ],
        "do_not": [
            "Treat Goodinfo/Wantgoo/CMoney as payment-date backups",
            "Silent Soft-Frozen flip",
            "Rewrite forward/e21 history",
            "Auto-overwrite e22 dividend amounts from Yahoo",
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
        "",
        "## Phase C next",
        "",
    ]
    for item in summary.get("phase_c_next") or []:
        lines.append(f"- {item}")
    lines += [
        "",
        "Authority: `research/ops/DATA_SOURCE_RESILIENCE.md`",
        "",
    ]
    OUT_MD.write_text("\n".join(lines))
    print(json.dumps({k: summary[k] for k in (
        "label", "n_critical_without_backup", "n_grade_a", "n_grade_d",
        "flags", "kpi_ok", "phase_b_done",
    )}, indent=2))
    return 0 if summary["kpi_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
