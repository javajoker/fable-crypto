/* Shared page chrome and formatters. */
(function () {
  "use strict";
  const D = window.MODEL_DATA;
  const pages = [["index.html", "Portal"], ["forecast.html", "Forecast"], ["docs.html", "Docs"]];
  const here = location.pathname.split("/").pop() || "index.html";

  const fmt = {
    usdT: (v, long) => v == null ? "–" : "$" + (v >= 10 || !long ? v.toFixed(v >= 10 ? 1 : (long ? 2 : 1)) : v.toFixed(2)) + "T",
    t2: v => v == null ? "–" : "$" + v.toFixed(2) + "T",
    pct: (v, digits) => v == null ? "–" : (v > 0 ? "+" : v < 0 ? "−" : "") + Math.abs(v * 100).toFixed(digits == null ? 0 : digits) + "%",
    num: (v, d) => v == null ? "–" : (v < 0 ? "−" : "") + Math.abs(v).toFixed(d == null ? 2 : d),
    usd: v => v == null ? "–" : "$" + Math.round(v).toLocaleString("en-US"),
  };

  function chrome() {
    const head = document.createElement("header");
    head.className = "site-head";
    head.innerHTML = `<div class="wrap"><a class="brand" href="index.html">Crypto Macro Fair-Value Model</a><nav>` +
      pages.map(([h, t]) => `<a href="${h}"${h === here ? ' aria-current="page"' : ""}>${t}</a>`).join("") + `</nav></div>`;
    document.body.prepend(head);
    const foot = document.createElement("footer");
    foot.className = "site-foot";
    foot.innerHTML = `<div class="wrap">Workbook ${D.version} · data to ${D.latest} · site data built ${D.generated} · ` +
      `A description of a statistical relationship, not a prediction and not investment advice.</div>`;
    document.body.append(foot);
  }

  function signalClass(s) {
    return !s ? "" : s.startsWith("Cheap") || s === "Easing" ? "good" : s.startsWith("Rich") || s === "Tightening" ? "bad" : "flat";
  }

  const B = v => "$" + Math.round(v * 1000).toLocaleString("en-US") + "B", X = v => v.toFixed(1) + "×", SH = v => (v * 100).toFixed(2) + "%";
  const kpi = (k, v, s, cls) => `<div class="panel kpi"><div class="k">${k}</div><div class="v ${cls || ""}">${v}</div><div class="s">${s || ""}</div></div>`;

  /* The chain of tiles: flowing USD -> free USD -> locked USD (and its Treasury collateral) -> V -> market cap. */
  function chain(fm, backing, live) {
    const F = fm.latest, VS = fm.stats, locked = live ? live.stable : F.locked, cap = live ? live.cap : F.actual, v = cap / locked;
    const asof = live ? ", " + F.quarter : "";
    return kpi("1 · Flowing USD", fmt.usdT(F.m2, true), "M2 money stock" + asof) +
      kpi("2 · Free USD", fmt.usdT(F.free, true), "M2 − GDP ÷ V*: not tied up in the real economy" + asof) +
      kpi("3 · Locked in crypto", B(locked), `stablecoin supply · ${SH(locked / F.m2)} of M2 · ${Math.round(locked / F.free * 100)}% of free USD`) +
      kpi("3b · Treasuries behind it", B(locked * backing), `collateral at ${Math.round(backing * 100)}% backing: the same dollars, lent on to the US government`) +
      kpi("4 · Crypto V", X(v), live && live.volume ? `market cap per locked dollar · locked USD turns over ${(live.volume / locked).toFixed(2)}× a day in trading`
        : `market cap per locked dollar · median ${X(VS.med)}`) +
      kpi("= Crypto market cap", fmt.t2(cap), `${X(v)} × ${B(locked)}`);
  }

  /* Three small tables: the Fed, Wall Street, the Treasury market. */
  function lenses(m) {
    const row = (k, v, note) => `<tr><td>${k}</td><td><b>${v}</b></td><td class="muted">${note}</td></tr>`;
    const pp = v => fmt.num(v, 2) + "pp", f = m.fed, s = m.street, t = m.treasury;
    const box = (title, sub, rows) => `<div class="panel lens"><h3>${title}</h3><p class="small muted">${sub}</p><table>${rows}</table></div>`;
    return box("The Federal Reserve", "How much money there is and what it costs.",
        row("M2", fmt.usdT(f.m2, true), `${fmt.pct(f.m2Yoy, 1)} over a year`) +
        row("Policy rate", f.rate.toFixed(2) + "%", `${pp(f.rateChange)} over a year · <span class="pill ${signalClass(f.regime)}">${f.regime}</span>`) +
        row("Real policy rate", pp(f.realRate), `rate minus CPI at ${f.cpi.toFixed(1)}%`) +
        row("Reverse repo", B(f.rrp), `spare cash parked at the Fed; peak was ${fmt.usdT(f.rrpPeak, true)}`) +
        row("Money overhang", f.overhang.toFixed(2) + "×", `M2 against what GDP needs at normal velocity; 1.00 = none`) +
        row("Free USD", fmt.usdT(f.free, true), "the overhang in dollars")) +
      box("Wall Street", "How much risk appetite there is, and where crypto sits in it.",
        row("US equity market cap", fmt.usdT(s.equity, true), `${fmt.pct(s.equityYoy)} over a year`) +
        row("Buffett ratio", s.buffett.toFixed(2) + "×", "equity market cap ÷ GDP") +
        row("Crypto market cap, one year", fmt.pct(s.cryptoYoy), "against equities over the same year, above") +
        row("Crypto ÷ US equities", (s.cryptoToEquity * 100).toFixed(1) + "%", "crypto's size next to the stock market") +
        row("Crypto beta to equities", s.beta.toFixed(1) + "×", "quarterly returns; crypto moves like leveraged equity") +
        row("Crypto ÷ gold", (s.cryptoToGold * 100).toFixed(0) + "%", `all above-ground gold is worth ${fmt.usdT(s.gold, true)}`)) +
      box("The Treasury market", "Where the locked dollars end up.",
        row("Total public debt", fmt.usdT(t.debt, true), `+${fmt.usdT(t.debtYoy, true)} over a year`) +
        row("Treasuries held by stablecoin issuers", B(t.collateral), "locked USD × assumed backing share") +
        row("Share of public debt", (t.shareOfDebt * 100).toFixed(2) + "%", "small against the stock of debt") +
        row("Share of the year's new debt", (t.shareOfNewDebt * 100).toFixed(1) + "%", "stablecoin growth as a buyer at the margin") +
        row("Interest earned by issuers", B(t.income) + " a year", "collateral × policy rate: holders of stablecoins forgo it"));
  }

  window.Site = { B, X, SH, kpi, chain, lenses,  fmt, chrome, signalClass, css: n => getComputedStyle(document.documentElement).getPropertyValue(n).trim() };
  document.addEventListener("DOMContentLoaded", chrome);
})();
