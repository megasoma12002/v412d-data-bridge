#!/usr/bin/env python3
"""E45 remaining-improve research batch — PAPER / OBSERVE ONLY.

Human: 「請問像E45系列策略還有可以改善的地方嗎」→「請進行研究」

Does:
  1) Extend/refresh observe trailing PAUSE tips (incl. M2 C35)
  2) Cross-sleeve scoreboard vs BASE (held-out / sealed / full + tip gates)
  3) Year MDD help honesty (2015/2018/2020/2022) for observe books
  4) Re-run cheap-protect × cost pack (tax-control reference)

Never Soft-Frozen / DEFAULT / stitch / HIGH_BETA flips.
Never invents replacement for retired MDD narrative.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from e16_soft_frozen_base import SOFT_FROZEN_FIN_CLIP
from e45_paper_harness import CLAIM_STATUS, WINDOWS_STANDARD, window_stats
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp

OUT = ROOT / "repro/e45-remaining-improve-20260908"
OPS = ROOT / "research/ops"
E45 = ROOT / "research/e45"

SLEEVES = {
    "CHAL_E45_E3": {
        "base": ROOT / "repro/e45-dual-paper-observe/outputs/base_e16_e18_e22_v2s_daily_nav.csv",
        "chal": ROOT / "repro/e45-dual-paper-observe/outputs/chal_e45_e3_daily_nav.csv",
    },
    "BLEND_E45_A25": {
        "base": ROOT / "repro/e45-blend025-dual-paper-observe/outputs/base_e16_e18_e22_v2s_daily_nav.csv",
        "chal": ROOT / "repro/e45-blend025-dual-paper-observe/outputs/blend_e45_a25_daily_nav.csv",
    },
    "BLEND_E45_A05": {
        "base": ROOT / "repro/e45-blend005-dual-paper-observe/outputs/base_e16_e18_e22_v2s_daily_nav.csv",
        "chal": ROOT / "repro/e45-blend005-dual-paper-observe/outputs/blend_e45_a05_daily_nav.csv",
    },
    "SLEEVE_FIN_ONLY_A10": {
        "base": ROOT / "repro/e45-sleeve-local-dual-paper-observe/outputs/base_e16_e18_e22_v2s_daily_nav.csv",
        "chal": ROOT / "repro/e45-sleeve-local-dual-paper-observe/outputs/sleeve_fin_only_a10_daily_nav.csv",
    },
    "M2_RELOC_BIL_FX_C35": {
        "base": ROOT / "repro/e45-m2-bil-fx-dual-paper-observe/outputs/base_e16_e18_e22_v2s_daily_nav.csv",
        "chal": ROOT / "repro/e45-m2-bil-fx-dual-paper-observe/outputs/m2_reloc_bil_fx_c35_daily_nav.csv",
    },
}

CRISIS_YEARS = (2015, 2018, 2020, 2022)
ALERT_PP = 3.0
PAUSE_PP = 5.0


def load_nav(path: Path) -> pd.DataFrame:
    d = pd.read_csv(path)
    d["date"] = pd.to_datetime(d["date"])
    return d.sort_values("date").reset_index(drop=True)


def score_pair(base_s: dict, chal_s: dict) -> dict:
    mdd_pp = mdd_delta_pp(base_s.get("max_drawdown"), chal_s.get("max_drawdown"))
    cagr_pp = cagr_delta_pp(base_s.get("cagr"), chal_s.get("cagr"), missing_as_zero=True)
    give = abs(float(cagr_pp)) if cagr_pp is not None else 9.0
    return {
        "mdd_improve_pp": float(mdd_pp),
        "cagr_giveback_pp": float(cagr_pp) if cagr_pp is not None else None,
        "score": float(mdd_pp) - 0.5 * give,
        "cagr_chal": chal_s.get("cagr"),
        "mdd_chal": chal_s.get("max_drawdown"),
    }


def year_mdd(nav: pd.DataFrame, year: int) -> float | None:
    w = nav[(nav["date"] >= pd.Timestamp(year, 1, 1)) & (nav["date"] <= pd.Timestamp(year, 12, 31))]
    if len(w) < 20:
        return None
    path = w["nav"].to_numpy(dtype=float)
    peak = np.maximum.accumulate(path)
    return float(np.min(path / peak - 1.0))


def tip_gates(base: pd.DataFrame, chal: pd.DataFrame) -> dict:
    asof = min(base["date"].max(), chal["date"].max())

    def gb(window: str):
        start = pd.Timestamp(asof.year, 1, 1) if window == "ytd" else asof - pd.Timedelta(days=365)
        b = base[(base["date"] >= start) & (base["date"] <= asof)]
        c = chal[(chal["date"] >= start) & (chal["date"] <= asof)]
        if len(b) < 20 or len(c) < 20:
            return None, "INSUFFICIENT"
        sb = window_stats(b.reset_index(drop=True), None, None)
        sc = window_stats(c.reset_index(drop=True), None, None)
        if sb.get("cagr") is None or sc.get("cagr") is None:
            return None, "INSUFFICIENT"
        g = (sb["cagr"] - sc["cagr"]) * 100.0
        gate = "PAUSE_REVIEW" if g > PAUSE_PP else ("ALERT" if g > ALERT_PP else "PASS")
        return g, gate

    ytd_g, ytd_gate = gb("ytd")
    y1_g, y1_gate = gb("trailing_1y")
    return {
        "asof": asof.date().isoformat(),
        "ytd_giveback_pp": ytd_g,
        "ytd_gate": ytd_gate,
        "trailing_1y_giveback_pp": y1_g,
        "trailing_1y_gate": y1_gate,
    }


def sleeve_report(name: str, paths: dict) -> dict:
    if not paths["base"].exists() or not paths["chal"].exists():
        return {"sleeve": name, "ok": False, "reason": "missing_nav"}
    base = load_nav(paths["base"])
    chal = load_nav(paths["chal"])
    wins = {}
    for w, (a, b) in WINDOWS_STANDARD.items():
        sb = window_stats(base, a, b)
        sc = window_stats(chal, a, b)
        wins[w] = {"base": sb, "chal": sc, "vs_base": score_pair(sb, sc)}
    year_help = {}
    for y in CRISIS_YEARS:
        mb, mc = year_mdd(base, y), year_mdd(chal, y)
        if mb is None or mc is None:
            year_help[str(y)] = None
        else:
            year_help[str(y)] = (abs(mb) - abs(mc)) * 100.0  # positive ⇒ chal better MDD
    non2020 = [year_help[str(y)] for y in (2015, 2018, 2022) if year_help.get(str(y)) is not None]
    n_non2020_gt_025 = sum(1 for x in non2020 if x is not None and x > 0.25)
    return {
        "sleeve": name,
        "ok": True,
        "tip": tip_gates(base, chal),
        "windows": wins,
        "year_mdd_help_pp": year_help,
        "non2020_events_gt_025pp": int(n_non2020_gt_025),
        "heldout_score": wins["heldout_2019_plus"]["vs_base"]["score"],
        "sealed_score": wins["sealed_2023_plus"]["vs_base"]["score"],
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "outputs").mkdir(exist_ok=True)
    generated = datetime.now(timezone.utc).isoformat()

    print("==> observe pause refresh (incl C35)", flush=True)
    pause = subprocess.run(
        [sys.executable, str(ROOT / "scripts/e45_observe_pause_refresh.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    print(pause.stdout[-1500:], flush=True)
    if pause.returncode != 0:
        sys.stderr.write(pause.stderr[-2000:] + "\n")
        raise SystemExit(f"pause refresh failed rc={pause.returncode}")

    print("==> cross-sleeve scoreboard", flush=True)
    reports = [sleeve_report(k, v) for k, v in SLEEVES.items()]
    (OUT / "outputs/cross_sleeve_scoreboard.json").write_text(
        json.dumps({"generated_at_utc": generated, "sleeves": reports}, indent=2, default=str) + "\n"
    )

    print("==> cheap-protect × cost pack", flush=True)
    cheap = subprocess.run(
        [sys.executable, str(ROOT / "scripts/e45_cheap_protect_cost_data_paper.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    print(cheap.stdout[-2000:], flush=True)
    cheap_ok = cheap.returncode == 0
    if not cheap_ok:
        sys.stderr.write(cheap.stderr[-2000:] + "\n")

    ok = [r for r in reports if r.get("ok")]
    ranked = sorted(ok, key=lambda r: r["heldout_score"], reverse=True)
    tip_pause = [
        r["sleeve"]
        for r in ok
        if r["tip"]["ytd_gate"] == "PAUSE_REVIEW" or r["tip"]["trailing_1y_gate"] == "PAUSE_REVIEW"
    ]
    multi_ok = [r["sleeve"] for r in ok if r["non2020_events_gt_025pp"] >= 2]

    payload = {
        "generated_at_utc": generated,
        "label": "E45_REMAINING_IMPROVE_RESEARCH_BATCH",
        "ballot": "請進行研究 (E45 remaining improve)",
        "soft_frozen_keep": list(SOFT_FROZEN_FIN_CLIP),
        "default_books_keep": "E22_v2s_tw",
        "stitch": "FORBIDDEN",
        "high_beta": "HOLD_DRAFT_NOT_OPEN",
        "claim_status": CLAIM_STATUS,
        "live_wire": False,
        "pause_refresh_ok": True,
        "cheap_protect_ok": cheap_ok,
        "ranked_heldout": [
            {
                "sleeve": r["sleeve"],
                "heldout_score": r["heldout_score"],
                "sealed_score": r["sealed_score"],
                "tip": r["tip"],
                "non2020_events_gt_025pp": r["non2020_events_gt_025pp"],
                "year_mdd_help_pp": r["year_mdd_help_pp"],
            }
            for r in ranked
        ],
        "tip_pause_sleeves": tip_pause,
        "non2020_multi_event_pass_sleeves": multi_ok,
        "verdict": {
            "same_knob_family": "EXHAUSTED_PRIOR",
            "observe_trailing": "STILL_PAUSE_NO_STITCH",
            "best_heldout_observe_sleeve": ranked[0]["sleeve"] if ranked else None,
            "new_mechanism_needed_for_kpi": True,
            "actionable_next": [
                "continue_C35_and_tax_control_observe",
                "no_stitch_until_clean_trailing",
                "new_mechanism_only_if_§2_full_pack",
            ],
        },
    }
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    OPS.joinpath("E45_REMAINING_IMPROVE_RESEARCH_BATCH.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    lines = [
        "# E45 Remaining-Improve Research Batch",
        "",
        f"Generated: `{generated}`",
        "Ballot: **請進行研究** (E45 remaining avenues) · Soft-Frozen **KEEP** · stitch **FORBIDDEN**",
        f"Claimed MDD narrative: **`{CLAIM_STATUS}`**",
        f"Cheap-protect pack ok: **{cheap_ok}**",
        "",
        "## Tip trailing gates (observe)",
        "",
        "| Sleeve | asof | YTD | 1y | YTD giveback | 1y giveback | held-out score | sealed score | non-2020 events>0.25pp |",
        "|---|---|---|---|---:|---:|---:|---:|---:|",
    ]
    for r in ranked:
        t = r["tip"]

        def fmt(x):
            return "n/a" if x is None else f"{x:+.2f}"

        lines.append(
            f"| `{r['sleeve']}` | {t['asof']} | **{t['ytd_gate']}** | **{t['trailing_1y_gate']}** | "
            f"{fmt(t['ytd_giveback_pp'])} | {fmt(t['trailing_1y_giveback_pp'])} | "
            f"{r['heldout_score']:.3f} | {r['sealed_score']:.3f} | {r['non2020_events_gt_025pp']} |"
        )
    lines += [
        "",
        "## Year MDD help pp (positive = better than BASE)",
        "",
        "| Sleeve | 2015 | 2018 | 2020 | 2022 |",
        "|---|---:|---:|---:|---:|",
    ]
    for r in ranked:
        yh = r["year_mdd_help_pp"]

        def f2(y):
            v = yh.get(str(y))
            return "n/a" if v is None else f"{v:+.2f}"

        lines.append(
            f"| `{r['sleeve']}` | {f2(2015)} | {f2(2018)} | {f2(2020)} | {f2(2022)} |"
        )
    lines += [
        "",
        "## Verdict",
        "",
        f"- Tip PAUSE/ALERT sleeves: `{tip_pause}` → **continue observe; no stitch**.",
        f"- Non-2020 multi-event (≥2 of 2015/2018/2022 >0.25pp): `{multi_ok or 'none'}`.",
        f"- Best held-out observe sleeve this refresh: `{payload['verdict']['best_heldout_observe_sleeve']}`.",
        "- Same-knob E45 intensity family remains **exhausted**; further KPI progress needs **new mechanism** §2 pack.",
        "- Cheap-protect × cost remains **tax-control reference**, not Soft-Frozen/stitch evidence.",
        "",
        "## Hard non-actions",
        "",
        "- Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN · HIGH_BETA HOLD · no invented MDD",
        "",
        f"Repro: `{OUT.relative_to(ROOT)}/`",
        "Pause refresh: `research/ops/E45_OBSERVE_PAUSE_REFRESH.md`",
        "Cheap-protect: `research/ops/E45_CHEAP_PROTECT_COST_DATA.md`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "REPORT.md").write_text(md)
    OPS.joinpath("E45_REMAINING_IMPROVE_RESEARCH_BATCH.md").write_text(md)
    E45.joinpath("E45_REMAINING_IMPROVE_RESEARCH_BATCH.md").write_text(md)

    # sleeves status touch
    status = OPS / "E45_OBSERVE_SLEEVES_STATUS.md"
    if status.exists():
        note = (
            f"\n## Remaining-improve batch ({generated[:10]})\n\n"
            f"Paper batch `E45_REMAINING_IMPROVE_RESEARCH_BATCH.md` refreshed tip PAUSE "
            f"(incl. C35) + cross-sleeve scoreboard + cheap-protect. stitch FORBIDDEN.\n"
        )
        txt = status.read_text()
        if "Remaining-improve batch" not in txt:
            status.write_text(txt.rstrip() + "\n" + note)

    print(json.dumps({
        "best_heldout": payload["verdict"]["best_heldout_observe_sleeve"],
        "tip_pause": tip_pause,
        "non2020_multi": multi_ok,
        "cheap_ok": cheap_ok,
    }, indent=2))
    return 0 if cheap_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
