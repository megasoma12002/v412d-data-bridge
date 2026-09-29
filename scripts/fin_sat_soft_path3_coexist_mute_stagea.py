#!/usr/bin/env python3
"""FIN×SAT Soft↔Path3 coexistence mute Stage A (paper demo).

Mute Soft FIN∪TEL Exact T+1 on Path3 flip+hit; Soft 0050 KEEP; Path3 -P3T0 KEEP.
Flag remains OFF in LiveConfig until dedicated ACCEPT.

Register: 0kaa · Parent: Stage B weight-engine FULL_ENGINE_BOTH_OK
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from e16_soft_frozen_base import FIN, TEL
from live_config import (
    LIVE,
    LIVE_SOFT_PATH3_COEXIST_MUTE,
    LIVE_SOFT_PATH3_COEXIST_MUTE_POLICY,
)
from live_path3_t0_switch_emitter import (
    BOOK_COMP,
    BOOK_SAT,
    load_or_build_signal,
    maybe_emit_switch_orders,
)
from live_path3_t0_weight_engine import ENGINE_ID, plan_delta_shares
from live_soft_path3_coexist_mute import (
    DEFAULT_POLICY,
    MECHANISM_ID,
    apply_coexist_mute,
)
from ops_repro_ssot import write_ops_and_repro_pointer, write_repro_pointer
from t0_carve_fin_sat_switch import CARVE_OUT_ID

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "fin-sat-soft-path3-coexist-mute-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_SAT_SOFT_PATH3_COEXIST_MUTE_STAGEA_CHARTER"
SCREEN_ID = "FIN_SAT_SOFT_PATH3_COEXIST_MUTE_STAGEA_SCREEN"
DECISION_ID = "FIN_SAT_SOFT_PATH3_COEXIST_MUTE_STAGEA_DECISION_PACK"
BALLOT_ID = "LIVE_SOFT_PATH3_COEXIST_MUTE_BALLOT_DRAFT"
REGISTER = "0kaa"

STATE = ROOT / "forward/e21/portfolio_state.json"
MARKET = ROOT / "forward/e21/live_market.csv"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_pos_prices() -> tuple[dict[str, float], dict[str, float], str]:
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


def _stub_soft_rows(asof: str) -> list[dict[str, Any]]:
    """Synthetic Soft Exact T+1 rows spanning Soft universe + satellite."""
    rows: list[dict[str, Any]] = []
    for i, c in enumerate(list(FIN) + list(TEL)):
        side = "SELL" if i % 2 == 0 else "BUY"
        rows.append(
            {
                "order_id": f"{asof}-{c}-{side}",
                "code": c,
                "side": side,
                "qty": 1000.0,
                "signal_date": asof,
            }
        )
    rows.append(
        {
            "order_id": f"{asof}-0050-BUY",
            "code": "0050",
            "side": "BUY",
            "qty": 2000.0,
            "signal_date": asof,
        }
    )
    rows.append(
        {
            "order_id": f"{asof}-00631L-BUY",
            "code": "00631L",
            "side": "BUY",
            "qty": 1000.0,
            "signal_date": asof,
        }
    )
    return rows


def _demo_leg(
    *,
    label: str,
    asof: str,
    pos: dict[str, float],
    prices: dict[str, float],
    sig: pd.DataFrame,
) -> dict[str, Any]:
    soft = _stub_soft_rows(asof)
    delta, plan_meta = plan_delta_shares(
        asof=asof, pos=pos, prices=prices, signal=sig, require_flip=True
    )
    flip = bool((plan_meta.get("switch") or {}).get("flip"))

    kept_off, meta_off = apply_coexist_mute(
        soft,
        mute_enabled=False,
        emit_enabled=True,
        flip=flip,
        path3_delta_shares=delta,
        policy=DEFAULT_POLICY,
    )
    kept_on, meta_on = apply_coexist_mute(
        soft,
        mute_enabled=True,
        emit_enabled=True,
        flip=flip,
        path3_delta_shares=delta,
        policy=DEFAULT_POLICY,
    )

    path3_rows: list[dict[str, Any]] = []
    emit_meta: dict[str, Any] = {"n_orders": 0}
    if delta is not None:
        path3_rows, emit_meta = maybe_emit_switch_orders(
            asof=asof,
            prices=prices,
            delta_shares=delta,
            authorized=True,
            signal=sig,
        )
    # Final book as pipeline would: muted Soft + Path3
    final = list(kept_on) + list(path3_rows)
    soft_fin_tel_on = [r for r in kept_on if str(r.get("code")) in set(FIN) | set(TEL)]
    soft_0050_on = [r for r in kept_on if str(r.get("code")) == "0050"]
    soft_sat_on = [r for r in kept_on if str(r.get("code")) == "00631L"]

    return {
        "label": label,
        "asof": asof,
        "flip": flip,
        "plan_reason": plan_meta.get("reason"),
        "n_soft_before": len(soft),
        "n_soft_kept_off": len(kept_off),
        "n_soft_kept_on": len(kept_on),
        "n_muted": int(meta_on.get("n_muted") or 0),
        "muted_codes": meta_on.get("muted_codes"),
        "soft_fin_tel_remaining": len(soft_fin_tel_on),
        "soft_0050_kept": len(soft_0050_on) == 1,
        "soft_satellite_kept": len(soft_sat_on) == 1,
        "n_path3_orders": int(emit_meta.get("n_orders") or len(path3_rows)),
        "all_p3t0": all(str(r.get("order_id", "")).endswith("-P3T0") for r in path3_rows)
        if path3_rows
        else False,
        "all_carve": all(r.get("carve_out_id") == CARVE_OUT_ID for r in path3_rows)
        if path3_rows
        else False,
        "n_final_orders": len(final),
        "mute_meta_on": meta_on,
        "engine_id": plan_meta.get("engine_id") or ENGINE_ID,
    }


def _verdict(
    *,
    to_sat: dict[str, Any],
    to_comp: dict[str, Any],
    noflip: dict[str, Any],
    flag_still_off: bool,
) -> str:
    if not flag_still_off:
        return "BLOCK"
    for leg in (to_sat, to_comp):
        if not leg.get("flip"):
            return "MUTE_NO_FLIP"
        if int(leg.get("n_soft_before") or 0) <= 2:
            return "MUTE_SOFT_ALREADY_EMPTY"
        if int(leg.get("n_path3_orders") or 0) <= 0 or not leg.get("all_p3t0"):
            return "MUTE_PATH3_REGRESSED"
        if int(leg.get("n_muted") or 0) <= 0:
            return "MUTE_SOFT_ALREADY_EMPTY"
        if int(leg.get("soft_fin_tel_remaining") or 0) != 0:
            return "MUTE_PATH3_REGRESSED"
        if not leg.get("soft_0050_kept") or not leg.get("soft_satellite_kept"):
            return "MUTE_PATH3_REGRESSED"
    # non-flip: Soft must be intact under mute_enabled True
    if int(noflip.get("n_muted") or 0) != 0:
        return "MUTE_PATH3_REGRESSED"
    if int(noflip.get("n_soft_kept_on") or 0) != int(noflip.get("n_soft_before") or -1):
        return "MUTE_PATH3_REGRESSED"
    return "MUTE_WIRED_DEMO_OK"


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()
    pos, prices, state_asof = _load_pos_prices()
    sig = load_or_build_signal()
    flips = sig[sig["flip"].astype(bool)].copy()
    to_sat_rows = flips[flips["book"].astype(str) == BOOK_SAT]
    to_comp_rows = flips[flips["book"].astype(str) == BOOK_COMP]
    if to_sat_rows.empty or to_comp_rows.empty:
        raise SystemExit("need both COMP→SAT and SAT→COMP flips")
    sat_asof = str(pd.Timestamp(to_sat_rows.iloc[-1]["date"]).date())
    comp_asof = str(pd.Timestamp(to_comp_rows.iloc[-1]["date"]).date())

    to_sat = _demo_leg(label="COMP→SAT", asof=sat_asof, pos=pos, prices=prices, sig=sig)
    to_comp = _demo_leg(label="SAT→COMP", asof=comp_asof, pos=pos, prices=prices, sig=sig)

    soft_nf = _stub_soft_rows(state_asof)
    nf_delta, nf_plan = plan_delta_shares(
        asof=state_asof, pos=pos, prices=prices, signal=sig, require_flip=True
    )
    nf_kept, nf_meta = apply_coexist_mute(
        soft_nf,
        mute_enabled=True,
        emit_enabled=True,
        flip=bool((nf_plan.get("switch") or {}).get("flip")),
        path3_delta_shares=nf_delta,
        policy=DEFAULT_POLICY,
    )
    noflip = {
        "asof": state_asof,
        "reason": nf_plan.get("reason"),
        "n_soft_before": len(soft_nf),
        "n_soft_kept_on": len(nf_kept),
        "n_muted": int(nf_meta.get("n_muted") or 0),
        "should_mute": nf_meta.get("should_mute"),
    }

    flag_still_off = (not LIVE_SOFT_PATH3_COEXIST_MUTE) and (not LIVE.live_soft_path3_coexist_mute)
    verdict = _verdict(to_sat=to_sat, to_comp=to_comp, noflip=noflip, flag_still_off=flag_still_off)

    pd.DataFrame(
        [
            {
                "leg": "to_sat",
                "asof": to_sat["asof"],
                "n_muted": to_sat["n_muted"],
                "n_path3": to_sat["n_path3_orders"],
            },
            {
                "leg": "to_comp",
                "asof": to_comp["asof"],
                "n_muted": to_comp["n_muted"],
                "n_path3": to_comp["n_path3_orders"],
            },
            {
                "leg": "noflip",
                "asof": noflip["asof"],
                "n_muted": noflip["n_muted"],
                "n_path3": 0,
            },
        ]
    ).to_csv(OUT / "demo_mute_summary.csv", index=False)

    screen = {
        "label": f"{SCREEN_ID}_{generated.replace(':', '').replace('-', '')}",
        "generated_at_utc": generated,
        "verdict": verdict,
        "register": REGISTER,
        "mechanism_id": MECHANISM_ID,
        "policy": DEFAULT_POLICY,
        "live_flag_default_off": flag_still_off,
        "live_policy_config": LIVE_SOFT_PATH3_COEXIST_MUTE_POLICY,
        "state_asof": state_asof,
        "to_sat": to_sat,
        "to_comp": to_comp,
        "noflip_control": noflip,
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
        f"Mechanism `{MECHANISM_ID}` · policy `{DEFAULT_POLICY}` · live flag OFF={flag_still_off}",
        "",
        "## Flip-day mute demo",
        "",
        "| leg | asof | n_soft | n_muted | Soft FIN/TEL left | Soft 0050 | satellite | n_Path3 | all_-P3T0 |",
        "|---|---|---:|---:|---:|---|---|---:|---|",
        f"| COMP→SAT | {to_sat['asof']} | {to_sat['n_soft_before']} | {to_sat['n_muted']} | "
        f"{to_sat['soft_fin_tel_remaining']} | {to_sat['soft_0050_kept']} | {to_sat['soft_satellite_kept']} | "
        f"{to_sat['n_path3_orders']} | {to_sat['all_p3t0']} |",
        f"| SAT→COMP | {to_comp['asof']} | {to_comp['n_soft_before']} | {to_comp['n_muted']} | "
        f"{to_comp['soft_fin_tel_remaining']} | {to_comp['soft_0050_kept']} | {to_comp['soft_satellite_kept']} | "
        f"{to_comp['n_path3_orders']} | {to_comp['all_p3t0']} |",
        "",
        f"no-flip @{state_asof}: n_muted={noflip['n_muted']} · should_mute={noflip['should_mute']} · `{noflip['reason']}`",
        "",
        "Repro: `repro/fin-sat-soft-path3-coexist-mute-stagea/`",
        "",
    ]
    write_ops_and_repro_pointer(OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", "\n".join(md) + "\n", kind="screen")

    dec = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: 2026-09-29 · Verdict: **`{verdict}`**",
            "Status: Soft-Frozen clips / Exact T+1 **KEEP** elsewhere · mute flag **OFF** · "
            "Path3 emit/fill/engine B **ON** · broker **false** · cutover **BLOCKED**",
            f"Register: **{REGISTER}** · Mechanism: `{MECHANISM_ID}` · Policy: `{DEFAULT_POLICY}`",
            "",
            "## Answer",
            "",
            f"COMP→SAT @{to_sat['asof']}: muted **{to_sat['n_muted']}** Soft FIN/TEL · "
            f"Path3 **{to_sat['n_path3_orders']}** `-P3T0` · Soft 0050/satellite KEEP.",
            f"SAT→COMP @{to_comp['asof']}: muted **{to_comp['n_muted']}** Soft FIN/TEL · "
            f"Path3 **{to_comp['n_path3_orders']}** `-P3T0` · Soft 0050/satellite KEEP.",
            f"no-flip @{state_asof}: Soft intact (n_muted=0).",
            "",
            "## Implication",
            "",
            "- `MUTE_WIRED_DEMO_OK`：helper + e21 hook wired · live flag still OFF until ACCEPT",
            "- DRAFT ballot: `LIVE_SOFT_PATH3_COEXIST_MUTE_BALLOT_DRAFT.md`",
            "- broker / cutover 仍另票",
            "",
            f"Screen: `{SCREEN_ID}.md` · Charter: `{CHARTER_ID}.md`",
            "",
            f"Label: `{DECISION_ID}_2026-09-29__{verdict}__FLAG_OFF__NO_BROKER`",
            "",
        ]
    )
    write_ops_and_repro_pointer(OPS / f"{DECISION_ID}.md", REP / f"{DECISION_ID}.md", dec, kind="decision pack")
    (OPS / f"{DECISION_ID}.json").write_text(
        json.dumps(
            {
                "label": f"{DECISION_ID}_2026-09-29__{verdict}__FLAG_OFF__NO_BROKER",
                "verdict": verdict,
                "register": REGISTER,
                "mechanism_id": MECHANISM_ID,
                "policy": DEFAULT_POLICY,
                "live_flag_default_off": flag_still_off,
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

    ballot = "\n".join(
        [
            f"# {BALLOT_ID}",
            "",
            "Date: 2026-09-29",
            f"Status: **DRAFT** · awaiting human ACCEPT · Stage A verdict **`{verdict}`**",
            "Soft-Frozen clips / Exact T+1 KEEP elsewhere · broker false · cutover BLOCKED",
            "",
            "## Proposed ACCEPT line",
            "",
            "```",
            LIVE.live_soft_path3_coexist_mute_ballot,
            "```",
            "",
            "## Effect if ACCEPT",
            "",
            "- Flip `live_soft_path3_coexist_mute=True` in `live_config.py`",
            f"- Policy `{DEFAULT_POLICY}`: Path3 flip+hit → mute Soft FIN∪TEL Exact T+1",
            "- Soft 0050 Exact T+1 KEEP · Path3 `-P3T0` KEEP · COOL/FUSE/CONF_RET3 KEEP",
            "- Does **not** authorize broker write or Path3 strategy cutover",
            "",
            f"Parent decision: `{DECISION_ID}.md`",
            "",
            f"Label: `{BALLOT_ID}_2026-09-29__DRAFT__FLAG_OFF`",
            "",
        ]
    )
    write_ops_and_repro_pointer(OPS / f"{BALLOT_ID}.md", REP / f"{BALLOT_ID}.md", ballot, kind="ballot draft")
    (OPS / f"{BALLOT_ID}.json").write_text(
        json.dumps(
            {
                "id": BALLOT_ID,
                "status": "DRAFT",
                "register": REGISTER,
                "verdict_parent": verdict,
                "accept_line": LIVE.live_soft_path3_coexist_mute_ballot,
                "flag_name": "live_soft_path3_coexist_mute",
                "flag_current": False,
                "policy": DEFAULT_POLICY,
                "broker_live_write": False,
                "cutover": "BLOCKED",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    write_repro_pointer(OPS / f"{BALLOT_ID}.json", REP / f"{BALLOT_ID}.json", kind="ballot draft")

    print(
        json.dumps(
            {
                "verdict": verdict,
                "flag_off": flag_still_off,
                "to_sat": {
                    "asof": to_sat["asof"],
                    "n_muted": to_sat["n_muted"],
                    "n_path3": to_sat["n_path3_orders"],
                },
                "to_comp": {
                    "asof": to_comp["asof"],
                    "n_muted": to_comp["n_muted"],
                    "n_path3": to_comp["n_path3_orders"],
                },
                "noflip": noflip,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
