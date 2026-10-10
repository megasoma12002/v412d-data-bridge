"""Explicit terminal legacy partials and replacement of unfunded stale intents.

Current paper BUY policy remains all-or-none. Historical partial-fill remainders
are cancelled explicitly; current target planning uses actual positions rather
than reviving obsolete September signals. CSV fills/orders remain immutable.
"""
from pathlib import Path
import pandas as pd

def cancelled_ids(state_dir):
    path=Path(state_dir)/'order_events.csv'
    if not path.exists():return set()
    events=pd.read_csv(path,dtype={'order_id':str})
    return set(events.loc[events.status.str.startswith('CANCELLED'),'order_id'])

def prepare_order_events(state_dir,asof,new_orders,new_fills,cutover):
    from e16_soft_frozen_base import FIN,TEL
    root=Path(state_dir);op=root/'orders.csv';fp=root/'fills.csv'
    if not op.exists():return []
    orders=pd.read_csv(op,dtype={'code':str});fills=pd.read_csv(fp,dtype={'code':str}) if fp.exists() else pd.DataFrame()
    if new_fills:fills=pd.concat([fills,pd.DataFrame(new_fills)],ignore_index=True)
    amounts=fills.groupby('fill_id').quantity.sum().to_dict() if not fills.empty else {}
    cancelled=cancelled_ids(root);newcodes={r['code'] for r in new_orders};rows=[]
    for o in orders.itertuples():
        if o.order_id in cancelled:continue
        filled=float(amounts.get(o.order_id,0));remainder=float(o.quantity)-filled
        if remainder<0:raise RuntimeError('Order overfill: '+o.order_id)
        if 0<filled<float(o.quantity):
            reason='CANCELLED_LEGACY_PARTIAL_REMAINDER'
        elif filled==0 and o.signal_date<asof and (o.code in newcodes or (cutover and o.code in FIN+TEL)):
            reason='CANCELLED_REPLACED_BY_CURRENT_TARGET'
        else:continue
        rows.append(dict(event_id=asof+'-'+o.order_id+'-'+reason,date=asof,order_id=o.order_id,
            status=reason,filled_quantity=filled,cancelled_quantity=remainder,
            reason='Actual holdings are replanned at close; no stale remainder resurrection'))
    return rows

def write_order_lifecycle(state_dir,asof):
    root=Path(state_dir)
    if not (root/'orders.csv').exists():return
    orders=pd.read_csv(root/'orders.csv',dtype={'code':str})
    fills=pd.read_csv(root/'fills.csv',dtype={'code':str}) if (root/'fills.csv').exists() else pd.DataFrame()
    amounts=fills.groupby('fill_id').quantity.sum().to_dict() if not fills.empty else {}
    events=pd.read_csv(root/'order_events.csv').set_index('order_id') if (root/'order_events.csv').exists() else pd.DataFrame()
    rows=[]
    for o in orders.itertuples():
        filled=float(amounts.get(o.order_id,0));remainder=float(o.quantity)-filled
        if remainder<0:raise RuntimeError('Order overfill')
        status='FILLED' if remainder==0 else 'PENDING_ALL_OR_NONE'
        if not events.empty and o.order_id in events.index:
            e=events.loc[o.order_id];status=str(e.iloc[-1].status if isinstance(e,pd.DataFrame) else e.status)
        rows.append(dict(order_id=o.order_id,signal_date=o.signal_date,code=o.code,side=o.side,
            requested=o.quantity,filled=filled,remainder=remainder,status=status,asof=asof))
    pd.DataFrame(rows).to_csv(root/'order_lifecycle.csv',index=False)
