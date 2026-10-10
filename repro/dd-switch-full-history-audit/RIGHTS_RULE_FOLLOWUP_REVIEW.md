# Historical conversion rules and bounded source recovery — 2026-10-10

No new event delivery or quote gap is closed. Remaining categories: stock delivery 6, subscription delivery 9, rights/ordinary phase 4 (overlapping). DD_SWITCH T+1 was not run.

## Newly preserved official evidence

- TDCC 2006-03-27 historical book-entry rule: point 6 schedules conversion of deposited rights/payment certificates on the exchange-announced new-share listing date; point 5 requires the broker to check deliverable balance before selling. The official history index identifies this as the version preceding 2017-12-21.
- TDCC 2017-12-21 rule retains the listing-date conversion procedure and deliverable-balance condition.
- TWSE 2011-01-12 trading rule, effective 2011-03-28: account requirement; whole trading units and odd-lot treatment; odd-lot orders stop three business days before replacement shares list. This 2011 version is used for the legacy Mega events; the rule is not applied retroactively from today's version.
- TWSE 2009-11-12 code notice distinguishes temporary instruments by a four-digit stock code plus an L–Z suffix. It does not identify any event's actual suffix. No guessed code or ordinary quote substitution is permitted.

`scripts/dd_switch_rights_rule_review.py` produces 11 conditional conversion schedules: six subscriptions and two Mega phases with preserved primary listing dates, and three subscriptions with secondary-only listing leads (Hua Nan 2012-02-07, CTBC 2012-04-30 and CTBC 2013-05-10). General rules support a scheduled process; they do not certify that a particular event completed, that a holder paid/subscribed or received shares, or the historical availability of every input. All event delivery fields stay uncertified.

## Retrieval outcomes

TWSE MI_INDEX for 2011-09-16 was source-blocked. The capture runner skipped the three other requests to that host and retained the blocked response. No quotes were recovered.

Hua Nan transfer-agent type-2 table covers only ROC114/115 and provides no target 2010–2013 event evidence. Mega's current issuer distribution table ends at ROC103 and supplies no target 2011/2012 row.

The issuer-linked IR-cloud 2011 annual viewer returned HTML for the cover and contents pages, revealing page-image links; both observed image URLs returned HTTP404. The surviving viewer controls are not annual report content and cannot certify delivery. Failed responses are preserved.

## Verification

`rights_rule_followup_capture.zip` contains 12 new captures plus eight preserved primary listing notices and a scoped manifest. ZIP integrity, all 20 raw/compressed SHA256 pairs, historical rule wording and eight ROC listing dates passed. 32 existing source/capture/scoped-delivery tests passed with PYTHONPATH=scripts; the first invocation lacked that import path and was corrected. The comprehensive inventory includes clearly labeled conditional rule schedules and the third secondary listing lead, with all categories still open. Canonical data and forward paths remain unchanged.
