#!/usr/bin/env python3
"""DD_SWITCH R1: refreshed parent books and share/cash T+1 replay.

No tuning, no live-history rewrite. A versioned runtime is published only after
all input and replay checks pass. Original return-blend research stays intact.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import shutil
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

import fin_sat_path3_daily_share_ssot_stagea as parent
import cool_t50_lev_short_assist_stagea as short
import e22_dividend_accounting as e22
from dd_switch_runtime import DEFAULT_DIR, r1_research_destination
from e22_books_apply import apply_books_for_date
from e45_paper_harness import load_market, load_dividends
from e50_early_stack_combined_nav import FIN, TEL, e16_features, simulate_core
from fin_buy_quality_helpers import and_buy_ok, or_buy_ok, catalog_gate, not_gate, below_ma_ok, raw_close_panel
from live_fill_core import _paper_fill_rows
from live_ledger import make_order_id
from live_path3_t0_switch_emitter import BOOK_COMP, BOOK_SAT, build_sat_lead_signal
from path3_comp_sat_daily_share_ssot import shares_panel_from_long, plan_delta_ledger_scaled
from sleeve_gap_trade import sleeve_trade_from_gap
from tw_share_lots import board_lots
from twse_session_sources import cached_load_calendar_window, DEFAULT_CALENDAR_DIR
from within_sleeve_alloc import build_kd_season_tilt_scores, build_pre_exdiv_window_buy_ok, FIN_PRE_EXDIV_KD, TEL_EQUAL
from ta_indicator_catalog import build_low_high_catalog

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/dd-switch-t1-r1"
SHARE_EVENTS = {"2025-06-18": {"0050": 4}, "2026-03-31": {"00631L": 22}}
CLOSED = {d: {"00631L"} for d in ["2026-03-25", "2026-03-26", "2026-03-27", "2026-03-30"]}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def refresh_off(asof, out, *, base_path=None, calendar_path=None, append_after=None):
    """Append official raw TWSE bars; never fill missing post-list opens."""
    path = Path(base_path) if base_path else ROOT / "data/def_proxies/00631L_ohlcv.csv"
    raw = pd.read_csv(path, dtype={"code": str}, parse_dates=["date"])
    last = raw.date.max()
    calendar = pd.read_csv(calendar_path or ROOT / "forward/e21/live_market.csv", usecols=["date"], parse_dates=["date"]).date.drop_duplicates()
    missing = calendar[(calendar >= raw.date.min()) & (calendar <= asof) & ~calendar.isin(raw.date)]
    missing = missing[~missing.dt.strftime("%F").isin(CLOSED)]
    if append_after is not None:
        missing = missing[missing > pd.Timestamp(append_after)]
    months = sorted(set(missing.dt.to_period("M")))
    rows = []
    for period in months:
        month = period.to_timestamp()
        snapshot = out / ("twse_00631L_" + month.strftime("%Y%m") + ".json")
        # Reuse an immutable response only when it covers every requested day.
        payload = json.loads(snapshot.read_text()) if snapshot.exists() else {}
        def parsed_days(value):
            return {pd.Timestamp(int(r[0].split("/")[0]) + 1911, int(r[0].split("/")[1]), int(r[0].split("/")[2])) for r in value.get("data", [])}
        needed = set(missing[missing.dt.to_period("M") == period])
        if not needed.issubset(parsed_days(payload)):
            query = urllib.parse.urlencode({"response": "json", "date": month.strftime("%Y%m01"), "stockNo": "00631L"})
            url = "https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY?" + query
            with urllib.request.urlopen(url, timeout=45) as response:
                payload = json.load(response)
            if payload.get("stat") != "OK":
                raise RuntimeError(f"TWSE price response: {payload.get('stat')}")
            snapshot.write_text(json.dumps(payload, ensure_ascii=False))
        if not needed.issubset(parsed_days(payload)):
            raise RuntimeError(f"Official TWSE bars missing {sorted(needed - parsed_days(payload))}")
        for row in payload["data"]:
            y, m, d = map(int, row[0].split("/"))
            day = pd.Timestamp(y + 1911, m, d)
            if day not in needed:
                continue
            # Filling an old adjusted series across a corporate action would
            # require its adjustment ledger; fail instead of inventing a factor.
            neighbors = raw.loc[(raw.date - day).abs().sort_values().index[:2]]
            if not np.allclose(neighbors.adj_close / neighbors.close, 1):
                raise RuntimeError(f"00631L historical adjustment required at {day}")
            def number(index):
                return float(str(row[index]).replace(",", ""))
            bar = dict(date=day, code="00631L", open=number(3), high=number(4), low=number(5), close=number(6), adj_close=number(6), volume=number(1))
            if not 0 < bar["low"] <= min(bar["open"], bar["close"]) <= max(bar["open"], bar["close"]) <= bar["high"]:
                raise RuntimeError(f"Invalid official OHLC {day}")
            rows.append(bar)
    raw = pd.concat([raw, pd.DataFrame(rows)], ignore_index=True).sort_values("date")
    raw = raw[raw.date <= asof].drop_duplicates("date", keep="last")
    raw.to_csv(out / "00631L_ohlcv.csv", index=False)
    return raw


def parents(m, div, off, out):
    """Reuse locked COMP/SAT construction; capture positions and fills once."""
    parent.sat.DEF_CODE = "00631L"
    off = off.copy()
    eq_dates = pd.DatetimeIndex(sorted(m.date.unique()))
    listed = off.date.min()
    missing = eq_dates[(eq_dates >= listed) & ~eq_dates.isin(off.date)]
    missing = missing[~missing.strftime("%F").isin(CLOSED)]
    if len(missing):
        raise RuntimeError(f"Missing 00631L raw bars (no stale-open fill): {missing.strftime('%F').tolist()[:10]}")
    market, listed = parent.sat.attach_inv(m, off)
    _p, sleeve, _t, regime = e16_features(m)
    cal = pd.DatetimeIndex(sorted(m.date.unique()))
    lows, highs = build_low_high_catalog(m, cal, list(FIN))
    raw = raw_close_panel(m, cal, list(FIN))
    kd = build_kd_season_tilt_scores(m, div, FIN, k_thresh=float(parent.LIVE_KD["k_thresh"]), season_start=parent.LIVE_KD["season_start"], season_end=parent.LIVE_KD["season_end"], pre_days=int(parent.LIVE_KD["pre_days"]), active_score=float(parent.LIVE_KD["active_score"]))
    buy = build_pre_exdiv_window_buy_ok(cal, div, FIN, pre_days=int(parent.LIVE_KD["pre_days"]), also_stock_ex=True)
    scores, sell = parent._buy_scores(kd, lows), parent._sell_base(highs)
    target = parent._target_live(parent._sleeve_score(m, sleeve, parent.LIVE_SLEEVE_ALPHA), regime)
    # Preserve the live offense cash-on-ex clock for COOL; parent accounting is v3.
    from live_dh_fuse_cutover import build_fuse_offense_sim
    offense, _, _ = build_fuse_offense_sim(m, div)
    cool = parent._cool_from_offense(m, offense)
    feat = parent.stagea._risk_features(m, parent.stagea._nav_series(offense))
    ret1, ret3 = short._0050_rets(m, target.index)
    off_px = short._off_close(off, target.index)
    comp_buy = and_buy_ok(buy, or_buy_ok(catalog_gate(lows["BELOW_MA120"]), catalog_gate(lows["K9_LT30"])))
    comp_sell = not_gate(below_ma_ok(raw, 150))
    books = {}
    for name, alpha, buy_ok, sell_ok in [("BASE", .10, buy, None), (BOOK_COMP, parent.CHAL_ALPHA, comp_buy, comp_sell), (BOOK_SAT, parent.CHAL_ALPHA, buy, None)]:
        print("parent", name, flush=True)
        schedule, _ = short.build_schedule(target, cool, alpha=float(alpha), hold_h=parent.HOLD_H, listed_from=listed, track="CONFIRM", confirm=parent.CONFIRM, ret1=ret1, ret3=ret3, proxy=feat["proxy_mdd63"].reindex(target.index).fillna(0), off_px=off_px)
        sink = []
        nav, fills, meta = simulate_core(market, target, regime, div, share_events=SHARE_EVENTS, closed_sessions=CLOSED, apply_e22=True, apply_stock_div=True, capital=parent.DEFAULT_CAPITAL, lot_size=parent.BOARD_LOT, financial_alloc=FIN_PRE_EXDIV_KD, telecom_alloc=TEL_EQUAL, fin_name_scores=scores, fin_buy_ok=buy_ok, fin_sell_scores=sell, fin_sell_ok=sell_ok, e22_version=e22.DEFAULT_BOOKS_VERSION, sleeve_weight_schedule=schedule, def_code="00631L", daily_pos_sink=sink)
        nav["date"] = pd.to_datetime(nav["date"])
        schedule.index = pd.to_datetime(schedule.index)
        shares = pd.DataFrame(sink)
        nav.to_csv(out / ("parent_nav_" + name + ".csv"), index=False)
        fills.to_csv(out / ("parent_fills_" + name + ".csv"), index=False)
        shares.to_csv(out / ("shares_" + name + ".csv"), index=False)
        books[name] = dict(nav=nav, shares=shares_panel_from_long(shares), schedule=schedule)
    signal = build_sat_lead_signal(comp=books[BOOK_COMP]["nav"][["date", "nav"]], sat=books[BOOK_SAT]["nav"][["date", "nav"]], theta=parent.load_or_build_signal.__globals__.get("P3_OBSERVE_THETA", .005))
    signal.to_csv(out / "signal.csv", index=False)
    return market, books, signal


@dataclass
class Book:
    pos: dict
    cash: float
    recv: dict = field(default_factory=dict)
    skip: set = field(default_factory=set)
    pending: list = field(default_factory=list)
    nav: list = field(default_factory=list)
    fills: list = field(default_factory=list)
    orders: list = field(default_factory=list)
    dividends: list = field(default_factory=list)
    positions: list = field(default_factory=list)


def mark(book, prices):
    missing = [c for c, q in book.pos.items() if q and c not in prices]
    if missing:
        raise RuntimeError(f"Missing marks {missing}")
    return book.cash + sum(q * prices[c] for c, q in book.pos.items() if q) + sum(book.recv.values())


def advance(book, day, opens, closes, events):
    for code, factor in SHARE_EVENTS.get(day.strftime("%F"), {}).items():
        book.pos[code] = book.pos.get(code, 0) * factor
        for order in book.pending:
            if order["code"] == code:
                order["quantity"] *= factor
                order["reference_close"] /= factor
    entitlement = dict(book.pos)
    due = pd.DataFrame([o for o in book.pending if o["code"] not in CLOSED.get(day.strftime("%F"), set())])
    if not due.empty:
        due = due.sort_values("side", ascending=False)  # SELL before BUY
        if any(pd.to_datetime(due.signal_date) >= day):
            raise RuntimeError("Replay signal must precede fill")
        book.pos, book.cash, fills = _paper_fill_rows(pending=due, latest=day, open_prices=opens, pos=book.pos, cash=book.cash, carve_authorized=False)
        book.fills.extend(fills)
        done = {f["fill_id"] for f in fills}
        book.pending = [o for o in book.pending if o["order_id"] not in done]
    sessions, settlements = cached_load_calendar_window(day.year, calendar_dir=DEFAULT_CALENDAR_DIR, span=1, soft_miss=True)
    book.pos, book.cash, book.recv, res = apply_books_for_date(day.strftime("%F"), book.pos, book.cash, events, version=e22.DEFAULT_BOOKS_VERSION, skip_keys=book.skip, mark_prices=closes, receivables=book.recv, session_dates=sessions, settlement_dates=settlements, entitlement_positions=entitlement)
    for detail in res.details:
        if "key" in detail:
            book.skip.add(str(detail["key"]))
        book.dividends.append({"date": day.strftime("%F"), **detail})
    nav = mark(book, closes)
    if nav <= 0 or book.cash < -1e-6 or any(q < -1e-6 for q in book.pos.values()):
        raise RuntimeError("Replay cash/shares invariant")
    row = dict(date=day.strftime("%F"), nav=nav, cash=book.cash, receivables=sum(book.recv.values()), financial=sum(book.pos.get(c, 0) * closes[c] for c in FIN), telecom=sum(book.pos.get(c, 0) * closes[c] for c in TEL))
    book.nav.append(row)
    for code, quantity in book.pos.items():
        book.positions.append(dict(date=row["date"], code=code, shares=quantity))
    return nav


def orders(book, day, prices, target, parent_shares, active):
    nav = mark(book, prices)
    # Exactly the current WITHIN policy: FIN/TEL ordinary orders suppressed.
    financial_codes = list(FIN) + [c for c in book.pos if c.startswith('28') and c not in FIN]
    pre = dict(Financial=sum(book.pos.get(c, 0) * prices[c] for c in financial_codes if c in prices) / nav, Telecom=sum(book.pos.get(c, 0) * prices[c] for c in TEL) / nav, **{"0050": book.pos.get("0050", 0) * prices["0050"] / nav})
    trade, _ = sleeve_trade_from_gap(pre, target)
    delta, _ = plan_delta_ledger_scaled(live_pos=book.pos, prices=prices, ledger_shares=parent_shares)
    if not active:
        delta = {c: -q for c, q in book.pos.items() if c in list(FIN) + list(TEL)}
    etf_qty = int(board_lots(abs(trade["0050"] * nav) / prices["0050"]))
    ordinary = {}
    if etf_qty:
        ordinary["0050"] = etf_qty if trade["0050"] > 0 else -min(etf_qty, int(board_lots(book.pos.get("0050", 0))))
    off_target = int(board_lots(float(target.get("OFF", 0)) * nav / prices["00631L"]))
    off_delta = off_target - int(board_lots(book.pos.get("00631L", 0)))
    if off_delta:
        ordinary["00631L"] = off_delta
    existing = {o["order_id"] for o in book.pending}
    for code, change in {**ordinary, **delta}.items():
        q = int(board_lots(abs(change)))
        if not q:
            continue
        side = "BUY" if change > 0 else "SELL"
        oid = make_order_id(signal_date=day.date(), code=code, side=side) + ("-P3T0" if code in FIN + TEL else "")
        row = dict(order_id=oid, signal_date=day.strftime("%F"), code=code, side=side, quantity=q, reference_close=prices[code], execution_clock="NEXT_SESSION_OPEN")
        if oid not in existing:
            book.pending.append(row)
            book.orders.append(row)


def stats(nav):
    d = pd.DataFrame(nav)
    v = d.nav.astype(float)
    days = (pd.Timestamp(d.date.iloc[-1]) - pd.Timestamp(d.date.iloc[0])).days
    return dict(start=d.date.iloc[0], end=d.date.iloc[-1], n=len(d), initial=float(v.iloc[0]), final=float(v.iloc[-1]), return_pct=float((v.iloc[-1] / v.iloc[0] - 1) * 100), cagr_252_pct=float(((v.iloc[-1] / v.iloc[0]) ** (252 / (len(v)-1)) - 1) * 100) if len(v)>1 else None, cagr_calendar_pct=float(((v.iloc[-1] / v.iloc[0]) ** (365.25 / days) - 1) * 100) if days>0 else None, mdd_pct=float((v / v.cummax() - 1).min() * 100))


def replay(market, books, signal, div, out, initial=None, start=None):
    """Parallel real-account L4/TRAIL/DD; decision at close, fills next open."""
    base = books["BASE"]["nav"].set_index("date")
    sig = signal.set_index("date")
    dates = base.index.intersection(sig.index)
    if initial is None:
        # Fixed bootstrap, not selected using performance: first 2013 session.
        seed_day = dates[dates >= pd.Timestamp("2013-01-01")][0]
        seed = books["BASE"]["shares"].loc[seed_day].to_dict()
        cash = float(base.loc[seed_day, "cash"])
        recv_balance = float(base.loc[seed_day].get("e22_receivable_balance", 0) or 0)
        if abs(recv_balance) > 1e-6:
            raise RuntimeError("Bootstrap requires keyed receivables")
        initial = dict(positions=seed, cash=cash, e22_receivables={}, e22_applied_keys=[])
        start = seed_day + pd.Timedelta(days=1)
    dates = dates[dates >= pd.Timestamp(start)]
    close = market.pivot(index="date", columns="code", values="close")
    opens = market.pivot(index="date", columns="code", values="open")
    accounts = {k: Book(dict(initial["positions"]), float(initial["cash"]), recv=dict(initial.get("e22_receivables", {})), skip=set(initial.get("e22_applied_keys", []))) for k in ["L4", "TRAIL", "DD_SWITCH"]}
    events = e22.dividend_events_from_frame(div)
    base_r = base.nav.reindex(dates).pct_change().fillna(0)
    premium = []
    controls = []
    for i, day in enumerate(dates):
        cl, op = close.loc[day].dropna().to_dict(), opens.loc[day].dropna().to_dict()
        if "00631L" not in cl:
            if day.strftime("%F") in CLOSED:
                prior = close.loc[close.index < day, "00631L"].dropna()
                cl["00631L"] = float(prior.iloc[-1])
            else:  # pre-list satellite is flat, weight zero
                cl["00631L"] = op["00631L"] = 1.0
        # All virtual books complete day t before a close-t decision is made.
        navs = {k: advance(b, day, op, cl, events) for k, b in accounts.items()}
        prev_l4 = accounts["L4"].nav[-2]["nav"] if i else navs["L4"]
        # Match the existing lag-1 rolling-sum premium rule, with real share books.
        trail_on = (sum(premium[-42:]) if len(premium) >= 14 else 0) >= -.01
        premium.append(navs["L4"] / prev_l4 - 1 - float(base_r.loc[day]))
        dd_l4 = navs["L4"] / max(r["nav"] for r in accounts["L4"].nav) - 1
        dd_tr = navs["TRAIL"] / max(r["nav"] for r in accounts["TRAIL"].nav) - 1
        want_trail = dd_tr >= dd_l4
        active = not want_trail or trail_on
        book_name = str(sig.loc[day, "book"])
        panel = books[book_name]["shares"]
        shares = panel.loc[day].to_dict()
        sched = books["BASE"]["schedule"].loc[day]
        target = {"Financial": float(sched["Financial"]), "Telecom": float(sched["Telecom"]), "0050": float(sched["0050"]), "OFF": float(sched.get("DEF", 0))}
        for key, on in [("L4", True), ("TRAIL", trail_on), ("DD_SWITCH", active)]:
            orders(accounts[key], day, cl, target, shares, on)
        controls.append(dict(date=day.strftime("%F"), book=book_name, want_trail=want_trail, trail42_on=trail_on, active=active, l4_dd=dd_l4, trail_dd=dd_tr, signal_available="AFTER_CLOSE", execution_clock="NEXT_SESSION_OPEN"))
    result = {}
    for name, b in accounts.items():
        pd.DataFrame(b.nav).to_csv(out / ("nav_" + name + ".csv"), index=False)
        for label in ["fills", "orders", "dividends", "positions"]:
            pd.DataFrame(getattr(b, label)).to_csv(out / (label + "_" + name + ".csv"), index=False)
        result[name] = stats(b.nav)
        result[name].update(n_fills=len(b.fills), fees_tax=sum(f["fees_tax"] for f in b.fills), pending_orders=len(b.pending), zero_fin_tel_days=sum(r["financial"]+r["telecom"] < 1e-6 for r in b.nav))
    pd.DataFrame(controls).to_csv(out / "controls.csv", index=False)
    return result


def publish(out, asof, destination):
    destination=r1_research_destination(destination)
    # Controller return windows must share the replay bootstrap date.
    base = pd.read_csv(out / "parent_nav_BASE.csv")
    first = pd.read_csv(out / "nav_L4.csv").date.min()
    base[base.date >= first].to_csv(out / "controller_base.csv", index=False)
    files = dict(off="00631L_ohlcv.csv", signal="signal.csv", base="controller_base.csv", l4="nav_L4.csv", trail="nav_TRAIL.csv", dd="nav_DD_SWITCH.csv", shares_COMP_H150_x_A20="shares_COMP_H150_x_A20.csv", shares_SAT_A20_RELAX="shares_SAT_A20_RELAX.csv")
    for key, name in files.items():
        frame = pd.read_csv(out / name)
        if frame.empty or str(frame.date.max())[:10] != asof.strftime("%F"):
            raise RuntimeError(f"Refusing stale publication: {key}")
        keys = ["date", "code"] if key.startswith("shares_") else ["date"]
        if frame.duplicated(keys).any():
            raise RuntimeError(f"Duplicate publication observations: {key}")
        if "nav" in frame and (not np.isfinite(frame.nav).all() or (frame.nav <= 0).any()):
            raise RuntimeError(f"Invalid NAV publication: {key}")
    hashes = {k: sha(out / v) for k, v in files.items()}
    ident = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()[:16]
    relative = "generations/" + ident
    generation = destination / relative
    generation.mkdir(parents=True, exist_ok=True)
    for name in files.values():
        shutil.copyfile(out / name, generation / name)
    meta = dict(version="DD_SWITCH_T1_R1", asof=asof.strftime("%F"), generation=relative, files=files, hashes=hashes, clock="CLOSE_T_TO_NEXT_SESSION_OPEN", original_research_preserved=True,controller_model_scope="R1_RESEARCH_NON_EQUIVALENT_TO_ORIGINAL")
    destination.mkdir(parents=True, exist_ok=True)
    tmp = destination / "current.json.tmp"
    tmp.write_text(json.dumps(meta, indent=2) + "\n")
    tmp.replace(destination / "current.json")
    return meta


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--asof")
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--refresh-prices", action="store_true")
    ap.add_argument("--publish", action="store_true")
    ap.add_argument("--runtime-dir", type=Path, default=DEFAULT_DIR)
    args = ap.parse_args()
    if args.publish:
        r1_research_destination(args.runtime_dir)
    out = args.out.resolve()
    if out == ROOT / "forward/e21" or (ROOT / "forward/e21") in out.parents:
        raise SystemExit("Never reconstruct into immutable live history")
    out.mkdir(parents=True, exist_ok=True)
    m, div = load_market(), load_dividends()
    asof = pd.Timestamp(args.asof).normalize() if args.asof else m.date.max()
    m = m[m.date <= asof]
    if m.date.max() != asof:
        raise RuntimeError("Requested market asof unavailable")
    off = refresh_off(asof, out) if args.refresh_prices else pd.read_csv(ROOT / "data/def_proxies/00631L_ohlcv.csv", parse_dates=["date"], dtype={"code": str})
    market, books, signal = parents(m, div, off, out)
    result = replay(market, books, signal, div, out)
    manifest = dict(version="DD_SWITCH_T1_R1", asof=asof.strftime("%F"), code_hashes={str(p.relative_to(ROOT)): sha(p) for p in sorted((ROOT / "scripts").glob("*.py"))}, share_events=SHARE_EVENTS, closed_sessions={k: sorted(v) for k, v in CLOSED.items()}, source_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(), market_hash=sha(ROOT / "forward/e21/live_market.csv"), dividends_hash=sha(ROOT / "data/dividend_events/e22_dividend_events.csv"), off_hash=sha(out / "00631L_ohlcv.csv") if (out / "00631L_ohlcv.csv").exists() else sha(ROOT / "data/def_proxies/00631L_ohlcv.csv"), parameters=dict(theta=.005, trail_window=42, trail_threshold=-.01, capital=parent.DEFAULT_CAPITAL, books=e22.DEFAULT_BOOKS_VERSION), initialization="fixed_first_2013_BASE_parent_bootstrap", results=result, decision="INCONCLUSIVE", promotion="RETAIN_BASELINE", limitations=["Historical counterfactual of current WITHIN policy; fixed 2013 parent bootstrap", "No new tuning or pure unseen holdout claim", "Parent adjusted data is current snapshot, not reconstructed vintage PIT", "T+1 open price model, not broker execution proof", "FIN/TEL cash reentry follows current ledger-scaled policy; no invented refill"])
    (out / "summary.json").write_text(json.dumps(manifest, indent=2) + "\n")
    if args.publish:
        publish(out, asof, args.runtime_dir.resolve())
    print(json.dumps(manifest, indent=2), flush=True)


if __name__ == "__main__":
    main()
