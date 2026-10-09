#!/usr/bin/env python3
"""Matched core-sleeve execution experiment: protection vs lost upside.

Segregated FIN/TEL wallets solve cash reentry in research. This is not the
complete live account (0050/private paths excluded) or a fitted champion.
"""
import argparse,hashlib,json
from pathlib import Path
import pandas as pd
from dd_switch_crisis_policies import RiskOverlay,POLICIES
from dd_switch_funded_sleeve import FundingJournal
from dd_switch_full_live_books import Book,load_prices,metrics
from dd_switch_crisis_audit import features
from dd_switch_live_replay import verify_runtime_generation
from path3_comp_sat_daily_share_ssot import FIN,TEL,dollar_mix
from live_fill_core import _paper_fill_rows
from e22_dividend_accounting import load_dividend_events
from twse_session_sources import cached_load_calendar_window
ROOT=Path(__file__).resolve().parents[1]
INITIAL=500000000.

def market_features(index):
    out=pd.DataFrame({'dd63':index/index.rolling(63,min_periods=63).max()-1,
                      'ret5':index.pct_change(5),'ret20':index.pct_change(20),
                      'above_ma20':index>index.rolling(20,min_periods=20).mean()})
    return out

def forward_labels(series,days=20):
    # Ex-post evaluator only. Last incomplete horizon stays NaN, never negative.
    lows=pd.concat([series.shift(-i) for i in range(1,days+1)],axis=1)
    valid=lows.notna().all(axis=1)
    return ((lows.min(axis=1)/series-1)<=-.10).astype(float).where(valid)

def simulate(policy,days,panel,mfeatures,dd,signals,ledgers,events,out,epoch,official_days):
    first=days[0];bookname=signals.loc[first,'book'];source=ledgers[bookname].loc[first]
    px=panel.loc[first,'close'].to_dict();fin=sum(source.get(c,0)*px[c] for c in FIN);tel=sum(source.get(c,0)*px[c] for c in TEL)
    if fin+tel<=0:raise ValueError('Need explicit nonzero initial parent core mix')
    capital={'FIN':INITIAL*.95*fin/(fin+tel),'TEL':INITIAL*.95*tel/(fin+tel)}
    books={name:Book(value) for name,value in capital.items()};funds={name:FundingJournal(value) for name,value in capital.items()}
    names={'FIN':FIN,'TEL':TEL};selected_events={name:[e for e in events if e.code in codes and e.ex_date>=first] for name,codes in names.items()}
    pending={};controller=RiskOverlay(policy);nav=[];positions=[];fills=[];decisions=[];residuals=[];attempts=[]
    for day in days:
        close=panel.loc[day,'close'].to_dict();op=panel.loc[day,'open'].to_dict()
        for name,b in books.items():
            entitlement=dict(b.positions)
            if pending.get(name):
                orders=pd.DataFrame(pending[name]);orders['buy']=orders.side.eq('BUY');orders=orders.sort_values(['buy','code'])
                pos,cash,new=_paper_fill_rows(pending=orders,latest=pd.Timestamp(day),open_prices=op,pos=dict(b.positions),cash=b.cash,carve_authorized=False)
                for row in new:
                    b.trade(day,row['code'],row['side'],row['quantity'],row['fill_price'],row['fees_tax']);funds[name].fill(row)
                    fills.append(dict(**row,sleeve=name))
                assert b.positions==pos and abs(b.cash-cash)<1e-5
                done={r['fill_id'] for r in new}
                for row in pending[name]:attempts.append(dict(**row,attempt_date=day,filled=row['order_id'] in done,sleeve=name))
            before=b.cash
            b.apply_dividends(day,'E22_v3_recv_pay_effdelay',selected_events[name],close,entitlement)
            funds[name].credit_dividend(day,b.cash-before)
            residuals.append(dict(date=day,sleeve=name,funding_residual=funds[name].reconcile(b.cash)))
            for c,q in b.positions.items():positions.append(dict(date=day,code=c,quantity=q,sleeve=name))
        value=INITIAL*.05+sum(b.nav(close) for b in books.values())
        cash=INITIAL*.05+sum(b.cash for b in books.values());recv=sum(sum(b.receivables.values()) for b in books.values())
        held=sum(q*close[c] for b in books.values() for c,q in b.positions.items())
        assert abs(value-cash-recv-held)<1e-5
        nav.append(dict(date=day,nav=value,cash=cash,receivables=recv,held_notional=held))
        observation=mfeatures.loc[day].to_dict();decision=controller.observe(observation,bool(dd.loc[pd.Timestamp(day),'active']))
        decisions.append(dict(date=day,policy=policy,dd_active=bool(dd.loc[pd.Timestamp(day),'active']),**observation,**decision))
        bookname=signals.loc[day,'book'];mother=ledgers[bookname].loc[day];pending={}
        for name,b in books.items():
            available=b.cash+sum(q*close[c] for c,q in b.positions.items()) # receivables not spendable
            mix=dollar_mix(mother,close,names[name]);target={c:int(available*decision['scale']*w/close[c]//1000)*1000 for c,w in mix.items()}
            orders=[]
            for c in sorted(set(b.positions)|set(target)):
                change=target.get(c,0)-b.positions.get(c,0)
                quantity=int(abs(change)//1000)*1000
                if quantity:orders.append(dict(order_id=epoch+'-'+policy+'-'+day+'-'+c,signal_date=day,code=c,side='BUY' if change>0 else 'SELL',quantity=quantity))
            pending[name]=orders
    nav=pd.DataFrame(nav);decisions=pd.DataFrame(decisions);fill_frame=pd.DataFrame(fills);position_frame=pd.DataFrame(positions)
    report=metrics(nav,INITIAL)
    expected_next=dict(zip(official_days[:-1],official_days[1:]))
    report.update(policy=policy,epoch=epoch,start=days[0],end=days[-1],fills=len(fills),fees_tax=sum(f['fees_tax'] for f in fills),
        slippage=sum(f['gross']/(1.0005 if f['side']=='BUY' else .9995)*.0005 for f in fills),
        cash_dividend=sum(f.dividend_cash for f in funds.values()),dividend_records=sum(len(b.dividends) for b in books.values()),
        funding_max_residual=max(abs(r['funding_residual']) for r in residuals),min_cash=float(nav.cash.min()),
        risk_reduced_days=int(decisions.scale.lt(1).sum()),stock_dividend_odd_lots_remaining={c:q%1000 for b in books.values() for c,q in b.positions.items() if q%1000},
        t1_all_fills=all(f['fill_date']>f['signal_date'] for f in fills),recovery_transitions=int((decisions.scale.gt(decisions.scale.shift(1))).sum()),
        delayed_due_to_missing_market_sessions=sum(f['fill_date']!=expected_next.get(f['signal_date']) for f in fills),
        unfilled_buy_attempts=sum(not r['filled'] and r['side']=='BUY' for r in attempts),initial_sleeve_capital=capital,
        funding=dict(net_sales=sum(f.net_sales for f in funds.values()),buy_spend=sum(f.buy_spend for f in funds.values()),cash_dividend=sum(f.dividend_cash for f in funds.values()),final_cash=sum(b.cash for b in books.values())))
    dest=out/epoch/policy;dest.mkdir(parents=True)
    nav.to_csv(dest/'nav.csv',index=False);decisions.to_csv(dest/'decisions.csv',index=False);fill_frame.to_csv(dest/'fills.csv',index=False);position_frame.to_csv(dest/'positions.csv',index=False)
    pd.DataFrame(residuals).to_csv(dest/'funding_residuals.csv',index=False);pd.DataFrame(attempts).to_csv(dest/'order_attempts.csv',index=False)
    pd.DataFrame([dict(sleeve=name,**row) for name,f in funds.items() for row in f.rows]).to_csv(dest/'funding_journal.csv',index=False)
    (dest/'summary.json').write_text(json.dumps(report,indent=2))
    return report,nav,decisions

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--allow-observation-gaps',action='store_true',help='Explicit diagnostic only; cannot certify exact T+1');p.add_argument('--epoch',choices=['all','complete_window_2026_0529_0731'],default='all');a=p.parse_args();a.out=a.out.resolve()
    if (ROOT/'repro').resolve() not in a.out.parents:raise SystemExit('Isolated research output only')
    a.out.mkdir(parents=True,exist_ok=False)
    spec=ROOT/'repro/dd-switch-crisis-profit-prespecified/policies.json';spec_hash=hashlib.sha256(spec.read_bytes()).hexdigest()
    runtime=ROOT/'repro/dd-switch-live-repair-runtime-certified';meta=json.loads((runtime/'current.json').read_text());g=verify_runtime_generation(runtime,meta)
    frames={key:pd.read_csv(g/meta['files'][key],parse_dates=['date']) for key in ['base','l4','trail']};dd=features(frames)
    signals=pd.read_csv(g/meta['files']['signal']).set_index('date')
    ledgers={name:pd.read_csv(g/meta['files']['shares_'+name],dtype={'code':str}).pivot(index='date',columns='code',values='shares').fillna(0.) for name in ['COMP_H150_x_A20','SAT_A20_RELAX']}
    panel,_=load_prices();index=panel.xs('TAIEX',level='code').close.sort_index();mfeatures=market_features(index)
    events=load_dividend_events(ROOT/'data/dividend_events/e22_dividend_events.csv',require_exists=True,fail_closed_amounts=True)
    epochs={'development_2025':('2025-01-01','2025-12-31'),'validation_2026':('2026-01-01',meta['asof']),'continuous_2025_2026':('2025-01-01',meta['asof'])}
    if a.epoch!='all':epochs={'complete_window_2026_0529_0731':('2026-05-29','2026-07-31')}
    reports=[];label_reports=[];attribution=[];calendar_hashes={};coverage=[]
    for epoch,(start,end) in epochs.items():
        all_days=[]
        for year in range(int(start[:4]),int(end[:4])+1):
            sessions,_=cached_load_calendar_window(year);all_days += [str(d) for d in sessions if start<=str(d)<=end]
            path=ROOT/f'data/calendars/twse_sessions_{year}.csv';calendar_hashes[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
        official_days=sorted(set(all_days));days=[];missing=[];missing_controls=[]
        for day in official_days:
            if day not in panel.index.get_level_values('date') or set(FIN+TEL+['TAIEX'])-set(panel.loc[day].index):missing.append(day)
            elif day not in signals.index or pd.Timestamp(day) not in dd.index:missing_controls.append(day)
            else:days.append(day)
        coverage.append(dict(epoch=epoch,missing_market_sessions=missing,missing_control_sessions=missing_controls,official_sessions=len(official_days),observed_sessions=len(days)))
        if (missing or missing_controls) and not a.allow_observation_gaps:
            raise ValueError('Incomplete sessions; diagnostic override required: '+str(missing+missing_controls))
        for day in days:
            if set(FIN+TEL+['TAIEX'])-set(panel.loc[day].index):raise ValueError('Incomplete core prices: '+day)
            if day not in signals.index or pd.Timestamp(day) not in dd.index:raise ValueError('Missing control session: '+day)
            if mfeatures.loc[day].isna().any():raise ValueError('Incomplete causal market features')
        base_nav=None;labels=None
        for policy in POLICIES:
            r,nav,decisions=simulate(policy,days,panel,mfeatures,dd,signals,ledgers,events,a.out,epoch,official_days)
            if policy=='CORE_ON':base_nav=nav;labels={'market':forward_labels(index.reindex(official_days)).reindex(days),'core_on':forward_labels(nav.set_index('date').nav.reindex(official_days)).reindex(days)}
            delta=nav.nav.diff().fillna(nav.nav.iloc[0]-INITIAL)-base_nav.nav.diff().fillna(base_nav.nav.iloc[0]-INITIAL)
            pnl=base_nav.nav.diff().fillna(base_nav.nav.iloc[0]-INITIAL)
            r.update(nav_gain_vs_core_on=r['final_nav']-float(base_nav.nav.iloc[-1]),
                baseline_down_days_gain=float(delta[pnl<0].sum()),baseline_up_days_difference=float(delta[pnl>=0].sum()))
            assert abs(r['nav_gain_vs_core_on']-r['baseline_down_days_gain']-r['baseline_up_days_difference'])<1e-4
            attribution.append(pd.DataFrame({'date':days,'epoch':epoch,'policy':policy,'baseline_daily_pnl':pnl,'relative_daily_pnl':delta,'risk_scale':decisions.scale}))
            alarm=decisions.set_index('date').scale.lt(1)
            for name,label in labels.items():
                truth=label.dropna().astype(bool);pred=alarm.reindex(truth.index)
                tp=int((pred&truth).sum());fp=int((pred&~truth).sum());fn=int((~pred&truth).sum());tn=int((~pred&~truth).sum())
                label_reports.append(dict(epoch=epoch,policy=policy,label=name,tp=tp,fp=fp,fn=fn,tn=tn,
                    precision=None if tp+fp==0 else tp/(tp+fp),recall=None if tp+fn==0 else tp/(tp+fn),
                    valid_days=len(truth),positive_days=int(truth.sum()),definition='Future 20 complete sessions min close / current close <= -10%; ex-post only'))
            reports.append(r);print(epoch,policy,round(r['return_pct'],4),round(r['observed_mdd_pct'],4),flush=True)
    assert hashlib.sha256(spec.read_bytes()).hexdigest()==spec_hash
    pd.DataFrame(reports).to_csv(a.out/'policy_comparison.csv',index=False);pd.DataFrame(label_reports).to_csv(a.out/'label_precision_recall.csv',index=False);pd.concat(attribution).to_csv(a.out/'daily_relative_pnl.csv',index=False)
    books=json.loads((ROOT/'repro/dd-switch-live-repair-books/summary.json').read_text());assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==v for n,v in books['source_sha256'].items() if n.startswith('forward/e21/'))
    result=dict(status='DATA_GAPPED_NEXT_OBSERVATION_DIAGNOSTIC_NOT_EXACT_T1_CERTIFIED' if any(c['missing_market_sessions'] or c['missing_control_sessions'] for c in coverage) else 'FUNDED_CORE_ONLY_PRESPECIFIED_PROTECTION_UPSIDE_EXPERIMENT_NO_PROMOTION',reports=reports,labels=label_reports,coverage=coverage,
        specification_sha256=spec_hash,calendar_hashes=calendar_hashes,runtime_manifest_sha256=hashlib.sha256((runtime/'current.json').read_bytes()).hexdigest(),
        canonical_history_unchanged=True,production_funding_not_modified=True,
        source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [g/meta['files']['signal'],g/meta['files']['base'],g/meta['files']['l4'],g/meta['files']['trail'],g/meta['files']['shares_COMP_H150_x_A20'],g/meta['files']['shares_SAT_A20_RELAX'],ROOT/'forward/e21/live_market.csv',ROOT/'data/dividend_events/e22_dividend_events.csv']},
        program_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__).resolve(),ROOT/'scripts/dd_switch_crisis_policies.py',ROOT/'scripts/dd_switch_funded_sleeve.py']},
        limits=['Core-only FIN/TEL matched experiment; 0050/private overlays excluded; not current full live DD_SWITCH performance',
        'Wallets preserve common 95% bootstrap allocation, 5% idle reserve, original parent within-sleeve mixtures; daily recon from total funded sleeve wealth incl cash',
        '2025 retrospective development and 2026 chronological validation were already inspected in prior work; not genuinely blind out-of-sample',
        'No tuning/search after specification; six fixed policies, no automatic champion selection or deployment',
        'Fixed current snapshot of dividends and original shadow share histories; not fully vintage PIT corporate-actions database',
        'E22 receivable/payment/stock books used, no spend of receivables; board-lot exits may leave stock-dividend odd lots',
        'Market labels are imperfect for core risk; trailing horizon is evaluation-only, last incomplete labels excluded',
        'Missing official market sessions are explicitly reported, no forward-filled opens/closes; diagnostic fills may be delayed; official forward labels reject incomplete horizons',
        'Market indicator rolling windows use available source observations; missing dates prevent exact-session certification',
        'Complete-window subset is chosen by calendar coverage after gap discovery, not by profit ranking; indicator warmup retains earlier input gaps',
        'Day-sign PnL bridge is descriptive paired-account attribution, not a pure causal false-alarm cost estimate',
        'Fixed 5bp open paper fills and current fee policy; no real liquidity proof; cash yield zero'])
    (a.out/'summary.json').write_text(json.dumps(result,indent=2))
    print(pd.DataFrame(reports)[['epoch','policy','return_pct','observed_mdd_pct','nav_gain_vs_core_on','baseline_down_days_gain','baseline_up_days_difference','fees_tax']].to_string(index=False))
if __name__=='__main__':main()
