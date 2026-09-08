# FIN EQUAL × RS_EXDIV λ-mix — coexistence probe

Generated: `2026-09-08T10:56:40.658816+00:00`
Soft-Frozen **KEEP** · live wire **false**
Status: **COEXIST_CANDIDATE_FOUND**

Definition: `λ·FIN_EQUAL + (1−λ)·FIN_RS_SOFT_TILT_EXDIV` (notional blend → 整張)
Coexist rule: held-out score > 0 **and** tip YTD+1y both PASS (giveback ≤ 3pp)

## Grid vs `FIN_EQUAL`

| id | λ(EQUAL) | heldout score | MDD↑pp | CAGR giveback | YTD gate | 1y gate | coexist? |
|---|---:|---:|---:|---:|---|---|---|
| `FIN_EQUAL` | 1.00 | — | — | — | PASS | PASS | — |
| `FIN_RS_SOFT_TILT_EXDIV` | 0.00 | 0.540 | 1.112 | 1.144 | PAUSE_REVIEW | PAUSE_REVIEW | False |
| `MIX_L25` | 0.25 | 0.383 | 0.900 | 1.033 | PAUSE_REVIEW | PAUSE_REVIEW | False |
| `MIX_L50` | 0.50 | 0.252 | 0.602 | 0.701 | ALERT | ALERT | False |
| `MIX_L75` | 0.75 | 0.129 | 0.303 | 0.346 | PASS | PASS | True |

## Tip giveback (vs EQUAL, asof tip)

| id | λ | YTD giveback pp | 1y giveback pp |
|---|---:|---:|---:|
| `MIX_L75` | 0.75 | 2.00 | 2.20 |
| `MIX_L50` | 0.50 | 3.54 | 4.01 |
| `MIX_L25` | 0.25 | 5.12 | 5.63 |
| `FIN_RS_SOFT_TILT_EXDIV` | 0.00 | 5.90 | 6.44 |

## Verdict

**Coexist candidate: `MIX_L75` (λ=0.75 EQUAL / 0.25 RS_EXDIV)** — held-out **+0.129** and tip YTD/1y both **PASS**.

Tradeoff is smooth on this grid: more EQUAL → tip cleaner, less held-out MDD lift. Pure RS_EXDIV still best held-out (+0.540) but remains tip **PAUSE**. Mid λ (`MIX_L50`) is tip **ALERT** only — not tip-clean under the ≤3pp rule.

**Next (optional, not this ballot):** add `MIX_L75` as a third dual-paper observe leg, or replace RS_EXDIV challenger with mix for tip-clean observe. Live wire still **FORBIDDEN** until dedicated ACCEPT.

## Hard rules

- Soft-Frozen KEEP · no live wire
- Does not reopen Stage B hard TOP1/TOP2
- Dual-paper OPERATING observe for pure RS_EXDIV unchanged

Repro: `repro/fin-equal-rs-mix-20260908/`
