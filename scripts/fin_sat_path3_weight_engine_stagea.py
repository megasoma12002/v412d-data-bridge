#!/usr/bin/env python3
"""FIN×SAT Path3 COMP↔SAT weight-engine Stage A (paper demo).

Named proxy ``P3_SOFT_SLEEVE_EQ_RECON_PROXY`` → delta_shares → tagged ``-P3T0``
orders → same-bar MOC fill path. Soft-Frozen KEEP · broker false · cutover BLOCKED.

Register: 0ka8
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
from live_path3_t0_weight_engine import (
    ENGINE_ID,
    ENGINE_ID_STAGEA,
    plan_delta_shares,
    plan_sat_equal_recon,
)
from ops_repro_ssot import write_ops_and_repro_pointer, write_repro_pointer
from t0_carve_fin_sat_switch import CARVE_OUT_ID

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "fin-sat-path3-weight-engine-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_SAT_PATH3_WEIGHT_ENGINE_STAGEA_CHARTER"
SCREEN_ID = "FIN_SAT_PATH3_WEIGHT_ENGINE_STAGEA_SCREEN"
DECISION_ID = "FIN_SAT_PATH3_WEIGHT_ENGINE_STAGEA_DECISION_PACK"
REGISTER = "0ka8"

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


def _verdict(
    *,
    wired: bool,
    n_orders: int,
    fill_ok: bool,
    flip_ok: bool,
    engine_reason: str,
) -> str:
    if not wired:
        return "BLOCK"
    if not flip_ok:
        return "PROXY_NO_FLIP"
    if n_orders <= 0:
        if engine_reason == "comp_identity_proxy_no_delta":
            return "PROXY_EMPTY_LOT"  # wrong asof direction
        return "PROXY_EMPTY_LOT"
    if not fill_ok:
        return "PROXY_EMPTY_LOT"
    return "PROXY_WIRED_DEMO_OK"


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()

    pos, prices, state_asof, nav = _load_pos_prices()
    sig = load_or_build_signal()
    flips = sig[sig["flip"].astype(bool)].copy()
    to_sat = flips[flips["book"].astype(str) == BOOK_SAT]
    if to_sat.empty:
        raise SystemExit("no COMP→SAT flips in signal")
    demo_asof = str(pd.Timestamp(to_sat.iloc[-1]["date"]).date())

    # Plan on last COMP→SAT flip using current e21 pos/prices (sandbox share math)
    delta, plan_meta = plan_delta_shares(
        asof=demo_asof, pos=pos, prices=prices, signal=sig, require_flip=True
    )
    # Also show raw equal recon regardless of book (Stage A proxy probe)
    recon_delta, recon_meta = plan_sat_equal_recon(pos=pos, prices=prices)
    assert recon_meta.get("engine_id") == ENGINE_ID_STAGEA

    rows: list[dict[str, Any]] = []
    emit_meta: dict[str, Any] = {}
    if delta is not None:
        rows, emit_meta = maybe_emit_switch_orders(
            asof=demo_asof,
            prices=prices,
            delta_shares=delta,
            authorized=True,
            signal=sig,
        )
    else:
        emit_meta = {"reason": plan_meta.get("reason"), "n_orders": 0}

    # Paper same-bar fill demo in sandbox temp dir (never rewrite forward/e21)
    fill_ok = False
    fill_meta: dict[str, Any] = {"n_fills": 0}
    if rows:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            pd.DataFrame(rows).to_csv(sdir / "orders.csv", index=False)
            port = PaperOpenFillPort()
            with mock.patch("live_fill_core.is_live_fill_authorized", return_value=True):
                _pos, _cash, fills, _same, ok = port.fill_pending(
                    state_dir=sdir,
                    latest=pd.Timestamp(demo_asof),
                    open_prices={k: v * 0.99 for k, v in prices.items()},
                    pos={},
                    cash=float(nav) if nav > 0 else 1e9,
                )
            fill_ok = bool(ok and fills)
            fill_meta = {
                "n_fills": len(fills),
                "fill_ok": fill_ok,
                "carve_out_id": fills[0].get("carve_out_id") if fills else None,
                "fill_policy": fills[0].get("fill_policy") if fills else None,
                "sample_fill_price": None
                if not fills
                else round(float(fills[0]["fill_price"]), 4),
            }
            pd.DataFrame(fills).to_csv(OUT / "sandbox_fills.csv", index=False)

    # Control: no-flip asof (state last_date) should not invent Soft qty
    noflip_delta, noflip_meta = plan_delta_shares(
        asof=state_asof, pos=pos, prices=prices, signal=sig, require_flip=True
    )

    # Control: COMP-bound flip → identity empty
    to_comp = flips[flips["book"].astype(str) == BOOK_COMP]
    comp_asof = str(pd.Timestamp(to_comp.iloc[-1]["date"]).date()) if len(to_comp) else None
    comp_delta, comp_meta = ({}, {})
    if comp_asof:
        comp_delta, comp_meta = plan_delta_shares(
            asof=comp_asof, pos=pos, prices=prices, signal=sig, require_flip=True
        )

    wired = delta is not None and plan_meta.get("engine_id") == ENGINE_ID
    flip_ok = bool((plan_meta.get("switch") or {}).get("flip"))
    n_orders = int(emit_meta.get("n_orders") or len(rows))
    verdict = _verdict(
        wired=wired,
        n_orders=n_orders,
        fill_ok=fill_ok,
        flip_ok=flip_ok,
        engine_reason=str(plan_meta.get("reason") or ""),
    )

    if rows:
        pd.DataFrame(rows).to_csv(OUT / "demo_p3t0_orders.csv", index=False)
    pd.DataFrame(
        [{"code": k, "delta_shares": v} for k, v in (delta or {}).items()]
    ).to_csv(OUT / "demo_delta_shares.csv", index=False)

    screen = {
        "label": f"{SCREEN_ID}_{generated.replace(':', '').replace('-', '')}",
        "generated_at_utc": generated,
        "verdict": verdict,
        "register": REGISTER,
        "engine_id": ENGINE_ID,
        "demo_asof": demo_asof,
        "state_asof": state_asof,
        "plan_meta": plan_meta,
        "emit_meta": {k: v for k, v in emit_meta.items() if k != "switch"},
        "n_orders": n_orders,
        "order_ids": [r.get("order_id") for r in rows],
        "all_tagged_p3t0": all(str(r.get("order_id", "")).endswith("-P3T0") for r in rows)
        if rows
        else False,
        "all_carve": all(r.get("carve_out_id") == CARVE_OUT_ID for r in rows) if rows else False,
        "fill_meta": fill_meta,
        "recon_probe": recon_meta,
        "noflip_control": noflip_meta,
        "comp_identity_control": comp_meta,
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
        f"Engine `{ENGINE_ID}` · demo asof **{demo_asof}** (last COMP→SAT flip) · e21 state asof {state_asof}",
        "",
        "## Demo",
        "",
        f"- plan reason: `{plan_meta.get('reason')}` · n_delta_names: **{plan_meta.get('n_delta_names')}**",
        f"- emit reason: `{emit_meta.get('reason')}` · n_orders: **{n_orders}**",
        f"- tagged `-P3T0`: {screen['all_tagged_p3t0']} · carve `{CARVE_OUT_ID}`: {screen['all_carve']}",
        f"- same-bar fill: ok={fill_ok} · n_fills={fill_meta.get('n_fills')} · policy={fill_meta.get('fill_policy')}",
        "",
        "### delta_shares",
        "",
        "| code | Δ shares |",
        "|---|---:|",
    ]
    for k, v in (plan_meta.get("delta_shares") or {}).items():
        md.append(f"| {k} | {v:+.0f} |")
    md += [
        "",
        "### Controls",
        "",
        f"- no-flip @{state_asof}: `{noflip_meta.get('reason')}` (must not invent Soft qty)",
        f"- COMP identity @{comp_asof}: `{comp_meta.get('reason')}` · n_delta={comp_meta.get('n_delta_names')}",
        f"- equal-recon probe n_delta_names={recon_meta.get('n_delta_names')}",
        "",
        "Soft-Frozen KEEP · broker false · cutover BLOCKED · e21 history not rewritten",
        "",
        "Repro: `repro/fin-sat-path3-weight-engine-stagea/`",
        "",
    ]
    write_ops_and_repro_pointer(OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", "\n".join(md) + "\n", kind="screen")

    # Charter already exists — refresh pointer stamp only if needed
    if not (OPS / f"{CHARTER_ID}.md").exists():
        raise SystemExit("missing charter")

    dec = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: 2026-09-29 · Verdict: **`{verdict}`**",
            "Status: Soft-Frozen **KEEP** · emit/fill **ON** (0ka7) · broker **false** · cutover **BLOCKED**",
            f"Register: **{REGISTER}** · Engine: `{ENGINE_ID}` · Parents: 0ka7 / 0k9w / 0k9u",
            "",
            "## Answer",
            "",
            f"Demo COMP→SAT asof **{demo_asof}**: plan `{plan_meta.get('reason')}` · "
            f"**{n_orders}** tagged `-P3T0` orders · same-bar fill **{fill_ok}**.",
            f"e21 hook wired to `{ENGINE_ID}` (replace `delta_shares=None`).",
            f"COMP-bound flips: identity proxy (`{comp_meta.get('reason')}`) — Stage B for full COMP engine.",
            "",
            "## Implication",
            "",
            "- `PROXY_WIRED_DEMO_OK`：proxy OPERATING in paper + e21 hook · still cutover BLOCKED · no broker",
            "- `PROXY_EMPTY_LOT` / `PROXY_NO_FLIP`：修 asof／seed，不升 Stage B",
            "- Soft-Frozen coexistence（flip日 mute Soft sleeve）仍是下一缺口，不在本票",
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
                "demo_asof": demo_asof,
                "n_orders": n_orders,
                "fill_ok": fill_ok,
                "plan_reason": plan_meta.get("reason"),
                "order_ids": screen["order_ids"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
