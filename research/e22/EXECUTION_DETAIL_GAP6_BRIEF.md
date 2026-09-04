# Gap #6 — Execution-Detail Simplifications (Dividends / Lots)

Date: 2026-09-04  
Scope: How official and research paths handle cash/stock dividends, tax, odd lots, and payment-date cashflow vs live custody.  
Status: **research brief only** — does not rewrite SOFT_FROZEN E22_v2 / Exact T+1.

Related (not rewritten here):

- `FROZEN_STRATEGY_SPEC.md` Layer-2 lifecycle checklist (ex → receivable → pay → tax → odd lot)
- `research/e22/DIVIDEND_LEDGER_COMPLETE.md`, `STOCK_DIVIDEND_LEDGER.md`
- Sibling branches: `cursor/e22-v2s-formal-stock-d049`, `cursor/e22-v3-h1-payment-d049`, `cursor/e22-stock-div-research-d049`

Gap #6 is the **execution-economics fidelity** gap left after G5 wiring (E22 cash-ex into an official path). Ledger fields are largely complete; the **sim still simplifies** what a broker/custody book actually does.

---

## 1. What each path models today

| Surface | Cash dividends | Stock dividends | Payment date | Sell tax | Dividend tax | Lot policy |
|---|---|---|---|---|---|---|
| Live `scripts/e21_forward_pipeline.py` + `forward/e21/` | **None** | None | Unused | TAX_STOCK 30bp / TAX_ETF 10bp on **sells only** | None | `int(value/price)` (1-share; not 1000 board lot) |
| Official E22_v2 (`scripts/e22_v2_forward_pipeline.py`, sibling branch) | Credit `shares×cash_div` on **`cash_ex_date`** | **Not applied** | Ledger complete; **not used for cash** | Same sell tax | None (TAX0) | Same `int(...)` |
| Challenger `scripts/e50_early_stack_combined_nav.py` (this repo) | Same ex-date cash credit when `apply_e22` | Optional `shares *= 1+stock/10` on **`stock_ex_date`** | Delivery only (docs); not NAV clock | Same sell tax | None | `lot_qty` = `int(abs(value)/price)`; sells `int(pos)` |
| Formal books module `e22_dividend_accounting.py` (v2s branch) | Cash on ex-date (`E22_v2` / `E22_v2s`) | `E22_v2s` only | Stored on events; not applied as cash clock | N/A (accounting helper) | None | Caller still truncates with `int(pos)` |
| E22_v3 H1 sandbox | Ex vs **pay** credit | Not the H1 axis | **Used** as credit clock | Sell tax unchanged | Research haircut 0/10/20% | Same |

### Script notes

- **`e21_forward_pipeline.py`**: Exact T+1 open ±5bp; fees 14.25bp×0.6; **no** dividend ledger read.
- **`e50_early_stack_combined_nav.py`**: copies E21 loop; E22 cash on ex; stock optional; payment date explicitly “delivery only”.
- **`e22_dividend_accounting.py`** (sibling): canonical `E22_v2` vs `E22_v2s`; forbids `adj_close` NAV + share increase double-count.
- Official v2 cutover: seed from E21 positions/cash; **no historical dividend backfill** into prior live NAV.

---

## 2. Gap inventory

| # | Item | Modeled | Missing / simplified | Severity |
|---|---|---|---|---|
| 6.1 | Cash credit clock | Ex-date cash into `cash` (v2 / challenger) | No dividend **receivable** asset; cash arrives economically early vs custody | **Med** for cash/liquidity & pay-date PnL; **Low** for raw-price total-return mark if price gaps on ex |
| 6.2 | Payment-date cashflow | Ledger fields **complete** (144/144 cash, 52/52 stock after Yahoo) | Official path ignores pay date; v3 H1 interesting but **not promoted** | **Low–Med** (ops liquidity); research util lift ~0.002 thin |
| 6.3 | Dividend / withholding tax | Sell-side 證交稅 only | No resident/non-resident dividend tax; v3 H2 haircuts hurt util badly | **Med** if comparing to after-tax live books; **Low** if labeled pre-tax research |
| 6.4 | Stock dividends | Challenger / v2s: share factor on stock ex | Official v2 **cash-only** → understates holdings when marking raw close (~**+2.5 pp CAGR** correction in research) | **High** for total-return books on raw close; **governance** if promoting |
| 6.5 | Fractional shares | Float positions after stock factor | Sells use `int(pos)` → **stranded fractions**; no cash-in-lieu / odd-lot disposal | **Med** (accumulates; e.g. 0.264 元/股 → non-integer adds) |
| 6.6 | Taiwan board lot (整股 1000) | 1-share “lots” | No 整股 rounding; no 零股 market (worse fill / separate session) | **Med–High** for live capacity realism; **Low** for relative sleeve research at 3M capital if mostly ≥1000 |
| 6.7 | Spec extras (supplementary premium, reinvestment date, fill/non-fill) | Not modeled | Listed in `FROZEN_STRATEGY_SPEC` lifecycle; untouched | **Low** for current core universe / research priority |
| 6.8 | Live vs research split | Research full-history; live cutover-forward | E21 live still no div; v2 live from cutover only; research NAV ≠ live history | **High** for “published CAGR” vs “live ledger” confusion — label carefully |

Severity key: High = wrong economics or identity risk; Med = material cash/NAV drift; Low = documented limitation OK for now.

---

## 3. Options to close each gap

| Gap | Research proxy (sandbox OK) | Formal books / live version |
|---|---|---|
| 6.1 / 6.2 Timing | Keep ex-date for continuous NAV with raw prices; optional dual book: receivable on ex, cash on pay (mark receivable at cash amount) | New version id only (`E22_v3_CASH_PAY_*` or receivable books). Do **not** edit `forward/e22_v2/`. H1 stays sandbox until explicit approval |
| 6.3 Div tax | Keep TAX0 as optimistic research; publish H2 10/20% haircut sensitivity beside results | Formal: pick one rule (e.g. net cash after assumed withholding) as **named** books version; still sell-tax separate |
| 6.4 Stock shares | Already: `E22_CASH_PLUS_STOCK` / `E22_v2s` side-by-side (~13.78% vs 11.25%) | Promote **`E22_v2s`** (or equivalent) as formal raw-price books; preserve **`E22_v2` cash-only** label. Cutover-forward only — no live history rewrite |
| 6.5 Fractionals | Round shares to int on stock ex **or** track residual + cash-in-lieu at ex close | Formal: floor shares + cash-in-lieu on payment/ex; audit `dividends_applied` keys |
| 6.6 Board lots | Sensitivity: `qty = 1000 * int(value/(price*1000))`; odd-lot sell ban or haircut | Challenger lot policy under E18 (EXPERIMENTAL per `FROZEN_GOVERNANCE`); Exact T+1 unchanged |
| 6.8 Live/research | Always report three labels: E21 (no div), E22_v2 live (cutover+), research full-history | Ops docs already: no backfill into E21 |

---

## 4. Recommended staged handling (do not break Exact T+1 / SOFT_FROZEN)

**Hard constraints**

- Exact T+1 open fill clock stays HARD_FROZEN.
- Do not in-place retune E22_v2 cash-ex semantics.
- Do not rewrite `forward/e21/` history or silently merge stock into v2.

**Stage A — Label & inventory (now, zero behavior change)**

1. Treat Gap #6 as the execution-fidelity backlog after G5/T1.
2. Keep published research figures tagged: `E22_v2 cash-only`, `E22_v2s cash+stock`, `E22_v3 H1 pay-date sandbox`.
3. Document that sell tax ≠ dividend tax.

**Stage B — Formal books without touching v2 (highest EV)**

1. Land / merge `e22_dividend_accounting.py` + **E22_v2s** as the raw-price total-return books version (stock on `stock_ex_date`).
2. Live apply **cutover-forward only** (idempotent `dividends_applied.csv`); historical compare stays in `repro/e22-v2s-historical-recompute/`.
3. Exact T+1 + fee schedule unchanged.

**Stage C — Fractionals + lots (challenger under E18)**

1. After stock apply: `floor(shares)` + optional cash-in-lieu of remainder.
2. Optional board-lot sizing challenger (1000); report turnover/NAV delta vs 1-share policy.
3. Folder: `repro/e18-lot-policy-*` — do not overwrite E18 SOFT_FROZEN.

**Stage D — Payment-date / receivable (only if ops need cash timing)**

1. Keep H1 as `H1_PAY_DATE_INTERESTING_CONTINUE_SANDBOX` (thin util bar; tax kills both clocks).
2. If promoting cash timing: new `E22_v3_*` + paper parallel; prefer receivable+pay cash over “pay-date only” for NAV continuity with raw ex gaps.
3. Do not replace v2 by default.

**Stage E — Dividend tax**

1. Leave TAX0 as research default.
2. If live after-tax books required: one pre-registered net-of-tax rule as a **named** sensitivity, not a silent haircut on v2.

---

## 5. Live broker / custody vs sim

| Event | Typical TW broker/custody | Current sim |
|---|---|---|
| Cash ex-date | Price drops; **dividend receivable** booked; cash **not** yet spendable | Cash balance credited immediately |
| Cash payment date | Cash lands; receivable clears | Ignored on official path |
| Stock ex / pay | Share count up; odd lots may settle as 零股 or cash-in-lieu | Float share increase on ex (challenger); no CIL |
| Trading | 整股 1000 primary; 零股 separate / worse | Any integer ≥1 at open ±5bp, always filled |
| Tax | 證交稅 on sells; dividend income tax / withholding outside trading loop | Sell tax only; dividend gross |

So: **ex-date cash credit is a research NAV proxy**, not a custody cashflow model. Fine for total-return vs raw close; wrong for cash-buffer / margin / “can I buy tomorrow with dividend cash?” questions.

---

## 6. Key paths

| Path | Role |
|---|---|
| `scripts/e21_forward_pipeline.py` | Live E16+E18; **no** dividends |
| `scripts/e22_v2_forward_pipeline.py` | Official SOFT_FROZEN cash-ex path (sibling / promote branch) |
| `scripts/e50_early_stack_combined_nav.py` | Research combined NAV; cash + optional stock |
| `scripts/e22_dividend_accounting.py` | Canonical v2 / v2s apply helper (v2s branch) |
| `scripts/research_e22_v3_h1.py` | Pay-date vs ex-date + tax haircut sandbox |
| `data/dividend_events/e22_dividend_events.csv` | Event ledger (ex + pay complete) |
| `research/e22/DIVIDEND_LEDGER_COMPLETE.md` | Cash/stock field completeness |
| `research/e22/STOCK_DIVIDEND_LEDGER.md` / `STOCK_DIVIDEND_RESEARCH.md` | Stock factor + ~2.5 pp finding |
| `research/e22/E22_V2S_FORMAL_BOOKS.md` | Formal books rule (v2s branch) |
| `research/reopen/E22_V3_CHARTER.md` + `E22_V3_H1_DECISION.md` | H1 continue-sandbox, no promote |
| `FROZEN_STRATEGY_SPEC.md` §Layer 2 | Full lifecycle wishlist (odd lot, tax, receivable, …) |
| `FROZEN_GOVERNANCE.md` §E18/E22 | Lot/fee/tax/timing changes → EXPERIMENTAL challenger |

---

## 7. Bottom line

Gap #6 is **not** missing payment-date *data* anymore — it is **deliberate execution simplification**:

1. Official economics = **ex-date gross cash only** (E22_v2).
2. Stock shares, pay-date cash, receivable, dividend tax, board lots, and fractionals are **research/challenger** or **unmodeled**.
3. Safest next step without breaking Exact T+1 / SOFT_FROZEN: promote/label **E22_v2s stock-aware books** beside preserved v2; keep pay-date and lot/tax work in named sandboxes.
