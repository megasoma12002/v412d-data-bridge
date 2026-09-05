# DATA_SOURCE_PHASE_C_PROBES

- as_of: `2026-09-05`
- overall: **PASS**
- Soft-Frozen **KEEP**; no e21 rewrite; TAIEX Yahoo failover **opt-in only**

## Gates

| Probe | Status | Detail |
|---|---|---|
| C1_fin12_history_shadow | PASS | DRIFT on 1 ticker(s); does not count toward PASS |
| C2_adj_corporate_action_shadow | PASS | n_ok=8 |
| C3_taiex_optional_failover | PASS | Helper is opt-in only; e21 still uses FinMind TaiwanStockPrice(TAIEX). |

## Hard rules preserved

- Soft-Frozen KEEP
- No e21 history rewrite
- No Goodinfo/Wantgoo/CMoney reopen
- Yahoo TAIEX failover is **opt-in helper only** (not silent e21 primary switch)

Authority: `research/ops/DATA_SOURCE_RESILIENCE.md`

