# Live fill extreme + mechanism audit (paper / observe)

Date: 2026-09-26  
Status: **CHARTER OPEN · AUDIT RUNNING** · Soft-Frozen live **KEEP** · no live wire / no tip rewrite  
Human: 事後審計（fill vs 高低）+ 機制對照（clip／T+1／COOL／KD）

Scope: `forward/e21/fills.csv` executed tip fills (observe ledger).  
Note: tip fill window **2026-08-25 → 2026-09-16** predates COOL live ACCEPT (2026-09-25); tip defense stamp was **DH**. Audit reports **both** tip `dh_exposure` (historical) and reconstructed **`COOL_c8`** (current-stack twin) for stratification.

Label: `LIVE_FILL_EXTREME_AUDIT_CHARTER_2026-09-26__OPEN`

**Audit ≠ live change · ≠ Soft-Frozen flip · ≠ tip history rewrite.**

---

## A — Fill vs local extreme

For each fill, vs OHLC on the **fill code**:

| Metric | BUY | SELL |
|---|---|---|
| Primary | `(px − low_N) / low_N` | `(high_N − px) / high_N` |
| Window | ±**N** calendar trading days around **fill_date** | same |
| N grid | **5 · 21** | |

Strata: sleeve **FIN / TEL / 0050** · side · defense (tip DH & reconstructed COOL).

## B — Mechanism contrast (same window)

On each fill’s `signal_date`, tag which mechanisms were **binding / active**:

| Tag | Rule |
|---|---|
| `T1_DRAG` | Always on Exact T+1; quantify `(fill_px − signal_day_ext) / signal_day_ext` (BUY vs low, SELL vs high) |
| `CLIP_BOUND` | Soft-Frozen sleeve weight at tip signal sits on FIN/TEL/0050 clip edge (±1e-4) |
| `DEFENSE_DH` | Tip `dh_exposure < 1` (historical live defense) |
| `DEFENSE_COOL_CF` | Reconstructed COOL_c8 exposure `< 1` on signal_date (counterfactual current stack) |
| `KD_OFFSEASON` | FIN fill outside KD_OPT season Apr15–May15 |
| `KD_BUY_BLOCK` | FIN BUY while `pre_exdiv buy_ok=False` (if reconstructable) |

“擋掉” here = **binding on that fill day** (not a separate rejected-order log — tip does not store refusals).

## Out of scope

- Soft-Frozen / KD / COOL / TEL live retune  
- Tip wipe/replay · broker  

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/live_fill_extreme_audit.py
```

Artifacts: `research/ops/LIVE_FILL_EXTREME_*` · `repro/live-fill-extreme-audit/`
