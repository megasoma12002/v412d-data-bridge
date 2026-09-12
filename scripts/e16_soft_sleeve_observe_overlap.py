#!/usr/bin/env python3
"""Soft-assist vs Sleeve-tilt observe overlap (paper only).

Compares excess daily returns of each challenger vs its own base:
  Soft-assist: SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a05 vs LIVE_KD_OPT
  Sleeve-tilt: SLEEVE_RSI14_LT30_a0225 vs LIVE_STACK

Reports correlation / same-sign overlap / joint drawdown contribution.
Does NOT authorize Soft-assist × Sleeve-tilt combo or any live wire.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOFT_COMPARE = ROOT / "repro/soft-assist-dual-paper-observe/outputs/dual_paper_nav_compare.csv"
SLEEVE_COMPARE = (
    ROOT / "repro/sleeve-tilt-dual-paper-observe/outputs/dual_paper_nav_compare.csv"
)
OUT_DIR = ROOT / "repro/soft-sleeve-observe-overlap"
OPS = ROOT / "research/ops"
SOFT_ID = "SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a05"
SLEEVE_ID = "SLEEVE_RSI14_LT30_a0225"


def _load_compare(path: Path, tag: str) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"Missing {path}; refresh dual-paper ledgers first")
    d = pd.read_csv(path)
    d["date"] = pd.to_datetime(d["date"])
    need = {"date", "nav_base", "nav_chal"}
    if not need.issubset(d.columns):
        raise SystemExit(f"{path} missing {need}")
    d = d.sort_values("date").drop_duplicates("date").reset_index(drop=True)
    d[f"rel_{tag}"] = d["nav_chal"].astype(float) / d["nav_base"].astype(float)
    # Excess daily return of challenger vs base (active return)
    r_base = d["nav_base"].astype(float).pct_change()
    r_chal = d["nav_chal"].astype(float).pct_change()
    d[f"ex_{tag}"] = r_chal - r_base
    return d[["date", f"rel_{tag}", f"ex_{tag}"]]


def _dd(rel: pd.Series) -> pd.Series:
    peak = rel.cummax()
    return rel / peak.replace(0.0, np.nan) - 1.0


def _window_stats(df: pd.DataFrame, start: pd.Timestamp | None, end: pd.Timestamp | None) -> dict:
    w = df
    if start is not None:
        w = w[w["date"] >= start]
    if end is not None:
        w = w[w["date"] <= end]
    w = w.dropna(subset=["ex_soft", "ex_sleeve"]).reset_index(drop=True)
    if len(w) < 30:
        return {
            "n_days": int(len(w)),
            "corr_excess": None,
            "same_sign_frac": None,
            "both_neg_frac": None,
            "joint_dd_day_frac": None,
            "mean_joint_dd_depth": None,
            "soft_mdd_rel": None,
            "sleeve_mdd_rel": None,
        }
    xs = w["ex_soft"].astype(float)
    xt = w["ex_sleeve"].astype(float)
    corr = float(xs.corr(xt)) if xs.std() > 0 and xt.std() > 0 else None
    same = float(((np.sign(xs) == np.sign(xt)) & (xs != 0) & (xt != 0)).mean())
    both_neg = float(((xs < 0) & (xt < 0)).mean())
    dd_s = _dd(w["rel_soft"].astype(float))
    dd_t = _dd(w["rel_sleeve"].astype(float))
    # Material joint relative DD: both ≥10bp below own peak
    material = -0.001
    soft_mat = dd_s <= material
    sleeve_mat = dd_t <= material
    either = soft_mat | sleeve_mat
    both_mat = soft_mat & sleeve_mat
    joint_frac = float(both_mat.sum() / either.sum()) if either.any() else 0.0
    if both_mat.any():
        depth = np.minimum(-dd_s[both_mat], -dd_t[both_mat])
        mean_depth = float(depth.mean())
    else:
        mean_depth = 0.0
    # Shared underperformance contribution: when soft excess < 0, mean sleeve excess (and swap)
    soft_down = xs < 0
    sleeve_down = xt < 0
    soft_pain_sleeve_mean = float(xt[soft_down].mean()) if soft_down.any() else None
    sleeve_pain_soft_mean = float(xs[sleeve_down].mean()) if sleeve_down.any() else None
    return {
        "n_days": int(len(w)),
        "corr_excess": corr,
        "same_sign_frac": same,
        "both_neg_frac": both_neg,
        "joint_dd_day_frac": joint_frac,
        "mean_joint_dd_depth": mean_depth,
        "soft_mdd_rel": float(dd_s.min()),
        "sleeve_mdd_rel": float(dd_t.min()),
        "when_soft_down_mean_sleeve_ex": soft_pain_sleeve_mean,
        "when_sleeve_down_mean_soft_ex": sleeve_pain_soft_mean,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "reports").mkdir(exist_ok=True)
    OPS.mkdir(parents=True, exist_ok=True)

    soft = _load_compare(SOFT_COMPARE, "soft")
    sleeve = _load_compare(SLEEVE_COMPARE, "sleeve")
    m = soft.merge(sleeve, on="date", how="inner").sort_values("date").reset_index(drop=True)
    asof = pd.Timestamp(m["date"].max())

    windows = {
        "full": (None, None),
        "heldout_2019_plus": (pd.Timestamp("2019-01-01"), None),
        "sealed_2023_plus": (pd.Timestamp("2023-01-01"), None),
        "ytd": (pd.Timestamp(asof.year, 1, 1), asof),
        "trailing_1y": (asof - pd.Timedelta(days=365), asof),
    }
    by_window = {name: _window_stats(m, a, b) for name, (a, b) in windows.items()}
    held = by_window["heldout_2019_plus"]

    # Report-only flags (do NOT gate promote; do NOT authorize combo)
    high_overlap = bool(
        held.get("corr_excess") is not None
        and held["corr_excess"] >= 0.50
        and held.get("same_sign_frac") is not None
        and held["same_sign_frac"] >= 0.55
    )
    high_joint_dd = bool(
        held.get("joint_dd_day_frac") is not None and held["joint_dd_day_frac"] >= 0.35
    )

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "SOFT_SLEEVE_OBSERVE_OVERLAP_2026-09-11",
        "status": "PAPER_REPORT_ONLY",
        "live_wire": False,
        "combo_authorized": False,
        "asof": str(asof.date()),
        "soft_challenger": SOFT_ID,
        "sleeve_challenger": SLEEVE_ID,
        "definition": {
            "excess_daily": "chal_return - base_return per track",
            "same_sign_frac": "share of days both excess returns same sign and non-zero",
            "both_neg_frac": "share of days both underperform their base",
            "joint_dd_day_frac": "among days with either rel-NAV DD≤−50bp, share where BOTH ≤−50bp",
            "mean_joint_dd_depth": "mean min(|dd_soft|,|dd_sleeve|) on material joint-DD days",
        },
        "windows": by_window,
        "heldout_flags": {
            "high_overlap_report": high_overlap,
            "high_joint_dd_report": high_joint_dd,
            "note": "Flags are report-only. High overlap/joint-DD argue against auto-combo, not for it.",
        },
        "non_actions": [
            "No Soft-assist x Sleeve-tilt auto-combo",
            "No live Soft-assist / Sleeve-tilt / Soft-Frozen / KD / TEL / E45 wire",
            "Overlap does not unlock promote",
        ],
    }

    def pct(x):
        return "—" if x is None else f"{100 * float(x):.1f}%"

    def num(x):
        return "—" if x is None else f"{float(x):.3f}"

    lines = [
        "# Soft-assist vs Sleeve-tilt Observe Overlap (paper only)",
        "",
        f"Generated: `{payload['generated_at_utc']}` · asof **{payload['asof']}**",
        f"Soft `{SOFT_ID}` ∥ Sleeve `{SLEEVE_ID}` · **no combo · no live wire**",
        "",
        "## Held-out (2019+) snapshot",
        "",
        f"- Corr(excess): **{num(held.get('corr_excess'))}**",
        f"- Same-sign frac: **{pct(held.get('same_sign_frac'))}**",
        f"- Both-underperform frac: **{pct(held.get('both_neg_frac'))}**",
        f"- Joint DD day frac: **{pct(held.get('joint_dd_day_frac'))}**",
        f"- Mean joint DD depth: **{pct(held.get('mean_joint_dd_depth'))}**",
        f"- Report flags: high_overlap=`{high_overlap}` · high_joint_dd=`{high_joint_dd}`",
        "",
        "## Windows",
        "",
        "| Window | N | Corr | Same-sign | Both− | Joint DD days | Mean joint DD | Soft rel MDD | Sleeve rel MDD |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, st in by_window.items():
        lines.append(
            f"| `{name}` | {st['n_days']} | {num(st['corr_excess'])} | "
            f"{pct(st['same_sign_frac'])} | {pct(st['both_neg_frac'])} | "
            f"{pct(st['joint_dd_day_frac'])} | {pct(st['mean_joint_dd_depth'])} | "
            f"{pct(st['soft_mdd_rel'])} | {pct(st['sleeve_mdd_rel'])} |"
        )
    lines += [
        "",
        "## Reading",
        "",
        "- Excess = challenger daily return − that track’s base daily return.",
        "- High held-out corr / same-sign / joint DD → **independent observe still required**; do **not** auto-combo.",
        "- This report never opens live cutover or a joint ACCEPT ballot.",
        "",
        "## Non-actions",
        "",
        "- No Soft-assist × Sleeve-tilt combo",
        "- No live wire from this report",
        "",
        "## Label",
        "",
        f"`{payload['label']}__NO_COMBO__NO_LIVE`",
        "",
    ]
    md = "\n".join(lines)
    zh = "\n".join(
        [
            "# Soft-assist vs Sleeve-tilt Observe Overlap（只測 paper）",
            "",
            f"產生：`{payload['generated_at_utc']}` · asof **{payload['asof']}**",
            f"Heldout corr **{num(held.get('corr_excess'))}** · same-sign **{pct(held.get('same_sign_frac'))}** · joint DD days **{pct(held.get('joint_dd_day_frac'))}**",
            f"flags: high_overlap=`{high_overlap}` · high_joint_dd=`{high_joint_dd}`",
            "",
            "**不上 live、不授權 combo。** 高 overlap 是反對自動拼裝的證據。",
            "",
            "英文：`SOFT_SLEEVE_OBSERVE_OVERLAP.md`",
            "",
        ]
    )

    (OUT_DIR / "outputs").mkdir(parents=True, exist_ok=True)
    m.to_csv(OUT_DIR / "outputs" / "soft_sleeve_excess_aligned.csv", index=False)
    (OUT_DIR / "reports" / "soft_sleeve_observe_overlap.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (OUT_DIR / "reports" / "SOFT_SLEEVE_OBSERVE_OVERLAP.md").write_text(md, encoding="utf-8")
    (OPS / "SOFT_SLEEVE_OBSERVE_OVERLAP.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (OPS / "SOFT_SLEEVE_OBSERVE_OVERLAP.md").write_text(md, encoding="utf-8")
    (OPS / "SOFT_SLEEVE_OBSERVE_OVERLAP.zh-TW.md").write_text(zh, encoding="utf-8")

    print(
        json.dumps(
            {
                "asof": payload["asof"],
                "heldout_corr": held.get("corr_excess"),
                "heldout_same_sign": held.get("same_sign_frac"),
                "heldout_joint_dd_frac": held.get("joint_dd_day_frac"),
                "high_overlap_report": high_overlap,
                "high_joint_dd_report": high_joint_dd,
                "combo_authorized": False,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
