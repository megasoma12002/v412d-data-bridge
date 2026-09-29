#!/usr/bin/env python3
"""FIN×SAT Path3 COMP↔SAT weight-engine Stage B (paper demo).

Full asof recon: COMP OR_K9×HARD150 · SAT RELAX KD · both-direction `-P3T0`.
Soft-Frozen KEEP · broker false · cutover BLOCKED.

Register: 0ka9 · Parent: 0ka8 PROXY_WIRED_DEMO_OK
"""
from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest import mock

import pandas as pd

from live_fill_core import PaperOpenFillPort
from live_path3_t0_switch_emitter import (
    BOOK_COMP,
    BOOK_SAT,
    load_or_build_signal,
    maybe_emit_switch_orders,
)
from live_path3_t0_weight_engine import ENGINE_ID, plan_delta_shares
from ops_repro_ssot import write_ops_and_repro_pointer, write_repro_pointer
from t0_carve_fin_sat_switch import CARVE_OUT_ID

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "fin-sat-path3-weight-engine-stageb"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_SAT_PATH3_WEIGHT_ENGINE_STAGEB_CHARTER"
SCREEN_ID = "FIN_SAT_PATH3_WEIGHT_ENGINE_STAGEB_SCREEN"
DECISION_ID = "FIN_SAT_PATH3_WEIGHT_ENGINE_STAGEB_DECISION_PACK"
REGISTER = "0ka9"

STATE = ROOT / "forward/e21/portfolio_state.json"
MARKET = ROOT / "forward/e21/live_market.csv"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_pos_prices() -> tuple[dict[str, float], dict[str, float], str, float]:
    ps = json.loads(STATE.read_text(encoding="utf-8"))
    pos = {str(k): float(v) for k, v in (ps.get("positions") or {}).items()}
    asof = str(ps.get("last_date") or "2026-09-24")
    nav = float(ps.get("last_nav") or 0.0)
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
    return pos, prices, asof, nav


def _paper_fill(rows: list[dict[str, Any]], asof: str, prices: dict[str, float], nav: float) -> dict[str, Any]:
    if not rows:
        return {"n_fills": 0, "fill_ok": False}
    with tempfile.TemporaryDirectory() as td:
        sdir = Path(td)
        pd.DataFrame(rows).to_csv(sdir / "orders.csv", index=False)
        port = PaperOpenFillPort()
        with mock.patch("live_fill_core.is_live_fill_authorized", return_value=True):
            _pos, _cash, fills, _same, ok = port.fill_pending(
                state_dir=sdir,
                latest=pd.Timestamp(asof),
                open_prices={k: v * 0.99 for k, v in prices.items()},
                pos={},
                cash=float(nav) if nav > 0 else 1e9,
            )
        return {
            "n_fills": len(fills),
            "fill_ok": bool(ok and fills),
            "carve_out_id": fills[0].get("carve_out_id") if fills else None,
            "fill_policy": fills[0].get("fill_policy") if fills else None,
        }


def _demo_leg(
    *,
    label: str,
    asof: str,
    pos: dict[str, float],
    prices: dict[str, float],
    nav: float,
    sig: pd.DataFrame,
) -> dict[str, Any]:
    delta, plan_meta = plan_delta_shares(
        asof=asof, pos=pos, prices=prices, signal=sig, require_flip=True
    )
    rows: list[dict[str, Any]] = []
    emit_meta: dict[str, Any] = {"n_orders": 0, "reason": plan_meta.get("reason")}
    if delta is not None:
        rows, emit_meta = maybe_emit_switch_orders(
            asof=asof,
            prices=prices,
            delta_shares=delta,
            authorized=True,
            signal=sig,
        )
    fill_meta = _paper_fill(rows, asof, prices, nav)
    return {
        "label": label,
        "asof": asof,
        "plan_reason": plan_meta.get("reason"),
        "policy": plan_meta.get("policy"),
        "n_delta_names": plan_meta.get("n_delta_names"),
        "delta_shares": plan_meta.get("delta_shares"),
        "forced_zero_hard": plan_meta.get("forced_zero_hard"),
        "n_orders": int(emit_meta.get("n_orders") or len(rows)),
        "emit_reason": emit_meta.get("reason"),
        "order_ids": [r.get("order_id") for r in rows],
        "all_p3t0": all(str(r.get("order_id", "")).endswith("-P3T0") for r in rows) if rows else False,
        "all_carve": all(r.get("carve_out_id") == CARVE_OUT_ID for r in rows) if rows else False,
        "fill": fill_meta,
        "plan_meta": {k: v for k, v in plan_meta.items() if k != "switch"},
    }


def _verdict(to_sat: dict[str, Any], to_comp: dict[str, Any]) -> str:
    sat_ok = to_sat["n_orders"] > 0 and to_sat["fill"]["fill_ok"] and to_sat["all_p3t0"]
    comp_ok = to_comp["n_orders"] > 0 and to_comp["fill"]["fill_ok"] and to_comp["all_p3t0"]
    if sat_ok and comp_ok:
        return "FULL_ENGINE_BOTH_OK"
    if sat_ok and not comp_ok:
        return "FULL_ENGINE_SAT_ONLY"
    if comp_ok and not sat_ok:
        return "FULL_ENGINE_COMP_ONLY"
    if to_sat["n_orders"] == 0 and to_comp["n_orders"] == 0:
        return "FULL_ENGINE_EMPTY"
    return "FULL_ENGINE_PARTIAL"


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()
    pos, prices, state_asof, nav = _load_pos_prices()
    sig = load_or_build_signal()
    flips = sig[sig["flip"].astype(bool)].copy()
    to_sat_rows = flips[flips["book"].astype(str) == BOOK_SAT]
    to_comp_rows = flips[flips["book"].astype(str) == BOOK_COMP]
    if to_sat_rows.empty or to_comp_rows.empty:
        raise SystemExit("need both COMP→SAT and SAT→COMP flips")
    sat_asof = str(pd.Timestamp(to_sat_rows.iloc[-1]["date"]).date())
    comp_asof = str(pd.Timestamp(to_comp_rows.iloc[-1]["date"]).date())

    to_sat = _demo_leg(label="COMP→SAT", asof=sat_asof, pos=pos, prices=prices, nav=nav, sig=sig)
    to_comp = _demo_leg(label="SAT→COMP", asof=comp_asof, pos=pos, prices=prices, nav=nav, sig=sig)
    noflip_delta, noflip_meta = plan_delta_shares(
        asof=state_asof, pos=pos, prices=prices, signal=sig, require_flip=True
    )
    verdict = _verdict(to_sat, to_comp)

    pd.DataFrame(
        [{"leg": "to_sat", "code": k, "delta": v} for k, v in (to_sat.get("delta_shares") or {}).items()]
        + [{"leg": "to_comp", "code": k, "delta": v} for k, v in (to_comp.get("delta_shares") or {}).items()]
    ).to_csv(OUT / "demo_delta_shares.csv", index=False)
    for leg, demo in (("to_sat", to_sat), ("to_comp", to_comp)):
        if demo["order_ids"]:
            # rebuild rows via plan for CSV
            d, _ = plan_delta_shares(asof=demo["asof"], pos=pos, prices=prices, signal=sig)
            rows, _ = maybe_emit_switch_orders(
                asof=demo["asof"], prices=prices, delta_shares=d, authorized=True, signal=sig
            )
            pd.DataFrame(rows).to_csv(OUT / f"demo_orders_{leg}.csv", index=False)

    charter = "\n".join(
        [
            f"# {CHARTER_ID}",
            "",
            "Date: 2026-09-29",
            "Status: **Stage B — full COMP/SAT asof recon** · Soft-Frozen **KEEP** · emit/fill **ON** · "
            "broker **false** · cutover **BLOCKED**",
            "Parents: 0ka8 `PROXY_WIRED_DEMO_OK` · 0ka7 observe θ=0.005 + T+0",
            f"Register: **{REGISTER}**",
            "",
            "## Question",
            "",
            "Can Path3 emit **both** COMP→SAT and SAT→COMP flips with non-empty tagged `-P3T0` "
            "using asof recon policies matching paper books (COMP=OR_K9×HARD150 · SAT=RELAX KD), "
            "without Soft clip / CONF α / broker / cutover?",
            "",
            "## Method",
            "",
            f"- Engine `{ENGINE_ID}`",
            "- Freeze Soft sleeve $ from live pos; rebuild FIN dest by policy; TEL equal; 0050 KEEP",
            "- COMP: OR_K9 buy_ok ∧ HARD150 sell_ok · KD score tilt · HARD fail → dest 0",
            "- SAT: base pre-ex buy_ok · KD score tilt · no HARD",
            "- Paper sandbox demo only · e21 history not rewritten",
            "",
            "## Non-goals",
            "",
            "- Soft-Frozen flip-day coexistence mute",
            "- live CONF α densify · broker · Path3 strategy cutover",
            "- Cloning paper share ledgers (no daily pos SSOT)",
            "",
            f"Label: `{CHARTER_ID}_2026-09-29__ASOF_RECON_B__NO_BROKER`",
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
                "parent": "0ka8",
                "soft_frozen_keep": True,
                "broker_live_write": False,
                "cutover": "BLOCKED",
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
        "to_sat": to_sat,
        "to_comp": to_comp,
        "noflip_control": noflip_meta,
        "soft_frozen_keep": True,
        "broker_live_write": False,
        "cutover": "BLOCKED",
        "e21_history_rewritten": False,
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
        "## Both-direction demo",
        "",
        "| leg | asof | policy | n_Δ | n_orders | fill_ok | reason |",
        "|---|---|---|---:|---:|---|---|",
        f"| COMP→SAT | {to_sat['asof']} | {to_sat.get('policy')} | {to_sat.get('n_delta_names')} | "
        f"{to_sat['n_orders']} | {to_sat['fill']['fill_ok']} | {to_sat['plan_reason']} |",
        f"| SAT→COMP | {to_comp['asof']} | {to_comp.get('policy')} | {to_comp.get('n_delta_names')} | "
        f"{to_comp['n_orders']} | {to_comp['fill']['fill_ok']} | {to_comp['plan_reason']} |",
        "",
        f"no-flip @{state_asof}: `{noflip_meta.get('reason')}`",
        "",
        "Repro: `repro/fin-sat-path3-weight-engine-stageb/`",
        "",
    ]
    write_ops_and_repro_pointer(OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", "\n".join(md) + "\n", kind="screen")

    dec = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: 2026-09-29 · Verdict: **`{verdict}`**",
            "Status: Soft-Frozen **KEEP** · emit/fill **ON** · broker **false** · cutover **BLOCKED**",
            f"Register: **{REGISTER}** · Engine: `{ENGINE_ID}` · Parent: 0ka8",
            "",
            "## Answer",
            "",
            f"COMP→SAT @{to_sat['asof']}: **{to_sat['n_orders']}** `-P3T0` · fill={to_sat['fill']['fill_ok']} · `{to_sat['plan_reason']}`.",
            f"SAT→COMP @{to_comp['asof']}: **{to_comp['n_orders']}** `-P3T0` · fill={to_comp['fill']['fill_ok']} · `{to_comp['plan_reason']}`.",
            "",
            "## Implication",
            "",
            "- `FULL_ENGINE_BOTH_OK`：Stage B proxy→full asof recon HIT · e21 already wired via `plan_or_none_for_pipeline`",
            "- Soft coexistence mute / cutover / broker 仍另票",
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
                "to_sat": {
                    "asof": to_sat["asof"],
                    "n_orders": to_sat["n_orders"],
                    "fill_ok": to_sat["fill"]["fill_ok"],
                    "reason": to_sat["plan_reason"],
                },
                "to_comp": {
                    "asof": to_comp["asof"],
                    "n_orders": to_comp["n_orders"],
                    "fill_ok": to_comp["fill"]["fill_ok"],
                    "reason": to_comp["plan_reason"],
                },
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
