#!/usr/bin/env python3
"""FIN×SAT local-mutex Stage A — tip vs held temporal separation (paper).

Charter: research/ops/FIN_SAT_LOCAL_MUTEX_STAGEA_CHARTER.md
Parents: 0k9m/0k9l TIP_MDD_ONLY · COMP + SAT_RELAX KEEP.
Soft-Frozen KEEP · Exact T+1 · no live · no feature-table expand.
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
from ops_repro_ssot import write_ops_and_repro_pointer
from research_metric_helpers import mdd_delta_pp

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "fin-sat-local-mutex-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_SAT_LOCAL_MUTEX_STAGEA_CHARTER"
SCREEN_ID = "FIN_SAT_LOCAL_MUTEX_STAGEA_SCREEN"
DECISION_ID = "FIN_SAT_LOCAL_MUTEX_STAGEA_DECISION_PACK"
BASE_ID = "CTRL_LIVE_A10"

LIVE_NAV = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/ctrl_live_a10_daily_nav.csv"
COMP_NAV = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/comp_h150_x_a20_daily_nav.csv"
SAT_NAV = ROOT / "repro/sat-a20-relax-dual-paper-observe/outputs/sat_a20_relax_daily_nav.csv"

THETA = 0.01
CAGR_FLOOR_PP = 0.10
HELD_MDD_MIN_PP = -0.25
HELD_ABS_MDD_MAX = 0.15
TIP_MDD_MIN_PP = 0.0
TIP_CAGR_MIN_PP = 0.0
VS_SAT_HELD_EXTRA_PP = 0.05
DRAG_DENSITY_N = 63
DRAG_DENSITY_MIN = 0.5


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
    if len(u) != len(m):
        raise ValueError("len mismatch")
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
    hit = bool(fam == "switch" and shaped)
    ub_shaped = bool(fam == "ub" and shaped)
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
        "hit": hit,
        "ub_shaped": ub_shaped,
    }


def _diagnose(panel: pd.DataFrame, asof: pd.Timestamp) -> dict[str, Any]:
    tip = panel["date"] >= (asof - pd.Timedelta(days=365))
    held = panel["date"] >= pd.Timestamp("2019-01-01")
    pre = held & ~tip

    def rate(mask: pd.Series, col: str) -> float:
        sub = panel.loc[mask, col]
        return round(float(sub.mean()) * 100, 2) if len(sub) else 0.0

    def sum_rel(mask: pd.Series) -> dict[str, float]:
        sub = panel.loc[mask].dropna(subset=["rel"])
        out = {
            "ALL": round(float(sub["rel"].sum()), 6),
            "SAT_LEAD": round(float(sub.loc[sub["sat_lead"], "rel"].sum()), 6),
            "COMP_LEAD": round(float(sub.loc[sub["comp_lead"], "rel"].sum()), 6),
            "SIMILAR": round(float(sub.loc[sub["similar"], "rel"].sum()), 6),
        }
        return out

    p_sat_tip = rate(tip, "sat_lead")
    p_sat_pre = rate(pre, "sat_lead")
    p_comp_tip = rate(tip, "comp_lead")
    p_comp_pre = rate(pre, "comp_lead")
    d_sat = (p_sat_tip - p_sat_pre) / 100.0
    d_comp = (p_comp_pre - p_comp_tip) / 100.0
    local_mutex_score = round(float(d_sat + d_comp), 4)

    tip_sums = sum_rel(tip)
    held_sums = sum_rel(held)
    tip_damage_from_sat = None
    if tip_sums["ALL"] != 0:
        tip_damage_from_sat = round(tip_sums["SAT_LEAD"] / tip_sums["ALL"], 4)

    # same-day conflict: tip calendar day that is COMP_LEAD (local wants COMP, tip window wants SAT)
    conflict_pct = rate(tip, "comp_lead")
    local = local_mutex_score >= 0.35 and (tip_damage_from_sat or 0) >= 0.8 and conflict_pct <= 15.0

    return {
        "asof": str(asof.date()),
        "theta": THETA,
        "n_tip": int(tip.sum()),
        "n_pre_tip": int(pre.sum()),
        "n_held": int(held.sum()),
        "p_sat_lead_tip_pct": p_sat_tip,
        "p_sat_lead_pre_pct": p_sat_pre,
        "p_comp_lead_tip_pct": p_comp_tip,
        "p_comp_lead_pre_pct": p_comp_pre,
        "p_drag_tip_pct": rate(tip, "drag"),
        "p_drag_pre_pct": rate(pre, "drag"),
        "delta_p_sat_lead_tip_minus_pre": round(p_sat_tip - p_sat_pre, 2),
        "delta_p_comp_lead_pre_minus_tip": round(p_comp_pre - p_comp_tip, 2),
        "local_mutex_score": local_mutex_score,
        "sum_rel_tip": tip_sums,
        "sum_rel_held": held_sums,
        "sum_rel_pre": sum_rel(pre),
        "tip_damage_frac_from_sat_lead": tip_damage_from_sat,
        "tip_comp_lead_conflict_pct": conflict_pct,
        "p_comp_lead_and_drag": round(float((panel["comp_lead"] & panel["drag"]).mean()) * 100, 4),
        "local_mutex_diag": bool(local),
    }


def _verdict(diag: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    sw = [r for r in rows if r["fam"] == "switch"]
    ubs = [r for r in rows if r["fam"] == "ub"]
    if any(r["eval"]["hit"] for r in sw):
        return "LOCAL_MUTEX_HIT"
    ub_ok = any(r["eval"]["ub_shaped"] for r in ubs)
    causal_tip_mdd_econ = [
        r
        for r in sw
        if r["eval"]["gates"]["economic"]
        and r["eval"]["gates"]["tip_mdd"]
        and not r["eval"]["gates"]["tip_cagr"]
    ]
    if diag.get("local_mutex_diag") and ub_ok and causal_tip_mdd_econ and not any(
        r["eval"]["gates"]["tip_cagr"] for r in sw
    ):
        return "TIP_LAG_BLOCK"
    if diag.get("local_mutex_diag") and ub_ok:
        return "LOCAL_MUTEX_SIGNAL"
    if (diag.get("tip_comp_lead_conflict_pct") or 0) >= 25:
        return "GLOBAL_CONFLICT"
    if causal_tip_mdd_econ:
        return "TIP_MDD_ONLY"
    return "NO_EDGE"


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
    panel["rc"] = panel["nav_c"].pct_change().fillna(0.0)
    panel["rs"] = panel["nav_s"].pct_change().fillna(0.0)
    panel["rel"] = panel["rc"] - panel["rs"]
    panel["trail_rel_63"] = _trail(panel["rel"], 63)
    panel["sat_lead"] = panel["trail_rel_63"] <= -THETA
    panel["comp_lead"] = panel["trail_rel_63"] >= THETA
    panel["similar"] = ~panel["sat_lead"] & ~panel["comp_lead"]
    panel["drag"] = panel["trail_rel_63"] < 0.0
    panel["sat_lead_l1"] = panel["sat_lead"].shift(1)
    panel["drag_l1"] = panel["drag"].shift(1)
    panel["drag_den63_l1"] = panel["drag"].astype(float).rolling(DRAG_DENSITY_N, min_periods=21).mean().shift(1)
    panel["tiplike_l1"] = panel["drag_den63_l1"] >= DRAG_DENSITY_MIN

    asof = pd.Timestamp(panel["date"].max())
    tip_mask = panel["date"] >= (asof - pd.Timedelta(days=365))
    diag = _diagnose(panel, asof)
    panel.to_csv(OUT / "local_mutex_panel.csv", index=False)
    (OUT / "local_mutex_diag.json").write_text(json.dumps(diag, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"diag": diag}, ensure_ascii=False), flush=True)

    books: list[dict[str, Any]] = [
        {"id": BASE_ID, "fam": "ctrl", "use": None},
        {"id": "REF_SAT_RELAX", "fam": "ref", "use": "sat"},
        {"id": "REF_COMP_H150_A20", "fam": "ref", "use": "comp"},
        {"id": "UB_TIPWIN_SAT", "fam": "ub", "mask": tip_mask.fillna(False).to_numpy()},
        {"id": "UB_STATE_SD", "fam": "ub", "mask": panel["sat_lead"].fillna(False).to_numpy()},
        {
            "id": "R_SAT_LEAD_L1",
            "fam": "switch",
            "mask": panel["sat_lead_l1"].fillna(False).to_numpy(),
        },
        {
            "id": "R_DRAG_L1",
            "fam": "switch",
            "mask": panel["drag_l1"].fillna(False).to_numpy(),
        },
        {
            "id": "R_TIPLIKE_L1",
            "fam": "switch",
            "mask": (
                panel["sat_lead_l1"].fillna(False) & panel["tiplike_l1"].fillna(False)
            ).to_numpy(),
        },
        {
            "id": "R_PRE_COMP_TIP_SAT_L1",
            "fam": "switch",
            # tip-like density → SAT; else COMP (local: park COMP outside tip-like)
            "mask": panel["tiplike_l1"].fillna(False).to_numpy(),
        },
    ]

    base_w = _pack(live)
    sat_w = _pack(sat_nav)
    sat_held = cagr_lift_pp(
        (base_w.get("heldout_2019_plus") or {}).get("cagr"),
        (sat_w.get("heldout_2019_plus") or {}).get("cagr"),
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
            meta = {
                "pct_days_sat": 100.0 if spec["use"] == "sat" else 0.0,
                "n_flips": 0,
                "rule": spec["use"],
            }
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
    hits.sort(key=lambda r: float(r["eval"]["held_cagr_lift_pp"] or -9), reverse=True)
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
        "sat_held_cagr_lift_pp": None if sat_held is None else round(float(sat_held), 4),
        "diagnosis": diag,
        "books": [
            {"id": r["id"], "fam": r["fam"], "meta": r["meta"], "eval": r["eval"], "tip": r["tip"]} for r in rows
        ],
        "register": "0k9n",
    }

    screen_md = "\n".join(
        [
            f"# {SCREEN_ID}",
            "",
            f"Date: 2026-09-28 · Generated `{generated}`",
            f"Status: **{verdict}** · Soft-Frozen **KEEP** · parents **KEEP** · live wire **false**",
            "",
            "## Diagnosis",
            "",
            f"- local_mutex_diag=`{diag['local_mutex_diag']}` · score=`{diag['local_mutex_score']}`",
            f"- P(SAT_LEAD|tip)={diag['p_sat_lead_tip_pct']}% vs pre={diag['p_sat_lead_pre_pct']}% · Δ={diag['delta_p_sat_lead_tip_minus_pre']}",
            f"- P(COMP_LEAD|tip)={diag['p_comp_lead_tip_pct']}% vs pre={diag['p_comp_lead_pre_pct']}% · Δpre−tip={diag['delta_p_comp_lead_pre_minus_tip']}",
            f"- tip damage frac from SAT_LEAD=`{diag['tip_damage_frac_from_sat_lead']}` · tip COMP_LEAD conflict=`{diag['tip_comp_lead_conflict_pct']}%`",
            f"- P(drag|tip)={diag['p_drag_tip_pct']}% vs pre={diag['p_drag_pre_pct']}%",
            "",
            "## Books",
            "",
            "| ID | fam | %SAT | flips | heldCAGR↑ | tipCAGR↑ | tipClean | shaped | HIT/UB |",
            "|---|---|---:|---:|---:|---:|---|---|---|",
        ]
        + [
            "| {id} | {fam} | {ps} | {fl} | {cagr} | {tc} | {clean} | {sh} | {mark} |".format(
                id=r["id"],
                fam=r["fam"],
                ps=r["meta"]["pct_days_sat"],
                fl=r["meta"]["n_flips"],
                cagr=r["eval"]["held_cagr_lift_pp"],
                tc=r["eval"]["tip_ytd_cagr_pp"],
                clean=r["eval"]["gates"]["tip_clean"],
                sh=r["eval"]["gates"]["shaped"],
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
        "Parents: 0k9m/0k9l · register **0k9n**",
        "",
        "## Verdict",
        "",
        f"**`{verdict}`**",
        "",
        "## Reading",
        "",
        f"- local_mutex_diag=`{diag['local_mutex_diag']}` score=`{diag['local_mutex_score']}`",
        f"- tip SAT_LEAD {diag['p_sat_lead_tip_pct']}% vs pre {diag['p_sat_lead_pre_pct']}% · tip COMP_LEAD only {diag['p_comp_lead_tip_pct']}%",
        f"- tip sum_rel ALL={diag['sum_rel_tip']['ALL']} · from SAT_LEAD={diag['sum_rel_tip']['SAT_LEAD']} (frac {diag['tip_damage_frac_from_sat_lead']})",
        f"- held sum_rel COMP_LEAD={diag['sum_rel_held']['COMP_LEAD']} · SAT_LEAD={diag['sum_rel_held']['SAT_LEAD']}",
        "",
    ]
    if ub_shaped:
        dlines.append("UB shaped (non-causal):")
        for r in ub_shaped:
            dlines.append(
                f"- `{r['id']}` held↑ {r['eval']['held_cagr_lift_pp']} tipY↑ {r['eval']['tip_ytd_cagr_pp']} %SAT {r['meta']['pct_days_sat']}"
            )
        dlines.append("")
    if hits:
        dlines.append(f"Champion switch: `{hits[0]['id']}`")
        dlines.append("")
    else:
        dlines.append("No causal switch HIT.")
        dlines.append("")

    dlines += ["## Books", ""]
    for r in rows:
        if r["fam"] in ("ctrl",):
            continue
        g = r["eval"]["gates"]
        dlines.append(
            f"- `{r['id']}` ({r['fam']}) · %SAT={r['meta']['pct_days_sat']} · "
            f"held↑ {r['eval']['held_cagr_lift_pp']} tipY↑ {r['eval']['tip_ytd_cagr_pp']} · "
            f"tipClean={g['tip_clean']} shaped={g['shaped']}"
        )
    dlines += [
        "",
        "## Binding",
        "",
        "1. Soft-Frozen / Exact T+1 / COOL / SELL_a75 / live CONF α=0.10 KEEP",
        "2. COMPOSITE + SAT_RELAX observes **KEEP OPEN**",
        "3. Do not expand feature table or rule grid after peek",
        "4. UB is diagnosis only · not observe · not live",
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
        "local_mutex_diag": diag.get("local_mutex_diag"),
        "local_mutex_score": diag.get("local_mutex_score"),
        "best_hit": None if not hits else hits[0]["id"],
        "best_ub_shaped": None if not ub_shaped else ub_shaped[0]["id"],
        "charter": f"research/ops/{CHARTER_ID}.md",
        "screen": f"research/ops/{SCREEN_ID}.md",
        "register": "0k9n",
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

    print(json.dumps({"verdict": verdict, "best_ub": None if not ub_shaped else ub_shaped[0]["id"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
