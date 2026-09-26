#!/usr/bin/env python3
"""大盤下行 sensor → hold 00632R; clear → sell. Stage A paper.

Charter: research/ops/MKTDOWN_T50_INV_CHARTER.md
Sensors on 0050: RET5≤-3/-5%, DD20≤-5/-8%. Soft-Frozen KEEP.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import cool_t50_inv_satellite_stagea as sat
import e16_soft_frozen_base as soft
from e50_early_stack_combined_nav import FIN, e16_features
from soft_assist_helpers import LIVE_KD
from ta_indicator_catalog import build_low_high_catalog
from within_sleeve_alloc import build_kd_season_tilt_scores, build_pre_exdiv_window_buy_ok

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "mktdown-t50-inv-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "MKTDOWN_T50_INV_CHARTER"
SCREEN_ID = "MKTDOWN_T50_INV_STAGEA_SCREEN"
BASE_ID = sat.BASE_ID
DEF_CODE = sat.DEF_CODE
ALPHAS = (0.50, 1.00)
DEF_UNIT = 0.25

# (sensor_id, kind, window, thresh)
SENSORS = (
    ("RET5_M3", "ret", 5, -0.03),
    ("RET5_M5", "ret", 5, -0.05),
    ("DD20_M5", "dd", 20, -0.05),
    ("DD20_M8", "dd", 20, -0.08),
)


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_sensors(prices_0050: pd.Series) -> dict[str, pd.Series]:
    px = prices_0050.astype(float)
    out: dict[str, pd.Series] = {}
    for sid, kind, win, thr in SENSORS:
        if kind == "ret":
            r = px.pct_change(int(win), fill_method=None)
            out[sid] = (r <= float(thr)).fillna(False)
        else:
            peak = px.rolling(int(win), min_periods=max(5, win // 2)).max()
            dd = px / peak - 1.0
            out[sid] = (dd <= float(thr)).fillna(False)
    return out


def build_sched(target3, cool, gate, *, alpha, listed_from):
    idx = target3.index
    c = cool.reindex(idx).fillna(1.0).astype(float).clip(0.0, 1.0)
    g = gate.reindex(idx).fillna(False).astype(bool) & (idx >= listed_from)
    def_w = pd.Series(0.0, index=idx, dtype=float)
    def_w = def_w.where(~g, float(alpha) * float(DEF_UNIT))
    return pd.DataFrame(
        {
            "Financial": target3["Financial"].astype(float) * c,
            "Telecom": target3["Telecom"].astype(float) * c,
            "0050": target3["0050"].astype(float) * c,
            "DEF": def_w.astype(float),
        },
        index=idx,
    ), float(g.mean()), int(g.sum())


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.8]

    print("loading ...", flush=True)
    market0 = sat.load_market()
    dividends = sat.load_dividends()
    inv = sat.load_inv_bars()
    market, listed_from = sat.attach_inv(market0, inv)

    _p, sleeve, _tgt, regime = e16_features(market0)
    cal = pd.DatetimeIndex(pd.to_datetime(market0["date"]).drop_duplicates().sort_values())
    lows, highs = build_low_high_catalog(market0, cal, list(FIN))
    kd = build_kd_season_tilt_scores(
        market0, dividends, FIN,
        k_thresh=float(LIVE_KD["k_thresh"]),
        season_start=LIVE_KD["season_start"],
        season_end=LIVE_KD["season_end"],
        pre_days=int(LIVE_KD["pre_days"]),
        active_score=float(LIVE_KD["active_score"]),
    )
    buy_ok = build_pre_exdiv_window_buy_ok(
        cal, dividends, FIN, pre_days=int(LIVE_KD["pre_days"]), also_stock_ex=True
    )
    buy_live = sat._buy(kd, lows)
    sell_live = sat._sell(highs)
    score_live = sat._sleeve_score(market0, sleeve, float(sat.LIVE_SLEEVE_ALPHA))
    tgt_live = sat._target_live(score_live, regime)

    px = (
        market0[market0["code"] == "0050"]
        .drop_duplicates("date")
        .set_index("date")["adj_close"]
        .astype(float)
        .sort_index()
    )
    px.index = pd.to_datetime(px.index)
    sensors = build_sensors(px.reindex(tgt_live.index).ffill())
    for sid, g in sensors.items():
        print(f"  sensor {sid} frac={float(g.mean()):.4f}", flush=True)

    fuse_off, _, _ = sat._sim(
        market0, tgt_live, regime, dividends,
        scores=buy_live, buy_ok=buy_ok, sell=sell_live,
        exposure=pd.Series(1.0, index=tgt_live.index),
    )
    cool = sat._cool_from_offense(market0, fuse_off)
    cool.to_frame("cool_exposure").to_csv(OUT / "exposure_cool.csv")

    print(f"{BASE_ID} ...", flush=True)
    base_nav, n_base, _ = sat._sim(
        market0, tgt_live, regime, dividends,
        scores=buy_live, buy_ok=buy_ok, sell=sell_live, exposure=cool,
    )
    base_nav.to_csv(OUT / f"nav_{BASE_ID}.csv", index=False)
    base_w = sat._pack(base_nav)

    books = []
    for sid, _, _, _ in SENSORS:
        for a in ALPHAS:
            books.append((f"MD_{sid}_A{int(a*100):02d}", sid, float(a)))

    rows = []
    tip0 = sat._tip(base_nav, base_nav)
    br = sat._score_row(
        base_w, base_w, tip0, rid=BASE_ID, alpha=0.0, mode="base",
        n_fills=n_base, mean_def=0.0, defend_frac=0.0,
    )
    br["coexist"] = False
    br["sensor"] = "NONE"
    rows.append(br)

    for i, (bid, sid, alpha) in enumerate(books, 1):
        print(f"  [{i}/{len(books)}] {bid} ...", flush=True)
        sched, on_frac, on_days = build_sched(
            tgt_live, cool, sensors[sid], alpha=alpha, listed_from=listed_from
        )
        sched.to_csv(OUT / f"schedule_{bid}.csv")
        nav, n_fills, _ = sat._sim(
            market, tgt_live, regime, dividends,
            scores=buy_live, buy_ok=buy_ok, sell=sell_live, schedule=sched,
        )
        nav.to_csv(OUT / f"nav_{bid}.csv", index=False)
        tip = sat._tip(base_nav, nav)
        row = sat._score_row(
            base_w, sat._pack(nav), tip, rid=bid, alpha=alpha, mode="mktdown",
            n_fills=n_fills, mean_def=float(sched["DEF"].mean()), defend_frac=on_frac,
        )
        row["sensor"] = sid
        row["on_days"] = on_days
        rows.append(row)

    chal = [r for r in rows if r["id"] != BASE_ID]
    hits = [r for r in chal if r["coexist"]]
    softs = [
        r for r in chal
        if r["gates"]["sealed_mdd"] and r["gates"]["held_mdd"] and r["gates"]["tip_mdd_ok"]
        and not r["gates"]["held_cagr_floor"]
    ]
    if hits:
        verdict = "MKTDOWN_INV_HIT"
    elif softs:
        verdict = "MKTDOWN_INV_SOFT"
    elif any(r["gates"]["tip_clean"] for r in chal):
        verdict = "MDD_BLOCK"
    else:
        verdict = "NO_LIFT"

    ranked = sorted(chal, key=lambda r: -float(r["score"]))
    payload = {
        "generated_at_utc": _utc(),
        "label": SCREEN_ID,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "status": verdict,
        "live_wire": False,
        "soft_frozen_keep": True,
        "def_code": DEF_CODE,
        "thesis": "00632R useful in market-down; gate on 0050 RET5/DD20",
        "sensor_frac": {sid: round(float(sensors[sid].mean()), 6) for sid, *_ in SENSORS},
        "baseline": BASE_ID,
        "baseline_windows": base_w,
        "n_challengers": len(chal),
        "n_coexist": len(hits),
        "coexist_ids": [r["id"] for r in sorted(hits, key=lambda r: -r["score"])],
        "soft_ids": [r["id"] for r in softs],
        "best": (sorted(hits, key=lambda r: -r["score"])[0] if hits else (ranked[0] if ranked else None)),
        "ranked": ranked,
    }
    (REP / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2) + "\n")
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2) + "\n")

    lines = [
        "# 大盤下行 × 00632R — Stage A Screen",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Status: **{verdict}** · Soft-Frozen **KEEP** · live wire **false**",
        f"Thesis: 反1 useful in **market-down** · DEF=`{DEF_CODE}`",
        "",
        f"Coexist / HIT: **{len(hits)}** / {len(chal)}",
        "",
        "| book | sensor | α | CAGR↑ held | CAGR↑ seal | MDD↑ held | MDD↑ seal | tip | coexist |",
        "|---|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for r in ranked:
        tip_ok = "Y" if r["gates"]["tip_mdd_ok"] else "N"
        lines.append(
            f"| `{r['id']}` | {r['sensor']} | {r['alpha']:.2f} | "
            f"{r['held_cagr_lift_pp']:+.2f} | {r['sealed_cagr_lift_pp']:+.2f} | "
            f"{r['held_mdd_improve_pp']:+.2f} | {r['sealed_mdd_improve_pp']:+.2f} | "
            f"{tip_ok} | {'Y' if r['coexist'] else 'N'} |"
        )
    lines += [
        "",
        f"Sensor frac: {payload['sensor_frac']}",
        "",
        "Repro: `PYTHONPATH=scripts python3 scripts/mktdown_t50_inv_stagea.py`",
        "",
        f"Label: `{SCREEN_ID}_{payload['generated_at_utc'][:10]}__{verdict}`",
        "",
    ]
    md = "\n".join(lines)
    (REP / f"{SCREEN_ID}.md").write_text(md)
    (OPS / f"{SCREEN_ID}.md").write_text(md)

    decision = {
        "label": "MKTDOWN_T50_INV_DECISION",
        "generated_at_utc": _utc(),
        "status": verdict,
        "live_wire": False,
        "n_coexist": len(hits),
        "coexist_ids": payload["coexist_ids"],
        "soft_ids": payload["soft_ids"],
        "best": None if not payload["best"] else payload["best"]["id"],
        "charter": f"research/ops/{CHARTER_ID}.md",
        "stage_a": f"research/ops/{SCREEN_ID}.md",
    }
    dlines = [
        "# 大盤下行 × 00632R — Decision Pack",
        "",
        f"Date: 2026-09-25 · Generated `{decision['generated_at_utc']}`",
        f"Status: **{verdict}** · Soft-Frozen **KEEP** · live wire **false**",
        "",
        "Human: 00632R 在大盤下行時有用 → gate on 0050 RET5/DD20.",
        "",
        f"Coexist / HIT: **{len(hits)}**.",
        "",
    ]
    if hits:
        b = sorted(hits, key=lambda r: -r["score"])[0]
        dlines += [
            f"Best: `{b['id']}` · held CAGR↑ **{b['held_cagr_lift_pp']:+.2f}** · "
            f"sealed MDD↑ **{b['sealed_mdd_improve_pp']:+.2f}**",
            "",
            "Next: paper observe only — not live.",
            "",
        ]
    elif softs:
        b = softs[0]
        dlines += [
            f"SOFT: `{b['id']}` · held CAGR↑ {b['held_cagr_lift_pp']:+.2f} · "
            f"sealed MDD↑ {b['sealed_mdd_improve_pp']:+.2f}",
            "",
        ]
    else:
        dlines += ["No tip-clean MDD-safe CAGR lift under market-down gates.", ""]
    dlines += [
        "Binding: Soft-Frozen KEEP · no live 00632R without Class D ACCEPT.",
        "",
        f"Label: `MKTDOWN_T50_INV_DECISION_2026-09-25__{verdict}`",
        "",
    ]
    (OPS / "MKTDOWN_T50_INV_DECISION_PACK.json").write_text(json.dumps(decision, indent=2) + "\n")
    (OPS / "MKTDOWN_T50_INV_DECISION_PACK.md").write_text("\n".join(dlines))
    print(json.dumps({
        "verdict": verdict,
        "n_coexist": len(hits),
        "soft_ids": payload["soft_ids"],
        "sensor_frac": payload["sensor_frac"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
