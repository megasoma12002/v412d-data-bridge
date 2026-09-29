#!/usr/bin/env python3
"""FIN×SAT FFT dual Stage A: (1) exogenous 0050 FFT × TD AND · (2) non-switch soft tilt.

Arm A (0ka1): causal STFT on **0050** trail (not COMP−SAT self-loop) AND with
SAT_LEAD / r0050_63 for Path3 switch / COMP-entry filter.

Arm B (0ka2): keep Path3 hard switch; soft-blend exposure by FFT amp/recon;
plus observe-only IC vs forward COMP−SAT (no weight change).

Parents: 0ka0 FFT_ENTRY_WEAK · 0k9j FFT_SIGNAL · 0k9p FFT_LAG_NO_EDGE · 0k9z SIGNAL_WEAK
Soft-Frozen KEEP · Path3 observe KEEP · fill/emit OFF · no live
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from numpy.fft import irfft, rfft, rfftfreq

import cool_t50_inv_satellite_stagea as sat
from e45_paper_harness import WINDOWS_STANDARD, window_stats
from fin_sell_quality_helpers import cagr_lift_pp
from ops_repro_ssot import write_ops_and_repro_pointer, write_repro_pointer
from research_metric_helpers import mdd_delta_pp

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "fin-sat-fft-exog-tilt-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

LIVE_NAV = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/ctrl_live_a10_daily_nav.csv"
COMP_NAV = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/comp_h150_x_a20_daily_nav.csv"
SAT_NAV = ROOT / "repro/sat-a20-relax-dual-paper-observe/outputs/sat_a20_relax_daily_nav.csv"

THETA = 0.01
PERIODS = (85.0, 128.0, 256.0)
STFT_WIN = 128
IC_EDGE = 0.15
IC_WEAK = 0.08
HIT_EDGE = 0.60
HIT_WEAK = 0.55
TILTS = (0.05, 0.10, 0.15, 0.25)
CAGR_FLOOR_PP = 0.10
HELD_MDD_MIN_PP = -0.25
TIP_MDD_MIN_PP = 0.0
TIP_CAGR_MIN_PP = 0.0

REG_A = "0ka1"
REG_B = "0ka2"
CHARTER_A = "FIN_SAT_FFT_EXOG_AND_STAGEA_CHARTER"
SCREEN_A = "FIN_SAT_FFT_EXOG_AND_STAGEA_SCREEN"
DECISION_A = "FIN_SAT_FFT_EXOG_AND_STAGEA_DECISION_PACK"
CHARTER_B = "FIN_SAT_FFT_NONSWITCH_TILT_STAGEA_CHARTER"
SCREEN_B = "FIN_SAT_FFT_NONSWITCH_TILT_STAGEA_SCREEN"
DECISION_B = "FIN_SAT_FFT_NONSWITCH_TILT_STAGEA_DECISION_PACK"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)[["date", "nav"]].assign(
        nav=lambda x: x["nav"].astype(float)
    )


def _trail(r: pd.Series, n: int) -> pd.Series:
    return (1.0 + r).rolling(n, min_periods=n).apply(lambda x: float(np.prod(x) - 1.0), raw=True)


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
            out[wname] = {"mdd_improve_pp": None, "cagr_lift_pp": None}
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
        }
    return out


def _year_ret(nav: pd.DataFrame, year: int) -> float | None:
    d = nav.copy()
    d["y"] = pd.to_datetime(d["date"]).dt.year
    g = d[d["y"] == year].reset_index(drop=True)
    if len(g) < 20:
        return None
    return round(float(g["nav"].iloc[-1] / g["nav"].iloc[0] - 1.0) * 100, 2)


def _spearman(x: np.ndarray, y: np.ndarray) -> float | None:
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 20:
        return None
    xr = pd.Series(x[m]).rank().to_numpy()
    yr = pd.Series(y[m]).rank().to_numpy()
    if xr.std() < 1e-12 or yr.std() < 1e-12:
        return None
    return float(np.corrcoef(xr, yr)[0, 1])


def _band_mask(freqs: np.ndarray, period: float, width: float = 0.30) -> np.ndarray:
    lo = 1.0 / (period * (1.0 + width))
    hi = 1.0 / (period * (1.0 - width))
    return (freqs >= lo) & (freqs <= hi) & (freqs > 0)


def _causal_stft(x: np.ndarray, *, win: int, periods: tuple[float, ...]) -> dict[str, np.ndarray]:
    n = len(x)
    phase = np.full(n, np.nan)
    amp = np.full(n, np.nan)
    recon = np.full(n, np.nan)
    freqs = rfftfreq(win, d=1.0)
    mask = np.zeros(len(freqs), dtype=bool)
    for p in periods:
        mask |= _band_mask(freqs, p)
    if not mask.any():
        return {"phase": phase, "amp": amp, "recon": recon, "dphase": phase.copy()}
    for i in range(win - 1, n):
        seg = np.asarray(x[i - win + 1 : i + 1], dtype=float).copy()
        if not np.isfinite(seg).all():
            continue
        seg = seg - seg.mean()
        X = rfft(seg)
        Y = np.zeros_like(X)
        Y[mask] = X[mask]
        y = irfft(Y, n=win)
        Yq = np.zeros_like(Y)
        Yq[mask] = -1j * np.sign(freqs[mask]) * Y[mask]
        q = irfft(Yq, n=win)
        recon[i] = float(y[-1])
        amp[i] = float(np.hypot(y[-1], q[-1]))
        phase[i] = float(np.arctan2(q[-1], y[-1]))
    dphase = np.full(n, np.nan)
    valid = np.isfinite(phase)
    if valid.sum() >= 3:
        idx = np.where(valid)[0]
        un = np.unwrap(phase[idx])
        dp = np.empty_like(un)
        dp[0] = np.nan
        dp[1:] = np.diff(un)
        dphase[idx] = dp
    return {"phase": phase, "amp": amp, "recon": recon, "dphase": dphase}


def _blend(comp: pd.DataFrame, sat_df: pd.DataFrame, w_sat: np.ndarray) -> pd.DataFrame:
    w = np.clip(np.asarray(w_sat, dtype=float), 0.0, 1.0)
    rc = comp["nav"].pct_change().fillna(0.0).to_numpy()
    rs = sat_df["nav"].pct_change().fillna(0.0).to_numpy()
    r = (1.0 - w) * rc + w * rs
    nav = (1.0 + r).cumprod() * float(comp["nav"].iloc[0])
    return pd.DataFrame({"date": comp["date"].to_numpy(), "nav": nav})


def _eval_vs_live(live: pd.DataFrame, chal: pd.DataFrame, *, fam: str, id_: str, extra: dict | None = None) -> dict[str, Any]:
    tip = _tip(live, chal)
    held_base = (_pack(live).get("heldout_2019_plus") or {}).get("cagr")
    held_chal = (_pack(chal).get("heldout_2019_plus") or {}).get("cagr")
    held_mdd_b = (_pack(live).get("heldout_2019_plus") or {}).get("max_drawdown")
    held_mdd_c = (_pack(chal).get("heldout_2019_plus") or {}).get("max_drawdown")
    cagr_pp = cagr_lift_pp(held_base, held_chal)
    mdd_pp = mdd_delta_pp(held_mdd_b, held_mdd_c)
    tip_y = (tip.get("ytd") or {}).get("cagr_lift_pp")
    tip_1 = (tip.get("trailing_1y") or {}).get("cagr_lift_pp")
    tip_ym = (tip.get("ytd") or {}).get("mdd_improve_pp")
    tip_1m = (tip.get("trailing_1y") or {}).get("mdd_improve_pp")
    tip_cagr_ok = tip_y is not None and tip_1 is not None and tip_y >= TIP_CAGR_MIN_PP and tip_1 >= TIP_CAGR_MIN_PP
    tip_mdd_ok = tip_ym is not None and tip_1m is not None and tip_ym >= TIP_MDD_MIN_PP and tip_1m >= TIP_MDD_MIN_PP
    tip_clean = bool(tip_cagr_ok and tip_mdd_ok)
    cagr_ok = cagr_pp is not None and float(cagr_pp) >= CAGR_FLOOR_PP
    mdd_ok = mdd_pp is not None and float(mdd_pp) >= HELD_MDD_MIN_PP
    y2022_b = _year_ret(live, 2022)
    y2022_c = _year_ret(chal, 2022)
    y2022_gap = None if y2022_b is None or y2022_c is None else round(y2022_c - y2022_b, 2)
    row = {
        "id": id_,
        "fam": fam,
        "held_cagr_lift_pp": None if cagr_pp is None else round(float(cagr_pp), 4),
        "held_mdd_pp": None if mdd_pp is None else round(float(mdd_pp), 4),
        "tip_ytd_cagr_pp": tip_y,
        "tip_1y_cagr_pp": tip_1,
        "tip_ytd_mdd_pp": tip_ym,
        "tip_1y_mdd_pp": tip_1m,
        "tip_clean": tip_clean,
        "y2022_vs_base": y2022_gap,
        "gates": {
            "cagr": bool(cagr_ok),
            "mdd": bool(mdd_ok),
            "tip_clean": tip_clean,
            "y2022_nonneg": y2022_gap is not None and y2022_gap >= 0,
            "shaped": bool(cagr_ok and mdd_ok and tip_clean),
        },
    }
    if extra:
        row.update(extra)
    return row


def _screen_entry_feats(events: pd.DataFrame, feats: list[str]) -> list[dict[str, Any]]:
    y = events["comp_minus_sat_ep"].to_numpy(dtype=float)
    y_bin = events["y_good"].to_numpy(dtype=float)
    out: list[dict[str, Any]] = []
    for f in feats:
        if f not in events.columns:
            continue
        x = events[f].to_numpy(dtype=float)
        ic = _spearman(x, y)
        m = np.isfinite(x) & np.isfinite(y_bin)
        hit = side = None
        if m.sum() >= 20:
            med = float(np.nanmedian(x[m]))
            hit_hi = float(np.mean((x[m] >= med).astype(float) == y_bin[m]))
            hit_lo = float(np.mean((x[m] <= med).astype(float) == y_bin[m]))
            if hit_hi >= hit_lo:
                hit, side = hit_hi, "high→good"
            else:
                hit, side = hit_lo, "low→good"
        ic_oof = _spearman(
            events.loc[events["year"] <= 2018, f].to_numpy(dtype=float),
            events.loc[events["year"] <= 2018, "comp_minus_sat_ep"].to_numpy(dtype=float),
        )
        ic_held = _spearman(
            events.loc[events["year"] >= 2019, f].to_numpy(dtype=float),
            events.loc[events["year"] >= 2019, "comp_minus_sat_ep"].to_numpy(dtype=float),
        )
        out.append(
            {
                "feature": f,
                "n": int(np.isfinite(x).sum()),
                "ic_full": None if ic is None else round(ic, 4),
                "ic_oof_le2018": None if ic_oof is None else round(ic_oof, 4),
                "ic_held_ge2019": None if ic_held is None else round(ic_held, 4),
                "hit_median": None if hit is None else round(hit, 4),
                "hit_side": side,
                "abs_ic": 0.0 if ic is None else abs(ic),
            }
        )
    out.sort(key=lambda r: r["abs_ic"], reverse=True)
    return out


def label_comp_entries(m: pd.DataFrame, feat_cols: list[str]) -> pd.DataFrame:
    w = m["w_sat"].to_numpy()
    rows: list[dict[str, Any]] = []
    i = 1
    while i < len(m):
        if w[i - 1] > 0.5 and w[i] < 0.5:
            j = i
            while j + 1 < len(m) and w[j + 1] < 0.5:
                j += 1
            ep = m.iloc[i : j + 1]
            rc = float((1.0 + ep["r_c"]).prod() - 1.0)
            rs = float((1.0 + ep["r_s"]).prod() - 1.0)
            row0 = m.iloc[i]
            rec: dict[str, Any] = {
                "date": str(row0["date"].date()),
                "year": int(row0["date"].year),
                "n_days": int(j - i + 1),
                "comp_minus_sat_ep": round((rc - rs) * 100, 4),
                "y_good": int(rc > rs),
            }
            for c in feat_cols:
                v = row0[c]
                rec[c] = None if pd.isna(v) else float(v)
            rows.append(rec)
            i = j + 1
            continue
        i += 1
    return pd.DataFrame(rows)


def _write_pack(
    *,
    charter_id: str,
    screen_id: str,
    decision_id: str,
    register: str,
    verdict: str,
    charter_lines: list[str],
    screen_md: str,
    decision_md: str,
    screen_obj: dict[str, Any],
    decision_obj: dict[str, Any],
) -> None:
    write_ops_and_repro_pointer(
        OPS / f"{charter_id}.md", REP / f"{charter_id}.md", "\n".join(charter_lines) + "\n", kind="charter"
    )
    (OPS / f"{charter_id}.json").write_text(
        json.dumps(
            {
                "id": charter_id,
                "register": register,
                "soft_frozen_keep": True,
                "path3_observe_keep": True,
                "fill_emit_flags": False,
                "live_wire": False,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    write_repro_pointer(OPS / f"{charter_id}.json", REP / f"{charter_id}.json", kind="charter")
    (OUT / f"{screen_id.lower()}.json").write_text(
        json.dumps(screen_obj, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8"
    )
    (OPS / f"{screen_id}.json").write_text(
        json.dumps(screen_obj, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8"
    )
    write_repro_pointer(OPS / f"{screen_id}.json", REP / f"{screen_id}.json", kind="screen")
    write_ops_and_repro_pointer(OPS / f"{screen_id}.md", REP / f"{screen_id}.md", screen_md, kind="screen")
    write_ops_and_repro_pointer(
        OPS / f"{decision_id}.md", REP / f"{decision_id}.md", decision_md, kind="decision pack"
    )
    (OPS / f"{decision_id}.json").write_text(
        json.dumps(decision_obj, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8"
    )
    write_repro_pointer(OPS / f"{decision_id}.json", REP / f"{decision_id}.json", kind="decision pack")


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()

    live = _load(LIVE_NAV)
    comp = _load(COMP_NAV)
    sat_df = _load(SAT_NAV)
    dates = sorted(set(live["date"]) & set(comp["date"]) & set(sat_df["date"]))
    live = live[live["date"].isin(dates)].reset_index(drop=True)
    comp = comp[comp["date"].isin(dates)].reset_index(drop=True)
    sat_df = sat_df[sat_df["date"].isin(dates)].reset_index(drop=True)

    market0 = sat.load_market()
    px = market0[market0["code"].astype(str) == "0050"].copy()
    px["date"] = pd.to_datetime(px["date"])
    close = (
        px.drop_duplicates("date")
        .set_index("date")["adj_close" if "adj_close" in px.columns else "close"]
        .astype(float)
    )
    close = close[~close.index.duplicated(keep="last")]
    r0050 = close.pct_change()

    m = (
        comp.rename(columns={"nav": "nav_c"})
        .merge(sat_df.rename(columns={"nav": "nav_s"}), on="date")
        .sort_values("date")
        .reset_index(drop=True)
    )
    m["r_c"] = m["nav_c"].pct_change().fillna(0.0)
    m["r_s"] = m["nav_s"].pct_change().fillna(0.0)
    m["rel"] = m["r_c"] - m["r_s"]
    m["trail_rel_63"] = _trail(m["rel"], 63)
    m["sat_lead"] = (m["trail_rel_63"] <= -THETA).fillna(False)
    m["w_sat"] = m["sat_lead"].astype(float)
    m["r0050"] = m["date"].map(r0050)
    m["r0050_63"] = _trail(m["r0050"].fillna(0.0), 63)
    m["rel_5"] = m["rel"].rolling(5, min_periods=5).sum()

    print("causal STFT on exogenous trail_r0050_63 ...", flush=True)
    x50 = m["r0050_63"].fillna(0.0).to_numpy()
    stft50 = _causal_stft(x50, win=STFT_WIN, periods=PERIODS)
    for k, arr in stft50.items():
        m[f"exog_{k}"] = arr

    # also endogenous carriers for compare-only (not for promote)
    xrel = m["trail_rel_63"].fillna(0.0).to_numpy()
    stft_rel = _causal_stft(xrel, win=STFT_WIN, periods=PERIODS)
    for k, arr in stft_rel.items():
        m[f"endo_{k}"] = arr

    feat_cols = [
        "r0050_63",
        "rel_5",
        "exog_phase",
        "exog_amp",
        "exog_recon",
        "exog_dphase",
        "endo_recon",
        "endo_dphase",
    ]
    events = label_comp_entries(m, feat_cols)
    events.to_csv(OUT / "comp_entry_events_exog.csv", index=False)
    feat_rows = _screen_entry_feats(events, feat_cols)
    pd.DataFrame(feat_rows).to_csv(OUT / "feature_screen_exog.csv", index=False)

    exog_rows = [r for r in feat_rows if str(r["feature"]).startswith("exog_")]
    td_rows = [r for r in feat_rows if r["feature"] in ("r0050_63", "rel_5")]
    exog_best = exog_rows[0] if exog_rows else None
    td_best = next((r for r in td_rows if r["feature"] == "r0050_63"), td_rows[0] if td_rows else None)

    # --- Arm A probes: hard switch AND ---
    w_p3 = m["w_sat"].to_numpy(dtype=float)
    nav_p3 = _blend(comp, sat_df, w_p3)
    nav_p3.to_csv(OUT / "nav_P3_T0_STATE.csv", index=False)

    books_a: list[dict[str, Any]] = []
    books_a.append(_eval_vs_live(live, nav_p3, fam="ref", id_="P3_T0_STATE", extra={"pct_sat": round(float(w_p3.mean()) * 100, 2)}))

    # TD AND: SAT only if SAT_LEAD AND r0050_63 <= median(neg)
    r50 = m["r0050_63"].to_numpy(dtype=float)
    med_r50 = float(np.nanmedian(r50[np.isfinite(r50)]))
    w_td = ((m["sat_lead"].to_numpy()) & (r50 <= med_r50)).astype(float)
    nav_td = _blend(comp, sat_df, w_td)
    nav_td.to_csv(OUT / "nav_AND_TD_R0050.csv", index=False)
    books_a.append(
        _eval_vs_live(
            live,
            nav_td,
            fam="and",
            id_="AND_TD_R0050",
            extra={"pct_sat": round(float(w_td.mean()) * 100, 2), "rule": "SAT_LEAD & r0050_63<=med"},
        )
    )

    # EXOG AND variants
    for feat, side_prefer in (
        ("exog_recon", "low"),  # low recon → risk-off / SAT prefer when also SAT_LEAD
        ("exog_amp", "high"),
        ("exog_dphase", "low"),
        ("exog_phase", "low"),
    ):
        x = m[feat].to_numpy(dtype=float)
        med = float(np.nanmedian(x[np.isfinite(x)])) if np.isfinite(x).any() else 0.0
        if side_prefer == "low":
            fft_ok = x <= med
        else:
            fft_ok = x >= med
        # enter SAT only when SAT_LEAD AND fft_ok
        w = (m["sat_lead"].to_numpy() & fft_ok & np.isfinite(x)).astype(float)
        nav = _blend(comp, sat_df, w)
        nid = f"AND_EXOG_{feat}"
        nav.to_csv(OUT / f"nav_{nid}.csv", index=False)
        books_a.append(
            _eval_vs_live(
                live,
                nav,
                fam="and",
                id_=nid,
                extra={
                    "pct_sat": round(float(w.mean()) * 100, 2),
                    "rule": f"SAT_LEAD & {feat} {side_prefer} med",
                },
            )
        )

    # Block COMP on exit from SAT when exog best says risk (high→good means block if low)
    if exog_best and exog_best.get("hit_side"):
        f = exog_best["feature"]
        x = m[f].to_numpy(dtype=float)
        thr = float(np.nanmedian(events[f].to_numpy(dtype=float))) if f in events.columns else float(np.nanmedian(x[np.isfinite(x)]))
        side = exog_best["hit_side"]
        w = np.zeros(len(m), dtype=float)
        for i in range(len(m)):
            if w_p3[i] > 0.5:
                w[i] = 1.0
                continue
            xi = x[i]
            if not np.isfinite(xi):
                w[i] = 0.0
                continue
            block = xi < thr if side == "high→good" else xi > thr
            if i > 0 and w[i - 1] > 0.5 and block:
                w[i] = 1.0
            else:
                w[i] = 0.0
        nav = _blend(comp, sat_df, w)
        nav.to_csv(OUT / "nav_BLOCK_EXOG_BEST.csv", index=False)
        books_a.append(
            _eval_vs_live(
                live,
                nav,
                fam="block",
                id_="BLOCK_EXOG_BEST",
                extra={"pct_sat": round(float(w.mean()) * 100, 2), "feature": f, "side": side},
            )
        )

    # Arm A verdict — must beat / not lose parent P3 (not just live CTRL)
    p3a = next(b for b in books_a if b["id"] == "P3_T0_STATE")
    p3_tip = p3a.get("tip_ytd_cagr_pp")
    p3_held = p3a.get("held_cagr_lift_pp")
    p3_y22 = p3a.get("y2022_vs_base")

    def _beats_p3(b: dict[str, Any]) -> bool:
        if b.get("fam") == "ref":
            return False
        ty, he, y22 = b.get("tip_ytd_cagr_pp"), b.get("held_cagr_lift_pp"), b.get("y2022_vs_base")
        if ty is None or he is None or p3_tip is None or p3_held is None:
            return False
        tip_ok = float(ty) + 0.05 >= float(p3_tip)
        held_ok = float(he) + 0.15 >= float(p3_held)
        y_ok = y22 is None or p3_y22 is None or float(y22) + 0.25 >= float(p3_y22)
        improved = (
            float(ty) > float(p3_tip) + 0.10
            or float(he) > float(p3_held) + 0.10
            or (y22 is not None and p3_y22 is not None and float(y22) > float(p3_y22) + 0.50)
        )
        return bool(b["gates"]["tip_clean"] and tip_ok and held_ok and y_ok and improved)

    and_beats = [b for b in books_a if _beats_p3(b)]
    tip_soft = [
        b
        for b in books_a
        if b["fam"] in ("and", "block")
        and b["gates"]["tip_clean"]
        and not _beats_p3(b)
    ]
    eb = exog_best or {}
    abs_ic = eb.get("abs_ic") or 0.0
    hit = eb.get("hit_median") or 0.0
    if and_beats:
        verdict_a = "EXOG_FFT_HIT"
    elif tip_soft and abs_ic >= IC_EDGE and hit >= HIT_WEAK:
        verdict_a = "EXOG_FFT_SOFT"
    elif abs_ic >= IC_EDGE and hit >= HIT_WEAK:
        verdict_a = "EXOG_FFT_SIGNAL"
    elif abs_ic >= IC_WEAK or hit >= HIT_WEAK:
        verdict_a = "EXOG_FFT_WEAK"
    else:
        verdict_a = "EXOG_FFT_NO_EDGE"

    # --- Arm B: non-switch soft tilt + observe IC ---
    amp = m["exog_amp"].to_numpy(dtype=float)
    amp_med = float(np.nanmedian(amp[np.isfinite(amp)])) if np.isfinite(amp).any() else 0.0
    amp_z = np.where(np.isfinite(amp), np.tanh((amp - amp_med) / (amp_med + 1e-12)), 0.0)
    recon = m["exog_recon"].to_numpy(dtype=float)
    recon_med = float(np.nanmedian(recon[np.isfinite(recon)])) if np.isfinite(recon).any() else 0.0
    recon_sign = np.where(np.isfinite(recon), np.sign(recon - recon_med), 0.0)

    books_b: list[dict[str, Any]] = []
    books_b.append(_eval_vs_live(live, nav_p3, fam="ref", id_="P3_HARD", extra={"pct_sat": round(float(w_p3.mean()) * 100, 2)}))

    for a in TILTS:
        # tilt toward SAT when amp high (defensive spectral energy)
        w_amp = np.clip(w_p3 + a * amp_z, 0.0, 1.0)
        nav_amp = _blend(comp, sat_df, w_amp)
        nav_amp.to_csv(OUT / f"nav_TILT_AMP_{int(a*100)}.csv", index=False)
        books_b.append(
            _eval_vs_live(
                live,
                nav_amp,
                fam="tilt",
                id_=f"TILT_AMP_{int(a*100)}",
                extra={"tilt": a, "pct_sat": round(float(w_amp.mean()) * 100, 2)},
            )
        )
        # tilt toward SAT when recon below median (negative band)
        w_rec = np.clip(w_p3 - a * recon_sign, 0.0, 1.0)  # recon high → less SAT
        nav_rec = _blend(comp, sat_df, w_rec)
        nav_rec.to_csv(OUT / f"nav_TILT_RECON_{int(a*100)}.csv", index=False)
        books_b.append(
            _eval_vs_live(
                live,
                nav_rec,
                fam="tilt",
                id_=f"TILT_RECON_{int(a*100)}",
                extra={"tilt": a, "pct_sat": round(float(w_rec.mean()) * 100, 2)},
            )
        )

    # Observe-only: IC of exog feats vs forward COMP−SAT 21d (no weight change)
    fwd = []
    for h in (5, 21, 63):
        y = []
        for i in range(len(m)):
            end = min(i + h - 1, len(m) - 1)
            g = m.iloc[i : end + 1]
            y.append(float((1.0 + g["r_c"]).prod() - (1.0 + g["r_s"]).prod()))
        m[f"fwd_cms_{h}"] = y
        for f in ("exog_amp", "exog_recon", "exog_dphase", "exog_phase", "r0050_63"):
            ic = _spearman(m[f].to_numpy(dtype=float), m[f"fwd_cms_{h}"].to_numpy(dtype=float))
            fwd.append({"feat": f, "h": h, "ic": None if ic is None else round(ic, 4), "abs_ic": 0.0 if ic is None else abs(ic)})
    fwd.sort(key=lambda r: r["abs_ic"], reverse=True)
    pd.DataFrame(fwd).to_csv(OUT / "observe_fwd_ic.csv", index=False)

    # Arm B verdict — soft tilt must not lose to Path3 hard parent
    p3b = next(b for b in books_b if b["id"] == "P3_HARD")
    p3b_tip = p3b.get("tip_ytd_cagr_pp")
    p3b_held = p3b.get("held_cagr_lift_pp")
    p3b_y22 = p3b.get("y2022_vs_base")

    def _tilt_beats_p3(b: dict[str, Any]) -> bool:
        if b.get("fam") != "tilt":
            return False
        ty, he, y22 = b.get("tip_ytd_cagr_pp"), b.get("held_cagr_lift_pp"), b.get("y2022_vs_base")
        if ty is None or he is None or p3b_tip is None or p3b_held is None:
            return False
        tip_ok = float(ty) + 0.05 >= float(p3b_tip)
        held_ok = float(he) + 0.15 >= float(p3b_held)
        y_ok = y22 is None or p3b_y22 is None or float(y22) + 0.25 >= float(p3b_y22)
        improved = (
            float(ty) > float(p3b_tip) + 0.10
            or float(he) > float(p3b_held) + 0.10
            or (y22 is not None and p3b_y22 is not None and float(y22) > float(p3b_y22) + 0.50)
        )
        return bool(b["gates"]["tip_clean"] and tip_ok and held_ok and y_ok and improved)

    tilt_beats = [b for b in books_b if _tilt_beats_p3(b)]
    tilt_tip_only = [
        b for b in books_b if b["fam"] == "tilt" and b["gates"]["tip_clean"] and not _tilt_beats_p3(b)
    ]
    best_obs = fwd[0] if fwd else None
    # observe "FFT-only" if best abs_ic is an exog_* feat (not pure TD r0050)
    fft_obs = [r for r in fwd if str(r["feat"]).startswith("exog_")]
    best_fft_obs = fft_obs[0] if fft_obs else None
    if tilt_beats:
        verdict_b = "FFT_TILT_HIT"
    elif tilt_tip_only and best_fft_obs and (best_fft_obs.get("abs_ic") or 0) >= IC_EDGE:
        verdict_b = "FFT_TILT_SOFT"
    elif best_fft_obs and (best_fft_obs.get("abs_ic") or 0) >= IC_WEAK:
        verdict_b = "FFT_OBSERVE_ONLY"
    else:
        # all tilts dominated by P3 hard; weak/no FFT observe edge
        dominated = bool(tilt_tip_only) and not tilt_beats
        verdict_b = "FFT_TILT_DOMINATED" if dominated else "FFT_TILT_NO_EDGE"

    # persist books
    (OUT / "books_arm_a.json").write_text(json.dumps(books_a, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT / "books_arm_b.json").write_text(json.dumps(books_b, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # ---- write Arm A packs ----
    summary_a = {
        "exog_best": exog_best,
        "td_best": td_best,
        "n_entries": len(events),
        "books": books_a,
    }
    charter_a = [
        f"# {CHARTER_A}",
        "",
        "Date: 2026-09-29",
        "Status: **Stage A — exogenous 0050 FFT × TD AND** · Soft-Frozen **KEEP** · Path3 observe **KEEP** · "
        "fill/emit **OFF** · no live",
        "Parents: 0ka0 / 0k9j / 0k9p / 0k9z",
        f"Register: **{REG_A}**",
        "",
        "## Question",
        "",
        "外生 `trail_r0050_63` 因果 STFT（85/128/256td）× 時域 SAT_LEAD／`r0050_63` AND，"
        "能否當 Path3 買賣／進場濾網？",
        "",
        f"Label: `{CHARTER_A}_2026-09-29__EXOG_FFT_AND__NO_LIVE`",
        "",
    ]
    md_a = [
        f"# {SCREEN_A}",
        "",
        f"Date: 2026-09-29 · `{generated}` · Verdict **`{verdict_a}`**",
        "",
        "## Entry feature screen",
        "",
        "| feature | IC | OOF | held | hit | side |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for r in feat_rows[:10]:
        md_a.append(
            f"| `{r['feature']}` | {r['ic_full']} | {r['ic_oof_le2018']} | {r['ic_held_ge2019']} | "
            f"{r['hit_median']} | {r['hit_side']} |"
        )
    md_a += ["", "## Books", "", "| id | fam | held↑ | tipY↑ | tipClean | y2022 | shaped |", "|---|---|---:|---:|---|---:|---|"]
    for b in books_a:
        md_a.append(
            f"| `{b['id']}` | {b['fam']} | {b['held_cagr_lift_pp']} | {b['tip_ytd_cagr_pp']} | "
            f"{b['tip_clean']} | {b['y2022_vs_base']} | {b['gates']['shaped']} |"
        )
    md_a += ["", "Repro: `repro/fin-sat-fft-exog-tilt-stagea/`", ""]
    best_a = max(
        (b for b in books_a if b["fam"] != "ref"),
        key=lambda b: (b["gates"]["shaped"], b["tip_clean"], b["held_cagr_lift_pp"] or -999),
        default=None,
    )
    dec_a = "\n".join(
        [
            f"# {DECISION_A}",
            "",
            f"Date: 2026-09-29 · Verdict: **`{verdict_a}`**",
            "Status: Soft-Frozen **KEEP** · Path3 observe **KEEP** · fill/emit **OFF** · no live",
            f"Register: **{REG_A}**",
            "",
            "## Answer",
            "",
            f"外生 FFT 最佳 `{eb.get('feature')}` IC **{eb.get('ic_full')}** hit **{eb.get('hit_median')}** "
            f"(vs TD `r0050_63` IC {(td_best or {}).get('ic_full')}).",
            f"最佳規則書：`{(best_a or {}).get('id')}` tipY↑ {(best_a or {}).get('tip_ytd_cagr_pp')} · "
            f"held↑ {(best_a or {}).get('held_cagr_lift_pp')} · y2022={(best_a or {}).get('y2022_vs_base')} "
            f"（P3 tipY↑ {p3_tip} held↑ {p3_held} y2022 {p3_y22} — **未擊敗 parent**）。",
            "",
            "## Implication",
            "",
            "- 判決相對 **P3 parent**（非僅 vs live）：輸 tip／held／2022 → 不 HIT。",
            "- HIT／SOFT 才可開小規則 follow-up；WEAK／NO_EDGE → 外生頻譜不當買賣主特徵。",
            "- 不翻 Path3 observe／fill／emit · Soft-Frozen Exact T+1 KEEP。",
            "",
            f"Screen: `{SCREEN_A}.md` · Charter: `{CHARTER_A}.md`",
            "",
            f"Label: `{DECISION_A}_2026-09-29__{verdict_a}__NO_LIVE`",
            "",
        ]
    )
    _write_pack(
        charter_id=CHARTER_A,
        screen_id=SCREEN_A,
        decision_id=DECISION_A,
        register=REG_A,
        verdict=verdict_a,
        charter_lines=charter_a,
        screen_md="\n".join(md_a) + "\n",
        decision_md=dec_a,
        screen_obj={
            "label": f"{SCREEN_A}_{generated.replace(':','').replace('-','')}",
            "verdict": verdict_a,
            "register": REG_A,
            "features": feat_rows,
            "books": books_a,
            "summary": summary_a,
            "soft_frozen_keep": True,
            "live_wire": False,
        },
        decision_obj={
            "label": f"{DECISION_A}_2026-09-29__{verdict_a}__NO_LIVE",
            "verdict": verdict_a,
            "register": REG_A,
            "exog_best": exog_best,
            "td_best": td_best,
            "best_book": best_a,
            "books": books_a,
            "soft_frozen_keep": True,
            "path3_observe_keep": True,
            "fill_emit_flags": False,
            "live_wire": False,
        },
    )

    # ---- Arm B packs ----
    charter_b = [
        f"# {CHARTER_B}",
        "",
        "Date: 2026-09-29",
        "Status: **Stage A — FFT non-switch soft tilt / observe** · Soft-Frozen **KEEP** · "
        "Path3 observe **KEEP** · fill/emit **OFF** · no live",
        "Parents: 0ka0 / 0k9j / 0ka1",
        f"Register: **{REG_B}**",
        "",
        "## Question",
        "",
        "在**不改** Path3 硬切換下，外生 FFT amp／recon soft-tilt（a=5–25%）能否改善 tip／held？"
        "或僅具觀測 IC？",
        "",
        f"Label: `{CHARTER_B}_2026-09-29__NONSWITCH_TILT__NO_LIVE`",
        "",
    ]
    md_b = [
        f"# {SCREEN_B}",
        "",
        f"Date: 2026-09-29 · `{generated}` · Verdict **`{verdict_b}`**",
        "",
        "## Observe-only fwd IC (top)",
        "",
        "| feat | h | IC |",
        "|---|---:|---:|",
    ]
    for r in fwd[:8]:
        md_b.append(f"| `{r['feat']}` | {r['h']} | {r['ic']} |")
    md_b += ["", "## Soft-tilt books", "", "| id | held↑ | tipY↑ | tipClean | y2022 | shaped |", "|---|---:|---:|---|---:|---|"]
    for b in books_b:
        md_b.append(
            f"| `{b['id']}` | {b['held_cagr_lift_pp']} | {b['tip_ytd_cagr_pp']} | "
            f"{b['tip_clean']} | {b['y2022_vs_base']} | {b['gates']['shaped']} |"
        )
    md_b += ["", "Repro: `repro/fin-sat-fft-exog-tilt-stagea/`", ""]
    best_b = max(
        (b for b in books_b if b["fam"] == "tilt"),
        key=lambda b: (b["gates"]["shaped"], b["tip_clean"], b["held_cagr_lift_pp"] or -999),
        default=None,
    )
    dec_b = "\n".join(
        [
            f"# {DECISION_B}",
            "",
            f"Date: 2026-09-29 · Verdict: **`{verdict_b}`**",
            "Status: Soft-Frozen **KEEP** · Path3 observe **KEEP** · fill/emit **OFF** · no live",
            f"Register: **{REG_B}**",
            "",
            "## Answer",
            "",
            f"Soft-tilt 最佳 `{ (best_b or {}).get('id') }` tipY↑ {(best_b or {}).get('tip_ytd_cagr_pp')} · "
            f"held↑ {(best_b or {}).get('held_cagr_lift_pp')} · tipClean={(best_b or {}).get('tip_clean')} "
            f"（對照 P3 tipY↑ {p3b_tip} held↑ {p3b_held} y2022 {p3b_y22} — tilt **未優於** hard parent）。",
            f"Observe-only best `{ (best_obs or {}).get('feat') }` h={(best_obs or {}).get('h')} "
            f"IC={(best_obs or {}).get('ic')}；最佳外生 FFT observe "
            f"`{ (best_fft_obs or {}).get('feat') }` IC={(best_fft_obs or {}).get('ic')}。",
            "",
            "## Implication",
            "",
            "- Soft-tilt 必須不輸 P3 hard（tip／held／2022）；僅 tip-clean vs live 不算 HIT。",
            "- `FFT_TILT_DOMINATED`／`NO_EDGE` → 頻域不當曝險旋鈕；Path3 hard switch **KEEP**。",
            "- Soft-Frozen Exact T+1 KEEP · fill/emit OFF · no live。",
            "",
            f"Screen: `{SCREEN_B}.md` · Charter: `{CHARTER_B}.md`",
            "",
            f"Label: `{DECISION_B}_2026-09-29__{verdict_b}__NO_LIVE`",
            "",
        ]
    )
    _write_pack(
        charter_id=CHARTER_B,
        screen_id=SCREEN_B,
        decision_id=DECISION_B,
        register=REG_B,
        verdict=verdict_b,
        charter_lines=charter_b,
        screen_md="\n".join(md_b) + "\n",
        decision_md=dec_b,
        screen_obj={
            "label": f"{SCREEN_B}_{generated.replace(':','').replace('-','')}",
            "verdict": verdict_b,
            "register": REG_B,
            "observe_fwd_ic": fwd,
            "books": books_b,
            "soft_frozen_keep": True,
            "live_wire": False,
        },
        decision_obj={
            "label": f"{DECISION_B}_2026-09-29__{verdict_b}__NO_LIVE",
            "verdict": verdict_b,
            "register": REG_B,
            "best_tilt": best_b,
            "best_observe": best_obs,
            "books": books_b,
            "soft_frozen_keep": True,
            "path3_observe_keep": True,
            "fill_emit_flags": False,
            "live_wire": False,
        },
    )

    print(
        json.dumps(
            {
                "arm_a": {"verdict": verdict_a, "exog_best": exog_best, "best_book": best_a},
                "arm_b": {"verdict": verdict_b, "best_tilt": best_b, "best_observe": best_obs},
            },
            indent=2,
            ensure_ascii=False,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
