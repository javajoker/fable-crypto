# Workbook guide

A reference for the layout of `crypto_model_v2.xlsx` (v2.2). For what the numbers mean see [methodology](methodology.md); for the quarterly routine see the [update guide](update-guide.md).

## Colour conventions

| Appearance | Meaning |
|---|---|
| Blue text | Input, typed in |
| Italic blue text | Estimated input (interpolated or scaled; see the [data dictionary](data-dictionary.md)) |
| Black text | Formula |
| Green text | Formula that reads from another sheet |
| Yellow fill | Cells meant to be edited: assumptions on `Params`, the scenario row on `Model` |
| Green / red fill | Conditional formatting: Cheap or Easing or `OK` in green; Rich or Tightening or `CHECK` in red |

Units are USD trillions unless the column header says otherwise. Headers are bilingual (Chinese / English).

## Sheets

### `Guide`

Instructions, how to read the output, limits, colour legend, version note.

### `Summary`

Four blocks, all formulas:

| Block | Content |
|---|---|
| Latest reading | Actual, fair value, band, gap, both Z-scores, valuation signal, liquidity regime for the latest actual quarter |
| Scenario row | Fair value and band under the scenario inputs; scenario gap if a crypto value is typed in |
| How far to trust it | n, R², SE, Durbin–Watson, Engle–Granger τ, backtest correlation and hit rate, with plain yes/no readings |
| Integrity checks | Nine checks and an overall status (see below) |
| Liquidity chain | Flowing USD, free USD, locked USD, Treasury collateral, crypto V and market cap for the latest quarter |
| Driver model, scenario row | Locked USD, crypto V and market cap one quarter ahead under the scenario inputs |

### `Model`

One row per quarter from row 9. The row whose label contains `(scenario)` is the scenario row; keep that text out of every other cell in column B.

| Columns | Group | Content |
|---|---|---|
| B | | Quarter label |
| C–L | Inputs | M2, ON RRP, GDP, CPI YoY, Fed funds target, public debt, US equity cap, crypto cap, gold price, gold stock |
| M–T | Diagnostics | Gold market value, velocity, overhang ratio, excess money, real policy rate, Buffett ratio, crypto / M2, change in debt |
| U–W | Regression variables | ln crypto, ln M2, ln equity |
| X–AC | Fair value, full sample | Fair value, −1 SE, +1 SE, valuation gap, residual, Z-score |
| AD–AJ | Real-time signal | Real-time fair value, real-time SE, real-time Z, valuation signal, 4-quarter rate change, liquidity regime, next-quarter crypto return |
| AK–AO | Helpers | Residual change, crypto log return, equity log return, out-of-sample pair flag, directional hit |

### `Flow`

The liquidity-flow chain and the driver model. Its rows match `Model` one for one: same row numbers, same scenario row. It reads `Model` by row number, so the two sheets must stay in step.

| Columns | Group | Content |
|---|---|---|
| B–F | Linked from Model | Quarter, M2, GDP, crypto market cap, US equity cap |
| G | Input | Stablecoin supply (locked USD). In the scenario row it defaults to last quarter's lock-in share × the scenario's M2 |
| H–K | The chain | Free USD, lock-in share, share of free USD, Treasury collateral |
| L–P | Crypto V | V, ln V, its change, the change in ln equity cap, the pull toward V's running average |
| Q–S | Driver model | V and market cap one quarter ahead given that quarter's equity move and locked USD, and the miss against the actual |

Columns Q–S use coefficients fitted on the whole sample, so for past quarters they show fit, not forecasts. The out-of-sample test is in the web app.

### `Params`

| Rows | Content |
|---|---|
| 5–10 | Editable assumptions (yellow): V*, ounces per tonne, Z thresholds, regime threshold, minimum estimation window. Entries are validated |
| 14–16 | Regression coefficients, standard errors, t-stats |
| 18–24 | R², SE, observations, Durbin–Watson, Engle–Granger τ, return beta and its t-stat |
| 27–31 | Range control: first data row, scenario row, last actual row, latest quarter, first real-time quarter. Formulas; do not edit |
| 34–35 | Editable (yellow): share of stablecoin reserves held in Treasuries (an assumption), lookback for the usual range of V |
| 36–42 | Driver model: β (equities), κ (pull to average), average V, median and quartiles of V over the lookback, observations |

### `Backtest`

Counts, average next-quarter return and share of gains by signal; correlation, t-stat and hit rate; a written verdict dated 16 November 2026. The verdict text is static and should be re-read against the numbers after each update.

### `Charts`

1. Actual crypto market cap vs fair value with the ±1 SE band
2. Real-time Z-score
3. Valuation gap, full sample
4. Locked USD
5. Crypto V

Chart ranges run through the scenario row, so a quarter inserted above it appears without editing the charts. The scenario row shows as the last point of the fair-value lines.

### `Data_Sources`, `Audit_Log`, `Original_v1`

Source and confidence grade per series, the stablecoin series included; the audit of the original sheet (14 logic problems, 87 data corrections); the original sheet itself. These are records and are not read by any formula.

## Named ranges

All of them start at the first data row and end at `Params!C29`, the last actual row. They are what makes the workbook extend itself.

| Name | Column on `Model` | Used for |
|---|---|---|
| `Reg_Y` | U | Dependent variable, ln crypto |
| `Reg_X` | V:W | Regressors, ln M2 and ln equity |
| `Resid` | AB | Residuals |
| `Resid_Lead`, `Resid_Lag` | AB | Residuals from the second row on, and up to the second-last row (Durbin–Watson, Engle–Granger) |
| `dResid` | AK | Residual changes (Engle–Granger) |
| `Ret_Crypto`, `Ret_Equity` | AL, AM | Quarterly log returns (return beta) |
| `BT_Z`, `BT_Signal`, `BT_NextRet` | AF, AG, AJ | Backtest inputs |
| `BT_OOS`, `BT_Hit` | AN, AO | Out-of-sample pair flag and directional hit |

And on `Flow`:

| Name | Column on `Flow` | Used for |
|---|---|---|
| `Flow_Locked` | G | Stablecoin supply (the "locked USD filled in" check) |
| `Flow_V`, `Flow_lnV` | L, M | Crypto V and its log |
| `Flow_dV` | N | Change in ln V, from the third quarter on (dependent variable of the V equation) |
| `Flow_X` | O:P | Its two regressors |

They are defined as, for example, `Model!$U$9:INDEX(Model!$U:$U,Params!$C$29)`. `INDEX` is used in preference to `OFFSET` because it is not volatile.

## Formula conventions

**Looking at another quarter.** A formula that needs the previous or next quarter finds it by position, not by a direct cell reference:

```
change in debt      =H21-INDEX($H:$H,ROW()-1)
4-quarter change    =G21-INDEX($G:$G,ROW()-4)
next-quarter return =INDEX($J:$J,ROW()+1)/J21-1
```

A direct reference such as `=H21-H20` breaks silently when a row is inserted between the two cells. The positional form does not.

**Expanding window.** The real-time columns estimate on everything above the current row:

```
=IF(COUNT($U$9:INDEX($U:$U,ROW()-1))<Params!$C$10,"",
    EXP(TREND($U$9:INDEX($U:$U,ROW()-1),$V$9:INDEX($W:$W,ROW()-1),V21:W21)))
```

The window never includes the current row, which is what keeps the signal free of look-ahead.

**Every row has the same formula.** Rows differ only in their own row number, so the row above can always be copied down. The first data row is the one exception: it has no previous quarter.

**Blank, not zero.** Cells with nothing to report return `""`. Totals and statistics are written to ignore them.

## Integrity checks

On `Summary`. Each returns `OK` or `CHECK`.

| Check | Fails when |
|---|---|
| Scenario row found | No label in `Model` column B contains `(scenario)` |
| No blank inputs in actual quarters | An input cell in C–L is empty |
| All inputs numeric | Text was typed into an input cell |
| Level inputs positive | M2, GDP, equity cap or crypto cap is zero or negative |
| Observations match rows | The regression is not using every actual quarter |
| Residuals sum to zero | The fair-value columns and the regression are on different samples |
| Minimum window is usable | The window is below 4 or leaves almost nothing to test on |
| No formula errors on Model | Any calculated cell on `Model` shows an error |
| Locked USD filled in | `Flow` lacks a stablecoin value for an actual quarter |

## Compatibility

The workbook uses only functions available since Excel 2007 (`LINEST`, `TREND`, `INDEX`, `MATCH`, `SUMPRODUCT`, `COUNTIFS`, `AVERAGEIFS`). It has no macros, no external links and no volatile functions, and no formula depends on array entry. It is checked in both Excel and LibreOffice Calc.

The two do not always agree: up to v2.2 the scenario row was found with `SUMPRODUCT(MAX(...))`, which LibreOffice evaluates as an array and Excel does not, so Excel showed `#VALUE!` throughout. A new formula should be tried in Excel before it is relied on.
