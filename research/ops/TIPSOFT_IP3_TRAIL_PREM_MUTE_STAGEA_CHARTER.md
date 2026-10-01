# TIPSOFT_IP3_TRAIL_PREM_MUTE_STAGEA_CHARTER

Date: 2026-09-30
Register: **0kb1** · Parents: 0kb0, 0kaz, 0kay, 0kaw

## Question

Can a **live-win episode census** plus **causal trailing prem mute** (3-state LIVE / P3 / P3+P4, year-regret / year-wins objective) raise yearly win-rate and cut regret vs oracle while held ≥ NEAR−ε and drawdown floors hold — without year dummies?

## Design

- Base: `BASE_LIVE_FUSE_COOL` Exact T+1 · Ref NEARPEAK3 / Path4 NEAR∧sat
- DIAG census: live-win years drag episodes (NEAR on ∧ prem_p3<0) — not a gate
- Mute: lag-1 rolling sum(prem_p3)/prem_on / confirm-K · optional COOL mutex
- 3-state: enter P3 on NEAR∧¬mute; P4 on sat∧¬mute4; else LIVE
- Success: `strong` = held+ vs NEAR + year obj; or `year_obj` with held≥NEAR−0.05
- Forbidden: year-cut · lookahead promote · hybrid T+0 · Path4 live · re-grid 0kb0 latch

Label: `TIPSOFT_IP3_TRAIL_PREM_MUTE_STAGEA_CHARTER_2026-09-30`
