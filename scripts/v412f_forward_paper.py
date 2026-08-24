#!/usr/bin/env python3
"""Generate frozen V4.12-D and E4 parallel forward-paper signals."""
import argparse,json
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import pandas as pd
import v412d_formal_router as d
import v412e1_crisis_buffer as e1
import v412e11_graduated_crisis as e11
import v412e2_e3_three_rounds as e3mod
import v412e4_execution_efficiency as e4

STOCKS=sorted(sum(d.GROUPS.values(),[]))

def weights_dict(row): return {s:round(float(row.get(s,0)),8) for s in STOCKS if float(row.get(s,0))>1e-10}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--raw',required=True); p.add_argument('--adjusted',required=True); p.add_argument('--forward-dir',required=True); p.add_argument('--start-date',default='2026-08-24'); a=p.parse_args()
    out=Path(a.forward_dir); out.mkdir(parents=True,exist_ok=True); raw=pd.read_csv(a.raw); adj=pd.read_csv(a.adjusted)
    z=d.prep(raw); rc,ro,ac,ao=e1.aligned_matrices(raw,adj); scores=d.make_scores(z,1); dates=list(rc.index); latest=dates[-1]
    dsig,_=d.targets(scores,dates,21,2,75)
    q=e3mod.raw_risk_features(z); exposure=e3mod.exposure_controller(q,'voltarget',.5,20,.14,.5)
    rt=2*d.FEE+d.TAX; base=e1.buffered_targets(scores,dates,0,5*rt,84); e4sig=e4.partial_rebalance(base,.25,.05); e4scaled=e4sig.mul(exposure,axis=0)
    # Signal at close T is the target for the next session open. Current executed weights are prior signal.
    current_d=dsig.shift(1).fillna(0).iloc[-1]; current_e4=e4scaled.shift(1).fillna(0).iloc[-1]
    next_d=dsig.iloc[-1]; next_e4=e4scaled.iloc[-1]
    run_utc=datetime.now(timezone.utc).isoformat()
    latest_obj={'version':'V4.12-F','run_utc':run_utc,'signal_date':latest.date().isoformat(),'execution':'next TWSE session open','data_latest_date':latest.date().isoformat(),
                'D':{'current_weights':weights_dict(current_d),'next_open_target':weights_dict(next_d),'cash_target':round(1-float(next_d.sum()),8)},
                'E4':{'current_weights':weights_dict(current_e4),'next_open_target':weights_dict(next_e4),'cash_target':round(1-float(next_e4.sum()),8),'risk_exposure':round(float(exposure.iloc[-1]),8)}}
    (out/'latest_signal.json').write_text(json.dumps(latest_obj,ensure_ascii=False,indent=2)+'\n')
    rows=[]
    for model,target,exp in [('D',next_d,1.0),('E4',next_e4,float(exposure.iloc[-1]))]:
        rows.append({'signal_date':latest.date().isoformat(),'run_utc':run_utc,'model':model,'exposure':exp,'cash_target':1-float(target.sum()),**{s:float(target.get(s,0)) for s in STOCKS}})
    hist=out/'signals_history.csv'; old=pd.read_csv(hist) if hist.exists() else pd.DataFrame()
    new=pd.DataFrame(rows)
    if len(old): old=old[~((old.signal_date==latest.date().isoformat())&old.model.isin(['D','E4']))]
    pd.concat([old,new],ignore_index=True).sort_values(['signal_date','model']).to_csv(hist,index=False)
    # Recomputed total-return paper curves. Only dates after the frozen forward start are published.
    dnav,dw,dc,_=e11.nav_with_exposure(ac,ao,dsig,pd.Series(1.,index=rc.index)); e4nav,e4w,e4c,_=e11.nav_with_exposure(ac,ao,e4sig,exposure)
    curves=pd.DataFrame({'date':rc.index,'D_nav':dnav.values,'E4_nav':e4nav.values,'E4_exposure':exposure.values})
    curves=curves[curves.date>=pd.Timestamp(a.start_date)].copy()
    if len(curves):
        for c in ('D_nav','E4_nav'): curves[c]=curves[c]/curves[c].iloc[0]
    curves.to_csv(out/'paper_nav_recomputed.csv',index=False)
    qc={'status':'PASS','run_utc':run_utc,'latest_date':latest.date().isoformat(),'raw_rows':len(raw),'signal_rows_total':len(pd.read_csv(hist)),'paper_rows':len(curves),
        'rules':['raw OHLCV signals through T','T+1 open target','adjusted layer evaluation only','D and E4 parameters frozen','same-date reruns replace rather than duplicate'],
        'checks':{'D_weight_sum':float(next_d.sum()),'E4_weight_sum':float(next_e4.sum()),'E4_exposure':float(exposure.iloc[-1]),'future_dates':int((rc.index>pd.Timestamp.utcnow().tz_localize(None)).sum())}}
    assert 0<=next_d.sum()<=1.000001 and 0<=next_e4.sum()<=1.000001 and qc['checks']['future_dates']==0
    (out/'forward_qc.json').write_text(json.dumps(qc,ensure_ascii=False,indent=2)+'\n'); print(json.dumps(latest_obj,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
