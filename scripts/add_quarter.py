#!/usr/bin/env python3
"""Add a quarter to the workbook, or revise one that is already there.

    python3 scripts/add_quarter.py --from-json data/quarters/2026Q4.json
    python3 scripts/add_quarter.py --quarter "2026 Q4" --m2 23.70 --rrp 0.01 --gdp 33.40 --cpi 3.6 \
        --rate 4.0 --debt 40.60 --equity 74.10 --crypto 2.55 --gold 4300 --gold-t 223500 --stable 0.29
    python3 scripts/add_quarter.py --quarter "2026 Q3" --crypto 2.97        # revise one value

A new quarter must be the one right after the latest quarter, and needs all eleven inputs
(ten on the Model sheet, plus stablecoin supply on the Flow sheet).
For an existing quarter, only the values given are changed.

The JSON form is what fetch_inputs.py writes:
    {"quarter": "2026 Q4", "inputs": {"m2": 23.70, ...}, "estimated": ["equity", "gold_t"]}
Series listed under "estimated" are shown in italic blue, the workbook's mark for estimates.

The script does what the update guide describes doing by hand: on Model and on Flow it inserts
a row above the scenario row, fills it, moves the scenario on by one quarter (inputs carried
forward, crypto blank) and rebuilds the charts. Afterwards it runs check_model.py. Use --dry-run to preview.
"""
import argparse
import json
import subprocess
import sys
from copy import copy
from pathlib import Path

import openpyxl
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import PatternFill

import wb as lib

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--workbook", default=str(lib.WORKBOOK))
ap.add_argument("--from-json")
ap.add_argument("--quarter", help='label such as "2026 Q4"')
for key, (_, desc, unit) in lib.ALL_INPUTS.items():
    ap.add_argument(f"--{key.replace('_', '-')}", type=float, dest=key, help=f"{desc} ({unit})")
ap.add_argument("--estimated", default="", help="comma-separated series keys to mark as estimates, e.g. equity,gold_t")
ap.add_argument("--dry-run", action="store_true")
ap.add_argument("--no-check", action="store_true")
args = ap.parse_args()

quarter, values, estimated = args.quarter, {}, [k for k in args.estimated.split(",") if k]
if args.from_json:
    spec = json.loads(Path(args.from_json).read_text())
    quarter = quarter or spec["quarter"]
    values.update({k: v for k, v in spec.get("inputs", {}).items() if v is not None})
    estimated += spec.get("estimated", [])
values.update({k: getattr(args, k) for k in lib.ALL_INPUTS if getattr(args, k) is not None})

if not quarter or not lib.QUARTER_RE.match(quarter):
    sys.exit('give the quarter as "YYYY Qn", e.g. --quarter "2026 Q4"')
unknown = [k for k in list(values) + estimated if k not in lib.ALL_INPUTS]
if unknown:
    sys.exit(f"unknown series: {unknown}. Valid keys: {', '.join(lib.ALL_INPUTS)}")
for k, v in values.items():
    if not isinstance(v, (int, float)) or isinstance(v, bool):
        sys.exit(f"{k}: {v!r} is not a number")
    if k in ("m2", "gdp", "equity", "crypto", "gold", "gold_t", "stable") and v <= 0:
        sys.exit(f"{k}: must be above zero")

book = openpyxl.load_workbook(args.workbook)
M, F = book["Model"], book["Flow"]
scen = lib.scenario_row(M)
last = scen - 1
labels = {M[f"B{r}"].value: r for r in range(lib.FIRST, scen)}
latest = M[f"B{last}"].value


def write_inputs(r, vals, italic_keys=()):
    for k, v in vals.items():
        cell = lib.cell_for(book, k, r)
        print(f"  {quarter}  {k:<7} {cell.value!s:>10} -> {v}")
        cell.value = v
        if k in italic_keys or cell.font.i:
            f = copy(cell.font)
            f.i = k in italic_keys
            cell.font = f


if quarter in labels:
    if not values:
        sys.exit(f"{quarter} exists; give at least one value to revise")
    print(f"Revising {quarter} (row {labels[quarter]})")
    write_inputs(labels[quarter], values, estimated)
elif quarter == lib.next_quarter(latest):
    missing = [k for k in lib.ALL_INPUTS if k not in values]
    if missing:
        sys.exit(f"{quarter} is a new quarter and needs all eleven inputs. Missing: {', '.join(missing)}")
    print(f"Adding {quarter} after {latest} (new row {scen}; scenario moves to row {scen + 1})")

    M.insert_rows(scen)                                   # values and styles move down; references do not
    new, moved = scen, scen + 1
    for c in range(2, lib.LAST_COL + 1):
        above, cell, old = M.cell(last, c), M.cell(new, c), M.cell(moved, c)
        cell.font, cell.fill, cell.border = copy(above.font), copy(above.fill), copy(above.border)
        cell.alignment, cell.number_format = copy(above.alignment), above.number_format
        if isinstance(above.value, str) and above.value.startswith("="):
            cell.value = lib.shift_own_row(above.value, last, new)
        if isinstance(old.value, str) and old.value.startswith("="):
            old.value = lib.shift_own_row(old.value, scen, moved)
    F.insert_rows(scen)                                   # the Flow sheet keeps the same row numbers
    for c in range(2, lib.FLOW_LAST_COL + 1):
        above, cell, old = F.cell(last, c), F.cell(new, c), F.cell(moved, c)
        cell.font, cell.fill, cell.border = copy(above.font), copy(above.fill), copy(above.border)
        cell.alignment, cell.number_format = copy(above.alignment), above.number_format
        if isinstance(above.value, str) and above.value.startswith("="):
            cell.value = lib.shift_own_row(above.value, last, new)
        if isinstance(old.value, str) and old.value.startswith("="):
            old.value = lib.shift_own_row(old.value, scen, moved)     # incl. the scenario's locked-USD default
    for rng in list(F.merged_cells.ranges):
        if rng.min_row >= scen:
            F.unmerge_cells(str(rng))
            rng.shift(row_shift=1)
            F.merge_cells(str(rng))

    M[f"B{new}"] = quarter
    write_inputs(new, values, estimated)
    for k in lib.ALL_INPUTS:                              # plain (not italic) unless flagged
        cell = lib.cell_for(book, k, new)
        f = copy(cell.font)
        f.i = k in estimated
        cell.font = f

    M[f"B{moved}"] = f"{lib.next_quarter(quarter)} (scenario)"
    for k, (col, _, _) in lib.INPUTS.items():             # scenario: carry forward, crypto blank
        M[f"{col}{moved}"] = None if k == "crypto" else values[k]

    for rng in list(M.merged_cells.ranges):               # the note under the table
        if rng.min_row >= scen:
            M.unmerge_cells(str(rng))
            rng.shift(row_shift=1)
            M.merge_cells(str(rng))
    for r in sorted((r for r in M.row_dimensions if r >= scen), reverse=True):
        M.row_dimensions[r + 1].height = M.row_dimensions[r].height

    M.conditional_formatting._cf_rules.clear()            # signal colours, one row longer
    ok, bad = PatternFill("solid", bgColor="C6EFCE"), PatternFill("solid", bgColor="FFC7CE")
    for col, good_test, bad_test in (("AG", 'LEFT(AG{0},5)="Cheap"', 'LEFT(AG{0},4)="Rich"'),
                                     ("AI", 'LEFT(AI{0},6)="Easing"', 'LEFT(AI{0},5)="Tight"')):
        rng = f"{col}{lib.FIRST}:{col}{moved}"
        M.conditional_formatting.add(rng, FormulaRule(formula=[good_test.format(lib.FIRST)], fill=ok))
        M.conditional_formatting.add(rng, FormulaRule(formula=[bad_test.format(lib.FIRST)], fill=bad))
    lib.build_charts(book, moved)
else:
    sys.exit(f'"{quarter}" is neither an existing quarter nor the next one ({lib.next_quarter(latest)}).')

if args.dry_run:
    print("Dry run: nothing saved.")
    sys.exit(0)

book.save(args.workbook)
print(f"Saved {args.workbook}")
print("Note: the saved file holds formulas without calculated values until it is opened and saved in Excel.")
if quarter not in labels:
    print("Still to do by hand: add the quarter's sources and grades to Data_Sources, re-read the Backtest verdict.")
if not args.no_check:
    here = Path(__file__).parent
    sys.exit(subprocess.run([sys.executable, str(here / "check_model.py"), args.workbook]).returncode)
