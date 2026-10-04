# TIPSOFT_IP3_Y2020_CRISIS_SIGNAL_REFINE_STAGEA_SCREEN

Date: 2026-10-04 · Verdict: **`IP3_Y2020_CRISIS_SIGNAL_REFINE_HIT`** · top=**`and::rvol63_l4&fuse_prem_neg5`**
Register: **0kbi** · **SIGNAL_REFINE_PARALLEL** · n=200 · HIT=12 · WEAK=129 · OVERFIT=27 · NO_EDGE=32

## Meta

- base `L4_LIVE_P3_WITHIN` `repro/research-live-align-gap-stagea/outputs/nav_L4_LIVE_P3_WITHIN.csv` · soft `L1_SOFT_T1`
- Mar2020 2020-02-20→2020-03-23 · floors from 0kbh (no tighten)
- skipped parent detectors: VIX proxy (no data file), breadth (no series available)

## Floors (0kbh)

- |IC|≥**0.08** · hit(H1'20)≥**0.58** · recall(Mar)≥**0.35** · lead≥**3.0**d · FA≠2020≤**0.12** · OOS|IC|≥**0.05** · year-dummy|IC|<**0.55**

## vs 0kbh champ

- 0kbh: `rvol20_l4` IC **0.1249** · hit **0.5172** · lead **32.0**d
- refine: `and::rvol63_l4&fuse_prem_neg5` IC **0.1776** · hit **0.6724** · lead **21.0**d
- Δ IC **0.0527** · Δ hit **0.1552** · SIGNAL_HIT achieved **True**

## Family counts

| Family | n | HIT | WEAK | OVERFIT | NO_EDGE |
|---|---:|---:|---:|---:|---:|
| adaptive_threshold | 18 | 0 | 9 | 1 | 8 |
| and_combo | 58 | 2 | 32 | 13 | 11 |
| baseline | 12 | 0 | 12 | 0 | 0 |
| dual_horizon | 16 | 0 | 13 | 2 | 1 |
| episode | 24 | 0 | 14 | 5 | 5 |
| k_confirm | 16 | 2 | 9 | 0 | 5 |
| or_combo | 56 | 8 | 40 | 6 | 2 |

## Top refine arms

| Arm | Family | IC(sp) | IC OOS | hit(Mar) | recall | lead d | FA≠2020 | verdict |
|---|---|---:|---:|---:|---:|---:|---:|---|
| and::rvol63_l4&fuse_prem_neg5 | and_combo | 0.1776 | 0.1725 | 0.6724 | 0.5 | 21.0 | 0.091 | SIGNAL_HIT |
| or::rvol20_l4|atr_like_20 | or_combo | 0.1764 | 0.1718 | 0.5948 | 0.5 | 32.0 | 0.0891 | SIGNAL_HIT |
| or::rvol20_l4|dd63_l4 | or_combo | 0.1047 | 0.0972 | 0.6293 | 0.7273 | 32.0 | 0.0897 | SIGNAL_HIT |
| or::rvol20_l4|fuse_prem_neg5 | or_combo | 0.0868 | 0.067 | 0.6379 | 0.6818 | 32.0 | 0.09 | SIGNAL_HIT |
| or::neg_gap_ma200|fuse_prem_neg5 | or_combo | 0.109 | 0.0787 | 0.8017 | 0.4091 | 12.0 | 0.0996 | SIGNAL_HIT |
| or::atr_like_20|dd63_l4 | or_combo | 0.1157 | 0.1054 | 0.6983 | 0.4545 | 13.0 | 0.0961 | SIGNAL_HIT |
| or::neg_gap_ma200|dd63_l4 | or_combo | 0.0956 | 0.0775 | 0.7414 | 0.4545 | 13.0 | 0.0971 | SIGNAL_HIT |
| or::cool_defend_l1|fuse_prem_neg5 | or_combo | 0.0969 | 0.1003 | 0.7414 | 0.4091 | 12.0 | 0.0958 | SIGNAL_HIT |
| andflag::fuse_neg_flag&fuse_prem_neg5 | and_combo | 0.0875 | 0.0697 | 0.7414 | 0.4091 | 12.0 | 0.0958 | SIGNAL_HIT |
| or::atr_like_20|fuse_prem_neg5 | or_combo | 0.0854 | 0.0767 | 0.7155 | 0.4091 | 12.0 | 0.0968 | SIGNAL_HIT |
| kconfirm2::fuse_prem_neg5 | k_confirm | 0.0851 | 0.0706 | 0.7586 | 0.3636 | 11.0 | 0.0567 | SIGNAL_HIT |
| kconfirm2::fuse_neg_flag | k_confirm | 0.0825 | 0.0651 | 0.7586 | 0.3636 | 11.0 | 0.0734 | SIGNAL_HIT |
| and::fuse_neg_flag&rvol63_l4 | and_combo | 0.2015 | 0.2038 | 0.3103 | 1.0 | 32.0 | 0.5482 | SIGNAL_WEAK |
| and::rvol20_l4&atr_like_20&fuse_neg_flag | and_combo | 0.1389 | 0.1273 | 0.4655 | 0.8636 | 32.0 | 0.3839 | SIGNAL_WEAK |
| and::rvol20_l4&fuse_neg_flag | and_combo | 0.1351 | 0.1268 | 0.4569 | 0.8636 | 32.0 | 0.5533 | SIGNAL_WEAK |
| or::rvol20_l4|fuse_neg_flag | or_combo | 0.1274 | 0.1191 | 0.5948 | 0.6818 | 32.0 | 0.1653 | SIGNAL_WEAK |
| and::atr_like_20&fuse_neg_flag | and_combo | 0.1424 | 0.1303 | 0.319 | 1.0 | 32.0 | 0.5396 | SIGNAL_WEAK |
| adapt_p90::atr_like_20 | adaptive_threshold | 0.0783 | 0.0674 | 0.6983 | 0.9545 | 32.0 | 0.1637 | SIGNAL_WEAK |
| adapt_p80::atr_like_20 | adaptive_threshold | 0.085 | 0.0749 | 0.5086 | 1.0 | 32.0 | 0.264 | SIGNAL_WEAK |
| orflag::neg_gap_ma200|dd63_l4 | or_combo | 0.0907 | 0.0898 | 0.7155 | 0.5909 | 20.0 | 0.183 | SIGNAL_WEAK |

## Best by family

- **adaptive_threshold**: `adapt_p90::atr_like_20` IC=0.0783 hit=0.6983 lead=32.0 · SIGNAL_WEAK
- **and_combo**: `and::fuse_neg_flag&rvol63_l4` IC=0.2015 hit=0.3103 lead=32.0 · SIGNAL_WEAK
- **baseline**: `base::rvol20_l4` IC=0.1249 hit=0.5172 lead=32.0 · SIGNAL_WEAK
- **dual_horizon**: `dual_mdd::rvol20_l4` IC=0.1301 hit=0.5172 lead=32.0 · SIGNAL_WEAK
- **episode**: `episode_h10::rvol20_l4` IC=0.0667 hit=0.5172 lead=32.0 · SIGNAL_WEAK
- **k_confirm**: `kconfirm2::fuse_prem_neg5` IC=0.0851 hit=0.7586 lead=11.0 · SIGNAL_HIT
- **or_combo**: `or::rvol20_l4|atr_like_20` IC=0.1764 hit=0.5948 lead=32.0 · SIGNAL_HIT

## Optimize / disposition

1. Objective: refine 0kbh WEAK singles → try SIGNAL_HIT via combo/confirm/adapt/dual/episode
2. Top `and::rvol63_l4&fuse_prem_neg5` family=and_combo IC=0.1776 hit(Mar)=0.6724 lead=21.0d FA≠2020=0.091 verdict=SIGNAL_HIT
3. vs 0kbh champ `rvol20_l4`: IC Δ=0.0527 · hit Δ=0.1552 · SIGNAL_HIT achieved=True
4. Clears: HIT=12 · WEAK=129 · OVERFIT=27 · NO_EDGE=32 / n=200
5. Families: baseline · and/or_combo · k_confirm · adaptive_threshold · dual_horizon · episode
6. **SIGNAL_REFINE / PARALLEL** — detection only; **signal ≠ apply**
7. Does **not** unlock soak freeze · does **not** recommend LIVE wire
8. No tip Soft promote · no year-oracle · Soft KEEP · Path4 OFF · broker false
9. Floors reused from 0kbh for comparability (no tighten)
10. Refine cleared SIGNAL_HIT floors — still **no LIVE apply**; next would be observe-only ballot if human wants (SOAK freeze unchanged)
11. Caution: multi-arm screen (~200) — HIT is floor-clear detection, not LIVE prove; prefer interpretable arms (k-confirm / simple AND) before any observe draft

Repro: `PYTHONPATH=scripts python3 scripts/tipsoft_ip3_y2020_crisis_signal_refine_stagea.py`

Label: `TIPSOFT_IP3_Y2020_CRISIS_SIGNAL_REFINE_STAGEA_SCREEN_2026-10-04__IP3_Y2020_CRISIS_SIGNAL_REFINE_HIT__SIGNAL_REFINE_PARALLEL`
