#!/usr/bin/env python3
"""Shared dual/multi-paper ledger driver (ops / research).

Collapses near-copy ``*_dual_paper_ledgers.py`` scripts onto ``simulate_core``
via ``DualPaperLedgerSpec`` / ``MultiPaperLedgerSpec``. Soft-Frozen unchanged;
no live wire. Strategy book construction stays in prepare callbacks / helpers.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import pandas as pd

from e45_paper_harness import (
    WINDOWS_STANDARD,
    deltas_vs_base,
    load_dividends,
    load_market,
    window_stats,
)
from e50_early_stack_combined_nav import simulate_core
from portfolio_capital import DEFAULT_CAPITAL
from tw_share_lots import BOARD_LOT

ROOT = Path(__file__).resolve().parents[1]

PrepareFn = Callable[[pd.DataFrame, pd.DataFrame], "PreparedBooks"]
ReportFn = Callable[["LedgerResult"], None]


@dataclass
class PreparedBooks:
    """Outputs of a ledger prepare step (strategy stays outside the runner)."""

    base_target: pd.DataFrame
    base_regime: pd.Series
    chal_target: pd.DataFrame
    chal_regime: pd.Series
    base_kwargs: dict[str, Any] = field(default_factory=dict)
    chal_kwargs: dict[str, Any] = field(default_factory=dict)
    # Extra artifacts written under outputs/ (Series/DataFrame).
    extras: dict[str, pd.Series | pd.DataFrame] = field(default_factory=dict)
    # Free-form context for report builders (scores, flags, metadata).
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DualPaperLedgerSpec:
    """Config for one BASE vs CHAL Exact T+1 paper ledger pair."""

    label: str
    out_dir: Path
    base_id: str
    chal_id: str
    prepare: PrepareFn
    base_nav_name: str
    chal_nav_name: str
    compare_chal_col: str = "nav_chal"
    compare_rel_col: str = "rel_chal_vs_base"
    write_fills: bool = True
    base_fills_name: str | None = None
    chal_fills_name: str | None = None
    base_targets_name: str | None = "base_targets.csv"
    chal_targets_name: str | None = None
    capital: float = DEFAULT_CAPITAL
    lot_size: int = BOARD_LOT
    # None → simulate_core default (E22_v2s_tw). Pass E22_V2S explicitly when required.
    e22_version: str | None = None
    apply_e22: bool = True
    apply_stock_div: bool = True
    assert_exact_t1: bool = True
    soft_frozen_clip: Sequence[float] | None = None
    windows: Mapping[str, tuple] = field(default_factory=lambda: dict(WINDOWS_STANDARD))
    load_market_fn: Callable[[], pd.DataFrame] = load_market
    load_dividends_fn: Callable[[], pd.DataFrame] = load_dividends
    preflight: Callable[[], None] | None = None
    report_fn: ReportFn | None = None
    status: str = "OPERATING_OBSERVE"


@dataclass
class LedgerResult:
    spec: DualPaperLedgerSpec
    nav_base: pd.DataFrame
    nav_chal: pd.DataFrame
    fills_base: pd.DataFrame
    fills_chal: pd.DataFrame
    meta_base: dict
    meta_chal: dict
    prepared: PreparedBooks
    books: dict[str, dict]
    held: dict
    sealed: dict | None
    compare: pd.DataFrame
    out_dir: Path


@dataclass(frozen=True)
class MultiChallengerLedgerBook:
    chal_id: str
    nav_name: str
    fills_name: str | None = None
    targets_name: str | None = None
    compare_col: str | None = None


@dataclass
class PreparedMultiBooks:
    base_target: pd.DataFrame
    base_regime: pd.Series
    base_kwargs: dict[str, Any] = field(default_factory=dict)
    # chal_id -> (target, regime, kwargs, extras)
    challengers: dict[str, tuple[pd.DataFrame, pd.Series, dict[str, Any], dict[str, Any]]] = field(
        default_factory=dict
    )
    context: dict[str, Any] = field(default_factory=dict)


MultiPrepareFn = Callable[[pd.DataFrame, pd.DataFrame], PreparedMultiBooks]
MultiReportFn = Callable[["MultiLedgerResult"], None]


@dataclass(frozen=True)
class MultiPaperLedgerSpec:
    label: str
    out_dir: Path
    base_id: str
    base_nav_name: str
    prepare: MultiPrepareFn
    challengers: tuple[MultiChallengerLedgerBook, ...]
    write_fills: bool = True
    base_fills_name: str | None = None
    base_targets_name: str | None = "base_targets.csv"
    capital: float = DEFAULT_CAPITAL
    lot_size: int = BOARD_LOT
    e22_version: str | None = None
    apply_e22: bool = True
    apply_stock_div: bool = True
    assert_exact_t1: bool = True
    soft_frozen_clip: Sequence[float] | None = None
    windows: Mapping[str, tuple] = field(default_factory=lambda: dict(WINDOWS_STANDARD))
    load_market_fn: Callable[[], pd.DataFrame] = load_market
    load_dividends_fn: Callable[[], pd.DataFrame] = load_dividends
    preflight: Callable[[], None] | None = None
    report_fn: MultiReportFn | None = None
    status: str = "OPERATING_OBSERVE"


@dataclass
class MultiLedgerResult:
    spec: MultiPaperLedgerSpec
    nav_base: pd.DataFrame
    nav_by_chal: dict[str, pd.DataFrame]
    fills_base: pd.DataFrame
    fills_by_chal: dict[str, pd.DataFrame]
    meta_base: dict
    meta_by_chal: dict[str, dict]
    prepared: PreparedMultiBooks
    books: dict[str, dict]
    compare: pd.DataFrame
    out_dir: Path


def _sim_kwargs(spec: DualPaperLedgerSpec | MultiPaperLedgerSpec, extra: dict[str, Any]) -> dict[str, Any]:
    kw = {
        "apply_e22": spec.apply_e22,
        "apply_stock_div": spec.apply_stock_div,
        "capital": float(spec.capital),
        "lot_size": int(spec.lot_size),
    }
    if spec.e22_version is not None:
        kw["e22_version"] = spec.e22_version
    kw.update(extra)
    return kw


def _assert_soft_frozen(clip: Sequence[float] | None) -> None:
    if clip is None:
        return
    import e16_soft_frozen_base as soft

    expected = [float(clip[0]), float(clip[1])]
    if list(soft.SOFT_FROZEN_FIN_CLIP) != expected:
        raise SystemExit(
            f"Soft-Frozen clip drift: live={list(soft.SOFT_FROZEN_FIN_CLIP)} expected={expected}"
        )


def _window_book(nav: pd.DataFrame, meta: dict, windows: Mapping[str, tuple]) -> dict:
    win = {wname: window_stats(nav, ws, we) for wname, (ws, we) in windows.items()}
    return {
        "exact_t1_ok": bool(meta.get("exact_t1_ok")),
        "same_bar_fills": int(meta.get("same_bar_fills", -1)),
        "mean_e45_exposure": meta.get("mean_e45_exposure"),
        "e45_sleeve_names": meta.get("e45_sleeve_names"),
        "windows": win,
    }


def run_dual_paper_ledgers(spec: DualPaperLedgerSpec) -> LedgerResult:
    if spec.preflight is not None:
        spec.preflight()
    _assert_soft_frozen(spec.soft_frozen_clip)

    out = Path(spec.out_dir)
    (out / "outputs").mkdir(parents=True, exist_ok=True)
    (out / "reports").mkdir(parents=True, exist_ok=True)

    print("loading market + dividends ...", flush=True)
    market = spec.load_market_fn()
    dividends = spec.load_dividends_fn()
    prepared = spec.prepare(market, dividends)

    print(f"{spec.base_id} ...", flush=True)
    nav_b, fills_b, meta_b = simulate_core(
        market,
        prepared.base_target,
        prepared.base_regime,
        dividends,
        **_sim_kwargs(spec, prepared.base_kwargs),
    )
    print(f"{spec.chal_id} ...", flush=True)
    nav_c, fills_c, meta_c = simulate_core(
        market,
        prepared.chal_target,
        prepared.chal_regime,
        dividends,
        **_sim_kwargs(spec, prepared.chal_kwargs),
    )
    if spec.assert_exact_t1:
        if not meta_b.get("exact_t1_ok") or not meta_c.get("exact_t1_ok"):
            raise SystemExit(
                f"Exact T+1 fail: base={meta_b.get('exact_t1_ok')} chal={meta_c.get('exact_t1_ok')}"
            )

    nav_b.to_csv(out / "outputs" / spec.base_nav_name, index=False)
    nav_c.to_csv(out / "outputs" / spec.chal_nav_name, index=False)
    if spec.write_fills:
        bf = spec.base_fills_name or spec.base_nav_name.replace("_daily_nav.csv", "_fills.csv")
        cf = spec.chal_fills_name or spec.chal_nav_name.replace("_daily_nav.csv", "_fills.csv")
        fills_b.to_csv(out / "outputs" / bf, index=False)
        fills_c.to_csv(out / "outputs" / cf, index=False)
    if spec.base_targets_name:
        prepared.base_target.to_csv(out / "outputs" / spec.base_targets_name)
    if spec.chal_targets_name:
        prepared.chal_target.to_csv(out / "outputs" / spec.chal_targets_name)
    for name, obj in prepared.extras.items():
        obj.to_csv(out / "outputs" / name)

    compare = (
        nav_b[["date", "nav"]]
        .rename(columns={"nav": "nav_base"})
        .merge(
            nav_c[["date", "nav"]].rename(columns={"nav": spec.compare_chal_col}),
            on="date",
            how="inner",
        )
    )
    compare[spec.compare_rel_col] = compare[spec.compare_chal_col] / compare["nav_base"]
    compare.to_csv(out / "outputs" / "dual_paper_nav_compare.csv", index=False)

    books = {
        spec.base_id: _window_book(nav_b, meta_b, spec.windows),
        spec.chal_id: _window_book(nav_c, meta_c, spec.windows),
    }
    held = None
    sealed = None
    if "heldout_2019_plus" in books[spec.base_id]["windows"]:
        held = deltas_vs_base(
            books[spec.base_id]["windows"]["heldout_2019_plus"],
            books[spec.chal_id]["windows"]["heldout_2019_plus"],
        )
    if "sealed_2023_plus" in books[spec.base_id]["windows"]:
        sealed = deltas_vs_base(
            books[spec.base_id]["windows"]["sealed_2023_plus"],
            books[spec.chal_id]["windows"]["sealed_2023_plus"],
        )

    result = LedgerResult(
        spec=spec,
        nav_base=nav_b,
        nav_chal=nav_c,
        fills_base=fills_b,
        fills_chal=fills_c,
        meta_base=meta_b,
        meta_chal=meta_c,
        prepared=prepared,
        books=books,
        held=held or {},
        sealed=sealed,
        compare=compare,
        out_dir=out,
    )
    if spec.report_fn is not None:
        spec.report_fn(result)
    return result


def run_multi_paper_ledgers(spec: MultiPaperLedgerSpec) -> MultiLedgerResult:
    if spec.preflight is not None:
        spec.preflight()
    _assert_soft_frozen(spec.soft_frozen_clip)

    out = Path(spec.out_dir)
    (out / "outputs").mkdir(parents=True, exist_ok=True)
    (out / "reports").mkdir(parents=True, exist_ok=True)

    print("loading market + dividends ...", flush=True)
    market = spec.load_market_fn()
    dividends = spec.load_dividends_fn()
    prepared = spec.prepare(market, dividends)

    print(f"{spec.base_id} ...", flush=True)
    nav_b, fills_b, meta_b = simulate_core(
        market,
        prepared.base_target,
        prepared.base_regime,
        dividends,
        **_sim_kwargs(spec, prepared.base_kwargs),
    )
    if spec.assert_exact_t1 and not meta_b.get("exact_t1_ok"):
        raise SystemExit("Exact T+1 fail on base")

    nav_b.to_csv(out / "outputs" / spec.base_nav_name, index=False)
    if spec.write_fills:
        bf = spec.base_fills_name or spec.base_nav_name.replace("_daily_nav.csv", "_fills.csv")
        fills_b.to_csv(out / "outputs" / bf, index=False)
    if spec.base_targets_name:
        prepared.base_target.to_csv(out / "outputs" / spec.base_targets_name)

    nav_by: dict[str, pd.DataFrame] = {}
    fills_by: dict[str, pd.DataFrame] = {}
    meta_by: dict[str, dict] = {}
    books = {spec.base_id: _window_book(nav_b, meta_b, spec.windows)}

    compare = nav_b[["date", "nav"]].rename(columns={"nav": "nav_base"})
    for book in spec.challengers:
        if book.chal_id not in prepared.challengers:
            raise SystemExit(f"prepare() missing challenger {book.chal_id}")
        tgt, regime, kwargs, extras = prepared.challengers[book.chal_id]
        print(f"{book.chal_id} ...", flush=True)
        nav_c, fills_c, meta_c = simulate_core(
            market,
            tgt,
            regime,
            dividends,
            **_sim_kwargs(spec, kwargs),
        )
        if spec.assert_exact_t1 and not meta_c.get("exact_t1_ok"):
            raise SystemExit(f"Exact T+1 fail on {book.chal_id}")
        nav_c.to_csv(out / "outputs" / book.nav_name, index=False)
        if spec.write_fills:
            cf = book.fills_name or book.nav_name.replace("_daily_nav.csv", "_fills.csv")
            fills_c.to_csv(out / "outputs" / cf, index=False)
        if book.targets_name:
            tgt.to_csv(out / "outputs" / book.targets_name)
        for name, obj in extras.items():
            obj.to_csv(out / "outputs" / name)
        col = book.compare_col or f"nav_{book.chal_id.lower()}"
        compare = compare.merge(
            nav_c[["date", "nav"]].rename(columns={"nav": col}),
            on="date",
            how="inner",
        )
        nav_by[book.chal_id] = nav_c
        fills_by[book.chal_id] = fills_c
        meta_by[book.chal_id] = meta_c
        books[book.chal_id] = _window_book(nav_c, meta_c, spec.windows)

    compare.to_csv(out / "outputs" / "dual_paper_nav_compare.csv", index=False)
    result = MultiLedgerResult(
        spec=spec,
        nav_base=nav_b,
        nav_by_chal=nav_by,
        fills_base=fills_b,
        fills_by_chal=fills_by,
        meta_base=meta_b,
        meta_by_chal=meta_by,
        prepared=prepared,
        books=books,
        compare=compare,
        out_dir=out,
    )
    if spec.report_fn is not None:
        spec.report_fn(result)
    return result


def write_json_md_pair(
    *,
    out_dir: Path,
    report_stem: str,
    payload: dict,
    md_lines: list[str],
    mirror_dirs: Sequence[Path] = (),
    mirror_stem: str | None = None,
) -> None:
    body = json.dumps(payload, indent=2, default=str) + "\n"
    md = "\n".join(md_lines) + "\n"
    (out_dir / "reports").mkdir(parents=True, exist_ok=True)
    (out_dir / "reports" / f"{report_stem}.json").write_text(body, encoding="utf-8")
    (out_dir / f"{report_stem}.md").write_text(md, encoding="utf-8")
    stem = mirror_stem or report_stem
    for d in mirror_dirs:
        d.mkdir(parents=True, exist_ok=True)
        d.joinpath(f"{stem}.json").write_text(body, encoding="utf-8")
        d.joinpath(f"{stem}.md").write_text(md, encoding="utf-8")


def standard_metric_table(books: dict[str, dict]) -> list[str]:
    lines = [
        "| Book | Window | CAGR | MDD | n_days | Exact T+1 |",
        "|---|---|---:|---:|---:|---|",
    ]
    for book, payload in books.items():
        for wname, st in payload["windows"].items():
            cagr = st.get("cagr")
            mdd = st.get("max_drawdown")
            lines.append(
                f"| {book} | {wname} | "
                f"{(cagr if cagr is not None else float('nan')):.2%} | "
                f"{(mdd if mdd is not None else float('nan')):.2%} | "
                f"{st.get('n_days')} | {payload['exact_t1_ok']} |"
            )
    return lines


def cli_main(spec: DualPaperLedgerSpec) -> int:
    result = run_dual_paper_ledgers(spec)
    summary = {
        "label": spec.label,
        "status": spec.status,
        "live_wire": False,
        "base_id": spec.base_id,
        "challenger_id": spec.chal_id,
        "heldout": result.held,
        "sealed": result.sealed,
        "exact_t1": {
            "base": bool(result.meta_base.get("exact_t1_ok")),
            "chal": bool(result.meta_chal.get("exact_t1_ok")),
        },
    }
    print(json.dumps(summary, indent=2, default=str))
    print("EXIT:0")
    return 0


def cli_main_multi(spec: MultiPaperLedgerSpec) -> int:
    result = run_multi_paper_ledgers(spec)
    summary = {
        "label": spec.label,
        "status": spec.status,
        "live_wire": False,
        "base_id": spec.base_id,
        "challengers": [c.chal_id for c in spec.challengers],
        "exact_t1_base": bool(result.meta_base.get("exact_t1_ok")),
    }
    print(json.dumps(summary, indent=2, default=str))
    print("EXIT:0")
    return 0


# --- E45 exposure family helpers (shared prepare) ---------------------------------

def prepare_e45_exposure_pair(
    market: pd.DataFrame,
    dividends: pd.DataFrame,
    *,
    alpha: float,
    exposure_csv_name: str,
    exposure_series_name: str,
    e45_sleeve_names: tuple[str, ...] | None = None,
) -> PreparedBooks:
    """BASE early-stack vs CHAL with E45 exposure overlay (α∈(0,1] or full)."""
    from e45_paper_harness import (
        E45_PROFILE_DEFAULT,
        blend_exposure,
        e16_features,
        e45_full_exposure,
    )

    _p, _s, target, regime = e16_features(market)
    e45_full = e45_full_exposure(market, E45_PROFILE_DEFAULT)
    if float(alpha) >= 1.0:
        exposure = e45_full.astype(float)
    else:
        blended = blend_exposure(e45_full, float(alpha))
        assert blended is not None
        exposure = blended
    exposure = exposure.rename(exposure_series_name)
    chal_kwargs: dict[str, Any] = {"e45_exposure": exposure}
    if e45_sleeve_names is not None:
        chal_kwargs["e45_sleeve_names"] = e45_sleeve_names
    return PreparedBooks(
        base_target=target,
        base_regime=regime,
        chal_target=target,
        chal_regime=regime,
        base_kwargs={"e45_exposure": None},
        chal_kwargs=chal_kwargs,
        extras={exposure_csv_name: exposure},
        context={
            "blend_alpha": float(alpha),
            "e45_profile": E45_PROFILE_DEFAULT,
            "e45_sleeve_names": list(e45_sleeve_names) if e45_sleeve_names else None,
        },
    )


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def live_kd_sim_kwargs(
    *,
    scores,
    buy_ok,
    sell_scores=None,
    e45_exposure=None,
) -> dict[str, Any]:
    """Common simulate_core kwargs for Soft-Frozen + KD_OPT + TEL_EQUAL paper books."""
    from within_sleeve_alloc import FIN_PRE_EXDIV_KD, TEL_EQUAL

    kw: dict[str, Any] = {
        "financial_alloc": FIN_PRE_EXDIV_KD,
        "telecom_alloc": TEL_EQUAL,
        "fin_name_scores": scores,
        "fin_buy_ok": buy_ok,
        "fin_sell_scores": sell_scores,
    }
    if e45_exposure is not None:
        kw["e45_exposure"] = e45_exposure
    return kw


def preflight_live_kd(live_kd: dict, *, refuse_soft_assist_leak: bool = False) -> Callable[[], None]:
    def _run() -> None:
        from live_kd_guard import assert_live_kd_aligned

        assert_live_kd_aligned(live_kd)
        if refuse_soft_assist_leak:
            import e21_forward_pipeline as e21

            if "soft_assist" in Path(e21.__file__).read_text(encoding="utf-8"):
                raise SystemExit(
                    "Refuse: e21_forward_pipeline imports/mentions soft_assist (live wire leak)"
                )

    return _run
