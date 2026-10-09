"""Actual-fill cash ownership for DD exits; no synthetic capital or receivables.

Reservations are claims inside account cash, never additional NAV. Ownership
continues after reentry, including board-lot residual cash and paid dividends.
"""
from copy import deepcopy
import math
import pandas as pd
from e16_soft_frozen_base import FIN, TEL
from live_fill_core import _iter_pending, _paper_fill_rows, _exact_t1_stats

GROUPS = {'FIN': list(FIN), 'TEL': list(TEL)}
VERSION = 'DD_ACTUAL_FILL_FUNDING_V1'

def sleeve(code):
    return next((k for k, codes in GROUPS.items() if str(code) in codes), None)

class DDFunding:
    def __init__(self, saved=None):
        self.state = deepcopy(saved) if saved else dict(version=VERSION, balances={'FIN':0.,'TEL':0.}, owned=[], orders={}, applied=[])
        if self.state.get('version') != VERSION:
            raise RuntimeError('Unknown DD funding version')
        if set(self.state['balances']) != set(GROUPS) or set(self.state['owned'])-set(GROUPS):
            raise RuntimeError('Invalid DD sleeve ownership')
        if len(self.state['applied']) != len(set(self.state['applied'])) or set(self.state['orders'].values())-set(self.state['owned']):
            raise RuntimeError('Invalid DD funding event/order registry')
        self.events = []
        self.check()

    def check(self, cash=None):
        if any(not math.isfinite(float(x)) or float(x)<-1e-5 for x in self.state['balances'].values()):
            raise RuntimeError('Invalid DD funding balance')
        if cash is not None and (not math.isfinite(float(cash)) or self.total > float(cash)+1e-5):
            raise RuntimeError('DD reservations exceed actual account cash')

    @property
    def total(self):
        return sum(self.state['balances'].values())

    def post(self, key, date, group, amount, kind):
        if key in self.state['applied']:
            raise RuntimeError('Duplicate DD funding event: '+key)
        amount=float(amount)
        if not math.isfinite(amount) or self.state['balances'][group]+amount < -1e-5:
            raise RuntimeError('DD funding overdraft or nonfinite credit')
        self.state['balances'][group] += amount
        self.state['applied'].append(key)
        self.events.append(dict(event_id=key,date=date,sleeve=group,kind=kind,amount=amount,balance=self.state['balances'][group]))

    def register(self, rows, gate):
        if not gate.get('ok'):
            raise RuntimeError('Cannot register DD ownership without valid gate')
        self.state['gate_active']=bool(gate['path3_active'])
        self.state['gate_asof']=gate.get('asof')
        for row in rows:
            group=sleeve(row['code'])
            if group and str(row['order_id']).endswith('-P3T0'):
                if not gate['path3_active'] and row['side']=='SELL' and group not in self.state['owned']:
                    self.state['owned'].append(group)
                if group in self.state['owned']:
                    self.state['orders'][str(row['order_id'])]=group

    def dividends(self, rows):
        for row in rows:
            group=sleeve(row['code'])
            paid=float(row.get('cash_credit',0) or 0)+float(row.get('cil_cash_credit',0) or 0)
            if group in self.state['owned'] and paid:
                self.post('DIV:'+str(row['key']),row['date'],group,paid,'PAID_DIVIDEND')

    def funded_plan(self, delta, meta, pos, prices):
        from path3_comp_sat_daily_share_ssot import scale_mix_to_shares
        from live_ledger import BUY_FEE, SLIP
        delta=dict(delta)
        for group in self.state['owned']:
            codes=GROUPS[group]
            mix=meta.get(group.lower()+'_mix')
            if mix is None:
                raise RuntimeError('DD funded reentry requires ledger mix')
            if not mix:  # Existing planner fail-closed semantics.
                continue
            value=sum(float(pos.get(c,0))*float(prices[c]) for c in codes)
            # Close-based estimate only: actual open gaps still obey affordability.
            cost=(1+SLIP)*(1+BUY_FEE)
            target=scale_mix_to_shares(mix,sleeve_dollars=value+self.state['balances'][group]/cost,prices=prices)
            for c in codes:
                delta.pop(c,None)
                raw=float(target.get(c,0))-float(pos.get(c,0))
                q=math.copysign(int(abs(raw)//1000)*1000,raw)
                if abs(q)>=1000-1e-9:delta[c]=q
        return delta, {**meta,'delta_shares':delta,'n_delta_names':len(delta),'dd_reserved_cash':dict(self.state['balances'])}

def reject_unfunded_legacy_exit(state_dir, saved):
    if saved is not None:
        return
    path=state_dir/'signals.csv'
    if path.exists():
        frame=pd.read_csv(path)
        if 'tipsoft_dd_path3_active' in frame:
            prior=frame.tipsoft_dd_path3_active.astype(str).str.lower().eq('false')
            if prior.any():
                raise RuntimeError('Legacy DD exit lacks cash ownership: reconstruct actual fills before adoption')


class FundingPaperPort:
    name='paper'
    def __init__(self, funding):self.funding=funding
    def fill_pending(self, *, state_dir, latest, open_prices, pos, cash):
        f=self.funding
        f.check(cash)
        fills=[]
        for _, row in _iter_pending(state_dir,latest,carve_authorized=False).iterrows():
            group=f.state['orders'].get(str(row.order_id))
            pocket=(f.state['balances'][group] if group else max(0.,cash-f.total)) if row.side=='BUY' else cash
            pos, _, accepted=_paper_fill_rows(pending=pd.DataFrame([row]),latest=latest,open_prices=open_prices,pos=pos,cash=pocket,carve_authorized=False)
            for fill in accepted:
                amount=(fill['gross']-fill['fees_tax']) if fill['side']=='SELL' else -fill['gross']-fill['fees_tax']
                cash += amount
                if group:f.post('FILL:'+str(fill['fill_id']),fill['fill_date'],group,amount,fill['side'])
                fills.append(fill)
            f.check(cash)
        same,ok=_exact_t1_stats(fills,carve_authorized=False)
        return pos,cash,fills,same,ok
