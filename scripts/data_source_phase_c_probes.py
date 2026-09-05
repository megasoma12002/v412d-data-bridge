#!/usr/bin/env python3
"""Phase C probes: Fin-12 history shadow, adj dual-source, TAIEX failover dry-run.

C1/C2 use committed live_market (primary history store) vs Yahoo — flag-only.
C3 exercises scripts/taiex_fetch_with_failover.py (opt-in; e21 default unchanged).

Soft-Frozen KEEP. No forward/e21 rewrite. No Goodinfo/Wantgoo/CMoney.
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LIVE_MKT = ROOT / "forward/e21/live_market.csv"
OUT_DIR = ROOT / "repro" / "data-source-phase-c"
OPS_DIR = ROOT / "research" / "ops"
OUT_JSON = OUT_DIR / "DATA_SOURCE_PHASE_C_PROBES.json"
OUT_MD = OUT_DIR / "DATA_SOURCE_PHASE_C_PROBES.md"
OPS_JSON = OPS_DIR / "DATA_SOURCE_PHASE_C_PROBES.json"
OPS_MD = OPS_DIR / "DATA_SOURCE_PHASE_C_PROBES.md"
TAIEX_HELPER = ROOT / "scripts" / "taiex_fetch_with_failover.py"

# Full Fin sleeve + telecom used in Soft-Frozen / E22 books
FIN12 = ["2880", "2886", "2892", "5880", "2412", "3045", "4904", "0050"]

C1_DRIFT_MAX = 0.008  # mean abs daily return diff
C1_CORR_MIN = 0.95
C1_MIN_ROWS = 500
C2_DRIFT_WARN = 0.015
C2_MIN_ROWS = 500


def _status(ok: bool, reason: str = "") -> dict[str, Any]:
    return {"status": "PASS" if ok else "FAIL", "reason": reason}


def load_live() -> pd.DataFrame:
    d = pd.read_csv(LIVE_MKT, dtype={"code": str})
    d["date"] = pd.to_datetime(d["date"]).dt.strftime("%Y-%m-%d")
    for c in ("close", "adj_close"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    return d


def align_returns(a: pd.Series, b: pd.Series) -> tuple[pd.Series, pd.Series]:
    m = pd.concat([a.rename("a"), b.rename("b")], axis=1).dropna()
    return m["a"], m["b"]


def _yahoo_full(symbol: str, start: str) -> pd.DataFrame:
    """Yahoo OHLCV with Adj Close when available."""
    try:
        import yfinance as yf
    except ImportError as ex:  # pragma: no cover
        raise RuntimeError("yfinance not installed") from ex
    d = yf.download(symbol, start=start, auto_adjust=False, progress=False, threads=False)
    if d is None or d.empty:
        return pd.DataFrame()
    if isinstance(d.columns, pd.MultiIndex):
        d.columns = d.columns.get_level_values(0)
    out = d.reset_index().rename(columns={"Date": "date"})
    out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
    keep = {"date": "date", "Close": "close", "Adj Close": "adj_close"}
    cols = [c for c in keep if c in out.columns or c == "date"]
    # rebuild
    frame = pd.DataFrame({"date": out["date"]})
    if "Close" in out.columns:
        frame["close"] = pd.to_numeric(out["Close"], errors="coerce")
    if "Adj Close" in out.columns:
        frame["adj_close"] = pd.to_numeric(out["Adj Close"], errors="coerce")
    return frame.dropna(subset=[c for c in ("close",) if c in frame.columns])


def probe_c1_fin12_history(live: pd.DataFrame) -> dict[str, Any]:
    """C1: live_market close vs Yahoo .TW Close — full-history return shadow."""
    start = str(live["date"].min())
    per: dict[str, Any] = {}
    drifts: list[float] = []
    corrs: list[float] = []
    detail_rows: list[pd.DataFrame] = []

    for code in FIN12:
        prim = live[live["code"] == code][["date", "close"]].dropna().sort_values("date")
        prim = prim.set_index("date")["close"].astype(float)
        try:
            y = _yahoo_full(f"{code}.TW", start=start)
        except Exception as ex:  # noqa: BLE001
            per[code] = {"status": "SKIP", "reason": f"yahoo_err:{type(ex).__name__}"}
            continue
        if y.empty or "close" not in y.columns:
            per[code] = {"status": "SKIP", "reason": "empty_yahoo"}
            continue
        y_px = y.set_index("date")["close"].astype(float)
        a, b = align_returns(prim.pct_change().dropna(), y_px.pct_change().dropna())
        if len(a) < C1_MIN_ROWS:
            per[code] = {"status": "SKIP", "reason": f"short_overlap_{len(a)}"}
            continue
        mad = float(np.mean(np.abs(a.values - b.values)))
        corr = float(np.corrcoef(a.values, b.values)[0, 1]) if len(a) > 2 else float("nan")
        drifts.append(mad)
        if not math.isnan(corr):
            corrs.append(corr)
        ok_ticker = (
            mad <= C1_DRIFT_MAX
            and (not math.isnan(corr))
            and corr >= C1_CORR_MIN
        )
        per[code] = {
            "status": "OK" if ok_ticker else "DRIFT",
            "n": int(len(a)),
            "mean_abs_return_diff": mad,
            "corr": None if math.isnan(corr) else corr,
        }
        detail_rows.append(
            pd.DataFrame(
                {
                    "code": code,
                    "date": a.index,
                    "ret_live": a.values,
                    "ret_yahoo": b.values,
                }
            )
        )
        time.sleep(0.15)

    if detail_rows:
        pd.concat(detail_rows, ignore_index=True).to_csv(
            OUT_DIR / "c1_fin12_history_returns.csv", index=False
        )

    ok_rows = [v for v in per.values() if v.get("status") == "OK"]
    drift_rows = [v for v in per.values() if v.get("status") == "DRIFT"]
    mean_mad = float(np.mean(drifts)) if drifts else float("nan")
    mean_corr = float(np.mean(corrs)) if corrs else float("nan")
    # Fail-closed: require enough OK tickers AND finite mean MAD within named threshold
    # (no undocumented 1.5× slack; NaN mean_mad does not pass).
    passed = (
        len(ok_rows) >= 6
        and (not math.isnan(mean_mad))
        and mean_mad <= C1_DRIFT_MAX
    )
    note = ""
    if drift_rows:
        note = f"DRIFT on {len(drift_rows)} ticker(s); does not count toward PASS"
    return {
        "probe": "C1_fin12_history_shadow",
        "primary": "forward/e21/live_market.csv close",
        "shadow": "Yahoo .TW Close",
        "window_start": start,
        "tickers": per,
        "n_ok": len(ok_rows),
        "n_drift": len(drift_rows),
        "mean_abs_return_diff": None if math.isnan(mean_mad) else mean_mad,
        "mean_corr": None if math.isnan(mean_corr) else mean_corr,
        "thresholds": {"mean_abs_return_diff_max": C1_DRIFT_MAX, "corr_min": C1_CORR_MIN},
        "detail_csv": "repro/data-source-phase-c/c1_fin12_history_returns.csv",
        "note": note,
        "gate": _status(
            passed,
            ""
            if passed
            else f"n_ok={len(ok_rows)} mean_mad={mean_mad}; need n_ok>=6",
        ),
    }


def probe_c2_adj_dual_source(live: pd.DataFrame) -> dict[str, Any]:
    """C2: live adj_close vs Yahoo Adj Close — corporate-action proxy shadow."""
    start = str(live["date"].min())
    per: dict[str, Any] = {}
    drifts: list[float] = []
    detail_rows: list[pd.DataFrame] = []

    for code in FIN12:
        prim = live[live["code"] == code][["date", "adj_close"]].dropna().sort_values("date")
        prim = prim.set_index("date")["adj_close"].astype(float)
        try:
            y = _yahoo_full(f"{code}.TW", start=start)
        except Exception as ex:  # noqa: BLE001
            per[code] = {"status": "SKIP", "reason": f"yahoo_err:{type(ex).__name__}"}
            continue
        if y.empty or "adj_close" not in y.columns:
            per[code] = {"status": "SKIP", "reason": "no_yahoo_adj"}
            continue
        y_px = y.set_index("date")["adj_close"].astype(float)
        a, b = align_returns(prim.pct_change().dropna(), y_px.pct_change().dropna())
        if len(a) < C2_MIN_ROWS:
            per[code] = {"status": "SKIP", "reason": f"short_overlap_{len(a)}"}
            continue
        mad = float(np.mean(np.abs(a.values - b.values)))
        corr = float(np.corrcoef(a.values, b.values)[0, 1]) if len(a) > 2 else float("nan")
        drifts.append(mad)
        status = "OK"
        if mad > C2_DRIFT_WARN:
            status = "INFO_DRIFT"
        per[code] = {
            "status": status,
            "n": int(len(a)),
            "mean_abs_return_diff": mad,
            "corr": None if math.isnan(corr) else corr,
        }
        detail_rows.append(
            pd.DataFrame(
                {
                    "code": code,
                    "date": a.index,
                    "ret_live_adj": a.values,
                    "ret_yahoo_adj": b.values,
                }
            )
        )
        time.sleep(0.15)

    if detail_rows:
        pd.concat(detail_rows, ignore_index=True).to_csv(
            OUT_DIR / "c2_adj_returns.csv", index=False
        )

    # Fail-closed: only OK counts toward coverage; INFO_DRIFT must not inflate PASS.
    covered_ok = [v for v in per.values() if v.get("status") == "OK"]
    drift_info = [v for v in per.values() if v.get("status") == "INFO_DRIFT"]
    mean_mad = float(np.mean(drifts)) if drifts else float("nan")
    passed = (
        len(covered_ok) >= 6
        and len(drift_info) == 0
        and (not math.isnan(mean_mad))
        and mean_mad <= C2_DRIFT_WARN
    )
    note = ""
    if drift_info:
        note = (
            f"INFO_DRIFT on {len(drift_info)} ticker(s); excluded from PASS coverage "
            f"(mean_mad={mean_mad if not math.isnan(mean_mad) else 'nan'})"
        )
    elif covered_ok and not math.isnan(mean_mad) and mean_mad > C2_DRIFT_WARN:
        note = (
            f"mean_mad={mean_mad:.4f}>{C2_DRIFT_WARN} "
            "(adj methodology may differ; do not auto-overwrite e21)"
        )
    return {
        "probe": "C2_adj_corporate_action_shadow",
        "primary": "forward/e21/live_market.csv adj_close",
        "shadow": "Yahoo .TW Adj Close",
        "window_start": start,
        "tickers": per,
        "n_ok": len(covered_ok),
        "n_info_drift": len(drift_info),
        "mean_abs_return_diff": None if math.isnan(mean_mad) else mean_mad,
        "drift_warn_threshold": C2_DRIFT_WARN,
        "detail_csv": "repro/data-source-phase-c/c2_adj_returns.csv",
        "note": note,
        "gate": _status(
            passed,
            "" if passed else f"n_ok={len(covered_ok)} need>=6 and zero INFO_DRIFT",
        ),
    }


def probe_c3_taiex_failover() -> dict[str, Any]:
    """C3: dry-run optional Yahoo failover helper (does not change e21 default)."""
    out_primary = OUT_DIR / "taiex_primary_dryrun.csv"
    out_fail = OUT_DIR / "taiex_failover_dryrun.csv"
    out_force = OUT_DIR / "taiex_force_yahoo_dryrun.csv"

    def run(extra: list[str], outp: Path) -> dict[str, Any]:
        cmd = [
            sys.executable,
            str(TAIEX_HELPER),
            "--start",
            "2024-01-01",
            "--out",
            str(outp),
            *extra,
        ]
        p = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
        meta_path = outp.with_suffix(".meta.json")
        meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
        return {
            "returncode": p.returncode,
            "meta": meta,
            "stderr_tail": (p.stderr or "")[-400:],
            "n_rows": int(meta.get("n_rows", 0)),
        }

    primary = run([], out_primary)
    failover = run(["--enable-yahoo-failover", "--simulate-finmind-fail"], out_fail)
    force = run(["--force-yahoo"], out_force)

    primary_ok = primary["returncode"] == 0 and primary["n_rows"] > 0
    failover_ok = (
        failover["returncode"] == 0
        and failover["n_rows"] > 0
        and str(failover["meta"].get("source", "")).startswith("yahoo")
        and bool(failover["meta"].get("failover_used"))
    )
    force_ok = force["returncode"] == 0 and force["n_rows"] > 0
    passed = primary_ok and failover_ok and force_ok
    return {
        "probe": "C3_taiex_optional_failover",
        "helper": "scripts/taiex_fetch_with_failover.py",
        "default_unchanged": True,
        "note": "Helper is opt-in only; e21 still uses FinMind TaiwanStockPrice(TAIEX).",
        "primary": primary,
        "failover_on_finmind_fail": failover,
        "force_yahoo": force,
        "gate": _status(passed, "" if passed else "failover helper dry-run incomplete"),
    }


def write_md(payload: dict[str, Any]) -> str:
    lines = [
        "# DATA_SOURCE_PHASE_C_PROBES",
        "",
        f"- as_of: `{payload['as_of']}`",
        f"- overall: **{payload['overall_status']}**",
        "- Soft-Frozen **KEEP**; no e21 rewrite; TAIEX Yahoo failover **opt-in only**",
        "",
        "## Gates",
        "",
        "| Probe | Status | Detail |",
        "|---|---|---|",
    ]
    for key in (
        "C1_fin12_history_shadow",
        "C2_adj_corporate_action_shadow",
        "C3_taiex_optional_failover",
    ):
        block = payload["probes"][key]
        g = block["gate"]
        detail = g.get("reason") or block.get("note") or f"n_ok={block.get('n_ok', 'n/a')}"
        lines.append(f"| {key} | {g['status']} | {detail} |")
    lines.extend(
        [
            "",
            "## Hard rules preserved",
            "",
            "- Soft-Frozen KEEP",
            "- No e21 history rewrite",
            "- No Goodinfo/Wantgoo/CMoney reopen",
            "- Yahoo TAIEX failover is **opt-in helper only** (not silent e21 primary switch)",
            "",
            "Authority: `research/ops/DATA_SOURCE_RESILIENCE.md`",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--skip-c1", action="store_true")
    ap.add_argument("--skip-c2", action="store_true")
    ap.add_argument("--skip-c3", action="store_true")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OPS_DIR.mkdir(parents=True, exist_ok=True)
    live = load_live()
    probes: dict[str, Any] = {}
    if not args.skip_c1:
        print("C1 Fin-12 history shadow (live_market vs Yahoo)...", flush=True)
        probes["C1_fin12_history_shadow"] = probe_c1_fin12_history(live)
    if not args.skip_c2:
        print("C2 adj dual-source (live adj_close vs Yahoo Adj Close)...", flush=True)
        probes["C2_adj_corporate_action_shadow"] = probe_c2_adj_dual_source(live)
    if not args.skip_c3:
        print("C3 TAIEX failover dry-run...", flush=True)
        probes["C3_taiex_optional_failover"] = probe_c3_taiex_failover()

    statuses = [p["gate"]["status"] for p in probes.values()]
    overall = "PASS" if statuses and all(s == "PASS" for s in statuses) else "FAIL"
    payload = {
        "as_of": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "DATA_SOURCE_PHASE_C_PROBES",
        "overall_status": overall,
        "live_wire": False,
        "soft_frozen_unchanged": True,
        "probes": probes,
        "constraints": {
            "soft_frozen_keep": True,
            "no_e21_history_rewrite": True,
            "no_blocked_scrapers": True,
            "taiex_failover_opt_in_only": True,
        },
        "authority": "research/ops/DATA_SOURCE_RESILIENCE_PHASE_C_CHARTER.md",
    }
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    md = write_md(payload)
    OUT_JSON.write_text(text, encoding="utf-8")
    OUT_MD.write_text(md, encoding="utf-8")
    OPS_JSON.write_text(text, encoding="utf-8")
    OPS_MD.write_text(md, encoding="utf-8")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OPS_JSON}")
    print(f"OVERALL={overall}")
    return 0 if overall == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
