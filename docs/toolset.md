# Toolset

Scripts in `scripts/` that keep the workbook, the data files and the site current. They need Python 3 and `openpyxl`; fetching also uses `curl`. A `Makefile` wraps the routine ones.

| Command | What it does |
|---|---|
| `make check` | Recomputes the model independently and compares it with the workbook |
| `make audit` | Compares the workbook's inputs with FRED and the Treasury |
| `make stablecoins` | Refreshes locked USD (`data/stablecoins.csv`) from DefiLlama |
| `make site` | Rebuilds the site's generated files |
| `make update` | `stablecoins`, `check` and `site` in one go |
| `make serve` | Serves the site at http://localhost:8765 |

## Adding a quarter

**1. Fetch what can be fetched.**

```bash
python3 scripts/fetch_inputs.py "2026 Q4"
```

This writes `data/quarters/2026Q4.json`. Six of the ten inputs come from public sources with no API key, one is estimated, and three are left empty:

| Series | Source |
|---|---|
| `m2`, `gdp`, `cpi`, `rate`, `rrp` | FRED: `M2SL`, `GDP`, `CPIAUCNS`, `DFEDTARU`, `RRPONTSYD` |
| `debt` | US Treasury, Debt to the Penny |
| `gold_t` | Estimated: previous quarter + 906 tonnes |
| `equity` | **By hand**: Siblis Research |
| `crypto` | **By hand**: CoinGecko quarterly report. The script prints today's live value as a guide |
| `gold` | **By hand**: LBMA Gold Price PM, last fixing of the quarter |

A series that is not published yet is left empty with the note "not available yet". GDP for a quarter first appears about a month after it ends.

**2. Fill in the empty values** in the JSON file. List any series you estimated under `"estimated"`; the workbook shows those in italic blue.

**3. Apply it.**

```bash
python3 scripts/add_quarter.py --from-json data/quarters/2026Q4.json
```

The script inserts a row above the scenario row, fills it, moves the scenario on by one quarter with inputs carried forward, extends the conditional formatting and rebuilds the charts. It then runs the check. A new quarter must be the one right after the latest and needs all ten inputs. Use `--dry-run` to preview.

**4. Publish.**

```bash
make update
```

**5. By hand:** add the quarter's sources and grades to the `Data_Sources` sheet, and re-read the written verdict on the `Backtest` sheet against the new numbers.

The same steps can still be done in Excel, as the [update guide](update-guide.md) describes. Run `make update` afterwards either way.

## Revising a value

Name an existing quarter and give only what changes:

```bash
python3 scripts/add_quarter.py --quarter "2026 Q3" --crypto 2.97
```

## The scripts

### `check_model.py`

Reads the blue input cells, recomputes the regression, the real-time signal and the backtest in plain Python, and compares 23 results with the workbook's own. Exit code 0 means all match.

A workbook saved by `add_quarter.py` holds formulas without calculated values, because `openpyxl` does not calculate. In that case the check lets LibreOffice calculate a temporary copy and checks that. Without LibreOffice, open the workbook in Excel, save it, and run the check again.

### `fetch_inputs.py`

`fetch_inputs.py "2026 Q4"` prepares a quarter, as above. `fetch_inputs.py --audit` compares every quarter in the workbook with the sources and lists values that differ by more than a tolerance: 1% for M2, GDP and debt, 5% for reverse repo, 0.15 points for CPI, exact for the policy rate. It changes nothing.

On 16 November 2026 the audit compared 167 values and found 3 differences, all in reverse repo, which is a memo series that no formula uses.

FRED drops connections from clients it does not recognise, so the script identifies itself as `curl`.

### `add_quarter.py`

Adds or revises a quarter, from a JSON file or from flags such as `--m2 23.70`. It refuses a quarter that is neither existing nor next, a new quarter with missing inputs, and non-positive values where a logarithm or a division needs them.

### `fetch_stablecoins.py`

Rewrites `data/stablecoins.csv` with USD stablecoin supply at each quarter-end in the workbook, from DefiLlama. This is the liquidity-flow model's locked USD. The whole file is rewritten each run so that revisions at the source are picked up.

### `build_site.py`

Regenerates `site/data/` and `site/downloads/` from the workbook, the stablecoin file and the markdown docs. It reads input cells only, so it does not need a calculated workbook. It warns if a quarter has no stablecoin value.

### `wb.py`

Shared helpers: where things are in the workbook, reading inputs, shifting row references, building charts, calculating a copy with LibreOffice. Not a command.

## Where the data lives

| Data | Home | Maintained by |
|---|---|---|
| The ten macro and market inputs | The workbook, `Model` sheet, blue cells | `add_quarter.py`, or by hand in Excel |
| Stablecoin supply | `data/stablecoins.csv` | `fetch_stablecoins.py` |
| Prepared quarters | `data/quarters/*.json` | `fetch_inputs.py`, then by hand |
| Everything under `site/data/` and `site/downloads/` | Generated; do not edit | `build_site.py` |

Stablecoin supply is not in the workbook. The liquidity-flow and driver models exist in the web app only; the workbook still holds the regression model.

## Known limits

- Three inputs have no free source and are typed in by hand.
- `add_quarter.py` was tested on a copy of the workbook, verified through LibreOffice. A workbook it has saved has not been opened in Excel as part of this work.
- A workbook saved by `add_quarter.py` loses nothing that the workbook currently uses, but `openpyxl` does not preserve every Excel feature. If you add shapes, slicers or pivot tables in Excel, check that they survive.
