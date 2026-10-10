# GitHub gap search review — 2026-10-10

Result: **0 additional gaps closed**. Stock delivery 6, subscription delivery 9, rights/ordinary phases 4, and full-history blockers 9 remain open. Categories overlap.

## Repository branches

Inventoried eight relevant local remote-tracking branch snapshots, pinning commit and relevant blob SHAs in `github_gap_search_audit.json`: main, e50a0-point-in-time, e50a1-full-backfill, e50a1-causal-layer, cursor/e22-stock-div-research-d049, cursor/e22-v3-h1-payment-d049, cursor/data-gap-fill-sources-d049, and cursor/twse-session-calendar-charter-da22. This is a bounded search, not an exhaustive claim about every branch or deleted commit.

Reviewed main's stock-dividend research, payment proxy README, Yahoo backfill code, 2891 cash-payment fill note, and calendar charter. The stock research applies shares on the ex-date as an experimental convention. The payment proxy is superseded; the later backfill uses Yahoo dates. The 2891 note concerns a previously filled **cash** event in 2010, not the open 2012/2013 subscription events. The calendar files in these snapshots cover 2025/2026, not the missing pre-2025 official history. None supplies new primary general stock-delivery evidence.

## Public GitHub archives

Found `shinbutou/nccu_bigdata` at commit `4c3a9cceee4709886a963cf0ae372d2506e29170`. Captured seven basic-info CSVs for 2880 (ROC 100–102), 2886 (100–101), and 2891 (101–102). Each has issuer, title, reported announcement date/time, but **no announcement body**. Retained 107 broad capital/dividend title leads, including subsidiaries and unrelated events; this is not a count of missing evidence.

The pinned, untruncated tree lists detailed-info files for these issuers only for ROC 106–109. Therefore this particular snapshot does not provide detailed bodies for the target older years. It does not establish that the original notices are absent elsewhere.

Public code searches also examined matches in `aRthur08701244/Intern-in-CTBC`. Search queries and returned file URLs are recorded in `github_gap_public_searches.json`. Large CSV files can match an issuer in one row and a delivery term in another; these search hits are unverified leads. The exact phrase query for 華南金 / 102年增資 returned no files, which is not proof of historical absence.

## Evidence and next retrieval

`github_gap_index_capture.zip` preserves the seven index files. SHA256 and Git blob SHA checks passed for every archived file, and ZIP integrity passed. Git commit time and mirror-reported announcement time do not certify original publication vintage.

Next retrieval should use issuer, date and exact title from the index to request the primary MOPS detail or issuer/transfer-agent notice. Require explicit ordinary-share book-entry/delivery language and instrument/holder scope. Do not replace delivery with record dates, registration dates, rights-certificate issuance, or listing alone.

Canonical data, forward state and strategy execution were not changed. Full-history certification remains blocked; DD_SWITCH T+1 was not run.
