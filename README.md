# Crypto Macro Fair-Value Model

How much USD can become crypto market cap? This project follows the dollars: how much USD is flowing, how much of it is locked into the crypto market and lent on to the US Treasury, and what multiple the market puts on each locked dollar. It reads the result against the Federal Reserve and Wall Street.

It has three parts:

- **A web app and portal** in [site/](site/index.html): the chain of dollars today, scenario forecasts for total crypto and Bitcoin, and the docs. Static files, no backend.
- **An Excel workbook**, [docs/crypto_model_v2.xlsx](docs/crypto_model_v2.xlsx) (v2.1): a regression of crypto market cap on M2 and US equity wealth, used as a cross-check. Every result is a live formula.
- **A toolset** in [scripts/](scripts/): fetch new data, add a quarter, verify, rebuild the site.

Not investment advice.

## The chain today

| Step | Measure | 2026 Q3 |
|---|---|---|
| 1. Flowing USD | M2 money stock | $23.4T |
| 2. Free USD | M2 − GDP ÷ V*: not needed by the real economy at normal velocity | $0.64T |
| 3. Locked USD | USD stablecoin supply: dollars that entered crypto through the primary market | $304B (1.30% of M2) |
| 3b. Treasuries behind it | Locked USD × share of reserves in Treasuries (assumed 75%) | $228B |
| 4. Crypto V | Market cap ÷ locked USD: what trading makes of each locked dollar | 9.7× |
| Result | Crypto market cap = V × locked USD | $2.96T |

The app's default forecast, the driver model, lets the Fed move locked USD through M2 and Wall Street move crypto V through equities. Tested out of sample it is a translator, not an oracle: told where equities went, it was 3% more accurate than assuming no change; not told, it was no better. A typical one-quarter error is about 26%.

## Quick start

```bash
make serve
```

then open http://localhost:8765. Or open `site/index.html` directly from disk.

## What the regression cross-check says

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

These figures are also on the workbook's `Summary` sheet and on the portal, where they update themselves.

## Repository layout

| Path | What it is |
|---|---|
| [site/](site/index.html) | Portal, forecast app and docs viewer |
| [docs/crypto_model_v2.xlsx](docs/crypto_model_v2.xlsx) | The workbook |
| [data/stablecoins.csv](data/stablecoins.csv) | Locked USD by quarter |
| [docs/methodology.md](docs/methodology.md) | Both models: equations, theory, estimates, forecast test, limitations, references |
| [docs/web-app.md](docs/web-app.md) | What the site shows and how it is put together |
| [docs/toolset.md](docs/toolset.md) | The scripts, and how to add a quarter with them |
| [docs/workbook-guide.md](docs/workbook-guide.md) | Sheet-by-sheet and column-by-column reference, named ranges, formula conventions |
| [docs/update-guide.md](docs/update-guide.md) | The same update done by hand in Excel |
| [docs/data-dictionary.md](docs/data-dictionary.md) | Every input series: definition, source, confidence grade |
| [scripts/](scripts/) | `fetch_inputs.py`, `add_quarter.py`, `fetch_stablecoins.py`, `build_site.py`, `check_model.py` |
| [Makefile](Makefile) | `make update`, `make check`, `make audit`, `make serve` |
| [CHANGELOG.md](CHANGELOG.md) | Version history |

## Keeping it current

```bash
python3 scripts/fetch_inputs.py "2026 Q4"
```

fetches six of the ten inputs from FRED and the Treasury and writes a file with three values to fill in by hand. Then:

```bash
python3 scripts/add_quarter.py --from-json data/quarters/2026Q4.json
```

```bash
make update
```

The first adds the quarter to the workbook and checks it; the second refreshes locked USD and rebuilds the site. Details in the [toolset guide](docs/toolset.md).

## Using the workbook

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

The script reads the blue input cells, recomputes the regression, the real-time signal and the backtest without using any spreadsheet formulas, and compares 23 results with the workbook's. It needs Python 3 and `openpyxl`. `make update` runs it for you.

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

- No model here beats "no change" at forecasting crypto market cap unless it is told where equities go.
- Locked USD counts stablecoins only. The Treasury backing share is an assumption.
- 28 quarters is a small sample, and only 15 can be tested out of sample.
- Cointegration is not established, so there is no statistical evidence that gaps close.
- The M2 coefficient also absorbs the crypto adoption trend.
- No crypto-native variables (stablecoin supply, ETF flows, on-chain activity).
- Data quality is uneven. Many pre-2025 values are rounded reference figures and some are interpolated. Check the grades in the [data dictionary](docs/data-dictionary.md) before relying on any single cell.

