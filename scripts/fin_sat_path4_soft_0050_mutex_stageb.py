#!/usr/bin/env python3
"""Path4 Soft-0050 mutex Stage B (0kal) — richer dual books · paper only.

Parent 0kak: Soft-core ON↔OFF carve ``PATH4_MUTEX_HIT`` / ``SW_TRAIL_001``.
Stage B replaces zero-0050 OFF with **clip Soft books**:

- ``SOFT_HI``  — live Soft-Frozen clips F[0.60,0.80] E[0.00,0.50] (+ FUSE+COOL)
- ``SOFT_LO``  — same FIN/TEL, ETF hi **0.35** (HI–LO ETF clip)
- ``SOFT_DEF`` — prior FINBAND F[0.60,0.90] E[0.00,0.35] sticky DEF sleeve

Mutex: causal ``trail_rel_a_b_63`` between book pair returns; ``B_LEAD`` iff
≤ −θ (mirror Path3 SAT_LEAD / Stage A OFF_LEAD). Soft KEEP · broker false ·
cutover BLOCKED · no live · **forbid Path3 trail / P3 flip calendar**.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import asymm_0050_bull_densify_under_cool_stagea as asymm
import e16_clip_search_challenger as clip
import e16_soft_frozen_base as soft
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, load_market, window_stats
from e50_early_stack_combined_nav import FIN, e16_features
from fin_sell_quality_helpers import cagr_lift_pp
from ops_repro_ssot import write_ops_and_repro_pointer, write_repro_pointer
from research_metric_helpers import mdd_delta_pp
from ta_indicator_catalog import build_low_high_catalog
from within_sleeve_alloc import build_kd_season_tilt_scores, build_pre_exdiv_window_buy_ok

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "fin-sat-path4-soft-0050-mutex-stageb"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"
PARENT_A = ROOT / "repro/fin-sat-path4-soft-0050-mutex-stagea/outputs"

CHARTER_ID = "FIN_SAT_PATH4_SOFT_0050_MUTEX_STAGEB_CHARTER"
SCREEN_ID = "FIN_SAT_PATH4_SOFT_0050_MUTEX_STAGEB_SCREEN"
DECISION_ID = "FIN_SAT_PATH4_SOFT_0050_MUTEX_STAGEB_DECISION_PACK"
REGISTER = "0kal"

# Clip boxes (fin_lo, fin_hi, tel_lo, tel_hi, etf_lo, etf_hi)
CLIPS_HI = asymm.LIVE_CLIPS  # (0.60, 0.80, 0.03, 0.35, 0.00, 0.50)
CLIPS_LO = (0.60, 0.80, 0.03, 0.35, 0.00, 0.35)  # HI–LO ETF only
CLIPS_DEF = asymm.PRIOR_FINBAND  # (0.60, 0.90, 0.03, 0.35, 0.00, 0.35)

TRAIL = 63
THETAS = (0.005, 0.01, 0.02)
SEALED_MDD_FLOOR_PP = -0.25
TIP_Y_FLOOR_PP = -1.0
HELD_CAGR_FLOOR_PP = 0.10


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _nav_to_series(nav: pd.DataFrame) -> pd.Series:
    x = nav.copy()
    x["date"] = pd.to_datetime(x["date"]).dt.normalize()
    # Soft sims store absolute NAV; normalize to 1.0 start for metrics
    s = x.set_index("date")["nav"].astype(float).sort_index()
    return s / float(s.iloc[0])


def _rets(nav_s: pd.Series) -> pd.Series:
    return nav_s.pct_change().fillna(0.0)


def _trail_rel(r_a: pd.Series, r_b: pd.Series, window: int = TRAIL) -> pd.Series:
    rel = (r_a - r_b).astype(float)
    x = np.log1p(rel.clip(lower=-0.999999))
    return np.expm1(x.rolling(window, min_periods=window).sum())


def _switch_rets(r_a: pd.Series, r_b: pd.Series, b_lead: pd.Series) -> pd.Series:
    lead = b_lead.reindex(r_a.index).fillna(False).astype(bool)
    return pd.Series(
        np.where(lead.to_numpy(), r_b.to_numpy(), r_a.to_numpy()),
        index=r_a.index,
        dtype=float,
    )


def _nav_from_rets(rets: pd.Series) -> pd.DataFrame:
    r = rets.dropna()
    nav = (1.0 + r).cumprod()
    nav = nav / float(nav.iloc[0])
    return pd.DataFrame({"date": r.index.to_numpy(), "nav": nav.to_numpy(dtype=float)})


def _pack(nav: pd.DataFrame) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name, (start, end) in WINDOWS_STANDARD.items():
        st = window_stats(nav, start, end)
        out[name] = {
            "cagr": None if st.get("cagr") is None else round(float(st["cagr"]), 6),
            "max_drawdown": None
            if st.get("max_drawdown") is None
            else round(float(st["max_drawdown"]), 6),
            "n_days": int(st.get("n_days") or 0),
        }
    return out


def _tip(base: pd.DataFrame, chal: pd.DataFrame) -> dict[str, Any]:
    asof = pd.Timestamp(pd.to_datetime(base["date"]).max())
    b_dates = pd.to_datetime(base["date"])
    c_dates = pd.to_datetime(chal["date"])
    out: dict[str, Any] = {}
    for wname, start in (
        ("ytd", pd.Timestamp(asof.year, 1, 1)),
        ("trailing_1y", asof - pd.Timedelta(days=365)),
    ):
        b = base[(b_dates >= start) & (b_dates <= asof)].reset_index(drop=True)
        c = chal[(c_dates >= start) & (c_dates <= asof)].reset_index(drop=True)
        if len(b) < 20 or len(c) < 20:
            out[wname] = {"cagr_lift_pp": None, "mdd_improve_pp": None}
            continue
        bn = b["nav"].astype(float) / float(b["nav"].iloc[0])
        cn = c["nav"].astype(float) / float(c["nav"].iloc[0])
        b_mdd = float((bn / bn.cummax() - 1.0).min())
        c_mdd = float((cn / cn.cummax() - 1.0).min())
        years = (len(b) - 1) / 252.0
        bc = float(bn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        cc = float(cn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        out[wname] = {
            "cagr_lift_pp": None
            if cagr_lift_pp(bc, cc) is None
            else round(float(cagr_lift_pp(bc, cc)), 4),
            "mdd_improve_pp": round(float(mdd_delta_pp(b_mdd, c_mdd)), 4),
        }
    return out


def _delta_windows(base_w: dict, chal_w: dict) -> dict[str, Any]:
    out = {}
    for k in ("full", "heldout_2019_plus", "sealed_2023_plus"):
        b, c = base_w.get(k) or {}, chal_w.get(k) or {}
        out[k] = {
            "cagr_lift_pp": None
            if cagr_lift_pp(b.get("cagr"), c.get("cagr")) is None
            else round(float(cagr_lift_pp(b.get("cagr"), c.get("cagr"))), 4),
            "mdd_improve_pp": None
            if b.get("max_drawdown") is None or c.get("max_drawdown") is None
            else round(float(mdd_delta_pp(b["max_drawdown"], c["max_drawdown"])), 4),
            "base_cagr": b.get("cagr"),
            "chal_cagr": c.get("cagr"),
            "base_mdd": b.get("max_drawdown"),
            "chal_mdd": c.get("max_drawdown"),
        }
    return out


def _arm_verdict(delta: dict[str, Any], tip: dict[str, Any]) -> str:
    held = delta["heldout_2019_plus"]
    sealed = delta["sealed_2023_plus"]
    tip_y = (tip.get("ytd") or {}).get("cagr_lift_pp")
    if held.get("cagr_lift_pp") is None or sealed.get("mdd_improve_pp") is None:
        return "INCOMPLETE"
    held_ok = float(held["cagr_lift_pp"]) >= HELD_CAGR_FLOOR_PP
    sealed_ok = float(sealed["mdd_improve_pp"]) >= SEALED_MDD_FLOOR_PP
    tip_ok = tip_y is None or float(tip_y) >= TIP_Y_FLOOR_PP
    full_ok = float(delta["full"].get("cagr_lift_pp") or 0) > 0
    if held_ok and sealed_ok and tip_ok and full_ok:
        return "HIT"
    if held_ok and sealed_ok and tip_ok:
        return "HELD_HIT"
    if sealed_ok and tip_ok and float(held["cagr_lift_pp"]) > -0.5:
        return "SOFT"
    if float(sealed["mdd_improve_pp"]) < SEALED_MDD_FLOOR_PP:
        return "MDD_BLOCK"
    if tip_y is not None and float(tip_y) < TIP_Y_FLOOR_PP:
        return "TIP_BLOCK"
    return "NO_EDGE"


def _build_sticky_nav(
    *,
    clips: tuple[float, ...],
    market,
    dividends,
    regime,
    score,
    buy_live,
    buy_ok,
    sell_live,
) -> pd.DataFrame:
    flo, fhi, tlo, thi, elo, ehi = clips
    tgt = clip.build_targets_with_clips(
        regime=regime,
        score=score,
        fin_lo=flo,
        fin_hi=fhi,
        tel_lo=tlo,
        tel_hi=thi,
        etf_lo=elo,
        etf_hi=ehi,
    )
    # Offense pass → COOL from offense → final Soft NAV (live stack)
    off, _ = asymm._sim(
        market, tgt, regime, dividends, scores=buy_live, buy_ok=buy_ok, sell=sell_live
    )
    cool = asymm._cool_from_offense(market, off)
    nav, _ = asymm._sim(
        market,
        tgt,
        regime,
        dividends,
        scores=buy_live,
        buy_ok=buy_ok,
        sell=sell_live,
        exposure=cool,
    )
    return nav


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()

    print("loading Soft features ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, sleeve, _tgt, regime = e16_features(market)
    cal = pd.DatetimeIndex(pd.to_datetime(market["date"]).drop_duplicates().sort_values())
    lows, highs = build_low_high_catalog(market, cal, list(FIN))
    kd = build_kd_season_tilt_scores(
        market,
        dividends,
        FIN,
        k_thresh=float(asymm.LIVE_KD["k_thresh"]),
        season_start=asymm.LIVE_KD["season_start"],
        season_end=asymm.LIVE_KD["season_end"],
        pre_days=int(asymm.LIVE_KD["pre_days"]),
        active_score=float(asymm.LIVE_KD["active_score"]),
    )
    buy_ok = build_pre_exdiv_window_buy_ok(
        cal, dividends, FIN, pre_days=int(asymm.LIVE_KD["pre_days"]), also_stock_ex=True
    )
    buy_live = asymm._buy(kd, lows)
    sell_live = asymm._sell(highs)
    score_live = asymm._sleeve_score(market, sleeve, float(asymm.LIVE_SLEEVE_ALPHA))

    books = {
        "SOFT_HI": CLIPS_HI,
        "SOFT_LO": CLIPS_LO,
        "SOFT_DEF": CLIPS_DEF,
    }
    sticky_nav: dict[str, pd.DataFrame] = {}
    sticky_rets: dict[str, pd.Series] = {}
    mean_etf: dict[str, float] = {}

    for name, clips in books.items():
        print(f"sim sticky {name} clips={clips} ...", flush=True)
        nav = _build_sticky_nav(
            clips=clips,
            market=market,
            dividends=dividends,
            regime=regime,
            score=score_live,
            buy_live=buy_live,
            buy_ok=buy_ok,
            sell_live=sell_live,
        )
        sticky_nav[name] = nav
        nav.to_csv(OUT / f"nav_REF_{name}.csv", index=False)
        s = _nav_to_series(nav)
        sticky_rets[name] = _rets(s)
        # mean target ETF from clips mid as proxy; better from tgt — recompute light
        flo, fhi, tlo, thi, elo, ehi = clips
        tgt = clip.build_targets_with_clips(
            regime=regime,
            score=score_live,
            fin_lo=flo,
            fin_hi=fhi,
            tel_lo=tlo,
            tel_hi=thi,
            etf_lo=elo,
            etf_hi=ehi,
        )
        mean_etf[name] = round(float(tgt["0050"].mean()), 4)

    # Align calendars
    idx = sticky_rets["SOFT_HI"].index
    for k in sticky_rets:
        idx = idx.intersection(sticky_rets[k].index)
    for k in list(sticky_rets):
        sticky_rets[k] = sticky_rets[k].reindex(idx).fillna(0.0)

    pairs = (
        ("HI_LO", "SOFT_HI", "SOFT_LO"),
        ("HI_DEF", "SOFT_HI", "SOFT_DEF"),
    )

    arms: dict[str, pd.Series] = {
        "REF_SOFT_HI": sticky_rets["SOFT_HI"],
        "REF_SOFT_LO": sticky_rets["SOFT_LO"],
        "REF_SOFT_DEF": sticky_rets["SOFT_DEF"],
    }
    meta_arms: dict[str, dict[str, Any]] = {
        "REF_SOFT_HI": {"kind": "sticky", "book": "SOFT_HI", "mean_etf": mean_etf["SOFT_HI"]},
        "REF_SOFT_LO": {"kind": "sticky", "book": "SOFT_LO", "mean_etf": mean_etf["SOFT_LO"]},
        "REF_SOFT_DEF": {"kind": "sticky", "book": "SOFT_DEF", "mean_etf": mean_etf["SOFT_DEF"]},
    }

    for pair_id, a, b in pairs:
        r_a, r_b = sticky_rets[a], sticky_rets[b]
        trail = _trail_rel(r_a, r_b)
        for th in THETAS:
            lead = (trail <= -float(th)) & trail.notna()
            name = f"SW_{pair_id}_{str(th).replace('.', '')}"
            arms[name] = _switch_rets(r_a, r_b, lead)
            meta_arms[name] = {
                "kind": "trail_mutex",
                "pair": pair_id,
                "book_a": a,
                "book_b": b,
                "theta": th,
                "pct_b": round(float(lead.fillna(False).mean()), 4),
                "n_b_days": int(lead.fillna(False).sum()),
                "n_flips": int(
                    (lead.fillna(False) != lead.fillna(False).shift(1).fillna(False)).sum()
                ),
            }

    # Parent Stage A champion context (Soft-core carve) if present
    parent_ctx = {}
    parent_nav_path = PARENT_A / "nav_SW_TRAIL_001.csv"
    if parent_nav_path.exists() and (PARENT_A / "nav_REF_SOFT_ON.csv").exists():
        p_on = pd.read_csv(PARENT_A / "nav_REF_SOFT_ON.csv", parse_dates=["date"])
        p_sw = pd.read_csv(parent_nav_path, parse_dates=["date"])
        parent_ctx = {
            "arm": "SW_TRAIL_001",
            "note": "Stage A Soft-core carve parent — not Soft Exact clip books",
            "delta_vs_soft_on": _delta_windows(_pack(p_on), _pack(p_sw)),
            "tip_vs_soft_on": _tip(p_on, p_sw),
        }

    navs = {k: _nav_from_rets(v) for k, v in arms.items()}
    for k, nav in navs.items():
        nav.to_csv(OUT / f"nav_{k}.csv", index=False)

    base = navs["REF_SOFT_HI"]
    bw = _pack(base)
    rows = []
    for arm, nav in navs.items():
        if arm == "REF_SOFT_HI":
            continue
        delta = _delta_windows(bw, _pack(nav))
        tip = _tip(base, nav)
        v = _arm_verdict(delta, tip)
        rows.append(
            {
                "arm": arm,
                "verdict_vs_hi": v,
                "full_cagr_lift_pp": delta["full"]["cagr_lift_pp"],
                "held_cagr_lift_pp": delta["heldout_2019_plus"]["cagr_lift_pp"],
                "sealed_mdd_improve_pp": delta["sealed_2023_plus"]["mdd_improve_pp"],
                "tip_ytd_cagr_lift_pp": (tip.get("ytd") or {}).get("cagr_lift_pp"),
                "tip_1y_cagr_lift_pp": (tip.get("trailing_1y") or {}).get("cagr_lift_pp"),
                "meta": meta_arms.get(arm, {}),
                "delta": delta,
                "tip": tip,
            }
        )

    hit = [r for r in rows if r["verdict_vs_hi"] in {"HIT", "HELD_HIT"}]
    # Prefer switch arms over sticky LO/DEF if both HIT
    sw_hit = [r for r in hit if str(r["arm"]).startswith("SW_")]
    pool = sw_hit or hit
    if pool:
        champion = max(
            pool,
            key=lambda r: (
                float(r["held_cagr_lift_pp"] or -999),
                float(r["tip_ytd_cagr_lift_pp"] or -999),
                float(r["sealed_mdd_improve_pp"] or -999),
            ),
        )
        pack_verdict = "PATH4_MUTEX_STAGEB_HIT"
    else:
        soft_rows = [r for r in rows if r["verdict_vs_hi"] == "SOFT"]
        if soft_rows:
            champion = max(soft_rows, key=lambda r: float(r["held_cagr_lift_pp"] or -999))
            pack_verdict = "PATH4_MUTEX_STAGEB_SOFT"
        else:
            champion = max(rows, key=lambda r: float(r["held_cagr_lift_pp"] or -999))
            pack_verdict = f"PATH4_MUTEX_STAGEB_{champion['verdict_vs_hi']}"

    # Beats parent Stage A held?
    parent_held = None
    if parent_ctx:
        parent_held = (parent_ctx["delta_vs_soft_on"].get("heldout_2019_plus") or {}).get(
            "cagr_lift_pp"
        )
    beats_parent = parent_held is not None and float(champion["held_cagr_lift_pp"] or 0) > float(
        parent_held
    )

    summary = [
        {
            "arm": r["arm"],
            "verdict_vs_hi": r["verdict_vs_hi"],
            "full_cagr_lift_pp": r["full_cagr_lift_pp"],
            "held_cagr_lift_pp": r["held_cagr_lift_pp"],
            "sealed_mdd_improve_pp": r["sealed_mdd_improve_pp"],
            "tip_ytd_cagr_lift_pp": r["tip_ytd_cagr_lift_pp"],
            "tip_1y_cagr_lift_pp": r["tip_1y_cagr_lift_pp"],
            **{f"meta_{k}": v for k, v in (r["meta"] or {}).items()},
        }
        for r in rows
    ]
    pd.DataFrame(summary).to_csv(OUT / "arms_vs_soft_hi.csv", index=False)

    screen = {
        "generated_at_utc": generated,
        "register": REGISTER,
        "parent": "0kak",
        "mech": "PATH4_SOFT_0050_MUTEX",
        "verdict": pack_verdict,
        "champion_arm": champion["arm"],
        "beats_parent_held": beats_parent,
        "clips": {
            "SOFT_HI": list(CLIPS_HI),
            "SOFT_LO": list(CLIPS_LO),
            "SOFT_DEF": list(CLIPS_DEF),
        },
        "mean_etf_target": mean_etf,
        "arms_vs_soft_hi": summary,
        "champion": {
            "arm": champion["arm"],
            "verdict_vs_hi": champion["verdict_vs_hi"],
            "delta": champion["delta"],
            "tip": champion["tip"],
            "meta": champion["meta"],
        },
        "parent_stagea_context": parent_ctx,
        "forbid_path3_inputs": True,
        "gates": {
            "held_cagr_floor_pp": HELD_CAGR_FLOOR_PP,
            "sealed_mdd_floor_pp": SEALED_MDD_FLOOR_PP,
            "tip_y_floor_pp": TIP_Y_FLOOR_PP,
        },
    }
    (OUT / "screen.json").write_text(json.dumps(screen, indent=2) + "\n", encoding="utf-8")

    charter = "\n".join(
        [
            f"# {CHARTER_ID}",
            "",
            f"Date: {generated[:10]}",
            "Status: **Stage B — Path4 Soft-0050 mutex richer books** · Soft **KEEP** · "
            "broker **false** · cutover **BLOCKED** · no live",
            "Parent: 0kak `PATH4_MUTEX_HIT` Soft-core ON↔OFF",
            f"Register: **{REGISTER}**",
            "",
            "## Question",
            "",
            "Do **clip Soft books** (HI live ETF≤0.50 vs LO ETF≤0.35 / DEF FINBAND) "
            "under the same trail-mutex structure beat sticky HI more than Stage A "
            "zero-0050 OFF — without Path3 hitchhiking?",
            "",
            "## Books",
            "",
            f"- SOFT_HI = live clips `{list(CLIPS_HI)}` + FUSE+COOL",
            f"- SOFT_LO = HI–LO ETF `{list(CLIPS_LO)}` + FUSE+COOL",
            f"- SOFT_DEF = prior FINBAND `{list(CLIPS_DEF)}` + FUSE+COOL",
            "",
            "## Non-goals",
            "",
            "- Path3 flip inputs · live wire · Soft clip ACCEPT · broker · 0kae–0kaj recon",
            "",
            f"Label: `{CHARTER_ID}_{generated[:10]}__PATH4_STAGEB__NO_LIVE`",
            "",
        ]
    )
    write_ops_and_repro_pointer(OPS / f"{CHARTER_ID}.md", REP / f"{CHARTER_ID}.md", charter, kind="charter")
    (OPS / f"{CHARTER_ID}.json").write_text(
        json.dumps(
            {
                "id": CHARTER_ID,
                "register": REGISTER,
                "parent": "0kak",
                "mech": "PATH4_SOFT_0050_MUTEX",
                "soft_keep": True,
                "broker": False,
                "cutover_blocked": True,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    write_repro_pointer(OPS / f"{CHARTER_ID}.json", REP / f"{CHARTER_ID}.json", kind="charter")

    def _fmt(r: dict) -> str:
        return (
            f"| {r['arm']} | {r['verdict_vs_hi']} | {r['held_cagr_lift_pp']} | "
            f"{r['full_cagr_lift_pp']} | {r['sealed_mdd_improve_pp']} | "
            f"{r['tip_ytd_cagr_lift_pp']} | {r['tip_1y_cagr_lift_pp']} |"
        )

    screen_md = "\n".join(
        [
            f"# {SCREEN_ID}",
            "",
            f"Date: {generated[:10]} · Verdict: **`{pack_verdict}`** · "
            f"champion=**`{champion['arm']}`**",
            f"Register: **{REGISTER}** · parent 0kak · beats_parent_held=**{beats_parent}**",
            f"mean ETF tgt HI/LO/DEF = {mean_etf['SOFT_HI']}/{mean_etf['SOFT_LO']}/{mean_etf['SOFT_DEF']}",
            "",
            "## Arms vs sticky SOFT_HI (live Soft Exact + FUSE+COOL)",
            "",
            "| Arm | vs HI | held | full | sealed MDD↑ | tipY | tip1y |",
            "|---|---|---:|---:|---:|---:|---:|",
            *[_fmt(r) for r in summary],
            "",
            f"Repro: `PYTHONPATH=scripts python3 scripts/fin_sat_path4_soft_0050_mutex_stageb.py`",
            "",
            f"Label: `{SCREEN_ID}_{generated[:10]}__{pack_verdict}`",
            "",
        ]
    )
    write_ops_and_repro_pointer(OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", screen_md, kind="screen")
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(screen, indent=2) + "\n", encoding="utf-8")
    write_repro_pointer(OPS / f"{SCREEN_ID}.json", REP / f"{SCREEN_ID}.json", kind="screen")

    next_steps = []
    if pack_verdict == "PATH4_MUTEX_STAGEB_HIT":
        next_steps.append(
            f"Carry `{champion['arm']}` — optional Stage C coexist / e21 smoke — still no live"
        )
        if not beats_parent:
            next_steps.append(
                "Stage B HIT but held ≤ Stage A carve parent — keep both; prefer richer book only if tip/MDD dominate"
            )
    elif pack_verdict == "PATH4_MUTEX_STAGEB_SOFT":
        next_steps.append("Borderline — tip/held disposition; Stage A carve parent may remain champion")
    else:
        next_steps.append(
            "Richer clip books no promote over sticky HI — keep Stage A Soft-core ON↔OFF as Path4 paper champion"
        )
    next_steps.append("Soft KEEP · Path3 keep_0050=True · no live")

    decision = {
        "label": f"{DECISION_ID}_{generated[:10]}__{pack_verdict}__NO_LIVE",
        "verdict": pack_verdict,
        "register": REGISTER,
        "parent": "0kak",
        "champion_arm": champion["arm"],
        "held_cagr_lift_pp": champion["held_cagr_lift_pp"],
        "tip_ytd_cagr_lift_pp": champion["tip_ytd_cagr_lift_pp"],
        "beats_parent_held": beats_parent,
        "parent_stagea_held_cagr_lift_pp": parent_held,
        "soft_keep": True,
        "broker": False,
        "cutover_blocked": True,
        "live_wire": False,
        "next": next_steps,
    }
    decision_md = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: {generated[:10]} · Verdict: **`{pack_verdict}`** · "
            f"champion=**`{champion['arm']}`**",
            f"Register: **{REGISTER}** · Parent: **0kak**",
            "",
            "## Champion vs sticky SOFT_HI",
            "",
            f"- held CAGR lift: **{champion['held_cagr_lift_pp']}** pp",
            f"- full CAGR lift: **{champion['full_cagr_lift_pp']}** pp",
            f"- sealed MDD improve: **{champion['sealed_mdd_improve_pp']}** pp",
            f"- tipY / tip1y: **{champion['tip_ytd_cagr_lift_pp']}** / "
            f"**{champion['tip_1y_cagr_lift_pp']}**",
            f"- beats Stage A parent held: **{beats_parent}** "
            f"(parent held={parent_held})",
            "",
            "## Disposition",
            "",
            "- Soft Exact clip dual-book mutex (HI/LO/DEF) · not Path3 hitchhike.",
            "- Live Soft / Path3 unchanged.",
            "",
            "## Next",
            "",
            *[f"{i+1}. {s}" for i, s in enumerate(next_steps)],
            "",
            f"Label: `{decision['label']}`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{DECISION_ID}.md", REP / f"{DECISION_ID}.md", decision_md, kind="decision pack"
    )
    (OPS / f"{DECISION_ID}.json").write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    write_repro_pointer(OPS / f"{DECISION_ID}.json", REP / f"{DECISION_ID}.json", kind="decision pack")

    print(
        json.dumps(
            {
                "verdict": pack_verdict,
                "champion": champion["arm"],
                "held_cagr_lift_pp": champion["held_cagr_lift_pp"],
                "tip_ytd_cagr_lift_pp": champion["tip_ytd_cagr_lift_pp"],
                "sealed_mdd_improve_pp": champion["sealed_mdd_improve_pp"],
                "beats_parent_held": beats_parent,
                "parent_held": parent_held,
                "mean_etf": mean_etf,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
