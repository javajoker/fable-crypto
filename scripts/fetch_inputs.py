#!/usr/bin/env python3
"""Fetch the inputs that have a free public source, for one quarter or as an audit of the workbook.

    python3 scripts/fetch_inputs.py "2026 Q4"      # writes data/quarters/2026Q4.json
    python3 scripts/fetch_inputs.py --audit        # compares every workbook quarter with the sources

Fetched automatically (no API key):
    m2, gdp, cpi, rate, rrp   FRED (M2SL, GDP, CPIAUCNS, DFEDTARU, RRPONTSYD)
    debt                      US Treasury Debt to the Penny
    stable, rwa               DefiLlama: USD stablecoin supply; RWA category (a narrow count)
    bills                     US Treasury, Monthly Statement of the Public Debt: bills outstanding
Estimated:
    gold_t                    previous quarter + about 900 tonnes (the workbook's method)
To be filled in by hand in the JSON (no free quarter-end source):
    equity                    Siblis Research, US equity market value
    crypto                    CoinGecko quarterly report (today's live value is printed as a guide)
    gold                      LBMA Gold Price PM, last fixing of the quarter

Then apply the file with:  python3 scripts/add_quarter.py --from-json data/quarters/2026Q4.json
"""
import argparse
import csv
import io
import json
import shutil
import subprocess
import sys
import urllib.request
from datetime import date, datetime, timezone

import wb as lib

UA = {"User-Agent": "curl/8.7.1", "Accept": "*/*"}      # FRED drops connections from unfamiliar clients
CURL = shutil.which("curl")
FRED = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={}&cosd=2018-01-01"
DEBT = ("https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny"
        "?fields=record_date,tot_pub_debt_out_amt&filter=record_date:gte:2019-10-01&sort=record_date&page[size]=10000")
STABLE = "https://stablecoins.llama.fi/stablecoincharts/all"
BILLS = ("https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/debt/mspd/mspd_table_1"
         "?fields=record_date,security_type_desc,total_mil_amt&filter=security_class_desc:eq:Bills,record_date:gte:2019-10-01"
         "&sort=record_date&page[size]=1000")
RWA = "https://api.llama.fi/charts/categories/RWA"          # a narrow count: see the data dictionary
TOLERANCE = {"m2": 0.01, "gdp": 0.01, "debt": 0.01, "bills": 0.01, "stable": 0.02, "rwa": 0.05, "rrp": 0.05, "cpi": 0.15, "rate": 0.001}   # relative, except cpi/rate (points)


def get(url):
    """curl when available (much faster and steadier against these hosts), else urllib."""
    if CURL:
        r = subprocess.run([CURL, "-sS", "-f", "-L", "-g", "-m", "45", url], capture_output=True, text=True)
        if r.returncode:
            raise RuntimeError(r.stderr.strip() or f"curl exit {r.returncode}")
        return r.stdout
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=45) as r:
        return r.read().decode()


_cache = {}


def source(key, load):
    """Load a source once per run. A failure is remembered too, so an audit does not retry it per quarter."""
    if key not in _cache:
        try:
            _cache[key] = load()
        except Exception as e:
            _cache[key] = e
    if isinstance(_cache[key], Exception):
        raise _cache[key]
    return _cache[key]


def fred(series):
    def load():
        rows = csv.reader(io.StringIO(get(FRED.format(series))))
        next(rows)
        return [(date.fromisoformat(d), float(v)) for d, v in rows if v not in ("", ".")]
    return source(series, load)


def quarter_dates(label):
    y, q = map(int, lib.QUARTER_RE.match(label).groups())
    end_month = q * 3
    start = date(y, end_month - 2, 1)
    end = date(y + (end_month == 12), end_month % 12 + 1, 1).toordinal() - 1
    return start, date(y, end_month, 1), date.fromordinal(end)


def fetch(label):
    """Return ({key: value}, {key: note}) for the series that could be fetched."""
    start, last_month, end = quarter_dates(label)
    out, notes = {}, {}

    def on(series, when):
        return next((v for d, v in fred(series) if d == when), None)

    def last_in_quarter(series):
        obs = [(d, v) for d, v in fred(series) if start <= d <= end]
        return obs[-1] if obs else (None, None)

    try:
        v = on("M2SL", last_month)
        if v is not None:
            out["m2"], notes["m2"] = round(v / 1000, 2), f"FRED M2SL {last_month:%b %Y}"
        v = on("GDP", start)
        if v is not None:
            out["gdp"], notes["gdp"] = round(v / 1000, 2), f"FRED GDP {label} (latest vintage)"
        now, ago = on("CPIAUCNS", last_month), on("CPIAUCNS", last_month.replace(year=last_month.year - 1))
        if now and ago:
            out["cpi"], notes["cpi"] = round((now / ago - 1) * 100, 1), f"FRED CPIAUCNS {last_month:%b %Y} vs a year earlier"
        d, v = last_in_quarter("DFEDTARU")
        if v is not None and (end - d).days <= 5:
            out["rate"], notes["rate"] = v, f"FRED DFEDTARU {d}"
        d, v = last_in_quarter("RRPONTSYD")
        if v is not None and (end - d).days <= 5:
            out["rrp"], notes["rrp"] = round(v / 1000, 2), f"FRED RRPONTSYD {d}"
    except Exception as e:                                             # network or format trouble: report, keep going
        notes["fred"] = f"FRED fetch failed: {e}"
    try:
        debt = source("debt", lambda: [(date.fromisoformat(r["record_date"]), float(r["tot_pub_debt_out_amt"]))
                                       for r in json.loads(get(DEBT))["data"]])
        obs = [(d, v) for d, v in debt if start <= d <= end]
        if obs and (end - obs[-1][0]).days <= 5:
            out["debt"], notes["debt"] = round(obs[-1][1] / 1e12, 2), f"Treasury Debt to the Penny {obs[-1][0]}"
    except Exception as e:
        notes["treasury"] = f"Treasury fetch failed: {e}"
    try:
        bills = source("bills", lambda: [(date.fromisoformat(r["record_date"]), float(r["total_mil_amt"]))
                                         for r in json.loads(get(BILLS))["data"] if r["security_type_desc"] == "Marketable"])
        obs = [(d, v) for d, v in bills if d == end]
        if obs:
            out["bills"], notes["bills"] = round(obs[-1][1] / 1e6, 3), f"Treasury MSPD table 1, bills, {end}"
    except Exception as e:
        notes["treasury_bills"] = f"Treasury bills fetch failed: {e}"
    try:
        stable = source("stable", lambda: sorted(
            (datetime.fromtimestamp(int(r["date"]), timezone.utc).date(), r["totalCirculatingUSD"].get("peggedUSD"))
            for r in json.loads(get(STABLE)) if r["totalCirculatingUSD"].get("peggedUSD")))
        obs = [(d, v) for d, v in stable if d <= end]
        if obs and (end - obs[-1][0]).days <= 7:
            out["stable"], notes["stable"] = round(obs[-1][1] / 1e12, 4), f"DefiLlama stablecoins {obs[-1][0]}"
        rwa = source("rwa", lambda: sorted((datetime.fromtimestamp(int(t), timezone.utc).date(), v)
                                           for t, v in json.loads(get(RWA))["tvl"].items()))
        obs = [(d, v) for d, v in rwa if d <= end]
        if obs and (end - obs[-1][0]).days <= 7:
            out["rwa"], notes["rwa"] = round(obs[-1][1] / 1e12, 5), f"DefiLlama RWA category {obs[-1][0]} (narrow count)"
        elif rwa and end < rwa[0][0]:
            out["rwa"], notes["rwa"] = 0, "before the DefiLlama RWA series starts"
    except Exception as e:
        notes["defillama"] = f"DefiLlama fetch failed: {e}"
    return out, notes


ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("quarter", nargs="?", help='e.g. "2026 Q4"')
ap.add_argument("--audit", action="store_true", help="compare the workbook's quarters with the sources")
ap.add_argument("--workbook", default=str(lib.WORKBOOK))
ap.add_argument("--out", help="output file (default data/quarters/<quarter>.json)")
args = ap.parse_args()

import openpyxl  # noqa: E402

rows, _ = lib.read_inputs(openpyxl.load_workbook(args.workbook))

if args.audit:
    print(f"{'quarter':<9}{'series':<8}{'workbook':>10}{'source':>10}{'diff':>9}   source")
    differ = compared = 0
    for row in rows:
        got, notes = fetch(row["quarter"])
        for k, v in got.items():
            compared += 1
            have = row[k]
            diff = v - have
            limit = TOLERANCE[k] if k in ("cpi", "rate") else max(TOLERANCE[k] * abs(v), 0.0005 if k == "stable" else 0.0002 if k == "rwa" else 0.011)
            if abs(diff) > limit:
                differ += 1
                d = 4 if k in ("stable", "rwa") else 2
                print(f"{row['quarter']:<9}{k:<8}{have:>10.{d}f}{v:>10.{d}f}{diff:>+9.{d}f}   {notes[k]}")
    for k in ("fred", "treasury", "treasury_bills", "defillama"):
        if k in notes:
            print(f"WARNING: {notes[k]}")
    print(f"\n{compared} values compared, {differ} differ by more than the tolerance "
          f"(1% for m2/gdp/debt/bills, 2% for stable, 5% for rrp/rwa, 0.15pp for cpi, exact for rate).")
    print("Not compared: equity, crypto, gold, gold_t (no free source). GDP is the latest vintage; the workbook holds\n"
          "earlier vintages for some quarters. Nothing was changed. To apply a value: add_quarter.py --quarter ... --<series> ...")
    sys.exit(0)

if not args.quarter or not lib.QUARTER_RE.match(args.quarter):
    sys.exit('give a quarter such as "2026 Q4", or --audit')

got, notes = fetch(args.quarter)
inputs = {k: got.get(k) for k in lib.ALL_INPUTS}
estimated = []
prev = next((r for r in rows if lib.next_quarter(r["quarter"]) == args.quarter), None)
if prev and prev["gold_t"]:
    inputs["gold_t"] = round(prev["gold_t"] + 906)
    notes["gold_t"] = "previous quarter + 906 t (about 3,600 t of net additions a year); estimate"
    estimated.append("gold_t")
try:
    live = json.loads(get("https://api.coingecko.com/api/v3/global"))["data"]["total_market_cap"]["usd"] / 1e12
    notes["crypto"] = f"FILL IN: quarter-end value from the CoinGecko quarterly report. Live value today: ${live:.2f}T"
except Exception:
    notes["crypto"] = "FILL IN: quarter-end value from the CoinGecko quarterly report"
notes["equity"] = "FILL IN: Siblis Research US equity market value; if estimated from the S&P 500 path, add 'equity' to estimated"
notes["gold"] = "FILL IN: LBMA Gold Price PM, last fixing of the quarter"

out = args.out or str(lib.ROOT / "data" / "quarters" / f"{args.quarter.replace(' ', '')}.json")
path = __import__("pathlib").Path(out)
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps({"quarter": args.quarter, "inputs": inputs, "estimated": estimated, "notes": notes}, indent=2) + "\n")

print(f"{args.quarter}")
for k in lib.ALL_INPUTS:
    v = inputs[k]
    print(f"  {k:<7} {'--' if v is None else v:>10}   {notes.get(k, 'not available yet')}")
for k in ("fred", "treasury", "treasury_bills", "defillama"):
    if k in notes:
        print(f"  WARNING: {notes[k]}")
missing = [k for k, v in inputs.items() if v is None]
print(f"\nWrote {path}")
if missing:
    print(f"Fill in {', '.join(missing)} in that file, then:")
print(f"  python3 scripts/add_quarter.py --from-json {path.relative_to(lib.ROOT) if path.is_relative_to(lib.ROOT) else path}")
