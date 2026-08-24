#!/usr/bin/env python3
"""Fail-closed QC for E21 forward ledgers."""
import argparse,json
from pathlib import Path
import pandas as pd

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--state-dir',default='e21_state');a=ap.parse_args();s=Path(a.state_dir);checks={}
    sig=pd.read_csv(s/'signals.csv');nav=pd.read_csv(s/'nav.csv');orders=pd.read_csv(s/'orders.csv',dtype={'code':str})
    checks['signals_unique_date']=not sig.date.duplicated().any();checks['nav_unique_date']=not nav.date.duplicated().any();checks['orders_unique_id']=not orders.order_id.duplicated().any();checks['weights_sum_one']=bool(((sig[['e16_financial','e16_telecom','e16_0050']].sum(1)-1).abs()<1e-8).all());checks['nav_positive']=bool((nav.nav_e16_e18>0).all());checks['no_negative_cash']=bool((nav.cash>=-1).all());checks['date_monotonic']=bool(pd.to_datetime(sig.date).is_monotonic_increasing and pd.to_datetime(nav.date).is_monotonic_increasing)
    checks['frozen_financial_universe']=set(['2880','2886','2892','5880']).issuperset(set(orders.code.astype(str))-set(['2412','3045','4904','0050']))
    if (s/'fills.csv').exists():
        fills=pd.read_csv(s/'fills.csv',dtype={'code':str});checks['fills_unique_id']=not fills.fill_id.duplicated().any();checks['fills_reference_existing_orders']=set(fills.fill_id.astype(str)).issubset(set(orders.order_id.astype(str)))
    audit=[json.loads(x) for x in (s/'audit_chain.jsonl').read_text().splitlines() if x.strip()];checks['audit_unique_date']=len({x['date'] for x in audit})==len(audit);checks['audit_chain_links']=all(audit[i]['previous_hash']==audit[i-1]['hash'] for i in range(1,len(audit)))
    status={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'signal_rows':len(sig),'nav_rows':len(nav),'order_rows':len(orders)};(s/'qc_status.json').write_text(json.dumps(status,indent=2)+'\n');print(json.dumps(status,indent=2))
    if status['status']!='PASS':raise SystemExit(1)
if __name__=='__main__':main()
