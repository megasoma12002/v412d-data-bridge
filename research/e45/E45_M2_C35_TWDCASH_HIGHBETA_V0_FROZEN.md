# E45 M2 — C35 Retarget + Tradable TWD Cash + HIGH_BETA Hygiene (FROZEN BEFORE METRICS)

Date: 2026-09-07  
Status: **FROZEN — PAPER COMPLETE** — Soft-Frozen **KEEP** · DEFAULT **KEEP** · stitch **FORBIDDEN**  
Parent: `E45_M2_BIL_FX_OPTIMIZE_V0_FROZEN.md` · operating observe `E45_M2_BIL_FX_OBSERVE_OPEN.md`  
Claimed MDD: **`RETIRED_HISTORICAL_NARRATIVE`** — no invented replacement

## Why this batch

Human asked to execute the post-optimize research queue **in order**:

| # | Item | This freeze |
|---|---|---|
| **A** | C35 observe retarget | Ballot **DRAFT only** — do **not** silent-swap C50 lock |
| **B** | True tradable TWD cash / short | Listed short-bond ETFs already ingested (`00740B`, `00751B`) + honesty vs CBC / cash0 / 00720B |
| **C** | HIGH_BETA | Research hygiene — **HOLD DRAFT**; no OPEN |

## A. C35 observe retarget (DRAFT)

Operating lock today: **`M2_RELOC_BIL_FX_C50`**.  
Optimize cut grid (κ=1) among §2 PASS books prefers **lowest held giveback** → **`M2_RELOC_BIL_FX_C35`** (informational; C40 may have higher score).

Freeze rule for ballot read:

- Evidence from `E45_M2_BIL_FX_OPTIMIZE.md` / `optimize_section2_qualification.csv`
- Human choices: **HOLD DRAFT** (default) / **ACCEPT OPEN C35** (retarget lock) / **REJECT**
- ACCEPT would require a separate PR to change operating docs + month-end lock — **not this paper alone**
- C50 remains OPERATING until explicit ACCEPT C35

## B. Tradable TWD cash-like (listed)

Retail bank-deposit NAV / FinMind deposit-rate history is **not** available on free FinMind tier (probe 2026-09-07 → sponsor gate).  
Closest **tradable listed** TWD cash-like proxies already under `data/def_proxies/`:

| Code | Class | Honesty |
|---|---|---|
| `00740B` | `tw_short_bond_etf` | Listed short-duration TW bond ETF — **not** bank cash |
| `00751B` | `tw_short_bond_etf` | Same family |
| `00720B` | short-bond ref | Prior §2 **FAIL** (improve pack) |
| `TWD_CASH_CBC` | policy carry | Rediscount — upper-bound policy, not retail |
| `TWD_CASH0` | zero floor | Bound only |

Destination algebra: same `RELOC_TWD_720B` / `RELOC_BIL_FX` sleeve relocate.  
Books @ c=0.50 (and C75 informational): `M2_RELOC_TWD_740B_C50`, `M2_RELOC_TWD_751B_C50`, `M2_RELOC_TWD_SHORT_BASKET_C50` (equal-weight 740B+751B after both listed; pre-list = cash0).  
Refs: `BIL_FX`, `TWD_CASH_CBC`, `TWD_CASH0`, `TWD_720B`.

## C. HIGH_BETA hygiene

Paper densify already prefers **`FIN_ONLY_A10`** over HIGH_BETA α grid.  
This batch only:

- Reaffirm ballot **HOLD DRAFT / NOT OPEN**
- Cross-link operating FIN_A10 + BIL_FX C50 observe
- Do **not** wire HIGH_BETA into month-end pack

## Explicit non-actions

- No Soft-Frozen / DEFAULT / stitch / live_market merge  
- No silent C50→C35 observe lock change  
- No HIGH_BETA OPEN  
- No pretend 00740B/00751B/CBC = retail TWD deposit  
- No invent MDD replacement  
- No E45 mild-α densify  

Label: `E45_M2_C35_TWDCASH_HIGHBETA_V0_FROZEN_2026-09-07__PAPER_DRAFT_ONLY__STITCH_FORBIDDEN`

## Paper results (post-run)

- A: preferred retarget **C35** by giveback-min; ballot **DRAFT / NOT OPEN**; C50 stays OPERATING  
- B: `00740B`/`00751B`/basket **§2 FAIL** (negative held scores); retail deposit NAV unavailable free FinMind; keep BIL_FX / CBC / cash0 as honesty refs  
- C: HIGH_BETA **HOLD DRAFT** hygiene recorded  

Artifacts: `E45_M2_C35_RETARGET_BALLOT.md` · `E45_M2_TWD_TRADABLE_CASH.md` · `E45_HIGH_BETA_HOLD_DRAFT_HYGIENE.md` · batch `E45_M2_C35_TWDCASH_HIGHBETA_BATCH.md`
