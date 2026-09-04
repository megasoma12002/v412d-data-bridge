# S9A1 Paper / Monitor Runbook

Status: **MIXED overlay — paper/monitor only** (Governance Option 2)  
Not frozen. Not E45. Not production.

## Locked config (do not retune)

```
challenger_id: S9A1
bull_alpha: TECH2 (momentum_family_score, defensive_family_score)
bull_mode: BREADTH_REGIME
ridge_lambda: 1.0
portfolio: C4
  top_k: 22
  rebalance_every: 42
  exit_multiple: 2.25
  neutralization: NONE
  industry_cap: 5
  replace_rank_gap: 5
  liquidity_floor: 20_000_000

detector: COMBO_VOL70_VAL03
  not crisis_vote2
  AND rolling-252d mkt_vol_60d >= prior-window p70 (hysteresis on=2, off=5)
  AND val_ic_lag21 >= 0.03

**Live / paper feed caveat (Stage-13 R1):** the archived `val_ic_lag21` only
shifts raw IC by 1 day while labels are 21d forward. For any as-of-T monitor,
rebuild value-IC with `shift >= 21` on raw IC before the rolling mean (see
`GOVERNANCE_OPTION2_ADVERSARIAL_CAVEATS.md`). Do not retune the 0.03 / p70 cuts.

controller: FREEZE_REB
  while detector on → skip C4 rebalance dates (hold names)
  else → normal C4 cadence
```

Reference artifacts:

- `E50-A3-R1_STAGE9A_S9A1_HELDOUT.md`
- `reports/stage9a_s9a1_heldout_decision.json`
- `E50-A3-R1_STAGE11_E45C1_MONTE_CARLO.md`
- `E50-A3-R1_STAGE13_ADVERSARIAL_10ROUNDS.md`
- scripts: `e50a3r1_stage9a_s9a1_heldout.py`, `e50a3r1_stage11_e45c1_monte_carlo.py`, `e50a3r1_stage13_adversarial_10rounds.py`

## Side-by-side accounts

| Account | Description |
|---|---|
| **REF_C4** | Full-invest TECH2+C4 |
| **PAPER_S9A1** | Same alpha/rules + S9A1 freeze overlay |

Always report both. Never present S9A1 alone as “the strategy.”

## Monitor KPIs (primary)

Compare PAPER_S9A1 vs REF_C4 on each review window:

1. **Stress mean excess** (on S9A1 detector days) — want S9A1 ≥ C4  
2. **Stress compound** on those days — want S9A1 ≥ C4  
3. **Max drawdown** — prefer not much worse than C4  
4. **CAGR / utility** — informational  
5. **Average daily turnover** — stay near ≤2.5% soft ceiling  
6. **Bootstrap P(excess&gt;0)** — soft warning if &lt;0.70; **not** an auto-kill for paper mode  

## Cadence

- After each month-end (or each research refresh of PIT panel): rebuild REF_C4 and PAPER_S9A1 NAVs  
- File a short note: KPI table + whether stress edge still holds  
- If stress edge flips negative for **two consecutive** review periods → pause paper overlay and reopen research (new info set), do **not** retune detector  

## Red lines

- No parameter search on 2019–2022 / 2023–latest for this lock  
- No claiming PASS_HELDOUT or frozen promotion from monitor results alone  
- No in-place E45 edits “to match S9A1”  

## How to regenerate comparison

From repo root (data paths as in prior stages):

```bash
PYTHONPATH=scripts python3 scripts/e50a3r1_stage11_e45c1_monte_carlo.py \
  --panel /tmp/a2/causal_factor_panel.parquet \
  --labels /tmp/a2/forward_labels_research_only.parquet \
  --prices /tmp/a0/point_in_time_universe.csv \
  --actions /tmp/a1/corporate_action_ledger.csv.gz \
  --a2-qc /tmp/a2/qc_status.json \
  --out repro/e50a3r1-turnover-diagnosis-20260903 \
  --draws 2000
```

For a single held-out-style refresh of S9A1 vs C4:

```bash
PYTHONPATH=scripts python3 scripts/e50a3r1_stage9a_s9a1_heldout.py \
  --panel /tmp/a2/causal_factor_panel.parquet \
  --labels /tmp/a2/forward_labels_research_only.parquet \
  --prices /tmp/a0/point_in_time_universe.csv \
  --actions /tmp/a1/corporate_action_ledger.csv.gz \
  --a2-qc /tmp/a2/qc_status.json \
  --stage9a-summary repro/e50a3r1-turnover-diagnosis-20260903/reports/stage9a_e45c1_freeze_orth_oof_summary.json \
  --out repro/e50a3r1-turnover-diagnosis-20260903
```

## Baseline snapshot (at acceptance)

Validation 2019–2022 (from Stage-9A / Stage-11):

| | S9A1 | C4 |
|---|---:|---:|
| CAGR | 23.5% | 21.7% |
| MDD | −29.8% | −31.9% |
| Bootstrap | 0.623 | 0.559 |
| Stress mean excess | 0.00078 | 0.00035 |
| Val stress MC P(beat C4) | ~0.94–0.95 | — |
