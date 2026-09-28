#!/usr/bin/env python3
"""FIN×SAT 互斥特徵→切換 Stage A — year diag + pre-registered lag-1 switches (paper).

Charter: research/ops/FIN_SAT_MUTEX_FEAT_STAGEA_CHARTER.md
Parents: 0k9e/0k9f TIP_MDD_ONLY · COMP + SAT_RELAX observes KEEP.
Soft-Frozen / SELL_a75 / live CONF α=0.10 KEEP · no live · no peek-fit thresholds.
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
REPRO = ROOT / "repro" / "fin-sat-mutex-feat-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_SAT_MUTEX_FEAT_STAGEA_CHARTER"
SCREEN_ID = "FIN_SAT_MUTEX_FEAT_STAGEA_SCREEN"
DECISION_ID = "FIN_SAT_MUTEX_FEAT_STAGEA_DECISION_PACK"
BASE_ID = "CTRL_LIVE_A10"

LIVE_NAV = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/ctrl_live_a10_daily_nav.csv"
COMP_NAV = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/comp_h150_x_a20_daily_nav.csv"
SAT_NAV = ROOT / "repro/sat-a20-relax-dual-paper-observe/outputs/sat_a20_relax_daily_nav.csv"

CAGR_FLOOR_PP = 0.10
HELD_MDD_MIN_PP = -0.25
HELD_ABS_MDD_MAX = 0.15
TIP_MDD_MIN_PP = 0.0
TIP_CAGR_MIN_PP = 0.0
VS_SAT_HELD_EXTRA_PP = 0.05

GRID: list[dict[str, Any]] = [
    {"id": "CTRL_LIVE_A10", "fam": "ctrl", "rule": "ctrl"},
    {"id": "REF_SAT_RELAX", "fam": "ref", "rule": "always_sat"},
    {"id": "REF_COMP_H150_A20", "fam": "ref", "rule": "always_comp"},
    {"id": "SW_CRISIS_SAT", "fam": "switch", "rule": "crisis_sat"},
    {"id": "SW_BEARCRISIS_SAT", "fam": "switch", "rule": "bearcrisis_sat"},
    {"id": "SW_BULL_COMP", "fam": "switch", "rule": "bull_comp"},
    {"id": "SW_0050DD08_SAT", "fam": "switch", "rule": "dd0050", "thr": -0.08},
    {"id": "SW_0050DD12_SAT", "fam": "switch", "rule": "dd0050", "thr": -0.12},
    {"id": "SW_0050RET63NEG_SAT", "fam": "switch", "rule": "ret63neg"},
]


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_nav(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)[["date", "nav"]].assign(nav=lambda x: x["nav"].astype(float))


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


def _year_ret(nav: pd.Series) -> float:
    return float(nav.iloc[-1]) / float(nav.iloc[0]) - 1.0


def _year_mdd(nav: pd.Series) -> float:
    n = nav.astype(float) / float(nav.iloc[0])
    return float((n / n.cummax() - 1.0).min())


def _build_feat_panel(dates: pd.DatetimeIndex) -> pd.DataFrame:
    print("loading market + regime + 0050 ...", flush=True)
    market0 = sat.load_market()
    _p, _sleeve, _t, regime = e16_features(market0)
    reg = pd.Series(regime.values, index=pd.to_datetime(regime.index)).sort_index()
    # de-dup index if needed
    reg = reg[~reg.index.duplicated(keep="last")]

    px = market0[market0["code"].astype(str) == "0050"].copy()
    px["date"] = pd.to_datetime(px["date"])
    px = px.sort_values("date").drop_duplicates("date")
    close = px.set_index("date")["adj_close" if "adj_close" in px.columns else "close"].astype(float)
    close = close[~close.index.duplicated(keep="last")]
    r = close.pct_change()
    trail63 = (1.0 + r).rolling(63, min_periods=63).apply(lambda x: float(np.prod(x) - 1.0), raw=True)
    roll_mdd63 = close.rolling(63, min_periods=63).apply(
        lambda w: float((pd.Series(w) / pd.Series(w).cummax() - 1.0).min()), raw=True
    )

    feat = pd.DataFrame({"date": dates})
    feat["regime"] = feat["date"].map(reg)
    feat["r0050_63"] = feat["date"].map(trail63)
    feat["mdd0050_63"] = feat["date"].map(roll_mdd63)
    # lag-1 causal copies for switching
    feat["regime_l1"] = feat["regime"].shift(1)
    feat["r0050_63_l1"] = feat["r0050_63"].shift(1)
    feat["mdd0050_63_l1"] = feat["mdd0050_63"].shift(1)
    return feat


def _yearly_diag(live: pd.DataFrame, comp: pd.DataFrame, sat_nav: pd.DataFrame, feat: pd.DataFrame) -> list[dict[str, Any]]:
    m = (
        live.rename(columns={"nav": "nav_live"})
        .merge(comp.rename(columns={"nav": "nav_comp"}), on="date")
        .merge(sat_nav.rename(columns={"nav": "nav_sat"}), on="date")
        .merge(feat[["date", "regime"]], on="date", how="left")
    )
    m["year"] = m["date"].dt.year
    rows: list[dict[str, Any]] = []
    for y, g in m.groupby("year"):
        if len(g) < 20:
            continue
        rc = _year_ret(g["nav_comp"])
        rs = _year_ret(g["nav_sat"])
        rl = _year_ret(g["nav_live"])
        winner = "COMP" if rc > rs else ("SAT" if rs > rc else "TIE")
        reg_share = (g["regime"].value_counts(normalize=True) * 100.0).to_dict() if g["regime"].notna().any() else {}
        # 0050 year from aligned feat
        f_y = feat[feat["date"].dt.year == int(y)].dropna(subset=["r0050_63"])
        # use year close path from mdd/ret on mapped days — recompute from first/last available mdd proxy via trail
        # Better: map 0050 close year ret via feat dates present in g
        px_proxy = g.merge(feat[["date", "r0050_63", "mdd0050_63"]], on="date", how="left")
        # year 0050 return approx from compounding daily? use nav-style from inverse of trail — simpler join market later
        rows.append(
            {
                "year": int(y),
                "n_days": int(len(g)),
                "live_ret_pct": round(rl * 100.0, 2),
                "comp_ret_pct": round(rc * 100.0, 2),
                "sat_ret_pct": round(rs * 100.0, 2),
                "comp_minus_sat_pp": round((rc - rs) * 100.0, 2),
                "winner": winner,
                "comp_mdd_pct": round(_year_mdd(g["nav_comp"]) * 100.0, 2),
                "sat_mdd_pct": round(_year_mdd(g["nav_sat"]) * 100.0, 2),
                "pct_bull": round(float(reg_share.get("Bull", 0.0)), 2),
                "pct_bear": round(float(reg_share.get("Bear", 0.0)), 2),
                "pct_crisis": round(float(reg_share.get("Crisis", 0.0)), 2),
                "pct_sideways": round(float(reg_share.get("Sideways", 0.0)), 2),
                "mean_mdd0050_63": None
                if px_proxy["mdd0050_63"].isna().all()
                else round(float(px_proxy["mdd0050_63"].mean()) * 100.0, 2),
                "min_mdd0050_63": None
                if px_proxy["mdd0050_63"].isna().all()
                else round(float(px_proxy["mdd0050_63"].min()) * 100.0, 2),
                "mean_r0050_63": None
                if px_proxy["r0050_63"].isna().all()
                else round(float(px_proxy["r0050_63"].mean()) * 100.0, 2),
            }
        )
    return rows


def _contrast(year_rows: list[dict[str, Any]]) -> dict[str, Any]:
    df = pd.DataFrame(year_rows)
    keys = ["pct_bull", "pct_bear", "pct_crisis", "pct_sideways", "mean_mdd0050_63", "min_mdd0050_63", "mean_r0050_63", "comp_minus_sat_pp"]
    out: dict[str, Any] = {"n_comp_win": int((df["winner"] == "COMP").sum()), "n_sat_win": int((df["winner"] == "SAT").sum())}
    for side in ("COMP", "SAT"):
        sub = df[df["winner"] == side]
        out[side] = {
            k: None if sub.empty or sub[k].isna().all() else round(float(sub[k].mean()), 3) for k in keys
        }
        out[f"{side}_years"] = [int(y) for y in sub["year"].tolist()]
    # delta COMP_mean - SAT_mean
    out["comp_minus_sat_feat"] = {}
    for k in keys:
        a, b = out["COMP"].get(k), out["SAT"].get(k)
        out["comp_minus_sat_feat"][k] = None if a is None or b is None else round(float(a) - float(b), 3)
    return out


def _use_sat_signal(feat: pd.DataFrame, spec: dict[str, Any]) -> pd.Series:
    rule = str(spec["rule"])
    if rule == "always_sat":
        return pd.Series(True, index=feat.index)
    if rule == "always_comp":
        return pd.Series(False, index=feat.index)
    if rule == "ctrl":
        raise ValueError("ctrl")
    reg = feat["regime_l1"]
    if rule == "crisis_sat":
        return (reg == "Crisis").fillna(False)
    if rule == "bearcrisis_sat":
        return reg.isin(["Bear", "Crisis"]).fillna(False)
    if rule == "bull_comp":
        # Bull → COMP (False); else SAT
        return (~(reg == "Bull")).fillna(True)
    if rule == "dd0050":
        thr = float(spec["thr"])
        return (feat["mdd0050_63_l1"] < thr).fillna(False)
    if rule == "ret63neg":
        return (feat["r0050_63_l1"] < 0.0).fillna(False)
    raise ValueError(rule)


def _switch_nav(comp: pd.DataFrame, sat_nav: pd.DataFrame, feat: pd.DataFrame, spec: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    m = (
        comp.rename(columns={"nav": "nav_c"})
        .merge(sat_nav.rename(columns={"nav": "nav_s"}), on="date")
        .merge(feat, on="date", how="left")
        .sort_values("date")
        .reset_index(drop=True)
    )
    use_sat = _use_sat_signal(m, spec)
    rc = m["nav_c"].pct_change().fillna(0.0)
    rs = m["nav_s"].pct_change().fillna(0.0)
    r = np.where(use_sat.to_numpy(), rs.to_numpy(), rc.to_numpy())
    nav = (1.0 + r).cumprod() * float(m["nav_c"].iloc[0])
    flips = int(np.sum(use_sat.to_numpy()[1:] != use_sat.to_numpy()[:-1])) if len(use_sat) > 1 else 0
    meta = {
        "pct_days_sat": round(float(use_sat.mean()) * 100.0, 2),
        "n_flips": flips,
        "n_days": int(len(m)),
        "rule": str(spec.get("rule")),
    }
    return pd.DataFrame({"date": m["date"].to_numpy(), "nav": nav}), meta


def _oracle_year_nav(comp: pd.DataFrame, sat_nav: pd.DataFrame, year_rows: list[dict[str, Any]]) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Look-ahead year pick — diagnosis upper bound only."""
    winners = {int(r["year"]): r["winner"] for r in year_rows}
    m = comp.rename(columns={"nav": "nav_c"}).merge(sat_nav.rename(columns={"nav": "nav_s"}), on="date").sort_values("date")
    m["year"] = m["date"].dt.year
    use_sat = m["year"].map(lambda y: winners.get(int(y), "SAT") == "SAT")
    rc = m["nav_c"].pct_change().fillna(0.0)
    rs = m["nav_s"].pct_change().fillna(0.0)
    r = np.where(use_sat.to_numpy(), rs.to_numpy(), rc.to_numpy())
    nav = (1.0 + r).cumprod() * float(m["nav_c"].iloc[0])
    meta = {
        "pct_days_sat": round(float(use_sat.mean()) * 100.0, 2),
        "n_flips": int(np.sum(use_sat.to_numpy()[1:] != use_sat.to_numpy()[:-1])) if len(use_sat) > 1 else 0,
        "n_days": int(len(m)),
        "rule": "oracle_year_lookahead",
        "lookahead": True,
    }
    return pd.DataFrame({"date": m["date"].to_numpy(), "nav": nav}), meta


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
        "tip_ytd_mdd_pp": tip_ytd_mdd,
        "tip_1y_mdd_pp": tip_1y_mdd,
        "tip_ytd_cagr_pp": tip_ytd_cagr,
        "tip_1y_cagr_pp": tip_1y_cagr,
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
        "cagr_sign": "chal_minus_base",
    }


def _verdict(rows: list[dict[str, Any]]) -> str:
    switches = [r for r in rows if r["fam"] == "switch"]
    if any(r["eval"]["hit"] for r in switches):
        return "MUTEX_HIT"
    soft = [
        r
        for r in switches
        if r["eval"]["gates"]["tip_clean"]
        and r["eval"]["gates"]["economic"]
        and not r["eval"]["gates"]["vs_sat_held"]
    ]
    if soft:
        return "TIP_CLEAN_SOFT"
    if any(
        r["eval"]["gates"]["tip_mdd"]
        and not r["eval"]["gates"]["tip_cagr"]
        and r["eval"]["gates"]["economic"]
        for r in rows
        if r["id"] != BASE_ID and r["fam"] != "diag"
    ):
        return "TIP_MDD_ONLY"
    if any(
        r["eval"]["gates"]["cagr"] and not r["eval"]["gates"]["tip_mdd"]
        for r in rows
        if r["id"] != BASE_ID and r["fam"] != "diag"
    ):
        return "TIP_BLOCK"
    if any(r["fam"] == "switch" for r in rows):
        return "DIAG_ONLY"
    return "NO_EDGE"


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    for p in (LIVE_NAV, COMP_NAV, SAT_NAV):
        if not p.exists():
            raise FileNotFoundError(p)

    print("loading parent NAVs ...", flush=True)
    live = _load_nav(LIVE_NAV)
    comp = _load_nav(COMP_NAV)
    sat_nav = _load_nav(SAT_NAV)
    dates = sorted(set(live["date"]) & set(comp["date"]) & set(sat_nav["date"]))
    live = live[live["date"].isin(dates)].reset_index(drop=True)
    comp = comp[comp["date"].isin(dates)].reset_index(drop=True)
    sat_nav = sat_nav[sat_nav["date"].isin(dates)].reset_index(drop=True)

    feat = _build_feat_panel(pd.DatetimeIndex(dates))
    year_rows = _yearly_diag(live, comp, sat_nav, feat)
    contrast = _contrast(year_rows)
    pd.DataFrame(year_rows).to_csv(OUT / "yearly_comp_vs_sat.csv", index=False)
    (OUT / "feature_contrast.json").write_text(json.dumps(contrast, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"contrast": contrast}, ensure_ascii=False), flush=True)

    base_w = _pack(live)
    sat_w = _pack(sat_nav)
    sat_held = cagr_lift_pp(
        (base_w.get("heldout_2019_plus") or {}).get("cagr"),
        (sat_w.get("heldout_2019_plus") or {}).get("cagr"),
    )

    rows: list[dict[str, Any]] = []
    for spec in GRID:
        bid = str(spec["id"])
        fam = str(spec["fam"])
        print(f"{bid} {spec.get('rule')} ...", flush=True)
        if fam == "ctrl":
            nav = live.copy()
            meta = {"pct_days_sat": 0.0, "n_flips": 0, "n_days": int(len(nav)), "rule": "ctrl"}
        else:
            nav, meta = _switch_nav(comp, sat_nav, feat, spec)
        nav.to_csv(OUT / f"nav_{bid}.csv", index=False)
        wpack = _pack(nav)
        tip = (
            {
                "ytd": {"mdd_improve_pp": 0.0, "cagr_lift_pp": 0.0, "gate": "PASS"},
                "trailing_1y": {"mdd_improve_pp": 0.0, "cagr_lift_pp": 0.0, "gate": "PASS"},
            }
            if bid == BASE_ID
            else _tip(live, nav)
        )
        ev = _eval_row(base_w, wpack, tip, fam=fam, sat_held_cagr=sat_held)
        rows.append({"id": bid, "fam": fam, "meta": meta, "windows": wpack, "tip": tip, "eval": ev, "spec": spec})
        print(json.dumps({"book": bid, "meta": meta, "eval": ev}, ensure_ascii=False), flush=True)

    # Oracle year (diag only)
    print("ORACLE_YEAR lookahead diag ...", flush=True)
    o_nav, o_meta = _oracle_year_nav(comp, sat_nav, year_rows)
    o_nav.to_csv(OUT / "nav_ORACLE_YEAR.csv", index=False)
    o_w = _pack(o_nav)
    o_tip = _tip(live, o_nav)
    o_ev = _eval_row(base_w, o_w, o_tip, fam="diag", sat_held_cagr=sat_held)
    o_ev["hit"] = False
    rows.append({"id": "ORACLE_YEAR", "fam": "diag", "meta": o_meta, "windows": o_w, "tip": o_tip, "eval": o_ev, "spec": {"rule": "oracle_year"}})
    print(json.dumps({"book": "ORACLE_YEAR", "meta": o_meta, "eval": o_ev}, ensure_ascii=False), flush=True)

    verdict = _verdict(rows)
    generated = _utc()
    payload = {
        "label": f"{SCREEN_ID}_{generated.replace(':', '').replace('-', '')}",
        "generated_at_utc": generated,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "status": "STAGE_A_SCREEN_DONE",
        "verdict": verdict,
        "live_wire": False,
        "soft_frozen_keep": True,
        "parent_observes_keep": True,
        "sat_held_cagr_lift_pp": None if sat_held is None else round(float(sat_held), 4),
        "yearly": year_rows,
        "feature_contrast": contrast,
        "gates": {
            "held_cagr_lift_pp": CAGR_FLOOR_PP,
            "held_mdd_pp_floor": HELD_MDD_MIN_PP,
            "tip_cagr_pp_floor": TIP_CAGR_MIN_PP,
            "tip_mdd_pp_floor": TIP_MDD_MIN_PP,
            "vs_sat_held_extra_pp": VS_SAT_HELD_EXTRA_PP,
        },
        "books": [
            {
                "id": r["id"],
                "fam": r["fam"],
                "meta": r["meta"],
                "windows": r["windows"],
                "tip": r["tip"],
                "eval": r["eval"],
            }
            for r in rows
        ],
    }

    ylines = [
        "| year | winner | ΔCOMP−SAT | COMP% | SAT% | %Bull | %Bear | %Crisis | minMDD0050_63 |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in year_rows:
        ylines.append(
            f"| {r['year']} | {r['winner']} | {r['comp_minus_sat_pp']} | {r['comp_ret_pct']} | {r['sat_ret_pct']} | "
            f"{r['pct_bull']} | {r['pct_bear']} | {r['pct_crisis']} | {r['min_mdd0050_63']} |"
        )

    screen_md = "\n".join(
        [
            f"# {SCREEN_ID}",
            "",
            f"Date: 2026-09-28 · Generated `{generated}`",
            f"Status: **{verdict}** · Soft-Frozen **KEEP** · parent observes **KEEP** · live wire **false**",
            "",
            "Year mutex features → pre-registered lag-1 switches · HIT: tip-clean + held≥+0.10 + vs SAT +0.05.",
            "",
            "## Yearly COMP vs SAT",
            "",
            *ylines,
            "",
            "## Feature contrast (mean COMP-win − SAT-win)",
            "",
            "```json",
            json.dumps(contrast.get("comp_minus_sat_feat", {}), indent=2, ensure_ascii=False),
            "```",
            "",
            f"COMP-win years: {contrast.get('COMP_years')} · SAT-win years: {contrast.get('SAT_years')}",
            "",
            "## Books",
            "",
            "| ID | fam | %SAT | flips | heldCAGR↑ | tipCAGR↑ | tipClean | vsSAT | HIT |",
            "|---|---|---:|---:|---:|---:|---|---|---|",
        ]
        + [
            "| {id} | {fam} | {ps} | {fl} | {cagr} | {tc} | {clean} | {vs} | {hit} |".format(
                id=r["id"],
                fam=r["fam"],
                ps=r["meta"]["pct_days_sat"],
                fl=r["meta"]["n_flips"],
                cagr=r["eval"]["held_cagr_lift_pp"],
                tc=r["eval"]["tip_ytd_cagr_pp"],
                clean=r["eval"]["gates"]["tip_clean"],
                vs=r["eval"]["gates"]["vs_sat_held"],
                hit=r["eval"]["hit"],
            )
            for r in rows
        ]
        + ["", f"Verdict: **`{verdict}`**", "", f"Label: `{SCREEN_ID}_2026-09-28__{verdict}`", ""]
    )

    hits = [r for r in rows if r["eval"]["hit"]]
    hits.sort(key=lambda r: float(r["eval"]["held_cagr_lift_pp"] or -9), reverse=True)
    best = hits[0] if hits else None
    tip_clean_econ = [
        r
        for r in rows
        if r["fam"] == "switch" and r["eval"]["gates"]["tip_clean"] and r["eval"]["gates"]["economic"]
    ]
    tip_clean_econ.sort(key=lambda r: float(r["eval"]["held_cagr_lift_pp"] or -9), reverse=True)
    oracle = next(r for r in rows if r["id"] == "ORACLE_YEAR")

    dlines = [
        f"# {DECISION_ID}",
        "",
        f"Date: 2026-09-28 · Generated `{generated}`",
        f"Status: **{verdict}** · Soft-Frozen **KEEP** · COMPOSITE+SAT_RELAX observes **KEEP** · live wire **false**",
        "",
        f"Charter: `{CHARTER_ID}.md`",
        f"Screen: `{SCREEN_ID}.md`",
        "Parents: 0k9e/0k9f TIP_MDD_ONLY · COMPOSITE · SAT_RELAX · register **0k9g**",
        "",
        "## Verdict",
        "",
        f"**`{verdict}`**",
        "",
        f"SAT held CAGR↑ = {None if sat_held is None else round(float(sat_held), 4)}pp.",
        "",
        "## Mutex diagnosis",
        "",
        f"- COMP-win years ({contrast.get('n_comp_win')}): {contrast.get('COMP_years')}",
        f"- SAT-win years ({contrast.get('n_sat_win')}): {contrast.get('SAT_years')}",
        f"- Feat Δ(COMP−SAT means): `{json.dumps(contrast.get('comp_minus_sat_feat', {}), ensure_ascii=False)}`",
        (
            f"- Oracle year (lookahead, not HIT): held CAGR↑ {oracle['eval']['held_cagr_lift_pp']} · "
            f"tipCAGR↑ {oracle['eval']['tip_ytd_cagr_pp']} · tipClean={oracle['eval']['gates']['tip_clean']}"
        ),
        "",
    ]
    if best:
        dlines += [
            f"Champion: `{best['id']}` · held CAGR↑ {best['eval']['held_cagr_lift_pp']} · %SAT {best['meta']['pct_days_sat']}",
            "",
            "Even HIT → observe ballot **DRAFT only** · parents KEEP · no live.",
            "",
        ]
    elif tip_clean_econ:
        top = tip_clean_econ[0]
        dlines += [
            f"Best tip-clean economic switch: `{top['id']}` · held CAGR↑ {top['eval']['held_cagr_lift_pp']} · vs_sat={top['eval']['gates']['vs_sat_held']}",
            "",
        ]
    else:
        dlines += ["No pre-registered switch cleared tip-clean economic gates.", ""]

    dlines += [
        "## Binding",
        "",
        "1. Soft-Frozen / Exact T+1 / COOL / SELL_a75 / live CONF α=0.10 KEEP",
        "2. COMPOSITE + SAT_RELAX observes **KEEP OPEN**",
        "3. Do not expand feature thresholds after peek · do not reopen blend/REL grids",
        "4. Oracle year is diagnosis only · not an observe candidate",
        "5. Even HIT → paper observe ballot DRAFT only · no live wire",
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
        "best_hit": None if best is None else best["id"],
        "best_tip_clean_economic_switch": None if not tip_clean_econ else tip_clean_econ[0]["id"],
        "oracle_year_held_cagr_lift_pp": oracle["eval"]["held_cagr_lift_pp"],
        "oracle_year_tip_clean": oracle["eval"]["gates"]["tip_clean"],
        "feature_contrast": contrast,
        "sat_held_cagr_lift_pp": None if sat_held is None else round(float(sat_held), 4),
        "register": "0k9g",
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
            body = path.read_text(encoding="utf-8")
            body = body.replace(open_s, done_s, 1)
            body = body.replace(
                f"{CHARTER_ID}_2026-09-28__OPEN__NO_LIVE_WIRE",
                f"{CHARTER_ID}_2026-09-28__DONE_{verdict}__NO_LIVE_WIRE",
            )
            path.write_text(body, encoding="utf-8")
    cj_path = OPS / f"{CHARTER_ID}.json"
    if cj_path.exists():
        cj = json.loads(cj_path.read_text(encoding="utf-8"))
        cj["status"] = "STAGE_A_DONE"
        cj["verdict"] = verdict
        cj["label"] = f"{CHARTER_ID}_2026-09-28__DONE_{verdict}__NO_LIVE_WIRE"
        cj["screen"] = f"research/ops/{SCREEN_ID}.md"
        cj["decision"] = f"research/ops/{DECISION_ID}.md"
        cj_path.write_text(json.dumps(cj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps({"verdict": verdict, "n_books": len(rows), "sat_held": sat_held}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
