#!/usr/bin/env python3
"""0050 BUY fill Stage A — adj metric fix + slew sensitivity (paper only).

Charter: research/ops/ETF0050_BUY_FILL_STAGEA_CHARTER.md
Soft-Frozen KEEP · Exact T+1 KEEP · no live wire.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import live_cool_c8_cutover as cool_cut
import live_dh_fuse_cutover as fuse_cut
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, load_market, window_stats
from live_fill_extreme_audit import N_GRID, _window_ext
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "etf0050-buy-fill-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "ETF0050_BUY_FILL_STAGEA_CHARTER"
SCREEN_ID = "ETF0050_BUY_FILL_STAGEA_SCREEN"
DECISION_ID = "ETF0050_BUY_FILL_STAGEA_DECISION_PACK"
BOOK_ID = "LIVE_FUSE_ADDITIVE_SELL_a75_COOL_c8"
HELDOUT = "heldout_2019_plus"
CODE = "0050"

FILL_IMPROVE_PP = 0.25
MDD_SLACK_PP = -0.50
CAGR_GIVEBACK_MAX_PP = 0.50

SLEW_ABS = (0.005, 0.010, 0.020)
SLEW_FRAC = (0.25, 0.50)


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ohlc_raw(market: pd.DataFrame, code: str) -> pd.DataFrame:
    m = market[market["code"].astype(str) == str(code)].copy()
    m["date"] = pd.to_datetime(m["date"]).dt.normalize()
    m = m.drop_duplicates("date").sort_values("date").set_index("date")
    for col in ("open", "high", "low", "close"):
        if col not in m.columns:
            m[col] = np.nan
    return m[["open", "high", "low", "close"]].astype(float)


def _ohlc_adj(market: pd.DataFrame, code: str) -> pd.DataFrame:
    """Scale OHLC by adj_close/close so split days stay continuous."""
    m = market[market["code"].astype(str) == str(code)].copy()
    m["date"] = pd.to_datetime(m["date"]).dt.normalize()
    m = m.drop_duplicates("date").sort_values("date").set_index("date")
    for col in ("open", "high", "low", "close", "adj_close"):
        if col not in m.columns:
            m[col] = np.nan
    close = m["close"].astype(float)
    adj = m["adj_close"].astype(float)
    factor = adj / close.replace(0, np.nan)
    factor = factor.ffill().bfill().fillna(1.0)
    out = pd.DataFrame(index=m.index)
    for col in ("open", "high", "low", "close"):
        out[col] = m[col].astype(float) * factor
    # Prefer adj_close as close when present
    out["close"] = adj.where(adj.notna(), out["close"])
    return out


def _dist(panel: pd.DataFrame, fill_d: pd.Timestamp, side: str, px: float, n: int) -> float | None:
    lo, hi, _ = _window_ext(panel, fill_d, n)
    if lo is None or hi is None or lo <= 0 or hi <= 0:
        return None
    if side == "BUY":
        return (px - lo) / lo * 100.0
    return (hi - px) / hi * 100.0


def _t1_drag(panel: pd.DataFrame, sig_d: pd.Timestamp, side: str, px: float) -> float | None:
    if panel.empty or sig_d not in panel.index:
        return None
    s_low = float(panel.loc[sig_d, "low"])
    s_high = float(panel.loc[sig_d, "high"])
    if side == "BUY" and s_low > 0:
        return (px - s_low) / s_low * 100.0
    if side == "SELL" and s_high > 0:
        return (s_high - px) / s_high * 100.0
    return None


def _annotate_fills(
    fills: pd.DataFrame,
    *,
    raw_panel: pd.DataFrame,
    adj_panel: pd.DataFrame,
    cool: pd.Series,
) -> pd.DataFrame:
    rows = []
    for _, f in fills.iterrows():
        code = str(f["code"])
        if code != CODE:
            continue
        side = str(f["side"]).upper()
        px = float(f["fill_price"])
        sig_d = pd.Timestamp(f["signal_date"]).normalize()
        fill_d = pd.Timestamp(f["fill_date"]).normalize()
        # scale fill px onto adj plane via same-day factor
        if fill_d in adj_panel.index and fill_d in raw_panel.index:
            raw_c = float(raw_panel.loc[fill_d, "close"])
            adj_c = float(adj_panel.loc[fill_d, "close"])
            fac = adj_c / raw_c if raw_c > 0 else 1.0
        else:
            fac = 1.0
        px_adj = px * fac
        cool_exp = None
        if sig_d in cool.index and pd.notna(cool.loc[sig_d]):
            cool_exp = float(cool.loc[sig_d])
        else:
            prior = cool.index[cool.index <= sig_d]
            if len(prior):
                cool_exp = float(cool.loc[prior[-1]])
        row = {
            "signal_date": sig_d,
            "fill_date": fill_d,
            "side": side,
            "quantity": int(f["quantity"]),
            "fill_price": px,
            "fill_price_adj": px_adj,
            "cool_exposure": cool_exp,
            "defense_cool": bool(cool_exp is not None and cool_exp < 1.0 - 1e-12),
            "t1_raw": _t1_drag(raw_panel, sig_d, side, px),
            "t1_adj": _t1_drag(adj_panel, sig_d, side, px_adj),
        }
        for n in N_GRID:
            row[f"n{n}_raw"] = _dist(raw_panel, fill_d, side, px, n)
            row[f"n{n}_adj"] = _dist(adj_panel, fill_d, side, px_adj, n)
        rows.append(row)
    return pd.DataFrame(rows)


def _stats(sub: pd.DataFrame, col: str = "n5_adj") -> dict[str, Any]:
    if sub is None or sub.empty:
        return {"n": 0}
    s = pd.to_numeric(sub[col], errors="coerce").dropna()
    t1 = pd.to_numeric(sub.get("t1_adj"), errors="coerce").dropna()
    out: dict[str, Any] = {
        "n": int(len(sub)),
        "mean": round(float(s.mean()), 4) if len(s) else None,
        "median": round(float(s.median()), 4) if len(s) else None,
        "p90": round(float(s.quantile(0.90)), 4) if len(s) else None,
        "share_le3": round(float((s <= 3.0).mean()), 4) if len(s) else None,
        "mean_t1": round(float(t1.mean()), 4) if len(t1) else None,
    }
    return out


def _window_mask(dates: pd.Series, a: date | None, b: date | None) -> pd.Series:
    d = pd.to_datetime(dates).dt.date
    ok = pd.Series(True, index=dates.index)
    if a is not None:
        ok &= d >= a
    if b is not None:
        ok &= d <= b
    return ok


def _strata(detail: pd.DataFrame) -> dict[str, Any]:
    buy = detail[detail["side"] == "BUY"]
    sell = detail[detail["side"] == "SELL"]
    out: dict[str, Any] = {
        "buy": _stats(buy),
        "sell": _stats(sell),
        "buy_raw": _stats(buy, "n5_raw"),
        "sell_raw": _stats(sell, "n5_raw"),
        "windows": {},
        "cool": {
            "buy_on": _stats(buy[buy["defense_cool"]]),
            "buy_off": _stats(buy[~buy["defense_cool"]]),
            "sell_on": _stats(sell[sell["defense_cool"]]),
            "sell_off": _stats(sell[~sell["defense_cool"]]),
        },
        "t1_buckets_buy": {},
        "qty_tercile_buy": {},
    }
    for wname, (a, b) in WINDOWS_STANDARD.items():
        wb = buy[_window_mask(buy["fill_date"], a, b)]
        ws = sell[_window_mask(sell["fill_date"], a, b)]
        out["windows"][wname] = {
            "buy_adj": _stats(wb),
            "sell_adj": _stats(ws),
            "buy_raw": _stats(wb, "n5_raw"),
        }
    # T+1 buckets on BUY adj
    t1 = buy["t1_adj"]
    edges = [(-np.inf, 0.5, "<=0.5"), (0.5, 1.0, "0.5-1"), (1.0, 2.0, "1-2"), (2.0, np.inf, ">2")]
    for lo, hi, lab in edges:
        if np.isfinite(hi):
            m = t1.notna() & (t1 > lo) & (t1 <= hi) if np.isfinite(lo) else t1.notna() & (t1 <= hi)
        else:
            m = t1.notna() & (t1 > lo)
        out["t1_buckets_buy"][lab] = _stats(buy[m])
    # qty terciles
    if len(buy) >= 3:
        q = buy["quantity"]
        try:
            cats = pd.qcut(q, 3, labels=["Q1_small", "Q2_mid", "Q3_large"], duplicates="drop")
            for lab in cats.astype(str).unique():
                out["qty_tercile_buy"][lab] = _stats(buy[cats == lab])
        except ValueError:
            out["qty_tercile_buy"] = {"note": "qcut_failed"}
    return out


def apply_etf_buy_slew_abs(target: pd.DataFrame, max_up: float) -> pd.DataFrame:
    t = target[["Financial", "Telecom", "0050"]].astype(float).copy()
    prev = float(t.iloc[0]["0050"])
    rows = [t.iloc[0].tolist()]
    for i in range(1, len(t)):
        fin, tel, etf = (float(t.iloc[i]["Financial"]), float(t.iloc[i]["Telecom"]), float(t.iloc[i]["0050"]))
        capped = min(etf, prev + float(max_up))
        if capped < etf - 1e-15:
            residual = etf - capped
            ft = fin + tel
            if ft > 1e-12:
                fin += residual * fin / ft
                tel += residual * tel / ft
            else:
                fin += residual
            etf = capped
            s = fin + tel + etf
            fin, tel, etf = fin / s, tel / s, etf / s
        prev = etf
        rows.append([fin, tel, etf])
    return pd.DataFrame(rows, index=t.index, columns=["Financial", "Telecom", "0050"])


def apply_etf_buy_slew_frac(target: pd.DataFrame, frac: float) -> pd.DataFrame:
    """Each day move only ``frac`` of the intended up-gap toward target 0050."""
    t = target[["Financial", "Telecom", "0050"]].astype(float).copy()
    prev = float(t.iloc[0]["0050"])
    rows = [t.iloc[0].tolist()]
    f = float(frac)
    for i in range(1, len(t)):
        fin, tel, etf_tgt = (
            float(t.iloc[i]["Financial"]),
            float(t.iloc[i]["Telecom"]),
            float(t.iloc[i]["0050"]),
        )
        if etf_tgt > prev:
            etf = prev + f * (etf_tgt - prev)
        else:
            etf = etf_tgt  # allow full down moves
        if abs(etf - etf_tgt) > 1e-15:
            residual = etf_tgt - etf
            ft = fin + tel
            if ft > 1e-12:
                fin += residual * fin / ft
                tel += residual * tel / ft
            else:
                fin += residual
            s = fin + tel + etf
            fin, tel, etf = fin / s, tel / s, etf / s
        prev = etf
        rows.append([fin, tel, etf])
    return pd.DataFrame(rows, index=t.index, columns=["Financial", "Telecom", "0050"])


def _nav_pack(nav: pd.DataFrame) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, (a, b) in WINDOWS_STANDARD.items():
        st = window_stats(nav, a, b)
        out[k] = {
            "cagr": None if st.get("cagr") is None else round(float(st["cagr"]), 6),
            "max_drawdown": None
            if st.get("max_drawdown") is None
            else round(float(st["max_drawdown"]), 6),
            "n_days": int(st.get("n_days") or 0),
        }
    return out


def _run_stack(
    market: pd.DataFrame,
    dividends: pd.DataFrame,
    target: pd.DataFrame,
    cool: pd.Series,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Simulate FUSE softs with given target + COOL exposure (reuse fuse panels)."""
    import e22_dividend_accounting as e22div
    from e50_early_stack_combined_nav import e16_features, simulate_core
    from portfolio_capital import DEFAULT_CAPITAL
    from tw_share_lots import BOARD_LOT
    from within_sleeve_alloc import FIN_PRE_EXDIV_KD, TEL_EQUAL

    _prices, _sleeve, _t0, regime = e16_features(market)
    _kd, buy_ok, buy, sell = fuse_cut._kd_panels(market, dividends)
    nav, fills, meta = simulate_core(
        market,
        target,
        regime,
        dividends,
        apply_e22=True,
        e22_version=e22div.PRESERVED_CASH_ON_EX,
        apply_stock_div=True,
        capital=float(DEFAULT_CAPITAL),
        lot_size=int(BOARD_LOT),
        financial_alloc=FIN_PRE_EXDIV_KD,
        telecom_alloc=TEL_EQUAL,
        fin_name_scores=buy,
        fin_buy_ok=buy_ok,
        fin_sell_scores=sell,
        e45_exposure=cool.astype(float),
    )
    if not bool(meta.get("exact_t1_ok")):
        raise RuntimeError("exact_t1_ok failed")
    return nav, fills, meta


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)

    print("loading market ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    raw_panel = _ohlc_raw(market, CODE)
    adj_panel = _ohlc_adj(market, CODE)

    print("base FUSE offense + COOL ...", flush=True)
    fuse_nav, _, fuse_meta = fuse_cut.build_fuse_offense_sim(market, dividends)
    cool = cool_cut.build_cool_exposure_from_offense(market, fuse_nav)
    cool.to_frame("cool_exposure").to_csv(OUT / "cool_from_fuse.csv")
    base_target = fuse_cut.fuse_target_for_market(market)
    base_nav, base_fills, base_meta = _run_stack(market, dividends, base_target, cool)
    base_nav.to_csv(OUT / "nav_base_fuse_cool.csv", index=False)
    base_fills.to_csv(OUT / "fills_base_fuse_cool.csv", index=False)

    detail = _annotate_fills(base_fills, raw_panel=raw_panel, adj_panel=adj_panel, cool=cool)
    detail.to_csv(OUT / "etf0050_fill_detail_base.csv", index=False)
    strata = _strata(detail)

    metric = {
        "buy_n": int((detail["side"] == "BUY").sum()),
        "sell_n": int((detail["side"] == "SELL").sum()),
        "buy_n5_raw": strata["buy_raw"],
        "buy_n5_adj": strata["buy"],
        "sell_n5_raw": strata["sell_raw"],
        "sell_n5_adj": strata["sell"],
        "raw_minus_adj_buy_mean": None
        if strata["buy_raw"].get("mean") is None or strata["buy"].get("mean") is None
        else round(float(strata["buy_raw"]["mean"]) - float(strata["buy"]["mean"]), 4),
        "artifact_note": (
            "2025-06-18 ~4:1 split makes raw ±5d explode; adj_close-scaled OHLC is authoritative"
        ),
    }

    base_w = _nav_pack(base_nav)
    base_buy_n5 = strata["buy"].get("mean")

    challengers: list[dict[str, Any]] = []

    def _eval(rid: str, track: str, meta: dict, target: pd.DataFrame) -> dict[str, Any]:
        print(f"  sim {rid} ...", flush=True)
        nav, fills, _m = _run_stack(market, dividends, target, cool)
        det = _annotate_fills(fills, raw_panel=raw_panel, adj_panel=adj_panel, cool=cool)
        st = _strata(det)
        buy_mean = (st["buy"] or {}).get("mean")
        fill_improve = None
        if buy_mean is not None and base_buy_n5 is not None:
            fill_improve = round(float(base_buy_n5) - float(buy_mean), 4)  # + = better
        chal_w = _nav_pack(nav)
        gb = cagr_delta_pp(
            (base_w.get(HELDOUT) or {}).get("cagr"),
            (chal_w.get(HELDOUT) or {}).get("cagr"),
            missing_as_zero=True,
        )
        md = mdd_delta_pp(
            (base_w.get(HELDOUT) or {}).get("max_drawdown"),
            (chal_w.get(HELDOUT) or {}).get("max_drawdown"),
        )
        fill_ok = fill_improve is not None and float(fill_improve) >= float(FILL_IMPROVE_PP)
        nav_ok = (
            md is not None
            and float(md) >= float(MDD_SLACK_PP)
            and (gb is None or float(gb) <= float(CAGR_GIVEBACK_MAX_PP))
        )
        row = {
            "id": rid,
            "track": track,
            "meta": meta,
            "n_fills_0050": int(len(det)),
            "n_buy": int((det["side"] == "BUY").sum()),
            "n_sell": int((det["side"] == "SELL").sum()),
            "buy_n5_adj": st["buy"],
            "sell_n5_adj": st["sell"],
            "buy_n5_raw": st["buy_raw"],
            "fill_improve_pp": fill_improve,
            "fill_gate": bool(fill_ok),
            "held_cagr_giveback_pp": None if gb is None else round(float(gb), 4),
            "held_mdd_improve_pp": None if md is None else round(float(md), 4),
            "nav_gate": bool(nav_ok),
            "hit": bool(fill_ok and nav_ok),
            "windows_nav": chal_w,
            "strata_cool": st["cool"],
            "strata_windows_buy_adj": {
                k: v.get("buy_adj") for k, v in st["windows"].items()
            },
        }
        det.to_csv(OUT / f"etf0050_fill_detail_{rid}.csv", index=False)
        return row

    print("slew absolute grid ...", flush=True)
    for step in SLEW_ABS:
        rid = f"SLEW_UP_{int(step * 10000)}bp"
        tgt = apply_etf_buy_slew_abs(base_target, step)
        challengers.append(
            _eval(rid, "SLEW_UP_ABS", {"max_up": step}, tgt)
        )

    print("slew frac grid ...", flush=True)
    for frac in SLEW_FRAC:
        rid = f"SLEW_FRAC_{int(frac * 100)}"
        tgt = apply_etf_buy_slew_frac(base_target, frac)
        challengers.append(
            _eval(rid, "SLEW_UP_FRAC", {"frac": frac}, tgt)
        )

    hits = [c for c in challengers if c.get("hit")]
    fill_only = [c for c in challengers if c.get("fill_gate") and not c.get("nav_gate")]
    if hits:
        verdict = "ETF_BUY_SLEW_HIT"
    elif fill_only:
        verdict = "FILL_BETTER_NAV_COST"
    elif (
        metric.get("raw_minus_adj_buy_mean") is not None
        and float(metric["raw_minus_adj_buy_mean"]) >= 1.0
        and not any(c.get("fill_gate") for c in challengers)
    ):
        verdict = "METRIC_ARTIFACT_ONLY"
    else:
        verdict = "NO_LIFT"

    # residual after adj: vs FIN not computed here; report buy adj mean
    payload = {
        "generated_at_utc": _utc(),
        "label": SCREEN_ID,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "status": verdict,
        "live_wire": False,
        "soft_frozen_keep": True,
        "book_id": BOOK_ID,
        "gates": {
            "fill_improve_pp": FILL_IMPROVE_PP,
            "mdd_slack_pp": MDD_SLACK_PP,
            "cagr_giveback_max_pp": CAGR_GIVEBACK_MAX_PP,
        },
        "base": {
            "fuse_offense_n_fills": fuse_meta.get("n_fills"),
            "stack_n_fills": int(len(base_fills)),
            "nav": base_w,
            "metric": metric,
            "strata": strata,
        },
        "challengers": challengers,
        "n_hit": int(len(hits)),
        "binding": [
            "Soft-Frozen live KEEP",
            "Exact T+1 KEEP",
            "No tip rewrite",
            "No live wire from Stage A",
        ],
    }
    (REP / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2) + "\n")
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2) + "\n")

    lines = [
        "# 0050 BUY fill Stage A — Screen",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Status: **`{verdict}`** · Soft-Frozen KEEP · **no live wire** · `{BOOK_ID}`",
        "",
        "## 1 — Metric fix (raw vs adj)",
        "",
        f"0050 BUY n={metric['buy_n']} · SELL n={metric['sell_n']}",
        f"BUY ±5d raw mean **{(metric['buy_n5_raw'] or {}).get('mean')}%** · "
        f"adj mean **{(metric['buy_n5_adj'] or {}).get('mean')}%** · "
        f"raw−adj **{metric.get('raw_minus_adj_buy_mean')}**",
        f"BUY ±5d adj median **{(metric['buy_n5_adj'] or {}).get('median')}%** · "
        f"SELL adj mean **{(metric['sell_n5_adj'] or {}).get('mean')}%**",
        "",
        f"_{metric['artifact_note']}_",
        "",
        "## 2 — Strata (adj ±5d)",
        "",
        "### Windows BUY",
        "",
        "| window | n | adj mean | adj med | raw mean | T+1 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for wname, w in strata["windows"].items():
        ba, br = w.get("buy_adj") or {}, w.get("buy_raw") or {}
        if not ba.get("n"):
            continue
        lines.append(
            f"| `{wname}` | {ba.get('n')} | {ba.get('mean')} | {ba.get('median')} | "
            f"{br.get('mean')} | {ba.get('mean_t1')} |"
        )

    lines += [
        "",
        "### COOL × side",
        "",
        "| slice | n | ±5 adj mean | T+1 |",
        "|---|---:|---:|---:|",
    ]
    for k, st in strata["cool"].items():
        if not st.get("n"):
            continue
        lines.append(f"| `{k}` | {st.get('n')} | {st.get('mean')} | {st.get('mean_t1')} |")

    lines += [
        "",
        "### T+1 buckets (BUY)",
        "",
        "| bucket | n | ±5 adj mean |",
        "|---|---:|---:|",
    ]
    for k, st in strata["t1_buckets_buy"].items():
        if not st.get("n"):
            continue
        lines.append(f"| {k} | {st.get('n')} | {st.get('mean')} |")

    lines += [
        "",
        "### Qty terciles (BUY)",
        "",
        "| tercile | n | ±5 adj mean | T+1 |",
        "|---|---:|---:|---:|",
    ]
    for k, st in strata["qty_tercile_buy"].items():
        if not isinstance(st, dict) or not st.get("n"):
            continue
        lines.append(f"| `{k}` | {st.get('n')} | {st.get('mean')} | {st.get('mean_t1')} |")

    lines += [
        "",
        "## 3 — Slew sensitivity",
        "",
        f"Base 0050 BUY adj ±5d mean **{base_buy_n5}%** · "
        f"fill gate improve ≥{FILL_IMPROVE_PP}pp · "
        f"NAV: MDD≥{MDD_SLACK_PP}pp & CAGR giveback≤{CAGR_GIVEBACK_MAX_PP}pp",
        "",
        "| id | track | buy n | adj ±5 | improve pp | fill | held CAGR gb | held MDD↑ | nav | HIT |",
        "|---|---|---:|---:|---:|---|---:|---:|---|---|",
    ]
    for c in challengers:
        lines.append(
            f"| `{c['id']}` | {c['track']} | {c.get('n_buy')} | "
            f"{(c.get('buy_n5_adj') or {}).get('mean')} | {c.get('fill_improve_pp')} | "
            f"{'Y' if c.get('fill_gate') else 'n'} | {c.get('held_cagr_giveback_pp')} | "
            f"{c.get('held_mdd_improve_pp')} | {'Y' if c.get('nav_gate') else 'n'} | "
            f"{'Y' if c.get('hit') else 'n'} |"
        )

    lines += [
        "",
        f"Hits: **{len(hits)}** · Verdict: **`{verdict}`**",
        "",
        "Repro: `PYTHONPATH=scripts python3 scripts/etf0050_buy_fill_stagea.py`",
        "",
        f"Label: `{SCREEN_ID}_{payload['generated_at_utc'][:10]}__{verdict}`",
        "",
    ]
    md = "\n".join(lines)
    (REP / f"{SCREEN_ID}.md").write_text(md)
    (OPS / f"{SCREEN_ID}.md").write_text(md)

    decision = {
        "label": DECISION_ID,
        "generated_at_utc": _utc(),
        "status": verdict,
        "verdict": verdict,
        "live_wire": False,
        "soft_frozen_keep": True,
        "n_hit": int(len(hits)),
        "metric": metric,
        "best_fill": max(
            challengers, key=lambda c: (c.get("fill_improve_pp") is not None, c.get("fill_improve_pp") or -9)
        )
        if challengers
        else None,
        "binding": payload["binding"],
        "next": (
            "Discussion only — HIT ⇒ optional paper observe ballot; "
            "METRIC_ARTIFACT_ONLY ⇒ keep live, fix audit metrics to adj; "
            "do not Soft-Frozen flip from this Stage A"
        ),
        "charter": f"research/ops/{CHARTER_ID}.md",
        "screen": f"research/ops/{SCREEN_ID}.md",
    }
    # JSON-serialize best_fill without huge nests
    if decision["best_fill"]:
        bf = decision["best_fill"]
        decision["best_fill"] = {
            "id": bf["id"],
            "fill_improve_pp": bf.get("fill_improve_pp"),
            "buy_n5_adj_mean": (bf.get("buy_n5_adj") or {}).get("mean"),
            "held_cagr_giveback_pp": bf.get("held_cagr_giveback_pp"),
            "held_mdd_improve_pp": bf.get("held_mdd_improve_pp"),
            "hit": bf.get("hit"),
        }
    dlines = [
        "# 0050 BUY fill Stage A — Decision Pack",
        "",
        f"Date: 2026-09-26 · Generated `{decision['generated_at_utc']}`",
        f"Status: **{verdict}`** · Soft-Frozen **KEEP** · live wire **false**",
        "",
        f"Raw−adj BUY ±5d gap **{metric.get('raw_minus_adj_buy_mean')}pp** · "
        f"adj BUY mean **{(metric.get('buy_n5_adj') or {}).get('mean')}%** · "
        f"slew hits **{len(hits)}**.",
        "",
        "## Binding",
        "",
    ] + [f"{i}. {b}" for i, b in enumerate(decision["binding"], 1)]
    dlines += [
        "",
        f"Next: {decision['next']}",
        "",
        f"Label: `{DECISION_ID}_2026-09-26__{verdict}`",
        "",
    ]
    # fix typo in status line
    dlines[3] = f"Status: **{verdict}** · Soft-Frozen **KEEP** · live wire **false**"
    for path in (OPS, REP):
        (path / f"{DECISION_ID}.json").write_text(json.dumps(decision, indent=2) + "\n")
        (path / f"{DECISION_ID}.md").write_text("\n".join(dlines) + "\n")

    (REPRO / "README.md").write_text(
        "\n".join(
            [
                "# 0050 BUY fill Stage A repro",
                "",
                f"Charter: `research/ops/{CHARTER_ID}.md`",
                f"Screen: `reports/{SCREEN_ID}.md`",
                f"Decision: `reports/{DECISION_ID}.md`",
                "",
                "```bash",
                "PYTHONPATH=scripts python3 scripts/etf0050_buy_fill_stagea.py",
                "```",
                "",
            ]
        )
    )

    print(
        json.dumps(
            {
                "verdict": verdict,
                "metric": metric,
                "n_challengers": len(challengers),
                "n_hit": len(hits),
                "challenger_summary": [
                    {
                        "id": c["id"],
                        "fill_improve_pp": c.get("fill_improve_pp"),
                        "fill_gate": c.get("fill_gate"),
                        "nav_gate": c.get("nav_gate"),
                        "hit": c.get("hit"),
                    }
                    for c in challengers
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
