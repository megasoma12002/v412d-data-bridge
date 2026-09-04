#!/usr/bin/env python3
"""Early-stack combined NAV challenger (EXPERIMENTAL / read-only).

Closes the architectural gap documented in E50_HANDOFF_VERIFICATION.md:
  Market -> E16 Core -> E18+E22 Execution -> (optional E45 lineage proxy)

Does NOT modify SOFT_FROZEN baselines:
  - does not edit scripts/e21_forward_pipeline.py
  - does not append to forward/e21/ immutable ledgers
  - does not invent or promote an official e45 module
  - does not retune E45 / E16 / E18 / E22 parameters in place

Outputs under a challenger sandbox only.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

# Mirror E21 SOFT_FROZEN membership / fees (read-only copy of constants; not an edit).
FIN = ["2880", "2886", "2892", "5880"]
TEL = ["2412", "3045", "4904"]
ALL = FIN + TEL + ["0050"]
BUY_FEE = 0.001425 * 0.6
SELL_FEE = 0.001425 * 0.6
TAX_STOCK = 0.003
TAX_ETF = 0.001
SLIP = 0.0005
CAPITAL = 3_000_000.0
WARMUP_DAYS = 252


def e16_features(m: pd.DataFrame):
    """Causal E16 target history — same logic as e21_forward_pipeline.features (copy)."""
    p = m.pivot(index="date", columns="code", values="adj_close").sort_index().ffill()
    r = p.pct_change(fill_method=None).fillna(0)
    sleeve = pd.DataFrame(
        {"Financial": r[FIN].mean(1), "Telecom": r[TEL].mean(1), "0050": r["0050"]}
    )
    tc = p["TAIEX"]
    tr = tc.pct_change()
    ma = tc.rolling(200).mean()
    vol = tr.rolling(20).std() * np.sqrt(252)
    dd = tc / tc.rolling(252, min_periods=120).max() - 1
    reg = pd.Series("Sideways", index=p.index)
    reg[(tc > ma) & (vol < 0.25)] = "Bull"
    reg[tc < ma] = "Bear"
    reg[(vol > 0.35) | (dd < -0.15)] = "Crisis"
    nav = (1 + sleeve).cumprod()
    m20 = nav / nav.shift(20) - 1
    m60 = nav / nav.shift(60) - 1
    sv = sleeve.rolling(20).std() * np.sqrt(252)
    d60 = nav / nav.rolling(60, min_periods=20).max() - 1

    def z(x):
        return x.sub(x.mean(1), axis=0).div(x.std(1).replace(0, np.nan), axis=0).fillna(0)

    score = 0.35 * z(m20) + 0.35 * z(m60) - 0.20 * z(sv) + 0.10 * z(d60)
    out = []
    cur = np.array([0.9, 0.1, 0.0])
    for i, _dt in enumerate(p.index):
        rg = reg.iloc[i]
        pri = {
            "Bull": np.array([0.85, 0.05, 0.10]),
            "Crisis": np.array([0.60, 0.35, 0.05]),
            "Bear": np.array([0.70, 0.25, 0.05]),
            "Sideways": np.array([0.85, 0.10, 0.05]),
        }[rg]
        cand = np.maximum(pri + 0.10 * np.clip(score.iloc[i].to_numpy(), -2, 2), 0)
        cand[0] = np.clip(cand[0], 0.50, 0.95)
        cand[1] = np.clip(cand[1], 0.03, 0.35)
        cand[2] = np.clip(cand[2], 0, 0.35)
        cand /= cand.sum()
        desired = 0.75 * cur + 0.25 * cand
        if np.abs(desired - cur).sum() >= 0.02:
            cur = desired
        out.append(cur.copy())
    target = pd.DataFrame(out, index=p.index, columns=["Financial", "Telecom", "0050"])
    return p, sleeve, target, reg


def lot_qty(value: float, price: float) -> int:
    if price <= 0 or not math.isfinite(price):
        return 0
    return int(abs(value) / price)


def simulate_core(
    market: pd.DataFrame,
    target: pd.DataFrame,
    regime: pd.Series,
    dividends: pd.DataFrame | None,
    *,
    apply_e22: bool,
    e45_crisis_equity_scale: float | None,
    capital: float = CAPITAL,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Exact T+1 open fills on raw close/open; optional E22 cash credits; optional E45 proxy scale."""
    m = market.copy()
    m["date"] = pd.to_datetime(m["date"])
    closes = m.pivot(index="date", columns="code", values="close").sort_index().ffill()
    opens = m.pivot(index="date", columns="code", values="open").sort_index().ffill()
    dates = [d for d in closes.index if d in target.index]
    if len(dates) < WARMUP_DAYS + 10:
        raise RuntimeError("insufficient history for E16 warmup")

    # dividend map: cash_ex_date -> list[(code, cash_div)]
    div_map: dict[pd.Timestamp, list[tuple[str, float]]] = {}
    if apply_e22 and dividends is not None and len(dividends):
        d = dividends.copy()
        d["code"] = d["code"].astype(str)
        d["cash_ex_date"] = pd.to_datetime(d["cash_ex_date"], errors="coerce")
        d["cash_dividend"] = pd.to_numeric(d["cash_dividend"], errors="coerce")
        d = d.dropna(subset=["cash_ex_date", "cash_dividend"])
        d = d[d["code"].isin(ALL)]
        for _, row in d.iterrows():
            div_map.setdefault(pd.Timestamp(row["cash_ex_date"]).normalize(), []).append(
                (str(row["code"]), float(row["cash_dividend"]))
            )

    pos = {c: 0.0 for c in ALL}
    cash = float(capital)
    pending: list[dict] = []
    nav_rows = []
    fill_rows = []
    trade_start = dates[WARMUP_DAYS]
    same_bar = 0
    div_cash_total = 0.0
    crisis_days = 0

    for i, dt in enumerate(dates):
        if dt < trade_start:
            continue
        op = opens.loc[dt]
        cl = closes.loc[dt]

        # 1) Fill pending orders at today's open (E18 Exact T+1)
        still = []
        for o in pending:
            if pd.Timestamp(o["signal_date"]) >= dt:
                still.append(o)
                continue
            side = o["side"]
            code = o["code"]
            q = int(o["quantity"])
            fp = float(op[code]) * (1 + SLIP if side == "BUY" else 1 - SLIP)
            gross = q * fp
            tax = TAX_ETF if code == "0050" else TAX_STOCK
            fee = gross * (BUY_FEE if side == "BUY" else SELL_FEE + tax)
            if side == "BUY" and gross + fee > cash:
                q = max(0, int(cash / (fp * (1 + BUY_FEE))))
                gross = q * fp
                fee = gross * BUY_FEE
            if q < 1:
                continue
            if side == "BUY":
                pos[code] += q
                cash -= gross + fee
            else:
                q = min(q, int(pos[code]))
                if q < 1:
                    continue
                gross = q * fp
                fee = gross * (SELL_FEE + tax)
                pos[code] -= q
                cash += gross - fee
            fill_rows.append(
                {
                    "fill_date": dt.date().isoformat(),
                    "signal_date": o["signal_date"].date().isoformat()
                    if hasattr(o["signal_date"], "date")
                    else str(o["signal_date"]),
                    "code": code,
                    "side": side,
                    "quantity": q,
                    "fill_price": fp,
                    "gross": gross,
                    "fees_tax": fee,
                }
            )
            if pd.Timestamp(o["signal_date"]).normalize() >= dt.normalize():
                same_bar += 1
        pending = still

        # 2) E22 cash dividend credit on ex-date (challenger approx: credit same day)
        day_div = 0.0
        if apply_e22:
            for code, cdiv in div_map.get(pd.Timestamp(dt).normalize(), []):
                sh = pos.get(code, 0.0)
                if sh > 0 and cdiv > 0:
                    credit = sh * cdiv
                    cash += credit
                    day_div += credit
                    div_cash_total += credit

        # 3) Mark NAV at close
        vals = {c: pos[c] * float(cl[c]) for c in ALL}
        nav = cash + sum(vals.values())
        rg = str(regime.loc[dt]) if dt in regime.index else "Sideways"
        if rg == "Crisis":
            crisis_days += 1

        # 4) Target weights (E16); optional E45 lineage proxy scales *gross equity*
        tw = target.loc[dt]
        sleeve_w = {
            "Financial": float(tw["Financial"]),
            "Telecom": float(tw["Telecom"]),
            "0050": float(tw["0050"]),
        }
        equity_scale = 1.0
        if e45_crisis_equity_scale is not None and rg == "Crisis":
            equity_scale = float(e45_crisis_equity_scale)
            s = sum(sleeve_w.values())
            if s > 0:
                sleeve_w = {k: v / s * equity_scale for k, v in sleeve_w.items()}

        sleeve_vals = {
            "Financial": sum(vals[c] for c in FIN),
            "Telecom": sum(vals[c] for c in TEL),
            "0050": vals["0050"],
        }
        pre = {k: (v / nav if nav > 0 else 0.0) for k, v in sleeve_vals.items()}
        gap = {k: sleeve_w[k] - pre[k] for k in pre}
        trade = np.zeros(3)
        if max(abs(v) for v in gap.values()) >= 0.015:
            trade = np.array([gap["Financial"], gap["Telecom"], gap["0050"]]) * 0.75
            if abs(trade).sum() > 0.20:
                trade *= 0.20 / abs(trade).sum()

        # 5) Create next-day orders (signal today → fill tomorrow open)
        sleeve_trade = dict(zip(["Financial", "Telecom", "0050"], trade))
        for sleeve_name, codes in [("Financial", FIN), ("Telecom", TEL), ("0050", ["0050"])]:
            value = sleeve_trade[sleeve_name] * nav / len(codes)
            for c in codes:
                px = float(cl[c])
                qty = lot_qty(value, px)
                if qty < 1:
                    continue
                side = "BUY" if value > 0 else "SELL"
                if side == "SELL":
                    qty = min(qty, int(pos.get(c, 0)))
                if qty < 1:
                    continue
                pending.append(
                    {
                        "signal_date": dt,
                        "code": c,
                        "side": side,
                        "quantity": qty,
                    }
                )

        nav_rows.append(
            {
                "date": dt.date().isoformat(),
                "nav": nav,
                "cash": cash,
                "gross_equity": sum(vals.values()),
                "equity_weight": (sum(vals.values()) / nav) if nav else 0.0,
                "regime": rg,
                "e45_equity_scale": equity_scale,
                "dividend_credit": day_div,
                "pre_financial": pre["Financial"],
                "pre_telecom": pre["Telecom"],
                "pre_0050": pre["0050"],
                "tgt_financial": sleeve_w["Financial"],
                "tgt_telecom": sleeve_w["Telecom"],
                "tgt_0050": sleeve_w["0050"],
            }
        )

    nav_df = pd.DataFrame(nav_rows)
    fills_df = pd.DataFrame(fill_rows)
    meta = {
        "n_days": len(nav_df),
        "n_fills": len(fills_df),
        "same_bar_fills": same_bar,
        "exact_t1_ok": same_bar == 0,
        "dividend_cash_total": div_cash_total,
        "crisis_days": crisis_days,
        "start": nav_df["date"].iloc[0] if len(nav_df) else None,
        "end": nav_df["date"].iloc[-1] if len(nav_df) else None,
    }
    return nav_df, fills_df, meta


def nav_stats(nav: pd.DataFrame, col: str = "nav") -> dict:
    if nav is None or len(nav) < 2:
        return {"cagr": None, "max_drawdown": None, "utility": None, "vol": None}
    r = nav[col].pct_change().dropna().to_numpy()
    path = nav[col].to_numpy()
    years = len(r) / 252.0
    cagr = float((path[-1] / path[0]) ** (1.0 / years) - 1.0) if years > 0 and path[0] > 0 else None
    peak = np.maximum.accumulate(path)
    mdd = float(np.min(path / peak - 1.0))
    vol = float(np.std(r, ddof=1) * np.sqrt(252)) if len(r) > 2 else None
    util = (cagr or 0.0) - 0.5 * abs(mdd)
    return {"cagr": cagr, "max_drawdown": mdd, "utility": util, "vol": vol, "n_days": len(nav)}


def verify_e45_claim(repo: Path) -> dict:
    """Artifact audit for the handoff claim MDD ≈ -13.16%."""
    claim = -0.1316
    found = []
    search_paths = [
        repo / "research" / "v412e1",
        repo / "research" / "v412e11",
        repo / "research" / "v412e2e3",
        repo / "FROZEN_STRATEGY_SPEC.md",
        repo / "E50_HANDOFF_VERIFICATION.md",
    ]
    # documented lineage MDDs from reports
    lineage = {
        "E1_validation_mdd": -0.1721,
        "E1_1_validation_mdd": -0.1581,
        "E3_validation_mdd": -0.1849,
        "V412D_validation_mdd_reported": -0.1891,
        "handoff_claim_mdd": claim,
    }
    text_hits = []
    for p in [repo / "FROZEN_STRATEGY_SPEC.md", repo / "FROZEN_GOVERNANCE.md", repo / "E50_HANDOFF_VERIFICATION.md"]:
        if p.exists() and "13.16" in p.read_text():
            text_hits.append(str(p))
    # scan json/csv for exact -0.1316 or -13.16
    numeric_hit = False
    for root in [repo / "research" / "v412e1", repo / "research" / "v412e11", repo / "research" / "v412e2e3"]:
        if not root.exists():
            continue
        for f in root.rglob("*"):
            if f.suffix.lower() not in {".json", ".csv", ".md"}:
                continue
            try:
                txt = f.read_text(errors="ignore")
            except Exception:
                continue
            if "13.16" in txt or "-0.1316" in txt:
                found.append(str(f.relative_to(repo)))
                numeric_hit = True
    return {
        "claim_mdd": claim,
        "claim_status": "NOT_FOUND_IN_ARTIFACTS" if not numeric_hit else "FOUND",
        "text_mentions_only": text_hits,
        "artifact_files_with_13_16": found,
        "lineage_reported_mdds": lineage,
        "e45_module_paths": [str(p.relative_to(repo)) for p in (repo / "scripts").glob("e45*")],
        "lineage_scripts": [
            "scripts/v412e1_crisis_buffer.py",
            "scripts/v412e11_graduated_crisis.py",
            "scripts/v412e2_e3_three_rounds.py",
        ],
        "research_decision": json.loads((repo / "research" / "v412e2e3" / "research_decision.json").read_text())
        if (repo / "research" / "v412e2e3" / "research_decision.json").exists()
        else None,
        "conclusion": (
            "No official e45 module; MDD≈-13.16% remains UNVERIFIED text claim. "
            "Closest lineage MDDs are E1/E1.1/E3 validation figures (more severe). "
            "Formal strategy remains V4.12-D; E3 validation_pass but not promoted."
        ),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", type=Path, default=Path("forward/e21/live_market.csv"))
    ap.add_argument("--dividends", type=Path, default=Path("data/dividend_events/e22_dividend_events.csv"))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--capital", type=float, default=CAPITAL)
    ap.add_argument(
        "--e45-crisis-equity-scale",
        type=float,
        default=0.70,
        help="CHALLENGER proxy only: scale sleeve weights by this factor on E16 Crisis days",
    )
    args = ap.parse_args()
    out = args.out
    (out / "outputs").mkdir(parents=True, exist_ok=True)
    (out / "reports").mkdir(parents=True, exist_ok=True)
    repo = Path(".").resolve()

    print("loading market / dividends ...", flush=True)
    market = pd.read_csv(args.market, dtype={"code": str})
    market["date"] = pd.to_datetime(market["date"])
    required = set(ALL + ["TAIEX"])
    complete = market.groupby("date")["code"].apply(lambda s: required.issubset(set(s)))
    keep = complete[complete].index
    market = market[market["date"].isin(keep)].sort_values(["date", "code"])
    dividends = pd.read_csv(args.dividends, dtype={"code": str}) if args.dividends.exists() else pd.DataFrame()

    print("building causal E16 targets ...", flush=True)
    _p, _sleeve, target, regime = e16_features(market)
    regime_share = regime.value_counts(normalize=True).to_dict()

    variants = {
        "E16_E18": dict(apply_e22=False, e45_crisis_equity_scale=None),
        "E16_E18_E22": dict(apply_e22=True, e45_crisis_equity_scale=None),
        "E16_E18_E22_E45PROXY": dict(
            apply_e22=True, e45_crisis_equity_scale=args.e45_crisis_equity_scale
        ),
    }
    results = {}
    for name, cfg in variants.items():
        print(f"simulating {name} ...", flush=True)
        nav, fills, meta = simulate_core(
            market, target, regime, dividends, capital=args.capital, **cfg
        )
        stats = nav_stats(nav)
        nav.to_csv(out / "outputs" / f"{name.lower()}_daily_nav.csv", index=False)
        fills.to_csv(out / "outputs" / f"{name.lower()}_fills.csv", index=False)
        results[name] = {"stats": stats, "meta": meta, **cfg}
        print(
            f"  {name}: CAGR={stats['cagr']:.4f} MDD={stats['max_drawdown']:.4f} "
            f"util={stats['utility']:.4f} fills={meta['n_fills']} div$={meta['dividend_cash_total']:.0f}",
            flush=True,
        )

    e45_audit = verify_e45_claim(repo)
    # compare E22 incremental
    a = results["E16_E18"]["stats"]
    b = results["E16_E18_E22"]["stats"]
    c = results["E16_E18_E22_E45PROXY"]["stats"]

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "EARLY_STACK_COMBINED_NAV_CHALLENGER",
        "governance": {
            "modifies_soft_frozen_files": False,
            "e16_e18_e22_e45_inplace_edit": False,
            "e45_proxy_is_official": False,
            "label": "EXPERIMENTAL_CHALLENGER_SANDBOX",
        },
        "inputs": {
            "market": str(args.market),
            "dividends": str(args.dividends),
            "capital": args.capital,
            "warmup_days": WARMUP_DAYS,
            "core_universe": ALL,
        },
        "regime_share": {str(k): float(v) for k, v in regime_share.items()},
        "variants": results,
        "deltas": {
            "e22_minus_e16e18_cagr": (b["cagr"] or 0) - (a["cagr"] or 0),
            "e22_minus_e16e18_mdd": (b["max_drawdown"] or 0) - (a["max_drawdown"] or 0),
            "e45proxy_minus_e22_cagr": (c["cagr"] or 0) - (b["cagr"] or 0),
            "e45proxy_minus_e22_mdd": (c["max_drawdown"] or 0) - (b["max_drawdown"] or 0),
            "e22_dividend_cash_total": results["E16_E18_E22"]["meta"]["dividend_cash_total"],
        },
        "e45_verification": e45_audit,
        "decisions": {
            "e16_full_history_reconstruction": "DONE_IN_CHALLENGER",
            "e22_wired_into_nav_copy": "DONE_IN_CHALLENGER",
            "e45_official_module": "STILL_MISSING",
            "e45_mdd_claim_13_16": e45_audit["claim_status"],
            "combined_four_layer_engine": "PARTIAL_CORE_EXEC_DIV_PLUS_PROXY",
            "next": (
                "Keep this sandbox as the Phase-10 integration baseline. "
                "Do not promote E45PROXY. Official E45 still requires a named module "
                "and verified baseline artifact before any SOFT_FROZEN_CRITICAL challenger."
            ),
        },
    }

    (out / "reports" / "early_stack_combined_nav_summary.json").write_text(
        json.dumps(report, indent=2, default=str) + "\n"
    )

    lines = [
        "# Early-Stack Combined NAV Challenger",
        "",
        "**EXPERIMENTAL sandbox.** Does not edit E16 / E18 / E22 / E45 SOFT_FROZEN baselines.",
        "",
        "## What this closes",
        "",
        "1. **E16 full-history causal reconstruction** from `forward/e21/live_market.csv`",
        "2. **E18 Exact T+1** open fills on the reconstructed book",
        "3. **E22 dividends** credited on `cash_ex_date` into a NAV *copy*",
        "4. **E45 verification** of the −13.16% MDD claim + lineage inventory",
        "5. **E45PROXY** (challenger only): scale equity sleeve weights on E16 `Crisis` days",
        "",
        "## Results",
        "",
        "| Variant | CAGR | MDD | Util | Vol | Div cash |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name in variants:
        s = results[name]["stats"]
        div = results[name]["meta"]["dividend_cash_total"]
        lines.append(
            f"| {name} | {100*(s['cagr'] or 0):.2f}% | {100*(s['max_drawdown'] or 0):.2f}% | "
            f"{s['utility']:.4f} | {100*(s['vol'] or 0):.2f}% | {div:,.0f} |"
        )
    lines += [
        "",
        f"- E22 CAGR lift vs E16+E18: `{report['deltas']['e22_minus_e16e18_cagr']:.4%}`",
        f"- E45PROXY MDD change vs E16+E18+E22: `{report['deltas']['e45proxy_minus_e22_mdd']:.4%}`",
        "",
        "## E45 verification",
        "",
        f"- Official `e45` module paths: **{e45_audit['e45_module_paths'] or 'none'}**",
        f"- Handoff claim MDD ≈ −13.16%: **`{e45_audit['claim_status']}`**",
        f"- Lineage MDDs: E1 `{lineage_fmt(-0.1721)}`, E1.1 `{lineage_fmt(-0.1581)}`, E3 `{lineage_fmt(-0.1849)}`",
        f"- Research decision: `{e45_audit.get('research_decision')}`",
        "",
        "## Decisions",
        "",
    ]
    for k, v in report["decisions"].items():
        lines.append(f"- `{k}`: {v}")
    lines += [
        "",
        "## Explicit non-actions",
        "",
        "- No in-place edit of E21 ledgers or `e21_forward_pipeline.py`",
        "- No promotion of E45PROXY to SOFT_FROZEN_CRITICAL",
        "- No A3-R1 overlay merge in this pass (core stack first)",
        "",
        "Artifact: `reports/early_stack_combined_nav_summary.json`",
        "",
    ]
    (out / "EARLY_STACK_COMBINED_NAV.md").write_text("\n".join(lines))
    print(json.dumps({"decisions": report["decisions"], "deltas": report["deltas"]}, indent=2, default=str))


def lineage_fmt(x: float) -> str:
    return f"{100*x:.2f}%"


if __name__ == "__main__":
    main()
