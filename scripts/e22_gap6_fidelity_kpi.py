#!/usr/bin/env python3
"""Gap #6 execution-fidelity KPI — RESEARCH / OPS only.

Complements e22_data_quality_kpi (ledger field blank-rates) with:
  - Code default assert (E22_v3_recv_pay_effdelay after Stage-E ACCEPT 2026-09-16)
  - Live forward/e21 evidence that books fields are present
  - Ex→pay lag stats (timing gap magnitude)
  - Open receivable-window stub (universe events, not position-weighted)
  - Dividend-tax haircut sensitivity on live dividends_applied (if any)
  - Odd-lot / D5 / Stage-E promote status

Does not cutover, does not rewrite forward/e21 history.
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
    e22_day = (ROOT / "scripts/live_e22_day.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    imports_e22 = any(
        (isinstance(n, ast.Import) and any(a.name == "e22_dividend_accounting" for a in n.names))
        or (isinstance(n, ast.ImportFrom) and n.module == "e22_dividend_accounting")
        for n in tree.body
    )
    # Thin pipeline may call apply_e22_day; apply_books_for_date lives in live_e22_day.
    mentions_apply = (
        "apply_dividends_for_date" in src
        or "apply_books_for_date" in src
        or ("apply_e22_day" in src and "apply_books_for_date" in e22_day)
    )
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
        "effex_variant_named": e22div.E22_V2S_TW_EFFEX,
        "recv_effdelay_named": e22div.E22_V3_RECV_PAY_EFFDELAY,
        "tw_is_default": default == e22div.E22_V2S_TW,
        "effex_is_default": default == e22div.E22_V2S_TW_EFFEX,
        "recv_effdelay_is_default": default == e22div.E22_V3_RECV_PAY_EFFDELAY,
        "code_ok": bool(
            default == e22div.E22_V3_RECV_PAY_EFFDELAY
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
            "nhi211_net_cash": None,
            "nhi211_premium": None,
            "nhi211_n_above_threshold": None,
            "note": "No dividends_applied.csv yet — tax sensitivity deferred until live applies cash events.",
        }
    d = pd.read_csv(div_path)
    cash = d[d.get("kind", pd.Series(dtype=str)).astype(str) == "cash"] if "kind" in d.columns else d
    col = "cash_credit" if "cash_credit" in cash.columns else None
    if col is None:
        return {"available": False, "note": "dividends_applied.csv missing cash_credit column"}
    from nhi_dividend_supplemental_premium import nhi_dividend_premium

    amounts = pd.to_numeric(cash[col], errors="coerce").fillna(0.0)
    gross = float(amounts.sum())
    nhi_premium = 0.0
    nhi_net = 0.0
    n_above = 0
    for g in amounts.tolist():
        r = nhi_dividend_premium(float(g))
        nhi_premium += float(r.premium_twd)
        nhi_net += float(r.net_cash_twd)
        if r.applies:
            n_above += 1
    return {
        "available": True,
        "gross_cash_credit": gross,
        "haircut_0pct": gross,
        "haircut_10pct": gross * 0.90,
        "haircut_20pct": gross * 0.80,
        "nhi211_net_cash": nhi_net,
        "nhi211_premium": nhi_premium,
        "nhi211_n_above_threshold": int(n_above),
        "note": (
            "Report-only; formal books remain TAX0 (pre-tax). "
            "NHI211 columns use nhi_dividend_supplemental_premium threshold rule — not a Soft-Frozen gate."
        ),
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
            "Formal books accrue receivable on effective_ex_trade under "
            "E22_v3_recv_pay_effdelay (Stage-E ACCEPT); cash settles on effective_payment. "
            "Preserved cash-on-ex path: E22_v2s_tw_effex. "
            "This count is universe-level timing exposure vs custody pay-date, not position-weighted PnL."
        ),
        "severity": "Med for cash/liquidity timing; Low for raw-price total-return mark",
    }

    tax = _tax_sensitivity(LIVE_DIR / "dividends_applied.csv")

    odd_lot = {
        "status": "PROMOTED",
        # Odd-lot / D5 promote landed on effex; Stage-E DEFAULT is v3_recv_pay_effdelay.
        "formal_default": e22div.DEFAULT_BOOKS_VERSION,
        "odd_lot_promote_books": e22div.E22_V2S_TW_EFFEX,
        "named_tw_variant": e22div.E22_V2S_TW,
        "effex_variant": e22div.E22_V2S_TW_EFFEX,
        "promote_checklist": "research/ops/ODD_LOT_PROMOTE_CHECKLIST.md",
        "closeout": "research/e22/GAP65_ODD_LOT_CLOSEOUT.md",
        "human_ballot": "ACCEPT promote 2026-09-05; D5 effex ACCEPT 2026-09-16; Stage-E recv ACCEPT 2026-09-16",
        "do_not_set_default_without_human_pr": False,
    }

    flags: list[str] = []
    if not code.get("recv_effdelay_is_default"):
        flags.append(
            f"DEFAULT_BOOKS_VERSION={code['default_books_version']} "
            f"(expected {e22div.E22_V3_RECV_PAY_EFFDELAY})"
        )
    if not code["e21_imports_e22_module"] or not code["e21_calls_apply_dividends"]:
        flags.append("e21_forward_pipeline missing E22 apply wiring")
    if code.get("formal_status_wired_e21") is False:
        flags.append("formal_status says e21 not wired")
    if not live["live_ledger_e22_fields_present"]:
        flags.append("LIVE_LEDGER_E22_FIELDS_MISSING")

    kpi = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "E22_GAP6_FIDELITY_KPI",
        "live_wire": False,
        "soft_frozen_unchanged": False,
        "d5_accept": True,
        "formal_books": e22div.E22_V3_RECV_PAY_EFFDELAY,
        "preserved_cash_on_ex": e22div.PRESERVED_CASH_ON_EX,
        "code_wire": code,
        "live_ledger": live,
        "ex_to_pay_lag": {"cash": cash_lag, "stock": stock_lag},
        "receivable_stub": receivable,
        "div_tax_sensitivity": tax,
        "odd_lot": odd_lot,
        "gap_refs": {
            "brief": "research/e22/EXECUTION_DETAIL_GAP6_BRIEF.md",
            "handling": "research/gaps/E50A_AND_EXEC_GAP_HANDLING.md",
            "delay_charter": "research/ops/TWSE_DIVIDEND_CREDIT_DELAY_CHARTER.md",
            "tax_recv_charter": "research/ops/FORMAL_TAX_RECEIVABLE_BOOKS_CHARTER.md",
        },
        "flags": flags,
        "code_ok": bool(code["code_ok"] and code.get("recv_effdelay_is_default")),
        "live_evidence_ok": bool(live["live_ledger_e22_fields_present"]),
        "kpi_ok": None,  # filled below
        # CI smoke gate = code wire only. Full kpi_ok still requires live evidence
        # (AND). Do not soft-OR live_evidence into kpi_ok.
        "ci_smoke_ok": None,
    }
    # Fail-closed: code path AND live ledger evidence must both be green.
    # (Previously code_ok alone could greenwash missing live E22 fields.)
    kpi["kpi_ok"] = bool(kpi["code_ok"] and kpi["live_evidence_ok"])
    kpi["ci_smoke_ok"] = bool(kpi["code_ok"])
    if kpi["code_ok"] and not kpi["live_evidence_ok"]:
        flags.append("KPI_BLOCKED_LIVE_EVIDENCE_MISSING")
        kpi["flags"] = flags

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(kpi, indent=2) + "\n")

    def days(x: float | None) -> str:
        return "n/a" if x is None else f"{x:.1f}"

    lines = [
        "# E22 Gap #6 Fidelity KPI",
        "",
        f"Generated: `{kpi['generated_at_utc']}`",
        "Status: **OPS / RESEARCH** — Soft-Frozen Stage-E ACCEPT; live DEFAULT **`E22_v3_recv_pay_effdelay`** (receivable + effective pay).",
        "",
        "## Code wire",
        "",
        f"- Default books: **`{code['default_books_version']}`** (expect `E22_v3_recv_pay_effdelay`)",
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
        f"- observed books version: **{live.get('observed_books_version')}** — "
        "**tip lag ops debt** until next weekday forward advances tip to live DEFAULT "
        "`E22_v3_recv_pay_effdelay` (tip-align ACCEPT 2026-09-19; no history rewrite; "
        "tip lag ≠ second DEFAULT)",
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
            f"- NHI211 net / premium (threshold 2.11%): **{tax.get('nhi211_net_cash'):.2f}** / "
            f"**{tax.get('nhi211_premium'):.2f}** (n_above={tax.get('nhi211_n_above_threshold')})",
        ]
    else:
        lines.append(f"- {tax.get('note')}")
    lines += [
        "",
        "## Odd-lot / D5 (`E22_v2s_tw` → `E22_v2s_tw_effex`)",
        "",
        f"- Status: **{odd_lot['status']}** — code DEFAULT `{odd_lot['formal_default']}` "
        f"(odd-lot promote path `{odd_lot['odd_lot_promote_books']}`; legacy TW `{odd_lot['named_tw_variant']}`)",
        f"- Ballot: `{odd_lot['human_ballot']}`",
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
        f"Monitoring KPI OK (code **and** live evidence): **{kpi['kpi_ok']}**",
        f"- code_ok: **{kpi['code_ok']}**",
        f"- live_evidence_ok: **{kpi['live_evidence_ok']}**",
        f"- ci_smoke_ok (= code_ok): **{kpi['ci_smoke_ok']}**",
        "",
        "Re-run: `python3 scripts/e22_gap6_fidelity_kpi.py`",
        "",
    ]
    OUT_MD.write_text("\n".join(lines))
    print(json.dumps(kpi, indent=2))
    # Exit: 0 kpi_ok; 1 code wire fail; 2 live evidence missing (ops debt).
    if not kpi["code_ok"]:
        return 1
    if not kpi["live_evidence_ok"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
