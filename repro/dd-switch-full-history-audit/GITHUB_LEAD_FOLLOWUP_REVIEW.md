# GitHub lead followup — 2026-10-10

**No additional primary general-delivery facts established.** The remaining categories stay at stock delivery 6, subscription delivery 9, rights/ordinary phase 4 and full-history blockers 9; categories overlap. No strategy run or canonical changes.

## Two newly located final listing leads

| Event | Earlier voucher/book-entry stage | Candidate ordinary listing / voucher termination | Evidence status |
| --- | --- | --- | --- |
| 2880 subscription, ex 2011-11-07 | 2011-12-29 | 2012-02-07 | Secondary final notice; primary original and ordinary delivery still required |
| 2891 subscription, ex 2012-02-10 | 2012-04-12 | 2012-04-30 | Secondary final notice; primary original and ordinary delivery still required |

The final notices refer to 1,200,000,000 and 715,000,000 shares respectively. Their book-entry clauses refer back to the earlier stage dates, not to a separately dated ordinary conversion delivery. Prior preserved primary notices explicitly identify the earlier securities as subscription vouchers. These leads are appended only to available-evidence descriptions in the comprehensive inventory; primary listing and delivery fields stay unchanged.

Sources: https://m.cnyes.com/news/id/2263066 and https://n.yam.com/Article/20120424408004. The desktop Hua Nan URL timed out at the bounded 15-second limit; its mobile view was captured successfully. The failed partial transport is retained and excluded.

The CTBC 2013 registration reprint https://m.cnyes.com/news/id/1509129 identifies the 1,333,400,000-share issue and the 2013-04-17 voucher credit, while leaving ordinary replacement/listing for another announcement. It adds no final delivery date.

## Primary and GitHub retrieval

Two date-led MOPS detail probes, for Hua Nan 2013-09-06 and CTBC 2012-04-24, returned HTTP 200 empty shells without announcement content. These are unsuccessful evidence retrievals, despite completed HTTP transport. They do not prove the original notices are absent.

Four pinned CSVs from `aRthur08701244/Intern-in-CTBC` were downloaded and matched to their Git blob SHAs at commit `258f42aa4502b458b11fcb96f875cdd80266df3f`. They cover selected May/September 2013 news and contain 6,638 data rows in total. A row-level search for the target issuers together with voucher/final-delivery terms returned no matches. This selected corpus is not a complete news archive and cannot establish absence.

## Saved evidence and verification

`github_lead_followup_capture.zip` contains the six targeted HTTP captures (including the failure), four GitHub CSV captures and their manifests. `scripts/dd_switch_github_lead_review.py` reads the archive directly, verifies all ten raw/compressed SHA256 pairs, checks the four Git blob SHAs, and validates event quantities and the distinct stage dates before generating `github_lead_followup_review.json`. ZIP integrity and all checks passed.

Capture progress files are complete and there are no background capture jobs. Publication vintage, holder election, ordinary conversion and full-history certification remain unresolved. DD_SWITCH T+1 was not executed.
