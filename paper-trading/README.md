# Paper trading (Claude decides, no real money)

Every trade here is virtual. No order is ever sent to Dhan from this plan.

## Rules (fixed in advance, not changed mid-day)

- **Virtual capital:** ₹10,000
- **Instrument:** GOLDBEES (NSE, security id 14428), intraday, long only
- **Setup, Opening Range Breakout (ORB):**
  - Opening range = high and low of the 9:15-9:30 IST candles.
  - **Buy** when price trades above the opening-range high (checked at each check-in from 9:35 to 13:30). No new entries after 13:30.
  - **Stop-loss** = opening-range low, but never more than 0.6% below entry.
  - **Target** = 2 x the risk (entry minus stop-loss) above entry.
  - **Time exit:** anything still open at 15:10 is sold at the market price.
- **Position size:** risk at most 1% of capital (₹100) per trade: qty = floor(100 / (entry - stop)), capped by available capital.
- **One trade per day.** If the stop-loss is hit, no re-entry that day.
- **Day loss limit:** ₹200. Hit it and trading stops for the day.
- Fills are taken at the price seen at the check-in (LTP), not intraday extremes; brokerage is ignored.

## Limits of this test

Prices are checked only at scheduled check-ins (about every 30 minutes), so real fills could be better or worse.
One day or one week of results proves nothing. Judge it after 20+ trades.

## Log

See `log.md`.
