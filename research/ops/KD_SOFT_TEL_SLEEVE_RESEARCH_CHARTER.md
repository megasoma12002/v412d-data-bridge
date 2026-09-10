# KD Soft / TEL / Sleeve Research Charter (paper)

Date: 2026-09-10  
Status: **PAPER DONE** (screen complete · no live wire)  
Human: **「理論上還能開、但未測／勝算低 — 軟輔助 · 改 KD 季節／門檻 · 電信／sleeve 層指標 — 這幾個研究研究」**  
Soft-Frozen **KEEP** · live **KD_OPT KEEP** · live **TEL_EQUAL KEEP** · FIN posture **no micro-tune** for live · E45 stitch **OFF**

## Context

Hard-gate indicator assists on `LIVE_KD_OPT` returned **`ASSIST_NO_LIFT`** (`KD_OPT_INDICATOR_ASSIST_SCREEN.md`).  
Three remaining low-odds paper paths were not covered by that hard-AND screen.

## Tracks

| Track | Question | Mechanism (paper) |
|---|---|---|
| **A Soft assist** | Can **score boost** (not hard block) lift live KD? | Buy: `kd_scores + boost·low_i`; Sell: `fin_sell_scores` soft-tilt on high_j (no `sell_ok`) |
| **B KD retune** | Does any season × K × pre-ex beat live lock? | Grid vs `LIVE_KD_OPT`; posture locks live micro-tune — paper only |
| **C TEL / sleeve** | Do Telecom within-sleeve or E16 sleeve-score indicators help? | TEL policies / KD / soft tilt; sleeve score tilt → rebuilt Soft-Frozen targets |

## Gates

- Coexist vs `FIN_EQUAL`: tip YTD+1y PASS and held-out score > 0  
- Beat-live: coexist **and** held-out score > `LIVE_KD_OPT` (Track C also reports vs live stack with `TEL_EQUAL`)

## Artifacts

- Script: `scripts/e16_kd_soft_tel_sleeve_research.py`
- Results: `research/ops/KD_SOFT_TEL_SLEEVE_RESEARCH_SCREEN.md` (+ `.json`)
- Repro: `repro/kd-soft-tel-sleeve-research/`

## Non-actions

- No Soft-Frozen flip  
- No live KD_OPT param change / FIN micro-tune without dedicated ACCEPT  
- No live TEL_EQUAL flip  
- No E45 stitch  

## Label

`KD_SOFT_TEL_SLEEVE_RESEARCH_2026-09-10__PAPER_ONLY__LIVE_KEEP`
