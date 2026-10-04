# TIPSOFT_IP3_MAJOR_DD_ATLAS_STAGEA_DECISION_PACK

Date: 2026-10-04
Register: **0kbl** · Parents: 0kbk, 0kbj, 0kbi, 0kbf · **MAJOR_DD_ATLAS_PARALLEL**
Verdict: **`MAJOR_DD_ATLAS_PARTIAL`**
Tip SHA: `a5a9e6667bacff07fa98b9ce7fbab0897fc3b006`

## Bottom line

- Best cross-era detector (excl Mar2020): `base::fuse_prem_neg5` OOS_HIT **2** non2020 **2**
- Major regime counts: CLIFF **12** · GRIND **4** · OTHER **6**
- Implication: Some cross-era lift exists but floors are uneven — consistent with 0kbk SPLIT_HIT (regime tools differ) and 0kbj OVERFIT_2020 (Mar window strongest).

## Hard keeps

- Soft KEEP · Path4 OFF · broker false · Exact T+1
- **signal ≠ apply** · soak freeze unchanged · no LIVE · no tip Soft promote
- No pre-2010/GFC claim — data not in-repo

## Next (human)

- If ROBUST: prefer multi-era detectors over Mar2020-only cash-gate narratives
- If ERA_SPECIFIC/NO_EDGE: treat 0kbj OVERFIT_2020 as confirmed; do not unlock soak
- Respect 0kbk cliff/grind specialization when designing any future Stage B

Screen: `TIPSOFT_IP3_MAJOR_DD_ATLAS_STAGEA_SCREEN.md` · Charter: `TIPSOFT_IP3_MAJOR_DD_ATLAS_STAGEA_CHARTER.md`
Repro: `PYTHONPATH=scripts python3 scripts/tipsoft_ip3_major_dd_atlas_stagea.py`
