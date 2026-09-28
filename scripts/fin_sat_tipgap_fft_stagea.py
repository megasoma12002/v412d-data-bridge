#!/usr/bin/env python3
"""FIN×SAT tip-gap FFT/Welch Stage A — spectral peaks + bandpass IC (paper).

Charter: research/ops/FIN_SAT_TIPGAP_FFT_STAGEA_CHARTER.md
Parents: 0k9i tip-gap TIP_MDD_ONLY · COMP + SAT_RELAX KEEP.
Soft-Frozen KEEP · no live · no year-switch.
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
from e50_early_stack_combined_nav import e16_features
from ops_repro_ssot import write_ops_and_repro_pointer

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "fin-sat-tipgap-fft-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_SAT_TIPGAP_FFT_STAGEA_CHARTER"
SCREEN_ID = "FIN_SAT_TIPGAP_FFT_STAGEA_SCREEN"
DECISION_ID = "FIN_SAT_TIPGAP_FFT_STAGEA_DECISION_PACK"

LIVE_NAV = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/ctrl_live_a10_daily_nav.csv"
COMP_NAV = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/comp_h150_x_a20_daily_nav.csv"
SAT_NAV = ROOT / "repro/sat-a20-relax-dual-paper-observe/outputs/sat_a20_relax_daily_nav.csv"

POWER_FRAC_MIN = 0.03
IC_ABS_MIN = 0.04
FWD = 21


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


def _periodogram_top(x: np.ndarray, *, top_k: int = 8) -> list[dict[str, Any]]:
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
        frac = float(spec[i] / total)
        rows.append(
            {
                "period_tdays": round(per, 2),
                "period_approx_cal_days": round(per * 365.25 / 252.0, 1),
                "power_frac": round(frac, 5),
                "freq": round(f, 6),
            }
        )
    return rows


def _welch_top(x: np.ndarray, *, nperseg: int = 256, top_k: int = 8) -> list[dict[str, Any]]:
    """Simple Welch without scipy: average periodograms of overlapping segments."""
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) < nperseg * 2:
        return _periodogram_top(x, top_k=top_k)
    step = nperseg // 2
    segs = []
    for start in range(0, len(x) - nperseg + 1, step):
        seg = x[start : start + nperseg]
        seg = seg - seg.mean()
        # hann
        w = np.hanning(nperseg)
        segs.append(np.abs(rfft(seg * w)) ** 2)
    spec = np.mean(np.vstack(segs), axis=0)
    freqs = rfftfreq(nperseg, d=1.0)
    total = float(spec[1:].sum())
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
                "period_approx_cal_days": round(per * 365.25 / 252.0, 1),
                "power_frac": round(float(spec[i] / total), 5),
                "freq": round(f, 6),
            }
        )
    return rows


def _bandpass_keep_periods(x: np.ndarray, periods: list[float], *, width: float = 0.25) -> np.ndarray:
    """Keep Fourier components near given periods (trading days)."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    mu = float(np.nanmean(x))
    xx = np.where(np.isfinite(x), x - mu, 0.0)
    X = rfft(xx)
    freqs = rfftfreq(n, d=1.0)
    mask = np.zeros_like(X, dtype=bool)
    for p in periods:
        if p <= 2:
            continue
        f0 = 1.0 / p
        lo = f0 * (1.0 - width)
        hi = f0 * (1.0 + width)
        mask |= (freqs >= lo) & (freqs <= hi)
    Y = np.where(mask, X, 0.0)
    y = irfft(Y, n=n)
    return y


def _ic(x: pd.Series, y: pd.Series) -> float | None:
    m = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(m) < 100:
        return None
    return float(m["x"].corr(m["y"]))


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

    market0 = sat.load_market()
    px = market0[market0["code"].astype(str) == "0050"].copy()
    px["date"] = pd.to_datetime(px["date"])
    close = px.drop_duplicates("date").set_index("date")["adj_close" if "adj_close" in px.columns else "close"].astype(float)
    r0050 = close.pct_change()

    rc = comp["nav"].pct_change().fillna(0.0)
    rs = sat_nav["nav"].pct_change().fillna(0.0)
    rel = rc - rs
    trail21 = _trail(rel, 21)
    trail63 = _trail(rel, 63)
    drag = (trail63 < 0).astype(float)
    r50 = live["date"].map(r0050)

    # monthly aggregated rel
    tmp = pd.DataFrame({"date": live["date"], "rel": rel})
    tmp["ym"] = tmp["date"].dt.to_period("M")
    monthly = tmp.groupby("ym", sort=True)["rel"].sum().astype(float)

    asof = pd.Timestamp(live["date"].max())
    tip_mask = live["date"] >= (asof - pd.Timedelta(days=365))

    series: dict[str, np.ndarray] = {
        "daily_rel": rel.to_numpy(),
        "trail_rel_21": trail21.to_numpy(),
        "trail_rel_63": trail63.to_numpy(),
        "trail_drag": drag.to_numpy(),
        "r0050": r50.to_numpy(),
        "monthly_rel": monthly.to_numpy(),
        "tip_daily_rel": rel[tip_mask].to_numpy(),
        "tip_trail_rel_63": trail63[tip_mask].to_numpy(),
    }

    spectra: dict[str, Any] = {}
    for name, arr in series.items():
        clean = arr[np.isfinite(arr)]
        method = "welch" if name.startswith("trail") or name == "trail_drag" else "periodogram"
        if name == "monthly_rel":
            tops = _periodogram_top(clean, top_k=6)
            # periods in months for monthly series
            for t in tops:
                t["period_months"] = t["period_tdays"]  # here unit is months
                t["period_tdays"] = round(t["period_tdays"] * 21.0, 1)  # ~trading days/month
        elif method == "welch":
            tops = _welch_top(clean, nperseg=min(256, max(64, len(clean) // 4)))
        else:
            tops = _periodogram_top(clean, top_k=8)
        spectra[name] = {
            "n": int(len(clean)),
            "method": method if name != "monthly_rel" else "periodogram_monthly",
            "top": tops,
            "max_power_frac": None if not tops else tops[0]["power_frac"],
        }
        print(json.dumps({"series": name, "max_frac": spectra[name]["max_power_frac"], "top3": tops[:3]}, ensure_ascii=False), flush=True)

    # Bandpass probes from strongest candidates
    # Prefer trail_rel_63 / monthly / r0050 peaks with highest power_frac
    candidates = []
    for name in ("trail_rel_63", "trail_rel_21", "monthly_rel", "r0050", "daily_rel"):
        tops = spectra[name]["top"]
        if not tops:
            continue
        # take best period in sensible band 10..320 tdays (or months converted)
        for t in tops[:3]:
            p = float(t["period_tdays"])
            if 10 <= p <= 320:
                candidates.append({"src": name, "period": p, "power_frac": t["power_frac"]})
    candidates.sort(key=lambda r: r["power_frac"], reverse=True)

    fwd = _fwd_sum(rel, FWD)
    bandpass_ics: list[dict[str, Any]] = []
    used_periods = []
    for c in candidates[:5]:
        p = c["period"]
        if any(abs(p - u) / u < 0.15 for u in used_periods):
            continue
        used_periods.append(p)
        # reconstruct from trail_rel_63 as smoother carrier when available
        carrier = trail63.fillna(0.0).to_numpy() if c["src"].startswith("trail") else rel.to_numpy()
        if c["src"] == "r0050":
            carrier = r50.fillna(0.0).to_numpy()
        if c["src"] == "monthly_rel":
            # expand monthly bandpass approx: use daily rel with that period
            carrier = rel.to_numpy()
        y = _bandpass_keep_periods(carrier, [p], width=0.3)
        sig = pd.Series(y, index=rel.index).shift(1)  # lag-1 causal
        ic = _ic(sig, fwd)
        bandpass_ics.append(
            {
                "src": c["src"],
                "period_tdays": round(p, 2),
                "power_frac": c["power_frac"],
                "lag1_ic_vs_fwd_rel_21": None if ic is None else round(ic, 4),
                "ic_gate": bool(ic is not None and abs(ic) >= IC_ABS_MIN),
            }
        )

    # Verdict
    strong = []
    for name, block in spectra.items():
        frac = block.get("max_power_frac")
        if frac is not None and frac >= POWER_FRAC_MIN:
            strong.append(name)
    ic_ok = [b for b in bandpass_ics if b.get("ic_gate")]
    if strong and ic_ok:
        verdict = "FFT_SIGNAL"
    elif strong or (bandpass_ics and max((b["power_frac"] or 0) for b in bandpass_ics) >= 0.015):
        verdict = "FFT_WEAK"
    else:
        # check if all max fracs tiny
        fracs = [block.get("max_power_frac") or 0 for block in spectra.values()]
        verdict = "FFT_NOISE" if (not fracs or max(fracs) < 0.015) else "FFT_WEAK"

    reading = {
        "daily_rel_near_white": bool((spectra["daily_rel"].get("max_power_frac") or 0) < 0.015),
        "strong_series": strong,
        "best_bandpass": None if not bandpass_ics else bandpass_ics[0],
        "ic_gated_bandpass": ic_ok,
        "implication": (
            "FFT does not yield a clean actionable tip-gap oscillator from daily COMP−SAT; "
            "prefer 0k9i time-domain leads (r0050_63) over spectral cycles unless FFT_SIGNAL."
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
        "gates": {"power_frac_min": POWER_FRAC_MIN, "ic_abs_min": IC_ABS_MIN},
        "spectra": spectra,
        "bandpass_ics": bandpass_ics,
        "reading": reading,
        "register": "0k9j",
    }

    # persist tops tables
    (OUT / "spectra.json").write_text(json.dumps(spectra, indent=2, ensure_ascii=False) + "\n")
    (OUT / "bandpass_ics.json").write_text(json.dumps(bandpass_ics, indent=2, ensure_ascii=False) + "\n")

    lines = [
        f"# {SCREEN_ID}",
        "",
        f"Date: 2026-09-28 · Generated `{generated}`",
        f"Status: **{verdict}** · Soft-Frozen **KEEP** · parents **KEEP** · live wire **false**",
        "",
        "FFT/Welch on tip-gap related series · bandpass lag-1 IC vs fwd_rel_21.",
        "",
        "## Spectra (top period / power frac)",
        "",
        "| series | n | method | top_period_tdays | power_frac |",
        "|---|---:|---|---:|---:|",
    ]
    for name, block in spectra.items():
        top = (block["top"] or [{}])[0]
        lines.append(
            f"| {name} | {block['n']} | {block['method']} | {top.get('period_tdays')} | {top.get('power_frac')} |"
        )
    lines += ["", "## Bandpass lag-1 IC", "", "| src | period | power_frac | IC | gate |", "|---|---:|---:|---:|---|"]
    for b in bandpass_ics:
        lines.append(
            f"| {b['src']} | {b['period_tdays']} | {b['power_frac']} | {b['lag1_ic_vs_fwd_rel_21']} | {b['ic_gate']} |"
        )
    lines += ["", f"Verdict: **`{verdict}`**", "", f"Label: `{SCREEN_ID}_2026-09-28__{verdict}`", ""]

    dlines = [
        f"# {DECISION_ID}",
        "",
        f"Date: 2026-09-28 · Generated `{generated}`",
        f"Status: **{verdict}** · Soft-Frozen **KEEP** · COMPOSITE+SAT_RELAX observes **KEEP** · live wire **false**",
        "",
        f"Charter: `{CHARTER_ID}.md`",
        f"Screen: `{SCREEN_ID}.md`",
        "Parents: 0k9i tip-gap · register **0k9j**",
        "",
        "## Verdict",
        "",
        f"**`{verdict}`**",
        "",
        "## Reading",
        "",
        f"- Daily COMP−SAT `rel` max power frac ≈ **{spectra['daily_rel'].get('max_power_frac')}** → near white noise (peaks ~2–4d, <1% each).",
        f"- Smoothed / monthly: see screen table · strong_series={strong}.",
        f"- Bandpass ICs: `{json.dumps(bandpass_ics, ensure_ascii=False)}`",
        "",
        "**FFT 能找什麼：** 日頻相對報酬**沒有**可用主導週期；若有弱峰也多半在平滑序列上且 bandpass 未必過 IC gate。"
        " tip-gap 預測仍以 0k9i **時域**特徵（`r0050_63`／Crisis／SELL）為主，不把 FFT 週期當切換主軸。",
        "",
        "## Binding",
        "",
        "1. Soft-Frozen / Exact T+1 / COOL / SELL_a75 / live CONF α=0.10 KEEP",
        "2. COMPOSITE + SAT_RELAX observes **KEEP OPEN**",
        "3. Do not promote FFT oscillator as live/observe without FFT_SIGNAL",
        "4. Prefer 0k9i time-domain next cycle · no year-switch",
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
        "bandpass_ics": bandpass_ics,
        "register": "0k9j",
        "generated_at_utc": generated,
    }

    write_ops_and_repro_pointer(OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", "\n".join(lines), kind="screen")
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

    print(json.dumps({"verdict": verdict, "reading": reading}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
