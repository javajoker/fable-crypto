# Update guide

How to add a quarter, run a scenario and check the result, working in Excel. Layout details are in the [workbook guide](workbook-guide.md).

The [toolset](toolset.md) does the same from the command line and fetches most of the inputs for you. Whichever route you take, finish with `make update` so that the site and the stablecoin data follow the workbook.

## Adding a quarter

1. **Collect the ten inputs** for the quarter that has ended. Definitions, sources and links are in the [data dictionary](data-dictionary.md). Use the same definitions as earlier rows (for example quarter-end month for M2, upper bound for the Fed funds target).
2. **Insert a row** on `Model` directly above the yellow scenario row. Right-click the scenario row's number and choose Insert.
3. **Copy the row above** into the new row (the whole row, columns B to AO).
4. **Type the new values** over the copied ones: the quarter label in B and the inputs in C to L. Follow the colour convention: plain blue for sourced values, italic blue for estimates.
5. **Refresh the scenario row.** Change its label to the next quarter, keeping the text `(scenario)`, and set its yellow inputs. Clear its crypto cell unless you want a scenario gap.
6. **Check `Summary`.** The latest quarter should be the one you added, and all eight integrity checks should read `OK`.
7. **Update the records.** Add the quarter's sources and confidence grades to `Data_Sources`, and re-read the written verdict on `Backtest` against the new numbers.
8. **Save, then check and republish:**

```bash
make update
```

This refreshes stablecoin supply, runs the independent check and rebuilds the site's data.

Nothing else needs editing. The regression, diagnostics, backtest, `Summary` and charts all follow the last actual row.

## Running a scenario

Overwrite the yellow cells in the scenario row on `Model`:

- Leave **crypto blank** to see the fair value and band that the scenario's M2 and equity cap imply.
- Type a **crypto value** to also see the scenario valuation gap.

The result is on the scenario row itself and in the scenario block on `Summary`. The scenario row never enters the regression or the backtest, whatever you type.

## Changing assumptions

Edit the yellow cells on `Params`.

| Cell | Effect |
|---|---|
| V* anchor velocity | Changes the overhang diagnostics only |
| Z thresholds | Reclassify quarters as Rich / Cheap / Neutral, and so change the backtest table |
| Regime threshold | Reclassifies Tightening / Easing |
| Minimum estimation window | Moves the first real-time quarter. A longer window gives more stable early estimates and fewer out-of-sample quarters |

The thresholds were set before looking at results. Tuning them to improve the backtest would make the backtest meaningless.

## Revising history

Blue cells can be overwritten at any time, for example when GDP is revised. Note that revising history changes the "real-time" columns too: they show what the model would have said given *today's* data for those quarters, not the data as first published.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| `Scenario row found` reads `CHECK` | The scenario label lost the text `(scenario)` |
| The latest quarter on `Summary` is not the one added | The new row was inserted below the scenario row, or a second label contains `(scenario)` |
| `No blank inputs` or `All inputs numeric` reads `CHECK` | A missing value, or a number typed as text (often a trailing space or a `$` sign) |
| `Observations match rows` reads `CHECK` | Crypto cap is blank in an actual quarter |
| `#VALUE!` or `#NUM!` in the real-time columns | The minimum window is below 4, or an input is zero or negative |
| The check script reports mismatches | The workbook was not recalculated and saved after the last edit, or a formula was overwritten with a value |
| The check script finds no values at all | The file was last saved by a tool that does not calculate formulas. Open it in Excel and save |
