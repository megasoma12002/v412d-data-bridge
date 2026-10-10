"""Fixed-parent DD_SWITCH timing attribution; return-space sanity check only.

Not a next-open fill backtest: original parents lack executable joint holdings.
No parameter optimization, live writes, or new controller sources.
"""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd
import tipsoft_ip3_trail42_l4_signal_switch_stagea as legacy
from e45_paper_harness import window_stats,WINDOWS_STANDARD
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'repro/dd-switch-clock-attribution'
OUT.mkdir(parents=True,exist_ok=True)
l4_path=legacy.TWIN/'nav_REF_L4.csv'
if not l4_path.exists():l4_path=legacy.ALIGN/'nav_L4_LIVE_P3_WITHIN.csv'
tr_path=legacy.OBS/'nav_TRAIL42_FT_CASH.csv'
if not tr_path.exists():tr_path=legacy.TWIN/'nav_TWIN_TRAIL42_CASH.csv'
l4=legacy._load(l4_path);tr=legacy._load(tr_path)
p=pd.concat({'l4':legacy._returns(l4),'trail':legacy._returns(tr)},axis=1,join='inner').dropna()
navs=(1+p).cumprod();dd=navs/navs.cummax()-1
signal=dd.trail>=dd.l4
lag=signal.shift(1,fill_value=False)
models={'L4':p.l4,'TRAIL42':p.trail,'DD_same_day':p.trail.where(signal,p.l4),'DD_lag1_proxy':p.trail.where(lag,p.l4)}
switched=lag.ne(lag.shift(1,fill_value=False))
# Hypothetical incremental cost per decision flip on full account NAV.
# Not actual turnover: needed share deltas and traded fraction are unknown.
for bp in (5,10,20,50):models[f'DD_lag1_{bp}bp_per_flip_sensitivity']=models['DD_lag1_proxy']-switched.astype(float)*bp/10000
# Calendar sensitivity: aggregate original parent NAV changes between common
# dates instead of dropping L4 returns on dates absent from TRAIL. Gaps still
# prevent any claim of daily execution or complete daily drawdowns.
interval=pd.concat({'l4':l4.set_index('date').nav.reindex(p.index).pct_change().fillna(0),'trail':tr.set_index('date').nav.reindex(p.index).pct_change().fillna(0)},axis=1)
i_nav=(1+interval).cumprod();i_dd=i_nav/i_nav.cummax()-1
i_signal=i_dd.trail>=i_dd.l4
i_lag=i_signal.shift(1,fill_value=False)
models.update(interval_L4=interval.l4,interval_TRAIL42=interval.trail,interval_DD_same_day=interval.trail.where(i_signal,interval.l4),interval_DD_lag1_proxy=interval.trail.where(i_lag,interval.l4))
windows={**WINDOWS_STANDARD,'tip_ytd':(pd.Timestamp(p.index.max().year,1,1).date(),p.index.max().date())}
rows=[]
for name,ret in models.items():
 nav=legacy._nav_from_returns(ret)
 nav.to_csv(OUT/(name+'.csv'),index=False)
 for w,(a,b) in windows.items():
  s=window_stats(nav,a,b)
  if s.get('cagr') is None:continue
  rows.append(dict(model=name,window=w,cagr_pct=s['cagr']*100,mdd_pct=s['max_drawdown']*100,n=s['n_days']))
frame=pd.DataFrame(rows)
base=frame[frame.model=='L4'].set_index('window').cagr_pct
interval_base=frame[frame.model=='interval_L4'].set_index('window').cagr_pct
frame['benchmark']=['interval_L4' if x.startswith('interval_') else 'L4' for x in frame.model]
frame['lift_vs_L4_pp']=[r.cagr_pct-(interval_base.loc[r.window] if r.benchmark=='interval_L4' else base.loc[r.window]) for r in frame.itertuples()]
frame.to_csv(OUT/'metrics.csv',index=False)
raw_baseline={w:window_stats(l4,a,b) for w,(a,b) in windows.items()}
orig=legacy.OUT/'nav_TRAIL_WHEN_TR_DD_GTE_L4.csv'
ref=legacy._load(orig).set_index('date').nav
recreated=legacy._nav_from_returns(models['DD_same_day']).set_index('date').nav
relative_residual=float((recreated/ref.reindex(recreated.index)-1).abs().max())
if relative_residual>1e-10:raise RuntimeError('Original champion not reproduced')
decomp=[]
for w in frame.window.unique():
 f=frame[frame.window==w].set_index('model')
 x=float(f.loc['DD_same_day','lift_vs_L4_pp']);y=float(f.loc['DD_lag1_proxy','lift_vs_L4_pp'])
 raw=float(raw_baseline[w]['cagr']*100)
 matched=float(base.loc[w])
 decomp.append(dict(window=w,raw_L4_cagr_pct=raw,matched_L4_cagr_pct=matched,original_claimed_lift_pp=x+matched-raw,benchmark_calendar_component_pp=matched-raw,matched_original_lift_pp=x,lag1_remaining_matched_lift_pp=y,timing_sensitive_lift_pp=x-y,retained_matched_gain_ratio_pct=100*y/x if x>0 else None))
p.assign(signal_trail=signal,lag1_trail=lag,lag1_flip=switched).reset_index().to_csv(OUT/'decisions.csv',index=False)
summary=dict(method='fixed_parent_same_day_vs_one_observation_lag_return_proxy',source_files={str(x.relative_to(ROOT)):hashlib.sha256(x.read_bytes()).hexdigest() for x in [l4_path,tr_path,orig]},source_start=str(p.index.min().date()),source_end=str(p.index.max().date()),original_champion_relative_residual=relative_residual,n_lag1_flips=int(switched.sum()),missing_TRAIL_dates=l4.loc[~l4.date.isin(tr.date),'date'].dt.strftime('%F').tolist(),decomposition=decomp,limitations=['Lag1 is next common observation, not next-open fills; gaps, overnight/open-close effects unresolved','Original parent return stitches, reentry, corporate actions and NAV marks not changed or independently validated','Ratios measure timing sensitivity in CAGR lift, not fractions of realized profit or proof of executable alpha','Incremental bps per flip are sensitivity assumptions, not measured share turnover costs','No genuine intraday T0 test; causal intraday execution may retain a different amount'])
(OUT/'summary.json').write_text(json.dumps(summary,indent=2))
print(frame[frame.model.isin(['L4','TRAIL42','DD_same_day','DD_lag1_proxy'])].to_string(index=False))
print(json.dumps(decomp,indent=2))
