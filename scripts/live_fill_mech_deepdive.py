#!/usr/bin/env python3
"""Comprehensive fill-mechanism deep dive (A–D) — observe only.

Builds on tip + backtest fill extreme audits. Soft-Frozen KEEP; no live wire.

A T+1 cost decomposition
B KD season vs off-season (FIN)
C CLIP_FIN_HI edge fills (FIN)
D COOL defend fills + offense vs COOL NAV windows
"""
from __future__ import annotations

import ast
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import live_cool_c8_cutover as cool_cut
import live_dh_fuse_cutover as fuse_cut
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, load_market, window_stats
from live_config import KD_OPT
from live_fill_extreme_audit import _agg_from_extremes, _in_kd_season
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "live-fill-extreme-audit"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "LIVE_FILL_MECH_DEEPDIVE_CHARTER"
SCREEN_ID = "LIVE_FILL_MECH_DEEPDIVE_SCREEN"
DECISION_ID = "LIVE_FILL_MECH_DEEPDIVE_DECISION_PACK"
BOOK_ID = "LIVE_FUSE_ADDITIVE_SELL_a75_COOL_c8"

TIP_DETAIL = OUT / "fill_extreme_detail.csv"
BT_DETAIL = OUT / "backtest_fill_extreme_detail.csv"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_cell(x: Any) -> Any:
    if isinstance(x, (dict, list)):
        return x
    if isinstance(x, str):
        s = x.strip()
        if not s:
            return {}
        try:
            return ast.literal_eval(s)
        except (SyntaxError, ValueError):
            try:
                return json.loads(s)
            except json.JSONDecodeError:
                return {}
    return {}


def _load_detail(path: Path, *, source: str) -> pd.DataFrame:
    assert path.exists(), f"missing {path} — run tip/backtest audit first"
    df = pd.read_csv(path, dtype={"code": str})
    df["source"] = source
    df["signal_date"] = pd.to_datetime(df["signal_date"]).dt.normalize()
    df["fill_date"] = pd.to_datetime(df["fill_date"]).dt.normalize()
    df["mechanisms"] = df["mechanisms"].map(_parse_cell)
    df["extremes"] = df["extremes"].map(_parse_cell)
    df["n5_dist"] = df["extremes"].map(
        lambda e: float(e["n5"]["dist_pct"])
        if isinstance(e, dict) and (e.get("n5") or {}).get("ok")
        else np.nan
    )
    df["n21_dist"] = df["extremes"].map(
        lambda e: float(e["n21"]["dist_pct"])
        if isinstance(e, dict) and (e.get("n21") or {}).get("ok")
        else np.nan
    )
    df["t1"] = pd.to_numeric(df["t1_drag_vs_signal_ext_pct"], errors="coerce")
    mech = df["mechanisms"]
    df["tag_kd_off"] = mech.map(lambda m: "KD_OFFSEASON" in m if isinstance(m, list) else False)
    df["tag_kd_block"] = mech.map(lambda m: "KD_BUY_BLOCK" in m if isinstance(m, list) else False)
    df["tag_clip_fin_hi"] = mech.map(lambda m: "CLIP_FIN_HI" in m if isinstance(m, list) else False)
    df["tag_clip_any"] = mech.map(
        lambda m: any(str(x).startswith("CLIP_") for x in m) if isinstance(m, list) else False
    )
    if "defense_cool" in df.columns:
        df["cool_on"] = df["defense_cool"].fillna(False).astype(bool)
    elif "defense_cool_cf" in df.columns:
        df["cool_on"] = df["defense_cool_cf"].fillna(False).astype(bool)
    else:
        df["cool_on"] = False
    if "defense_dh" in df.columns:
        df["dh_on"] = df["defense_dh"].fillna(False).astype(bool)
    elif "defense_dh_cf" in df.columns:
        df["dh_on"] = df["defense_dh_cf"].fillna(False).astype(bool)
    else:
        df["dh_on"] = False
    # KD season from calendar (independent of tip tags for backtest FIN)
    df["kd_in_season"] = df["signal_date"].map(_in_kd_season)
    return df


def _fill_stats(sub: pd.DataFrame) -> dict[str, Any]:
    if sub.empty:
        return {"n": 0}
    t1 = sub["t1"].dropna()
    n5 = sub["n5_dist"].dropna()
    n21 = sub["n21_dist"].dropna()
    out: dict[str, Any] = {
        "n": int(len(sub)),
        "n_buy": int((sub["side"] == "BUY").sum()),
        "n_sell": int((sub["side"] == "SELL").sum()),
        "mean_t1": round(float(t1.mean()), 4) if len(t1) else None,
        "median_t1": round(float(t1.median()), 4) if len(t1) else None,
        "p90_t1": round(float(t1.quantile(0.90)), 4) if len(t1) else None,
        "mean_n5": round(float(n5.mean()), 4) if len(n5) else None,
        "median_n5": round(float(n5.median()), 4) if len(n5) else None,
        "p90_n5": round(float(n5.quantile(0.90)), 4) if len(n5) else None,
        "share_n5_le1": round(float((n5 <= 1.0).mean()), 4) if len(n5) else None,
        "share_n5_le3": round(float((n5 <= 3.0).mean()), 4) if len(n5) else None,
        "mean_n21": round(float(n21.mean()), 4) if len(n21) else None,
    }
    if len(t1) and len(n5) and len(t1) == len(sub) and len(n5) == len(sub):
        out["corr_t1_n5"] = round(float(np.corrcoef(t1, n5)[0, 1]), 4)
    elif len(t1) >= 10 and len(n5) >= 10:
        both = sub.dropna(subset=["t1", "n5_dist"])
        if len(both) >= 10:
            out["corr_t1_n5"] = round(
                float(np.corrcoef(both["t1"], both["n5_dist"])[0, 1]), 4
            )
    return out


def _delta(a: dict[str, Any], b: dict[str, Any], key: str) -> float | None:
    if a.get(key) is None or b.get(key) is None:
        return None
    return round(float(a[key]) - float(b[key]), 4)


def _window_mask(dates: pd.Series, a: date | None, b: date | None) -> pd.Series:
    d = pd.to_datetime(dates).dt.date
    ok = pd.Series(True, index=dates.index)
    if a is not None:
        ok &= d >= a
    if b is not None:
        ok &= d <= b
    return ok


def _t1_buckets(sub: pd.DataFrame) -> list[dict[str, Any]]:
    edges = [(-np.inf, 0.5), (0.5, 1.0), (1.0, 2.0), (2.0, np.inf)]
    labels = ["<=0.5", "0.5-1", "1-2", ">2"]
    rows = []
    t1 = sub["t1"]
    n = max(int(t1.notna().sum()), 1)
    for (lo, hi), lab in zip(edges, labels):
        m = t1.notna() & (t1 > lo) & (t1 <= hi) if np.isfinite(lo) else t1.notna() & (t1 <= hi)
        if np.isfinite(lo) and not np.isfinite(hi):
            m = t1.notna() & (t1 > lo)
        elif np.isfinite(lo) and np.isfinite(hi):
            m = t1.notna() & (t1 > lo) & (t1 <= hi)
        elif not np.isfinite(lo) and np.isfinite(hi):
            m = t1.notna() & (t1 <= hi)
        c = int(m.sum())
        rows.append(
            {
                "bucket": lab,
                "n": c,
                "share": round(c / n, 4),
                "mean_n5": round(float(sub.loc[m, "n5_dist"].mean()), 4) if c else None,
            }
        )
    return rows


def analyze_source(df: pd.DataFrame, label: str) -> dict[str, Any]:
    """Run A–D blocks on one fill detail frame."""
    a_sleeve_side = []
    for sleeve in ("ALL", "FIN", "TEL", "0050", "SAT", "OTHER"):
        for side in ("ALL", "BUY", "SELL"):
            sub = df
            if sleeve != "ALL":
                sub = sub[sub["sleeve"] == sleeve]
            if side != "ALL":
                sub = sub[sub["side"] == side]
            if sub.empty:
                continue
            st = _fill_stats(sub)
            st.update({"sleeve": sleeve, "side": side})
            a_sleeve_side.append(st)

    a_windows = {}
    for wname, (a, b) in WINDOWS_STANDARD.items():
        sub = df[_window_mask(df["fill_date"], a, b)]
        a_windows[wname] = _fill_stats(sub)

    a_buckets = {
        "ALL": _t1_buckets(df),
        "BUY": _t1_buckets(df[df["side"] == "BUY"]),
        "SELL": _t1_buckets(df[df["side"] == "SELL"]),
    }

    # B — KD (FIN only)
    fin = df[df["sleeve"] == "FIN"]
    kd_in = fin[fin["kd_in_season"]]
    kd_out = fin[~fin["kd_in_season"]]
    b_kd = {
        "fin_n": int(len(fin)),
        "in_season": _fill_stats(kd_in),
        "off_season": _fill_stats(kd_out),
        "delta_off_minus_in_mean_n5": _delta(_fill_stats(kd_out), _fill_stats(kd_in), "mean_n5"),
        "delta_off_minus_in_mean_t1": _delta(_fill_stats(kd_out), _fill_stats(kd_in), "mean_t1"),
        "by_side": {
            side: {
                "in_season": _fill_stats(kd_in[kd_in["side"] == side]),
                "off_season": _fill_stats(kd_out[kd_out["side"] == side]),
            }
            for side in ("BUY", "SELL")
        },
        "kd_buy_block": _fill_stats(fin[fin["tag_kd_block"]]),
        "windows": {},
    }
    for wname, (a, b) in WINDOWS_STANDARD.items():
        wfin = fin[_window_mask(fin["fill_date"], a, b)]
        win = wfin[wfin["kd_in_season"]]
        wout = wfin[~wfin["kd_in_season"]]
        b_kd["windows"][wname] = {
            "in_season": _fill_stats(win),
            "off_season": _fill_stats(wout),
            "delta_n5": _delta(_fill_stats(wout), _fill_stats(win), "mean_n5"),
        }

    # C — CLIP_FIN_HI (FIN)
    clip = fin[fin["tag_clip_fin_hi"]]
    nclip = fin[~fin["tag_clip_fin_hi"]]
    fin_w = pd.to_numeric(fin.get("e16_financial"), errors="coerce")
    c_clip = {
        "fin_n": int(len(fin)),
        "clip_fin_hi": _fill_stats(clip),
        "not_clip_fin_hi": _fill_stats(nclip),
        "delta_clip_minus_not_mean_n5": _delta(_fill_stats(clip), _fill_stats(nclip), "mean_n5"),
        "delta_clip_minus_not_mean_t1": _delta(_fill_stats(clip), _fill_stats(nclip), "mean_t1"),
        "fin_weight": {
            "mean": round(float(fin_w.mean()), 4) if fin_w.notna().any() else None,
            "median": round(float(fin_w.median()), 4) if fin_w.notna().any() else None,
            "share_ge_0_79": round(float((fin_w >= 0.79).mean()), 4)
            if fin_w.notna().any()
            else None,
            "share_ge_0_80": round(float((fin_w >= 0.80 - 1e-4).mean()), 4)
            if fin_w.notna().any()
            else None,
        },
        "cross_kd": {
            "clip_and_offseason": _fill_stats(clip[clip["tag_kd_off"] | ~clip["kd_in_season"]]),
            "clip_and_inseason": _fill_stats(clip[clip["kd_in_season"]]),
            "notclip_offseason": _fill_stats(nclip[~nclip["kd_in_season"]]),
            "notclip_inseason": _fill_stats(nclip[nclip["kd_in_season"]]),
        },
        "windows": {},
    }
    for wname, (a, b) in WINDOWS_STANDARD.items():
        wfin = fin[_window_mask(fin["fill_date"], a, b)]
        wc = wfin[wfin["tag_clip_fin_hi"]]
        wn = wfin[~wfin["tag_clip_fin_hi"]]
        c_clip["windows"][wname] = {
            "clip_fin_hi": _fill_stats(wc),
            "not_clip_fin_hi": _fill_stats(wn),
            "delta_n5": _delta(_fill_stats(wc), _fill_stats(wn), "mean_n5"),
        }

    # D — COOL
    cool_on = df[df["cool_on"]]
    cool_off = df[~df["cool_on"]]
    d_cool = {
        "cool_on": _fill_stats(cool_on),
        "cool_off": _fill_stats(cool_off),
        "delta_on_minus_off_mean_n5": _delta(_fill_stats(cool_on), _fill_stats(cool_off), "mean_n5"),
        "delta_on_minus_off_mean_t1": _delta(_fill_stats(cool_on), _fill_stats(cool_off), "mean_t1"),
        "by_sleeve": {},
        "by_side": {
            side: {
                "cool_on": _fill_stats(cool_on[cool_on["side"] == side]),
                "cool_off": _fill_stats(cool_off[cool_off["side"] == side]),
            }
            for side in ("BUY", "SELL")
        },
        "cross_kd_fin": {
            "cool_on_kd_off": _fill_stats(
                fin[fin["cool_on"] & ~fin["kd_in_season"]]
            ),
            "cool_on_kd_in": _fill_stats(fin[fin["cool_on"] & fin["kd_in_season"]]),
            "cool_off_kd_off": _fill_stats(
                fin[~fin["cool_on"] & ~fin["kd_in_season"]]
            ),
            "cool_off_kd_in": _fill_stats(fin[~fin["cool_on"] & fin["kd_in_season"]]),
        },
        "windows": {},
    }
    for sleeve in ("FIN", "TEL", "0050"):
        s_on = cool_on[cool_on["sleeve"] == sleeve]
        s_off = cool_off[cool_off["sleeve"] == sleeve]
        d_cool["by_sleeve"][sleeve] = {
            "cool_on": _fill_stats(s_on),
            "cool_off": _fill_stats(s_off),
            "delta_n5": _delta(_fill_stats(s_on), _fill_stats(s_off), "mean_n5"),
        }
    for wname, (a, b) in WINDOWS_STANDARD.items():
        w = df[_window_mask(df["fill_date"], a, b)]
        d_cool["windows"][wname] = {
            "cool_on": _fill_stats(w[w["cool_on"]]),
            "cool_off": _fill_stats(w[~w["cool_on"]]),
            "delta_n5": _delta(
                _fill_stats(w[w["cool_on"]]), _fill_stats(w[~w["cool_on"]]), "mean_n5"
            ),
        }

    return {
        "label": label,
        "n_fills": int(len(df)),
        "fill_date_min": str(df["fill_date"].min().date()) if len(df) else None,
        "fill_date_max": str(df["fill_date"].max().date()) if len(df) else None,
        "A_t1": {
            "overall": _fill_stats(df),
            "sleeve_side": a_sleeve_side,
            "windows": a_windows,
            "t1_buckets": a_buckets,
        },
        "B_kd": b_kd,
        "C_clip": c_clip,
        "D_cool": d_cool,
    }


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


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)

    tip = _load_detail(TIP_DETAIL, source="tip")
    bt = _load_detail(BT_DETAIL, source="backtest")

    print(f"tip fills={len(tip)} backtest fills={len(bt)}", flush=True)
    tip_an = analyze_source(tip, "tip")
    bt_an = analyze_source(bt, "backtest_fuse_cool")

    # D NAV: offense vs COOL stack (backtest twin)
    print("building offense vs COOL NAV windows ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    fuse_nav, _, fuse_meta = fuse_cut.build_fuse_offense_sim(market, dividends)
    cool = cool_cut.build_cool_exposure_from_offense(market, fuse_nav)
    cool_nav, _, cool_meta = fuse_cut.build_fuse_offense_sim(
        market, dividends, e45_exposure=cool
    )
    off_w = _nav_pack(fuse_nav)
    cool_w = _nav_pack(cool_nav)
    nav_vs = {}
    for k in WINDOWS_STANDARD:
        o, c = off_w[k], cool_w[k]
        gb = cagr_delta_pp(o.get("cagr"), c.get("cagr"), missing_as_zero=True)
        md = mdd_delta_pp(o.get("max_drawdown"), c.get("max_drawdown"))
        nav_vs[k] = {
            "offense": o,
            "cool_stack": c,
            "cagr_giveback_pp": None if gb is None else round(float(gb), 4),
            "mdd_improve_pp": None if md is None else round(float(md), 4),
        }

    # Ranked findings (backtest-primary)
    findings: list[dict[str, Any]] = []
    bt_a = bt_an["A_t1"]["overall"]
    findings.append(
        {
            "id": "A_T1_STRUCTURAL",
            "rank": 1,
            "claim": "Exact T+1 is the structural fill-cost driver across full history",
            "evidence": {
                "mean_t1": bt_a.get("mean_t1"),
                "mean_n5": bt_a.get("mean_n5"),
                "corr_t1_n5": bt_a.get("corr_t1_n5"),
                "tip_mean_t1": tip_an["A_t1"]["overall"].get("mean_t1"),
                "tip_mean_n5": tip_an["A_t1"]["overall"].get("mean_n5"),
            },
        }
    )
    b = bt_an["B_kd"]
    findings.append(
        {
            "id": "B_KD_OFFSEASON",
            "rank": 2,
            "claim": "FIN KD off-season fill quality vs in-season",
            "evidence": {
                "in_n5": (b["in_season"] or {}).get("mean_n5"),
                "off_n5": (b["off_season"] or {}).get("mean_n5"),
                "delta_n5": b.get("delta_off_minus_in_mean_n5"),
                "delta_t1": b.get("delta_off_minus_in_mean_t1"),
                "in_n": (b["in_season"] or {}).get("n"),
                "off_n": (b["off_season"] or {}).get("n"),
            },
        }
    )
    c = bt_an["C_clip"]
    findings.append(
        {
            "id": "C_CLIP_FIN_HI",
            "rank": 3,
            "claim": "FIN CLIP_FIN_HI edge fills vs non-edge",
            "evidence": {
                "clip_n5": (c["clip_fin_hi"] or {}).get("mean_n5"),
                "not_n5": (c["not_clip_fin_hi"] or {}).get("mean_n5"),
                "delta_n5": c.get("delta_clip_minus_not_mean_n5"),
                "delta_t1": c.get("delta_clip_minus_not_mean_t1"),
                "clip_n": (c["clip_fin_hi"] or {}).get("n"),
                "fin_share_ge_080": (c.get("fin_weight") or {}).get("share_ge_0_80"),
            },
        }
    )
    d = bt_an["D_cool"]
    findings.append(
        {
            "id": "D_COOL_DEFEND",
            "rank": 4,
            "claim": "COOL defend days: fill distance bump vs NAV MDD benefit",
            "evidence": {
                "delta_n5": d.get("delta_on_minus_off_mean_n5"),
                "delta_t1": d.get("delta_on_minus_off_mean_t1"),
                "cool_on_n": (d["cool_on"] or {}).get("n"),
                "heldout_mdd_improve_pp": (nav_vs.get("heldout_2019_plus") or {}).get(
                    "mdd_improve_pp"
                ),
                "heldout_cagr_giveback_pp": (nav_vs.get("heldout_2019_plus") or {}).get(
                    "cagr_giveback_pp"
                ),
                "sealed_mdd_improve_pp": (nav_vs.get("sealed_2023_plus") or {}).get(
                    "mdd_improve_pp"
                ),
            },
        }
    )

    # Priority suggestion from magnitudes (observe ranking only)
    deltas = [
        ("B_KD", abs(b.get("delta_off_minus_in_mean_n5") or 0.0)),
        ("C_CLIP", abs(c.get("delta_clip_minus_not_mean_n5") or 0.0)),
        ("D_COOL", abs(d.get("delta_on_minus_off_mean_n5") or 0.0)),
    ]
    deltas.sort(key=lambda x: -x[1])
    priority = [x[0] for x in deltas]

    verdict = "FILL_MECH_DEEPDIVE_DONE"
    payload = {
        "generated_at_utc": _utc(),
        "label": SCREEN_ID,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "status": verdict,
        "live_wire": False,
        "soft_frozen_keep": True,
        "book_id": BOOK_ID,
        "kd_season": {
            "start": list(KD_OPT["season_start"]),
            "end": list(KD_OPT["season_end"]),
        },
        "tip": tip_an,
        "backtest": bt_an,
        "nav_offense_vs_cool": nav_vs,
        "fuse_meta_n_fills": fuse_meta.get("n_fills"),
        "cool_meta_n_fills": cool_meta.get("n_fills"),
        "findings": findings,
        "observe_priority_by_abs_n5_delta": priority,
        "binding": [
            "Soft-Frozen live KEEP",
            "Exact T+1 KEEP",
            "No tip rewrite",
            "No live wire — discussion only after this pack",
        ],
    }
    (REP / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2) + "\n")
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2) + "\n")

    def _row(st: dict[str, Any]) -> str:
        if not st or not st.get("n"):
            return "— | — | — | —"
        return (
            f"{st.get('n')} | {st.get('mean_n5')} | {st.get('mean_t1')} | {st.get('mean_n21')}"
        )

    lines = [
        "# Fill mechanism deep dive (A–D) — Screen",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Status: **`{verdict}`** · Soft-Frozen KEEP · **no live wire** · `{BOOK_ID}`",
        "",
        f"Tip fills **{tip_an['n_fills']}** · Backtest twin fills **{bt_an['n_fills']}** "
        f"(`{bt_an['fill_date_min']}` → `{bt_an['fill_date_max']}`)",
        "",
        "## Findings (backtest-primary)",
        "",
    ]
    for fnd in findings:
        ev = fnd["evidence"]
        lines.append(f"### {fnd['id']} — {fnd['claim']}")
        lines.append("")
        lines.append("```")
        lines.append(json.dumps(ev, indent=2))
        lines.append("```")
        lines.append("")

    lines += [
        f"Observe priority by |Δ ±5d mean| (B/C/D): **{' > '.join(priority)}**",
        "",
        "## A — T+1 decomposition (backtest)",
        "",
        f"Overall mean T+1 **{bt_a.get('mean_t1')}%** · ±5d **{bt_a.get('mean_n5')}%** · "
        f"corr(T+1,±5d) **{bt_a.get('corr_t1_n5')}**",
        "",
        "| sleeve | side | n | ±5 mean% | T+1 mean% | ±21 mean% |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for sleeve in ("ALL", "FIN", "TEL", "0050"):
        for side in ("ALL", "BUY", "SELL"):
            st = next(
                (
                    x
                    for x in bt_an["A_t1"]["sleeve_side"]
                    if x["sleeve"] == sleeve and x["side"] == side
                ),
                None,
            )
            if not st:
                continue
            lines.append(
                f"| {sleeve} | {side} | {st.get('n')} | {st.get('mean_n5')} | "
                f"{st.get('mean_t1')} | {st.get('mean_n21')} |"
            )

    lines += [
        "",
        "### T+1 buckets (backtest ALL)",
        "",
        "| bucket | n | share | mean ±5% |",
        "|---|---:|---:|---:|",
    ]
    for bkt in bt_an["A_t1"]["t1_buckets"]["ALL"]:
        lines.append(
            f"| {bkt['bucket']} | {bkt['n']} | {bkt['share']} | {bkt['mean_n5']} |"
        )

    lines += [
        "",
        "### Windows (backtest)",
        "",
        "| window | n | ±5 mean% | T+1 mean% |",
        "|---|---:|---:|---:|",
    ]
    for wname, st in bt_an["A_t1"]["windows"].items():
        if not st.get("n"):
            continue
        lines.append(
            f"| `{wname}` | {st.get('n')} | {st.get('mean_n5')} | {st.get('mean_t1')} |"
        )

    lines += [
        "",
        "## B — KD season (FIN, backtest)",
        "",
        f"In-season n={b['in_season'].get('n')} ±5 **{b['in_season'].get('mean_n5')}%** · "
        f"Off-season n={b['off_season'].get('n')} ±5 **{b['off_season'].get('mean_n5')}%** · "
        f"Δ(off−in) ±5 **{b.get('delta_off_minus_in_mean_n5')}** · "
        f"Δ T+1 **{b.get('delta_off_minus_in_mean_t1')}**",
        "",
        "| window | in ±5 | off ±5 | Δ |",
        "|---|---:|---:|---:|",
    ]
    for wname, w in b["windows"].items():
        lines.append(
            f"| `{wname}` | {(w.get('in_season') or {}).get('mean_n5')} | "
            f"{(w.get('off_season') or {}).get('mean_n5')} | {w.get('delta_n5')} |"
        )

    lines += [
        "",
        "## C — CLIP_FIN_HI (FIN, backtest)",
        "",
        f"CLIP n={c['clip_fin_hi'].get('n')} ±5 **{c['clip_fin_hi'].get('mean_n5')}%** · "
        f"not CLIP n={c['not_clip_fin_hi'].get('n')} ±5 **{c['not_clip_fin_hi'].get('mean_n5')}%** · "
        f"Δ(clip−not) ±5 **{c.get('delta_clip_minus_not_mean_n5')}** · "
        f"Δ T+1 **{c.get('delta_clip_minus_not_mean_t1')}**",
        f"FIN weight share ≥0.80: **{(c.get('fin_weight') or {}).get('share_ge_0_80')}**",
        "",
        "| cross | n | ±5 mean% | T+1 |",
        "|---|---:|---:|---:|",
    ]
    for k, st in c["cross_kd"].items():
        lines.append(
            f"| `{k}` | {st.get('n')} | {st.get('mean_n5')} | {st.get('mean_t1')} |"
        )

    lines += [
        "",
        "## D — COOL defend (backtest fills + NAV)",
        "",
        f"COOL on n={d['cool_on'].get('n')} ±5 **{d['cool_on'].get('mean_n5')}%** · "
        f"off n={d['cool_off'].get('n')} ±5 **{d['cool_off'].get('mean_n5')}%** · "
        f"Δ ±5 **{d.get('delta_on_minus_off_mean_n5')}** · "
        f"Δ T+1 **{d.get('delta_on_minus_off_mean_t1')}**",
        "",
        "| sleeve | on ±5 | off ±5 | Δ |",
        "|---|---:|---:|---:|",
    ]
    for sleeve, st in d["by_sleeve"].items():
        lines.append(
            f"| {sleeve} | {(st.get('cool_on') or {}).get('mean_n5')} | "
            f"{(st.get('cool_off') or {}).get('mean_n5')} | {st.get('delta_n5')} |"
        )

    lines += [
        "",
        "### Offense vs COOL stack NAV",
        "",
        "| window | off CAGR | cool CAGR | giveback pp | off MDD | cool MDD | MDD improve pp |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for wname, w in nav_vs.items():
        o, cnav = w["offense"], w["cool_stack"]
        lines.append(
            f"| `{wname}` | {o.get('cagr')} | {cnav.get('cagr')} | "
            f"{w.get('cagr_giveback_pp')} | {o.get('max_drawdown')} | "
            f"{cnav.get('max_drawdown')} | {w.get('mdd_improve_pp')} |"
        )

    lines += [
        "",
        "## Tip mirror (short window)",
        "",
        f"Tip overall ±5 **{tip_an['A_t1']['overall'].get('mean_n5')}%** · "
        f"T+1 **{tip_an['A_t1']['overall'].get('mean_t1')}%** · "
        f"COOL-on fills **{tip_an['D_cool']['cool_on'].get('n', 0)}** · "
        f"FIN CLIP_FIN_HI n={tip_an['C_clip']['clip_fin_hi'].get('n')} · "
        f"FIN KD off n={tip_an['B_kd']['off_season'].get('n')}",
        "",
        "Repro:",
        "```bash",
        "PYTHONPATH=scripts python3 scripts/live_fill_extreme_audit.py",
        "PYTHONPATH=scripts python3 scripts/live_fill_extreme_backtest_audit.py",
        "PYTHONPATH=scripts python3 scripts/live_fill_mech_deepdive.py",
        "```",
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
        "book_id": BOOK_ID,
        "findings": findings,
        "observe_priority_by_abs_n5_delta": priority,
        "binding": payload["binding"],
        "next": (
            "Human discussion only — pick ZERO or ONE Stage A from "
            f"priority {priority}; do not batch-retune from this pack"
        ),
        "charter": f"research/ops/{CHARTER_ID}.md",
        "screen": f"research/ops/{SCREEN_ID}.md",
    }
    dlines = [
        "# Fill mechanism deep dive (A–D) — Decision Pack",
        "",
        f"Date: 2026-09-26 · Generated `{decision['generated_at_utc']}`",
        f"Status: **{verdict}** · Soft-Frozen **KEEP** · live wire **false**",
        "",
        "Comprehensive observe pack over tip + FUSE+COOL backtest fills. "
        "No live change authorized.",
        "",
        f"Observe priority (|Δ ±5d|): **{' > '.join(priority)}**",
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
    for path in (OPS, REP):
        (path / f"{DECISION_ID}.json").write_text(json.dumps(decision, indent=2) + "\n")
        (path / f"{DECISION_ID}.md").write_text("\n".join(dlines) + "\n")

    print(
        json.dumps(
            {
                "verdict": verdict,
                "priority": priority,
                "findings": [
                    {"id": f["id"], "evidence": f["evidence"]} for f in findings
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
