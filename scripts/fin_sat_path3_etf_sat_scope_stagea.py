#!/usr/bin/env python3
"""Path3 scope: can 0050 / satellite (00631L) join Path3 recon? Stage A paper.

Parents: 0kab ledger LIVE WIRED (FIN∪TEL recon · keep_0050=True) · 0kaa mute
(Soft 0050/satellite KEEP) · 0kac cutover default WITHIN_SLEEVE_PATH3 (0050 KEEP).

Soft-Frozen KEEP · broker false · cutover BLOCKED · no live wire.
Register: 0kad
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from live_path3_t0_switch_emitter import BOOK_COMP, BOOK_SAT, load_or_build_signal
from ops_repro_ssot import write_ops_and_repro_pointer, write_repro_pointer
from path3_comp_sat_daily_share_ssot import (
    ENGINE_ID,
    load_book_shares,
    plan_delta_shares_ledger,
)

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "fin-sat-path3-etf-sat-scope-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_SAT_PATH3_ETF_SAT_SCOPE_STAGEA_CHARTER"
SCREEN_ID = "FIN_SAT_PATH3_ETF_SAT_SCOPE_STAGEA_SCREEN"
DECISION_ID = "FIN_SAT_PATH3_ETF_SAT_SCOPE_STAGEA_DECISION_PACK"
REGISTER = "0kad"

ETF_CODE = "0050"
SATELLITE_CODE = "00631L"
PROBE_CODES = (ETF_CODE, SATELLITE_CODE)
BASELINE_CODES = ("2880", "2412")
STATE = ROOT / "forward/e21/portfolio_state.json"
MARKET = ROOT / "forward/e21/live_market.csv"
PROXY_631L = ROOT / "data/def_proxies/00631L_ohlcv.csv"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_live_pos_prices() -> tuple[dict[str, float], dict[str, float], str]:
    ps = json.loads(STATE.read_text(encoding="utf-8"))
    pos = {str(k): float(v) for k, v in (ps.get("positions") or {}).items()}
    asof = str(ps.get("last_date") or "")
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
    if SATELLITE_CODE not in prices and PROXY_631L.exists():
        inv = pd.read_csv(PROXY_631L)
        inv["date"] = pd.to_datetime(inv["date"])
        use = inv[inv["date"] <= pd.Timestamp(asof)]
        if not use.empty:
            prices[SATELLITE_CODE] = float(use.iloc[-1]["close"])
    return pos, prices, asof


def _code_divergence(
    comp: pd.DataFrame,
    sat: pd.DataFrame,
    code: str,
    flip_dates: list[pd.Timestamp],
) -> dict[str, Any]:
    dates = comp.index.intersection(sat.index)
    if code not in comp.columns or code not in sat.columns:
        return {"code": code, "ok": False, "reason": "missing_in_ledger"}
    d = comp.loc[dates, code].astype(float) - sat.loc[dates, code].astype(float)
    nz = d.abs() > 1e-9
    flip_d = []
    for dt in flip_dates:
        if dt not in dates:
            continue
        flip_d.append(float(comp.loc[dt, code]) - float(sat.loc[dt, code]))
    arr = np.asarray(flip_d, dtype=float)
    tip = dates.max()
    return {
        "code": code,
        "ok": True,
        "n_days": int(len(dates)),
        "n_nonzero_share_delta": int(nz.sum()),
        "pct_days_differ": round(float(nz.mean()), 6),
        "max_abs_share_delta": round(float(d.abs().max()), 1),
        "median_abs_share_delta_when_diff": round(
            float(d.abs()[nz].median()) if nz.any() else 0.0, 1
        ),
        "tip_date": str(tip.date()),
        "tip_comp_shares": round(float(comp.loc[tip, code]), 1),
        "tip_sat_shares": round(float(sat.loc[tip, code]), 1),
        "tip_delta_shares": round(float(comp.loc[tip, code] - sat.loc[tip, code]), 1),
        "flip": {
            "n_flips": int(len(arr)),
            "n_nonzero": int((np.abs(arr) > 1e-9).sum()),
            "pct_nonzero": round(float((np.abs(arr) > 1e-9).mean()) if len(arr) else 0.0, 6),
            "max_abs": round(float(np.abs(arr).max()) if len(arr) else 0.0, 1),
            "median_abs_when_nz": round(
                float(np.median(np.abs(arr)[np.abs(arr) > 1e-9]))
                if (np.abs(arr) > 1e-9).any()
                else 0.0,
                1,
            ),
        },
    }


def _probe_keep_0050(
    *,
    asof: str,
    dest_book: str,
    live_pos: dict[str, float],
    prices: dict[str, float],
    panels: dict[str, pd.DataFrame],
) -> dict[str, Any]:
    """Compare ledger recon with keep_0050 True vs False on one flip asof."""
    d_keep, m_keep = plan_delta_shares_ledger(
        asof=asof,
        dest_book=dest_book,
        live_pos=live_pos,
        prices=prices,
        panels=panels,
        keep_0050=True,
    )
    d_move, m_move = plan_delta_shares_ledger(
        asof=asof,
        dest_book=dest_book,
        live_pos=live_pos,
        prices=prices,
        panels=panels,
        keep_0050=False,
    )
    keep_d = dict(d_keep or {})
    move_d = dict(d_move or {})
    etf_only = {
        k: round(float(v), 1)
        for k, v in move_d.items()
        if k == ETF_CODE or (k in keep_d and abs(float(v) - float(keep_d.get(k, 0.0))) > 1e-9)
    }
    return {
        "asof": asof,
        "dest_book": dest_book,
        "keep_0050_true": {
            "reason": m_keep.get("reason"),
            "n_delta_names": m_keep.get("n_delta_names"),
            "has_0050": ETF_CODE in keep_d,
            "delta_0050": keep_d.get(ETF_CODE),
        },
        "keep_0050_false": {
            "reason": m_move.get("reason"),
            "n_delta_names": m_move.get("n_delta_names"),
            "has_0050": ETF_CODE in move_d,
            "delta_0050": move_d.get(ETF_CODE),
        },
        "extra_or_changed_vs_keep": etf_only,
    }


def _verdict(screen: dict[str, Any]) -> str:
    etf = screen["divergence"][ETF_CODE]
    sat = screen["divergence"][SATELLITE_CODE]
    etf_material = bool(etf.get("ok") and etf.get("pct_days_differ", 0) >= 0.5)
    sat_sparse = bool(sat.get("ok") and sat.get("pct_days_differ", 1) < 0.5)
    probes = screen.get("keep_0050_probes") or []
    probe_moves = any(
        (p.get("keep_0050_false") or {}).get("has_0050") for p in probes
    )
    # Split verdict: ETF may probe; satellite needs overlay re-home — not direct P3.
    if etf_material and sat_sparse:
        return "ETF_DIVERGES__SATELLITE_OVERLAY_BLOCK"
    if etf_material and probe_moves:
        return "ETF_DIVERGES__PROBE_OPEN"
    if etf_material:
        return "ETF_DIVERGES__KEEP_DEFAULT"
    if sat_sparse:
        return "NO_ETF_EDGE__SATELLITE_OVERLAY_BLOCK"
    return "SCOPE_AMBIGUOUS"


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()

    comp = load_book_shares(BOOK_COMP)
    sat = load_book_shares(BOOK_SAT)
    panels = {BOOK_COMP: comp, BOOK_SAT: sat}
    sig = load_or_build_signal()
    sig["date"] = pd.to_datetime(sig["date"])
    flip_dates = [
        pd.Timestamp(d).normalize()
        for d in sig.loc[sig["flip"].astype(bool), "date"]
        if pd.Timestamp(d).normalize() in comp.index.intersection(sat.index)
    ]

    divergence = {
        c: _code_divergence(comp, sat, c, flip_dates)
        for c in list(PROBE_CODES) + list(BASELINE_CODES)
    }

    pos, prices, state_asof = _load_live_pos_prices()
    flips = sig[sig["flip"].astype(bool)].copy()
    to_sat = flips[flips["book"].astype(str) == BOOK_SAT]
    to_comp = flips[flips["book"].astype(str) == BOOK_COMP]
    probes: list[dict[str, Any]] = []
    if not to_sat.empty and not to_comp.empty:
        for label, row, book in (
            ("COMP→SAT", to_sat.iloc[-1], BOOK_SAT),
            ("SAT→COMP", to_comp.iloc[-1], BOOK_COMP),
        ):
            asof = str(pd.Timestamp(row["date"]).date())
            probe = _probe_keep_0050(
                asof=asof, dest_book=book, live_pos=pos, prices=prices, panels=panels
            )
            probe["label"] = label
            probes.append(probe)

    # Satellite is never in plan_delta_shares_ledger recon today — document gap.
    sat_note = {
        "code": SATELLITE_CODE,
        "in_ledger_codes": SATELLITE_CODE in comp.columns and SATELLITE_CODE in sat.columns,
        "in_path3_recon_today": False,
        "owner_today": "COOL / Soft satellite overlay (not Path3 sleeve recon)",
        "path3_apply_requires": [
            "re-home COOL exposure owner away from Soft Exact T+1 satellite fills",
            "define COMP vs SAT satellite policy (often near-identical at tip)",
            "separate ballot from FIN∪TEL Path3 carve",
        ],
    }

    screen: dict[str, Any] = {
        "generated_at_utc": generated,
        "register": REGISTER,
        "engine_id": ENGINE_ID,
        "state_asof": state_asof,
        "ledger_panel_end": str(pd.Timestamp(comp.index.max()).date()),
        "n_flip_days": len(flip_dates),
        "divergence": divergence,
        "keep_0050_probes": probes,
        "satellite_note": sat_note,
        "live_pos_codes": sorted(pos),
        "binding_parents": {
            "0kab_keep_0050": True,
            "0kaa_mute_keeps_0050_and_satellite": True,
            "0kac_default_scope_0050_keep": True,
            "0kac_satellite_overlays_keep": True,
        },
    }
    verdict = _verdict(screen)
    screen["verdict"] = verdict

    charter_md = "\n".join(
        [
            f"# {CHARTER_ID}",
            "",
            f"Date: {generated[:10]}",
            "Status: **Stage A — can Path3 own Soft 0050 / satellite?** · Soft-Frozen **KEEP** · "
            "broker **false** · cutover **BLOCKED** · no live",
            "Parents: 0kab ledger · 0kaa mute · 0kac `WITHIN_SLEEVE_PATH3` (0050 KEEP)",
            f"Register: **{REGISTER}**",
            "",
            "## Question",
            "",
            "Today Path3 ledger-scaled recon moves **FIN∪TEL only** (`keep_0050=True`). "
            "Mute keeps Soft **0050** and **satellites** (e.g. `00631L`). "
            "Should Stage B+ research extend Path3 to those codes?",
            "",
            "## Split (do not bundle)",
            "",
            "| Code | Role today | Path3 today | Research ask |",
            "|---|---|---|---|",
            f"| `{ETF_CODE}` | Soft sleeve ETF clip Exact T+1 | KEEP | Optional recon when COMP/SAT ETF shares diverge? |",
            f"| `{SATELLITE_CODE}` | COOL/Soft satellite overlay | out of recon | Can Path3 book own satellite, or must overlay re-home first? |",
            "",
            "## Method",
            "",
            "- Measure COMP vs SAT daily share divergence for 0050 / 00631L (vs FIN/TEL baselines)",
            "- Flip-day subset stats",
            "- Paper probe: `plan_delta_shares_ledger(..., keep_0050=False)` on last COMP→SAT / SAT→COMP",
            "- Satellite: charter gap only (no silent wire into FIN∪TEL engine)",
            "",
            "## Non-goals",
            "",
            "- Live `keep_0050=False` · mute scope expand · cutover ACCEPT · broker",
            "- Soft clip densify / CONF α flip",
            "- Treating FinPriv names (2881/…) as Path3 Soft universe",
            "- Auto-folding COOL into Path3 without overlay re-home charter",
            "",
            "## Verdict ladder",
            "",
            "| Verdict | Meaning |",
            "|---|---|",
            "| `ETF_DIVERGES__PROBE_OPEN` | 0050 COMP≠SAT material · paper `keep_0050=False` probe next |",
            "| `ETF_DIVERGES__SATELLITE_OVERLAY_BLOCK` | 0050 material · satellite remains overlay-blocked |",
            "| `ETF_DIVERGES__KEEP_DEFAULT` | 0050 diverges but default KEEP still preferred |",
            "| `NO_ETF_EDGE__SATELLITE_OVERLAY_BLOCK` | 0050 near-identical · satellite not direct P3 |",
            "| `SCOPE_AMBIGUOUS` | need human pick |",
            "",
            f"Label: `{CHARTER_ID}_{generated[:10]}__0050_00631L__NO_LIVE`",
            "",
        ]
    )
    write_ops_and_repro_pointer(OPS / f"{CHARTER_ID}.md", REP / f"{CHARTER_ID}.md", charter_md, kind="charter")
    (OPS / f"{CHARTER_ID}.json").write_text(
        json.dumps(
            {
                "id": CHARTER_ID,
                "register": REGISTER,
                "status": "STAGE_A",
                "codes": list(PROBE_CODES),
                "parents": ["0kab", "0kaa", "0kac"],
                "soft_keep": True,
                "broker": False,
                "cutover_blocked": True,
                "label": f"{CHARTER_ID}_{generated[:10]}__0050_00631L__NO_LIVE",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    write_repro_pointer(OPS / f"{CHARTER_ID}.json", REP / f"{CHARTER_ID}.json", kind="charter")

    (OUT / "screen.json").write_text(json.dumps(screen, indent=2) + "\n", encoding="utf-8")
    screen_md = "\n".join(
        [
            f"# {SCREEN_ID}",
            "",
            f"Date: {generated[:10]} · Verdict: **`{verdict}`**",
            f"Register: **{REGISTER}** · ledger panel end: `{screen['ledger_panel_end']}` · "
            f"live state: `{state_asof}` · flips: {screen['n_flip_days']}",
            "",
            "## Divergence (COMP − SAT shares)",
            "",
            "| Code | % days differ | flip % nz | tip Δ shares | max |Δ| |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for c in list(PROBE_CODES) + list(BASELINE_CODES):
        r = divergence[c]
        if not r.get("ok"):
            screen_md += f"\n| `{c}` | — | — | — | missing |"
            continue
        fl = r["flip"]
        screen_md += (
            f"\n| `{c}` | {100*r['pct_days_differ']:.1f}% | {100*fl['pct_nonzero']:.1f}% | "
            f"{r['tip_delta_shares']:.0f} | {r['max_abs_share_delta']:.0f} |"
        )
    screen_md += "\n\n## keep_0050=False probes (last flip each way)\n\n"
    for p in probes:
        kf = p["keep_0050_false"]
        screen_md += (
            f"- **{p['label']}** @{p['asof']} → `{p['dest_book']}` · "
            f"keep=True n_delta={p['keep_0050_true']['n_delta_names']} · "
            f"keep=False n_delta={kf['n_delta_names']} · "
            f"Δ0050={kf.get('delta_0050')}\n"
        )
    screen_md += (
        "\n## Satellite\n\n"
        f"- `{SATELLITE_CODE}` in ledger: **{sat_note['in_ledger_codes']}** · "
        f"in Path3 recon today: **{sat_note['in_path3_recon_today']}**\n"
        f"- Owner today: {sat_note['owner_today']}\n"
        "- Direct Path3 apply blocked until overlay re-home\n\n"
        "## Engine note\n\n"
        "- `keep_0050=False` under freeze-sleeve-$ is a **no-op** for single-name ETF "
        "(mix≡1 → same live ETF $). ETF Path3 needs a new policy.\n\n"
        f"Repro: `PYTHONPATH=scripts python3 scripts/fin_sat_path3_etf_sat_scope_stagea.py`\n\n"
        f"Label: `{SCREEN_ID}_{generated[:10]}__{verdict}`\n"
    )
    write_ops_and_repro_pointer(OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", screen_md, kind="screen")
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(screen, indent=2) + "\n", encoding="utf-8")
    write_repro_pointer(OPS / f"{SCREEN_ID}.json", REP / f"{SCREEN_ID}.json", kind="screen")

    next_steps = []
    if "ETF_DIVERGES" in verdict:
        next_steps.append(
            "Design ETF Path3 policy beyond keep_0050=False (today freeze-ETF-$ × "
            "single-name mix is a no-op). Candidates: (a) paper Soft sleeve % for 0050 "
            "from COMP/SAT schedule → scale live Soft NAV; (b) absolute ledger share "
            "ratio 0050/(FIN+TEL+0050) under live Soft $; (c) leave KEEP"
        )
        next_steps.append(
            "Paper dual after policy pick: KEEP vs ETF-recon on Path3 flip/cutover window "
            "(tipY/held/sealed + 0050 trade count) — Soft KEEP / no live"
        )
    next_steps.append(
        "Satellite: do **not** fold 00631L into Path3 recon; open overlay re-home charter "
        "only if cutover scope needs Path3-owned DEF"
    )
    next_steps.append("0kac PAPER_WITHIN_HIT remains primary Path3 roadmap (FIN∪TEL daily)")

    # Engine gap: keep_0050=False currently cannot move 0050 under freeze-sleeve-$ design.
    etf_engine_gap = {
        "flag": "keep_0050_false_noop_under_freeze_sleeve_dollars",
        "why": (
            "ETF sleeve is a single code; dollar_mix → {0050:1.0}; scale_mix_to_shares "
            "rebuilds the same live ETF notional → delta≈0. Material COMP≠SAT share "
            "divergence is invisible to this API."
        ),
        "implication": "0050 Path3 research needs a new recon policy, not a bool flip",
    }
    decision = {
        "label": f"{DECISION_ID}_{generated[:10]}__{verdict}__NO_LIVE",
        "verdict": verdict,
        "register": REGISTER,
        "generated_at_utc": generated,
        "etf_code": ETF_CODE,
        "satellite_code": SATELLITE_CODE,
        "etf_pct_days_differ": (divergence[ETF_CODE] or {}).get("pct_days_differ"),
        "satellite_pct_days_differ": (divergence[SATELLITE_CODE] or {}).get("pct_days_differ"),
        "etf_engine_gap": etf_engine_gap,
        "keep_0050_false_moves_etf": any(
            (p.get("keep_0050_false") or {}).get("has_0050") for p in probes
        ),
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
            f"Date: {generated[:10]} · Verdict: **`{verdict}`**",
            f"Register: **{REGISTER}**",
            "",
            "## Finding",
            "",
            f"- **`{ETF_CODE}`:** COMP vs SAT diverge **{100*(divergence[ETF_CODE].get('pct_days_differ') or 0):.1f}%** of days; "
            f"flip-day nonzero **{100*(divergence[ETF_CODE].get('flip') or {}).get('pct_nonzero') or 0:.0f}%** — "
            "**material book divergence**.",
            f"- **Engine gap:** `keep_0050=False` under freeze-sleeve-$ recon is a **no-op** "
            f"(probes moved 0050: **{decision['keep_0050_false_moves_etf']}**). Need new ETF policy.",
            f"- **`{SATELLITE_CODE}`:** diverge only **{100*(divergence[SATELLITE_CODE].get('pct_days_differ') or 0):.1f}%** of days; "
            "overlay-owned (COOL/Soft) — **not** direct Path3 sleeve apply.",
            "",
            "## Disposition",
            "",
            "- **Research 0050 under Path3:** YES — but Stage B = **new recon policy design**, not live bool.",
            "- **Apply Path3 to satellite now:** NO — overlay re-home charter first.",
            "- Do **not** block 0kac `PAPER_WITHIN_HIT` (FIN∪TEL) on this track.",
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

    print(json.dumps({"verdict": verdict, "etf_pct": decision["etf_pct_days_differ"], "sat_pct": decision["satellite_pct_days_differ"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
