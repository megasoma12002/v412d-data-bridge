#!/usr/bin/env python3
"""MDD / loss-engine diagnosis on formal E22_v2s NAV (RESEARCH_ONLY).

Measures where drawdowns form under live-core books. Does not retune E16,
does not live-wire, and does not claim a PASS challenger.

Outputs:
  repro/mdd-loss-engine/reports/mdd_diagnosis.json
  research/gaps/MDD_LOSS_ENGINE_DIAGNOSIS.md (+ JSON)
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
NAV_PATH = ROOT / "repro/e22-v2s-historical-recompute/outputs/e22_v2s_daily_nav.csv"
OUT_DIR = ROOT / "repro/mdd-loss-engine"
REPORTS = OUT_DIR / "reports"
RESEARCH = ROOT / "research/gaps"

TARGET_CAGR = 0.20
TARGET_MDD = -0.15


def max_drawdown(nav: np.ndarray) -> float:
    peak = np.maximum.accumulate(nav)
    return float(np.min(nav / peak - 1.0))


def cagr(nav: np.ndarray, n_days: int) -> float:
    if n_days <= 1 or nav[0] <= 0:
        return float("nan")
    years = n_days / 252.0
    return float((nav[-1] / nav[0]) ** (1.0 / years) - 1.0)


def drawdown_episodes(dates: list, nav: np.ndarray, min_depth: float = -0.08) -> list[dict]:
    peak = nav[0]
    peak_i = 0
    in_dd = False
    start_i = 0
    trough_i = 0
    trough_nav = nav[0]
    eps: list[dict] = []
    for i in range(len(nav)):
        if nav[i] >= peak:
            if in_dd:
                depth = trough_nav / peak - 1.0
                if depth <= min_depth:
                    eps.append(
                        {
                            "peak_date": str(dates[peak_i]),
                            "start_date": str(dates[start_i]),
                            "trough_date": str(dates[trough_i]),
                            "recover_date": str(dates[i]),
                            "depth": float(depth),
                            "length_days": int(trough_i - start_i + 1),
                            "recover_days": int(i - trough_i),
                        }
                    )
                in_dd = False
            peak = nav[i]
            peak_i = i
        else:
            if not in_dd:
                in_dd = True
                start_i = i
                trough_i = i
                trough_nav = nav[i]
            elif nav[i] < trough_nav:
                trough_i = i
                trough_nav = nav[i]
    if in_dd:
        depth = trough_nav / peak - 1.0
        if depth <= min_depth:
            eps.append(
                {
                    "peak_date": str(dates[peak_i]),
                    "start_date": str(dates[start_i]),
                    "trough_date": str(dates[trough_i]),
                    "recover_date": None,
                    "depth": float(depth),
                    "length_days": int(trough_i - start_i + 1),
                    "recover_days": None,
                }
            )
    eps.sort(key=lambda x: x["depth"])
    return eps


def main() -> None:
    df = pl.read_csv(NAV_PATH).with_columns(pl.col("date").str.to_date()).sort("date")
    nav = df["nav"].to_numpy()
    dates = df["date"].to_list()
    rets = np.diff(nav) / nav[:-1]
    eq = df["equity_weight"].to_numpy()
    fin = df["tgt_financial"].to_numpy()
    e45 = df["e45_equity_scale"].to_numpy()
    regimes = df["regime"].to_list()

    overall = {
        "start": str(dates[0]),
        "end": str(dates[-1]),
        "n_days": int(len(nav)),
        "cagr": cagr(nav, len(nav)),
        "max_drawdown": max_drawdown(nav),
        "mean_equity_weight": float(np.nanmean(eq)),
        "mean_tgt_financial": float(np.nanmean(fin)),
        "mean_e45_equity_scale": float(np.nanmean(e45)),
        "gap_cagr_pp": float((cagr(nav, len(nav)) - TARGET_CAGR) * 100.0),
        "gap_mdd_pp_deeper_than_15": float((-TARGET_MDD + max_drawdown(nav)) * -100.0)
        if max_drawdown(nav) < TARGET_MDD
        else float((max_drawdown(nav) - TARGET_MDD) * 100.0),
    }
    # clearer MDD gap: how many pp deeper than -15%
    mdd = overall["max_drawdown"]
    overall["mdd_pp_vs_neg15"] = float((mdd - TARGET_MDD) * 100.0)  # negative => deeper

    episodes = drawdown_episodes(dates, nav, min_depth=-0.08)
    top = episodes[:5]

    # Path stats inside each top episode (peak→trough)
    enriched = []
    for ep in top:
        start = pl.date(
            int(ep["peak_date"][:4]), int(ep["peak_date"][5:7]), int(ep["peak_date"][8:10])
        )
        end = pl.date(
            int(ep["trough_date"][:4]), int(ep["trough_date"][5:7]), int(ep["trough_date"][8:10])
        )
        sub = df.filter((pl.col("date") >= start) & (pl.col("date") <= end))
        reg_counts = sub["regime"].value_counts().to_dicts()
        enriched.append(
            {
                **ep,
                "mean_tgt_financial": float(sub["tgt_financial"].mean()),
                "mean_equity_weight": float(sub["equity_weight"].mean()),
                "mean_e45_equity_scale": float(sub["e45_equity_scale"].mean()),
                "min_e45_equity_scale": float(sub["e45_equity_scale"].min()),
                "regime_counts": {r["regime"]: int(r["count"]) for r in reg_counts},
                "share_crisis_regime": float((sub["regime"] == "Crisis").sum() / max(sub.height, 1)),
            }
        )

    # Worst single-day losses and concurrent state
    order = np.argsort(rets)[:15]
    worst_days = []
    for j in order:
        i = j + 1  # return from i-1 → i uses state at i
        worst_days.append(
            {
                "date": str(dates[i]),
                "ret": float(rets[j]),
                "regime": regimes[i],
                "tgt_financial": float(fin[i]),
                "equity_weight": float(eq[i]),
                "e45_equity_scale": float(e45[i]),
            }
        )

    # Conditional mean daily return by regime
    by_reg = []
    for reg in sorted(set(regimes)):
        idx = [k for k, r in enumerate(regimes) if r == reg and k > 0]
        if not idx:
            continue
        r = rets[[k - 1 for k in idx]]
        by_reg.append(
            {
                "regime": reg,
                "n_days": len(idx),
                "mean_ret": float(np.mean(r)),
                "mean_tgt_financial": float(np.mean(fin[idx])),
                "mean_equity_weight": float(np.mean(eq[idx])),
                "mean_e45_equity_scale": float(np.mean(e45[idx])),
                "share_of_calendar": float(len(idx) / (len(nav) - 1)),
            }
        )

    # Simple PROXY counterfactuals on NAV returns (label clearly — not Exact T+1 engine)
    # L1a: on Crisis days, scale that day's equity return contribution by 0.70 / 0.50
    # Approximate: r_proxy = r * (cash_w + eq_w * scale) / (cash_w + eq_w) ≈ r * (1 - eq*(1-scale))
    def proxy_scale(crisis_scale: float) -> dict:
        r2 = rets.copy()
        for j in range(len(rets)):
            i = j + 1
            if regimes[i] == "Crisis":
                ew = float(eq[i])
                r2[j] = rets[j] * (1.0 - ew * (1.0 - crisis_scale))
        nav2 = np.empty(len(nav))
        nav2[0] = nav[0]
        for j in range(len(rets)):
            nav2[j + 1] = nav2[j] * (1.0 + r2[j])
        return {
            "label": f"PROXY_CRISIS_EQ_SCALE_{int(crisis_scale * 100)}",
            "note": "Return-path proxy only; not Exact T+1 / not fill-accurate",
            "crisis_equity_scale": crisis_scale,
            "cagr": cagr(nav2, len(nav2)),
            "max_drawdown": max_drawdown(nav2),
            "mdd_improve_pp_vs_base": float((max_drawdown(nav2) - mdd) * 100.0),
            "cagr_giveback_pp_vs_base": float((overall["cagr"] - cagr(nav2, len(nav2))) * 100.0),
        }

    proxies = [proxy_scale(0.70), proxy_scale(0.50), proxy_scale(0.30)]

    # FIN weight conditional: days with fin>=0.80 vs <0.60 mean return in Crisis
    crisis_idx = [k for k, r in enumerate(regimes) if r == "Crisis" and k > 0]
    hi = [k for k in crisis_idx if fin[k] >= 0.80]
    lo = [k for k in crisis_idx if fin[k] <= 0.60]
    fin_crisis = {
        "crisis_days": len(crisis_idx),
        "crisis_fin_ge_80_n": len(hi),
        "crisis_fin_ge_80_mean_ret": float(np.mean(rets[[k - 1 for k in hi]])) if hi else None,
        "crisis_fin_le_60_n": len(lo),
        "crisis_fin_le_60_mean_ret": float(np.mean(rets[[k - 1 for k in lo]])) if lo else None,
    }

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "book": "E22_v2s formal historical recompute",
        "nav_path": str(NAV_PATH.relative_to(ROOT)),
        "live_wire": False,
        "research_only": True,
        "targets": {"cagr": TARGET_CAGR, "mdd": TARGET_MDD},
        "overall": overall,
        "top_drawdown_episodes_min_8pct": enriched,
        "worst_daily_losses": worst_days,
        "by_regime": by_reg,
        "finance_in_crisis": fin_crisis,
        "proxy_loss_overlays": proxies,
        "implications": [
            "Formal core MDD ~-22.6% remains ~8pp deeper than -15% target.",
            "FIN_CAP_50 (parallel research) improves held MDD ~3pp to ~-19.6% — still short of -15%.",
            "Need a dedicated loss engine (exposure/crisis budget), not more TECH2 stress remix or S1 cut retune.",
            "Proxy crisis equity scales are hypothesis generators only — any candidate must re-run Exact T+1 OOF+held-out.",
        ],
    }

    REPORTS.mkdir(parents=True, exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)
    (REPORTS / "mdd_diagnosis.json").write_text(json.dumps(payload, indent=2) + "\n")
    (RESEARCH / "MDD_LOSS_ENGINE_DIAGNOSIS.json").write_text(json.dumps(payload, indent=2) + "\n")

    lines = [
        "# MDD Loss-Engine Diagnosis (E22_v2s formal)",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Status: **RESEARCH_ONLY** — no live-wire, no Soft-Frozen edit.",
        "",
        "## Overall gap",
        "",
        f"| Metric | Value | vs target |",
        f"|---|---:|---|",
        f"| CAGR | {overall['cagr']:.2%} | target ≥20% → **{overall['gap_cagr_pp']:+.1f} pp** |",
        f"| MDD | {overall['max_drawdown']:.2%} | target ≤15% depth → **{overall['mdd_pp_vs_neg15']:+.1f} pp** (neg=deeper) |",
        f"| Mean tgt Financial | {overall['mean_tgt_financial']:.1%} | structural concentration |",
        f"| Mean E45 equity scale | {overall['mean_e45_equity_scale']:.3f} | existing crisis scaler |",
        "",
        "## Top drawdown episodes (≥8% depth)",
        "",
        "| Peak | Trough | Depth | Mean fin | Mean eq | Mean E45 | Crisis share |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for ep in enriched:
        lines.append(
            f"| {ep['peak_date']} | {ep['trough_date']} | {ep['depth']:.1%} | "
            f"{ep['mean_tgt_financial']:.1%} | {ep['mean_equity_weight']:.1%} | "
            f"{ep['mean_e45_equity_scale']:.3f} | {ep['share_crisis_regime']:.1%} |"
        )
    lines += [
        "",
        "## Regime conditional (daily)",
        "",
        "| Regime | N | Mean ret | Mean fin | Mean eq | Mean E45 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for r in by_reg:
        lines.append(
            f"| {r['regime']} | {r['n_days']} | {r['mean_ret']:.5f} | "
            f"{r['mean_tgt_financial']:.1%} | {r['mean_equity_weight']:.1%} | "
            f"{r['mean_e45_equity_scale']:.3f} |"
        )
    lines += [
        "",
        "## Finance × Crisis (descriptive)",
        "",
        f"- Crisis days: **{fin_crisis['crisis_days']}**",
        f"- Crisis & fin≥80%: n={fin_crisis['crisis_fin_ge_80_n']}, mean ret={fin_crisis['crisis_fin_ge_80_mean_ret']}",
        f"- Crisis & fin≤60%: n={fin_crisis['crisis_fin_le_60_n']}, mean ret={fin_crisis['crisis_fin_le_60_mean_ret']}",
        "",
        "## Proxy overlays (NOT Exact T+1 — hypothesis only)",
        "",
        "| Proxy | CAGR | MDD | MDD Δpp vs base | CAGR giveback pp |",
        "|---|---:|---:|---:|---:|",
    ]
    for p in proxies:
        lines.append(
            f"| {p['label']} | {p['cagr']:.2%} | {p['max_drawdown']:.2%} | "
            f"{p['mdd_improve_pp_vs_base']:+.2f} | {p['cagr_giveback_pp_vs_base']:+.2f} |"
        )
    lines += [
        "",
        "## Implications for L1 charter",
        "",
        "1. Core MDD will not hit ≤15% via Stage-8 TECH2 remix or Track B S1 cut retune (both closed).",
        "2. FIN_CAP_50 helps ~3pp but leaves ~−19.6% held MDD — need **additional** crisis/exposure loss engine.",
        "3. Proxy crisis equity scales that improve MDD must be rebuilt as Exact T+1 challengers with frozen OOF→held-out gates.",
        "4. Keep BASE_E16 / E22_v2s ledgers; any promote is cutover-only dual paper books.",
        "",
        "See charter: `research/gaps/MDD_LOSS_ENGINE_CHARTER.md`",
        "",
    ]
    md = "\n".join(lines)
    (OUT_DIR / "MDD_LOSS_ENGINE_DIAGNOSIS.md").write_text(md)
    (RESEARCH / "MDD_LOSS_ENGINE_DIAGNOSIS.md").write_text(md)
    print(json.dumps({"cagr": overall["cagr"], "mdd": mdd, "n_episodes": len(episodes)}, indent=2))
    print("EXIT:0")


if __name__ == "__main__":
    main()
