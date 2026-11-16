# Crypto Macro Fair-Value Model

An Excel model that asks one question: given the level of US money supply (M2) and US equity wealth, what has total crypto market cap typically been, how far is today's value from that, and how much should that gap be trusted?

The model is the workbook [docs/crypto_model_v2.xlsx](docs/crypto_model_v2.xlsx), currently at **v2.1**. Everything in it is a live formula, including the regression. It was built on 16 November 2026 from an earlier sheet, `crypto.xlsx`, which is kept unchanged inside the workbook as the `Original_v1` sheet.

Not investment advice.

## What the model says today

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

These figures are also on the workbook's `Summary` sheet, where they update themselves.

## Repository layout

| Path | What it is |
|---|---|
| [docs/crypto_model_v2.xlsx](docs/crypto_model_v2.xlsx) | The model |
| [docs/methodology.md](docs/methodology.md) | Equations, theory, current estimates, limitations, references |
| [docs/workbook-guide.md](docs/workbook-guide.md) | Sheet-by-sheet and column-by-column reference, named ranges, formula conventions |
| [docs/update-guide.md](docs/update-guide.md) | How to add a quarter, run a scenario, and check the result |
| [docs/data-dictionary.md](docs/data-dictionary.md) | Every input series: definition, source, confidence grade |
| [scripts/check_model.py](scripts/check_model.py) | Recomputes the model in plain Python and compares it with the workbook |
| [CHANGELOG.md](CHANGELOG.md) | Version history |

## Quick start

1. Open the workbook and go to `Summary`. It shows the latest reading, the statistics that say how far to trust it, and eight integrity checks that should all read `OK`.
2. To try your own assumptions, overwrite the yellow scenario row at the bottom of `Model`, or the yellow cells on `Params`.
3. To add a new quarter, insert a row above the scenario row, copy the row above into it and type the new inputs. Nothing else needs editing. Details are in the [update guide](docs/update-guide.md).

## The workbook at a glance

| Sheet | Purpose |
|---|---|
| `Guide` | One-page instructions and colour legend |
| `Summary` | Latest reading, scenario, trust statistics, integrity checks |
| `Model` | Inputs, diagnostics, fair value, real-time signal. One row per quarter |
| `Params` | Editable assumptions (yellow), live regression output, range control |
| `Backtest` | Out-of-sample performance of the signal |
| `Charts` | Actual vs fair value with error band; real-time Z-score; valuation gap |
| `Data_Sources` | Definition, source, link and confidence grade for every series |
| `Audit_Log` | 14 logic/formula problems in the original sheet and 87 data corrections |
| `Original_v1` | The original sheet, untouched |

The model in one line: `ln(Crypto) = a + b1·ln(M2) + b2·ln(Equity)`, estimated by `LINEST` on all actual quarters for the fair value, and re-estimated on earlier quarters only for the real-time signal. See [methodology](docs/methodology.md).

## Checking the workbook

```bash
python3 scripts/check_model.py
```

The script reads the blue input cells, recomputes the regression, the real-time signal and the backtest without using any spreadsheet formulas, and compares 23 results with the values saved in the workbook. It needs Python 3 and `openpyxl`. Run it after each quarterly update, once the workbook has been saved from Excel.

## What changed in v2.1

v2.1 is a restructuring of v2. The model, the data and every reported number are the same.

- **No more hand-edited ranges.** Estimation and backtest ranges are named ranges that end at the last actual quarter, so adding a quarter no longer means extending ranges in `Params` and `Backtest`.
- **Row insertion is safe.** Formulas that look at the previous or next quarter now find it by position, so they stay correct when a row is inserted.
- **The minimum estimation window is a live parameter.** In v2 changing it on `Params` had no effect.
- **New `Summary` sheet** with the latest reading and integrity checks.
- **Charts fixed.** The v2 charts plotted each value one quarter late. They were rebuilt, and a valuation-gap chart was added.

Full list in the [changelog](CHANGELOG.md).

## Limitations

The main ones, explained in [methodology](docs/methodology.md#limitations):

- 28 quarters is a small sample, and only 15 can be tested out of sample.
- Cointegration is not established, so there is no statistical evidence that gaps close.
- The M2 coefficient also absorbs the crypto adoption trend.
- No crypto-native variables (stablecoin supply, ETF flows, on-chain activity).
- Data quality is uneven. Many pre-2025 values are rounded reference figures and some are interpolated. Check the grades in the [data dictionary](docs/data-dictionary.md) before relying on any single cell.

