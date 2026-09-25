#!/usr/bin/env python3
"""Held-|MDD|≤17% Stage R1 paper screen (charter 2026-09-25).

Offense = paper LIVE_STACK twin under current Stage-E DEFAULT books.
Finite new actuators only (HARD_FLOOR / PROXY_CIRCUIT / STEP_SCALE).
Controls: BASE_LIVE · CTRL_DH_dd06 (expected miss).

Soft-Frozen tip KEEP · no live wire · no ledger revert.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import e16_soft_frozen_base as soft
import e22_dividend_accounting as e22div
import e45_defend_handoff_stagea_screen as dh
from e45_defend_handoff_helpers import DD_THRESHOLD, VOL_Z_THRESHOLD
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, load_market, window_stats
from e50_early_stack_combined_nav import FIN, e16_features, simulate_core
from portfolio_capital import DEFAULT_CAPITAL
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp
from soft_assist_helpers import LIVE_KD
from tw_share_lots import BOARD_LOT
from within_sleeve_alloc import (
    FIN_PRE_EXDIV_KD,
    TEL_EQUAL,
    build_kd_season_tilt_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "held-mdd17-target-r1"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "HELD_MDD17_TARGET_PAPER_CHARTER"
SCREEN_ID = "HELD_MDD17_TARGET_R1_SCREEN"
ARTIFACT = "research/ops/HELD_MDD17_TARGET_R1_SCREEN.md"

# Target: |MDD| ≤ 17%  ⟺  max_drawdown >= -0.17
MDD_FLOOR = -0.17
GIVEBACK_CAP_PP = 3.0
HELDOUT = "heldout_2019_plus"
E22_VERSION = e22div.DEFAULT_BOOKS_VERSION

HARD_TRIGGERS = (0.08, 0.10, 0.12, 0.15)
HARD_FLOORS = (0.0, 0.25, 0.50)
HARD_RECOVER = 0.97

PROXY_XS = (0.08, 0.10, 0.12, 0.15)
PROXY_FLOORS = (0.0, 0.25, 0.50)
PROXY_COOLDOWN = 5

STEP_SCALES = (0.20, 0.25, 0.30)
STEP_FLOORS = (0.0, 0.25)


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _nav_series(nav: pd.DataFrame) -> pd.Series:
    d = nav.copy()
    d["date"] = pd.to_datetime(d["date"])
    return d.set_index("date")["nav"].astype(float).sort_index()


def _pack_windows(nav: pd.DataFrame) -> dict[str, Any]:
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


def _tip_windows(base_nav: pd.DataFrame, chal_nav: pd.DataFrame) -> dict[str, Any]:
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
            out[wname] = {
                "mdd_improve_pp": None,
                "cagr_giveback_pp": None,
                "gate": "INSUFFICIENT",
            }
            continue
        bn = b["nav"].astype(float) / float(b["nav"].iloc[0])
        cn = c["nav"].astype(float) / float(c["nav"].iloc[0])
        b_mdd = float((bn / bn.cummax() - 1.0).min())
        c_mdd = float((cn / cn.cummax() - 1.0).min())
        years = (len(b) - 1) / 252.0
        bc = float(bn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        cc = float(cn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        gb = cagr_delta_pp(bc, cc)
        out[wname] = {
            "mdd_improve_pp": round(float(mdd_delta_pp(b_mdd, c_mdd)), 4),
            "cagr_giveback_pp": None if gb is None else round(float(gb), 4),
            "gate": "PASS",
        }
    return out


def _held_delta(base_w: dict[str, Any], chal_w: dict[str, Any]) -> dict[str, Any] | None:
    b, c = base_w.get(HELDOUT), chal_w.get(HELDOUT)
    if not b or not c or b.get("cagr") is None or c.get("cagr") is None:
        return None
    gb = cagr_delta_pp(b.get("cagr"), c.get("cagr"))
    return {
        "mdd_improve_pp": round(
            float(mdd_delta_pp(b.get("max_drawdown"), c.get("max_drawdown"))), 4
        ),
        "cagr_giveback_pp": None if gb is None else round(float(gb), 4),
        "base_cagr": b["cagr"],
        "chal_cagr": c["cagr"],
        "base_mdd": b["max_drawdown"],
        "chal_mdd": c["max_drawdown"],
        "hit_mdd17": float(c["max_drawdown"]) >= MDD_FLOOR,
    }


def _exposure_hard_floor(nav: pd.Series, trigger: float, floor: float, recover: float) -> pd.Series:
    """Causal: when peak DD <= -trigger, hold exposure=floor until recover*peak."""
    out = pd.Series(1.0, index=nav.index, dtype=float)
    peak = float(nav.iloc[0])
    defending = False
    for i, dt in enumerate(nav.index):
        v = float(nav.iloc[i])
        if not defending:
            peak = max(peak, v)
            dd = v / peak - 1.0
            if dd <= -float(trigger):
                defending = True
                out.iloc[i] = float(floor)
        else:
            out.iloc[i] = float(floor)
            if v >= peak * float(recover):
                defending = False
                peak = v
                out.iloc[i] = 1.0
    return out


def _exposure_proxy_circuit(
    dates: pd.DatetimeIndex, proxy_mdd63: pd.Series, x: float, floor: float
) -> pd.Series:
    out = pd.Series(1.0, index=dates, dtype=float)
    cool = 0
    px = proxy_mdd63.reindex(dates).fillna(0.0)
    for i, _dt in enumerate(dates):
        if cool > 0:
            cool -= 1
            out.iloc[i] = float(floor)
            continue
        if float(px.iloc[i]) <= -float(x):
            out.iloc[i] = float(floor)
            cool = PROXY_COOLDOWN
        else:
            out.iloc[i] = 1.0
    return out


def _exposure_step_scale(nav: pd.Series, scale: float, floor: float) -> pd.Series:
    out = pd.Series(1.0, index=nav.index, dtype=float)
    peak = float(nav.iloc[0])
    for i, _dt in enumerate(nav.index):
        v = float(nav.iloc[i])
        peak = max(peak, v)
        dd = v / peak - 1.0
        if dd >= 0:
            out.iloc[i] = 1.0
        else:
            out.iloc[i] = float(max(floor, 1.0 + dd / float(scale)))
    return out


def _run_book(
    market: pd.DataFrame,
    target: pd.DataFrame,
    regime: pd.Series,
    dividends: pd.DataFrame,
    *,
    scores: pd.DataFrame,
    buy_ok: pd.DataFrame,
    exposure: pd.Series | None,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = dict(
        apply_e22=True,
        apply_stock_div=True,
        capital=float(DEFAULT_CAPITAL),
        lot_size=int(BOARD_LOT),
        financial_alloc=FIN_PRE_EXDIV_KD,
        telecom_alloc=TEL_EQUAL,
        fin_name_scores=scores,
        fin_buy_ok=buy_ok,
        e22_version=E22_VERSION,
    )
    if exposure is not None:
        kwargs["e45_exposure"] = exposure.astype(float)
    nav, fills, meta = simulate_core(market, target, regime, dividends, **kwargs)
    if not bool(meta.get("exact_t1_ok")):
        raise RuntimeError("exact_t1_ok failed")
    return {"nav": nav, "n_fills": int(len(fills)), "meta": meta, "mean_exp": meta.get("mean_e45_exposure")}


def _verdict(rows: list[dict[str, Any]]) -> tuple[str, list[str]]:
    ok: list[str] = []
    hit_fail: list[str] = []
    for r in rows:
        if r.get("track") in ("BASE", "CTRL"):
            continue
        h = r.get("heldout_delta") or {}
        tip = r.get("tip") or {}
        if not h.get("hit_mdd17"):
            continue
        tips_ok = all(
            (tip.get(w) or {}).get("gate") == "PASS"
            and (tip.get(w) or {}).get("mdd_improve_pp") is not None
            and float((tip.get(w) or {}).get("mdd_improve_pp")) >= 0.0
            for w in ("ytd", "trailing_1y")
        )
        gb = h.get("cagr_giveback_pp")
        if tips_ok and gb is not None and float(gb) <= GIVEBACK_CAP_PP:
            ok.append(r["id"])
        else:
            hit_fail.append(r["id"])
    if ok:
        return "MDD17_HIT_CAGR_OK", ok
    if hit_fail:
        return "MDD17_HIT_CAGR_FAIL", hit_fail
    return "NO_HIT", []


def main() -> int:
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.8]
    OUT.mkdir(parents=True, exist_ok=True)
    REP.mkdir(parents=True, exist_ok=True)
    OPS.mkdir(parents=True, exist_ok=True)

    print("loading ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _prices, _sleeve, target, regime = e16_features(market)
    cal = pd.DatetimeIndex(pd.to_datetime(market["date"]).drop_duplicates().sort_values())
    kd_scores = build_kd_season_tilt_scores(
        market,
        dividends,
        FIN,
        k_thresh=float(LIVE_KD["k_thresh"]),
        season_start=LIVE_KD["season_start"],
        season_end=LIVE_KD["season_end"],
        pre_days=int(LIVE_KD["pre_days"]),
        active_score=float(LIVE_KD["active_score"]),
    )
    kd_ok = build_pre_exdiv_window_buy_ok(
        cal, dividends, FIN, pre_days=int(LIVE_KD["pre_days"]), also_stock_ex=True
    )

    print(f"BASE_LIVE books={E22_VERSION} ...", flush=True)
    base = _run_book(
        market, target, regime, dividends, scores=kd_scores, buy_ok=kd_ok, exposure=None
    )
    base_nav_s = _nav_series(base["nav"])
    base_w = _pack_windows(base["nav"])
    feat = dh._risk_features(market, base_nav_s)
    dates = pd.DatetimeIndex(base_nav_s.index)

    recipes: list[tuple[str, str, pd.Series | None, dict[str, Any]]] = [
        ("BASE_LIVE", "BASE", None, {}),
    ]

    # Control: live DH_dd06
    exp_dh = dh._build_exposure(dates, feat, DD_THRESHOLD, VOL_Z_THRESHOLD)
    recipes.append(
        (
            "CTRL_DH_dd06",
            "CTRL",
            exp_dh,
            {"dd": DD_THRESHOLD, "vz": VOL_Z_THRESHOLD, "shrink": 0.50},
        )
    )

    for trig in HARD_TRIGGERS:
        for floor in HARD_FLOORS:
            rid = f"HARD_FLOOR_t{int(trig*100):02d}_f{int(floor*100):02d}"
            exp = _exposure_hard_floor(base_nav_s, trig, floor, HARD_RECOVER)
            recipes.append(
                (rid, "HARD_FLOOR", exp, {"trigger": trig, "floor": floor, "recover": HARD_RECOVER})
            )

    for x in PROXY_XS:
        for floor in PROXY_FLOORS:
            rid = f"PROXY_x{int(x*100):02d}_f{int(floor*100):02d}"
            exp = _exposure_proxy_circuit(dates, feat["proxy_mdd63"], x, floor)
            recipes.append((rid, "PROXY_CIRCUIT", exp, {"x": x, "floor": floor}))

    for scale in STEP_SCALES:
        for floor in STEP_FLOORS:
            rid = f"STEP_s{int(scale*100):02d}_f{int(floor*100):02d}"
            exp = _exposure_step_scale(base_nav_s, scale, floor)
            recipes.append((rid, "STEP_SCALE", exp, {"scale": scale, "floor": floor}))

    rows: list[dict[str, Any]] = []
    for rid, track, exposure, params in recipes:
        print(f"sim {rid} ...", flush=True)
        if rid == "BASE_LIVE":
            book = base
        else:
            book = _run_book(
                market,
                target,
                regime,
                dividends,
                scores=kd_scores,
                buy_ok=kd_ok,
                exposure=exposure,
            )
        chal_w = _pack_windows(book["nav"]) if rid != "BASE_LIVE" else base_w
        held = (
            {
                "mdd_improve_pp": 0.0,
                "cagr_giveback_pp": 0.0,
                "base_cagr": base_w[HELDOUT]["cagr"],
                "chal_cagr": base_w[HELDOUT]["cagr"],
                "base_mdd": base_w[HELDOUT]["max_drawdown"],
                "chal_mdd": base_w[HELDOUT]["max_drawdown"],
                "hit_mdd17": float(base_w[HELDOUT]["max_drawdown"]) >= MDD_FLOOR,
            }
            if rid == "BASE_LIVE"
            else _held_delta(base_w, chal_w)
        )
        tip = (
            {
                "ytd": {"mdd_improve_pp": 0.0, "cagr_giveback_pp": 0.0, "gate": "PASS"},
                "trailing_1y": {"mdd_improve_pp": 0.0, "cagr_giveback_pp": 0.0, "gate": "PASS"},
            }
            if rid == "BASE_LIVE"
            else _tip_windows(base["nav"], book["nav"])
        )
        mean_exp = 1.0 if exposure is None else float(np.asarray(exposure, dtype=float).mean())
        row = {
            "id": rid,
            "track": track,
            "params": params,
            "windows": chal_w if rid != "BASE_LIVE" else base_w,
            "heldout_delta": held,
            "tip": tip,
            "mean_exposure": round(mean_exp, 4),
            "n_fills": book["n_fills"],
        }
        rows.append(row)
        book["nav"].to_csv(OUT / f"nav_{rid}.csv", index=False)
        h = held or {}
        print(
            f"  held MDD {100*float(h.get('chal_mdd') or 0):.2f}% "
            f"hit17={h.get('hit_mdd17')} giveback={h.get('cagr_giveback_pp')} "
            f"mean_exp={mean_exp:.3f}",
            flush=True,
        )

    verdict, winners = _verdict(rows)
    summary = {
        "label": SCREEN_ID,
        "charter": CHARTER_ID,
        "generated_at_utc": _utc(),
        "status": "PAPER_ONLY",
        "live_wire": False,
        "soft_frozen_keep": True,
        "e22_books_version": E22_VERSION,
        "target": {
            "held_mdd_floor": MDD_FLOOR,
            "meaning": "|MDD| <= 17%  iff  max_drawdown >= -0.17",
            "giveback_cap_pp": GIVEBACK_CAP_PP,
            "heldout_window": HELDOUT,
        },
        "base_held": base_w[HELDOUT],
        "verdict": verdict,
        "winners": winners,
        "n_recipes": len(rows),
        "rows": rows,
        "stale_note": (
            "2026-09-13 MENU3 held MDD -17.2% used DEFAULT E22_v2s_tw; "
            "this screen uses current Stage-E DEFAULT on current ledger."
        ),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (OPS / "HELD_MDD17_TARGET_R1_SCREEN.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    # Markdown report
    lines = [
        "# Held-|MDD|≤17% Stage R1 Screen",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        f"Books: `{E22_VERSION}` · Soft-Frozen **KEEP** · live wire **False**",
        f"Base held-out: CAGR `{100*float(base_w[HELDOUT]['cagr']):.2f}%` · "
        f"MDD `{100*float(base_w[HELDOUT]['max_drawdown']):.2f}%`",
        f"Target: `max_drawdown >= {MDD_FLOOR}` (|MDD|≤17%) · giveback cap `{GIVEBACK_CAP_PP} pp`",
        f"Verdict: **`{verdict}`** · winners: `{winners}`",
        "",
        "## Leaderboard (held-out)",
        "",
        "| id | track | held CAGR | held MDD | hit17 | ΔCAGR gb pp | MDD↑ pp | mean exp | tip ytd↑ | tip 1y↑ |",
        "|---|---|---:|---:|---|---:|---:|---:|---:|---:|",
    ]
    ranked = sorted(
        rows,
        key=lambda r: (
            0 if (r.get("heldout_delta") or {}).get("hit_mdd17") else 1,
            -float((r.get("heldout_delta") or {}).get("chal_mdd") or -9),
            float((r.get("heldout_delta") or {}).get("cagr_giveback_pp") or 99),
        ),
    )
    for r in ranked:
        h = r.get("heldout_delta") or {}
        tip = r.get("tip") or {}
        w = (r.get("windows") or {}).get(HELDOUT) or {}
        lines.append(
            "| `{id}` | {track} | {cagr} | {mdd} | {hit} | {gb} | {md} | {mex} | {ty} | {t1} |".format(
                id=r["id"],
                track=r["track"],
                cagr="n/a" if w.get("cagr") is None else f"{100*float(w['cagr']):.2f}%",
                mdd="n/a" if w.get("max_drawdown") is None else f"{100*float(w['max_drawdown']):.2f}%",
                hit=h.get("hit_mdd17"),
                gb=h.get("cagr_giveback_pp"),
                md=h.get("mdd_improve_pp"),
                mex=r.get("mean_exposure"),
                ty=(tip.get("ytd") or {}).get("mdd_improve_pp"),
                t1=(tip.get("trailing_1y") or {}).get("mdd_improve_pp"),
            )
        )
    lines += [
        "",
        "## Reading",
        "",
        "- `hit17=True` means held |MDD| ≤ 17%.",
        "- Controls `BASE_LIVE` / `CTRL_DH_dd06` document the stale −17% gap under current Stage-E data.",
        "- Soft-Frozen tip untouched; even HIT → paper observe only.",
        "",
        f"Repro: `repro/held-mdd17-target-r1/` · Charter: `{CHARTER_ID}`",
        "",
        f"Label: `{SCREEN_ID}_{summary['generated_at_utc'][:10]}__{verdict}`",
        "",
    ]
    text = "\n".join(lines)
    (REP / "HELD_MDD17_TARGET_R1_SCREEN.md").write_text(text, encoding="utf-8")
    (OPS / "HELD_MDD17_TARGET_R1_SCREEN.md").write_text(text, encoding="utf-8")
    (REPRO / "README.md").write_text(
        "\n".join(
            [
                "# Held-|MDD|≤17% R1 repro",
                "",
                f"Verdict: **{verdict}**",
                "Soft-Frozen KEEP · paper only.",
                "",
                "```bash",
                "PYTHONPATH=scripts python3 scripts/held_mdd17_target_r1_screen.py",
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps({"verdict": verdict, "winners": winners, "base_held": base_w[HELDOUT]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
