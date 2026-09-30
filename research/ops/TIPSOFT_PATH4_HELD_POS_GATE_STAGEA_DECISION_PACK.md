# TIPSOFT_PATH4_HELD_POS_GATE_STAGEA_DECISION_PACK

Date: 2026-09-30 · Verdict: **`PATH4_HELD_POS_HIT`** · champion=**`P4_C001_NEAR&SAT`**
Register: **0kay**

## Result

- held vs NEARPEAK3: **0.0273** pp
- sealed vs live: **-0.0523** pp
- tipY vs live: **6.0402** pp
- held_pos floor clears: **4** / 174

## Disposition

- Promote Path4 observe only on `PATH4_HELD_POS_HIT`
- Otherwise Path4 live OFF KEEP on top of 0kaw NEARPEAK3 observe

## Next

1. Objective: Path4 gate with held_vs_NEARPEAK3 > 0 and live sealed/tip floors
2. Champion `P4_C001_NEAR&SAT` held_vs_near=0.0273 sealed_vs_live=-0.0523 tipY=6.0402 live=HIT near=SOFT
3. held_pos_vs_near clears floors: n=4 / screened=174
4. any held_vs_near>0 (ignoring floors): n=4
5. Oracle DIAG `P4_C00025_ORACLE_POS_DIAG` held_vs_near=3.0158 (lookahead — never promote)
6. If PATH4_HELD_POS_HIT → draft observe on top of 0kaw; else Path4 OFF KEEP
7. Soft KEEP · Path4 live OFF · hybrid T+0 FORBIDDEN · no wire

Label: `TIPSOFT_PATH4_HELD_POS_GATE_STAGEA_DECISION_PACK_2026-09-30__PATH4_HELD_POS_HIT__NO_LIVE`
