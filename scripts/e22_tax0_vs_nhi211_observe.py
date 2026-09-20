#!/usr/bin/env python3
"""Observe-only TAX0 Stage-E vs NHI211 sandbox on FIN cash dividends (2023+).

Light alternative to a full sealed day-walk: walk Soft-Frozen FIN cash events
with tip share counts (or --shares), apply Stage-E effective ex/pay clocks via
``load_calendar_window``, and compare gross TAX0 settle cash vs NHI 2.11%
threshold net.

Writes ``research/ops/E22_TAX0_VS_NHI211_OBSERVE.{md,json}``.
``promote_ready=false`` · Soft-Frozen KEEP · tip history untouched · no live wire.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import e22_dividend_accounting as formal
import e22_v3_sandbox_books as sandbox
from e50_early_stack_combined_nav import FIN
from nhi_dividend_supplemental_premium import (
    NHI_DIVIDEND_THRESHOLD_TWD,
    NHI_SUPPLEMENTAL_RATE,
    nhi_dividend_premium,
)
from twse_session_sources import DEFAULT_CALENDAR_DIR, load_calendar_window

ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "research" / "ops"
TIP_STATE = ROOT / "forward" / "e21" / "portfolio_state.json"
SEALED_START = "2023-01-01"
TAX0 = formal.DEFAULT_BOOKS_VERSION  # E22_v3_recv_pay_effdelay
NHI211 = sandbox.E22_V3_RECV_PAY_EFFDELAY_NHI211


def _tip_fin_shares() -> dict[str, float]:
    if not TIP_STATE.exists():
        return {c: 1000.0 for c in FIN}
    state = json.loads(TIP_STATE.read_text(encoding="utf-8"))
    pos = state.get("positions") or {}
    out: dict[str, float] = {}
    for c in FIN:
        try:
            out[c] = float(pos.get(c, 1000.0))
        except (TypeError, ValueError):
            out[c] = 1000.0
    return out


def _load_sessions_for_events(events) -> tuple[list, list]:
    years: set[int] = set()
    for ev in events:
        for raw in (ev.ex_date, ev.payment_date):
            s = str(raw or "")[:10]
            if len(s) == 10:
                try:
                    years.add(int(s[:4]))
                except ValueError:
                    pass
    if not years:
        years.add(datetime.now(timezone.utc).year)
    # Union Y±1 windows across event years (fail-closed on newest center).
    sessions: list = []
    settlements: list = []
    for y in sorted(years):
        try:
            s, t = load_calendar_window(y, calendar_dir=DEFAULT_CALENDAR_DIR, span=1)
            sessions.extend(s)
            settlements.extend(t)
        except FileNotFoundError:
            continue
    if not sessions:
        # Last resort: tip year
        center = max(years)
        sessions, settlements = load_calendar_window(
            center, calendar_dir=DEFAULT_CALENDAR_DIR, span=1
        )
    return sorted(set(sessions)), sorted(set(settlements))


def run_observe(*, shares_override: float | None = None) -> dict:
    tip_shares = _tip_fin_shares()
    if shares_override is not None:
        tip_shares = {c: float(shares_override) for c in FIN}

    events = [
        e
        for e in formal.load_dividend_events()
        if e.code in FIN
        and e.kind == "cash"
        and str(e.ex_date or "")[:10] >= SEALED_START
    ]
    sessions, settlements = _load_sessions_for_events(events)

    rows: list[dict] = []
    tax0_total = 0.0
    nhi_total = 0.0
    premium_total = 0.0
    n_above = 0

    for ev in sorted(events, key=lambda e: (e.ex_date, e.code)):
        sh = float(tip_shares.get(ev.code, 0.0))
        gross = float(ev.amount) * sh
        ex_eff = sandbox.resolve_ex_day(
            ev, use_effective=True, sessions=sessions
        )
        pay_eff = sandbox.resolve_pay_day(
            ev, use_effective=True, settlements=settlements
        )
        prem = nhi_dividend_premium(gross)
        tax0_total += gross
        nhi_total += float(prem.net_cash_twd)
        premium_total += float(prem.premium_twd)
        if prem.applies:
            n_above += 1
        rows.append(
            {
                "code": ev.code,
                "ex_date": str(ev.ex_date)[:10],
                "payment_date": str(ev.payment_date or "")[:10],
                "effective_ex": ex_eff,
                "effective_pay": pay_eff,
                "shares": sh,
                "amount_per_share": float(ev.amount),
                "gross_tax0": gross,
                "nhi_applies": prem.applies,
                "nhi_premium": float(prem.premium_twd),
                "net_nhi211": float(prem.net_cash_twd),
                "delta_vs_tax0": float(prem.net_cash_twd) - gross,
            }
        )

    generated = datetime.now(timezone.utc).isoformat()
    payload = {
        "generated_at_utc": generated,
        "method": (
            "Focused FIN cash-event walk (sealed_2023_plus+), not full sealed day-walk. "
            "Stage-E effective ex/pay via load_calendar_window; NHI via "
            "nhi_dividend_supplemental_premium on tip (or --shares) position sizes."
        ),
        "tax0_version": TAX0,
        "nhi211_version": NHI211,
        "promote_ready": False,
        "soft_frozen_keep": True,
        "live_default_untouched": TAX0,
        "nhi_rate": NHI_SUPPLEMENTAL_RATE,
        "nhi_threshold_twd": NHI_DIVIDEND_THRESHOLD_TWD,
        "sealed_start": SEALED_START,
        "fin_codes": list(FIN),
        "shares_source": "override" if shares_override is not None else "tip_portfolio_state",
        "shares_by_code": tip_shares,
        "n_cash_events": len(rows),
        "n_events_above_nhi_threshold": n_above,
        "sum_gross_tax0": tax0_total,
        "sum_net_nhi211": nhi_total,
        "sum_nhi_premium": premium_total,
        "sum_delta_vs_tax0": nhi_total - tax0_total,
        "calendar_sessions_n": len(sessions),
        "calendar_settlements_n": len(settlements),
        "events": rows,
        "note": (
            "Observe-only cashflow fidelity. Custody may withhold 2.11% at pay when "
            "single gross ≥ 20k; Stage-E TAX0 still credits gross. No tip rewrite."
        ),
    }
    return payload


def write_artifacts(payload: dict) -> tuple[Path, Path]:
    OPS.mkdir(parents=True, exist_ok=True)
    json_path = OPS / "E22_TAX0_VS_NHI211_OBSERVE.json"
    md_path = OPS / "E22_TAX0_VS_NHI211_OBSERVE.md"
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# E22 TAX0 vs NHI211 — observe-only",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Status: **OBSERVE** · Soft-Frozen **KEEP** · `promote_ready=false` · **no** live NHI wire",
        "",
        "## Method",
        "",
        f"- {payload['method']}",
        f"- TAX0 (live DEFAULT): `{payload['tax0_version']}`",
        f"- NHI211 sandbox: `{payload['nhi211_version']}`",
        f"- Window: cash events with `ex_date >= {payload['sealed_start']}` on FIN `{', '.join(payload['fin_codes'])}`",
        f"- Shares: `{payload['shares_source']}` → `{payload['shares_by_code']}`",
        f"- NHI rule: single gross ≥ NT${payload['nhi_threshold_twd']:,.0f} → "
        f"{payload['nhi_rate'] * 100:.2f}% on full base (cap 10M)",
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"|---|---|",
        f"| Cash events | {payload['n_cash_events']} |",
        f"| Events ≥ NHI threshold | {payload['n_events_above_nhi_threshold']} |",
        f"| Σ gross TAX0 | {payload['sum_gross_tax0']:,.2f} |",
        f"| Σ net NHI211 | {payload['sum_net_nhi211']:,.2f} |",
        f"| Σ NHI premium | {payload['sum_nhi_premium']:,.2f} |",
        f"| Σ delta (NHI − TAX0) | {payload['sum_delta_vs_tax0']:,.2f} |",
        "",
        "## Posture",
        "",
        "- Live DEFAULT remains **TAX0 gross** Stage-E.",
        "- Sandbox NHI211 is cashflow-precision research only.",
        "- Tip history / Soft-Frozen untouched.",
        "",
        f"Peers: `NHI_DIVIDEND_SUPPLEMENTAL_PREMIUM_NOTE.md` · `TAX_FOR_CASHFLOW_PURPOSE.md`",
        "",
        "## Label",
        "",
        "`E22_TAX0_VS_NHI211_OBSERVE__2026-09-20`",
        "",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return md_path, json_path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--shares",
        type=float,
        default=None,
        help="Override all FIN codes to this share count (default: tip portfolio)",
    )
    a = ap.parse_args()
    payload = run_observe(shares_override=a.shares)
    md_path, json_path = write_artifacts(payload)
    print(
        json.dumps(
            {
                "md": str(md_path),
                "json": str(json_path),
                "n_events": payload["n_cash_events"],
                "n_above_threshold": payload["n_events_above_nhi_threshold"],
                "sum_nhi_premium": payload["sum_nhi_premium"],
                "promote_ready": False,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
