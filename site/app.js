/* The page's charts, figures and tables, drawn from data.json.

   Nothing is computed here that the report did not already compute: `facsimile site` writes
   data.json from the same records as the README's tables, and this file selects, formats and
   draws. No library, no off-origin request, nothing inline, so the page runs under the content
   security policy in staticwebapp.config.json. */

"use strict";

const SVG = "http://www.w3.org/2000/svg";

const DATASETS = {
  acs: { name: "ACS census, California", short: "ACS", plain: "census" },
  ieeecis: { name: "IEEE-CIS card transactions", short: "IEEE-CIS", plain: "card" },
  sparcs: { name: "NY SPARCS hospital discharges", short: "SPARCS", plain: "hospital" },
};
const ORDER = ["acs", "ieeecis", "sparcs"];

const METHODS = {
  copula: { name: "Gaussian copula", dp: false, cls: "s-copula" },
  ctgan: { name: "CTGAN", dp: false, cls: "s-ctgan" },
  tvae: { name: "TVAE", dp: false, cls: "s-tvae" },
  tabddpm: { name: "TabDDPM", dp: false, cls: "s-ddpm" },
  mst: { name: "MST", dp: true, cls: "s-mst" },
  aim: { name: "AIM", dp: true, cls: "s-aim" },
  pate_ctgan: { name: "PATE-CTGAN", dp: true, cls: "s-pate" },
};
const METHOD_ORDER = ["copula", "ctgan", "tvae", "tabddpm", "mst", "aim", "pate_ctgan"];

/* The leakage ladder: positive controls, never on the surface. */
const LADDER = {
  perturb: { name: "Perturbed copy", cls: "l-perturb", what: "the training records themselves, numbers jittered by a bin and 10% of values swapped, the classic disclosure-control release" },
  smote: { name: "SMOTE-NC", cls: "l-smote", what: "each record interpolated between a real record and one of its five nearest real neighbours, as SMOTE is used for 'synthetic' data" },
  kanon: { name: "k-anonymity, k = 5", cls: "l-kanon", what: "every attribute but the secret generalised until each record matches four others, the secret released as is" },
  tvae_overfit: { name: "TVAE, 3,000 epochs", cls: "l-tvae", what: "the grid's TVAE trained ten times longer than its default, the way a model ends up overfitted" },
};
const LADDER_ORDER = ["perturb", "smote", "kanon", "tvae_overfit"];

const ATTACKS = {
  singling_out_univariate: "Singling out, one attribute",
  singling_out_multivariate: "Singling out, several attributes",
  linkability_k1: "Linkability, 1 neighbour",
  linkability_k10: "Linkability, 10 neighbours",
  inference: "Inference",
};

const TASKS = {
  income: "income above $50,000",
  employment: "employed or not",
  fraud: "fraud or not",
  long_stay: "a stay of more than five days",
  high_charge: "charges of $50,000 or more",
};

const BUDGETS = [0.5, 1, 2, 4, 8, null];

/* ---------------------------------------------------------------- small helpers */

function $(id) {
  return document.getElementById(id);
}

function el(tag, attrs, text) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs || {})) node.setAttribute(key, value);
  if (text !== undefined) node.textContent = text;
  return node;
}

function sv(tag, attrs, text) {
  const node = document.createElementNS(SVG, tag);
  for (const [key, value] of Object.entries(attrs || {})) node.setAttribute(key, value);
  if (text !== undefined) node.textContent = text;
  return node;
}

function svgRoot(width, height, label) {
  return sv("svg", {
    viewBox: `0 0 ${width} ${height}`,
    role: "img",
    "aria-label": label,
    preserveAspectRatio: "xMidYMid meet",
  });
}

function fmt(value, digits) {
  return value.toLocaleString("en-CA", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function signed(value, digits) {
  const text = fmt(Math.abs(value), digits);
  if (Math.abs(value) < 0.5 * Math.pow(10, -digits)) return fmt(0, digits);
  return value < 0 ? `-${text}` : `+${text}`;
}

function pct(value, digits) {
  return `${fmt(100 * value, digits === undefined ? 1 : digits)}%`;
}

function strong(text) {
  return el("strong", {}, text);
}

/* A paragraph assembled from strings and elements, so that bold runs are elements and no
   data ever reaches innerHTML. */
function fill(node, parts) {
  node.textContent = "";
  for (const part of parts) node.append(typeof part === "string" ? document.createTextNode(part) : part);
}

function legend(node, items) {
  node.textContent = "";
  for (const [swatchClass, text, shape] of items) {
    const item = el("span", { class: "legend-item" });
    item.append(el("span", { class: `swatch ${shape || "solid"} ${swatchClass}` }), document.createTextNode(text));
    node.append(item);
  }
}

function epsLabel(eps) {
  return eps === null ? "no privacy" : `epsilon ${eps}`;
}

function config(cell) {
  return `${METHODS[cell.method].name}, ${epsLabel(cell.epsilon)}`;
}

/* Every task within the margin on every seed: the rule's utility half, at any margin. */
function usefulAt(cell, margin) {
  return Object.values(cell.utility).every((u) => u.delta_lo_worst > -margin);
}

function margin() {
  return Number($("surface-margin").value);
}

function cellsOf(data, ds) {
  return data.cells.filter((c) => c.dataset === ds);
}

function scored(cell) {
  return cell.utility && cell.risk;
}

/* The task a cell does worst on: the one the rule judges. */
function worstTask(cell) {
  let worst = null;
  for (const [task, u] of Object.entries(cell.utility)) if (!worst || u.delta < worst.u.delta) worst = { task, u };
  return worst;
}

function taskOf(cell, task) {
  return task === "worst" ? worstTask(cell) : { task, u: cell.utility[task] };
}

function leakOf(data, cell) {
  return data.leaks.filter((l) => l.dataset === cell.dataset && l.method === cell.method && l.epsilon === cell.epsilon);
}

function hardwareShort(text) {
  if (!text) return "";
  if (text.startsWith("AWS")) return "AWS m6a.8xlarge, 32 vCPU";
  if (text.includes("GTX 1650")) return "GTX 1650 GPU";
  if (text.includes("i5-10400F")) return "i5-10400F CPU";
  return text;
}

/* ---------------------------------------------------------------- the first screen */

function hero(data) {
  const attacked = data.cells.filter(scored);
  const tables = attacked.reduce((n, c) => n + c.seeds_attacked.length, 0);
  $("hero-tables").textContent = String(tables);
  $("hero-tables-note").textContent = `${attacked.length} configurations: three datasets, seven synthesisers, privacy levels from epsilon 0.5 to none, each made three times`;

  const leaks = data.leaks;
  $("hero-leaks").textContent = `${leaks.length} of ${attacked.length}`;
  $("hero-leaks-unit").textContent = leaks.length === 1 ? "synthesiser configuration broken by the attacks" : "synthesiser configurations broken by the attacks";
  if (leaks.length) {
    const l = leaks[0];
    const exposed = (data.exposed_leaks || []).filter((x) => METHODS[x.method]).length;
    $("hero-leaks-note").textContent = `${METHODS[l.method].name} at epsilon ${l.epsilon}, with a privacy guarantee, on the ${DATASETS[l.dataset].plain} data: the inference attack, ${pct(l.risk)} excess.${exposed ? ` ${exposed} more on the most unusual people.` : ""}`;
  }

  // The positive controls: what the attacks find on the techniques synthetic data replaces.
  const classical = (data.ladder || []).filter((r) => r.method !== "tvae_overfit" && LADDER[r.method]);
  const broken = classical.filter((r) => Object.values(r.risk).some((v) => v.detected));
  $("hero-ladder").textContent = `${broken.length} of ${classical.length}`;
  const top = (data.ladder_leaks || []).filter((l) => LADDER[l.method] && ATTACKS[l.attack]).sort((a, b) => b.risk - a.risk)[0];
  const overfit = (data.ladder || []).filter((r) => r.method === "tvae_overfit");
  const overfitCaught = overfit.filter((r) => Object.values(r.risk).some((v) => v.detected)).length;
  if (classical.length) {
    $("hero-ladder-note").textContent = `A perturbed copy, SMOTE-NC and k-anonymity, on every dataset${top ? `, with up to ${pct(top.risk)} excess` : ""}. An overfitted TVAE was ${overfitCaught ? `caught on ${overfitCaught} of ${overfit.length}` : "not caught"}.`;
  }

  const useful = attacked.filter((c) => c.passes_utility).length;
  $("hero-useful").textContent = `${useful} of ${attacked.length}`;
  const loose = data.rule.sensitivity_delta_auc;
  if (loose) {
    const looser = attacked.filter((c) => usefulAt(c, loose) && c.passes_risk);
    $("hero-loose").textContent = `${looser.length} of ${attacked.length}`;
    $("hero-loose-unit").textContent = `configuration${looser.length === 1 ? "" : "s"} as useful as the real data, at a looser ${loose}`;
    // One phrase per synthesiser and budget, its datasets in brackets.
    const groups = new Map();
    for (const c of looser) {
      const key = `${METHODS[c.method].name} ${c.epsilon === null ? "without privacy" : `at epsilon ${c.epsilon}`}`;
      groups.set(key, [...(groups.get(key) || []), DATASETS[c.dataset].plain]);
    }
    const named = [...groups].map(([k, ds]) => `${k} (${ds.join(" and ")} data)`).join("; ");
    const dp = looser.filter((c) => c.epsilon !== null).length;
    $("hero-loose-note").textContent = `${looser.length ? `${named}, with no detected risk. ` : ""}${dp ? `${dp} with a privacy guarantee.` : "Nothing with a privacy guarantee."} A what-if, added after the results.`;
  }
}

/* ---------------------------------------------------------------- the surface */

function surfaceControls(data) {
  const dsSelect = $("surface-dataset");
  for (const ds of ORDER) dsSelect.append(el("option", { value: ds }, DATASETS[ds].name));
  const taskSelect = $("surface-task");
  function tasks() {
    taskSelect.textContent = "";
    taskSelect.append(el("option", { value: "worst" }, "The worst task, as the rule judges"));
    const first = cellsOf(data, dsSelect.value).find(scored);
    for (const task of Object.keys(first.utility)) taskSelect.append(el("option", { value: task }, TASKS[task] || task));
  }
  tasks();
  dsSelect.addEventListener("change", () => {
    tasks();
    surface(data);
    fidelity(data);
  });
  taskSelect.addEventListener("change", () => surface(data));
  const slider = $("surface-margin");
  slider.value = String(data.rule.sensitivity_delta_auc ?? 0.05);
  const moved = () => {
    $("surface-margin-value").textContent = margin().toFixed(2);
    surface(data);
  };
  slider.addEventListener("input", moved);
  $("surface-margin-value").textContent = margin().toFixed(2);
}

function surface(data) {
  const ds = $("surface-dataset").value;
  const task = $("surface-task").value;
  const cells = cellsOf(data, ds).filter(scored);
  const W = 760;
  const H = 400;
  const m = { l: 58, r: 18, t: 18, b: 46 };
  const values = cells.map((c) => taskOf(c, task).u);
  // The slider reaches 0.20, so the axis always shows that far down and never jumps as it moves.
  const lowest = Math.min(...values.map((u) => u.delta_lo_worst), -0.2);
  const yMin = Math.floor((lowest - 0.02) * 20) / 20;
  const yMax = 0.03;
  const y = (v) => m.t + ((yMax - v) / (yMax - yMin)) * (H - m.t - m.b);
  const colW = (W - m.l - m.r) / BUDGETS.length;
  const x = (i) => m.l + colW * (i + 0.5);
  // The no-privacy column holds four synthesisers, the budget columns three.
  const offsets = { copula: -21, ctgan: -7, tvae: 7, tabddpm: 21, mst: -14, aim: 0, pate_ctgan: 14 };

  const svg = svgRoot(W, H, `How much usefulness each synthesiser loses on ${DATASETS[ds].name}, by privacy budget`);
  // The margin the reader chose, under the strip the rule accepts, and the zero line: as good as real.
  const chosen = margin();
  svg.append(sv("rect", { class: "zone-soft", x: m.l, y: y(0), width: W - m.l - m.r, height: y(-chosen) - y(0) }));
  svg.append(sv("rect", { class: "zone", x: m.l, y: y(0), width: W - m.l - m.r, height: y(-Math.min(chosen, data.rule.delta_auc)) - y(0) }));
  for (let v = 0; v >= yMin - 1e-9; v -= 0.05) {
    const yy = y(v);
    svg.append(sv("line", { class: v === 0 ? "zero" : "gridline", x1: m.l, x2: W - m.r, y1: yy, y2: yy }));
    svg.append(sv("text", { class: "tick", x: m.l - 8, y: yy + 4, "text-anchor": "end" }, signed(v, 2)));
  }
  svg.append(sv("text", { class: "zone-label", x: m.l + 6, y: y(-data.rule.delta_auc) - 4, "text-anchor": "start" }, "strict standard, 0.02"));
  if (chosen > data.rule.delta_auc + 1e-9) {
    svg.append(sv("line", { class: "margin-line", x1: m.l, x2: W - m.r, y1: y(-chosen), y2: y(-chosen) }));
    svg.append(sv("text", { class: "margin-label", x: m.l + 6, y: y(-chosen) - 4, "text-anchor": "start" }, `your margin, ${chosen.toFixed(2)}`));
  }
  BUDGETS.forEach((b, i) => {
    svg.append(sv("text", { class: "tick", x: x(i), y: H - m.b + 18, "text-anchor": "middle" }, b === null ? "none" : String(b)));
  });
  svg.append(sv("line", { class: "divider", x1: m.l + colW * 5, x2: m.l + colW * 5, y1: m.t, y2: H - m.b }));
  svg.append(sv("text", { class: "axis-title", x: m.l + colW * 2.5, y: H - 8, "text-anchor": "middle" }, "privacy guarantee: epsilon, stronger to the left"));
  svg.append(sv("text", { class: "axis-title", x: m.l + colW * 5.5, y: H - 8, "text-anchor": "middle" }, "no guarantee"));
  svg.append(sv("text", { class: "axis-title", x: 14, y: m.t + (H - m.t - m.b) / 2, transform: `rotate(-90 14 ${m.t + (H - m.t - m.b) / 2})`, "text-anchor": "middle" }, "AUC gap against real data"));

  const readout = $("surface-readout");
  const marks = [];
  for (const method of METHOD_ORDER) {
    const own = cells.filter((c) => c.method === method).sort((a, b) => (a.epsilon ?? 99) - (b.epsilon ?? 99));
    if (!own.length) continue;
    const pts = own.map((c) => ({ c, i: BUDGETS.indexOf(c.epsilon), t: taskOf(c, task) }));
    if (METHODS[method].dp && pts.length > 1) {
      svg.append(sv("polyline", { class: `series ${METHODS[method].cls}`, points: pts.map((p) => `${x(p.i) + offsets[method]},${y(p.t.u.delta)}`).join(" ") }));
    }
    for (const p of pts) {
      const cx = x(p.i) + offsets[method];
      svg.append(sv("line", { class: `whisker ${METHODS[method].cls}`, x1: cx, x2: cx, y1: y(p.t.u.delta_lo_worst), y2: y(p.t.u.delta_hi_best) }));
      if (leakOf(data, p.c).length) svg.append(sv("circle", { class: "leak-ring", cx, cy: y(p.t.u.delta), r: 9 }));
      svg.append(sv("circle", { class: `dot ${METHODS[method].cls}`, cx, cy: y(p.t.u.delta), r: 4.5 }));
      marks.push({ cx, cy: y(p.t.u.delta), p });
    }
  }
  for (const mk of marks) {
    const hit = sv("circle", { class: "catcher", cx: mk.cx, cy: mk.cy, r: 12, fill: "transparent", tabindex: 0 });
    const show = () => {
      const { c, t } = mk.p;
      const detected = Object.entries(c.risk).filter(([, r]) => r.detected).map(([a]) => ATTACKS[a].toLowerCase());
      const leak = leakOf(data, c);
      fill(readout, [
        el("span", { class: "when" }, config(c)),
        el("span", { class: "pair" }, `${signed(t.u.delta, 3)} AUC predicting ${TASKS[t.task] || t.task} (runs range ${signed(t.u.delta_lo_worst, 3)} to ${signed(t.u.delta_hi_best, 3)})`),
        el("span", { class: "pair" }, leak.length ? `Leak: ${leak.map((l) => `${l.attack} ${pct(l.risk)}`).join(", ")}` : detected.length ? `A hint of risk that did not survive the correction for five attacks: ${detected.join(", ")}` : "No attack detected a risk"),
      ]);
    };
    hit.addEventListener("mouseenter", show);
    hit.addEventListener("focus", show);
    svg.append(hit);
  }
  const node = $("surface-chart");
  node.textContent = "";
  node.append(svg);
  readout.textContent = "Point at a dot to read it.";

  legend($("surface-legend"), [
    ...METHOD_ORDER.map((mm) => [`sw-${METHODS[mm].cls}`, `${METHODS[mm].name}${METHODS[mm].dp ? "" : ", no privacy"}`]),
    ["sw-leak", "a named leak", "ring"],
  ]);
  $("surface-caption").textContent = "Each dot is the average of three runs. AIM has no dots at epsilon 4 and 8: one table ran for more than 28 hours and used up to 53 GB of memory without finishing, and at epsilon 2 it was already far below the bar (see What this page does not show, at the end). Each vertical line runs from the lowest run's 95% lower bound to the highest run's upper bound. Usefulness: the same LightGBM model is trained once on the synthetic table and once on the real one, both are tested on real people neither has seen, and the real-trained score is subtracted from the synthetic-trained one.";

  const best = cells.reduce((a, c) => (worstTask(c).u.delta > worstTask(a).u.delta ? c : a));
  const dp = cells.filter((c) => c.epsilon !== null);
  const bestDp = dp.reduce((a, c) => (worstTask(c).u.delta > worstTask(a).u.delta ? c : a));
  const plain = (c) => `${METHODS[c.method].name} ${c.epsilon === null ? "without privacy" : `at epsilon ${c.epsilon}`}`;
  fill($("surface-verdict"), [
    strong(`On the ${DATASETS[ds].plain} data, nothing meets the strict 0.02 standard. `),
    `The closest is ${plain(best)}, ${signed(worstTask(best).u.delta, 3)} AUC on its worst task. The closest with a privacy guarantee is ${plain(bestDp)}, at ${signed(worstTask(bestDp).u.delta, 3)}. `,
    mstSpan(cells),
  ]);
  marginVerdict(data, ds, cells);
}

/* What a looser (or tighter) margin buys: a sensitivity line, never the rule. */
function marginVerdict(data, ds, cells) {
  const chosen = margin();
  const label = chosen.toFixed(2);
  const all = data.cells.filter(scored);
  const useful = cells.filter((c) => usefulAt(c, chosen));
  const clean = useful.filter((c) => c.passes_risk);
  const allUseful = all.filter((c) => usefulAt(c, chosen));
  const allClean = allUseful.filter((c) => c.passes_risk);
  const private_ = allClean.filter((c) => c.epsilon !== null).length;
  const named = (c) => `${METHODS[c.method].name} ${c.epsilon === null ? "without privacy" : `at epsilon ${c.epsilon}`}`;
  const list = (xs) => (xs.length < 3 ? xs.join(" and ") : `${xs.slice(0, -1).join(", ")} and ${xs[xs.length - 1]}`);
  const risk = clean.length === useful.length
    ? "with no risk detected"
    : `though only ${clean.length} of ${useful.length} ${clean.length === 1 ? "has" : "have"} no risk detected`;
  const here = useful.length
    ? `On the ${DATASETS[ds].plain} data, ${list(useful.map(named))} ${useful.length === 1 ? "makes" : "make"} the cut on every task and every run, ${risk}. `
    : `On the ${DATASETS[ds].plain} data, nothing makes the cut on every task and every run. `;
  fill($("surface-margin-verdict"), [
    strong(`With a loss of up to ${label} accepted: `),
    here,
    `Across all three datasets, ${allClean.length} of ${all.length} configurations would pass, ${private_ ? `${private_} of them with a privacy guarantee` : "none of them with a privacy guarantee"}. `,
    Math.abs(chosen - data.rule.delta_auc) > 1e-9 ? `This is a what-if, added after the results were in. The strict ${data.rule.delta_auc} stays the recommendation.` : "This is the strict standard itself.",
  ]);
}

/* How much MST, the steadiest of the private methods, moves between epsilon 2 and 8. */
function mstSpan(cells) {
  const at = (eps) => cells.find((c) => c.method === "mst" && c.epsilon === eps);
  const two = at(2);
  const eight = at(8);
  if (!two || !eight) return "";
  const moved = worstTask(eight).u.delta - worstTask(two).u.delta;
  return `More privacy budget buys less than you might hope: giving MST four times as much, epsilon 8 instead of 2, moves it by only ${signed(moved, 3)} AUC on its worst task.`;
}

function fidelity(data) {
  const ds = $("surface-dataset").value;
  const cells = cellsOf(data, ds).filter(scored);
  const W = 760;
  const H = 340;
  const m = { l: 58, r: 18, t: 16, b: 46 };
  const xs = cells.map((c) => c.marginal_error["2way"]);
  const ys = cells.map((c) => worstTask(c).u.delta);
  const xMax = Math.ceil(Math.max(...xs) * 10 + 0.5) / 10;
  const yMin = Math.floor((Math.min(...ys) - 0.03) * 20) / 20;
  const x = (v) => m.l + (v / xMax) * (W - m.l - m.r);
  const y = (v) => m.t + ((0.02 - v) / (0.02 - yMin)) * (H - m.t - m.b);
  const svg = svgRoot(W, H, "Marginal error against usefulness, one mark per configuration");
  for (let v = 0; v <= xMax + 1e-9; v += 0.1) {
    svg.append(sv("line", { class: "gridline", x1: x(v), x2: x(v), y1: m.t, y2: H - m.b }));
    svg.append(sv("text", { class: "tick", x: x(v), y: H - m.b + 16, "text-anchor": "middle" }, fmt(v, 1)));
  }
  for (let v = 0; v >= yMin - 1e-9; v -= 0.1) {
    svg.append(sv("line", { class: v === 0 ? "zero" : "gridline", x1: m.l, x2: W - m.r, y1: y(v), y2: y(v) }));
    svg.append(sv("text", { class: "tick", x: m.l - 8, y: y(v) + 4, "text-anchor": "end" }, signed(v, 1)));
  }
  svg.append(sv("text", { class: "axis-title", x: m.l + (W - m.l - m.r) / 2, y: H - 8, "text-anchor": "middle" }, "two-way marginal error: lower looks more like the data"));
  svg.append(sv("text", { class: "axis-title", x: 14, y: m.t + (H - m.t - m.b) / 2, transform: `rotate(-90 14 ${m.t + (H - m.t - m.b) / 2})`, "text-anchor": "middle" }, "worst-task AUC versus real"));
  const readout = $("fidelity-readout");
  for (const c of cells) {
    const dot = sv("circle", { class: `dot ${METHODS[c.method].cls}`, cx: x(c.marginal_error["2way"]), cy: y(worstTask(c).u.delta), r: 5, tabindex: 0 });
    const show = () => fill(readout, [el("span", { class: "when" }, config(c)), el("span", { class: "pair" }, `marginal error ${fmt(c.marginal_error["2way"], 3)}, usefulness ${signed(worstTask(c).u.delta, 3)} AUC`)]);
    dot.addEventListener("mouseenter", show);
    dot.addEventListener("focus", show);
    svg.append(dot);
  }
  const node = $("fidelity-chart");
  node.textContent = "";
  node.append(svg);
  readout.textContent = "Point at a dot to read it.";

  const byError = [...cells].sort((a, b) => a.marginal_error["2way"] - b.marginal_error["2way"]);
  const byUse = [...cells].sort((a, b) => worstTask(b).u.delta - worstTask(a).u.delta);
  const copula = cells.find((c) => c.method === "copula");
  fill($("fidelity-lead"), [
    "Synthetic-data tools usually report fidelity: how closely the copy reproduces the real data's counts. The two-way marginal error below is one such score, and lower looks more like the real data. ",
    strong(`On ${DATASETS[ds].short}, the Gaussian copula is number ${byError.indexOf(copula) + 1} of ${cells.length} for fidelity and number ${byUse.indexOf(copula) + 1} for usefulness`),
    `, at ${signed(worstTask(copula).u.delta, 3)} AUC. The most useful table, ${config(byUse[0])}, is number ${byError.indexOf(byUse[0]) + 1} for fidelity. Looking like the data and being useful are different things, so this project reports fidelity only as fidelity.`,
  ]);
  $("fidelity-caption").textContent = "Two-way marginal error: the mean total-variation distance between real and synthetic counts over sampled pairs of columns. Usefulness as in the chart above.";
}

/* ---------------------------------------------------------------- the leak */

/* What each attack's success rate counts, for the leak card's captions. */
const LEAK_WORDS = {
  inference: {
    how: "guessing a person's income bracket from their other attributes",
    main: "of the people the synthesiser was trained on had their income bracket guessed right",
    control: "of people it never saw, with the same attack on the same table",
  },
  singling_out_multivariate: {
    how: "combinations of attributes read off the table, each meant to fit exactly one person",
    main: "of those combinations picked out exactly one of the people the synthesiser was trained on",
    control: "picked out exactly one of the people it never saw",
  },
};

function leak(data) {
  const card = $("leak-card");
  card.textContent = "";
  const leaks = data.leaks.filter((l) => ATTACKS[l.attack] && METHODS[l.method]);
  if (!leaks.length) {
    card.append(el("p", {}, "No attack detected a risk on any configuration."));
    return;
  }
  const at = (l) => (l.epsilon === null ? "no privacy" : `epsilon ${l.epsilon}`);
  for (const l of leaks) {
    const words = LEAK_WORDS[l.attack] || {
      how: ATTACKS[l.attack].toLowerCase(),
      main: "success on the people the synthesiser was trained on",
      control: "success on people it never saw",
    };
    const head = el("div", { class: "leak-head" });
    head.append(el("span", { class: "eyebrow" }, leaks.length === 1 ? "The one leak" : "A leak"), el("h3", {}, `${METHODS[l.method].name} at ${at(l)}, ${DATASETS[l.dataset].name}`));
    head.append(el("p", { class: "note" }, `${l.library} ${l.version}, 20,000 rows, ${l.seeds} seeds pooled. The attack: ${ATTACKS[l.attack].toLowerCase()}, ${words.how}.`));
    const stats = el("div", { class: "headline" });
    const stat = (figure, caption, cls, range) => {
      const s = el("div", { class: `stat ${cls || ""}` });
      s.append(el("span", { class: "figure" }, figure), el("span", { class: "caption" }, caption));
      if (range) s.append(el("span", { class: "range" }, range));
      return s;
    };
    stats.append(
      stat(pct(l.main_rate), words.main),
      stat(pct(l.control_rate), words.control),
      stat(pct(l.risk), "excess: what the table gives away about the people in it", "down", `95% interval ${pct(l.lo)} to ${pct(l.hi)}`),
    );
    card.append(head, stats);
    const ref = l.reference;
    if (ref) {
      card.append(el("p", { class: "note" }, ref.detected
        ? `Anonymeter, the reference library, on the same tables and pooled the same way: ${pct(ref.value)}, 95% interval ${pct(ref.lo)} to ${pct(ref.hi)}, detected at the corrected level too.`
        : `Not reproduced by Anonymeter, the reference library: on the same tables, pooled the same way, it puts the excess at ${pct(ref.value)}, 95% interval ${pct(ref.lo)} to ${pct(ref.hi)}, not detected at the corrected level. The leak is this project's measurement, shown with that caveat.`));
    }
  }
  const dcrOf = (l) => {
    const cell = data.cells.find((c) => c.dataset === l.dataset && c.method === l.method && c.epsilon === l.epsilon);
    return cell && cell.dcr ? cell.dcr.closer_to_training_share : null;
  };
  const verdict = [];
  for (const l of leaks.filter((x) => x.epsilon !== null)) {
    const dcr = dcrOf(l);
    verdict.push(
      strong("Differential privacy limits a leak. It does not promise there is none. "),
      `At epsilon ${l.epsilon} the guarantee still lets one person's presence nudge what the table says, and here the nudge was measurable. It is small. The attack guesses right for ${pct(l.control_rate)} of strangers anyway, because the table is useful, and does only ${fmt(100 * (l.main_rate - l.control_rate), 1)} percentage points better on the people it was trained on. `,
      dcr !== null ? `The usual distance check gives it a reassuring ${fmt(dcr, 3)}, as a later section shows. ` : "",
    );
  }
  for (const l of leaks.filter((x) => x.epsilon === null)) {
    const dcr = dcrOf(l);
    verdict.push(
      strong(`${METHODS[l.method].name} has no guarantee, and here it shows. `),
      `It is the synthesiser whose tables come nearest the real data for training models, and the one configuration without privacy that an attack breaks on all its targets: ${ATTACKS[l.attack].toLowerCase()}, ${fmt(100 * (l.main_rate - l.control_rate), 1)} percentage points more often on the people it was trained on than on strangers. `,
      dcr !== null ? `Distance to closest record passes it too, at ${fmt(dcr, 3)}. ` : "",
    );
  }
  verdict.push(...data.membershipFm.map((m) => ` A second membership attacker flags it too. With Google's TabFM foundation model in place of the usual random forest, at about 1,000 rows, it tells whether a person was in the training data ${pct(m.risk)} of the time, against a coin's 50% (95% interval ${pct(m.lo)} to ${pct(m.hi)}), where the forest saw nothing.`));
  fill($("leak-verdict"), verdict);
}

/* ---------------------------------------------------------------- the leakage ladder */

function ladderControls(data) {
  const select = $("ladder-dataset");
  for (const ds of ORDER) select.append(el("option", { value: ds }, DATASETS[ds].name));
  select.addEventListener("change", () => ladder(data));
}

function ladder(data) {
  const rows = data.ladder || [];
  const ds = $("ladder-dataset").value;
  const own = LADDER_ORDER.map((m) => rows.find((r) => r.dataset === ds && r.method === m)).filter((r) => r && r.risk);
  const grid = cellsOf(data, ds).filter(scored);
  const attacks = Object.keys(ATTACKS);
  const W = 760;
  const rowH = 58;
  const m = { l: 210, r: 18, t: 10, b: 40 };
  const H = m.t + rowH * attacks.length + m.b;
  const highest = Math.max(0.05, ...own.flatMap((r) => attacks.map((a) => r.risk[a].hi)));
  const xMax = Math.ceil(highest * 20) / 20;
  const x = (v) => m.l + (v / xMax) * (W - m.l - m.r);
  const svg = svgRoot(W, H, `Risk on each attack for the four leaky methods on ${DATASETS[ds].name}, beside the largest risk any grid synthesiser showed`);
  const step = xMax > 0.4 ? 0.1 : 0.05;
  for (let v = 0; v <= xMax + 1e-9; v += step) {
    svg.append(sv("line", { class: v === 0 ? "zero" : "gridline", x1: x(v), x2: x(v), y1: m.t, y2: H - m.b }));
    svg.append(sv("text", { class: "tick", x: x(v), y: H - m.b + 16, "text-anchor": "middle" }, `${fmt(100 * v, 0)}%`));
  }
  svg.append(sv("text", { class: "axis-title", x: m.l + (W - m.l - m.r) / 2, y: H - 6, "text-anchor": "middle" }, "risk: excess success on training records over control"));
  const readout = $("ladder-readout");
  attacks.forEach((a, i) => {
    const top = m.t + i * rowH;
    const mid = top + rowH / 2;
    svg.append(sv("text", { class: "row-label", x: 8, y: mid + 4 }, ATTACKS[a]));
    const gridMax = Math.max(0, ...grid.map((c) => c.risk[a].value));
    svg.append(sv("line", { class: "grid-max", x1: x(gridMax), x2: x(gridMax), y1: top + 8, y2: top + rowH - 8 }));
    own.forEach((r, k) => {
      const risk = r.risk[a];
      const cy = top + 12 + k * ((rowH - 24) / Math.max(own.length - 1, 1));
      svg.append(sv("line", { class: `whisker ${LADDER[r.method].cls}`, x1: x(risk.lo), x2: x(risk.hi), y1: cy, y2: cy }));
      const dot = sv("circle", { class: `dot ${LADDER[r.method].cls}${risk.detected ? "" : " hollow"}`, cx: x(risk.value), cy, r: 5, tabindex: 0 });
      const show = () => fill(readout, [
        el("span", { class: "when" }, `${LADDER[r.method].name}, ${ATTACKS[a].toLowerCase()}`),
        el("span", { class: "pair" }, `risk ${pct(risk.value)} (${pct(risk.lo)} to ${pct(risk.hi)}), ${pct(risk.main_rate)} of training records against ${pct(risk.control_rate)} of control`),
        el("span", { class: "pair" }, risk.detected ? "detected" : "not detected"),
      ]);
      dot.addEventListener("mouseenter", show);
      dot.addEventListener("focus", show);
      svg.append(dot);
    });
  });
  const node = $("ladder-chart");
  node.textContent = "";
  node.append(svg);
  readout.textContent = own.length ? "Point at a dot to read it." : "The ladder's tables are still being attacked.";
  legend($("ladder-legend"), [
    ...LADDER_ORDER.map((mm) => [`sw-${LADDER[mm].cls}`, LADDER[mm].name, "dot"]),
    ["sw-grid-max", "largest risk among the seven synthesisers", "solid"],
  ]);
  $("ladder-caption").textContent = "Risks pooled over three runs, 6,000 attack attempts each, with 95% intervals. A filled dot is a detected risk, at the same corrected bar the leak section uses; a hollow one is not.";

  const cards = $("ladder-cards");
  cards.textContent = "";
  for (const mm of LADDER_ORDER) {
    const r = own.find((x) => x.method === mm);
    const card = el("article", { class: "guide-card" });
    const found = r ? Object.entries(r.risk).filter(([, v]) => v.detected).map(([a]) => ATTACKS[a].toLowerCase()) : [];
    if (r && r.membership && r.membership.detected) found.push("membership inference");
    const gap = r && r.utility ? worstTask(r).u.delta : null;
    const unusual = r && r.risk_exposed ? Object.entries(r.risk_exposed).filter(([a, v]) => v.detected && !r.risk[a].detected).map(([a]) => ATTACKS[a].toLowerCase()) : [];
    card.append(
      el("h3", {}, LADDER[mm].name),
      el("p", {}, LADDER[mm].what + "."),
      el("p", { class: "card-result" }, r ? `${found.length ? `Caught by ${found.join(", ")}` : "Caught by no attack"}${unusual.length ? `; on its most unusual records, by ${unusual.join(", ")}` : ""}${gap !== null ? `; usefulness ${signed(gap, 3)} AUC` : ""}.` : "Still being attacked."),
    );
    cards.append(card);
  }

  const all = rows.filter((r) => r.risk);
  const caught = all.filter((r) => Object.values(r.risk).some((v) => v.detected));
  fill($("ladder-verdict"), all.length ? [
    strong(`The attacks caught ${caught.length} of the ${all.length} leaky tables they were given. `),
    ...(() => {
      const missed = [...new Set(all.filter((r) => !caught.includes(r)).map((r) => LADDER[r.method].name))];
      return missed.length ? [`The ones they missed are ${missed.join(", ")}: trained ten times longer on 20,000 records, it showed no measurable memorisation, which the plan had allowed for. `] : [];
    })(),
    "On the same attacks the seven synthesisers sit near zero, apart from the leak above. So a clean result for a synthesiser means the attacks found nothing they would have found in tables like these. It does not mean the attacks were too weak to find anything.",
  ] : ["The ladder's tables are still being attacked."]);

  const exposed = (data.exposed_leaks || []).filter((l) => METHODS[l.method]);
  const gridExposed = data.cells.filter((c) => c.risk_exposed);
  fill($("exposed-note"), gridExposed.length ? [
    strong("And the most unusual people? "),
    `They are the easiest to pick out, so every synthesiser's table was attacked again on the most unusual quarter of its targets, against the most unusual quarter of the control group. ${exposed.length ? `That found ${exposed.length} more detected risk${exposed.length === 1 ? "" : "s"}: ${exposed.map((l) => `${METHODS[l.method].name} at ${epsLabel(l.epsilon)} on ${DATASETS[l.dataset].short}, ${ATTACKS[l.attack].toLowerCase()}, ${pct(l.risk)}`).join("; ")}.` : `Across ${gridExposed.length} configurations it found no risk that the full set of targets had not already shown.`}`,
  ] : ["The attacks on the most exposed records are still running."]);
}

/* ---------------------------------------------------------------- distance to closest record */

function dcrChart(data) {
  const cells = data.cells.filter(scored).filter((c) => c.dcr);
  const W = 760;
  const rowH = 74;
  const m = { l: 92, r: 18, t: 14, b: 40 };
  const H = m.t + rowH * ORDER.length + m.b;
  const shares = cells.map((c) => c.dcr.closer_to_training_share);
  const lo = Math.floor(Math.min(...shares, 0.47) * 50) / 50;
  const hi = Math.ceil(Math.max(...shares, 0.53) * 50) / 50;
  const x = (v) => m.l + ((v - lo) / (hi - lo)) * (W - m.l - m.r);
  const svg = svgRoot(W, H, "Distance to closest record for every configuration, with the configurations it flags and the one that leaked");
  for (let v = lo; v <= hi + 1e-9; v += 0.02) {
    svg.append(sv("line", { class: Math.abs(v - 0.5) < 1e-9 ? "zero" : "gridline", x1: x(v), x2: x(v), y1: m.t, y2: H - m.b }));
    svg.append(sv("text", { class: "tick", x: x(v), y: H - m.b + 16, "text-anchor": "middle" }, fmt(v, 2)));
  }
  svg.append(sv("text", { class: "axis-title", x: m.l + (W - m.l - m.r) / 2, y: H - 6, "text-anchor": "middle" }, "share of synthetic records closer to a training record than to a control"));
  const readout = $("dcr-readout");
  ORDER.forEach((ds, r) => {
    const top = m.t + r * rowH;
    const mid = top + rowH / 2;
    const nulls = (data.dcr_null || {})[ds] || [];
    if (nulls.length) svg.append(sv("rect", { class: "null-band", x: x(Math.min(...nulls)), width: Math.max(2, x(Math.max(...nulls)) - x(Math.min(...nulls))), y: top + 8, height: rowH - 16, rx: 3 }));
    svg.append(sv("text", { class: "row-label", x: 8, y: mid + 4 }, DATASETS[ds].short));
    const own = cells.filter((c) => c.dataset === ds).sort((a, b) => a.dcr.closer_to_training_share - b.dcr.closer_to_training_share);
    own.forEach((c, k) => {
      const flagged = c.dcr.closer_lo_min > 0.5;
      const leaked = leakOf(data, c).length > 0;
      const cy = mid + ((k % 3) - 1) * 12;
      const dot = sv("circle", { class: `dcr-dot ${leaked ? "leaked" : flagged ? "flagged" : ""}`, cx: x(c.dcr.closer_to_training_share), cy, r: leaked ? 7 : 5, tabindex: 0 });
      const show = () => fill(readout, [
        el("span", { class: "when" }, `${DATASETS[ds].short}, ${config(c)}`),
        el("span", { class: "pair" }, `share ${fmt(c.dcr.closer_to_training_share, 3)}, lowest seed's lower bound ${fmt(c.dcr.closer_lo_min, 3)}`),
        el("span", { class: "pair" }, `${flagged ? "DCR says unsafe" : "DCR says fine"}; ${leaked ? "an attack detected a leak" : "no attack detected a risk"}`),
      ]);
      dot.addEventListener("mouseenter", show);
      dot.addEventListener("focus", show);
      svg.append(dot);
    });
  });
  const node = $("dcr-chart");
  node.textContent = "";
  node.append(svg);
  readout.textContent = "Point at a dot to read it.";
  legend($("dcr-legend"), [
    ["sw-flagged", "DCR flags it: every seed's interval above one half", "dot"],
    ["sw-leaked", "the one an attack broke", "dot"],
    ["sw-faint", "neither", "dot"],
    ["sw-null", "real records the synthesiser never saw", "block"],
  ]);
  $("dcr-caption").textContent = "4,000 synthetic records per table, against 2,000 training records and 2,000 control records, with ties split evenly. A table that knows nothing about the people it trained on scores one half.";
  const flagged = cells.filter((c) => c.dcr.closer_lo_min > 0.5);
  const dpFlagged = flagged.filter((c) => c.epsilon !== null);
  const leaked = cells.filter((c) => leakOf(data, c).length);
  fill($("dcr-verdict"), [
    strong(`It got it wrong both ways. `),
    `It flagged ${flagged.length} configurations that no attack could break, ${dpFlagged.length} of them with a privacy guarantee, and it passed ${leaked.length === 1 ? "the one" : "every one"} an attack did break. `,
    "A release gate built on this check would have blocked every MST table on the card data and let through the table the inference attack breaks. This project keeps the number in its tables, labelled for what it is, and never calls it privacy.",
  ]);
}

/* ---------------------------------------------------------------- the gate */

function gate(data) {
  const g = data.gate;
  if (!g || !g.runs) return;
  const groups = [];
  for (const ds of ORDER) {
    const runs = g.runs.filter((r) => r.dataset === ds);
    const open = (k) => (k.endsWith("|null") ? 0 : 1);
    const keys = [...new Set(runs.map((r) => `${r.method}|${r.epsilon}`))].sort((a, b) => open(a) - open(b));
    for (const key of keys) {
      const own = runs.filter((r) => `${r.method}|${r.epsilon}` === key);
      const worst = own.map((r) => r.suites.reduce((a, s) => (s.difference < a.difference ? s : a)));
      groups.push({
        ds,
        run: own[0],
        mean: (100 * worst.reduce((a, s) => a + s.difference, 0)) / worst.length,
        lo: 100 * Math.min(...worst.map((s) => s.lo)),
        hi: 100 * Math.max(...worst.map((s) => s.hi)),
        outcomes: [...new Set(own.map((r) => r.outcome))],
        seeds: own.length,
        items: worst[0].paired_items,
        needed: worst[0].items_needed,
      });
    }
  }
  const W = 760;
  const rowH = 38;
  const m = { l: 250, r: 120, t: 12, b: 40 };
  const H = m.t + rowH * groups.length + m.b;
  const xMin = Math.floor(Math.min(...groups.map((gr) => gr.lo)) / 5) * 5;
  const x = (v) => m.l + ((v - xMin) / (2 - xMin)) * (W - m.l - m.r);
  const svg = svgRoot(W, H, "The release gate's verdict on the nearest configurations");
  for (let v = xMin; v <= 0; v += 5) {
    svg.append(sv("line", { class: v === 0 ? "zero" : "gridline", x1: x(v), x2: x(v), y1: m.t, y2: H - m.b }));
    svg.append(sv("text", { class: "tick", x: x(v), y: H - m.b + 16, "text-anchor": "middle" }, v === 0 ? "0" : String(v)));
  }
  svg.append(sv("line", { class: "budget", x1: x(-g.delta_points), x2: x(-g.delta_points), y1: m.t, y2: H - m.b }));
  svg.append(sv("text", { class: "budget-label", x: x(-g.delta_points) - 4, y: H - m.b - 4, "text-anchor": "end" }, `margin -${g.delta_points}`));
  svg.append(sv("text", { class: "axis-title", x: m.l + (W - m.l - m.r) / 2, y: H - 6, "text-anchor": "middle" }, "worst-task AUC points, synthetic-trained minus real-trained"));
  groups.forEach((gr, i) => {
    const mid = m.t + i * rowH + rowH / 2;
    const dp = gr.run.epsilon !== null;
    svg.append(sv("text", { class: "row-label", x: 8, y: mid - 2 }, DATASETS[gr.ds].short));
    svg.append(sv("text", { class: "row-note", x: 8, y: mid + 12 }, config(gr.run)));
    svg.append(sv("rect", { class: `bar ${dp ? "gate-dp" : "gate-open"}`, x: x(gr.mean), y: mid - 9, width: x(0) - x(gr.mean), height: 18, rx: 2 }));
    svg.append(sv("line", { class: "whisker", x1: x(gr.lo), x2: x(gr.hi), y1: mid, y2: mid }));
    svg.append(sv("line", { class: "whisker", x1: x(gr.lo), x2: x(gr.lo), y1: mid - 5, y2: mid + 5 }));
    svg.append(sv("line", { class: "whisker", x1: x(gr.hi), x2: x(gr.hi), y1: mid - 5, y2: mid + 5 }));
    const verdict = gr.outcomes.length === 1 ? `${gr.outcomes[0]}, ${gr.seeds} of ${gr.seeds}` : gr.outcomes.join(" / ");
    svg.append(sv("text", { class: `verdict-label ${gr.outcomes.includes("block") ? "blocked" : "undecided"}`, x: W - m.r + 10, y: mid + 4 }, verdict));
  });
  const node = $("gate-chart");
  node.textContent = "";
  node.append(svg);
  legend($("gate-legend"), [
    ["sw-gate-open", "nearest of all seven, no privacy guarantee"],
    ["sw-gate-dp", "nearest with differential privacy"],
  ]);
  $("gate-caption").textContent = "An item is a pair of real test records, one positive and one negative, never reused; it is correct when the model scores the positive one higher, so the share correct estimates the AUC. Paired bootstrap, 2,000 resamples, Holm's adjustment across a dataset's tasks.";
  const open = groups.filter((gr) => gr.run.epsilon === null);
  const dps = groups.filter((gr) => gr.run.epsilon !== null);
  const rangeText = (gs) => `${fmt(Math.min(...gs.map((gr) => -gr.mean)), 1)} to ${fmt(Math.max(...gs.map((gr) => -gr.mean)), 1)}`;
  fill($("gate-verdict"), [
    strong("No synthetic table here is as good as the real data for training these models. "),
    `The best synthesiser without privacy leaves a model ${rangeText(open)} AUC points worse on its worst task, and the best with a privacy guarantee ${rangeText(dps)} points worse. On the census and hospital data the gate blocks every candidate on every run.`,
  ]);
  const undecided = groups.find((gr) => gr.outcomes.includes("not decided"));
  if (undecided) {
    fill($("gate-assumption"), [
      strong("Why the card data is not decided. "),
      `Its test set has only ${undecided.items} fraud cases, and the gate wants at least ${undecided.needed} before it will settle a question as fine as 2 points. So it declines rather than guess. This project reports that as not decided, never as a pass, even though every interval on the card data sits entirely below the margin.`,
    ]);
  }
}

/* ---------------------------------------------------------------- membership */

function membership(data) {
  const rows = [];
  for (const ds of ORDER) {
    const copy = data.groundhog_reference.find((r) => r.dataset === ds && r.method === "copy");
    if (copy) rows.push({ ds, label: "copy of the training data (control)", acc: copy.ours.point, lo: copy.ours.lo, hi: copy.ours.hi, copy: true });
    for (const c of cellsOf(data, ds).filter((c) => c.membership)) {
      rows.push({ ds, label: config(c), acc: c.membership.accuracy, lo: c.membership.lo, hi: c.membership.hi, method: c.method });
    }
  }
  const W = 760;
  const rowH = 19;
  const m = { l: 250, r: 18, t: 24, b: 40 };
  const gap = 12;
  const H = m.t + rows.length * rowH + gap * (ORDER.length - 1) + m.b;
  const x = (v) => m.l + ((v - 0.2) / 0.6) * (W - m.l - m.r);
  const svg = svgRoot(W, H, "Membership inference accuracy for every configuration measured, with the copied-data control");
  for (let v = 0.2; v <= 0.8 + 1e-9; v += 0.1) {
    svg.append(sv("line", { class: Math.abs(v - 0.5) < 1e-9 ? "zero" : "gridline", x1: x(v), x2: x(v), y1: m.t, y2: H - m.b }));
    svg.append(sv("text", { class: "tick", x: x(v), y: H - m.b + 16, "text-anchor": "middle" }, fmt(v, 1)));
  }
  svg.append(sv("text", { class: "zero-label", x: x(0.5), y: m.t - 8, "text-anchor": "middle" }, "chance"));
  svg.append(sv("text", { class: "axis-title", x: m.l + (W - m.l - m.r) / 2, y: H - 6, "text-anchor": "middle" }, "accuracy telling members from non-members"));
  const readout = $("membership-readout");
  let yy = m.t;
  let last = null;
  for (const r of rows) {
    if (last && r.ds !== last) yy += gap;
    const mid = yy + rowH / 2;
    if (r.ds !== last) svg.append(sv("text", { class: "row-label", x: 8, y: mid + 4 }, DATASETS[r.ds].short));
    svg.append(sv("text", { class: "row-note", x: m.l - 10, y: mid + 4, "text-anchor": "end" }, r.label));
    svg.append(sv("line", { class: "whisker", x1: x(r.lo), x2: x(r.hi), y1: mid, y2: mid }));
    const dot = sv("circle", { class: r.copy ? "dot copy-dot" : `dot ${METHODS[r.method].cls}`, cx: x(r.acc), cy: mid, r: r.copy ? 5 : 4, tabindex: 0 });
    const show = () => fill(readout, [el("span", { class: "when" }, `${DATASETS[r.ds].short}, ${r.label}`), el("span", { class: "pair" }, `accuracy ${fmt(r.acc, 3)} (${fmt(r.lo, 3)} to ${fmt(r.hi, 3)})`)]);
    dot.addEventListener("mouseenter", show);
    dot.addEventListener("focus", show);
    svg.append(dot);
    last = r.ds;
    yy += rowH;
  }
  const node = $("membership-chart");
  node.textContent = "";
  node.append(svg);
  readout.textContent = "Point at a dot to read it.";
  $("membership-caption").textContent = "Six target people per dataset, 40 practice tables and 20 test tables each: 120 trials per configuration, with exact (Clopper-Pearson) 95% intervals. The copy control is a 'synthesiser' that simply hands back its training data.";

  const copies = data.groundhog_reference.filter((r) => r.method === "copy");
  const pooled = (k) => {
    const correct = copies.reduce((a, r) => a + Math.round(r[k].point * r[k].n), 0);
    const trials = copies.reduce((a, r) => a + r[k].n, 0);
    return { correct, trials };
  };
  const ours = pooled("ours");
  const tapas = pooled("tapas");
  const head = $("membership-headline");
  head.textContent = "";
  const stat = (figure, caption, range) => {
    const s = el("div", { class: "stat" });
    s.append(el("span", { class: "figure" }, figure), el("span", { class: "caption" }, caption));
    if (range) s.append(el("span", { class: "range" }, range));
    return s;
  };
  const inChance = data.cells.filter((c) => c.membership).filter((c) => c.membership.lo <= 0.5 && c.membership.hi >= 0.5);
  head.append(
    stat(`${inChance.length} of ${data.cells.filter((c) => c.membership).length}`, "configurations whose interval includes chance"),
    stat(fmt(ours.correct / ours.trials, 3), "this project's attack on a copy of the training data", `${ours.correct} of ${ours.trials} right, three datasets`),
    stat(fmt(tapas.correct / tapas.trials, 3), "the reference library, TAPAS, on the same tables", `${tapas.correct} of ${tapas.trials} right`),
  );
  fill($("membership-verdict"), [
    strong("The paper's attack is at chance everywhere, and that says less than it seems. "),
    "Even when the 'synthetic' table is the training data itself, the attack is right only a little more than half the time at this scale, in this project's version and in the authors' library alike. So a result at chance here means the attack could not tell, not that the table is safe. The three regulators' attacks run on the full 20,000-row tables, and they carry the risk numbers.",
    ...data.membershipFm.map((m) => ` A stronger classifier on the same evidence, the TabFM foundation model, does see one: ${METHODS[m.method].name} at epsilon ${m.epsilon} on ${DATASETS[m.dataset].short}, ${fmt(m.risk, 3)} against a coin's 0.5. It is the same configuration as the leak above.`),
  ]);
}

/* ---------------------------------------------------------------- the reference check */

function checked(data) {
  const ag = data.agreement;
  const pairs = Object.values(ag.by_attack).reduce((a, b) => a + b.pairs, 0);
  const overlap = Object.values(ag.by_attack).reduce((a, b) => a + b.pairs * b.intervals_overlap, 0);
  const same = Object.values(ag.by_attack).reduce((a, b) => a + b.pairs * b.same_call, 0);
  const head = $("checked-headline");
  head.textContent = "";
  const stat = (figure, caption, range) => {
    const s = el("div", { class: "stat up" });
    s.append(el("span", { class: "figure" }, figure), el("span", { class: "caption" }, caption));
    if (range) s.append(el("span", { class: "range" }, range));
    return s;
  };
  head.append(
    stat(`${Math.round(overlap)} of ${pairs}`, `risk intervals that overlap Anonymeter's, on ${ag.tables} configurations and five attacks`),
    stat(`${Math.round(same)} of ${pairs}`, "the same detected-or-not call; the rest sit at the edge, explained in docs/attacks.md"),
    stat("Resolved", "a gap with TAPAS on membership inference: this project's features were weaker, so every run was redone with the library's encoding"),
  );
  fill($("checked-verdict"), [
    strong("Agreeing with the authors' own code is what shows the attacks are theirs. "),
    "On membership inference the check found this project's version weaker than the library's, so it was fixed and every membership run redone: 9,720 synthesiser fits, on a rented machine and a desktop. Along the way it turned up a bug in the reference library itself: TAPAS 1.0.0 misreads ordered columns in its histogram features. ",
    strong("It also took back a leak. "),
    "TabDDPM was first reported as leaking on the census data through singling out. Anonymeter, run on the same tables, did not agree, and the two disagreed in opposite directions from run to run: the mark of a random search, not of a leak. The fix was decided and written into the plan before anything was rerun: every singling-out attack now averages five independent searches, in both versions, on all 153 tables. The leak disappeared in both and was withdrawn. Every step is written up in the repository.",
  ]);
}

/* ---------------------------------------------------------------- takeaways */

function takeaways(data) {
  const attacked = data.cells.filter(scored);
  const flagged = attacked.filter((c) => c.dcr && c.dcr.closer_lo_min > 0.5);
  const l = data.leaks[0];
  const best = (pool) => pool.reduce((a, c) => (worstTask(c).u.delta > worstTask(a).u.delta ? c : a));
  const gaps = ORDER.map((ds) => {
    const cs = attacked.filter((c) => c.dataset === ds);
    return { open: -worstTask(best(cs.filter((c) => c.epsilon === null))).u.delta, dp: -worstTask(best(cs.filter((c) => c.epsilon !== null))).u.delta };
  });
  const span = (vs) => `${fmt(Math.min(...vs), 2)} to ${fmt(Math.max(...vs), 2)}`;
  const cards = [
    ["Demand a control group, or the number means nothing", "An attack on a useful table always works on someone, because predicting people is what the table is for. Only the extra success over people the synthesiser never saw is a leak. Ask any vendor what their privacy score is measured against."],
    ["Test the attacks before trusting a clean result", "Four methods people really use, a perturbed copy, SMOTE, k-anonymity and an overfitted model, went through the same attacks. The regulators' three attacks caught every perturbed copy, SMOTE and k-anonymity table they were given. Without checks like these, 'no leak found' looks exactly like 'attack too weak to find one'."],
    ["Attack the unusual people separately", "Randomly chosen targets are mostly ordinary people. Attacked again on the most unusual quarter, tables with a privacy guarantee at epsilon 1 and 2 gave away 4.6% to 7.2% on inference, where the full set of targets showed 2.5% or nothing at all."],
    ["Training longer is not the same as memorising", "TVAE trained for 3,000 epochs instead of 300, on 20,000 records, showed no detected risk on its full targets on any dataset; only inference on the most unusual card records found one. Overfitting is mostly a small-table worry. At this size, the classical methods people call safe were far more dangerous."],
    ["The most useful 'synthetic' tables were the leakiest", "The only tables that met the strict 0.02 standard for usefulness were a perturbed copy and SMOTE output, and the attacks broke both. A usefulness score on its own would have picked exactly the wrong tables."],
    ["Do not use distance to closest record as the privacy test", `It flagged ${flagged.length} tables no attack could break and passed the one that leaked, yet it is the check most tools show first. It does catch crude copies, every perturbed copy, SMOTE and k-anonymity table, but on real synthesisers it got the answer wrong in both directions.`],
    ["Differential privacy limits a leak; it does not make it zero", l ? `${METHODS[l.method].name} at epsilon ${l.epsilon} carries a formal guarantee and still gave away ${pct(l.risk)} on income bracket. Epsilon is a promise about the method. Whether a leak shows up on your data is a separate question, and only an attack answers it.` : "Epsilon is a promise about the method, not a measurement of a table."],
    ["Privacy has a price, and you can measure it before you pay", `The best synthesiser without privacy lost ${span(gaps.map((g) => g.open))} AUC on its worst task, and the best one with a guarantee lost ${span(gaps.map((g) => g.dp))}. That is the conversation a privacy officer and a data scientist need to have, with numbers on the table.`],
    ["Looking like the data is not the same as being useful", "The Gaussian copula reproduces the counts better than most and trains some of the worst models. Judge a synthetic table by training on it and testing on real data, not by a similarity score."],
    ["A null result is only as good as the attack's power", "The paper's membership attack found nothing anywhere, and could barely spot a straight copy of the training data. A stronger classifier on the same evidence found one leak it had missed. Saying so is the difference between 'we found no leak' and 'there is no leak'."],
    ["A leak claim deserves the same scrutiny as a safety claim", "One leak reported here did not survive a second look: checked against the authors' library, it turned out to be noise from a random search. The rule for settling it was fixed before the rerun and applied to every table, so it could as easily have added leaks as removed one."],
  ];
  const node = $("takeaway-cards");
  node.textContent = "";
  for (const [title, body] of cards) {
    const card = el("article", { class: "guide-card" });
    card.append(el("h3", {}, title), el("p", {}, body));
    node.append(card);
  }
}

/* ---------------------------------------------------------------- the explorer */

function explorer(data) {
  const select = $("explorer-dataset");
  for (const ds of ORDER) select.append(el("option", { value: ds }, DATASETS[ds].name));
  const draw = () => {
    const table = $("explorer-table");
    table.textContent = "";
    const head = el("thead");
    const hr = el("tr");
    const columns = [
      ["Synthesiser", "", false],
      ["Epsilon", "", false],
      ["Single out, 1", ATTACKS.singling_out_univariate, true],
      ["Single out, n", ATTACKS.singling_out_multivariate, true],
      ["Link, k 1", ATTACKS.linkability_k1, true],
      ["Link, k 10", ATTACKS.linkability_k10, true],
      ["Inference", ATTACKS.inference, true],
      ["Member", "Membership inference accuracy, chance 0.5", true],
      ["Usefulness", "AUC gap on the worst task, synthetic-trained minus real-trained", true],
      ["Fidelity", "Two-way marginal error", true],
      ["DCR", "Share of synthetic records closer to a training record", true],
      ["Fit", "Median fit time over seeds, and where", true],
    ];
    for (const [label, title, num] of columns) {
      const th = el("th", { scope: "col", class: num ? "num" : "" }, label);
      if (title) th.setAttribute("title", title);
      hr.append(th);
    }
    head.append(hr);
    const body = el("tbody");
    const cells = cellsOf(data, select.value).sort((a, b) => METHOD_ORDER.indexOf(a.method) - METHOD_ORDER.indexOf(b.method) || (a.epsilon ?? 99) - (b.epsilon ?? 99));
    for (const c of cells) {
      const tr = el("tr");
      tr.append(el("th", { scope: "row" }, METHODS[c.method].name), el("td", {}, c.epsilon === null ? "none" : String(c.epsilon)));
      if (c.not_run) {
        const td = el("td", { colspan: "10", class: "not-run" }, c.not_run.replace(/^not run: /, "Not run: "));
        tr.append(td);
        body.append(tr);
        continue;
      }
      if (!scored(c)) continue;
      const leaks = leakOf(data, c).map((x) => x.attack);
      for (const a of Object.keys(ATTACKS)) {
        const r = c.risk[a];
        const td = el("td", { class: "num" });
        const v = el("span", { class: leaks.includes(a) ? "worse" : "" }, fmt(100 * r.value, 1));
        td.append(v, el("span", { class: "interval" }, ` ${fmt(100 * r.lo, 1)} to ${fmt(100 * r.hi, 1)}`));
        tr.append(td);
      }
      tr.append(el("td", { class: "num" }, c.membership ? fmt(c.membership.accuracy, 3) : ""));
      const w = worstTask(c);
      const td = el("td", { class: "num" });
      td.append(document.createTextNode(signed(w.u.delta, 3)), el("span", { class: "interval" }, ` ${TASKS[w.task] ? w.task.replace("_", " ") : w.task}`));
      tr.append(td);
      tr.append(el("td", { class: "num" }, fmt(c.marginal_error["2way"], 3)));
      tr.append(el("td", { class: "num" }, c.dcr ? fmt(c.dcr.closer_to_training_share, 3) : ""));
      const fit = el("td", { class: "num" });
      if (c.fit_seconds_median !== undefined) fit.append(document.createTextNode(`${Math.round(c.fit_seconds_median).toLocaleString("en-CA")} s`), el("span", { class: "interval" }, ` ${hardwareShort(c.hardware[0])}`));
      tr.append(fit);
      body.append(tr);
    }
    table.append(head, body);
  };
  select.addEventListener("change", draw);
  draw();
}

function footer(data) {
  const v = data.versions;
  $("foot-versions").textContent = `Libraries: sdv ${v.sdv}, smartnoise-synth ${v["smartnoise-synth"]}, opendp ${v.opendp}, lightgbm ${v.lightgbm}, anonymeter ${v.anonymeter}`;
}

/* ---------------------------------------------------------------- start */

function render(data) {
  // The cards and the hero are about the 20,000-row grid. The second membership attacker's
  // detections are at about 1,000 rows and are told beside the leak, not counted as more leaks.
  data.membershipFm = data.leaks.filter((l) => l.attack === "membership_tabfm");
  data.leaks = data.leaks.filter((l) => l.attack !== "membership_tabfm");
  hero(data);
  surfaceControls(data);
  surface(data);
  fidelity(data);
  leak(data);
  ladderControls(data);
  ladder(data);
  dcrChart(data);
  gate(data);
  membership(data);
  checked(data);
  takeaways(data);
  explorer(data);
  footer(data);
}

fetch("data.json")
  .then((response) => {
    if (!response.ok) throw new Error(`data.json: ${response.status}`);
    return response.json();
  })
  .then(render)
  .catch((error) => {
    const node = $("failure");
    node.hidden = false;
    node.textContent = `The page could not draw its charts (${error.message}). The same numbers are in the repository's README and docs/results.md.`;
  });
