#!/usr/bin/env python3
"""Independent check of crypto_model_v2.xlsx.

Reads the blue input cells from the `Model` sheet, recomputes the regression, the
real-time (expanding-window) signal and the backtest statistics in plain Python, and
compares them with the values Excel last calculated and saved in the workbook.

    python3 scripts/check_model.py [path/to/workbook.xlsx]

Exit code 0 = everything matches, 1 = at least one mismatch.
Needs only `openpyxl`. The workbook must have been saved by Excel or LibreOffice
after its last change, otherwise there are no calculated values to compare.
"""
import math
import sys

import openpyxl

PATH = sys.argv[1] if len(sys.argv) > 1 else "docs/crypto_model_v2.xlsx"
FIRST = 9          # first data row on Model
TOL = 1e-6


def ols(y, xs):
    """OLS with intercept. xs = list of regressor columns. Returns (coefs, se_regression, r2)."""
    n, k = len(y), len(xs) + 1
    cols = [[1.0] * n] + xs
    a = [[sum(ci[t] * cj[t] for t in range(n)) for cj in cols] + [sum(ci[t] * y[t] for t in range(n))] for ci in cols]
    for i in range(k):                                   # Gauss-Jordan with partial pivoting
        p = max(range(i, k), key=lambda r: abs(a[r][i]))
        a[i], a[p] = a[p], a[i]
        for r in range(k):
            if r != i:
                f = a[r][i] / a[i][i]
                a[r] = [u - f * v for u, v in zip(a[r], a[i])]
    beta = [a[i][k] / a[i][i] for i in range(k)]
    fit = [sum(b * c[t] for b, c in zip(beta, cols)) for t in range(n)]
    sse = sum((y[t] - fit[t]) ** 2 for t in range(n))
    mean = sum(y) / n
    sst = sum((v - mean) ** 2 for v in y)
    return beta, math.sqrt(sse / (n - k)), 1 - sse / sst


def corr(a, b):
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / math.sqrt(
        sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))


def sign(v):
    return (v > 0) - (v < 0)


wb = openpyxl.load_workbook(PATH, data_only=True)
M, P, B = wb["Model"], wb["Params"], wb["Backtest"]

scen = max(c.row for c in M["B"] if isinstance(c.value, str) and "(scenario)" in c.value)
last = scen - 1
rows = range(FIRST, last + 1)
m2 = [M[f"C{r}"].value for r in rows]
eq = [M[f"I{r}"].value for r in rows]
cr = [M[f"J{r}"].value for r in rows]
if any(not isinstance(v, (int, float)) or v <= 0 for v in m2 + eq + cr):
    sys.exit("FAIL: blank, non-numeric or non-positive M2 / equity / crypto input in an actual quarter")
y, x1, x2 = [math.log(v) for v in cr], [math.log(v) for v in m2], [math.log(v) for v in eq]
n = len(y)

results = []


def check(label, expected, cell_value):
    ok = isinstance(cell_value, (int, float)) and abs(expected - cell_value) <= TOL * max(1.0, abs(expected))
    results.append(ok)
    print(f"{'ok  ' if ok else 'FAIL'}  {label:<46} python {expected:>12.6f}   workbook {cell_value!s:>20}")


# ---- full-sample regression (Params)
(a, b1, b2), se, r2 = ols(y, [x1, x2])
check("intercept a", a, P["C14"].value)
check("b1 (ln M2)", b1, P["C15"].value)
check("b2 (ln equity)", b2, P["C16"].value)
check("R-squared", r2, P["C18"].value)
check("SE of regression", se, P["C19"].value)
check("observations", n, P["C20"].value)

resid = [y[t] - (a + b1 * x1[t] + b2 * x2[t]) for t in range(n)]
dw = sum((resid[t] - resid[t - 1]) ** 2 for t in range(1, n)) / sum(e * e for e in resid)
check("Durbin-Watson", dw, P["C21"].value)

d, lag = [resid[t] - resid[t - 1] for t in range(1, n)], resid[:-1]
rho = sum(u * v for u, v in zip(d, lag)) / sum(v * v for v in lag)
s2 = sum((u - rho * v) ** 2 for u, v in zip(d, lag)) / (len(d) - 1)
check("Engle-Granger tau", rho / math.sqrt(s2 / sum(v * v for v in lag)), P["C22"].value)

ry, rx = [y[t] - y[t - 1] for t in range(1, n)], [x2[t] - x2[t - 1] for t in range(1, n)]
(_, beta), se_r, _ = ols(ry, [rx])
mx = sum(rx) / len(rx)
check("crypto beta to equities", beta, P["C23"].value)
check("  t-stat of beta", beta / (se_r / math.sqrt(sum((v - mx) ** 2 for v in rx))), P["C24"].value)

# ---- latest fair value (Model, last actual row)
fv = math.exp(a + b1 * x1[-1] + b2 * x2[-1])
check("fair value, latest quarter", fv, M[f"X{last}"].value)
check("valuation gap, latest quarter", cr[-1] / fv - 1, M[f"AA{last}"].value)

# ---- real-time signal, earlier quarters only (Model AD:AF)
window = int(P["C10"].value)
z = {}
for t in range(window, n):
    (ta, tb1, tb2), tse, _ = ols(y[:t], [x1[:t], x2[:t]])
    z[t] = (y[t] - (ta + tb1 * x1[t] + tb2 * x2[t])) / tse
bad = [FIRST + t for t, v in z.items()
       if not isinstance(M[f"AF{FIRST + t}"].value, (int, float)) or abs(v - M[f"AF{FIRST + t}"].value) > 1e-5]
early = [r for r in range(FIRST, FIRST + window) if isinstance(M[f"AF{r}"].value, (int, float))]
results.append(not bad and not early)
print(f"{'ok  ' if not bad and not early else 'FAIL'}  real-time Z-score, {len(z)} quarters from row {FIRST + window}"
      + (f"   mismatch rows {bad} / unexpected early rows {early}" if bad or early else ""))
check("real-time Z, latest quarter", z[n - 1], M[f"AF{last}"].value)

# ---- backtest (signal at t, return over t -> t+1; the last quarter has no next return yet)
pairs = [(z[t], cr[t + 1] / cr[t] - 1) for t in range(window, n - 1)]
zs, rets = [p[0] for p in pairs], [p[1] for p in pairs]
c = corr(zs, rets)
check("out-of-sample quarters", len(pairs), B["C9"].value)
check("average next-quarter return", sum(rets) / len(rets), B["D9"].value)
check("correlation Z vs next return", c, B["C12"].value)
check("  t-stat of correlation", c * math.sqrt((len(pairs) - 2) / (1 - c * c)), B["C13"].value)
check("directional hit rate", sum(sign(-u) == sign(v) for u, v in pairs) / len(pairs), B["C14"].value)
cheap, rich = P["C8"].value, P["C7"].value
check("'Cheap' quarters", sum(u <= cheap for u in zs), B["C6"].value)
check("'Neutral' quarters", sum(cheap < u < rich for u in zs), B["C7"].value)
check("'Rich' quarters", sum(u >= rich for u in zs), B["C8"].value)

# ---- the workbook's own integrity checks
if "Summary" in wb.sheetnames:
    overall = next((c.offset(0, 1).value for c in wb["Summary"]["B"] if c.value == "Overall"), None)
    results.append(overall == "ALL OK")
    print(f"{'ok  ' if overall == 'ALL OK' else 'FAIL'}  Summary integrity checks: {overall}")

print(f"\n{PATH}: {n} quarters ({M[f'B{FIRST}'].value} to {M[f'B{last}'].value}), "
      f"{sum(results)}/{len(results)} checks passed")
sys.exit(0 if all(results) else 1)
