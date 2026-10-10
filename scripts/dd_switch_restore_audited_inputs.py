#!/usr/bin/env python3
"""Restore only missing research inputs after matching their original audited hashes.

No strategy execution, canonical market edits, network requests or hash updates.
The CSV serialization round trip mirrors dd_switch_seven_session_rebuild.py.
"""
import hashlib
import io
import json
import subprocess
import zipfile
from pathlib import Path

import pandas as pd

from dd_switch_session_market import attach_off, raw_response, repair_equity

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'repro/dd-switch-full-history-audit'
REFS = {
    'parents': 'f73c1ba1f48d77b4728ce510da97ae8a0885038e',
    'mothers': '5449f76b3a3feba434f40e0c5e10483e32c00b44',
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    expected = json.loads((OUT / 'audited_input_sha256.json').read_text())
    live_path = ROOT / 'forward/e21/live_market.csv'
    assert sha(live_path.read_bytes()) == expected[str(live_path.relative_to(ROOT))]
    release = ROOT / 'repro/dd-switch-seven-session-complete-release'
    source_hashes = json.loads((release / 'inputs/manifest.json').read_text())['source_sha256']
    annual = {}
    annual_rows = json.loads((OUT / 'source_manifest.json').read_text())
    with zipfile.ZipFile(OUT / 'sources_evidence.zip') as archive:
        for row in annual_rows:
            if row['status'] != 'FETCHED':
                continue
            rel = row['path']
            raw = archive.read(str((ROOT / rel).relative_to(OUT)))
            assert sha(raw) == row['sha256'], rel
            annual[rel] = raw
    off_source = release / 'runtime/generations/corrected-complete/off.csv'
    off_rel = 'repro/dd-switch-seven-session-rebuild/inputs/00631L_actual.csv'
    candidates = {off_rel: off_source.read_bytes()}
    sources = {str(off_source.relative_to(ROOT)): sha(candidates[off_rel])}
    live = pd.read_csv(live_path, dtype={'code': str}, parse_dates=['date'])
    base = ROOT / 'data/def_proxies/00631L_ohlcv.csv'
    latest = release / 'sources/00631L_latest.json'
    off = pd.read_csv(base, dtype={'code': str}, parse_dates=['date'])
    extra = raw_response(latest)
    extra['adj_close'] = extra.close
    off = pd.concat([off, extra[~extra.date.isin(off.date)]], ignore_index=True).sort_values('date')
    assert sha(off.to_csv(index=False).encode()) == expected[off_rel]
    sources.update({str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in (base, latest, live_path)})
    dependencies = list((ROOT / 'repro/dd-switch-history-gap-recovery/sources').glob('*.json'))
    dependencies += list((ROOT / 'data/telecom_0050_complete').glob('*_2010_latest_ohlcv.csv'))
    dependencies += [ROOT / 'forward/e9/e9_telecom_adjusted.csv', ROOT / 'forward/e10s2/e10s2_0050_adjusted.csv']
    dependencies += [Path(__file__), ROOT / 'scripts/dd_switch_session_market.py']
    sources.update({str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in dependencies})
    for kind, ref in REFS.items():
        identity = ref + ':forward/e21/live_market.csv'
        raw = subprocess.check_output(['git', 'show', identity], cwd=ROOT)
        assert sha(raw) == source_hashes[identity], identity
        sources[identity] = sha(raw)
        original = pd.read_csv(io.BytesIO(raw), dtype={'code': str}, parse_dates=['date'])
        market = repair_equity(original, live, ROOT)
        market = pd.read_csv(io.StringIO(market.to_csv(index=False)), dtype={'code': str}, parse_dates=['date'])
        attached, _ = attach_off(market, off)
        candidates[f'repro/dd-switch-seven-session-rebuild/inputs/{kind}_with_off.csv'] = attached.to_csv(index=False).encode()
    archived = {}
    artifact_hashes = json.loads((release / 'artifact_sha256.json').read_text())
    prior_nav_hashes = {r['path']: r['sha256'] for r in json.loads((OUT / 'nav_coverage.json').read_text())}
    for kind in REFS:
        for source in sorted((release / kind).glob('*.csv')):
            if not source.name.startswith(('nav_', 'fills_')):
                continue
            raw = source.read_bytes()
            assert sha(raw) == artifact_hashes[str(source.relative_to(release))], source
            rel = f'repro/dd-switch-seven-session-rebuild/{kind}/{source.name}'
            if source.name.startswith('nav_'):
                assert sha(raw) == prior_nav_hashes[rel], rel
            archived[rel] = raw
            sources[str(source.relative_to(ROOT))] = sha(raw)
    assert len(archived) == 14, 'Expected nine saved NAVs and five fill artifacts'
    # Validate all three before writing any file. Existing files must also match.
    for rel, raw in candidates.items():
        assert sha(raw) == expected[rel], rel
    all_restored = {**candidates, **archived, **annual}
    for rel, raw in all_restored.items():
        if (ROOT / rel).exists():
            assert sha((ROOT / rel).read_bytes()) == sha(raw), rel
    for rel, raw in all_restored.items():
        path = ROOT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_bytes(raw)
    result = dict(status='RESTORED_EXACT_AUDITED_HASHES', inputs={r: sha(b) for r, b in candidates.items()},
                  archived_outputs={r: sha(b) for r, b in archived.items()},
                  annual_snapshot_hashes={r: sha(b) for r, b in annual.items()},
                  source_sha256=sources, strategy_executed=False, canonical_modified=False,
                  method='Original input-only construction; exact original SHA256 required for every restored CSV')
    (OUT / 'audited_input_restoration.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
