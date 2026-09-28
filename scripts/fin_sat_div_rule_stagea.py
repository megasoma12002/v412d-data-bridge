#!/usr/bin/env python3
"""FIN×SAT divergence switch-rule Stage A — enter/confirm/exit (paper).

Charter: research/ops/FIN_SAT_DIV_RULE_STAGEA_CHARTER.md
Parents: 0k9l/0k9i TIP_MDD_ONLY · COMP + SAT_RELAX KEEP.
Soft-Frozen KEEP · no live · no feature-table expand · no year-switch.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

import cool_t50_inv_satellite_stagea as sat
from e45_paper_harness import WINDOWS_STANDARD, window_stats
from e50_early_stack_combined_nav import e16_features
from fin_sell_quality_helpers import cagr_lift_pp
from ops_repro_ssot import write_ops_and_repro_pointer
from research_metric_helpers import mdd_delta_pp

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "fin-sat-div-rule-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_SAT_DIV_RULE_STAGEA_CHARTER"
SCREEN_ID = "FIN_SAT_DIV_RULE_STAGEA_SCREEN"
DECISION_ID = "FIN_SAT_DIV_RULE_STAGEA_DECISION_PACK"
BASE_ID = "CTRL_LIVE_A10"

LIVE_NAV = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/ctrl_live_a10_daily_nav.csv"
COMP_NAV = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/comp_h150_x_a20_daily_nav.csv"
SAT_NAV = ROOT / "repro/sat-a20-relax-dual-paper-observe/outputs/sat_a20_relax_daily_nav.csv"
COMP_FILLS = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/comp_h150_x_a20_fills.csv"

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


def _build_signals(dates: pd.DatetimeIndex, comp: pd.DataFrame, sat_nav: pd.DataFrame) -> pd.DataFrame:
    print("building signals ...", flush=True)
    market0 = sat.load_market()
    _p, _s, _t, regime = e16_features(market0)
    reg = pd.Series(regime.values, index=pd.to_datetime(regime.index)).sort_index()
    reg = reg[~reg.index.duplicated(keep="last")]
    px = market0[market0["code"].astype(str) == "0050"].copy()
    px["date"] = pd.to_datetime(px["date"])
    close = px.drop_duplicates("date").set_index("date")["adj_close" if "adj_close" in px.columns else "close"].astype(float)
    close = close[~close.index.duplicated(keep="last")]
    r0050 = close.pct_change()

    c = comp.set_index("date")["nav"].reindex(dates).astype(float)
    s = sat_nav.set_index("date")["nav"].reindex(dates).astype(float)
    rel = c.pct_change() - s.pct_change()

    sells = pd.Series(0.0, index=dates)
    if COMP_FILLS.exists():
        f = pd.read_csv(COMP_FILLS)
        f["fill_date"] = pd.to_datetime(f["fill_date"])
        cnt = f[f["side"].astype(str).str.upper() == "SELL"].groupby("fill_date").size()
        sells = cnt.reindex(dates).fillna(0.0)

    df = pd.DataFrame({"date": dates})
    df["r0050_63"] = _trail(df["date"].map(r0050), 63).to_numpy()
    df["trail_rel_63"] = _trail(pd.Series(rel.to_numpy()), 63).to_numpy()
    df["crisis"] = (df["date"].map(reg) == "Crisis").astype(float)
    df["comp_sells_21"] = sells.rolling(21, min_periods=1).sum().to_numpy()
    for col in ("r0050_63", "trail_rel_63", "crisis", "comp_sells_21"):
        df[f"{col}_l1"] = df[col].shift(1)

    med_r = float(df["r0050_63_l1"].median(skipna=True))
    med_s = float(df["comp_sells_21_l1"].median(skipna=True))
    df["HOT"] = df["r0050_63_l1"] > med_r
    df["CONF"] = (df["crisis_l1"] > 0.5) | (df["comp_sells_21_l1"] > med_s)
    df["DIV"] = df["trail_rel_63_l1"] <= -THETA
    df["REC"] = df["trail_rel_63_l1"] >= 0.0
    df["NOT_HOT"] = df["r0050_63_l1"] <= med_r
    # COOL5: NOT_HOT consecutive >=5 (as of lag-1 day)
    nh = df["NOT_HOT"].fillna(False).astype(bool).to_numpy()
    cool = np.zeros(len(df), dtype=bool)
    run = 0
    for i in range(len(df)):
        if nh[i]:
            run += 1
        else:
            run = 0
        cool[i] = run >= 5
    df["COOL5"] = cool
    df.attrs["med_r"] = med_r
    df.attrs["med_s"] = med_s
    return df


def _apply_hold(enter: np.ndarray, exit_sig: np.ndarray, *, min_hold: int = 0) -> np.ndarray:
    n = len(enter)
    out = np.zeros(n, dtype=bool)
    on = False
    held = 0
    for i in range(n):
        if not on:
            if enter[i]:
                on = True
                held = 1
        else:
            held += 1
            if held > min_hold and exit_sig[i]:
                on = False
                held = 0
        out[i] = on
    return out


def _rule_div_only(df: pd.DataFrame) -> np.ndarray:
    return df["DIV"].fillna(False).to_numpy()


def _rule_hot_and_conf(df: pd.DataFrame) -> np.ndarray:
    return (df["HOT"].fillna(False) & df["CONF"].fillna(False)).to_numpy()


def _rule_enter_exit(df: pd.DataFrame) -> np.ndarray:
    enter = (df["HOT"].fillna(False) & df["CONF"].fillna(False)).to_numpy()
    exit_sig = (df["COOL5"].fillna(False) | df["REC"].fillna(False)).to_numpy()
    return _apply_hold(enter, exit_sig, min_hold=0)


def _rule_div_conf_hold(df: pd.DataFrame) -> np.ndarray:
    enter = (df["DIV"].fillna(False) & df["CONF"].fillna(False)).to_numpy()
    exit_sig = df["REC"].fillna(False).to_numpy()
    return _apply_hold(enter, exit_sig, min_hold=21)


def _rule_crisis_hold21(df: pd.DataFrame) -> np.ndarray:
    crisis = (df["crisis_l1"].fillna(0) > 0.5).to_numpy()
    # exit when not crisis for 5 consecutive
    not_c = ~crisis
    exit5 = np.zeros(len(df), dtype=bool)
    run = 0
    for i in range(len(df)):
        if not_c[i]:
            run += 1
        else:
            run = 0
        exit5[i] = run >= 5
    return _apply_hold(crisis, exit5, min_hold=21)


def _rule_hot_then_div(df: pd.DataFrame) -> np.ndarray:
    hot = df["HOT"].fillna(False).to_numpy()
    div = df["DIV"].fillna(False).to_numpy()
    rec = df["REC"].fillna(False).to_numpy()
    n = len(df)
    enter = np.zeros(n, dtype=bool)
    last_hot = -10**9
    for i in range(n):
        if hot[i]:
            last_hot = i
        if div[i] and (i - last_hot) <= 21 and last_hot >= 0:
            enter[i] = True
    return _apply_hold(enter, rec, min_hold=0)


RULES: list[dict[str, Any]] = [
    {"id": "CTRL_LIVE_A10", "fam": "ctrl"},
    {"id": "REF_SAT_RELAX", "fam": "ref", "always": "sat"},
    {"id": "REF_COMP_H150_A20", "fam": "ref", "always": "comp"},
    {"id": "R_DIV_ONLY", "fam": "switch", "fn": _rule_div_only},
    {"id": "R_HOT_AND_CONF", "fam": "switch", "fn": _rule_hot_and_conf},
    {"id": "R_ENTER_EXIT", "fam": "switch", "fn": _rule_enter_exit},
    {"id": "R_DIV_CONF_HOLD", "fam": "switch", "fn": _rule_div_conf_hold},
    {"id": "R_CRISIS_HOLD21", "fam": "switch", "fn": _rule_crisis_hold21},
    {"id": "R_HOT_THEN_DIV", "fam": "switch", "fn": _rule_hot_then_div},
]


def _switch_nav(comp, sat_nav, use_sat: np.ndarray) -> tuple[pd.DataFrame, dict[str, Any]]:
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
    hit = bool(fam == "switch" and tip_clean and economic and vs_sat_ok)
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
        },
        "hit": hit,
    }


def _verdict(rows: list[dict[str, Any]]) -> str:
    sw = [r for r in rows if r["fam"] == "switch"]
    if any(r["eval"]["hit"] for r in sw):
        return "RULE_HIT"
    if any(
        r["eval"]["gates"]["tip_clean"]
        and r["eval"]["gates"]["economic"]
        and not r["eval"]["gates"]["vs_sat_held"]
        for r in sw
    ):
        return "TIP_CLEAN_SOFT"
    if any(
        r["eval"]["gates"]["tip_mdd"]
        and not r["eval"]["gates"]["tip_cagr"]
        and r["eval"]["gates"]["economic"]
        for r in sw
    ):
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

    sig = _build_signals(pd.DatetimeIndex(dates), comp, sat_nav)
    sig.to_csv(OUT / "rule_signals.csv", index=False)

    base_w = _pack(live)
    sat_w = _pack(sat_nav)
    sat_held = cagr_lift_pp(
        (base_w.get("heldout_2019_plus") or {}).get("cagr"),
        (sat_w.get("heldout_2019_plus") or {}).get("cagr"),
    )

    rows: list[dict[str, Any]] = []
    for spec in RULES:
        bid = spec["id"]
        fam = spec["fam"]
        print(f"{bid} ...", flush=True)
        if fam == "ctrl":
            nav = live.copy()
            meta = {"pct_days_sat": 0.0, "n_flips": 0, "rule": "ctrl"}
        elif fam == "ref":
            nav = sat_nav.copy() if spec["always"] == "sat" else comp.copy()
            meta = {
                "pct_days_sat": 100.0 if spec["always"] == "sat" else 0.0,
                "n_flips": 0,
                "rule": spec["always"],
            }
        else:
            fn: Callable = spec["fn"]
            use = fn(sig)
            nav, meta = _switch_nav(comp, sat_nav, use)
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

    verdict = _verdict(rows)
    generated = _utc()
    hits = [r for r in rows if r["eval"]["hit"]]
    hits.sort(key=lambda r: float(r["eval"]["held_cagr_lift_pp"] or -9), reverse=True)
    best = hits[0] if hits else None
    econ_tipmdd = [
        r
        for r in rows
        if r["fam"] == "switch"
        and r["eval"]["gates"]["economic"]
        and r["eval"]["gates"]["tip_mdd"]
        and not r["eval"]["gates"]["tip_cagr"]
    ]
    econ_tipmdd.sort(key=lambda r: float(r["eval"]["held_cagr_lift_pp"] or -9), reverse=True)

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
        "signal_medians": {"r0050_63": sig.attrs.get("med_r"), "comp_sells_21": sig.attrs.get("med_s")},
        "books": [
            {"id": r["id"], "fam": r["fam"], "meta": r["meta"], "eval": r["eval"], "tip": r["tip"]} for r in rows
        ],
        "register": "0k9m",
    }

    screen_md = "\n".join(
        [
            f"# {SCREEN_ID}",
            "",
            f"Date: 2026-09-28 · Generated `{generated}`",
            f"Status: **{verdict}** · Soft-Frozen **KEEP** · parents **KEEP** · live wire **false**",
            "",
            "Enter/confirm/exit divergence rules (HOT∧CONF, DIV, crisis hold) · lag-1 · HIT tip-clean+held+vsSAT.",
            "",
            "## Books",
            "",
            "| ID | fam | %SAT | flips | heldCAGR↑ | tipCAGR↑ | tipClean | vsSAT | HIT |",
            "|---|---|---:|---:|---:|---:|---|---|---|",
        ]
        + [
            "| {id} | {fam} | {ps} | {fl} | {cagr} | {tc} | {clean} | {vs} | {hit} |".format(
                id=r["id"],
                fam=r["fam"],
                ps=r["meta"]["pct_days_sat"],
                fl=r["meta"]["n_flips"],
                cagr=r["eval"]["held_cagr_lift_pp"],
                tc=r["eval"]["tip_ytd_cagr_pp"],
                clean=r["eval"]["gates"]["tip_clean"],
                vs=r["eval"]["gates"]["vs_sat_held"],
                hit=r["eval"]["hit"],
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
        "Parents: 0k9l/0k9i · register **0k9m**",
        "",
        "## Verdict",
        "",
        f"**`{verdict}`**",
        "",
    ]
    if best:
        dlines += [
            f"Champion: `{best['id']}` · held CAGR↑ {best['eval']['held_cagr_lift_pp']} · tipCAGR↑ {best['eval']['tip_ytd_cagr_pp']}",
            "",
            "Even HIT → observe ballot DRAFT only · parents KEEP · no live.",
            "",
        ]
    elif econ_tipmdd:
        top = econ_tipmdd[0]
        dlines += [
            f"Best economic tipMDD rule: `{top['id']}` · held↑ {top['eval']['held_cagr_lift_pp']} · tipCAGR↑ {top['eval']['tip_ytd_cagr_pp']} · %SAT {top['meta']['pct_days_sat']}",
            "",
        ]
    else:
        dlines += ["No switch cleared economic tipMDD path.", ""]

    dlines += ["## Rule books", ""]
    for r in rows:
        if r["fam"] != "switch":
            continue
        g = r["eval"]["gates"]
        dlines.append(
            f"- `{r['id']}` · %SAT={r['meta']['pct_days_sat']} flips={r['meta']['n_flips']} · "
            f"held↑ {r['eval']['held_cagr_lift_pp']} tipCAGR↑ {r['eval']['tip_ytd_cagr_pp']} · "
            f"tipClean={g['tip_clean']} econ={g['economic']} vsSAT={g['vs_sat_held']}"
        )
    dlines += [
        "",
        "## Binding",
        "",
        "1. Soft-Frozen / Exact T+1 / COOL / SELL_a75 / live CONF α=0.10 KEEP",
        "2. COMPOSITE + SAT_RELAX observes **KEEP OPEN**",
        "3. Do not expand feature table or rule grid after peek",
        "4. Even RULE_HIT → paper observe DRAFT only · no live",
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
        "best_hit": None if best is None else best["id"],
        "best_economic_tipmdd": None if not econ_tipmdd else econ_tipmdd[0]["id"],
        "charter": f"research/ops/{CHARTER_ID}.md",
        "screen": f"research/ops/{SCREEN_ID}.md",
        "register": "0k9m",
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

    print(json.dumps({"verdict": verdict, "best_hit": None if not best else best["id"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
