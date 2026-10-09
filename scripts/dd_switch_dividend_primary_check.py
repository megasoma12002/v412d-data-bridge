#!/usr/bin/env python3
"""Compare archived issuer/agent pages without inventing publication vintage."""
from io import StringIO
import json
import re
from pathlib import Path
import pandas as pd
from dd_switch_full_history_sources import ROOT

OUT=ROOT/'repro/dd-switch-full-history-audit'

def day(value):
    numbers=re.findall(r'\d+',str(value))
    if len(numbers)!=3:return ''
    y,m,d=map(int,numbers)
    if y<1911:y+=1911
    return f'{y:04d}-{m:02d}-{d:02d}'

def tables(name):
    p=OUT/'sources'/(name+'.html')
    if not p.exists():return []
    text=p.read_text();initial=pd.read_html(StringIO(text))
    converters={c:str for t in initial for c in t.columns if not isinstance(c,int)}
    return pd.read_html(StringIO(text),converters=converters)

def amount(value):
    s=str(value).strip().replace(',','')
    return float(s) if re.fullmatch(r'\d+(?:\.\d+)?',s) else 0.

def main():
    refs=[]
    mega=tables('mega_dividend')
    if mega:
        for row in mega[0].itertuples(index=False,name=None):
            ex=day(row[8]);pay=day(row[2]);stock_pay=day(row[6])
            refs.append(dict(code='2886',leg='cash',ex_date=ex,payment_date=pay,amount=amount(row[1]),source='PRIMARY_MEGA_HISTORY_CURRENT_PAGE',amount_display=str(row[1])))
            stock=amount(row[3])+amount(row[4])
            if stock>0:refs.append(dict(code='2886',leg='stock',ex_date=ex,payment_date=stock_pay,amount=stock,source='PRIMARY_MEGA_HISTORY_CURRENT_PAGE',amount_display=str(row[3])))
    cht=tables('cht_dividend')
    if cht:
        now=dict(cht[0].iloc[:7].itertuples(index=False,name=None))
        cash=re.search(r'([0-9]+\.[0-9]+)',now.get('現金股利',''))
        if cash:refs.append(dict(code='2412',leg='cash',ex_date=day(now['除權息交易日']),payment_date=day(now['現金發放日']),amount=float(cash.group(1)),amount_display=cash.group(1),source='PRIMARY_CHT_CURRENT_PAGE'))
        for row in cht[1].itertuples(index=False,name=None):
            # This historical table proves payment and amount, not ex-date.
            v=amount(row[2])+amount(row[5])
            refs.append(dict(code='2412',leg='cash',ex_date='',payment_date=day(row[6]),amount=v,amount_display=str(row[2]),source='PRIMARY_CHT_HISTORY_PAYMENT_AND_AMOUNT_ONLY'))
    for t in tables('hnfhc_agent'):
        if t.shape[1]!=2 or len(t)>15:continue
        fields=dict(t.itertuples(index=False,name=None))
        if '現金股利每股(元)' in fields:
            refs.append(dict(code='2880',leg='cash',ex_date=day(fields['除息交易日']),payment_date=day(fields['現金股利發放日']),amount=amount(fields['現金股利每股(元)']),amount_display=str(fields['現金股利每股(元)']),source='PRIMARY_HN_SECURITIES_AGENT_CURRENT_PAGE'))
    ctbc=tables('ctbc_agent_dividend')
    for t in ctbc:
        if t.shape[1]!=6 or len(t)<10 or '證券代號' not in t.columns:continue
        for r in t.to_dict('records'):
            if str(r['證券代號'])!='2891':continue
            refs.append(dict(code='2891',leg='cash',ex_date=day(r['除息交易日']),payment_date=day(r['發放日']),amount=amount(r['每股現金股利（元）']),amount_display=str(r['每股現金股利（元）']),source='PRIMARY_CTBC_AGENT_CURRENT_PAGE'))
    fet=tables('fet_dividend')
    if len(fet)>1:
        for row in fet[1].itertuples(index=False,name=None):
            ex=day(row[3])
            if ex and ex>='2010-01-01':refs.append(dict(code='4904',leg='cash',ex_date=ex,payment_date='',amount=amount(row[0]),amount_display=str(row[0]),source='PRIMARY_FET_HISTORY_EX_AND_AMOUNT_ONLY'))
    twm=tables('twm_dividend')
    if twm:
        html=(OUT/'sources/twm_dividend.html').read_text()
        payment=re.search(r'股利發放日[：:]\s*(\d+年\d+月\d+日)',html)
        for row in twm[0].itertuples(index=False,name=None):
            ex=day(row[4]);text=str(row[1]);match=re.match(r'([0-9]+(?:\.[0-9]+)?)',text)
            if not ex:
                year=re.search(r'(\d+)年分配',str(row[0]));md=re.findall(r'\d+',str(row[4]))
                if year and len(md)==2:ex=day(year.group(1)+'/'+md[0]+'/'+md[1])
            if ex and ex>='2010-01-01' and match:
                pay=day(payment.group(1)) if payment and ex.startswith('2026-') else ''
                refs.append(dict(code='3045',leg='cash',ex_date=ex,payment_date=pay,amount=float(match.group(1)),amount_display=match.group(1),source='PRIMARY_TWM_CURRENT_AND_HISTORY'))
    reference=pd.DataFrame(refs).drop_duplicates(['code','leg','ex_date','payment_date'])
    reference=reference[(reference.payment_date>='2010-01-01')|(reference.ex_date>='2010-01-01')]
    ledger=pd.read_csv(ROOT/'data/dividend_events/e22_dividend_events.csv',dtype={'code':str}).fillna('')
    result=[]
    for r in reference.to_dict('records'):
        leg=r['leg'];pool=ledger[ledger.code.eq(r['code'])]
        if r['ex_date']:pool=pool[pool[leg+'_ex_date'].eq(r['ex_date'])]
        elif r['payment_date']:pool=pool[pool[leg+'_payment_date'].eq(r['payment_date'])]
        if len(pool)!=1:
            result.append(dict(**r,status='NO_UNIQUE_LEDGER_MATCH',publication_vintage_certified=False));continue
        own=pool.iloc[0];delta=abs(float(own[leg+'_dividend'])-r['amount'])
        text=r['amount_display'];digits=len(text.partition('.')[2]) if '.' in text else 0
        bound=.5*10**(-digits)
        result.append(dict(**r,ledger_ex_date=own[leg+'_ex_date'],ledger_payment_date=own[leg+'_payment_date'],ledger_amount=float(own[leg+'_dividend']),absolute_amount_difference=delta,amount_status='EXACT' if delta<1e-8 else ('WITHIN_SOURCE_DISPLAY_PRECISION' if delta<=bound+1e-8 else 'REVIEW_AMOUNT_MISMATCH'),payment_match=own[leg+'_payment_date']==r['payment_date'] if r['payment_date'] else None,publication_vintage_certified=False,status='MATCHED_CURRENT_PRIMARY_PAGE'))
    report=pd.DataFrame(result);report.to_csv(OUT/'dividend_primary_page_check.csv',index=False)
    summary=dict(primary_comparisons=len(report),matched_current_primary_rows=int(report.status.eq('MATCHED_CURRENT_PRIMARY_PAGE').sum()),amount_review_rows=int(report.get('amount_status',pd.Series(dtype=str)).eq('REVIEW_AMOUNT_MISMATCH').sum()),payment_review_rows=int(report.get('payment_match',pd.Series(dtype=object)).eq(False).sum()),available_at_certified_rows=0,canonical_ledger_modified=False,limits=['Current issuer pages are not archived first-publication evidence','Source rounding is distinguished from exact cash entitlements','CTBC last-transfer date is NOT an amended ex-date','FET historical table has no cash-payment date'])
    (OUT/'dividend_primary_page_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary))

if __name__=='__main__':main()
