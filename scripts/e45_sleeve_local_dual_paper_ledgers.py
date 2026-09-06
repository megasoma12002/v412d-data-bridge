#!/usr/bin/env python3
"""E45 sleeve-local FIN_ONLY α=0.10 dual-paper ledgers (OPERATING OBSERVE — not live).

Side-by-side Exact T+1 paper books:
  BASE_E16_E18_E22_v2s — Soft-Frozen early-stack + formal E22_v2s
  SLEEVE_FIN_ONLY_A10  — same stack + E45 E3_VOLTARGET_WINNER @ α=0.10 on Financial sleeve only

Opened by human ballot: ``E45 ACCEPT OPEN sleeve-local observe``.
Parent: ``research/ops/E45_SLEEVE_LOCAL_OBSERVE_OPEN.md``.
Does NOT edit Soft-Frozen / DEFAULT / authorize stitch.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from e45_paper_harness import (
    BOOK_BASE,
    CLAIM_STATUS,
    E45_PROFILE_DEFAULT,
    ROOT,
    SLEEVE_FIN_ONLY,
    WINDOWS_STANDARD,
    blend_exposure,
    deltas_vs_base,
    e16_features,
    e45_full_exposure,
    load_dividends,
    load_market,
    run_early_stack,
    window_stats,
)

OUT = ROOT / "repro/e45-sleeve-local-dual-paper-observe"
RESEARCH = ROOT / "research/e45"

BASE_ID = BOOK_BASE
CHAL_ID = "SLEEVE_FIN_ONLY_A10"
BLEND_ALPHA = 0.10
SLEEVES = SLEEVE_FIN_ONLY


def main() -> None:
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)

    print("loading market + dividends ...", flush=True)
    market = load_market()
    dividends = load_dividends()

    print(f"{BASE_ID} features + sim ...", flush=True)
    _p, _s, target, regime = e16_features(market)
    nav_b, fills_b, meta_b = run_early_stack(
        market, target, regime, dividends, e45_exposure=None
    )

    print(f"{CHAL_ID} {E45_PROFILE_DEFAULT} sleeves={SLEEVES} α={BLEND_ALPHA} ...", flush=True)
    e45_full = e45_full_exposure(market, E45_PROFILE_DEFAULT)
    e45_blend = blend_exposure(e45_full, BLEND_ALPHA)
    assert e45_blend is not None
    e45_blend = e45_blend.rename("e45_sleeve_fin_only_a10_exposure")
    nav_c, fills_c, meta_c = run_early_stack(
        market,
        target,
        regime,
        dividends,
        e45_exposure=e45_blend,
        e45_sleeve_names=SLEEVES,
    )

    nav_b.to_csv(OUT / "outputs" / "base_e16_e18_e22_v2s_daily_nav.csv", index=False)
    nav_c.to_csv(OUT / "outputs" / "sleeve_fin_only_a10_daily_nav.csv", index=False)
    fills_b.to_csv(OUT / "outputs" / "base_e16_e18_e22_v2s_fills.csv", index=False)
    fills_c.to_csv(OUT / "outputs" / "sleeve_fin_only_a10_fills.csv", index=False)
    target.to_csv(OUT / "outputs" / "base_targets.csv")
    e45_blend.to_csv(OUT / "outputs" / "sleeve_fin_only_a10_exposure.csv")

    jb = nav_b[["date", "nav"]].rename(columns={"nav": "nav_base"})
    jc = nav_c[["date", "nav"]].rename(columns={"nav": "nav_sleeve_fin_only_a10"})
    joined = jb.merge(jc, on="date", how="inner")
    joined["rel_sleeve_vs_base"] = joined["nav_sleeve_fin_only_a10"] / joined["nav_base"]
    joined.to_csv(OUT / "outputs" / "dual_paper_nav_compare.csv", index=False)

    books: dict = {}
    for name, nav, meta in [(BASE_ID, nav_b, meta_b), (CHAL_ID, nav_c, meta_c)]:
        win = {w: window_stats(nav, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
        books[name] = {
            "exact_t1_ok": bool(meta.get("exact_t1_ok")),
            "mean_e45_exposure": meta.get("mean_e45_exposure"),
            "e45_sleeve_names": meta.get("e45_sleeve_names"),
            "windows": win,
        }

    held = deltas_vs_base(books[BASE_ID]["windows"]["heldout_2019_plus"], books[CHAL_ID]["windows"]["heldout_2019_plus"])
    sealed = deltas_vs_base(books[BASE_ID]["windows"]["sealed_2023_plus"], books[CHAL_ID]["windows"]["sealed_2023_plus"])

    proposal = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "E45_SLEEVE_LOCAL_DUAL_PAPER_OBSERVE_SLEEVE",
        "status": "OPERATING_OBSERVE",
        "live_wire": False,
        "soft_frozen_default_unchanged": True,
        "stitch_authorized": False,
        "cutover_authorized": False,
        "ballot": "E45 ACCEPT OPEN sleeve-local observe",
        "base_id": BASE_ID,
        "locked_challenger": CHAL_ID,
        "blend_alpha": BLEND_ALPHA,
        "e45_profile": E45_PROFILE_DEFAULT,
        "e45_sleeve_names": list(SLEEVES),
        "claimed_mdd_status": CLAIM_STATUS,
        "exact_t1": {
            "base": books[BASE_ID]["exact_t1_ok"],
            "sleeve_fin_only_a10": books[CHAL_ID]["exact_t1_ok"],
        },
        "books": books,
        "heldout_delta_vs_base": held,
        "sealed_delta_vs_base": sealed,
        "ops_checklist": [
            "Keep Soft-Frozen live default = BASE until a separate stitch / cutover PR",
            "Run BASE + SLEEVE_FIN_ONLY_A10 paper ledgers in parallel with month-end monitor",
            "Re-check YTD / trailing_1y PAUSE gates each month-end (observe ≠ promote)",
            "Do not silent-edit Soft-Frozen; do not rewrite forward/e21 history",
            "Observe sleeve ≠ stitch license; second human stitch ACCEPT still required",
            "Never cite −13.16%; use dated lineage / challenger MDDs only",
            "Leave FULL + A25 + A05 observe sleeves operating in parallel",
        ],
        "non_goals": [
            "Auto live-wire / four-layer stitch from this observe sleeve",
            "Soft-Frozen clip flip",
            "DEFAULT books flip away from E22_v2s_tw",
            "Invent a replacement for retired −13.16% narrative",
            "Retire FULL / A25 / A05 observe without separate ballot",
        ],
    }

    (OUT / "reports" / "e45_sleeve_local_dual_paper_observe.json").write_text(
        json.dumps(proposal, indent=2, default=str) + "\n"
    )
    (RESEARCH / "E45_SLEEVE_LOCAL_DUAL_PAPER_OBSERVE.json").write_text(
        json.dumps(proposal, indent=2, default=str) + "\n"
    )

    lines = [
        "# E45 Sleeve-Local FIN_ONLY α=0.10 Dual-Paper Observe Sleeve",
        "",
        f"Generated: `{proposal['generated_at_utc']}`",
        "Status: **OPERATING OBSERVE** — Soft-Frozen live default **unchanged**; live stitch **FORBIDDEN**.",
        "",
        "## Locked paper books",
        "",
        f"- **{BASE_ID}**: Soft-Frozen early-stack Exact T+1 + E22_v2s formal books",
        f"- **{CHAL_ID}**: same stack + α={BLEND_ALPHA:.2f} × E45 `{E45_PROFILE_DEFAULT}` on sleeves `{', '.join(SLEEVES)}` only",
        f"- Claimed −13.16%: **`{CLAIM_STATUS}`** (do not cite)",
        "",
        "## Dual paper metrics",
        "",
        "| Book | Window | CAGR | MDD | n_days | Exact T+1 |",
        "|---|---|---:|---:|---:|---|",
    ]
    for book, payload in books.items():
        for wname, st in payload["windows"].items():
            cagr, mdd = st.get("cagr"), st.get("max_drawdown")
            lines.append(
                f"| {book} | {wname} | "
                f"{(cagr if cagr is not None else float('nan')):.2%} | "
                f"{(mdd if mdd is not None else float('nan')):.2%} | "
                f"{st.get('n_days')} | {payload['exact_t1_ok']} |"
            )
    lines += [
        "",
        f"Held-out vs BASE: MDD improve **{held['mdd_improve_pp']:.2f} pp**; "
        f"CAGR giveback **{held['cagr_giveback_pp']:.2f} pp**; score **{held['score']:.3f}**.",
        f"Sealed vs BASE: MDD improve **{sealed['mdd_improve_pp']:.2f} pp**; "
        f"CAGR giveback **{sealed['cagr_giveback_pp']:.2f} pp**; score **{sealed['score']:.3f}**.",
        "",
        "## Ops checklist",
        "",
    ]
    for i, item in enumerate(proposal["ops_checklist"], 1):
        lines.append(f"{i}. {item}")
    lines += ["", "## Explicit non-goals", ""]
    for item in proposal["non_goals"]:
        lines.append(f"- {item}")
    lines += [
        "",
        "## Label",
        "",
        "`E45_SLEEVE_LOCAL_DUAL_PAPER_OBSERVE_SLEEVE`",
        "",
        "## Reproduce",
        "",
        "```bash",
        "python3 scripts/e45_sleeve_local_dual_paper_ledgers.py",
        "```",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "E45_SLEEVE_LOCAL_DUAL_PAPER_OBSERVE.md").write_text(md)
    (RESEARCH / "E45_SLEEVE_LOCAL_DUAL_PAPER_OBSERVE.md").write_text(md)
    print(json.dumps({
        "label": proposal["label"],
        "status": proposal["status"],
        "heldout": held,
        "sealed": sealed,
        "stitch_authorized": False,
    }, indent=2))
    print("EXIT:0")


if __name__ == "__main__":
    main()
