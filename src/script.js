const DATA = __DATA__;
// Logo and colour follow the model maker; OpenCode Go is a plan, shown as a small mark on the badge.
const MAKERS = {
  "Claude": { logo: "logo-claude", key: "claude" }, "ChatGPT": { logo: "logo-openai", key: "chatgpt" },
  "Gemini": { logo: "logo-gemini", key: "gemini" }, "Grok": { logo: "logo-grok", key: "grok" },
  "Muse": { logo: "logo-meta", key: "muse" }, "DeepSeek": { logo: "logo-deepseek", key: "deepseek" },
  "Kimi": { logo: "logo-kimi", key: "kimi" },
};
const pcol = m => `var(--p-${MAKERS[m.maker || m].key})`;
const pon = m => `var(--on-${MAKERS[m.maker || m].key})`;
const EFFORT_ORDER = ["none", "low", "medium", "high", "xhigh", "max", "default", "not stated"];
const GRADE_TEXT = { measured: "measured", inferred: "inferred", modelled: "modelled" };
const ELIGIBLE = g => g === "measured";
const usd = v => v >= 1 ? "$" + v.toFixed(2) : v >= 0.01 ? "$" + v.toFixed(3) : "$" + v.toFixed(4);
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
const store = {
  get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} },
};
const params = new URLSearchParams(location.search);

const capMode = "public";  // public capacity sources only
const BENCHES = ["coding"];
let bench = BENCHES.includes(params.get("bench")) ? params.get("bench") : (BENCHES.includes(store.get("subvalue-bench-v3")) ? store.get("subvalue-bench-v3") : "coding");
// Filter: a maker name, "go" for everything served through OpenCode Go, or "" for all.
let filter = params.has("provider") ? params.get("provider") : (store.get("subvalue-filter") || "");
let B, P, ALL;
// Focus: tapping a point shows only that model (same plan and family) at every effort level.
let focus = params.get("focus") || "";
const famKey = p => p.plan + "|" + p.family;
const inFilter = p => !filter || (filter === "go" ? p.via_go : p.maker === filter);
const isFocus = p => !!focus && famKey(p) === focus;
function selectData() {
  B = DATA.benchmarks[bench]; ALL = B.modes[capMode];
  if (filter && !ALL.some(inFilter)) filter = "";
  if (focus && !ALL.some(p => famKey(p) === focus && inFilter(p))) focus = "";
  P = ALL.filter(inFilter);
  document.getElementById("benchabout").innerHTML = `<b>${esc(B.long)}.</b> ${esc(B.about)} Score: ${esc(B.score)}. <a href="${esc(B.url)}">Source</a>.`;
  document.querySelectorAll("#benchseg button").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.bench === bench)));
  drawFilters();
}
const scale = { 1: store.get("subvalue-scale1") === "linear" ? "linear" : "log", 2: store.get("subvalue-scale2") === "linear" ? "linear" : "log" };
const qScale = params.get("scale");
if (qScale === "log" || qScale === "linear") scale[1] = scale[2] = qScale;


// Badge: maker logo in a round badge. Measured: filled. Inferred: hollow ring. Modelled: dashed ring.
const R = 11;
function badge(p) {
  const m = MAKERS[p.maker], s = 14, col = pcol(p), filled = ELIGIBLE(p.grade), dash = p.grade === "modelled" ? ` stroke-dasharray="3 2.5"` : "";
  return `<circle r="${R}" fill="${filled ? col : "var(--surface)"}" stroke="${filled ? "var(--surface)" : col}" stroke-width="2"${dash}/>
    ${p.grade === "own" ? `<circle r="${R + 3.5}" fill="none" stroke="${col}" stroke-width="1.5"/>` : ""}
    <use href="#${m.logo}" x="${-s / 2}" y="${-s / 2}" width="${s}" height="${s}" fill="${filled ? pon(p) : col}"/>
    ${p.via_go ? `<g transform="translate(${R - 2} ${R - 2})"><circle r="5.5" fill="var(--surface)" stroke="var(--p-opencode)" stroke-width="1"/><use href="#logo-opencode" x="-3.5" y="-3.5" width="7" height="7" fill="var(--p-opencode)"/></g>` : ""}`;
}
function makerBadge(maker) {
  return `<svg width="20" height="20" viewBox="-10 -10 20 20" aria-hidden="true"><circle r="9.5" fill="${pcol(maker)}"/><use href="#${MAKERS[maker].logo}" x="-6" y="-6" width="12" height="12" fill="${pon(maker)}"/></svg>`;
}
const goBadge = `<svg width="20" height="20" viewBox="-10 -10 20 20" aria-hidden="true"><circle r="9" fill="var(--surface)" stroke="var(--p-opencode)" stroke-width="1.5"/><use href="#logo-opencode" x="-6" y="-6" width="12" height="12" fill="var(--p-opencode)"/></svg>`;
const pointBadge = p => `<span style="display:inline-flex;align-items:center;gap:6px">${makerBadge(p.maker)}${esc(p.maker)}${p.via_go ? " · via Go" : ""}</span>`;
const gradePill = g => `<span class="grade ${g}">${GRADE_TEXT[g]}</span>`;

// Provider filter chips (makers present in the current benchmark, plus OpenCode Go).
function drawFilters() {
  const makers = Object.keys(MAKERS).filter(m => ALL.some(p => p.maker === m));
  const hasGo = ALL.some(p => p.via_go);
  const chip = (val, label, icon) => `<button type="button" class="chip${val ? "" : " all"}" data-f="${esc(val)}" aria-pressed="${String(filter === val && (val !== "" || !focus))}">${icon}${esc(label)}</button>`;
  const fp = focus && ALL.find(p => famKey(p) === focus);
  const focusChip = fp ? `<button type="button" class="chip" id="focusChip" aria-pressed="true" title="Stop highlighting">${makerBadge(fp.maker)}Highlighting ${esc(fp.family)} · ✕</button>` : "";
  document.getElementById("filters").innerHTML = chip("", "All", "") + makers.map(m => chip(m, m, makerBadge(m))).join("") + (hasGo ? chip("go", "OpenCode Go", goBadge) : "") + focusChip;
  const fc = document.getElementById("focusChip");
  if (fc) fc.addEventListener("click", () => { focus = ""; workLabel = ""; selectData(); renderAll(); });
  document.querySelectorAll("#filters .chip").forEach(b => b.addEventListener("click", () => {
    filter = filter === b.dataset.f ? "" : b.dataset.f; focus = "";
    store.set("subvalue-filter", filter);
    selectData(); renderAll();
  }));
}

function niceTicks(max) {
  const raw = max / 5, mag = Math.pow(10, Math.floor(Math.log10(raw)));
  const step = [1, 2, 2.5, 5, 10].map(f => f * mag).find(s => raw <= s);
  const top = Math.ceil(max / step) * step, t = [];
  for (let v = 0; v <= top + step / 2; v += step) t.push(+v.toFixed(6));
  return { top, ticks: t };
}
// Axis fitted to the data: log uses padded min/max with 1-2-5 ticks; linear starts at 0 with nice ticks.
function axis(kind, values, a, b) {
  const lo = Math.min(...values), hi = Math.max(...values);
  if (kind === "log") {
    const pad = lo === hi ? 0.3 : 0.12;
    const d0 = Math.log10(lo) - pad, d1 = Math.log10(hi) + pad, ticks = [];
    const steps = d1 - d0 < 1.6 ? [1, 1.5, 2, 3, 5, 7] : [1, 2, 5];
    for (let e = Math.floor(d0); e <= Math.ceil(d1); e++) for (const f of steps) {
      const v = f * Math.pow(10, e), l = Math.log10(v);
      if (l >= d0 && l <= d1) ticks.push(+v.toPrecision(3));
    }
    return { f: v => a + (Math.log10(v) - d0) / (d1 - d0) * (b - a), ticks };
  }
  const { top, ticks } = niceTicks(hi * 1.05);
  return { f: v => a + v / top * (b - a), ticks };
}
const fmtTick = (v, money) => money ? "$" + (v >= 1 || v === 0 ? v : +v.toPrecision(2)) : String(v);

function frame(kind, xAx, yAx, m, W, H, xTitle, yTitle, xMoney = false, yMoney = true) {
  let g = "";
  for (const v of xAx.ticks) g += `<line x1="${xAx.f(v)}" x2="${xAx.f(v)}" y1="${m.t}" y2="${H - m.b}" stroke="var(--grid)"/><text x="${xAx.f(v)}" y="${H - m.b + 16}" text-anchor="middle">${fmtTick(v, xMoney)}</text>`;
  for (const v of yAx.ticks) g += `<line x1="${m.l}" x2="${W - m.r}" y1="${yAx.f(v)}" y2="${yAx.f(v)}" stroke="var(--grid)"/><text x="${m.l - 8}" y="${yAx.f(v) + 4}" text-anchor="end">${fmtTick(v, yMoney)}</text>`;
  g += `<line x1="${m.l}" x2="${W - m.r}" y1="${H - m.b}" y2="${H - m.b}" stroke="var(--axis)"/>`;
  g += `<text x="${(m.l + W - m.r) / 2}" y="${H - 6}" text-anchor="middle">${xTitle} (${kind})</text>`;
  g += `<text transform="translate(14 ${(m.t + H - m.b) / 2}) rotate(-90)" text-anchor="middle">${yTitle} (${kind})</text>`;
  return g;
}

// Line through each model's effort levels, in a dimmed version of the maker's colour.
function familyLines(pts, fx, fy, hl = "") {
  const fam = {};
  for (const p of pts) (fam[p.plan + "|" + p.family] = fam[p.plan + "|" + p.family] || []).push(p);
  let g = "";
  for (const arr of Object.values(fam)) {
    if (arr.length < 2) continue;
    arr.sort((a, b) => EFFORT_ORDER.indexOf(a.effort) - EFFORT_ORDER.indexOf(b.effort));
    g += `<polyline points="${arr.map(p => `${fx(p)},${fy(p)}`).join(" ")}" fill="none" stroke="${pcol(arr[0])}" stroke-width="${hl && famKey(arr[0]) === hl ? 2.5 : 1.5}" stroke-linejoin="round" opacity="${!hl ? 0.35 : famKey(arr[0]) === hl ? 0.9 : 0.08}"/>`;
  }
  return g;
}

function wireTips(svg, tip, html) {
  const show = el => {
    tip.innerHTML = html(P[+el.dataset.i]);
    tip.style.display = "block";
    const bx = el.getBoundingClientRect(), wrap = svg.parentElement.getBoundingClientRect();
    let left = bx.left - wrap.left + 22; if (left > wrap.width - 290) left = Math.max(4, bx.left - wrap.left - 290);
    tip.style.left = left + "px"; tip.style.top = Math.max(0, bx.top - wrap.top - 10) + "px";
  };
  const hide = () => tip.style.display = "none";
  svg.querySelectorAll(".pt").forEach(el => {
    el.addEventListener("mouseenter", () => show(el)); el.addEventListener("focus", () => show(el));
    el.addEventListener("click", () => { const p = P[+el.dataset.i]; const same = workLabel === p.label; focus = same ? "" : famKey(p); workLabel = same ? "" : p.label; hide(); selectData(); renderAll(); });
    el.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); el.dispatchEvent(new Event("click")); } });
    el.addEventListener("mouseleave", hide); el.addEventListener("blur", hide);
  });
}
function labelAt(text, x, y, W, cls, side) {
  if (side === "above") return `<text class="lbl ${cls}" x="${Math.min(Math.max(x, 60), W - 60)}" y="${y - R - 7}" text-anchor="middle">${esc(text)}</text>`;
  const right = x < W - 150;
  return `<text class="lbl ${cls}" x="${x + (right ? 16 : -16)}" y="${y + 4}" text-anchor="${right ? "start" : "end"}">${esc(text)}</text>`;
}
const tipHtml = p => `<b>${esc(p.label)}</b> ${gradePill(p.grade)}
  <div>${esc(p.plan)} · effort ${esc(p.effort)}</div>
  <div>${usd(p.per_task)} per task · score ${p.idx} · ${p.mins} min per task</div>
  <div>${p.tasks.toLocaleString()} tasks/mo at full cap · API ${usd(p.api)}/task</div>
  <div style="margin-top:4px">${esc(p.note)}</div>`;

const gradeLegend = `<span><svg width="14" height="14" viewBox="-7 -7 14 14"><circle r="6" fill="var(--ink2)"/></svg>Measured</span>
  <span><svg width="14" height="14" viewBox="-7 -7 14 14"><circle r="5.5" fill="none" stroke="var(--ink2)" stroke-width="1.5"/></svg>Inferred</span>
  <span><svg width="14" height="14" viewBox="-7 -7 14 14"><circle r="5.5" fill="none" stroke="var(--ink2)" stroke-width="1.5" stroke-dasharray="3 2.5"/></svg>Modelled</span>
  <span>${goBadge.replace('width="20" height="20"', 'width="14" height="14"')}Served via OpenCode Go</span>
  <span><svg width="26" height="10"><line x1="1" x2="25" y1="5" y2="5" stroke="var(--p-claude)" stroke-width="1.5" opacity="0.45"/></svg>Effort levels of one model</span>`;
const drawLegend = () => document.getElementById("legend").innerHTML = gradeLegend + `<span><svg width="26" height="14"><line x1="4" x2="22" y1="7" y2="7" stroke="var(--ink)" stroke-opacity="0.12" stroke-width="10" stroke-linecap="round"/></svg>${yMode === "score" ? "Quality frontier" : "Cost–speed frontier"}</span><span><svg width="34" height="14" viewBox="0 0 34 14"><circle cx="7" cy="7" r="6" fill="var(--ink2)"/><circle cx="25" cy="7" r="6" fill="var(--ink2)" opacity="0.3"/></svg>${yMode === "score" ? "On the frontier / something cheaper scores as well" : "On the frontier / beaten on cost and time"}</span><span><b style="color:var(--ink)">Bold label</b>&nbsp;cheapest measured</span>`;

function emptyChart(svg, W, H) {
  svg.setAttribute("width", W); svg.setAttribute("height", 120);
  svg.innerHTML = `<text x="${W / 2}" y="60" text-anchor="middle">No points for this provider in this benchmark</text>`;
}

// ---- Chart 1: score against subscription cost per task, with the quality frontier ----
// Minimum score: points below it fade and drop out of the ranking, so a cheap weak model can't win by default.
let minScore = null;  // null = off (lowest score in the benchmark)
let maxCost = null;   // null = off; subscription $ per task
let maxMins = null;   // null = off; minutes per task
const qn = k => { const v = parseFloat(params.get(k)); return isNaN(v) ? null : v; };
minScore = qn("min"); maxCost = qn("maxcost"); maxMins = qn("maxmin");
let yMode = params.get("y") === "time" || (params.get("y") !== "score" && store.get("subvalue-y2") === "time") ? "time" : "score";  // score is the default
const passes = p => (minScore === null || p.idx >= minScore) && (maxCost === null || p.per_task <= maxCost) && (maxMins === null || p.mins <= maxMins);
const failReason = p => minScore !== null && p.idx < minScore ? "Below the minimum score"
  : maxCost !== null && p.per_task > maxCost ? "Above the maximum cost per task"
  : maxMins !== null && p.mins > maxMins ? "Above the maximum minutes per task" : "";
const ranked = () => [...P].filter(passes).sort((a, b) => a.per_task - b.per_task);

// Quality frontier: walking from cheapest to dearest, keep each point that beats every cheaper point's score.
function qualityFrontier(pts) {
  const s = [...pts].sort((a, b) => a.per_task - b.per_task || b.idx - a.idx);
  const f = []; let best = -Infinity;
  for (const p of s) if (p.idx > best) { f.push(p); best = p.idx; }
  return f;
}

// Sliders: score is linear; cost and minutes span orders of magnitude, so they map 0–1000 onto a log range.
const SL = 1000;
const logRange = vals => { const lo = Math.min(...vals), hi = Math.max(...vals); return [lo, hi]; };
const toLog = (v, [lo, hi]) => Math.round(SL * Math.log(v / lo) / Math.log(hi / lo));
const fromLog = (t, [lo, hi]) => lo * Math.pow(hi / lo, t / SL);
const fmtMins = v => v < 10 ? v.toFixed(1) : String(Math.round(v));
function syncSlider() {
  const el = document.getElementById("minScore"), out = document.getElementById("minScoreOut");
  const scores = ALL.map(p => p.idx), lo = Math.floor(Math.min(...scores)), hi = Math.ceil(Math.max(...scores));
  el.min = lo; el.max = hi; el.step = 0.5;
  if (minScore !== null && (minScore < lo || minScore > hi)) minScore = null;
  el.value = minScore === null ? lo : minScore;
  out.textContent = minScore === null || minScore <= lo ? "off" : `≥ ${(+el.value).toFixed(1)}`;

  const cr = logRange(ALL.map(p => p.per_task)), ce = document.getElementById("maxCost");
  ce.min = 0; ce.max = SL; ce.step = 1;
  if (maxCost !== null && (maxCost < cr[0] || maxCost >= cr[1])) maxCost = null;
  ce.value = maxCost === null ? SL : toLog(maxCost, cr);
  document.getElementById("maxCostOut").textContent = maxCost === null ? "off" : `≤ ${usd(maxCost)}`;

  const mr = logRange(ALL.map(p => p.mins)), me = document.getElementById("maxMins");
  me.min = 0; me.max = SL; me.step = 1;
  if (maxMins !== null && (maxMins < mr[0] || maxMins >= mr[1])) maxMins = null;
  me.value = maxMins === null ? SL : toLog(maxMins, mr);
  document.getElementById("maxMinsOut").textContent = maxMins === null ? "off" : `≤ ${fmtMins(maxMins)} min`;

  document.querySelectorAll("#yseg button").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.y === yMode)));
}
const refilter = () => { syncSlider(); drawLegend(); drawChart(); drawRec(); drawTable(); drawWorking(); };
document.getElementById("minScore").addEventListener("input", e => {
  const v = +e.target.value; minScore = v <= +e.target.min ? null : v; refilter();
});
document.getElementById("maxCost").addEventListener("input", e => {
  const t = +e.target.value; maxCost = t >= SL ? null : fromLog(t, logRange(ALL.map(p => p.per_task))); refilter();
});
document.getElementById("maxMins").addEventListener("input", e => {
  const t = +e.target.value; maxMins = t >= SL ? null : fromLog(t, logRange(ALL.map(p => p.mins))); refilter();
});
document.querySelectorAll("#yseg button").forEach(b => b.addEventListener("click", () => {
  yMode = b.dataset.y; store.set("subvalue-y2", yMode); refilter();
}));

function drawChart() {
  const svg = document.getElementById("chart"), kind = scale[1];
  const W = svg.parentElement.clientWidth - 32, H = Math.max(360, Math.min(540, W * 0.68));
  if (!P.length) return emptyChart(svg, W, H);
  svg.setAttribute("width", W); svg.setAttribute("height", H);
  const m = { l: 56, r: 20, t: 22, b: 44 };
  const xAx = axis(kind, P.map(p => p.per_task), m.l, W - m.r);
  let yAx;
  if (yMode === "score") {
    // Score is a bounded index, so it stays linear whichever scale the cost axis uses.
    const sc = P.map(p => p.idx), lo = Math.min(...sc), hi = Math.max(...sc), pad = Math.max(2, (hi - lo) * 0.08);
    const y0 = Math.floor((lo - pad) / 5) * 5, y1 = Math.ceil((hi + pad) / 5) * 5, st = y1 - y0 > 40 ? 10 : 5, ticks = [];
    for (let v = y0; v <= y1; v += st) ticks.push(v);
    yAx = { f: v => H - m.b - (v - y0) / (y1 - y0) * (H - m.t - m.b), ticks };
  } else yAx = axis(kind, P.map(p => p.mins), H - m.b, m.t);
  const fx = p => xAx.f(p.per_task), fy = p => yAx.f(yMode === "score" ? p.idx : p.mins);
  let g = frame(yMode === "score" ? kind : kind, xAx, yAx, m, W, H, `Subscription $ per ${B.task}`,
                yMode === "score" ? B.score : `Minutes per ${B.task}`, true, false);
  if (yMode === "score") g = g.replace(`${esc(B.score)} (${kind})`, esc(B.score));
  g += familyLines(P.filter(p => passes(p) || isFocus(p)), fx, fy, focus);  // connect effort levels that pass the filters (and the highlighted model)
  // Frontier among points that pass the filters. Time: nothing else is both cheaper and faster.
  // Score: nothing cheaper scores higher.
  const fr = (yMode === "score" ? qualityFrontier : frontierOf)(P.filter(passes)), onF = new Set(fr);
  if (fr.length > 1) {
    const byCost = [...fr].sort((a, b) => a.per_task - b.per_task);
    g += `<polyline points="${byCost.map(p => `${fx(p)},${fy(p)}`).join(" ")}" fill="none" stroke="var(--ink)" stroke-opacity="0.09" stroke-width="12" stroke-linejoin="round" stroke-linecap="round"/>`;
  }
  const r = ranked(), best = r.find(p => ELIGIBLE(p.grade));
  let labels = "";
  const rank = p => isFocus(p) ? 3 : (passes(p) ? 1 : 0) + (onF.has(p) || p === best ? 1 : 0);
  for (const p of [...P].sort((a, b) => rank(a) - rank(b))) {
    const x = fx(p), y = fy(p), on = passes(p);
    const cls = focus ? (isFocus(p) ? (on ? " focus" : " focus off-f") : " faint") : (!on ? " off" : (onF.has(p) || p === best ? "" : " dim"));
    g += `<g class="pt${cls}" data-i="${P.indexOf(p)}" transform="translate(${x} ${y})" tabindex="0">
      <circle r="14" fill="transparent"/><g transform="scale(${p === best ? 1.25 : 1})">${badge(p)}</g></g>`;
  }
  // Labels: the pick first, then frontier points, skipping any that would overlap.
  const placed = P.filter(p => focus ? isFocus(p) : passes(p)).map(p => [fx(p) - 13, fy(p) - 13, 26, 26]);  // visible badges are obstacles
  const fits = (x0, y0, w, h) => !placed.some(b => x0 < b[0] + b[2] && b[0] < x0 + w && y0 < b[1] + b[3] && b[1] < y0 + h);
  // While a model is highlighted, label only its effort levels.
  const want = focus ? P.filter(isFocus).sort((a, b) => EFFORT_ORDER.indexOf(b.effort) - EFFORT_ORDER.indexOf(a.effort))
    : [best, ...[...fr].reverse()].filter((p, i, a) => p && a.indexOf(p) === i);
  for (const p of want) {
    const x = fx(p), y = fy(p), w = p.label.length * 6.3 + 6, h = 14;
    const spots = [[x - w / 2, y - R - 22, "middle", x, y - R - 11], [x + 18, y - 7, "start", x + 18, y + 4],
                   [x - 18 - w, y - 7, "end", x - 18, y + 4], [x - w / 2, y + R + 8, "middle", x, y + R + 19]];
    const s = spots.find(([x0, y0]) => x0 > m.l && x0 + w < W - m.r && y0 > 2 && fits(x0, y0, w, h));
    if (!s) continue;
    placed.push([s[0], s[1], w, h]);
    labels += `<text class="lbl${p === best || isFocus(p) ? " win" : ""}" x="${s[3]}" y="${s[4]}" text-anchor="${s[2]}">${esc(p.label)}</text>`;
  }
  svg.innerHTML = g + labels;
  wireTips(svg, document.getElementById("tip"), p => tipHtml(p) + `<div>${!passes(p) ? failReason(p) : onF.has(p) ? (yMode === "score" ? "On the quality frontier: nothing cheaper scores higher" : "On the cost–speed frontier: nothing is both cheaper and faster") : (yMode === "score" ? "Off the frontier: something cheaper scores at least as well" : "Off the frontier: another point is both cheaper and faster")}</div>`);
}

function drawRec() {
  const r = ranked(), eligible = r.filter(p => ELIGIBLE(p.grade)), best = eligible[0];
  const fr = (yMode === "score" ? [...qualityFrontier(P.filter(passes))].reverse() : frontierOf(P.filter(passes)));
  const scope = [filter ? (filter === "go" ? "OpenCode Go" : filter) : "", minScore !== null ? `score ≥ ${minScore.toFixed(1)}` : "", maxCost !== null ? `≤ ${usd(maxCost)}` : "", maxMins !== null ? `≤ ${fmtMins(maxMins)} min` : ""].filter(Boolean).join(" · ");
  let h = `<div class="label">Cheapest measured${scope ? " · " + esc(scope) : ""}</div>`;
  if (best) {
    h += `<div class="pick" style="display:flex;align-items:center;gap:8px">${makerBadge(best.maker)}${esc(best.label)}</div><div class="plan">${esc(best.plan)} · ${gradePill(best.grade)}</div>
      <div class="big">${usd(best.per_task)} <small>per task · score ${best.idx}</small></div>
      <div class="meta">${best.tasks.toLocaleString()} tasks/mo at full cap · ${best.mins} min per task</div>`;
  } else h += `<div class="pick">No measured option${minScore !== null ? " at this score" : ""}</div>`;
  h += `<div class="block"><b>${yMode === "score" ? "Quality frontier" : "Cost–speed frontier"}</b> <span class="meta">(${yMode === "score" ? "highest score first" : "fastest first"}; score, minutes)</span><ol class="rank">${fr.map(p => `<li><span>${esc(p.label)} <span class="meta">(${p.idx}, ${p.mins} min${ELIGIBLE(p.grade) ? "" : ", " + GRADE_TEXT[p.grade]})</span></span><span>${usd(p.per_task)}</span></li>`).join("")}</ol></div>`;
  h += `<div class="block"><b>Measured, cheapest first</b><ol class="rank">${eligible.slice(0, 8).map(p => `<li><span>${esc(p.label)} <span class="meta">(${p.idx})</span></span><span>${usd(p.per_task)}</span></li>`).join("") || "<li><span>None</span></li>"}</ol></div>`;
  h += `<div class="block">${r.length} of ${ALL.length} points pass the filters. Set a minimum score for the work you're routing, then take the cheapest point above it.</div>`;
  document.getElementById("rec").innerHTML = h;
}

function drawTable() {
  const r = ranked(), best = r.find(p => ELIGIBLE(p.grade));
  document.getElementById("tblhead").textContent = `${filter ? (filter === "go" ? "OpenCode Go" : filter) + " points" : "All points"}${minScore !== null || maxCost !== null || maxMins !== null ? " passing the filters" : ""} (${r.length})`;
  document.getElementById("tbl").innerHTML = `<thead><tr><th>Maker</th><th>Model</th><th>Effort</th><th>Plan</th><th>Evidence</th><th class="n">Score</th><th class="n">API $/task</th><th class="n">Tasks/mo</th><th class="n">Sub $/task</th><th class="n">Min/task</th><th>Note</th></tr></thead><tbody>` +
    r.map(p => `<tr class="${p === best ? "win" : ""}${isFocus(p) ? " hl" : ""}"><td style="white-space:nowrap">${pointBadge(p)}</td><td>${esc(p.family)}</td><td>${esc(p.effort)}</td><td>${esc(p.plan)}</td><td>${gradePill(p.grade)}</td><td class="n"><b>${p.idx}</b></td><td class="n">${usd(p.api)}</td><td class="n">${p.tasks.toLocaleString()}</td><td class="n"><b>${usd(p.per_task)}</b></td><td class="n">${p.mins}</td><td class="note">${esc(p.note)}</td></tr>`).join("") + "</tbody>";
}

// Pareto frontier on cost and time: fastest first, keep a point if it is cheaper than every faster point.
function frontierOf(pts) {
  const s = [...pts].sort((a, b) => a.mins - b.mins || a.per_task - b.per_task);
  const f = []; let best = Infinity;
  for (const p of s) if (p.per_task < best) { f.push(p); best = p.per_task; }
  return f;
}
// Plans table
function drawPlans() {
  const icon = { Claude: makerBadge("Claude"), ChatGPT: makerBadge("ChatGPT"), Gemini: makerBadge("Gemini"), Grok: makerBadge("Grok"), Muse: makerBadge("Muse"), "OpenCode Go": goBadge };
  document.getElementById("plans").innerHTML = `<thead><tr><th>Provider</th><th>Plan</th><th class="n">Price/mo (US$)</th><th class="n">Plan capacity/mo (API $)</th><th>Capacity evidence</th><th>Notes</th></tr></thead><tbody>` +
    Object.values(DATA.plans).map(p => `<tr><td style="white-space:nowrap"><span style="display:inline-flex;align-items:center;gap:6px">${icon[p.provider] || ""}${esc(p.provider)}</span></td><td>${esc(p.plan)}</td><td class="n">$${p.price}</td><td class="n">${p.public ? "$" + Math.round(p.public).toLocaleString() : "per model"}</td><td class="note">${p.sources.map(x => esc(x)).join("<br>")} <a href="${esc(p.cap_url)}">Source</a></td><td class="note">${esc(p.alt)}</td></tr>`).join("") + "</tbody>";
}

// Working panel: the tapped point, or the cheapest measured point by default.
let workLabel = params.get("point") || "";
function drawWorking() {
  const el = document.getElementById("working");
  const p = (workLabel && P.find(q => q.label === workLabel)) || ranked().find(q => ELIGIBLE(q.grade)) || ranked()[0];
  if (!p) { el.innerHTML = "<p class='note'>No points match the current filters.</p>"; return; }
  el.innerHTML = `<div class="wtitle">${makerBadge(p.maker)}${esc(p.label)} · ${esc(p.plan)} ${gradePill(p.grade)}</div>
    <table><tbody>${p.working.map(([k, v]) => `<tr><td>${esc(k)}</td><td>${esc(v)}</td></tr>`).join("")}</tbody></table>
    <p class="note" style="margin-top:8px">${esc(p.note)}${workLabel ? "" : " Tap any point to see its working."}</p>`;
}
function renderAll() { syncSlider(); drawLegend(); drawChart(); drawRec(); drawTable(); drawWorking(); }

// Controls: benchmark, scales
document.querySelectorAll("#benchseg button").forEach(b => b.addEventListener("click", () => {
  bench = b.dataset.bench; store.set("subvalue-bench-v3", bench); selectData(); renderAll();
}));
document.querySelectorAll("[data-scale-for]").forEach(grp => {
  const id = grp.dataset.scaleFor;
  const sync = () => grp.querySelectorAll("button").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.scale === scale[id])));
  grp.querySelectorAll("button").forEach(b => b.addEventListener("click", () => {
    scale[id] = b.dataset.scale; store.set("subvalue-scale" + id, scale[id]); sync();
    drawChart();
  }));
  sync();
});

selectData();
renderAll();
drawPlans();
addEventListener("resize", drawChart);
