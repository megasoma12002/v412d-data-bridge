import hashlib,json,os,tempfile,unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import pandas as pd
from dd_switch_daily_refresh import publish_verified_runtime,KEYS,VERSION
from dd_switch_original_inputs import append_market,append_dividends
from live_dd_handoff import prepare_handoff
from live_order_lifecycle import prepare_order_events,write_order_lifecycle
from live_fill_core import _iter_pending,_paper_fill_rows
from live_session_io import assert_session_preflight
from e21_forward_range import pending_sessions

class LiveRepair(unittest.TestCase):
    def fixture_runtime(self,root):
        generation=root/'generations/source';generation.mkdir(parents=True)
        files={k:k+'.csv' for k in KEYS};hashes={}
        for key,name in files.items():
            target=generation/name;target.write_text('date,nav\n2026-10-08,100\n')
            hashes[key]=hashlib.sha256(target.read_bytes()).hexdigest()
        cert=dict(status='ORIGINAL_RESEARCH_PREFIX_REPRODUCED_AND_APPEND_ONLY_EXTENDED',
            construction_refs=dict(live_stack='5449f76b3a3feba434f40e0c5e10483e32c00b44',
                upper_layers='97933be85192e8d0ef89695be0c292342bba694d',parent_ledgers='f73c1ba1f48d77b4728ce510da97ae8a0885038e'),
            prefix_gate_disagreement={'active':0},parent_max_share_difference=0,mother_max_relative_error=1e-15)
        meta=dict(version='DD_SWITCH_ORIGINAL_LINEAGE_T1_RESEARCH',original_research_preserved=True,
            certification=cert,asof='2026-10-08',generation='generations/source',files=files,hashes=hashes)
        (root/'current.json').write_text(json.dumps(meta));return meta

    def test_atomic_publication_and_bad_source_keeps_pointer(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);source=root/'source';dest=root/'published';meta=self.fixture_runtime(source)
            result=publish_verified_runtime(source,dest,'2026-10-08');self.assertEqual(result['version'],VERSION)
            before=(dest/'current.json').read_bytes()
            (source/meta['generation']/meta['files']['l4']).write_text('corrupt')
            with self.assertRaisesRegex(RuntimeError,'checksum'):publish_verified_runtime(source,dest,'2026-10-08')
            self.assertEqual(before,(dest/'current.json').read_bytes())
    def test_missing_prefix_certificate_cannot_publish(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);meta=self.fixture_runtime(root/'source');meta.pop('certification')
            (root/'source/current.json').write_text(json.dumps(meta))
            with self.assertRaisesRegex(ValueError,'certification'):publish_verified_runtime(root/'source',root/'dest','2026-10-08')
            self.assertFalse((root/'dest/current.json').exists())
    def test_new_daily_generation_cannot_revise_published_prefix(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);meta=self.fixture_runtime(root/'source')
            publish_verified_runtime(root/'source',root/'dest','2026-10-08')
            before=(root/'dest/current.json').read_bytes();meta['asof']='2026-10-09'
            for key,name in meta['files'].items():
                target=root/'source'/meta['generation']/name
                target.write_text('date,nav\n2026-10-08,101\n2026-10-09,102\n')
                meta['hashes'][key]=hashlib.sha256(target.read_bytes()).hexdigest()
            (root/'source/current.json').write_text(json.dumps(meta))
            with self.assertRaisesRegex(ValueError,'prefix revised'):
                publish_verified_runtime(root/'source',root/'dest','2026-10-09')
            self.assertEqual(before,(root/'dest/current.json').read_bytes())
    def test_canonical_runtime_rejects_research_and_requires_all_inputs(self):
        from dd_switch_runtime import preflight
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);meta=self.fixture_runtime(root)
            with patch('dd_switch_runtime.DEFAULT_DIR',root),patch.dict(os.environ,{'E21_DD_INPUTS_DIR':str(root)}):
                with self.assertRaisesRegex(RuntimeError,'certified original daily'):preflight('2026-10-08')
                meta.update(version=VERSION,prefix_certified=True);(root/'current.json').write_text(json.dumps(meta))
                self.assertTrue(preflight('2026-10-08')['ok'])
                meta['files'].pop('signal');(root/'current.json').write_text(json.dumps(meta))
                with self.assertRaisesRegex(RuntimeError,'complete original inputs'):preflight('2026-10-08')
    def test_canonical_forward_override_cannot_feed_R1_before_any_features(self):
        import e21_forward_pipeline as pipeline
        args=SimpleNamespace(asof='2026-10-08')
        with patch('e21_forward_pipeline.load_market_session',return_value=(None,pd.Timestamp('2026-10-08'),None)), \
             patch('dd_switch_runtime.preflight',return_value={'version':'R1','prefix_certified':True}), \
             patch('e21_forward_pipeline.features') as features:
            with self.assertRaisesRegex(RuntimeError,'Canonical forward'):
                pipeline._run_locked_session(args,pipeline.CANON_STATE,pipeline.CANON_MARKET,'paper')
            features.assert_not_called()
    def test_append_never_revises_prefix(self):
        original=pd.DataFrame([dict(date=pd.Timestamp('2026-09-29'),code='2880',close=10)])
        tip=pd.DataFrame([dict(date=pd.Timestamp('2026-09-29'),code='2880',close=999),
                          dict(date=pd.Timestamp('2026-09-30'),code='2880',close=11)])
        result=append_market(original,tip,'2026-09-30');self.assertEqual(result.close.tolist(),[10,11])
    def test_empty_postcutoff_dividends_preserve_columns(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);frame=pd.DataFrame([dict(code='2880',fiscal_year='114',announcement_date='2026-07-01',cash_ex_date='2026-08-01',stock_ex_date='2026-08-01')])
            frame.to_csv(root/'original.csv',index=False);frame.to_csv(root/'current.csv',index=False)
            out=append_dividends(root/'original.csv',root/'current.csv',root/'out.csv','2026-10-08')
            self.assertEqual(pd.read_csv(out).columns.tolist(),frame.columns.tolist())
    def test_invalid_replacement_stops_before_suppressing_soft(self):
        from live_day_overlays import apply_path3_tipsoft_overlays
        with patch('live_path3_t0_weight_engine.plan_or_none_for_pipeline',return_value=(None,{'reason':'ledger_stale'})), \
             patch('live_path3_strategy_cutover.suppress_soft_fin_tel') as mute:
            with self.assertRaisesRegex(RuntimeError,'ledger_stale'):
                apply_path3_tipsoft_overlays([],asof=pd.Timestamp('2026-10-01'),pos={},prices={})
            mute.assert_not_called()
    def test_daily_price_append_does_not_backfill_frozen_research_gap(self):
        from dd_switch_rebuild import refresh_off
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            bars=pd.DataFrame([dict(date=d,code='00631L',open=10.,high=10.,low=10.,close=10.,adj_close=10.,volume=1.) for d in ['2026-09-28','2026-09-30']])
            bars.to_csv(root/'base.csv',index=False)
            pd.DataFrame({'date':['2026-09-28','2026-09-29','2026-09-30']}).to_csv(root/'market.csv',index=False)
            with patch('urllib.request.urlopen',side_effect=AssertionError('Frozen gap must not download')):
                result=refresh_off(pd.Timestamp('2026-09-30'),root,base_path=root/'base.csv',calendar_path=root/'market.csv',append_after='2026-09-29')
            self.assertEqual(result.date.dt.strftime('%F').tolist(),['2026-09-28','2026-09-30'])
    def test_handoff_same_day_orders_and_prior_fills_positions(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'current.json').write_text('{}')
            gate=dict(ok=True,asof='2026-10-01',path3_active=True)
            overlay=SimpleNamespace(path3_cutover_meta={'applied':True},path3_weight_meta=dict(
                ledger_asof='2026-10-01',delta_shares={'2880':-1000.},switch={'book':'SAT'},tipsoft_dd_switch={'gate':gate}))
            orders=[dict(order_id='2026-10-01-2880-SELL-P3T0',code='2880',side='SELL',quantity=1000.,execution_clock='NEXT_SESSION_OPEN')]
            result=prepare_handoff({},'2026-10-01',{'2880':2000.},500.,overlay,orders,root)
            self.assertEqual(result['positions_after_prior_open_fills'],{'2880':2000.})
            self.assertEqual(result['status'],'T1_ORDERS_SCHEDULED')
            orders[0]['execution_clock']='SAME_BAR'
            with self.assertRaisesRegex(RuntimeError,r'T\+1'):prepare_handoff({},'2026-10-01',{'2880':2000.},500.,overlay,orders,root)
    def test_legacy_partial_cancelled_without_resurrecting_old_target(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            pd.DataFrame([dict(order_id='old',signal_date='2026-09-03',code='5880',side='BUY',quantity=101000)]).to_csv(root/'orders.csv',index=False)
            pd.DataFrame([dict(fill_id='old',quantity=91000)]).to_csv(root/'fills.csv',index=False)
            events=prepare_order_events(root,'2026-10-01',[],[],True)
            self.assertEqual(events[0]['cancelled_quantity'],10000)
            self.assertEqual(events[0]['status'],'CANCELLED_LEGACY_PARTIAL_REMAINDER')
            pd.DataFrame(events).to_csv(root/'order_events.csv',index=False)
            self.assertTrue(_iter_pending(root,pd.Timestamp('2026-10-02'),carve_authorized=False).empty)
            write_order_lifecycle(root,'2026-10-01');self.assertEqual(pd.read_csv(root/'order_lifecycle.csv').iloc[0].remainder,10000)
    def test_unfunded_buy_retained_then_current_target_replaces_it(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);order=dict(order_id='old',signal_date='2026-10-01',code='2880',side='BUY',quantity=2000)
            pd.DataFrame([order]).to_csv(root/'orders.csv',index=False)
            pos,cash,fills=_paper_fill_rows(pending=pd.DataFrame([order]),latest=pd.Timestamp('2026-10-02'),open_prices={'2880':100.},pos={},cash=100001.,carve_authorized=False)
            self.assertEqual(fills,[]);self.assertEqual(cash,100001.)
            self.assertEqual(len(_iter_pending(root,pd.Timestamp('2026-10-02'),carve_authorized=False)),1)
            events=prepare_order_events(root,'2026-10-02',[],fills,True)
            pd.DataFrame(events).to_csv(root/'order_events.csv',index=False)
            self.assertTrue(_iter_pending(root,pd.Timestamp('2026-10-05'),carve_authorized=False).empty)
    def test_session_jump_rejected_and_range_includes_missing_monday(self):
        calendar=[date(2026,10,2),date(2026,10,5),date(2026,10,6)]
        with tempfile.TemporaryDirectory() as temp,patch('twse_session_sources.cached_load_calendar_window',return_value=(calendar,calendar)):
            with self.assertRaisesRegex(SystemExit,'2026-10-05'):
                assert_session_preflight(Path(temp),{'last_date':'2026-10-02'},pd.Timestamp('2026-10-06'))
        from live_ledger import ALL
        market=pd.DataFrame([dict(date=d,code=c,open=10.,close=10.,adj_close=10.) for d in ['2026-10-05','2026-10-06'] for c in ALL+['TAIEX']])
        self.assertEqual(pending_sessions('2026-10-02','2026-10-06',calendar,market),['2026-10-05','2026-10-06'])
        with self.assertRaisesRegex(ValueError,'2026-10-05'):
            pending_sessions('2026-10-02','2026-10-06',calendar,market[market.date=='2026-10-06'])

if __name__=='__main__':unittest.main()
