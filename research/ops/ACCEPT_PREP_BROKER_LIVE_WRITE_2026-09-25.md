# ACCEPT PREP — Broker live-write (not EXECUTE)

Status: **PREP ACCEPTED** (2026-09-25 deferred-ops ballot) — **EXECUTE still BLOCKED**  
Soft-Frozen: **KEEP** · `broker_live_write_accepted=False` · `API_WIRED=False`

## Ballot (prep)

> `ACCEPT PREP broker live-write cutover checklist; do not flip Soft-Frozen live-write gates until UAT readonly Login MsgCode 0001/00001 and a separate EXECUTE ballot.`

## Gates (unchanged — all required for EXECUTE)

1. `LiveConfig.broker_live_write_accepted=True` (ACCEPT PR)
2. Env `E21_BROKER_WRITE_LIVE=1`
3. `forward/e21/broker_live_write_accept.json` with `"accepted": true`
4. Canonical Soft-Frozen path still refuses non-`paper` fill port unless explicitly authorized
5. Yuanta: `API_WIRED=True` + DLL only after UAT/PROD readonly evidence

## EXECUTE prerequisites (human)

- [ ] UAT firewall open; `ystest.yuanta.com.tw:443` OK from `35.206.200.31`
- [ ] UAT readonly Login MsgCode `0001`/`00001` + GetStoreSummary/GetBankBalance
- [ ] PROD readonly (separate machine) optional but recommended
- [ ] Secrets only in Secret Manager / VM env — never git
- [ ] New ballot: `ACCEPT EXECUTE broker live-write …` with date + scope (UAT shadow vs Soft-Frozen paper port)

## Non-goals this cycle

- No `SendStockOrder` / SendAlgo
- No merge of R4 cash into tip
- No Soft-Frozen clip flip

Label: `ACCEPT_PREP_2026-09-25_BROKER_LIVE_WRITE`
