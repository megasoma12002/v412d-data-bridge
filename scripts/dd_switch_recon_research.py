#!/usr/bin/env python3
"""Summarize fixed, feedback-driven T+1 reconciliation sensitivities.

All policies use identical frozen original-lineage controls and observed raw
prices. This short window is diagnostic, not out-of-sample strategy selection.
"""
import argparse, hashlib, json
from pathlib import Path
import pandas as pd
from dd_switch_full_live_books import load_prices,reconstruct
from dd_switch_gap_attribution import book_flows
from dd_switch_original_live_audit import clock_audit,TERMS
from e22_dividend_accounting import load_dividend_events
ROOT=Path(__file__).resolve().parents[1]
POLICIES=('audit','epsilon','one_lot','sleeve_5bp','sleeve_20bp')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    a.out=a.out.resolve()
    if (ROOT/'repro').resolve() not in a.out.parents:raise SystemExit('Research output only')
    a.out.mkdir(parents=True,exist_ok=False)
    panel,calendar=load_prices()
    events=load_dividend_events(ROOT/'data/dividend_events/e22_dividend_events.csv',require_exists=True,fail_closed_amounts=True)
    reports={};flows={};navs={};audits={};clocks={};hashes={};daily=[]
    controls=['date','tipsoft_dd_want_trail','tipsoft_dd_trail42_on','tipsoft_dd_path3_active']
    frozen=ROOT/'repro/dd-switch-original-live-t1'
    original_fills=pd.read_csv(frozen/'fills.csv',dtype={'code':str})
    original_controls=pd.read_csv(frozen/'signals.csv')[controls]
    fillcols=['signal_date','fill_date','code','side','quantity','fill_price','fees_tax']
    for policy in POLICIES:
        source=ROOT/('repro/dd-switch-recon-'+policy)
        nav,pos,resid,book,_,_,report=reconstruct(source,panel,calendar,events)
        fills=pd.read_csv(source/'fills.csv',dtype={'code':str});orders=pd.read_csv(source/'orders.csv',dtype={'code':str})
        signals=pd.read_csv(source/'signals.csv')[controls]
        pd.testing.assert_frame_equal(signals,original_controls)
        if policy=='audit':pd.testing.assert_frame_equal(fills[fillcols],original_fills[fillcols])
        audits[policy]=pd.read_json(source/'recon_audit.jsonl',lines=True,dtype={'code':str},convert_dates=False)
        audit=audits[policy]
        report.update(policy=policy,post_seed_fills=int((fills.fill_date>'2026-09-29').sum()),
            buffered_intents=int(audit.buffered.sum()),numerical_one_lot_sells=int(audit.numerical_one_lot_sell.sum()),
            controls_equal=True)
        clocks[policy]=clock_audit(fills,orders,calendar,'2026-09-29')
        flow=book_flows(nav,pos,fills,panel,report['initial']).set_index(['date','code'])
        flows[policy]=flow;navs[policy]=nav;reports[policy]=report
        nav.to_csv(a.out/(policy+'_complete_nav.csv'),index=False)
        resid.to_csv(a.out/(policy+'_book_residuals.csv'),index=False)
        pos.to_csv(a.out/(policy+'_positions.csv'),index=False)
        audit.to_csv(a.out/(policy+'_recon_intents.csv'),index=False)
        for file in ('fills.csv','orders.csv','signals.csv','portfolio_state.json','recon_audit.jsonl'):
            hashes[str((source/file).relative_to(ROOT))]=hashlib.sha256((source/file).read_bytes()).hexdigest()
        fills.to_csv(a.out/(policy+'_fills.csv'),index=False)
        orders[orders.signal_date>'2026-09-29'].to_csv(a.out/(policy+'_post_seed_orders.csv'),index=False)
    bridges={}
    base=reports['audit']
    for policy in POLICIES:
        diff=flows[policy][TERMS].subtract(flows['audit'][TERMS],fill_value=0)
        components=diff.sum().to_dict();gain=reports[policy]['final_nav']-base['final_nav']
        if abs(sum(components.values())-gain)>1e-4:raise ValueError('Accounting bridge does not close')
        bridges[policy]=dict(nav_gain=gain,components=components,residual=sum(components.values())-gain)
        reports[policy].update(nav_gain=gain,fee_saving=base['fees_tax']-reports[policy]['fees_tax'])
        diff.to_csv(a.out/(policy+'_minus_audit_asset_pnl.csv'))
        d=navs[policy][['date','nav']].merge(navs['audit'][['date','nav']],on='date',suffixes=('','_baseline'))
        d['nav_gain']=d.nav-d.nav_baseline;d['policy']=policy;daily.append(d)
    pd.concat(daily).to_csv(a.out/'daily_policy_comparison.csv',index=False)
    pd.DataFrame(reports.values()).to_csv(a.out/'policy_comparison.csv',index=False)
    intents=audits['audit'];one=intents[intents.delta.abs()==1000]
    rounding=dict(intents=len(intents),one_lot_intents=len(one),numerical_one_lot_sells=int(one.numerical_one_lot_sell.sum()),
        economic_sub_lot_sell_intents=int(((one.delta<0)&(one.fractional_gap_to_current<0)&(one.fractional_gap_to_current>-1000)).sum()),
        largest_deltas=intents.reindex(intents.delta.abs().sort_values(ascending=False).index).head(7).to_dict('records'))
    runtime=ROOT/'repro/dd-switch-original-runtime-t1'
    manifest=json.loads((runtime/'current.json').read_text())
    shares=pd.read_csv(runtime/manifest['generation']/manifest['files']['shares_SAT_A20_RELAX'],dtype={'code':str})
    pivot=shares[shares.date>='2026-09-29'].pivot(index='date',columns='code',values='shares')
    constant=bool(pivot.eq(pivot.iloc[0]).all().all())
    rounding['SAT_parent_shares_unchanged_0929_through_1008']=constant
    summary=dict(status='RECONCILED_FIXED_POLICY_SENSITIVITY_ONLY',seed='2026-09-29',
        reports=reports,rounding_audit=rounding,bridges=bridges,clock_audits=clocks,baseline_fills_exact=True,
        source_sha256=hashes,runtime_manifest_sha256=hashlib.sha256((runtime/'current.json').read_bytes()).hexdigest(),
        program_sha256={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in
            [Path(__file__).resolve(),ROOT/'scripts/dd_switch_recon_pipeline.py',ROOT/'scripts/dd_switch_live_replay.py']},limits=[
            'Only seven regenerated sessions after 9/29; 32-session full NAV includes identical earlier records',
            'All policies prespecified; no best-threshold search or out-of-sample claim',
            'Full production position/cash feedback; buffers affect only same-book nonzero recon',
            'Future skipped target differences are recomputed from actual positions, not summed old share deltas',
            'DD exits run after the buffer and retain priority; no observed exit or book flip in this short window',
            'Open fixed slippage only; no real depth, participation or broker fill proof',
            'No production deployment or original virtual-NAV promotion'])
    (a.out/'summary.json').write_text(json.dumps(summary,indent=2))
    text=['# DD_SWITCH 小幅再配置敏感度研究','',
        '截至 2026-10-08。使用已核對原母帳、T 日收盤訊號／下一交易日開盤成交。9/29 前帳本相同，之後 7 個交易日重新跑正式 pipeline；以下報酬與回撤涵蓋完整 32 個交易日。','',
        '| 固定方案 | 報酬 | 最大回撤 | 比基準增加 NAV | 節省費稅 | 新成交筆數 |',
        '|---|---:|---:|---:|---:|---:|']
    labels={'audit':'原 T+1 基準','epsilon':'只修浮點取整','one_lot':'一張以內緩衝','sleeve_5bp':'袖套金額 5bp 緩衝','sleeve_20bp':'袖套金額 20bp 緩衝'}
    for policy,r in reports.items():
        text.append(f"| {labels[policy]} | {r['return_pct']:.6f}% | {r['observed_mdd_pct']:.6f}% | {r['nav_gain']:,.2f} | {r['fee_saving']:,.2f} | {r['post_seed_fills']} |")
    text+=['','## 取整與交易來源','',
        f"基準 {len(intents)} 筆 Path3 再配置意圖中，有 {len(one)} 筆一張調整；其中純浮點誤差造成的一張賣出 {rounding['numerical_one_lot_sells']} 筆，實質目標減少不足一張但被向下取整放大為一張賣出 {rounding['economic_sub_lot_sell_intents']} 筆。最後一天意圖可能尚未成交。",
        '大筆 9/30 再配置是母帳比例與現有持股不一致，並非一張取整噪音。單靠小額緩衝無法追回主要大型調整成本。','',
        f'額外核對：選中的 SAT 母帳股數自9/29至10/08完全不變：{constant}。因此本期大筆調整主要是既有 live 持股向母帳比例對齊；其後一張賣出呈現整張向下取整後、袖套金額縮小再縮放的連續磨損。這不是這段期間每日新母帳換股的證據。',
        '一張緩衝增加 NAV 18,549.56 元，其中費稅節省6,062.81元；其餘是成交價差與持股路徑的合計影響，不能全部當作穩定交易成本節省。相較剩餘原帳差距1,051,703.62元，本期僅縮小約1.76%。','',
        '一張方案按股數；5/20bp 方案按該金融或電信袖套現有市值，分別為 0.05%/0.20%。換 COMP/SAT、持股歸零、新增名稱不緩衝；DD 退場在緩衝之後套用，仍保留完整退場權限。當天未交易差距會在下一交易日用實際持股重新計算。','',
        '## 驗證與用途','',
        '基準成交逐欄重現既有原鏈 T+1；全部方案 DD 控制訊號一致、完整現金／持股／NAV 對帳通過，T+1 成交時鐘通過，逐資產損益橋接閉合。',
        '這是短期敏感度分析，不能據此選最佳門檻。樣本未涵蓋新的換組合或 DD 退場事件，保護規則另有單元測試。應以更長期間與未參與設定門檻的後續樣本驗證，才考慮 live 採用。原研究虛擬報酬差距不是必須追平的績效目標。',
        '下一階段優先把忠實來源鏈從較早的共同種子持續刷新、完整產生訂單，再檢查9/30巨額對齊是否由先前持股偏離累積；不能用延遲正確換股來製造本期報酬改善。大型調整的分批成交需有實際量價／深度資料驗證容量與等待風險。',
        '', '## 重跑', '', '```bash',
        'for policy in audit epsilon one_lot sleeve_5bp sleeve_20bp; do',
        '  python scripts/dd_switch_live_replay.py --inputs-dir repro/dd-switch-original-runtime-t1 --out repro/dd-switch-recon-$policy --recon-research-policy "$policy"',
        'done',
        'python scripts/dd_switch_recon_research.py --out repro/dd-switch-recon-final',
        'PYTHONPATH=scripts python -m unittest discover -s tests -p "test_dd_switch_*.py"',
        '```',
        '重跑時改用新的研究輸出目錄，工具拒絕覆寫既有目錄。基礎逐筆輸出與凍結runtime已隨PR保存。',
        '','完整逐筆意圖、成交、持股、NAV、每日相對差距與會計分解見同目錄 CSV；來源 SHA256 見 summary.json。']
    (a.out/'README.md').write_text('\n'.join(text)+'\n')
    print(pd.DataFrame(reports.values())[['policy','return_pct','observed_mdd_pct','nav_gain','fee_saving','post_seed_fills']].to_string(index=False))
    print(json.dumps(rounding,indent=2))

if __name__=='__main__':main()
