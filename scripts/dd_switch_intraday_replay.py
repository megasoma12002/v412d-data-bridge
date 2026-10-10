#!/usr/bin/env python3
"""Fixed DD rule on timestamped parent snapshots and quote-depth paper fills.

Research only. Quote availability is evidence for a fill *model*, not a broker
acknowledgement. No daily-return fractions or full-day returns enter decisions.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import pandas as pd
from live_ledger import SLIP, fees_tax_for
from dd_switch_capital_policy import POLICIES, CapitalController

ROOT = Path(__file__).resolve().parents[1]
TZ = 'Asia/Taipei'
CLOCKS = ('10:00', '12:00', '13:20')

def timestamp(value):
    t = pd.Timestamp(value)
    if t.tzinfo is None:
        raise ValueError('Timestamps must include timezone offsets')
    return t.tz_convert(TZ)

def read_bundle(path):
    meta = json.loads((path/'manifest.json').read_text())
    if meta.get('evidence_kind') != 'timestamped_market_observations':
        raise ValueError('Daily proxies / synthetic intraday data are not research evidence')
    if meta.get('parent_scope') != 'full_account':
        raise ValueError('Full parent allocations, including private sleeves, are required')
    frames = {}
    for name in ('sessions', 'daily_nav', 'snapshots', 'targets', 'quotes', 'events'):
        file = path/(name+'.csv')
        if hashlib.sha256(file.read_bytes()).hexdigest() != meta['sha256'][file.name]:
            raise ValueError('Input checksum mismatch: '+file.name)
        frames[name] = pd.read_csv(file, dtype={'code': str, 'snapshot_id': str})
    for name, cols in {'daily_nav':['available_at'], 'snapshots':['observed_at','available_at'],
                       'targets':['available_at'], 'quotes':['timestamp','available_at'],
                       'events':['effective_at']}.items():
        for col in cols:
            frames[name][col] = frames[name][col].map(timestamp)
    s, q = frames['snapshots'], frames['quotes']
    if (s.available_at < s.observed_at).any() or (q.available_at < q.timestamp).any():
        raise ValueError('Availability precedes observation')
    if q.duplicated(['timestamp','code']).any() or s.snapshot_id.duplicated().any():
        raise ValueError('Duplicate observations')
    if ((q.ask < q.bid) | (q.bid <= 0) | (q.bid_size < 0) | (q.ask_size < 0)).any():
        raise ValueError('Invalid quotes')
    for name, cols in {'quotes':['bid','ask','bid_size','ask_size'],
                       'snapshots':['l4_nav','trail_nav'], 'targets':['weight'],
                       'daily_nav':['l4_nav','trail_nav']}.items():
        if not frames[name][cols].apply(lambda col: col.map(math.isfinite)).all().all():
            raise ValueError('Missing numeric inputs: '+name)
    if (s[['l4_nav','trail_nav']] <= 0).any().any():
        raise ValueError('Invalid snapshot NAV')
    if not frames['events'].kind.isin(['split']).all():
        raise ValueError('Unsupported corporate actions; dividend entitlement/payment ledger required')
    session_dates = set(frames['sessions'].date)
    for name, col in (('snapshots','observed_at'),('quotes','timestamp'),('events','effective_at')):
        if not set(frames[name][col].map(lambda t: t.strftime('%F'))) <= session_dates:
            raise ValueError('Observation / event outside declared sessions: '+name)
    frames['metadata'] = meta
    return frames

def decisions(frames, clock, parent='DD_SWITCH', next_session=False):
    """Use only prior-session EOD peaks and contemporaneously observed NAV."""
    sessions = frames['sessions'].date.astype(str).tolist()
    if sessions != sorted(set(sessions)):
        raise ValueError('Sessions must be unique and sorted')
    daily = frames['daily_nav']
    snapshots = frames['snapshots']
    targets = frames['targets']
    if daily.date.duplicated().any() or (daily[['l4_nav','trail_nav']] <= 0).any().any():
        raise ValueError('Invalid daily parent NAV')
    active_start = snapshots.observed_at.dt.strftime('%F').min()
    rows = []
    for i, day in enumerate(sessions):
        cutoff = timestamp(day+'T'+clock+':00+08:00')
        historic = daily[(daily.date < day) & (daily.available_at <= cutoff)]
        # sessions.csv includes warmup history. Neither missing history nor
        # missing observations can silently shorten the comparison calendar.
        if i and set(historic.date) != set(sessions[:i]):
            raise ValueError('Missing / unavailable prior daily NAV: '+day)
        snap = snapshots[(snapshots.observed_at.dt.strftime('%F') == day) &
                         (snapshots.available_at <= cutoff)]
        if snap.empty:
            if day >= active_start:
                raise ValueError('Missing contemporaneous parent snapshot: '+day+' '+clock)
            continue  # explicitly preceding warmup history
        snap = snap.sort_values(['observed_at','available_at']).iloc[-1]
        max_age = 1800 if next_session else 60
        if (cutoff-snap.observed_at).total_seconds() > max_age:
            raise ValueError('Stale intraday parent snapshot: '+day)
        l4_peak = max(float(snap.l4_nav), float(historic.l4_nav.max()) if len(historic) else float(snap.l4_nav))
        tr_peak = max(float(snap.trail_nav), float(historic.trail_nav.max()) if len(historic) else float(snap.trail_nav))
        l4_dd, tr_dd = float(snap.l4_nav)/l4_peak-1, float(snap.trail_nav)/tr_peak-1
        choice = ('TRAIL42' if tr_dd >= l4_dd else 'L4') if parent == 'DD_SWITCH' else parent
        alloc = targets[(targets.snapshot_id == snap.snapshot_id) & (targets.parent == choice)]
        if alloc.empty or (alloc.available_at > cutoff).any():
            raise ValueError('Missing / future parent allocation: '+day)
        if alloc.code.duplicated().any() or (alloc.weight < 0).any() or alloc.weight.sum() > 1+1e-9:
            raise ValueError('Invalid parent allocation')
        execution_day = sessions[i+1] if next_session and i+1 < len(sessions) else day
        if next_session and i+1 == len(sessions):
            continue  # no future session in this bundle
        ready = timestamp(execution_day+'T09:00:00+08:00') if next_session else cutoff
        rows.append(dict(signal_at=cutoff, ready_at=ready, execution_day=execution_day,
                         snapshot_id=snap.snapshot_id, parent=choice, l4_dd=l4_dd,
                         trail_dd=tr_dd, weights={c:float(w) for c,w in zip(alloc.code,alloc.weight) if w>0}))
    return rows

def replay(frames, plans, initial_cash, latency_ms=1000, participation=0.1, capital_policy=None):
    """One cash/share account; sells first, lot rounding, shared live costs.

    A displayed-depth participation limit is a configurable model assumption.
    Pending targets replace older targets and expire at session end. No implicit
    capital refill: target weight is multiplied by this account's current NAV.
    """
    if initial_cash <= 0 or latency_ms < 0 or not 0 < participation <= 1:
        raise ValueError('Invalid capital / execution settings')
    cash = float(initial_cash)
    pos, marks, fills, nav, events_log = {}, {}, [], [], []
    mark_times = {}
    controller = CapitalController(capital_policy) if capital_policy else None
    pending = None
    lag = pd.Timedelta(milliseconds=latency_ms)
    events = []
    for plan in plans:
        events.append((plan['ready_at'], 1, 'decision', plan))
    for row in frames['events'].to_dict('records'):
        events.append((row['effective_at'], 0, 'action', row))
    for at, group in frames['quotes'].groupby('available_at', sort=True):
        events.append((at, 2, 'quotes', group))
    current_day = None
    seen_today = set()
    def mark_day():
        if current_day is None:
            return
        missing = {c for c, qty in pos.items() if qty and c not in seen_today}
        if missing:
            raise ValueError('Missing daily held-asset marks: '+str(sorted(missing)))
        nav.append(dict(date=current_day, cash=cash, holdings=sum(pos.get(c,0)*p for c,p in marks.items()),
                        nav=cash+sum(pos.get(c,0)*p for c,p in marks.items())))
    for at, _, kind, obj in sorted(events, key=lambda x:(x[0],x[1])):
        day = at.strftime('%F')
        if day != current_day:
            mark_day()
            current_day, seen_today = day, set()
            pending = None
        if kind == 'action':
            if obj['kind'] != 'split':
                raise ValueError('Unsupported corporate action; explicit entitlement/payment accounting required')
            factor = float(obj['factor'])
            if factor <= 0:
                raise ValueError('Invalid split factor')
            code = obj['code']
            pos[code] = pos.get(code,0)*factor
            if code in marks:
                marks[code] /= factor
            if pending and '_desired' in pending:
                pending['_desired'][code] = pending['_desired'].get(code,0)*factor
            events_log.append(dict(at=str(at), kind='split', code=code, factor=factor))
        elif kind == 'decision':
            pending = dict(obj)
            risk = {}
            if controller:
                # Only completed prior-session account marks enter this layer.
                # A same-session signal never uses today's eventual closing NAV.
                history = [initial_cash]+[r['nav'] for r in nav]
                observed_nav = history[-1]
                momentum = observed_nav/history[max(0,len(history)-21)]-1
                pending['weights'],risk = controller.allocate(obj['weights'],observed_nav,momentum)
                pending['_cash_floor_ratio'] = risk['reserve_floor']
            events_log.append(dict(at=str(at), kind='replace_target', snapshot_id=obj['snapshot_id'],
                                   targets=json.dumps(pending['weights']),**risk))
        else:
            valid = obj[(obj.timestamp <= at) & ((at-obj.timestamp).dt.total_seconds() <= 60)]
            valid = valid.sort_values('timestamp').drop_duplicates('code',keep='last')
            valid = valid[[r.timestamp.strftime('%F') == day and
                           (r.code not in mark_times or r.timestamp > mark_times[r.code])
                           for r in valid.itertuples()]] if len(valid) else valid
            for r in valid.itertuples():
                marks[r.code] = (float(r.bid)+float(r.ask))/2
                mark_times[r.code] = r.timestamp
                seen_today.add(r.code)
            if not pending or at <= pending['ready_at']+lag or at <= pending['signal_at']+lag:
                continue
            weights = pending['weights']
            if any(c not in seen_today for c in set(weights) | {c for c,n in pos.items() if n}):
                continue
            account_nav = cash+sum(pos.get(c,0)*p for c,p in marks.items())
            if '_desired' not in pending:
                pending['_desired'] = {c:int(account_nav*w/marks[c]//1000)*1000 for c,w in weights.items()}
                pending['_cash_floor'] = account_nav*pending.get('_cash_floor_ratio',0)
            desired = pending['_desired']
            # Freeze this decision's share target until a new signal replaces it.
            candidates = []
            for r in valid.itertuples():
                if r.timestamp <= max(pending['signal_at'],pending['ready_at'])+lag:
                    continue  # a delayed pre-signal quote cannot prove a fill
                delta = desired.get(r.code,0)-pos.get(r.code,0)
                if delta:
                    candidates.append((delta > 0, r.code, delta, r))
            for buy, code, delta, r in sorted(candidates, key=lambda x:(x[0],x[1])):
                side = 'BUY' if buy else 'SELL'
                depth = float(r.ask_size if buy else r.bid_size)
                qty = min(int(abs(delta)//1000)*1000, int(depth*participation//1000)*1000)
                price = float(r.ask if buy else r.bid)*(1+SLIP if buy else 1-SLIP)
                if not buy:
                    qty = min(qty, int(pos.get(code,0)//1000)*1000)
                while qty and buy and qty*price+fees_tax_for(side=side,code=code,gross=qty*price)>cash-pending.get('_cash_floor',0):
                    qty -= 1000
                if not qty:
                    continue
                gross = qty*price
                fee = fees_tax_for(side=side, code=code, gross=gross)
                cash += -gross-fee if buy else gross-fee
                pos[code] = pos.get(code,0)+(qty if buy else -qty)
                fills.append(dict(signal_at=str(pending['signal_at']),fill_at=str(at),quote_at=str(r.timestamp),
                                  snapshot_id=pending['snapshot_id'],parent=pending['parent'],code=code,
                                  side=side,quantity=qty,fill_price=price,gross=gross,fees_tax=fee,cash_after=cash))
                if cash < -1e-6 or pos[code] < 0:
                    raise RuntimeError('Cash / position constraint violated')
    mark_day()
    return dict(fills=fills, nav=nav, events=events_log, final_positions=pos, final_cash=cash)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundle',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--initial-cash',type=float,required=True)
    p.add_argument('--latency-ms',type=int,default=1000)
    p.add_argument('--participation',type=float,default=0.1)
    p.add_argument('--capital-policy',choices=[p.name for p in POLICIES],default='BASELINE')
    a=p.parse_args()
    frames=read_bundle(a.bundle)
    summary=[]
    completed=[]
    arms=[(parent,clock,False) for clock in CLOCKS for parent in ('L4','TRAIL42','DD_SWITCH')]
    arms += [('DD_SWITCH','14:00',True)]
    for parent,clock,t1 in arms:
        plans=decisions(frames,clock,parent,t1)
        if not plans:
            raise ValueError('No contemporaneous decisions for arm '+parent+' '+clock)
        policy=next(p for p in POLICIES if p.name==a.capital_policy)
        result=replay(frames,plans,a.initial_cash,a.latency_ms,a.participation,policy)
        name=parent+'_'+('T1' if t1 else clock.replace(':',''))
        completed.append((name,plans,result))
        series=pd.Series([a.initial_cash]+[r['nav'] for r in result['nav']])
        summary.append(dict(arm=name,return_pct=(series.iloc[-1]/a.initial_cash-1)*100,
                            observed_mdd_pct=float((series/series.cummax()-1).min()*100),
                            fills=len(result['fills']),fees_tax=sum(r['fees_tax'] for r in result['fills'])))
    a.out.mkdir(parents=True,exist_ok=False)
    for name,plans,result in completed:
        for key in ('fills','nav','events'):
            pd.DataFrame(result[key]).to_csv(a.out/(name+'_'+key+'.csv'),index=False)
        pd.DataFrame([{**r,'weights':json.dumps(r['weights'])} for r in plans]).to_csv(a.out/(name+'_decisions.csv'),index=False)
    (a.out/'summary.json').write_text(json.dumps(dict(status='QUOTE_FILL_MODEL_ONLY',arms=summary,
        input_manifest=frames['metadata'],
        capital_policy=a.capital_policy,
        initial_cash=a.initial_cash,latency_ms=a.latency_ms,participation=a.participation,
        limitations=['No broker fills; depth/slippage/latency are model assumptions',
                     'MDD uses available quote marks, not full market path',
                     'No tuning; intraday DD uses prior EOD peaks plus observed snapshot NAV',
                     'Fresh cash bootstrap: not a continuation of existing live positions']),indent=2))
    print(json.dumps(summary,indent=2))

if __name__=='__main__':
    main()
