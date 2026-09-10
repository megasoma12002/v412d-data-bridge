# Indicator Buy/Sell Mechanism Charter — Round-1 Screen

Date: 2026-09-10  
Status: **OPEN / PAPER ONLY**  
Ballot cue: human **「請開指標買賣 charter 並先做第一輪 screen」**  
Soft-Frozen: **[0.60, 0.90] KEEP** · live **KD_OPT + TEL_EQUAL** KEEP · E45 stitch **OFF**

## Intent

Ask whether **other technical indicators** (beyond live TAIEX regime + Yahoo K9) can improve **MDD** and **CAGR / tip giveback** on Exact T+1 paper NAVs — without touching live wire.

This is a **new-mechanism** path (not FIN within-sleeve KD micro-tune). FIN posture `NO_FIN_MICROTUNE` stays: live `KD_OPT` params are not re-opened from this charter alone.

## Scope

| In | Out |
|---|---|
| Paper Exact T+1 · capital 500M · lot 1000 | Live `e21` / Soft-Frozen flip |
| Soft-Frozen sleeve targets fixed (live SSOT) | E45 stitch / Soft_A densify |
| FIN within-sleeve indicator challengers | Telecom indicator grid (Round-2+) |
| Tip YTD/1y + held-out score vs baselines | Inventing announce/pay dates |

## Baselines (anchors)

| ID | Meaning |
|---|---|
| `FIN_EQUAL` | Equal-split FIN (sleeve-level Soft-Frozen only) |
| `LIVE_KD_OPT` | Live lock: `FIN_PRE_EXDIV_KD` · `KD_APR15_MAY15_Klt30_T15` |
| `FIN_RS_SOFT_TILT_EXDIV` | Existing momentum RS soft-tilt + ex-day skip |

Telecom always **`TEL_EQUAL`**. 0050 single-name.

## Round-1 challenger families (FIN only)

All use Soft-Frozen targets + Exact T+1. Indicators are **causal** (no lookahead).

| Family | Score / gate idea |
|---|---|
| `RSI14_OS_SEASON` | Season Apr15–May15: RSI(14)&lt;30 → active soft-tilt; pre-ex T−15 skip |
| `MACD_HIST_SEASON` | Same season: MACD hist&gt;0 first hit → active; pre-ex T−15 skip |
| `MA_GOLD_SEASON` | Same season: close&gt;MA20&gt;MA60 → active; pre-ex T−15 skip |
| `BB_LOWER_SEASON` | Same season: close&lt;BB lower(20,2) → active; pre-ex T−15 skip |
| `RSI14_OS_ALWAYS` | Always-on soft-tilt when RSI&lt;30; ex-day skip only |
| `MACD_HIST_ALWAYS` | Always-on when MACD hist&gt;0; ex-day skip only |
| `MA_GOLD_ALWAYS` | Always-on MA gold; ex-day skip only |
| `VOL_UP_ALWAYS` | Volume &gt; 20d mean & close&gt;prev → tilt; ex-day skip only |

Season windows match live KD season so Round-1 isolates **indicator vs K9**, not calendar retune.

## Gates / ranking

Same order as KD optimize:

1. **Coexist**: tip YTD+1y **PASS** AND held-out score **&gt; 0** (vs `FIN_EQUAL`)
2. Else no tip **PAUSE**, max held-out score
3. Else max held-out score

Score: `mdd_improve_pp − 0.5 · |cagr_giveback_pp|` on held-out.  
Also report vs `LIVE_KD_OPT` (must beat live on held-out **and** tip-clean to be promote-discussable).

## Pass → next

| Outcome | Next |
|---|---|
| ≥1 coexist **and** held-out ≥ live KD_OPT | Dual-paper observe OPEN (separate note) |
| Coexist but &lt; live | Archive as “no lift vs live”; optional Round-2 (TEL / sleeve-router) |
| None tip-clean | Autopsy + STOP or tighten family list |

## Non-actions

1. No Soft-Frozen / KD_OPT / TEL_EQUAL live change from this charter alone.  
2. No E45 stitch.  
3. No silent FIN KD season/K-threshold retune.  
4. No cutover without dedicated ACCEPT after observe green.

## Artifacts

| Role | Path |
|---|---|
| This charter | `research/ops/INDICATOR_BUY_SELL_CHARTER.md` |
| ZH | `research/ops/INDICATOR_BUY_SELL_CHARTER.zh-TW.md` |
| Machine stub | `research/ops/INDICATOR_BUY_SELL_CHARTER.json` |
| Screen script | `scripts/e16_indicator_buy_sell_screen.py` |
| Round-1 results | `research/ops/INDICATOR_BUY_SELL_SCREEN_R1.md` (+ `.json`) |
| Repro | `repro/indicator-buy-sell-screen-r1/` |

## Label

`INDICATOR_BUY_SELL_CHARTER_2026-09-10__PAPER_ONLY__R1_SCREEN_OPEN__LIVE_KD_OPT_KEEP`
