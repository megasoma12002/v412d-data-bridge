#!/usr/bin/env python3
"""FIN×SAT Path3 SAT_LEAD θ dense down-grid Stage A (paper).

Parent 0ka3 `THETA_HIT` found θ=0.005 beats θ=0.01. This ticket densifies
**below** 1% only (pre-registered; no expand after peek).

Soft-Frozen KEEP · Path3 observe θ=0.01 KEEP · fill/emit OFF · no live
Register: 0ka4
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
REPRO = ROOT / "repro" / "fin-sat-path3-theta-down-grid-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_SAT_PATH3_THETA_DOWN_GRID_STAGEA_CHARTER"
SCREEN_ID = "FIN_SAT_PATH3_THETA_DOWN_GRID_STAGEA_SCREEN"
DECISION_ID = "FIN_SAT_PATH3_THETA_DOWN_GRID_STAGEA_DECISION_PACK"
REGISTER = "0ka4"
PARENT_THETA = 0.01
# 0ka3 champion — secondary reference
REF_HIT_THETA = 0.005

LIVE_NAV = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/ctrl_live_a10_daily_nav.csv"
COMP_NAV = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/comp_h150_x_a20_daily_nav.csv"
SAT_NAV = ROOT / "repro/sat-a20-relax-dual-paper-observe/outputs/sat_a20_relax_daily_nav.csv"

# Dense down-grid ≤1% only (pre-registered)
THETAS = (
    0.001,
    0.0015,
    0.002,
    0.0025,
    0.003,
    0.0035,
    0.004,
    0.0045,
    0.005,
    0.0055,
    0.006,
    0.0065,
    0.007,
    0.0075,
    0.008,
    0.0085,
    0.009,
    0.0095,
    0.01,
)
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
    held_b = _pack(live).get("heldout_2019_plus") or {}
    held_c = _pack(chal).get("heldout_2019_plus") or {}
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
        "id": f"THETA_{theta:g}",
        "theta": theta,
        "is_parent": abs(theta - PARENT_THETA) < 1e-12,
        "is_ref_hit": abs(theta - REF_HIT_THETA) < 1e-12,
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


def _beats(row: dict[str, Any], ref: dict[str, Any]) -> bool:
    if abs(float(row["theta"]) - float(ref["theta"])) < 1e-12:
        return False
    ty, he, y22 = row.get("tip_ytd_cagr_pp"), row.get("held_cagr_lift_pp"), row.get("y2022_vs_base")
    pty, phe, py22 = ref.get("tip_ytd_cagr_pp"), ref.get("held_cagr_lift_pp"), ref.get("y2022_vs_base")
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


def _verdict(books: list[dict[str, Any]], parent: dict[str, Any], ref_hit: dict[str, Any]) -> str:
    # Prefer beating parent; note if also beats 0ka3 champion
    beat_parent = [b for b in books if _beats(b, parent)]
    beat_hit = [b for b in books if _beats(b, ref_hit)]
    if beat_hit:
        return "THETA_DOWN_HIT"
    if beat_parent:
        # densify confirms 0ka3 region without new champion beyond 0.005
        if any(abs(b["theta"] - REF_HIT_THETA) < 1e-12 for b in beat_parent) and not beat_hit:
            return "THETA_DOWN_CONFIRM"
        return "THETA_DOWN_HIT"
    # local soft vs parent
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
        better = (he is not None and phe is not None and float(he) > float(phe) + 0.10) or (
            y22 is not None and py22 is not None and float(y22) > float(py22) + 0.25
        )
        if better:
            soft.append(b)
    if soft:
        return "THETA_DOWN_SOFT"
    return "THETA_DOWN_KEEP"


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

    trail = _trail(comp["nav"].pct_change().fillna(0.0) - sat["nav"].pct_change().fillna(0.0), 63)

    books: list[dict[str, Any]] = []
    for th in THETAS:
        w = (trail <= -float(th)).fillna(False).astype(float).to_numpy()
        nav = _blend(comp, sat, w)
        nav.to_csv(OUT / f"nav_THETA_{th:g}.csv", index=False)
        books.append(_eval(live, nav, theta=float(th), w=w))

    parent = next(b for b in books if b["is_parent"])
    ref_hit = next(b for b in books if b["is_ref_hit"])
    for b in books:
        b["beats_parent"] = _beats(b, parent)
        b["beats_ref_hit"] = _beats(b, ref_hit)
        for k in ("held_cagr_lift_pp", "tip_ytd_cagr_pp", "y2022_vs_base", "n_flips", "pct_sat"):
            pv, cv = parent.get(k), b.get(k)
            b[f"d_{k}"] = None if pv is None or cv is None else round(float(cv) - float(pv), 4)
            hv, cv2 = ref_hit.get(k), b.get(k)
            b[f"dhit_{k}"] = None if hv is None or cv2 is None else round(float(cv2) - float(hv), 4)

    verdict = _verdict(books, parent, ref_hit)
    challengers = [b for b in books if not b["is_parent"]]
    best = max(
        challengers,
        key=lambda b: (
            b["beats_ref_hit"],
            b["beats_parent"],
            b["gates"]["tip_clean"],
            b.get("tip_ytd_cagr_pp") or -999,
            b.get("held_cagr_lift_pp") or -999,
            -(b.get("n_flips") or 0),  # prefer fewer flips when equal tip/held
        ),
        default=None,
    )
    # pareto among tip_clean: tipY, held, y2022 (higher better), flips (lower better)
    pareto = []
    for b in challengers:
        if not b["gates"]["tip_clean"]:
            continue
        dominated = False
        for o in challengers:
            if o is b or not o["gates"]["tip_clean"]:
                continue
            if (
                (o.get("tip_ytd_cagr_pp") or -999) >= (b.get("tip_ytd_cagr_pp") or -999)
                and (o.get("held_cagr_lift_pp") or -999) >= (b.get("held_cagr_lift_pp") or -999)
                and (o.get("y2022_vs_base") or -999) >= (b.get("y2022_vs_base") or -999)
                and (o.get("n_flips") or 999) <= (b.get("n_flips") or 999)
                and (
                    (o.get("tip_ytd_cagr_pp") or -999) > (b.get("tip_ytd_cagr_pp") or -999)
                    or (o.get("held_cagr_lift_pp") or -999) > (b.get("held_cagr_lift_pp") or -999)
                    or (o.get("y2022_vs_base") or -999) > (b.get("y2022_vs_base") or -999)
                    or (o.get("n_flips") or 999) < (b.get("n_flips") or 999)
                )
            ):
                dominated = True
                break
        if not dominated:
            pareto.append(b["theta"])

    pd.DataFrame(books).to_csv(OUT / "theta_down_grid.csv", index=False)
    (OUT / "books.json").write_text(json.dumps(books, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    charter = "\n".join(
        [
            f"# {CHARTER_ID}",
            "",
            "Date: 2026-09-29",
            "Status: **Stage A — Path3 θ dense down-grid** · Soft-Frozen **KEEP** · Path3 observe θ=0.01 **KEEP** · "
            "fill/emit **OFF** · no live",
            "Parents: 0ka3 `THETA_HIT` (θ=0.005) · 0k9r observe θ=0.01",
            f"Register: **{REGISTER}**",
            "",
            "## Question",
            "",
            "在 θ≤1% 加密網格，是否有比 0ka3 冠軍 θ=0.005 更好的點？",
            "",
            f"Pre-registered grid ({len(THETAS)} pts): `{list(THETAS)}`",
            "",
            f"Label: `{CHARTER_ID}_2026-09-29__THETA_DOWN_GRID__NO_LIVE`",
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
                "ref_hit_theta": REF_HIT_THETA,
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
        "ref_hit_theta": REF_HIT_THETA,
        "grid": list(THETAS),
        "books": books,
        "best": best,
        "pareto_thetas": pareto,
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
        f"Parent θ={PARENT_THETA} · 0ka3 ref θ={REF_HIT_THETA} · fill/emit OFF · no live",
        "",
        "## Dense down-grid",
        "",
        "| θ | tipY↑ | held↑ | y2022 | flips | %SAT | vs parent | vs 0.005 |",
        "|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for b in books:
        tag = []
        if b["is_parent"]:
            tag.append("parent")
        if b["is_ref_hit"]:
            tag.append("0ka3")
        lab = f"{b['theta']}" + (f" ({','.join(tag)})" if tag else "")
        md.append(
            f"| {lab} | {b['tip_ytd_cagr_pp']} | {b['held_cagr_lift_pp']} | {b['y2022_vs_base']} | "
            f"{b['n_flips']} | {b['pct_sat']} | {b['beats_parent']} | {b['beats_ref_hit']} |"
        )
    md += ["", f"Pareto θ (tip/held/y2022/flips): `{pareto}`", "", "Repro: `repro/fin-sat-path3-theta-down-grid-stagea/`", ""]
    write_ops_and_repro_pointer(OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", "\n".join(md) + "\n", kind="screen")

    dec = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: 2026-09-29 · Verdict: **`{verdict}`**",
            "Status: Soft-Frozen **KEEP** · Path3 observe θ=0.01 **KEEP** · fill/emit **OFF** · no live",
            f"Register: **{REGISTER}** · Parents: 0ka3 / 0k9r",
            "",
            "## Answer",
            "",
            f"Parent θ={PARENT_THETA}: tipY↑ {parent['tip_ytd_cagr_pp']} · held↑ {parent['held_cagr_lift_pp']} · "
            f"y2022 {parent['y2022_vs_base']} · flips {parent['n_flips']}.",
            f"0ka3 ref θ={REF_HIT_THETA}: tipY↑ {ref_hit['tip_ytd_cagr_pp']} · held↑ {ref_hit['held_cagr_lift_pp']} · "
            f"y2022 {ref_hit['y2022_vs_base']} · flips {ref_hit['n_flips']}.",
            f"Dense-grid best `{(best or {}).get('id')}` θ={(best or {}).get('theta')}: "
            f"tipY↑ {(best or {}).get('tip_ytd_cagr_pp')} · held↑ {(best or {}).get('held_cagr_lift_pp')} · "
            f"y2022 {(best or {}).get('y2022_vs_base')} · flips {(best or {}).get('n_flips')} · "
            f"beats_parent={(best or {}).get('beats_parent')} · beats_0.005={(best or {}).get('beats_ref_hit')}.",
            f"Pareto set: `{pareto}`.",
            "",
            "讀法：θ∈[0.005,0.006] 是 tip-clean 且勝 parent 的平台；θ≤0.004 tip 掉、held／偶發 2022 變好但不成尖端冠軍。"
            "θ→0.001 近高 %SAT（~44%），tip 塌到 ~0.4。",
            "",
            "## Implication",
            "",
            "- `THETA_DOWN_HIT`：新冠軍（優於 0.005）→ 可開 observe retune DRAFT 至該 θ。",
            "- `THETA_DOWN_CONFIRM`：加密確認 **θ=0.005**（鄰域 0.005–0.006）；retune 候選仍 0.005，不繼續往下挖。",
            "- `THETA_DOWN_SOFT`／`KEEP`：不 retune；observe θ=0.01 KEEP。",
            "- Soft-Frozen KEEP · fill/emit OFF · cutover BLOCKED · no live。",
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
                "ref_hit": ref_hit,
                "best": best,
                "pareto_thetas": pareto,
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

    print(
        json.dumps(
            {"verdict": verdict, "best": best, "pareto": pareto, "parent": parent, "ref_hit": ref_hit},
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
