# TIPSOFT_IP3_CRISIS_SIGNAL_HIST_OOS_STAGEA_CHARTER

Date: 2026-10-04
Register: **0kbj** · Parents: 0kbi, 0kbh, 0kbf
Label: **SIGNAL_HIST_OOS_PARALLEL** · SOAK-SAFE parallel · **signal ≠ apply**

## Question

Do 0kbi SIGNAL_HIT refine arms (esp. champ `and::rvol63_l4&fuse_prem_neg5` and other HIT/k-confirm arms) still detect stress in **historical crisis windows** with lag-1 causal metrics, or are they 2020-only / overfit?

## Episodes (TWSE-relevant)

1. **GFC / 金融海嘯**: 2008-09 → 2009-03 (fail loud if missing)
2. **2015**: TW/China crash 2015-06 → 2015-09 (eval 2015-04→2015-10)
3. Optional: **2011** EU/US stress · **2018 Q4**
4. **Mar2020** kept as in-sample reference (selection window)

## Arms under test

- Champ: `and::rvol63_l4&fuse_prem_neg5`
- Other 0kbi SIGNAL_HIT arms (OR/AND/k-confirm) + `base::rvol20_l4` (0kbh)

## Metrics (detection only)

- IC vs fwd stress (`fwd_mdd_10` / `fwd_ret_crash_10`) in eval window
- hit / recall / F1 inside episode (eval-window balanced)
- median lead into local trough (L4 NAV, else 0050)
- FA rate in non-crisis years of same decade
- Per arm×episode: `OOS_HIT` / `OOS_WEAK` / `OOS_MISS` / `NO_DATA`

## Global verdict rule

- `IP3_CRISIS_SIGNAL_HIST_OOS_ROBUST` if champ clears OOS floors on ≥2 of {2008,2015}
- `…_PARTIAL` if one historical episode only
- `…_OVERFIT_2020` if strong on 2020 / weak-miss on available 2008&2015
- `…_NO_DATA` if history too short

## Hard constraints

- Soft KEEP · Path4 OFF · broker false · Exact T+1 lag-1
- **signal ≠ apply** · no LIVE · no tip Soft promote · no year-oracle
- no size-apply promote · soak freeze unchanged

Label: `TIPSOFT_IP3_CRISIS_SIGNAL_HIST_OOS_STAGEA_CHARTER_2026-10-04__SIGNAL_HIST_OOS_PARALLEL`
