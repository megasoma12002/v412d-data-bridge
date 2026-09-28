#!/usr/bin/env python3
"""FIN×SAT FFT-phase Exact T+1 lag Stage A (paper).

Charter: research/ops/FIN_SAT_FFT_PHASE_LAG_STAGEA_CHARTER.md
Parents: 0k9o TIP_LAG_BLOCK · 0k9j FFT_SIGNAL · Soft-Frozen KEEP.
Causal STFT phase/recon on trail_rel bands — can it lead SAT_LEAD enter?
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
from ops_repro_ssot import write_ops_and_repro_pointer
from research_metric_helpers import mdd_delta_pp

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "fin-sat-fft-phase-lag-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_SAT_FFT_PHASE_LAG_STAGEA_CHARTER"
SCREEN_ID = "FIN_SAT_FFT_PHASE_LAG_STAGEA_SCREEN"
DECISION_ID = "FIN_SAT_FFT_PHASE_LAG_STAGEA_DECISION_PACK"
BASE_ID = "CTRL_LIVE_A10"

LIVE_NAV = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/ctrl_live_a10_daily_nav.csv"
COMP_NAV = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/comp_h150_x_a20_daily_nav.csv"
SAT_NAV = ROOT / "repro/sat-a20-relax-dual-paper-observe/outputs/sat_a20_relax_daily_nav.csv"

THETA = 0.01
HALF_THETA = 0.005
CAGR_FLOOR_PP = 0.10
HELD_MDD_MIN_PP = -0.25
HELD_ABS_MDD_MAX = 0.15
TIP_MDD_MIN_PP = 0.0
TIP_CAGR_MIN_PP = 0.0
VS_SAT_HELD_EXTRA_PP = 0.05

# 0k9j periods ±30%
PERIODS = (85.0, 128.0, 256.0)
WINS = (64, 128, 256)
LEAD_KS = (1, 2, 3, 5)


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


def _switch_nav(comp: pd.DataFrame, sat_nav: pd.DataFrame, use_sat: np.ndarray) -> tuple[pd.DataFrame, dict[str, Any]]:
    m = (
        comp.rename(columns={"nav": "nav_c"})
        .merge(sat_nav.rename(columns={"nav": "nav_s"}), on="date")
        .sort_values("date")
        .reset_index(drop=True)
    )
    u = np.asarray(use_sat, dtype=bool)
    rc = m["nav_c"].pct_change().fillna(0.0)
    rs = m["nav_s"].pct_change().fillna(0.0)
    r = np.where(u, rs.to_numpy(), rc.to_numpy())
    nav = (1.0 + r).cumprod() * float(m["nav_c"].iloc[0])
    flips = int(np.sum(u[1:] != u[:-1])) if len(u) > 1 else 0
    return pd.DataFrame({"date": m["date"].to_numpy(), "nav": nav}), {
        "pct_days_sat": round(float(np.mean(u)) * 100, 2),
        "n_flips": flips,
    }


def _eval_row(
    base_w: dict[str, Any],
    chal_w: dict[str, Any],
    tip: dict[str, Any],
    *,
    fam: str,
    sat_held_cagr: float | None,
) -> dict[str, Any]:
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
    shaped = bool(tip_clean and economic and vs_sat_ok)
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
            "shaped": shaped,
        },
        "hit": bool(fam == "switch" and shaped),
        "ub_shaped": bool(fam == "ub" and shaped),
    }


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
        # quadrature via spectral Hilbert on kept bins
        Yq = np.zeros_like(Y)
        Yq[mask] = -1j * np.sign(freqs[mask]) * Y[mask]
        q = irfft(Yq, n=win)
        recon[i] = float(y[-1])
        amp[i] = float(np.hypot(y[-1], q[-1]))
        phase[i] = float(np.arctan2(q[-1], y[-1]))

    # unwrap for dphase
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


def _rank_ic(x: pd.Series, y: pd.Series) -> float | None:
    a = pd.concat([x, y], axis=1).dropna()
    if len(a) < 80:
        return None
    return float(a.iloc[:, 0].rank().corr(a.iloc[:, 1].rank()))


def _lead_table(feat: pd.DataFrame, cols: list[str]) -> list[dict[str, Any]]:
    y = feat["enter"].astype(float)
    rows: list[dict[str, Any]] = []
    for col in cols:
        for k in LEAD_KS:
            ic = _rank_ic(feat[col].shift(k), y)
            rows.append(
                {
                    "feat": col,
                    "k": k,
                    "ic": None if ic is None else round(ic, 4),
                    "abs_ic": None if ic is None else round(abs(ic), 4),
                }
            )
    rows.sort(key=lambda r: (r["abs_ic"] is None, -(r["abs_ic"] or -1), r["k"]))
    return rows


def _verdict(diag: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    sw = [r for r in rows if r["fam"] == "switch"]
    if any(r["eval"]["hit"] for r in sw):
        return "FFT_LAG_HIT"
    best_ic = diag.get("best_fft_abs_ic") or 0.0
    trail_ic = diag.get("trail_abs_ic_k1") or 0.0
    ub_ok = any(r["eval"]["ub_shaped"] for r in rows if r["fam"] == "ub")
    if best_ic >= 0.08 and best_ic + 0.02 >= trail_ic:
        if any(r["eval"]["gates"]["tip_clean"] for r in sw):
            return "FFT_LAG_SIGNAL"
        return "FFT_LAG_SIGNAL" if best_ic >= 0.12 else "FFT_LAG_NO_EDGE"
    if ub_ok and all(not r["eval"]["gates"]["tip_cagr"] for r in sw):
        return "TIP_LAG_BLOCK"
    if any(
        r["eval"]["gates"]["economic"] and r["eval"]["gates"]["tip_mdd"] and not r["eval"]["gates"]["tip_cagr"]
        for r in sw
    ):
        return "TIP_MDD_ONLY"
    return "FFT_LAG_NO_EDGE"


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

    panel = (
        live.rename(columns={"nav": "nav_l"})
        .merge(comp.rename(columns={"nav": "nav_c"}), on="date")
        .merge(sat_nav.rename(columns={"nav": "nav_s"}), on="date")
        .sort_values("date")
        .reset_index(drop=True)
    )
    panel["rel"] = panel["nav_c"].pct_change().fillna(0.0) - panel["nav_s"].pct_change().fillna(0.0)
    panel["trail_rel_63"] = _trail(panel["rel"], 63)
    sat_lead = (panel["trail_rel_63"] <= -THETA).fillna(False).astype(bool)
    prev = sat_lead.shift(1).fillna(False).astype(bool)
    panel["sat_lead"] = sat_lead
    panel["enter"] = sat_lead.to_numpy() & (~prev.to_numpy())
    panel["trail_rel_63_l1"] = panel["trail_rel_63"].shift(1)

    print("causal STFT features ...", flush=True)
    x = panel["trail_rel_63"].fillna(0.0).to_numpy()
    # primary win=128 (balanced); also compute 64/256 for IC table
    all_ic_rows: list[dict[str, Any]] = []
    primary = None
    for win in WINS:
        feats = _causal_stft_features(x, win=win, periods=PERIODS)
        prefix = f"w{win}"
        for name, arr in feats.items():
            panel[f"{prefix}_{name}"] = arr
            panel[f"{prefix}_{name}_l1"] = pd.Series(arr).shift(1)
        sub = _lead_table(
            panel,
            [f"{prefix}_phase", f"{prefix}_dphase", f"{prefix}_recon", f"{prefix}_amp"],
        )
        for r in sub:
            r["win"] = win
        all_ic_rows.extend(sub)
        if win == 128:
            primary = feats

    trail_ics = _lead_table(panel, ["trail_rel_63"])
    all_ic_rows.sort(key=lambda r: (r["abs_ic"] is None, -(r["abs_ic"] or -1)))
    best_fft = next((r for r in all_ic_rows if r["feat"] != "trail_rel_63"), None)
    trail_k1 = next((r for r in trail_ics if r["k"] == 1), None)

    diag = {
        "n_enter": int(panel["enter"].sum()),
        "periods": list(PERIODS),
        "wins": list(WINS),
        "top_fft_ic": all_ic_rows[:12],
        "trail_lead_ic": trail_ics,
        "best_fft_abs_ic": None if not best_fft else best_fft.get("abs_ic"),
        "best_fft": best_fft,
        "trail_abs_ic_k1": None if not trail_k1 else trail_k1.get("abs_ic"),
        "note": "Causal STFT end-point phase/recon on trail_rel_63 bands from 0k9j",
    }
    (OUT / "fft_phase_diag.json").write_text(json.dumps(diag, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    panel.to_csv(OUT / "fft_phase_panel.csv", index=False)
    print(json.dumps({"best_fft": best_fft, "trail_k1": trail_k1}, ensure_ascii=False), flush=True)

    assert primary is not None
    # probe masks from win=128 lag-1
    phase_l1 = panel["w128_phase_l1"]
    dphase_l1 = panel["w128_dphase_l1"]
    recon_l1 = panel["w128_recon_l1"]
    amp_l1 = panel["w128_amp_l1"]
    trail_l1 = panel["trail_rel_63_l1"]
    amp_up = amp_l1 > amp_l1.shift(5)

    # dangerous quadrant: phase in (π/2, π] U [-π, -π/2) ≈ cos(phase)<0 already in recon
    phase_quad = (phase_l1 > 0.5) | (phase_l1 < -0.5)  # |phase| large
    r_phase = (phase_quad.fillna(False) & (recon_l1 < 0).fillna(False)).to_numpy()
    dph_hi = dphase_l1.abs() >= float(dphase_l1.abs().median(skipna=True) or 0)
    r_dphase = (dph_hi.fillna(False) & (trail_l1 < 0).fillna(False)).to_numpy()
    r_recon = (recon_l1 <= -HALF_THETA).fillna(False).to_numpy()
    r_amp = (amp_up.fillna(False) & (recon_l1 < 0).fillna(False)).to_numpy()
    sat_l1 = panel["sat_lead"].shift(1).fillna(False).astype(bool).to_numpy()
    ub_m1 = (
        panel["sat_lead"].to_numpy()
        | pd.Series(panel["enter"]).shift(-1).fillna(False).astype(bool).to_numpy()
    )

    books: list[dict[str, Any]] = [
        {"id": BASE_ID, "fam": "ctrl"},
        {"id": "REF_SAT_RELAX", "fam": "ref", "use": "sat"},
        {"id": "REF_COMP_H150_A20", "fam": "ref", "use": "comp"},
        {"id": "UB_ENTER_M1", "fam": "ub", "mask": ub_m1},
        {"id": "R_SAT_LEAD_L1", "fam": "switch", "mask": sat_l1},
        {"id": "R_PHASE_QUAD_L1", "fam": "switch", "mask": r_phase},
        {"id": "R_DPHASE_HI_L1", "fam": "switch", "mask": r_dphase},
        {"id": "R_RECON_HALF_L1", "fam": "switch", "mask": r_recon},
        {"id": "R_AMP_TREND_L1", "fam": "switch", "mask": r_amp},
    ]

    base_w = _pack(live)
    sat_held = cagr_lift_pp(
        (base_w.get("heldout_2019_plus") or {}).get("cagr"),
        (_pack(sat_nav).get("heldout_2019_plus") or {}).get("cagr"),
    )

    rows: list[dict[str, Any]] = []
    for spec in books:
        bid = spec["id"]
        fam = spec["fam"]
        print(f"{bid} ...", flush=True)
        if fam == "ctrl":
            nav = live.copy()
            meta = {"pct_days_sat": 0.0, "n_flips": 0, "rule": "ctrl"}
        elif fam == "ref":
            nav = sat_nav.copy() if spec["use"] == "sat" else comp.copy()
            meta = {"pct_days_sat": 100.0 if spec["use"] == "sat" else 0.0, "n_flips": 0, "rule": spec["use"]}
        else:
            nav, meta = _switch_nav(comp, sat_nav, spec["mask"])
            meta["rule"] = bid
        nav.to_csv(OUT / f"nav_{bid}.csv", index=False)
        tip = (
            {
                "ytd": {"mdd_improve_pp": 0.0, "cagr_lift_pp": 0.0, "gate": "PASS"},
                "trailing_1y": {"mdd_improve_pp": 0.0, "cagr_lift_pp": 0.0, "gate": "PASS"},
            }
            if bid == BASE_ID
            else _tip(live, nav)
        )
        ev = _eval_row(base_w, _pack(nav), tip, fam=fam, sat_held_cagr=sat_held)
        rows.append({"id": bid, "fam": fam, "meta": meta, "eval": ev, "tip": tip})
        print(json.dumps({"book": bid, "meta": meta, "eval": ev}, ensure_ascii=False), flush=True)

    verdict = _verdict(diag, rows)
    generated = _utc()
    hits = [r for r in rows if r["eval"]["hit"]]
    ub_shaped = [r for r in rows if r["eval"]["ub_shaped"]]
    ub_shaped.sort(key=lambda r: float(r["eval"]["held_cagr_lift_pp"] or -9), reverse=True)

    payload = {
        "label": f"{SCREEN_ID}_{generated.replace(':', '').replace('-', '')}",
        "generated_at_utc": generated,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "status": "STAGE_A_SCREEN_DONE",
        "verdict": verdict,
        "live_wire": False,
        "soft_frozen_keep": True,
        "parent_observes_keep": True,
        "diagnosis": diag,
        "books": [
            {"id": r["id"], "fam": r["fam"], "meta": r["meta"], "eval": r["eval"], "tip": r["tip"]} for r in rows
        ],
        "register": "0k9p",
    }

    screen_md = "\n".join(
        [
            f"# {SCREEN_ID}",
            "",
            f"Date: 2026-09-28 · Generated `{generated}`",
            f"Status: **{verdict}** · Soft-Frozen **KEEP** · parents **KEEP** · live wire **false**",
            "",
            "## FFT-phase lead vs enter",
            "",
            f"- best_fft=`{diag.get('best_fft')}`",
            f"- trail_abs_ic_k1=`{diag.get('trail_abs_ic_k1')}`",
            "",
            "| feat | win | k | IC |",
            "|---|---:|---:|---:|",
        ]
        + [f"| {r['feat']} | {r.get('win','')} | {r['k']} | {r['ic']} |" for r in all_ic_rows[:10]]
        + [
            "",
            "## Books",
            "",
            "| ID | fam | %SAT | heldCAGR↑ | tipCAGR↑ | tipClean | mark |",
            "|---|---|---:|---:|---:|---|---|",
        ]
        + [
            "| {id} | {fam} | {ps} | {cagr} | {tc} | {clean} | {mark} |".format(
                id=r["id"],
                fam=r["fam"],
                ps=r["meta"]["pct_days_sat"],
                cagr=r["eval"]["held_cagr_lift_pp"],
                tc=r["eval"]["tip_ytd_cagr_pp"],
                clean=r["eval"]["gates"]["tip_clean"],
                mark=("HIT" if r["eval"]["hit"] else ("UB" if r["eval"]["ub_shaped"] else "·")),
            )
            for r in rows
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
        "Parents: 0k9o/0k9j/0k9n · register **0k9p**",
        "",
        "## Verdict",
        "",
        f"**`{verdict}`**",
        "",
        "## Reading",
        "",
        f"- best FFT lead IC: {json.dumps(diag.get('best_fft'), ensure_ascii=False)}",
        f"- trail_rel lag-1 |IC| vs enter: `{diag.get('trail_abs_ic_k1')}`",
        f"- enters={diag.get('n_enter')}",
        "",
    ]
    if ub_shaped:
        dlines.append("UB shaped:")
        for r in ub_shaped:
            dlines.append(
                f"- `{r['id']}` held↑ {r['eval']['held_cagr_lift_pp']} tipY↑ {r['eval']['tip_ytd_cagr_pp']}"
            )
        dlines.append("")
    if hits:
        dlines += [f"Champion: `{hits[0]['id']}`", ""]
    else:
        dlines += ["No causal FFT_LAG_HIT.", ""]

    dlines += ["## Books", ""]
    for r in rows:
        if r["fam"] == "ctrl":
            continue
        g = r["eval"]["gates"]
        dlines.append(
            f"- `{r['id']}` ({r['fam']}) · %SAT={r['meta']['pct_days_sat']} · "
            f"held↑ {r['eval']['held_cagr_lift_pp']} tipY↑ {r['eval']['tip_ytd_cagr_pp']} · "
            f"tipClean={g['tip_clean']}"
        )
    dlines += [
        "",
        "## Binding",
        "",
        "1. Soft-Frozen / Exact T+1 / COOL / SELL_a75 / live CONF α=0.10 KEEP",
        "2. COMPOSITE + SAT_RELAX observes **KEEP OPEN**",
        "3. Causal FFT window cannot invent lead beyond carrier; do not expand spectrum grid after peek",
        "4. UB diagnosis only · no observe · no live",
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
        "best_fft_abs_ic": diag.get("best_fft_abs_ic"),
        "trail_abs_ic_k1": diag.get("trail_abs_ic_k1"),
        "best_hit": None if not hits else hits[0]["id"],
        "best_ub_shaped": None if not ub_shaped else ub_shaped[0]["id"],
        "charter": f"research/ops/{CHARTER_ID}.md",
        "screen": f"research/ops/{SCREEN_ID}.md",
        "register": "0k9p",
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

    print(json.dumps({"verdict": verdict, "best_fft_abs_ic": diag.get("best_fft_abs_ic")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
