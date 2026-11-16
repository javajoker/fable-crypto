#!/usr/bin/env python3
"""Refresh data/stablecoins.csv: USD-pegged stablecoin supply at each quarter-end in the workbook.

    python3 scripts/fetch_stablecoins.py

Stablecoin supply is the liquidity-flow model's measure of "locked USD": dollars that have
crossed into the crypto market through the primary market (minting) and sit there as dollars.
Source: DefiLlama, https://stablecoins.llama.fi/stablecoincharts/all (free, no key).
The whole file is rewritten each run, so revisions at the source are picked up.
"""
import csv
import json
import subprocess
from datetime import datetime, timezone

import openpyxl

import wb as lib

URL = "https://stablecoins.llama.fi/stablecoincharts/all"
OUT = lib.ROOT / "data" / "stablecoins.csv"

raw = subprocess.run(["curl", "-s", "-m", "60", "-A", "curl/8.7.1", URL], capture_output=True, text=True, check=True).stdout
series = {datetime.fromtimestamp(int(r["date"]), timezone.utc).date(): r["totalCirculatingUSD"].get("peggedUSD")
          for r in json.loads(raw)}
days = sorted(d for d, v in series.items() if v)

rows, _ = lib.read_inputs(openpyxl.load_workbook(lib.WORKBOOK)["Model"])
out = []
for r in rows:
    y, q = map(int, lib.QUARTER_RE.match(r["quarter"]).groups())
    end = datetime(y + (q == 4), q % 4 * 3 + 1, 1).date().toordinal() - 1          # last day of the quarter
    day = max((d for d in days if d.toordinal() <= end), default=None)
    if day is None or end - day.toordinal() > 7:
        print(f"{r['quarter']}: no observation near quarter-end, skipped")
        continue
    out.append((r["quarter"], day.isoformat(), round(series[day] / 1e12, 4)))

OUT.parent.mkdir(exist_ok=True)
with open(OUT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["quarter", "observed", "stablecoins_usd_trillion"])
    w.writerows(out)
print(f"wrote {OUT.relative_to(lib.ROOT)}: {len(out)} quarters, latest {out[-1][0]} = ${out[-1][2] * 1000:.1f}B "
      f"(source latest: {days[-1]} = ${series[days[-1]] / 1e9:.1f}B)")
