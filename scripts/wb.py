"""Shared helpers for the workbook tools. Not a command; see add_quarter.py, fetch_inputs.py, build_site.py."""
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKBOOK = ROOT / "docs" / "crypto_model_v2.xlsx"
FIRST = 9                       # first data row on Model
LAST_COL = 41                   # AO

# input columns on Model, in sheet order: key -> (column letter, description, unit)
INPUTS = {
    "m2":     ("C", "M2 money stock, SA, last month of quarter", "$T"),
    "rrp":    ("D", "ON RRP balance, last business day (memo)", "$T"),
    "gdp":    ("E", "Nominal GDP, SAAR", "$T"),
    "cpi":    ("F", "CPI-U YoY, last month of quarter", "%"),
    "rate":   ("G", "Fed funds target, upper bound, quarter-end", "%"),
    "debt":   ("H", "Total public debt, quarter-end", "$T"),
    "equity": ("I", "US equity market cap, quarter-end", "$T"),
    "crypto": ("J", "Total crypto market cap, quarter-end", "$T"),
    "gold":   ("K", "Gold price, LBMA PM, quarter-end", "$/oz"),
    "gold_t": ("L", "Above-ground gold stock", "tonnes"),
}
QUARTER_RE = re.compile(r"^(\d{4}) Q([1-4])$")


def next_quarter(label):
    y, q = map(int, QUARTER_RE.match(label).groups())
    return f"{y + (q == 4)} Q{q % 4 + 1}"


def scenario_row(ws):
    rows = [c.row for c in ws["B"] if isinstance(c.value, str) and "(scenario)" in c.value]
    if len(rows) != 1:
        raise SystemExit(f"expected exactly one '(scenario)' label in Model column B, found {len(rows)}")
    return rows[0]


def read_inputs(ws):
    """Rows of actual quarters and the scenario row, inputs only (no calculated values needed)."""
    scen = scenario_row(ws)

    def row(r):
        d = {"quarter": str(ws[f"B{r}"].value).replace(" (scenario)", "")}
        for key, (col, _, _) in INPUTS.items():
            cell = ws[f"{col}{r}"]
            d[key] = cell.value
            if cell.font is not None and cell.font.i:
                d.setdefault("estimated", []).append(key)
        return d

    return [row(r) for r in range(FIRST, scen)], row(scen)


def read_params(wb):
    p = wb["Params"]
    return {"v_star": p["C5"].value, "z_rich": p["C7"].value, "z_cheap": p["C8"].value,
            "regime_threshold": p["C9"].value, "min_window": int(p["C10"].value)}


def shift_own_row(formula, old, new):
    """Rewrite references to row `old` as row `new`, the way a copied row behaves in Excel.
    Absolute rows ($U$9) and whole-column references are left alone."""
    return re.sub(r"(?<![A-Z$])(\$?[A-Z]{1,3})%d(?!\d)" % old, lambda m: f"{m.group(1)}{new}", formula)


def recalculated_copy(path):
    """Return a temp copy of the workbook with formulas calculated by LibreOffice, or None if unavailable."""
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        mac = Path("/Applications/LibreOffice.app/Contents/MacOS/soffice")
        soffice = str(mac) if mac.exists() else None
    if not soffice:
        return None
    out = Path(tempfile.mkdtemp(prefix="crypto_model_"))
    profile = Path(tempfile.mkdtemp(prefix="lo_profile_"))
    subprocess.run([soffice, f"-env:UserInstallation=file://{profile}", "--headless", "--calc",
                    "--convert-to", "xlsx:Calc MS Excel 2007 XML", "--outdir", str(out), str(path)],
                   check=True, capture_output=True, timeout=180)
    return out / Path(path).name


def has_cached_values(path):
    import openpyxl
    wb = openpyxl.load_workbook(path, data_only=True)
    return isinstance(wb["Params"]["C19"].value, (int, float))


def build_charts(wb, scen):
    """(Re)build the three charts on `Charts` so they cover rows FIRST..scen of Model."""
    from openpyxl.chart import BarChart, LineChart, Reference, Series
    from openpyxl.chart.series import SeriesLabel
    from openpyxl.chart.shapes import GraphicalProperties
    from openpyxl.drawing.line import LineProperties

    model, sheet = wb["Model"], wb["Charts"]
    sheet._charts = []
    cats = Reference(model, min_col=2, min_row=FIRST, max_row=scen)

    def values(col):
        return Reference(model, min_col=col, min_row=FIRST, max_row=scen)

    def finish(chart, title, fmt, anchor):
        chart.title = title
        chart.title.overlay = False
        chart.roundedCorners = False
        chart.x_axis.delete = False
        chart.y_axis.delete = False
        chart.x_axis.tickLblSkip = 2
        chart.x_axis.tickLblPos = "low"
        chart.x_axis.majorTickMark = "none"
        chart.y_axis.majorTickMark = "none"
        chart.y_axis.number_format = fmt
        chart.y_axis.majorGridlines.spPr = GraphicalProperties(ln=LineProperties(solidFill="E3E2DD", w=6350))
        chart.width, chart.height = 26, 10.5
        chart.display_blanks = "gap"
        chart.set_categories(cats)
        sheet.add_chart(chart, anchor)

    line = LineChart()
    for col, title, color, width, dash in ((10, "Actual crypto market cap", "2A78D6", 28575, "solid"),
                                           (24, "Fair value", "EB6834", 28575, "solid"),
                                           (25, "Fair value -1 SE", "9A9992", 12700, "dash"),
                                           (26, "Fair value +1 SE", "9A9992", 12700, "dash")):
        s = Series(values(col), title=None)
        s.tx = SeriesLabel(v=title)
        s.graphicalProperties = GraphicalProperties(ln=LineProperties(solidFill=color, w=width, prstDash=dash))
        s.marker.symbol = "none"
        s.smooth = False
        line.series.append(s)
    line.legend.position = "b"
    line.legend.overlay = False
    finish(line, "Crypto market cap vs macro fair value ($T)", "0.0", "B4")

    for col, label, color, title, fmt, anchor in (
            (32, "Real-time Z-score", "2A78D6", "Real-time valuation Z-score (below -1 = cheap vs macro, above +1 = rich)", "0.0", "B27"),
            (27, "Valuation gap", "EB6834", "Valuation gap, full sample (actual / fair value - 1)", "0%", "B50")):
        bar = BarChart()
        bar.type = "col"
        bar.gapWidth = 60
        s = Series(values(col), title=None)
        s.tx = SeriesLabel(v=label)
        s.graphicalProperties = GraphicalProperties(solidFill=color)
        s.invertIfNegative = False
        bar.series.append(s)
        bar.legend = None
        finish(bar, title, fmt, anchor)
