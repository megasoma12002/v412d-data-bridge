# Tip-safe FAST — Paper Charter (R2 Stage B)

Date: 2026-09-25  
Status: **PAPER CHARTER OPEN** · Stage B screen pending  
Parent: `HELD_MDD17_R2_CAGR0_PAPER_CHARTER` · Human band floor **−14.5%** ACCEPT  
Soft-Frozen tip: **KEEP** · live clip / FUSE / DH: **KEEP** (no live wire)

Label: `HELD_MDD17_R2_TIPSAFE_FAST_STAGEB_CHARTER_2026-09-25__PAPER_OPEN__NO_LIVE_WIRE`

## Why Stage B

Stage A near-band best CAGR signal: **`FAST_x08_ex06_f50_d21`**

| window | CAGR | MDD | vs LIVE |
|---|---:|---:|---|
| held-out 2019+ | 15.00% | −14.45% | giveback **+0.56 pp** (in ACCEPT band) |
| paper tip YTD / 1y | — | — | **MDD worse** (~−0.99 pp) → hygiene **fail** |

Ask: can a **finite tip-safe FAST** family keep held MDD in **[−14.5%, −13%]** and held giveback **near +0.56 pp** (cap ≤ **0.70 pp**), **and** clear tip YTD/1y `mdd_improve_pp >= 0`?

## Non-actions

- No live wire · no Soft-Frozen flip · no open search  
- No ledger/tip history rewrite  
- Stage A roles other than FAST are out of scope (controls only)

## Stage B tracks (tip-safe variants of FAST)

Offense = paper `LIVE_STACK` · Stage-E DEFAULT · current ledger.  
Anchor control: `FAST_x08_ex06_f50_d21` (expected tip fail).

| Track | Causal tip-safety idea |
|---|---|
| `FLOOR_UP` | Same FAST enter/exit; **higher floor** (cut less in mild/tip windows) |
| `DUAL_ENTRY` | Enter only if PROXY ≤ −x **and** book MDD63 ≤ −b |
| `FAST_EXIT` | Quicker rebound exit / shorter max-dwell |
| `BOOK_GATE` | Enter only if book peak DD already ≤ −g (no cut from flat tip) |
| `COOL_EXT` | Longer post-exit cooldown (anti re-churn into tip dips) |

Finite grids freeze in `scripts/held_mdd17_r2_tipsafe_fast_stageb_screen.py`.

## Targets (held-out + tip)

| Metric | Target |
|---|---|
| held MDD band | `−0.145 ≤ max_drawdown ≤ −0.13` |
| held CAGR giveback | preserve class ≤ **0.70 pp** (stretch ≤ **0.56 pp**) |
| tip YTD + trailing 1y | `mdd_improve_pp >= 0` each |

## Verdicts

| Verdict | Meaning |
|---|---|
| `TIPSAFE_STRETCH` | band + tip OK + gb ≤ 0.56 pp |
| `TIPSAFE_PRESERVE` | band + tip OK + gb ≤ 0.70 pp |
| `TIPSAFE_OK` | band + tip OK + gb ≤ 1.00 pp |
| `TIP_FAIL` | band hit but tip hygiene fail (incl. FAST anchor) |
| `NO_BAND` | no recipe in MDD band |

Even HIT → **paper observe ballot only**; never live wire from Stage B.

## Artifacts

- Charter: `research/ops/HELD_MDD17_R2_TIPSAFE_FAST_STAGEB_CHARTER.md`  
- ZH: `research/ops/HELD_MDD17_R2_TIPSAFE_FAST_STAGEB_CHARTER.zh-TW.md`  
- Screen: `scripts/held_mdd17_r2_tipsafe_fast_stageb_screen.py`  
- Report: `research/ops/HELD_MDD17_R2_TIPSAFE_FAST_STAGEB_SCREEN.md` · `repro/held-mdd17-r2-tipsafe-fast-stageb/`
