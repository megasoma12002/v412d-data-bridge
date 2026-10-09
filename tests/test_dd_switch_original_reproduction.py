import unittest
import pandas as pd
from dd_switch_original_reproduction import normalize_signal,compare
from live_path3_t0_switch_emitter import BOOK_COMP,BOOK_SAT

class OriginalReproductionTest(unittest.TestCase):
    def test_observe_csv_without_book_keeps_sat_decision(self):
        signal=pd.DataFrame({'date':pd.to_datetime(['2026-09-28','2026-09-29']),
                             'sat_lead':[False,True],'w_sat':[0.,1.]})
        result=normalize_signal(signal)
        self.assertEqual(result.book.tolist(),[BOOK_COMP,BOOK_SAT])
        self.assertNotIn('book',signal)

    def test_prefix_comparison_normalizes_dates_and_rejects_missing_days(self):
        old=pd.DataFrame({'date':pd.to_datetime(['2026-09-28','2026-09-29']),'nav':[100.,101.]})
        new=pd.DataFrame({'date':['2026-09-28','2026-09-29','2026-09-30'],'nav':[100.,101.,102.]})
        self.assertTrue(compare(old,new)['pass_parity'])
        self.assertFalse(compare(old,new.iloc[[1,2]])['pass_parity'])
        new.loc[1,'nav']=102.
        result=compare(old,new)
        self.assertFalse(result['pass_parity'])
        self.assertEqual(result['first_mismatch'],'2026-09-29')

if __name__=='__main__':unittest.main()
