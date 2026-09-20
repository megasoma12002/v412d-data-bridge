# 民股 MDD V4 A0 — Sealed episode autopsy (FROZEN)

Generated: `2026-09-19T14:29:44.129124+00:00`
Status: **A0_STOP_SPAN_TOO_LONG** · A1 authorized: **False**
Window: `sealed_2023_plus` · `2023-01-03` → `2026-09-16` · n=887
Challenger: `SF4_OFFENSE` (`SF4_P60-90_V0-15_F10_KD`) vs `LIVE_PUB_KD`
Rule: deepest 3 relative-DD troughs · max span **120** sessions

## Episodes (frozen)

| rank | peak | trough | DD_rel | sessions | too_long |
|---:|---|---|---:|---:|---|
| 1 | `2024-07-12` | `2025-04-22` | -3.42% | 184 | Y |
| 2 | `2024-07-12` | `2025-05-08` | -3.14% | 195 | Y |
| 3 | `2024-07-12` | `2025-05-09` | -3.02% | 196 | Y |

## Binding

1. Soft-Frozen KEEP · sealed gate unchanged · no live wire.
2. Episode list is **FROZEN** — do not expand after A1 starts.
3. A1 **not** authorized (span too long) — Soft-Frozen KEEP.

Repro: `PYTHONPATH=scripts python3 scripts/e16_priv_mdd_sealed_episode_v4_a0.py`

Label: `PRIV_MDD_SEALED_EPISODE_A0_2026-09-19__A0_STOP_SPAN_TOO_LONG`
