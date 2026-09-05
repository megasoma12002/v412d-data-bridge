#!/usr/bin/env python3
"""Gap #6 execution-fidelity KPI — RESEARCH / OPS only.

Complements e22_data_quality_kpi (ledger field blank-rates) with:
  - Code default assert (E22_v2s)
  - Live forward/e21 evidence that books fields are present
  - Ex→pay lag stats (timing gap magnitude)
  - Open receivable-window stub (universe events, not position-weighted)
  - Dividend-tax haircut sensitivity on live dividends_applied (if any)
  - Odd-lot promote status (E22_v2s_tw DEFERRED)

Does not edit Soft-Frozen, does not cutover, does not rewrite forward/e21.
"""
from __future__ import annotations

import ast
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import e22_dividend_accounting as e22div

ROOT = Path(__file__).resolve().parents[1]
EVENTS = ROOT / "data/dividend_events/e22_dividend_events.csv"
FORMAL = ROOT / "data/dividend_events/e22_v2s_formal_status.json"
LIVE_DIR = ROOT / "forward/e21"
E21_PIPE = ROOT / "scripts/e21_forward_pipeline.py"
OUT_DIR = ROOT / "research/ops"
OUT_JSON = OUT_DIR / "E22_GAP6_FIDELITY_KPI.json"
OUT_MD = OUT_DIR / "E22_GAP6_FIDELITY_KPI.md"


def _lag_stats(ex: pd.Series, pay: pd.Series) -> dict:
    ex_dt = pd.to_datetime(ex, errors="coerce")
    pay_dt = pd.to_datetime(pay, errors="coerce")
    lag = (pay_dt - ex_dt).dt.days.dropna()
    if lag.empty:
        return {"n": 0, "median_days": None, "p90_days": None, "mean_days": None, "min_days": None, "max_days": None}
    return {
        "n": int(len(lag)),
        "median_days": float(lag.median()),
        "p90_days": float(lag.quantile(0.9)),
        "mean_days": float(lag.mean()),
        "min_days": float(lag.min()),
        "max_days": float(lag.max()),
    }


def _code_wire_assert() -> dict:
    src = E21_PIPE.read_text(encoding="utf-8")
    tree = ast.parse(src)
    imports_e22 = any(
        (isinstance(n, ast.Import) and any(a.name == "e22_dividend_accounting" for a in n.names))
        or (isinstance(n, ast.ImportFrom) and n.module == "e22_dividend_accounting")
        for n in tree.body
    )
    mentions_apply = "apply_dividends_for_date" in src
    mentions_default = "DEFAULT_BOOKS_VERSION" in src or "E22_BOOKS_VERSION" in src
    formal = {}
    if FORMAL.exists():
        formal = json.loads(FORMAL.read_text())
    wired = (formal.get("wired") or {}).get("e21_forward_pipeline")
    default = e22div.DEFAULT_BOOKS_VERSION
    return {
        "default_books_version": default,
        "default_is_e22_v2s": default == e22div.E22_V2S,
        "e21_imports_e22_module": imports_e22,
        "e21_calls_apply_dividends": mentions_apply,
        "e21_references_books_version": mentions_default,
        "formal_status_wired_e21": wired,
        "tw_variant_named": e22div.E22_V2S_TW,
        "tw_is_default": default == e22div.E22_V2S_TW,
        "code_ok": bool(
            default == e22div.E22_V2S
            and imports_e22
            and mentions_apply
            and (wired is True or wired is None)
        ),
    }


def _live_ledger_evidence(asof: str | None) -> dict:
    state_path = LIVE_DIR / "portfolio_state.json"
    nav_path = LIVE_DIR / "nav.csv"
    div_path = LIVE_DIR / "dividends_applied.csv"
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    nav_cols: list[str] = []
    if nav_path.exists():
        nav_cols = list(pd.read_csv(nav_path, nrows=0).columns)
    has_state_version = "e22_books_version" in state
    has_state_manifest = "e22_manifest" in state
    has_nav_version = "e22_version" in nav_cols
    has_div_file = div_path.exists()
    n_div_rows = int(len(pd.read_csv(div_path))) if has_div_file else 0
    version_observed = state.get("e22_books_version")
    if version_observed is None and has_nav_version:
        nav = pd.read_csv(nav_path)
        if len(nav):
            version_observed = str(nav["e22_version"].iloc[-1])
    fields_present = bool(has_state_version and has_state_manifest and has_nav_version)
    return {
        "live_dir": str(LIVE_DIR),
        "asof": asof or state.get("last_date"),
        "portfolio_has_e22_books_version": has_state_version,
        "portfolio_has_e22_manifest": has_state_manifest,
        "nav_has_e22_version_col": has_nav_version,
        "dividends_applied_exists": has_div_file,
        "dividends_applied_n": n_div_rows,
        "observed_books_version": version_observed,
        "live_ledger_e22_fields_present": fields_present,
        "note": (
            None
            if fields_present
            else (
                "Live ledger artifacts predate E22 field persistence "
                "(code path is wired; next forward run should write e22_* fields). "
                "Do not rewrite history."
            )
        ),
    }


def _tax_sensitivity(div_path: Path) -> dict:
    if not div_path.exists():
        return {
            "available": False,
            "gross_cash_credit": None,
            "haircut_0pct": None,
            "haircut_10pct": None,
            "haircut_20pct": None,
            "note": "No dividends_applied.csv yet — tax sensitivity deferred until live applies cash events.",
        }
    d = pd.read_csv(div_path)
    cash = d[d.get("kind", pd.Series(dtype=str)).astype(str) == "cash"] if "kind" in d.columns else d
    col = "cash_credit" if "cash_credit" in cash.columns else None
    if col is None:
        return {"available": False, "note": "dividends_applied.csv missing cash_credit column"}
    gross = float(pd.to_numeric(cash[col], errors="coerce").fillna(0).sum())
    return {
        "available": True,
        "gross_cash_credit": gross,
        "haircut_0pct": gross,
        "haircut_10pct": gross * 0.90,
        "haircut_20pct": gross * 0.80,
        "note": "Report-only; formal books remain TAX0 (pre-tax). Not a Soft-Frozen gate.",
    }


def main() -> int:
    if not EVENTS.exists():
        raise SystemExit(f"missing {EVENTS}")

    d = pd.read_csv(EVENTS)
    cash = d[d["cash_dividend"].fillna(0).astype(float) > 0].copy()
    stock = d[d["stock_dividend"].fillna(0).astype(float) > 0].copy()

    code = _code_wire_assert()
    state_path = LIVE_DIR / "portfolio_state.json"
    asof = None
    if state_path.exists():
        asof = json.loads(state_path.read_text()).get("last_date")
    asof = str(asof or datetime.now(timezone.utc).date())[:10]
    asof_ts = pd.Timestamp(asof)

    live = _live_ledger_evidence(asof)
    cash_lag = _lag_stats(cash["cash_ex_date"], cash["cash_payment_date"]) if len(cash) else _lag_stats(pd.Series(dtype=str), pd.Series(dtype=str))
    stock_lag = _lag_stats(stock["stock_ex_date"], stock["stock_payment_date"]) if len(stock) else _lag_stats(pd.Series(dtype=str), pd.Series(dtype=str))

    cash_ex = pd.to_datetime(cash["cash_ex_date"], errors="coerce")
    cash_pay = pd.to_datetime(cash["cash_payment_date"], errors="coerce")
    open_recv = cash[(cash_ex <= asof_ts) & (cash_pay > asof_ts)]
    receivable = {
        "asof": asof,
        "n_cash_events_in_receivable_window": int(len(open_recv)),
        "codes": sorted({str(c) for c in open_recv["code"].astype(str)}) if len(open_recv) else [],
        "policy_note": (
            "Formal books credit cash on cash_ex_date (no receivable asset). "
            "This count is universe-level timing exposure vs custody pay-date, not position-weighted PnL."
        ),
        "severity": "Med for cash/liquidity timing; Low for raw-price total-return mark",
    }

    tax = _tax_sensitivity(LIVE_DIR / "dividends_applied.csv")

    odd_lot = {
        "status": "DEFERRED",
        "formal_default": e22div.E22_V2S,
        "named_tw_variant": e22div.E22_V2S_TW,
        "promote_checklist": "research/ops/ODD_LOT_PROMOTE_CHECKLIST.md",
        "closeout": "research/e22/GAP65_ODD_LOT_CLOSEOUT.md",
        "do_not_set_default_without_human_pr": True,
    }

    flags: list[str] = []
    if not code["default_is_e22_v2s"]:
        flags.append(f"DEFAULT_BOOKS_VERSION={code['default_books_version']} (expected E22_v2s)")
    if not code["e21_imports_e22_module"] or not code["e21_calls_apply_dividends"]:
        flags.append("e21_forward_pipeline missing E22 apply wiring")
    if code.get("formal_status_wired_e21") is False:
        flags.append("formal_status says e21 not wired")
    if not live["live_ledger_e22_fields_present"]:
        flags.append("LIVE_LEDGER_E22_FIELDS_MISSING")
    if code.get("tw_is_default"):
        flags.append("E22_v2s_tw unexpectedly set as DEFAULT (promote requires human PR)")

    kpi = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "E22_GAP6_FIDELITY_KPI",
        "live_wire": False,
        "soft_frozen_unchanged": True,
        "formal_books": e22div.E22_V2S,
        "code_wire": code,
        "live_ledger": live,
        "ex_to_pay_lag": {"cash": cash_lag, "stock": stock_lag},
        "receivable_stub": receivable,
        "div_tax_sensitivity": tax,
        "odd_lot": odd_lot,
        "gap_refs": {
            "brief": "research/e22/EXECUTION_DETAIL_GAP6_BRIEF.md",
            "handling": "research/gaps/E50A_AND_EXEC_GAP_HANDLING.md",
        },
        "flags": flags,
        "code_ok": bool(code["code_ok"] and code["default_is_e22_v2s"] and not code.get("tw_is_default")),
        "live_evidence_ok": bool(live["live_ledger_e22_fields_present"]),
        "kpi_ok": None,  # filled below
    }
    # Monitoring KPI is green when code path is correct; live evidence may lag until next forward.
    kpi["kpi_ok"] = bool(kpi["code_ok"])

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(kpi, indent=2) + "\n")

    def days(x: float | None) -> str:
        return "n/a" if x is None else f"{x:.1f}"

    lines = [
        "# E22 Gap #6 Fidelity KPI",
        "",
        f"Generated: `{kpi['generated_at_utc']}`",
        "Status: **OPS / RESEARCH** — Soft-Frozen unchanged; no cutover; no odd-lot promote.",
        "",
        "## Code wire",
        "",
        f"- Default books: **`{code['default_books_version']}`** (expect `E22_v2s`)",
        f"- E21 imports/apply: **{code['e21_imports_e22_module']}** / **{code['e21_calls_apply_dividends']}**",
        f"- Formal status wired: **{code.get('formal_status_wired_e21')}**",
        f"- Code OK: **{kpi['code_ok']}**",
        "",
        "## Live ledger evidence (`forward/e21`)",
        "",
        f"- asof: **{live.get('asof')}**",
        f"- `e22_books_version` in portfolio_state: **{live['portfolio_has_e22_books_version']}**",
        f"- `e22_manifest` in portfolio_state: **{live['portfolio_has_e22_manifest']}**",
        f"- `e22_version` col in nav.csv: **{live['nav_has_e22_version_col']}**",
        f"- `dividends_applied.csv`: **{live['dividends_applied_exists']}** (n={live['dividends_applied_n']})",
        f"- Live evidence OK: **{kpi['live_evidence_ok']}**",
    ]
    if live.get("note"):
        lines += ["", f"> {live['note']}"]
    lines += [
        "",
        "## Ex → pay lag (ledger completeness already green; this is timing fidelity)",
        "",
        f"- Cash median / p90 days: **{days(cash_lag['median_days'])}** / **{days(cash_lag['p90_days'])}** (n={cash_lag['n']})",
        f"- Stock median / p90 days: **{days(stock_lag['median_days'])}** / **{days(stock_lag['p90_days'])}** (n={stock_lag['n']})",
        "",
        "## Receivable stub (universe, report-only)",
        "",
        f"- Open cash events with ex≤asof < pay: **{receivable['n_cash_events_in_receivable_window']}**",
        f"- Codes: `{', '.join(receivable['codes']) or 'none'}`",
        f"- {receivable['policy_note']}",
        "",
        "## Dividend tax sensitivity (report-only; formal = TAX0)",
        "",
    ]
    if tax.get("available"):
        lines += [
            f"- Gross cash credits applied: **{tax['gross_cash_credit']:.2f}**",
            f"- After 10% / 20% haircut: **{tax['haircut_10pct']:.2f}** / **{tax['haircut_20pct']:.2f}**",
        ]
    else:
        lines.append(f"- {tax.get('note')}")
    lines += [
        "",
        "## Odd-lot (`E22_v2s_tw`)",
        "",
        f"- Status: **{odd_lot['status']}** — default remains `{odd_lot['formal_default']}`",
        f"- Promote checklist: `{odd_lot['promote_checklist']}`",
        "",
        "## Flags",
        "",
    ]
    if flags:
        for f in flags:
            lines.append(f"- `{f}`")
    else:
        lines.append("- None")
    lines += [
        "",
        f"Monitoring KPI OK (code path): **{kpi['kpi_ok']}**",
        "",
        "Re-run: `python3 scripts/e22_gap6_fidelity_kpi.py`",
        "",
    ]
    OUT_MD.write_text("\n".join(lines))
    print(json.dumps(kpi, indent=2))
    return 0 if kpi["kpi_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
