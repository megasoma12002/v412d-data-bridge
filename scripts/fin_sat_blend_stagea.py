#!/usr/bin/env python3
"""FIN×SAT 配資混合 Stage A — COMPOSITE × SAT_RELAX daily-return blend (paper).

Charter: research/ops/FIN_SAT_BLEND_STAGEA_CHARTER.md
Parents: COMP_H150_x_A20 observe · SAT_A20_RELAX observe (both KEEP).
Soft-Frozen / SELL_a75 / live CONF α=0.10 KEEP · no live wire · no new overlays.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from e45_paper_harness import WINDOWS_STANDARD, window_stats
from fin_sell_quality_helpers import cagr_lift_pp
from ops_repro_ssot import write_ops_and_repro_pointer
from research_metric_helpers import mdd_delta_pp

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "fin-sat-blend-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_SAT_BLEND_STAGEA_CHARTER"
SCREEN_ID = "FIN_SAT_BLEND_STAGEA_SCREEN"
DECISION_ID = "FIN_SAT_BLEND_STAGEA_DECISION_PACK"
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
    {"id": "CTRL_LIVE_A10", "fam": "ctrl", "w_comp": None},
    {"id": "REF_SAT_RELAX", "fam": "ref", "w_comp": 0.00},
    {"id": "REF_COMP_H150_A20", "fam": "ref", "w_comp": 1.00},
    {"id": "BLEND_C25", "fam": "blend", "w_comp": 0.25},
    {"id": "BLEND_C35", "fam": "blend", "w_comp": 0.35},
    {"id": "BLEND_C40", "fam": "blend", "w_comp": 0.40},
    {"id": "BLEND_C50", "fam": "blend", "w_comp": 0.50},
    {"id": "BLEND_C65", "fam": "blend", "w_comp": 0.65},
    {"id": "BLEND_C75", "fam": "blend", "w_comp": 0.75},
]


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_nav(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    df["nav"] = df["nav"].astype(float)
    return df[["date", "nav"]]


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


def _blend_nav(nav_comp: pd.DataFrame, nav_sat: pd.DataFrame, w_comp: float) -> pd.DataFrame:
    m = pd.merge(
        nav_comp.rename(columns={"nav": "nav_c"}),
        nav_sat.rename(columns={"nav": "nav_s"}),
        on="date",
        how="inner",
    ).sort_values("date")
    rc = m["nav_c"].pct_change().fillna(0.0)
    rs = m["nav_s"].pct_change().fillna(0.0)
    w = float(w_comp)
    r = w * rc + (1.0 - w) * rs
    nav = (1.0 + r).cumprod() * float(m["nav_c"].iloc[0])
    return pd.DataFrame({"date": m["date"].to_numpy(), "nav": nav.to_numpy()})


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
    hit = bool(fam == "blend" and tip_clean and economic and vs_sat_ok)
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
    blends = [r for r in rows if r["fam"] == "blend"]
    if any(r["eval"]["hit"] for r in blends):
        return "BLEND_HIT"
    soft = [
        r
        for r in blends
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
        if r["id"] != BASE_ID
    ):
        return "TIP_MDD_ONLY"
    if any(
        r["eval"]["gates"]["cagr"] and not r["eval"]["gates"]["tip_mdd"]
        for r in rows
        if r["id"] != BASE_ID
    ):
        return "TIP_BLOCK"
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
    sat = _load_nav(SAT_NAV)

    # Align all three on intersection dates for fair blend vs live.
    dates = sorted(set(live["date"]) & set(comp["date"]) & set(sat["date"]))
    live = live[live["date"].isin(dates)].reset_index(drop=True)
    comp = comp[comp["date"].isin(dates)].reset_index(drop=True)
    sat = sat[sat["date"].isin(dates)].reset_index(drop=True)

    base_w = _pack(live)
    # Precompute SAT held lift for vs-sat gate.
    sat_tip = _tip(live, sat)
    sat_w = _pack(sat)
    sat_held = cagr_lift_pp(
        (base_w.get("heldout_2019_plus") or {}).get("cagr"),
        (sat_w.get("heldout_2019_plus") or {}).get("cagr"),
    )

    rows: list[dict[str, Any]] = []
    for spec in GRID:
        bid = str(spec["id"])
        fam = str(spec["fam"])
        w = spec["w_comp"]
        print(f"{bid} w_comp={w} ...", flush=True)
        if fam == "ctrl":
            nav = live.copy()
        else:
            assert w is not None
            nav = _blend_nav(comp, sat, float(w))
        nav.to_csv(OUT / f"nav_{bid}.csv", index=False)
        wpack = _pack(nav)
        if bid == BASE_ID:
            tip = {
                "ytd": {"mdd_improve_pp": 0.0, "cagr_lift_pp": 0.0, "gate": "PASS"},
                "trailing_1y": {"mdd_improve_pp": 0.0, "cagr_lift_pp": 0.0, "gate": "PASS"},
            }
        else:
            tip = _tip(live, nav)
        ev = _eval_row(base_w, wpack, tip, fam=fam, sat_held_cagr=sat_held)
        rows.append(
            {
                "id": bid,
                "fam": fam,
                "w_comp": w,
                "windows": wpack,
                "tip": tip,
                "eval": ev,
                "spec": spec,
            }
        )
        print(json.dumps({"book": bid, "eval": ev}, ensure_ascii=False), flush=True)

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
        "inputs": {
            "live": str(LIVE_NAV.relative_to(ROOT)),
            "comp": str(COMP_NAV.relative_to(ROOT)),
            "sat": str(SAT_NAV.relative_to(ROOT)),
        },
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
                "w_comp": r["w_comp"],
                "windows": r["windows"],
                "tip": r["tip"],
                "eval": r["eval"],
            }
            for r in rows
        ],
    }

    screen_md = "\n".join(
        [
            f"# {SCREEN_ID}",
            "",
            f"Date: 2026-09-28 · Generated `{generated}`",
            f"Status: **{verdict}** · Soft-Frozen **KEEP** · parent observes **KEEP** · live wire **false**",
            "",
            "Daily-return blend `w·COMP + (1−w)·SAT` · HIT needs tip-clean + held≥+0.10 + vs SAT +0.05.",
            "",
            "## Books",
            "",
            "| ID | fam | w_COMP | heldCAGR↑ | heldMDD↑ | tipMDD↑ | tipCAGR↑ | tipClean | vsSAT | HIT |",
            "|---|---|---:|---:|---:|---:|---:|---|---|---|",
        ]
        + [
            "| {id} | {fam} | {w} | {cagr} | {mdd} | {tm} | {tc} | {clean} | {vs} | {hit} |".format(
                id=r["id"],
                fam=r["fam"],
                w="—" if r["w_comp"] is None else r["w_comp"],
                cagr=r["eval"]["held_cagr_lift_pp"],
                mdd=r["eval"]["held_mdd_pp"],
                tm=r["eval"]["tip_ytd_mdd_pp"],
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
        if r["fam"] == "blend"
        and r["eval"]["gates"]["tip_clean"]
        and r["eval"]["gates"]["economic"]
    ]
    tip_clean_econ.sort(key=lambda r: float(r["eval"]["held_cagr_lift_pp"] or -9), reverse=True)

    dlines = [
        f"# {DECISION_ID}",
        "",
        f"Date: 2026-09-28 · Generated `{generated}`",
        f"Status: **{verdict}** · Soft-Frozen **KEEP** · COMPOSITE+SAT_RELAX observes **KEEP** · live wire **false**",
        "",
        f"Charter: `{CHARTER_ID}.md`",
        f"Screen: `{SCREEN_ID}.md`",
        "Parents: COMPOSITE observe · SAT_A20_RELAX observe",
        "",
        "## Verdict",
        "",
        f"**`{verdict}`**",
        "",
        f"SAT parent held CAGR↑ = {None if sat_held is None else round(float(sat_held), 4)}pp · "
        f"blend must clear tip-clean + held≥+0.10 + vs SAT ≥+{VS_SAT_HELD_EXTRA_PP}.",
        "",
    ]
    if best:
        dlines += [
            (
                f"Champion: `{best['id']}` · w_COMP={best['w_comp']} · held CAGR↑ {best['eval']['held_cagr_lift_pp']}pp · "
                f"tipCAGR↑ YTD {best['eval']['tip_ytd_cagr_pp']} · tipMDD↑ {best['eval']['tip_ytd_mdd_pp']}"
            ),
            "",
            "Even HIT → observe ballot **DRAFT only** · do not auto-CLOSE parent observes · no live.",
            "",
        ]
    elif tip_clean_econ:
        top = tip_clean_econ[0]
        dlines += [
            (
                f"Best tip-clean economic blend: `{top['id']}` · w={top['w_comp']} · "
                f"held CAGR↑ {top['eval']['held_cagr_lift_pp']} · vs_sat={top['eval']['gates']['vs_sat_held']}"
            ),
            "",
        ]
    else:
        dlines += ["No blend cleared tip-clean economic gates.", ""]

    dlines += [
        "## Binding",
        "",
        "1. Soft-Frozen / Exact T+1 / COOL / SELL_a75 / live CONF α=0.10 KEEP",
        "2. COMPOSITE + SAT_RELAX observes **KEEP OPEN**",
        "3. Do not reopen HARD×α / COOL-HARD mechanism grids from this pack",
        "4. Even HIT → paper observe ballot DRAFT only · no live wire",
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
        "best_tip_clean_economic_blend": None if not tip_clean_econ else tip_clean_econ[0]["id"],
        "sat_held_cagr_lift_pp": None if sat_held is None else round(float(sat_held), 4),
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
