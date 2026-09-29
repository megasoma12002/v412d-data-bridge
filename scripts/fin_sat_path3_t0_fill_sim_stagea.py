#!/usr/bin/env python3
"""FIN×SAT Path3 T0 fill-carve simulate Stage A (paper).

Simulates expected NAV if live ACCEPT enables ``T0_CARVE_FIN_SAT_SWITCH``
same-bar fill at ``reference_close`` (MOC close) vs status-quo Exact T+1 open.

Books:
  CTRL_LIVE_A10          — live Soft-Frozen base
  FILL_CARVE_CLOSE       — Path3 switch filled same-bar @ close ≡ P3_T0_STATE
  STATUS_QUO_T1          — Path3 decision same-day, fill/earn next open (lag-1)
  P2_SAT_PURE            — always-SAT tip line (SF-legal ref)

Soft-Frozen KEEP · Path3 observe KEEP · fill flag stays OFF · no live · no broker.
Register: 0k9v
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
REPRO = ROOT / "repro" / "fin-sat-path3-t0-fill-sim-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_SAT_PATH3_T0_FILL_SIM_STAGEA_CHARTER"
SCREEN_ID = "FIN_SAT_PATH3_T0_FILL_SIM_STAGEA_SCREEN"
DECISION_ID = "FIN_SAT_PATH3_T0_FILL_SIM_STAGEA_DECISION_PACK"
BASE_ID = "CTRL_LIVE_A10"
REGISTER = "0k9v"
CARVE_OUT_ID = "T0_CARVE_FIN_SAT_SWITCH"

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


def _trail(r: pd.Series, n: int = 63) -> pd.Series:
    return (1.0 + r).rolling(n, min_periods=n).apply(lambda x: float(np.prod(x) - 1.0), raw=True)


def _blend(comp: pd.DataFrame, sat: pd.DataFrame, w: np.ndarray) -> tuple[pd.DataFrame, dict[str, Any]]:
    rc = comp["nav"].pct_change().fillna(0.0).to_numpy()
    rs = sat["nav"].pct_change().fillna(0.0).to_numpy()
    r = (1.0 - w) * rc + w * rs
    nav = (1.0 + r).cumprod() * float(comp["nav"].iloc[0])
    chal = pd.DataFrame({"date": comp["date"].to_numpy(), "nav": nav})
    flips = int(np.sum(np.abs(np.diff(w)) > 1e-12))
    meta = {
        "pct_days_sat": round(float(np.mean(w)) * 100, 2),
        "n_flips": flips,
        "mean_w_sat": round(float(np.mean(w)), 4),
    }
    return chal, meta


def _yearly(base: pd.DataFrame, chal: pd.DataFrame) -> list[dict[str, Any]]:
    b = base.copy()
    c = chal.copy()
    b["year"] = pd.to_datetime(b["date"]).dt.year
    c["year"] = pd.to_datetime(c["date"]).dt.year
    rows: list[dict[str, Any]] = []
    for y in sorted(set(b["year"]) & set(c["year"])):
        bb = b[b["year"] == y].reset_index(drop=True)
        cc = c[c["year"] == y].reset_index(drop=True)
        if len(bb) < 20 or len(cc) < 20:
            continue
        bret = float(bb["nav"].iloc[-1] / bb["nav"].iloc[0] - 1.0) * 100
        cret = float(cc["nav"].iloc[-1] / cc["nav"].iloc[0] - 1.0) * 100
        bn = bb["nav"] / float(bb["nav"].iloc[0])
        cn = cc["nav"] / float(cc["nav"].iloc[0])
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
                "winner": "FILL_CARVE" if cret > bret else ("BASE" if cret < bret else "TIE"),
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
        "fill_carve_shaped": bool((not sf_ok) and shaped),
    }


def _verdict(rows: list[dict[str, Any]]) -> str:
    carve = next((r for r in rows if r["id"] == "FILL_CARVE_CLOSE"), None)
    quo = next((r for r in rows if r["id"] == "STATUS_QUO_T1"), None)
    if carve and carve["eval"]["fill_carve_shaped"] and quo and not quo["eval"]["gates"]["tip_clean"]:
        return "FILL_CARVE_CLOSE_ONLY"
    if carve and carve["eval"]["fill_carve_shaped"] and quo and quo["eval"]["hit"]:
        return "BOTH_HIT"
    if carve and carve["eval"]["gates"]["tip_clean"]:
        return "FILL_CARVE_SOFT"
    return "FILL_SIM_BLOCK"


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
    w_close = sat_lead.astype(float).to_numpy()
    w_t1 = sat_lead.shift(1).fillna(False).astype(float).to_numpy()
    w_sat = np.ones(len(comp))

    base_w = _pack(live)
    sat_held = cagr_lift_pp(
        (base_w.get("heldout_2019_plus") or {}).get("cagr"),
        (_pack(sat).get("heldout_2019_plus") or {}).get("cagr"),
    )

    specs = [
        {
            "id": BASE_ID,
            "fam": "ctrl",
            "sf_ok": True,
            "w": None,
            "note": "live Soft-Frozen base (Exact T+1 stack)",
        },
        {
            "id": "FILL_CARVE_CLOSE",
            "fam": "fill_sim",
            "sf_ok": False,
            "w": w_close,
            "note": (
                f"Simulated live fill carve {CARVE_OUT_ID}: tagged Path3 switch "
                "fills same-bar @ reference_close (≡ P3_T0_STATE observe upper bound)"
            ),
        },
        {
            "id": "STATUS_QUO_T1",
            "fam": "fill_sim",
            "sf_ok": True,
            "w": w_t1,
            "note": "No fill carve: Path3 decision day-t, earn from T+1 open (SAT_LEAD.shift(1))",
        },
        {
            "id": "P2_SAT_PURE",
            "fam": "ref",
            "sf_ok": True,
            "w": w_sat,
            "note": "always SAT tip line (SF-legal ref)",
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
        row = {
            "id": bid,
            "fam": spec["fam"],
            "meta": meta,
            "eval": ev,
            "tip": tip,
            "windows": _pack(nav),
        }
        rows.append(row)
        print(json.dumps({"book": bid, "sf_ok": spec["sf_ok"], "eval": ev}, ensure_ascii=False), flush=True)

    carve = next(r for r in rows if r["id"] == "FILL_CARVE_CLOSE")
    quo = next(r for r in rows if r["id"] == "STATUS_QUO_T1")
    gap = {
        "held_cagr_gap_pp": round(
            float(carve["eval"]["held_cagr_lift_pp"] or 0) - float(quo["eval"]["held_cagr_lift_pp"] or 0),
            4,
        ),
        "tip_ytd_gap_pp": round(
            float(carve["eval"]["tip_ytd_cagr_pp"] or 0) - float(quo["eval"]["tip_ytd_cagr_pp"] or 0),
            4,
        ),
        "tip_1y_gap_pp": round(
            float(carve["eval"]["tip_1y_cagr_pp"] or 0) - float(quo["eval"]["tip_1y_cagr_pp"] or 0),
            4,
        ),
        "sealed_cagr_gap_pp": round(
            float((carve["windows"].get("sealed_2023_plus") or {}).get("cagr") or 0) * 100
            - float((quo["windows"].get("sealed_2023_plus") or {}).get("cagr") or 0) * 100,
            4,
        ),
    }
    yearly = _yearly(live, navs["FILL_CARVE_CLOSE"])
    wl = (
        sum(1 for y in yearly if y["winner"] == "FILL_CARVE"),
        sum(1 for y in yearly if y["winner"] == "BASE"),
    )
    verdict = _verdict(rows)
    generated = _utc()

    # Charter (ops SSOT)
    charter_md = "\n".join(
        [
            f"# {CHARTER_ID}",
            "",
            "Date: 2026-09-29",
            "Status: **Stage A — fill-carve simulate** · Soft-Frozen **KEEP** · Path3 observe **KEEP** · "
            "fill flag **OFF** · cutover **BLOCKED** · no live · no broker",
            f"Parents: 0k9r Path3 observe OPEN · carve `{CARVE_OUT_ID}` · fill PREP ballot (DRAFT)",
            f"Register: **{REGISTER}**",
            "",
            "## Question",
            "",
            "若最終 ACCEPT live fill carve-out（Path3 tagged switch 同 bar 以 `reference_close` 成交），"
            "相對維持 Exact T+1（無 carve），paper NAV 模擬效果如何？",
            "",
            "## Method",
            "",
            "- `FILL_CARVE_CLOSE`: SAT_LEAD(day t) 權重當日全額進收益 ≡ observe `P3_T0_STATE` / live MOC close",
            "- `STATUS_QUO_T1`: SAT_LEAD.shift(1) ≡ 決策當日、成交／收益 T+1 open",
            "- Gates: held CAGR / MDD band · tip YTD+1y clean · vs SAT held extra",
            "- 非整本帳 T+0；僅 Path3 COMP↔SAT 切換 carve",
            "",
            "## Non-goals",
            "",
            "- 不翻 `LIVE.live_t0_carve_fin_sat_switch_fill`",
            "- 不接 Path3 order emitter / broker",
            "- 不改 Soft-Frozen clips / CONF α / 全局 Exact T+1",
            "",
            f"Label: `{CHARTER_ID}_2026-09-29__FILL_SIM__NO_LIVE`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{CHARTER_ID}.md", REP / f"{CHARTER_ID}.md", charter_md, kind="charter"
    )
    charter_json = {
        "id": CHARTER_ID,
        "register": REGISTER,
        "carve_out_id": CARVE_OUT_ID,
        "books": [s["id"] for s in specs],
        "soft_frozen_keep": True,
        "path3_observe_keep": True,
        "live_wire": False,
        "fill_flag": False,
        "cutover": "BLOCKED",
    }
    (OPS / f"{CHARTER_ID}.json").write_text(
        json.dumps(charter_json, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    write_repro_pointer(OPS / f"{CHARTER_ID}.json", REP / f"{CHARTER_ID}.json", kind="charter")

    screen = {
        "label": f"{SCREEN_ID}_{generated.replace(':', '').replace('-', '')}",
        "generated_at_utc": generated,
        "charter": CHARTER_ID,
        "register": REGISTER,
        "verdict": verdict,
        "theta": THETA,
        "carve_out_id": CARVE_OUT_ID,
        "mapping": {
            "FILL_CARVE_CLOSE": "live fill allowlist ON + reference_close same-bar ≡ P3_T0_STATE",
            "STATUS_QUO_T1": "fill allowlist OFF / Exact T+1 open earn",
        },
        "gap_carve_minus_t1": gap,
        "fill_carve_yearly_wl": {"carve_wins": wl[0], "base_wins": wl[1]},
        "rows": rows,
        "yearly_fill_carve_vs_base": yearly,
        "soft_frozen_keep": True,
        "path3_observe_keep": True,
        "live_wire": False,
        "fill_flag": False,
    }
    (OUT / "screen.json").write_text(json.dumps(screen, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    md_lines = [
        f"# {SCREEN_ID}",
        "",
        f"Date: 2026-09-29 · generated `{generated}`",
        f"Verdict: **`{verdict}`** · Soft-Frozen KEEP · Path3 observe KEEP · fill flag OFF · no live",
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
        "## Gap (`FILL_CARVE_CLOSE` − `STATUS_QUO_T1`)",
        "",
        f"- held CAGR gap: **{gap['held_cagr_gap_pp']}** pp",
        f"- tip YTD gap: **{gap['tip_ytd_gap_pp']}** pp",
        f"- tip 1y gap: **{gap['tip_1y_gap_pp']}** pp",
        f"- sealed CAGR gap: **{gap['sealed_cagr_gap_pp']}** pp",
        "",
        f"Fill-carve yearly W–L vs live: **{wl[0]}–{wl[1]}**",
        "",
        "Repro: `repro/fin-sat-path3-t0-fill-sim-stagea/`",
        "",
    ]
    screen_md = "\n".join(md_lines) + "\n"
    write_ops_and_repro_pointer(OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", screen_md, kind="screen")
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(screen, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_repro_pointer(OPS / f"{SCREEN_ID}.json", REP / f"{SCREEN_ID}.json", kind="screen")

    sealed_c = carve["windows"].get("sealed_2023_plus") or {}
    sealed_q = quo["windows"].get("sealed_2023_plus") or {}
    sealed_b = (next(r for r in rows if r["id"] == BASE_ID)["windows"].get("sealed_2023_plus") or {})

    decision_md = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: 2026-09-29 · Verdict: **`{verdict}`**",
            "Status: Soft-Frozen **KEEP** · Path3 observe **KEEP** · fill flag **OFF** · "
            "cutover **BLOCKED** · no live · no broker",
            "",
            "## Answer",
            "",
            "模擬「ACCEPT fill carve → Path3 切換單同 bar 以 close／`reference_close` 成交」的回測效果：",
            "",
            f"- **`FILL_CARVE_CLOSE`**: held↑ **{carve['eval']['held_cagr_lift_pp']}** · "
            f"tipY↑ **{carve['eval']['tip_ytd_cagr_pp']}** · tip1y↑ {carve['eval']['tip_1y_cagr_pp']} · "
            f"tipClean={carve['eval']['gates']['tip_clean']} · shaped={carve['eval']['gates']['shaped']}",
            f"- **`STATUS_QUO_T1`（無 carve）**: held↑ {quo['eval']['held_cagr_lift_pp']} · "
            f"tipY↑ **{quo['eval']['tip_ytd_cagr_pp']}** · tipClean={quo['eval']['gates']['tip_clean']}",
            f"- Tip YTD gap（carve − T1）: **{gap['tip_ytd_gap_pp']}** pp",
            "",
            "### Sealed 2023+",
            "",
            f"| Book | CAGR | MDD |",
            f"|---|---:|---:|",
            f"| `CTRL_LIVE_A10` | {sealed_b.get('cagr')} | {sealed_b.get('max_drawdown')} |",
            f"| `FILL_CARVE_CLOSE` | {sealed_c.get('cagr')} | {sealed_c.get('max_drawdown')} |",
            f"| `STATUS_QUO_T1` | {sealed_q.get('cagr')} | {sealed_q.get('max_drawdown')} |",
            "",
            "## Implication",
            "",
            "- 建議路徑若走到 live fill carve（同 bar close），paper 預期 **≈ observe `P3_T0_STATE`**：held + tip 形狀 HIT。",
            "- 若不開 carve、只做 T+1 成交，tip YTD **為負**（與 hybrid／0k9s 同結論）。",
            "- 本 Stage A **不**翻 flag、**不**接下單；僅給 ACCEPT fill 前的效果上限。",
            "- Soft-Frozen／全局 Exact T+1／CONF α **KEEP**；cutover 仍 **BLOCKED**。",
            "",
            "## Yearly `FILL_CARVE_CLOSE` vs live",
            "",
            "| Year | base% | carve% | Δpp | winner |",
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
            f"Screen: `{SCREEN_ID}.md` · Charter: `{CHARTER_ID}.md` · Register **{REGISTER}**",
            "",
            f"Label: `{DECISION_ID}_2026-09-29__{verdict}__NO_LIVE`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{DECISION_ID}.md", REP / f"{DECISION_ID}.md", decision_md, kind="decision pack"
    )
    decision_json = {
        "label": f"{DECISION_ID}_2026-09-29__{verdict}__NO_LIVE",
        "verdict": verdict,
        "register": REGISTER,
        "carve_out_id": CARVE_OUT_ID,
        "gap_carve_minus_t1": gap,
        "fill_carve_close": carve["eval"],
        "status_quo_t1": quo["eval"],
        "sealed": {
            "base": sealed_b,
            "fill_carve_close": sealed_c,
            "status_quo_t1": sealed_q,
        },
        "yearly_wl": {"carve": wl[0], "base": wl[1]},
        "soft_frozen_keep": True,
        "path3_observe_keep": True,
        "live_wire": False,
        "fill_flag": False,
        "cutover": "BLOCKED",
    }
    (OPS / f"{DECISION_ID}.json").write_text(
        json.dumps(decision_json, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    write_repro_pointer(OPS / f"{DECISION_ID}.json", REP / f"{DECISION_ID}.json", kind="decision pack")

    print(
        json.dumps(
            {
                "verdict": verdict,
                "gap": gap,
                "fill_carve": carve["eval"],
                "status_quo_t1": quo["eval"],
                "yearly_wl": {"carve": wl[0], "base": wl[1]},
            },
            ensure_ascii=False,
            indent=2,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
