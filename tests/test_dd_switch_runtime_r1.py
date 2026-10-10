import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import pandas as pd
from dd_switch_runtime import preflight, inputs
from live_fill_core import _exact_t1_stats, _iter_pending
from t0_carve_fin_sat_switch import CARVE_OUT_ID, authorize_same_bar_fill
from e21_qc import exact_t1_from_fills

class RuntimeGuards(unittest.TestCase):
    def test_stale_and_corrupt_inputs_are_blocked(self):
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ, {'E21_DD_INPUTS_DIR':d}):
            root=Path(d); gen=root/'generations/a';gen.mkdir(parents=True)
            f=gen/'nav.csv';f.write_text('date,nav\n2026-10-08,100\n')
            meta=dict(asof='2026-10-08',generation='generations/a',files={'l4':'nav.csv'},hashes={'l4':hashlib.sha256(f.read_bytes()).hexdigest()})
            (root/'current.json').write_text(json.dumps(meta))
            self.assertTrue(preflight('2026-10-08')['ok'])
            with self.assertRaisesRegex(RuntimeError,'stale'):preflight('2026-10-09')
            f.write_text('date,nav\n2026-10-08,101\n')
            with self.assertRaisesRegex(RuntimeError,'checksum'):preflight('2026-10-08')
            meta['files']['l4']='../../escape.csv';(root/'current.json').write_text(json.dumps(meta))
            with self.assertRaisesRegex(RuntimeError,'outside'):inputs()

    def test_t0_tag_never_allows_before_signal_or_t1_same_day(self):
        rows=[dict(signal_date='2026-10-08',fill_date='2026-10-07',carve_out_id=CARVE_OUT_ID)]
        self.assertFalse(_exact_t1_stats(rows,carve_authorized=True)[1])
        rows[0].update(fill_date='2026-10-08',execution_clock='NEXT_SESSION_OPEN')
        self.assertFalse(authorize_same_bar_fill(rows[0],authorized=True))
        self.assertFalse(_exact_t1_stats(rows,carve_authorized=True)[1])
        with patch('t0_carve_fin_sat_switch.is_live_fill_authorized',return_value=True):
            self.assertFalse(exact_t1_from_fills(pd.DataFrame(rows))['exact_t1_ok'])

    def test_t1_tag_waits_over_weekend(self):
        with tempfile.TemporaryDirectory() as d:
            pd.DataFrame([dict(order_id='x',signal_date='2026-10-02',code='2880',side='BUY',quantity=1000,carve_out_id=CARVE_OUT_ID,execution_clock='NEXT_SESSION_OPEN')]).to_csv(Path(d)/'orders.csv',index=False)
            self.assertTrue(_iter_pending(Path(d),pd.Timestamp('2026-10-02'),carve_authorized=True).empty)
            self.assertEqual(len(_iter_pending(Path(d),pd.Timestamp('2026-10-05'),carve_authorized=True)),1)

if __name__=='__main__':unittest.main()

class CorporateActionGuards(unittest.TestCase):
    def test_halt_has_no_fill_and_split_changes_units_without_cash_credit(self):
        from dd_switch_rebuild import Book, advance, FIN, TEL
        book=Book({'00631L':1000},100000,pending=[dict(order_id='off',signal_date='2026-03-24',code='00631L',side='BUY',quantity=1000,reference_close=443.15)])
        advance(book,pd.Timestamp('2026-03-25'),{}, {**{c:1 for c in FIN+TEL}, '00631L':443.15}, [])
        self.assertEqual(book.fills,[])
        self.assertEqual(book.pos['00631L'],1000)
        advance(book,pd.Timestamp('2026-03-31'),{'00631L':19.67},{**{c:1 for c in FIN+TEL}, '00631L':19.26},[])
        self.assertEqual(book.pos['00631L'],22000)
        self.assertEqual(book.pending[0]['quantity'],22000)
        self.assertEqual(book.cash,100000)
