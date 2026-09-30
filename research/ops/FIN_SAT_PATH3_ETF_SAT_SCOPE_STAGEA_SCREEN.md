# FIN_SAT_PATH3_ETF_SAT_SCOPE_STAGEA_SCREEN

Date: 2026-09-30 · Verdict: **`ETF_DIVERGES__SATELLITE_OVERLAY_BLOCK`**
Register: **0kad** · ledger panel end: `2026-09-24` · live state: `2026-09-29` · flips: 199

## Divergence (COMP − SAT shares)

| Code | % days differ | flip % nz | tip Δ shares | max |Δ| |
|---|---:|---:|---:|---:|
| `0050` | 99.3% | 100.0% | 130000 | 3422000 |
| `00631L` | 29.8% | 37.7% | 0 | 7430000 |
| `2880` | 100.0% | 100.0% | -2402961 | 31692857 |
| `2412` | 99.7% | 100.0% | -261000 | 1301000 |

## keep_0050=False probes (last flip each way)

- **COMP→SAT** @2026-06-12 → `SAT_A20_RELAX` · keep=True n_delta=7 · keep=False n_delta=7 · Δ0050=None
- **SAT→COMP** @2026-05-20 → `COMP_H150_x_A20` · keep=True n_delta=7 · keep=False n_delta=7 · Δ0050=None

## Satellite

- `00631L` in ledger: **True** · in Path3 recon today: **False**
- Owner today: COOL / Soft satellite overlay (not Path3 sleeve recon)
- Direct Path3 apply blocked until overlay re-home

## Engine note

- `keep_0050=False` under freeze-sleeve-$ is a **no-op** for single-name ETF (mix≡1 → same live ETF $). ETF Path3 needs a new policy.

Repro: `PYTHONPATH=scripts python3 scripts/fin_sat_path3_etf_sat_scope_stagea.py`

Label: `FIN_SAT_PATH3_ETF_SAT_SCOPE_STAGEA_SCREEN_2026-09-30__ETF_DIVERGES__SATELLITE_OVERLAY_BLOCK`
