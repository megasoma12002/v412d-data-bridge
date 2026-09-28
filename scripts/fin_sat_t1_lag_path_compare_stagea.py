#!/usr/bin/env python3
"""FIN×SAT Exact T+1 lag handling-path compare Stage A (paper).

Charter: research/ops/FIN_SAT_T1_LAG_PATH_COMPARE_STAGEA_CHARTER.md
Parents: 0k9n/0k9o/0k9p TIP_LAG_BLOCK · Soft-Frozen KEEP.
Compare stop-switch / pure-SAT / T+0 counterfactual / non-binary blend.
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
REPRO = ROOT / "repro" / "fin-sat-t1-lag-path-compare-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_SAT_T1_LAG_PATH_COMPARE_STAGEA_CHARTER"
SCREEN_ID = "FIN_SAT_T1_LAG_PATH_COMPARE_STAGEA_SCREEN"
DECISION_ID = "FIN_SAT_T1_LAG_PATH_COMPARE_STAGEA_DECISION_PACK"
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


def _blend_nav(comp: pd.DataFrame, sat_nav: pd.DataFrame, w_sat: np.ndarray) -> tuple[pd.DataFrame, dict[str, Any]]:
    m = (
        comp.rename(columns={"nav": "nav_c"})
        .merge(sat_nav.rename(columns={"nav": "nav_s"}), on="date")
        .sort_values("date")
        .reset_index(drop=True)
    )
    w = np.clip(np.asarray(w_sat, dtype=float), 0.0, 1.0)
    if len(w) != len(m):
        raise ValueError("len mismatch")
    rc = m["nav_c"].pct_change().fillna(0.0).to_numpy()
    rs = m["nav_s"].pct_change().fillna(0.0).to_numpy()
    r = (1.0 - w) * rc + w * rs
    nav = (1.0 + r).cumprod() * float(m["nav_c"].iloc[0])
    flips = int(np.sum(np.abs(np.diff(w)) > 1e-12)) if len(w) > 1 else 0
    return pd.DataFrame({"date": m["date"].to_numpy(), "nav": nav}), {
        "pct_days_sat": round(float(np.mean(w)) * 100, 2),
        "n_flips": flips,
        "mean_w_sat": round(float(np.mean(w)), 4),
    }


def _eval_row(
    base_w: dict[str, Any],
    chal_w: dict[str, Any],
    tip: dict[str, Any],
    *,
    fam: str,
    sat_held_cagr: float | None,
    sf_ok: bool,
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
    # score for ranking
    tip_cagr_s = 0.0 if tip_ytd_cagr is None else float(np.clip(tip_ytd_cagr, -5.0, 5.0))
    held_s = 0.0 if cagr_pp is None else float(np.clip(cagr_pp, -2.0, 5.0))
    mdd_s = 0.0 if mdd_pp is None else float(np.clip(mdd_pp, -1.0, 1.0))
    score = round(1.5 * tip_cagr_s + (1.0 if tip_mdd_ok else 0.0) + held_s + 0.5 * mdd_s, 4)
    return {
        "held_cagr_lift_pp": None if cagr_pp is None else round(float(cagr_pp), 4),
        "held_mdd_pp": None if mdd_pp is None else round(float(mdd_pp), 4),
        "held_abs_mdd": None if abs_mdd is None else round(float(abs_mdd), 6),
        "tip_ytd_cagr_pp": tip_ytd_cagr,
        "tip_1y_cagr_pp": tip_1y_cagr,
        "tip_ytd_mdd_pp": tip_ytd_mdd,
        "tip_1y_mdd_pp": tip_1y_mdd,
        "family": fam,
        "sf_ok": sf_ok,
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
        "score": score,
        "hit": bool(sf_ok and shaped and fam in ("path", "switch")),
        "t0_shaped": bool((not sf_ok) and shaped),
    }


def _verdict(rows: list[dict[str, Any]]) -> str:
    sf = [r for r in rows if r["eval"]["sf_ok"] and r["fam"] in ("path", "switch", "ref")]
    t0 = [r for r in rows if (not r["eval"]["sf_ok"]) and r["fam"] == "path"]
    if any(r["eval"]["hit"] for r in sf):
        return "PATH_HIT"
    if any(r["eval"]["t0_shaped"] for r in t0) and not any(r["eval"]["gates"]["shaped"] for r in sf):
        return "T0_ONLY_EDGE"
    # tradeoff: best tip-clean sf vs best held sf differ
    tip_ok = [r for r in sf if r["eval"]["gates"]["tip_clean"]]
    held_ok = [
        r
        for r in sf
        if r["eval"]["gates"]["cagr"] and r["eval"]["gates"]["mdd_near_flat"] and r["eval"]["gates"]["mdd_band"]
    ]
    if tip_ok and held_ok:
        best_tip = max(tip_ok, key=lambda r: float(r["eval"]["tip_ytd_cagr_pp"] or -99))
        best_held = max(held_ok, key=lambda r: float(r["eval"]["held_cagr_lift_pp"] or -99))
        if best_tip["id"] != best_held["id"]:
            return "PATH_TRADEOFF"
    if tip_ok or any(r["eval"]["gates"]["economic"] for r in sf):
        return "PATH_SOFT"
    return "NO_SF_EDGE"


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

    rel = comp["nav"].pct_change().fillna(0.0) - sat_nav["nav"].pct_change().fillna(0.0)
    trail = _trail(rel, 63)
    sat_lead = (trail <= -THETA).fillna(False).astype(bool)
    prev = sat_lead.shift(1).fillna(False).astype(bool)
    enter = sat_lead.to_numpy() & (~prev.to_numpy())
    trail_l1 = trail.shift(1)
    sat_l1 = sat_lead.shift(1).fillna(False).astype(bool).to_numpy()

    n = len(comp)
    w_comp = np.zeros(n)
    w_sat = np.ones(n)
    w_blend = np.clip((-trail_l1.fillna(0.0) / THETA).to_numpy(), 0.0, 1.0)
    w_scale50 = np.where(sat_l1, 0.5, 0.0)
    w_state_sd = sat_lead.astype(float).to_numpy()
    w_enter_m1 = (sat_lead.to_numpy() | pd.Series(enter).shift(-1).fillna(False).to_numpy()).astype(float)
    w_sat_l1 = sat_l1.astype(float)

    books: list[dict[str, Any]] = [
        {"id": BASE_ID, "fam": "ctrl", "path": "ctrl", "sf_ok": True, "w": None, "nav_src": "live"},
        {"id": "P1_STOP_LIVE", "fam": "path", "path": "1_stop", "sf_ok": True, "nav_src": "live"},
        {"id": "P1_STOP_COMP", "fam": "path", "path": "1_stop", "sf_ok": True, "w": w_comp},
        {"id": "P2_SAT_PURE", "fam": "path", "path": "2_sat", "sf_ok": True, "w": w_sat},
        {"id": "P3_T0_STATE", "fam": "path", "path": "3_t0", "sf_ok": False, "w": w_state_sd},
        {"id": "P3_T0_ENTER_M1", "fam": "path", "path": "3_t0", "sf_ok": False, "w": w_enter_m1},
        {"id": "P4_BLEND_TRAIL", "fam": "path", "path": "4_mech", "sf_ok": True, "w": w_blend},
        {"id": "P4_SCALE50_L1", "fam": "path", "path": "4_mech", "sf_ok": True, "w": w_scale50},
        {"id": "R_SAT_LEAD_L1", "fam": "switch", "path": "ref_switch", "sf_ok": True, "w": w_sat_l1},
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
        if spec.get("nav_src") == "live" or bid == BASE_ID:
            nav = live.copy()
            meta = {"pct_days_sat": 0.0, "n_flips": 0, "mean_w_sat": 0.0, "rule": "live"}
        else:
            nav, meta = _blend_nav(comp, sat_nav, spec["w"])
            meta["rule"] = bid
        nav.to_csv(OUT / f"nav_{bid}.csv", index=False)
        tip = (
            {
                "ytd": {"mdd_improve_pp": 0.0, "cagr_lift_pp": 0.0, "gate": "PASS"},
                "trailing_1y": {"mdd_improve_pp": 0.0, "cagr_lift_pp": 0.0, "gate": "PASS"},
            }
            if bid in (BASE_ID, "P1_STOP_LIVE")
            else _tip(live, nav)
        )
        # P1_STOP_LIVE tip vs live is zero by construction
        if bid == "P1_STOP_LIVE":
            tip = {
                "ytd": {"mdd_improve_pp": 0.0, "cagr_lift_pp": 0.0, "gate": "PASS"},
                "trailing_1y": {"mdd_improve_pp": 0.0, "cagr_lift_pp": 0.0, "gate": "PASS"},
            }
        ev = _eval_row(
            base_w,
            _pack(nav),
            tip,
            fam=fam,
            sat_held_cagr=sat_held,
            sf_ok=bool(spec["sf_ok"]),
        )
        rows.append(
            {
                "id": bid,
                "fam": fam,
                "path": spec["path"],
                "meta": meta,
                "eval": ev,
                "tip": tip,
            }
        )
        print(json.dumps({"book": bid, "path": spec["path"], "sf_ok": spec["sf_ok"], "eval": ev}, ensure_ascii=False), flush=True)

    verdict = _verdict(rows)
    generated = _utc()

    sf_rows = [r for r in rows if r["eval"]["sf_ok"] and r["id"] != BASE_ID]
    t0_rows = [r for r in rows if not r["eval"]["sf_ok"]]
    sf_ranked = sorted(sf_rows, key=lambda r: float(r["eval"]["score"]), reverse=True)
    t0_shaped = [r for r in t0_rows if r["eval"]["t0_shaped"]]
    hits = [r for r in sf_rows if r["eval"]["hit"]]
    hits.sort(key=lambda r: float(r["eval"]["held_cagr_lift_pp"] or -9), reverse=True)

    best_sf = sf_ranked[0] if sf_ranked else None
    best_tip_sf = None
    tip_cands = [r for r in sf_rows if r["eval"]["gates"]["tip_clean"]]
    if tip_cands:
        best_tip_sf = max(tip_cands, key=lambda r: float(r["eval"]["tip_ytd_cagr_pp"] or -99))
    best_held_sf = max(sf_rows, key=lambda r: float(r["eval"]["held_cagr_lift_pp"] or -99)) if sf_rows else None

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
        "ranking_sf": [
            {
                "id": r["id"],
                "path": r["path"],
                "score": r["eval"]["score"],
                "tip_clean": r["eval"]["gates"]["tip_clean"],
                "held_cagr_lift_pp": r["eval"]["held_cagr_lift_pp"],
                "tip_ytd_cagr_pp": r["eval"]["tip_ytd_cagr_pp"],
                "shaped": r["eval"]["gates"]["shaped"],
            }
            for r in sf_ranked
        ],
        "books": [
            {
                "id": r["id"],
                "fam": r["fam"],
                "path": r["path"],
                "meta": r["meta"],
                "eval": r["eval"],
                "tip": r["tip"],
            }
            for r in rows
        ],
        "register": "0k9q",
    }

    screen_md = "\n".join(
        [
            f"# {SCREEN_ID}",
            "",
            f"Date: 2026-09-28 · Generated `{generated}`",
            f"Status: **{verdict}** · Soft-Frozen **KEEP** · parents **KEEP** · live wire **false**",
            "",
            "## Soft-Frozen ranking (score)",
            "",
            "| rank | ID | path | score | heldCAGR↑ | tipY↑ | tipClean | shaped |",
            "|---:|---|---|---:|---:|---:|---|---|",
        ]
        + [
            f"| {i+1} | {r['id']} | {r['path']} | {r['eval']['score']} | {r['eval']['held_cagr_lift_pp']} | "
            f"{r['eval']['tip_ytd_cagr_pp']} | {r['eval']['gates']['tip_clean']} | {r['eval']['gates']['shaped']} |"
            for i, r in enumerate(sf_ranked)
        ]
        + [
            "",
            "## T+0 counterfactual",
            "",
            "| ID | score | heldCAGR↑ | tipY↑ | tipClean | t0_shaped |",
            "|---|---:|---:|---:|---|---|",
        ]
        + [
            f"| {r['id']} | {r['eval']['score']} | {r['eval']['held_cagr_lift_pp']} | {r['eval']['tip_ytd_cagr_pp']} | "
            f"{r['eval']['gates']['tip_clean']} | {r['eval']['t0_shaped']} |"
            for r in t0_rows
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
        "Parents: 0k9n/0k9o/0k9p · register **0k9q**",
        "",
        "## Verdict",
        "",
        f"**`{verdict}`**",
        "",
        "## Reading",
        "",
    ]
    if best_sf:
        dlines.append(
            f"- Soft-Frozen best score: `{best_sf['id']}` score={best_sf['eval']['score']} · "
            f"held↑ {best_sf['eval']['held_cagr_lift_pp']} tipY↑ {best_sf['eval']['tip_ytd_cagr_pp']} · "
            f"tipClean={best_sf['eval']['gates']['tip_clean']}"
        )
    if best_tip_sf:
        dlines.append(
            f"- Soft-Frozen best tip-clean: `{best_tip_sf['id']}` tipY↑ {best_tip_sf['eval']['tip_ytd_cagr_pp']} · "
            f"held↑ {best_tip_sf['eval']['held_cagr_lift_pp']} heldMDD {best_tip_sf['eval']['held_mdd_pp']}"
        )
    if best_held_sf:
        dlines.append(
            f"- Soft-Frozen best held CAGR: `{best_held_sf['id']}` held↑ {best_held_sf['eval']['held_cagr_lift_pp']} · "
            f"tipY↑ {best_held_sf['eval']['tip_ytd_cagr_pp']}"
        )
    if t0_shaped:
        dlines.append("T+0 counterfactual shaped:")
        for r in t0_shaped:
            dlines.append(
                f"- `{r['id']}` held↑ {r['eval']['held_cagr_lift_pp']} tipY↑ {r['eval']['tip_ytd_cagr_pp']}"
            )
    dlines.append("")
    if hits:
        dlines += [f"SF champion HIT: `{hits[0]['id']}`", ""]
    else:
        dlines += ["No Soft-Frozen PATH_HIT.", ""]

    dlines += ["## All books", ""]
    for r in rows:
        if r["id"] == BASE_ID:
            continue
        g = r["eval"]["gates"]
        dlines.append(
            f"- `{r['id']}` path={r['path']} sf={r['eval']['sf_ok']} score={r['eval']['score']} · "
            f"held↑ {r['eval']['held_cagr_lift_pp']} tipY↑ {r['eval']['tip_ytd_cagr_pp']} · "
            f"tipClean={g['tip_clean']} shaped={g['shaped']}"
        )
    dlines += [
        "",
        "## Binding",
        "",
        "1. Soft-Frozen / Exact T+1 / COOL / SELL_a75 / live CONF α=0.10 KEEP",
        "2. COMPOSITE + SAT_RELAX observes **KEEP OPEN**",
        "3. T+0 paths are counterfactual only · not observe · not live without policy change",
        "4. Do not expand path grid after peek",
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
        "best_sf_score": None if not best_sf else best_sf["id"],
        "best_sf_tip_clean": None if not best_tip_sf else best_tip_sf["id"],
        "best_sf_held": None if not best_held_sf else best_held_sf["id"],
        "best_hit": None if not hits else hits[0]["id"],
        "t0_shaped": [r["id"] for r in t0_shaped],
        "charter": f"research/ops/{CHARTER_ID}.md",
        "screen": f"research/ops/{SCREEN_ID}.md",
        "register": "0k9q",
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

    print(
        json.dumps(
            {
                "verdict": verdict,
                "best_sf": None if not best_sf else best_sf["id"],
                "best_tip_sf": None if not best_tip_sf else best_tip_sf["id"],
                "best_held_sf": None if not best_held_sf else best_held_sf["id"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
