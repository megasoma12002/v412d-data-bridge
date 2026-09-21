# Cashflow three views (現金流三視角)

Date: 2026-09-21 (amended; SSOT opened 2026-09-20)  
Status: **OPS SSOT** — Soft-Frozen **KEEP** · Stage-E DEFAULT `E22_v3_recv_pay_effdelay` (TAX0)  
Human priority (2026-09-20): **計算好現金流的數字** — not after-tax DEFAULT (ballot A KEEP TAX0)  
Tax purpose (same day): **稅的目的是要有精準的現金流** · `TAX_FOR_CASHFLOW_PURPOSE.md`  
Machine report: `scripts/cashflow_three_views_report.py` → `CASHFLOW_THREE_VIEWS_REPORT.*`  
Phase 2: **CONFIRMED** 2026-09-21 — tip == Stage-E · `TIP_CATCHUP_MONDAY_2026-09-21.md`

## Why three views

「現金流數字」在這個系統裡不是單一 `cash` 欄位。三個時鐘必須分開標、分開算、分開對帳：

| View | Number | Clock | Answers |
|---|---|---|---|
| **A** | `portfolio_state.cash` | Exact T+1 fill day | Paper books cash leg for NAV |
| **B** | `settled_cash_estimate` | Trade T+2 (R4) | How much is *settled / spendable* (liquidity ≠ NAV) |
| **C** | `cash + e22_receivables` | Dividend effective ex → effective pay (Stage-E) | Dividend cashflow timing under **TAX0** |

**Never merge** A↔B↔C into one Soft-Frozen cash. R4 and Stage-E are overlays / books legs, not a second DEFAULT.

## Current tip snapshot (research)

As of tip `last_date=2026-09-21`:

- Tip books **`E22_v3_recv_pay_effdelay`** == code DEFAULT → **Stage-E aligned** (`tip_lag=false`)
- View **A** ≈ **50,415.51**
- View **B** ≈ **50,415.51** (`unsettled_net` ≈ 0 this asof) — identity_ok; still liquidity ≠ NAV label
- View **C** receivable = **0** today (no open ex→pay row); clock is **live** on tip

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
- Tip is on Stage-E — View C receivable clock is active (recv may be 0 outside ex→pay windows).

## Ops path to “算準”

| Priority | Action | Closes |
|---|---|---|
| ~~**P0**~~ | ~~Next green weekday forward → tip Stage-E~~ | **DONE 2026-09-21** (Phase 2) |
| **P0** | Daily `cashflow_three_views_report.py` (+ post-forward attach) | Numbers visible & identity-checked |
| **P1** | R4 week-1 spot: A vs B, unsettled | Liquidity honesty |
| **P1** | Real custody → R5 vs View B | Custody cash truth (observe) |
| **P1** | `dividends_applied` on Stage-E tip div days | Div apply evidence for C (G7) |

## Explicit non-actions

- Merge R4 `settled_cash_estimate` into `portfolio_state.cash`  
- After-tax `tax10`/`tax20` DEFAULT for “better cashflow”  
- Weekend invent / rewrite `forward/e21` history  
- Soft-Frozen / alpha / broker live-write promote

## Known cashflow haircut (sandbox): NHI 補充保費

Human (2026-09-20): **股利單次達 NT$20,000 → 二代健保補充保費 2.11% 就源扣繳**.  

- **≠** ballot A 所得稅（年終）；這是 **發放日現金** 可能少一截.  
- Live Stage-E still credits **TAX0 gross** — custody may show net after 2.11% when payment ≥ 20k.  
- Research helper: `nhi_dividend_supplemental_premium.py` · note `NHI_DIVIDEND_SUPPLEMENTAL_PREMIUM_NOTE.md`  
- Cashflow-precision sandbox (not live): **`E22_v3_recv_pay_effdelay_nhi211`** · purpose `TAX_FOR_CASHFLOW_PURPOSE.md`  
- **No** live wire this cycle (needs dedicated ballot).

## Related

- Tip Monday: `TIP_CATCHUP_MONDAY_CHECKLIST.md` (**CONFIRMED** 2026-09-21) · `PHASE_2_TIP_CATCHUP_CONFIRMED_2026-09-21.md`  
- R4/R5: `R4_R5_WEEK1_OBSERVE_CHECKLIST.md` · `TWSE_T2_SETTLEMENT_ESTIMATE_CHARTER.md`  
- Div delay: `TWSE_DIVIDEND_CREDIT_DELAY_CHARTER.md`  
- Realism roadmap: `REALISM_AUTOMATION_GAP_CLOSE_2026-09-20.md`  
- Tax posture: `E22_V3_WITHHOLDING_RESIDENT_NOTE.md` (ballot A — 所得稅 outside)  
- NHI: `NHI_DIVIDEND_SUPPLEMENTAL_PREMIUM_NOTE.md`

## Label

`CASHFLOW_THREE_VIEWS__2026-09-21_PHASE2`
