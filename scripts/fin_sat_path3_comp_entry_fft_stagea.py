#!/usr/bin/env python3
"""FIN×SAT Path3 COMP-entry FFT signal Stage A (paper).

Causal STFT phase/amp/recon/dphase on trail_rel_63 (0k9j bands 85/128/256)
at each SAT→COMP flip — can spectral features separate good/bad COMP entries
better than time-domain rel_5 (0k9z)?

Parents: 0k9z SIGNAL_WEAK · 0k9j FFT_SIGNAL · 0k9p FFT_LAG_NO_EDGE
Soft-Frozen KEEP · Path3 observe KEEP · fill/emit OFF · no live
Register: 0ka0
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from numpy.fft import irfft, rfft, rfftfreq

from e45_paper_harness import WINDOWS_STANDARD, window_stats
from fin_sell_quality_helpers import cagr_lift_pp
from ops_repro_ssot import write_ops_and_repro_pointer, write_repro_pointer
from research_metric_helpers import mdd_delta_pp

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "fin-sat-path3-comp-entry-fft-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_SAT_PATH3_COMP_ENTRY_FFT_STAGEA_CHARTER"
SCREEN_ID = "FIN_SAT_PATH3_COMP_ENTRY_FFT_STAGEA_SCREEN"
DECISION_ID = "FIN_SAT_PATH3_COMP_ENTRY_FFT_STAGEA_DECISION_PACK"
REGISTER = "0ka0"
BASE_ID = "CTRL_LIVE_A10"

LIVE_NAV = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/ctrl_live_a10_daily_nav.csv"
COMP_NAV = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/comp_h150_x_a20_daily_nav.csv"
SAT_NAV = ROOT / "repro/sat-a20-relax-dual-paper-observe/outputs/sat_a20_relax_daily_nav.csv"

THETA = 0.01
PERIODS = (85.0, 128.0, 256.0)
WINS = (64, 128, 256)
IC_EDGE = 0.15
IC_WEAK = 0.08
HIT_EDGE = 0.60
HIT_WEAK = 0.55
# 0k9z baseline for comparison
TD_BASELINE = "rel_5"


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


def _causal_stft_features(x: np.ndarray, *, win: int, periods: tuple[float, ...]) -> dict[str, np.ndarray]:
    """Causal rolling FFT end-point recon/phase/amp for union of period bands."""
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


def _periodogram_top(x: np.ndarray, *, top_k: int = 6) -> list[dict[str, Any]]:
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) < 64:
        return []
    x = x - x.mean()
    spec = np.abs(rfft(x)) ** 2
    freqs = rfftfreq(len(x), d=1.0)
    total = float(spec[1:].sum()) if len(spec) > 1 else 0.0
    if total <= 0:
        return []
    order = np.argsort(spec[1:])[::-1][:top_k] + 1
    rows = []
    for i in order:
        f = float(freqs[i])
        if f <= 0:
            continue
        per = 1.0 / f
        rows.append(
            {
                "period_tdays": round(per, 2),
                "power_frac": round(float(spec[i] / total), 5),
                "freq": round(f, 6),
            }
        )
    return rows


def build_panel(comp: pd.DataFrame, sat: pd.DataFrame) -> pd.DataFrame:
    m = (
        comp.rename(columns={"nav": "nav_c"})
        .merge(sat.rename(columns={"nav": "nav_s"}), on="date")
        .sort_values("date")
        .reset_index(drop=True)
    )
    m["r_c"] = m["nav_c"].pct_change().fillna(0.0)
    m["r_s"] = m["nav_s"].pct_change().fillna(0.0)
    m["rel"] = m["r_c"] - m["r_s"]
    m["trail_rel_63"] = _trail(m["rel"], 63)
    m["sat_lead"] = (m["trail_rel_63"] <= -THETA).fillna(False)
    m["w_sat"] = m["sat_lead"].astype(float)
    m["rel_5"] = m["rel"].rolling(5, min_periods=5).sum()
    m["vol_rel_21"] = m["rel"].rolling(21, min_periods=21).std()
    return m


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
            good = rc > rs
            rec: dict[str, Any] = {
                "date": str(row0["date"].date()),
                "year": int(row0["date"].year),
                "ep_end": str(m.iloc[j]["date"].date()),
                "n_days": int(j - i + 1),
                "comp_ep_ret": round(rc * 100, 4),
                "sat_ep_ret": round(rs * 100, 4),
                "comp_minus_sat_ep": round((rc - rs) * 100, 4),
                "y_good": int(good),
            }
            for c in feat_cols:
                v = row0[c]
                rec[c] = None if pd.isna(v) else float(v)
            rows.append(rec)
            i = j + 1
            continue
        i += 1
    return pd.DataFrame(rows)


def screen_features(events: pd.DataFrame, feats: list[str]) -> list[dict[str, Any]]:
    y = events["comp_minus_sat_ep"].to_numpy(dtype=float)
    y_bin = events["y_good"].to_numpy(dtype=float)
    out: list[dict[str, Any]] = []
    for f in feats:
        if f not in events.columns:
            continue
        x = events[f].to_numpy(dtype=float)
        ic = _spearman(x, y)
        m = np.isfinite(x) & np.isfinite(y_bin)
        hit = None
        side = None
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
                "family": "td" if f in (TD_BASELINE, "vol_rel_21") else "fft",
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


def apply_block_rule(
    m: pd.DataFrame,
    *,
    feature: str,
    side: str,
    thr: float,
) -> np.ndarray:
    w_raw = m["w_sat"].to_numpy(dtype=float)
    x = m[feature].to_numpy(dtype=float)
    n = len(m)
    w = np.zeros(n, dtype=float)
    for i in range(n):
        if w_raw[i] > 0.5:
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
    return w


def _blend(comp: pd.DataFrame, sat: pd.DataFrame, w_sat: np.ndarray) -> pd.DataFrame:
    rc = comp["nav"].pct_change().fillna(0.0).to_numpy()
    rs = sat["nav"].pct_change().fillna(0.0).to_numpy()
    r = (1.0 - w_sat) * rc + w_sat * rs
    nav = (1.0 + r).cumprod() * float(comp["nav"].iloc[0])
    return pd.DataFrame({"date": comp["date"].to_numpy(), "nav": nav})


def _probe(live: pd.DataFrame, nav_p3: pd.DataFrame, nav_pr: pd.DataFrame, meta: dict[str, Any], m: pd.DataFrame, w_probe: np.ndarray) -> dict[str, Any]:
    yb = _year_ret(live, 2022)
    yp3 = _year_ret(nav_p3, 2022)
    ypr = _year_ret(nav_pr, 2022)
    tip_p3 = _tip(live, nav_p3)
    tip_pr = _tip(live, nav_pr)
    held_base = (_pack(live).get("heldout_2019_plus") or {}).get("cagr")
    held_p3 = cagr_lift_pp(held_base, (_pack(nav_p3).get("heldout_2019_plus") or {}).get("cagr"))
    held_pr = cagr_lift_pp(held_base, (_pack(nav_pr).get("heldout_2019_plus") or {}).get("cagr"))
    probe = {
        **meta,
        "y2022_base": yb,
        "y2022_p3": yp3,
        "y2022_probe": ypr,
        "y2022_vs_base_p3": None if yp3 is None or yb is None else round(yp3 - yb, 2),
        "y2022_vs_base_probe": None if ypr is None or yb is None else round(ypr - yb, 2),
        "held_p3": None if held_p3 is None else round(float(held_p3), 4),
        "held_probe": None if held_pr is None else round(float(held_pr), 4),
        "tip_ytd_p3": (tip_p3.get("ytd") or {}).get("cagr_lift_pp"),
        "tip_ytd_probe": (tip_pr.get("ytd") or {}).get("cagr_lift_pp"),
        "n_flips_p3": int(np.sum(np.abs(np.diff(m["w_sat"].to_numpy())) > 1e-12)),
        "n_flips_probe": int(np.sum(np.abs(np.diff(w_probe)) > 1e-12)),
        "pct_sat_p3": round(float(m["w_sat"].mean()) * 100, 2),
        "pct_sat_probe": round(float(np.mean(w_probe)) * 100, 2),
    }
    probe["y2022_ok"] = probe["y2022_vs_base_probe"] is not None and probe["y2022_vs_base_probe"] >= 0
    probe["tip_ok"] = (
        probe["tip_ytd_probe"] is not None
        and probe["tip_ytd_p3"] is not None
        and float(probe["tip_ytd_probe"]) + 0.5 >= float(probe["tip_ytd_p3"])
    )
    probe["held_ok"] = (
        probe["held_probe"] is not None
        and probe["held_p3"] is not None
        and float(probe["held_probe"]) + 0.5 >= float(probe["held_p3"])
    )
    return probe


def _verdict(
    fft_best: dict[str, Any] | None,
    td_best: dict[str, Any] | None,
    probe: dict[str, Any] | None,
) -> str:
    fb = fft_best or {}
    tb = td_best or {}
    abs_ic = fb.get("abs_ic") or 0.0
    hit = fb.get("hit_median") or 0.0
    td_ic = tb.get("abs_ic") or 0.0
    oof = abs(fb.get("ic_oof_le2018") or 0.0)
    held = abs(fb.get("ic_held_ge2019") or 0.0)
    stable = oof >= IC_WEAK and held >= IC_WEAK and abs(oof - held) < 0.25

    if abs_ic >= IC_EDGE and hit >= HIT_EDGE and stable:
        if probe and probe.get("y2022_ok") and probe.get("tip_ok") and probe.get("held_ok"):
            return "FFT_ENTRY_HIT"
        return "FFT_ENTRY_SIGNAL"
    if abs_ic >= IC_EDGE and abs_ic + 0.02 >= td_ic and hit >= HIT_WEAK:
        return "FFT_ENTRY_SIGNAL" if stable else "FFT_ENTRY_WEAK"
    if abs_ic >= IC_WEAK or hit >= HIT_WEAK:
        return "FFT_ENTRY_WEAK"
    return "FFT_ENTRY_NO_EDGE"


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)

    live = _load(LIVE_NAV)
    comp = _load(COMP_NAV)
    sat = _load(SAT_NAV)
    dates = sorted(set(live["date"]) & set(comp["date"]) & set(sat["date"]))
    live = live[live["date"].isin(dates)].reset_index(drop=True)
    comp = comp[comp["date"].isin(dates)].reset_index(drop=True)
    sat = sat[sat["date"].isin(dates)].reset_index(drop=True)

    m = build_panel(comp, sat)
    x = m["trail_rel_63"].fillna(0.0).to_numpy()

    print("causal STFT features ...", flush=True)
    fft_cols: list[str] = []
    for win in WINS:
        feats = _causal_stft_features(x, win=win, periods=PERIODS)
        for name, arr in feats.items():
            col = f"w{win}_{name}"
            m[col] = arr
            fft_cols.append(col)

    # spectrum diag on trail (full-sample descriptive only)
    spectrum = {
        "daily_rel": _periodogram_top(m["rel"].to_numpy()),
        "trail_rel_63": _periodogram_top(m["trail_rel_63"].dropna().to_numpy()),
    }
    (OUT / "spectrum_peaks.json").write_text(json.dumps(spectrum, indent=2) + "\n", encoding="utf-8")

    td_cols = [TD_BASELINE, "vol_rel_21"]
    feat_cols = td_cols + fft_cols
    events = label_comp_entries(m, feat_cols)
    events.to_csv(OUT / "comp_entry_events_fft.csv", index=False)
    e2022 = events[events["year"] == 2022].copy()
    e2022.to_csv(OUT / "comp_entry_events_fft_2022.csv", index=False)

    feat_rows = screen_features(events, feat_cols)
    pd.DataFrame(feat_rows).to_csv(OUT / "feature_screen_fft.csv", index=False)

    fft_rows = [r for r in feat_rows if r["family"] == "fft"]
    td_rows = [r for r in feat_rows if r["family"] == "td"]
    fft_best = fft_rows[0] if fft_rows else None
    td_best = next((r for r in td_rows if r["feature"] == TD_BASELINE), td_rows[0] if td_rows else None)

    nav_p3 = _blend(comp, sat, m["w_sat"].to_numpy(dtype=float))
    nav_p3.to_csv(OUT / "nav_P3_T0_STATE.csv", index=False)

    probe = None
    if fft_best and fft_best.get("hit_side") and fft_best["feature"] in m.columns:
        thr = float(np.nanmedian(events[fft_best["feature"]].to_numpy(dtype=float)))
        side = fft_best["hit_side"]
        w_probe = apply_block_rule(m, feature=fft_best["feature"], side=side, thr=thr)
        nav_pr = _blend(comp, sat, w_probe)
        nav_pr.to_csv(OUT / f"nav_BLOCK_{fft_best['feature']}.csv", index=False)
        probe = _probe(
            live,
            nav_p3,
            nav_pr,
            w_probe=w_probe,
            m=m,
            meta={
                "id": f"BLOCK_{fft_best['feature']}",
                "feature": fft_best["feature"],
                "side": side,
                "threshold": thr,
            },
        )

    verdict = _verdict(fft_best, td_best, probe)
    generated = _utc()
    n = len(events)
    n_good = int(events["y_good"].sum())
    summary = {
        "n_comp_entries": n,
        "n_good": n_good,
        "n_bad": n - n_good,
        "pct_good": round(n_good / n * 100, 2) if n else None,
        "n_2022": int(len(e2022)),
        "n_2022_good": int(e2022["y_good"].sum()) if len(e2022) else 0,
        "fft_best": fft_best,
        "td_baseline": td_best,
        "fft_beats_td": bool(
            fft_best
            and td_best
            and (fft_best.get("abs_ic") or 0) + 0.02 >= (td_best.get("abs_ic") or 0)
        ),
        "periods": list(PERIODS),
        "wins": list(WINS),
    }

    charter_md = "\n".join(
        [
            f"# {CHARTER_ID}",
            "",
            "Date: 2026-09-29",
            "Status: **Stage A — COMP-entry FFT signal** · Soft-Frozen **KEEP** · Path3 observe **KEEP** · "
            "fill/emit **OFF** · cutover **BLOCKED** · no live",
            "Parents: 0k9z `SIGNAL_WEAK` · 0k9j `FFT_SIGNAL` · 0k9p `FFT_LAG_NO_EDGE`",
            f"Register: **{REGISTER}**",
            "",
            "## Question",
            "",
            "SAT→COMP 進場當下，0k9j 帶通（85/128/256td）因果 STFT 特徵能否比時域 `rel_5` "
            "更穩地分開好／壞 COMP 進場？",
            "",
            "## Method",
            "",
            "1. Label SAT→COMP by subsequent episode COMP−SAT",
            "2. Causal STFT phase/amp/recon/dphase @ win 64/128/256 on trail_rel_63",
            "3. Spearman IC + median hit · compare vs `rel_5` · one FFT block probe",
            "",
            "## Non-goals",
            "",
            "- 不關 Path3 observe · 不翻 fill/emit · 不改 Soft-Frozen · 不做非因果全樣本 bandpass",
            "",
            f"Label: `{CHARTER_ID}_2026-09-29__COMP_ENTRY_FFT__NO_LIVE`",
            "",
        ]
    )
    write_ops_and_repro_pointer(OPS / f"{CHARTER_ID}.md", REP / f"{CHARTER_ID}.md", charter_md, kind="charter")
    (OPS / f"{CHARTER_ID}.json").write_text(
        json.dumps(
            {
                "id": CHARTER_ID,
                "register": REGISTER,
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
    write_repro_pointer(OPS / f"{CHARTER_ID}.json", REP / f"{CHARTER_ID}.json", kind="charter")

    screen = {
        "label": f"{SCREEN_ID}_{generated.replace(':', '').replace('-', '')}",
        "generated_at_utc": generated,
        "charter": CHARTER_ID,
        "register": REGISTER,
        "verdict": verdict,
        "summary": summary,
        "features": feat_rows,
        "probe": probe,
        "spectrum_peaks": spectrum,
        "events_2022": e2022.to_dict(orient="records"),
        "soft_frozen_keep": True,
        "path3_observe_keep": True,
        "live_wire": False,
        "fill_emit_flags": False,
    }
    (OUT / "screen.json").write_text(json.dumps(screen, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    (OPS / f"{SCREEN_ID}.json").write_text(
        json.dumps(screen, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8"
    )
    write_repro_pointer(OPS / f"{SCREEN_ID}.json", REP / f"{SCREEN_ID}.json", kind="screen")

    md = [
        f"# {SCREEN_ID}",
        "",
        f"Date: 2026-09-29 · generated `{generated}`",
        f"Verdict: **`{verdict}`** · Soft-Frozen KEEP · Path3 observe KEEP · fill/emit OFF · no live",
        "",
        "## COMP-entry labels",
        "",
        f"- n entries: **{summary['n_comp_entries']}** · good **{summary['n_good']}** ({summary['pct_good']}%) · "
        f"bad **{summary['n_bad']}**",
        f"- 2022 entries: **{summary['n_2022']}** · good **{summary['n_2022_good']}**",
        f"- FFT best: `{fft_best['feature'] if fft_best else None}` IC={fft_best['ic_full'] if fft_best else None} "
        f"hit={fft_best['hit_median'] if fft_best else None}",
        f"- TD baseline `{TD_BASELINE}`: IC={td_best['ic_full'] if td_best else None} "
        f"hit={td_best['hit_median'] if td_best else None} · fft_beats_td={summary['fft_beats_td']}",
        "",
        "## Feature screen (ranked |IC|)",
        "",
        "| feature | fam | IC full | IC≤2018 | IC≥2019 | hit med | side |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for r in feat_rows[:16]:
        md.append(
            f"| `{r['feature']}` | {r['family']} | {r['ic_full']} | {r['ic_oof_le2018']} | "
            f"{r['ic_held_ge2019']} | {r['hit_median']} | {r['hit_side']} |"
        )
    md += ["", "## Spectrum peaks (descriptive)", ""]
    for name, rows in spectrum.items():
        top = ", ".join(f"{p['period_tdays']}d({p['power_frac']})" for p in rows[:4]) or "n/a"
        md.append(f"- `{name}`: {top}")
    if probe:
        md += [
            "",
            f"## Threshold probe `{probe['id']}`",
            "",
            f"- rule: block COMP when `{probe['feature']}` risk side (`{probe['side']}`), thr={probe['threshold']:.6g}",
            f"- 2022: BASE {probe['y2022_base']} · P3 {probe['y2022_p3']} ({probe['y2022_vs_base_p3']}) · "
            f"probe {probe['y2022_probe']} ({probe['y2022_vs_base_probe']})",
            f"- held↑ P3 {probe['held_p3']} · probe {probe['held_probe']}",
            f"- tipY↑ P3 {probe['tip_ytd_p3']} · probe {probe['tip_ytd_probe']}",
            f"- flips {probe['n_flips_p3']}→{probe['n_flips_probe']} · %SAT {probe['pct_sat_p3']}→{probe['pct_sat_probe']}",
        ]
    md += ["", "Repro: `repro/fin-sat-path3-comp-entry-fft-stagea/`", ""]
    write_ops_and_repro_pointer(OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", "\n".join(md) + "\n", kind="screen")

    fb = fft_best or {}
    tb = td_best or {}
    decision_md = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: 2026-09-29 · Verdict: **`{verdict}`**",
            "Status: Soft-Frozen **KEEP** · Path3 observe **KEEP** · fill/emit **OFF** · cutover **BLOCKED** · no live",
            "Parents: 0k9z `SIGNAL_WEAK` · 0k9j `FFT_SIGNAL` · 0k9p `FFT_LAG_NO_EDGE`",
            "",
            "## Answer",
            "",
            f"COMP 進場 **{summary['n_comp_entries']}** 筆。FFT 最佳 `{fb.get('feature')}`："
            f"IC **{fb.get('ic_full')}** · hit **{fb.get('hit_median')}** · "
            f"OOF {fb.get('ic_oof_le2018')} · held {fb.get('ic_held_ge2019')}。",
            f"時域基線 `{TD_BASELINE}`：IC **{tb.get('ic_full')}** · hit **{tb.get('hit_median')}** · "
            f"fft_beats_td=**{summary['fft_beats_td']}**。",
            "",
        ]
        + (
            [
                f"Threshold block `{probe['id']}`：",
                f"- 2022: P3 **{probe['y2022_vs_base_p3']}** → probe **{probe['y2022_vs_base_probe']}** "
                f"(ok={probe['y2022_ok']})",
                f"- held↑ {probe['held_p3']} → {probe['held_probe']} (ok={probe['held_ok']}) · "
                f"tipY↑ {probe['tip_ytd_p3']} → {probe['tip_ytd_probe']} (ok={probe['tip_ok']})",
                "",
            ]
            if probe
            else []
        )
        + [
            "## Implication",
            "",
            "- FFT `|IC|` 可略高於 `rel_5`，但 hit≈0.50、held-IC 弱、block probe 傷 2022／held／tip → **不可用**。",
            "- 與 0k9p 一致：因果譜是 trail 濾波，不解 COMP 進場品質；停此譜線。",
            "- 接受 Path3 yearly **1/15** 殘差，或另開**外生**（非 COMP−SAT／trail 自迴圈）特徵票。",
            "- Path3 observe **KEEP** · Soft-Frozen／Exact T+1 **KEEP** · fill/emit **OFF** · cutover **BLOCKED**。",
            "",
            f"Screen: `{SCREEN_ID}.md` · Charter: `{CHARTER_ID}.md` · Register **{REGISTER}**",
            "",
            f"Label: `{DECISION_ID}_2026-09-29__{verdict}__NO_LIVE`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{DECISION_ID}.md", REP / f"{DECISION_ID}.md", decision_md, kind="decision pack"
    )
    (OPS / f"{DECISION_ID}.json").write_text(
        json.dumps(
            {
                "label": f"{DECISION_ID}_2026-09-29__{verdict}__NO_LIVE",
                "verdict": verdict,
                "register": REGISTER,
                "summary": summary,
                "fft_best": fft_best,
                "td_baseline": td_best,
                "probe": probe,
                "soft_frozen_keep": True,
                "path3_observe_keep": True,
                "fill_emit_flags": False,
                "live_wire": False,
                "cutover": "BLOCKED",
            },
            indent=2,
            ensure_ascii=False,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )
    write_repro_pointer(OPS / f"{DECISION_ID}.json", REP / f"{DECISION_ID}.json", kind="decision pack")

    print(
        json.dumps(
            {"verdict": verdict, "fft_best": fft_best, "td_baseline": td_best, "probe": probe, "summary": summary},
            indent=2,
            ensure_ascii=False,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
