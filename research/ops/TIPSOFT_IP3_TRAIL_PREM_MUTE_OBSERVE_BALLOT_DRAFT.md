# TIPSOFT_IP3_TRAIL_PREM_MUTE_OBSERVE_BALLOT_DRAFT

Date: 2026-09-30
Status: **DRAFT — awaiting human OPEN** · Soft KEEP · Path4 live OFF · hybrid T+0 carve **FORBIDDEN** · cutover **BLOCKED**

## Proposed human line

```
OPEN paper observe: TIPSOFT_P3_TRAIL_MUTE_W63_SAT (tip Soft Exact T+1 · NEARPEAK3 3-state · mute when lag63 prem_p3<-0.01 ∧ sat_lead · NOT hybrid T+0)
```

## Champion

- `MUTE_P3_W63_Tm001__S3_MUTESAT`
- tip Soft Exact T+1 Soft+FUSE+COOL base
- 3-state LIVE / P3 / P3+P4 on NEARPEAK3 · sat_lead
- Mute stack when lag-1 rolling 63d `prem_p3 < -0.01` **and** `sat_lead` (census-shaped)
- held vs NEARPEAK3 **+0.0704** pp · year regret↑ **+0.1355** · tipY vs live **+6.0402** · sealed **−0.0523**
- 0kb1 Stage A **`IP3_TRAIL_MUTE_HIT`** · strong clears **9**

## Non-goals

- Live wire / Soft-Frozen flip / hybrid T+0 carve / year-cut
- Replace 0kaw NEARPEAK3 observe without human OPEN
- Path4 live wire (0kay DRAFT remains separate)

## Evidence

- `TIPSOFT_IP3_TRAIL_PREM_MUTE_STAGEA_DECISION_PACK.md`
- Census: `repro/tipsoft-ip3-trail-prem-mute-stagea/outputs/live_win_episode_census.json`
- Repro NAV: `repro/tipsoft-ip3-trail-prem-mute-stagea/outputs/nav_MUTE_P3_W63_Tm001__S3_MUTESAT.csv`

Label: `TIPSOFT_IP3_TRAIL_PREM_MUTE_OBSERVE_BALLOT_DRAFT_2026-09-30__AWAITING_OPEN__NO_LIVE`
