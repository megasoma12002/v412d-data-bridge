# Offense SELL_a75 — Near-flat floor +0.15 rescore (paper policy)

Date: 2026-09-26  
Status: **NEAR_FLAT_HIT** under human ACCEPT floor  
Human: `ACCEPT near-flat: SELL_a75 under COOL (CAGR floor +0.15)`  
Soft-Frozen · COOL_c8 **KEEP** · live wire **false**

## Gate change (policy only — no re-sim)

| Gate | Stage A charter | After ACCEPT |
|---|---|---|
| held CAGR↑ floor | +0.20 pp | **+0.15 pp** (this champion only) |
| held \|MDD\| band | ≤ 15% | unchanged |
| tip YTD/1y MDD | not worse than base | unchanged |

## Champion (Stage A screen)

| id | held CAGR↑ | held MDD↑ | in band | tip | Stage A | After floor |
|---|---:|---:|:---:|:---:|---|---|
| `SELL_a75` | **+0.17** | **−0.04** | Y | Y | SOFT | **NEAR_FLAT_HIT** |

Control check: `SLEEVE_a0250` (+0.08) / `SELL_a25` (+0.04) still **below** +0.15 → remain SOFT (not promoted).

## Binding

- Paper observe policy only  
- Live Soft sell amp stays default until dedicated cutover ACCEPT  
- Do not retune Soft/Sleeve grid after sealed peek  

## Refs

- Screen: `OFFENSE_CAGR_UNDER_COOL_STAGEA_SCREEN.{md,json}`  
- Ballot: `OFFENSE_SELL_A75_NEAR_FLAT_ACCEPT_BALLOT_EXECUTED.md`

Label: `OFFENSE_SELL_A75_NEAR_FLAT_FLOOR015_RESCORE_2026-09-26__NEAR_FLAT_HIT`
