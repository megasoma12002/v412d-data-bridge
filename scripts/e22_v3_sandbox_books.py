#!/usr/bin/env python3
"""E22_v3 sandbox books — tax / receivable Stage B (charter ACCEPT 2026-09-05).

Research / sandbox only. Soft-Frozen KEEP.
``DEFAULT_BOOKS_VERSION`` stays ``E22_v2s_tw`` — this module never flips it.

Named sandbox versions (charter):
  E22_v3_recv_pay — receivable on cash ex; cash on payment_date; TAX0; stock = TW odd-lot
  E22_v3_tax10    — ex-date cash × 0.90; stock = TW odd-lot
  E22_v3_tax20    — ex-date cash × 0.80; stock = TW odd-lot

Combined recv+tax is intentionally NOT implemented until each axis alone has evidence.

Receivables dict keys: ``f"{code}:{ex_date}"`` (pending gross credits).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

import e22_dividend_accounting as base

E22_V3_RECV_PAY = "E22_v3_recv_pay"
E22_V3_TAX10 = "E22_v3_tax10"
E22_V3_TAX20 = "E22_v3_tax20"
SANDBOX_VERSIONS = frozenset({E22_V3_RECV_PAY, E22_V3_TAX10, E22_V3_TAX20})
TAX_HAIRCUT = {E22_V3_TAX10: 0.10, E22_V3_TAX20: 0.20}
STOCK_BASE_VERSION = base.E22_V2S_TW


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
) -> tuple[dict[str, float], float, dict[str, float], SandboxApplyResult]:
    """Apply one sandbox books day. Never mutates live DEFAULT semantics."""
    if version not in SANDBOX_VERSIONS:
        raise ValueError(f"not a Stage-B sandbox version: {version}")

    day = str(day)[:10]
    skip = set(skip_keys or ())
    events_list = list(events)
    pos = {k: float(v) for k, v in positions.items()}
    cash_out = float(cash)
    recv = {k: float(v) for k, v in receivables.items()}
    out = SandboxApplyResult(sandbox_version=version)

    if version == E22_V3_RECV_PAY:
        # Ex-date: accrue receivable (not spendable cash)
        for ev in base.events_on_date(events_list, day):
            if ev.kind != "cash":
                continue
            key = f"cash:{ev.code}:{ev.ex_date}"
            if key in skip:
                continue
            sh = float(pos.get(ev.code, 0.0) or 0.0)
            if sh <= 0:
                continue
            gross = sh * float(ev.amount)
            pk = _pending_key(ev.code, ev.ex_date)
            recv[pk] = float(recv.get(pk, 0.0) or 0.0) + gross
            out.receivable_credit += gross
            out.cash_events += 1
            out.details.append(
                {
                    "key": key,
                    "kind": "cash_receivable",
                    "code": ev.code,
                    "ex_date": ev.ex_date,
                    "payment_date": ev.payment_date,
                    "pending_key": pk,
                    "gross_credit": gross,
                    "cash_credit": 0.0,
                    "version": version,
                }
            )

        # Payment-date: settle pending receivable → cash
        for ev in events_list:
            if ev.kind != "cash":
                continue
            pay = str(ev.payment_date or "")[:10]
            if not pay or pay != day:
                continue
            pk = _pending_key(ev.code, ev.ex_date)
            settle_key = f"settle:{pk}:{pay}"
            if settle_key in skip:
                continue
            gross = float(recv.get(pk, 0.0) or 0.0)
            if gross <= 0:
                continue
            recv[pk] = 0.0
            cash_out += gross
            out.cash_credit += gross
            out.receivable_settled += gross
            out.settle_events += 1
            out.details.append(
                {
                    "key": settle_key,
                    "kind": "cash_settle",
                    "code": ev.code,
                    "ex_date": ev.ex_date,
                    "payment_date": pay,
                    "pending_key": pk,
                    "cash_credit": gross,
                    "version": version,
                }
            )
    else:
        w = float(TAX_HAIRCUT[version])
        out.tax_haircut_rate = w
        for ev in base.events_on_date(events_list, day):
            if ev.kind != "cash":
                continue
            key = f"cash:{ev.code}:{ev.ex_date}"
            if key in skip:
                continue
            sh = float(pos.get(ev.code, 0.0) or 0.0)
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

    # Stock axis: reuse promoted TW odd-lot formal path (cash/CIL only from stock)
    stock_only = [e for e in events_list if e.kind == "stock"]
    pos, cash_out, stock_res = base.apply_dividends_for_date(
        day,
        pos,
        cash_out,
        stock_only,
        version=STOCK_BASE_VERSION,
        skip_keys=skip,
        par_table=par_table,
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
    return {
        "sandbox": True,
        "e22_books_version": version,
        "live_default_untouched": base.DEFAULT_BOOKS_VERSION,
        "soft_frozen_unchanged": True,
        "cash_timing": (
            "receivable_on_ex_cash_on_pay"
            if version == E22_V3_RECV_PAY
            else "cash_ex_date_net_of_sandbox_withholding"
        ),
        "tax_haircut": TAX_HAIRCUT.get(version, 0.0),
        "stock_path": STOCK_BASE_VERSION,
        "combined_recv_tax": False,
        "promote_ready": False,
        "charter": "research/ops/FORMAL_TAX_RECEIVABLE_BOOKS_CHARTER.md",
        "ballot": "ACCEPT charter 2026-09-05",
    }


def smoke_compare() -> dict:
    """Tiny dual-book smoke vs DEFAULT on one known cash event (2880 2010)."""
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

    # Formal default path
    pos_f, cash_f, res_f = base.apply_dividends_for_date(
        ev.ex_date, pos0, cash0, [ev], version=base.DEFAULT_BOOKS_VERSION
    )

    rows = {
        "formal_default": {
            "version": base.DEFAULT_BOOKS_VERSION,
            "cash_after_ex": cash_f,
            "cash_credit": res_f.cash_credit,
            "receivable": 0.0,
        }
    }
    for ver in sorted(SANDBOX_VERSIONS):
        pos_s, cash_s, recv_s, res_s = apply_sandbox_for_date(
            ev.ex_date, pos0, cash0, {}, [ev], version=ver
        )
        cash_pay = cash_s
        recv_pay = dict(recv_s)
        if ver == E22_V3_RECV_PAY and ev.payment_date:
            pos_s, cash_pay, recv_pay, res_pay = apply_sandbox_for_date(
                ev.payment_date, pos_s, cash_s, recv_s, [ev], version=ver
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
        "default_untouched": base.DEFAULT_BOOKS_VERSION == base.E22_V2S_TW,
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
