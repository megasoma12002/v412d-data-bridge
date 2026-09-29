# Cutover checklist — FIN×SAT Path3 P3_T0_STATE (T0_CARVE_FIN_SAT_SWITCH)

Status: **PARTIAL LIVE WIRED (flip carve)** · Soft-Frozen KEEP · strategy cutover still **BLOCKED** (see 0kac) · broker **false** · live CONF α=0.10 KEEP · observe OPERATING  
Observe ballot: `FIN_SAT_PATH3_T0_STATE_OBSERVE_BALLOT_EXECUTED_OPEN.md`  
Policy: `FIN_SAT_T0_CARVEOUT_POLICY_BALLOT_EXECUTED_ACCEPT.md`  
Strategy cutover checklist: `CUTOVER_CHECKLIST_PATH3_STRATEGY.md`

## Gate (flip-day carve — already ACCEPTed)

- [x] Sealed MDD alert reviewed — human **ACCEPTABLE** (−0.17pp) · `FIN_SAT_PATH3_T0_SEALED_MDD_DISPOSITION.md`
- [x] Fill carve + emit ON (0ka7)
- [x] Weight engine ledger LIVE WIRED (0kab)
- [x] Soft flip mute LIVE WIRED (0kaa)
- [ ] Sustained clean month-end on dual-paper (no PAUSE cascade)
- [ ] Path3 **strategy** cutover (replace Soft primary) — **0kac CHARTER** · not this carve checklist
- [ ] Broker live-write ACCEPT (separate)

Until 0kac paper HIT + ACCEPT: Soft remains primary daily · Path3 = flip carve only.
