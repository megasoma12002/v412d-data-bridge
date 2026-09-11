# External Borrow Notes — Soft-assist ∥ Sleeve-tilt ∥ Month-end promote

Date: 2026-09-11  
Status: **REFERENCE ONLY · NO LIVE WIRE · NO AUTO-COMBO**  
Scope: Map public quant-practitioner hygiene onto **our** dual observes and month-end paper gates.  
Does **not** reopen stopped Stage A screens. Does **not** authorize Soft-assist × Sleeve-tilt combo.

| Local posture | Path |
|---|---|
| Soft-assist observe | `SOFT_ASSIST_OBSERVE_POSTURE.md` · challenger `SOFT_CHAMP_PLUS_K9_LT30_a10` |
| Sleeve-tilt observe | `SLEEVE_LAYER_TILT_OBSERVE_POSTURE.md` · challenger `SLEEVE_BELOW_MA60_a01` |
| Month-end paper gates | `MONTH_END_PROMOTE_GATE_CHECKLIST.md` (Gates A–I · Soft↔Sleeve overlap column) |
| Overlap report | `SOFT_SLEEVE_OBSERVE_OVERLAP.md` (report-only) |
| Live cutovers | `CUTOVER_CHECKLIST_SOFT_ASSIST.md` · `CUTOVER_CHECKLIST_SLEEVE_LAYER_TILT.md` (**BLOCKED**) |

## Note 1 — Paper → next stage is ops, not a prettier equity curve

**Sources:** [NexusFi algo live deployment](https://nexusfi.com/a/automation/algo-trading-live-deployment) · [Quant Memo go-live checklist](https://quantmemo.com/concepts/the-go-live-checklist) · [quant-live-readiness-kit](https://github.com/cyangIIT/quant-live-readiness-kit) · [Oyamori retail checklist](https://oyamori.com/learning/retail-algo-trader-checklist/)

**Borrow:** Paper / forward observe proves **execution + data + risk plumbing** (order lifecycle, reconcile, kill switch, freeze ID, held-out). Profit during paper is a bonus, not the gate.

**Map to us:**

| External idea | Our artifact |
|---|---|
| Freeze what is running | Gate **F** (challenger ID unchanged) · posture Binding |
| Tip / trailing clean before promote | Gates **B–C** · month-end monitors |
| Held-out / OOS positive | Gate **D** |
| Alerts / monitoring clear | Gate **E** |
| Kill / no silent wire | Gate **I** + cutover **BLOCKED** until exact ACCEPT |
| Limited-live envelope | Dedicated cutover PR only (not this page) |

**Do not borrow:** Treating one clean month as sustained promote; using paper CAGR/MDD as live claim badges.

## Note 2 — Soft signal: inform trades; do not trade against them alone

**Source:** AQR [To Trade or Not to Trade?](https://www.aqr.com/Insights/Research/Journal-Article/To-Trade-or-Not-to-Trade-Informed-Trading-With-Short-Term-Signals-for-LongTerm-Investors)

**Borrow:** Fast-decaying / soft information can steer a slower book by **avoiding trades that fight the soft view**, instead of standing up a second live book that pays full turnover for the soft signal alone.

**Map to us:** Soft-assist changes **within-FIN name scores** on top of live `KD_OPT`; live stays `KD_OPT` HOLD until dedicated ACCEPT. Soft OR / add-score (not hard AND) matches “assist, don’t replace.”

**Do not borrow:** Promoting Soft-assist because the soft line alone looks good in isolation; reopening hard-AND indicator gates already `ASSIST_NO_LIFT`.

## Note 3 — Tactical tilt must clear the diversification hurdle

**Sources:** AQR [Tactical Tilts and Foregone Diversification](https://www.aqr.com/Insights/Research/White-Papers/Tactical-Tilts-and-Foregone-Diversification) · AQR [Challenges of Incorporating Tactical Views](https://www.aqr.com/-/media/AQR/Documents/Insights/Alternative-Thinking/Alternative-Thinking-Challenges-of-Incorporating-Tactical-Views.pdf)

**Borrow:** A tilt is strategic book + L/S overlay. Breakeven hit-rate rises when the two sleeves are **less** correlated — you forgo diversification. Aggressive sleeve reweights need evidence that overcomes that penalty, not just a tip-clean paper line.

**Map to us:** Sleeve-tilt (`SLEEVE_BELOW_MA60_a01`) only adjusts **router sleeve weights**; Soft-Frozen clips / KD / TEL HOLD. Gate **H** forbids proposing Soft×Sleeve combo from month-end pack. Overlap corr near zero does **not** lower the hurdle for fusion — it raises the cost of wrong fusion (you would destroy independent excess).

**Do not borrow:** Auto-increasing tilt amplitude from a single good month; joint ACCEPT of Soft + Sleeve on one ballot.

## Note 4 — “Plays well with others” ≠ auto-combine into one book

**Sources:** Allocate Smartly [Strategies That Play Well With Others](https://allocatesmartly.com/strategies-that-play-well-with-others/) · [Combining strategies & timing luck](https://allocatesmartly.com/member-analysis-the-effect-of-combining-strategies-on-timing-luck/) · [Tranching timing luck](https://allocatesmartly.com/taming-excessive-timing-luck-in-taa-by-tranching-strategies/)

**Borrow:** Low pairwise correlation / complementary behavior is a reason to **keep both tracks alive and measure them**, and can reduce timing-luck noise. It is **not** a license to fuse weights without a new charter. Combining dissimilar strategies is a portfolio-construction decision with its own ballot.

**Map to us:** `SOFT_SLEEVE_OBSERVE_OVERLAP.md` columns (corr / same-sign / both− / joint DD) feed the month-end log only. Seed heldout (2026-09-10): corr **≈−0.025**, same-sign **~55%**, both− **~26.5%**, joint DD days **~33%** → excess largely independent → **KEEP independent observe**. High or low overlap **never** unlocks combo (Gate **H**).

**Do not borrow:** Optimizer “add because low corr” → silent Soft×Sleeve product; month-end day luck shopping without documenting Gate F ID freeze.

## Note 5 — Wear the Architect hat before any fuse

**Source:** Robot Wealth [Edge Alchemy](https://robotwealth.com/edge-alchemy/) (Scientist → Engineer → Architect → Operator)

**Borrow:** Scientist = mechanism; Engineer = tradable costs; **Architect** = how two strategies interact when they disagree; Operator = today’s orders. Jumping Engineer→Operator (fuse in code because both screens looked fine) skips Architect.

**Map to us:** Dual-paper OPERATING on two actuators (name soft vs sleeve tilt) is intentional Architect separation. Promote path is month-end A–I → `READY_FOR_DEDICATED_ACCEPT_BALLOT` → human ACCEPT string → cutover PR. Combo would need a **new** charter after both coexist under Architect review — not pack green alone.

**Do not borrow:** Retail multi-bot “rolling corr > 0.7 auto-drop weaker sleeve” as a silent ops rule on these two observes (would fight KEEP OBSERVE + Gate H).

## What we explicitly skip from the open web

- PTT / retail “存股配置” threads (allocation folklore, not dual-paper governance)
- Parameter screenshots / single equity curves without held-out or tip hygiene
- Auto risk-parity / corr-drop allocators wired into Soft or Sleeve observe
- Any source that treats paper PnL as sufficient for live wire

## Operator use (month-end)

1. Run `python3 scripts/ops_month_end_paper_pack.py`.  
2. Fill `MONTH_END_PROMOTE_GATE_CHECKLIST.md` Soft and Sleeve columns (A–I).  
3. Copy overlap row from `SOFT_SLEEVE_OBSERVE_OVERLAP.md`.  
4. Re-read Notes **1 / 3 / 4 / 5** before any ballot draft; Note **2** before Soft-assist ACCEPT wording.  
5. Default verdict remains **`KEEP_OBSERVE`**.

## Non-actions

- No live Soft-assist / Sleeve-tilt / Soft-Frozen / KD / TEL / E45 wire from this page  
- No Soft-assist × Sleeve-tilt auto-combo or joint ACCEPT  
- No reopen of STOP Stage A (dry-powder, ETF ex-calendar, hard-AND indicators, …)  
- No claim badges from paper numbers  

## Label

`EXTERNAL_BORROW_NOTES_2026-09-11__SOFT_SLEEVE_MONTH_END__NO_LIVE__NO_COMBO`
