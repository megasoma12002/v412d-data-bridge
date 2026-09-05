#!/usr/bin/env python3
"""E22 dividend data-quality KPI — RESEARCH / OPS only.

Summarizes payment-date / ex-date completeness for the Soft-Frozen live books
path (E22_v2s). Does not edit events, does not flip Soft-Frozen, does not cutover.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EVENTS = ROOT / "data/dividend_events/e22_dividend_events.csv"
GAP_REPORT = ROOT / "data/dividend_events/e22_payment_date_gap_report.json"
FORMAL = ROOT / "data/dividend_events/e22_v2s_formal_status.json"
OUT_DIR = ROOT / "research/ops"
OUT_JSON = OUT_DIR / "E22_DATA_QUALITY_KPI.json"
OUT_MD = OUT_DIR / "E22_DATA_QUALITY_KPI.md"


def _blank_rate(s: pd.Series) -> float:
    if len(s) == 0:
        return 0.0
    blank = s.isna() | (s.astype(str).str.strip() == "") | (s.astype(str).str.lower() == "nan")
    return float(blank.mean())


def main() -> int:
    if not EVENTS.exists():
        raise SystemExit(f"missing {EVENTS}")

    d = pd.read_csv(EVENTS)
    cash = d[d["cash_dividend"].fillna(0).astype(float) > 0].copy()
    stock = d[d["stock_dividend"].fillna(0).astype(float) > 0].copy()

    kpi = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "E22_DATA_QUALITY_KPI",
        "live_wire": False,
        "soft_frozen_unchanged": True,
        "formal_books": "E22_v2s",
        "events_path": str(EVENTS),
        "n_events": int(len(d)),
        "n_cash_rows": int(len(cash)),
        "n_stock_rows": int(len(stock)),
        "cash_payment_date_blank_rate": _blank_rate(cash["cash_payment_date"]) if len(cash) else None,
        "cash_ex_date_blank_rate": _blank_rate(cash["cash_ex_date"]) if len(cash) else None,
        "stock_payment_date_blank_rate": _blank_rate(stock["stock_payment_date"]) if len(stock) else None,
        "stock_ex_date_blank_rate": _blank_rate(stock["stock_ex_date"]) if len(stock) else None,
        "announcement_date_blank_rate": _blank_rate(d["announcement_date"]),
    }

    if GAP_REPORT.exists():
        kpi["gap_report"] = json.loads(GAP_REPORT.read_text())
    if FORMAL.exists():
        formal = json.loads(FORMAL.read_text())
        kpi["formal_status"] = {
            "formal_books": formal.get("formal_books"),
            "wired_e21": (formal.get("wired") or {}).get("e21_forward_pipeline"),
            "unit_ok": (formal.get("verify") or {}).get("unit_ok"),
        }

    # Soft thresholds (ops visibility; not Soft-Frozen flip triggers)
    flags = []
    if (kpi["cash_payment_date_blank_rate"] or 0) > 0.02:
        flags.append("cash_payment_date_blank_rate>2%")
    if (kpi["cash_ex_date_blank_rate"] or 0) > 0.02:
        flags.append("cash_ex_date_blank_rate>2%")
    gap = kpi.get("gap_report") or {}
    if gap.get("n_still_missing_official", 0) not in (0, None):
        flags.append(f"n_still_missing_official={gap.get('n_still_missing_official')}")
    kpi["flags"] = flags
    kpi["kpi_ok"] = len(flags) == 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(kpi, indent=2) + "\n")

    def pct(x: float | None) -> str:
        return "n/a" if x is None else f"{100 * x:.2f}%"

    lines = [
        "# E22 Data-Quality KPI",
        "",
        f"Generated: `{kpi['generated_at_utc']}`",
        "Status: **OPS / RESEARCH** — Soft-Frozen unchanged; E22_v2s remains formal books.",
        "",
        f"- Events: **{kpi['n_events']}** (cash rows {kpi['n_cash_rows']}, stock rows {kpi['n_stock_rows']})",
        f"- Cash payment-date blank rate: **{pct(kpi['cash_payment_date_blank_rate'])}**",
        f"- Cash ex-date blank rate: **{pct(kpi['cash_ex_date_blank_rate'])}**",
        f"- Stock payment-date blank rate: **{pct(kpi['stock_payment_date_blank_rate'])}**",
        f"- Stock ex-date blank rate: **{pct(kpi['stock_ex_date_blank_rate'])}**",
        f"- KPI OK: **{kpi['kpi_ok']}**",
        "",
        "## Flags",
        "",
    ]
    if flags:
        for f in flags:
            lines.append(f"- {f}")
    else:
        lines.append("- None")
    lines += [
        "",
        "## Note",
        "",
        "- Timing policy for formal books remains ex-date based (see `e22_v2s_formal_status.json`).",
        "- Payment-date completeness is an ops completeness KPI, not a Soft-Frozen gate.",
        "- Re-run: `python3 scripts/e22_data_quality_kpi.py`",
        "",
    ]
    OUT_MD.write_text("\n".join(lines))
    print(json.dumps(kpi, indent=2))
    return 0 if kpi["kpi_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
