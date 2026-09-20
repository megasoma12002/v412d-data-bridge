#!/usr/bin/env python3
"""E22_v3 sandbox books — tax / receivable (charter ACCEPT 2026-09-05).

``E22_v3_recv_pay_effdelay`` is live DEFAULT after Stage-E ACCEPT 2026-09-16
(routed via ``e22_books_apply``). Tax haircut versions remain sandbox-only until
resident/non-resident withholding note is promote-ready.

Named versions:
  E22_v3_recv_pay — receivable on cash ex; cash on payment_date; TAX0; stock = TW odd-lot
  E22_v3_tax10    — ex-date cash × 0.90; stock = TW odd-lot
  E22_v3_tax20    — ex-date cash × 0.80; stock = TW odd-lot
  E22_v3_recv_pay_tax10 — receivable on ex (net of 10%); cash on pay; stock = TW odd-lot
  E22_v3_recv_pay_tax20 — receivable on ex (net of 20%); cash on pay; stock = TW odd-lot
  E22_v3_recv_pay_effdelay — **live DEFAULT** — recv_pay + effective ex/payment snaps
  E22_v3_recv_pay_effdelay_nhi211 — sandbox: Stage-E timing + NHI 2.11% when single
    cash-div credit ≥ NT$20k (cashflow-precision research; not live)

Preserved cash-on-ex formal: ``E22_v2s_tw_effex`` (override with confirm flag).

Receivables dict keys: ``f"{code}:{ex_date}"`` (pending credits; raw ex identity).
Tax purpose (human 2026-09-20): precise **cashflow**, not year-end 所得稅 beauty —
see ``TAX_FOR_CASHFLOW_PURPOSE.md``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Iterable, Sequence

import e22_dividend_accounting as base
from nhi_dividend_supplemental_premium import nhi_dividend_premium
from twse_dividend_delay_estimate import effective_ex_trade, effective_payment

E22_V3_RECV_PAY = "E22_v3_recv_pay"
E22_V3_TAX10 = "E22_v3_tax10"
E22_V3_TAX20 = "E22_v3_tax20"
E22_V3_RECV_PAY_TAX10 = "E22_v3_recv_pay_tax10"
E22_V3_RECV_PAY_TAX20 = "E22_v3_recv_pay_tax20"
E22_V3_RECV_PAY_EFFDELAY = "E22_v3_recv_pay_effdelay"
E22_V3_RECV_PAY_EFFDELAY_NHI211 = "E22_v3_recv_pay_effdelay_nhi211"
SANDBOX_VERSIONS = frozenset(
    {
        E22_V3_RECV_PAY,
        E22_V3_TAX10,
        E22_V3_TAX20,
        E22_V3_RECV_PAY_TAX10,
        E22_V3_RECV_PAY_TAX20,
        E22_V3_RECV_PAY_EFFDELAY,
        E22_V3_RECV_PAY_EFFDELAY_NHI211,
    }
)
TAX_HAIRCUT = {
    E22_V3_TAX10: 0.10,
    E22_V3_TAX20: 0.20,
    E22_V3_RECV_PAY_TAX10: 0.10,
    E22_V3_RECV_PAY_TAX20: 0.20,
}
RECV_PAY_FAMILY = frozenset(
    {
        E22_V3_RECV_PAY,
        E22_V3_RECV_PAY_TAX10,
        E22_V3_RECV_PAY_TAX20,
        E22_V3_RECV_PAY_EFFDELAY,
        E22_V3_RECV_PAY_EFFDELAY_NHI211,
    }
)
EFFDELAY_FAMILY = frozenset({E22_V3_RECV_PAY_EFFDELAY, E22_V3_RECV_PAY_EFFDELAY_NHI211})
NHI211_FAMILY = frozenset({E22_V3_RECV_PAY_EFFDELAY_NHI211})
STOCK_BASE_VERSION = base.E22_V2S_TW


def _net_cash_credit(gross: float, version: str) -> tuple[float, float, float, str]:
    """Return (net_credit, effective_rate, premium_twd, assumption).

    NHI211: premium is applied on **settle** (caller accrues gross receivable).
    Flat taxW sandboxes: haircut on accrual (receivable/cash stores net).
    """
    g = float(gross)
    if version in NHI211_FAMILY:
        r = nhi_dividend_premium(g)
        eff = (r.premium_twd / g) if g > 0 else 0.0
        return (
            float(r.net_cash_twd),
            float(eff),
            float(r.premium_twd),
            "nhi211_threshold_cashflow_precision_on_settle",
        )
    w = float(TAX_HAIRCUT.get(version, 0.0))
    premium = g * w
    if w > 0:
        assumption = (
            "sandbox_flat_withholding_on_receivable; "
            "not NHI rule — see TAX_FOR_CASHFLOW_PURPOSE.md"
        )
    else:
        assumption = "tax0_receivable_effdelay" if version in EFFDELAY_FAMILY else "tax0_receivable"
    return g * (1.0 - w), w, premium, assumption


def _parse_day(raw: str) -> date | None:
    s = str(raw or "").strip()[:10]
    if len(s) != 10:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


def resolve_ex_day(
    ev: base.DivEvent,
    *,
    use_effective: bool,
    sessions: Sequence[date] | None,
) -> str:
    raw = str(ev.ex_date or "")[:10]
    if not use_effective or not sessions:
        return raw
    d = _parse_day(raw)
    if d is None:
        return raw
    return effective_ex_trade(d, sessions).isoformat()


def resolve_pay_day(
    ev: base.DivEvent,
    *,
    use_effective: bool,
    settlements: Sequence[date] | None,
    mops_amendments: dict[tuple[str, str], str] | None = None,
) -> str:
    raw = str(ev.payment_date or "")[:10]
    mops_amd: date | None = None
    if mops_amendments and raw:
        from e22_mops_payment_amendments import lookup_amendment

        mops_amd = lookup_amendment(mops_amendments, ev.code, raw)
    if mops_amd is not None:
        return mops_amd.isoformat()
    if not use_effective or not settlements:
        return raw
    d = _parse_day(raw)
    if d is None:
        return raw
    return effective_payment(d, settlements).isoformat()


@dataclass
class SandboxApplyResult:
    cash_credit: float = 0.0
    receivable_credit: float = 0.0
    receivable_settled: float = 0.0
    stock_shares_added: float = 0.0
    cil_cash_credit: float = 0.0
    tax_haircut_rate: float = 0.0
    cash_events: int = 0
    settle_events: int = 0
    stock_events: int = 0
    details: list = field(default_factory=list)
    sandbox_version: str = ""
    default_untouched: str = base.DEFAULT_BOOKS_VERSION


def _pending_key(code: str, ex_date: str) -> str:
    return f"{code}:{str(ex_date)[:10]}"


def apply_sandbox_for_date(
    day: str,
    positions: dict[str, float],
    cash: float,
    receivables: dict[str, float],
    events: Iterable[base.DivEvent],
    *,
    version: str,
    skip_keys: set[str] | None = None,
    par_table: dict[str, float] | None = None,
    session_dates: Sequence[date] | None = None,
    settlement_dates: Sequence[date] | None = None,
    mops_amendments: dict[tuple[str, str], str] | None = None,
    entitlement_positions: dict[str, float] | None = None,
) -> tuple[dict[str, float], float, dict[str, float], SandboxApplyResult]:
    """Apply one sandbox books day. Never mutates live DEFAULT semantics.

    ``E22_v3_recv_pay_effdelay`` accrues / settles on effective ex / payment
    (needs ``session_dates`` / ``settlement_dates``; outside calendar → raw).
    Optional ``mops_amendments`` overlay wins on payment (D4).

    ``entitlement_positions`` (optional) is the share map for cash/stock credits;
    defaults to ``positions``. Stock path applies entitlement-based delta onto
    current books positions.
    """
    if version not in SANDBOX_VERSIONS:
        raise ValueError(f"not a Stage-B sandbox version: {version}")

    day = str(day)[:10]
    skip = set(skip_keys or ())
    events_list = list(events)
    pos = {k: float(v) for k, v in positions.items()}
    ent = (
        {k: float(v) for k, v in entitlement_positions.items()}
        if entitlement_positions is not None
        else pos
    )
    cash_out = float(cash)
    recv = {k: float(v) for k, v in receivables.items()}
    out = SandboxApplyResult(sandbox_version=version)
    use_eff = version in EFFDELAY_FAMILY

    if version in RECV_PAY_FAMILY:
        # Flat sandbox taxW rate for metadata; NHI211 uses per-event threshold.
        w_meta = float(TAX_HAIRCUT.get(version, 0.0))
        if version in NHI211_FAMILY:
            w_meta = 0.0211
        out.tax_haircut_rate = w_meta
        # Ex-date (raw or effective): accrue receivable
        for ev in events_list:
            if ev.kind != "cash":
                continue
            ex_match = resolve_ex_day(
                ev, use_effective=use_eff, sessions=session_dates
            )
            if ex_match != day:
                continue
            if not str(ev.payment_date or "").strip():
                raise ValueError(
                    f"blank payment_date for recv_pay cash event "
                    f"code={ev.code!r} ex_date={ev.ex_date!r}"
                )
            key = f"cash:{ev.code}:{ev.ex_date}"
            if key in skip:
                continue
            sh = float(ent.get(ev.code, 0.0) or 0.0)
            if sh <= 0:
                continue
            gross = sh * float(ev.amount)
            if version in NHI211_FAMILY:
                # Accrue gross; NHI premium applied on settle.
                credit = gross
                eff_rate = 0.0
                premium = 0.0
                assumption = "nhi211_gross_receivable_premium_on_settle"
            else:
                credit, eff_rate, premium, assumption = _net_cash_credit(gross, version)
            pk = _pending_key(ev.code, ev.ex_date)
            recv[pk] = float(recv.get(pk, 0.0) or 0.0) + credit
            out.receivable_credit += credit
            out.cash_events += 1
            out.details.append(
                {
                    "key": key,
                    "kind": "cash_receivable",
                    "code": ev.code,
                    "ex_date": ev.ex_date,
                    "effective_ex_trade": ex_match,
                    "payment_date": ev.payment_date,
                    "pending_key": pk,
                    "gross_credit": gross,
                    "tax_haircut_rate": eff_rate,
                    "premium_twd": premium,
                    "receivable_credit": credit,
                    "cash_credit": 0.0,
                    "assumption": assumption,
                    "version": version,
                }
            )

        # Payment-date (raw or effective): settle pending receivable → cash
        for ev in events_list:
            if ev.kind != "cash":
                continue
            pay = resolve_pay_day(
                ev,
                use_effective=use_eff,
                settlements=settlement_dates,
                mops_amendments=mops_amendments if use_eff else None,
            )
            if not pay or pay != day:
                continue
            pk = _pending_key(ev.code, ev.ex_date)
            settle_key = f"settle:{pk}:{pay}"
            if settle_key in skip:
                continue
            credit = float(recv.get(pk, 0.0) or 0.0)
            if credit <= 0:
                continue
            recv[pk] = 0.0
            settle_detail: dict = {
                "key": settle_key,
                "kind": "cash_settle",
                "code": ev.code,
                "ex_date": ev.ex_date,
                "payment_date": ev.payment_date,
                "effective_payment": pay,
                "pending_key": pk,
                "tax_haircut_rate": w_meta,
                "version": version,
            }
            if version in NHI211_FAMILY:
                net, eff_rate, premium, assumption = _net_cash_credit(credit, version)
                cash_out += net
                out.cash_credit += net
                out.receivable_settled += credit
                settle_detail.update(
                    {
                        "gross_credit": credit,
                        "cash_credit": net,
                        "premium_twd": premium,
                        "tax_haircut_rate": eff_rate,
                        "assumption": assumption,
                    }
                )
            else:
                cash_out += credit
                out.cash_credit += credit
                out.receivable_settled += credit
                settle_detail["cash_credit"] = credit
            out.settle_events += 1
            out.details.append(settle_detail)
    else:
        w = float(TAX_HAIRCUT[version])
        out.tax_haircut_rate = w
        for ev in base.events_on_date(events_list, day):
            if ev.kind != "cash":
                continue
            key = f"cash:{ev.code}:{ev.ex_date}"
            if key in skip:
                continue
            sh = float(ent.get(ev.code, 0.0) or 0.0)
            if sh <= 0:
                continue
            gross = sh * float(ev.amount)
            net = gross * (1.0 - w)
            cash_out += net
            out.cash_credit += net
            out.cash_events += 1
            out.details.append(
                {
                    "key": key,
                    "kind": "cash_taxed",
                    "code": ev.code,
                    "ex_date": ev.ex_date,
                    "payment_date": ev.payment_date,
                    "gross_credit": gross,
                    "tax_haircut_rate": w,
                    "cash_credit": net,
                    "assumption": (
                        "sandbox_flat_withholding; "
                        "resident/non-resident rule must be written before promote"
                    ),
                    "version": version,
                }
            )

    # Stock axis: reuse promoted TW odd-lot formal path (cash/CIL only from stock).
    # Effdelay family snaps stock books to effective_ex_trade as well.
    stock_ver = base.E22_V2S_TW_EFFEX if use_eff else STOCK_BASE_VERSION
    stock_only = [e for e in events_list if e.kind == "stock"]
    pos, cash_out, stock_res = base.apply_dividends_for_date(
        day,
        pos,
        cash_out,
        stock_only,
        version=stock_ver,
        skip_keys=skip,
        par_table=par_table,
        session_dates=session_dates if use_eff else None,
        entitlement_positions=ent,
    )
    out.stock_shares_added += float(stock_res.stock_shares_added)
    out.cil_cash_credit += float(stock_res.cil_cash_credit)
    out.cash_credit += float(stock_res.cil_cash_credit)
    out.stock_events += int(stock_res.stock_events)
    out.details.extend(list(stock_res.details or []))

    recv = {k: v for k, v in recv.items() if abs(float(v)) > 1e-12}
    return pos, cash_out, recv, out


def version_manifest(version: str) -> dict:
    if version not in SANDBOX_VERSIONS:
        raise ValueError(version)
    cash_timing = "receivable_on_ex_cash_on_pay"
    if version in EFFDELAY_FAMILY:
        cash_timing = "receivable_on_effective_ex_cash_on_effective_pay"
    elif version not in RECV_PAY_FAMILY:
        cash_timing = "cash_ex_date_net_of_sandbox_withholding"
    stock_path = base.E22_V2S_TW_EFFEX if version in EFFDELAY_FAMILY else STOCK_BASE_VERSION
    return {
        "sandbox": True,
        "e22_books_version": version,
        "live_default_untouched": base.DEFAULT_BOOKS_VERSION,
        "soft_frozen_unchanged": True,
        "cash_timing": cash_timing,
        "tax_haircut": (
            0.0211 if version in NHI211_FAMILY else TAX_HAIRCUT.get(version, 0.0)
        ),
        "nhi211_threshold": version in NHI211_FAMILY,
        "stock_path": stock_path,
        "combined_recv_tax": version in {E22_V3_RECV_PAY_TAX10, E22_V3_RECV_PAY_TAX20},
        "effdelay": version in EFFDELAY_FAMILY,
        "promote_ready": False if version in NHI211_FAMILY else (version == E22_V3_RECV_PAY_EFFDELAY),
        "stage_e_live_default": version == E22_V3_RECV_PAY_EFFDELAY,
        "cashflow_precision_sandbox": version in NHI211_FAMILY,
        "charter": "research/ops/FORMAL_TAX_RECEIVABLE_BOOKS_CHARTER.md",
        "delay_charter": "research/ops/TWSE_DIVIDEND_CREDIT_DELAY_CHARTER.md",
        "tax_purpose": "research/ops/TAX_FOR_CASHFLOW_PURPOSE.md",
        "ballot": "ACCEPT Stage-E promote 2026-09-16",
    }


def smoke_compare() -> dict:
    """Tiny dual-book smoke vs DEFAULT on one known cash event (2880 2010)."""
    from pathlib import Path

    from twse_session_sources import (
        DEFAULT_CALENDAR_DIR,
        read_calendar_csv,
        session_dates,
        settlement_dates,
    )

    events = [
        e
        for e in base.load_dividend_events()
        if e.code == "2880" and e.kind == "cash" and e.ex_date.startswith("2010-")
    ]
    if not events:
        return {"ok": False, "reason": "no 2880 2010 cash events"}
    ev = events[0]
    pos0 = {"2880": 1000.0}
    cash0 = 0.0
    cal_path = DEFAULT_CALENDAR_DIR / "twse_sessions_2026.csv"
    sessions = settlements = None
    if Path(cal_path).exists():
        cal = read_calendar_csv(cal_path)
        sessions = session_dates(cal)
        settlements = settlement_dates(cal)

    # Preserved cash-on-ex formal path (D5), not live DEFAULT after Stage-E
    formal_ver = base.PRESERVED_CASH_ON_EX
    pos_f, cash_f, res_f = base.apply_dividends_for_date(
        ev.ex_date, pos0, cash0, [ev], version=formal_ver
    )

    rows = {
        "formal_preserved_effex": {
            "version": formal_ver,
            "cash_after_ex": cash_f,
            "cash_credit": res_f.cash_credit,
            "receivable": 0.0,
        }
    }
    for ver in sorted(SANDBOX_VERSIONS):
        pos_s, cash_s, recv_s, res_s = apply_sandbox_for_date(
            ev.ex_date,
            pos0,
            cash0,
            {},
            [ev],
            version=ver,
            session_dates=sessions,
            settlement_dates=settlements,
        )
        cash_pay = cash_s
        recv_pay = dict(recv_s)
        if ver in RECV_PAY_FAMILY and ev.payment_date:
            pos_s, cash_pay, recv_pay, res_pay = apply_sandbox_for_date(
                ev.payment_date,
                pos_s,
                cash_s,
                recv_s,
                [ev],
                version=ver,
                session_dates=sessions,
                settlement_dates=settlements,
            )
            settled = res_pay.receivable_settled
        else:
            settled = 0.0
        rows[ver] = {
            "version": ver,
            "cash_after_ex": cash_s,
            "receivable_after_ex": sum(recv_s.values()),
            "cash_after_pay": cash_pay,
            "receivable_after_pay": sum(recv_pay.values()),
            "settled": settled,
            "tax_haircut_rate": res_s.tax_haircut_rate,
            "manifest": version_manifest(ver),
        }

    formal_credit = float(res_f.cash_credit)
    tax10_net = formal_credit * 0.90
    tax20_net = formal_credit * 0.80
    checks = {
        "default_untouched": base.DEFAULT_BOOKS_VERSION
        in (base.E22_V3_RECV_PAY_EFFDELAY, base.E22_V2S_TW_EFFEX, base.E22_V2S_TW),
        "default_is_recv_effdelay": base.DEFAULT_BOOKS_VERSION
        == base.E22_V3_RECV_PAY_EFFDELAY,
        "recv_ex_cash_zero": abs(rows[E22_V3_RECV_PAY]["cash_after_ex"]) < 1e-9,
        "recv_ex_receivable_eq_formal": abs(
            rows[E22_V3_RECV_PAY]["receivable_after_ex"] - formal_credit
        )
        < 1e-9,
        "recv_pay_clears": abs(rows[E22_V3_RECV_PAY]["receivable_after_pay"]) < 1e-9,
        "recv_pay_cash_eq_formal": abs(
            rows[E22_V3_RECV_PAY]["cash_after_pay"] - formal_credit
        )
        < 1e-9,
        "tax10_net": abs(rows[E22_V3_TAX10]["cash_after_ex"] - tax10_net) < 1e-9,
        "tax20_net": abs(rows[E22_V3_TAX20]["cash_after_ex"] - tax20_net) < 1e-9,
        "recv_tax10_ex_recv_eq_net": abs(
            rows[E22_V3_RECV_PAY_TAX10]["receivable_after_ex"] - tax10_net
        )
        < 1e-9,
        "recv_tax10_pay_cash_eq_net": abs(
            rows[E22_V3_RECV_PAY_TAX10]["cash_after_pay"] - tax10_net
        )
        < 1e-9,
        "recv_tax20_ex_recv_eq_net": abs(
            rows[E22_V3_RECV_PAY_TAX20]["receivable_after_ex"] - tax20_net
        )
        < 1e-9,
        "recv_tax20_pay_cash_eq_net": abs(
            rows[E22_V3_RECV_PAY_TAX20]["cash_after_pay"] - tax20_net
        )
        < 1e-9,
        # 2010 outside 2026 calendar → effdelay behaves like raw recv_pay
        "effdelay_matches_recv_pay": abs(
            rows[E22_V3_RECV_PAY_EFFDELAY]["cash_after_pay"]
            - rows[E22_V3_RECV_PAY]["cash_after_pay"]
        )
        < 1e-9
        and abs(
            rows[E22_V3_RECV_PAY_EFFDELAY]["receivable_after_ex"]
            - rows[E22_V3_RECV_PAY]["receivable_after_ex"]
        )
        < 1e-9,
    }
    return {
        "ok": all(checks.values()),
        "event": {
            "code": ev.code,
            "ex_date": ev.ex_date,
            "payment_date": ev.payment_date,
            "amount": ev.amount,
            "shares": 1000.0,
            "formal_gross": formal_credit,
        },
        "checks": checks,
        "rows": rows,
        "soft_frozen_keep": True,
        "default_books_version": base.DEFAULT_BOOKS_VERSION,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(smoke_compare(), indent=2, ensure_ascii=False))
