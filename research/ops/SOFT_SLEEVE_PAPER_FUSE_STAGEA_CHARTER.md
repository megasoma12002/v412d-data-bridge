# Soft × Sleeve Paper Fuse — Stage A Research Charter (paper only)

Date: 2026-09-12  
Status: **PAPER STAGE A DONE** · verdict **`FUSE_PROMOTE_SHAPED_BEATS_BOTH`**  
Parent lock: `RESEARCH_POSTURE_LOCK_RULEPATH_FIRST_DL_NEW_MECH`  
Operating observes **KEEP** (independent): Soft `SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a05` ∥ Sleeve `SLEEVE_RSI14_LT30_a0225`  
Month-end Gate **H** + External Borrow Notes **4–5**: auto-fuse remains **FORBIDDEN** on the operating path.

This charter is the **Architect** exception path: a finite paper Stage A to measure whether a **constructed** Soft×Sleeve combination can promote-shaped-beat the better of the two independent observes — **without** changing dual-observe ops or opening live.

## Why this charter exists

Human ask: how to do item 3 — Soft×Sleeve fuse is a governance lock, not proof that combination is useless.  
Month-end 2026-09-11 overlap: heldout corr ≈ **+0.112**, joint-DD day frac ≈ **47%**, `high_joint_dd=True` → **anti-auto-fuse** evidence, but still allows a **dedicated** paper fuse screen under this charter.

## Mechanism (new vs independent observes)

| Layer | Independent observe today | Fuse Stage A |
|---|---|---|
| Soft-assist | FIN name soft buy/sell on KD path | Same Soft observe softs |
| Sleeve-tilt | Soft-Frozen router RSI14 tilt α=0.225 | Same Sleeve observe tilt |
| Combination | **Forbidden** on ops path | **One book applies both actuators in one `simulate_core`** |

This is a **new role / portfolio-construction mechanism** (joint actuator), not Soft-buy MLP deepen and not another RSI threshold sweep.

## Question

On the **LIVE_STACK** base, does any finite Soft×Sleeve paper fuse book clear tip-MDD hygiene and **promote-shaped-beat**:

1. Soft observe alone (stack-equivalent Soft softs), **and**
2. Sleeve observe alone, **and**
3. preferably the max held-out score of those two independents?

**Promote-shaped** = tip YTD+1y **PASS** **and** tip YTD+1y MDD not worse than `LIVE_STACK` **and** held-out score > 0.

## Finite Stage A books (8)

| # | Book ID | Construction |
|---|---|---|
| 1 | `LIVE_STACK` | Base |
| 2 | `SOFT_ONLY_ON_STACK` | Soft observe buy/sell softs · **default** Soft-Frozen router (no sleeve tilt) |
| 3 | `SLEEVE_ONLY` | Operating Sleeve observe `SLEEVE_RSI14_LT30_a0225` · live KD scores (no Soft softs) |
| 4 | `FUSE_ADDITIVE` | Soft observe softs **+** Sleeve observe router tilt (primary fuse) |
| 5 | `FUSE_SOFT_GATE_SLEEVE` | Soft softs active only on days sleeve RSI14 tilt fires (any sleeve) |
| 6 | `FUSE_SLEEVE_GATE_SOFT` | Sleeve tilt active only when Soft sell soft > 1 (overbought exit days) |
| 7 | `NAV_BLEND_50` | Post-hoc 0.5·Soft-only NAV + 0.5·Sleeve-only NAV (diagnostic; not a live book) |
| 8 | `FUSE_HALF_ALPHA` | Soft observe softs + Sleeve tilt at **α=0.1125** (half amplitude) |

Script (to implement on go): `scripts/e16_soft_sleeve_paper_fuse_stagea_screen.py`  
Artifacts: `research/ops/SOFT_SLEEVE_PAPER_FUSE_STAGEA_SCREEN.md` · `repro/soft-sleeve-paper-fuse-stagea/`

## Success / failure

| Verdict | Meaning |
|---|---|
| `FUSE_PROMOTE_SHAPED_BEATS_BOTH` | ≥1 fuse book promote-shaped and held > Soft-only **and** Sleeve-only |
| `FUSE_BEATS_ONE_NOT_BOTH` | Fuse beats one independent but not both |
| `BEATS_LIVE_NO_INDEPENDENT_LIFT` | Fuse beats `LIVE_STACK` but not the better independent observe |
| `NO_LIFT` | No promote-shaped fuse book |

Even `FUSE_PROMOTE_SHAPED_BEATS_BOTH` does **not** open ops fuse, observe swap, or live wire — needs a **separate** human ballot after Architect review.

## Explicit non-actions

- No Soft×Sleeve **auto-fuse** on month-end / dual-observe operating path (Gate H stays)  
- No Soft or Sleeve **observe swap** from this screen  
- No live Soft-assist / Sleeve-tilt / Soft-Frozen / KD / TEL / E45 wire  
- No joint ACCEPT / cutover checklist unlock  
- No Soft-buy MLP deepen / T2 Soft-buy reopen  
- No login-wall scrape  

## Preconditions to run screen

1. Human says go on this charter (this draft alone ≠ run).  
2. Dual observes still OPERATING on the IDs above.  
3. Latest month-end pack logged (2026-09-11: both `KEEP_OBSERVE`).

## Label

`SOFT_SLEEVE_PAPER_FUSE_STAGEA_CHARTER_2026-09-12__FUSE_PROMOTE_SHAPED_BEATS_BOTH`
