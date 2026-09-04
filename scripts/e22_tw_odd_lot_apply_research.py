#!/usr/bin/env python3
"""Research: how to apply Taiwan odd-lot (畸零股) rules to E22 books.

Compares:
  - E22_v2s           float keep (current formal)
  - E22_v2s_cil       floor + CIL at raw close (prior research mark)
  - E22_v2s_tw        floor + CIL at par NT$10, yuan truncate (TW practice)

Also documents what NOT to model in formal books (拼湊、劃撥費充抵、整股1000).
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from e50_early_stack_combined_nav import ALL, e16_features, nav_stats, simulate_core
import e22_dividend_accounting as e22div

OUT = Path("repro/e22-tw-odd-lot-apply")
REPORT = Path("research/e22/TW_ODD_LOT_APPLY.md")
SUMMARY_JSON = Path("research/e22/TW_ODD_LOT_APPLY.json")


def unit_checks() -> dict:
    """Par CIL: 0.4 share × 10 = 4; 0.05 × 10 = 0.5 → floor 0 yuan."""
    assert e22div.tw_par_cil_cash(0.4) == 4.0
    assert e22div.tw_par_cil_cash(0.05) == 0.0
    assert e22div.tw_par_cil_cash(0.099) == 0.0
    assert e22div.tw_par_cil_cash(0.1) == 1.0

    pos0 = {"2880": 1000.0}
    ev = [
        e22div.DivEvent(code="2880", kind="stock", ex_date="2020-01-02", amount=0.264, payment_date="")
    ]
    # gross=1026.4 → floor 1026, frac 0.4 → par CIL 4
    pos_tw, cash_tw, r_tw = e22div.apply_dividends_for_date(
        "2020-01-02", pos0, 0.0, ev, version=e22div.E22_V2S_TW
    )
    assert pos_tw["2880"] == 1026.0
    assert cash_tw == 4.0
    # market CIL at close=30 → 0.4*30=12
    pos_m, cash_m, r_m = e22div.apply_dividends_for_date(
        "2020-01-02",
        pos0,
        0.0,
        ev,
        version=e22div.E22_V2S_CIL,
        mark_prices={"2880": 30.0},
    )
    assert pos_m["2880"] == 1026.0
    assert abs(cash_m - 12.0) < 1e-9
    return {
        "par_cil_0p4": 4.0,
        "par_cil_0p05": 0.0,
        "example_264pct_par_cil": float(r_tw.cil_cash_credit),
        "example_264pct_mkt30_cil": float(r_m.cil_cash_credit),
        "passed": True,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)
    checks = unit_checks()

    market = pd.read_csv("forward/e21/live_market.csv", dtype={"code": str})
    market["date"] = pd.to_datetime(market["date"])
    required = set(ALL + ["TAIEX"])
    complete = market.groupby("date")["code"].apply(lambda s: required.issubset(set(s)))
    market = market[market["date"].isin(complete[complete].index)].sort_values(["date", "code"])
    dividends = pd.read_csv("data/dividend_events/e22_dividend_events.csv", dtype={"code": str})
    _p, _s, target, regime = e16_features(market)

    specs = [
        ("E22_v2s", e22div.E22_V2S),
        ("E22_v2s_cil", e22div.E22_V2S_CIL),
        ("E22_v2s_tw", e22div.E22_V2S_TW),
    ]
    results = {}
    for name, ver in specs:
        print(f"simulating {name} ...", flush=True)
        nav, fills, meta = simulate_core(
            market,
            target,
            regime,
            dividends,
            apply_e22=True,
            apply_stock_div=True,
            e22_version=ver,
        )
        stats = nav_stats(nav)
        stats["start_nav"] = float(nav["nav"].iloc[0])
        stats["end_nav"] = float(nav["nav"].iloc[-1])
        nav.to_csv(OUT / "outputs" / f"{name.lower()}_daily_nav.csv", index=False)
        end_pos = meta.get("end_positions") or {}
        dust = {k: float(v) - math.floor(float(v)) for k, v in end_pos.items()}
        results[name] = {
            "stats": stats,
            "meta": {
                k: meta.get(k)
                for k in (
                    "e22_books_version",
                    "dividend_cash_total",
                    "cil_cash_total",
                    "fractional_shares_cashed",
                    "stock_div_events",
                    "stock_div_shares_added",
                    "end_positions",
                    "exact_t1_ok",
                    "e22_manifest",
                )
            },
            "end_fractional_dust_total": float(sum(dust.values())),
        }
        print(
            f"  {name}: CAGR={stats['cagr']:.6%} end={stats['end_nav']:.0f} "
            f"cil={meta.get('cil_cash_total')} dust={results[name]['end_fractional_dust_total']:.4f}",
            flush=True,
        )

    base = results["E22_v2s"]["stats"]
    deltas = {}
    for name in ["E22_v2s_cil", "E22_v2s_tw"]:
        st = results[name]["stats"]
        deltas[name] = {
            "cagr_delta_pp": ((st["cagr"] or 0) - (base["cagr"] or 0)) * 100.0,
            "mdd_delta_pp": ((st["max_drawdown"] or 0) - (base["max_drawdown"] or 0)) * 100.0,
            "end_nav_delta": (st["end_nav"] or 0) - (base["end_nav"] or 0),
            "end_nav_ratio": (st["end_nav"] / base["end_nav"]) if base["end_nav"] else None,
            "cil_cash_total": results[name]["meta"].get("cil_cash_total"),
            "fractional_shares_cashed": results[name]["meta"].get("fractional_shares_cashed"),
            "end_dust": results[name]["end_fractional_dust_total"],
        }

    mapping = {
        "layers": [
            {
                "tw_concept": "不足一股畸零股（公司法 §240）",
                "practice": "面額折現（通常 NT$10），元以下捨去；可拼湊整股；剩餘洽特定人",
                "e22_apply": "E22_v2s_tw: floor(shares_gross); cash += floor(frac × 10)",
                "status": "IMPLEMENTED_NAMED_VERSION",
            },
            {
                "tw_concept": "零股交易 1–999 股（證交所零股辦法）",
                "practice": "可持有與買賣非整千股；股利按股數同權",
                "e22_apply": "Keep lot_size=1 fills; do NOT force board_lot_1000 in formal books",
                "status": "KEEP_AS_IS",
            },
            {
                "tw_concept": "整股 1000（主盤交易單位）",
                "practice": "主盤委託單位；非持股必須為 1000 倍數",
                "e22_apply": "E18 capacity challenger only (separate from CIL)",
                "status": "CHALLENGER_ONLY",
            },
            {
                "tw_concept": "拼湊整股視窗 / 劃撥費充抵",
                "practice": "股務作業；未拼湊才折現；款常充抵手續費→實領可近 0",
                "e22_apply": "Optional haircut sensitivity; not default formal books",
                "status": "DEFER",
            },
            {
                "tw_concept": "畸零股現金入帳時點",
                "practice": "股務／發放作業（近 payment），非除權當日市價結算",
                "e22_apply": "Amount fixed at par; credit on stock_ex_date for TR continuity "
                "(optional E22_v3 pay-clock later)",
                "status": "EX_DATE_AMOUNT_OK",
            },
        ],
        "version_ladder": [
            {"id": "E22_v2", "role": "cash-only baseline"},
            {"id": "E22_v2s", "role": "formal float stock shares (current default)"},
            {"id": "E22_v2s_cil", "role": "research: floor + market-close CIL"},
            {"id": "E22_v2s_tw", "role": "TW-practice candidate: floor + par-10 CIL"},
        ],
    }

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "TW_ODD_LOT_APPLY_RESEARCH",
        "governance": {
            "rewrites_live_history": False,
            "changes_default": False,
            "default_remains": e22div.DEFAULT_BOOKS_VERSION,
            "unit_checks": checks,
        },
        "mapping": mapping,
        "variants": results,
        "deltas_vs_v2s": deltas,
        "decision": {
            "recommended_tw_apply": "E22_v2s_tw",
            "why": (
                "Matches Company Act §240 + issuer announcements (par cash for <1 share); "
                "clears fractional dust; does not over-constrain to board lots; "
                "NAV impact vs float v2s is negligible."
            ),
            "vs_market_cil": (
                "E22_v2s_cil overstates odd-lot cash vs TW practice when price >> par; "
                "keep as research sensitivity only."
            ),
            "live_default": "KEEP_E22_v2s_UNTIL_EXPLICIT_PROMOTE_OF_TW",
            "do_not": [
                "Force lot_size=1000 as formal books",
                "Model 拼湊 window as portfolio alpha",
                "Silently replace E22_v2s without new version id",
                "Rewrite forward/e21 history",
            ],
        },
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2, default=str) + "\n")

    lines = [
        "# How to Apply Taiwan Odd-Lot Rules to E22 Books",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        "",
        "**Research.** Default stays `E22_v2s`. No live history rewrite.",
        "",
        "## Taiwan rule map → E22",
        "",
        "| TW concept | Practice | E22 apply | Status |",
        "|---|---|---|---|",
    ]
    for row in mapping["layers"]:
        lines.append(
            f"| {row['tw_concept']} | {row['practice']} | `{row['e22_apply']}` | {row['status']} |"
        )
    lines += [
        "",
        "## Legal / practice anchors",
        "",
        "- **公司法 §240**：盈餘以發行新股分派時，**不滿一股之金額，以現金分派之**。",
        "- **發行人公告慣例**：不足一股按**面額**折現（通常 NT$10），**計算至元、元以下捨去**；"
        "停止過戶前後可拼湊；剩餘洽特定人按面額認購。",
        "- **證交所零股交易辦法**：零股以**1 股**為單位（1–999），與整股（1000）並行；"
        "**持股不必是 1000 倍數**。",
        "",
        "## Named version ladder",
        "",
        "| Version | Role |",
        "|---|---|",
    ]
    for v in mapping["version_ladder"]:
        lines.append(f"| `{v['id']}` | {v['role']} |")
    lines += [
        "",
        "### `E22_v2s_tw` rule (recommended TW apply)",
        "",
        "1. `shares_gross = shares × (1 + stock_dividend/10)`",
        "2. `shares = floor(shares_gross)`",
        "3. `cash += floor(frac × 10)`  ← par, yuan truncate",
        "",
        "Cash dividends unchanged. Exact T+1 unchanged. `lot_size` stays 1 (零股 OK).",
        "",
        "## Side-by-side sensitivity",
        "",
        "| Variant | CAGR | MDD | End NAV | CIL cash | End dust |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name in ["E22_v2s", "E22_v2s_cil", "E22_v2s_tw"]:
        st = results[name]["stats"]
        meta = results[name]["meta"]
        lines.append(
            f"| {name} | {100*(st['cagr'] or 0):.4f}% | {100*(st['max_drawdown'] or 0):.2f}% | "
            f"{st['end_nav']:,.0f} | {meta.get('cil_cash_total') or 0:,.2f} | "
            f"{results[name]['end_fractional_dust_total']:.4f} |"
        )
    lines += [
        "",
        "### Deltas vs E22_v2s",
        "",
    ]
    for name, d in deltas.items():
        lines.append(
            f"- **{name}**: CAGR Δ `{d['cagr_delta_pp']:.4f}` pp; "
            f"end NAV Δ `{d['end_nav_delta']:,.2f}`; "
            f"CIL `{d['cil_cash_total']:,.2f}`; dust `{d['end_dust']:.4f}`"
        )
    lines += [
        "",
        "## Decision",
        "",
        f"- Recommended TW apply: **`{summary['decision']['recommended_tw_apply']}`**",
        f"- Why: {summary['decision']['why']}",
        f"- vs market CIL: {summary['decision']['vs_market_cil']}",
        f"- Live default: `{summary['decision']['live_default']}`",
        "",
        "Do not:",
        "",
    ]
    for x in summary["decision"]["do_not"]:
        lines.append(f"- {x}")
    lines += [
        "",
        "## Code",
        "",
        "- `scripts/e22_dividend_accounting.py` — `E22_v2s_tw`, `tw_par_cil_cash()`",
        "- `scripts/e22_tw_odd_lot_apply_research.py` — this study",
        "- `scripts/e21_forward_pipeline.py` — `--e22-version E22_v2s_tw` selectable",
        "",
        "## Artifacts",
        "",
        f"- `{SUMMARY_JSON}`",
        f"- `{OUT}/`",
        "",
    ]
    REPORT.write_text("\n".join(lines) + "\n")
    print(json.dumps({"deltas_vs_v2s": deltas, "decision": summary["decision"]}, indent=2, default=str))
    print(f"wrote {REPORT}", flush=True)


if __name__ == "__main__":
    main()
