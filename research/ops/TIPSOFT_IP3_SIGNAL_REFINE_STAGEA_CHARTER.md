# TIPSOFT_IP3_SIGNAL_REFINE_STAGEA_CHARTER

Date: 2026-09-30
Register: **0kaz** · Parents: 0kay, 0kaw, 0kau

## Question

Can causal daily confirms/mutes refine `I_p3` (and optionally `I_p4`) so stack-on days keep research edge and other days fall back to live Soft, closing the year-book oracle gap **without year dummies**?

## Design

- Base: `BASE_LIVE_FUSE_COOL` Exact T+1
- Ref: `I_p3=NEARPEAK3` (0kaw) · optional Path4 `NEAR∧sat_lead` CASH_001 (0kay)
- Challengers: NEAR ∧ confirm / NEAR ∧ ¬mute / θ variants · P4 OFF/SAT/DEFEND/NOTBLEED
- Success: `held_vs_near > 0` + live sealed/tip floors **or** year_gap_improve ≥ 0.05pp with live held floor
- Forbidden: year cuts · lookahead promote · hybrid T+0 · Path4 live wire

Label: `TIPSOFT_IP3_SIGNAL_REFINE_STAGEA_CHARTER_2026-09-30`
