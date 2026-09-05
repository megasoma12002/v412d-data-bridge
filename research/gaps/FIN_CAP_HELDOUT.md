# FIN_CAP Held-out Decision (locked FIN_CAP_50)

Generated: `2026-09-05T00:55:02.239463+00:00`

## Decision: `PASS_HELDOUT_FIN_CAP`

Locked from OOF: `FIN_CAP_50` fin∈[0.35,0.5]

| | CAGR | MDD |
|---|---:|---:|
| BASE held-out | 0.18235031521908462 | -0.22639131293777315 |
| FIN_CAP_50 held-out | 0.16601509541261028 | -0.19575705858876424 |

- MDD improve: `3.06` pp (need ≥1)
- CAGR giveback: `1.63` pp (need ≤3)
- Finance max on held-out: `0.500` (cap_ok=True)

Held-out **PASS**. Still **not live**. Explicit promote PR required to change E16 clips.
Recommend keeping BASE_E16 paper ledger beside any cutover.

Label: `RESEARCH_FIN_CAP_HELDOUT__NO_LIVE_WIRE`
