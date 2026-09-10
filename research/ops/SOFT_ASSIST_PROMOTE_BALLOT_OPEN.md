# Soft-Assist Promote — Ballot OPEN

Date: 2026-09-10  
Status: **OPEN** — awaiting human reply  
Evidence: `KD_SOFT_TEL_SLEEVE_RESEARCH_SCREEN.md` (#182)  
Soft-Frozen **KEEP** · live **`KD_OPT` KEEP** until ACCEPT · live **`TEL_EQUAL` KEEP** · E45 stitch **OFF**

## Purpose

Decide whether the tip-clean **soft-assist** paper lift (score boost / sell soft-tilt — **not** hard AND gates) advances to paper observe and/or live cutover.

Hard AND assists previously returned **`ASSIST_NO_LIFT`**. Soft weights returned **`BEATS_LIVE`** (paper).

## Champion (recommended)

| Field | Value |
|---|---|
| Id | `SOFT_BOTH__BELOW_MA120__RSI6_GT80` |
| Base | Live `KD_OPT` = `KD_APR15_MAY15_Klt30_T15` (season / K / pre-ex **unchanged**) |
| Buy soft | `kd_scores + 1.0 · BELOW_MA120` (weight boost, no extra buy gate) |
| Sell soft | `fin_sell_scores` soft-tilt on `RSI6_GT80` (not hard `sell_ok`) |
| Telecom / Soft-Frozen | EQUAL / FINBAND unchanged |

Paper (asof 2026-09-09): held-out **0.631** vs live **0.541** (Δ **+0.090**); tip YTD+1y **PASS**; MDD↑ **+0.745** pp; CAGR giveback **+0.228** pp.

## Honesty

- Lift is tip-clean but **not** 「大勝」magnitude.  
- Soft-assist is a **new within-sleeve mechanism** on top of KD (not a season/K micro-tune). FIN hold posture still forbids silent live param edits — this ballot is the explicit gate.  
- OPEN observe ≠ live wire. Live wire needs **ACCEPT cutover** (option C below) or a later dedicated cutover after observe.

## Reply with exactly one of

### A — OPEN paper observe (recommended first step)

```
OPEN Soft-assist observe: SOFT_BOTH__BELOW_MA120__RSI6_GT80
```

Effect: authorizes dual-paper observe `LIVE_KD_OPT` ∥ champion soft-assist (month-end tip + held-out). **No live wire.** Soft-Frozen / TEL KEEP.

### B — KEEP live (close promote this cycle)

```
KEEP live KD_OPT (no Soft-assist)
```

Effect: archive promote agenda; live stays plain `KD_OPT`; evidence retained.

### C — ACCEPT live Soft-assist cutover (skip observe)

```
ACCEPT live Soft-assist cutover: SOFT_BOTH__BELOW_MA120__RSI6_GT80
```

Effect: authorizes a **dedicated** forward-only cutover PR wiring champion soft-assist into live Financial within-sleeve (KD base + soft buy boost + soft sell tilt). Soft-Frozen / TEL / E45 unchanged. Prefer A first unless you explicitly want skip-observe.

### D — DEFER

```
DEFER Soft-assist promote
```

Effect: leave OPEN; no wire; revisit later.

### E — REJECT

```
REJECT Soft-assist promote
```

Effect: close promote this cycle (same live effect as B; stronger “do not reopen soon” signal).

## Explicit non-choices (out of ballot)

- Soft-Frozen clip flip  
- Sleeve-layer tilt (`SLEEVE_BELOW_MA60_*`) — separate option C from prior menu  
- KD season / K / pre-ex retune  
- Telecom within-sleeve change  
- E45 stitch  

## After OPEN observe (if A)

Only if tip stays clean and held-out lift holds → bring a **cutover** ACCEPT (same C string or a refreshed cutover ballot). Checklist to draft on ACCEPT path: `CUTOVER_CHECKLIST_SOFT_ASSIST.md` (not yet drafted until C or post-observe cutover).

## Label

`SOFT_ASSIST_PROMOTE_BALLOT_OPEN_2026-09-10__AWAIT_HUMAN__LIVE_KD_KEEP`
