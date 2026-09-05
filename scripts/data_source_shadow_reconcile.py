#!/usr/bin/env python3
"""Data-source shadow reconcile — Phase B (OPS / RESEARCH only).

Three shadow checks (never overwrite formal ledgers / live history):
  1) TAIEX: live_market (FinMind path) vs Yahoo ^TWII  [daily *returns*]
  2) Dividend cash amounts: e22 ledger vs Yahoo TW quote pages  [flag-only]
  3) Fin sleeve recent closes: live_market vs Yahoo .TW

Emits:
  research/ops/DATA_SOURCE_SHADOW_RECONCILE.{json,md}
  repro/data-source-shadow/*.csv

Soft-Frozen unchanged. No live-wire. No forward/e21 rewrite.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "research/ops"
REPRO = ROOT / "repro/data-source-shadow"
LIVE_MKT = ROOT / "forward/e21/live_market.csv"
DIV_PATH = ROOT / "data/dividend_events/e22_dividend_events.csv"

FIN_SLEEVE = ["2880", "2886", "2892", "5880"]
ALL_STOCKS = FIN_SLEEVE + ["2412", "3045", "4904", "0050"]

sys.path.insert(0, str(ROOT / "scripts"))
from e22_backfill_payment_dates_yahoo import get as yahoo_get  # noqa: E402
from e22_backfill_payment_dates_yahoo import parse_yahoo  # noqa: E402

try:
    import yfinance as yf
except ImportError:  # pragma: no cover
    yf = None


def load_live() -> pd.DataFrame:
    d = pd.read_csv(LIVE_MKT, dtype={"code": str})
    d["date"] = pd.to_datetime(d["date"]).dt.strftime("%Y-%m-%d")
    d["close"] = pd.to_numeric(d["close"], errors="coerce")
    return d


def yahoo_ohlcv(symbol: str, start: str) -> pd.DataFrame:
    if yf is None:
        raise RuntimeError("yfinance not installed")
    d = yf.download(symbol, start=start, auto_adjust=False, progress=False, threads=False)
    if d is None or d.empty:
        return pd.DataFrame(columns=["date", "close"])
    if isinstance(d.columns, pd.MultiIndex):
        d.columns = d.columns.get_level_values(0)
    out = d.reset_index().rename(columns={"Date": "date", "Close": "close"})
    out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
    out["close"] = pd.to_numeric(out["close"], errors="coerce")
    return out[["date", "close"]].dropna()


def reconcile_taiex(live: pd.DataFrame, lookback_days: int) -> dict:
    asof = str(live["date"].max())
    start = (pd.Timestamp(asof) - pd.Timedelta(days=lookback_days)).strftime("%Y-%m-%d")
    prim = live[live["code"] == "TAIEX"][["date", "close"]].rename(columns={"close": "close_live"})
    prim = prim[prim["date"] >= start]
    y = yahoo_ohlcv("^TWII", start=start).rename(columns={"close": "close_yahoo"})
    m = prim.merge(y, on="date", how="inner").sort_values("date")
    if m.empty:
        return {
            "id": "taiex",
            "status": "NO_OVERLAP",
            "ok": False,
            "n_overlap": 0,
            "note": "no overlapping TAIEX/^TWII dates in lookback",
        }
    m["ret_live"] = m["close_live"].pct_change()
    m["ret_yahoo"] = m["close_yahoo"].pct_change()
    path = REPRO / "taiex_live_vs_yahoo.csv"
    m.to_csv(path, index=False)
    rr = m.dropna(subset=["ret_live", "ret_yahoo"])
    ret_corr = float(rr["ret_live"].corr(rr["ret_yahoo"])) if len(rr) > 3 else None
    ret_mae = float((rr["ret_live"] - rr["ret_yahoo"]).abs().mean()) if len(rr) else None
    ok = ret_mae is not None and ret_mae <= 0.005 and ret_corr is not None and ret_corr >= 0.95
    return {
        "id": "taiex",
        "status": "PASS" if ok else "DRIFT",
        "ok": bool(ok),
        "n_overlap": int(len(m)),
        "start": start,
        "asof": asof,
        "ret_corr": ret_corr,
        "ret_mae": ret_mae,
        "detail_csv": str(path.relative_to(ROOT)),
        "thresholds": {"ret_mae_max": 0.005, "ret_corr_min": 0.95},
        "note": "Compare daily returns; ^TWII levels may differ from FinMind TAIEX",
    }


def reconcile_div_amounts(rel_tol: float = 0.02, abs_tol: float = 0.02) -> dict:
    if not DIV_PATH.exists():
        return {"id": "dividend_amount", "status": "MISSING_LEDGER", "ok": False}
    led = pd.read_csv(DIV_PATH, dtype={"code": str})
    yahoo_rows: list[dict] = []
    errors: list[str] = []
    codes = sorted(set(ALL_STOCKS) & set(led["code"].astype(str).unique()))
    for code in codes:
        try:
            html = yahoo_get(f"https://tw.stock.yahoo.com/quote/{code}.TW/dividend")
            yahoo_rows.extend(parse_yahoo(code, html))
            time.sleep(0.35)
        except Exception as ex:  # noqa: BLE001
            errors.append(f"{code}:{type(ex).__name__}:{ex}")
    ydf = pd.DataFrame(yahoo_rows)
    if ydf.empty:
        return {
            "id": "dividend_amount",
            "status": "YAHOO_EMPTY",
            "ok": False,
            "fetch_errors": errors,
        }
    # parse_yahoo fields: cash_ex_date, cash_dividend
    ycash = ydf.copy()
    ycash["cash_ex_date"] = ycash.get("cash_ex_date", pd.Series(dtype=str)).astype(str)
    if "cash_dividend" not in ycash.columns:
        return {
            "id": "dividend_amount",
            "status": "YAHOO_SCHEMA",
            "ok": False,
            "yahoo_cols": list(ydf.columns),
            "fetch_errors": errors,
        }
    ycash["cash_dividend_y"] = pd.to_numeric(ycash["cash_dividend"], errors="coerce")
    ycash = ycash[ycash["cash_ex_date"].str.len() >= 8].dropna(subset=["cash_dividend_y"])
    ycash = ycash[ycash["cash_dividend_y"] > 0]

    led_c = led.copy()
    # ledger column names
    ex_col = "cash_ex_date" if "cash_ex_date" in led_c.columns else None
    amt_col = "cash_dividend" if "cash_dividend" in led_c.columns else None
    if ex_col is None or amt_col is None:
        return {
            "id": "dividend_amount",
            "status": "LEDGER_SCHEMA",
            "ok": False,
            "ledger_cols": list(led.columns),
        }
    led_c[ex_col] = led_c[ex_col].astype(str)
    led_c[amt_col] = pd.to_numeric(led_c[amt_col], errors="coerce")
    led_c = led_c[(led_c[ex_col].str.len() >= 8) & (led_c[amt_col] > 0)]
    led_c = led_c.rename(columns={ex_col: "cash_ex_date", amt_col: "cash_dividend"})

    m = led_c.merge(
        ycash[["code", "cash_ex_date", "cash_dividend_y"]],
        on=["code", "cash_ex_date"],
        how="inner",
    )
    if m.empty:
        return {
            "id": "dividend_amount",
            "status": "NO_OVERLAP",
            "ok": False,
            "n_yahoo_rows": int(len(ycash)),
            "fetch_errors": errors,
        }
    m["abs_diff"] = (m["cash_dividend"] - m["cash_dividend_y"]).abs()
    m["rel_diff"] = (m["cash_dividend"] - m["cash_dividend_y"]) / m["cash_dividend_y"].replace(0, np.nan)
    m["flag"] = (m["abs_diff"] > abs_tol) & (m["rel_diff"].abs() > rel_tol)
    path = REPRO / "dividend_amount_live_vs_yahoo.csv"
    m.to_csv(path, index=False)
    n_flag = int(m["flag"].sum())
    return {
        "id": "dividend_amount",
        "status": "PASS" if n_flag == 0 else "DRIFT",
        "ok": n_flag == 0,
        "n_overlap": int(len(m)),
        "n_flagged": n_flag,
        "max_abs_diff": float(m["abs_diff"].max()),
        "max_abs_rel_diff": float(m["rel_diff"].abs().max()),
        "thresholds": {"abs_tol": abs_tol, "rel_tol": rel_tol},
        "fetch_errors": errors,
        "detail_csv": str(path.relative_to(ROOT)),
        "note": "Flag-only; does not rewrite e22_dividend_events.csv",
    }


def reconcile_fin_recent(
    live: pd.DataFrame,
    lookback_days: int,
    rel_tol_level: float = 0.03,
    ret_mae_max: float = 0.005,
    ret_corr_min: float = 0.95,
) -> dict:
    """Shadow Fin sleeve vs Yahoo.

    Levels may differ (raw vs adj). Gate on *daily returns* like TAIEX;
    report level diffs as informational.
    """
    asof = str(live["date"].max())
    start = (pd.Timestamp(asof) - pd.Timedelta(days=lookback_days)).strftime("%Y-%m-%d")
    rows = []
    errors: list[str] = []
    for code in FIN_SLEEVE:
        prim = live[(live["code"] == code) & (live["date"] >= start)][["date", "close"]].rename(
            columns={"close": "close_live"}
        )
        try:
            y = yahoo_ohlcv(f"{code}.TW", start=start).rename(columns={"close": "close_yahoo"})
        except Exception as ex:  # noqa: BLE001
            errors.append(f"{code}:{type(ex).__name__}:{ex}")
            continue
        m = prim.merge(y, on="date", how="inner").sort_values("date")
        if len(m) < 5:
            continue
        m["code"] = code
        m["abs_rel_diff"] = (m["close_live"] - m["close_yahoo"]).abs() / m["close_yahoo"].replace(
            0, np.nan
        )
        m["ret_live"] = m["close_live"].pct_change()
        m["ret_yahoo"] = m["close_yahoo"].pct_change()
        rows.append(m)
        time.sleep(0.2)
    if not rows:
        return {
            "id": "fin12_recent",
            "status": "NO_OVERLAP",
            "ok": False,
            "fetch_errors": errors,
        }
    allm = pd.concat(rows, ignore_index=True)
    path = REPRO / "fin_sleeve_recent_live_vs_yahoo.csv"
    allm.to_csv(path, index=False)

    per_rows = []
    for code, g in allm.groupby("code"):
        rr = g.dropna(subset=["ret_live", "ret_yahoo"])
        ret_corr = float(rr["ret_live"].corr(rr["ret_yahoo"])) if len(rr) > 3 else None
        ret_mae = float((rr["ret_live"] - rr["ret_yahoo"]).abs().mean()) if len(rr) else None
        per_rows.append(
            {
                "code": code,
                "n": int(len(g)),
                "max_abs_rel_level": float(g["abs_rel_diff"].max()),
                "mean_abs_rel_level": float(g["abs_rel_diff"].mean()),
                "ret_corr": ret_corr,
                "ret_mae": ret_mae,
                "returns_ok": bool(
                    ret_mae is not None
                    and ret_mae <= ret_mae_max
                    and ret_corr is not None
                    and ret_corr >= ret_corr_min
                ),
            }
        )
    per = pd.DataFrame(per_rows)
    worst_level = float(per["max_abs_rel_level"].max())
    returns_ok = bool(per["returns_ok"].all())
    # PASS if returns align; LEVEL_DRIFT if only levels differ
    if returns_ok and worst_level > rel_tol_level:
        status, ok = "PASS_LEVEL_SCALE_NOTE", True
    elif returns_ok:
        status, ok = "PASS", True
    else:
        status, ok = "DRIFT", False
    return {
        "id": "fin12_recent",
        "status": status,
        "ok": ok,
        "codes": FIN_SLEEVE,
        "n_overlap_rows": int(len(allm)),
        "start": start,
        "asof": asof,
        "max_abs_rel_diff_level": worst_level,
        "returns_ok": returns_ok,
        "per_code": per.to_dict(orient="records"),
        "thresholds": {
            "ret_mae_max": ret_mae_max,
            "ret_corr_min": ret_corr_min,
            "level_rel_tol_note": rel_tol_level,
        },
        "fetch_errors": errors,
        "detail_csv": str(path.relative_to(ROOT)),
        "note": (
            "Gate on daily returns (raw vs Yahoo adj levels may differ ~2–3% for some names)"
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lookback-days", type=int, default=40)
    ap.add_argument("--skip-div", action="store_true")
    args = ap.parse_args()

    REPRO.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    live = load_live()
    checks: list[dict] = []
    print("TAIEX shadow ...", flush=True)
    checks.append(reconcile_taiex(live, args.lookback_days))
    print("Fin sleeve recent shadow ...", flush=True)
    checks.append(reconcile_fin_recent(live, args.lookback_days))
    if args.skip_div:
        checks.append({"id": "dividend_amount", "status": "SKIPPED", "ok": True, "note": "--skip-div"})
    else:
        print("Dividend amount shadow ...", flush=True)
        checks.append(reconcile_div_amounts())

    # Shadow drift is informational for ops; exit 0 unless hard failure (NO_OVERLAP on all)
    hard_fail = all(c.get("status") in {"NO_OVERLAP", "YAHOO_EMPTY", "MISSING_LEDGER"} for c in checks)
    n_drift = sum(1 for c in checks if c.get("status") == "DRIFT")
    all_ok = all(bool(c.get("ok")) for c in checks)
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "DATA_SOURCE_SHADOW_RECONCILE",
        "phase": "B",
        "live_wire": False,
        "soft_frozen_unchanged": True,
        "lookback_days": args.lookback_days,
        "checks": checks,
        "n_checks": len(checks),
        "n_drift": n_drift,
        "all_ok": all_ok,
        "authority": "research/ops/DATA_SOURCE_RESILIENCE.md",
        "do_not": [
            "Overwrite e22_dividend_events.csv from Yahoo amounts",
            "Rewrite forward/e21 history",
            "Soft-Frozen flip",
        ],
    }
    (OUT_DIR / "DATA_SOURCE_SHADOW_RECONCILE.json").write_text(json.dumps(summary, indent=2) + "\n")

    lines = [
        "# Data Source Shadow Reconcile — Phase B",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        "Status: **OPS SHADOW** — Soft-Frozen unchanged; no ledger overwrite.",
        "",
        f"- Lookback days: **{args.lookback_days}**",
        f"- All OK: **{all_ok}**",
        f"- Drift checks: **{n_drift}**",
        "",
        "| Check | Status | OK | Notes |",
        "|---|---|:---:|---|",
    ]
    for c in checks:
        bits = []
        if c.get("ret_mae") is not None:
            bits.append(f"ret_mae={c['ret_mae']:.4g}")
        if c.get("ret_corr") is not None:
            bits.append(f"corr={c['ret_corr']:.4g}")
        if c.get("n_flagged") is not None:
            bits.append(f"flagged={c['n_flagged']}/{c.get('n_overlap')}")
        if c.get("max_abs_rel_diff") is not None and c["id"] != "taiex":
            bits.append(f"max|rel|={c['max_abs_rel_diff']:.4g}")
        note = c.get("detail_csv") or c.get("note") or ""
        if bits:
            note = f"{note} ({', '.join(bits)})"
        lines.append(f"| `{c['id']}` | {c.get('status')} | {c.get('ok')} | {note} |")
    lines += [
        "",
        "## Hard rules",
        "",
        "- Dividend amounts: **flag-only**",
        "- No Soft-Frozen flip",
        "- No `forward/e21` rewrite",
        "",
        "Authority: `research/ops/DATA_SOURCE_RESILIENCE.md`",
        "",
    ]
    (OUT_DIR / "DATA_SOURCE_SHADOW_RECONCILE.md").write_text("\n".join(lines))
    print(
        json.dumps(
            {
                "all_ok": all_ok,
                "n_drift": n_drift,
                "checks": [f"{c['id']}:{c.get('status')}" for c in checks],
            },
            indent=2,
        )
    )
    return 1 if hard_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
