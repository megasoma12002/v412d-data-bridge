#!/usr/bin/env python3
"""Research-only announcement snapshots; never certify missing historical vintages."""
from datetime import time
import pandas as pd
from within_sleeve_alloc import build_kd_season_tilt_scores, build_pre_exdiv_window_buy_ok


def aware(value):
    stamp = pd.Timestamp(value)
    if stamp.tzinfo is None:
        raise ValueError('Explicit publication/cutoff timezone required')
    return stamp


def schedule_snapshot(versions, cutoff, codes):
    cutoff = aware(cutoff)
    known = []
    excluded = 0
    for row in versions:
        if row['code'] not in codes:
            continue
        if not row.get('reported_at'):
            excluded += 1
            continue
        stamp = aware(row['reported_at'])
        if stamp <= cutoff:
            known.append((stamp, row))
    events = {}
    clocks = {}
    for stamp, row in sorted(known, key=lambda x: (x[0], x[1]['event_id'])):
        leg = row.get('leg', 'cash')
        if leg not in ('cash', 'stock'):
            raise ValueError('Unknown instrument leg')
        key = row['event_id']  # Stable identity supplied by source, never infer revisions by year.
        identity = (row['code'], leg)
        if key in events and events[key]['identity'] != identity:
            raise ValueError('Event identity changed across versions')
        if 'ex_date' not in row:
            continue
        ex = row['ex_date']
        if ex:
            pd.Timestamp(ex)  # Reject malformed dates; an explicit blank withdraws the schedule.
        tie = (key, stamp)
        if tie in clocks and clocks[tie] != ex:
            raise ValueError('Conflicting schedules at the same publication clock')
        clocks[tie] = ex
        events[key] = dict(identity=identity, ex_date=ex, reported_at=row['reported_at'])
    rows = [dict(code=v['identity'][0], cash_ex_date=v['ex_date'] if v['identity'][1] == 'cash' else '',
                 stock_ex_date=v['ex_date'] if v['identity'][1] == 'stock' else '') for v in events.values() if v['ex_date']]
    return pd.DataFrame(rows, columns=['code', 'cash_ex_date', 'stock_ex_date']), excluded


def features_at(market, versions, calendar, codes, cutoff, parameters):
    """One close decision, using past quotes and known schedules only.

    Future calendar labels supply session distances, never future prices. A
    caller must separately certify that calendar and announcement versions were
    historically available. This adapter is not connected to frozen production.
    """
    stamp = aware(cutoff).tz_convert('Asia/Taipei')
    if stamp.time() < time(13, 30):
        raise ValueError('Close-based features require a cutoff at/after market close')
    day = stamp.tz_localize(None).normalize()
    calendar = pd.DatetimeIndex(pd.to_datetime(calendar)).sort_values().unique()
    if day not in calendar:
        raise ValueError('Cutoff is not a calendar session')
    m = market.copy()
    m['date'] = pd.to_datetime(m['date'])
    m['code'] = m['code'].astype(str)
    m = m[(m.date <= day) & m.code.isin(codes)]
    if m.duplicated(['date', 'code']).any():
        raise ValueError('Duplicate quote keys')
    if not set(m.date).issubset(set(calendar)):
        raise ValueError('Quote date missing from supplied calendar')
    for code in codes:
        current = m[(m.code == code) & (m.date == day)]
        if len(current) != 1 or current[['high', 'low', 'close']].isna().any().any():
            raise ValueError('Missing current close quote: ' + code)
    schedules, excluded = schedule_snapshot(versions, stamp, codes)
    # This request returns only today's feature. Allocations before this year's
    # season cannot define that decision; retain them in the source inventory.
    lower_bound = max(calendar.min(), pd.Timestamp(day.year, 1, 1))
    outside = schedules.apply(lambda row: all(not row[c] or pd.Timestamp(row[c]) < lower_bound
                                              for c in ('cash_ex_date', 'stock_ex_date')), axis=1)
    outside_count = int(outside.sum())
    schedules = schedules.loc[~outside]
    for column in ('cash_ex_date', 'stock_ex_date'):
        for ex in schedules[column]:
            if ex and pd.Timestamp(ex) not in calendar:
                raise ValueError('Known ex-date requires an exact supplied session: ' + ex)
    # Existing KD code locates a known future ex-date in its date index. Supply
    # calendar-only placeholders so a market prefix does not silently erase it.
    padding = [dict(date=d, code=c, high=float('nan'), low=float('nan'), close=float('nan'))
               for d in calendar[calendar > day] for c in codes]
    padded = pd.concat([m, pd.DataFrame(padding)], ignore_index=True)
    kd = build_kd_season_tilt_scores(padded, schedules, codes, **parameters)
    ok = build_pre_exdiv_window_buy_ok(calendar, schedules, codes,
                                     pre_days=parameters['pre_days'], also_stock_ex=True)
    return dict(date=day.date().isoformat(), cutoff=stamp.isoformat(),
                kd={c: float(kd.loc[day, c]) for c in codes},
                buy_ok={c: bool(ok.loc[day, c]) for c in codes},
                known_schedules=len(schedules), missing_clocks_excluded=excluded,
                expired_schedules_excluded=outside_count,
                publication_vintage_certified=False, backtest_ready=False)
