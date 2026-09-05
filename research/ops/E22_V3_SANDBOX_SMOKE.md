# E22_v3 Sandbox Smoke — Stage B

- ok: **True**
- live DEFAULT untouched: `E22_v2s_tw`
- Soft-Frozen KEEP: **True**
- ballot: ACCEPT charter 2026-09-05

## Event

```json
{
  "code": "2880",
  "ex_date": "2010-08-12",
  "payment_date": "2010-09-03",
  "amount": 0.2,
  "shares": 1000.0,
  "formal_gross": 200.0
}
```

## Checks

- `default_untouched`: **True**
- `recv_ex_cash_zero`: **True**
- `recv_ex_receivable_eq_formal`: **True**
- `recv_pay_clears`: **True**
- `recv_pay_cash_eq_formal`: **True**
- `tax10_net`: **True**
- `tax20_net`: **True**

## Note

Sandbox only. No DEFAULT promote. Combined recv+tax not implemented.
