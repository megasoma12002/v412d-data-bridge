# TWSE 除權息入帳延後 — research charter

Status: **RESEARCH / CHARTER** — observe-only · Soft-Frozen / `E22_v2s_tw` / LIVE_* unchanged  
Depends on: session + settlement calendar (#237 / #239) · Gap #6 dividend timing  
Related: `FORMAL_TAX_RECEIVABLE_BOOKS_CHARTER.md` · `TWSE_T2_SETTLEMENT_ESTIMATE_CHARTER.md` · `e22_dividend_accounting.py`

## 0. Why this is a separate clock

Trade **T+2 交割** and **除權息入帳** are not the same pipeline.

```text
Trade:     signal → Exact T+1 fill → +2 settlement business days → custody cash/shares
Dividend:  停止過戶 / 基準日 → 除權息交易日(ex) → … lag … → 現金發放日(payment) → bank credit
```

| Clock | Repo today | Moved by typhoon / 封關? |
|---|---|---|
| Exact T+1 fill | `fills.csv` | Yes — no fill on closed board |
| Custody trade T+2 | `twse_t2_settlement_estimate` | Yes — `is_settlement` (+ 封關僅交割) |
| Formal books cash | **`cash_ex_date`** (`E22_v2s_tw`) | **No** — calendar match only |
| Custody cash spendable | usually **`payment_date`** | Often yes — bank/票交所 停班顺延 |
| Sandbox pay books | `E22_v3_recv_pay*` | Uses ledger `payment_date` as-is; **no** auto-shift |

Dividend ex→pay is the **fourth clock** already called out in the T+2 charter — this doc fills the delay rules.

---

## 1. Two delay surfaces (do not merge)

### A. 除權息**交易日** (ex-date / board)

| Rule | Source |
|---|---|
| Ex day is a **trading** event (open reference / limit prices) | TWSE 營業細則 §67 chain |
| If **集中市場全日休市** on the scheduled ex day | That day's ex stocks: 漲跌停／開盤參考價適用於**次一營業日**；實務上當日除權息檔 **顺延至次一營業日**交易（例：2026-07-10 巴威，21 檔顺延） |
| Ex days **after** the closed day | Keep original date **unless** issuer changes 權利分派基準日 | TWSE FAQ Q5 |
| 停止過戶 / 基準日 | Issuer-set; **not** auto-shifted by typhoon alone | FAQ Q5 |

**Repo impact:** live books match `ex_date == asof`. If TWSE postpones ex trading one day but ledger still has old `ex_date`, formal credit fires on a **non-session** day (no bar) unless events are refreshed. Soft signal helpers already snap some ex lists to “first session on/after” for trading bans — cash credit does not.

### B. 現金股利**發放／入帳** (payment_date)

| Rule | Source |
|---|---|
| Investor spendable cash ≈ company **現金股利發放日** (+ broker/bank batch) | MOPS / issuer; Gap #6 |
| Weekend / 国定假 | Issuer schedules around; if lands on non-bank day → next business day |
| Typhoon | Often **金融機構／票交所**停班 → companies announce payment **顺延下一營業日** (MOPS 重大訊息). May be **regional**: 未停班縣市仍原日發放 |
| TWSE board close alone | Insufficient SSOT for “everyone delayed” — bank locality matters |
| 封關「僅交割」日 (e.g. 2026-02-12/13) | Board closed; banks usually open — payment can still occur; do not treat as 春节放假 |

**Cannot fully automate** regional bank delay from Taipei CAP alone. Best automation ladder:

1. Prefer **issuer MOPS amendment** (原發放日 → 變更後發放日) when present  
2. Else heuristic: if `payment_date` ∉ settlement/bank business calendar → snap to next `is_settlement=1` day (ops estimate only)  
3. Never rewrite Soft-Frozen NAV from the heuristic without ACCEPT

---

## 2. What the repo does today (gap)

| Layer | Behavior |
|---|---|
| `e22_dividend_accounting.apply_dividends_for_date` | Credits cash/stock when **`ex_date == day`**; stores `payment_date` unused for cash |
| `E22_v2s_tw` live | `cash_timing: cash_ex_date` · `stock_timing: stock_ex_date` |
| `E22_v3_recv_pay*` sandbox | Receivable on ex; cash on ledger **payment_date** — **no** holiday/typhoon snap |
| Session / T+2 modules | Do **not** call into dividend apply |
| Ex→pay KPI | Calendar-day lag report — not session-day |

**Known Gap #6.1 / 6.2:** formal cash early vs custody pay. This charter adds Gap **6.9**:

| # | Item | Status |
|---|---|---|
| **6.9a** | Ex trading day postponed when board closed | Not in ledger refresh / apply |
| **6.9b** | Payment delayed by bank/票交所 停班 | Not auto; needs MOPS overlay or heuristic |
| **6.9c** | Stock / CIL pay-date delay | Same class as 6.9b; books still credit shares on `stock_ex_date` |

---

## 3. Recommended model (observe-only until ACCEPT)

### 3.1 Calendars

Reuse #237 / #239:

| Need | Use |
|---|---|
| Ex trading postpone | Next **`is_session=1`** after closed day |
| Payment heuristic snap | Next **`is_settlement=1`** (includes 封關僅交割; excludes 春节/颱風全日) |
| Regional bank stop | **Manual / MOPS** — out of scope for v1 auto |

### 3.2 Effective dates (estimate)

```text
effective_ex_trade(ex_date):
  if calendar.is_session(ex_date): return ex_date
  else: return nth_session_on_or_after(ex_date)   # typhoon / weekend

effective_payment(payment_date):
  if mops_amendment: return amended_date
  if calendar.is_settlement(payment_date): return payment_date
  else: return nth_settlement_after(payment_date-1, 1)  # next settlement day
```

### 3.3 Books policy options (do **not** flip Soft-Frozen here)

| Option | Behavior | When |
|---|---|---|
| **S0 (today)** | Credit on raw ledger `ex_date` | Soft-Frozen keep |
| **S1 observe** | Emit `dividend_delay_estimate.csv`: raw vs effective ex/pay | Ops pack |
| **S2 sandbox** | `E22_v3_recv_pay` cash on **effective_payment** | Stage B extension |
| **S3** | Refresh `ex_date` from TWSE same-day ex list after typhoon | Event pipeline ACCEPT |

---

## 4. Worked examples

### 4.1 巴威 2026-07-10（台北停班 → 台股休市）

| Event | Effect |
|---|---|
| Board | Closed; 應屆交割顺延 |
| Scheduled ex that day | **23** 上市/上櫃/興櫃檔顺延至 **2026-07-13**（新聞盤點；含 2891 中信金、3034 聯詠等） |
| Cash payment scheduled 07-10 | 北市停班 → 銀行／票交所停班 → 股務跨行匯撥常顺延至 07-13；**未停班縣市**可能仍原日 |
| TWSE FAQ Q5 | 原訂**當日**除權息檔：漲跌停／開盤參考價適用次一營業日；休市**之後**原訂檔若公司未改基準日則不顺延 |

Formal `E22_v2s_tw` if holding: would still attempt cash credit on ledger `ex_date` if it equals 07-10 even though no session — **identity mismatch** with market.

### 4.2 封關 2026

| Date | Board | Settlement | Dividend note |
|---|---|---|---|
| 02-11 最後交易日 | open | yes | Last ex/trade day before break |
| 02-12 / 02-13 僅交割 | closed | **yes** | Payment **can** land here; not 春节 |
| 02-16–20 春节 | closed | no | Payment should not be scheduled; if ledger has it → snap heuristic |
| 02-23 開紅盤 | open | yes | Resume ex trading |

### 4.3 Empirical scan (`e22_dividend_events.csv` × `twse_sessions_2026.csv`)

| Finding | Detail |
|---|---|
| In-calendar field snaps | **1** row: `2891` `cash_ex_date` 2026-07-10 → effective **2026-07-13** (`delay_ex_days=3`; payment 08-07 unchanged) |
| Other 2026 sleeve events | 17 more 2026-dated rows; none land on CLOSED/TYPHOON or weekend inside the pinned calendar |
| Payment on 封關僅交割 | No ledger row uses 2026-02-12/13 as payment — heuristic would **keep** those days (`is_settlement=1`) |
| Outside-calendar history | Pre-2026 weekend payments left raw (`*_outside_calendar`) — no false snap to 2026-01-02 |
| Dual legs | Cash / stock ex+pay estimated separately (same typhoon snap applies to both ex legs) |

CLI:

```bash
PYTHONPATH=scripts python3 scripts/twse_dividend_delay_estimate.py
# → repro/div-delay/dividend_delay_estimate.csv
# → repro/div-delay/dividend_delay_estimate.summary.json
```

---

## 5. Implementation phases

| Phase | Deliverable | Gate |
|---|---|---|
| **D0** | This charter | — |
| **D1** | Pure helpers: `effective_ex_trade` / `effective_payment` + unit tests (typhoon + 封關 + consecutive) | Observe |
| **D2** | CLI estimate over `e22_dividend_events.csv` → repro CSV + summary JSON (cash/stock legs; no books mutate) | Observe ✅ |
| **D3** | Optional wire into `E22_v3_recv_pay` sandbox only | Sandbox ACCEPT |
| **D4** | MOPS payment-amendment fetch overlay | Ops |
| **D5** | Soft-Frozen books change | **Explicit ACCEPT** — not this PR |

Parallel: keep trade T+2 (#239) and session MIS/CAP (#237) as SSOT for board/settlement calendars.

---

## 6. Pitfalls

1. Treating payment delay as trade T+2.  
2. Snapping payment with **trading-only** sessions → wrong push past 封關僅交割 days.  
3. Assuming Taipei CAP delays **all** investors’ dividends (regional banks).  
4. Moving Soft-Frozen cash from ex → pay without version bump.  
5. Confusing 基準日 / 停止過戶 (issuer) with ex trading postpone (market).  
6. Double-count: adjusting both ledger `ex_date` and apply-asof without idempotent keys.

---

## 7. Minimal API sketch (D1)

```text
effective_ex_trade(day, session_dates) -> date
effective_payment(day, settlement_dates, *, mops_amendment: date|None) -> date

estimate_event(row, sessions, settlements) -> dict
  # cash_* and stock_* effective/delay fields + compat aliases
```

```bash
PYTHONPATH=scripts python3 scripts/twse_dividend_delay_estimate.py \
  --events data/dividend_events/e22_dividend_events.csv \
  --calendar data/calendars/twse_sessions_2026.csv \
  --out repro/div-delay/dividend_delay_estimate.csv
```

---

## 8. Pointers

- TWSE 天然災害 FAQ Q5（除權息交易日）: `https://www.twse.com.tw/zh/about/suspended_faq.html`  
- TWSE 休市原則: `https://www.twse.com.tw/zh/clearing/suspended.html`  
- Session / 封關交割日: `TWSE_SESSION_CALENDAR_CHARTER.md` · `TWSE_T2_SETTLEMENT_ESTIMATE_CHARTER.md`  
- Gap #6: `research/e22/EXECUTION_DETAIL_GAP6_BRIEF.md`  
- Books: `scripts/e22_dividend_accounting.py` · `FORMAL_TAX_RECEIVABLE_BOOKS_CHARTER.md`  
- Events: `data/dividend_events/e22_dividend_events.csv`

Label: `TWSE_DIVIDEND_CREDIT_DELAY__RESEARCH_CHARTER`
