#!/usr/bin/env python3
"""Locate recorded live-vs-parent mix gaps and audit their order origins.

Historical parent mixes are hindsight benchmarks, not reconstructed publication
vintages. A T-close mix gap alone is not a T+1 execution failure. Recorded
configuration stamps, order lifecycle and source freshness establish the break.
Canonical history is read-only; no rollout, strategy tuning or synthetic fills.
"""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
import pandas as pd
from dd_switch_full_live_books import load_prices,prices_on,reconstruct
from dd_switch_live_replay import verify_runtime_generation
from e22_dividend_accounting import load_dividend_events
from live_ledger import max_affordable_buy_qty
from path3_comp_sat_daily_share_ssot import FIN,TEL,dollar_mix,plan_delta_ledger_scaled
ROOT=Path(__file__).resolve().parents[1]

def flag(value):
    return str(value).strip().lower() in ('true','1','1.0')

def lifecycle(orders,fills,calendar,initial,cutoff):
    if orders.order_id.duplicated().any() or fills.fill_id.duplicated().any():raise ValueError('Duplicate order/fill id')
    ordermap=orders.set_index('order_id');days=sorted(calendar);nextday=dict(zip(days[:-1],days[1:]))
    cash=initial;rows=[];seen=set()
    for fill in fills.itertuples():
        if fill.fill_id not in ordermap.index:raise ValueError('Orphan fill')
        o=ordermap.loc[fill.fill_id]
        if o.code!=fill.code or o.side!=fill.side or o.signal_date!=fill.signal_date:raise ValueError('Order/fill identity mismatch')
        missing=float(o.quantity)-float(fill.quantity)
        if missing<0:raise ValueError('Overfill')
        affordable=max_affordable_buy_qty(cash,float(fill.fill_price)) if fill.side=='BUY' else None
        limited=bool(missing>0 and fill.side=='BUY' and float(fill.quantity)==affordable)
        if missing and not limited:raise ValueError('Unexplained partial fill')
        expected=nextday.get(fill.signal_date)
        if not expected or fill.fill_date<expected:raise ValueError('Before-next-session fill')
        rows.append(dict(order_id=fill.fill_id,signal_date=fill.signal_date,fill_date=fill.fill_date,code=fill.code,
            side=fill.side,requested=float(o.quantity),filled=float(fill.quantity),remainder=missing,
            cash_before=cash,affordable=affordable,next_session=expected,
            status='CASH_LIMITED_REMAINDER_NOT_RETRIED_BY_ORDER_ID' if limited else 'FULL_FILL',
            delayed=fill.fill_date>expected))
        cash+=-float(fill.gross)-float(fill.fees_tax) if fill.side=='BUY' else float(fill.gross)-float(fill.fees_tax)
        seen.add(fill.fill_id)
    for oid,o in ordermap.iterrows():
        if oid in seen:continue
        expected=nextday.get(o.signal_date)
        status='PENDING_AFTER_CUTOFF' if not expected or expected>cutoff else 'UNFILLED_ELIGIBLE_ORDER'
        rows.append(dict(order_id=oid,signal_date=o.signal_date,fill_date=None,code=o.code,side=o.side,
            requested=float(o.quantity),filled=0.,remainder=float(o.quantity),next_session=expected,status=status,delayed=False))
    return pd.DataFrame(rows),cash

def mix_gap(pos,ledger,prices,names):
    actual=dollar_mix(pos,prices,names);target=dollar_mix(ledger,prices,names)
    notional=sum(pos.get(c,0)*prices.get(c,0) for c in names)
    if not actual or not target:return None,notional
    # One-way turnover between fully-invested sleeve mixes. This ignores lot
    # flooring and does not assert exact cash-neutral affordability.
    return .5*sum(abs(actual.get(c,0)-target.get(c,0)) for c in set(actual)|set(target)),notional

def recorded_regime(row):
    if flag(row.get('path3_strategy_cutover_applied')):
        if row.get('path3_t0_weight_reason')=='ledger_stale':return 'CUTOVER_STALE_LEDGER_NO_RECON'
        return 'CUTOVER_OTHER'
    if row.get('path3_t0_weight_reason')=='no_flip':return 'FLIP_ONLY_NO_SWITCH'
    return 'PRE_DAILY_PATH3_CUTOVER_OR_NO_STAMP'

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    out=a.out.resolve()
    if (ROOT/'repro').resolve() not in out.parents:raise SystemExit('Isolated research output required')
    out.mkdir(parents=True,exist_ok=False)
    runtime=ROOT/'repro/dd-switch-original-runtime-t1';meta=json.loads((runtime/'current.json').read_text())
    generation=verify_runtime_generation(runtime,meta)
    signals=pd.read_csv(generation/meta['files']['signal']).set_index('date')
    parents={book:pd.read_csv(generation/meta['files']['shares_'+book],dtype={'code':str}).pivot(index='date',columns='code',values='shares').fillna(0)
             for book in ('COMP_H150_x_A20','SAT_A20_RELAX')}
    archived=ROOT/'repro/fin-sat-path3-daily-share-ssot-stagea/outputs/daily_shares_SAT_A20_RELAX.csv'
    old=pd.read_csv(archived,dtype={'code':str});old_tip=str(old.date.max())
    old_row=old[old.date==old_tip].set_index('code').shares
    certified_row=parents['SAT_A20_RELAX'].loc[old_tip]
    pd.testing.assert_series_equal(old_row.sort_index(),certified_row[old_row.index].sort_index(),check_names=False)
    panel,calendar=load_prices();events=load_dividend_events(ROOT/'data/dividend_events/e22_dividend_events.csv',require_exists=True,fail_closed_amounts=True)
    reports={};daily=[];mixrows=[];intentrows=[];hashes={};orderaudits={};snapshots={}
    for name,source in {'RECORDED':ROOT/'forward/e21','VERIFIED_T1':ROOT/'repro/dd-switch-original-live-t1'}.items():
        nav,pos,residual,book,snaps,_,report=reconstruct(source,panel,calendar,events)
        reports[name]=report;snapshots[name]=snaps
        fills=pd.read_csv(source/'fills.csv',dtype={'code':str});orders=pd.read_csv(source/'orders.csv',dtype={'code':str})
        audit,cash=lifecycle(orders,fills,calendar,report['initial'],report['end']);orderaudits[name]=audit
        if abs(cash-book.cash)>1e-4:raise ValueError('Cash lifecycle mismatch; dividend-aware lifecycle required')
        audit.to_csv(out/(name+'_order_lifecycle.csv'),index=False)
        nav.to_csv(out/(name+'_complete_nav.csv'),index=False);pos.to_csv(out/(name+'_positions.csv'),index=False)
        residual.to_csv(out/(name+'_book_residuals.csv'),index=False)
        live=pd.read_csv(source/'signals.csv').set_index('date')
        for day,holding in snaps.items():
            px=prices_on(panel,day,'close');sig=signals.loc[signals.index<=day].iloc[-1];bookname=str(sig.book)
            parent=parents[bookname].loc[day].to_dict()
            row=live.loc[day].to_dict() if day in live.index else {}
            fields=dict(source=name,date=day,book=bookname,signal_asof=signals.index[signals.index<=day][-1],
                regime=recorded_regime(row) if day in live.index else 'NO_RECORDED_SIGNAL',
                recorded_weight_reason=row.get('path3_t0_weight_reason'),recorded_path3_orders=row.get('path3_t0_n_orders'),
                cutover_applied=flag(row.get('path3_strategy_cutover_applied')),soft_orders_muted=row.get('path3_strategy_cutover_n_muted'),
                dd_reason=row.get('tipsoft_dd_reason'),dd_stale=flag(row.get('tipsoft_dd_stale')),
                archived_ledger_lag_days=(pd.Timestamp(day)-pd.Timestamp(old_tip)).days if day>old_tip else 0)
            for sleeve,names in [('FIN',FIN),('TEL',TEL)]:
                gap,notional=mix_gap(holding,parent,px,names);fields[sleeve+'_mix_gap_pct']=None if gap is None else gap*100
                fields[sleeve+'_notional']=notional;fields[sleeve+'_oneway_alignment_notional']=None if gap is None else gap*notional
                actual=dollar_mix(holding,px,names);target=dollar_mix(parent,px,names)
                for code in names:mixrows.append(dict(source=name,date=day,book=bookname,sleeve=sleeve,code=code,
                    actual_shares=holding.get(code,0),parent_shares=parent.get(code,0),price=px[code],
                    actual_weight=actual.get(code,0),parent_weight=target.get(code,0)))
            delta,plan=plan_delta_ledger_scaled(live_pos=holding,prices=px,ledger_shares=parent)
            fields['hindsight_parent_recon_names']=len(delta)
            daily.append(fields)
            if day>='2026-09-29':
                for code,quantity in delta.items():intentrows.append(dict(source=name,date=day,book=bookname,code=code,
                    actual_shares=holding.get(code,0),delta=quantity,target=holding.get(code,0)+quantity,
                    reference_close=px[code],scope='HINDSIGHT_CLOSE_T_PLAN_NOT_SAME_DAY_EXECUTION_REQUIREMENT'))
        for file in ('fills.csv','orders.csv','signals.csv','nav.csv','portfolio_state.json'):
            hashes[str((source/file).relative_to(ROOT))]=hashlib.sha256((source/file).read_bytes()).hexdigest()
    daily=pd.DataFrame(daily);mixrows=pd.DataFrame(mixrows);intents=pd.DataFrame(intentrows)
    daily.to_csv(out/'daily_mix_gap_timeline.csv',index=False);mixrows.to_csv(out/'daily_asset_weights.csv',index=False)
    intents.to_csv(out/'hindsight_recon_intents.csv',index=False)
    live=daily[daily.source=='RECORDED'];block=live[live.regime=='CUTOVER_STALE_LEDGER_NO_RECON']
    if block.empty:raise ValueError('Expected recorded stale cutover evidence missing')
    cutoff=block.date.iloc[0]
    codes=list(FIN)+list(TEL)
    origin=snapshots['RECORDED'][cutoff]
    unchanged=all(all(pos.get(c,0)==origin.get(c,0) for c in codes) for day,pos in snapshots['RECORDED'].items() if day>=cutoff)
    orders=pd.read_csv(ROOT/'forward/e21/orders.csv',dtype={'code':str})
    postorders=orders[orders.signal_date>=cutoff]
    if not postorders[postorders.code.isin(codes)].empty:raise ValueError('Found post-cutover FIN/TEL orders; re-evaluate freeze claim')
    filled_after=pd.read_csv(ROOT/'forward/e21/fills.csv',dtype={'code':str})
    ftfills=filled_after[(filled_after.fill_date>=cutoff)&filled_after.code.isin(codes)]
    current=pd.read_csv(ROOT/'repro/dd-switch-original-live-t1/orders.csv',dtype={'code':str})
    initialplan=intents[(intents.source=='RECORDED')&(intents.date==cutoff)]
    generated=current[(current.signal_date==cutoff)&current.order_id.str.endswith('-P3T0')]
    matched=initialplan.merge(generated,on='code',suffixes=('_plan','_order'))
    if len(matched)!=len(initialplan) or not all(matched.delta.abs()==matched.quantity):raise ValueError('Fresh-input initial plan mismatch')
    from live_path3_t0_weight_engine import plan_or_none_for_pipeline
    previous_env=os.environ.get('E21_DD_INPUTS_DIR');trace={}
    try:
        for label,directory in [('ARCHIVED_FALLBACK',out/'absent_runtime_for_archived_probe'),('VERIFIED_RUNTIME',runtime)]:
            os.environ['E21_DD_INPUTS_DIR']=str(directory)
            delta,detail=plan_or_none_for_pipeline(asof=cutoff,pos=origin,prices=prices_on(panel,cutoff,'close'))
            trace[label]=dict(delta=delta,reason=detail.get('reason'),ledger_asof=detail.get('ledger_asof'),
                ledger_lag_calendar_days=detail.get('ledger_lag_calendar_days'),switch=detail.get('switch'))
    finally:
        if previous_env is None:os.environ.pop('E21_DD_INPUTS_DIR',None)
        else:os.environ['E21_DD_INPUTS_DIR']=previous_env
    if trace['ARCHIVED_FALLBACK']['reason']!='ledger_stale' or trace['ARCHIVED_FALLBACK']['delta'] is not None:
        raise ValueError('Archived planner failure not reproduced')
    expected_delta=dict(zip(initialplan.code,initialplan.delta))
    if trace['VERIFIED_RUNTIME']['delta']!=expected_delta:raise ValueError('Current planner differs from certified initial recon')
    (out/'same_holdings_source_control.json').write_text(json.dumps(trace,indent=2))
    git_provenance={}
    for ref,file in [('825506af90a85f39919dc390c55dd055bf365ca7','scripts/e21_forward_pipeline.py'),
                     ('3a0e3e7d','repro/fin-sat-path3-daily-share-ssot-stagea/outputs/daily_shares_SAT_A20_RELAX.csv')]:
        content=subprocess.check_output(['git','show',ref+':'+file],cwd=ROOT)
        sha=subprocess.check_output(['git','rev-parse',ref],cwd=ROOT,text=True).strip()
        git_provenance[sha+':'+file]=dict(sha256=hashlib.sha256(content).hexdigest())
        if file.endswith('.csv'):
            from io import BytesIO
            git_provenance[sha+':'+file]['max_date']=str(pd.read_csv(BytesIO(content),usecols=['date']).date.max())
        else:
            lines=content.decode().splitlines()
            indices=[i for i,line in enumerate(lines) if 'suppress_soft_fin_tel' in line or 'plan_or_none_for_pipeline' in line]
            (out/'historical_cutover_call_order.txt').write_text('\n'.join(f'{i+1}: {lines[i]}' for i in indices)+'\n')
            if len(indices)!=2 or indices[0]>=indices[1]:raise ValueError('Historical call-order premise wrong')
    ra=orderaudits['RECORDED'];partial=ra[ra.status.str.startswith('CASH_LIMITED')]
    sourcefiles=[archived,runtime/'current.json',generation/meta['files']['signal'],generation/meta['files']['shares_SAT_A20_RELAX']]
    for f in sourcefiles:hashes[str(f.relative_to(ROOT))]=hashlib.sha256(f.read_bytes()).hexdigest()
    summary=dict(status='POSITION_ORIGIN_AND_ORDER_LIFECYCLE_RECONCILED',reports=reports,
        first_nonflat_benchmark_gap=str(live.loc[live.FIN_mix_gap_pct.notna(),'date'].iloc[0]),
        first_recorded_daily_cutover_failure=cutoff,archived_parent_tip=old_tip,
        archived_parent_tip_shares_equal_verified_parent=True,
        stale_cutover_recorded_days=block.date.tolist(),unchanged_FIN_TEL_shares_from_cutover=unchanged,
        post_cutover_FIN_TEL_order_count=int(postorders.code.isin(codes).sum()),
        post_cutover_path3_order_count=int(postorders.order_id.str.endswith('-P3T0').sum()),
        last_FIN_TEL_fills=ftfills[['signal_date','fill_date','code','side','quantity']].to_dict('records'),
        recorded_order_lifecycle=ra.status.value_counts().to_dict(),cash_limited_remainders=partial.to_dict('records'),
        delayed_orders=ra[ra.delayed].to_dict('records'),
        initial_fresh_recon=intents[(intents.source=='RECORDED')&(intents.date==cutoff)].to_dict('records'),
        fresh_recon_matches_verified_T1_initial_orders=True,same_holdings_source_control=trace,
        historical_git_provenance=git_provenance,source_sha256=hashes,
        program_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        limits=['Archived parent history is a hindsight benchmark, not proven publication-vintage data',
            'Before cutover live used different Soft rules; parent mix difference is not inherently an execution error',
            'EOD T mother targets are signals for T+1; same-day weight equality is not required',
            'Only recorded 32-session forward window; missing core signal dates are not synthesized',
            'No real broker/depth evidence, tuning, deployment or canonical book mutation'])
    (out/'summary.json').write_text(json.dumps(summary,indent=2))
    small=live[live.date.isin(['2026-08-25','2026-09-24','2026-09-29','2026-09-30','2026-10-08'])]
    print(small[['date','regime','FIN_mix_gap_pct','TEL_mix_gap_pct','soft_orders_muted']].to_string(index=False))
    print(json.dumps({k:v for k,v in summary.items() if k not in ('reports','source_sha256','initial_fresh_recon')},indent=2))
    lines=['# DD_SWITCH 持股偏離來源稽核','',
        '**主要斷點不是逐日漏成交，而是切換到每日 Path3 時，母帳過期且舊的金融／電信訂單已被關閉。**','',
        '## 已核對的時序','',
        '- 8/25 起 live 與原研究母帳袖套內比例已有差異，但當時使用 Soft 配置，尚未採用每日 Path3；兩者策略、歷史路徑及資金不同，不能把此差異視為錯單。',
        '- 9/29：Path3 紀錄 `no_flip`、0訂單，仍是只在換組合時接手；原 Soft 訂單照常產生。',
        '- 9/30：每日 WITHIN_SLEEVE_PATH3 已啟用，Soft金融／電信5筆訂單被抑制；Path3母持股截止9/29，回報 `ledger_stale`、0替代訂單。當日仍完成前一日6筆待成交，其中5筆金融／電信。',
        '- 10/1、10/2、10/6、10/7、10/8的記錄同樣母帳過期、每日抑制5筆Soft訂單、0 Path3訂單。10/2起另外記錄DD `nav_stale`，並非有效訊號指示持續持有。',
        '- 9/30收盤後到10/08，七檔公股金融／電信股数完全不變；新訂單僅0050。10/05沒有核心訊號記錄，只補持倉估值，不推測有抑制訂單。','',
        '## 比例差距','',
        '金融／電信各自比較市值權重，以兩組權重差絕對值總和的一半衡量；是將袖套內配置對齊所需的一側比例，不是NAV損失，也不是當日必須已成交的目標。不同帳戶資金大小經比例正規化排除。','',
        '| 日期 | 配置狀態 | 金融比例差 | 電信比例差 |','|---|---|---:|---:|']
    for r in small.itertuples():lines.append(f'| {r.date} | {r.regime} | {r.FIN_mix_gap_pct:.4f}% | {r.TEL_mix_gap_pct:.4f}% |')
    lines+=['','本期金融比例差没有逐日擴大；原先「逐漸偏離」的說法不精確。主要是舊配置未在接手時成功對齊，而後股數凍結。市值權重差仍會隨各股票價格改變，這不能被稱為每日新增持股錯誤。',
        '已核對新鮮來源的9/30收盤7筆再配置，與前次隔離T+1重播的初始Path3訂單逐碼／股數一致，於10/1成交。大筆2892買3,006,000股、2880賣1,324,000股、2886賣998,000股是對齊既有不一致配置，不是本期母帳每天換股。','',
        '同一9/30持股／價格控制實驗：讀封存來源回傳delta=None／ledger_stale／母帳日期9/29；只換成已核對新鮮來源即回傳7筆上述計畫、母帳與signal皆9/30。封存9/29母持股與核對版同日逐股數完全一致，排除更換一套不同母帳的解釋。此實驗只呼叫現有planner，不產生或寫入live訂單，沒有取消stale護欄。','',
        '## 訂單生命週期','',
        '- 108筆原訂單對107筆成交，沒有孤兒成交或重複ID。',
        '- 104筆足額成交；3筆5880買單部分成交，缺10,000／6,000／7,000股，與當時現金可負擔整張上限完全一致。日期為9/4、9/7、9/9，發生在每日Path3接手以前，沒有被描述成Path3漏單。',
        '- 上述部分成交一旦存在同order_id的fill_id，現有pending邏輯即視為已完成，不再重試餘量；這是另外的訂單狀態限制，需明確定義部分成交／剩餘取消或重試，不能靜默改寫舊成交。',
        '- 唯一未成交是10/08的0050買1,000股，下個交易日尚不在資料窗內，屬正常待成交。',
        '- 一筆0050訂單由10/2訊號延至10/6成交，原應10/5執行；10/5沒有pipeline記錄，屬漏跑日期延遲，與金融／電信停止再配置不同。','',
        '## 根因與修復順序','',
        '1. 資料刷新／接手失敗：先確保原母訊號、母持股、DD NAV與market使用相同交易日與版本，缺資料時整個session阻擋；不能把「舊策略已關閉、新策略未產單」當作成功持有。PR434現有頂層同日hash/asof預檢可阻擋，尚未部署。',
        '2. 遷移缺少初次對齊檢查：接手時比對實際袖套比例、現金與前一日待成交，明確保存首批T+1遷移訂單；不可假設沒有book flip就已持有新母帳。',
        '3. 訂單／日程生命週期：部分成交剩餘須有明確狀態，漏跑交易日不能僅補NAV後當作訂單準時完成。',
        '4. 一張日常取整磨損為次要問題，已有固定緩衝敏感度；先修資料與接手，再長期驗證緩衝。','',
        '此次只稽核，未改live策略、成交記錄或部署。最早比例差出現在不同策略時期；可判定的實際接手故障是9/30，不能聲稱從8/25開始策略都執行錯誤。','',
        'Git來源：9/30 cutover提交825506af90a85f39919dc390c55dd055bf365ca7的原pipeline先抑制Soft再呼叫Path3 planner；主線3a0e3e7d合併的PR372只補母持股至9/29。現有程式也保留此順序，頂層新預檢是此次PR434才新增。Git與記錄只能確定已記錄的版本／結果，未重建全歷史公告／資料修訂vintage。','',
        '## 重跑','', '```bash','python scripts/dd_switch_position_origin_audit.py --out repro/dd-switch-position-origin-new','```',
        '使用新的輸出目錄。完整32日權重／股數、逐日故障狀態、訂單生命週期與來源hash見同目錄CSV及summary.json。']
    (out/'README.md').write_text('\n'.join(lines)+'\n')

if __name__=='__main__':main()
