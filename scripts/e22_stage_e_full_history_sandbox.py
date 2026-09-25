#!/usr/bin/env python3
"""Stage-E full-history sandbox resim — RESEARCH only (ACCEPT 2026-09-25).

Writes under ``repro/`` only. Never touches Soft-Frozen ``forward/e21``.

Usage:
  python3 scripts/e22_stage_e_full_history_sandbox.py
  python3 scripts/e22_stage_e_full_history_sandbox.py --out-dir repro/stage-e-full-history-sandbox
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import e22_dividend_accounting as e22div
from e50_early_stack_combined_nav import e16_features, simulate_core
from portfolio_capital import DEFAULT_CAPITAL
from tw_share_lots import BOARD_LOT

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "repro" / "stage-e-full-history-sandbox"
MARKET_CANDIDATES = [
    ROOT / "forward/e21/live_market.csv",
    ROOT / "artifact/v412d_12stocks_2010_2026.csv",
]
DIV_PATH = ROOT / "data/dividend_events/e22_dividend_events.csv"


def _load_market() -> pd.DataFrame:
    for p in MARKET_CANDIDATES:
        if p.is_file() and p.stat().st_size > 0:
            df = pd.read_csv(p)
            if "date" in df.columns:
                return df
    raise SystemExit("No market panel found for sandbox resim")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    ap.add_argument(
        "--e22-version",
        default=e22div.DEFAULT_BOOKS_VERSION,
        help="Books version (default Stage-E DEFAULT)",
    )
    args = ap.parse_args()
    out: Path = args.out_dir
    if out.resolve() == (ROOT / "forward" / "e21").resolve() or "forward/e21" in str(
        out.resolve()
    ).replace("\\", "/"):
        raise SystemExit("Refusing to write under forward/e21 — Soft-Frozen KEEP")

    out.mkdir(parents=True, exist_ok=True)
    market = _load_market()
    dividends = pd.read_csv(DIV_PATH, dtype={"code": str})
    _prices, _sleeve, target, regime = e16_features(market)
    nav, fills, meta = simulate_core(
        market,
        target,
        regime,
        dividends,
        apply_e22=True,
        e22_version=str(args.e22_version),
        apply_stock_div=True,
        capital=float(DEFAULT_CAPITAL),
        lot_size=int(BOARD_LOT),
    )
    tip_path = ROOT / "forward/e21/portfolio_state.json"
    tip = json.loads(tip_path.read_text(encoding="utf-8")) if tip_path.is_file() else {}
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "STAGE_E_FULL_HISTORY_SANDBOX",
        "accept": "ACCEPT_RESEARCH_2026-09-25_STAGE_E_FULL_HISTORY_SANDBOX",
        "soft_frozen_keep": True,
        "writes_forward_e21": False,
        "e22_books_version": str(args.e22_version),
        "n_nav_rows": int(len(nav)),
        "n_fills": int(len(fills)),
        "exact_t1_ok": bool(meta.get("exact_t1_ok")),
        "sandbox_last_nav": float(nav["nav"].iloc[-1])
        if len(nav) and "nav" in nav.columns
        else (float(nav.iloc[-1]["nav_e16_e18"]) if len(nav) and "nav_e16_e18" in nav.columns else None),
        "tip_last_date": tip.get("last_date"),
        "tip_last_nav": tip.get("last_nav"),
        "tip_books": tip.get("e22_books_version"),
        "note": "Compare only — tip history not rewritten; method seam is intentional.",
    }
    nav.to_csv(out / "sandbox_nav.csv", index=False)
    pd.DataFrame(fills).to_csv(out / "sandbox_fills.csv", index=False)
    (out / "sandbox_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (out / "README.md").write_text(
        "\n".join(
            [
                "# Stage-E full-history sandbox",
                "",
                f"Generated: `{report['generated_at_utc']}`",
                "Status: **RESEARCH** — Soft-Frozen tip untouched.",
                "",
                f"- Books: `{report['e22_books_version']}`",
                f"- Sandbox last NAV: `{report['sandbox_last_nav']}`",
                f"- Tip last_date / NAV / books: `{report['tip_last_date']}` / `{report['tip_last_nav']}` / `{report['tip_books']}`",
                "",
                "Do not promote sandbox NAV into `forward/e21`.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
