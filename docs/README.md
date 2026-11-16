# Crypto Macro Fair-Value Model v2

Companion to `crypto_model_v2.xlsx`. Built 16 November 2026 from `crypto.xlsx` (kept unchanged inside the workbook as the `Original_v1` sheet).

## 1. What changed, in one paragraph

The original sheet ran a "liquidity waterfall": excess money, minus Treasury, gold and property absorption, minus what equities could absorb, times a rate multiplier, equals a target crypto market cap. That chain had a circular first step, mixed stocks with flows, and produced a target of exactly $0 in 21 of 29 quarters, so its "valuation gap" was just the actual market cap and its Buy/Sell labels (typed by hand) often contradicted the numbers next to them. Version 2 replaces the chain with an estimated relationship between crypto market cap, M2 and US equity wealth, reports how uncertain that relationship is, generates signals by formula using only information available at the time, and tests them out of sample. The input data were also corrected (87 values).

## 2. What the model says today

| | 2026 Q3 |
|---|---|
| Actual crypto market cap | $2.96T |
| Fair value given M2 and US equities | $5.2T (±1 SE band: $3.7T to $7.3T) |
| Valuation gap | about −43% |
| Real-time Z-score | −2.1 ("cheap vs macro") |
| Liquidity regime | Neutral (policy rate 0.25pp lower than a year earlier, after the September 2026 hike) |

**Read this with the next table in mind.** The same signal, tested on the 15 quarters where it could be tested out of sample, shows no timing skill:

| Out-of-sample check | Result |
|---|---|
| Average next-quarter return after "Cheap" (4 quarters) | +13% |
| Average next-quarter return after "Neutral" (11 quarters) | +13% |
| Correlation of Z-score with next-quarter return | −0.13 (t ≈ −0.5, not significant) |
| Directional hit rate | 53% |

So the gap is real as a description (crypto fell 47% from 2025 Q3 to 2026 Q2 while M2 and US equities made new highs), but the data cannot tell you whether it closes by crypto rising, by equities falling, or not at all. It is context, not a trade signal.

## 3. How the workbook works

| Sheet | Purpose |
|---|---|
| `Guide` | One-page instructions and colour legend |
| `Model` | Inputs, diagnostics, fair value, real-time signal. One row per quarter |
| `Params` | Editable assumptions (yellow) and live regression output with diagnostics |
| `Backtest` | Out-of-sample performance of the signal, all formulas |
| `Charts` | Actual vs fair value with error band; real-time Z-score |
| `Data_Sources` | Definition, source, link and confidence grade for every series |
| `Audit_Log` | 14 logic/formula problems in the original and 87 data corrections |
| `Original_v1` | Your original sheet, untouched |

Every result is a live formula. Change an input or a parameter and everything, including the regression coefficients, recalculates.

### Calculation steps on `Model`

1. **Inputs (columns C–L, blue).** M2, ON RRP (memo), nominal GDP, CPI YoY, Fed funds target (upper bound), total public debt, US equity market cap, crypto market cap, gold price, gold stock.
2. **Diagnostics (M–T).**
   - Gold market value = price × tonnes × 32,150.7 oz/t
   - Velocity `V = GDP / M2` (computed, no longer typed in)
   - Money overhang ratio `= M2 × V* / GDP`, and excess money `= M2 − GDP / V*`, where `V* = 1.45` is the 2015–2019 average velocity
   - Real policy rate `= rate − CPI`; Buffett ratio `= equity cap / GDP`; crypto / M2; quarterly change in debt
3. **Fair value, full sample (U–AC).**
   `ln(Crypto) = a + b1·ln(M2) + b2·ln(Equity)` estimated by `LINEST` over all actual quarters.
   Fair value `= EXP(a + b1·ln M2 + b2·ln Equity)`; band `= FV × EXP(±SE)`; gap `= actual / FV − 1`; Z `= residual / SE`.
4. **Real-time signal (AD–AJ).** For each quarter from 2022 Q4 on, the regression is re-estimated with `TREND` / `LINEST` on **earlier quarters only**, giving a fair value, standard error and Z-score that were knowable at the time.
   - Z ≥ +1 → "Rich vs macro"; Z ≤ −1 → "Cheap vs macro"; otherwise "Neutral". Thresholds are on `Params`.
   - Liquidity regime: Fed funds target up ≥ 0.5pp over four quarters → "Tightening"; down ≥ 0.5pp → "Easing".
5. **Scenario row (yellow).** 2026 Q4 inputs carried forward from Q3. Overwrite with your assumptions; leave crypto blank to see fair value only. It is excluded from estimation.

### Current estimates (`Params`)

| | Coefficient | t-stat |
|---|---|---|
| Intercept | −18.22 | −7.7 |
| ln(M2) | 3.81 | 3.3 |
| ln(US equity cap) | 1.80 | 4.2 |

R² = 0.86, SE = 0.34 log points, n = 28, Durbin–Watson = 0.85, Engle–Granger τ = −2.45. Quarterly return beta of crypto to US equities = 2.2 (t = 3.3).

### Updating each quarter

Overwrite the yellow scenario row with actuals, insert a new row above it and copy the formulas of the row above down, then extend the row ranges in the `Params` and `Backtest` formulas by one row. Sources and series codes are on `Data_Sources`.

## 4. Theory behind it

**Portfolio balance.** In Tobin's (1969) framework, money and other assets are imperfect substitutes: when the stock of money rises relative to what people want to hold for transactions, they rebalance into other assets and bid up their prices. Friedman (1988) applied the same idea to money and equity prices. This is the sound core of the original sheet's intuition. It implies a relation between asset *values* and the *stock* of money, which is why v2 compares stocks with stocks instead of subtracting flows from a stock.

**Why the original "excess liquidity" was circular.** The quantity equation `M·V = P·Y` is an identity. If V is measured as GDP/M2, then GDP/V equals M2 by construction and `M2 − GDP/V` is zero. To get information out of it, velocity has to be anchored to something outside the current quarter. The P-star literature (Hallman, Porter and Small, 1991) does exactly this, using long-run velocity V* to define a "money gap". v2 follows that approach for its overhang diagnostic.

**Crypto as a high-beta risk asset driven by US monetary conditions.** IMF research (Che, Copestake, Furceri and Terracciano, 2023) finds that one common factor explains about 80% of the variation in crypto prices, that its correlation with equities rose as institutions entered, and that Fed tightening lowers it much as it lowers the equity cycle. A follow-up (Copestake, Furceri and Terracciano, 2024) ties the equity co-movement to institutional participation. Iyer (2022) documents the post-2020 jump in crypto–equity correlation. This is why equity market cap is in the equation, and the 2.2 return beta in this dataset is consistent with it. Liu and Tsyvinski (2021) and Liu, Tsyvinski and Wu (2022) show crypto returns are driven by crypto-specific factors (market, size, momentum) more than by traditional macro factors, which is a reason to expect a wide error band around any macro fair value.

**Why the model reports cointegration and out-of-sample tests.** Regressing one trending series on another produces high R² and large t-stats even when the series are unrelated (Granger and Newbold, 1974). A levels relationship is only meaningful as an "equilibrium" if the residual is stationary (Engle and Granger, 1987; critical values in MacKinnon, 2010). Here τ = −2.45 against a threshold of roughly −3.5 to −4.1, so cointegration is **not** established. Separately, Welch and Goyal (2008) showed that many predictors that fit in sample fail out of sample, which is why the signal is computed in real time and tested on the next quarter's return.

## 5. Limitations

- **Small sample.** 28 quarters, 15 of them usable out of sample. Nothing here is statistically proven; the backtest can neither confirm nor rule out a modest effect.
- **The M2 coefficient is not a pure liquidity effect.** M2 trends upward over the same period that crypto adoption grew, so `b1 = 3.8` absorbs adoption. An elasticity that large should not be extrapolated.
- **No crypto-native variables.** Stablecoin supply, ETF flows, on-chain activity and leverage are absent. Adding them would likely help more than any further macro refinement.
- **Possible structural break.** The 2026 gap may reflect a change in the relationship (the −43% reading is partly driven by record equity values), not mispricing.
- **Real rate dropped from the equation.** It was insignificant with an unstable sign; it remains as a diagnostic column.
- **Data quality is uneven.** I could not download full series from FRED from this workspace. Values for 2025 Q1–2026 Q3 and the equity anchors were checked against the cited sources; most earlier values are rounded reference figures graded "B" (expected within about 1%), and some equity and gold-stock quarters are interpolated (graded "E", italic in the sheet). The equity "corrections" in `Audit_Log` are mostly a change of source and definition. Re-pull from the links on `Data_Sources` before relying on any single cell.
- **US real estate and "private credit AUM" were removed.** They could not be verified quarterly, and the private-credit figures were about 5–8× actual private-credit AUM (they match total private-markets AUM).
- Not investment advice.

## 6. References

- Che, N., Copestake, A., Furceri, D. and Terracciano, T. (2023). *The Crypto Cycle and US Monetary Policy.* IMF Working Paper 23/163. https://www.imf.org/en/publications/wp/issues/2023/08/04/the-crypto-cycle-and-us-monetary-policy-534834
- Copestake, A., Furceri, D. and Terracciano, T. (2024). *The Crypto Cycle and Institutional Investors.* CEPR Discussion Paper 19810.
- Engle, R. and Granger, C. (1987). Co-integration and error correction. *Econometrica* 55(2).
- Friedman, M. (1988). Money and the stock market. *Journal of Political Economy* 96(2).
- Granger, C. and Newbold, P. (1974). Spurious regressions in econometrics. *Journal of Econometrics* 2(2).
- Hallman, J., Porter, R. and Small, D. (1991). Is the price level tied to the M2 monetary aggregate in the long run? *American Economic Review* 81(4).
- Iyer, T. (2022). *Cryptic Connections: Spillovers between Crypto and Equity Markets.* IMF Global Financial Stability Note 2022/01.
- Liu, Y. and Tsyvinski, A. (2021). Risks and returns of cryptocurrency. *Review of Financial Studies* 34(6).
- Liu, Y., Tsyvinski, A. and Wu, X. (2022). Common risk factors in cryptocurrency. *Journal of Finance* 77(2).
- MacKinnon, J. (2010). *Critical Values for Cointegration Tests.* Queen's Economics Department Working Paper 1227.
- Tobin, J. (1969). A general equilibrium approach to monetary theory. *Journal of Money, Credit and Banking* 1(1).
- Welch, I. and Goyal, A. (2008). A comprehensive look at the empirical performance of equity premium prediction. *Review of Financial Studies* 21(4).

Data: Federal Reserve H.6 and FRED (M2SL, M2V, GDP, RRPONTSYD), BEA, BLS, US Treasury Debt to the Penny, Siblis Research (US equity market value), CoinGecko quarterly industry reports, LBMA / World Gold Council. Links per series are on `Data_Sources`.
