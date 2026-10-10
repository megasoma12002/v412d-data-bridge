#!/usr/bin/env python3
"""2020 crisis / short-crash overlay SANDBOX Stage A (0kbg).

SOAK-SAFE · PARALLEL paper research — **not** tip Soft Stage A for promote.

Question: on live-twin / L4 Path3 WITHIN (or BASE_LIVE_FUSE_COOL) NAV returns,
can offline overlays inspired by general crisis frameworks improve **2020 MDD**
(esp. Mar 2020 cliff) without destroying held CAGR?

Arms (synthetic exposure on daily returns · Exact T+1 lag-1 causal):
1. Vol targeting — scale by target/realized vol (20d/63d); high-vol floor 0.3–0.4
2. MA200 filter — 0050 below MA200 → force cash / zero equity
3. Account MDD throttle — from peak, DD≤−10% size×0.5; DD≤−15% halt risk
4. Small threshold grid + Mar2020 window metrics separate from full-year 2020
5. Optional light combo of best single arms

Hard constraints:
- NO_LIVE · no tip apply · no Soft FIN/TEL ACCEPT · no Path4 · no broker
- no year-oracle / yearmix commit
- does **not** reopen 0kb2 residual paper stacks as observe mainline
- does **not** unlock soak freeze · does **not** recommend LIVE wire
- Label: **SANDBOX / PARALLEL** (vs 0kb4 defend/FUSE knives — different family)

Repro: ``PYTHONPATH=scripts python3 scripts/tipsoft_ip3_y2020_crisis_sandbox_stagea.py``
"""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from e45_paper_harness import window_stats
from ops_repro_ssot import write_ops_and_repro_pointer, write_repro_pointer
from research_metric_helpers import mdd_delta_pp
from stagea_screen_helpers import (
    load_nav_csv as _load_nav,
    nav_from_returns as _nav_from_returns,
    pack_nav_windows as _pack,
    returns_from_nav as _returns,
    tip_lift as _tip,
    utc_now_z as _utc,
    window_delta as _delta,
)

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "tipsoft-ip3-y2020-crisis-sandbox-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

ALIGN = ROOT / "repro" / "research-live-align-gap-stagea" / "outputs"
LIVESTACK = ROOT / "repro" / "fin-sat-path3-path4-livestack-twin-stageb" / "outputs"
PX_0050 = ROOT / "data" / "telecom_0050_complete" / "0050_2010_latest_ohlcv.csv"

CHARTER_ID = "TIPSOFT_IP3_Y2020_CRISIS_SANDBOX_STAGEA_CHARTER"
SCREEN_ID = "TIPSOFT_IP3_Y2020_CRISIS_SANDBOX_STAGEA_SCREEN"
DECISION_ID = "TIPSOFT_IP3_Y2020_CRISIS_SANDBOX_STAGEA_DECISION_PACK"
REGISTER = "0kbg"
PARENTS = ("0kbf", "0kb4", "0kb2")
MECH = "TIPSOFT_IP3_Y2020_CRISIS_SANDBOX"
LABEL_TAG = "SANDBOX_PARALLEL"

BASE_ID = "L4_LIVE_P3_WITHIN"
ALT_BASE_ID = "BASE_LIVE_FUSE_COOL"
SEALED_MDD_FLOOR_PP = -0.25
TIP_Y_FLOOR_PP = -1.0
HELD_CAGR_FLOOR_PP = 0.10
Y2020_MDD_IMPROVE_FLOOR_PP = 0.50
MAR2020_MDD_IMPROVE_FLOOR_PP = 1.00
MAR2020_START = date(2020, 2, 20)
MAR2020_END = date(2020, 3, 23)
Y2020_START = date(2020, 1, 1)
Y2020_END = date(2020, 12, 31)


def _ann_vol(r: pd.Series, win: int) -> pd.Series:
    """Lag-1 causal realized vol (annualized)."""
    return r.shift(1).rolling(int(win), min_periods=max(5, int(win) // 3)).std() * np.sqrt(252.0)


def _load_0050_close(idx: pd.DatetimeIndex) -> pd.Series:
    px = pd.read_csv(PX_0050, parse_dates=["date"])
    px["date"] = pd.to_datetime(px["date"]).dt.normalize()
    col = "adjusted_close" if "adjusted_close" in px.columns else "close"
    s = px.set_index("date")[col].astype(float).sort_index()
    return s.reindex(idx).ffill()


def _window_mdd(nav: pd.DataFrame, start: date, end: date, *, min_days: int = 10) -> float | None:
    st = window_stats(nav, start, end, min_days=min_days)
    mdd = st.get("max_drawdown")
    return None if mdd is None else float(mdd)


def _apply_exposure(base_r: pd.Series, exposure: pd.Series) -> pd.Series:
    e = exposure.reindex(base_r.index).fillna(1.0).clip(0.0, 1.0)
    return (e * base_r).astype(float)


def _vol_target_exposure(
    base_r: pd.Series,
    *,
    win: int,
    target: float,
    floor: float,
) -> pd.Series:
    vol = _ann_vol(base_r, win).replace(0.0, np.nan)
    raw = (float(target) / vol).clip(lower=float(floor), upper=1.0).fillna(1.0)
    return raw.rename("exposure")


def _ma200_exposure(px: pd.Series, *, cash_level: float = 0.0) -> pd.Series:
    """Lag-1: below MA200 → cash_level; else 1.0."""
    ma = px.rolling(200, min_periods=100).mean()
    # Exact T+1: decide with yesterday's close vs yesterday's MA
    below = px.shift(1) < ma.shift(1)
    return pd.Series(np.where(below.fillna(False), float(cash_level), 1.0), index=px.index)


def _mdd_throttle_returns(
    base_r: pd.Series,
    base_exposure: pd.Series | None = None,
    *,
    dd10: float = -0.10,
    dd15: float = -0.15,
    scale10: float = 0.5,
    halt_level: float = 0.0,
) -> tuple[pd.Series, pd.Series]:
    """Path-dependent account-MDD throttle (Exact T+1: DD from prior NAV)."""
    n = len(base_r)
    be = (
        np.ones(n)
        if base_exposure is None
        else base_exposure.reindex(base_r.index).fillna(1.0).to_numpy(dtype=float)
    )
    out_r = np.zeros(n)
    out_e = np.ones(n)
    nav = 1.0
    peak = 1.0
    for i in range(n):
        dd = nav / peak - 1.0
        e = float(be[i])
        if dd <= float(dd15):
            e = float(halt_level)
        elif dd <= float(dd10):
            e = e * float(scale10)
        e = float(np.clip(e, 0.0, 1.0))
        out_e[i] = e
        out_r[i] = e * float(base_r.iloc[i])
        nav *= 1.0 + out_r[i]
        if nav > peak:
            peak = nav
    idx = base_r.index
    return pd.Series(out_r, index=idx), pd.Series(out_e, index=idx)


def _arm_verdict(
    *,
    held: float | None,
    sealed: float | None,
    tip_y: float | None,
    y20_mdd_imp: float | None,
    mar_mdd_imp: float | None,
) -> str:
    if held is None or sealed is None:
        return "INCOMPLETE"
    sealed_ok = float(sealed) >= SEALED_MDD_FLOOR_PP
    tip_ok = tip_y is None or float(tip_y) >= TIP_Y_FLOOR_PP
    held_ok = float(held) >= HELD_CAGR_FLOOR_PP
    y20_ok = y20_mdd_imp is not None and float(y20_mdd_imp) >= Y2020_MDD_IMPROVE_FLOOR_PP
    mar_ok = mar_mdd_imp is not None and float(mar_mdd_imp) >= MAR2020_MDD_IMPROVE_FLOOR_PP
    mdd_ok = bool(y20_ok or mar_ok)
    if not sealed_ok:
        return "MDD_BLOCK"
    if tip_y is not None and float(tip_y) < TIP_Y_FLOOR_PP:
        return "TIP_BLOCK"
    if held_ok and mdd_ok and sealed_ok and tip_ok:
        return "HIT"
    if mdd_ok and sealed_ok and tip_ok and float(held) > 0.02:
        return "SOFT"
    if mdd_ok and not held_ok:
        return "MDD_ONLY"
    if held_ok and not mdd_ok:
        return "HELD_BLOCK"
    if float(held) < -0.05:
        return "HELD_DESTROY"
    return "NO_EDGE"


def _patch_register(verdict: str, champ: dict[str, Any] | None, day: str) -> None:
    reg = OPS / "HUMAN_DECISION_REGISTER.md"
    rt = reg.read_text(encoding="utf-8")
    c = champ or {}
    new_row = (
        f"| 0kbg | 2020 crisis overlay SANDBOX (vol/MA200/MDD) | "
        f"**STAGE A `{verdict}`** ({day}) | "
        f"Parents 0kbf/0kb4/0kb2 · **SANDBOX/PARALLEL** · Exact T+1 synthetic exposure · "
        f"champ `{c.get('arm')}` held **{c.get('held_vs_base')}** · "
        f"y2020 MDD↑ **{c.get('y2020_mdd_improve_pp')}** · "
        f"Mar2020 MDD↑ **{c.get('mar2020_mdd_improve_pp')}** · "
        f"sealed **{c.get('sealed_vs_base')}** · vs 0kb4 defend knives (different family) · "
        f"**does not unlock soak** · Soft KEEP · Path4 OFF · no live · "
        f"`{DECISION_ID}.md` |"
    )
    lines = rt.splitlines()
    out: list[str] = []
    replaced = False
    for line in lines:
        if line.startswith("| 0kbg |"):
            out.append(new_row)
            replaced = True
        else:
            out.append(line)
    if not replaced:
        row_0kbf = None
        for i, line in enumerate(out):
            if line.startswith("| 0kbf |"):
                row_0kbf = i
                break
        if row_0kbf is not None:
            out.insert(row_0kbf + 1, new_row)
    reg.write_text("\n".join(out) + "\n", encoding="utf-8")


def _patch_ops_status(verdict: str, champ: dict[str, Any] | None, day: str) -> None:
    ops = OPS / "OPS_STATUS.md"
    ot = ops.read_text(encoding="utf-8")
    c = champ or {}
    line = (
        f"**Y2020 crisis sandbox (SANDBOX/PARALLEL {day}):** Stage A **`{verdict}`** · "
        f"register **0kbg** · champ `{c.get('arm')}` held **{c.get('held_vs_base')}** · "
        f"y2020 MDD↑ **{c.get('y2020_mdd_improve_pp')}** · "
        f"Mar2020 MDD↑ **{c.get('mar2020_mdd_improve_pp')}** · "
        f"vs 0kb4 `IP3_Y2020_DEFEND_NO_EDGE` (different family) · "
        f"**does not unlock soak freeze** · Soft KEEP · Path4 OFF · no live · "
        f"`{DECISION_ID}.md`  "
    )
    ot2, n = re.subn(
        r"\*\*Y2020 crisis sandbox \(SANDBOX/PARALLEL [^)]+\):\*\*.*",
        line,
        ot,
        count=1,
    )
    if n:
        ops.write_text(ot2, encoding="utf-8")
        return
    needle = "DD_SWITCH soak gate (2026-10-03 cadence):"
    idx = ot.find(needle)
    if idx < 0:
        needle = "2020 defend/off-peak knife"
        idx = ot.find(needle)
    if idx >= 0:
        end = ot.find("\n", idx) + 1
        ops.write_text(ot[:end] + line + "\n" + ot[end:], encoding="utf-8")


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()
    day = generated[:10]

    # Prefer align-gap L4; fall back to livestack twin
    l4_path = ALIGN / "nav_L4_LIVE_P3_WITHIN.csv"
    if not l4_path.exists():
        l4_path = LIVESTACK / "nav_LIVE_P3_WITHIN.csv"
    base_nav = _load_nav(l4_path)
    alt_nav = _load_nav(LIVESTACK / "nav_BASE_LIVE_FUSE_COOL.csv")
    nav0 = float(base_nav["nav"].iloc[0])

    base_r = _returns(base_nav)
    alt_r = _returns(alt_nav).reindex(base_r.index).fillna(0.0)
    px = _load_0050_close(base_r.index)

    base_w = _pack(base_nav)
    base_y20_mdd = _window_mdd(base_nav, Y2020_START, Y2020_END)
    base_mar_mdd = _window_mdd(base_nav, MAR2020_START, MAR2020_END, min_days=10)

    arms: dict[str, tuple[str, pd.Series]] = {
        "REF_BASE_L4": ("REF", base_r),
        "REF_ALT_L3_FUSE_COOL": ("REF", alt_r),
    }

    # --- Vol targeting grid ---
    for win in (20, 63):
        for target in (0.10, 0.12, 0.14, 0.16):
            for floor in (0.30, 0.40):
                name = f"VOL_W{win}_T{str(target).replace('.', '')}_F{str(floor).replace('.', '')}"
                exp = _vol_target_exposure(base_r, win=win, target=target, floor=floor)
                arms[name] = ("VOL", _apply_exposure(base_r, exp))

    # --- MA200 filter ---
    for cash in (0.0, 0.25):
        name = f"MA200_CASH{str(cash).replace('.', '')}"
        exp = _ma200_exposure(px, cash_level=cash)
        arms[name] = ("MA200", _apply_exposure(base_r, exp))

    # --- Account MDD throttle ---
    for dd10, dd15 in ((-0.08, -0.12), (-0.10, -0.15), (-0.12, -0.18)):
        for scale10 in (0.5, 0.4):
            tag = (
                f"MDD_D{str(abs(dd10)).replace('.', '')}"
                f"_H{str(abs(dd15)).replace('.', '')}"
                f"_S{str(scale10).replace('.', '')}"
            )
            r, _ = _mdd_throttle_returns(
                base_r, None, dd10=dd10, dd15=dd15, scale10=scale10, halt_level=0.0
            )
            arms[tag] = ("MDD", r)

    # --- Light combos (vol × MA200; MA200 × MDD; vol × MDD) ---
    vol_seed = _vol_target_exposure(base_r, win=20, target=0.12, floor=0.30)
    ma_seed = _ma200_exposure(px, cash_level=0.0)
    for name, be in (
        ("COMBO_VOL20_T012_F03_x_MA200", vol_seed * ma_seed),
        ("COMBO_MA200_x_VOL63_T014_F04", ma_seed * _vol_target_exposure(base_r, win=63, target=0.14, floor=0.40)),
    ):
        arms[name] = ("COMBO", _apply_exposure(base_r, be))

    for dd10, dd15 in ((-0.10, -0.15),):
        r, _ = _mdd_throttle_returns(
            base_r, ma_seed, dd10=dd10, dd15=dd15, scale10=0.5, halt_level=0.0
        )
        arms["COMBO_MA200_x_MDD10_15"] = ("COMBO", r)
        r2, _ = _mdd_throttle_returns(
            base_r, vol_seed * ma_seed, dd10=dd10, dd15=dd15, scale10=0.5, halt_level=0.0
        )
        arms["COMBO_VOL_MA_x_MDD10_15"] = ("COMBO", r2)

    rows: list[dict[str, Any]] = []
    arms_nav: dict[str, pd.DataFrame] = {BASE_ID: base_nav, ALT_BASE_ID: alt_nav}
    base_nav.to_csv(OUT / f"nav_{BASE_ID}.csv", index=False)
    alt_nav.to_csv(OUT / f"nav_{ALT_BASE_ID}.csv", index=False)

    for name, (fam, r) in arms.items():
        r = r.reindex(base_r.index).fillna(0.0)
        nav = _nav_from_returns(r, nav0)
        arms_nav[name] = nav
        chal_w = _pack(nav)
        d_base = _delta(base_w, chal_w)
        tip = _tip(base_nav, nav)
        y20_mdd = _window_mdd(nav, Y2020_START, Y2020_END)
        mar_mdd = _window_mdd(nav, MAR2020_START, MAR2020_END, min_days=10)
        y20_imp = (
            None
            if base_y20_mdd is None or y20_mdd is None
            else round(float(mdd_delta_pp(base_y20_mdd, y20_mdd)), 4)
        )
        mar_imp = (
            None
            if base_mar_mdd is None or mar_mdd is None
            else round(float(mdd_delta_pp(base_mar_mdd, mar_mdd)), 4)
        )
        held = d_base["heldout_2019_plus"]["cagr_lift_pp"]
        sealed = d_base["sealed_2023_plus"]["mdd_improve_pp"]
        tip_y = (tip.get("ytd") or {}).get("cagr_lift_pp")
        full_cagr = d_base["full"]["cagr_lift_pp"]
        verd = _arm_verdict(
            held=held,
            sealed=sealed,
            tip_y=tip_y,
            y20_mdd_imp=y20_imp,
            mar_mdd_imp=mar_imp,
        )
        # mean exposure ≈ E[r_overlay / r_base] on non-zero base days
        nz = base_r.abs() > 1e-12
        mean_exp = (
            float((r[nz] / base_r[nz]).clip(-0.01, 1.5).mean()) if int(nz.sum()) else 1.0
        )
        rows.append(
            {
                "arm": name,
                "family": fam,
                "verdict": verd,
                "held_vs_base": held,
                "full_cagr_vs_base": full_cagr,
                "sealed_vs_base": sealed,
                "tipY_vs_base": tip_y,
                "y2020_mdd": None if y20_mdd is None else round(float(y20_mdd), 6),
                "y2020_mdd_improve_pp": y20_imp,
                "mar2020_mdd": None if mar_mdd is None else round(float(mar_mdd), 6),
                "mar2020_mdd_improve_pp": mar_imp,
                "mean_exposure": round(mean_exp, 4),
                "is_ref": fam == "REF",
                "hit_clear": verd == "HIT",
                "mdd_help": bool(
                    (y20_imp is not None and y20_imp >= Y2020_MDD_IMPROVE_FLOOR_PP)
                    or (mar_imp is not None and mar_imp >= MAR2020_MDD_IMPROVE_FLOOR_PP)
                ),
                "held_ok": held is not None and float(held) >= HELD_CAGR_FLOOR_PP,
                "sealed_ok": sealed is not None and float(sealed) >= SEALED_MDD_FLOOR_PP,
            }
        )

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "arms_y2020_crisis_sandbox.csv", index=False)
    mech = df[~df.is_ref].copy()
    by_fam = (
        mech.groupby("family")
        .agg(
            n=("arm", "count"),
            n_hit=("hit_clear", "sum"),
            n_mdd_help=("mdd_help", "sum"),
            n_held_ok=("held_ok", "sum"),
            max_held=("held_vs_base", "max"),
            max_y20_mdd_imp=("y2020_mdd_improve_pp", "max"),
            max_mar_mdd_imp=("mar2020_mdd_improve_pp", "max"),
            max_sealed=("sealed_vs_base", "max"),
        )
        .reset_index()
    )
    by_fam.to_csv(OUT / "family_summary.csv", index=False)

    ranked = mech.sort_values(
        by=[
            "hit_clear",
            "held_ok",
            "mdd_help",
            "held_vs_base",
            "mar2020_mdd_improve_pp",
            "y2020_mdd_improve_pp",
            "sealed_vs_base",
        ],
        ascending=[False, False, False, False, False, False, False],
    )
    top = ranked.head(25)
    top.to_csv(OUT / "top_arms.csv", index=False)
    hits = mech[mech.hit_clear]
    hits.to_csv(OUT / "hits.csv", index=False)
    mdd_only = mech[mech.verdict == "MDD_ONLY"]
    mdd_only.to_csv(OUT / "mdd_only.csv", index=False)

    hits_n = int(hits.shape[0])
    soft_n = int((mech.verdict == "SOFT").sum())
    mdd_only_n = int(mdd_only.shape[0])
    held_block_n = int((mech.verdict == "HELD_BLOCK").sum())
    mdd_block_n = int((mech.verdict == "MDD_BLOCK").sum())

    if hits_n > 0:
        crow = hits.sort_values(
            by=["held_vs_base", "mar2020_mdd_improve_pp", "y2020_mdd_improve_pp"],
            ascending=[False, False, False],
        ).iloc[0]
        verdict = "IP3_Y2020_CRISIS_SANDBOX_HIT"
    elif soft_n > 0:
        crow = mech[mech.verdict == "SOFT"].sort_values(
            by=["held_vs_base", "mar2020_mdd_improve_pp"], ascending=[False, False]
        ).iloc[0]
        verdict = "IP3_Y2020_CRISIS_SANDBOX_SOFT"
    elif mdd_only_n > 0:
        # Prefer least held damage among arms that clear MDD floors (still not HIT).
        crow = mdd_only.sort_values(
            by=["held_vs_base", "mar2020_mdd_improve_pp", "y2020_mdd_improve_pp"],
            ascending=[False, False, False],
        ).iloc[0]
        verdict = "IP3_Y2020_CRISIS_SANDBOX_MDD_ONLY"
    elif held_block_n > 0:
        crow = mech[mech.verdict == "HELD_BLOCK"].sort_values(
            by=["held_vs_base"], ascending=[False]
        ).iloc[0]
        verdict = "IP3_Y2020_CRISIS_SANDBOX_HELD_BLOCK"
    else:
        crow = ranked.iloc[0] if len(ranked) else None
        verdict = "IP3_Y2020_CRISIS_SANDBOX_NO_EDGE"

    champ = None if crow is None else crow.to_dict()
    if champ:
        arms_nav[champ["arm"]].to_csv(OUT / f"nav_{champ['arm']}.csv", index=False)

    base_diag = {
        "base_id": BASE_ID,
        "base_path": str(l4_path.relative_to(ROOT)),
        "base_y2020_mdd": base_y20_mdd,
        "base_mar2020_mdd": base_mar_mdd,
        "mar2020_window": [str(MAR2020_START), str(MAR2020_END)],
        "held_floor_pp": HELD_CAGR_FLOOR_PP,
        "y2020_mdd_improve_floor_pp": Y2020_MDD_IMPROVE_FLOOR_PP,
        "mar2020_mdd_improve_floor_pp": MAR2020_MDD_IMPROVE_FLOOR_PP,
        "sealed_mdd_floor_pp": SEALED_MDD_FLOOR_PP,
    }
    (OUT / "base_diag.json").write_text(json.dumps(base_diag, indent=2) + "\n", encoding="utf-8")

    compare_0kb4 = {
        "register": "0kb4",
        "verdict": "IP3_Y2020_DEFEND_NO_EDGE",
        "family": "defend/off-peak/FUSE force-LIVE knives on 0kb2",
        "this_family": "crisis overlays (vol/MA200/account-MDD) on L4 NAV returns",
        "note": (
            "Different mechanism family — 0kb4 failed held+∧y20 on residual stack knives; "
            "0kbg screens synthetic crisis exposure on twin NAV. Neither unlocks soak freeze."
        ),
    }

    optimize = [
        "Objective: SANDBOX crisis overlays on L4 Path3 WITHIN NAV — cut Mar2020/y2020 MDD without held destroy",
        (
            f"Champion `{champ['arm']}` fam={champ['family']} held={champ['held_vs_base']} "
            f"y2020MDD↑={champ['y2020_mdd_improve_pp']} Mar2020MDD↑={champ['mar2020_mdd_improve_pp']} "
            f"sealed={champ['sealed_vs_base']} tipY={champ['tipY_vs_base']} verdict={champ['verdict']}"
            if champ
            else "No champion"
        ),
        f"Clears: HIT={hits_n} · SOFT={soft_n} · MDD_ONLY={mdd_only_n} · "
        f"HELD_BLOCK={held_block_n} · MDD_BLOCK={mdd_block_n} / mech={len(mech)}",
        f"Base L4 y2020 MDD={base_y20_mdd} · Mar2020 MDD={base_mar_mdd}",
        "Compare 0kb4: Y2020_DEFEND_NO_EDGE (defend/FUSE knives) — different family; stop_freeze_0kb2 KEEP",
        "Disposition: does **not** unlock soak freeze · does **not** recommend LIVE wire · "
        "does **not** reopen 0kb2 residual stacks",
        "Soft KEEP · Path4 OFF · broker false · no tip apply · no Soft FIN/TEL ACCEPT · no yearmix",
    ]

    screen = {
        "id": SCREEN_ID,
        "register": REGISTER,
        "parents": list(PARENTS),
        "generated_at_utc": generated,
        "mech": MECH,
        "label_tag": LABEL_TAG,
        "verdict": verdict,
        "soak_unlock": False,
        "live_wire_recommend": False,
        "reopen_0kb2_observe": False,
        "n_mech_screened": len(mech),
        "n_hit": hits_n,
        "n_soft": soft_n,
        "n_mdd_only": mdd_only_n,
        "n_held_block": held_block_n,
        "n_mdd_block": mdd_block_n,
        "base": base_diag,
        "compare_0kb4": compare_0kb4,
        "family_summary": by_fam.to_dict(orient="records"),
        "champion": champ,
        "top_arms": top.to_dict(orient="records"),
        "optimize_live": optimize,
        "soft_keep": True,
        "path4_live": False,
        "broker": False,
        "label": f"{SCREEN_ID}_{day}__{verdict}__{LABEL_TAG}",
    }
    (OUT / "screen.json").write_text(json.dumps(screen, indent=2) + "\n", encoding="utf-8")

    charter_md = "\n".join(
        [
            f"# {CHARTER_ID}",
            "",
            f"Date: {day}",
            f"Register: **{REGISTER}** · Parents: {', '.join(PARENTS)}",
            f"Label: **{LABEL_TAG}** · SOAK-SAFE parallel paper research",
            "",
            "## Question",
            "",
            "On live-twin / L4 Path3 WITHIN (or BASE_LIVE_FUSE_COOL) NAV returns, can offline "
            "overlays inspired by general crisis frameworks improve **2020 MDD** "
            "(esp. Mar 2020 cliff 2020-02-20→2020-03-23) without destroying held CAGR?",
            "",
            "## Arms",
            "",
            "1. Vol targeting (20d/63d × target vol × floor 0.3–0.4)",
            "2. MA200 filter on 0050 (lag-1 → cash / soft cash)",
            "3. Account MDD throttle (peak DD −8/−10/−12 → ×0.5; halt −12/−15/−18)",
            "4. Light combos of best single seeds",
            "",
            "## Hard constraints",
            "",
            "- NO_LIVE · no tip apply · no Soft FIN/TEL ACCEPT · no Path4 · no broker",
            "- no year-oracle / yearmix commit",
            "- **not** tip Soft Stage A for promote",
            "- does **not** reopen 0kb2 residual paper stacks",
            "- does **not** unlock soak freeze",
            "",
            "## vs 0kb4",
            "",
            "0kb4 `IP3_Y2020_DEFEND_NO_EDGE` = defend/off-peak/FUSE knives on 0kb2. "
            "This pack = synthetic crisis exposure on twin NAV — different family.",
            "",
            f"Label: `{CHARTER_ID}_{day}__{LABEL_TAG}`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{CHARTER_ID}.md", REP / f"{CHARTER_ID}.md", charter_md, kind="charter"
    )
    (OPS / f"{CHARTER_ID}.json").write_text(
        json.dumps(
            {
                "id": CHARTER_ID,
                "register": REGISTER,
                "parents": list(PARENTS),
                "mech": MECH,
                "label_tag": LABEL_TAG,
                "date": day,
                "forbidden": [
                    "live_wire",
                    "tip_apply",
                    "soft_fin_tel_accept",
                    "path4_live",
                    "broker",
                    "yearmix_commit",
                    "reopen_0kb2_observe_mainline",
                    "soak_unlock",
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    write_repro_pointer(OPS / f"{CHARTER_ID}.json", REP / f"{CHARTER_ID}.json", kind="charter")

    screen_md = [
        f"# {SCREEN_ID}",
        "",
        f"Date: {day} · Verdict: **`{verdict}`** · champion=**`{(champ or {}).get('arm')}`**",
        f"Register: **{REGISTER}** · **{LABEL_TAG}** · mech={len(mech)} · "
        f"HIT={hits_n} · SOFT={soft_n} · MDD_ONLY={mdd_only_n} · "
        f"HELD_BLOCK={held_block_n} · MDD_BLOCK={mdd_block_n}",
        "",
        "## Base",
        "",
        f"- `{BASE_ID}` path `{base_diag['base_path']}`",
        f"- y2020 MDD **{base_y20_mdd}** · Mar2020 MDD **{base_mar_mdd}** "
        f"({MAR2020_START}→{MAR2020_END})",
        f"- floors: held≥**{HELD_CAGR_FLOOR_PP}** · y2020 MDD↑≥**{Y2020_MDD_IMPROVE_FLOOR_PP}** · "
        f"Mar MDD↑≥**{MAR2020_MDD_IMPROVE_FLOOR_PP}** · sealed≥**{SEALED_MDD_FLOOR_PP}**",
        "",
        "## vs 0kb4",
        "",
        f"- {compare_0kb4['note']}",
        "",
        "## Family summary",
        "",
        "| Family | n | HIT | MDD help | held+ | max held | max y20 MDD↑ | max Mar MDD↑ | max sealed |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in by_fam.to_dict(orient="records"):
        screen_md.append(
            f"| {r['family']} | {r['n']} | {int(r['n_hit'])} | {int(r['n_mdd_help'])} | "
            f"{int(r['n_held_ok'])} | {r['max_held']} | {r['max_y20_mdd_imp']} | "
            f"{r['max_mar_mdd_imp']} | {r['max_sealed']} |"
        )
    screen_md += [
        "",
        "## Top arms",
        "",
        "| Arm | fam | held | y2020 MDD↑ | Mar2020 MDD↑ | sealed | tipY | verdict |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for r in top.to_dict(orient="records"):
        screen_md.append(
            f"| {r['arm']} | {r['family']} | {r['held_vs_base']} | "
            f"{r['y2020_mdd_improve_pp']} | {r['mar2020_mdd_improve_pp']} | "
            f"{r['sealed_vs_base']} | {r['tipY_vs_base']} | {r['verdict']} |"
        )
    screen_md += [
        "",
        "## Optimize / disposition",
        "",
        *[f"{i}. {line}" for i, line in enumerate(optimize, 1)],
        "",
        "Repro: `PYTHONPATH=scripts python3 scripts/tipsoft_ip3_y2020_crisis_sandbox_stagea.py`",
        "",
        f"Label: `{screen['label']}`",
        "",
    ]
    write_ops_and_repro_pointer(
        OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", "\n".join(screen_md), kind="screen"
    )
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(screen, indent=2) + "\n", encoding="utf-8")
    write_repro_pointer(OPS / f"{SCREEN_ID}.json", REP / f"{SCREEN_ID}.json", kind="screen")

    decision_md = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: {day} · Verdict: **`{verdict}`** · champion=**`{(champ or {}).get('arm')}`**",
            f"Register: **{REGISTER}** · Parents: {', '.join(PARENTS)} · **{LABEL_TAG}**",
            "",
            "## Result",
            "",
            (
                f"- family: **{(champ or {}).get('family')}**\n"
                f"- held vs L4: **{(champ or {}).get('held_vs_base')}**\n"
                f"- y2020 MDD improve: **{(champ or {}).get('y2020_mdd_improve_pp')}** "
                f"(base MDD {(base_y20_mdd)})\n"
                f"- Mar2020 MDD improve: **{(champ or {}).get('mar2020_mdd_improve_pp')}** "
                f"(base MDD {(base_mar_mdd)}; window {MAR2020_START}→{MAR2020_END})\n"
                f"- sealed **{(champ or {}).get('sealed_vs_base')}** · "
                f"tipY **{(champ or {}).get('tipY_vs_base')}**\n"
                f"- clears: HIT **{hits_n}** · SOFT **{soft_n}** · MDD_ONLY **{mdd_only_n}** · "
                f"HELD_BLOCK **{held_block_n}** · MDD_BLOCK **{mdd_block_n}**"
                if champ
                else f"- No clear · mech={len(mech)}"
            ),
            "",
            "## Disposition",
            "",
            "- **SANDBOX / PARALLEL** — not tip Soft Stage A for promote",
            "- HIT only if held+ (≥+0.10pp) AND (y2020 or Mar2020 MDD improve) AND sealed floor OK",
            "- Does **not** unlock soak freeze · does **not** recommend LIVE wire",
            "- Does **not** reopen 0kb2 residual paper stacks as observe mainline",
            "- vs 0kb4 `IP3_Y2020_DEFEND_NO_EDGE`: different family (crisis overlays vs defend/FUSE knives)",
            "- Soft KEEP · Path4 OFF · broker false · no tip apply",
            "",
            "## Next",
            "",
            *[f"{i}. {line}" for i, line in enumerate(optimize, 1)],
            "",
            f"Label: `{DECISION_ID}_{day}__{verdict}__{LABEL_TAG}__NO_LIVE`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{DECISION_ID}.md", REP / f"{DECISION_ID}.md", decision_md, kind="decision pack"
    )
    (OPS / f"{DECISION_ID}.json").write_text(
        json.dumps(
            {
                "id": DECISION_ID,
                "register": REGISTER,
                "parents": list(PARENTS),
                "label_tag": LABEL_TAG,
                "verdict": verdict,
                "champion": champ,
                "n_hit": hits_n,
                "n_soft": soft_n,
                "n_mdd_only": mdd_only_n,
                "soak_unlock": False,
                "live_wire_recommend": False,
                "reopen_0kb2_observe": False,
                "compare_0kb4": compare_0kb4,
                "soft_keep": True,
                "path4_live": False,
                "broker": False,
                "label": f"{DECISION_ID}_{day}__{verdict}__{LABEL_TAG}__NO_LIVE",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    write_repro_pointer(
        OPS / f"{DECISION_ID}.json", REP / f"{DECISION_ID}.json", kind="decision pack"
    )

    _patch_register(verdict, champ, day)
    _patch_ops_status(verdict, champ, day)

    summary = {
        "verdict": verdict,
        "champion": None if not champ else champ["arm"],
        "family": None if not champ else champ["family"],
        "held_vs_base": None if not champ else champ["held_vs_base"],
        "y2020_mdd_improve_pp": None if not champ else champ["y2020_mdd_improve_pp"],
        "mar2020_mdd_improve_pp": None if not champ else champ["mar2020_mdd_improve_pp"],
        "sealed_vs_base": None if not champ else champ["sealed_vs_base"],
        "tipY_vs_base": None if not champ else champ["tipY_vs_base"],
        "n_hit": hits_n,
        "n_soft": soft_n,
        "n_mdd_only": mdd_only_n,
        "n_mech": len(mech),
        "base_y2020_mdd": base_y20_mdd,
        "base_mar2020_mdd": base_mar_mdd,
        "soak_unlock": False,
        "live_wire_recommend": False,
        "label_tag": LABEL_TAG,
        "register": REGISTER,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
