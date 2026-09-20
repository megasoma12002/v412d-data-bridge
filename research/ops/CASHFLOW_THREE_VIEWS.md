# Cashflow three views (現金流三視角)

Date: 2026-09-20  
Status: **OPS SSOT** — Soft-Frozen **KEEP** · Stage-E DEFAULT `E22_v3_recv_pay_effdelay` (TAX0)  
Human priority (2026-09-20): **計算好現金流的數字** — not after-tax DEFAULT (ballot A KEEP TAX0)  
Machine report: `scripts/cashflow_three_views_report.py` → `CASHFLOW_THREE_VIEWS_REPORT.*`

## Why three views

「現金流數字」在這個系統裡不是單一 `cash` 欄位。三個時鐘必須分開標、分開算、分開對帳：

| View | Number | Clock | Answers |
|---|---|---|---|
| **A** | `portfolio_state.cash` | Exact T+1 fill day | Paper books cash leg for NAV |
| **B** | `settled_cash_estimate` | Trade T+2 (R4) | How much is *settled / spendable* (liquidity ≠ NAV) |
| **C** | `cash + e22_receivables` | Dividend effective ex → effective pay (Stage-E) | Dividend cashflow timing under **TAX0** |

**Never merge** A↔B↔C into one Soft-Frozen cash. R4 and Stage-E are overlays / books legs, not a second DEFAULT.

## Current tip snapshot (research)

As of tip `last_date=2026-09-16`:

- Tip books still **`E22_v2s_tw_effex`** (cash-on-ex) while code DEFAULT = Stage-E → **authorized tip lag**
- View **A** ≈ **50,416**
- View **B** ≈ **1,022** (`unsettled_net` ≈ 49,393) — intentional gap vs A
- View **C** receivable = **0 / absent** until weekday tip catch-up to Stage-E

Run:

```bash
python3 scripts/cashflow_three_views_report.py --write
```

## How each number is computed

### A — Exact T+1 paper cash

- Fills move paper `cash` on **fill date** (signal → next open).  
- Fees: `0.001425×0.6` + sell 證交稅 + **MIN_COMMISSION NT$20**.  
- Source: `live_ledger` / forward pipeline.

### B — R4 settled liquidity

```
settled_cash_estimate ≈ paper_cash − unsettled_net
```

- `unsettled_net` from fills whose `settle_date` (nth session +2, typhoon-aware) is after asof.  
- Script: `twse_t2_settlement_estimate.py`  
- Identity check (report): `|paper − unsettled − settled| ≤ NT$1`  
- **Not** NAV. Alert copy already says liquidity view NOT portfolio cash.

### C — Stage-E dividend cashflow (TAX0)

- Accrue **receivable** on effective ex; convert to **cash** on effective pay (+ MOPS pay amendments).  
- Wealth identity: `cash + e22_receivables + equity` (`live_ledger.holdings`).  
- Personal dividend income tax stays **outside** daily books (ballot A).  
- Tip lag means tip still credits cash on ex → View C incomplete until Phase 2 catch-up.

## Ops path to “算準”

| Priority | Action | Closes |
|---|---|---|
| **P0** | Next green weekday forward → tip `E22_v3_recv_pay_effdelay` | View C lands; tip-lag debt clears |
| **P0** | Daily `cashflow_three_views_report.py` (+ post-forward attach) | Numbers visible & identity-checked |
| **P1** | R4 week-1 spot: A vs B, unsettled | Liquidity honesty |
| **P1** | Real custody → R5 vs View B | Custody cash truth (observe) |
| **P2** | `dividends_applied` after Stage-E tip | Div apply evidence for C |

## Explicit non-actions

- Merge R4 `settled_cash_estimate` into `portfolio_state.cash`  
- After-tax `tax10`/`tax20` DEFAULT for “better cashflow”  
- Weekend invent / rewrite `forward/e21` history  
- Soft-Frozen / alpha / broker live-write promote

## Related

- Tip Monday: `TIP_CATCHUP_MONDAY_CHECKLIST.md` (Phase 2; open PR #266)  
- R4/R5: `R4_R5_WEEK1_OBSERVE_CHECKLIST.md` · `TWSE_T2_SETTLEMENT_ESTIMATE_CHARTER.md`  
- Div delay: `TWSE_DIVIDEND_CREDIT_DELAY_CHARTER.md`  
- Realism roadmap: `REALISM_AUTOMATION_GAP_CLOSE_2026-09-20.md`  
- Tax posture: `E22_V3_WITHHOLDING_RESIDENT_NOTE.md` (ballot A — tax outside)

## Label

`CASHFLOW_THREE_VIEWS__2026-09-20`
