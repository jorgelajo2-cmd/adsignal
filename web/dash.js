/* AdSignal: gráficos interactivos de las tarjetas de dashboard.
   Cada gráfico se declara en el HTML con data-chart y sus datos en JSON:
     data-chart="stems"  data-values="[0,2,1,…]"             actividad diaria
     data-chart="ring"   data-items='[["Marca",30],…]'        cuota
     data-chart="bars"   data-items='[["Marca",111],…]'       comparativa
   Sin puntero (PDF, impresión) se queda en su estado por defecto. */
(function () {
  "use strict";
  const html = document.documentElement;
  const quieto = () => html.classList.contains("static");
  const fmt = (n) => Number(n).toLocaleString("es-ES");
  const json = (el, k, d) => { try { return JSON.parse(el.dataset[k]); } catch (e) { return d; } };
  const mk = (tag, cls, padre) => { const e = document.createElement(tag); if (cls) e.className = cls; if (padre) padre.appendChild(e); return e; };
  const NS = "http://www.w3.org/2000/svg";

  function pill(chart) { return chart.querySelector(".pill") || mk("span", "pill", chart); }
  function ponPill(chart, nodo, texto) {
    // Posición sin transformaciones: vale también mientras la barra aún está creciendo
    const p = pill(chart);
    let x = 0, y = 0, n = nodo;
    while (n && n !== chart) { x += n.offsetLeft; y += n.offsetTop; n = n.offsetParent; }
    p.textContent = texto;
    p.style.left = (x + nodo.offsetWidth / 2) + "px";
    p.style.top = (y - 7) + "px";
  }

  /* --- tallos con rastro de luz --- */
  function stems(chart) {
    const vals = json(chart, "values", []);
    const unidad = chart.dataset.unit || "";
    const max = Math.max(1, ...vals);
    const caja = mk("div", "stems", chart);
    const cols = vals.map((v, i) => {
      const c = mk("div", "stem" + (v ? "" : " z"), caja);
      mk("i", "", c).style.setProperty("--h", (v / max * 100).toFixed(1) + "%");
      c.firstChild.style.setProperty("--d", i * 14 + "ms");
      return c;
    });
    const ej = json(chart, "axis", null);
    if (ej) { const a = mk("div", "stems-axis", chart); ej.forEach((t) => (mk("span", "", a).textContent = t)); }
    let def = vals.lastIndexOf(max);
    function activa(idx, trail) {
      cols.forEach((c, i) => {
        const d = Math.abs(i - idx);
        c.style.setProperty("--o", trail ? Math.max(.22, 1 - d / 5).toFixed(2) : (d === 0 ? 1 : .3));
        c.classList.toggle("on", i === idx);
      });
      const v = vals[idx];
      ponPill(chart, cols[idx].firstChild, v ? `${fmt(v)} ${unidad}`.trim() : "0");
    }
    function desdePuntero(e) {
      const r = caja.getBoundingClientRect();
      return Math.max(0, Math.min(vals.length - 1, Math.floor((e.clientX - r.left) / r.width * vals.length)));
    }
    caja.addEventListener("pointermove", (e) => activa(desdePuntero(e), true));
    caja.addEventListener("pointerleave", () => activa(def, false));
    return () => activa(def, false);
  }

  /* --- anillo de marcas --- */
  function ring(chart) {
    const items = json(chart, "items", []).filter((x) => x[1] > 0);
    const total = items.reduce((s, x) => s + x[1], 0) || 1;
    const N = 96, R0 = 58, cx = 100, cy = 100;
    const wrap = mk("div", "ring", chart);
    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("viewBox", "0 0 200 200");
    wrap.appendChild(svg);
    const centro = mk("div", "ring-c", wrap);
    const cLbl = mk("span", "", centro), cVal = mk("b", "", centro);
    const leyenda = chart.closest(".hc")?.querySelectorAll(".hc-legend [data-i]") || [];
    // reparte los ticks entre marcas según su cuota
    const dueño = [];
    let acum = 0;
    items.forEach((x, k) => { acum += x[1]; while (dueño.length < Math.round(acum / total * N)) dueño.push(k); });
    while (dueño.length < N) dueño.push(items.length - 1);
    const maxV = Math.max(...items.map((x) => x[1]));
    const base = dueño.map((k, i) => 9 + 15 * (items[k][1] / maxV) + 3 * Math.sin(i * 1.7) * Math.cos(i * .6));
    const ticks = base.map(() => { const l = document.createElementNS(NS, "line"); svg.appendChild(l); return l; });
    const ext = base.map(() => 0), meta = base.map(() => 0);
    let act = 0, ang = null, vivo = false;

    function pinta() {
      let sigue = false;
      ticks.forEach((l, i) => {
        ext[i] += (meta[i] - ext[i]) * (quieto() ? 1 : .18);
        if (Math.abs(meta[i] - ext[i]) > .05) sigue = true;
        const a = (i / N) * Math.PI * 2 - Math.PI / 2, len = base[i] + ext[i];
        const c = Math.cos(a), s = Math.sin(a);
        l.setAttribute("x1", (cx + c * R0).toFixed(2)); l.setAttribute("y1", (cy + s * R0).toFixed(2));
        l.setAttribute("x2", (cx + c * (R0 + len)).toFixed(2)); l.setAttribute("y2", (cy + s * (R0 + len)).toFixed(2));
        const on = dueño[i] === act;
        l.setAttribute("stroke", on ? `rgba(238,242,255,${(.82 + ext[i] / 60).toFixed(2)})` : `rgba(160,175,215,${(.2 + ext[i] / 40).toFixed(2)})`);
      });
      if (sigue) requestAnimationFrame(pinta); else vivo = false;
    }
    function anima() { if (quieto()) return pinta(); if (!vivo) { vivo = true; requestAnimationFrame(pinta); } }
    function marca(k) {
      act = k;
      cLbl.textContent = items[k][0];
      cVal.textContent = Math.round(items[k][1] / total * 100) + "%";
      leyenda.forEach((el) => el.classList.toggle("on", +el.dataset.i === k));
    }
    function objetivo() {
      meta.forEach((_, i) => {
        if (ang === null) { meta[i] = 0; return; }
        let d = Math.abs(i - ang); d = Math.min(d, N - d);
        meta[i] = 16 * Math.exp(-(d * d) / 18);
      });
    }
    wrap.addEventListener("pointermove", (e) => {
      const r = svg.getBoundingClientRect();
      let a = Math.atan2(e.clientY - (r.top + r.height / 2), e.clientX - (r.left + r.width / 2)) + Math.PI / 2;
      if (a < 0) a += Math.PI * 2;
      ang = a / (Math.PI * 2) * N;
      marca(dueño[Math.floor(ang) % N]); objetivo(); anima();
    });
    wrap.addEventListener("pointerleave", () => { ang = null; marca(0); objetivo(); anima(); });
    leyenda.forEach((el) => el.addEventListener("pointerenter", () => { marca(+el.dataset.i); anima(); }));
    if (!items.length) return () => {};
    return () => { marca(0); objetivo(); anima(); };
  }

  /* --- barras --- */
  function bars(chart) {
    const items = json(chart, "items", []);
    const unidad = chart.dataset.unit || "";
    const max = Math.max(1, ...items.map((x) => x[1]));
    const caja = mk("div", "vbars", chart);
    const cols = items.map(([nombre, v], i) => {
      const c = mk("div", "vbar", caja);
      const b = mk("i", "", c);
      b.style.setProperty("--h", Math.max(2, v / max * 100).toFixed(1) + "%");
      b.style.setProperty("--d", i * 60 + "ms");
      mk("span", "", c).textContent = nombre;
      return c;
    });
    const def = Math.min(items.length - 1, Math.max(0, +(chart.dataset.active ?? items.findIndex((x) => x[1] === max))));
    function activa(i) {
      cols.forEach((c, k) => c.classList.toggle("on", k === i));
      ponPill(chart, cols[i].firstChild, `${fmt(items[i][1])} ${unidad}`.trim());
    }
    cols.forEach((c, i) => c.addEventListener("pointerenter", () => activa(i)));
    caja.addEventListener("pointerleave", () => activa(def));
    return () => activa(def);
  }

  /* --- cifras que cuentan hacia arriba --- */
  function cuenta(el) {
    const fin = +el.dataset.count;
    if (!fin || quieto()) return;
    const t0 = performance.now(), dur = 1200;
    const paso = (t) => { const p = Math.min(1, (t - t0) / dur); el.textContent = fmt(Math.round(fin * (1 - Math.pow(1 - p, 3)))); if (p < 1) requestAnimationFrame(paso); };
    el.textContent = "0"; requestAnimationFrame(paso);
  }

  const TIPOS = { stems, ring, bars };
  function iniciar() {
    document.querySelectorAll(".hc").forEach((c) => c.addEventListener("pointermove", (e) => {
      const r = c.getBoundingClientRect();
      c.style.setProperty("--mx", (e.clientX - r.left) + "px");
      c.style.setProperty("--my", (e.clientY - r.top) + "px");
    }));
    const listos = [];
    document.querySelectorAll("[data-chart]").forEach((chart) => {
      const f = TIPOS[chart.dataset.chart];
      if (f) listos.push([chart, f(chart)]);
    });
    const muestra = (chart, ini) => { chart.classList.add("go"); ini(); setTimeout(ini, 60); };
    const aparecer = (el) => {
      el.classList.add("in");
      el.querySelectorAll("[data-count]").forEach(cuenta);
      listos.forEach(([c, ini]) => { if (el === c || el.contains(c)) muestra(c, ini); });
    };
    const rv = document.querySelectorAll(".rv");
    if (quieto() || !("IntersectionObserver" in window)) {
      rv.forEach((e) => e.classList.add("in"));
      listos.forEach(([c, ini]) => muestra(c, ini));
      return;
    }
    const io = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { aparecer(e.target); io.unobserve(e.target); } }), { threshold: .15 });
    rv.forEach((e) => io.observe(e));
    // gráficos fuera de un bloque .rv
    listos.forEach(([c, ini]) => { if (!c.closest(".rv")) io.observe(c); });
    // recoloca las pastillas si cambia el tamaño
    addEventListener("resize", () => listos.forEach(([c, ini]) => c.classList.contains("go") && ini()));
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", iniciar); else iniciar();
})();
