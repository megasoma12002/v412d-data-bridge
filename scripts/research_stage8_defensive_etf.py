#!/usr/bin/env python3
"""Stage 8 sandbox — defensive ETF sleeve challenger (NO promote).

Question: can a non-0050 ETF improve early-stack util/MDD vs official 3-sleeve?

Pre-registered books (≤3):
  BASE            E16+E18+E22 ex-date (Financial / Telecom / 0050)
  SLEEVE4_0056    add 0056 as 4th sleeve with Bear/Crisis-friendly priors
  RISKOFF_0056    keep 3-sleeve scores; in Bear/Crisis shift weight into 0056

ETF: 0056 (high-div; history covers full stack window). 006208 fetched as
negative-control note only (another broad-market clone — not a book).

PIT notes:
  - 0056 joined from FinMind daily; ranking uses close returns (no adj_close
    in free feed) → conservative for a high-div ETF.
  - Exact T+1 preserved; 0056 taxed as ETF.
  - Does not edit E22_v2 / E21 ledgers.

Bar (same as H1/S7): util > BASE + 0.002 and |MDD| ≤ |BASE MDD| + 0.005.
Sealed 2025+ diagnostic only. promotion=false.
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e50_early_stack_combined_nav as core

FIN, TEL = core.FIN, core.TEL
BUY_FEE, SELL_FEE = core.BUY_FEE, core.SELL_FEE
TAX_STOCK, TAX_ETF, SLIP = core.TAX_STOCK, core.TAX_ETF, core.SLIP
CAPITAL, WARMUP = core.CAPITAL, core.WARMUP_DAYS

UTIL_EPS = 0.002
MDD_EPS = 0.005
OUT_DEFAULT = Path("repro/stage8-defensive-etf-20260904")
DEF_CODE = "0056"


def nav_stats(nav: pd.Series) -> dict:
    nav = nav.dropna()
    if len(nav) < 3:
        return {"cagr": None, "mdd": None, "util": None, "n": int(len(nav)), "vol": None}
    r = nav.pct_change().dropna()
    years = max(len(r) / 252.0, 1e-9)
    cagr = float((nav.iloc[-1] / nav.iloc[0]) ** (1 / years) - 1)
    mdd = float((nav / nav.cummax() - 1).min())
    return {
        "cagr": cagr,
        "mdd": mdd,
        "util": cagr - 0.5 * abs(mdd),
        "n": int(len(nav)),
        "vol": float(r.std() * np.sqrt(252)),
    }


def load_etf_ohlcv(path: Path, code: str) -> pd.DataFrame:
    raw = pd.read_csv(path)
    raw["date"] = pd.to_datetime(raw["date"], errors="coerce")
    out = pd.DataFrame(
        {
            "date": raw["date"],
            "code": code,
            "open": pd.to_numeric(raw["open"], errors="coerce"),
            "high": pd.to_numeric(raw.get("max", raw.get("high")), errors="coerce"),
            "low": pd.to_numeric(raw.get("min", raw.get("low")), errors="coerce"),
            "close": pd.to_numeric(raw["close"], errors="coerce"),
            "volume": pd.to_numeric(raw.get("Trading_Volume", raw.get("volume")), errors="coerce"),
        }
    )
    out["adj_close"] = out["close"]  # conservative: no adj feed
    return out.dropna(subset=["date", "open", "close"])


def merge_market(base: pd.DataFrame, etf: pd.DataFrame) -> pd.DataFrame:
    m = pd.concat([base, etf], ignore_index=True)
    m["code"] = m["code"].astype(str)
    m["date"] = pd.to_datetime(m["date"])
    return m.sort_values(["date", "code"]).drop_duplicates(["date", "code"], keep="last")


def e16_features_3(m: pd.DataFrame):
    return core.e16_features(m)


def e16_features_4(m: pd.DataFrame, def_code: str = DEF_CODE):
    """4-sleeve E16-style targets; DEF gets higher Bear/Crisis prior."""
    p = m.pivot(index="date", columns="code", values="adj_close").sort_index().ffill()
    need = FIN + TEL + ["0050", def_code, "TAIEX"]
    for c in need:
        if c not in p.columns:
            raise RuntimeError(f"missing code in panel: {c}")
    r = p.pct_change(fill_method=None).fillna(0)
    sleeve = pd.DataFrame(
        {
            "Financial": r[FIN].mean(1),
            "Telecom": r[TEL].mean(1),
            "0050": r["0050"],
            "DEF": r[def_code],
        }
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
    # Pre-registered regime priors (Financial, Telecom, 0050, DEF)
    pri_map = {
        "Bull": np.array([0.80, 0.05, 0.10, 0.05]),
        "Sideways": np.array([0.75, 0.10, 0.05, 0.10]),
        "Bear": np.array([0.55, 0.15, 0.05, 0.25]),
        "Crisis": np.array([0.40, 0.20, 0.05, 0.35]),
    }
    out = []
    cur = np.array([0.85, 0.10, 0.05, 0.0])
    for i, _dt in enumerate(p.index):
        rg = reg.iloc[i]
        pri = pri_map[rg]
        cand = np.maximum(pri + 0.10 * np.clip(score.iloc[i].to_numpy(), -2, 2), 0)
        cand[0] = np.clip(cand[0], 0.35, 0.95)
        cand[1] = np.clip(cand[1], 0.03, 0.35)
        cand[2] = np.clip(cand[2], 0.0, 0.35)
        cand[3] = np.clip(cand[3], 0.0, 0.45)
        cand /= cand.sum()
        desired = 0.75 * cur + 0.25 * cand
        if np.abs(desired - cur).sum() >= 0.02:
            cur = desired
        out.append(cur.copy())
    target = pd.DataFrame(out, index=p.index, columns=["Financial", "Telecom", "0050", "DEF"])
    return p, sleeve, target, reg


def riskoff_targets(target3: pd.DataFrame, regime: pd.Series, shift: float = 0.25) -> pd.DataFrame:
    """Pre-registered: in Bear/Crisis move `shift` of Financial weight into DEF(0056)."""
    rows = []
    for dt, tw in target3.iterrows():
        rg = regime.loc[dt]
        fin, tel, e50 = float(tw["Financial"]), float(tw["Telecom"]), float(tw["0050"])
        def_w = 0.0
        if rg in ("Bear", "Crisis"):
            move = min(shift, fin - 0.35)  # keep Financial floor ~0.35
            move = max(move, 0.0)
            fin -= move
            def_w = move
        s = fin + tel + e50 + def_w
        rows.append({"Financial": fin / s, "Telecom": tel / s, "0050": e50 / s, "DEF": def_w / s})
    return pd.DataFrame(rows, index=target3.index)


def lot_qty(value: float, price: float) -> int:
    if price <= 0 or not math.isfinite(price):
        return 0
    return int(abs(value) / price)


def simulate_flex(
    market: pd.DataFrame,
    target: pd.DataFrame,
    regime: pd.Series,
    dividends: pd.DataFrame | None,
    *,
    sleeve_codes: dict[str, list[str]],
    apply_e22: bool = True,
) -> tuple[pd.DataFrame, dict]:
    """Exact T+1 simulator for 3 or 4 sleeves."""
    universe = sorted({c for codes in sleeve_codes.values() for c in codes})
    etf_codes = {c for c in universe if c.startswith("00")}
    m = market.copy()
    m["date"] = pd.to_datetime(m["date"])
    closes = m.pivot(index="date", columns="code", values="close").sort_index().ffill()
    opens = m.pivot(index="date", columns="code", values="open").sort_index().ffill()
    dates = [d for d in closes.index if d in target.index]
    if len(dates) < WARMUP + 10:
        raise RuntimeError("insufficient history")

    div_map: dict[pd.Timestamp, list[tuple[str, float]]] = {}
    if apply_e22 and dividends is not None and len(dividends):
        d = dividends.copy()
        d["code"] = d["code"].astype(str)
        d["cash_ex_date"] = pd.to_datetime(d["cash_ex_date"], errors="coerce")
        d["cash_dividend"] = pd.to_numeric(d["cash_dividend"], errors="coerce")
        d = d.dropna(subset=["cash_ex_date", "cash_dividend"])
        d = d[d["code"].isin(universe)]
        for _, row in d.iterrows():
            div_map.setdefault(pd.Timestamp(row["cash_ex_date"]).normalize(), []).append(
                (str(row["code"]), float(row["cash_dividend"]))
            )

    pos = {c: 0.0 for c in universe}
    cash = float(CAPITAL)
    pending: list[dict] = []
    nav_rows = []
    same_bar = 0
    div_cash_total = 0.0
    trade_start = dates[WARMUP]
    sleeve_names = list(target.columns)

    for dt in dates:
        if dt < trade_start:
            continue
        op = opens.loc[dt]
        cl = closes.loc[dt]
        still = []
        for o in pending:
            if pd.Timestamp(o["signal_date"]) >= dt:
                still.append(o)
                continue
            side, code, q = o["side"], o["code"], int(o["quantity"])
            fp = float(op[code]) * (1 + SLIP if side == "BUY" else 1 - SLIP)
            gross = q * fp
            tax = TAX_ETF if code in etf_codes else TAX_STOCK
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
            if pd.Timestamp(o["signal_date"]).normalize() >= dt.normalize():
                same_bar += 1
        pending = still

        day_div = 0.0
        if apply_e22:
            for code, cdiv in div_map.get(pd.Timestamp(dt).normalize(), []):
                sh = pos.get(code, 0.0)
                if sh > 0 and cdiv > 0:
                    credit = sh * cdiv
                    cash += credit
                    day_div += credit
                    div_cash_total += credit

        vals = {c: pos[c] * float(cl[c]) for c in universe}
        nav = cash + sum(vals.values())
        tw = target.loc[dt]
        sleeve_w = {k: float(tw[k]) for k in sleeve_names}
        sleeve_vals = {
            name: sum(vals[c] for c in sleeve_codes[name] if c in vals) for name in sleeve_names
        }
        pre = {k: (v / nav if nav > 0 else 0.0) for k, v in sleeve_vals.items()}
        gap = {k: sleeve_w[k] - pre[k] for k in pre}
        trade = np.array([gap[k] for k in sleeve_names])
        if max(abs(v) for v in gap.values()) >= 0.015:
            trade = trade * 0.75
            if abs(trade).sum() > 0.20:
                trade *= 0.20 / abs(trade).sum()
        else:
            trade = np.zeros(len(sleeve_names))

        for name, tr in zip(sleeve_names, trade):
            codes = sleeve_codes[name]
            value = float(tr) * nav / len(codes)
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
                pending.append({"signal_date": dt, "code": c, "side": side, "quantity": qty})

        row = {
            "date": dt.date().isoformat(),
            "nav": nav,
            "cash": cash,
            "regime": regime.loc[dt],
            "dividend_credit": day_div,
            "w_def": pre.get("DEF", 0.0),
            "tgt_def": sleeve_w.get("DEF", 0.0),
        }
        nav_rows.append(row)

    nav_df = pd.DataFrame(nav_rows)
    meta = {
        "exact_t1_ok": same_bar == 0,
        "same_bar_fills": same_bar,
        "dividend_cash_total": div_cash_total,
        "n_days": len(nav_df),
        "mean_tgt_def": float(nav_df["tgt_def"].mean()) if len(nav_df) and "tgt_def" in nav_df else 0.0,
        "mean_w_def": float(nav_df["w_def"].mean()) if len(nav_df) and "w_def" in nav_df else 0.0,
    }
    return nav_df, meta


def beats(ch: dict, base: dict) -> bool:
    if None in (ch.get("util"), base.get("util"), ch.get("mdd"), base.get("mdd")):
        return False
    return ch["util"] > base["util"] + UTIL_EPS and abs(ch["mdd"]) <= abs(base["mdd"]) + MDD_EPS


def slice_stats(nav_df: pd.DataFrame, start: str | None = None) -> dict:
    s = nav_df.set_index(pd.to_datetime(nav_df["date"]))["nav"]
    if start:
        s = s[s.index >= pd.Timestamp(start)]
    return nav_stats(s)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", default="forward/e21/live_market.csv")
    ap.add_argument("--dividends", default="data/dividend_events/e22_dividend_events.csv")
    ap.add_argument("--etf-0056", default="data/research_advanced/defensive_etf/0056_ohlcv.csv")
    ap.add_argument("--out", default=str(OUT_DEFAULT))
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    base_m = pd.read_csv(args.market, dtype={"code": str})
    base_m["date"] = pd.to_datetime(base_m["date"])
    etf = load_etf_ohlcv(Path(args.etf_0056), DEF_CODE)
    market = merge_market(base_m, etf)
    dividends = pd.read_csv(args.dividends, dtype={"code": str})

    print("building targets ...", flush=True)
    _p3, _s3, target3, regime = e16_features_3(market)
    _p4, _s4, target4, regime4 = e16_features_4(market, DEF_CODE)
    # align regime from 4-sleeve builder (same TAIEX rules)
    regime = regime4.reindex(target3.index).ffill()
    target_risk = riskoff_targets(target3, regime, shift=0.25)

    sleeve3 = {"Financial": FIN, "Telecom": TEL, "0050": ["0050"]}
    sleeve4 = {"Financial": FIN, "Telecom": TEL, "0050": ["0050"], "DEF": [DEF_CODE]}

    books_cfg = [
        ("BASE", target3, sleeve3),
        ("SLEEVE4_0056", target4, sleeve4),
        ("RISKOFF_0056", target_risk, sleeve4),
    ]
    books = {}
    for name, tgt, sleeves in books_cfg:
        print(f"run {name} ...", flush=True)
        # ensure target columns match sleeves
        nav, meta = simulate_flex(market, tgt, regime, dividends, sleeve_codes=sleeves, apply_e22=True)
        books[name] = {
            "stats_full": slice_stats(nav),
            "stats_sealed_2025p": slice_stats(nav, start="2025-01-01"),
            "meta": meta,
        }
        nav.to_csv(out / f"{name}_nav.csv", index=False)

    base = books["BASE"]["stats_full"]
    interesting = [n for n in ("SLEEVE4_0056", "RISKOFF_0056") if beats(books[n]["stats_full"], base)]
    exact_ok = all(books[n]["meta"]["exact_t1_ok"] for n in books)

    if interesting and exact_ok:
        decision = "STAGE8_DEFENSIVE_ETF_INTERESTING_CONTINUE_SANDBOX"
        stance = (
            f"{', '.join(interesting)} clear util/MDD bar vs BASE; still NO auto-promote. "
            "Next would be cost/liquidity stress + dividend-adjusted 0056 ranking — not live cutover."
        )
    else:
        decision = "STOP_STAGE8_DEFENSIVE_ETF_SLEEVE"
        stance = (
            "Neither SLEEVE4_0056 nor RISKOFF_0056 clears pre-registered bar vs BASE "
            "(or Exact T+1 failed). Do not retune priors/shift after sealed look."
        )

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stage": 8,
        "probe": "defensive_etf_0056_sleeve",
        "contract": "EXPERIMENTAL_SANDBOX_NO_PROMOTE",
        "etf_primary": DEF_CODE,
        "etf_note": "006208 fetched as broad-market clone control material only — not a book",
        "params": {
            "util_eps": UTIL_EPS,
            "mdd_eps": MDD_EPS,
            "riskoff_shift_from_financial": 0.25,
            "sleeve4_crisis_def_prior": 0.35,
            "0056_adj_close": "proxy_equals_close_conservative",
        },
        "books": books,
        "interesting_modes": interesting,
        "exact_t1_ok": exact_ok,
        "decision": decision,
        "stance": stance,
        "promotion": False,
        "e22_v2_untouched": True,
    }
    (out / "stage8_defensive_etf_report.json").write_text(json.dumps(report, indent=2, default=str) + "\n")

    md = f"""# Stage 8 Decision — Defensive ETF sleeve (0056)

Date: **2026-09-04**  
Probe: add high-div ETF **0056** vs official 3-sleeve early-stack (E16+E18+E22)  
Artifacts: `{out}/`

## Pre-registered books
| Book | Rule |
|---|---|
| BASE | Financial / Telecom / 0050 |
| SLEEVE4_0056 | 4th sleeve DEF=0056; Bear/Crisis priors up to ~25–35% |
| RISKOFF_0056 | In Bear/Crisis shift 25% of Financial weight → 0056 |

Bar: util > BASE + {UTIL_EPS}, |MDD| ≤ |BASE MDD| + {MDD_EPS}. Exact T+1 required.

## Full-sample

| Book | CAGR | MDD | Util | mean tgt DEF |
|---|---:|---:|---:|---:|
| BASE | {books['BASE']['stats_full']['cagr']:.4f} | {books['BASE']['stats_full']['mdd']:.4f} | {books['BASE']['stats_full']['util']:.4f} | 0 |
| SLEEVE4_0056 | {books['SLEEVE4_0056']['stats_full']['cagr']:.4f} | {books['SLEEVE4_0056']['stats_full']['mdd']:.4f} | {books['SLEEVE4_0056']['stats_full']['util']:.4f} | {books['SLEEVE4_0056']['meta']['mean_tgt_def']:.3f} |
| RISKOFF_0056 | {books['RISKOFF_0056']['stats_full']['cagr']:.4f} | {books['RISKOFF_0056']['stats_full']['mdd']:.4f} | {books['RISKOFF_0056']['stats_full']['util']:.4f} | {books['RISKOFF_0056']['meta']['mean_tgt_def']:.3f} |

Exact T+1: **{'PASS' if exact_ok else 'FAIL'}**

## Sealed 2025+ util (diagnostic)

| Book | Util |
|---|---:|
| BASE | {books['BASE']['stats_sealed_2025p']['util']:.4f} |
| SLEEVE4_0056 | {books['SLEEVE4_0056']['stats_sealed_2025p']['util']:.4f} |
| RISKOFF_0056 | {books['RISKOFF_0056']['stats_sealed_2025p']['util']:.4f} |

## Decision: `{decision}`

{stance}

Promotion: **false**. Official path remains E22_v2 (8 names).  
Limitation: 0056 ranking/execution uses raw close (no adj_close) — conservative for high-div ETF.
"""
    (out / "STAGE8_DECISION.md").write_text(md)
    Path("research/reopen/STAGE8_DECISION.md").parent.mkdir(parents=True, exist_ok=True)
    Path("research/reopen/STAGE8_DECISION.md").write_text(md)
    print(json.dumps({"decision": decision, "interesting": interesting, "exact_t1_ok": exact_ok}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
