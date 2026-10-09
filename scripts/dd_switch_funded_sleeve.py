"""Research-only segregated cash wallets with immutable fill funding journal.

Each sleeve owns its bootstrap capital, actual net sales, cash dividends and
unspent money. Reentry consumes that money; no repeated refill, other-sleeve
cash, receivables or mother NAV can be spent. No live funding promotion.
"""
from dataclasses import dataclass,field
import math
@dataclass
class FundingJournal:
    initial:float
    applied:set=field(default_factory=set)
    net_sales:float=0.
    buy_spend:float=0.
    dividend_cash:float=0.
    rows:list=field(default_factory=list)
    def fill(self,row):
        key=row['fill_id']
        if key in self.applied:raise ValueError('Duplicate funding fill: '+key)
        gross=float(row['gross']);fee=float(row['fees_tax'])
        if not math.isfinite(gross) or not math.isfinite(fee) or gross<=0 or fee<0:
            raise ValueError('Invalid funding amount')
        change=gross-fee if row['side']=='SELL' else -gross-fee
        if self.cash+change < -1e-5:raise ValueError('Funding overdraft')
        if row['side']=='SELL':self.net_sales+=gross-fee
        elif row['side']=='BUY':self.buy_spend+=gross+fee
        else:raise ValueError('Invalid funding side')
        self.applied.add(key);self.rows.append(dict(kind='FILL',**row,funding_cash=self.cash))
        if self.cash < -1e-5:raise ValueError('Funding overdraft')
    def credit_dividend(self,day,amount):
        key='DIVIDEND-'+day
        if key in self.applied:raise ValueError('Duplicate dividend funding day')
        if not math.isfinite(amount):raise ValueError('Invalid dividend amount')
        self.applied.add(key)
        self.dividend_cash+=amount
        if amount:self.rows.append(dict(kind='DIVIDEND_CASH',date=day,cash_credit=amount,funding_cash=self.cash))
    @property
    def cash(self):return self.initial+self.net_sales-self.buy_spend+self.dividend_cash
    def reconcile(self,cash):
        gap=self.cash-float(cash)
        if abs(gap)>1e-4:raise ValueError('Funding journal does not reconcile: '+str(gap))
        return gap
