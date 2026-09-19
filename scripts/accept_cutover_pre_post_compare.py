#!/usr/bin/env python3
"""PRE (main live) vs POST (ACCEPT cutover #257) Exact T+1 paper compare.

Research / ops only — does not flip Soft-Frozen or rewrite forward/e21.

PRE  = FUSE_ADDITIVE + DH_dd06 + KD_OPT (公股) + E22_v3_recv_pay_effdelay
POST = FUSE → BLEND_025 → L4_DD_PATH_08_50 → DH + PRIV_KD + E22_v3_recv_pay_tax10
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import e16_soft_frozen_base as soft
import e22_dividend_accounting as e22div
import live_blend_l4_cutover as bl
import live_dh_fuse_cutover as live_cut
import live_priv_native_cutover as priv
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, load_market, window_stats
from e50_early_stack_combined_nav import e16_features, simulate_core
from portfolio_capital import DEFAULT_CAPITAL
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp
from tw_share_lots import BOARD_LOT
from within_sleeve_alloc import FIN_PRE_EXDIV_KD, TEL_EQUAL

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/accept-cutover-pre-post-compare"
OPS = ROOT / "research/ops"


def _tip_windows(nav: pd.DataFrame) -> dict:
    asof = pd.Timestamp(pd.to_datetime(nav["date"]).max())
    dates = pd.to_datetime(nav["date"])
    out = {}
    for name, start in (
        ("ytd", pd.Timestamp(asof.year, 1, 1)),
        ("trailing_1y", asof - pd.Timedelta(days=365)),
    ):
        sub = nav[(dates >= start) & (dates <= asof)].reset_index(drop=True)
        out[name] = window_stats(sub, None, None) if len(sub) >= 20 else {
            "cagr": None,
            "max_drawdown": None,
            "n_days": int(len(sub)),
        }
    return out


def _pack(nav: pd.DataFrame) -> dict:
    win = {w: window_stats(nav, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
    win.update(_tip_windows(nav))
    return {
        w: {
            "cagr": None if st.get("cagr") is None else round(float(st["cagr"]), 6),
            "max_drawdown": None
            if st.get("max_drawdown") is None
            else round(float(st["max_drawdown"]), 6),
            "n_days": int(st.get("n_days") or 0),
        }
        for w, st in win.items()
    }


def _delta(pre: dict, post: dict) -> dict:
    out = {}
    for w, pst in post.items():
        pr = pre.get(w) or {}
        # giveback = PRE − POST (positive = POST lags / worse return)
        giveback = cagr_delta_pp(pr.get("cagr"), pst.get("cagr"), missing_as_zero=True)
        mdd_pp = mdd_delta_pp(pr.get("max_drawdown"), pst.get("max_drawdown"))
        out[w] = {
            "pre_cagr": pr.get("cagr"),
            "post_cagr": pst.get("cagr"),
            "cagr_giveback_pp": None if giveback is None else round(float(giveback), 4),
            "cagr_improve_pp": None if giveback is None else round(-float(giveback), 4),
            "pre_mdd": pr.get("max_drawdown"),
            "post_mdd": pst.get("max_drawdown"),
            "mdd_improve_pp": None if mdd_pp is None else round(float(mdd_pp), 4),
            "n_days": pst.get("n_days"),
        }
    return out


def _sim_stack(
    *,
    market: pd.DataFrame,
    dividends: pd.DataFrame,
    target: pd.DataFrame,
    regime: pd.Series,
    e22_version: str,
    label: str,
) -> tuple[pd.DataFrame, dict]:
    _kd, buy_ok, buy, sell = live_cut._kd_panels(market, dividends)
    # Offense pass (FUSE softs on this universe) drives DH exposure — paper-faithful MENU3.
    offense_target = live_cut.fuse_target_for_market(market)
    _p, _s, _t, offense_regime = e16_features(market)
    offense_nav, _fills_o, meta_o = simulate_core(
        market,
        offense_target,
        offense_regime,
        dividends,
        apply_e22=True,
        apply_stock_div=True,
        e22_version=e22_version,
        capital=float(DEFAULT_CAPITAL),
        lot_size=int(BOARD_LOT),
        financial_alloc=FIN_PRE_EXDIV_KD,
        telecom_alloc=TEL_EQUAL,
        fin_name_scores=buy,
        fin_buy_ok=buy_ok,
        fin_sell_scores=sell,
    )
    if not bool(meta_o.get("exact_t1_ok")):
        raise SystemExit(f"{label} offense exact_t1_ok failed")
    exp = live_cut.build_dh_exposure_from_offense(market, offense_nav)
    nav, fills, meta = simulate_core(
        market,
        target,
        regime,
        dividends,
        apply_e22=True,
        apply_stock_div=True,
        e22_version=e22_version,
        capital=float(DEFAULT_CAPITAL),
        lot_size=int(BOARD_LOT),
        financial_alloc=FIN_PRE_EXDIV_KD,
        telecom_alloc=TEL_EQUAL,
        fin_name_scores=buy,
        fin_buy_ok=buy_ok,
        fin_sell_scores=sell,
        e45_exposure=exp,
        e45_sleeve_names=("Financial", "Telecom", "0050"),
    )
    if not bool(meta.get("exact_t1_ok")):
        raise SystemExit(f"{label} final exact_t1_ok failed")
    return nav, {
        "label": label,
        "e22_books_version": e22_version,
        "exact_t1_ok": True,
        "n_fills": int(len(fills)),
        "mean_dh_exposure": float(exp.mean()) if len(exp) else None,
        "dh_defense_frac": float((exp < 0.999).mean()) if len(exp) else None,
        "end_nav": float(nav["nav"].iloc[-1]),
        "asof": str(pd.to_datetime(nav["date"]).max().date()),
    }


def main() -> int:
    assert list(soft.SOFT_FROZEN_FIN_CLIP) == [0.6, 0.9]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "outputs").mkdir(exist_ok=True)

    print("loading market ...", flush=True)
    market_pub = load_market()
    dividends = load_dividends()

    # --- PRE: main live (pub FIN, FUSE+DH, Stage-E books) ---
    print("PRE (main live) ...", flush=True)
    import e50_early_stack_combined_nav as e50

    pub_fin = ["2880", "2886", "2892", "5880"]
    soft.FIN = list(pub_fin)
    e50.FIN = list(pub_fin)
    e50.ALL = list(pub_fin) + ["2412", "3045", "4904", "0050"]
    pre_target = live_cut.fuse_target_for_market(market_pub)
    _p, _s, _t, pre_regime = e16_features(market_pub)
    nav_pre, meta_pre = _sim_stack(
        market=market_pub,
        dividends=dividends,
        target=pre_target,
        regime=pre_regime,
        e22_version=e22div.E22_V3_RECV_PAY_EFFDELAY,
        label="PRE_MAIN_FUSE_DH_PUB_EFFDELAY",
    )

    # --- POST: cutover (priv FIN, FUSE→BLEND→L4→DH, tax10) ---
    print("POST (cutover bundle) ...", flush=True)
    market_priv = priv.extend_market_for_priv(market_pub)
    priv.apply_priv_universe_globals()
    post_target = live_cut.fuse_target_for_market(market_priv)
    post_target, blend_meta = bl.apply_blend025(post_target, market_priv)
    post_target, l4_meta = bl.apply_l4_dd_path(post_target, market_priv)
    _p2, _s2, _t2, post_regime = e16_features(market_priv)
    nav_post, meta_post = _sim_stack(
        market=market_priv,
        dividends=dividends,
        target=post_target,
        regime=post_regime,
        e22_version=e22div.E22_V3_RECV_PAY_TAX10,
        label="POST_CUTOVER_FUSE_BLEND_L4_DH_PRIV_TAX10",
    )
    meta_post["blend025"] = blend_meta
    meta_post["l4_dd_path"] = l4_meta

    win_pre = _pack(nav_pre)
    win_post = _pack(nav_post)
    delta = _delta(win_pre, win_post)

    compare = (
        nav_pre[["date", "nav"]]
        .rename(columns={"nav": "nav_pre"})
        .merge(
            nav_post[["date", "nav"]].rename(columns={"nav": "nav_post"}),
            on="date",
            how="inner",
        )
    )
    compare["rel_post_vs_pre"] = compare["nav_post"] / compare["nav_pre"]
    compare.to_csv(OUT / "outputs" / "pre_post_compare_nav.csv", index=False)
    nav_pre.to_csv(OUT / "outputs" / "pre_daily_nav.csv", index=False)
    nav_post.to_csv(OUT / "outputs" / "post_daily_nav.csv", index=False)

    tip_rel = float(compare["rel_post_vs_pre"].iloc[-1]) if len(compare) else None
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "ACCEPT_CUTOVER_PRE_POST_COMPARE",
        "live_wire": False,
        "soft_frozen_clip": list(soft.SOFT_FROZEN_FIN_CLIP),
        "capital": float(DEFAULT_CAPITAL),
        "lot_size": int(BOARD_LOT),
        "pre": {
            **meta_pre,
            "stack": "FUSE_ADDITIVE + DH_dd06 + KD_OPT(公股) + E22_v3_recv_pay_effdelay",
            "windows": win_pre,
        },
        "post": {
            **meta_post,
            "stack": (
                "FUSE → BLEND_025 → L4_DD_PATH_08_50 → DH + PRIV_KD + "
                "E22_v3_recv_pay_tax10"
            ),
            "windows": win_post,
        },
        "delta_post_minus_pre": delta,
        "tip_rel_nav_post_vs_pre": tip_rel,
        "method_note": (
            "Exact T+1 simulate_core; DH exposure from FUSE offense NAV (MENU3); "
            "POST extends market via private_fin_adjusted ffill. "
            "Not a Soft-Frozen gate; tip lag / priv ffill may differ from forward tip."
        ),
    }
    (OUT / "reports" / "accept_cutover_pre_post_compare.json").parent.mkdir(
        parents=True, exist_ok=True
    )
    json_path = OUT / "reports" / "accept_cutover_pre_post_compare.json"
    json_path.write_text(json.dumps(payload, indent=2) + "\n")

    def pct(x):
        return "n/a" if x is None else f"{100.0 * float(x):.2f}%"

    def pp(x):
        return "n/a" if x is None else f"{float(x):+.2f} pp"

    lines = [
        "# ACCEPT cutover — PRE vs POST live-stack paper compare",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Status: **RESEARCH / OPS** — Soft-Frozen KEEP · no forward rewrite",
        "",
        "## Stacks",
        "",
        f"- **PRE (main):** `{payload['pre']['stack']}`",
        f"- **POST (#257):** `{payload['post']['stack']}`",
        f"- Tip relative NAV (POST/PRE): **{tip_rel:.4f}**" if tip_rel else "- Tip rel: n/a",
        f"- PRE end NAV: **{meta_pre['end_nav']:,.0f}** · POST end NAV: **{meta_post['end_nav']:,.0f}**",
        "",
        "## Windows (POST − PRE)",
        "",
        "| Window | PRE CAGR | POST CAGR | Giveback | Improve | PRE MDD | POST MDD | MDD improve |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for w in (
        "ytd",
        "trailing_1y",
        "sealed_2023_plus",
        "heldout_2019_plus",
        "full",
    ):
        d = delta[w]
        lines.append(
            f"| {w} | {pct(d['pre_cagr'])} | {pct(d['post_cagr'])} | {pp(d['cagr_giveback_pp'])} | "
            f"{pp(d['cagr_improve_pp'])} | {pct(d['pre_mdd'])} | {pct(d['post_mdd'])} | "
            f"{pp(d['mdd_improve_pp'])} |"
        )
    lines += [
        "",
        "## Read",
        "",
        "- **Giveback > 0** = POST lags PRE on CAGR (worse return).",
        "- **Improve > 0** = POST beats PRE on CAGR.",
        "- **MDD improve > 0** = POST shallower drawdown.",
        "- Overlay (BLEND/L4) usually dominates books tax10 (~−0.3 pp sealed on constant-hold).",
        "",
        f"Repro: `PYTHONPATH=scripts python3 scripts/accept_cutover_pre_post_compare.py`",
        f"Artifacts: `{OUT.relative_to(ROOT)}/`",
        "",
    ]
    md_path = OUT / "reports" / "accept_cutover_pre_post_compare.md"
    md_path.write_text("\n".join(lines))
    # Mirror short note under research/ops for humans.
    OPS.joinpath("ACCEPT_CUTOVER_PRE_POST_COMPARE.md").write_text("\n".join(lines))
    OPS.joinpath("ACCEPT_CUTOVER_PRE_POST_COMPARE.json").write_text(
        json.dumps(payload, indent=2) + "\n"
    )
    print(json.dumps({
        "tip_rel": tip_rel,
        "delta": {
            k: delta[k]
            for k in ("ytd", "trailing_1y", "sealed_2023_plus", "heldout_2019_plus")
        },
    }, indent=2))
    print(md_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
