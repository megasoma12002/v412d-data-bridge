#!/usr/bin/env python3
"""FIN×SAT divergence-episode Stage A — label COMP−SAT gaps, contrast features inside.

Charter: research/ops/FIN_SAT_DIV_EPISODE_STAGEA_CHARTER.md
Parents: 0k9i tip-gap · 0k9j/0k9k spectral · COMP + SAT_RELAX KEEP.
Soft-Frozen KEEP · no live · no year-switch · no feature-table expand.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import cool_t50_inv_satellite_stagea as sat
from e45_paper_harness import WINDOWS_STANDARD, window_stats
from e50_early_stack_combined_nav import e16_features
from fin_sell_quality_helpers import cagr_lift_pp
from ops_repro_ssot import write_ops_and_repro_pointer
from research_metric_helpers import mdd_delta_pp

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "fin-sat-div-episode-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_SAT_DIV_EPISODE_STAGEA_CHARTER"
SCREEN_ID = "FIN_SAT_DIV_EPISODE_STAGEA_SCREEN"
DECISION_ID = "FIN_SAT_DIV_EPISODE_STAGEA_DECISION_PACK"
BASE_ID = "CTRL_LIVE_A10"

LIVE_NAV = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/ctrl_live_a10_daily_nav.csv"
COMP_NAV = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/comp_h150_x_a20_daily_nav.csv"
SAT_NAV = ROOT / "repro/sat-a20-relax-dual-paper-observe/outputs/sat_a20_relax_daily_nav.csv"
COMP_FILLS = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/comp_h150_x_a20_fills.csv"

THETAS = (0.01, 0.02)
MIN_K = 5
IC_ABS_MIN = 0.04
HIT_RATE_MIN = 0.52
CAGR_FLOOR_PP = 0.10
HELD_MDD_MIN_PP = -0.25
HELD_ABS_MDD_MAX = 0.15
TIP_MDD_MIN_PP = 0.0
TIP_CAGR_MIN_PP = 0.0
VS_SAT_HELD_EXTRA_PP = 0.05

FEATS = [
    "crisis",
    "bearcrisis",
    "r0050_63",
    "mdd0050_63",
    "vol0050_21",
    "comp_sells_21",
    "zz08_bear",
]


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_nav(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)[["date", "nav"]].assign(
        nav=lambda x: x["nav"].astype(float)
    )


def _pack(nav: pd.DataFrame) -> dict[str, Any]:
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


def _tip(base_nav: pd.DataFrame, chal_nav: pd.DataFrame) -> dict[str, Any]:
    asof = pd.Timestamp(pd.to_datetime(base_nav["date"]).max())
    b_dates = pd.to_datetime(base_nav["date"])
    c_dates = pd.to_datetime(chal_nav["date"])
    out: dict[str, Any] = {}
    for wname, start in (
        ("ytd", pd.Timestamp(asof.year, 1, 1)),
        ("trailing_1y", asof - pd.Timedelta(days=365)),
    ):
        b = base_nav[(b_dates >= start) & (b_dates <= asof)].reset_index(drop=True)
        c = chal_nav[(c_dates >= start) & (c_dates <= asof)].reset_index(drop=True)
        if len(b) < 20 or len(c) < 20:
            out[wname] = {"mdd_improve_pp": None, "cagr_lift_pp": None, "gate": "INSUFFICIENT"}
            continue
        bn = b["nav"].astype(float) / float(b["nav"].iloc[0])
        cn = c["nav"].astype(float) / float(c["nav"].iloc[0])
        b_mdd = float((bn / bn.cummax() - 1.0).min())
        c_mdd = float((cn / cn.cummax() - 1.0).min())
        years = (len(b) - 1) / 252.0
        bc = float(bn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        cc = float(cn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        lift = cagr_lift_pp(bc, cc)
        out[wname] = {
            "mdd_improve_pp": round(float(mdd_delta_pp(b_mdd, c_mdd)), 4),
            "cagr_lift_pp": None if lift is None else round(float(lift), 4),
            "gate": "PASS",
        }
    return out


def _trail(r: pd.Series, n: int) -> pd.Series:
    return (1.0 + r).rolling(n, min_periods=n).apply(lambda x: float(np.prod(x) - 1.0), raw=True)


def _zigzag_bear(close: pd.Series, thr: float = 0.08) -> pd.Series:
    px = close.astype(float).ffill().to_numpy()
    n = len(px)
    bear = np.zeros(n, dtype=float)
    if n == 0:
        return pd.Series(bear, index=close.index)
    extreme = float(px[0])
    is_bear = False
    for i in range(1, n):
        p = float(px[i])
        if not is_bear:
            extreme = max(extreme, p)
            if extreme > 0 and (p / extreme - 1.0) <= -thr:
                is_bear = True
                extreme = p
        else:
            extreme = min(extreme, p)
            if extreme > 0 and (p / extreme - 1.0) >= thr:
                is_bear = False
                extreme = p
        bear[i] = 1.0 if is_bear else 0.0
    return pd.Series(bear, index=close.index)


def _run_label(raw: pd.Series, min_k: int) -> pd.Series:
    """Keep True only for runs of length >= min_k."""
    v = raw.fillna(False).astype(bool).to_numpy()
    out = np.zeros(len(v), dtype=bool)
    i = 0
    n = len(v)
    while i < n:
        if not v[i]:
            i += 1
            continue
        j = i
        while j < n and v[j]:
            j += 1
        if j - i >= min_k:
            out[i:j] = True
        i = j
    return pd.Series(out, index=raw.index)


def _build_panel(dates: pd.DatetimeIndex, comp: pd.DataFrame, sat_nav: pd.DataFrame) -> pd.DataFrame:
    print("building panel ...", flush=True)
    market0 = sat.load_market()
    _p, _s, _t, regime = e16_features(market0)
    reg = pd.Series(regime.values, index=pd.to_datetime(regime.index)).sort_index()
    reg = reg[~reg.index.duplicated(keep="last")]
    px = market0[market0["code"].astype(str) == "0050"].copy()
    px["date"] = pd.to_datetime(px["date"])
    close = px.drop_duplicates("date").set_index("date")["adj_close" if "adj_close" in px.columns else "close"].astype(float)
    close = close[~close.index.duplicated(keep="last")]
    r0050 = close.pct_change()

    c = comp.set_index("date")["nav"].reindex(dates).astype(float)
    s = sat_nav.set_index("date")["nav"].reindex(dates).astype(float)
    rc = c.pct_change()
    rs = s.pct_change()
    rel = rc - rs

    sells = pd.Series(0.0, index=dates)
    if COMP_FILLS.exists():
        f = pd.read_csv(COMP_FILLS)
        f["fill_date"] = pd.to_datetime(f["fill_date"])
        cnt = f[f["side"].astype(str).str.upper() == "SELL"].groupby("fill_date").size()
        sells = cnt.reindex(dates).fillna(0.0)

    feat = pd.DataFrame({"date": dates})
    feat["regime"] = feat["date"].map(reg)
    feat["close0050"] = feat["date"].map(close)
    feat["rel"] = rel.to_numpy()
    feat["trail_rel_63"] = _trail(pd.Series(feat["rel"]), 63).to_numpy()
    feat["crisis"] = (feat["regime"] == "Crisis").astype(float)
    feat["bearcrisis"] = feat["regime"].isin(["Bear", "Crisis"]).astype(float)
    feat["r0050_63"] = _trail(feat["date"].map(r0050), 63).to_numpy()
    feat["mdd0050_63"] = (
        feat["close0050"]
        .ffill()
        .rolling(63, min_periods=63)
        .apply(lambda w: float((pd.Series(w) / pd.Series(w).cummax() - 1.0).min()), raw=True)
        .to_numpy()
    )
    feat["vol0050_21"] = feat["date"].map(r0050).rolling(21, min_periods=21).std().to_numpy()
    feat["comp_sells_21"] = sells.rolling(21, min_periods=1).sum().to_numpy()
    feat["zz08_bear"] = _zigzag_bear(feat["close0050"]).to_numpy()
    for col in FEATS + ["trail_rel_63"]:
        feat[f"{col}_l1"] = feat[col].shift(1)
    return feat


def _label_states(feat: pd.DataFrame, theta: float, min_k: int) -> pd.DataFrame:
    tr = feat["trail_rel_63"]
    sat_raw = tr <= -theta
    comp_raw = tr >= theta
    sat = _run_label(sat_raw, min_k)
    comp = _run_label(comp_raw, min_k)
    # mutual exclusion if overlap (rare): prefer stronger |trail|
    both = sat & comp
    if both.any():
        prefer_sat = feat["trail_rel_63"] < 0
        sat = sat & (~both | prefer_sat)
        comp = comp & (~both | ~prefer_sat)
    state = np.array(["SIMILAR"] * len(feat), dtype=object)
    state[sat.to_numpy()] = "SAT_LEAD"
    state[comp.to_numpy()] = "COMP_LEAD"
    out = feat.copy()
    out["state"] = state
    # causal state for switching: based on lag-1 trail
    tr1 = feat["trail_rel_63_l1"]
    sat1 = _run_label(tr1 <= -theta, min_k)
    comp1 = _run_label(tr1 >= theta, min_k)
    st1 = np.array(["SIMILAR"] * len(feat), dtype=object)
    st1[sat1.to_numpy()] = "SAT_LEAD"
    st1[comp1.to_numpy()] = "COMP_LEAD"
    out["state_l1"] = st1
    return out


def _episode_table(df: pd.DataFrame) -> list[dict[str, Any]]:
    # contiguous runs of same state
    st = df["state"].to_numpy()
    dates = df["date"]
    rows = []
    i = 0
    n = len(df)
    while i < n:
        j = i + 1
        while j < n and st[j] == st[i]:
            j += 1
        g = df.iloc[i:j]
        rel_sum = float(g["rel"].fillna(0).sum())
        rows.append(
            {
                "state": str(st[i]),
                "start": str(g["date"].iloc[0].date()),
                "end": str(g["date"].iloc[-1].date()),
                "n_days": int(j - i),
                "rel_sum_pp": round(rel_sum * 100, 3),
                "mean_trail_rel_63": None
                if g["trail_rel_63"].isna().all()
                else round(float(g["trail_rel_63"].mean()), 5),
            }
        )
        i = j
    return rows


def _contrast(df: pd.DataFrame) -> dict[str, Any]:
    out: dict[str, Any] = {"n": {}}
    for st in ("SAT_LEAD", "COMP_LEAD", "SIMILAR"):
        g = df[df["state"] == st]
        out["n"][st] = int(len(g))
        out[st] = {}
        for f in FEATS:
            s = g[f]
            out[st][f] = None if s.isna().all() else round(float(s.mean()), 6)
    # deltas SAT_LEAD - SIMILAR and SAT_LEAD - COMP_LEAD
    out["sat_minus_similar"] = {}
    out["sat_minus_comp"] = {}
    for f in FEATS:
        a, b, c = out["SAT_LEAD"].get(f), out["SIMILAR"].get(f), out["COMP_LEAD"].get(f)
        out["sat_minus_similar"][f] = None if a is None or b is None else round(float(a) - float(b), 6)
        out["sat_minus_comp"][f] = None if a is None or c is None else round(float(a) - float(c), 6)
    return out


def _leading_ic(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Predict next-day SAT_LEAD (state) from lag-1 feats — evaluated on all days."""
    y = (df["state"] == "SAT_LEAD").astype(float)
    rows = []
    for f in FEATS:
        x = df[f"{f}_l1"]
        m = pd.DataFrame({"x": x, "y": y}).dropna()
        if len(m) < 100:
            continue
        ic = float(m["x"].corr(m["y"]))
        med = float(m["x"].median())
        # high x → more SAT_LEAD if IC>0
        pred = (m["x"] > med).astype(float) if ic >= 0 else (m["x"] <= med).astype(float)
        hit = float((pred == m["y"]).mean())
        # also conditional hit among days that are SIMILAR or about to diverge? report base
        rows.append(
            {
                "feat": f"{f}_l1",
                "ic": round(ic, 4) if ic == ic else None,
                "abs_ic": round(abs(ic), 4) if ic == ic else None,
                "sign_hit": round(hit, 4),
                "sat_when_high": bool(ic == ic and ic > 0),
                "ic_gate": bool(ic == ic and abs(ic) >= IC_ABS_MIN and hit >= HIT_RATE_MIN),
                "n": int(len(m)),
                "base_sat_rate": round(float(m["y"].mean()), 4),
            }
        )
    rows.sort(key=lambda r: float(r["abs_ic"] or 0), reverse=True)
    return rows


def _eval_row(base_w, chal_w, tip, *, fam: str, sat_held_cagr: float | None) -> dict[str, Any]:
    held_b = base_w.get("heldout_2019_plus") or {}
    held_c = chal_w.get("heldout_2019_plus") or {}
    cagr_pp = cagr_lift_pp(held_b.get("cagr"), held_c.get("cagr"))
    mdd_pp = mdd_delta_pp(held_b.get("max_drawdown"), held_c.get("max_drawdown"))
    abs_mdd = held_c.get("max_drawdown")
    tip_ytd_mdd = (tip.get("ytd") or {}).get("mdd_improve_pp")
    tip_1y_mdd = (tip.get("trailing_1y") or {}).get("mdd_improve_pp")
    tip_ytd_cagr = (tip.get("ytd") or {}).get("cagr_lift_pp")
    tip_1y_cagr = (tip.get("trailing_1y") or {}).get("cagr_lift_pp")
    tip_mdd_ok = (
        tip_ytd_mdd is not None
        and tip_1y_mdd is not None
        and float(tip_ytd_mdd) >= TIP_MDD_MIN_PP
        and float(tip_1y_mdd) >= TIP_MDD_MIN_PP
    )
    tip_cagr_ok = (
        tip_ytd_cagr is not None
        and tip_1y_cagr is not None
        and float(tip_ytd_cagr) >= TIP_CAGR_MIN_PP
        and float(tip_1y_cagr) >= TIP_CAGR_MIN_PP
    )
    cagr_ok = cagr_pp is not None and float(cagr_pp) >= CAGR_FLOOR_PP
    mdd_ok = mdd_pp is not None and float(mdd_pp) >= HELD_MDD_MIN_PP
    band_ok = abs_mdd is not None and abs(float(abs_mdd)) <= HELD_ABS_MDD_MAX
    vs_sat_ok = (
        cagr_pp is not None
        and sat_held_cagr is not None
        and float(cagr_pp) >= float(sat_held_cagr) + VS_SAT_HELD_EXTRA_PP
    )
    tip_clean = bool(tip_mdd_ok and tip_cagr_ok)
    economic = bool(cagr_ok and mdd_ok and band_ok and tip_mdd_ok)
    hit = bool(fam == "switch" and tip_clean and economic and vs_sat_ok)
    return {
        "held_cagr_lift_pp": None if cagr_pp is None else round(float(cagr_pp), 4),
        "held_mdd_pp": None if mdd_pp is None else round(float(mdd_pp), 4),
        "held_abs_mdd": None if abs_mdd is None else round(float(abs_mdd), 6),
        "tip_ytd_cagr_pp": tip_ytd_cagr,
        "tip_1y_cagr_pp": tip_1y_cagr,
        "tip_ytd_mdd_pp": tip_ytd_mdd,
        "tip_1y_mdd_pp": tip_1y_mdd,
        "family": fam,
        "gates": {
            "cagr": bool(cagr_ok),
            "mdd_near_flat": bool(mdd_ok),
            "mdd_band": bool(band_ok),
            "tip_mdd": bool(tip_mdd_ok),
            "tip_cagr": bool(tip_cagr_ok),
            "tip_clean": tip_clean,
            "economic": economic,
            "vs_sat_held": bool(vs_sat_ok),
        },
        "hit": hit,
    }


def _switch_nav(comp, sat_nav, use_sat: pd.Series) -> tuple[pd.DataFrame, dict[str, Any]]:
    m = (
        comp.rename(columns={"nav": "nav_c"})
        .merge(sat_nav.rename(columns={"nav": "nav_s"}), on="date")
        .sort_values("date")
        .reset_index(drop=True)
    )
    u = np.asarray(use_sat, dtype=bool)
    if len(u) != len(m):
        raise ValueError("use_sat length mismatch")
    rc = m["nav_c"].pct_change().fillna(0.0)
    rs = m["nav_s"].pct_change().fillna(0.0)
    r = np.where(u, rs.to_numpy(), rc.to_numpy())
    nav = (1.0 + r).cumprod() * float(m["nav_c"].iloc[0])
    flips = int(np.sum(u[1:] != u[:-1])) if len(u) > 1 else 0
    return pd.DataFrame({"date": m["date"].to_numpy(), "nav": nav}), {
        "pct_days_sat": round(float(np.mean(u)) * 100, 2),
        "n_flips": flips,
    }


def _verdict(contrast: dict[str, Any], ic_rows: list[dict[str, Any]], books: list[dict[str, Any]]) -> str:
    if any(b["eval"]["hit"] for b in books if b["fam"] == "switch"):
        return "DIV_HIT"
    # separation: at least 2 feats with |sat_minus_similar| meaningful
    deltas = contrast.get("sat_minus_similar") or {}
    sep = 0
    for f, v in deltas.items():
        if v is None:
            continue
        # binary feats: delta > 0.05; continuous: relative
        if f in ("crisis", "bearcrisis", "zz08_bear") and abs(v) >= 0.05:
            sep += 1
        elif f == "comp_sells_21" and abs(v) >= 0.5:
            sep += 1
        elif f in ("r0050_63", "mdd0050_63", "vol0050_21") and abs(v) >= 0.005:
            sep += 1
    gated = [r for r in ic_rows if r.get("ic_gate")]
    if books and any(
        b["eval"]["gates"]["tip_mdd"]
        and not b["eval"]["gates"]["tip_cagr"]
        and b["eval"]["gates"]["economic"]
        for b in books
        if b["fam"] == "switch"
    ):
        # if we also have separation, still TIP_MDD_ONLY is more specific for probes
        if any(b["fam"] == "switch" for b in books):
            return "TIP_MDD_ONLY"
    if sep >= 2 and gated:
        return "DIV_FEAT_READY"
    if sep >= 1 or gated:
        return "DIV_FEAT_WEAK"
    return "DIV_FEAT_WEAK"


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)

    live = _load_nav(LIVE_NAV)
    comp = _load_nav(COMP_NAV)
    sat_nav = _load_nav(SAT_NAV)
    dates = sorted(set(live["date"]) & set(comp["date"]) & set(sat_nav["date"]))
    live = live[live["date"].isin(dates)].reset_index(drop=True)
    comp = comp[comp["date"].isin(dates)].reset_index(drop=True)
    sat_nav = sat_nav[sat_nav["date"].isin(dates)].reset_index(drop=True)
    didx = pd.DatetimeIndex(dates)

    base_panel = _build_panel(didx, comp, sat_nav)

    all_theta: dict[str, Any] = {}
    primary_theta = 0.01
    primary = None

    for theta in THETAS:
        print(f"labeling theta={theta} ...", flush=True)
        df = _label_states(base_panel, theta, MIN_K)
        episodes = _episode_table(df)
        contrast = _contrast(df)
        ic_rows = _leading_ic(df)
        # tip-window subset contrast
        asof = pd.Timestamp(live["date"].max())
        tip = df[df["date"] >= asof - pd.Timedelta(days=365)]
        tip_contrast = _contrast(tip) if len(tip) > 50 else {}
        block = {
            "theta": theta,
            "min_k": MIN_K,
            "state_counts": contrast["n"],
            "pct_sat_lead": round(100.0 * contrast["n"]["SAT_LEAD"] / max(1, len(df)), 2),
            "pct_comp_lead": round(100.0 * contrast["n"]["COMP_LEAD"] / max(1, len(df)), 2),
            "pct_similar": round(100.0 * contrast["n"]["SIMILAR"] / max(1, len(df)), 2),
            "contrast": contrast,
            "tip_contrast": tip_contrast,
            "leading_ic": ic_rows,
            "n_episodes": len(episodes),
            "n_sat_episodes": sum(1 for e in episodes if e["state"] == "SAT_LEAD"),
            "n_comp_episodes": sum(1 for e in episodes if e["state"] == "COMP_LEAD"),
        }
        all_theta[str(theta)] = block
        pd.DataFrame(episodes).to_csv(OUT / f"episodes_theta_{theta}.csv", index=False)
        df.to_csv(OUT / f"panel_labeled_theta_{theta}.csv", index=False)
        print(json.dumps({"theta": theta, "counts": contrast["n"], "top_ic": ic_rows[:3]}, ensure_ascii=False), flush=True)
        if abs(theta - primary_theta) < 1e-12:
            primary = (df, block, ic_rows)

    assert primary is not None
    df, block, ic_rows = primary

    base_w = _pack(live)
    sat_w = _pack(sat_nav)
    sat_held = cagr_lift_pp(
        (base_w.get("heldout_2019_plus") or {}).get("cagr"),
        (sat_w.get("heldout_2019_plus") or {}).get("cagr"),
    )

    books: list[dict[str, Any]] = []
    for bid, fam, nav0 in (
        ("CTRL_LIVE_A10", "ctrl", live),
        ("REF_SAT_RELAX", "ref", sat_nav),
        ("REF_COMP_H150_A20", "ref", comp),
    ):
        tip = (
            {
                "ytd": {"mdd_improve_pp": 0.0, "cagr_lift_pp": 0.0, "gate": "PASS"},
                "trailing_1y": {"mdd_improve_pp": 0.0, "cagr_lift_pp": 0.0, "gate": "PASS"},
            }
            if bid == BASE_ID
            else _tip(live, nav0)
        )
        books.append(
            {
                "id": bid,
                "fam": fam,
                "meta": {"rule": fam},
                "eval": _eval_row(base_w, _pack(nav0), tip, fam=fam, sat_held_cagr=sat_held),
                "tip": tip,
            }
        )

    # Probe 1: causal SAT_LEAD state → hold SAT
    use_ep = (df["state_l1"] == "SAT_LEAD").to_numpy()
    nav, meta = _switch_nav(comp, sat_nav, pd.Series(use_ep))
    nav.to_csv(OUT / "nav_PRB_STATE_SAT_LEAD.csv", index=False)
    tip = _tip(live, nav)
    books.append(
        {
            "id": "PRB_STATE_SAT_LEAD",
            "fam": "switch",
            "meta": {**meta, "rule": "state_l1==SAT_LEAD"},
            "eval": _eval_row(base_w, _pack(nav), tip, fam="switch", sat_held_cagr=sat_held),
            "tip": tip,
        }
    )

    # Probe 2: best IC-gated feat (or top abs IC) median split
    gated = [r for r in ic_rows if r.get("ic_gate")]
    pick = gated[0] if gated else (ic_rows[0] if ic_rows else None)
    if pick:
        fname = pick["feat"]  # already *_l1
        x = df[fname]
        med = float(x.dropna().median())
        high = x > med
        use = high if pick["sat_when_high"] else ~high
        use = use.fillna(False).to_numpy()
        nav2, meta2 = _switch_nav(comp, sat_nav, pd.Series(use))
        bid = f"PRB_{fname.upper().replace('_L1','')}"[:28]
        nav2.to_csv(OUT / f"nav_{bid}.csv", index=False)
        tip2 = _tip(live, nav2)
        books.append(
            {
                "id": bid,
                "fam": "switch",
                "meta": {**meta2, "rule": fname, "ic": pick["ic"], "sat_when_high": pick["sat_when_high"]},
                "eval": _eval_row(base_w, _pack(nav2), tip2, fam="switch", sat_held_cagr=sat_held),
                "tip": tip2,
            }
        )

    for b in books:
        if b["fam"] == "switch":
            print(json.dumps({"book": b["id"], "meta": b["meta"], "eval": b["eval"]}, ensure_ascii=False), flush=True)

    verdict = _verdict(block["contrast"], ic_rows, books)
    generated = _utc()

    recommendation = {
        "method": "label_divergence_episodes_then_contrast",
        "primary_theta": primary_theta,
        "sat_lead_vs_similar": block["contrast"]["sat_minus_similar"],
        "sat_lead_vs_comp": block["contrast"]["sat_minus_comp"],
        "top_leading_ic": ic_rows[:5],
        "note": "Differences live in SAT_LEAD episodes; SIMILAR segments dilute full-sample spectra.",
    }

    payload = {
        "label": f"{SCREEN_ID}_{generated.replace(':', '').replace('-', '')}",
        "generated_at_utc": generated,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "status": "STAGE_A_SCREEN_DONE",
        "verdict": verdict,
        "live_wire": False,
        "soft_frozen_keep": True,
        "parent_observes_keep": True,
        "by_theta": all_theta,
        "recommendation": recommendation,
        "books": [
            {"id": b["id"], "fam": b["fam"], "meta": b["meta"], "eval": b["eval"], "tip": b["tip"]} for b in books
        ],
        "register": "0k9l",
    }
    (OUT / "div_episode_results.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")

    screen_md = "\n".join(
        [
            f"# {SCREEN_ID}",
            "",
            f"Date: 2026-09-28 · Generated `{generated}`",
            f"Status: **{verdict}** · Soft-Frozen **KEEP** · parents **KEEP** · live wire **false**",
            "",
            "Label COMP−SAT divergence episodes (trail_rel_63 ±θ, K=5), contrast features **inside** episodes.",
            "",
            "## Coverage by θ",
            "",
            "| θ | %SAT_LEAD | %COMP_LEAD | %SIMILAR | n_SAT_ep | n_COMP_ep |",
            "|---:|---:|---:|---:|---:|---:|",
        ]
        + [
            f"| {th} | {all_theta[str(th)]['pct_sat_lead']} | {all_theta[str(th)]['pct_comp_lead']} | "
            f"{all_theta[str(th)]['pct_similar']} | {all_theta[str(th)]['n_sat_episodes']} | {all_theta[str(th)]['n_comp_episodes']} |"
            for th in THETAS
        ]
        + [
            "",
            f"## Contrast θ={primary_theta} (SAT_LEAD − SIMILAR)",
            "",
            "```json",
            json.dumps(block["contrast"]["sat_minus_similar"], indent=2, ensure_ascii=False),
            "```",
            "",
            f"## Contrast θ={primary_theta} (SAT_LEAD − COMP_LEAD)",
            "",
            "```json",
            json.dumps(block["contrast"]["sat_minus_comp"], indent=2, ensure_ascii=False),
            "```",
            "",
            "## Leading IC → next-day SAT_LEAD",
            "",
            "| feat | IC | hit | gate | sat_when_high |",
            "|---|---:|---:|---|---|",
        ]
        + [
            f"| {r['feat']} | {r['ic']} | {r['sign_hit']} | {r['ic_gate']} | {r['sat_when_high']} |"
            for r in ic_rows
        ]
        + [
            "",
            "## Probes",
            "",
            "| ID | heldCAGR↑ | tipCAGR↑ | tipClean | HIT |",
            "|---|---:|---:|---|---|",
        ]
        + [
            f"| {b['id']} | {b['eval']['held_cagr_lift_pp']} | {b['eval']['tip_ytd_cagr_pp']} | "
            f"{b['eval']['gates']['tip_clean']} | {b['eval']['hit']} |"
            for b in books
        ]
        + ["", f"Verdict: **`{verdict}`**", "", f"Label: `{SCREEN_ID}_2026-09-28__{verdict}`", ""]
    )

    dlines = [
        f"# {DECISION_ID}",
        "",
        f"Date: 2026-09-28 · Generated `{generated}`",
        f"Status: **{verdict}** · Soft-Frozen **KEEP** · COMPOSITE+SAT_RELAX observes **KEEP** · live wire **false**",
        "",
        f"Charter: `{CHARTER_ID}.md`",
        f"Screen: `{SCREEN_ID}.md`",
        "Parents: 0k9i tip-gap · register **0k9l**",
        "",
        "## Verdict",
        "",
        f"**`{verdict}`**",
        "",
        "## Reading",
        "",
        f"- Primary θ={primary_theta}: SAT_LEAD {block['pct_sat_lead']}% · COMP_LEAD {block['pct_comp_lead']}% · SIMILAR {block['pct_similar']}%",
        f"- SAT_LEAD − SIMILAR: `{json.dumps(block['contrast']['sat_minus_similar'], ensure_ascii=False)}`",
        f"- SAT_LEAD − COMP_LEAD: `{json.dumps(block['contrast']['sat_minus_comp'], ensure_ascii=False)}`",
        f"- Top IC: `{json.dumps(ic_rows[:3], ensure_ascii=False)}`",
        "",
        "相似段佔多數時，全日平均／傅立葉被稀釋；互斥特徵應在 **SAT_LEAD episode** 內讀。",
        "",
        "## Binding",
        "",
        "1. Soft-Frozen / Exact T+1 / COOL / SELL_a75 / live CONF α=0.10 KEEP",
        "2. COMPOSITE + SAT_RELAX observes **KEEP OPEN**",
        "3. Do not expand feature table · no year-switch",
        "4. Next cycle rules should trigger on divergence-entry features, not full-sample averages",
        "",
        f"Label: `{DECISION_ID}_2026-09-28__{verdict}__NO_LIVE`",
        "",
    ]
    decision = {
        "label": f"{DECISION_ID}_2026-09-28__{verdict}__NO_LIVE",
        "status": verdict,
        "live_wire": False,
        "soft_frozen_keep": True,
        "parent_observes_keep": True,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "screen": f"research/ops/{SCREEN_ID}.md",
        "recommendation": recommendation,
        "register": "0k9l",
        "generated_at_utc": generated,
    }

    write_ops_and_repro_pointer(OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", screen_md, kind="screen")
    write_ops_and_repro_pointer(
        OPS / f"{SCREEN_ID}.json",
        REP / f"{SCREEN_ID}.json",
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        kind="screen",
    )
    write_ops_and_repro_pointer(OPS / f"{DECISION_ID}.md", REP / f"{DECISION_ID}.md", "\n".join(dlines))
    write_ops_and_repro_pointer(
        OPS / f"{DECISION_ID}.json",
        REP / f"{DECISION_ID}.json",
        json.dumps(decision, indent=2, ensure_ascii=False) + "\n",
    )

    for path, open_s, done_s in (
        (OPS / f"{CHARTER_ID}.md", "Status: **Stage A OPEN**", f"Status: **Stage A DONE — `{verdict}`**"),
        (OPS / f"{CHARTER_ID}.zh-TW.md", "狀態：**Stage A OPEN**", f"狀態：**Stage A DONE — `{verdict}`**"),
    ):
        if path.exists():
            body = path.read_text(encoding="utf-8").replace(open_s, done_s, 1)
            body = body.replace(
                f"{CHARTER_ID}_2026-09-28__OPEN__NO_LIVE_WIRE",
                f"{CHARTER_ID}_2026-09-28__DONE_{verdict}__NO_LIVE_WIRE",
            )
            path.write_text(body, encoding="utf-8")
    cj = json.loads((OPS / f"{CHARTER_ID}.json").read_text(encoding="utf-8"))
    cj["status"] = "STAGE_A_DONE"
    cj["verdict"] = verdict
    cj["label"] = f"{CHARTER_ID}_2026-09-28__DONE_{verdict}__NO_LIVE_WIRE"
    cj["screen"] = f"research/ops/{SCREEN_ID}.md"
    cj["decision"] = f"research/ops/{DECISION_ID}.md"
    (OPS / f"{CHARTER_ID}.json").write_text(json.dumps(cj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps({"verdict": verdict, "recommendation": recommendation}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
