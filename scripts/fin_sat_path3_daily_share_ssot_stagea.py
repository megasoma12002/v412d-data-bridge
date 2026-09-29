#!/usr/bin/env python3
"""FIN×SAT Path3 daily share SSOT Stage A (0kab).

Build path-dependent COMP/SAT Soft share ledgers via simulate_core daily_pos_sink,
then ledger-scaled recon vs live Soft pos on Path3 flip days (compare Stage B asof recon).

Soft KEEP · broker false · cutover BLOCKED · no live wire of ledger engine yet.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

import cool_t50_inv_satellite_stagea as sat
import cool_t50_lev_short_assist_stagea as short
import e16_clip_search_challenger as clip
import e16_soft_frozen_base as soft
import e22_dividend_accounting as e22div
import e45_defend_handoff_stagea_screen as stagea
from cool_c8_proxy_observe_helpers import build_cool_c8_exposure
from e50_early_stack_combined_nav import FIN, e16_features, simulate_core
from fin_buy_quality_helpers import (
    and_buy_ok,
    below_ma_ok,
    catalog_gate,
    not_gate,
    or_buy_ok,
    raw_close_panel,
)
from fin_sat_composite_observe_helpers import (
    CHAL_ALPHA,
    CONFIRM,
    HOLD_H,
    OFF_CODE,
)
from live_config import LIVE_FUSE_SOFT_SELL_BOOST
from live_path3_t0_switch_emitter import BOOK_COMP, BOOK_SAT, load_or_build_signal
from live_path3_t0_weight_engine import ENGINE_ID as ENGINE_B, plan_delta_shares
from ops_repro_ssot import write_ops_and_repro_pointer, write_repro_pointer
from path3_comp_sat_daily_share_ssot import (
    ENGINE_ID,
    REGISTER,
    plan_delta_shares_ledger,
    shares_panel_from_long,
    write_ledger_csv,
)
from portfolio_capital import DEFAULT_CAPITAL
from sleeve_tilt_helpers import ALPHA as LIVE_SLEEVE_ALPHA, sleeve_signal_panel
from soft_assist_helpers import (
    BUY_LOW_ID,
    LIVE_KD,
    SELL_HIGH_ID,
    soft_boost_scores,
    soft_sell_panel,
)
from ta_indicator_catalog import build_low_high_catalog
from tw_share_lots import BOARD_LOT
from within_sleeve_alloc import (
    FIN_PRE_EXDIV_KD,
    TEL_EQUAL,
    build_kd_season_tilt_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "fin-sat-path3-daily-share-ssot-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_SAT_PATH3_DAILY_SHARE_SSOT_STAGEA_CHARTER"
SCREEN_ID = "FIN_SAT_PATH3_DAILY_SHARE_SSOT_STAGEA_SCREEN"
DECISION_ID = "FIN_SAT_PATH3_DAILY_SHARE_SSOT_STAGEA_DECISION_PACK"

STATE = ROOT / "forward/e21/portfolio_state.json"
MARKET = ROOT / "forward/e21/live_market.csv"
E22_VERSION = e22div.DEFAULT_BOOKS_VERSION
SELL_AMP = float(LIVE_FUSE_SOFT_SELL_BOOST)


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _buy_scores(kd, lows) -> pd.DataFrame:
    out = soft_boost_scores(kd, lows[BUY_LOW_ID], 1.0)
    return soft_boost_scores(out, lows["K9_LT30"], 1.0)


def _sell_base(highs) -> pd.DataFrame:
    return soft_sell_panel(highs[SELL_HIGH_ID], boost=SELL_AMP)


def _sleeve_score(market, sleeve, alpha: float) -> pd.DataFrame:
    _p, _s, _t, _r, base_score = soft.build_soft_frozen_targets(market)
    tilt = sleeve_signal_panel(sleeve, "rsi_lt30", 14)
    return base_score + float(alpha) * tilt


def _target_live(score, regime):
    return clip.build_targets_with_clips(
        regime=regime,
        score=score,
        fin_lo=float(soft.SOFT_FROZEN_FIN_LO),
        fin_hi=float(soft.SOFT_FROZEN_FIN_HI),
        tel_lo=float(soft.SOFT_FROZEN_TEL_LO),
        tel_hi=float(soft.SOFT_FROZEN_TEL_HI),
        etf_lo=float(soft.SOFT_FROZEN_ETF_LO),
        etf_hi=float(soft.SOFT_FROZEN_ETF_HI),
    )


def _cool_from_offense(market, offense_nav: pd.DataFrame) -> pd.Series:
    nav_s = stagea._nav_series(offense_nav)
    feat = stagea._risk_features(market, nav_s)
    dates = pd.DatetimeIndex(nav_s.index)
    return build_cool_c8_exposure(dates, feat["proxy_mdd63"])


def _load_live_pos_prices() -> tuple[dict[str, float], dict[str, float], str]:
    ps = json.loads(STATE.read_text(encoding="utf-8"))
    pos = {str(k): float(v) for k, v in (ps.get("positions") or {}).items()}
    asof = str(ps.get("last_date") or "2026-09-24")
    m = pd.read_csv(MARKET, dtype={"code": str})
    m["date"] = pd.to_datetime(m["date"])
    day = m[m["date"] == pd.Timestamp(asof)]
    if day.empty:
        day = m[m["date"] == m["date"].max()]
        asof = str(pd.Timestamp(day["date"].iloc[0]).date())
    prices = {
        str(r.code): float(r.close)
        for r in day.itertuples()
        if str(r.code) != "TAIEX" and float(r.close) > 0
    }
    return pos, prices, asof


def build_ledgers() -> dict[str, Any]:
    """Run COMP + SAT paper sims with daily_pos_sink; write CSVs."""
    OUT.mkdir(parents=True, exist_ok=True)
    sat.DEF_CODE = OFF_CODE
    sat.DEF_PRICE = ROOT / "data/def_proxies/00631L_ohlcv.csv"

    print("loading market ...", flush=True)
    market0 = sat.load_market()
    dividends = sat.load_dividends()
    off = sat.load_inv_bars()
    market, listed_from = sat.attach_inv(market0, off)

    _p, sleeve, _t, regime = e16_features(market0)
    cal = pd.DatetimeIndex(pd.to_datetime(market0["date"]).drop_duplicates().sort_values())
    lows, highs = build_low_high_catalog(market0, cal, list(FIN))
    raw = raw_close_panel(market0, cal, list(FIN))
    kd = build_kd_season_tilt_scores(
        market0,
        dividends,
        list(FIN),
        k_thresh=float(LIVE_KD["k_thresh"]),
        season_start=LIVE_KD["season_start"],
        season_end=LIVE_KD["season_end"],
        pre_days=int(LIVE_KD["pre_days"]),
        active_score=float(LIVE_KD["active_score"]),
    )
    base_buy_ok = build_pre_exdiv_window_buy_ok(
        cal, dividends, list(FIN), pre_days=int(LIVE_KD["pre_days"]), also_stock_ex=True
    )
    scores = _buy_scores(kd, lows)
    sell0 = _sell_base(highs)
    sleeve_sc = _sleeve_score(market0, sleeve, LIVE_SLEEVE_ALPHA)
    tgt_live = _target_live(sleeve_sc, regime)

    print("offense NAV for cool ...", flush=True)
    off_nav, _, _ = simulate_core(
        market0,
        tgt_live,
        regime,
        dividends,
        apply_e22=True,
        apply_stock_div=True,
        capital=float(DEFAULT_CAPITAL),
        lot_size=int(BOARD_LOT),
        financial_alloc=FIN_PRE_EXDIV_KD,
        telecom_alloc=TEL_EQUAL,
        fin_name_scores=scores,
        fin_buy_ok=base_buy_ok,
        fin_sell_scores=sell0,
        e22_version=E22_VERSION,
    )
    cool = _cool_from_offense(market0, off_nav)
    nav_s = stagea._nav_series(off_nav)
    feat = stagea._risk_features(market0, nav_s)
    proxy = feat["proxy_mdd63"].reindex(tgt_live.index).fillna(0.0)
    ret1, ret3 = short._0050_rets(market0, tgt_live.index)
    off_px = short._off_close(off, tgt_live.index)

    extra = or_buy_ok(catalog_gate(lows["BELOW_MA120"]), catalog_gate(lows["K9_LT30"]))
    chal_buy = and_buy_ok(base_buy_ok, extra)
    sell_ok = not_gate(below_ma_ok(raw, 150))

    sched, _meta = short.build_schedule(
        tgt_live,
        cool,
        alpha=float(CHAL_ALPHA),
        hold_h=int(HOLD_H),
        listed_from=listed_from,
        track="CONFIRM",
        confirm=CONFIRM,
        ret1=ret1,
        ret3=ret3,
        proxy=proxy,
        off_px=off_px,
    )

    def _one(book_id: str, buy_ok, sell_ok_panel) -> dict[str, Any]:
        print(f"sim {book_id} with daily_pos_sink ...", flush=True)
        sink: list[dict[str, Any]] = []
        kw: dict[str, Any] = {
            "apply_e22": True,
            "apply_stock_div": True,
            "capital": float(DEFAULT_CAPITAL),
            "lot_size": int(BOARD_LOT),
            "financial_alloc": FIN_PRE_EXDIV_KD,
            "telecom_alloc": TEL_EQUAL,
            "fin_name_scores": scores,
            "fin_buy_ok": buy_ok,
            "fin_sell_scores": sell0,
            "e22_version": E22_VERSION,
            "sleeve_weight_schedule": sched,
            "def_code": OFF_CODE,
            "daily_pos_sink": sink,
        }
        if sell_ok_panel is not None:
            kw["fin_sell_ok"] = sell_ok_panel
        nav, fills, meta = simulate_core(market, tgt_live, regime, dividends, **kw)
        if not bool(meta.get("exact_t1_ok")):
            raise RuntimeError(f"exact_t1_ok failed for {book_id}")
        path = write_ledger_csv(sink, book_id, out_dir=OUT)
        return {
            "book": book_id,
            "path": str(path.relative_to(ROOT)),
            "n_rows": len(sink),
            "n_days": len({r["date"] for r in sink}),
            "n_nav_days": int(meta.get("n_days") or 0),
            "n_fills": int(meta.get("n_fills") or 0),
            "start": str(meta.get("start")),
            "end": str(meta.get("end")),
            "exact_t1_ok": bool(meta.get("exact_t1_ok")),
            "codes": sorted({str(r["code"]) for r in sink}),
        }

    comp = _one(BOOK_COMP, chal_buy, sell_ok)
    sat_book = _one(BOOK_SAT, base_buy_ok, None)
    return {"comp": comp, "sat": sat_book, "schedule_alpha": float(CHAL_ALPHA)}


def _delta_overlap(a: dict[str, float] | None, b: dict[str, float] | None) -> dict[str, Any]:
    aa = a or {}
    bb = b or {}
    keys = sorted(set(aa) | set(bb))
    same_sign = 0
    for k in keys:
        va, vb = float(aa.get(k, 0.0)), float(bb.get(k, 0.0))
        if abs(va) < 1e-9 and abs(vb) < 1e-9:
            continue
        if va * vb > 0:
            same_sign += 1
    return {
        "n_ledger": len(aa),
        "n_recon_b": len(bb),
        "n_union": len(keys),
        "n_same_sign": same_sign,
        "jaccard_codes": round(
            (len(set(aa) & set(bb)) / len(keys)) if keys else 1.0,
            4,
        ),
    }


def _verdict(build: dict[str, Any], legs: list[dict[str, Any]]) -> str:
    for side in ("comp", "sat"):
        b = build.get(side) or {}
        if int(b.get("n_rows") or 0) < 100:
            return "LEDGER_EMPTY"
        if not b.get("exact_t1_ok"):
            return "LEDGER_EMPTY"
    if not legs:
        return "LEDGER_EMPTY"
    for leg in legs:
        if leg.get("ledger_delta") is None:
            return "LEDGER_EMPTY"
        if int((leg.get("ledger_meta") or {}).get("n_delta_names") or 0) < 0:
            return "LEDGER_EMPTY"
    # HIT if ledgers built and ledger-scaled plan returns on both flip legs
    ok_legs = all(
        leg.get("ledger_delta") is not None
        and str((leg.get("ledger_meta") or {}).get("reason", "")).startswith("ledger_")
        for leg in legs
    )
    if ok_legs:
        return "LEDGER_SSOT_BUILT"
    return "LEDGER_EMPTY"


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()

    build = build_ledgers()
    panels = {
        BOOK_COMP: shares_panel_from_long(pd.read_csv(ROOT / build["comp"]["path"], dtype={"code": str})),
        BOOK_SAT: shares_panel_from_long(pd.read_csv(ROOT / build["sat"]["path"], dtype={"code": str})),
    }

    pos, prices, state_asof = _load_live_pos_prices()
    sig = load_or_build_signal()
    flips = sig[sig["flip"].astype(bool)].copy()
    to_sat = flips[flips["book"].astype(str) == BOOK_SAT]
    to_comp = flips[flips["book"].astype(str) == BOOK_COMP]
    if to_sat.empty or to_comp.empty:
        raise SystemExit("need both flip directions")
    sat_asof = str(pd.Timestamp(to_sat.iloc[-1]["date"]).date())
    comp_asof = str(pd.Timestamp(to_comp.iloc[-1]["date"]).date())

    legs: list[dict[str, Any]] = []
    for label, asof, book in (
        ("COMP→SAT", sat_asof, BOOK_SAT),
        ("SAT→COMP", comp_asof, BOOK_COMP),
    ):
        led_delta, led_meta = plan_delta_shares_ledger(
            asof=asof,
            dest_book=book,
            live_pos=pos,
            prices=prices,
            panels=panels,
            out_dir=OUT,
        )
        recon_delta, recon_meta = plan_delta_shares(
            asof=asof, pos=pos, prices=prices, signal=sig, require_flip=True
        )
        legs.append(
            {
                "label": label,
                "asof": asof,
                "dest_book": book,
                "ledger_delta": led_meta.get("delta_shares"),
                "ledger_meta": {k: v for k, v in led_meta.items() if k != "delta_shares"},
                "recon_b_delta": recon_meta.get("delta_shares"),
                "recon_b_reason": recon_meta.get("reason"),
                "recon_b_engine": recon_meta.get("engine_id") or ENGINE_B,
                "overlap": _delta_overlap(led_delta, recon_delta),
            }
        )

    verdict = _verdict(build, legs)

    charter = "\n".join(
        [
            f"# {CHARTER_ID}",
            "",
            "Date: 2026-09-29",
            "Status: **Stage A — Path3 COMP/SAT daily share SSOT** · Soft-Frozen **KEEP** · "
            "broker **false** · cutover **BLOCKED** · no live wire of ledger engine",
            "Parents: 0ka9 `P3_COMP_SAT_ASOF_RECON_B` · COMPOSITE/SAT_A20 dual-paper observe",
            f"Register: **{REGISTER}**",
            "",
            "## Question",
            "",
            "Can we build path-dependent daily Soft share ledgers for "
            f"`{BOOK_COMP}` and `{BOOK_SAT}` and plan flip deltas by "
            "**ledger-scaled recon** (freeze live Soft sleeve $ × paper within-sleeve mix), "
            "closing the Stage B asof-recon fidelity gap without broker/cutover/α flip?",
            "",
            "## Method",
            "",
            f"- Engine `{ENGINE_ID}`",
            "- Hook `simulate_core(..., daily_pos_sink=...)` → long `date,code,shares`",
            "- COMP: OR_K9×HARD150 · SAT: RELAX (base pre-ex) · densify α=0.20 schedule",
            "- Flip plan: `plan_delta_shares_ledger` · Soft 0050 KEEP",
            "- Compare to Stage B asof recon on last COMP→SAT / SAT→COMP flips (live e21 pos)",
            "",
            "## Non-goals",
            "",
            "- Absolute paper share clone onto live NAV (scale mismatch)",
            "- CONF α A10↔A20 align · broker · Path3 cutover · Soft clip flip",
            "- Replacing live `plan_or_none_for_pipeline` (Stage B of this track)",
            "",
            f"Label: `{CHARTER_ID}_2026-09-29__DAILY_POS_LEDGER__NO_BROKER`",
            "",
        ]
    )
    write_ops_and_repro_pointer(OPS / f"{CHARTER_ID}.md", REP / f"{CHARTER_ID}.md", charter, kind="charter")
    (OPS / f"{CHARTER_ID}.json").write_text(
        json.dumps(
            {
                "id": CHARTER_ID,
                "register": REGISTER,
                "engine_id": ENGINE_ID,
                "parent": "0ka9",
                "soft_frozen_keep": True,
                "broker_live_write": False,
                "cutover": "BLOCKED",
                "live_wire_ledger_engine": False,
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
        "engine_id": ENGINE_ID,
        "state_asof": state_asof,
        "build": build,
        "flip_legs": legs,
        "soft_frozen_keep": True,
        "broker_live_write": False,
        "cutover": "BLOCKED",
        "live_wire_ledger_engine": False,
    }
    (OUT / "screen.json").write_text(json.dumps(screen, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(screen, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_repro_pointer(OPS / f"{SCREEN_ID}.json", REP / f"{SCREEN_ID}.json", kind="screen")

    md = [
        f"# {SCREEN_ID}",
        "",
        f"Date: 2026-09-29 · `{generated}` · Verdict **`{verdict}`**",
        f"Engine `{ENGINE_ID}` · e21 state asof {state_asof}",
        "",
        "## Ledgers",
        "",
        "| book | n_rows | n_nav_days | n_fills | end |",
        "|---|---:|---:|---:|---|",
        f"| {build['comp']['book']} | {build['comp']['n_rows']} | {build['comp']['n_nav_days']} | "
        f"{build['comp']['n_fills']} | {build['comp']['end']} |",
        f"| {build['sat']['book']} | {build['sat']['n_rows']} | {build['sat']['n_nav_days']} | "
        f"{build['sat']['n_fills']} | {build['sat']['end']} |",
        "",
        "## Flip-day ledger-scaled vs Stage B recon",
        "",
        "| leg | asof | ledger n_Δ | recon_B n_Δ | jaccard | same_sign |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for leg in legs:
        ov = leg["overlap"]
        md.append(
            f"| {leg['label']} | {leg['asof']} | {ov['n_ledger']} | {ov['n_recon_b']} | "
            f"{ov['jaccard_codes']} | {ov['n_same_sign']} |"
        )
    md += ["", "Repro: `repro/fin-sat-path3-daily-share-ssot-stagea/`", ""]
    write_ops_and_repro_pointer(OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", "\n".join(md) + "\n", kind="screen")

    dec = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: 2026-09-29 · Verdict: **`{verdict}`**",
            "Status: Soft-Frozen **KEEP** · broker **false** · cutover **BLOCKED** · "
            "ledger engine **not live-wired**",
            f"Register: **{REGISTER}** · Engine: `{ENGINE_ID}` · Parent: 0ka9",
            "",
            "## Answer",
            "",
            f"COMP ledger: **{build['comp']['n_rows']}** rows · SAT ledger: **{build['sat']['n_rows']}** rows.",
            f"Flip demos: "
            + " · ".join(
                f"{leg['label']} ledgerΔ={leg['overlap']['n_ledger']} vs BΔ={leg['overlap']['n_recon_b']} "
                f"(jaccard={leg['overlap']['jaccard_codes']})"
                for leg in legs
            )
            + ".",
            "",
            "## Implication",
            "",
            "- `LEDGER_SSOT_BUILT`：日股數 SSOT 落地 · ledger-scaled recon API 可用",
            "- 下一票：可選 ACCEPT 將 `plan_or_none_for_pipeline` 切到 ledger（仍 cutover BLOCKED）",
            "- CONF α A10/A20 仍正交 · 另票",
            "",
            f"Screen: `{SCREEN_ID}.md` · Charter: `{CHARTER_ID}.md`",
            "",
            f"Label: `{DECISION_ID}_2026-09-29__{verdict}__NO_BROKER`",
            "",
        ]
    )
    write_ops_and_repro_pointer(OPS / f"{DECISION_ID}.md", REP / f"{DECISION_ID}.md", dec, kind="decision pack")
    (OPS / f"{DECISION_ID}.json").write_text(
        json.dumps(
            {
                "label": f"{DECISION_ID}_2026-09-29__{verdict}__NO_BROKER",
                "verdict": verdict,
                "register": REGISTER,
                "engine_id": ENGINE_ID,
                "screen": screen,
                "soft_frozen_keep": True,
                "broker_live_write": False,
                "cutover": "BLOCKED",
                "live_wire_ledger_engine": False,
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
            {
                "verdict": verdict,
                "comp_rows": build["comp"]["n_rows"],
                "sat_rows": build["sat"]["n_rows"],
                "legs": [
                    {
                        "label": leg["label"],
                        "asof": leg["asof"],
                        "overlap": leg["overlap"],
                        "ledger_reason": (leg.get("ledger_meta") or {}).get("reason"),
                    }
                    for leg in legs
                ],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
