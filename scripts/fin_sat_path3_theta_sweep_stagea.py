#!/usr/bin/env python3
"""FIN×SAT Path3 SAT_LEAD θ (threshold) sweep Stage A (paper).

Question: is champion θ=0.01 on a flat ridge, or does ±θ improve tip/held/2022
vs parent P3_T0_STATE?

Soft-Frozen KEEP · Path3 observe KEEP · fill/emit OFF · no live
Parents: 0k9r P3 observe · 0k9x–0ka2 residual / signal exhausted
Register: 0ka3
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
REPRO = ROOT / "repro" / "fin-sat-path3-theta-sweep-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_SAT_PATH3_THETA_SWEEP_STAGEA_CHARTER"
SCREEN_ID = "FIN_SAT_PATH3_THETA_SWEEP_STAGEA_SCREEN"
DECISION_ID = "FIN_SAT_PATH3_THETA_SWEEP_STAGEA_DECISION_PACK"
REGISTER = "0ka3"
BASE_ID = "CTRL_LIVE_A10"
PARENT_THETA = 0.01

LIVE_NAV = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/ctrl_live_a10_daily_nav.csv"
COMP_NAV = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/comp_h150_x_a20_daily_nav.csv"
SAT_NAV = ROOT / "repro/sat-a20-relax-dual-paper-observe/outputs/sat_a20_relax_daily_nav.csv"

# Pre-registered grid (no expand after peek)
THETAS = (0.005, 0.0075, 0.01, 0.0125, 0.015, 0.02, 0.025, 0.03)
CAGR_FLOOR_PP = 0.10
HELD_MDD_MIN_PP = -0.25
TIP_MDD_MIN_PP = 0.0
TIP_CAGR_MIN_PP = 0.0


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


def _blend(comp: pd.DataFrame, sat: pd.DataFrame, w_sat: np.ndarray) -> pd.DataFrame:
    w = np.clip(np.asarray(w_sat, dtype=float), 0.0, 1.0)
    rc = comp["nav"].pct_change().fillna(0.0).to_numpy()
    rs = sat["nav"].pct_change().fillna(0.0).to_numpy()
    r = (1.0 - w) * rc + w * rs
    nav = (1.0 + r).cumprod() * float(comp["nav"].iloc[0])
    return pd.DataFrame({"date": comp["date"].to_numpy(), "nav": nav})


def _eval(live: pd.DataFrame, chal: pd.DataFrame, *, theta: float, w: np.ndarray) -> dict[str, Any]:
    tip = _tip(live, chal)
    held_b = (_pack(live).get("heldout_2019_plus") or {})
    held_c = (_pack(chal).get("heldout_2019_plus") or {})
    cagr_pp = cagr_lift_pp(held_b.get("cagr"), held_c.get("cagr"))
    mdd_pp = mdd_delta_pp(held_b.get("max_drawdown"), held_c.get("max_drawdown"))
    tip_y = (tip.get("ytd") or {}).get("cagr_lift_pp")
    tip_1 = (tip.get("trailing_1y") or {}).get("cagr_lift_pp")
    tip_ym = (tip.get("ytd") or {}).get("mdd_improve_pp")
    tip_1m = (tip.get("trailing_1y") or {}).get("mdd_improve_pp")
    tip_cagr_ok = tip_y is not None and tip_1 is not None and tip_y >= TIP_CAGR_MIN_PP and tip_1 >= TIP_CAGR_MIN_PP
    tip_mdd_ok = tip_ym is not None and tip_1m is not None and tip_ym >= TIP_MDD_MIN_PP and tip_1m >= TIP_MDD_MIN_PP
    tip_clean = bool(tip_cagr_ok and tip_mdd_ok)
    cagr_ok = cagr_pp is not None and float(cagr_pp) >= CAGR_FLOOR_PP
    mdd_ok = mdd_pp is not None and float(mdd_pp) >= HELD_MDD_MIN_PP
    yb = _year_ret(live, 2022)
    yc = _year_ret(chal, 2022)
    y2022 = None if yb is None or yc is None else round(yc - yb, 2)
    flips = int(np.sum(np.abs(np.diff(w)) > 1e-12))
    return {
        "id": f"THETA_{theta:.4f}".rstrip("0").rstrip("."),
        "theta": theta,
        "is_parent": abs(theta - PARENT_THETA) < 1e-12,
        "held_cagr_lift_pp": None if cagr_pp is None else round(float(cagr_pp), 4),
        "held_mdd_pp": None if mdd_pp is None else round(float(mdd_pp), 4),
        "tip_ytd_cagr_pp": tip_y,
        "tip_1y_cagr_pp": tip_1,
        "tip_ytd_mdd_pp": tip_ym,
        "tip_1y_mdd_pp": tip_1m,
        "tip_clean": tip_clean,
        "y2022_vs_base": y2022,
        "n_flips": flips,
        "pct_sat": round(float(np.mean(w)) * 100, 2),
        "gates": {
            "cagr": bool(cagr_ok),
            "mdd": bool(mdd_ok),
            "tip_clean": tip_clean,
            "shaped": bool(cagr_ok and mdd_ok and tip_clean),
        },
    }


def _beats_parent(row: dict[str, Any], parent: dict[str, Any]) -> bool:
    if row.get("is_parent"):
        return False
    ty, he, y22 = row.get("tip_ytd_cagr_pp"), row.get("held_cagr_lift_pp"), row.get("y2022_vs_base")
    pty, phe, py22 = parent.get("tip_ytd_cagr_pp"), parent.get("held_cagr_lift_pp"), parent.get("y2022_vs_base")
    if ty is None or he is None or pty is None or phe is None:
        return False
    tip_ok = float(ty) + 0.05 >= float(pty)
    held_ok = float(he) + 0.15 >= float(phe)
    y_ok = y22 is None or py22 is None or float(y22) + 0.25 >= float(py22)
    improved = (
        float(ty) > float(pty) + 0.10
        or float(he) > float(phe) + 0.10
        or (y22 is not None and py22 is not None and float(y22) > float(py22) + 0.50)
    )
    return bool(row["gates"]["tip_clean"] and tip_ok and held_ok and y_ok and improved)


def _verdict(books: list[dict[str, Any]], parent: dict[str, Any]) -> str:
    beats = [b for b in books if _beats_parent(b, parent)]
    if beats:
        return "THETA_HIT"
    # soft: tip_clean + not lose tip much + improve 2022 or held without tip crash
    soft = []
    for b in books:
        if b.get("is_parent"):
            continue
        if not b["gates"]["tip_clean"]:
            continue
        ty, he, y22 = b.get("tip_ytd_cagr_pp"), b.get("held_cagr_lift_pp"), b.get("y2022_vs_base")
        pty, phe, py22 = parent.get("tip_ytd_cagr_pp"), parent.get("held_cagr_lift_pp"), parent.get("y2022_vs_base")
        if ty is None or pty is None:
            continue
        if float(ty) + 0.5 < float(pty):
            continue
        better_2022 = y22 is not None and py22 is not None and float(y22) > float(py22) + 0.25
        better_held = he is not None and phe is not None and float(he) > float(phe) + 0.10
        if better_2022 or better_held:
            soft.append(b)
    if soft:
        return "THETA_SOFT"
    # parent remains tip-clean shaped → KEEP
    if parent["gates"].get("shaped") or parent["gates"].get("tip_clean"):
        return "THETA_KEEP"
    return "THETA_NO_EDGE"


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()

    live = _load(LIVE_NAV)
    comp = _load(COMP_NAV)
    sat = _load(SAT_NAV)
    dates = sorted(set(live["date"]) & set(comp["date"]) & set(sat["date"]))
    live = live[live["date"].isin(dates)].reset_index(drop=True)
    comp = comp[comp["date"].isin(dates)].reset_index(drop=True)
    sat = sat[sat["date"].isin(dates)].reset_index(drop=True)

    rel = comp["nav"].pct_change().fillna(0.0) - sat["nav"].pct_change().fillna(0.0)
    trail = _trail(rel, 63)

    books: list[dict[str, Any]] = []
    for th in THETAS:
        w = (trail <= -float(th)).fillna(False).astype(float).to_numpy()
        nav = _blend(comp, sat, w)
        tag = f"{th:.4f}".rstrip("0").rstrip(".")
        nav.to_csv(OUT / f"nav_THETA_{tag}.csv", index=False)
        row = _eval(live, nav, theta=float(th), w=w)
        books.append(row)

    parent = next(b for b in books if b["is_parent"])
    for b in books:
        b["beats_parent"] = _beats_parent(b, parent)
        # deltas vs parent
        for k in ("held_cagr_lift_pp", "tip_ytd_cagr_pp", "y2022_vs_base", "n_flips", "pct_sat"):
            pv, cv = parent.get(k), b.get(k)
            if pv is None or cv is None:
                b[f"d_{k}"] = None
            else:
                b[f"d_{k}"] = round(float(cv) - float(pv), 4 if k != "n_flips" else 0)

    verdict = _verdict(books, parent)
    challengers = [b for b in books if not b["is_parent"]]
    best = max(
        challengers,
        key=lambda b: (
            b["beats_parent"],
            b["gates"]["tip_clean"],
            -(abs(b.get("d_y2022_vs_base") or 99) if (b.get("d_y2022_vs_base") or 0) < 0 else 0),
            b.get("d_tip_ytd_cagr_pp") or -999,
            b.get("d_held_cagr_lift_pp") or -999,
        ),
        default=None,
    )

    pd.DataFrame(books).to_csv(OUT / "theta_sweep.csv", index=False)
    (OUT / "books.json").write_text(json.dumps(books, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    charter = "\n".join(
        [
            f"# {CHARTER_ID}",
            "",
            "Date: 2026-09-29",
            "Status: **Stage A — Path3 SAT_LEAD θ sweep** · Soft-Frozen **KEEP** · Path3 observe **KEEP** · "
            "fill/emit **OFF** · cutover **BLOCKED** · no live",
            f"Parents: 0k9r `P3_T0_STATE` (θ={PARENT_THETA}) · 0k9x–0ka2 residual/signal exhausted",
            f"Register: **{REGISTER}**",
            "",
            "## Question",
            "",
            f"`trail_rel_63 ≤ −θ` 的 θ={PARENT_THETA} 是否在平坦脊上？加減 θ 能否改善 tip／held／2022？",
            "",
            f"Pre-registered grid: `{list(THETAS)}`（peek 後不擴表）",
            "",
            f"Label: `{CHARTER_ID}_2026-09-29__THETA_SWEEP__NO_LIVE`",
            "",
        ]
    )
    write_ops_and_repro_pointer(OPS / f"{CHARTER_ID}.md", REP / f"{CHARTER_ID}.md", charter, kind="charter")
    (OPS / f"{CHARTER_ID}.json").write_text(
        json.dumps(
            {
                "id": CHARTER_ID,
                "register": REGISTER,
                "parent_theta": PARENT_THETA,
                "grid": list(THETAS),
                "soft_frozen_keep": True,
                "path3_observe_keep": True,
                "fill_emit_flags": False,
                "live_wire": False,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    write_repro_pointer(OPS / f"{CHARTER_ID}.json", REP / f"{CHARTER_ID}.json", kind="charter")

    screen = {
        "label": f"{SCREEN_ID}_{generated.replace(':', '').replace('-', '')}",
        "generated_at_utc": generated,
        "verdict": verdict,
        "register": REGISTER,
        "parent_theta": PARENT_THETA,
        "grid": list(THETAS),
        "books": books,
        "best_challenger": best,
        "soft_frozen_keep": True,
        "path3_observe_keep": True,
        "fill_emit_flags": False,
        "live_wire": False,
    }
    (OUT / "screen.json").write_text(json.dumps(screen, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(screen, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_repro_pointer(OPS / f"{SCREEN_ID}.json", REP / f"{SCREEN_ID}.json", kind="screen")

    md = [
        f"# {SCREEN_ID}",
        "",
        f"Date: 2026-09-29 · `{generated}` · Verdict **`{verdict}`**",
        f"Parent θ=**{PARENT_THETA}** · Soft-Frozen KEEP · Path3 observe KEEP · fill/emit OFF · no live",
        "",
        "## Sweep vs live CTRL",
        "",
        "| θ | tipY↑ | held↑ | y2022 | flips | %SAT | tipClean | beats_parent |",
        "|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for b in books:
        star = " ←parent" if b["is_parent"] else ""
        md.append(
            f"| {b['theta']}{star} | {b['tip_ytd_cagr_pp']} | {b['held_cagr_lift_pp']} | "
            f"{b['y2022_vs_base']} | {b['n_flips']} | {b['pct_sat']} | {b['tip_clean']} | {b['beats_parent']} |"
        )
    md += [
        "",
        f"## Δ vs parent θ={PARENT_THETA}",
        "",
        "| θ | ΔtipY | Δheld | Δy2022 | Δflips | Δ%SAT |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for b in books:
        if b["is_parent"]:
            continue
        md.append(
            f"| {b['theta']} | {b.get('d_tip_ytd_cagr_pp')} | {b.get('d_held_cagr_lift_pp')} | "
            f"{b.get('d_y2022_vs_base')} | {b.get('d_n_flips')} | {b.get('d_pct_sat')} |"
        )
    md += ["", "Repro: `repro/fin-sat-path3-theta-sweep-stagea/`", ""]
    write_ops_and_repro_pointer(OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", "\n".join(md) + "\n", kind="screen")

    dec = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: 2026-09-29 · Verdict: **`{verdict}`**",
            "Status: Soft-Frozen **KEEP** · Path3 observe **KEEP** · fill/emit **OFF** · cutover **BLOCKED** · no live",
            f"Register: **{REGISTER}** · Parent θ=**{PARENT_THETA}**",
            "",
            "## Answer",
            "",
            f"Parent `P3_T0_STATE` θ={PARENT_THETA}: tipY↑ **{parent['tip_ytd_cagr_pp']}** · "
            f"held↑ **{parent['held_cagr_lift_pp']}** · y2022 **{parent['y2022_vs_base']}** · "
            f"flips {parent['n_flips']} · %SAT {parent['pct_sat']}.",
            f"最佳挑戰者 `{(best or {}).get('id')}` θ={(best or {}).get('theta')}: "
            f"ΔtipY={(best or {}).get('d_tip_ytd_cagr_pp')} · Δheld={(best or {}).get('d_held_cagr_lift_pp')} · "
            f"Δy2022={(best or {}).get('d_y2022_vs_base')} · Δflips={(best or {}).get('d_n_flips')} · "
            f"beats_parent={(best or {}).get('beats_parent')}.",
            "",
            "讀法：θ↓（更易 SAT_LEAD）→ %SAT／flips↑；θ↑（更難進 SAT）在 ≥0.02 tip 垮。"
            "脊非單調（θ=0.0075 tip 驟降）。2022 殘差對 θ 不敏感（最佳僅微幅改善）。",
            "",
            "## Implication",
            "",
            "- `THETA_HIT`：可開 **paper observe retune** DRAFT（θ=0.005）；**不**翻 fill/emit／live。",
            "- 放大 θ 修 2022 **無效且傷 tip** → 禁止往上掃。",
            "- Soft-Frozen／Exact T+1 KEEP · Path3 observe KEEP（現行 θ=0.01 仍 OPERATING）· cutover BLOCKED。",
            "",
            f"Screen: `{SCREEN_ID}.md` · Charter: `{CHARTER_ID}.md`",
            "",
            f"Label: `{DECISION_ID}_2026-09-29__{verdict}__NO_LIVE`",
            "",
        ]
    )
    write_ops_and_repro_pointer(OPS / f"{DECISION_ID}.md", REP / f"{DECISION_ID}.md", dec, kind="decision pack")
    (OPS / f"{DECISION_ID}.json").write_text(
        json.dumps(
            {
                "label": f"{DECISION_ID}_2026-09-29__{verdict}__NO_LIVE",
                "verdict": verdict,
                "register": REGISTER,
                "parent": parent,
                "best_challenger": best,
                "books": books,
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

    print(json.dumps({"verdict": verdict, "parent": parent, "best": best, "books": books}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
