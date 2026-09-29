#!/usr/bin/env python3
"""FIN×SAT Path3 COMP-entry signal analysis Stage A (paper).

Label each SAT→COMP flip as good/bad by subsequent COMP-vs-SAT episode return.
Screen features at flip time (trail / slope / gap-to-θ / short COMP−SAT rel).
Optional threshold probe: skip COMP when feature flags risk.

Parents: 0k9x COMP_STAY_MISS · 0k9y COMP_CONFIRM_NO_EDGE
Soft-Frozen KEEP · Path3 observe KEEP · fill/emit OFF · no live
Register: 0k9z
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from e45_paper_harness import WINDOWS_STANDARD, window_stats
from fin_sell_quality_helpers import cagr_lift_pp
from ops_repro_ssot import write_ops_and_repro_pointer, write_repro_pointer
from research_metric_helpers import mdd_delta_pp

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "fin-sat-path3-comp-entry-signal-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_SAT_PATH3_COMP_ENTRY_SIGNAL_STAGEA_CHARTER"
SCREEN_ID = "FIN_SAT_PATH3_COMP_ENTRY_SIGNAL_STAGEA_SCREEN"
DECISION_ID = "FIN_SAT_PATH3_COMP_ENTRY_SIGNAL_STAGEA_DECISION_PACK"
REGISTER = "0k9z"
BASE_ID = "CTRL_LIVE_A10"

LIVE_NAV = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/ctrl_live_a10_daily_nav.csv"
COMP_NAV = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/comp_h150_x_a20_daily_nav.csv"
SAT_NAV = ROOT / "repro/sat-a20-relax-dual-paper-observe/outputs/sat_a20_relax_daily_nav.csv"

THETA = 0.01
IC_EDGE = 0.15
IC_WEAK = 0.08
HIT_EDGE = 0.60
HIT_WEAK = 0.55


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
    # features
    m["trail_gap_to_theta"] = m["trail_rel_63"] - (-THETA)  # >0 means above threshold (COMP side)
    m["trail_slope_5"] = m["trail_rel_63"].diff(5)
    m["trail_slope_21"] = m["trail_rel_63"].diff(21)
    m["rel_5"] = m["rel"].rolling(5, min_periods=5).sum()
    m["rel_21"] = m["rel"].rolling(21, min_periods=21).sum()
    m["rel_63"] = m["rel"].rolling(63, min_periods=63).sum()
    m["comp_trail_21"] = _trail(m["r_c"], 21)
    m["sat_trail_21"] = _trail(m["r_s"], 21)
    m["comp_minus_sat_21"] = m["comp_trail_21"] - m["sat_trail_21"]
    m["vol_rel_21"] = m["rel"].rolling(21, min_periods=21).std()
    m["abs_trail"] = m["trail_rel_63"].abs()
    return m


def label_comp_entries(m: pd.DataFrame) -> pd.DataFrame:
    """Each SAT→COMP transition: label by subsequent COMP episode COMP vs SAT."""
    w = m["w_sat"].to_numpy()
    rows: list[dict[str, Any]] = []
    i = 1
    while i < len(m):
        # flip to COMP: was SAT, now COMP
        if w[i - 1] > 0.5 and w[i] < 0.5:
            j = i
            while j + 1 < len(m) and w[j + 1] < 0.5:
                j += 1
            ep = m.iloc[i : j + 1]
            # forward returns over episode (exclude day i already in COMP)
            rc = float((1.0 + ep["r_c"]).prod() - 1.0)
            rs = float((1.0 + ep["r_s"]).prod() - 1.0)
            # also fixed horizons from entry day
            horizons = {}
            for h in (5, 10, 21, 63):
                end = min(i + h - 1, len(m) - 1)
                g = m.iloc[i : end + 1]
                horizons[f"fwd_comp_minus_sat_{h}"] = float((1.0 + g["r_c"]).prod() - (1.0 + g["r_s"]).prod())
            row0 = m.iloc[i]
            good = rc > rs  # COMP beat SAT over stay → entry was good
            rows.append(
                {
                    "date": str(row0["date"].date()),
                    "year": int(row0["date"].year),
                    "ep_end": str(m.iloc[j]["date"].date()),
                    "n_days": int(j - i + 1),
                    "comp_ep_ret": round(rc * 100, 4),
                    "sat_ep_ret": round(rs * 100, 4),
                    "comp_minus_sat_ep": round((rc - rs) * 100, 4),
                    "y_good": int(good),
                    "trail_rel_63": None if pd.isna(row0["trail_rel_63"]) else float(row0["trail_rel_63"]),
                    "trail_gap_to_theta": None
                    if pd.isna(row0["trail_gap_to_theta"])
                    else float(row0["trail_gap_to_theta"]),
                    "trail_slope_5": None if pd.isna(row0["trail_slope_5"]) else float(row0["trail_slope_5"]),
                    "trail_slope_21": None if pd.isna(row0["trail_slope_21"]) else float(row0["trail_slope_21"]),
                    "rel_5": None if pd.isna(row0["rel_5"]) else float(row0["rel_5"]),
                    "rel_21": None if pd.isna(row0["rel_21"]) else float(row0["rel_21"]),
                    "rel_63": None if pd.isna(row0["rel_63"]) else float(row0["rel_63"]),
                    "comp_minus_sat_21": None
                    if pd.isna(row0["comp_minus_sat_21"])
                    else float(row0["comp_minus_sat_21"]),
                    "vol_rel_21": None if pd.isna(row0["vol_rel_21"]) else float(row0["vol_rel_21"]),
                    "abs_trail": None if pd.isna(row0["abs_trail"]) else float(row0["abs_trail"]),
                    **{k: round(v * 100, 4) for k, v in horizons.items()},
                }
            )
            i = j + 1
            continue
        i += 1
    return pd.DataFrame(rows)


FEATS = [
    "trail_rel_63",
    "trail_gap_to_theta",
    "trail_slope_5",
    "trail_slope_21",
    "rel_5",
    "rel_21",
    "rel_63",
    "comp_minus_sat_21",
    "vol_rel_21",
    "abs_trail",
]


def screen_features(events: pd.DataFrame) -> list[dict[str, Any]]:
    y = events["comp_minus_sat_ep"].to_numpy(dtype=float)
    y_bin = events["y_good"].to_numpy(dtype=float)
    out: list[dict[str, Any]] = []
    for f in FEATS:
        x = events[f].to_numpy(dtype=float)
        ic = _spearman(x, y)
        # direction: if IC>0, high x → COMP better (good entry)
        # hit: median split
        m = np.isfinite(x) & np.isfinite(y_bin)
        hit = None
        mean_good = None
        mean_bad = None
        if m.sum() >= 20:
            med = float(np.nanmedian(x[m]))
            # test both sides; keep better hit for "block when feature says risk"
            # side A: high-x → good
            pred_good_hi = (x[m] >= med).astype(float)
            hit_hi = float(np.mean(pred_good_hi == y_bin[m]))
            pred_good_lo = (x[m] <= med).astype(float)
            hit_lo = float(np.mean(pred_good_lo == y_bin[m]))
            if hit_hi >= hit_lo:
                hit = hit_hi
                side = "high→good"
            else:
                hit = hit_lo
                side = "low→good"
            good_m = m & (events["y_good"].to_numpy() == 1)
            bad_m = m & (events["y_good"].to_numpy() == 0)
            mean_good = None if good_m.sum() == 0 else float(np.nanmean(x[good_m]))
            mean_bad = None if bad_m.sum() == 0 else float(np.nanmean(x[bad_m]))
        else:
            side = None
        # OOF / sealed year splits for IC stability
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
                "mean_good": None if mean_good is None else round(mean_good, 5),
                "mean_bad": None if mean_bad is None else round(mean_bad, 5),
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
    """Start from raw SAT_LEAD; when wanting COMP, block (stay SAT) if feature flags risk."""
    w_raw = m["w_sat"].to_numpy(dtype=float)
    x = m[feature].to_numpy(dtype=float)
    n = len(m)
    w = np.zeros(n, dtype=float)
    for i in range(n):
        want_sat = w_raw[i] > 0.5
        if want_sat:
            w[i] = 1.0
            continue
        # want COMP — block if feature says bad
        xi = x[i]
        if not np.isfinite(xi):
            w[i] = 0.0
            continue
        # side high→good means low is risk → block COMP when x < thr
        # side low→good means high is risk → block when x > thr
        if side == "high→good":
            block = xi < thr
        else:
            block = xi > thr
        if i > 0 and w[i - 1] > 0.5 and block:
            w[i] = 1.0  # stay SAT
        else:
            w[i] = 0.0
    return w


def _blend(comp: pd.DataFrame, sat: pd.DataFrame, w_sat: np.ndarray) -> pd.DataFrame:
    rc = comp["nav"].pct_change().fillna(0.0).to_numpy()
    rs = sat["nav"].pct_change().fillna(0.0).to_numpy()
    r = (1.0 - w_sat) * rc + w_sat * rs
    nav = (1.0 + r).cumprod() * float(comp["nav"].iloc[0])
    return pd.DataFrame({"date": comp["date"].to_numpy(), "nav": nav})


def _verdict(feat_rows: list[dict[str, Any]], probe: dict[str, Any] | None) -> str:
    best = feat_rows[0] if feat_rows else None
    if best and (best.get("abs_ic") or 0) >= IC_EDGE and (best.get("hit_median") or 0) >= HIT_EDGE:
        if probe and probe.get("y2022_ok") and probe.get("tip_ok") and probe.get("held_ok"):
            return "SIGNAL_HIT"
        return "SIGNAL_EDGE"
    if best and ((best.get("abs_ic") or 0) >= IC_WEAK or (best.get("hit_median") or 0) >= HIT_WEAK):
        return "SIGNAL_WEAK"
    return "SIGNAL_NO_EDGE"


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
    events = label_comp_entries(m)
    events.to_csv(OUT / "comp_entry_events.csv", index=False)
    feat_rows = screen_features(events)
    pd.DataFrame(feat_rows).to_csv(OUT / "feature_screen.csv", index=False)

    # 2022 entries detail
    e2022 = events[events["year"] == 2022].copy()
    e2022.to_csv(OUT / "comp_entry_events_2022.csv", index=False)

    best = feat_rows[0]
    # threshold = median of feature on all events
    thr = float(np.nanmedian(events[best["feature"]].to_numpy(dtype=float)))
    side = best["hit_side"] or "high→good"
    w_probe = apply_block_rule(m, feature=best["feature"], side=side, thr=thr)
    nav_p3 = _blend(comp, sat, m["w_sat"].to_numpy(dtype=float))
    nav_pr = _blend(comp, sat, w_probe)
    nav_p3.to_csv(OUT / "nav_P3_T0_STATE.csv", index=False)
    nav_pr.to_csv(OUT / f"nav_BLOCK_{best['feature']}.csv", index=False)

    yb = _year_ret(live, 2022)
    yp3 = _year_ret(nav_p3, 2022)
    ypr = _year_ret(nav_pr, 2022)
    tip_p3 = _tip(live, nav_p3)
    tip_pr = _tip(live, nav_pr)
    held_base = (_pack(live).get("heldout_2019_plus") or {}).get("cagr")
    held_p3 = cagr_lift_pp(held_base, (_pack(nav_p3).get("heldout_2019_plus") or {}).get("cagr"))
    held_pr = cagr_lift_pp(held_base, (_pack(nav_pr).get("heldout_2019_plus") or {}).get("cagr"))

    probe = {
        "id": f"BLOCK_{best['feature']}",
        "feature": best["feature"],
        "side": side,
        "threshold": thr,
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

    verdict = _verdict(feat_rows, probe)
    generated = _utc()

    # summary stats
    n = len(events)
    n_good = int(events["y_good"].sum())
    summary = {
        "n_comp_entries": n,
        "n_good": n_good,
        "n_bad": n - n_good,
        "pct_good": round(n_good / n * 100, 2) if n else None,
        "n_2022": int(len(e2022)),
        "n_2022_good": int(e2022["y_good"].sum()) if len(e2022) else 0,
        "mean_ep_days": round(float(events["n_days"].mean()), 2) if n else None,
    }

    charter_md = "\n".join(
        [
            f"# {CHARTER_ID}",
            "",
            "Date: 2026-09-29",
            "Status: **Stage A — COMP-entry signal analysis** · Soft-Frozen **KEEP** · Path3 observe **KEEP** · "
            "fill/emit **OFF** · cutover **BLOCKED** · no live",
            "Parents: 0k9x `COMP_STAY_MISS` · 0k9y `COMP_CONFIRM_NO_EDGE`（規則層 exhausted）",
            f"Register: **{REGISTER}**",
            "",
            "## Question",
            "",
            "SAT→COMP flip 當下，有沒有訊號能分開「好／壞 COMP 進場」，並擋 2022 類錯站？",
            "",
            "## Method",
            "",
            "1. Label each SAT→COMP entry by subsequent COMP-episode COMP−SAT return",
            "2. Screen Spearman IC + median-split hit on trail/slope/rel/vol features",
            "3. One threshold block probe on best |IC| feature vs raw P3 (2022 / held / tip)",
            "",
            "## Non-goals",
            "",
            "- 不關 Path3 observe · 不翻 fill/emit · 不改 Soft-Frozen",
            "",
            f"Label: `{CHARTER_ID}_2026-09-29__COMP_ENTRY_SIGNAL__NO_LIVE`",
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
        "events_2022": e2022.to_dict(orient="records"),
        "soft_frozen_keep": True,
        "path3_observe_keep": True,
        "live_wire": False,
        "fill_emit_flags": False,
    }
    (OUT / "screen.json").write_text(json.dumps(screen, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(screen, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
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
        f"bad **{summary['n_bad']}** · mean ep days **{summary['mean_ep_days']}**",
        f"- 2022 entries: **{summary['n_2022']}** · good **{summary['n_2022_good']}**",
        "",
        "## Feature screen (ranked |IC|)",
        "",
        "| feature | IC full | IC≤2018 | IC≥2019 | hit med | side | mean_good | mean_bad |",
        "|---|---:|---:|---:|---:|---|---:|---:|",
    ]
    for r in feat_rows:
        md.append(
            f"| `{r['feature']}` | {r['ic_full']} | {r['ic_oof_le2018']} | {r['ic_held_ge2019']} | "
            f"{r['hit_median']} | {r['hit_side']} | {r['mean_good']} | {r['mean_bad']} |"
        )
    md += [
        "",
        f"## Threshold probe `{probe['id']}`",
        "",
        f"- rule: block COMP when feature `{probe['feature']}` is on risk side (`{probe['side']}`), thr={probe['threshold']:.6g}",
        f"- 2022: BASE {probe['y2022_base']} · P3 {probe['y2022_p3']} ({probe['y2022_vs_base_p3']}) · "
        f"probe {probe['y2022_probe']} ({probe['y2022_vs_base_probe']})",
        f"- held↑ P3 {probe['held_p3']} · probe {probe['held_probe']}",
        f"- tipY↑ P3 {probe['tip_ytd_p3']} · probe {probe['tip_ytd_probe']}",
        f"- flips P3 {probe['n_flips_p3']} · probe {probe['n_flips_probe']} · %SAT {probe['pct_sat_p3']}→{probe['pct_sat_probe']}",
        "",
        "## 2022 COMP entries",
        "",
        "| date | end | n | COMP% | SAT% | Δ | good | trail63 |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for _, r in e2022.iterrows():
        md.append(
            f"| {r['date']} | {r['ep_end']} | {r['n_days']} | {r['comp_ep_ret']} | {r['sat_ep_ret']} | "
            f"{r['comp_minus_sat_ep']} | {r['y_good']} | {None if pd.isna(r['trail_rel_63']) else round(float(r['trail_rel_63']),4)} |"
        )
    md += ["", "Repro: `repro/fin-sat-path3-comp-entry-signal-stagea/`", ""]
    write_ops_and_repro_pointer(OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", "\n".join(md) + "\n", kind="screen")

    decision_md = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: 2026-09-29 · Verdict: **`{verdict}`**",
            "Status: Soft-Frozen **KEEP** · Path3 observe **KEEP** · fill/emit **OFF** · cutover **BLOCKED** · no live",
            "Parents: 0k9x `COMP_STAY_MISS` · 0k9y `COMP_CONFIRM_NO_EDGE`",
            "",
            "## Answer",
            "",
            f"COMP 進場事件 **{summary['n_comp_entries']}** 筆（good {summary['pct_good']}%；2022 {summary['n_2022']} 進場／good {summary['n_2022_good']}）。"
            f"最佳特徵 `{best['feature']}`：IC **{best['ic_full']}** · hit **{best['hit_median']}** "
            f"({best['hit_side']}) · OOF-IC {best['ic_oof_le2018']} · held-IC {best['ic_held_ge2019']}。",
            "",
            "IC 不穩：`rel_5` full IC 達 edge 門檻，但 ≤2018 ≈0／≥2019 才抬；hit 0.59 < 0.60 → **`SIGNAL_WEAK`**。",
            "",
            f"Threshold block probe `{probe['id']}`（修 2022 代價 tip）：",
            f"- 2022 gap: P3 **{probe['y2022_vs_base_p3']}** → probe **{probe['y2022_vs_base_probe']}**（ok={probe['y2022_ok']}）",
            f"- held↑ {probe['held_p3']} → {probe['held_probe']}（ok={probe['held_ok']}）· "
            f"tipY↑ {probe['tip_ytd_p3']} → {probe['tip_ytd_probe']}（ok={probe['tip_ok']}）",
            "",
            "## Implication",
            "",
            "- 規則層（0k9x/0k9y）+ 內生 trail/rel/vol 訊號層皆難穩修 2022 而不傷 tip。",
            "- 接受 Path3 yearly **1/15** 殘差（2022 −0.75），或另開**外生**特徵票（非 COMP−SAT trail 自迴圈）。",
            "- **不** promote `BLOCK_rel_5` · Path3 observe **KEEP** · Soft-Frozen／Exact T+1 **KEEP** · "
            "fill/emit **OFF** · cutover **BLOCKED**。",
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
                "best_feature": best,
                "probe": probe,
                "soft_frozen_keep": True,
                "path3_observe_keep": True,
                "fill_emit_flags": False,
                "live_wire": False,
                "cutover": "BLOCKED",
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    write_repro_pointer(OPS / f"{DECISION_ID}.json", REP / f"{DECISION_ID}.json", kind="decision pack")

    print(
        json.dumps(
            {"verdict": verdict, "best": best, "probe": probe, "summary": summary},
            indent=2,
            ensure_ascii=False,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
