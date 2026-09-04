# Early-Stack Combined NAV Challenger (2026-09-04)

**EXPERIMENTAL.** Does **not** edit SOFT_FROZEN E16 / E18 / E22 / E45.

## Purpose

Close the handoff gap: roles existed, but the four-layer combined portfolio was never one engine.

This sandbox:

1. Reconstructs **E16** causal target history (2012–2026 after warmup)
2. Simulates **E18** Exact T+1 fills on a full-history book
3. Wires **E22** cash dividends into a NAV *copy*
4. Audits **E45** (−13.16% MDD claim = `NOT_FOUND`; no `e45` module)
5. Runs **E45PROXY** challenger only (scale equity on E16 Crisis days) — **not** official E45

## Headline results

| Variant | CAGR | MDD | Util |
|---|---:|---:|---:|
| E16_E18 | 7.22% | −22.77% | −0.0417 |
| E16_E18_E22 | **11.19%** | −22.11% | 0.0013 |
| E16_E18_E22_E45PROXY | 10.39% | **−20.13%** | 0.0032 |

- E22 CAGR lift ≈ **+4.0 pp** (dividend cash ≈ NT$2.61m on NT$3m start)
- Exact T+1: **PASS** on all variants
- E45 official module: **still missing**; do not promote proxy

## Run

```bash
python3 scripts/e50_early_stack_combined_nav.py \
  --market forward/e21/live_market.csv \
  --dividends data/dividend_events/e22_dividend_events.csv \
  --out repro/early-stack-combined-nav-20260904
```

## Artifacts

- `EARLY_STACK_COMBINED_NAV.md`
- `reports/early_stack_combined_nav_summary.json`
- `outputs/*_daily_nav.csv`, `outputs/*_fills.csv`

## Next (not done here)

- Attach E50-A overlay as a **separate capital sleeve** on top of E16_E18_E22
- Build a real named E45 module from lineage only via challenger + higher bar
- Never overwrite `forward/e21/` ledgers or promote without governance
