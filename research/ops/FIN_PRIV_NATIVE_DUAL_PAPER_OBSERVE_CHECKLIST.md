# 民營 Native Dual-Paper Observe Checklist

Date: 2026-09-09  
Status: **OPERATING OBSERVE** (paper only)  
Authority: `FIN_PRIV_NATIVE_WITHIN_SLEEVE_CHARTER.md` · `FIN_PRIV_NATIVE_WITHIN_SLEEVE_DECISION_PACK.md` · `FIN_PRIV_NATIVE_DUAL_PAPER_OBSERVE_OPEN.md` · `FIN_PRIV_NATIVE_OBSERVE_POSTURE.md` · `HUMAN_DECISION_REGISTER.md`

Soft-Frozen live: **[0.60, 0.90] FINBAND KEEP** (公股 R1 membership)  
Live DEFAULT books: **`E22_v2s_tw` KEEP**  
Live Financial within-sleeve: **`KD_OPT` KEEP** (公股 only)  
Live wire / e21 universe expand: **FORBIDDEN**  
4-sleeve Soft-Frozen cutover: **FORBIDDEN** (Stage A STOP)

## Sleeve definition (paper only)

| Book | Role |
|---|---|
| `PRIV_EQUAL` | Equal-split Financial dollars → PRIV_R3R4 (control) |
| `PRIV_KD_MAY_Klt25_T15` | Native May 1–31 · K&lt;25 · T−15 challenger |

Soft-Frozen **sleeve weights** from live FINBAND (公股 features); Financial dollars → 民營 only.  
Execution: capital **500,000,000** · lot **1000**.

## Pre-open checklist (recorded)

| # | Item | YES/NO |
|---|---|---|
| 1 | Soft-Frozen live clip remains FINBAND [0.60, 0.90] | **YES** |
| 2 | Live DEFAULT books remain `E22_v2s_tw` | **YES** |
| 3 | Live Financial within-sleeve remains 公股 `KD_OPT` | **YES** |
| 4 | Native optimize coexist + held-out score &gt; 0 | **YES** (~+0.63) |
| 5 | Dual ledgers + month-end monitor wired into pack | **YES** (#170) |
| 6 | No live-wire / Soft-Frozen flip / 4-sleeve PR bundled | **YES** |
| 7 | Observe ≠ promote understood | **YES** |

## During observe (fixed cadence)

| Cadence | Action |
|---|---|
| Month-end | `python3 scripts/e16_fin_priv_native_dual_paper_ledgers.py` |
| Month-end | `python3 scripts/e16_fin_priv_native_month_end_monitor.py` |
| Month-end | Or pack: `python3 scripts/ops_month_end_paper_pack.py [--refresh-ledgers]` |
| Month-end | Read tip gates (YTD / trailing_1y) + structural (held-out / sealed) |
| Continuous | No Soft-Frozen edit; no `forward/e21` universe expand; no silent DEFAULT change |

## Tip / structural reading guide

| Window | Role | Expect (design) |
|---|---|---|
| **ytd** / **trailing_1y** | Operating tip gates | ALERT if MDD worse or giveback &gt; 3 pp; PAUSE_REVIEW if giveback &gt; 5 pp |
| **heldout_2019_plus** | Structural lock | Score ~**+0.63**; giveback design 0.5 pp + 2 pp buffer |
| **sealed_2023_plus** | Report-only structural | Score ~flat; giveback design 0.8 pp + 2 pp buffer |
| **mtd** | Reported only | Not a cutover / status gate |

## Exit / escalate (status ballot — not live)

| Event | Action |
|---|---|
| Clean tip + held-out holds | Default **KEEP OBSERVE** |
| Tip ALERT / PAUSE_REVIEW | Extend observe; Soft-Frozen unchanged; no live talk |
| Sustained tip PAUSE or structural breach | Open **status ballot** → KEEP OBSERVE vs stricter paper (not live) |
| Human asks live expand / 4-sleeve | **REJECT** from this checklist — needs new charter + positive Stage A |

## Hard non-actions

- No Soft-Frozen flip  
- No live e21 民營 universe expand  
- No Soft-Frozen 4-sleeve Class D  
- No retune of live 公股 `KD_OPT` from this observe  
- No history rewrite  

## Label

`FIN_PRIV_NATIVE_DUAL_PAPER_OBSERVE_CHECKLIST_2026-09-09__OPERATING_OBSERVE__NO_LIVE_WIRE`
