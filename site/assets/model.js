/* The model, recomputed in the browser from window.MODEL_DATA.
   Same arithmetic as the workbook and scripts/check_model.py:
   ln(crypto) = a + b1 ln(M2) + b2 ln(equity), full sample for fair value,
   earlier quarters only for the real-time signal. */
(function () {
  "use strict";

  function ols(y, xs) {
    const n = y.length, cols = [y.map(() => 1)].concat(xs), k = cols.length;
    const a = cols.map(ci => cols.map(cj => ci.reduce((s, v, t) => s + v * cj[t], 0))
      .concat(ci.reduce((s, v, t) => s + v * y[t], 0)));
    for (let i = 0; i < k; i++) {
      let p = i;
      for (let r = i + 1; r < k; r++) if (Math.abs(a[r][i]) > Math.abs(a[p][i])) p = r;
      [a[i], a[p]] = [a[p], a[i]];
      for (let r = 0; r < k; r++) if (r !== i) {
        const f = a[r][i] / a[i][i];
        a[r] = a[r].map((u, c) => u - f * a[i][c]);
      }
    }
    const beta = a.map((row, i) => row[k] / row[i]);
    const fit = y.map((_, t) => beta.reduce((s, b, j) => s + b * cols[j][t], 0));
    const sse = y.reduce((s, v, t) => s + (v - fit[t]) ** 2, 0);
    const mean = y.reduce((s, v) => s + v, 0) / n;
    const sst = y.reduce((s, v) => s + (v - mean) ** 2, 0);
    return { beta, se: Math.sqrt(sse / (n - k)), r2: 1 - sse / sst };
  }

  function nextQuarter(label) {
    const m = /^(\d{4}) Q([1-4])$/.exec(label), y = +m[1], q = +m[2];
    return (q === 4 ? y + 1 : y) + " Q" + (q % 4 + 1);
  }

  function compute(data) {
    const Q = data.quarters, P = data.params, n = Q.length;
    const y = Q.map(r => Math.log(r.crypto)), x1 = Q.map(r => Math.log(r.m2)), x2 = Q.map(r => Math.log(r.equity));
    const full = ols(y, [x1, x2]), [a, b1, b2] = full.beta, se = full.se;

    const rows = Q.map((r, t) => {
      const fv = Math.exp(a + b1 * x1[t] + b2 * x2[t]);
      const row = {
        quarter: r.quarter, actual: r.crypto, m2: r.m2, equity: r.equity, rate: r.rate,
        fv, lo: fv * Math.exp(-se), hi: fv * Math.exp(se), gap: r.crypto / fv - 1,
        resid: y[t] - Math.log(fv), z: (y[t] - Math.log(fv)) / se,
        rtZ: null, rtFv: null, signal: null, regime: null,
        nextRet: t < n - 1 ? Q[t + 1].crypto / r.crypto - 1 : null,
      };
      if (t >= P.min_window) {                      // regression on quarters before t only
        const w = ols(y.slice(0, t), [x1.slice(0, t), x2.slice(0, t)]);
        const lf = w.beta[0] + w.beta[1] * x1[t] + w.beta[2] * x2[t];
        row.rtFv = Math.exp(lf);
        row.rtZ = (y[t] - lf) / w.se;
        row.signal = row.rtZ >= P.z_rich ? "Rich vs macro" : row.rtZ <= P.z_cheap ? "Cheap vs macro" : "Neutral";
      }
      if (t >= 4) {
        const d = r.rate - Q[t - 4].rate;
        row.rateChange = d;
        row.regime = d >= P.regime_threshold ? "Tightening" : d <= -P.regime_threshold ? "Easing" : "Neutral";
      }
      return row;
    });

    // residual diagnostics
    const e = rows.map(r => r.resid);
    let num = 0, den = 0;
    for (let t = 0; t < n; t++) { den += e[t] * e[t]; if (t) num += (e[t] - e[t - 1]) ** 2; }
    const d = e.slice(1).map((v, t) => v - e[t]), lag = e.slice(0, -1);
    const sll = lag.reduce((s, v) => s + v * v, 0);
    const rho = d.reduce((s, v, t) => s + v * lag[t], 0) / sll;
    const s2 = d.reduce((s, v, t) => s + (v - rho * lag[t]) ** 2, 0) / (d.length - 1);

    // backtest: signal at t against the return over t -> t+1
    const pairs = rows.filter(r => r.rtZ !== null && r.nextRet !== null);
    const zs = pairs.map(r => r.rtZ), rs = pairs.map(r => r.nextRet), m = pairs.length;
    const mz = zs.reduce((s, v) => s + v, 0) / m, mr = rs.reduce((s, v) => s + v, 0) / m;
    const corr = zs.reduce((s, v, i) => s + (v - mz) * (rs[i] - mr), 0) /
      Math.sqrt(zs.reduce((s, v) => s + (v - mz) ** 2, 0) * rs.reduce((s, v) => s + (v - mr) ** 2, 0));
    const group = name => {
      const g = pairs.filter(r => r.signal === name);
      return { n: g.length, avg: g.length ? g.reduce((s, r) => s + r.nextRet, 0) / g.length : null,
               up: g.length ? g.filter(r => r.nextRet > 0).length / g.length : null };
    };

    return {
      rows, latest: rows[n - 1], n,
      coef: { a, b1, b2, se, r2: full.r2 },
      dw: num / den, egTau: rho / Math.sqrt(s2 / sll),
      backtest: {
        n: m, avg: mr, corr, t: corr * Math.sqrt((m - 2) / (1 - corr * corr)),
        hit: pairs.filter(r => Math.sign(-r.rtZ) === Math.sign(r.nextRet)).length / m,
        cheap: group("Cheap vs macro"), neutral: group("Neutral"), rich: group("Rich vs macro"),
      },
    };
  }

  /* Scenario projection. Not a forecast: it shows what the fitted relation implies IF M2 and
     equities follow the assumed paths. `closure` is the share of the current gap assumed to
     close each quarter (0 = the gap persists, which is what the data support). */
  function project(model, s) {
    const { a, b1, b2, se } = model.coef, last = model.latest, out = [];
    let label = last.quarter;
    for (let h = 1; h <= s.horizon; h++) {
      label = nextQuarter(label);
      const m2 = last.m2 * Math.pow(1 + s.m2Growth, h / 4), equity = last.equity * Math.pow(1 + s.eqGrowth, h / 4);
      const fv = Math.exp(a + b1 * Math.log(m2) + b2 * Math.log(equity));
      const resid = last.resid * Math.pow(1 - s.closure, h);
      const path = fv * Math.exp(resid);
      out.push({ quarter: label, h, m2, equity, fv, lo: fv * Math.exp(-se), hi: fv * Math.exp(se),
                 path, pathLo: path * Math.exp(-se), pathHi: path * Math.exp(se), gap: Math.exp(resid) - 1 });
    }
    return out;
  }

  /* Trailing one-year growth of M2 and equities, used as the "trend" preset. */
  function trailingGrowth(model) {
    const r = model.rows, n = r.length;
    return { m2: r[n - 1].m2 / r[n - 5].m2 - 1, equity: r[n - 1].equity / r[n - 5].equity - 1 };
  }

  /* ---------------------------------------------------------------- liquidity-flow model
     flowing USD (M2)  ->  free USD = M2 - GDP / V*   (not needed to turn the real economy over)
                       ->  locked USD = stablecoin supply  (dollars that crossed into crypto, primary market)
     market cap = crypto V x locked USD               (secondary-market multiplier)
     The last line is an identity: V is DEFINED as cap / locked USD. Its value is in splitting
     the forecast into three things one can reason about: M2, the lock-in share, and V. */
  function quantile(sorted, p) {
    const i = (sorted.length - 1) * p, lo = Math.floor(i), hi = Math.ceil(i);
    return sorted[lo] + (sorted[hi] - sorted[lo]) * (i - lo);
  }

  function flow(data, lookback) {
    const P = data.params;
    const rows = data.quarters.filter(r => r.stable != null).map(r => {
      const free = r.m2 - r.gdp / P.v_star;
      return { quarter: r.quarter, m2: r.m2, gdp: r.gdp, actual: r.crypto, free, locked: r.stable,
               share: r.stable / r.m2, shareFree: free > 0 ? r.stable / free : null, v: r.crypto / r.stable };
    });
    const vs = rows.slice(-lookback).map(r => r.v).sort((x, y) => x - y);
    const stats = { lookback: Math.min(lookback, rows.length), q1: quantile(vs, 0.25), med: quantile(vs, 0.5), q3: quantile(vs, 0.75),
                    min: vs[0], max: vs[vs.length - 1] };
    rows.forEach(r => { r.implied = stats.med * r.locked; r.lo = stats.q1 * r.locked; r.hi = stats.q3 * r.locked; });
    const n = rows.length, k = Math.min(8, n - 1);
    return { rows, latest: rows[n - 1], stats, shareTrend: (rows[n - 1].share - rows[n - 1 - k].share) / k };
  }

  /* s: { m2Growth (per year), shareEnd (locked / M2 at the horizon), vEnd, horizon }.
     The share moves in a straight line and V geometrically from today's values to the targets. */
  function projectFlow(fm, s) {
    const last = fm.latest, out = [];
    let label = last.quarter;
    for (let h = 1; h <= s.horizon; h++) {
      label = nextQuarter(label);
      const w = h / s.horizon;
      const m2 = last.m2 * Math.pow(1 + s.m2Growth, h / 4);
      const share = last.share + (s.shareEnd - last.share) * w;
      const v = last.v * Math.pow(s.vEnd / last.v, w);
      const locked = share * m2;
      out.push({ quarter: label, h, m2, share, locked, v, path: v * locked,
                 implied: fm.stats.med * locked, lo: fm.stats.q1 * locked, hi: fm.stats.q3 * locked });
    }
    return out;
  }

  /* ---------------------------------------------------------------- macro context, three desks
     backing = assumed share of stablecoin reserves held in US Treasuries (an assumption, not data). */
  function macro(data, backing) {
    const Q = data.quarters, n = Q.length, r = Q[n - 1], y = Q[n - 5], P = data.params;
    const dl = k => Q.slice(1).map((q, t) => Math.log(q[k] / Q[t][k]));
    const beta = ols(dl("crypto"), [dl("equity")]).beta[1];
    const gold = q => q.gold * q.gold_t * 32150.7 / 1e12;
    const d = r.rate - y.rate;
    return {
      quarter: r.quarter,
      fed: { m2: r.m2, m2Yoy: r.m2 / y.m2 - 1, rate: r.rate, rateChange: d, realRate: r.rate - r.cpi, cpi: r.cpi, rrp: r.rrp,
             rrpPeak: Math.max(...Q.map(q => q.rrp)), velocity: r.gdp / r.m2, overhang: r.m2 * P.v_star / r.gdp, free: r.m2 - r.gdp / P.v_star,
             regime: d >= P.regime_threshold ? "Tightening" : d <= -P.regime_threshold ? "Easing" : "Neutral" },
      street: { equity: r.equity, equityYoy: r.equity / y.equity - 1, buffett: r.equity / r.gdp, cryptoToEquity: r.crypto / r.equity,
                cryptoYoy: r.crypto / y.crypto - 1, beta, gold: gold(r), cryptoToGold: r.crypto / gold(r) },
      treasury: { debt: r.debt, debtYoy: r.debt - y.debt, collateral: r.stable * backing, shareOfDebt: r.stable * backing / r.debt,
                  shareOfNewDebt: (r.stable - y.stable) * backing / (r.debt - y.debt), income: r.stable * backing * r.rate / 100 },
    };
  }

  /* ---------------------------------------------------------------- driver model (the default forecast)
     Locked USD:  S = lock-in share x M2                      (the Fed's lever: M2)
     Crypto V:    dln V = beta * dln Equity + kappa * (mean ln V - ln V[-1])
                                                              (Wall Street's lever, plus a pull back to V's own average)
     Market cap = V x S
     Two estimated numbers, no intercept. Chosen as the most stable of about twenty candidates in an
     out-of-sample comparison; `tournament` below reruns the headline part of that comparison on the
     current data, against "no change" and a plain equity-beta model. */
  function drivers(data) {
    const Q = data.quarters.filter(r => r.stable != null), n = Q.length, first = data.params.min_window;
    const lc = Q.map(r => Math.log(r.crypto)), lv = Q.map(r => Math.log(r.crypto / r.stable));
    const d = k => Q.map((r, t) => (t ? Math.log(r[k] / Q[t - 1][k]) : null));
    const dc = d("crypto"), de = d("equity"), dm = d("m2"), dv = lv.map((v, t) => (t ? v - lv[t - 1] : null));
    const mean = (a, from, to) => { let s = 0; for (let i = from; i < to; i++) s += a[i]; return s / (to - from); };

    function fitV(end) {                           // observations 2 .. end-1, each using only its own past
      let a11 = 0, a22 = 0, a12 = 0, b1 = 0, b2 = 0;
      for (let i = 2; i < end; i++) {
        const x1 = de[i], x2 = mean(lv, 0, i) - lv[i - 1], y = dv[i];
        a11 += x1 * x1; a22 += x2 * x2; a12 += x1 * x2; b1 += x1 * y; b2 += x2 * y;
      }
      const det = a11 * a22 - a12 * a12;
      return { beta: (b1 * a22 - b2 * a12) / det, kappa: (a11 * b2 - a12 * b1) / det };
    }
    function fitBeta(end) {
      const idx = []; for (let i = 2; i < end; i++) idx.push(i);
      const b = ols(idx.map(i => dc[i]), [idx.map(i => de[i])]).beta;
      return { a: b[0], b: b[1] };
    }

    const names = ["No change", "Equity beta only", "Driver model"], runs = { cond: [[], [], []], unc: [[], [], []] };
    for (let t = first; t < n; t++) {
      const fv = fitV(t), fb = fitBeta(t), pull = mean(lv, 0, t) - lv[t - 1];
      [["cond", de[t], dm[t]], ["unc", mean(de, 1, t), mean(dm, 1, t)]].forEach(([key, eq, m2]) => {
        [0, fb.a + fb.b * eq, m2 + fv.beta * eq + fv.kappa * pull].forEach((f, j) => runs[key][j].push({ err: dc[t] - f, hit: (f > 0) === (dc[t] > 0) }));
      });
    }
    const rmse = a => Math.sqrt(a.reduce((s, x) => s + x.err * x.err, 0) / a.length), hit = a => a.filter(x => x.hit).length / a.length;
    const table = names.map((name, j) => ({ name,
      rmseC: rmse(runs.cond[j]), ratioC: rmse(runs.cond[j]) / rmse(runs.cond[0]), hitC: j ? hit(runs.cond[j]) : null,
      rmseU: rmse(runs.unc[j]), ratioU: rmse(runs.unc[j]) / rmse(runs.unc[0]), hitU: j ? hit(runs.unc[j]) : null }));
    const full = fitV(n);
    return { beta: full.beta, kappa: full.kappa, vbar: Math.exp(mean(lv, 0, n)), lnVbar: mean(lv, 0, n),
             table, forecasts: n - first, rmse: table[2].rmseC, upShare: runs.cond[0].filter((x, i) => dc[first + i] > 0).length / (n - first) };
  }

  /* s: { m2Growth, eqGrowth (per year), shareDrift (change in locked/M2 per year, in share units), horizon } */
  function projectDrivers(dm, fm, s) {
    const last = fm.latest, out = [], eqQ = Math.log(1 + s.eqGrowth) / 4;
    let label = last.quarter, lnV = Math.log(last.v);
    for (let h = 1; h <= s.horizon; h++) {
      label = nextQuarter(label);
      const m2 = last.m2 * Math.pow(1 + s.m2Growth, h / 4), share = Math.max(0, last.share + s.shareDrift * h / 4), locked = share * m2;
      lnV += dm.beta * eqQ + dm.kappa * (dm.lnVbar - lnV);
      const v = Math.exp(lnV), path = v * locked, band = Math.exp(dm.rmse * Math.sqrt(h));
      out.push({ quarter: label, h, m2, share, locked, v, path, implied: fm.stats.med * locked, lo: fm.stats.q1 * locked, hi: fm.stats.q3 * locked,
                 errLo: path / band, errHi: path * band });
    }
    return out;
  }

  window.CryptoModel = { compute, project, trailingGrowth, nextQuarter, ols, flow, projectFlow, macro, drivers, projectDrivers };
})();
