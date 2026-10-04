# TIPSOFT_IP3_Y2020_CRISIS_SIGNAL_STAGEA_SCREEN

Date: 2026-10-04 · Verdict: **`IP3_Y2020_CRISIS_SIGNAL_WEAK`** · top=**`rvol20_l4`**
Register: **0kbh** · **SIGNAL_PARALLEL** · n=20 · HIT=0 · WEAK=18 · NO_EDGE=2

## Meta

- base `L4_LIVE_P3_WITHIN` `repro/research-live-align-gap-stagea/outputs/nav_L4_LIVE_P3_WITHIN.csv` · soft `L1_SOFT_T1`
- Mar2020 2020-02-20→2020-03-23 · primary label `fwd_mdd_10`
- skipped: VIX proxy (no data file), breadth (no series available)

## Floors

- |IC|≥**0.08** · hit(H1'20)≥**0.58** · recall(Mar)≥**0.35** · lead≥**3.0**d · FA≠2020≤**0.12** · OOS|IC|≥**0.05** · year-dummy|IC|<**0.55**

## Parents

- 0kbg: 0kbg size overlays cut Mar MDD but held≪0. This pack measures the same crisis family as **signals** (IC/hit/lead) without exposure apply.
- 0kb4: Defend/FUSE knives on 0kb2 — different family from crisis signal detect.
- 0kbf: Soak freeze unchanged — signal Stage A does not unlock SOAK_PASS.

## Top detectors

| Detector | IC(sp) | IC OOS | hit(Mar) | F1(Mar) | lead d | FA≠2020 | yr-dummy | verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| rvol20_l4 | 0.1249 | 0.1193 | 0.5172 | 0.2 | 32.0 | 0.0865 | 0.1554 | SIGNAL_WEAK |
| atr_like_20 | 0.1425 | 0.1347 | 0.6466 | 0.2264 | 7.0 | 0.0958 | 0.2097 | SIGNAL_WEAK |
| fuse_neg_flag | 0.0723 | 0.0541 | 0.7328 | 0.3673 | 12.0 | 0.1256 | 0.048 | SIGNAL_WEAK |
| cool_defend_l1 | 0.1207 | 0.1406 | 0.4569 | 0.1818 | 10.0 | 0.1894 | 0.2284 | SIGNAL_WEAK |
| consec_down_mkt | 0.0329 | 0.0311 | 0.7845 | 0.4681 | 28.0 | 0.2057 | 0.0168 | SIGNAL_WEAK |
| below_ma200 | 0.0431 | 0.039 | 0.5431 | 0.3117 | 32.0 | 0.7091 | 0.0241 | SIGNAL_WEAK |
| below_ma120 | 0.0827 | 0.0904 | 0.4741 | 0.0896 | 32.0 | 0.6943 | 0.009 | SIGNAL_WEAK |
| fuse_prem_neg5 | 0.0301 | 0.0115 | 0.7414 | 0.375 | 12.0 | 0.0958 | 0.0209 | SIGNAL_WEAK |
| rvol63_l4 | 0.1581 | 0.1685 | 0.2931 | 0.0465 | 3.0 | 0.0868 | 0.2094 | SIGNAL_WEAK |
| proxy_mdd63_soft | 0.1085 | 0.1181 | 0.2759 | 0.087 | 5.0 | 0.0823 | 0.2453 | SIGNAL_WEAK |
| neg_gap_ma120 | 0.1225 | 0.1202 | 0.8103 | 0.0 | None | 0.0859 | 0.104 | SIGNAL_WEAK |
| rvol20_mkt | 0.0715 | 0.0618 | 0.6466 | 0.0889 | 3.0 | 0.1 | 0.143 | SIGNAL_WEAK |
| neg_gap_ma60 | 0.111 | 0.1293 | 0.7586 | 0.0 | None | 0.0872 | 0.0938 | SIGNAL_WEAK |
| neg_gap_ma200 | 0.0996 | 0.0866 | 0.8103 | 0.0 | None | 0.0942 | 0.1172 | SIGNAL_WEAK |
| dd63_l4 | 0.0083 | -0.0017 | 0.7155 | 0.4407 | 20.0 | 0.0916 | 0.1202 | SIGNAL_WEAK |

## Counterfactual (illustrative only)

- cash-gate on `rvol20_l4`: held **-4.9135** · Mar MDD↑ **2.3262** · cash days **9.98%**
- ILLUSTRATIVE ONLY — not HIT path; signal≠apply; no size-overlay promote

## Optimize / disposition

1. Objective: lag-1 causal detectors for Mar2020 / 2020 crisis stress — IC/hit/lead; no exposure apply
2. Top `rvol20_l4` IC=0.1249 hit(Mar)=0.5172 lead=32.0d FA≠2020=0.0865 verdict=SIGNAL_WEAK
3. Clears: SIGNAL_HIT=0 · SIGNAL_WEAK=18 · SIGNAL_NO_EDGE=2 / n=20
4. vs 0kbg: MDD_ONLY size overlays hurt held → signal-only fork
5. Disposition: signal≠apply · soak freeze unchanged · no LIVE wire · no tip Soft promote · no year-oracle
6. Soft KEEP · Path4 OFF · broker false · Exact T+1
7. Illustrative CF cash-gate: held=-4.9135 MarMDD↑=2.3262 (NOT HIT path)

Repro: `PYTHONPATH=scripts python3 scripts/tipsoft_ip3_y2020_crisis_signal_stagea.py`

Label: `TIPSOFT_IP3_Y2020_CRISIS_SIGNAL_STAGEA_SCREEN_2026-10-04__IP3_Y2020_CRISIS_SIGNAL_WEAK__SIGNAL_PARALLEL`
