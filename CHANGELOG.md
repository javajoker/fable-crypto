# Changelog

## v2.2.1 — 16 November 2026

### Fixed

- **`#VALUE!` across the workbook in Excel.** `Params!C28`, which finds the scenario row, used `SUMPRODUCT(MAX(...))`. LibreOffice evaluates that as an array; Excel does not, and returned 0. Every named range ends at that row, so the regression, the diagnostics, the backtest and the driver model all failed. The cell is now `=MATCH("*(scenario)*",Model!$B$1:$B$500,0)`. No value changes in LibreOffice.

### Added

- **`Data_Sources`**: a row for USD stablecoin supply (DefiLlama), with definition, link, grade and notes. Series labels now name their sheet, e.g. "M2 (Model C)".

### Verification

- Opened and fully recalculated in Excel for Mac: coefficients, diagnostics, backtest, driver model and scenario match the LibreOffice values, and all nine integrity checks read `OK`.
- 29 of 29 checks pass.
- Still not done: opening a workbook saved by `add_quarter.py` in Excel.

## v2.2 — 16 November 2026

The liquidity-flow model is now in the workbook. The regression model and its numbers are unchanged: all 1,041 calculated values on `Model`, `Params` and `Backtest` match v2.1.

### Added

- **`Flow` sheet**: flowing USD, free USD, locked USD, lock-in share, Treasury collateral and crypto V for every quarter, and the driver model's one-quarter-ahead V and market cap, all as formulas. Its yellow scenario row works with the scenario row on `Model`.
- **Stablecoin supply** as an eleventh input, on `Flow` column G, for all 28 quarters.
- **`Params` rows 33–42**: the Treasury backing share and V lookback (editable), and the driver model's β, κ, average V, median and quartiles.
- **`Summary`**: a liquidity-chain block, a driver-model scenario block, and a ninth integrity check ("Locked USD filled in").
- **Two charts**: locked USD and crypto V.
- Named ranges `Flow_Locked`, `Flow_V`, `Flow_lnV`, `Flow_dV`, `Flow_X`.

### Changed

- **The workbook is the single home for data.** `data/stablecoins.csv` and `scripts/fetch_stablecoins.py` are gone. `fetch_inputs.py` fetches stablecoin supply with the other inputs and includes it in the audit; `add_quarter.py` writes it and keeps `Model` and `Flow` in step.
- `fetch_inputs.py` downloads with `curl` and no longer retries a failed source for every quarter. An audit takes about 15 seconds.
- `check_model.py` also verifies crypto V, β, κ, average and median V, and the scenario's V: 29 checks.
- The site takes the backing share and the V lookback from `Params`.
- Adding a quarter by hand in Excel now means inserting a row on two sheets. `add_quarter.py` is the safer route.

### Verification

- Recalculated in LibreOffice with no formula errors; 29 of 29 checks pass.
- β, κ, average V, the median and the quartiles in the workbook equal the web app's to at least nine digits.
- `add_quarter.py` on a copy: a new quarter without `--stable` is refused; adding 2026 Q4 and revising a stablecoin value both pass 29 of 29.
- `fetch_inputs.py --audit`: 196 values compared, 3 differ, all in reverse repo.
- Not done: opening the workbook in Excel.

## Site, liquidity-flow model and toolset — 16 November 2026

The workbook is unchanged at v2.1.

### Added

- **Web app and portal** in `site/`: static, no backend, no third-party libraries. A portal page, a forecast app and a docs viewer. All numbers are computed in the browser from the workbook's inputs.
- **Liquidity-flow model**: flowing USD (M2) → free USD → locked USD (stablecoin supply) → crypto V → market cap, with the Treasury collateral behind locked USD carried alongside.
- **Driver model**, the app's default forecast: locked USD follows M2, crypto V follows US equities and reverts toward its average. Selected by an out-of-sample comparison of about twenty forms; the comparison is rerun and shown in the app.
- **Macro lenses** for the Federal Reserve, Wall Street and the Treasury market.
- **Bitcoin** market cap and price implied by each scenario, from a dominance and supply assumption.
- **Live data** in the app, on request, from CoinGecko and DefiLlama.
- **Toolset**: `fetch_inputs.py` (FRED and Treasury, plus an audit mode), `add_quarter.py` (add or revise a quarter), `fetch_stablecoins.py`, `build_site.py`, and a `Makefile`.
- `data/stablecoins.csv`: stablecoin supply for all 28 quarters.
- Docs: `docs/web-app.md`, `docs/toolset.md`; new sections in `docs/methodology.md` and `docs/data-dictionary.md`.

### Changed

- `check_model.py` calculates a temporary copy with LibreOffice when the workbook holds no calculated values.
- The README now describes the project as a whole.

### Verification

- The browser's regression, diagnostics and backtest match the workbook and `check_model.py`.
- `add_quarter.py` was run on a copy: adding 2026 Q4 and revising 2026 Q3 both passed 23 of 23 checks. The real workbook was not modified.
- `fetch_inputs.py --audit` compared 167 workbook values with FRED and the Treasury: 3 differ, all in reverse repo (memo only).
- The site was exercised in a browser: three scenario modes, presets, live data, docs, phone width. No console errors.
- Not done: opening a workbook saved by `add_quarter.py` in Excel.

## v2.1 — 16 November 2026

A restructuring of the workbook. The model, the input data and every reported number are unchanged from v2: all 994 calculated values on `Model`, `Params` and `Backtest` match v2.

### Changed

- **Estimation ranges follow the data.** The regression, diagnostics and backtest read from named ranges (`Reg_Y`, `Reg_X`, `Resid`, `BT_Z` and others) that end at the last actual row. In v2 these were fixed ranges such as `Model!$U$9:$U$36` that had to be extended by hand in 27 formulas each quarter.
- **Cross-row formulas survive row insertion.** Change in debt, 4-quarter rate change, next-quarter return, residual change, log returns and the expanding estimation window now locate the neighbouring quarter with `INDEX(...,ROW()±k)`. In v2, inserting a row above the scenario row left the scenario row and the last quarter's next-quarter return pointing at the wrong cells.
- **The minimum estimation window is live.** `Params!C10` now controls where the real-time columns start. In v2 the cell was documentation only.
- **The next-quarter return ignores the scenario row.** In v2, typing a crypto value into the scenario row made the latest quarter show a "realised" next-quarter return. The guard keeps that out of the backtest now that its ranges are no longer fixed.
- **Backtest statistics return `n/a`** when there are too few out-of-sample quarters, not an error.
- **Update procedure.** One route only: insert a row above the scenario row and copy the row above into it.

### Added

- **`Summary` sheet**: latest reading, scenario, trust statistics and eight integrity checks.
- **Range control block** on `Params` (rows 27–31).
- **Helper columns** `AN` (out-of-sample pair) and `AO` (directional hit) on `Model`.
- **Valuation-gap chart** on `Charts`.
- **Conditional formatting** on the signal and regime columns and on the checks.
- **Input validation** on the editable `Params` cells.
- `scripts/check_model.py`, an independent recomputation of the model.
- Project documentation: `docs/methodology.md`, `docs/workbook-guide.md`, `docs/update-guide.md`, `docs/data-dictionary.md`.

### Fixed

- **Charts were shifted by one quarter.** In v2 each chart's value range started at row 8 (the units row) while its category range started at row 9, so every value was drawn against the following quarter's label. Both charts were rebuilt.

### Moved

- `docs/README.md` is now `README.md` at the repository root. Its theory, limitations and references sections moved to `docs/methodology.md`.

### Verification

- Recalculated in LibreOffice with no formula errors.
- All v2 values reproduced.
- `scripts/check_model.py` passes 23 of 23 checks on the shipped workbook, on a copy with a hypothetical extra quarter added, and on a copy with the minimum window set to 16.
- Not opened in Excel as part of this work, and row insertion was tested by reproducing its effect in a script, not by inserting a row in Excel.

## v2 — 16 November 2026

Rebuilt from `crypto.xlsx` (preserved as the `Original_v1` sheet).

- Replaced the "liquidity waterfall" with a regression of crypto market cap on M2 and US equity market cap.
- Added an error band, regression diagnostics, a real-time signal with no look-ahead, and an out-of-sample backtest.
- Signals generated by formula; in the original they were typed by hand.
- Corrected 87 input values and documented 14 logic and formula problems (`Audit_Log`).
- Removed US real estate and "private credit AUM".

## v1

The original `crypto.xlsx`.
