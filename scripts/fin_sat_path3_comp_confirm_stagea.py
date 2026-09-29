#!/usr/bin/env python3
"""FIN×SAT Path3 COMP-enter confirm / min-stay Stage A (paper).

Parent finding (0k9x COMP_STAY_MISS): 2022 sole P3 loss vs BASE from wrong COMP
stays — not May–Jun whipsaw. This Stage A probes harder COMP entry:
  - confirm D days of non-SAT_LEAD before allowing COMP
  - min-stay on SAT before COMP entry allowed
  - light combos

Soft-Frozen KEEP · Path3 observe KEEP · fill/emit flags OFF · no live.
Register: 0k9y
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
REPRO = ROOT / "repro" / "fin-sat-path3-comp-confirm-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_SAT_PATH3_COMP_CONFIRM_STAGEA_CHARTER"
SCREEN_ID = "FIN_SAT_PATH3_COMP_CONFIRM_STAGEA_SCREEN"
DECISION_ID = "FIN_SAT_PATH3_COMP_CONFIRM_STAGEA_DECISION_PACK"
REGISTER = "0k9y"
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


def _trail(r: pd.Series, n: int = 63) -> pd.Series:
    return (1.0 + r).rolling(n, min_periods=n).apply(lambda x: float(np.prod(x) - 1.0), raw=True)


def _blend(comp: pd.DataFrame, sat: pd.DataFrame, w_sat: np.ndarray) -> tuple[pd.DataFrame, dict[str, Any]]:
    rc = comp["nav"].pct_change().fillna(0.0).to_numpy()
    rs = sat["nav"].pct_change().fillna(0.0).to_numpy()
    r = (1.0 - w_sat) * rc + w_sat * rs
    nav = (1.0 + r).cumprod() * float(comp["nav"].iloc[0])
    chal = pd.DataFrame({"date": comp["date"].to_numpy(), "nav": nav})
    flips = int(np.sum(np.abs(np.diff(w_sat)) > 1e-12))
    return chal, {
        "pct_days_sat": round(float(np.mean(w_sat)) * 100, 2),
        "n_flips": flips,
        "mean_w_sat": round(float(np.mean(w_sat)), 4),
    }


def _year_ret(nav: pd.DataFrame, year: int = 2022) -> float | None:
    d = nav.copy()
    d["year"] = pd.to_datetime(d["date"]).dt.year
    g = d[d["year"] == year].reset_index(drop=True)
    if len(g) < 20:
        return None
    return round(float(g["nav"].iloc[-1] / g["nav"].iloc[0] - 1.0) * 100.0, 2)


def apply_comp_confirm(raw_sat_lead: np.ndarray, confirm_d: int) -> np.ndarray:
    """Harder COMP entry: need confirm_d consecutive days of NOT sat_lead.

    SAT entry (sat_lead True) remains same-day. Held book: 1=SAT, 0=COMP.
    """
    n = len(raw_sat_lead)
    w = np.zeros(n, dtype=float)
    # start COMP until first SAT lead
    non_lead_run = 0
    for i in range(n):
        want_sat = bool(raw_sat_lead[i])
        if want_sat:
            w[i] = 1.0
            non_lead_run = 0
            continue
        # want COMP
        non_lead_run += 1
        if i == 0:
            w[i] = 0.0
            continue
        if w[i - 1] >= 0.5:
            # currently on SAT — only leave after confirm_d non-lead days
            w[i] = 0.0 if non_lead_run >= confirm_d else 1.0
        else:
            w[i] = 0.0
    return w


def apply_sat_min_stay(raw_sat_lead: np.ndarray, min_stay: int) -> np.ndarray:
    """After entering SAT, forbid COMP for min_stay days."""
    n = len(raw_sat_lead)
    w = np.zeros(n, dtype=float)
    sat_age = 0
    for i in range(n):
        want_sat = bool(raw_sat_lead[i])
        if i == 0:
            w[i] = 1.0 if want_sat else 0.0
            sat_age = 1 if w[i] >= 0.5 else 0
            continue
        on_sat = w[i - 1] >= 0.5
        if want_sat:
            w[i] = 1.0
            sat_age = sat_age + 1 if on_sat else 1
        else:
            if on_sat and sat_age < min_stay:
                w[i] = 1.0
                sat_age += 1
            else:
                w[i] = 0.0
                sat_age = 0
    return w


def apply_combo(raw_sat_lead: np.ndarray, confirm_d: int, min_stay: int) -> np.ndarray:
    """Min-stay first on raw, then confirm filter for COMP exits."""
    # Build with min-stay against raw desire, then additionally require confirm
    # when leaving SAT: use confirm on the raw signal while respecting min-stay.
    n = len(raw_sat_lead)
    w = np.zeros(n, dtype=float)
    sat_age = 0
    non_lead_run = 0
    for i in range(n):
        want_sat = bool(raw_sat_lead[i])
        if want_sat:
            non_lead_run = 0
            w[i] = 1.0
            sat_age = sat_age + 1 if (i > 0 and w[i - 1] >= 0.5) else 1
            continue
        non_lead_run += 1
        if i == 0:
            w[i] = 0.0
            sat_age = 0
            continue
        on_sat = w[i - 1] >= 0.5
        if on_sat:
            if sat_age < min_stay or non_lead_run < confirm_d:
                w[i] = 1.0
                sat_age += 1
            else:
                w[i] = 0.0
                sat_age = 0
        else:
            w[i] = 0.0
            sat_age = 0
    return w


def _eval(
    base_w: dict[str, Any],
    chal_w: dict[str, Any],
    tip: dict[str, Any],
    *,
    fam: str,
    sat_held_cagr: float | None,
    sf_ok: bool,
    y2022_ret: float | None,
    y2022_base: float | None,
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
    y2022_gap = None
    if y2022_ret is not None and y2022_base is not None:
        y2022_gap = round(float(y2022_ret) - float(y2022_base), 2)
    y2022_ok = y2022_gap is not None and y2022_gap >= 0.0
    tip_cagr_s = 0.0 if tip_ytd_cagr is None else float(np.clip(tip_ytd_cagr, -5.0, 5.0))
    held_s = 0.0 if cagr_pp is None else float(np.clip(cagr_pp, -2.0, 5.0))
    mdd_s = 0.0 if mdd_pp is None else float(np.clip(mdd_pp, -1.0, 1.0))
    y_s = 0.0 if y2022_gap is None else float(np.clip(y2022_gap, -2.0, 2.0))
    score = round(1.5 * tip_cagr_s + (1.0 if tip_mdd_ok else 0.0) + held_s + 0.5 * mdd_s + 0.5 * y_s, 4)
    return {
        "held_cagr_lift_pp": None if cagr_pp is None else round(float(cagr_pp), 4),
        "held_mdd_pp": None if mdd_pp is None else round(float(mdd_pp), 4),
        "held_abs_mdd": None if abs_mdd is None else round(float(abs_mdd), 6),
        "tip_ytd_cagr_pp": tip_ytd_cagr,
        "tip_1y_cagr_pp": tip_1y_cagr,
        "tip_ytd_mdd_pp": tip_ytd_mdd,
        "tip_1y_mdd_pp": tip_1y_mdd,
        "y2022_ret_pct": y2022_ret,
        "y2022_vs_base_pp": y2022_gap,
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
            "y2022_nonneg": bool(y2022_ok),
        },
        "score": score,
        "hit": bool(sf_ok and shaped and y2022_ok),
        "path_shaped": bool((not sf_ok) and shaped),
        "path_hit_2022": bool((not sf_ok) and shaped and y2022_ok),
    }


def _verdict(rows: list[dict[str, Any]]) -> str:
    probes = [r for r in rows if r["id"] not in (BASE_ID, "P3_T0_STATE")]
    p3 = next((r for r in rows if r["id"] == "P3_T0_STATE"), None)
    hits = [r for r in probes if r["eval"]["path_hit_2022"]]
    if hits:
        best = max(hits, key=lambda r: r["eval"]["score"])
        # must not destroy tip vs P3 too badly
        if p3 and (best["eval"]["tip_ytd_cagr_pp"] or -99) + 0.5 < (p3["eval"]["tip_ytd_cagr_pp"] or 0):
            return "COMP_CONFIRM_SOFT"
        return "COMP_CONFIRM_HIT"
    soft = [
        r
        for r in probes
        if r["eval"]["gates"]["y2022_nonneg"] and r["eval"]["gates"]["tip_clean"]
    ]
    if soft:
        return "COMP_CONFIRM_SOFT"
    y_ok = [r for r in probes if r["eval"]["gates"]["y2022_nonneg"]]
    if y_ok and not any(r["eval"]["gates"]["tip_clean"] for r in y_ok):
        return "TIP_BLOCK"
    if any(r["eval"]["gates"]["y2022_nonneg"] for r in probes):
        return "COMP_CONFIRM_PARTIAL"
    return "COMP_CONFIRM_NO_EDGE"


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
    sat_lead = (trail <= -THETA).fillna(False).astype(bool).to_numpy()

    base_w = _pack(live)
    y2022_base = _year_ret(live, 2022)
    sat_held = cagr_lift_pp(
        (base_w.get("heldout_2019_plus") or {}).get("cagr"),
        (_pack(sat).get("heldout_2019_plus") or {}).get("cagr"),
    )

    specs: list[dict[str, Any]] = [
        {"id": BASE_ID, "fam": "ctrl", "sf_ok": True, "w": None, "note": "live Soft-Frozen base"},
        {
            "id": "P3_T0_STATE",
            "fam": "path_ref",
            "sf_ok": False,
            "w": sat_lead.astype(float),
            "note": "raw same-bar SAT_LEAD (observe upper bound)",
        },
    ]
    for d in (1, 2, 3, 5):
        specs.append(
            {
                "id": f"COMP_CONFIRM_D{d}",
                "fam": "confirm",
                "sf_ok": False,
                "w": apply_comp_confirm(sat_lead, d),
                "note": f"COMP entry needs {d} consecutive non-SAT_LEAD days",
            }
        )
    for s in (5, 10, 21):
        specs.append(
            {
                "id": f"SAT_MINSTAY_{s}",
                "fam": "minstay",
                "sf_ok": False,
                "w": apply_sat_min_stay(sat_lead, s),
                "note": f"after SAT entry, block COMP for {s} sessions",
            }
        )
    for d, s in ((2, 10), (3, 10), (2, 21), (3, 21)):
        specs.append(
            {
                "id": f"COMBO_D{d}_S{s}",
                "fam": "combo",
                "sf_ok": False,
                "w": apply_combo(sat_lead, d, s),
                "note": f"confirm D{d} + SAT min-stay {s}",
            }
        )

    rows: list[dict[str, Any]] = []
    for spec in specs:
        bid = spec["id"]
        print(f"{bid} ...", flush=True)
        if spec["w"] is None:
            nav = live.copy()
            meta = {"pct_days_sat": 0.0, "n_flips": 0, "mean_w_sat": 0.0}
        else:
            nav, meta = _blend(comp, sat, np.asarray(spec["w"], dtype=float))
        meta["note"] = spec["note"]
        nav.to_csv(OUT / f"nav_{bid}.csv", index=False)
        y2022 = 0.0 if bid == BASE_ID else _year_ret(nav, 2022)
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
            y2022_ret=y2022_base if bid == BASE_ID else y2022,
            y2022_base=y2022_base,
        )
        rows.append(
            {
                "id": bid,
                "fam": spec["fam"],
                "meta": meta,
                "eval": ev,
                "tip": tip,
                "windows": _pack(nav),
            }
        )
        print(
            json.dumps(
                {
                    "book": bid,
                    "y2022": ev["y2022_ret_pct"],
                    "y2022_gap": ev["y2022_vs_base_pp"],
                    "held": ev["held_cagr_lift_pp"],
                    "tipY": ev["tip_ytd_cagr_pp"],
                    "shaped": ev["gates"]["shaped"],
                    "score": ev["score"],
                },
                ensure_ascii=False,
            ),
            flush=True,
        )

    verdict = _verdict(rows)
    generated = _utc()
    p3 = next(r for r in rows if r["id"] == "P3_T0_STATE")
    probes = [r for r in rows if r["fam"] in ("confirm", "minstay", "combo")]
    best_probe = max(probes, key=lambda r: r["eval"]["score"])
    best_y2022 = max(probes, key=lambda r: (r["eval"]["y2022_vs_base_pp"] is not None, r["eval"]["y2022_vs_base_pp"] or -999))

    charter_md = "\n".join(
        [
            f"# {CHARTER_ID}",
            "",
            "Date: 2026-09-29",
            "Status: **Stage A — COMP enter confirm / SAT min-stay** · Soft-Frozen **KEEP** · "
            "Path3 observe **KEEP** · fill/emit **OFF** · cutover **BLOCKED** · no live",
            "Parents: 0k9r Path3 observe · 0k9v fill-sim · 0k9x `COMP_STAY_MISS` (2022 wrong COMP stays)",
            f"Register: **{REGISTER}**",
            "",
            "## Question",
            "",
            "能否用 **COMP 進場 confirm（連續非 SAT_LEAD）** 或 **SAT 最短停留** 修 2022 P3−BASE −0.75，"
            "且不傷 held／tip 形狀？",
            "",
            "## Probes",
            "",
            "- `COMP_CONFIRM_D{1,2,3,5}`",
            "- `SAT_MINSTAY_{5,10,21}`",
            "- `COMBO_D{2,3}_S{10,21}`",
            "- Refs: `CTRL_LIVE_A10` · `P3_T0_STATE`",
            "",
            "## Non-goals",
            "",
            "- 不關 Path3 observe · 不翻 fill/emit · 不改 Soft-Frozen / CONF α",
            "",
            f"Label: `{CHARTER_ID}_2026-09-29__COMP_CONFIRM__NO_LIVE`",
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
                "cutover": "BLOCKED",
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
        "theta": THETA,
        "y2022_base_ret_pct": y2022_base,
        "best_probe_by_score": best_probe["id"],
        "best_probe_by_y2022": best_y2022["id"],
        "rows": rows,
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
        "## Head-to-head",
        "",
        "| Book | fam | held↑ | tipY↑ | tip1y↑ | tipClean | shaped | y2022% | y2022−BASE | flips | %SAT | score |",
        "|---|---|---:|---:|---:|---|---|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        e = r["eval"]
        md.append(
            f"| `{r['id']}` | {r['fam']} | {e['held_cagr_lift_pp']} | {e['tip_ytd_cagr_pp']} | "
            f"{e['tip_1y_cagr_pp']} | {e['gates']['tip_clean']} | {e['gates']['shaped']} | "
            f"{e['y2022_ret_pct']} | {e['y2022_vs_base_pp']} | {r['meta']['n_flips']} | "
            f"{r['meta']['pct_days_sat']} | {e['score']} |"
        )
    md += [
        "",
        f"Best by score: `{best_probe['id']}` · Best 2022 gap: `{best_y2022['id']}`",
        "",
        "Repro: `repro/fin-sat-path3-comp-confirm-stagea/`",
        "",
    ]
    write_ops_and_repro_pointer(OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", "\n".join(md) + "\n", kind="screen")

    bp = best_probe["eval"]
    by = best_y2022["eval"]
    decision_md = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: 2026-09-29 · Verdict: **`{verdict}`**",
            "Status: Soft-Frozen **KEEP** · Path3 observe **KEEP** · fill/emit **OFF** · "
            "cutover **BLOCKED** · no live",
            "",
            "## Answer",
            "",
            "Paper 探 COMP 進場 confirm／SAT 最短停留，對照 raw `P3_T0_STATE`：",
            "",
            f"- **`P3_T0_STATE`**: held↑ {p3['eval']['held_cagr_lift_pp']} · tipY↑ {p3['eval']['tip_ytd_cagr_pp']} · "
            f"y2022 {p3['eval']['y2022_ret_pct']}% (vs BASE {p3['eval']['y2022_vs_base_pp']})",
            f"- **Best score `{best_probe['id']}`**: held↑ {bp['held_cagr_lift_pp']} · tipY↑ {bp['tip_ytd_cagr_pp']} · "
            f"y2022 {bp['y2022_ret_pct']}% ({bp['y2022_vs_base_pp']}) · shaped={bp['gates']['shaped']}",
            f"- **Best 2022 `{best_y2022['id']}`**: y2022 {by['y2022_ret_pct']}% ({by['y2022_vs_base_pp']}) · "
            f"tipY↑ {by['tip_ytd_cagr_pp']} · shaped={by['gates']['shaped']}",
            "",
            "## Implication",
            "",
            "- Path3 observe **KEEP OPEN**（不關）",
            "- fill/emit flags **KEEP OFF**",
            "- Soft-Frozen／Exact T+1／CONF α **KEEP**；cutover **BLOCKED**",
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
                "p3": p3["eval"],
                "best_probe": {"id": best_probe["id"], "eval": bp},
                "best_y2022": {"id": best_y2022["id"], "eval": by},
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
            {
                "verdict": verdict,
                "best_probe": best_probe["id"],
                "best_y2022": best_y2022["id"],
                "p3_y2022_gap": p3["eval"]["y2022_vs_base_pp"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
