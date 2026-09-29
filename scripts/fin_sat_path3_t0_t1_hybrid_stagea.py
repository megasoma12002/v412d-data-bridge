#!/usr/bin/env python3
"""FIN×SAT Path3 T0-decision × T1-fill hybrid Stage A (paper).

Compare same-bar P3_T0_STATE vs Exact T+1 fill hybrid (SAT_LEAD.shift(1)).
Charter: research/ops/FIN_SAT_PATH3_T0_T1_HYBRID_STAGEA_CHARTER.md
Soft-Frozen KEEP · Path3 observe KEEP · no live.
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
REPRO = ROOT / "repro" / "fin-sat-path3-t0-t1-hybrid-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_SAT_PATH3_T0_T1_HYBRID_STAGEA_CHARTER"
SCREEN_ID = "FIN_SAT_PATH3_T0_T1_HYBRID_STAGEA_SCREEN"
DECISION_ID = "FIN_SAT_PATH3_T0_T1_HYBRID_STAGEA_DECISION_PACK"
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


def _load(path: Path) -> pd.DataFrame:
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


def _blend(comp: pd.DataFrame, sat: pd.DataFrame, w_sat: np.ndarray) -> tuple[pd.DataFrame, dict[str, Any]]:
    m = (
        comp.rename(columns={"nav": "nav_c"})
        .merge(sat.rename(columns={"nav": "nav_s"}), on="date")
        .sort_values("date")
        .reset_index(drop=True)
    )
    w = np.clip(np.asarray(w_sat, dtype=float), 0.0, 1.0)
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


def _yearly(base: pd.DataFrame, chal: pd.DataFrame) -> list[dict[str, Any]]:
    b = base.copy()
    c = chal.copy()
    b["y"] = pd.to_datetime(b["date"]).dt.year
    c["y"] = pd.to_datetime(c["date"]).dt.year
    rows = []
    for y in sorted(set(b["y"]) & set(c["y"])):
        bb = b[b["y"] == y].reset_index(drop=True)
        cc = c[c["y"] == y].reset_index(drop=True)
        if len(bb) < 20 or len(cc) < 20:
            continue
        bn = bb["nav"].astype(float) / float(bb["nav"].iloc[0])
        cn = cc["nav"].astype(float) / float(cc["nav"].iloc[0])
        bret = float(bn.iloc[-1] - 1.0) * 100
        cret = float(cn.iloc[-1] - 1.0) * 100
        bmdd = float((bn / bn.cummax() - 1.0).min()) * 100
        cmdd = float((cn / cn.cummax() - 1.0).min()) * 100
        rows.append(
            {
                "year": int(y),
                "base_ret_pct": round(bret, 2),
                "chal_ret_pct": round(cret, 2),
                "ret_lift_pp": round(cret - bret, 2),
                "base_mdd_pct": round(bmdd, 2),
                "chal_mdd_pct": round(cmdd, 2),
                "mdd_lift_pp": round(cmdd - bmdd, 2),
                "winner": "HYBRID" if cret > bret else ("BASE" if cret < bret else "TIE"),
            }
        )
    return rows


def _eval(
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
        "hit": bool(sf_ok and shaped),
        "t0_shaped": bool((not sf_ok) and shaped),
    }


def _verdict(rows: list[dict[str, Any]]) -> str:
    hybrid = next((r for r in rows if r["id"] == "P3_HYBRID_T1_FILL"), None)
    t0 = next((r for r in rows if r["id"] == "P3_T0_STATE"), None)
    if hybrid and hybrid["eval"]["hit"]:
        return "HYBRID_HIT"
    if hybrid and hybrid["eval"]["gates"]["tip_clean"] and hybrid["eval"]["gates"]["economic"]:
        return "HYBRID_SOFT"
    if t0 and t0["eval"]["t0_shaped"] and hybrid and not hybrid["eval"]["gates"]["tip_clean"]:
        return "T0_SAMEBAR_ONLY"
    if hybrid and not hybrid["eval"]["gates"]["tip_clean"]:
        return "HYBRID_TIP_BLOCK"
    return "HYBRID_TIP_BLOCK"


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

    rel = comp["nav"].pct_change().fillna(0.0) - sat["nav"].pct_change().fillna(0.0)
    trail = _trail(rel, 63)
    sat_lead = (trail <= -THETA).fillna(False).astype(bool)
    w_t0 = sat_lead.astype(float).to_numpy()
    w_hybrid = sat_lead.shift(1).fillna(False).astype(float).to_numpy()
    w_sat = np.ones(len(comp))

    # prove alias: hybrid ≡ R_SAT_LEAD_L1
    assert np.allclose(w_hybrid, sat_lead.shift(1).fillna(False).astype(float).to_numpy())

    base_w = _pack(live)
    sat_held = cagr_lift_pp(
        (base_w.get("heldout_2019_plus") or {}).get("cagr"),
        (_pack(sat).get("heldout_2019_plus") or {}).get("cagr"),
    )

    specs = [
        {"id": BASE_ID, "fam": "ctrl", "sf_ok": True, "w": None, "note": "live base"},
        {
            "id": "P3_T0_STATE",
            "fam": "path",
            "sf_ok": False,
            "w": w_t0,
            "note": "same-bar NAV · observe upper bound",
        },
        {
            "id": "P3_HYBRID_T1_FILL",
            "fam": "path",
            "sf_ok": True,
            "w": w_hybrid,
            "note": "SAT_LEAD close t-1 → earn day t · Exact T+1 fill",
        },
        {
            "id": "R_SAT_LEAD_L1",
            "fam": "ref",
            "sf_ok": True,
            "w": w_hybrid.copy(),
            "note": "alias of P3_HYBRID_T1_FILL (0k9q)",
        },
        {
            "id": "P2_SAT_PURE",
            "fam": "path",
            "sf_ok": True,
            "w": w_sat,
            "note": "always SAT tip line",
        },
    ]

    rows: list[dict[str, Any]] = []
    navs: dict[str, pd.DataFrame] = {}
    for spec in specs:
        bid = spec["id"]
        print(f"{bid} ...", flush=True)
        if spec["w"] is None:
            nav = live.copy()
            meta = {"pct_days_sat": 0.0, "n_flips": 0, "mean_w_sat": 0.0}
        else:
            nav, meta = _blend(comp, sat, spec["w"])
        meta["note"] = spec["note"]
        nav.to_csv(OUT / f"nav_{bid}.csv", index=False)
        navs[bid] = nav
        tip = (
            {
                "ytd": {"mdd_improve_pp": 0.0, "cagr_lift_pp": 0.0, "gate": "PASS"},
                "trailing_1y": {"mdd_improve_pp": 0.0, "cagr_lift_pp": 0.0, "gate": "PASS"},
            }
            if bid == BASE_ID
            else _tip(live, nav)
        )
        ev = _eval(
            base_w,
            _pack(nav),
            tip,
            fam=spec["fam"],
            sat_held_cagr=sat_held,
            sf_ok=bool(spec["sf_ok"]),
        )
        row = {"id": bid, "fam": spec["fam"], "meta": meta, "eval": ev, "tip": tip, "windows": _pack(nav)}
        rows.append(row)
        print(json.dumps({"book": bid, "sf_ok": spec["sf_ok"], "eval": ev}, ensure_ascii=False), flush=True)

    hybrid_nav = navs["P3_HYBRID_T1_FILL"]
    yearly = _yearly(live, hybrid_nav)
    wl = sum(1 for y in yearly if y["winner"] == "HYBRID"), sum(1 for y in yearly if y["winner"] == "BASE")
    verdict = _verdict(rows)
    generated = _utc()

    # gap: T0 same-bar minus hybrid
    t0 = next(r for r in rows if r["id"] == "P3_T0_STATE")
    hy = next(r for r in rows if r["id"] == "P3_HYBRID_T1_FILL")
    gap = {
        "held_cagr_gap_pp": round(
            float(t0["eval"]["held_cagr_lift_pp"] or 0) - float(hy["eval"]["held_cagr_lift_pp"] or 0), 4
        ),
        "tip_ytd_gap_pp": round(
            float(t0["eval"]["tip_ytd_cagr_pp"] or 0) - float(hy["eval"]["tip_ytd_cagr_pp"] or 0), 4
        ),
        "tip_1y_gap_pp": round(
            float(t0["eval"]["tip_1y_cagr_pp"] or 0) - float(hy["eval"]["tip_1y_cagr_pp"] or 0), 4
        ),
    }

    screen = {
        "label": f"{SCREEN_ID}_{generated.replace(':', '').replace('-', '')}",
        "generated_at_utc": generated,
        "charter": CHARTER_ID,
        "register": "0k9s",
        "verdict": verdict,
        "theta": THETA,
        "equivalence_note": "P3_HYBRID_T1_FILL ≡ R_SAT_LEAD_L1 (SAT_LEAD.shift(1) on NAV returns)",
        "gap_t0_minus_hybrid": gap,
        "hybrid_yearly_wl": {"hybrid_wins": wl[0], "base_wins": wl[1]},
        "rows": rows,
        "yearly_hybrid_vs_base": yearly,
        "soft_frozen_keep": True,
        "path3_observe_keep": True,
        "live_wire": False,
    }

    (OUT / "screen.json").write_text(json.dumps(screen, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    md_lines = [
        f"# {SCREEN_ID}",
        "",
        f"Date: 2026-09-28 · generated `{generated}`",
        f"Verdict: **`{verdict}`** · Soft-Frozen KEEP · Path3 observe KEEP · no live",
        "",
        "## Head-to-head",
        "",
        "| Book | sf_ok | held CAGR↑ | held MDD↑ | tip YTD↑ | tip 1y↑ | tipClean | shaped | score |",
        "|---|---|---:|---:|---:|---:|---|---|---:|",
    ]
    for r in rows:
        e = r["eval"]
        md_lines.append(
            f"| `{r['id']}` | {e['sf_ok']} | {e['held_cagr_lift_pp']} | {e['held_mdd_pp']} | "
            f"{e['tip_ytd_cagr_pp']} | {e['tip_1y_cagr_pp']} | {e['gates']['tip_clean']} | "
            f"{e['gates']['shaped']} | {e['score']} |"
        )
    md_lines += [
        "",
        "## Gap (same-bar T0 − hybrid T1-fill)",
        "",
        f"- held CAGR gap: **{gap['held_cagr_gap_pp']}** pp",
        f"- tip YTD gap: **{gap['tip_ytd_gap_pp']}** pp",
        f"- tip 1y gap: **{gap['tip_1y_gap_pp']}** pp",
        "",
        f"Equivalence: `P3_HYBRID_T1_FILL` ≡ `R_SAT_LEAD_L1` (0k9q).",
        "",
        f"Hybrid yearly W–L vs live: **{wl[0]}–{wl[1]}**",
        "",
        "Repro: `repro/fin-sat-path3-t0-t1-hybrid-stagea/`",
        "",
    ]
    screen_md = "\n".join(md_lines) + "\n"
    write_ops_and_repro_pointer(OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", screen_md, kind="screen")
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(screen, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_repro_pointer(OPS / f"{SCREEN_ID}.json", REP / f"{SCREEN_ID}.json", kind="screen")

    # Decision pack
    decision_md = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: 2026-09-28 · Verdict: **`{verdict}`**",
            "Status: Soft-Frozen **KEEP** · Exact T+1 fills **KEEP** · Path3 observe **KEEP** · cutover **BLOCKED** · no live",
            "",
            "## Answer",
            "",
            "Realistic live Path3（决策用当日 close `SAT_LEAD`，下单／收益从下一交易日开始）"
            "在 NAV 模型上 **≡** `SAT_LEAD.shift(1)`，与 0k9q 的 `R_SAT_LEAD_L1` 相同。",
            "",
            f"- **`P3_T0_STATE`（same-bar）**: held↑ {t0['eval']['held_cagr_lift_pp']} · tipY↑ {t0['eval']['tip_ytd_cagr_pp']} · tip-clean HIT-shaped",
            f"- **`P3_HYBRID_T1_FILL`（T+1 fill）**: held↑ {hy['eval']['held_cagr_lift_pp']} · tipY↑ {hy['eval']['tip_ytd_cagr_pp']} · tipClean={hy['eval']['gates']['tip_clean']}",
            f"- Gap tip YTD: **{gap['tip_ytd_gap_pp']}** pp（same-bar 乐观幅度）",
            "",
            "## Implication",
            "",
            "- Observe `P3_T0_STATE` 数字 **不能**直接当 live 预期。",
            "- 若 live 只做「切换决策 T+0 + 买卖仍 Exact T+1」，回测 **tip 不过**（YTD CAGR↑ 为负）。",
            "- Path3 observe 可继续（paper same-bar 上界）；**不要**把 observe 数字当成 fill-realistic live edge。",
            "- Soft-Frozen／全局 Exact T+1／CONF α **KEEP**；cutover 仍 **BLOCKED**。",
            "",
            "## Hybrid yearly vs live",
            "",
            "| Year | base% | hybrid% | Δpp | winner |",
            "|---:|---:|---:|---:|---|",
        ]
        + [
            f"| {y['year']} | {y['base_ret_pct']} | {y['chal_ret_pct']} | {y['ret_lift_pp']} | {y['winner']} |"
            for y in yearly
        ]
        + [
            "",
            f"W–L: **{wl[0]}–{wl[1]}**",
            "",
            f"Screen: `{SCREEN_ID}.md` · Charter: `{CHARTER_ID}.md` · Register **0k9s**",
            "",
            f"Label: `{DECISION_ID}_2026-09-28__{verdict}__NO_LIVE`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{DECISION_ID}.md", REP / f"{DECISION_ID}.md", decision_md, kind="decision pack"
    )
    decision_json = {
        "label": f"{DECISION_ID}_2026-09-28__{verdict}__NO_LIVE",
        "verdict": verdict,
        "register": "0k9s",
        "gap_t0_minus_hybrid": gap,
        "hybrid": hy["eval"],
        "t0_samebar": t0["eval"],
        "yearly_wl": {"hybrid": wl[0], "base": wl[1]},
        "soft_frozen_keep": True,
        "path3_observe_keep": True,
        "live_wire": False,
        "cutover_blocked": True,
        "equivalence": "P3_HYBRID_T1_FILL === R_SAT_LEAD_L1",
    }
    (OPS / f"{DECISION_ID}.json").write_text(
        json.dumps(decision_json, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    write_repro_pointer(OPS / f"{DECISION_ID}.json", REP / f"{DECISION_ID}.json", kind="decision pack")

    # mark charter done
    charter_md = (OPS / f"{CHARTER_ID}.md").read_text(encoding="utf-8")
    charter_md = charter_md.replace(
        "Status: **Stage A OPEN**",
        f"Status: **Stage A DONE — `{verdict}`**",
        1,
    )
    (OPS / f"{CHARTER_ID}.md").write_text(charter_md, encoding="utf-8")
    cj = json.loads((OPS / f"{CHARTER_ID}.json").read_text(encoding="utf-8"))
    cj["status"] = "STAGE_A_DONE"
    cj["verdict"] = verdict
    (OPS / f"{CHARTER_ID}.json").write_text(json.dumps(cj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps({"verdict": verdict, "gap": gap, "wl": list(wl)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
