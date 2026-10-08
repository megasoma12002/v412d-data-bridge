#!/usr/bin/env python3
"""Reconcile complete recorded forward books; compare fixed cash policies.

Reference fills are immutable evidence. Counterfactuals replay the same recorded
order intents with next-session raw opens in independent cash/share/dividend
accounts. They do not regenerate missing strategy decisions or invent old live
history, and are not a historical simulation of today's entire configuration.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from dataclasses import dataclass,field
from pathlib import Path
import pandas as pd
from dd_switch_capital_policy import POLICIES,CapitalController
from e22_books_apply import apply_books_for_date
from e22_dividend_accounting import load_dividend_events
from e22_mops_payment_amendments import load_amendments
from live_ledger import SLIP,fees_tax_for,max_affordable_buy_qty
from twse_session_sources import cached_load_calendar_window

ROOT=Path(__file__).resolve().parents[1]

def target_quantity(nav,weight,close):
    # Tolerance is 1e-6 share, solely to preserve integer-lot identities after
    # converting shares -> weights -> shares through floating-point arithmetic.
    return int(math.floor(nav*weight/close/1000+1e-9))*1000

@dataclass
class Book:
    cash: float
    positions: dict=field(default_factory=dict)
    receivables: dict=field(default_factory=dict)
    applied: set=field(default_factory=set)
    dividends: list=field(default_factory=list)
    fills: list=field(default_factory=list)

    def trade(self,day,code,side,quantity,price,fee):
        gross=quantity*price
        self.cash += -gross-fee if side=='BUY' else gross-fee
        self.positions[code]=self.positions.get(code,0)+(quantity if side=='BUY' else -quantity)
        if self.cash < -1e-5 or self.positions[code] < -1e-6:
            raise ValueError('Negative cash / shares: '+day+' '+code)
        self.fills.append(dict(fill_date=day,code=code,side=side,quantity=quantity,
                               fill_price=price,gross=gross,fees_tax=fee,cash_after=self.cash))

    def apply_dividends(self,day,version,events,prices,entitlement):
        sessions,settlements=cached_load_calendar_window(int(day[:4]))
        self.positions,self.cash,self.receivables,result=apply_books_for_date(
            day,self.positions,self.cash,events,version=version,skip_keys=self.applied,
            mark_prices=prices,receivables=self.receivables,session_dates=sessions,
            settlement_dates=settlements,entitlement_positions=entitlement,
            mops_amendments=load_amendments())
        for row in result.details:
            self.applied.add(row['key'])
            self.dividends.append(dict(date=day,**row))

    def nav(self,prices):
        missing=[c for c,n in self.positions.items() if n and c not in prices]
        if missing:raise ValueError('Missing same-session raw marks: '+str(missing))
        return self.cash+sum(n*prices.get(c,0) for c,n in self.positions.items())+sum(self.receivables.values())

def load_prices():
    m=pd.read_csv(ROOT/'forward/e21/live_market.csv',dtype={'code':str})
    private=pd.read_csv(ROOT/'data/market/private_fin_adjusted.csv',dtype={'code':str})
    if private[['backward_adjustment_factor','raw_close']].isna().any().any():
        raise ValueError('Private raw-price conversion missing')
    private['open']=private.adjusted_open/private.backward_adjustment_factor
    private['close']=private.raw_close
    off_path=ROOT/'repro/dd-switch-t1-r1/00631L_ohlcv.csv'
    off=pd.read_csv(off_path if off_path.exists() else ROOT/'data/def_proxies/00631L_ohlcv.csv',dtype={'code':str})
    all_prices=pd.concat([m[['date','code','open','close']],private[['date','code','open','close']],off[['date','code','open','close']]])
    all_prices=all_prices.drop_duplicates(['date','code'],keep='first')
    return all_prices.set_index(['date','code']),sorted(m.date.unique())

def prices_on(panel,day,column):
    out=panel.loc[day,column].to_dict()
    if any(pd.isna(p) or p<=0 for p in out.values()):raise ValueError('Invalid raw prices: '+day)
    return out

def metrics(nav,initial):
    values=pd.Series([initial]+nav.nav.tolist())
    return dict(final_nav=float(values.iloc[-1]),profit=float(values.iloc[-1]-initial),
                return_pct=float((values.iloc[-1]/initial-1)*100),
                observed_mdd_pct=float((values/values.cummax()-1).min()*100),
                sessions=len(nav))

def reconstruct(source,panel,calendar,events):
    recorded=pd.read_csv(source/'nav.csv').set_index('date')
    fills=pd.read_csv(source/'fills.csv',dtype={'code':str})
    state=json.loads((source/'portfolio_state.json').read_text())
    start,end=recorded.index.min(),recorded.index.max()
    days=[d for d in calendar if start<=d<=end]
    expected=set()
    for year in range(int(start[:4]),int(end[:4])+1):
        sessions,_=cached_load_calendar_window(year)
        expected.update(str(d) for d in sessions if start<=str(d)<=end)
    if set(days)!=expected:
        raise ValueError('Raw market coverage differs from official session calendar')
    initial=float(recorded.iloc[0].cash)
    if abs(float(recorded.iloc[0].nav_e16_e18)-initial)>1e-6 or (fills.fill_date<start).any():
        raise ValueError('Non-flat bootstrap needs prior entitlement/position snapshot')
    if fills.fill_id.duplicated().any() or (~fills.side.isin(['BUY','SELL'])).any():
        raise ValueError('Invalid recorded fills')
    if not set(fills.fill_date)<=set(days):raise ValueError('Fill date absent from calendar')
    version_by_day=recorded.e22_version.reindex(days).ffill()
    b=Book(initial);rows=[];positions=[];residuals=[];snapshots={}
    for day in days:
        close=prices_on(panel,day,'close')
        entitlement=dict(b.positions)
        for f in fills[fills.fill_date==day].itertuples():
            if f.fill_date<f.signal_date:raise ValueError('Recorded fill before signal')
            expected=fees_tax_for(side=f.side,code=f.code,gross=f.quantity*f.fill_price)
            if abs(expected-f.fees_tax)>1e-5 or abs(f.quantity*f.fill_price-f.gross)>1e-5:
                raise ValueError('Recorded gross / fees mismatch')
            b.trade(day,f.code,f.side,float(f.quantity),float(f.fill_price),float(f.fees_tax))
        b.apply_dividends(day,version_by_day.loc[day],events,close,entitlement)
        value=b.nav(close)
        rows.append(dict(date=day,nav=value,cash=b.cash,receivables=sum(b.receivables.values()),
                         reconstructed_missing_nav=day not in recorded.index))
        for code,n in b.positions.items():positions.append(dict(date=day,code=code,quantity=n))
        snapshots[day]=dict(b.positions)
        if day in recorded.index:
            r=recorded.loc[day]
            residuals.append(dict(date=day,nav_residual=value-float(r.nav_e16_e18),
                                  cash_residual=b.cash-float(r.cash),
                                  receivable_residual=sum(b.receivables.values())-float(r.get('e22_receivable_balance',0) or 0)))
    final_position_residual=max([abs(n-b.positions.get(c,0)) for c,n in state['positions'].items()]+
                                [abs(n-state['positions'].get(c,0)) for c,n in b.positions.items()])
    audit=pd.DataFrame(residuals).fillna(0)
    if audit[['nav_residual','cash_residual','receivable_residual']].abs().max().max()>1e-4 or final_position_residual>1e-6:
        raise ValueError('Recorded book does not reconcile; inspect source / marks / dividends')
    nav=pd.DataFrame(rows)
    result=dict(**metrics(nav,initial),initial=initial,start=start,end=end,
                missing_nav_completed=[d for d in days if d not in recorded.index],
                max_nav_residual=float(audit.nav_residual.abs().max()),
                max_cash_residual=float(audit.cash_residual.abs().max()),
                final_position_residual=final_position_residual,
                fees_tax=sum(f['fees_tax'] for f in b.fills),dividend_records=len(b.dividends),
                cash_dividend_credit=sum(float(d.get('cash_credit',0)) for d in b.dividends))
    return nav,pd.DataFrame(positions),audit,b,snapshots,version_by_day,result

def target_intents(source,nav,snapshots,panel):
    orders=pd.read_csv(source/'orders.csv',dtype={'code':str})
    fills=pd.read_csv(source/'fills.csv',dtype={'code':str})
    intents={}
    for day in nav.date:
        # Filled-order knowledge is truncated to the close being reconstructed.
        done=set(fills.loc[fills.fill_date<=day,'fill_id'])
        pending=orders[(orders.signal_date<=day)&~orders.order_id.isin(done)]
        projected=dict(snapshots[day])
        for o in pending.itertuples():
            projected[o.code]=projected.get(o.code,0)+(o.quantity if o.side=='BUY' else -o.quantity)
        close=prices_on(panel,day,'close')
        value=float(nav.loc[nav.date==day,'nav'].iloc[0])
        weights={c:max(0,n)*close[c]/value for c,n in projected.items() if n>0}
        gross=sum(weights.values())
        if gross>1:weights={c:w/gross for c,w in weights.items()}
        # No signal was generated on source missing days: do not invent it.
        if (orders.signal_date==day).any():
            intents[day]=dict(weights=weights,projected_gross_weight=gross)
    return intents

def counterfactual(policy,days,intents,initial,panel,events,versions):
    b=Book(initial);controller=CapitalController(policy);pending=None;rows=[];decisions=[];positions=[]
    last_weights=None
    for day in days:
        close=prices_on(panel,day,'close');op=prices_on(panel,day,'open')
        entitlement=dict(b.positions)
        if pending:
            target,cash_floor,signal=pending
            candidates=[(desired-b.positions.get(c,0)>0,c,desired-b.positions.get(c,0)) for c,desired in target.items()]
            candidates += [(False,c,-n) for c,n in b.positions.items() if c not in target and n>0]
            for buy,code,delta in sorted(candidates):
                if not delta:continue
                side='BUY' if buy else 'SELL';price=op[code]*(1+SLIP if buy else 1-SLIP)
                quantity=int(abs(delta)//1000)*1000
                if buy:quantity=min(quantity,max_affordable_buy_qty(max(0,b.cash-cash_floor),price))
                else:quantity=min(quantity,int(b.positions.get(code,0)//1000)*1000)
                if quantity:
                    fee=fees_tax_for(side=side,code=code,gross=quantity*price)
                    b.trade(day,code,side,quantity,price,fee)
                    b.fills[-1]['signal_date']=signal
            pending=None  # expire remainder; replace only on actual source signal
        b.apply_dividends(day,versions.loc[day],events,close,entitlement)
        value=b.nav(close)
        rows.append(dict(date=day,nav=value,cash=b.cash,receivables=sum(b.receivables.values())))
        for c,n in b.positions.items():positions.append(dict(date=day,code=c,quantity=n))
        past=[initial]+[r['nav'] for r in rows[:-1]]
        momentum=value/past[max(0,len(past)-20)]-1
        old_scale=controller.scale
        d=controller.observe(value,momentum)  # update peak on every price session
        if day in intents:last_weights=intents[day]['weights']
        targets={}
        if last_weights is not None and (day in intents or abs(old_scale-d['scale'])>1e-10):
            weights={c:w*d['scale'] for c,w in last_weights.items()}
            targets={c:target_quantity(value,w,close[c]) for c,w in weights.items()}
            pending=(targets,value*d['reserve_floor'],day)
        decisions.append(dict(signal_date=day,source_new_intent=day in intents,
                              creates_order=pending is not None,targets=json.dumps(targets),**d))
    nav=pd.DataFrame(rows)
    return nav,pd.DataFrame(positions),b,pd.DataFrame(decisions),dict(**metrics(nav,initial),
        fills=len(b.fills),fees_tax=sum(f['fees_tax'] for f in b.fills),
        cash_dividend_credit=sum(float(d.get('cash_credit',0)) for d in b.dividends))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,default=ROOT/'repro/dd-switch-full-live-books')
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    panel,calendar=load_prices()
    events=load_dividend_events(ROOT/'data/dividend_events/e22_dividend_events.csv',require_exists=True,fail_closed_amounts=True)
    reports={};results=[];hashes={}
    for label,source in [('AS_RECORDED',ROOT/'forward/e21'),('R1_REPAIRED',ROOT/'repro/dd-switch-live-t1-r1')]:
        nav,positions,audit,b,snapshots,versions,report=reconstruct(source,panel,calendar,events)
        reports[label]=report
        for name,df in [('nav',nav),('positions',positions),('reconciliation',audit),('dividends',pd.DataFrame(b.dividends))]:
            df.to_csv(a.out/(label+'_'+name+'.csv'),index=False)
        for name in ('fills.csv','orders.csv','nav.csv','portfolio_state.json'):
            file=source/name;hashes[str(file.relative_to(ROOT))]=hashlib.sha256(file.read_bytes()).hexdigest()
        intents=target_intents(source,nav,snapshots,panel)
        for policy in POLICIES:
            cnav,cpos,cb,cdec,metrics_=counterfactual(policy,nav.date.tolist(),intents,report['initial'],panel,events,versions)
            name=label+'_'+policy.name
            for suffix,df in [('nav',cnav),('positions',cpos),('fills',pd.DataFrame(cb.fills)),('decisions',cdec),('dividends',pd.DataFrame(cb.dividends))]:
                df.to_csv(a.out/(name+'_'+suffix+'.csv'),index=False)
            results.append(dict(source=label,policy=policy.name,**metrics_))
    metrics_=pd.DataFrame(results)
    metrics_.to_csv(a.out/'metrics.csv',index=False)
    for name in ('data/dividend_events/e22_dividend_events.csv','forward/e21/live_market.csv','data/market/private_fin_adjusted.csv'):
        hashes[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    for name in ('data/calendars/twse_sessions_2026.csv','data/dividend_events/mops_payment_amendments.csv'):
        hashes[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    off=ROOT/'repro/dd-switch-t1-r1/00631L_ohlcv.csv'
    if not off.exists():off=ROOT/'data/def_proxies/00631L_ohlcv.csv'
    hashes[str(off.relative_to(ROOT))]=hashlib.sha256(off.read_bytes()).hexdigest()
    code_names=['scripts/dd_switch_full_live_books.py','scripts/live_ledger.py','scripts/e22_books_apply.py',
                'scripts/e22_dividend_accounting.py','scripts/e22_v3_sandbox_books.py','scripts/dd_switch_capital_policy.py']
    summary=dict(status='COMPLETE_RECORDED_FORWARD_BOOKS_SHORT_WINDOW',sources=reports,source_sha256=hashes,
                 code_sha256={x:hashlib.sha256((ROOT/x).read_bytes()).hexdigest() for x in code_names},
                 policies=[vars(p) for p in POLICIES],counterfactuals=results,
                 limitations=['Only actual recorded forward window; no invented 2013-2026 full-live history',
                              'Missing NAV dates mark existing holdings; missing strategy signals are not generated',
                              'Counterfactuals share exogenous recorded pending-order intents, not strategy feedback regeneration',
                              'BASELINE counterfactual replans targets and expires orders; compare policies to this arm, not directly to immutable reference',
                              'R1 changes controller inputs after 9/29; cannot treat difference as pure execution timing',
                              'Next-session raw open plus shared slip/cost model; no actual intraday fills or liquidity proof',
                              'Short-window returns not annualized; dividend coverage bounded by repository events',
                              'No policy promotion or live state mutation'])
    (a.out/'summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(reports,indent=2));print(metrics_.to_string(index=False))

if __name__=='__main__':main()
