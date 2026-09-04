#!/usr/bin/env python3
"""Research reopen Round-2 — challenger experiments (no promotions).

Tracks:
  E22_v3  — ex-date vs payment-date credit; tax haircuts 0/10/20%
  E16/E18 — pre-registered variants V1–V3 + cost stress
  Alpha3A — causal OperatingIncome YoY + Amihud liquidity features
  G4      — deeper cash deleverage schedules on e50_stack

Does not edit SOFT_FROZEN ledgers. Does not promote.
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


FIN, TEL, ALL = core.FIN, core.TEL, core.ALL
BUY_FEE, SELL_FEE = core.BUY_FEE, core.SELL_FEE
TAX_STOCK, TAX_ETF, SLIP = core.TAX_STOCK, core.TAX_ETF, core.SLIP
CAPITAL, WARMUP = core.CAPITAL, core.WARMUP_DAYS


def nav_stats(nav: pd.Series) -> dict:
    nav = nav.dropna()
    if len(nav) < 3:
        return {"cagr": None, "mdd": None, "util": None, "n": int(len(nav))}
    r = nav.pct_change().dropna()
    years = max(len(r) / 252.0, 1e-9)
    cagr = float((nav.iloc[-1] / nav.iloc[0]) ** (1 / years) - 1)
    mdd = float((nav / nav.cummax() - 1).min())
    return {"cagr": cagr, "mdd": mdd, "util": cagr - 0.5 * abs(mdd), "n": int(len(nav)), "vol": float(r.std() * np.sqrt(252))}


def e16_features_variant(
    m: pd.DataFrame,
    *,
    crisis_pri: np.ndarray | None = None,
    score_blend: float = 0.10,
):
    """Parameterized copy of E16 feature construction (challenger only)."""
    p = m.pivot(index="date", columns="code", values="adj_close").sort_index().ffill()
    r = p.pct_change(fill_method=None).fillna(0)
    sleeve = pd.DataFrame({"Financial": r[FIN].mean(1), "Telecom": r[TEL].mean(1), "0050": r["0050"]})
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
    crisis = crisis_pri if crisis_pri is not None else np.array([0.60, 0.35, 0.05])
    pri_map = {
        "Bull": np.array([0.85, 0.05, 0.10]),
        "Crisis": crisis,
        "Bear": np.array([0.70, 0.25, 0.05]),
        "Sideways": np.array([0.85, 0.10, 0.05]),
    }
    out = []
    cur = np.array([0.9, 0.1, 0.0])
    for i, _dt in enumerate(p.index):
        rg = reg.iloc[i]
        pri = pri_map[rg]
        cand = np.maximum(pri + score_blend * np.clip(score.iloc[i].to_numpy(), -2, 2), 0)
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


def simulate_core_flex(
    market: pd.DataFrame,
    target: pd.DataFrame,
    regime: pd.Series,
    dividends: pd.DataFrame | None,
    *,
    apply_e22: bool,
    capital: float = CAPITAL,
    div_credit_on: str = "cash_ex_date",
    div_tax_haircut: float = 0.0,
    gap_trigger: float = 0.015,
    trade_frac: float = 0.75,
    trade_cap: float = 0.20,
    cost_mult: float = 1.0,
) -> tuple[pd.DataFrame, dict]:
    """Flex challenger simulator (Exact T+1 preserved)."""
    m = market.copy()
    m["date"] = pd.to_datetime(m["date"])
    closes = m.pivot(index="date", columns="code", values="close").sort_index().ffill()
    opens = m.pivot(index="date", columns="code", values="open").sort_index().ffill()
    dates = [d for d in closes.index if d in target.index]
    div_map: dict[pd.Timestamp, list[tuple[str, float]]] = {}
    if apply_e22 and dividends is not None and len(dividends):
        d = dividends.copy()
        d["code"] = d["code"].astype(str)
        d["cash_dividend"] = pd.to_numeric(d["cash_dividend"], errors="coerce")
        d["cash_ex_date"] = pd.to_datetime(d["cash_ex_date"], errors="coerce")
        d["cash_payment_date"] = pd.to_datetime(d["cash_payment_date"], errors="coerce")
        credit_col = div_credit_on
        d = d.dropna(subset=[credit_col, "cash_dividend"])
        d = d[d["code"].isin(ALL)]
        d = d[d["cash_dividend"] > 0]
        for _, row in d.iterrows():
            credit = float(row["cash_dividend"]) * (1.0 - float(div_tax_haircut))
            div_map.setdefault(pd.Timestamp(row[credit_col]).normalize(), []).append(
                (str(row["code"]), credit)
            )

    pos = {c: 0.0 for c in ALL}
    cash = float(capital)
    pending: list[dict] = []
    nav_rows = []
    same_bar = 0
    div_cash_total = 0.0
    trade_start = dates[WARMUP]

    buy_fee = BUY_FEE * cost_mult
    sell_fee = SELL_FEE * cost_mult
    tax_stock = TAX_STOCK * cost_mult
    tax_etf = TAX_ETF * cost_mult

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
            tax = tax_etf if code == "0050" else tax_stock
            fee = gross * (buy_fee if side == "BUY" else sell_fee + tax)
            if side == "BUY" and gross + fee > cash:
                q = max(0, int(cash / (fp * (1 + buy_fee))))
                gross = q * fp
                fee = gross * buy_fee
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
                fee = gross * (sell_fee + tax)
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

        vals = {c: pos[c] * float(cl[c]) for c in ALL}
        nav = cash + sum(vals.values())
        tw = target.loc[dt]
        sleeve_w = {"Financial": float(tw["Financial"]), "Telecom": float(tw["Telecom"]), "0050": float(tw["0050"])}
        sleeve_vals = {
            "Financial": sum(vals[c] for c in FIN),
            "Telecom": sum(vals[c] for c in TEL),
            "0050": vals["0050"],
        }
        pre = {k: (v / nav if nav > 0 else 0.0) for k, v in sleeve_vals.items()}
        gap = {k: sleeve_w[k] - pre[k] for k in pre}
        trade = np.zeros(3)
        if max(abs(v) for v in gap.values()) >= gap_trigger:
            trade = np.array([gap["Financial"], gap["Telecom"], gap["0050"]]) * trade_frac
            if abs(trade).sum() > trade_cap:
                trade *= trade_cap / abs(trade).sum()
        sleeve_trade = dict(zip(["Financial", "Telecom", "0050"], trade))
        for sleeve_name, codes in [("Financial", FIN), ("Telecom", TEL), ("0050", ["0050"])]:
            value = sleeve_trade[sleeve_name] * nav / len(codes)
            for c in codes:
                px = float(cl[c])
                qty = core.lot_qty(value, px)
                if qty < 1:
                    continue
                side = "BUY" if value > 0 else "SELL"
                if side == "SELL":
                    qty = min(qty, int(pos.get(c, 0)))
                if qty < 1:
                    continue
                pending.append({"signal_date": dt, "code": c, "side": side, "quantity": qty})
        nav_rows.append({"date": dt.date().isoformat(), "nav": nav, "dividend_credit": day_div})

    nav_df = pd.DataFrame(nav_rows)
    meta = {
        "exact_t1_ok": same_bar == 0,
        "same_bar_fills": same_bar,
        "dividend_cash_total": div_cash_total,
        "div_credit_on": div_credit_on,
        "div_tax_haircut": div_tax_haircut,
        "gap_trigger": gap_trigger,
        "trade_frac": trade_frac,
        "cost_mult": cost_mult,
        "n_days": len(nav_df),
    }
    return nav_df, meta


def run_e22_v3(market, dividends, out: Path) -> dict:
    _, _, target, regime = core.e16_features(market)
    books = {}
    # Baseline v2 rule: ex-date, 0 tax
    configs = [
        ("EX_DATE_TAX0", dict(div_credit_on="cash_ex_date", div_tax_haircut=0.0)),
        ("EX_DATE_TAX10", dict(div_credit_on="cash_ex_date", div_tax_haircut=0.10)),
        ("EX_DATE_TAX20", dict(div_credit_on="cash_ex_date", div_tax_haircut=0.20)),
        ("PAY_DATE_TAX0", dict(div_credit_on="cash_payment_date", div_tax_haircut=0.0)),
        ("PAY_DATE_TAX10", dict(div_credit_on="cash_payment_date", div_tax_haircut=0.10)),
    ]
    # Also no-div control
    nav0, meta0 = simulate_core_flex(
        market, target, regime, dividends, apply_e22=False
    )
    books["NO_DIV"] = {"stats": nav_stats(nav0.set_index(pd.to_datetime(nav0["date"]))["nav"]), "meta": meta0}
    nav0.to_csv(out / "e22_NO_DIV_nav.csv", index=False)

    for name, cfg in configs:
        print(f"  E22_v3 {name} ...", flush=True)
        nav, meta = simulate_core_flex(
            market, target, regime, dividends, apply_e22=True, **cfg
        )
        s = nav_stats(nav.set_index(pd.to_datetime(nav["date"]))["nav"])
        books[name] = {"stats": s, "meta": meta}
        nav.to_csv(out / f"e22_{name}_nav.csv", index=False)

    base = books["EX_DATE_TAX0"]["stats"]
    ranking = sorted(
        [(k, v["stats"]["util"]) for k, v in books.items() if v["stats"]["util"] is not None],
        key=lambda x: x[1],
        reverse=True,
    )
    best = ranking[0][0] if ranking else None
    # Promotion stance: only recommend further work if payment-date clearly beats ex-date on util+mdd
    pay = books["PAY_DATE_TAX0"]["stats"]
    ex = books["EX_DATE_TAX0"]["stats"]
    pay_beats = (
        pay["util"] is not None
        and ex["util"] is not None
        and pay["util"] > ex["util"] + 0.002
        and abs(pay["mdd"]) <= abs(ex["mdd"]) + 0.005
    )
    report = {
        "books": {k: {**v["stats"], **{f"meta_{mk}": mv for mk, mv in v["meta"].items()}} for k, v in books.items()},
        "util_ranking": ranking,
        "best_util": best,
        "pay_vs_ex": {
            "pay_util": pay["util"],
            "ex_util": ex["util"],
            "pay_mdd": pay["mdd"],
            "ex_mdd": ex["mdd"],
            "pay_beats_ex": pay_beats,
        },
        "decision": (
            "CONTINUE_V3_SANDBOX_PAY_DATE_INTERESTING"
            if pay_beats
            else "KEEP_E22_V2_EX_DATE_BASELINE"
        ),
        "promotion": False,
    }
    (out / "e22_v3_round2.json").write_text(json.dumps(report, indent=2, default=str) + "\n")
    return report


def run_e16_e18(market, dividends, out: Path) -> dict:
    variants = {
        "BASE": dict(crisis_pri=np.array([0.60, 0.35, 0.05]), gap_trigger=0.015, trade_frac=0.75, cost_mult=1.0),
        "E16_V1_crisis_tilt": dict(crisis_pri=np.array([0.55, 0.40, 0.05]), gap_trigger=0.015, trade_frac=0.75, cost_mult=1.0),
        "E16_V2_gap_020": dict(crisis_pri=np.array([0.60, 0.35, 0.05]), gap_trigger=0.020, trade_frac=0.75, cost_mult=1.0),
        "E16_V3_trade_060": dict(crisis_pri=np.array([0.60, 0.35, 0.05]), gap_trigger=0.015, trade_frac=0.60, cost_mult=1.0),
        "E18_C1_cost_1_5": dict(crisis_pri=np.array([0.60, 0.35, 0.05]), gap_trigger=0.015, trade_frac=0.75, cost_mult=1.5),
        "E18_C1_cost_2_0": dict(crisis_pri=np.array([0.60, 0.35, 0.05]), gap_trigger=0.015, trade_frac=0.75, cost_mult=2.0),
    }
    books = {}
    for name, cfg in variants.items():
        print(f"  E16/E18 {name} ...", flush=True)
        crisis = cfg.pop("crisis_pri")
        _, _, target, regime = e16_features_variant(market, crisis_pri=crisis)
        nav, meta = simulate_core_flex(
            market, target, regime, dividends, apply_e22=True, div_credit_on="cash_ex_date", **cfg
        )
        cfg["crisis_pri"] = crisis.tolist()  # restore for report
        s = nav_stats(nav.set_index(pd.to_datetime(nav["date"]))["nav"])
        books[name] = {"stats": s, "meta": meta, "cfg": {**cfg, "crisis_pri": crisis.tolist()}}
        nav.to_csv(out / f"e16e18_{name}_nav.csv", index=False)

    base_u = books["BASE"]["stats"]["util"]
    deltas = {
        k: (v["stats"]["util"] - base_u) if v["stats"]["util"] is not None and base_u is not None else None
        for k, v in books.items()
    }
    # Challenger interesting if util lift > 50bps and MDD not worse by >1pp
    interesting = []
    for k, v in books.items():
        if k == "BASE":
            continue
        if k.startswith("E18_"):
            continue  # cost stress is robustness, not promotion candidate
        su, sm = v["stats"]["util"], v["stats"]["mdd"]
        bu, bm = books["BASE"]["stats"]["util"], books["BASE"]["stats"]["mdd"]
        if su is not None and bu is not None and (su - bu) >= 0.005 and abs(sm) <= abs(bm) + 0.01:
            interesting.append(k)
    report = {
        "books": {k: v["stats"] for k, v in books.items()},
        "util_delta_vs_base": deltas,
        "interesting_challengers": interesting,
        "decision": (
            "ADVANCE_INTERESTING_VARIANTS"
            if interesting
            else "NO_E16_VARIANT_BEATS_BASE_MATERIALY"
        ),
        "promotion": False,
    }
    (out / "e16_e18_round2.json").write_text(json.dumps(report, indent=2, default=str) + "\n")
    return report


def run_alpha_3a(out: Path) -> dict:
    """Build causal feature panels (no model fit in Round-2)."""
    import polars as pl

    feat_dir = out / "alpha_3a_features"
    feat_dir.mkdir(parents=True, exist_ok=True)

    # 1) OperatingIncome YoY with available_date
    print("  3A OperatingIncome YoY ...", flush=True)
    fin = pl.scan_csv(
        "/tmp/a1/causal_financials.csv.gz",
        schema_overrides={"stock_id": pl.String},
    )
    oi = (
        fin.filter(
            (pl.col("type") == "OperatingIncome")
            & (pl.col("statement") == "income")
            & pl.col("available_date").is_not_null()
        )
        .select(
            pl.col("stock_id").alias("code"),
            pl.col("period_end"),
            pl.col("available_date"),
            pl.col("value").alias("operating_income"),
        )
        .collect(engine="streaming")
        .to_pandas()
    )
    oi["period_end"] = pd.to_datetime(oi["period_end"], errors="coerce")
    oi["available_date"] = pd.to_datetime(oi["available_date"], errors="coerce")
    oi = oi.dropna(subset=["period_end", "available_date", "operating_income"])
    oi = oi.sort_values(["code", "period_end", "available_date"])
    oi["oi_lag4"] = oi.groupby("code")["operating_income"].shift(4)
    oi["oi_yoy"] = oi["operating_income"] / oi["oi_lag4"].replace(0, np.nan) - 1
    oi = oi.dropna(subset=["oi_yoy"])
    # Point-in-time: feature usable on available_date (not period_end)
    oi_out = oi[["code", "available_date", "period_end", "operating_income", "oi_yoy"]].copy()
    oi_out.to_parquet(feat_dir / "operating_income_yoy_pit.parquet", index=False)

    # 2) Amihud 20d on PIT — sample last 5y for speed, all codes that trade
    print("  3A Amihud (2019+) ...", flush=True)
    pit = (
        pl.scan_csv("/tmp/a0/point_in_time_universe.csv", schema_overrides={"code": pl.String})
        .filter(pl.col("date") >= "2019-01-01")
        .select("date", "code", "close", "volume")
        .collect(engine="streaming")
        .to_pandas()
    )
    pit["date"] = pd.to_datetime(pit["date"])
    pit = pit.dropna(subset=["close", "volume"])
    pit = pit[pit["volume"] > 0]
    pit = pit.sort_values(["code", "date"])
    pit["ret"] = pit.groupby("code")["close"].pct_change()
    pit["dollar_vol"] = pit["close"] * pit["volume"]
    pit["amihud_1d"] = pit["ret"].abs() / pit["dollar_vol"].replace(0, np.nan)
    pit["amihud_20"] = pit.groupby("code")["amihud_1d"].transform(
        lambda s: s.rolling(20, min_periods=10).mean()
    )
    # Causal: feature on T uses data through T (rolling ends at T) — OK for same-day signal if execution T+1
    # Shift 1 day so signal(T) uses amihud through T-1
    pit["amihud_20_lag1"] = pit.groupby("code")["amihud_20"].shift(1)
    ami = pit.dropna(subset=["amihud_20_lag1"])[["date", "code", "amihud_20_lag1", "ret"]]
    # Downsample to monthly last for storage
    ami["ym"] = ami["date"].dt.to_period("M")
    ami_m = ami.sort_values("date").groupby(["code", "ym"], as_index=False).tail(1)
    ami_m.to_parquet(feat_dir / "amihud_20_lag1_monthly.parquet", index=False)

    # Coverage / leakage checklist
    checklist = {
        "operating_income_yoy": {
            "n_rows": int(len(oi_out)),
            "n_codes": int(oi_out["code"].nunique()),
            "date_min": str(oi_out["available_date"].min().date()),
            "date_max": str(oi_out["available_date"].max().date()),
            "uses_available_date_not_period_end": True,
            "label_ready": False,
        },
        "amihud_20_lag1": {
            "n_rows_daily_kept_monthly": int(len(ami_m)),
            "n_codes": int(ami_m["code"].nunique()),
            "shifted_by_1_session": True,
            "window_start": "2019-01-01",
        },
        "forbidden_not_used": ["TECH2", "PRICE8", "S9A1", "A3_R1_model"],
    }
    report = {
        "features_dir": str(feat_dir),
        "checklist": checklist,
        "decision": "FEATURES_BUILT_NEXT_ROUND_IS_OOF_MODEL",
        "promotion": False,
        "next": [
            "Join features to Exact T+1 open labels on alpha universe",
            "OOF ridge/tree — no TECH2 panel",
            "one-shot held-out; stop",
        ],
    }
    (out / "alpha_3a_round2.json").write_text(json.dumps(report, indent=2, default=str) + "\n")
    return report


def run_g4(out: Path) -> dict:
    mix_path = Path("forward/e50_stack/nav_combined.csv")
    if not mix_path.exists():
        return {"decision": "MISSING_E50_STACK", "promotion": False}
    d = pd.read_csv(mix_path, parse_dates=["date"]).set_index("date")
    r = d["ret_combined"].astype(float)
    exp = d["exposure_e45"].astype(float)
    schedules = {
        "BASE_alpha_cut": r,
        "H1_scale_by_exp": r * exp,
        "H1_scale_by_exp_sq": r * (exp ** 2),
        "H1_floor_exp_0_70": r * exp.clip(lower=0.70),  # less aggressive
        "H1_crisis_half_when_exp_lt_085": r * np.where(exp < 0.85, 0.5, 1.0),
    }
    books = {}
    for name, rr in schedules.items():
        nav = (1 + pd.Series(rr, index=r.index)).cumprod()
        books[name] = nav_stats(nav)
        pd.DataFrame({"date": nav.index, "nav": nav.values}).to_csv(out / f"g4_{name}_nav.csv", index=False)
    base = books["BASE_alpha_cut"]
    # Prefer schedule with better util than base and not much worse bull (approx full-sample)
    better = [
        k
        for k, v in books.items()
        if k != "BASE_alpha_cut"
        and v["util"] is not None
        and base["util"] is not None
        and v["util"] >= base["util"]
        and abs(v["mdd"]) <= abs(base["mdd"]) + 0.01
    ]
    report = {
        "books": books,
        "better_or_equal_util": better,
        "decision": "KEEP_BASE_ALPHA_CUT" if not better else f"H1_CANDIDATES:{better}",
        "promotion": False,
        "note": "Cash deleverage only; no short instrument book yet.",
    }
    (out / "g4_round2.json").write_text(json.dumps(report, indent=2, default=str) + "\n")
    return report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("repro/research-reopen-round2-20260904"))
    ap.add_argument("--market", type=Path, default=Path("forward/e21/live_market.csv"))
    ap.add_argument("--dividends", type=Path, default=Path("data/dividend_events/e22_dividend_events.csv"))
    args = ap.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    Path("research/reopen").mkdir(parents=True, exist_ok=True)

    print("loading market/dividends ...", flush=True)
    market = pd.read_csv(args.market, dtype={"code": str})
    market["date"] = pd.to_datetime(market["date"])
    dividends = pd.read_csv(args.dividends, dtype={"code": str})

    print("=== E22_v3 ===", flush=True)
    e22 = run_e22_v3(market, dividends, out)
    print("=== E16/E18 ===", flush=True)
    e16 = run_e16_e18(market, dividends, out)
    print("=== Alpha 3A features ===", flush=True)
    a3 = run_alpha_3a(out)
    print("=== G4 ===", flush=True)
    g4 = run_g4(out)

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "round": 2,
        "promotion_any": False,
        "prior_decision": "DECISION_NO_PROMOTIONS_20260904",
        "tracks": {
            "e22_v3": {"decision": e22["decision"], "best": e22.get("best_util"), "pay_beats_ex": e22["pay_vs_ex"]["pay_beats_ex"]},
            "e16_e18": {"decision": e16["decision"], "interesting": e16["interesting_challengers"], "deltas": e16["util_delta_vs_base"]},
            "alpha_3a": {"decision": a3["decision"], "features_dir": a3["features_dir"]},
            "g4_hedge": {"decision": g4["decision"], "better": g4.get("better_or_equal_util")},
            "e45": {"decision": "STILL_NO_PROMOTION_KEEP_B"},
        },
    }
    (out / "ROUND2_SUMMARY.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
    Path("research/reopen/ROUND2_SUMMARY.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")

    lines = [
        "# Research Reopen — Round 2 Summary",
        "",
        "Challenger experiments only. **No promotions** (prior delegated decision stands).",
        "",
        "| Track | Decision |",
        "|---|---|",
        f"| E22_v3 | `{e22['decision']}` |",
        f"| E16/E18 | `{e16['decision']}` interesting=`{e16['interesting_challengers']}` |",
        f"| Alpha 3A | `{a3['decision']}` |",
        f"| G4 | `{g4['decision']}` |",
        f"| E45 | `STILL_NO_PROMOTION_KEEP_B` |",
        "",
        f"Artifacts: `{out}/`",
        "",
    ]
    md = "\n".join(lines)
    (out / "ROUND2_SUMMARY.md").write_text(md)
    Path("research/reopen/ROUND2_SUMMARY.md").write_text(md)
    print(json.dumps(summary["tracks"], indent=2, default=str))


if __name__ == "__main__":
    main()
