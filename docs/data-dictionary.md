# Data dictionary

Every input series on the `Model` sheet. This mirrors the `Data_Sources` sheet as of 16 November 2026; if the two ever differ, the sheet is the record.

## Confidence grades

| Grade | Meaning |
|---|---|
| A | Checked against the cited source on 16 November 2026 |
| B | Reference value, rounded, expected within about 1% (10% for early crypto caps). Re-pull from the source before relying on it |
| E | Estimated by the method described. Shown in italic blue in the sheet |

## Series

| Column | Series | Definition | Unit | Used in |
|---|---|---|---|---|
| C | M2 | Seasonally adjusted M2, last month of the quarter | $T | Regression, diagnostics |
| D | ON RRP | Overnight reverse repo balance, last business day | $T | Memo only |
| E | Nominal GDP | Current-dollar GDP, seasonally adjusted annual rate | $T | Diagnostics |
| F | CPI YoY | CPI-U all items, 12-month % change, last month of quarter | % | Diagnostics |
| G | Policy rate | Upper bound of the FOMC target range at quarter-end | % | Liquidity regime, diagnostics |
| H | Total public debt | Total public debt outstanding, quarter-end | $T | Diagnostics |
| I | US equity market cap | Market cap of all US-domiciled listed companies | $T | Regression, diagnostics |
| J | Crypto market cap | Total crypto market cap, quarter-end | $T | Regression, backtest |
| K | Gold price | LBMA Gold Price PM, last fixing of the quarter | $/oz | Diagnostics |
| L | Gold stock | Above-ground stock | tonnes | Diagnostics |

Only M2, US equity market cap and crypto market cap drive the fair value. The policy rate drives the liquidity regime. Everything else is context.

## Sources and confidence

| Series | Source | Confidence by period | Notes |
|---|---|---|---|
| M2 | Federal Reserve H.6 / FRED `M2SL` — https://fred.stlouisfed.org/series/M2SL | A: 2020 Q3–Q4, 2025 Q3–2026 Q3. B: others | Sep 2026 = $23.41T (H.6 of 27 Oct 2026) |
| ON RRP | NY Fed / FRED `RRPONTSYD` — https://fred.stlouisfed.org/series/RRPONTSYD | B: all | Not in any model formula. Quarter-end days show window-dressing spikes |
| Nominal GDP | BEA / FRED `GDP` — https://fred.stlouisfed.org/series/GDP | A: 2025 Q2–2026 Q3. B: earlier | 2026 Q3 = Q2 level × 1.056^(1/4) from the BEA advance estimate (29 Oct 2026). 2024 Q2–2025 Q1 derived from published year-on-year rates. Earlier quarters are a pre-revision vintage |
| CPI YoY | BLS — https://www.bls.gov/cpi/ | A: 2025 Q3, 2026 Q1–Q3. B: earlier | Mar 2026 3.3%, Jun 2026 3.5%, Sep 2026 3.7% |
| Policy rate | Federal Reserve FOMC statements / FRED `DFEDTARU` | A: 2025 Q4–2026 Q3. B: earlier | Cut to 3.50–3.75% in Dec 2025; raised to 3.75–4.00% in Sep 2026; held 28 Oct 2026 |
| Total public debt | US Treasury Debt to the Penny — https://fiscaldata.treasury.gov/datasets/debt-to-the-penny/ | A: 2025 Q3, 2026 Q1, 2026 Q3. B: others | Includes about $7.8T of intragovernmental holdings, which do not absorb market liquidity |
| US equity market cap | Siblis Research — https://siblisresearch.com/data/us-stock-market-value/ | A: year-ends 2019–2025, Jun 2025, Jun 2026, Sep 2026. E: other quarters | Estimated quarters scale the nearest published anchor by the S&P 500 price path, with the gap to the next anchor spread evenly. 2026 Q1 uses the S&P 500 change from Dec 2025 only |
| Crypto market cap | CoinGecko quarterly industry reports — https://www.coingecko.com/research | A: 2025 Q1–2026 Q3. B: earlier | 2026 Q3 $2.96T; Q2 = Q3 less the reported $840.1B gain; Q1 = Q2 plus the reported $304.8B loss; 2025 Q4 from "Q3 2026 is 4.0% below start of year" |
| Gold price | LBMA / World Gold Council — https://www.gold.org/goldhub/data/gold-prices | A: 2026 Q1 ($4,608), 2026 Q3 ($4,176). B: others | 2025 Q4 uses a reported year-end close of $4,323; 2026 Q2 is implied by a reported 3.7% Q3 gain to $4,157 |
| Gold stock | World Gold Council — https://www.gold.org/goldhub/data/how-much-gold | B: year-ends 2019–2024. E: 2025 onward and all intra-year quarters | Intra-year values are linear interpolations; 2025–26 assume about 3,600 tonnes of net additions a year |

## Removed series

US real estate value and "private credit AUM" were in the original sheet and were dropped in v2. Neither fed the original result in a meaningful way, quarterly values could not be verified, and the "private credit" figures ($7.5T–$17T) match total private-markets AUM, not private credit (about $2–4T depending on definition). The original values remain on `Original_v1`.

## Known weaknesses

- The US equity series matters most, because it is a regressor, and 18 of its 28 quarters are estimates between published anchors.
- Most values before 2025 are grade B. They are good enough for a regression on logs, where a 1% error in a level is small, but they should not be quoted individually.
- GDP is a mix of vintages. It affects only the diagnostics.
