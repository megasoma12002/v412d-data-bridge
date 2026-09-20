#!/usr/bin/env python3
"""Cashflow three-views report — Exact T+1 paper · R4 settled · Stage-E cash+recv.

Human ops priority (2026-09-20): 「計算好現金流的數字」under Soft-Frozen KEEP +
Stage-E TAX0 (dividend personal tax outside daily NAV).

These three numbers must never be merged into one clock:

  A) portfolio_state.cash          — Exact T+1 paper cash (fill day)
  B) settled_cash_estimate         — R4 T+2 liquidity (spendable estimate ≠ NAV)
  C) cash + e22_receivables        — Stage-E dividend timing (TAX0)

Tip lag: while tip books == E22_v2s_tw_effex, (C) has no receivable yet (cash-on-ex).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STAGE_E_DEFAULT = "E22_v3_recv_pay_effdelay"
PRESERVED_CASH_ON_EX = "E22_v2s_tw_effex"
OUT_DIR = ROOT / "research" / "ops"
OUT_JSON = OUT_DIR / "CASHFLOW_THREE_VIEWS_REPORT.json"
OUT_MD = OUT_DIR / "CASHFLOW_THREE_VIEWS_REPORT.md"

# R4 identity: settled ≈ paper - unsettled (float tolerance)
_R4_TOL = 1.0  # NT$1


def _f(x: Any) -> float | None:
    if x is None:
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def receivable_total(state: dict) -> float:
    recv = state.get("e22_receivables") or {}
    if not isinstance(recv, dict):
        return 0.0
    return float(sum(float(v) for v in recv.values()))


def r4_summary(state_dir: Path) -> dict:
    payload = _load_json(state_dir / "settlement_cash_estimate.json")
    if not payload:
        return {"present": False}
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else payload
    paper = _f(summary.get("paper_cash"))
    unsettled = _f(summary.get("unsettled_net"))
    settled = _f(summary.get("settled_cash_estimate"))
    identity_ok = None
    identity_delta = None
    if paper is not None and unsettled is not None and settled is not None:
        identity_delta = paper - unsettled - settled
        identity_ok = abs(identity_delta) <= _R4_TOL
    return {
        "present": True,
        "asof": summary.get("asof"),
        "paper_cash": paper,
        "settled_cash_estimate": settled,
        "unsettled_net": unsettled,
        "settling_today_net": _f(summary.get("settling_today_net")),
        "n_unsettled": summary.get("n_unsettled"),
        "identity_ok": identity_ok,
        "identity_delta": identity_delta,
        "note": summary.get("note")
        or "settled_cash_estimate ≈ paper_cash - unsettled_net; liquidity ≠ NAV",
    }


def build_report(state_dir: Path) -> dict:
    state_dir = state_dir.resolve()
    state = _load_json(state_dir / "portfolio_state.json")
    cash = _f(state.get("cash"))
    books = state.get("e22_books_version")
    last_date = state.get("last_date")
    recv_map = state.get("e22_receivables") if isinstance(state.get("e22_receivables"), dict) else {}
    recv_total = receivable_total(state)
    tip_lag = bool(books and books != STAGE_E_DEFAULT)
    cash_plus_recv = None if cash is None else cash + recv_total

    r4 = r4_summary(state_dir)
    paper_vs_r4 = None
    if cash is not None and r4.get("paper_cash") is not None:
        paper_vs_r4 = cash - float(r4["paper_cash"])

    views = {
        "A_paper_exact_t1": {
            "label_zh": "紙上 Exact T+1 現金（成交日入帳）",
            "label_en": "Exact T+1 paper cash (fill day)",
            "cash": cash,
            "source": "forward/e21/portfolio_state.json → cash",
            "use": "NAV cash leg; NOT spendable custody cash while trades unsettled",
            "not": "do not treat as broker settled balance",
        },
        "B_r4_settled_liquidity": {
            "label_zh": "R4 T+2 已交割流動性估計",
            "label_en": "R4 settled_cash_estimate (T+2 liquidity)",
            "settled_cash_estimate": r4.get("settled_cash_estimate"),
            "unsettled_net": r4.get("unsettled_net"),
            "paper_cash": r4.get("paper_cash"),
            "settling_today_net": r4.get("settling_today_net"),
            "identity_ok": r4.get("identity_ok"),
            "identity_delta": r4.get("identity_delta"),
            "present": r4.get("present"),
            "asof": r4.get("asof"),
            "source": "forward/e21/settlement_cash_estimate.json → summary",
            "use": "spendable / custody liquidity estimate",
            "not": "NOT Soft-Frozen NAV; never merge into portfolio_state.cash",
        },
        "C_stage_e_div_cashflow": {
            "label_zh": "Stage-E 股利現金流（TAX0：應收款→發放日現金）",
            "label_en": "Stage-E dividend cash + receivable (TAX0)",
            "e22_books_version": books,
            "stage_e_default": STAGE_E_DEFAULT,
            "tip_lag": tip_lag,
            "cash": cash,
            "e22_receivables_total": recv_total,
            "e22_receivables_n": len(recv_map or {}),
            "cash_plus_receivable": cash_plus_recv,
            "source": "portfolio_state cash + e22_receivables",
            "use": "dividend timing fidelity for NAV wealth (cash+recv+equity)",
            "not": "personal income tax haircut (ballot A KEEP TAX0 — outside daily books)",
        },
    }

    warnings: list[str] = []
    if tip_lag:
        warnings.append(
            f"TIP_LAG: tip books={books} (preserved cash-on-ex) vs DEFAULT={STAGE_E_DEFAULT}; "
            "View C receivable clock not on tip yet — weekday forward catch-up required"
        )
    if books == PRESERVED_CASH_ON_EX and recv_total == 0.0:
        warnings.append(
            "TIP still cash-on-ex: e22_receivables empty/absent is expected until Stage-E tip"
        )
    if r4.get("present") and r4.get("identity_ok") is False:
        warnings.append(
            f"R4_IDENTITY: |paper - unsettled - settled|={r4.get('identity_delta')} > {_R4_TOL}"
        )
    if paper_vs_r4 is not None and abs(paper_vs_r4) > _R4_TOL:
        warnings.append(
            f"PAPER_CASH_MISMATCH: portfolio_state.cash vs R4.paper_cash delta={paper_vs_r4}"
        )
    if not r4.get("present"):
        warnings.append("R4_MISSING: settlement_cash_estimate.json absent — View B unavailable")

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "CASHFLOW_THREE_VIEWS_REPORT",
        "soft_frozen_keep": True,
        "human_priority": "cashflow_numbers_under_tax0",
        "state_dir": str(state_dir),
        "last_date": last_date,
        "views": views,
        "cross_checks": {
            "paper_cash_minus_r4_paper_cash": paper_vs_r4,
            "r4_identity_ok": r4.get("identity_ok"),
            "tip_lag": tip_lag,
            "stage_e_aligned": (not tip_lag) if books else None,
        },
        "warnings": warnings,
        "next_ops": [
            "Weekday tip → E22_v3_recv_pay_effdelay (Phase 2) so View C receivable lands",
            "Keep R4 daily observe — View B is liquidity SSOT",
            "When custody export exists → R5 reconcile vs View B (observe-only)",
            "Do not merge A/B/C clocks; do not after-tax DEFAULT this cycle",
        ],
        "authority": [
            "research/ops/CASHFLOW_THREE_VIEWS.md",
            "research/ops/TWSE_T2_SETTLEMENT_ESTIMATE_CHARTER.md",
            "research/ops/TWSE_DIVIDEND_CREDIT_DELAY_CHARTER.md",
            "research/ops/ACCEPT_TIP_BOOKS_ALIGN_V3.md",
        ],
    }


def render_md(report: dict) -> str:
    v = report["views"]
    a, b, c = v["A_paper_exact_t1"], v["B_r4_settled_liquidity"], v["C_stage_e_div_cashflow"]
    lines = [
        "# Cashflow three-views report",
        "",
        f"Generated: `{report['generated_at_utc']}`",
        f"Tip `last_date`: `{report.get('last_date')}` · Soft-Frozen **KEEP**",
        f"Human priority: **計算好現金流的數字** (TAX0; tax outside daily NAV)",
        "",
        "## Views",
        "",
        f"| View | Meaning | Number |",
        f"|---|---|---|",
        f"| **A** | Exact T+1 paper cash | `{a.get('cash')}` |",
        f"| **B** | R4 settled_cash_estimate | `{b.get('settled_cash_estimate')}` |",
        f"| **B′** | R4 unsettled_net | `{b.get('unsettled_net')}` |",
        f"| **C** | Stage-E cash | `{c.get('cash')}` |",
        f"| **C′** | e22_receivables total | `{c.get('e22_receivables_total')}` |",
        f"| **C″** | cash + receivable | `{c.get('cash_plus_receivable')}` |",
        "",
        f"- tip books: `{c.get('e22_books_version')}` · tip_lag: **{c.get('tip_lag')}**",
        f"- R4 identity_ok: `{b.get('identity_ok')}` · present: `{b.get('present')}`",
        "",
        "## Warnings",
        "",
    ]
    if report.get("warnings"):
        for w in report["warnings"]:
            lines.append(f"- {w}")
    else:
        lines.append("- None")
    lines += ["", "## Next ops", ""]
    for n in report.get("next_ops") or []:
        lines.append(f"- {n}")
    lines += [
        "",
        "Re-run: `python3 scripts/cashflow_three_views_report.py --write`",
        "",
        "Label: `CASHFLOW_THREE_VIEWS_REPORT`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--state-dir", type=Path, default=ROOT / "forward" / "e21")
    ap.add_argument(
        "--write",
        action="store_true",
        help=f"Write {OUT_JSON.name} / {OUT_MD.name}",
    )
    ap.add_argument(
        "--fail-on-r4-identity",
        action="store_true",
        help="Non-zero exit if R4 paper−unsettled−settled exceeds NT$1",
    )
    args = ap.parse_args()

    report = build_report(args.state_dir)
    text = render_md(report)
    print(text)
    print(json.dumps(report, indent=2, ensure_ascii=False))

    if args.write:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        OUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        OUT_MD.write_text(text, encoding="utf-8")
        print(f"Wrote {OUT_JSON} and {OUT_MD}", file=sys.stderr)

    if args.fail_on_r4_identity:
        ok = report["views"]["B_r4_settled_liquidity"].get("identity_ok")
        if ok is False:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
