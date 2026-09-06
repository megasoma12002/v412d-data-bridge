#!/usr/bin/env python3
"""E22_v3 Stage B — sealed-window dual-book cash/receivable compare vs DEFAULT.

Paper / sandbox only. Does NOT flip DEFAULT_BOOKS_VERSION or Soft-Frozen.
Combined recv+tax remains NOT STARTED until each axis alone has evidence.

Method:
  Hold a constant 1000-share Soft-Frozen FIN sleeve through sealed_2023_plus.
  Day-walk formal DEFAULT vs each sandbox version; accumulate cash + receivables.
  Wealth = cash + receivable + marked FIN equity (close).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e22_dividend_accounting as formal
import e22_v3_sandbox_books as sandbox
from e16_soft_frozen_base import SOFT_FROZEN_FIN_CLIP
from e45_paper_harness import ROOT, WINDOWS_STANDARD, load_market
from e50_early_stack_combined_nav import FIN

OUT = ROOT / "repro/e22-v3-stage-b-sealed"
OPS = ROOT / "research/ops"
HOLD_SHARES = 1000.0
SEALED_START = WINDOWS_STANDARD["sealed_2023_plus"][0]


def detail_keys(res) -> set[str]:
    keys: set[str] = set()
    for d in res.details or []:
        if isinstance(d, dict) and d.get("key"):
            keys.add(str(d["key"]))
    return keys


def wealth(cash: float, recv: dict, pos: dict, px: dict) -> float:
    equity = sum(float(pos.get(c, 0.0)) * float(px.get(c, 0.0)) for c in pos)
    return float(cash) + float(sum(recv.values())) + equity


def run_book(version: str, events, days: list[str], px_by_day: dict) -> pd.DataFrame:
    pos = {c: HOLD_SHARES for c in FIN}
    cash = 0.0
    recv: dict[str, float] = {}
    skip: set[str] = set()
    rows = []
    for day in days:
        px = px_by_day.get(day, {})
        if version == formal.DEFAULT_BOOKS_VERSION:
            pos, cash, res = formal.apply_dividends_for_date(
                day, pos, cash, events, version=version, skip_keys=skip
            )
            skip |= detail_keys(res)
            recv_sum = 0.0
            recv_credit = 0.0
            settled = 0.0
        else:
            pos, cash, recv, res = sandbox.apply_sandbox_for_date(
                day, pos, cash, recv, events, version=version, skip_keys=skip
            )
            skip |= detail_keys(res)
            recv_sum = float(sum(recv.values()))
            recv_credit = float(res.receivable_credit)
            settled = float(res.receivable_settled)
        rows.append(
            {
                "date": day,
                "version": version,
                "cash": cash,
                "receivable": recv_sum,
                "equity": sum(float(pos.get(c, 0.0)) * float(px.get(c, 0.0)) for c in pos),
                "wealth": wealth(
                    cash,
                    recv if version != formal.DEFAULT_BOOKS_VERSION else {},
                    pos,
                    px,
                ),
                "cash_credit": float(res.cash_credit),
                "receivable_credit": recv_credit,
                "receivable_settled": settled,
                "stock_shares": sum(float(pos.get(c, 0.0)) for c in FIN),
            }
        )
    return pd.DataFrame(rows)


def window_cagr_mdd(nav: pd.Series) -> dict:
    if len(nav) < 2 or float(nav.iloc[0]) <= 0:
        return {"cagr": None, "max_drawdown": None, "n_days": int(len(nav))}
    years = max(len(nav) / 252.0, 1e-9)
    cagr = float((nav.iloc[-1] / nav.iloc[0]) ** (1.0 / years) - 1.0)
    mdd = float((nav / nav.cummax() - 1.0).min())
    return {"cagr": cagr, "max_drawdown": mdd, "n_days": int(len(nav))}


def main() -> int:
    out_o = OUT / "outputs"
    out_r = OUT / "reports"
    for d in (out_o, out_r, OPS):
        d.mkdir(parents=True, exist_ok=True)

    generated = datetime.now(timezone.utc).isoformat()
    market = load_market()
    market = market[market["code"].isin(FIN)].copy()
    market["date"] = pd.to_datetime(market["date"])
    sealed = market[market["date"] >= pd.Timestamp(SEALED_START)].copy()
    if sealed.empty:
        raise SystemExit("no sealed market rows")

    days = sorted(sealed["date"].dt.strftime("%Y-%m-%d").unique().tolist())
    sealed = sealed.assign(day=sealed["date"].dt.strftime("%Y-%m-%d"))
    px_by_day = {
        day: {str(r.code): float(r.close) for r in g.itertuples()}
        for day, g in sealed.groupby("day")
    }

    sealed_start_s = str(SEALED_START)
    events = [
        e
        for e in formal.load_dividend_events()
        if e.code in FIN
        and (
            e.ex_date >= sealed_start_s
            or (str(e.payment_date or "")[:10] >= sealed_start_s)
        )
    ]

    versions = [formal.DEFAULT_BOOKS_VERSION] + sorted(sandbox.SANDBOX_VERSIONS)
    frames: dict[str, pd.DataFrame] = {}
    for ver in versions:
        print(f"run {ver} days={len(days)} events={len(events)}", flush=True)
        df = run_book(ver, events, days, px_by_day)
        frames[ver] = df
        df.to_csv(out_o / f"{ver.replace('.', '_')}_daily_wealth.csv", index=False)

    formal_df = frames[formal.DEFAULT_BOOKS_VERSION]
    base_st = window_cagr_mdd(formal_df["wealth"] / float(formal_df["wealth"].iloc[0]))
    summary_rows = []
    for ver, df in frames.items():
        nav = df["wealth"] / float(df["wealth"].iloc[0])
        st = window_cagr_mdd(nav)
        delta_cagr = None
        delta_mdd = None
        if ver != formal.DEFAULT_BOOKS_VERSION:
            if st["cagr"] is not None and base_st["cagr"] is not None:
                delta_cagr = (st["cagr"] - base_st["cagr"]) * 100.0
            if st["max_drawdown"] is not None and base_st["max_drawdown"] is not None:
                delta_mdd = (abs(base_st["max_drawdown"]) - abs(st["max_drawdown"])) * 100.0
        summary_rows.append(
            {
                "version": ver,
                "sandbox": ver in sandbox.SANDBOX_VERSIONS,
                "end_wealth": float(df["wealth"].iloc[-1]),
                "end_cash": float(df["cash"].iloc[-1]),
                "end_receivable": float(df["receivable"].iloc[-1]),
                "cagr": st["cagr"],
                "max_drawdown": st["max_drawdown"],
                "delta_cagr_pp_vs_default": delta_cagr,
                "delta_mdd_improve_pp_vs_default": delta_mdd,
                "n_days": st["n_days"],
                "live_default_untouched": formal.DEFAULT_BOOKS_VERSION,
            }
        )
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(out_o / "sealed_window_version_summary.csv", index=False)

    lines = [
        "# E22_v3 Stage B — Sealed-Window Dual-Book Compare",
        "",
        f"Generated: `{generated}`",
        "Status: **SANDBOX RESEARCH** — Soft-Frozen **KEEP** · DEFAULT **`E22_v2s_tw` KEEP** · no promote",
        "",
        "## Method",
        "",
        f"- Window: `sealed_2023_plus` from `{SEALED_START}`",
        f"- Constant holdings: {HOLD_SHARES:.0f} shares × Soft-Frozen FIN `{', '.join(FIN)}`",
        "- Wealth = cash + receivable + marked equity",
        f"- Formal path: `{formal.DEFAULT_BOOKS_VERSION}`",
        "- Sandbox paths: `E22_v3_recv_pay` / `E22_v3_tax10` / `E22_v3_tax20`",
        "",
        "## Results vs DEFAULT",
        "",
        "| Version | Sandbox? | End wealth | CAGR | MDD | ΔCAGR pp | ΔMDD improve pp | End recv |",
        "|---|:---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, r in summary.iterrows():
        lines.append(
            f"| `{r['version']}` | {'Y' if r['sandbox'] else 'N'} | {r['end_wealth']:.2f} | "
            f"{'n/a' if r['cagr'] is None else f'{r['cagr']:.2%}'} | "
            f"{'n/a' if r['max_drawdown'] is None else f'{r['max_drawdown']:.2%}'} | "
            f"{'n/a' if r['delta_cagr_pp_vs_default'] is None else f'{r['delta_cagr_pp_vs_default']:+.2f}'} | "
            f"{'n/a' if r['delta_mdd_improve_pp_vs_default'] is None else f'{r['delta_mdd_improve_pp_vs_default']:+.2f}'} | "
            f"{r['end_receivable']:.2f} |"
        )
    lines += [
        "",
        "## Governance",
        "",
        f"- Live DEFAULT remains **`{formal.DEFAULT_BOOKS_VERSION}`** (untouched).",
        "- Soft-Frozen FIN clip **[0.50, 0.95] KEEP**.",
        "- Combined `recv_pay_taxW` still **NOT STARTED** (needs each axis alone first).",
        "- No E45 stitch; no Soft-Frozen / DEFAULT flip; no retired-narrative reinvention.",
        "",
        "## Withholding note",
        "",
        "Tax sandboxes use a **flat haircut** (10%/20%) — resident/non-resident rule must be written before any promote ballot.",
        "",
        f"Label: `E22_V3_STAGE_B_SEALED_{generated[:10]}__DEFAULT_KEEP`",
        "",
    ]
    md = "\n".join(lines)
    (out_r / "E22_V3_STAGE_B_SEALED_COMPARE.md").write_text(md)
    (OPS / "E22_V3_STAGE_B_SEALED_COMPARE.md").write_text(md)

    status = [
        "# E22_v3 Tax / Receivable — Stage B Status (refresh)",
        "",
        f"Date: {generated[:10]}",
        "Ballot: **ACCEPT charter** (human 2026-09-05) — still binding",
        f"Live DEFAULT: **`{formal.DEFAULT_BOOKS_VERSION}`** (untouched)",
        "Soft-Frozen: **[0.50, 0.95] KEEP**",
        "",
        "## Sandbox axes",
        "",
        "| Version | Role | Status |",
        "|---|---|---|",
        "| `E22_v3_recv_pay` | Receivable on ex; cash on pay; TAX0; stock=TW | **SANDBOX OPEN** + sealed compare DONE |",
        "| `E22_v3_tax10` | Ex cash × 0.90; stock=TW | **SANDBOX OPEN** + sealed compare DONE |",
        "| `E22_v3_tax20` | Ex cash × 0.80; stock=TW | **SANDBOX OPEN** + sealed compare DONE |",
        "| `E22_v3_recv_pay_taxW` | Combined | **NOT STARTED** |",
        "",
        "## Latest sealed evidence",
        "",
        "See `research/ops/E22_V3_STAGE_B_SEALED_COMPARE.md`.",
        "",
        "## Explicit non-actions",
        "",
        "- No DEFAULT flip · no Soft-Frozen flip · no forward/e21 rewrite · no E45 stitch",
        "",
        f"Label: `E22_V3_TAX_RECV_STAGE_B_{generated[:10]}__OPEN`",
        "",
    ]
    (OPS / "E22_V3_TAX_RECV_STAGE_B_STATUS.md").write_text("\n".join(status))

    payload = {
        "generated_at_utc": generated,
        "default_books_version": formal.DEFAULT_BOOKS_VERSION,
        "soft_frozen_keep": list(SOFT_FROZEN_FIN_CLIP),
        "sealed_start": str(SEALED_START),
        "hold_shares": HOLD_SHARES,
        "fin_codes": list(FIN),
        "summary": summary_rows,
        "promote_ready": False,
        "combined_recv_tax_started": False,
    }
    (out_o / "stage_b_sealed_summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    (OPS / "E22_V3_STAGE_B_SEALED_SUMMARY.json").write_text(json.dumps(payload, indent=2) + "\n")
    print("DONE Stage B sealed compare", flush=True)
    print(summary.to_string(index=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
