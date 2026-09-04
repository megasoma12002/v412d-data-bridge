#!/usr/bin/env python3
"""E50 four-layer paper forward (EXPERIMENTAL) — G2 gap fill.

Writes immutable paper ledgers under ``forward/e50_stack/`` beside live E21.
Does NOT edit ``forward/e21/`` or SOFT_FROZEN scripts in place.

Architecture (per GAP_FILL_PLAN G2 + E45-C1 decision B):
  Core sleeve   = E16 + Exact T+1 (E18) + E22 dividends (challenger core)
  Alpha sleeve  = locked A3-R1 research NAV returns (MIXED / Option-2)
  E45           = exposure *signal only* (alpha-cut-first); core membership unchanged
  Split         = 80% core / 20% alpha (EXPERIMENTAL until approved)

States: NORMAL | ALPHA_WEAK | CRISIS
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e45_crisis_core as e45
import e50_early_stack_combined_nav as core_sim


CORE_W = 0.80
ALPHA_W = 0.20
CAPITAL = 3_000_000.0


def append_immutable(path: Path, row: dict, key: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    new = pd.DataFrame([row])
    if path.exists():
        old = pd.read_csv(path)
        hit = old[old[key].astype(str) == str(row[key])]
        if len(hit):
            return False
        new = pd.concat([old, new], ignore_index=True)
    new.to_csv(path, index=False)
    return True


def classify_state(exposure: float, alpha_trail_20: float | None) -> str:
    """Pre-registered operating states (not a promotion gate).

    Thresholds chosen so NORMAL is reachable under E3 vol-target (often <1.0):
      CRISIS     exposure < 0.85
      ALPHA_WEAK mild de-lever (0.85≤exp<0.95) or alpha 20d trail < −5%
      NORMAL     otherwise
    Alpha-cut still uses continuous exposure; state is for ledger / ops only.
    """
    if exposure < 0.85:
        return "CRISIS"
    if exposure < 0.95:
        return "ALPHA_WEAK"
    if alpha_trail_20 is not None and alpha_trail_20 < -0.05:
        return "ALPHA_WEAK"
    return "NORMAL"


def build_books(
    market: pd.DataFrame,
    dividends: pd.DataFrame,
    alpha_nav: pd.Series,
    *,
    capital: float,
    core_w: float,
    alpha_w: float,
) -> dict:
    _, _, target, regime = core_sim.e16_features(market)
    nav_core, fills, meta = core_sim.simulate_core(
        market,
        target,
        regime,
        dividends,
        apply_e22=True,
        e45_exposure=None,  # decision B: do not bake E45 into core
        capital=capital,
    )
    core = nav_core.set_index(pd.to_datetime(nav_core["date"]))["nav"].astype(float)
    core_ret = core.pct_change().fillna(0.0)

    codes = core_sim.ALL
    close_eq = (
        market[market["code"].isin(codes)]
        .pivot(index="date", columns="code", values="close")
        .sort_index()
        .ffill()
    )
    e45_exp = e45.compute_exposure(close_eq, "E3_VOLTARGET_WINNER")["exposure"]

    alpha = alpha_nav.sort_index()
    alpha = alpha[~alpha.index.duplicated(keep="last")].astype(float)
    alpha_ret = alpha.pct_change().fillna(0.0)

    # Scale alpha unit NAV to sleeve capital for ledger readability
    overlap = core_ret.index.intersection(alpha_ret.index).intersection(e45_exp.index).sort_values()
    s = core_w + alpha_w
    cw0, aw0 = core_w / s, alpha_w / s

    rows = []
    nav_c = capital * cw0
    nav_a = capital * aw0
    nav_cash_buffer = 0.0
    for dt in overlap:
        exp = float(e45_exp.loc[dt])
        ar = float(alpha_ret.loc[dt])
        cr = float(core_ret.loc[dt])
        # trailing 20d alpha return for ALPHA_WEAK (pre-registered monitor, not selection)
        hist = alpha_ret.loc[:dt].tail(20)
        trail = float((1 + hist).prod() - 1) if len(hist) >= 5 else None
        state = classify_state(exp, trail)

        cw = cw0
        # Continuous alpha-cut-first (E45 signal): scale active alpha by exposure.
        # Residual of the alpha sleeve sits in cash (not forced into core).
        aw = aw0 * max(exp, 0.0)
        cash_w = cw0 + aw0 - cw - aw
        invest_frac = (aw / aw0) if aw0 > 0 else 0.0

        nav_c = nav_c * (1.0 + cr)
        nav_a = nav_a * (1.0 + invest_frac * ar)
        nav_combined = nav_c + nav_a
        rows.append(
            {
                "date": dt.date().isoformat(),
                "state": state,
                "e45_exposure": exp,
                "core_w": cw,
                "alpha_w": aw,
                "cash_w": cash_w,
                "alpha_invest_frac": invest_frac,
                "alpha_trail_20": trail,
                "ret_core": cr,
                "ret_alpha": ar,
                "ret_combined": (cw * cr + aw * ar + cash_w * 0.0),
                "nav_core": nav_c,
                "nav_alpha": nav_a,
                "nav_combined": nav_combined,
            }
        )

    book = pd.DataFrame(rows)
    return {
        "book": book,
        "core_nav_full": nav_core,
        "fills": fills,
        "meta": meta,
        "overlap_start": str(overlap[0].date()) if len(overlap) else None,
        "overlap_end": str(overlap[-1].date()) if len(overlap) else None,
        "n_overlap": int(len(overlap)),
        "core_w": cw0,
        "alpha_w": aw0,
    }


def write_ledgers(state_dir: Path, built: dict, config: dict) -> dict:
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "config.json").write_text(json.dumps(config, indent=2) + "\n")

    book = built["book"]
    written = {"nav_rows": 0, "state_rows": 0, "skipped": 0}
    for _, r in book.iterrows():
        nav_row = {
            "date": r["date"],
            "nav_core": r["nav_core"],
            "nav_alpha": r["nav_alpha"],
            "nav_combined": r["nav_combined"],
            "exposure_e45": r["e45_exposure"],
            "core_w": r["core_w"],
            "alpha_w": r["alpha_w"],
            "cash_w": r["cash_w"],
            "ret_combined": r["ret_combined"],
        }
        st_row = {
            "date": r["date"],
            "state": r["state"],
            "e45_exposure": r["e45_exposure"],
            "alpha_trail_20": r["alpha_trail_20"],
            "alpha_invest_frac": r["alpha_invest_frac"],
        }
        if append_immutable(state_dir / "nav_combined.csv", nav_row, "date"):
            written["nav_rows"] += 1
        else:
            written["skipped"] += 1
        if append_immutable(state_dir / "state_machine.csv", st_row, "date"):
            written["state_rows"] += 1

    # Separate sleeve extracts (overwrite OK — derived views of immutable combined)
    if len(book):
        book[["date", "nav_core"]].to_csv(state_dir / "nav_core.csv", index=False)
        book[["date", "nav_alpha"]].to_csv(state_dir / "nav_alpha.csv", index=False)
        book[["date", "e45_exposure"]].rename(columns={"e45_exposure": "exposure"}).to_csv(
            state_dir / "exposure_e45.csv", index=False
        )
        built["core_nav_full"].to_csv(state_dir / "nav_core_full_history.csv", index=False)
        if built["fills"] is not None and len(built["fills"]):
            built["fills"].to_csv(state_dir / "core_fills.csv", index=False)

    # Hash-chain audit over combined NAV dates
    audit = state_dir / "audit_chain.jsonl"
    prev = "GENESIS"
    if audit.exists():
        lines = [x for x in audit.read_text().splitlines() if x.strip()]
        if lines:
            prev = json.loads(lines[-1])["hash"]
        existing = {json.loads(x)["date"] for x in lines}
    else:
        existing = set()
    with audit.open("a") as f:
        for _, r in book.iterrows():
            if r["date"] in existing:
                continue
            payload = json.dumps(
                {
                    "date": r["date"],
                    "nav_combined": r["nav_combined"],
                    "state": r["state"],
                    "previous_hash": prev,
                },
                sort_keys=True,
                default=str,
            )
            h = hashlib.sha256(payload.encode()).hexdigest()
            f.write(json.dumps({"date": r["date"], "previous_hash": prev, "hash": h}) + "\n")
            prev = h
            existing.add(r["date"])

    return written


def run_qc(state_dir: Path) -> dict:
    checks = {}
    nav = pd.read_csv(state_dir / "nav_combined.csv")
    st = pd.read_csv(state_dir / "state_machine.csv")
    checks["nav_unique_date"] = not nav.date.duplicated().any()
    checks["state_unique_date"] = not st.date.duplicated().any()
    checks["nav_positive"] = bool((nav.nav_combined > 0).all() and (nav.nav_core > 0).all())
    checks["date_monotonic"] = bool(
        pd.to_datetime(nav.date).is_monotonic_increasing
        and pd.to_datetime(st.date).is_monotonic_increasing
    )
    wsum = (nav["core_w"] + nav["alpha_w"] + nav["cash_w"] - 1.0).abs()
    checks["sleeve_weights_sum_le_one"] = bool((wsum < 1e-8).all())
    checks["exposure_in_unit_interval"] = bool(
        (nav.exposure_e45 >= 0).all() and (nav.exposure_e45 <= 1.0 + 1e-9).all()
    )
    checks["states_valid"] = set(st.state).issubset({"NORMAL", "ALPHA_WEAK", "CRISIS"})
    if (state_dir / "audit_chain.jsonl").exists():
        audit = [json.loads(x) for x in (state_dir / "audit_chain.jsonl").read_text().splitlines() if x.strip()]
        checks["audit_unique_date"] = len({x["date"] for x in audit}) == len(audit)
        checks["audit_chain_links"] = all(
            audit[i]["previous_hash"] == audit[i - 1]["hash"] for i in range(1, len(audit))
        )
    # Exact T+1 inherited from core sim meta
    meta_path = state_dir / "bootstrap_meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        checks["exact_t1_core"] = bool(meta.get("core_exact_t1_ok", False))
        checks["no_same_bar_core"] = bool(meta.get("core_same_bar_fills", 1) == 0)

    # Compare paper vs E21 on overlapping live dates (informational, not a fail)
    e21_nav = Path("forward/e21/nav.csv")
    compare = {}
    if e21_nav.exists() and len(nav):
        e21 = pd.read_csv(e21_nav, parse_dates=["date"])
        paper = nav.copy()
        paper["date"] = pd.to_datetime(paper["date"])
        both = paper.merge(e21[["date", "nav_e16_e18"]], on="date", how="inner")
        compare = {
            "n_overlap_sessions": int(len(both)),
            "e21_dates": [d.date().isoformat() for d in both["date"]],
            "note": "Paper stack includes E22+alpha; E21 is core-short without E22 — levels not equal by design",
        }

    status = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "nav_rows": int(len(nav)),
        "state_rows": int(len(st)),
        "compare_vs_e21": compare,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (state_dir / "qc_status.json").write_text(json.dumps(status, indent=2) + "\n")
    return status


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", type=Path, default=Path("forward/e21/live_market.csv"))
    ap.add_argument(
        "--dividends", type=Path, default=Path("data/dividend_events/e22_dividend_events.csv")
    )
    ap.add_argument(
        "--alpha-nav",
        type=Path,
        default=Path("repro/e50a3r1-audit-20260903/outputs/a3r1/daily_nav.csv"),
    )
    ap.add_argument("--state-dir", type=Path, default=Path("forward/e50_stack"))
    ap.add_argument("--capital", type=float, default=CAPITAL)
    ap.add_argument("--core-weight", type=float, default=CORE_W)
    ap.add_argument("--alpha-weight", type=float, default=ALPHA_W)
    ap.add_argument(
        "--paper-from",
        type=str,
        default=None,
        help="Optional ISO date: only write ledgers on/after this date (e.g. E21 live start)",
    )
    args = ap.parse_args()

    market = pd.read_csv(args.market, dtype={"code": str})
    market["date"] = pd.to_datetime(market["date"])
    dividends = (
        pd.read_csv(args.dividends, dtype={"code": str}) if args.dividends.exists() else pd.DataFrame()
    )
    alpha_df = pd.read_csv(args.alpha_nav, parse_dates=["date"])
    alpha = alpha_df.set_index("date")["nav"].astype(float)

    built = build_books(
        market,
        dividends,
        alpha,
        capital=args.capital,
        core_w=args.core_weight,
        alpha_w=args.alpha_weight,
    )
    book = built["book"]
    if args.paper_from:
        cut = pd.Timestamp(args.paper_from)
        book = book[pd.to_datetime(book["date"]) >= cut].reset_index(drop=True)
        built = dict(built)
        built["book"] = book

    config = {
        "package": "forward/e50_stack",
        "status": "PAPER_EXPERIMENTAL",
        "modifies_e21": False,
        "e45_promoted": False,
        "e45_role": "SIGNAL_ONLY_ALPHA_CUT_FIRST",
        "e45_decision": "B_KEEP_D_AS_BASELINE_E45_API_ONLY",
        "alpha_source": str(args.alpha_nav),
        "alpha_status": "MIXED_OPTION2_LOCKED_A3R1",
        "core_weight": built["core_w"],
        "alpha_weight": built["alpha_w"],
        "apply_e22_on_core": True,
        "overlap_full": {"start": built["overlap_start"], "end": built["overlap_end"], "n": built["n_overlap"]},
        "paper_from": args.paper_from,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    meta = {
        "core_exact_t1_ok": built["meta"].get("exact_t1_ok"),
        "core_same_bar_fills": built["meta"].get("same_bar_fills"),
        "core_dividend_cash_total": built["meta"].get("dividend_cash_total"),
        "core_meta": built["meta"],
        "paper_rows": int(len(book)),
    }
    args.state_dir.mkdir(parents=True, exist_ok=True)
    (args.state_dir / "bootstrap_meta.json").write_text(json.dumps(meta, indent=2, default=str) + "\n")

    written = write_ledgers(args.state_dir, built, config)
    qc = run_qc(args.state_dir)

    # Summary report
    if len(book):
        path = book["nav_combined"].to_numpy()
        r = book["ret_combined"].to_numpy()
        years = max(len(r) / 252.0, 1e-9)
        cagr = float((path[-1] / path[0]) ** (1 / years) - 1) if path[0] > 0 else None
        peak = np.maximum.accumulate(path)
        mdd = float(np.min(path / peak - 1))
        summary = {
            "cagr": cagr,
            "max_drawdown": mdd,
            "utility": (cagr or 0) - 0.5 * abs(mdd),
            "n_days": int(len(book)),
            "start": book["date"].iloc[0],
            "end": book["date"].iloc[-1],
            "state_counts": book["state"].value_counts().to_dict(),
        }
    else:
        summary = {"error": "empty book"}
    (args.state_dir / "paper_summary.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")

    md = f"""# E50 Stack Paper Forward

**Status:** `PAPER_EXPERIMENTAL` — does not modify `forward/e21/`.

## Contract

- Core 80% / Alpha 20% (EXPERIMENTAL)
- Core = E16 + Exact T+1 + E22 dividends
- E45 = signal only → alpha-cut-first (decision **B**)
- Alpha = locked A3-R1 (Option-2 MIXED)

## QC

`{qc['status']}` — checks: `{json.dumps(qc['checks'])}`

## Paper window

`{summary.get('start')}` → `{summary.get('end')}` ({summary.get('n_days')} days)

| Metric | Value |
|---|---:|
| CAGR | {100*(summary.get('cagr') or 0):.2f}% |
| MDD | {100*(summary.get('max_drawdown') or 0):.2f}% |
| Util | {summary.get('utility') if summary.get('utility') is not None else 'n/a'} |

State counts: `{summary.get('state_counts')}`

## Explicit non-actions

- No E45 promotion
- No alpha promotion
- No in-place E21 rewrite
"""
    (args.state_dir / "README.md").write_text(md)
    print(json.dumps({"qc": qc["status"], "written": written, "summary": summary}, indent=2, default=str))
    if qc["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
