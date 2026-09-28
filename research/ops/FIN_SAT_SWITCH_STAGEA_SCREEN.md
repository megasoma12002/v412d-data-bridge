# FIN_SAT_SWITCH_STAGEA_SCREEN

Date: 2026-09-28 · Generated `2026-09-28T13:10:09Z`
Status: **TIP_MDD_ONLY** · Soft-Frozen **KEEP** · parent observes **KEEP** · live wire **false**

Lag-1 NAV switch COMP↔SAT · HIT needs tip-clean + held≥+0.10 + vs SAT +0.05.

## Books

| ID | fam | rule | %SAT | flips | heldCAGR↑ | tipCAGR↑ | tipClean | vsSAT | HIT |
|---|---|---|---:|---:|---:|---:|---|---|---|
| CTRL_LIVE_A10 | ctrl | ctrl | 0.0 | 0 | -0.0 | 0.0 | True | False | False |
| REF_SAT_RELAX | ref | always_sat | 100.0 | 0 | 0.3343 | 0.6801 | True | False | False |
| REF_COMP_H150_A20 | ref | always_comp | 0.0 | 0 | 0.5415 | -13.3591 | False | True | False |
| SW_REL21_CDEF | switch | rel L=21 def=comp hold=0 | 48.65 | 409 | 0.8699 | -5.5106 | False | True | False |
| SW_REL63_CDEF | switch | rel L=63 def=comp hold=0 | 47.01 | 191 | 1.1698 | -5.1372 | False | True | False |
| SW_REL126_CDEF | switch | rel L=126 def=comp hold=0 | 48.77 | 149 | 0.9199 | 0.6801 | True | True | False |
| SW_REL63_SDEF | switch | rel L=63 def=sat hold=0 | 48.92 | 190 | 1.1698 | -5.1372 | False | True | False |
| SW_DD63_CDEF | switch | dd L=63 def=comp hold=0 | 49.12 | 83 | -0.0341 | -7.8587 | False | False | False |
| SW_REL63_H21 | switch | rel L=63 def=comp hold=21 | 46.81 | 67 | 1.9581 | -5.5348 | False | True | False |

Verdict: **`TIP_MDD_ONLY`**

Label: `FIN_SAT_SWITCH_STAGEA_SCREEN_2026-09-28__TIP_MDD_ONLY`
