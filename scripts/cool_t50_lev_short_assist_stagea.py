#!/usr/bin/env python3
"""COOL × 00631L short-assist Stage A — tracks THIN / CONFIRM / STOP / RESIDUAL.

Charter: research/ops/COOL_T50_LEV_SHORT_ASSIST_STAGEA_CHARTER.md
Soft-Frozen KEEP · no live wire · no near-flat policy change.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

import cool_t50_inv_satellite_stagea as sat
import cool_t50_lev_rebound_stagea as reb
import e45_defend_handoff_stagea_screen as stagea
from cool_c8_proxy_observe_helpers import EXIT_X
from live_config import LIVE_FUSE_SOFT_SELL_BOOST

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "cool-t50-lev-short-assist-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "COOL_T50_LEV_SHORT_ASSIST_STAGEA_CHARTER"
SCREEN_ID = "COOL_T50_LEV_SHORT_ASSIST_STAGEA_SCREEN"
DECISION_ID = "COOL_T50_LEV_SHORT_ASSIST_DECISION_PACK"
BASE_ID = "BASE_LIVE_FUSE_COOL"
OFF_CODE = "00631L"
OFF_PRICE = ROOT / "data" / "def_proxies" / "00631L_ohlcv.csv"
SELL_AMP = float(LIVE_FUSE_SOFT_SELL_BOOST)


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _0050_rets(market0: pd.DataFrame, idx: pd.DatetimeIndex) -> tuple[pd.Series, pd.Series]:
    m = market0.copy()
    m["date"] = pd.to_datetime(m["date"])
    sub = m[m["code"].astype(str) == "0050"].sort_values("date")
    px = sub.set_index("date")["close"].astype(float).reindex(idx).ffill()
    ret1 = px.pct_change(1)
    ret3 = px.pct_change(3)
    return ret1, ret3


def _off_close(off_bars: pd.DataFrame, idx: pd.DatetimeIndex) -> pd.Series:
    o = off_bars.copy()
    o["date"] = pd.to_datetime(o["date"])
    return o.set_index("date")["close"].astype(float).reindex(idx).ffill()


def build_schedule(
    target3: pd.DataFrame,
    cool: pd.Series,
    *,
    alpha: float,
    hold_h: int,
    listed_from: pd.Timestamp,
    track: str,
    confirm: str | None = None,
    stop: float | None = None,
    ret1: pd.Series | None = None,
    ret3: pd.Series | None = None,
    proxy: pd.Series | None = None,
    off_px: pd.Series | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    idx = target3.index
    c = cool.reindex(idx).fillna(1.0).astype(float).clip(0.0, 1.0)
    listed = pd.Series(idx >= listed_from, index=idx)
    exits = reb.cool_exits(c)
    meta: dict[str, Any] = {"track": track, "confirm": confirm, "stop": stop}

    # Candidate entry days
    entry = exits & listed
    if track == "CONFIRM":
        assert ret1 is not None and ret3 is not None and proxy is not None
        if confirm == "RET1":
            entry = entry & (ret1.reindex(idx) > 0)
        elif confirm == "RET3":
            entry = entry & (ret3.reindex(idx) > 0)
        elif confirm == "RET1_PX":
            entry = entry & (ret1.reindex(idx) > 0) & (proxy.reindex(idx) > -float(EXIT_X))
        else:
            raise ValueError(confirm)

    pulse = pd.Series(False, index=idx)
    entry_locs = [i for i, v in enumerate(entry.to_numpy()) if bool(v)]
    n = len(idx)
    entry_of = pd.Series(-1, index=idx, dtype=int)
    for i0 in entry_locs:
        for k in range(int(hold_h)):
            j = i0 + k
            if j < n:
                pulse.iloc[j] = True
                if int(entry_of.iloc[j]) < 0:
                    entry_of.iloc[j] = i0

    if track == "RESIDUAL":
        # Size from released residual at exit (cool prev < 1)
        prev = c.shift(1).fillna(1.0)
        released = (1.0 - prev).clip(lower=0.0)
        off_w = pd.Series(0.0, index=idx, dtype=float)
        for i0 in entry_locs:
            w = float(alpha) * float(released.iloc[i0])
            w = min(w, float(alpha))
            for k in range(int(hold_h)):
                j = i0 + k
                if j < n and bool(listed.iloc[j]):
                    off_w.iloc[j] = w
    else:
        off_w = pd.Series(0.0, index=idx, dtype=float)
        off_w = off_w.where(~pulse, float(alpha))
        off_w = off_w.where(listed, 0.0)

        if track == "STOP" and stop is not None and off_px is not None:
            # Clear remaining pulse if drawdown from entry close <= -stop
            px = off_px.reindex(idx).astype(float)
            active_entry = -1
            entry_px = float("nan")
            for i in range(n):
                if int(entry_of.iloc[i]) >= 0 and (
                    active_entry != int(entry_of.iloc[i]) or not bool(pulse.iloc[i])
                ):
                    active_entry = int(entry_of.iloc[i])
                    entry_px = float(px.iloc[active_entry])
                if not bool(pulse.iloc[i]) or not bool(listed.iloc[i]):
                    off_w.iloc[i] = 0.0
                    continue
                if entry_px == entry_px and entry_px > 0:
                    dd = float(px.iloc[i]) / entry_px - 1.0
                    if dd <= -float(stop):
                        # zero from here through end of this pulse
                        e0 = active_entry
                        for j in range(i, min(n, e0 + int(hold_h))):
                            if int(entry_of.iloc[j]) == e0:
                                off_w.iloc[j] = 0.0
                                pulse.iloc[j] = False

    soft_scale = c * (1.0 - off_w).clip(lower=0.0)
    sched = pd.DataFrame(
        {
            "Financial": target3["Financial"].astype(float) * soft_scale,
            "Telecom": target3["Telecom"].astype(float) * soft_scale,
            "0050": target3["0050"].astype(float) * soft_scale,
            "DEF": off_w.astype(float),
        },
        index=idx,
    )
    meta.update(
        {
            "n_entries": int(len(entry_locs)),
            "pulse_frac": round(float((off_w > 0).mean()), 6),
            "mean_off": round(float(off_w.mean()), 6),
        }
    )
    return sched, meta


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    assert OFF_PRICE.exists(), OFF_PRICE
    assert sat.soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.8]

    sat.DEF_CODE = OFF_CODE
    sat.DEF_PRICE = OFF_PRICE

    print("loading ...", flush=True)
    market0 = sat.load_market()
    dividends = sat.load_dividends()
    off = sat.load_inv_bars()
    market, listed_from = sat.attach_inv(market0, off)

    from e50_early_stack_combined_nav import FIN, e16_features
    from soft_assist_helpers import LIVE_KD
    from ta_indicator_catalog import build_low_high_catalog
    from within_sleeve_alloc import build_kd_season_tilt_scores, build_pre_exdiv_window_buy_ok

    _p, sleeve, _tgt, regime = e16_features(market0)
    cal = pd.DatetimeIndex(pd.to_datetime(market0["date"]).drop_duplicates().sort_values())
    lows, highs = build_low_high_catalog(market0, cal, list(FIN))
    kd = build_kd_season_tilt_scores(
        market0,
        dividends,
        FIN,
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
    sell_live = sat._sell(highs, SELL_AMP)
    score_live = sat._sleeve_score(market0, sleeve, float(sat.LIVE_SLEEVE_ALPHA))
    tgt_live = sat._target_live(score_live, regime)

    print("offense + cool + features ...", flush=True)
    fuse_off, _, _ = sat._sim(
        market0,
        tgt_live,
        regime,
        dividends,
        scores=buy_live,
        buy_ok=buy_ok,
        sell=sell_live,
        exposure=pd.Series(1.0, index=tgt_live.index),
    )
    cool = sat._cool_from_offense(market0, fuse_off)
    cool.to_frame("cool_exposure").to_csv(OUT / "exposure_cool.csv")
    nav_s = stagea._nav_series(fuse_off)
    feat = stagea._risk_features(market0, nav_s)
    proxy = feat["proxy_mdd63"].reindex(tgt_live.index).fillna(0.0)
    ret1, ret3 = _0050_rets(market0, tgt_live.index)
    off_px = _off_close(off, tgt_live.index)
    n_exits = int(reb.cool_exits(cool).sum())
    defend_frac = float((cool < 1.0 - 1e-12).mean())
    print(f"exits={n_exits} defend_frac={defend_frac:.4f} listed={listed_from.date()}", flush=True)

    print(f"{BASE_ID} ...", flush=True)
    base_nav, n_base, _ = sat._sim(
        market0,
        tgt_live,
        regime,
        dividends,
        scores=buy_live,
        buy_ok=buy_ok,
        sell=sell_live,
        exposure=cool,
    )
    base_nav.to_csv(OUT / f"nav_{BASE_ID}.csv", index=False)
    base_w = sat._pack(base_nav)

    # books: (id, track, alpha, H, confirm, stop)
    books: list[tuple] = [(BASE_ID, "BASE", 0.0, 0, None, None)]
    for a in (0.03, 0.05, 0.08):
        for h in (1, 2):
            books.append((f"THIN_A{int(a*100):02d}_H{h}", "THIN", a, h, None, None))
    for conf in ("RET1", "RET3", "RET1_PX"):
        for a in (0.10, 0.25):
            for h in (3, 5):
                books.append(
                    (f"CONF_{conf}_A{int(a*100):02d}_H{h}", "CONFIRM", a, h, conf, None)
                )
    for a in (0.10, 0.25):
        for h in (5, 10):
            for st in (0.03, 0.05):
                books.append(
                    (
                        f"STOP_A{int(a*100):02d}_H{h}_S{int(st*100):02d}",
                        "STOP",
                        a,
                        h,
                        None,
                        st,
                    )
                )
    for a in (0.50, 1.00):
        for h in (1, 2, 3):
            books.append((f"RES_A{int(a*100):02d}_H{h}", "RESIDUAL", a, h, None, None))
    books.append(("PARENT_A10_H5", "THIN", 0.10, 5, None, None))  # parent ref cell

    rows: list[dict[str, Any]] = []
    for i, (bid, track, alpha, hold_h, conf, stop) in enumerate(books, 1):
        print(f"  [{i}/{len(books)}] {bid} ...", flush=True)
        if track == "BASE":
            tip = sat._tip(base_nav, base_nav)
            row = sat._score_row(
                base_w,
                base_w,
                tip,
                rid=bid,
                alpha=0.0,
                mode="base",
                n_fills=n_base,
                mean_def=0.0,
                defend_frac=defend_frac,
            )
            row.update({"track": "BASE", "hold_h": None, "confirm": None, "stop": None, "coexist": False})
            rows.append(row)
            continue
        sched, meta = build_schedule(
            tgt_live,
            cool,
            alpha=float(alpha),
            hold_h=int(hold_h),
            listed_from=listed_from,
            track=str(track),
            confirm=conf,
            stop=stop,
            ret1=ret1,
            ret3=ret3,
            proxy=proxy,
            off_px=off_px,
        )
        sched.to_csv(OUT / f"schedule_{bid}.csv")
        nav, n_fills, _ = sat._sim(
            market,
            tgt_live,
            regime,
            dividends,
            scores=buy_live,
            buy_ok=buy_ok,
            sell=sell_live,
            schedule=sched,
        )
        nav.to_csv(OUT / f"nav_{bid}.csv", index=False)
        tip = sat._tip(base_nav, nav)
        row = sat._score_row(
            base_w,
            sat._pack(nav),
            tip,
            rid=bid,
            alpha=float(alpha),
            mode=track.lower(),
            n_fills=n_fills,
            mean_def=float(meta["mean_off"]),
            defend_frac=defend_frac,
        )
        row.update(
            {
                "track": track,
                "hold_h": int(hold_h),
                "confirm": conf,
                "stop": stop,
                "n_entries": meta["n_entries"],
                "pulse_frac": meta["pulse_frac"],
            }
        )
        rows.append(row)

    chal = [r for r in rows if r["track"] not in ("BASE",)]
    # PARENT is reference — keep in chal for ranking but tag
    hits = [r for r in chal if r["coexist"] and r["id"] != "PARENT_A10_H5"]
    softs = [
        r
        for r in chal
        if r["id"] != "PARENT_A10_H5"
        and r["gates"]["sealed_mdd"]
        and r["gates"]["held_mdd"]
        and r["gates"]["tip_mdd_ok"]
        and not r["gates"]["held_cagr_floor"]
    ]
    if hits:
        verdict = "SHORT_ASSIST_HIT"
    elif softs:
        verdict = "SHORT_ASSIST_SOFT"
    elif any(r["gates"]["tip_clean"] for r in chal if r["id"] != "PARENT_A10_H5"):
        verdict = "MDD_BLOCK"
    else:
        verdict = "NO_LIFT"

    ranked = sorted(
        [r for r in chal if r["id"] != "PARENT_A10_H5"],
        key=lambda r: -float(r["score"]),
    )
    by_track: dict[str, list] = {}
    for r in ranked:
        by_track.setdefault(r["track"], []).append(r["id"])

    payload = {
        "generated_at_utc": _utc(),
        "label": SCREEN_ID,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "status": verdict,
        "live_wire": False,
        "soft_frozen_keep": True,
        "near_flat_policy_change": False,
        "off_code": OFF_CODE,
        "sell_amp": SELL_AMP,
        "n_cool_exits": n_exits,
        "cool_defend_frac": round(defend_frac, 6),
        "listed_from": str(listed_from.date()),
        "baseline": BASE_ID,
        "n_challengers": len(ranked),
        "n_coexist": len(hits),
        "coexist_ids": [r["id"] for r in sorted(hits, key=lambda r: -r["score"])],
        "soft_ids": [r["id"] for r in softs],
        "best": (sorted(hits, key=lambda r: -r["score"])[0] if hits else (ranked[0] if ranked else None)),
        "ranked": ranked,
        "by_track_top": {k: v[:5] for k, v in by_track.items()},
        "parent_ref": next(r for r in rows if r["id"] == "PARENT_A10_H5"),
    }
    (REP / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2) + "\n")
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2) + "\n")

    lines = [
        "# COOL × 00631L 短線輔助 — Stage A Screen",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Status: **`{verdict}`** · Soft-Frozen **KEEP** · live wire **false** · near-flat policy **OUT**",
        f"OFF=`{OFF_CODE}` · sell_amp=**{SELL_AMP:g}** · exits=**{n_exits}** · defend_frac=**{defend_frac:.2%}**",
        "",
        f"Coexist / HIT: **{len(hits)}** / {len(ranked)} · SOFT: **{len(softs)}**",
        "",
        "## Top 15 by score",
        "",
        "| book | track | α | H | CAGR↑h | CAGR↑s | MDD↑h | MDD↑s | tip | hit |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for r in ranked[:15]:
        tip_ok = "Y" if r["gates"]["tip_mdd_ok"] else "N"
        lines.append(
            f"| `{r['id']}` | {r['track']} | {r['alpha']:.2f} | {r['hold_h']} | "
            f"{r['held_cagr_lift_pp']:+.2f} | {r['sealed_cagr_lift_pp']:+.2f} | "
            f"{r['held_mdd_improve_pp']:+.2f} | {r['sealed_mdd_improve_pp']:+.2f} | "
            f"{tip_ok} | {'Y' if r['coexist'] else 'N'} |"
        )
    pref = payload["parent_ref"]
    lines += [
        "",
        "## Parent ref",
        "",
        f"`PARENT_A10_H5`: CAGR↑h {pref['held_cagr_lift_pp']:+.2f} · MDD↑s {pref['sealed_mdd_improve_pp']:+.2f} · tip={'Y' if pref['gates']['tip_mdd_ok'] else 'N'}",
        "",
        "## Binding",
        "",
        "1. Soft-Frozen + COOL **KEEP**.",
        "2. No near-flat floor change in this charter.",
        "3. Even HIT → paper observe only; live `00631L` needs Class D ACCEPT.",
        "",
        "Repro: `PYTHONPATH=scripts python3 scripts/cool_t50_lev_short_assist_stagea.py`",
        "",
        f"Label: `{SCREEN_ID}_{payload['generated_at_utc'][:10]}__{verdict}`",
        "",
    ]
    md = "\n".join(lines)
    (REP / f"{SCREEN_ID}.md").write_text(md)
    (OPS / f"{SCREEN_ID}.md").write_text(md)

    decision = {
        "label": DECISION_ID,
        "generated_at_utc": _utc(),
        "status": verdict,
        "live_wire": False,
        "n_coexist": len(hits),
        "coexist_ids": payload["coexist_ids"],
        "soft_ids": payload["soft_ids"],
        "best": None if not payload["best"] else payload["best"]["id"],
        "charter": f"research/ops/{CHARTER_ID}.md",
        "stage_a": f"research/ops/{SCREEN_ID}.md",
        "tracks": ["THIN", "CONFIRM", "STOP", "RESIDUAL"],
        "excluded": ["near_flat_policy"],
    }
    dlines = [
        "# COOL × 00631L 短線輔助 — Decision Pack (Stage A)",
        "",
        f"Date: 2026-09-26 · Generated `{decision['generated_at_utc']}`",
        f"Status: **{verdict}** · Soft-Frozen **KEEP** · live wire **false**",
        "",
        "Tracks: THIN · CONFIRM · STOP · RESIDUAL · **near-flat OUT**",
        "",
        f"HIT: **{len(hits)}** · SOFT: **{len(softs)}**.",
        "",
    ]
    if hits:
        b = sorted(hits, key=lambda r: -r["score"])[0]
        dlines += [
            f"Best: `{b['id']}` ({b['track']}) · held CAGR↑ **{b['held_cagr_lift_pp']:+.2f}** · "
            f"sealed MDD↑ **{b['sealed_mdd_improve_pp']:+.2f}**",
            "",
            "Next: paper observe ballot only.",
            "",
        ]
    elif softs:
        b = sorted(softs, key=lambda r: -r["score"])[0]
        dlines += [
            f"SOFT best: `{b['id']}` ({b['track']}) · held CAGR↑ {b['held_cagr_lift_pp']:+.2f} · "
            f"sealed MDD↑ {b['sealed_mdd_improve_pp']:+.2f}.",
            "",
            "Binding: Soft-Frozen KEEP · no live without new ACCEPT.",
            "",
        ]
    else:
        dlines += [
            "No tip-clean MDD-safe lift across tracks 1–4.",
            "",
            "Reading: short-assist 正2 still trades CAGR for sealed MDD under predeclared gates.",
            "",
            "Binding: Soft-Frozen KEEP · reopen only with **new** mechanism (not densify this grid).",
            "",
        ]
    dlines += [
        "## Refs",
        "",
        f"- Charter: `{CHARTER_ID}.md`",
        f"- Screen: `{SCREEN_ID}.md`",
        f"- Parent rebound: `COOL_T50_LEV_REBOUND_DECISION_PACK.md`",
        "",
        f"Label: `{DECISION_ID}_2026-09-26__{verdict}`",
        "",
    ]
    (OPS / f"{DECISION_ID}.json").write_text(json.dumps(decision, indent=2) + "\n")
    (OPS / f"{DECISION_ID}.md").write_text("\n".join(dlines))
    print(
        json.dumps(
            {
                "verdict": verdict,
                "n_coexist": len(hits),
                "soft_ids": payload["soft_ids"],
                "top3": [r["id"] for r in ranked[:3]],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
