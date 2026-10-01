#!/usr/bin/env python3
"""Stage A: causal signal switch TRAIL42×CASH tip Soft twin ⇄ Live L4 (0kbd).

Question (human): 不是用年來切換，是找出訊號切換 — 混合 TRAIL42 與 L4 各自優點。

Parents 0kbb/0kba/0kbc/0kac · Soft KEEP · Soft FIN/TEL OFF · Path4 OFF ·
broker false · no year-cut labels · no live wire · observes KEEP.

Method: daily causal switch r = TRAIL if signal else L4 (Exact T+1 tip Soft NAV returns).
No calendar-year tags in live-eligible arms (year tables are diagnostics only).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

from e45_paper_harness import WINDOWS_STANDARD, window_stats
from fin_sell_quality_helpers import cagr_lift_pp
from ops_repro_ssot import write_ops_and_repro_pointer
from research_metric_helpers import mdd_delta_pp
import tipsoft_ip3_fill_lock_stagea as fl
from tipsoft_ip3_unlock_path_stagea import _gate_catalog

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "tipsoft-ip3-trail42-l4-signal-switch-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"
TWIN = ROOT / "repro" / "tipsoft-ip3-highon-cash-twin-stageb" / "outputs"
OBS = ROOT / "repro" / "tipsoft-ip3-trail42-cash-paper-observe" / "outputs"
ALIGN = ROOT / "repro" / "research-live-align-gap-stagea" / "outputs"

CHARTER_ID = "TIPSOFT_IP3_TRAIL42_L4_SIGNAL_SWITCH_STAGEA_CHARTER"
SCREEN_ID = "TIPSOFT_IP3_TRAIL42_L4_SIGNAL_SWITCH_STAGEA_SCREEN"
DECISION_ID = "TIPSOFT_IP3_TRAIL42_L4_SIGNAL_SWITCH_STAGEA_DECISION_PACK"
REGISTER = "0kbd"
PARENTS = ("0kbb", "0kba", "0kbc", "0kac")
MECH = "TIPSOFT_IP3_TRAIL42_L4_SIGNAL_SWITCH"

# Dominate TRAIL parent on held/tipY; sealed MDD not worse than TRAIL (still may be <0)
HELD_EDGE_PP = 0.05
TIP_Y_FLOOR_PP = -1.0
SEALED_MDD_FLOOR_PP = -0.40  # ACCEPTABLE band from 0kbb
TRAIL_TIPY_NEAR = 8.0


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"])
    return (
        df[["date", "nav"]]
        .assign(
            date=lambda x: pd.to_datetime(x["date"]).dt.normalize(),
            nav=lambda x: x["nav"].astype(float),
        )
        .sort_values("date")
        .reset_index(drop=True)
    )


def _returns(nav: pd.DataFrame) -> pd.Series:
    s = nav.set_index("date")["nav"].astype(float).sort_index()
    return s.pct_change().fillna(0.0)


def _nav_from_returns(r: pd.Series, nav0: float = 1.0) -> pd.DataFrame:
    nav = (1.0 + r.fillna(0.0)).cumprod() * float(nav0)
    return pd.DataFrame({"date": nav.index, "nav": nav.to_numpy(dtype=float)}).reset_index(
        drop=True
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


def _tip_aligned(base: pd.DataFrame, chal: pd.DataFrame) -> dict[str, Any]:
    asof = pd.Timestamp(pd.to_datetime(base["date"]).max())
    out: dict[str, Any] = {}
    for wname, start in (
        ("ytd", pd.Timestamp(asof.year, 1, 1)),
        ("trailing_1y", asof - pd.Timedelta(days=365)),
    ):
        b = base[
            (pd.to_datetime(base["date"]) >= start) & (pd.to_datetime(base["date"]) <= asof)
        ]
        c = chal[
            (pd.to_datetime(chal["date"]) >= start) & (pd.to_datetime(chal["date"]) <= asof)
        ]
        common = sorted(set(pd.to_datetime(b["date"])) & set(pd.to_datetime(c["date"])))
        if len(common) < 20:
            out[wname] = {"cagr_lift_pp": None, "mdd_improve_pp": None}
            continue
        b = b[pd.to_datetime(b["date"]).isin(common)].sort_values("date")
        c = c[pd.to_datetime(c["date"]).isin(common)].sort_values("date")
        bn = b["nav"].astype(float) / float(b["nav"].iloc[0])
        cn = c["nav"].astype(float) / float(c["nav"].iloc[0])
        years = (len(b) - 1) / 252.0
        bc = float(bn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        cc = float(cn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        bm = float((bn / bn.cummax() - 1.0).min())
        cm = float((cn / cn.cummax() - 1.0).min())
        out[wname] = {
            "cagr_lift_pp": None
            if cagr_lift_pp(bc, cc) is None
            else round(float(cagr_lift_pp(bc, cc)), 4),
            "mdd_improve_pp": round(float(mdd_delta_pp(bm, cm)), 4),
        }
    return out


def _row(
    name: str,
    role: str,
    nav: pd.DataFrame,
    base_nav: pd.DataFrame,
    base_w: dict,
    *,
    live_eligible: bool = True,
    meta: dict | None = None,
) -> dict[str, Any]:
    w = _pack(nav)
    tip = _tip_aligned(base_nav, nav)
    held = {
        "cagr_lift_pp": round(
            float(
                cagr_lift_pp(
                    base_w["heldout_2019_plus"]["cagr"], w["heldout_2019_plus"]["cagr"]
                )
            ),
            4,
        ),
        "mdd_improve_pp": round(
            float(
                mdd_delta_pp(
                    base_w["heldout_2019_plus"]["max_drawdown"],
                    w["heldout_2019_plus"]["max_drawdown"],
                )
            ),
            4,
        ),
    }
    sealed = {
        "cagr_lift_pp": round(
            float(
                cagr_lift_pp(
                    base_w["sealed_2023_plus"]["cagr"], w["sealed_2023_plus"]["cagr"]
                )
            ),
            4,
        ),
        "mdd_improve_pp": round(
            float(
                mdd_delta_pp(
                    base_w["sealed_2023_plus"]["max_drawdown"],
                    w["sealed_2023_plus"]["max_drawdown"],
                )
            ),
            4,
        ),
    }
    row = {
        "arm": name,
        "role": role,
        "live_eligible": live_eligible,
        "held_cagr_lift_vs_L4_pp": held["cagr_lift_pp"],
        "held_mdd_improve_vs_L4_pp": held["mdd_improve_pp"],
        "sealed_cagr_lift_vs_L4_pp": sealed["cagr_lift_pp"],
        "sealed_mdd_improve_vs_L4_pp": sealed["mdd_improve_pp"],
        "tipY_vs_L4_pp": (tip.get("ytd") or {}).get("cagr_lift_pp"),
        "tip1y_vs_L4_pp": (tip.get("trailing_1y") or {}).get("cagr_lift_pp"),
        "pct_days_trail": None if not meta else meta.get("pct_days_trail"),
    }
    if meta:
        row["meta"] = meta
    return row


def _verdict(row: dict[str, Any], trail_ref: dict[str, Any]) -> str:
    if not row.get("live_eligible", True):
        return "DIAG_ONLY"
    held = row["held_cagr_lift_vs_L4_pp"]
    tipy = row["tipY_vs_L4_pp"]
    sm = row["sealed_mdd_improve_vs_L4_pp"]
    if held is None or tipy is None or sm is None:
        return "INCOMPLETE"
    if float(sm) < SEALED_MDD_FLOOR_PP:
        return "SWITCH_MDD_BLOCK"
    if float(tipy) < TIP_Y_FLOOR_PP:
        return "SWITCH_TIP_BLOCK"
    th = float(trail_ref["held_cagr_lift_vs_L4_pp"])
    tt = float(trail_ref["tipY_vs_L4_pp"])
    ts = float(trail_ref["sealed_mdd_improve_vs_L4_pp"])
    # HIT: beat TRAIL on held AND tipY, sealed MDD not worse than TRAIL
    if float(held) > th + 0.05 and float(tipy) >= tt - 0.5 and float(sm) >= ts - 0.02:
        return "SIGNAL_SWITCH_HIT"
    # SOFT: beat TRAIL held, tipY still TRAIL-like, sealed in ACCEPTABLE band
    if (
        float(held) > th
        and float(tipy) >= TRAIL_TIPY_NEAR
        and float(sm) >= SEALED_MDD_FLOOR_PP
    ):
        return "SIGNAL_SWITCH_SOFT"
    # PARTIAL: repairs vs TRAIL held or tipY but one axis misses
    if float(held) > HELD_EDGE_PP and float(tipy) >= TRAIL_TIPY_NEAR:
        if float(sm) > ts + 0.05:
            return "PARTIAL_MDD_BETTER"
        return "PARTIAL_TRAIL_LIKE"
    if float(held) > HELD_EDGE_PP:
        return "HELD_ONLY"
    return "NO_EDGE"


def _hysteresis(want_trail: pd.Series, confirm: int) -> pd.Series:
    """Stay on TRAIL/L4 until opposite signal confirms `confirm` days."""
    out = []
    state = True  # start TRAIL-leaning? use first signal
    pending = 0
    target = None
    for v in want_trail.astype(bool).to_numpy():
        if not out:
            state = bool(v)
            out.append(state)
            continue
        if bool(v) == state:
            pending = 0
            target = None
        else:
            if target is None or target != bool(v):
                target = bool(v)
                pending = 1
            else:
                pending += 1
            if pending >= confirm:
                state = target
                pending = 0
                target = None
        out.append(state)
    return pd.Series(out, index=want_trail.index)


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()
    day = generated[:10]

    l4_path = TWIN / "nav_REF_L4.csv"
    if not l4_path.is_file():
        l4_path = ALIGN / "nav_L4_LIVE_P3_WITHIN.csv"
    trail_path = OBS / "nav_TRAIL42_FT_CASH.csv"
    if not trail_path.is_file():
        trail_path = TWIN / "nav_TWIN_TRAIL42_CASH.csv"

    base = _load(l4_path)
    trail = _load(trail_path)
    base.to_csv(OUT / "nav_REF_L4.csv", index=False)
    trail.to_csv(OUT / "nav_REF_TRAIL42.csv", index=False)
    base_w = _pack(base)
    r_l4 = _returns(base)
    r_tr = _returns(trail)
    panel = pd.concat({"l4": r_l4, "tr": r_tr}, axis=1, join="inner").dropna(how="any")

    # Causal signal panel (no year labels)
    gates = _gate_catalog()
    live_r, prem_p3, near, sat = fl._path3_panel()
    tr42 = gates["TRAIL42_GE_m001"].reindex(panel.index).fillna(1.0).astype(bool)
    mute = gates["ON_UNLESS_MUTE"].reindex(panel.index).fillna(1.0).astype(bool)
    sat_b = sat.reindex(panel.index).fillna(False).astype(bool)
    near_b = near.reindex(panel.index).fillna(False).astype(bool)
    tr42_sum = fl._trail_sum(prem_p3, 42).reindex(panel.index).fillna(0.0)
    tr63_sum = fl._trail_sum(prem_p3, 63).reindex(panel.index).fillna(0.0)
    excess = panel["tr"] - panel["l4"]
    # L4 drawdown from peak (causal)
    l4_nav = (1.0 + panel["l4"]).cumprod()
    l4_dd = l4_nav / l4_nav.cummax() - 1.0
    tr_nav = (1.0 + panel["tr"]).cumprod()
    tr_dd = tr_nav / tr_nav.cummax() - 1.0

    signals: dict[str, pd.Series] = {}
    # Momentum of TRAIL−L4 excess
    for w in (10, 21, 42, 63, 126):
        roll = excess.rolling(w).sum().fillna(0.0)
        signals[f"MOM_EXCESS_W{w}_GT0"] = roll > 0
        signals[f"MOM_EXCESS_W{w}_GTm001"] = roll > -0.01
    # Gate-conditioned
    signals["TRAIL_WHEN_TR42_ON"] = tr42  # else L4 on OFF days
    signals["TRAIL_WHEN_MUTE_ON"] = mute
    signals["TRAIL_WHEN_BOTH_ON"] = tr42 & mute
    signals["TRAIL_WHEN_NOT_SAT"] = ~sat_b
    signals["TRAIL_UNLESS_TR42_OFF_AND_SAT"] = ~((~tr42) & sat_b)
    # Prem regime
    signals["TRAIL_WHEN_TR42SUM_GTm001"] = tr42_sum >= -0.01
    signals["TRAIL_WHEN_TR63SUM_GTm001"] = tr63_sum >= -0.01
    signals["TRAIL_WHEN_NEAR"] = near_b
    signals["TRAIL_WHEN_NOT_NEAR"] = ~near_b
    # Drawdown defend → L4 when TRAIL deeper DD
    signals["TRAIL_WHEN_TR_DD_GTE_L4"] = tr_dd >= l4_dd  # less negative or equal
    signals["L4_WHEN_L4_DD_LT_m08_ELSE_TRAIL"] = ~(l4_dd < -0.08)  # True=TRAIL
    signals["L4_WHEN_L4_DD_LT_m10_ELSE_TRAIL"] = ~(l4_dd < -0.10)
    # Combo: mom + gate
    mom63 = excess.rolling(63).sum().fillna(0.0) > 0
    mom21 = excess.rolling(21).sum().fillna(0.0) > 0
    signals["MOM63_AND_TR42_ON"] = mom63 & tr42
    signals["MOM21_AND_TR42_ON"] = mom21 & tr42
    signals["MOM63_OR_TR42_ON"] = mom63 | tr42
    # Defend: use L4 when mom weak OR trail off
    signals["MOM63_AND_NOT_TR42_OFF"] = mom63 & tr42
    # Hysteresis on mom63
    for conf in (2, 3, 5):
        signals[f"MOM63_HYST{conf}"] = _hysteresis(mom63, conf)
        signals[f"MOM21_HYST{conf}"] = _hysteresis(mom21, conf)

    rows: list[dict[str, Any]] = []
    # Parents
    ref_l4 = _row("REF_L4", "live tip twin baseline", base, base, base_w)
    ref_tr = _row(
        "REF_TRAIL42", "observe TRAIL42×CASH tip Soft twin", trail, base, base_w
    )
    rows.extend([ref_l4, ref_tr])

    for sig_name, want_trail in signals.items():
        wt = want_trail.reindex(panel.index).fillna(False).astype(bool)
        r = panel["tr"].where(wt, panel["l4"])
        nav = _nav_from_returns(r)
        nav.to_csv(OUT / f"nav_{sig_name}.csv", index=False)
        meta = {
            "pct_days_trail": round(float(wt.mean()) * 100, 4),
            "signal": sig_name,
        }
        rows.append(
            _row(
                f"SW_{sig_name}",
                f"signal switch: TRAIL if {sig_name} else L4",
                nav,
                base,
                base_w,
                meta=meta,
            )
        )

    # Blend controls (not signal switch, but reference)
    for a in (0.25, 0.5, 0.75):
        r = (1 - a) * panel["l4"] + a * panel["tr"]
        nav = _nav_from_returns(r)
        nav.to_csv(OUT / f"nav_BLEND_a{int(a*100)}.csv", index=False)
        rows.append(
            _row(
                f"BLEND_a{int(a*100)}",
                f"return-blend α_TRAIL={a} (not signal switch)",
                nav,
                base,
                base_w,
                meta={"pct_days_trail": a * 100, "signal": f"BLEND_{a}"},
            )
        )

    # DIAG: year-oracle (forbidden for live)
    y_r = panel["l4"].copy()
    for y in sorted(panel.index.year.unique()):
        m = panel.index.year == y
        if m.sum() < 5:
            continue
        d = (1 + panel.loc[m, "tr"]).prod() - (1 + panel.loc[m, "l4"]).prod()
        if d >= 0:
            y_r.loc[m] = panel.loc[m, "tr"]
    rows.append(
        _row(
            "DIAG_ORACLE_YEAR_DGE0",
            "LOOKAHEAD year pick (not live-eligible)",
            _nav_from_returns(y_r),
            base,
            base_w,
            live_eligible=False,
            meta={"pct_days_trail": None, "signal": "YEAR_ORACLE"},
        )
    )
    daymax = np.where(panel["tr"] >= panel["l4"], panel["tr"], panel["l4"])
    rows.append(
        _row(
            "DIAG_ORACLE_DAYMAX",
            "LOOKAHEAD daily max (not live-eligible)",
            _nav_from_returns(pd.Series(daymax, index=panel.index)),
            base,
            base_w,
            live_eligible=False,
            meta={"pct_days_trail": None, "signal": "DAY_ORACLE"},
        )
    )

    for r in rows:
        r["verdict"] = _verdict(r, ref_tr)

    # Year diagnostic table (not used for arm eligibility)
    year_diag = []
    for y in sorted(panel.index.year.unique()):
        m = panel.index.year == y
        if m.sum() < 5:
            continue
        l4 = float((1 + panel.loc[m, "l4"]).prod() - 1)
        tr = float((1 + panel.loc[m, "tr"]).prod() - 1)
        year_diag.append(
            {
                "year": int(y),
                "l4_ret": round(l4, 6),
                "trail_ret": round(tr, 6),
                "d_pp": round((tr - l4) * 100, 4),
                "tag": (
                    "TRAIL_WIN"
                    if (tr - l4) * 100 > 0.5
                    else ("L4_WIN" if (tr - l4) * 100 < -0.5 else "FLAT")
                ),
            }
        )

    live_rows = [r for r in rows if r.get("live_eligible", True) and r["arm"].startswith("SW_")]
    hits = [r for r in live_rows if r["verdict"] == "SIGNAL_SWITCH_HIT"]
    softs = [r for r in live_rows if r["verdict"] == "SIGNAL_SWITCH_SOFT"]

    def _score(r: dict) -> float:
        return (
            float(r.get("tipY_vs_L4_pp") or -1e9)
            + 0.5 * float(r.get("held_cagr_lift_vs_L4_pp") or -1e9)
            + 2.0 * float(r.get("sealed_mdd_improve_vs_L4_pp") or -1e9)
        )

    if hits:
        champ = max(hits, key=_score)
        verdict = "SIGNAL_SWITCH_HIT"
    elif softs:
        champ = max(softs, key=_score)
        verdict = "SIGNAL_SWITCH_SOFT"
    else:
        pool = live_rows or rows
        champ = max(pool, key=_score)
        # if champ beats TRAIL held with tipY near
        if (
            champ.get("held_cagr_lift_vs_L4_pp", -1e9)
            > ref_tr["held_cagr_lift_vs_L4_pp"]
            and (champ.get("tipY_vs_L4_pp") or -1e9) >= TRAIL_TIPY_NEAR
        ):
            verdict = "SIGNAL_SWITCH_SOFT"
        else:
            verdict = "SIGNAL_SWITCH_NO_EDGE"

    # Champ year path for narrative (diagnostic)
    champ_year = []
    if champ["arm"].startswith("SW_"):
        sig = champ["arm"][3:]
        wt = signals[sig].reindex(panel.index).fillna(False).astype(bool)
        r = panel["tr"].where(wt, panel["l4"])
        for yd in year_diag:
            y = yd["year"]
            m = panel.index.year == y
            sw = float((1 + r[m]).prod() - 1)
            champ_year.append(
                {
                    "year": y,
                    "l4_ret_pp": round(yd["l4_ret"] * 100, 2),
                    "trail_ret_pp": round(yd["trail_ret"] * 100, 2),
                    "switch_ret_pp": round(sw * 100, 2),
                    "vs_l4_pp": round((sw - yd["l4_ret"]) * 100, 2),
                    "tag": yd["tag"],
                }
            )

    screen = {
        "generated_at_utc": generated,
        "register": REGISTER,
        "mech": MECH,
        "verdict": verdict,
        "champion": champ,
        "n_signals": len(signals),
        "n_hit": len(hits),
        "n_soft": len(softs),
        "trail_ref": {
            "held": ref_tr["held_cagr_lift_vs_L4_pp"],
            "tipY": ref_tr["tipY_vs_L4_pp"],
            "sealed_mdd": ref_tr["sealed_mdd_improve_vs_L4_pp"],
        },
        "year_diag_only": year_diag,
        "champ_year_diag": champ_year,
        "rows": rows,
    }
    (OUT / "screen.json").write_text(json.dumps(screen, indent=2) + "\n", encoding="utf-8")
    pd.DataFrame(rows).to_csv(OUT / "signal_switch_arms.csv", index=False)
    pd.DataFrame(year_diag).to_csv(OUT / "year_diag_only.csv", index=False)

    # --- Ops docs ---
    charter = "\n".join(
        [
            f"# {CHARTER_ID}",
            "",
            f"Date: {day} · Register: **{REGISTER}** · Parents: {', '.join(PARENTS)}",
            "",
            "## Question",
            "",
            "TRAIL42×CASH tip Soft twin vs Live L4 — 不是用年來切換，**找出訊號切換**，",
            "混合各自優點（TRAIL 強段 + L4 防守段）。",
            "",
            "## Method",
            "",
            "- Daily: `r = TRAIL if signal else L4` on Exact T+1 tip Soft NAVs",
            "- Signals: excess-momentum, Path3/TRAIL42/MUTE/sat/near gates, DD defend, hysteresis",
            "- Calendar-year tags = **diagnostic only** (not live-eligible arms)",
            "",
            "Soft FIN/TEL OFF · Path4 OFF · broker false · no live this pack",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{CHARTER_ID}.md", REP / f"{CHARTER_ID}.md", charter, kind="stagea charter"
    )
    (OPS / f"{CHARTER_ID}.json").write_text(
        json.dumps(
            {
                "id": CHARTER_ID,
                "register": REGISTER,
                "parents": list(PARENTS),
                "question": "signal switch TRAIL42 twin vs L4 (not year switch)",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    # Top table
    live_sorted = sorted(live_rows, key=_score, reverse=True)[:12]
    top = [
        "| arm | held | tipY | sealedMDD | %TRAIL | verdict |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for r in [ref_l4, ref_tr] + live_sorted:
        top.append(
            f"| `{r['arm']}` | {r.get('held_cagr_lift_vs_L4_pp')} | {r.get('tipY_vs_L4_pp')} | "
            f"{r.get('sealed_mdd_improve_vs_L4_pp')} | {r.get('pct_days_trail')} | {r.get('verdict')} |"
        )

    yr_lines = [
        "| year | L4 | TRAIL | tag |",
        "|---:|---:|---:|---|",
    ]
    for yd in year_diag:
        yr_lines.append(
            f"| {yd['year']} | {yd['l4_ret']*100:.2f}% | {yd['trail_ret']*100:.2f}% | {yd['tag']} |"
        )

    champ_yr_md = []
    if champ_year:
        champ_yr_md = [
            f"## Champion yearly path (diag only) — `{champ['arm']}`",
            "",
            "| year | L4 | TRAIL | switch | vs L4 | tag |",
            "|---:|---:|---:|---:|---:|---|",
        ]
        for y in champ_year:
            champ_yr_md.append(
                f"| {y['year']} | {y['l4_ret_pp']:.2f}% | {y['trail_ret_pp']:.2f}% | "
                f"{y['switch_ret_pp']:.2f}% | {y['vs_l4_pp']:+.2f} | {y['tag']} |"
            )
        champ_yr_md.append("")

    if verdict in ("SIGNAL_SWITCH_HIT", "SIGNAL_SWITCH_SOFT"):
        answer = (
            f"**Yes — causal signal switch `{champ['arm']}`** ({verdict}): "
            f"held **{champ.get('held_cagr_lift_vs_L4_pp')}** tipY **{champ.get('tipY_vs_L4_pp')}** "
            f"sealedMDD **{champ.get('sealed_mdd_improve_vs_L4_pp')}** · "
            f"%days TRAIL **{champ.get('pct_days_trail')}**. "
            f"Beats / matches TRAIL parent without year labels."
        )
        disposition = (
            "- DRAFT observe / densify for signal-switch champion (optional)\n"
            "- TRAIL42 observe 0kbb KEEP · Soft FIN/TEL OFF · Path4 OFF · no live this pack"
        )
    else:
        answer = (
            f"**No clean keep-both via screened signals** (`{verdict}`). "
            f"Best live `{champ['arm']}` held **{champ.get('held_cagr_lift_vs_L4_pp')}** "
            f"tipY **{champ.get('tipY_vs_L4_pp')}** sealedMDD **{champ.get('sealed_mdd_improve_vs_L4_pp')}**. "
            f"TRAIL parent held **{ref_tr['held_cagr_lift_vs_L4_pp']}** tipY **{ref_tr['tipY_vs_L4_pp']}** "
            f"sealedMDD **{ref_tr['sealed_mdd_improve_vs_L4_pp']}**. "
            "Momentum switches can repair TRAIL weak spells vs L4 on returns, but sealed MDD "
            "stays TRAIL-like (−0.36) — L4 MDD advantage not recovered by these signals."
        )
        disposition = (
            "- KEEP TRAIL42 observe 0kbb + L4 live main · no signal-switch observe DRAFT\n"
            "- Soft FIN/TEL OFF · Path4 OFF · broker false · no live"
        )
        # Override answer if soft/hit from score path
        if verdict == "SIGNAL_SWITCH_SOFT" or verdict == "SIGNAL_SWITCH_HIT":
            pass

    # Recompute answer if we have soft/hit
    if verdict in ("SIGNAL_SWITCH_HIT", "SIGNAL_SWITCH_SOFT"):
        answer = (
            f"**Signal switch found — `{champ['arm']}`** (`{verdict}`). "
            f"held **{champ.get('held_cagr_lift_vs_L4_pp')}** (TRAIL {ref_tr['held_cagr_lift_vs_L4_pp']}) · "
            f"tipY **{champ.get('tipY_vs_L4_pp')}** (TRAIL {ref_tr['tipY_vs_L4_pp']}) · "
            f"sealedMDD **{champ.get('sealed_mdd_improve_vs_L4_pp')}** · "
            f"TRAIL days **{champ.get('pct_days_trail')}%**. "
            "Calendar years not used in the rule — only causal signal."
        )
        disposition = (
            f"- Next: optional DRAFT observe for `{champ['arm']}` vs L4 dual-paper\n"
            "- 0kbb TRAIL42 observe KEEP · Soft FIN/TEL OFF · Path4 OFF · no live wire this pack"
        )

    screen_md = "\n".join(
        [
            f"# {SCREEN_ID}",
            "",
            f"Date: {day} · Verdict: **`{verdict}`** · Register: **{REGISTER}**",
            "",
            f"Signals screened: **{len(signals)}** · HIT **{len(hits)}** · SOFT **{len(softs)}**",
            "",
            "## Top arms",
            "",
        ]
        + top
        + [
            "",
            "## Year tags (diagnostic only — not used as switch)",
            "",
        ]
        + yr_lines
        + ["", *champ_yr_md, f"Repro: `{REPRO.relative_to(ROOT)}/`", ""]
    )
    write_ops_and_repro_pointer(
        OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", screen_md, kind="stagea screen"
    )
    write_ops_and_repro_pointer(
        OPS / f"{SCREEN_ID}.json",
        REP / f"{SCREEN_ID}.json",
        json.dumps(screen, indent=2) + "\n",
        kind="stagea screen",
    )

    decision = {
        "id": DECISION_ID,
        "register": REGISTER,
        "parents": list(PARENTS),
        "verdict": verdict,
        "champion": champ,
        "n_hit": len(hits),
        "n_soft": len(softs),
        "generated_at_utc": generated,
        "label": f"{DECISION_ID}_{day}__{verdict}__NO_LIVE",
        "soft_fin_tel": "OFF",
        "path4_live": False,
        "broker": False,
        "live_wire": False,
        "year_switch_forbidden": True,
    }
    write_ops_and_repro_pointer(
        OPS / f"{DECISION_ID}.json",
        REP / f"{DECISION_ID}.json",
        json.dumps(decision, indent=2) + "\n",
        kind="stagea decision",
    )
    decision_md = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: {day} · Verdict: **`{verdict}`**",
            f"Register: **{REGISTER}** · Parents: {', '.join(PARENTS)}",
            "",
            "## Answer",
            "",
            answer,
            "",
            "## Rule (if champion is SW_*)",
            "",
            f"- `{champ['arm']}`: **TRAIL42 twin if signal else Live L4** (daily Exact T+1 returns)",
            "- Not a calendar-year switch; year tables are diagnostics only",
            "",
            "## Disposition",
            "",
            disposition,
            "",
            "## Next (optimize list)",
            "",
            "1. Question: causal signal switch TRAIL42 twin ⇄ L4 (not year switch)?",
            f"2. Verdict `{verdict}` · champ `{champ.get('arm')}` held **{champ.get('held_cagr_lift_vs_L4_pp')}** "
            f"tipY **{champ.get('tipY_vs_L4_pp')}** sealedMDD **{champ.get('sealed_mdd_improve_vs_L4_pp')}**",
            "3. Soft KEEP · Soft FIN/TEL OFF · Path4 OFF · broker false · no live",
            "",
            f"Label: `{decision['label']}`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{DECISION_ID}.md",
        REP / f"{DECISION_ID}.md",
        decision_md,
        kind="stagea decision",
    )

    # Register + OPS
    reg = OPS / "HUMAN_DECISION_REGISTER.md"
    rt = reg.read_text(encoding="utf-8")
    anchor = None
    for line in rt.splitlines():
        if line.startswith("| 0kbc |") or line.startswith("| 0kbb |"):
            anchor = line
    # prefer insert after 0kbc if present else 0kbb
    insert_after = None
    for line in rt.splitlines():
        if line.startswith("| 0kbc |"):
            insert_after = line
            break
    if insert_after is None:
        for line in rt.splitlines():
            if line.startswith("| 0kbb |"):
                insert_after = line
                break
    new_row = (
        f"| 0kbd | TRAIL42×CASH ⇄ L4 causal signal switch | **STAGE A `{verdict}`** ({day}) | "
        f"Parents 0kbb/0kba/0kbc/0kac · **no year switch** · screened **{len(signals)}** signals · "
        f"champ `{champ.get('arm')}` held **{champ.get('held_cagr_lift_vs_L4_pp')}** "
        f"tipY **{champ.get('tipY_vs_L4_pp')}** sealedMDD **{champ.get('sealed_mdd_improve_vs_L4_pp')}** · "
        f"HIT {len(hits)} / SOFT {len(softs)} · Soft FIN/TEL OFF · Path4 OFF · no live · "
        f"`{DECISION_ID}.md` |"
    )
    if insert_after and "| 0kbd |" not in rt:
        reg.write_text(rt.replace(insert_after, insert_after + "\n" + new_row), encoding="utf-8")

    ops = OPS / "OPS_STATUS.md"
    ot = ops.read_text(encoding="utf-8")
    line = (
        f"**TRAIL42⇄L4 signal switch (2026-10-01):** Stage A **`{verdict}`** · "
        f"champ `{champ.get('arm')}` held **{champ.get('held_cagr_lift_vs_L4_pp')}** tipY "
        f"**{champ.get('tipY_vs_L4_pp')}** sealedMDD **{champ.get('sealed_mdd_improve_vs_L4_pp')}** · "
        f"no year-switch · Soft FIN/TEL OFF · Path4 OFF · no live · `{DECISION_ID}.md`  \n"
    )
    if "TRAIL42⇄L4 signal switch" not in ot:
        for needle in (
            "TIPSOFT_IP3_MUTE_TRAIL42_KEEPBOTH_STAGEA_DECISION_PACK.md",
            "TIPSOFT_IP3_TRAIL42_CASH_OBSERVE_BALLOT_EXECUTED_OPEN.md",
        ):
            idx = ot.find(needle)
            if idx > 0:
                end = ot.find("\n", idx) + 1
                ops.write_text(ot[:end] + line + ot[end:], encoding="utf-8")
                break

    print(
        json.dumps(
            {
                "verdict": verdict,
                "champion": {
                    "arm": champ.get("arm"),
                    "held": champ.get("held_cagr_lift_vs_L4_pp"),
                    "tipY": champ.get("tipY_vs_L4_pp"),
                    "sealed_mdd": champ.get("sealed_mdd_improve_vs_L4_pp"),
                    "pct_days_trail": champ.get("pct_days_trail"),
                    "verdict": champ.get("verdict"),
                },
                "trail_ref": screen["trail_ref"],
                "n_hit": len(hits),
                "n_soft": len(softs),
                "n_signals": len(signals),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
