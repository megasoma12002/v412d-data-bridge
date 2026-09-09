# Cutover checklist — FIN 民營 native (BLOCKED)

Date: 2026-09-09  
Status: **NOT AUTHORIZED / BLOCKED**  
Soft-Frozen live Financial clip: **[0.60, 0.90] FINBAND KEEP**  
Live DEFAULT books: **`E22_v2s_tw` KEEP**  
Live Financial within-sleeve: **公股 `KD_OPT` KEEP**  
Live capital: **500M** · board-lot **1000**

Authority: `FIN_PRIV_NATIVE_OBSERVE_POSTURE.md` · `FIN_PRIV_NATIVE_WITHIN_SLEEVE_DECISION_PACK.md` · `HUMAN_DECISION_REGISTER.md`

## Why blocked

| Prior path | Verdict |
|---|---|
| PRIV / ALL12 replace vs `LIVE_PUB_KD` | **STOP** (0 coexist) |
| 公/民 dollar-split dual-sleeve | **STOP** (best held-out −2.54) |
| Soft-Frozen 4-sleeve FinPub/FinPriv | **STOP** (best −1.29) |
| Native within-民營 dual-paper | **OBSERVE ONLY** — not a live cutover license |

Paper observe PASS (tip clean / held-out &gt; 0 vs `PRIV_EQUAL`) does **not** imply PASS vs live 公股 stack.

## What would be required (future — not this PR)

| # | Gate | Today |
|---|---|---|
| 1 | New charter vs live 公股 stack (not vs PRIV_EQUAL alone) | **MISSING** |
| 2 | Stage A tip-clean **and** held-out score &gt; 0 vs `LIVE_PUB_KD` | **FAIL historically** |
| 3 | Soft-Frozen membership / clip decision (separate ballot) | **KEEP 公股 R1** |
| 4 | Dedicated human ACCEPT + cutover PR | **NOT OPEN** |
| 5 | No history rewrite · forward-only | N/A |

## Explicit non-authorization

- Do **not** wire 民營 names into Soft-Frozen or `forward/e21` from observe green alone  
- Do **not** treat status ballot **STRICTER PAPER** as live cutover  
- Do **not** bundle this checklist into Soft-Frozen / KD / E45 PRs  

## Label

`CUTOVER_CHECKLIST_FIN_PRIV_NATIVE__NOT_AUTHORIZED_BLOCKED_2026-09-09`
