# Cutover checklist — FIN within-sleeve

Date: 2026-09-09  
Status: **ACCEPTED — LIVE WIRED (forward-only)**  
Human ballot: **`ACCEPT`** → interpreted as **`ACCEPT live FIN within-sleeve cutover: KD_OPT`**  
Acceptance note: `FIN_WITHIN_SLEEVE_CUTOVER_ACCEPTED_KD_OPT.md`  
Soft-Frozen live Financial clip: **[0.50, 0.95] KEEP**  
Live DEFAULT books: **`E22_v2s_tw` KEEP**  
Live capital: **500M**  
Board-lot: **1000 KEEP**  
E45 stitch: **FORBIDDEN** (separate agenda)

Authority: `FIN_WITHIN_SLEEVE_ALLOC_CHARTER.md` · `FIN_WITHIN_SLEEVE_OBSERVE_POSTURE.md` · `FIN_WITHIN_SLEEVE_ALLOC_DECISION_PACK.md` · `HUMAN_DECISION_REGISTER.md`

## What cutover changed

- Live Financial within-sleeve: **`FIN_EQUAL` → `FIN_PRE_EXDIV_KD` (`KD_OPT` / `KD_APR15_MAY15_Klt30_T15`)**  
- Soft-Frozen sleeve weights / clips **unchanged**  
- DEFAULT books **`E22_v2s_tw` unchanged**  
- Telecom within-sleeve stays **EQUAL**  
- Forward-only; **no** history rewrite  

## Gates at ACCEPT

| # | Gate | Pass? |
|---|---|---|
| 1 | Charter ACCEPT + Stage B STOP + Stage C LOCKED | **YES** |
| 2 | Stage D multi-paper OPERATING (EQUAL ∥ RS ∥ MIX_L75 ∥ KD_OPT) | **YES** |
| 3 | Human chose **`KD_OPT`** | **YES** |
| 4 | Tip YTD+1y PASS (asof 2026-09-08) | **YES** |
| 5 | Held-out score &gt; 0 (~+0.65) | **YES** |
| 8 | Exact T+1 OK | **YES** |
| 9 | Live capital 500M | **YES** |
| 10–11 | Soft-Frozen / DEFAULT KEEP | **YES** |
| 12 | Dedicated cutover PR | **THIS PR** |
| 13 | No forbidden bundles | **YES** |

## Label

`CUTOVER_CHECKLIST_FIN_WITHIN_SLEEVE__ACCEPTED_KD_OPT_2026-09-09`
