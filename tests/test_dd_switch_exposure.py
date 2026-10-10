import unittest
import pandas as pd
from types import SimpleNamespace
from dd_switch_exposure_pipeline import stage_delta
from dd_switch_exposure_research import clock_price
class ExposureTests(unittest.TestCase):
    def test_staging_toward_zero_board_lots(self):
        self.assertEqual(stage_delta({'a':3006000,'b':-1324000,'c':1000},2),{'a':1503000.,'b':-662000.})
    def test_book_flip_not_delayed(self):
        self.assertEqual(stage_delta({'a':-1000},3,True),{'a':-1000})
    def test_last_stage_uses_entire_new_delta(self):
        self.assertEqual(stage_delta({'a':-17000},1),{'a':-17000})
    def test_close_reference_uses_signal_date_and_sell_slip(self):
        panel=pd.DataFrame([{'date':'2026-09-30','code':'2880','open':44.,'close':45.},{'date':'2026-10-01','code':'2880','open':46.,'close':47.}]).set_index(['date','code'])
        row=SimpleNamespace(signal_date='2026-09-30',fill_date='2026-10-01',code='2880',side='SELL',slippage_bp=5)
        self.assertEqual(clock_price(panel,row,'signal_close'),('2026-09-30',45.*.9995))
        self.assertEqual(clock_price(panel,row,'next_open'),('2026-10-01',46.*.9995))
if __name__=='__main__':unittest.main()
