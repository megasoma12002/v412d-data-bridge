# 民股／四類 × MDD New Mechanism N2 — Decision Pack

Date: 2026-09-19 · `2026-09-19T13:44:20.243241+00:00` (rerun with sink labels)  
Status: **STOP** (`STAGE_A_SCORE_POS_GATES_FAIL`) · Soft-Frozen **KEEP** · live wire **false**  
Frozen offense: `SF4_P60-90_V0-15_F10_KD` · ETF hi cap `0.35`

## Verdict

**No MDD coexist** under N2 FinPriv-scoped relocate (cash / 0050).

| Book | sink | MDD↑ held | MDD↑ sealed | tip | coexist |
|---|---|---:|---:|---|---|
| `N2_CASH_LOCAL_06` (best N2 score) | CASH | +2.00 | **−0.73** | Y | N |
| `N2_0050_LOCAL_08` (closest sealed) | 0050 | +0.44 | **−0.04** | **N** | N |
| `N2_0050_REL_05` | 0050 | −0.01 | **−0.10** | Y | N |
| `SF4_L4_08_REF` | REF | +0.82 | −0.20 | Y | N |
| `N1_LOCAL_08_OFF_REF` | REF | +0.13 | −0.25 | Y | N |

**0/8** N2 books clear sealed MDD↑ ≥ 0.  
CASH sinks lift **heldout** strongly but worsen sealed vs L4 ref.  
`N2_0050_LOCAL_08` is the **closest sealed in the whole ladder (−0.04 pp)** but fails **tip_clean** — not coexist.

## Binding

1. Soft-Frozen stays **3-sleeve 公股**.  
2. Do **not** Class-D flip to 四類 from this Stage.  
3. Do **not** retune FinPriv clips or TAIEX L4 from this result.  
4. N2 ladder step is **STOP**. Optional next: **N3** three-state ballot · or human **sealed-gate** change.

## Refs

- Charter: `PRIV_MDD_NEW_MECHANISM_CHARTER.md`  
- Stage A: `PRIV_MDD_NEW_MECH_N2_STAGE_A.md`  
- Prior N1 STOP: `PRIV_MDD_NEW_MECH_N1_DECISION_PACK.md`  

Label: `PRIV_MDD_NEW_MECH_N2_DECISION_2026-09-19__STOP_NO_SEALED_MDD_COEXIST`
