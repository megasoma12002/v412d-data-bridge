# FIN Within-Sleeve Observe Posture — LOCKED (hold)

Date: 2026-09-08 · live KD_OPT 2026-09-09 · hold posture 2026-09-09  
Status: **LOCKED** · Stage D **OPERATING OBSERVE** · live **`KD_OPT` HOLD**  
Soft-Frozen: **[0.60, 0.90] LIVE** (FINBAND) · live within-sleeve **`FIN_PRE_EXDIV_KD`** · E45 stitch **`BLEND_E45_A05` LIVE**  
Cutover notes: `FIN_WITHIN_SLEEVE_CUTOVER_ACCEPTED_KD_OPT.md` · `SOFT_FROZEN_CLIP_FLIP_ACCEPTED_FINBAND.md` · `E45_STITCH_ACCEPTED_BLEND_A05.md`

## Binding hold (updated 2026-09-09 EXECUTED)

Human「請都做」executed clip flip + E45 A05 stitch. Continuing month-end observe on the new live stack.

1. **Maintain live `KD_OPT`** — no further FIN within-sleeve param / season / mix probes unless new human OPEN.  
2. **Month-end observe** — refresh `FIN_EQUAL` ∥ `FIN_RS_SOFT_TILT_EXDIV` ∥ `MIX_L75` ∥ `KD_OPT`; read tip + held-out.  
3. **Soft-Frozen KEEP** — clip flip needs dedicated ballot (path to larger P&L move).  
4. **No FIN sleeve micro-tuning** — autumn / dual-season / EQUAL×KD already STOP or paper-exhausted.  
5. **「大勝」paths (separate ballots only)** — Soft-Frozen clip change **or** new mechanism (e.g. E45 stitch second ACCEPT); not another KD variant.

## Posture (4 paper books + live)

| Layer | Policy |
|---|---|
| Live Financial within-sleeve | **`KD_OPT`** / `FIN_PRE_EXDIV_KD` / `KD_APR15_MAY15_Klt30_T15` |
| Live Telecom / 0050 | EQUAL |
| Paper observe | EQUAL ∥ RS_EXDIV ∥ MIX_L75 ∥ KD_OPT @ 500M |
| Soft-Frozen | **[0.50, 0.95] KEEP** |

## Operating paths

| Role | Path |
|---|---|
| Pack | `scripts/ops_month_end_paper_pack.py` (`--refresh-ledgers` as needed) |
| Ledgers | `scripts/e16_fin_within_sleeve_dual_paper_ledgers.py` |
| Monitor | `scripts/e16_fin_within_sleeve_month_end_monitor.py` |

## Tip / held-out reading guide

| Book | Expect |
|---|---|
| **`KD_OPT` (live)** | Tip YTD+1y PASS; held-out score ~+0.65 design |
| **`MIX_L75`** | Tip PASS; held-out score > 0 (coexist reference) |
| **`FIN_RS_SOFT_TILT_EXDIV`** | May tip PAUSE; held-out ~+0.54 design |

## Hard non-actions

- No Soft-Frozen flip without dedicated ACCEPT  
- No further FIN within-sleeve micro-tune / autumn reopen from this posture  
- No Stage B hard reopen  
- No E45 stitch without **second** human ACCEPT  
- No history rewrite  

## 「大勝」ballot gate

| Path | Prerequisite |
|---|---|
| Soft-Frozen clip change | Dedicated human ballot + evidence pack |
| New mechanism (E45 stitch / other) | Charter + observe green + **second** ACCEPT where required |
| FIN within-sleeve retune | **Not** the default path — exhausted for this cycle |

## Label

`FIN_WITHIN_SLEEVE_HOLD_2026-09-09__KD_OPT_LIVE__MONTH_END_OBSERVE__NO_FIN_MICROTUNE__SOFT_FROZEN_KEEP`
