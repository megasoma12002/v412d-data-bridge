# FIN_SAT_PATH3_ETF_RECON_POLICY_STAGEA_SCREEN

Date: 2026-09-30 · Verdict: **`ETF_POLICY_LEDGER_RATIO_HIT`**
Register: **0kae** · flips=199 · ledger_end=`2026-09-24` · live=`2026-09-29`

## Schedule COMP vs SAT: **RULED_OUT_IDENTICAL_COMP_SAT**

- identical=True

## Policy summary (flip days, live tip capital proxy)

| Policy | % flips trade 0050 | n traded | median |Δ| | max |Δ| |
|---|---:|---:|---:|---:|
| `KEEP` | 0.0% | 0 | 0 | 0 |
| `SCHEDULE_W` | 100.0% | 199 | 218000 | 347000 |
| `LEDGER_SOFT_RATIO` | 100.0% | 199 | 165000 | 940000 |

## Last flip legs

- **COMP→SAT** @2026-06-12 book=`SAT_A20_RELAX`
  - `KEEP` Δ0050=None
  - `SCHEDULE_W` Δ0050=333000.0
  - `LEDGER_SOFT_RATIO` Δ0050=242000.0
- **SAT→COMP** @2026-05-20 book=`COMP_H150_x_A20`
  - `KEEP` Δ0050=None
  - `SCHEDULE_W` Δ0050=333000.0
  - `LEDGER_SOFT_RATIO` Δ0050=311000.0

Repro: `PYTHONPATH=scripts python3 scripts/fin_sat_path3_etf_recon_policy_stagea.py`

Label: `FIN_SAT_PATH3_ETF_RECON_POLICY_STAGEA_SCREEN_2026-09-30__ETF_POLICY_LEDGER_RATIO_HIT`
