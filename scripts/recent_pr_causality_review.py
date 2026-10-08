"""Append-future invariance probe of PR433; isolated research only."""
import sys,json
from pathlib import Path
import numpy as np
import pandas as pd
PR = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / 'pr-research'
sys.path.insert(0,str(PR/'scripts'))
import tipsoft_ip3_crisis_feat_despec_stagea as d
OUT=Path(__file__).resolve().parents[1]/'repro/recent-pr-causality-review'
OUT.mkdir(parents=True,exist_ok=True)
panel,meta=d.build_panel()
panel['date']=pd.to_datetime(panel.date)
cut=pd.Timestamp('2018-12-31')
short=panel[panel.date<=cut].copy()

def compare(label):
 full,_=d.build_despec_arms(panel)
 prefix,_=d.build_despec_arms(short)
 rows=[]
 for key in prefix:
  a=prefix[key];b=full[key].reindex(a.index)
  same=np.isclose(a.to_numpy(),b.to_numpy(),equal_nan=True,rtol=1e-10,atol=1e-12)
  rows.append(dict(mode=label,arm=key,changed_past_bars=int((~same).sum()),past_bars=len(a)))
 return rows
rows=compare('PR433_original')
# Research-only illustration: fit sign before 2015 and use only historical
# distributions for rank and alerts. This is not a proposed live policy.
def train_orient(x,y):
 mask=x.index<=pd.Timestamp('2014-11-30')
 ic=d._spearman(x[mask],y[mask])
 high=ic is None or ic>=0
 return (x if high else -x),high

def past_alert(x,stress_high=True,q=d.ALERT_Q):
 threshold=x.shift(1).rolling(252,min_periods=50).quantile(q if stress_high else 1-q)
 return ((x>=threshold) if stress_high else (x<=threshold)).fillna(False)
d._orient_stress=train_orient
d._rank_pct=lambda x:d._rolling_pct(x,252)
d._alert_mask=past_alert
rows+=compare('train_sign_past_distribution_demo')
frame=pd.DataFrame(rows);frame.to_csv(OUT/'prefix_invariance.csv',index=False)
summary=dict(pr=433,head='94de1e9c',cutoff=str(cut.date()),panel_start=str(panel.date.min().date()),panel_end=str(panel.date.max().date()),modes={mode:dict(arms=len(g),changed_arms=int((g.changed_past_bars>0).sum()),changed_values=int(g.changed_past_bars.sum())) for mode,g in frame.groupby('mode')},limitation='Structural causality probe, not fresh OOS performance or complete repair; original NAVs and full-sample candidate selection remain unaudited for live promotion')
(OUT/'summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
