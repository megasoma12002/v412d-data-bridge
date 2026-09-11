# ETF Ex-Calendar — Stage A Research Charter (paper only)

Date: 2026-09-11  
Status: **PAPER DONE / STOP ARCHIVE** (Stage A verdict **`NEAR_NO_BEAT`** · **no live wire**)  
Human: **開一張很窄的 ETF ex-calendar Stage A charter（只測 paper、不上 live）** → screen executed  
Soft-Frozen **KEEP** · live **`KD_OPT` KEEP** · **`TEL_EQUAL` KEEP** · E45 stitch **OFF** · Soft-assist observe **UNCHANGED** · Sleeve-tilt observe **UNCHANGED**  
Screen: `ETF_EX_CALENDAR_SCREEN.md` · script `scripts/e16_etf_ex_calendar_screen.py`

## Question

Does a **rules-based book around the known 0050 cash ex-date calendar** (pre-ex window long / calendar-month proxy) tip-clean beat **`BUY_HOLD_0050`** and/or coexist with **`LIVE_STACK`** after costs — without inventing `announcement_date` and without touching live?

**Hypothesis (seed, not verdict):** fixed ETF ex months (post-2016 ≈ Jan / Jul semi) leave a measurable pre-ex price wave; day-0 close drop is mostly mechanical; post-ex is weak. Stage A asks whether a **tradable** rule survives tip + held-out gates.

## Why this charter (narrow)

| Item | Note |
|---|---|
| Data | Soft-Frozen cash/stock **ex+pay blank 0%**; residual is **`0050`/`50` `announcement_date` × 27** (structural — FinMind empty / MOPS N/A / Yuanta has no announce field). Ex / pay / amount are **OK**. |
| Not a data-gap fill | Do **not** invent announce dates to “complete” E22. |
| Distinct actuator | Calendar timing on **0050 only** — not Soft-assist name scores, not sleeve-tilt router scores, not dry-powder DD gates, not E45. |
| Scope | **0050 only** in Stage A. No 0056 / 00878 / multi-ETF basket until Stage A tip-clean. |

## Live baseline (do not modify)

| Layer | Live |
|---|---|
| Soft-Frozen | FINBAND **[0.60, 0.90]** · TEL **[0.03, 0.35]** · 0050 **[0.00, 0.35]** |
| FIN within-sleeve | **`KD_OPT`** (`KD_APR15_MAY15_Klt30_T15`) |
| TEL / 0050 | EQUAL |
| Books / capital / lot | `E22_v2s_tw` · 500M · board-lot 1000 |
| E45 | stitch **OFF** |
| Observes | Soft-assist K9+ · Sleeve-tilt `SLEEVE_BELOW_MA60_a01` — **do not wire, pause, or auto-combo** |

## Mechanism (paper)

### Calendar sources (causal rules)

| Source id | Definition | Look-ahead note |
|---|---|---|
| `MONTH_PROXY` | **Primary.** For sessions on/after **2016-01-01**: long window in **January** and **July** only. Pre-2016: **October** only (historical annual schedule). Window = first **W** trading days of that month (**W ∈ {10, 15}**). | No use of that year’s exact ex day. |
| `EXACT_EX` | **Sensitivity.** Use realized `cash_ex_date` from E22 code `50` / Yuanta `0050` ledger. Long **[T−N, T−1]** trading days (exit before ex). **N ∈ {10, 20, 40}**. | Ex dates are public schedule facts in this ledger; **announce is blank** — treat as sensitivity, not primary claim of “known before price path.” |

Do **not** use cash amount, payment date, or invented announce to size or gate entries in Stage A.

### Book families (finite)

| Family | Rule |
|---|---|
| `BUY_HOLD_0050` | Baseline: 100% 0050 (adj), hold. |
| `LIVE_STACK` | Baseline: Soft-Frozen + KD_OPT + TEL_EQUAL (unchanged). |
| `CAL_LONG_0050` | Cash → 100% 0050 inside calendar window (`MONTH_PROXY` or `EXACT_EX`); else cash. |
| `CAL_OVER_BH` | Same long windows as `CAL_LONG_0050`, but **flat = buy&hold 0050** outside window (tests “add timing on top of BH”). |

**Stage A cap:** ≤ **~12** challengers + 2 baselines (≤ **14** books). Default grid:

1. `MONTH_PROXY` × W∈{10,15} × {`CAL_LONG_0050`, `CAL_OVER_BH`} → **4**  
2. `EXACT_EX` × N∈{10,20,40} × {`CAL_LONG_0050`, `CAL_OVER_BH`} → **6**  
3. Optional single stress (only if capacity): `EXACT_EX` N=20 hold through **T+5** (`HOLD_THRU`) — **1** book, report separately as mechanical-drop stress  

No β-hedge, no shorts, no levered pre-ex, no Soft-Frozen weight overlay in Stage A.

### Costs / lot

Same Exact T+1 / cost assumptions as other e16 paper screens; board-lot **1000**; report turnover.

## Design honesty

- Pre-ex positive adj returns in a quick study are **in-sample / unadjusted for β and cost** — Stage A must re-score with costs.  
- Day-0 ex close drop is largely mechanical — beating BH by exiting T−1 may just avoid the drop, not prove alpha. Report both vs BH and vs `LIVE_STACK`.  
- Month proxy avoids announce look-ahead; exact-ex is labeled sensitivity because announce is blank on all 27 E22 rows.

## Finite Stage A screen

1. Baselines: `BUY_HOLD_0050` · `LIVE_STACK`.  
2. Challengers: grid above (cap ≤14 books total).  
3. Metrics per book: full / `heldout_2019_plus` / `sealed_2023_plus` **CAGR + MDD**; tip YTD + trailing 1y vs **both** baselines; held-out score vs each baseline.  
4. Verdict labels: `NO_LIFT` · `COEXIST_NO_LIFT` · `BEATS_BH_ONLY` · `BEATS_LIVE` · `NEAR_NO_BEAT`.

## Gates

| Gate | Rule |
|---|---|
| Tip vs BH | YTD + 1y vs `BUY_HOLD_0050`: PASS (ALERT 3pp / PAUSE 5pp giveback) |
| Tip vs live | Same vs `LIVE_STACK` |
| Coexist vs live | tip-clean vs live **and** held-out score > 0 vs live |
| Beat-live | coexist **and** held-out Δ > 0 vs live self |
| Beat-BH | tip-clean vs BH **and** held-out score > 0 vs BH |
| Sealed | report-only for Stage A |

**Observe / live:** Stage A tip-clean beat-live → draft **OPEN observe** ballot only on human ask. **Never** auto-wire live. Soft-assist / sleeve observes stay independent (no auto-combo).

## Artifacts (Stage A)

| Role | Path |
|---|---|
| Charter | `research/ops/ETF_EX_CALENDAR_STAGE_A_CHARTER.md` (this file) |
| Charter (zh) | `research/ops/ETF_EX_CALENDAR_STAGE_A_CHARTER.zh-TW.md` |
| Charter (json) | `research/ops/ETF_EX_CALENDAR_STAGE_A_CHARTER.json` |
| Screen script | `scripts/e16_etf_ex_calendar_screen.py` |
| Results | `research/ops/ETF_EX_CALENDAR_SCREEN.md` (+ `.json` · `.zh-TW.md`) |
| Repro | `repro/etf-ex-calendar/` |
| Calendar inputs | `data/dividend_events/e22_dividend_events.csv` (code `50`) · `research/ops/yuanta_etf_div_0050.json` |

## Non-actions

- No live Soft-Frozen / KD_OPT / TEL / E45 change  
- No Soft-assist or sleeve-tilt observe retarget / pause / auto-combo  
- No inventing `announcement_date`  
- No multi-ETF expansion in Stage A  
- No Soft-Frozen 0050 clip flip or sleeve-weight overlay in Stage A  
- No “fill announce gap” research disguised as this charter  

## Out of scope

- Payment-date / receivable books  
- KD pre-ex T−15 retune (already locked in live `KD_OPT`)  
- Dividend-capture tax / odd-lot mechanics beyond existing `E22_v2s_tw`  
- Stage B observe dual-paper until Stage A + human ballot  

## Stage A outcome (2026-09-11)

- Books: **13** (2 baselines + 10 grid + 1 HOLD_THRU stress).
- Verdict: **`NEAR_NO_BEAT`** — tip-clean vs live **5** (all `CAL_OVER_BH` ≡ `BUY_HOLD_0050`) · beat-live **0** · coexist **0** · beat-BH **0**.
- `CAL_LONG_*` often improve held-out MDD vs live via cash drag, but tip YTD/1y **PAUSE_REVIEW** (return giveback) → no coexist.
- Decision: **STOP / archive**. Live Soft-Frozen / KD / TEL / E45 and Soft-assist / sleeve observes **unchanged**. **No live wire.**

## Success → next step

| Outcome | Next |
|---|---|
| `BEATS_LIVE` or strong coexist | Draft **OPEN observe** ballot (`LIVE_STACK` ∥ champion) — human only |
| `BEATS_BH_ONLY` | Archive as calendar curiosity; **no** live/observe path unless human expands charter |
| `NO_LIFT` / `NEAR_NO_BEAT` / fail tip | **STOP** / archive; live + observes unchanged |

**Applied:** Stage A → **STOP / archive** (`NEAR_NO_BEAT`); live unchanged.

## Label

`ETF_EX_CALENDAR_STAGE_A_CHARTER_2026-09-11__PAPER_DONE_STOP__NEAR_NO_BEAT__NO_LIVE`
