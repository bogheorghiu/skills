---
pattern: flights
uses:
  sources: [kind=flight-calendar, kind=flight-aggregator]
---
# Flights

1. **Airline calendars first.** Pull ±3 days around each date, in both directions, from the `flight-calendar` sources that match the route. Then run one `flight-aggregator` query to catch other carriers.
2. **Build the all-in price for each option:** fare + the baggage asked for + a seat only if needed + the currency effect. A fee you didn't look up for this route and date is a **Gap**; never estimate it into a total.
   - Never add amounts in different currencies. Convert each to the user's currency with a rate from a dated source you cite (a central-bank reference rate, or one the user gives), show the rate and its date, and tag the converted total UNRESOLVED: the card issuer's rate on the day will differ.
3. **Check the low-cost traps for each airline.** Verify them; don't recite them.
   - When free online check-in opens, and what the airport fallback costs.
   - The current free-bag size.
   - Bundle vs à-la-carte.
   - Pay in the fare's currency, not the airline's conversion.
   - Untick insurance and flex add-ons.
4. **Treat price-by-market / IP / cookie as a hypothesis.** Where a source exposes `market` or `currency`, run the same query twice and report the difference. Otherwise say it's untested.
5. **Flag awkward times** (dawn departures, midnight arrivals) as a real cost.
6. **Before quoting a price, read the source entry's `caveats`.** Some calendars price only the day's cheapest flight.
