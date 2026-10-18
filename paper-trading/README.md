# Paper trading (Claude decides, no real money)

Every trade here is virtual. No order is ever sent to Dhan from this plan.

## Rules (fixed in advance, not changed mid-day)

- **Virtual capital:** ₹50,000
- **Markets:** Nifty 50 (index id 13, IDX_I) and Bank Nifty (index id 25, IDX_I), traded as index **options**, intraday only.
- **Signal, Opening Range Breakout (ORB) on the index itself:**
  - Opening range = high and low of the index between 9:15 and 9:30 IST.
  - Index trades **above** the range high: **buy 1 lot of the ATM Call (CE)**.
  - Index trades **below** the range low: **buy 1 lot of the ATM Put (PE)**.
  - Checked at each check-in from 9:35 to 13:30. No new entries after 13:30.
- **Which option:** strike nearest to the index price at entry; nearest expiry, **but never an expiry that falls on the trade day** (then use the next one). Lot sizes: Nifty 65, Bank Nifty 30.
- **Stop-loss:** premium falls 25% below the buy price.
- **Target:** premium rises 50% above the buy price (2 x the risk).
- **Time exit:** anything still open at 15:10 is sold at the premium seen then.
- **One trade per index per day.** If its stop-loss is hit, no re-entry in that index that day.
- **Day loss limit:** ₹6,000 across both indices. Hit it and trading stops for the day.
- Fills are taken at the option LTP seen at the check-in, not intraday extremes; brokerage and taxes are ignored.

## Limits of this test

Prices are checked only at scheduled check-ins (about every 30 minutes), so real fills and stop-losses could be much worse, especially in options.
One day or one week of results proves nothing. Judge it after 20+ trades.

## Log

See `log.md`.
