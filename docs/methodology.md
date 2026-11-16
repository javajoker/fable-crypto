# Methodology

How the models work, why they are built this way, and where they should not be trusted.

There are two. The **macro regression** is described first. The **liquidity-flow model** and the **driver model** built on it are described [further down](#liquidity-flow-model). All three are in the workbook `crypto_model_v2.xlsx` (see the [workbook guide](workbook-guide.md)) and in the [web app](web-app.md), which adds multi-quarter scenarios and the out-of-sample comparison of forecasting methods.

## Background: what v2 replaced

The original sheet ran a "liquidity waterfall": excess money, minus Treasury, gold and property absorption, minus what equities could absorb, times a rate multiplier, equals a target crypto market cap. That chain had a circular first step, mixed stocks with flows, and produced a target of exactly $0 in 21 of 29 quarters, so its "valuation gap" was just the actual market cap, and its Buy/Sell labels (typed by hand) often contradicted the numbers next to them.

Version 2 replaced the chain with an estimated relationship between crypto market cap, M2 and US equity wealth. It reports how uncertain that relationship is, generates signals by formula using only information available at the time, and tests them out of sample. The input data were also corrected (87 values). The 14 problems and all corrections are listed on the `Audit_Log` sheet.

## Calculation steps

All steps are on the `Model` sheet, one row per quarter.

### 1. Inputs

M2, ON RRP (memo), nominal GDP, CPI YoY, Fed funds target (upper bound), total public debt, US equity market cap, crypto market cap, gold price, gold stock. Definitions and sources are in the [data dictionary](data-dictionary.md).

### 2. Diagnostics

These give context. None of them enters the regression.

- Gold market value = price × tonnes × 32,150.7 oz/t
- Velocity `V = GDP / M2`
- Money overhang ratio `= M2 × V* / GDP` and excess money `= M2 − GDP / V*`, where `V* = 1.45` is the 2015–2019 average velocity
- Real policy rate `= rate − CPI`
- Buffett ratio `= equity cap / GDP`
- Crypto / M2
- Quarterly change in public debt

### 3. Fair value, full sample

```
ln(Crypto) = a + b1·ln(M2) + b2·ln(Equity)
```

estimated by `LINEST` over all actual quarters. Then:

- Fair value `= EXP(a + b1·ln M2 + b2·ln Equity)`
- Band `= FV × EXP(±SE)`, where SE is the standard error of the regression in log points
- Valuation gap `= actual / FV − 1`
- Z-score `= residual / SE`

These columns use hindsight: the coefficients are fitted on the whole sample, including quarters after the one being valued.

### 4. Real-time signal

For each quarter, the same regression is re-estimated with `TREND` / `LINEST` on **earlier quarters only**. This gives a fair value, standard error and Z-score that were knowable at the time. The first real-time quarter is the one with at least `Minimum estimation window` earlier quarters (12 by default, so 2022 Q4).

- Z ≥ +1 → "Rich vs macro"; Z ≤ −1 → "Cheap vs macro"; otherwise "Neutral". The thresholds were set before looking at results and are not optimised.
- Liquidity regime: Fed funds target up ≥ 0.5pp over four quarters → "Tightening"; down ≥ 0.5pp → "Easing". The nominal target is used so that an inflation spike is not mistaken for easing.

The real-time Z-score divides by the regression's standard error, not by a forecast standard error. The forecast error would be larger, especially early on, so the real-time Z-scores are somewhat overstated in absolute size.

### 5. Backtest

Each real-time signal is paired with the following quarter's realised crypto return. The `Backtest` sheet reports the average next-quarter return by signal, the correlation between Z-score and next-quarter return with its t-statistic, and a directional hit rate (sign of −Z equals sign of the return).

### 6. Scenario row

The yellow row at the bottom of `Model` holds next-quarter inputs, carried forward from the latest quarter by default. Overwrite them with your assumptions. Leave crypto blank to see fair value only. The scenario row is never used in estimation or in the backtest.

## Liquidity-flow model

The question it answers: how much USD can become crypto market cap? It follows the dollars.

| Step | Definition |
|---|---|
| Flowing USD | M2 |
| Free USD | `M2 − GDP ÷ V*`, with V* = 1.45. Money beyond what the real economy needs at its normal velocity. This is the same anchored measure as the workbook's "excess money" |
| Locked USD | Supply of USD stablecoins at quarter-end (DefiLlama) |
| Lock-in share | Locked USD ÷ M2 |
| Treasury collateral | Locked USD × the share of stablecoin reserves held in US Treasuries |
| Crypto V | Crypto market cap ÷ locked USD |
| Market cap | Crypto V × locked USD |

**Primary and secondary market.** A dollar enters through the primary market when a stablecoin is minted against it. From then on it circulates in the secondary market, where trading sets prices. Crypto V is what that trading makes of each locked dollar. It is the counterpart of the velocity of M2, with market value in the place of GDP.

**The dual lens.** A dollar that buys a stablecoin does not leave the banking system. The issuer spends it on Treasury bills, the cash goes to whoever sold the bills, and M2 is unchanged. What is created is a second claim: a dollar-token inside the crypto market, backed by a Treasury bill outside it. Locked USD therefore counts twice, as liquidity inside crypto and as demand for US government debt. In 2026 Q3, at an assumed 75% backing, issuers held about $228B of Treasuries, 0.57% of the debt stock. Their weight as a buyer depends on how fast locked USD is growing: it added about $70B in 2024 and $100B in 2025, but only $12B in the year to 2026 Q3.

**What the identity can and cannot do.** `Market cap = V × locked USD` is true by definition, because V is defined as the ratio. It explains nothing on its own. Its use is to split a forecast into parts one can reason about separately: the money stock (the Fed), the share of it that crosses into crypto, and the multiple the market puts on it (Wall Street's appetite for risk).

**History.** Locked USD rose from $4B (0.03% of M2) at the end of 2019 to $304B (1.30%) in 2026 Q3. Crypto V fell from 45× to about 10× over the same period, as the stablecoin base grew faster than market cap. Over the last 16 quarters V had a median of 11.1× and a middle half of 9.3× to 13.7×.

**Free USD against locked USD.** Free USD peaked at $4.4T in 2020–2021 and has fallen to $0.64T as GDP caught up with the money stock. Locked USD kept rising throughout, from about 2% of free USD to 47%. So crypto's dollar base did not track the overhang quarter by quarter; it accumulated while the overhang was large and has not drained since.

### Driver model

The default forecast in the web app. It lets the Fed and Wall Street move the chain:

```
Locked USD   = lock-in share × M2
Δln V        = β · Δln(US equity cap) + κ · (average ln V − last ln V)
Market cap   = V × locked USD
```

- The Fed acts through M2, and so through locked USD.
- Wall Street acts through β: crypto V rises and falls with equities.
- κ pulls V back toward its own average.
- The lock-in share holds unless the user sets a drift.

Estimated on 26 quarters: β = 0.69, κ = 0.05 a quarter, average V = 13.4×. There is no intercept. The band around a scenario is the model's typical one-quarter error, widened with the square root of the horizon.

**How it was chosen, and how good it is.** About twenty candidate forms were compared on one-quarter-ahead forecasts, each fitted only on earlier quarters, across five different starting points for the test. The candidates varied how locked USD evolves (unchanged, momentum, momentum plus past returns) and what moves V (mean reversion, equities, the policy rate, combinations), and included ensembles. The findings:

| | Typical error, given the equity path | vs no change | Typical error, equity path unknown | vs no change |
|---|---|---|---|---|
| No change | 27% | – | 27% | – |
| Equity beta only | 26% | −5% | 27% | about 0% |
| Driver model | 26% | −3% | 27% | about 0% |

(16 forecasts, 2022 Q4 to 2026 Q3. Typical error is root-mean-square error in logs.)

- **Without knowing where equities go, nothing beats "no change".** This held for every candidate.
- Told the equity path, the equity-driven forms were 3% to 11% more accurate than "no change" in most test windows.
- The ranking of candidates changed with the test window. Richer forms, with intercepts, the policy rate or momentum in locked USD, won in some windows and lost badly in others. That is what too little data looks like.
- The form above was kept because it was the most stable, not because it was the best anywhere. Picking one form out of twenty by its test results flatters it.

So the driver model is a translator. It turns a view on the Fed and Wall Street into a crypto market cap. It does not supply the view, and a typical one-quarter error of about 26% says how loosely even a correct view maps to the outcome. The web app reruns this comparison on the current data and shows it under "How good is the forecast?".

**Limits specific to these models.**

- Stablecoin supply is the narrowest measure of locked USD. Direct fiat purchases and ETF inflows are missing, so V overstates the effect of a dollar of inflow.
- The Treasury backing share is an assumption; no free series reports reserve composition.
- V was far higher in 2019–2020, when the stablecoin base was tiny. That pulls its average up and makes κ small.
- Turnover velocity, trading volume ÷ locked USD, is available live only. Its history has no free source.
- The policy rate did not help forecasts reliably and is not in the V equation. The Fed enters through M2 only.

## Current estimates

| | Coefficient | t-stat |
|---|---|---|
| Intercept | −18.22 | −7.7 |
| ln(M2) | 3.81 | 3.3 |
| ln(US equity cap) | 1.80 | 4.2 |

R² = 0.86, SE = 0.34 log points, n = 28, Durbin–Watson = 0.85, Engle–Granger τ = −2.45. Quarterly return beta of crypto to US equities = 2.2 (t = 3.3).

These are as of 2026 Q3. The live values are on `Params` and `Summary`.

## Theory

**Portfolio balance.** In Tobin's (1969) framework, money and other assets are imperfect substitutes: when the stock of money rises relative to what people want to hold for transactions, they rebalance into other assets and bid up their prices. Friedman (1988) applied the same idea to money and equity prices. This is the sound core of the original sheet's intuition. It implies a relation between asset *values* and the *stock* of money, which is why the model compares stocks with stocks and does not subtract flows from a stock.

**Why the original "excess liquidity" was circular.** The quantity equation `M·V = P·Y` is an identity. If V is measured as GDP/M2, then GDP/V equals M2 by construction and `M2 − GDP/V` is zero. To get information out of it, velocity has to be anchored to something outside the current quarter. The P-star literature (Hallman, Porter and Small, 1991) does exactly this, using long-run velocity V* to define a "money gap". The overhang diagnostic follows that approach.

**Crypto as a high-beta risk asset driven by US monetary conditions.** IMF research (Che, Copestake, Furceri and Terracciano, 2023) finds that one common factor explains about 80% of the variation in crypto prices, that its correlation with equities rose as institutions entered, and that Fed tightening lowers it much as it lowers the equity cycle. A follow-up (Copestake, Furceri and Terracciano, 2024) ties the equity co-movement to institutional participation. Iyer (2022) documents the post-2020 jump in crypto–equity correlation. This is why equity market cap is in the equation, and the 2.2 return beta in this dataset is consistent with it. Liu and Tsyvinski (2021) and Liu, Tsyvinski and Wu (2022) show crypto returns are driven by crypto-specific factors (market, size, momentum) more than by traditional macro factors, which is a reason to expect a wide error band around any macro fair value.

**Why the model reports cointegration and out-of-sample tests.** Regressing one trending series on another produces high R² and large t-stats even when the series are unrelated (Granger and Newbold, 1974). A levels relationship is only meaningful as an "equilibrium" if the residual is stationary (Engle and Granger, 1987; critical values in MacKinnon, 2010). Here τ = −2.45 against a threshold of roughly −3.5 to −4.1, so cointegration is **not** established. Separately, Welch and Goyal (2008) showed that many predictors that fit in sample fail out of sample, which is why the signal is computed in real time and tested on the next quarter's return.

## Limitations

- **Small sample.** 28 quarters, 15 of them usable out of sample. Nothing here is statistically proven; the backtest can neither confirm nor rule out a modest effect.
- **The M2 coefficient is not a pure liquidity effect.** M2 trends upward over the same period that crypto adoption grew, so `b1 = 3.8` absorbs adoption. An elasticity that large should not be extrapolated.
- **No crypto-native variables.** Stablecoin supply, ETF flows, on-chain activity and leverage are absent. Adding them would likely help more than any further macro refinement.
- **Possible structural break.** The 2026 gap may reflect a change in the relationship (the −43% reading is partly driven by record equity values), not mispricing.
- **Real rate dropped from the equation.** It was insignificant with an unstable sign; it remains as a diagnostic column.
- **Persistent residuals.** Durbin–Watson is well below 2, so the t-statistics on the coefficients are overstated and gaps last for several quarters.
- **Data quality is uneven.** Full series could not be downloaded from FRED when the workbook was built. Values for 2025 Q1–2026 Q3 and the equity anchors were checked against the cited sources; most earlier values are rounded reference figures graded "B" (expected within about 1%), and some equity and gold-stock quarters are interpolated (graded "E", italic in the sheet). The equity "corrections" in `Audit_Log` are mostly a change of source and definition. Re-pull from the links in the [data dictionary](data-dictionary.md) before relying on any single cell.
- **US real estate and "private credit AUM" were removed.** They could not be verified quarterly, and the private-credit figures were about 5–8× actual private-credit AUM (they match total private-markets AUM).
- Not investment advice.

## Possible extensions

None of these is implemented.

- Add spot-ETF flows and exchange fiat inflows to locked USD, to widen it beyond stablecoins.
- Replace the assumed Treasury backing share with figures from issuers' reserve reports.
- Bring the out-of-sample comparison of forecasting methods into the workbook.
- Replace the regression SE in the real-time Z-score with the forecast standard error.
- Estimate an error-correction model if a longer sample ever supports cointegration.
- Move to monthly data to raise the number of observations.

## References

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
