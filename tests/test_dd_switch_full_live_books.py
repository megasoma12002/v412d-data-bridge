"""Accounting and time-cut tests; fixtures are not strategy evidence."""
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch
import pandas as pd
from dd_switch_full_live_books import Book,target_intents,counterfactual,target_quantity
from dd_switch_capital_policy import POLICIES
from e22_dividend_accounting import DivEvent

class FullBooksTest(unittest.TestCase):
    def test_integer_lot_weight_roundtrip(self):
        nav=500000000;price=103.8;quantity=32000
        self.assertEqual(target_quantity(nav,quantity*price/nav,price),quantity)
        self.assertEqual(target_quantity(nav,(quantity-.01)*price/nav,price),quantity-1000)

    @patch('dd_switch_full_live_books.cached_load_calendar_window',return_value=([date(2026,10,1),date(2026,10,8)],[date(2026,10,1),date(2026,10,8)]))
    def test_receivable_survives_sell_and_settles_once(self,_):
        b=Book(1000,positions={'2880':1000})
        events=[DivEvent('2880','cash','2026-10-01',1,'2026-10-08')]
        b.apply_dividends('2026-10-01','E22_v3_recv_pay',events,{'2880':10},{'2880':1000})
        self.assertEqual(sum(b.receivables.values()),1000)
        b.trade('2026-10-02','2880','SELL',1000,10,20)
        before=b.nav({'2880':10})
        b.apply_dividends('2026-10-08','E22_v3_recv_pay',events,{'2880':10},{})
        self.assertEqual(sum(b.receivables.values()),0)
        self.assertEqual(b.nav({'2880':10}),before)
        cash=b.cash
        b.apply_dividends('2026-10-08','E22_v3_recv_pay',events,{'2880':10},{})
        self.assertEqual(b.cash,cash)

    @patch('dd_switch_full_live_books.cached_load_calendar_window',return_value=([date(2026,10,1),date(2026,10,8)],[date(2026,10,1),date(2026,10,8)]))
    def test_ex_day_buy_has_no_prior_entitlement(self,_):
        b=Book(100000,positions={'2880':1000})
        events=[DivEvent('2880','cash','2026-10-01',1,'2026-10-08')]
        b.apply_dividends('2026-10-01','E22_v3_recv_pay',events,{'2880':10},{})
        b.apply_dividends('2026-10-08','E22_v3_recv_pay',events,{'2880':10},{'2880':1000})
        self.assertEqual(b.cash,100000)
        self.assertEqual(sum(b.receivables.values()),0)

    @patch('dd_switch_full_live_books.cached_load_calendar_window',return_value=([date(2026,10,1)],[date(2026,10,1)]))
    def test_stock_dividend_uses_entitlement_not_post_fill_shares(self,_):
        b=Book(1000,positions={'2880':3000})
        b.apply_dividends('2026-10-01','E22_v3_recv_pay',[DivEvent('2880','stock','2026-10-01',2)],{'2880':10},{'2880':1000})
        self.assertEqual(b.positions['2880'],3200)

    def test_future_orders_and_future_fills_do_not_change_prior_intent(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)
            orders=pd.DataFrame([dict(order_id='o1',signal_date='2026-10-01',code='0050',side='BUY',quantity=1000),
                                 dict(order_id='future',signal_date='2026-10-02',code='9999',side='BUY',quantity=999999)])
            orders.to_csv(path/'orders.csv',index=False)
            fills=pd.DataFrame([dict(fill_id='o1',fill_date='2026-10-02')]);fills.to_csv(path/'fills.csv',index=False)
            nav=pd.DataFrame([dict(date='2026-10-01',nav=200000)])
            panel=pd.DataFrame([dict(date='2026-10-01',code='0050',close=100)]).set_index(['date','code'])
            intents=target_intents(path,nav,{'2026-10-01':{}},panel)
            self.assertEqual(intents['2026-10-01']['weights'],{'0050':.5})
            orders.iloc[:1].to_csv(path/'orders.csv',index=False)
            fills.iloc[:0].to_csv(path/'fills.csv',index=False)
            self.assertEqual(intents,target_intents(path,nav,{'2026-10-01':{}},panel))

    @patch('dd_switch_full_live_books.cached_load_calendar_window',return_value=([],[]))
    def test_next_session_fill_reserve_and_prefix_invariance(self,_):
        days=['2026-10-01','2026-10-02','2026-10-05']
        panel=pd.DataFrame([dict(date=d,code='0050',open=100,close=100) for d in days]).set_index(['date','code'])
        intents={days[0]:dict(weights={'0050':1})};versions=pd.Series('E22_v2s_tw',index=days)
        short=counterfactual(POLICIES[2],days[:2],intents,1_000_000,panel,[],versions)
        full=counterfactual(POLICIES[2],days,intents,1_000_000,panel,[],versions)
        self.assertEqual(short[2].fills,full[2].fills)
        self.assertEqual(full[2].fills[0]['fill_date'],days[1])
        self.assertGreaterEqual(full[2].cash,100000)
        self.assertEqual(short[0].nav.tolist(),full[0].nav.iloc[:2].tolist())

if __name__=='__main__':unittest.main()
