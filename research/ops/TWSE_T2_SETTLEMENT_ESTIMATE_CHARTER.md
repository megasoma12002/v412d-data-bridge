# TWSE T+2 settlement cash estimate — implementation research

Status: **RESEARCH / CHARTER** — observe-only · Soft-Frozen / LIVE_* / `E22_v2s_tw` unchanged  
Depends on: session calendar method (`TWSE_SESSION_CALENDAR_CHARTER.md`, PR #237)  
Related: `live_execution` fills · `live_ledger` fees · Exact T+1 ≠ custody T+2

## 0. What this is (and is not)

| Is | Is not |
|---|---|
| Ops **交割金額試算** from live `fills.csv` | A second NAV / Soft-Frozen flip |
| `settle_date = fill_date + 2 trading sessions` | Calendar +2 days |
| Liquidity / broker-prep overlay | Dividend receivable / E22_v3 pay-date books |
| Reuses `gross` + `fees_tax` on fills | Re-inventing fee model (unless ACCEPT) |

**TWSE fact (investor side):** 普通股／ETF 款券交割在成交日後**第二個營業日**（T+2）；投資人通常須於 T+2 上午對券商完成交割；同日買賣多為**淨額**一筆交割款。

**Repo fact:** paper / live pipeline books cash at **Exact T+1 fill** (signal → next session open). `portfolio_state.cash` is **trade-time cash**, not settled bank cash. Estimate module: `scripts/twse_t2_settlement_estimate.py` (observe-only).
---

## 1. Three clocks (do not merge)

```text
signal_date  --Exact T+1-->  fill_date  --T+2 sessions-->  settle_date
   (order)                    (trade)                      (custody cash/shares)
```

| Clock | Meaning in this repo | Artifact |
|---|---|---|
| Exact T+1 | Signal day → fill at next session open | `orders.csv` → `fills.csv` |
| Paper cash | Cash moves on `fill_date` | `portfolio_state.json` / `nav.csv` |
| Custody T+2 | Cash/shares settle `+2 sessions` after fill | **new estimate only** |

Dividend **ex → pay** (`FORMAL_TAX_RECEIVABLE_BOOKS_CHARTER` / `E22_v3_recv_pay`) is a **fourth** clock — never reuse for trade settlement.

---

## 2. Amount formulas (v1 = match live fill economics)

Reuse each fill row (`scripts/live_execution.py` / `live_ledger.py`):

```text
BUY  settlement_cash = -(gross + fees_tax)   # pay broker on settle_date
SELL settlement_cash = +(gross - fees_tax)   # receive on settle_date
```

Where live already set:

- `gross = quantity * fill_price`
- `fill_price = open * (1 ± SLIP)` (paper)
- BUY: `fees_tax = max(gross * BUY_FEE, MIN_COMMISSION)` (`BUY_FEE=0.001425*0.6`, `MIN_COMMISSION=20`)
- SELL: `fees_tax = max(gross * SELL_FEE, MIN_COMMISSION) + gross * (TAX_STOCK|TAX_ETF)`

**v1 deliberately ignores** (document as known gap → later ACCEPT):

- Day-trade tax preference (0.15%) — live stack is not day-trade SSOT
- Pre-fund / 全額交割 / 處置股 specials
- Netting presentation is **by settle_date** (sum fills settling that day), which matches “一天一筆淨額交割款” at investor–broker level

~~Broker **minimum commission** (often NT$20 / 整股)~~ — **ACCEPT closed** via `live_ledger.MIN_COMMISSION` / `fees_tax_for`.

Optional v1.1 column: `settlement_cash_no_slip` using unslipped open — for broker price reconcile only.

---

## 3. Session offset (holidays / typhoon)

```text
settle_date = nth_open_session_after(fill_date, n=2)
# implemented as nth_settlement_after(settlement_dates(...), fill_date, 2)
```

| Input | Source |
|---|---|
| Preferred | `is_settlement=1` rows in `twse_sessions_YYYY.csv` (#237) — **not** trading-only |
| Interim | Sorted unique **complete** dates from `forward/e21/live_market.csv` (trading days only; misses 封關 settlement-only) |

**Must not:** `fill_date + timedelta(days=2)`.  
国定假 / 颱風假 / 补班日 / 封關交割日 規則見 §3.3。
### 3.1 Why typhoon breaks calendar +2

TWSE：台北市全日／上午停班 → **集中市場全日休市**，當日**應屆交割款券順延**至次一營業日。

| Example (2026-07 Bawei) | Calendar +2 (wrong) | Session T+2 (correct) |
|---|---|---|
| Fill **2026-07-08** (Thu) | 2026-07-10 (**typhoon closed**) | **2026-07-13** (Mon) — skips Fri typhoon + weekend |
| Fill **2026-07-07** (Wed) | 2026-07-09 | 2026-07-09 (Thu still open) |
| No fill on 2026-07-10 | — | No settlement row; pending Exact T+1 waits for next open |

If a previously computed `settle_date` is later demoted to typhoon closed by CAP/MI overlay, **re-run** the estimate against the updated session CSV — do not leave obligation on a non-session day.

### 3.2 Consecutive typhoon / multi-day closes

`nth_session_after` counts **open sessions only** — any streak of closed weekdays (one typhoon lasting Mon–Wed, or two storms back-to-back) is skipped automatically. No special “max one typhoon day” cap.

| Mechanism | Consecutive behavior |
|---|---|
| Session CSV `is_session=0` rows | T+1 / T+2 walk past every closed day until N opens accumulate |
| CAP overlay | One alert may list a **date range** (`8/3至8/5`) or `今天及明天` → each day demoted (`target_dates`) |
| Per-day CAP / MI_INDEX empty | Also fine — each day overlaid independently |
| Recompute | If day-2 of a streak is announced after fill, regenerate estimate |

Example: fill Fri → Mon/Tue/Wed all typhoon closed → settle = following Fri (2nd open after fill), not Mon+2 calendar logic.

### 3.3 過年封關 vs 交割日（兩套日曆）

| Kind | Board (`is_session`) | Custody T+2 (`is_settlement`) | 2026 example |
|---|---|---|---|
| 最後交易日 / 開紅盤 | yes | yes | 02-11 封關 · 02-23 開紅盤 |
| **無交易，僅辦理結算交割** | **no** | **yes** | **02-12 · 02-13** |
| 春節放假 / 補假 | no | no | 02-16–02-20 |
| 颱風全日休市 | no | no（應屆交割顺延） | 07-10 |

**Correct T+2 across 封關**
- Fill **2026-02-10** → settle **2026-02-12**（僅交割日）
- Fill **2026-02-11** → settle **2026-02-13**（僅交割日，年前完成）
- Wrong if using trading-only sessions: would push settle to **02-24** after 開紅盤

Exact T+1 / broker submit still use `is_session` only — no fills on 02-12/02-13.

**Prototype (R1+R3):** `scripts/twse_t2_settlement_estimate.py` reads `fills.csv` + pinned session calendar; observe-only CSV/JSON.

---

## 4. Recommended module seams

```text
scripts/twse_t2_settlement_estimate.py   # pure estimate + CLI
scripts/twse_session_calendar.py         # shared offset (calendar charter)
forward/e21/fills.csv                    # read-only input
forward/e21/settlement_cash_estimate.csv # optional daily artifact (observe)
forward/e21/settlement_cash_estimate.json
```

**Do not mutate:** `portfolio_state.json`, `nav.csv`, `fills.csv`, Soft-Frozen, `E22_v2s_tw`.

**Optional hook:** after fills in `e21_forward_pipeline` (or GHA step), regenerate estimate — same pattern as `pipeline_t1_audit.json`.

**Broker later:** `FillPort` stays trade/fill; settlement estimate compares to custody statements; gating submit on settled cash needs separate ACCEPT.

---

## 5. Data contract (v1)

### Per-fill row (detail)

| Field | Notes |
|---|---|
| `fill_id`, `fill_date`, `code`, `side`, `quantity` | From fills |
| `gross`, `fees_tax` | From fills (SSOT) |
| `settlement_cash` | Signed; BUY negative |
| `settle_date` | +2 sessions after `fill_date` |
| `sessions_to_settle` | 2, or 0/1 if asof already past |

### Daily summary (asof = session `D`)

| Field | Notes |
|---|---|
| `settling_today_net` | Σ `settlement_cash` where `settle_date == D` |
| `unsettled_payables` | Σ BUY not yet settled as of D (absolute or signed) |
| `unsettled_receivables` | Σ SELL not yet settled |
| `unsettled_net` | payables + receivables (signed) |
| `paper_cash` | From `portfolio_state` (fill-time) |
| `settled_cash_estimate` | `paper_cash - unsettled_net` **label clearly** — liquidity view, **not** NAV |

Identity (if unsettled_net = sum of signed settlement_cash still open):

```text
settled_cash_estimate ≈ paper_cash - unsettled_net
```

Explain in report: paper already booked fill-time cash; estimate backs out unsettled to approximate **交割帐户可用资金**.

---

## 6. Implementation phases

| Phase | Deliverable | Gate |
|---|---|---|
| **R0** | This charter | — |
| **R1** | Pure functions + unit tests (holiday + **typhoon** gap) | **Prototype landed** · `twse_t2_settlement_estimate.py` |
| **R2** | CLI: `--state-dir forward/e21 --asof YYYY-MM-DD` → CSV/JSON | **Prototype landed** (writes observe artifact under state-dir / `--out-dir`) |
| **R3** | Offset via `twse_sessions_YYYY.csv` / `nth_session_after` (#237) | **Prototype landed** (merged session calendar) |
| **R4** | Daily emit from forward workflow (`v412f-forward-paper` step) | **ACCEPT observe ✅** |
| **R5** | Broker reconcile pack (`twse_t2_broker_reconcile.py` estimate vs custody fixture) | **ACCEPT observe ✅** (no live gate) |

Parallel (from calendar charter): P1–P3 session calendar — **required before R5 / broker live submit**.

P4 fill port: `BrokerPreflightFillPort` maps session-gated **fixture acks** → shadow fills under `broker_preflight/`. Soft-Frozen `fills.csv` untouched unless **all** of: `live_config.broker_live_write_accepted=True` (ACCEPT PR), `E21_BROKER_WRITE_LIVE=1`, circuit closed, ack↔pending match, idempotent `client_order_id`, daily live-write budget, **exclusive process lock**, and **confirm+reserve broker dedupe** (`scripts/broker_safety.py`). Soft-Frozen `order_id` SSOT: `live_ledger.make_order_id` (`{date}-{code}-{side}`). No real broker network client; OPEN sessions emit `submit_intents_*.json` (`INTENT_ONLY`, `require_confirm_before_submit`) only.

---

## 7. Pitfalls checklist

1. Confusing Exact T+1 fill cash with T+2 settled cash → wrong liquidity.  
2. Reusing E22_v3 receivable for trades.  
3. Calendar +2 across 国定假 / 颱風假.  
4. Double-counting: subtracting unsettled from NAV without saying “estimate”.  
5. Pending `orders.csv` rows (not yet filled) → **no** settlement obligation.  
6. Slippage in `gross` ≠ exchange print — OK for paper estimate; broker reconcile uses exchange price.  
7. Min commission — **closed** (`MIN_COMMISSION=20`); day-trade tax — v1 gap (not SSOT).  
8. Changing live cash timing to T+2 inside pipeline — **forbidden** without ACCEPT (would rewrite Exact T+1 economics).

---

## 8. Minimal API sketch (R1)

```text
nth_session_after(sessions: list[date], start: date, n: int) -> date

estimate_fill(fill: dict, sessions) -> dict  # adds settle_date, settlement_cash

summarize(fills, sessions, asof, paper_cash) -> summary_dict
```

CLI:

```bash
python3 scripts/twse_t2_settlement_estimate.py \
  --state-dir forward/e21 \
  --asof 2026-09-15
```

---

## 9. Acceptance tests (when coded)

- Fri fill before long weekend → `settle_date` skips non-sessions  
- **Fill before 2026-07-10 typhoon → settle_date skips Fri closed day (→ Mon)**  
- BUY/SELL signs and fee reuse match a hand-computed fill row  
- `asof` with no open unsettled → unsettled_net = 0  
- Does not write `portfolio_state` / `nav.csv`  
- Dividend-only days with no fills → empty detail, summary zeros  

---

## 10. Pointers

- Fills / fees: `scripts/live_execution.py`, `scripts/live_ledger.py`  
- Pipeline day order: `scripts/e21_forward_pipeline.py`  
- Session calendar: `research/ops/TWSE_SESSION_CALENDAR_CHARTER.md` (#237) · `scripts/twse_session_sources.py`  
- Estimate CLI: `scripts/twse_t2_settlement_estimate.py`  
- Dividend receivable (orthogonal): `FORMAL_TAX_RECEIVABLE_BOOKS_CHARTER.md`  
- **除權息入帳延後** (ex vs payment; typhoon/封關): `TWSE_DIVIDEND_CREDIT_DELAY_CHARTER.md` · `twse_dividend_delay_estimate.py`  
- TWSE 款券交割時點: twse.com.tw clearing operations (T+2 營業日) · 天然災害休市顺延: `suspended.html`

Label: `TWSE_T2_SETTLEMENT_ESTIMATE__RESEARCH_CHARTER`
