"""Record first valid DD/Path3 handoff from actual post-fill positions."""
import hashlib,json
from pathlib import Path
HANDOFF_VERSION='ORIGINAL_LINEAGE_T1_HANDOFF_V1'

def prepare_handoff(state,asof,positions,cash,overlays,order_rows,runtime,state_dir=None,new_fills=None):
    previous=state.get('dd_switch_handoff')
    if previous and previous.get('version')==HANDOFF_VERSION:
        import pandas as pd
        fp=Path(state_dir)/'fills.csv' if state_dir else None
        filled=set(pd.read_csv(fp).fill_id.astype(str)) if fp and fp.exists() else set()
        filled.update(str(r['fill_id']) for r in (new_fills or []))
        pending=[oid for oid in previous['order_ids'] if oid not in filled]
        from live_order_lifecycle import cancelled_ids
        cancelled=cancelled_ids(state_dir) if state_dir else set()
        replaced=[oid for oid in pending if oid in cancelled]
        return {**previous,'last_checked':asof,'unfilled_initial_order_ids':pending,
            'cancelled_initial_order_ids':replaced,
            'status':('INITIAL_ORDERS_FILLED' if previous['order_ids'] and not pending else
                      'INITIAL_INTENTS_REPLACED' if replaced else previous['status'])}
    if not overlays.path3_cutover_meta.get('applied'):return previous
    plan=overlays.path3_weight_meta;gate=(plan.get('tipsoft_dd_switch') or {}).get('gate') or {}
    if plan.get('ledger_asof')!=asof or not gate.get('ok') or gate.get('asof')!=asof:
        raise RuntimeError('Initial handoff requires same-day parent and valid DD gate')
    rows=[row for row in order_rows if str(row['order_id']).endswith('-P3T0')]
    delta=plan.get('delta_shares',{}) if gate.get('path3_active') else {
        r['code']:(r['quantity'] if r['side']=='BUY' else -r['quantity']) for r in rows}
    emitted={r['code']:(r['quantity'] if r['side']=='BUY' else -r['quantity']) for r in rows}
    if emitted!={c:q for c,q in delta.items() if abs(q)>=1000}:
        raise RuntimeError('Initial handoff plan not fully represented by emitted orders')
    if any(r.get('execution_clock')!='NEXT_SESSION_OPEN' for r in rows):
        raise RuntimeError('Initial handoff must use T+1 qualification')
    meta=Path(runtime)/'current.json'
    return dict(version=HANDOFF_VERSION,signal_date=asof,ledger_asof=plan['ledger_asof'],
        gate_asof=gate['asof'],active=bool(gate.get('path3_active')),book=(plan.get('switch') or {}).get('book'),
        status='T1_ORDERS_SCHEDULED' if rows else 'NO_BOARD_LOT_DELTA',
        positions_after_prior_open_fills=dict(positions),cash_after_prior_open_fills=float(cash),
        planned_delta=emitted,order_ids=[r['order_id'] for r in rows],
        runtime_manifest_sha256=hashlib.sha256(meta.read_bytes()).hexdigest(),
        execution_clock='NEXT_SESSION_OPEN')
