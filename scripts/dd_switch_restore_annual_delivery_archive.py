#!/usr/bin/env python3
"""Reassemble the exact hashed issuer-evidence ZIP from committed, resumable parts."""
import hashlib,json
from pathlib import Path
OUT=Path(__file__).resolve().parents[1]/'repro/dd-switch-full-history-audit'
def main():
    manifest=json.loads((OUT/'issuer_annual_delivery_archive_parts.json').read_text())
    assert manifest['archive_name']=='issuer_annual_delivery_capture_delta.zip'
    chunks=[]
    for i,part in enumerate(manifest['parts'],1):
        assert part['name']==manifest['archive_name']+f'.part{i:03}'
        data=(OUT/part['name']).read_bytes()
        assert len(data)==part['size'],part['name']
        assert hashlib.sha256(data).hexdigest()==part['sha256'],part['name']
        chunks.append(data)
    raw=b''.join(chunks)
    assert len(raw)==manifest['archive_bytes']
    assert hashlib.sha256(raw).hexdigest()==manifest['archive_sha256']
    target=OUT/manifest['archive_name'];temporary=target.with_suffix('.zip.tmp')
    temporary.write_bytes(raw);temporary.replace(target)
    print(f"Verified {len(chunks)} parts; archive SHA256 {manifest['archive_sha256']}")
if __name__=='__main__':main()
