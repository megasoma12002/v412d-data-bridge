#!/usr/bin/env python3
"""FIN×SAT tip-gap Wavelet + Laplace Stage A (numpy-only, paper).

Charter: research/ops/FIN_SAT_TIPGAP_WAVE_LAP_STAGEA_CHARTER.md
Parents: 0k9j FFT_SIGNAL · 0k9i tip-gap · COMP + SAT_RELAX KEEP.
Soft-Frozen KEEP · no live · no year-switch.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ops_repro_ssot import write_ops_and_repro_pointer

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "fin-sat-tipgap-wave-lap-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_SAT_TIPGAP_WAVE_LAP_STAGEA_CHARTER"
SCREEN_ID = "FIN_SAT_TIPGAP_WAVE_LAP_STAGEA_SCREEN"
DECISION_ID = "FIN_SAT_TIPGAP_WAVE_LAP_STAGEA_DECISION_PACK"

COMP_NAV = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/comp_h150_x_a20_daily_nav.csv"
SAT_NAV = ROOT / "repro/sat-a20-relax-dual-paper-observe/outputs/sat_a20_relax_daily_nav.csv"
LIVE_NAV = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/ctrl_live_a10_daily_nav.csv"

IC_ABS_MIN = 0.04
FWD = 21
# Morlet scales → periods ~ 4π·scale/(ω0+sqrt(2+ω0^2)) with ω0=6 ≈ 1.03*scale* something
# Use period ≈ scale * 1.033 for ω0=6 (Torrence & Compo)
W0 = 6.0
PERIOD_FACTOR = 4 * np.pi / (W0 + np.sqrt(2.0 + W0 * W0))  # ~1.033


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_nav(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)[["date", "nav"]].assign(
        nav=lambda x: x["nav"].astype(float)
    )


def _trail(r: pd.Series, n: int) -> pd.Series:
    return (1.0 + r).rolling(n, min_periods=n).apply(lambda x: float(np.prod(x) - 1.0), raw=True)


def _fwd_sum(x: pd.Series, n: int) -> pd.Series:
    acc = pd.Series(0.0, index=x.index)
    valid = pd.Series(True, index=x.index)
    for i in range(1, n + 1):
        acc = acc + x.shift(-i)
        valid &= x.shift(-i).notna()
    return acc.where(valid)


def _ic(x: pd.Series, y: pd.Series) -> float | None:
    m = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(m) < 100:
        return None
    v = float(m["x"].corr(m["y"]))
    return None if v != v else v


def _morlet_cwt(x: np.ndarray, scales: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return power |W|^2 shape (n_scales, n) and periods."""
    x = np.asarray(x, dtype=float)
    x = np.where(np.isfinite(x), x, 0.0)
    x = x - x.mean()
    n = len(x)
    # FFT convolution
    X = np.fft.fft(x)
    freqs = np.fft.fftfreq(n, d=1.0)
    power = np.zeros((len(scales), n), dtype=float)
    for i, s in enumerate(scales):
        # Morlet ψ̂(sω) ∝ exp(-(sω - ω0)^2/2) for ω>0
        omega = 2 * np.pi * freqs
        psihat = np.exp(-0.5 * (s * omega - W0) ** 2)
        psihat[freqs < 0] = 0.0
        # normalize
        psihat *= np.sqrt(2 * np.pi * s)
        W = np.fft.ifft(X * psihat)
        power[i] = np.abs(W) ** 2
    periods = scales * PERIOD_FACTOR
    return power, periods


def _cwt_summary(power: np.ndarray, periods: np.ndarray, *, tip_slice: slice | None = None) -> dict[str, Any]:
    if tip_slice is not None:
        pmean = power[:, tip_slice].mean(axis=1)
    else:
        pmean = power.mean(axis=1)
    total = float(pmean.sum())
    if total <= 0:
        return {"top": [], "ridge_period": None, "max_frac": 0.0}
    order = np.argsort(pmean)[::-1][:6]
    top = []
    for i in order:
        top.append(
            {
                "period_tdays": round(float(periods[i]), 2),
                "power_frac": round(float(pmean[i] / total), 5),
            }
        )
    # ridge: argmax scale at each time, then mode period
    ridge_idx = np.argmax(power, axis=0)
    # modal period among ridge
    vals, counts = np.unique(ridge_idx, return_counts=True)
    mode_i = int(vals[np.argmax(counts)])
    return {
        "top": top,
        "ridge_period_mode": round(float(periods[mode_i]), 2),
        "max_frac": top[0]["power_frac"] if top else 0.0,
    }


def _wavelet_ridge_signal(power: np.ndarray, periods: np.ndarray, x: np.ndarray) -> np.ndarray:
    """Proxy: at each t, take local bandpass around ridge period via Morlet projection magnitude signed by x."""
    # Use power-weighted period then reconstruct with cosine phase from analytic-ish: sign from x smoothed
    ridge_idx = np.argmax(power, axis=0)
    # amplitude ~ sqrt(power at ridge)
    amp = np.sqrt(np.maximum(power[ridge_idx, np.arange(len(x))], 0.0))
    # phase proxy: local sign of x after light smooth
    xx = pd.Series(x).fillna(0.0)
    sm = xx.rolling(5, min_periods=1).mean().to_numpy()
    sig = amp * np.sign(sm + 1e-15)
    return sig


def _band_power_signal(power: np.ndarray, periods: np.ndarray, lo: float, hi: float) -> np.ndarray:
    mask = (periods >= lo) & (periods <= hi)
    if not np.any(mask):
        return np.zeros(power.shape[1])
    return np.sqrt(np.maximum(power[mask].mean(axis=0), 0.0))


def _numerical_laplace(x: np.ndarray, sigmas: np.ndarray, omegas: np.ndarray) -> np.ndarray:
    """|X(σ+jω)| for unilateral sum; shape (n_sigma, n_omega)."""
    x = np.asarray(x, dtype=float)
    x = np.where(np.isfinite(x), x, 0.0)
    x = x - x.mean()
    n = len(x)
    t = np.arange(n, dtype=float)
    # X[s] = sum x[n] exp(-s n), s=σ+jω
    mag = np.zeros((len(sigmas), len(omegas)), dtype=float)
    for i, sig in enumerate(sigmas):
        # decay weight
        w = np.exp(-sig * t)
        xw = x * w
        # FFT-like over omega: for each omega, sum xw * exp(-jω t)
        # Use matrix for modest grids
        # exp(-j ω t) = cos - j sin
        for j, om in enumerate(omegas):
            re = np.sum(xw * np.cos(om * t))
            im = np.sum(xw * np.sin(om * t))
            mag[i, j] = float(np.hypot(re, im))
    return mag


def _laplace_peaks(mag: np.ndarray, sigmas: np.ndarray, omegas: np.ndarray, top_k: int = 5) -> list[dict[str, Any]]:
    flat = mag.ravel()
    if flat.size == 0 or float(flat.max()) <= 0:
        return []
    # top peaks with simple non-max suppression
    idxs = np.argsort(flat)[::-1]
    peaks = []
    taken = np.zeros_like(flat, dtype=bool)
    n_om = len(omegas)
    for idx in idxs:
        if taken[idx]:
            continue
        i, j = divmod(int(idx), n_om)
        om = float(omegas[j])
        if om <= 1e-9:
            continue
        period = 2 * np.pi / om
        if period < 5 or period > 400:
            continue
        peaks.append(
            {
                "sigma": round(float(sigmas[i]), 5),
                "omega": round(om, 5),
                "period_tdays": round(period, 2),
                "mag": round(float(mag[i, j]), 6),
                "mag_frac": round(float(mag[i, j] / flat.max()), 5),
            }
        )
        # suppress neighborhood
        for di in range(-1, 2):
            for dj in range(-2, 3):
                ii, jj = i + di, j + dj
                if 0 <= ii < len(sigmas) and 0 <= jj < n_om:
                    taken[ii * n_om + jj] = True
        if len(peaks) >= top_k:
            break
    return peaks


def _laplace_oscillator(n: int, period: float, sigma: float) -> np.ndarray:
    """Causal damped oscillator e^{σt} sin(ωt) as feature template (σ usually ≤0)."""
    t = np.arange(n, dtype=float)
    om = 2 * np.pi / period
    # use decaying envelope if sigma>0 in peak search meant Re(s); for causal stable use -abs(sigma)
    return np.exp(-abs(sigma) * t) * np.sin(om * t)


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)

    print("loading ...", flush=True)
    live = _load_nav(LIVE_NAV)
    comp = _load_nav(COMP_NAV)
    sat_nav = _load_nav(SAT_NAV)
    dates = sorted(set(live["date"]) & set(comp["date"]) & set(sat_nav["date"]))
    live = live[live["date"].isin(dates)].reset_index(drop=True)
    comp = comp[comp["date"].isin(dates)].reset_index(drop=True)
    sat_nav = sat_nav[sat_nav["date"].isin(dates)].reset_index(drop=True)

    rc = comp["nav"].pct_change().fillna(0.0)
    rs = sat_nav["nav"].pct_change().fillna(0.0)
    rel = (rc - rs).astype(float)
    trail63 = _trail(rel, 63)
    fwd = _fwd_sum(rel, FWD)

    asof = pd.Timestamp(live["date"].max())
    tip_mask = (live["date"] >= (asof - pd.Timedelta(days=365))).to_numpy()
    tip_slice = slice(int(np.argmax(tip_mask)), len(tip_mask)) if tip_mask.any() else slice(0, 0)

    # scales covering ~8..320 trading-day periods
    target_periods = np.unique(np.round(np.geomspace(8, 320, 48)).astype(int)).astype(float)
    scales = target_periods / PERIOD_FACTOR

    results: dict[str, Any] = {"wavelet": {}, "laplace": {}, "ics": []}

    for name, series in (
        ("daily_rel", rel.to_numpy()),
        ("trail_rel_63", trail63.fillna(0.0).to_numpy()),
    ):
        print(f"CWT {name} ...", flush=True)
        power, periods = _morlet_cwt(series, scales)
        np.save(OUT / f"cwt_power_{name}.npy", power)
        full = _cwt_summary(power, periods)
        tip = _cwt_summary(power, periods, tip_slice=tip_slice)
        results["wavelet"][name] = {"full": full, "tip": tip}

        # IC: ridge signal and band powers around FFT-interesting bands
        ridge = _wavelet_ridge_signal(power, periods, series)
        for label, sig in (
            ("ridge", ridge),
            ("band_85_128", _band_power_signal(power, periods, 70, 140)),
            ("band_200_280", _band_power_signal(power, periods, 200, 280)),
        ):
            # for band power (always ≥0), use signed by trail direction
            s = pd.Series(sig)
            if label.startswith("band"):
                s = s * np.sign(trail63.fillna(0.0).to_numpy() + 1e-15)
            ic = _ic(s.shift(1), fwd)
            results["ics"].append(
                {
                    "method": "wavelet",
                    "series": name,
                    "feature": label,
                    "lag1_ic": None if ic is None else round(ic, 4),
                    "ic_gate": bool(ic is not None and abs(ic) >= IC_ABS_MIN),
                }
            )
        print(json.dumps({"cwt": name, "full_top": full["top"][:3], "tip_top": tip["top"][:3]}, ensure_ascii=False), flush=True)

    # Laplace on trail_rel_63 (smoother) and daily_rel
    # σ grid: 0..0.05 (light decay), ω for periods 10..300
    sigmas = np.linspace(0.0, 0.04, 9)
    periods_lap = np.geomspace(10, 300, 40)
    omegas = 2 * np.pi / periods_lap

    for name, series in (
        ("daily_rel", rel.to_numpy()),
        ("trail_rel_63", trail63.fillna(0.0).to_numpy()),
    ):
        print(f"Laplace {name} ...", flush=True)
        # subsample for speed if long: use last 1500 days + full for trail
        x = series
        if len(x) > 1800 and name == "daily_rel":
            x = x[-1800:]
        mag = _numerical_laplace(x, sigmas, omegas)
        peaks = _laplace_peaks(mag, sigmas, omegas, top_k=6)
        results["laplace"][name] = {"peaks": peaks, "n": int(len(x))}
        np.save(OUT / f"laplace_mag_{name}.npy", mag)

        for pk in peaks[:3]:
            osc = _laplace_oscillator(len(series), pk["period_tdays"], pk["sigma"])
            # correlate oscillator with series via convolution residual: use osc as filter kernel lagged
            # feature = causal filter: rolling corr with osc template truncated
            kern = osc[: min(len(osc), int(pk["period_tdays"] * 2))]
            # matched filter via cumulative — simple: convolve series with flipped kern
            feat = np.convolve(series, kern[::-1], mode="full")[: len(series)]
            ic = _ic(pd.Series(feat).shift(1), fwd)
            results["ics"].append(
                {
                    "method": "laplace",
                    "series": name,
                    "feature": f"osc_p{pk['period_tdays']}_s{pk['sigma']}",
                    "period_tdays": pk["period_tdays"],
                    "sigma": pk["sigma"],
                    "lag1_ic": None if ic is None else round(ic, 4),
                    "ic_gate": bool(ic is not None and abs(ic) >= IC_ABS_MIN),
                }
            )
        print(json.dumps({"laplace": name, "peaks": peaks[:3]}, ensure_ascii=False), flush=True)

    gated = [r for r in results["ics"] if r.get("ic_gate")]
    # structure present?
    w_frac = max(
        results["wavelet"]["daily_rel"]["full"].get("max_frac") or 0,
        results["wavelet"]["trail_rel_63"]["full"].get("max_frac") or 0,
    )
    has_lap = any(results["laplace"][k]["peaks"] for k in results["laplace"])

    if gated and (w_frac >= 0.05 or has_lap):
        verdict = "WAVE_LAP_SIGNAL"
    elif gated or w_frac >= 0.05:
        verdict = "WAVE_LAP_WEAK"
    else:
        verdict = "WAVE_LAP_NOISE"

    reading = {
        "wavelet_daily_top": results["wavelet"]["daily_rel"]["full"]["top"][:3],
        "wavelet_trail_top": results["wavelet"]["trail_rel_63"]["full"]["top"][:3],
        "wavelet_tip_trail_top": results["wavelet"]["trail_rel_63"]["tip"]["top"][:3],
        "laplace_trail_peaks": results["laplace"]["trail_rel_63"]["peaks"][:3],
        "ic_gated": gated,
        "vs_fft_0k9j": "Expect overlap with 85/128/256td if wavelet ridges agree; Laplace poles add decay σ.",
        "practical": (
            "Use wavelet band 70–140td and/or Laplace damped oscillator as assist to 0k9i "
            "time-domain; do not replace r0050_63 / Crisis / SELL."
        ),
    }

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
        "results": results,
        "reading": reading,
        "register": "0k9k",
    }
    (OUT / "wave_lap_results.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")

    screen_md = "\n".join(
        [
            f"# {SCREEN_ID}",
            "",
            f"Date: 2026-09-28 · Generated `{generated}`",
            f"Status: **{verdict}** · Soft-Frozen **KEEP** · parents **KEEP** · live wire **false**",
            "",
            "Morlet CWT + numerical unilateral Laplace on tip-gap series · lag-1 IC vs fwd_rel_21.",
            "",
            "## Wavelet (global mean power)",
            "",
            "| series | top periods (tdays) | max_frac | tip top |",
            "|---|---|---:|---|",
            (
                f"| daily_rel | {[t['period_tdays'] for t in results['wavelet']['daily_rel']['full']['top'][:3]]} | "
                f"{results['wavelet']['daily_rel']['full']['max_frac']} | "
                f"{[t['period_tdays'] for t in results['wavelet']['daily_rel']['tip']['top'][:3]]} |"
            ),
            (
                f"| trail_rel_63 | {[t['period_tdays'] for t in results['wavelet']['trail_rel_63']['full']['top'][:3]]} | "
                f"{results['wavelet']['trail_rel_63']['full']['max_frac']} | "
                f"{[t['period_tdays'] for t in results['wavelet']['trail_rel_63']['tip']['top'][:3]]} |"
            ),
            "",
            "## Laplace peaks (trail_rel_63)",
            "",
            "| period | sigma | mag_frac |",
            "|---:|---:|---:|",
        ]
        + [
            f"| {p['period_tdays']} | {p['sigma']} | {p['mag_frac']} |"
            for p in results["laplace"]["trail_rel_63"]["peaks"][:5]
        ]
        + [
            "",
            "## Lag-1 IC features",
            "",
            "| method | series | feature | IC | gate |",
            "|---|---|---|---:|---|",
        ]
        + [
            f"| {r['method']} | {r['series']} | {r['feature']} | {r['lag1_ic']} | {r['ic_gate']} |"
            for r in results["ics"]
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
        "Parents: 0k9j FFT · 0k9i tip-gap · register **0k9k**",
        "",
        "## Verdict",
        "",
        f"**`{verdict}`**",
        "",
        "## Reading",
        "",
        f"- Wavelet daily top: `{json.dumps(reading['wavelet_daily_top'], ensure_ascii=False)}`",
        f"- Wavelet trail top: `{json.dumps(reading['wavelet_trail_top'], ensure_ascii=False)}`",
        f"- Wavelet tip-trail top: `{json.dumps(reading['wavelet_tip_trail_top'], ensure_ascii=False)}`",
        f"- Laplace trail peaks: `{json.dumps(reading['laplace_trail_peaks'], ensure_ascii=False)}`",
        f"- IC-gated: `{json.dumps(gated, ensure_ascii=False)}`",
        "",
        reading["practical"],
        "",
        "## Binding",
        "",
        "1. Soft-Frozen / Exact T+1 / COOL / SELL_a75 / live CONF α=0.10 KEEP",
        "2. COMPOSITE + SAT_RELAX observes **KEEP OPEN**",
        "3. Wavelet/Laplace = diagnosis/assist · not sole switch · not live",
        "4. Prefer 0k9i time-domain + optional 70–140td wavelet band / damped osc · no year-switch",
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
        "reading": reading,
        "register": "0k9k",
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

    print(json.dumps({"verdict": verdict, "n_ic_gated": len(gated), "reading": reading}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
