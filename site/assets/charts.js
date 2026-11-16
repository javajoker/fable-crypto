/* Small dependency-free SVG charts: a line chart with an optional band and a bar chart.
   Colours come from CSS variables so both follow the light / dark theme. */
(function () {
  "use strict";
  const NS = "http://www.w3.org/2000/svg";
  const W = 900, PAD = { l: 52, r: 16, t: 14, b: 34 };

  function el(name, attrs, parent) {
    const e = document.createElementNS(NS, name);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }

  function niceTicks(min, max, count) {
    const span = max - min || 1, step0 = span / count, mag = Math.pow(10, Math.floor(Math.log10(step0)));
    const step = [1, 2, 2.5, 5, 10].map(m => m * mag).find(s => s >= step0);
    const ticks = [];
    for (let v = Math.ceil(min / step) * step; v <= max + step * 1e-9; v += step) ticks.push(+v.toFixed(10));
    return ticks;
  }

  function frame(host, o, yMin, yMax, H) {
    host.innerHTML = "";
    host.classList.add("chart");
    const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": o.label || "chart" }, host);
    const n = o.x.length, iw = W - PAD.l - PAD.r, ih = H - PAD.t - PAD.b;
    const log = !!o.log;
    const f = v => (log ? Math.log(v) : v);
    const lo = f(yMin), hi = f(yMax);
    const sx = i => PAD.l + (o.bars ? (i + 0.5) * iw / n : (n === 1 ? iw / 2 : i * iw / (n - 1)));
    const sy = v => PAD.t + ih - (f(v) - lo) / (hi - lo) * ih;
    const ticks = log
      ? [0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100].filter(v => v >= yMin && v <= yMax)
      : niceTicks(yMin, yMax, 5);
    ticks.forEach(v => {
      el("line", { x1: PAD.l, x2: W - PAD.r, y1: sy(v), y2: sy(v), class: "grid" }, svg);
      el("text", { x: PAD.l - 8, y: sy(v) + 4, class: "tick", "text-anchor": "end" }, svg).textContent = o.yFormat(v);
    });
    const every = Math.ceil(n / 10);
    o.x.forEach((lab, i) => {
      if (i % every === 0 || i === n - 1) {
        if (i !== n - 1 && n - 1 - i < every * 0.6) return;
        el("text", { x: sx(i), y: H - 12, class: "tick", "text-anchor": "middle" }, svg).textContent = lab.replace(" ", " ");
      }
    });
    return { svg, sx, sy, n, ih, iw, H };
  }

  function tooltip(host, c, o, rowsFor) {
    const tip = document.createElement("div");
    tip.className = "chart-tip";
    tip.hidden = true;
    host.appendChild(tip);
    const guide = el("line", { y1: PAD.t, y2: c.H - PAD.b, class: "guide", visibility: "hidden" }, c.svg);
    const hit = el("rect", { x: PAD.l, y: PAD.t, width: c.iw, height: c.ih, fill: "transparent" }, c.svg);
    function move(ev) {
      const box = c.svg.getBoundingClientRect();
      const px = ((ev.touches ? ev.touches[0].clientX : ev.clientX) - box.left) / box.width * W;
      let i = Math.round(o.bars ? (px - PAD.l) / c.iw * c.n - 0.5 : (px - PAD.l) / c.iw * (c.n - 1));
      i = Math.max(0, Math.min(c.n - 1, i));
      const lines = rowsFor(i);
      if (!lines.length) { tip.hidden = true; guide.setAttribute("visibility", "hidden"); return; }
      guide.setAttribute("x1", c.sx(i)); guide.setAttribute("x2", c.sx(i)); guide.setAttribute("visibility", "visible");
      tip.innerHTML = `<b>${o.x[i]}</b>` + lines.map(l => `<div><i style="background:${l.color}"></i>${l.name}<span>${l.value}</span></div>`).join("");
      tip.hidden = false;
      const left = c.sx(i) / W * box.width;
      tip.style.left = Math.min(Math.max(left + 12, 0), box.width - tip.offsetWidth - 4) + "px";
      tip.style.top = "8px";
    }
    hit.addEventListener("mousemove", move);
    hit.addEventListener("touchstart", move, { passive: true });
    hit.addEventListener("touchmove", move, { passive: true });
    hit.addEventListener("mouseleave", () => { tip.hidden = true; guide.setAttribute("visibility", "hidden"); });
  }

  /* o: { x:[labels], series:[{name,color,values,dash,width}], bands:[{lo,hi,color,name}], split:index,
          splitLabel, yFormat, log, height } — values may contain null for "no data". */
  function line(host, o) {
    const all = [];
    o.series.forEach(s => s.values.forEach(v => v != null && all.push(v)));
    (o.bands || []).forEach(b => b.lo.concat(b.hi).forEach(v => v != null && all.push(v)));
    let yMin = Math.min(...all), yMax = Math.max(...all);
    if (o.log) { yMin *= 0.85; yMax *= 1.15; } else { yMin = Math.min(0, yMin); yMax *= 1.06; }
    const c = frame(host, o, yMin, yMax, o.height || 380);

    if (o.split != null) {
      el("rect", { x: c.sx(o.split), y: PAD.t, width: c.sx(c.n - 1) - c.sx(o.split), height: c.ih, class: "future" }, c.svg);
      el("text", { x: c.sx(o.split) + 8, y: PAD.t + 14, class: "note" }, c.svg).textContent = o.splitLabel || "scenario";
    }
    (o.bands || []).forEach(b => {
      let d = "", back = "", open = false;
      b.lo.forEach((v, i) => {
        if (v == null) return;
        d += (open ? "L" : "M") + c.sx(i) + " " + c.sy(b.hi[i]);
        back = "L" + c.sx(i) + " " + c.sy(v) + back;
        open = true;
      });
      if (d) el("path", { d: d + back + "Z", fill: b.color, class: "band" }, c.svg);
    });
    o.series.forEach(s => {
      let d = "", open = false;
      s.values.forEach((v, i) => {
        if (v == null) { open = false; return; }
        d += (open ? "L" : "M") + c.sx(i) + " " + c.sy(v);
        open = true;
      });
      el("path", { d, fill: "none", stroke: s.color, "stroke-width": s.width || 2.5, "stroke-dasharray": s.dash || "",
                   "stroke-linejoin": "round", "stroke-linecap": "round" }, c.svg);
      const li = s.values.reduce((p, v, i) => (v != null ? i : p), -1);
      if (li >= 0 && s.dot !== false) el("circle", { cx: c.sx(li), cy: c.sy(s.values[li]), r: 3.5, fill: s.color }, c.svg);
    });
    tooltip(host, c, o, i => o.series.filter(s => s.values[i] != null && !s.quiet)
      .map(s => ({ name: s.name, color: s.color, value: o.yFormat(s.values[i], true) }))
      .concat((o.bands || []).filter(b => b.lo[i] != null && b.name)
        .map(b => ({ name: b.name, color: b.color, value: o.yFormat(b.lo[i], true) + " – " + o.yFormat(b.hi[i], true) }))));
    legend(host, o.series.filter(s => !s.quiet).map(s => ({ name: s.name, color: s.color, dash: !!s.dash }))
      .concat((o.bands || []).filter(b => b.name).map(b => ({ name: b.name, color: b.color, box: true }))));
  }

  /* o: { x, values, color(value,i), refs:[{value,label}], yFormat, name, height } */
  function bars(host, o) {
    const vals = o.values.filter(v => v != null).concat((o.refs || []).map(r => r.value));
    const span = Math.max(...vals) - Math.min(...vals) || 1;
    const yMin = Math.min(0, Math.min(...vals) - span * 0.08), yMax = Math.max(0, Math.max(...vals) + span * 0.08);
    const c = frame(host, Object.assign({ bars: true }, o), yMin, yMax, o.height || 260);
    const bw = c.iw / c.n * 0.68;
    o.values.forEach((v, i) => {
      if (v == null) return;
      const y0 = c.sy(0), y1 = c.sy(v);
      el("rect", { x: c.sx(i) - bw / 2, y: Math.min(y0, y1), width: bw, height: Math.max(1, Math.abs(y1 - y0)), fill: o.color(v, i), rx: 1.5 }, c.svg);
    });
    el("line", { x1: PAD.l, x2: W - PAD.r, y1: c.sy(0), y2: c.sy(0), class: "axis" }, c.svg);
    (o.refs || []).forEach(r => {
      el("line", { x1: PAD.l, x2: W - PAD.r, y1: c.sy(r.value), y2: c.sy(r.value), class: "ref" }, c.svg);
      el("text", { x: PAD.l + 6, y: c.sy(r.value) - 5, class: "note" }, c.svg).textContent = r.label;
    });
    tooltip(host, c, Object.assign({ bars: true }, o), i => o.values[i] == null ? [] :
      [{ name: o.name, color: o.color(o.values[i], i), value: o.yFormat(o.values[i], true) }]);
  }

  function legend(host, items) {
    const d = document.createElement("div");
    d.className = "legend";
    d.innerHTML = items.map(i => `<span><i class="${i.box ? "box" : i.dash ? "dash" : ""}" style="--c:${i.color}"></i>${i.name}</span>`).join("");
    host.appendChild(d);
  }

  window.Charts = { line, bars };
})();
