#!/usr/bin/env python3
"""SAT_A20_H5 sealed-hygiene Stage B — STOP overlay only (paper).

Charter: research/ops/SAT_A20_SEALED_HYGIENE_STAGEB_CHARTER.md
Locked champion CONF_RET3 α=0.20 H=5; finite stops S02/S03/S05.
α/H densify OUT · Soft-Frozen KEEP · no live wire.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

import cool_t50_inv_satellite_stagea as sat
import cool_t50_lev_rebound_stagea as reb
import cool_t50_lev_short_assist_stagea as short
import e16_soft_frozen_base as soft
import e50_early_stack_combined_nav as e50
from e45_paper_harness import load_dividends, load_market
from live_config import LIVE_FUSE_SOFT_SELL_BOOST
from soft_assist_helpers import LIVE_KD
from ta_indicator_catalog import build_low_high_catalog
from within_sleeve_alloc import build_kd_season_tilt_scores, build_pre_exdiv_window_buy_ok

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "sat-a20-sealed-hygiene-stageb"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "SAT_A20_SEALED_HYGIENE_STAGEB_CHARTER"
SCREEN_ID = "SAT_A20_SEALED_HYGIENE_STAGEB_SCREEN"
DECISION_ID = "SAT_A20_SEALED_HYGIENE_DECISION_PACK"
BASE_ID = "BASE_LIVE_CONF"
PARENT_ID = "SAT_A20_H5"
OFF_CODE = "00631L"
OFF_PRICE = ROOT / "data" / "def_proxies" / "00631L_ohlcv.csv"
SELL_AMP = float(LIVE_FUSE_SOFT_SELL_BOOST)

ALPHA = 0.20
HOLD_H = 5
BASE_ALPHA = 0.10
BASE_H = 5
STOPS = (0.02, 0.03, 0.05)

CAGR_FLOOR_PP = 0.20
HELD_MDD_MIN_PP = -0.50
SEALED_MDD_MIN_PP = 0.0  # hygiene gate vs BASE
TIP_MDD_TOL_PP = -0.50


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _score_row(base_w, chal_w, tip, *, rid: str, kind: str, n_fills: int, meta: dict) -> dict[str, Any]:
    h, s = chal_w[sat.HELDOUT], chal_w[sat.SEALED]
    bh, bs = base_w[sat.HELDOUT], base_w[sat.SEALED]
    held_cagr = sat.cagr_delta_pp(bh.get("cagr"), h.get("cagr"), missing_as_zero=True)
    sealed_cagr = sat.cagr_delta_pp(bs.get("cagr"), s.get("cagr"), missing_as_zero=True)
    if held_cagr is not None:
        held_cagr = -float(held_cagr)
    if sealed_cagr is not None:
        sealed_cagr = -float(sealed_cagr)
    held_mdd = float(sat.mdd_delta_pp(bh.get("max_drawdown"), h.get("max_drawdown")))
    sealed_mdd = float(sat.mdd_delta_pp(bs.get("max_drawdown"), s.get("max_drawdown")))
    tip_clean = tip.get("ytd", {}).get("gate") == "PASS" and tip.get("trailing_1y", {}).get("gate") == "PASS"
    tip_mdd_ok = tip_clean and float(tip["ytd"].get("mdd_improve_pp") or -9) >= TIP_MDD_TOL_PP and float(
        tip["trailing_1y"].get("mdd_improve_pp") or -9
    ) >= TIP_MDD_TOL_PP
    cagr_ok = held_cagr is not None and held_cagr >= CAGR_FLOOR_PP
    held_mdd_ok = held_mdd >= HELD_MDD_MIN_PP
    sealed_ok = sealed_mdd >= SEALED_MDD_MIN_PP
    hygiene_hit = bool(cagr_ok and held_mdd_ok and sealed_ok)
    gates = {
        "held_cagr_floor": bool(cagr_ok),
        "held_mdd": bool(held_mdd_ok),
        "sealed_mdd": bool(sealed_ok),
        "tip_mdd_ok": bool(tip_mdd_ok),
    }
    score = (
        0.45 * ((held_cagr or 0.0) + (sealed_cagr or 0.0))
        + 0.55 * (held_mdd + sealed_mdd)
        - 0.25 * max(0.0, -(held_cagr or 0.0))
    )
    return {
        "id": rid,
        "kind": kind,
        "n_fills": n_fills,
        "meta": meta,
        "windows": chal_w,
        "held_cagr_lift_pp": None if held_cagr is None else round(held_cagr, 4),
        "sealed_cagr_lift_pp": None if sealed_cagr is None else round(sealed_cagr, 4),
        "held_mdd_improve_pp": round(held_mdd, 4),
        "sealed_mdd_improve_pp": round(sealed_mdd, 4),
        "tip": tip,
        "gates": gates,
        "hygiene_hit": hygiene_hit,
        "score": round(float(score), 4),
    }


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.8]
    assert float(soft.REBALANCE_L1_MIN) == 0.05
    assert OFF_PRICE.exists(), OFF_PRICE

    sat.DEF_CODE = OFF_CODE
    sat.DEF_PRICE = OFF_PRICE
    short.OFF_CODE = OFF_CODE
    short.OFF_PRICE = OFF_PRICE

    print("loading ...", flush=True)
    market0 = load_market()
    dividends = load_dividends()
    off = sat.load_inv_bars()
    market_off, listed_from = sat.attach_inv(market0, off)
    print(f"{OFF_CODE} listed_from={listed_from.date()} sell_amp={SELL_AMP}", flush=True)

    _p, sleeve, _t, regime = e50.e16_features(market0)
    cal = pd.DatetimeIndex(pd.to_datetime(market0["date"]).drop_duplicates().sort_values())
    lows, highs = build_low_high_catalog(market0, cal, list(soft.FIN))
    kd = build_kd_season_tilt_scores(
        market0,
        dividends,
        soft.FIN,
        k_thresh=float(LIVE_KD["k_thresh"]),
        season_start=LIVE_KD["season_start"],
        season_end=LIVE_KD["season_end"],
        pre_days=int(LIVE_KD["pre_days"]),
        active_score=float(LIVE_KD["active_score"]),
    )
    buy_ok = build_pre_exdiv_window_buy_ok(
        cal, dividends, soft.FIN, pre_days=int(LIVE_KD["pre_days"]), also_stock_ex=True
    )
    buy_live = sat._buy(kd, lows)
    sell_live = sat._sell(highs, SELL_AMP)
    score_live = sat._sleeve_score(market0, sleeve, float(sat.LIVE_SLEEVE_ALPHA))
    tgt = sat._target_live(score_live, regime)

    print("offense + cool ...", flush=True)
    fuse_off, _, _ = sat._sim(
        market0,
        tgt,
        regime,
        dividends,
        scores=buy_live,
        buy_ok=buy_ok,
        sell=sell_live,
        exposure=pd.Series(1.0, index=tgt.index),
    )
    cool = sat._cool_from_offense(market0, fuse_off)
    cool.to_frame("cool_exposure").to_csv(OUT / "exposure_cool.csv")
    n_exits = int(reb.cool_exits(cool).sum())
    defend_frac = float((cool < 1.0 - 1e-12).mean())

    ret1, ret3 = short._0050_rets(market0, pd.DatetimeIndex(tgt.index))
    proxy = sat.stagea._risk_features(market0, sat.stagea._nav_series(fuse_off))[
        "proxy_mdd63"
    ].reindex(tgt.index).ffill()
    off_px = short._off_close(off, pd.DatetimeIndex(tgt.index))

    books: list[dict[str, Any]] = [
        {"id": BASE_ID, "kind": "BASE", "alpha": BASE_ALPHA, "hold_h": BASE_H, "stop": None, "track": "CONFIRM"},
        {"id": PARENT_ID, "kind": "PARENT", "alpha": ALPHA, "hold_h": HOLD_H, "stop": None, "track": "CONFIRM"},
    ]
    for st in STOPS:
        books.append(
            {
                "id": f"A20_STOP_S{int(st * 100):02d}",
                "kind": "STOP",
                "alpha": ALPHA,
                "hold_h": HOLD_H,
                "stop": float(st),
                "track": "STOP",
            }
        )
    assert len(books) == 5, len(books)

    rows: list[dict[str, Any]] = []
    base_nav = None
    base_w = None
    parent_row = None

    for book in books:
        bid = book["id"]
        print(f"  [{bid}] stop={book['stop']} ...", flush=True)
        if book["stop"] is None:
            sched, meta = short.build_schedule(
                tgt,
                cool,
                alpha=float(book["alpha"]),
                hold_h=int(book["hold_h"]),
                listed_from=listed_from,
                track="CONFIRM",
                confirm="RET3",
                ret1=ret1,
                ret3=ret3,
                proxy=proxy,
                off_px=off_px,
            )
        else:
            # CONFIRM entry (RET3) + STOP overlay — short.build_schedule STOP track skips confirm
            idx = tgt.index
            c = cool.reindex(idx).fillna(1.0).astype(float).clip(0.0, 1.0)
            listed = pd.Series(idx >= listed_from, index=idx)
            exits = reb.cool_exits(c)
            entry = exits & listed & (ret3.reindex(idx) > 0)
            pulse = pd.Series(False, index=idx)
            entry_of = pd.Series(-1, index=idx, dtype=int)
            entry_locs = [i for i, v in enumerate(entry.to_numpy()) if bool(v)]
            n = len(idx)
            for i0 in entry_locs:
                for k in range(int(book["hold_h"])):
                    j = i0 + k
                    if j < n:
                        pulse.iloc[j] = True
                        if int(entry_of.iloc[j]) < 0:
                            entry_of.iloc[j] = i0
            off_w = pd.Series(0.0, index=idx, dtype=float)
            off_w = off_w.where(~pulse, float(book["alpha"]))
            off_w = off_w.where(listed, 0.0)
            px = off_px.reindex(idx).astype(float)
            stop = float(book["stop"])
            active_entry = -1
            entry_px = float("nan")
            n_stops = 0
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
                    if dd <= -stop:
                        n_stops += 1
                        e0 = active_entry
                        for j in range(i, min(n, e0 + int(book["hold_h"]))):
                            if int(entry_of.iloc[j]) == e0:
                                off_w.iloc[j] = 0.0
                                pulse.iloc[j] = False
            soft_scale = c * (1.0 - off_w).clip(lower=0.0)
            sched = pd.DataFrame(
                {
                    "Financial": tgt["Financial"].astype(float) * soft_scale,
                    "Telecom": tgt["Telecom"].astype(float) * soft_scale,
                    "0050": tgt["0050"].astype(float) * soft_scale,
                    "DEF": off_w.astype(float),
                },
                index=idx,
            )
            meta = {
                "track": "CONFIRM_STOP",
                "confirm": "RET3",
                "stop": stop,
                "n_stops": int(n_stops),
                "pulse_frac": float(pulse.mean()),
                "mean_off": float(off_w.mean()),
                "n_entries": int(len(entry_locs)),
            }

        sched.to_csv(OUT / f"schedule_{bid}.csv")
        nav, n_fills, _ = sat._sim(
            market_off,
            tgt,
            regime,
            dividends,
            scores=buy_live,
            buy_ok=buy_ok,
            sell=sell_live,
            schedule=sched,
        )
        nav.to_csv(OUT / f"nav_{bid}.csv", index=False)

        if bid == BASE_ID:
            base_nav = nav
            base_w = sat._pack(nav)
            tip = sat._tip(base_nav, base_nav)
            row = _score_row(
                base_w,
                base_w,
                tip,
                rid=bid,
                kind="BASE",
                n_fills=n_fills,
                meta={"alpha": BASE_ALPHA, "hold_h": BASE_H, "stop": None, **{k: meta.get(k) for k in ("n_entries", "pulse_frac", "mean_off")}},
            )
            row["hygiene_hit"] = False
            rows.append(row)
            continue

        assert base_nav is not None and base_w is not None
        tip = sat._tip(base_nav, nav)
        row = _score_row(
            base_w,
            sat._pack(nav),
            tip,
            rid=bid,
            kind=book["kind"],
            n_fills=n_fills,
            meta={
                "alpha": book["alpha"],
                "hold_h": book["hold_h"],
                "stop": book["stop"],
                "n_entries": meta.get("n_entries"),
                "n_stops": meta.get("n_stops"),
                "pulse_frac": meta.get("pulse_frac"),
                "mean_off": meta.get("mean_off"),
            },
        )
        rows.append(row)
        if bid == PARENT_ID:
            parent_row = row

    stop_rows = [r for r in rows if r["kind"] == "STOP"]
    hits = [r for r in stop_rows if r["hygiene_hit"]]
    # Parent sealed soft?
    parent_sealed_soft = parent_row is not None and not parent_row["gates"]["sealed_mdd"]

    if hits:
        verdict = "HYGIENE_HIT"
    elif parent_row is not None and parent_row["gates"]["held_cagr_floor"] and parent_row["gates"]["held_mdd"]:
        verdict = "PARENT_KEEP"
    else:
        verdict = "NO_LIFT"

    ranked = sorted([r for r in rows if r["kind"] != "BASE"], key=lambda r: -float(r["score"]))

    payload = {
        "generated_at_utc": _utc(),
        "label": SCREEN_ID,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "status": verdict,
        "live_wire": False,
        "soft_frozen_keep": True,
        "exact_t1_keep": True,
        "alpha_h_densify": False,
        "locked_parent": PARENT_ID,
        "baseline": BASE_ID,
        "n_cool_exits": n_exits,
        "cool_defend_frac": round(defend_frac, 6),
        "gates": {
            "held_cagr_lift_pp_min": CAGR_FLOOR_PP,
            "held_mdd_improve_pp_min": HELD_MDD_MIN_PP,
            "sealed_mdd_improve_pp_min": SEALED_MDD_MIN_PP,
        },
        "parent_sealed_soft": parent_sealed_soft,
        "n_stop_books": len(stop_rows),
        "n_hygiene_hit": len(hits),
        "hygiene_hit_ids": [r["id"] for r in sorted(hits, key=lambda r: -r["score"])],
        "best": (
            sorted(hits, key=lambda r: -r["score"])[0]["id"]
            if hits
            else PARENT_ID
        ),
        "ranked": ranked,
        "parent": parent_row,
        "baseline_windows": base_w,
    }
    (REP / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2) + "\n")
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2) + "\n")

    lines = [
        "# SAT_A20 sealed-hygiene Stage B — Screen",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Status: **`{verdict}`** · α/H densify **OUT** · Soft-Frozen **KEEP** · live wire **false**",
        f"Parent `{PARENT_ID}` · Base `{BASE_ID}` · cool_exits=**{n_exits}**",
        "",
        f"HYGIENE_HIT: **{len(hits)}** / {len(stop_rows)} STOP books",
        "",
        "## Ranked (vs BASE_LIVE_CONF)",
        "",
        "| book | kind | stop | CAGR↑h | MDD↑h | MDD↑s | tip | hygiene |",
        "|---|---|---:|---:|---:|---:|---|---|",
    ]
    for r in ranked:
        tip_ok = "Y" if r["gates"]["tip_mdd_ok"] else "N"
        st = r["meta"].get("stop")
        st_s = "—" if st is None else f"{float(st):.0%}"
        lines.append(
            f"| `{r['id']}` | {r['kind']} | {st_s} | "
            f"{r['held_cagr_lift_pp']:+.2f} | {r['held_mdd_improve_pp']:+.2f} | "
            f"{r['sealed_mdd_improve_pp']:+.2f} | {tip_ok} | "
            f"{'Y' if r['hygiene_hit'] else 'N'} |"
        )
    lines += [
        "",
        "## Binding",
        "",
        "1. α／H densify **OUT** — STOP overlay only.",
        "2. Soft-Frozen · Exact T+1 · L1=0.05 **KEEP**.",
        "3. Even HYGIENE_HIT → paper only; no live wire.",
        "",
        "Repro: `PYTHONPATH=scripts python3 scripts/sat_a20_sealed_hygiene_stageb.py`",
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
        "n_hygiene_hit": len(hits),
        "hygiene_hit_ids": payload["hygiene_hit_ids"],
        "best": payload["best"],
        "parent": PARENT_ID,
        "parent_sealed_mdd_improve_pp": None if parent_row is None else parent_row["sealed_mdd_improve_pp"],
        "charter": f"research/ops/{CHARTER_ID}.md",
        "stage_b": f"research/ops/{SCREEN_ID}.md",
        "parent_stage_a": "research/ops/NEXT_MECH_STAGEA_DECISION_PACK.md",
    }
    dlines = [
        "# SAT_A20 sealed-hygiene — Decision Pack (Stage B)",
        "",
        f"Date: 2026-09-27 · Generated `{decision['generated_at_utc']}`",
        f"Status: **{verdict}** · α/H densify **OUT** · live wire **false**",
        "",
        f"Parent: `{PARENT_ID}` · STOP grid S02/S03/S05 · HYGIENE_HIT: **{len(hits)}**",
        "",
    ]
    if verdict == "HYGIENE_HIT" and hits:
        b = sorted(hits, key=lambda r: -r["score"])[0]
        dlines += [
            f"Best: `{b['id']}` · held CAGR↑ **{b['held_cagr_lift_pp']:+.2f}** · "
            f"held MDD↑ **{b['held_mdd_improve_pp']:+.2f}** · sealed MDD↑ **{b['sealed_mdd_improve_pp']:+.2f}**",
            "",
            "Next: paper observe / ACCEPT discussion on STOP variant (one cell). No live wire.",
            "",
        ]
    elif verdict == "PARENT_KEEP":
        dlines += [
            f"STOP overlays do **not** recover sealed MDD≥0 while keeping CAGR/MDD gates.",
            "",
            f"Keep parent `{PARENT_ID}` as-is for ACCEPT discussion "
            f"(sealed MDD↑ {parent_row['sealed_mdd_improve_pp']:+.2f} hygiene soft).",
            "",
            "Reading: sealed soft is the price of α=0.20 CAGR lift; STOP cuts pulse but does not "
            "flip sealed hygiene under predeclared gates. Do **not** densify α/H further.",
            "",
            "Binding: Soft-Frozen KEEP · Exact T+1 KEEP · L1=0.05 KEEP · no live wire.",
            "",
        ]
    else:
        dlines += [
            "Parent and STOP miss charter gates.",
            "",
            "Binding: Soft-Frozen KEEP · no live wire.",
            "",
        ]
    dlines += [
        "## Refs",
        "",
        f"- Charter: `{CHARTER_ID}.md`",
        f"- Screen: `{SCREEN_ID}.md`",
        "- Parent: `NEXT_MECH_STAGEA_DECISION_PACK.md`",
        "",
        f"Label: `{DECISION_ID}_2026-09-27__{verdict}`",
        "",
    ]
    (OPS / f"{DECISION_ID}.json").write_text(json.dumps(decision, indent=2) + "\n")
    (OPS / f"{DECISION_ID}.md").write_text("\n".join(dlines))
    (REP / f"{DECISION_ID}.json").write_text(json.dumps(decision, indent=2) + "\n")
    (REP / f"{DECISION_ID}.md").write_text("\n".join(dlines))
    (OPS / f"{DECISION_ID}.zh-TW.md").write_text(
        "\n".join(
            [
                "# SAT_A20 sealed-hygiene — 決策包",
                "",
                f"狀態：**{verdict}** · α／H densify **OUT** · 不進 live",
                f"HIT：**{len(hits)}** · best：`{payload['best']}`",
                "",
                "複現：`PYTHONPATH=scripts python3 scripts/sat_a20_sealed_hygiene_stageb.py`",
                "",
            ]
        )
    )

    print(
        json.dumps(
            {
                "verdict": verdict,
                "n_hygiene_hit": len(hits),
                "hygiene_hit_ids": payload["hygiene_hit_ids"],
                "parent_sealed": None if parent_row is None else parent_row["sealed_mdd_improve_pp"],
                "ranked": [
                    {
                        "id": r["id"],
                        "cagr": r["held_cagr_lift_pp"],
                        "mdd_h": r["held_mdd_improve_pp"],
                        "mdd_s": r["sealed_mdd_improve_pp"],
                        "hit": r["hygiene_hit"],
                    }
                    for r in ranked
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
