/* HBALS v2 browser lab
 * Faithful JavaScript implementation of the final HBALS configuration in
 * v2/src/tsp_core.py. The interactive preview uses a user-selected iteration
 * cap for responsiveness; the experiment explorer below reads saved Python
 * run averages from assets/data/hbals-v2-data.js.
 */
(() => {
  'use strict';

  const DATA = window.HBALS_V2_DATA;
  if (!DATA) return;

  const $ = id => document.getElementById(id);
  const root = document.documentElement;
  const canvas = $('map');
  const ctx = canvas?.getContext('2d');
  if (!canvas || !ctx) return;

  const palette = {
    HBALS: '#F2B632',
    'ILS-2opt': '#4EA4E8',
    'GA-2opt': '#65B982',
    'ACO-2opt': '#D18B53',
    'MS-2opt': '#A889D8',
    BA: '#D66C83'
  };
  const methodNames = ['HBALS', 'ILS-2opt', 'GA-2opt', 'ACO-2opt', 'MS-2opt', 'BA'];
  const mainNames = DATA.instances.filter(x => x.group === 'main').map(x => x.name);
  const instanceByName = Object.fromEntries(DATA.instances.map(x => [x.name, x]));
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const state = {
    instance: 'eil51',
    base: [], extra: [], points: [], n: 0,
    distance: null, population: [], costs: [], best: [], bestCost: Infinity,
    evals: 0, iteration: 0, iterationLimit: 80,
    running: false, paused: false, finished: false,
    generation: 0, timer: 0, frame: 0,
    custom: false, bounds: null,
    transform: { scale: 1, ox: 0, oy: 0 },
    beePhase: 0,
    hiddenMethods: new Set()
  };

  const ui = {
    picker: $('picker'),
    dsname: $('dsname'),
    iteration: $('it'),
    length: $('len'),
    known: $('known'),
    gap: $('gap'),
    evals: $('evals'),
    status: $('status'),
    run: $('rerun'),
    pause: $('pause'),
    limit: $('iteration-limit'),
    reset: $('reset'),
    progress: $('demo-progress'),
    progressLabel: $('progress-label'),
    expInstance: $('experiment-instance'),
    expChart: $('experiment-chart'),
    expLegend: $('experiment-legend'),
    expMeta: $('experiment-meta'),
    expNote: $('experiment-note'),
    ablationTable: $('ablation-table')
  };

  const isFa = () => root.lang === 'fa';
  const text = (en, fa) => isFa() ? fa : en;
  const randomInt = n => Math.floor(Math.random() * n);
  const fmtInt = n => Math.round(n).toLocaleString('en-US');
  const fmtEval = n => n >= 1e9 ? `${(n / 1e9).toFixed(2)}B` : n >= 1e6 ? `${(n / 1e6).toFixed(2)}M` : n.toLocaleString('en-US');
  const fmtGap = v => `${v.toFixed(3)}%`;
  const cssVar = name => getComputedStyle(root).getPropertyValue(name).trim();

  // All benchmark coordinates and the BKS values below are parsed from the
  // EUC_2D TSPLIB files and BKS list included with the supplied v2 study.
  function buildPicker() {
    if (!ui.picker) return;
    ui.picker.replaceChildren();
    const groups = [
      { label: text('Main study · 12 instances', 'آزمایش اصلی · ۱۲ نمونه'), items: DATA.instances.filter(x => x.group === 'main') },
      { label: text('Larger instances · 3', 'نمونه‌های بزرگ‌تر · ۳'), items: DATA.instances.filter(x => x.group === 'large') }
    ];
    groups.forEach(group => {
      const wrap = document.createElement('div');
      wrap.className = 'picker-group';
      const label = document.createElement('span');
      label.className = 'picker-group-label';
      label.textContent = group.label;
      wrap.append(label);
      const row = document.createElement('div');
      row.className = 'picker-row';
      group.items.forEach(inst => {
        const b = document.createElement('button');
        b.type = 'button';
        b.dataset.ds = inst.name;
        b.setAttribute('aria-pressed', inst.name === state.instance ? 'true' : 'false');
        b.innerHTML = `<span>${inst.name}</span><small>${inst.n}</small>`;
        b.addEventListener('click', () => selectInstance(inst.name));
        row.append(b);
      });
      wrap.append(row);
      ui.picker.append(wrap);
    });
    const custom = document.createElement('div');
    custom.className = 'picker-group';
    const customLabel = document.createElement('span');
    customLabel.className = 'picker-group-label';
    customLabel.textContent = text('Custom', 'سفارشی');
    custom.append(customLabel);
    const row = document.createElement('div');
    row.className = 'picker-row';
    const random = document.createElement('button');
    random.type = 'button';
    random.dataset.ds = 'random';
    random.setAttribute('aria-pressed', 'false');
    random.innerHTML = `<span>${text('Random cities', 'شهرهای تصادفی')}</span><small>30</small>`;
    random.addEventListener('click', () => selectInstance('random'));
    row.append(random);
    custom.append(row);
    ui.picker.append(custom);
  }

  function fillExperimentPicker() {
    if (!ui.expInstance) return;
    const selected = ui.expInstance.value || 'eil51';
    ui.expInstance.replaceChildren();
    DATA.instances.forEach(inst => {
      const opt = document.createElement('option');
      opt.value = inst.name;
      opt.textContent = `${inst.name} · ${inst.n} ${text('cities', 'شهر')}`;
      ui.expInstance.append(opt);
    });
    ui.expInstance.value = instanceByName[selected] ? selected : 'eil51';
  }

  function updateStaticTranslations() {
    document.querySelectorAll('[data-hb-en]').forEach(el => {
      el.innerHTML = isFa() && el.dataset.hbFa ? el.dataset.hbFa : el.dataset.hbEn;
    });
    if (ui.picker) buildPicker();
    fillExperimentPicker();
    if (ui.pause && !ui.pause.disabled) ui.pause.textContent = state.paused ? text('Resume', 'ادامه') : text('Pause', 'مکث');
    updateReadout();
    drawExperiment();
  }

  function getBounds(points) {
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    points.forEach(([x, y]) => {
      minX = Math.min(minX, x); maxX = Math.max(maxX, x);
      minY = Math.min(minY, y); maxY = Math.max(maxY, y);
    });
    if (!Number.isFinite(minX)) return { minX: 0, maxX: 1000, minY: 0, maxY: 700 };
    return { minX, maxX, minY, maxY };
  }

  function resizeCanvas() {
    const rect = canvas.getBoundingClientRect();
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    state.width = Math.max(1, rect.width);
    state.height = Math.max(1, rect.height);
    canvas.width = Math.round(state.width * dpr);
    canvas.height = Math.round(state.height * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    fitPoints();
    drawMap();
  }

  function fitPoints() {
    const b = state.bounds || getBounds(state.points);
    const pad = 24;
    const rx = Math.max(b.maxX - b.minX, 1e-9);
    const ry = Math.max(b.maxY - b.minY, 1e-9);
    const scale = Math.min((state.width - pad * 2) / rx, (state.height - pad * 2) / ry);
    state.transform = {
      scale,
      ox: (state.width - scale * rx) / 2 - scale * b.minX,
      oy: (state.height - scale * ry) / 2 + scale * b.maxY
    };
  }

  function screenPoint(p) {
    const t = state.transform;
    return [t.ox + p[0] * t.scale, t.oy - p[1] * t.scale];
  }

  function buildDistanceMatrix() {
    const n = state.n;
    const flat = new Float64Array(n * n);
    for (let i = 0; i < n; i++) {
      for (let j = i + 1; j < n; j++) {
        const dx = state.points[i][0] - state.points[j][0];
        const dy = state.points[i][1] - state.points[j][1];
        const d = Math.hypot(dx, dy);
        // TSPLIB EUC_2D uses nearest-integer rounding. User-added cities use
        // exact Euclidean distances, as in the original interactive preview.
        const value = state.custom ? d : Math.floor(d + 0.5);
        flat[i * n + j] = value;
        flat[j * n + i] = value;
      }
    }
    state.distance = flat;
  }

  const dist = (i, j) => state.distance[i * state.n + j];

  function tourLength(tour) {
    const n = state.n;
    let sum = 0;
    for (let i = 0; i < n - 1; i++) sum += dist(tour[i], tour[i + 1]);
    sum += dist(tour[n - 1], tour[0]);
    state.evals += n;
    return sum;
  }

  function nearestNeighbour(start) {
    const n = state.n;
    const visited = new Uint8Array(n);
    const tour = new Array(n);
    tour[0] = start;
    visited[start] = 1;
    let current = start;
    for (let k = 1; k < n; k++) {
      let nearest = -1, bestDistance = Infinity;
      for (let j = 0; j < n; j++) {
        if (!visited[j] && dist(current, j) < bestDistance) {
          bestDistance = dist(current, j);
          nearest = j;
        }
      }
      tour[k] = nearest;
      visited[nearest] = 1;
      current = nearest;
    }
    state.evals += Math.floor(n * n / 2);
    return tour;
  }

  function randomTour() {
    const tour = Array.from({ length: state.n }, (_, i) => i);
    for (let i = tour.length - 1; i > 0; i--) {
      const j = randomInt(i + 1);
      [tour[i], tour[j]] = [tour[j], tour[i]];
    }
    return tour;
  }

  function swapDelta(tour, i, j) {
    const n = state.n;
    if (i > j) [i, j] = [j, i];
    if (j === i + 1) {
      const a = tour[(i - 1 + n) % n], b = tour[i], e = tour[j], f = tour[(j + 1) % n];
      return dist(a, e) + dist(e, b) + dist(b, f) - dist(a, b) - dist(b, e) - dist(e, f);
    }
    if (i === 0 && j === n - 1) {
      const a = tour[n - 2], b = tour[n - 1], e = tour[0], f = tour[1];
      return dist(a, e) + dist(e, b) + dist(b, f) - dist(a, b) - dist(b, e) - dist(e, f);
    }
    const a = tour[(i - 1 + n) % n], b = tour[i], c = tour[i + 1];
    const d = tour[j - 1], e = tour[j], f = tour[(j + 1) % n];
    const oldCost = dist(a, b) + dist(b, c) + dist(d, e) + dist(e, f);
    const newCost = dist(a, e) + dist(e, c) + dist(d, b) + dist(b, f);
    return newCost - oldCost;
  }

  function randomSwap(tour) {
    const n = state.n;
    const i = randomInt(n);
    let j = randomInt(n);
    while (j === i) j = randomInt(n);
    const delta = swapDelta(tour, i, j);
    [tour[i], tour[j]] = [tour[j], tour[i]];
    state.evals += 4;
    return delta;
  }

  // Same first-improvement 2-opt scan/restart rule and evaluation accounting
  // as the Numba implementation in v2/src/tsp_core.py.
  function twoOpt(tour, maxMoves) {
    const n = state.n;
    let moves = 0, gain = 0, evaluations = 0;
    while (moves < maxMoves) {
      let found = false;
      for (let i = 1; i < n - 2; i++) {
        const a = tour[i - 1], b = tour[i], Dab = dist(a, b);
        for (let j = i + 2; j < n; j++) {
          const c = tour[j], d = j + 1 < n ? tour[j + 1] : tour[0];
          const delta = dist(a, c) + dist(b, d) - Dab - dist(c, d);
          if (delta < -1e-9) {
            evaluations += j - i - 1;
            let left = i, right = j;
            while (left < right) {
              [tour[left], tour[right]] = [tour[right], tour[left]];
              left++; right--;
            }
            gain += delta;
            moves++;
            found = true;
            break;
          }
        }
        if (found) break;
        evaluations += n - i - 2;
      }
      if (!found) break;
    }
    state.evals += evaluations;
    return gain;
  }

  // The paper now describes this accurately as a random segment reversal,
  // not a conventional 3-opt move.
  function lightSegmentReversal(tour, tries) {
    const n = state.n;
    let bestDelta = 0, bestI = -1, bestJ = -1;
    for (let q = 0; q < tries; q++) {
      let x = 1 + randomInt(n - 1), y = 1 + randomInt(n - 1), z = 1 + randomInt(n - 1);
      while (y === x) y = 1 + randomInt(n - 1);
      while (z === x || z === y) z = 1 + randomInt(n - 1);
      [x, y, z] = [x, y, z].sort((a, b) => a - b);
      const i = x, j = y;
      const a = tour[i - 1], b = tour[i], c = tour[j - 1], d = tour[j];
      const delta = dist(a, c) + dist(b, d) - dist(a, b) - dist(c, d);
      if (delta < bestDelta - 1e-9) {
        bestDelta = delta;
        bestI = i;
        bestJ = j - 1;
      }
    }
    state.evals += tries;
    if (bestI >= 0) {
      let l = bestI, r = bestJ;
      while (l < r) {
        [tour[l], tour[r]] = [tour[r], tour[l]];
        l++; r--;
      }
    }
    return bestDelta;
  }

  // Final v2 HBALS parameterization: n=20, m=12, e=3, nep=8, nsp=4,
  // fixed neighbourhood k=1; 70%/30% local-search probabilities and a 10%
  // elite random segment-reversal probability. No adaptive neighbourhood.
  function searchSite(base, baseCost, count, k, pLocal, localMoves, pReverse, reverseTries) {
    let bestTour = base.slice();
    let bestCost = baseCost;
    for (let q = 0; q < count; q++) {
      const candidate = base.slice();
      let candidateCost = baseCost;
      for (let j = 0; j < k; j++) candidateCost += randomSwap(candidate);
      if (pLocal > 0 && Math.random() < pLocal) candidateCost += twoOpt(candidate, localMoves);
      if (pReverse > 0 && Math.random() < pReverse) candidateCost += lightSegmentReversal(candidate, reverseTries);
      if (candidateCost < bestCost) {
        bestTour = candidate;
        bestCost = candidateCost;
      }
    }
    return [bestTour, bestCost];
  }

  function initializePopulation() {
    state.population = [];
    state.evals = 0;
    const countNN = Math.max(1, Math.floor(0.5 * 20));
    for (let i = 0; i < 20; i++) {
      const tour = i < countNN && i < state.n ? nearestNeighbour(i) : randomTour();
      state.population.push(tour);
    }
    state.costs = state.population.map(tourLength);
    const bestIndex = state.costs.indexOf(Math.min(...state.costs));
    state.best = state.population[bestIndex].slice();
    state.bestCost = state.costs[bestIndex];
  }

  function initializeSearch() {
    state.generation++;
    clearTimeout(state.timer);
    state.running = false;
    state.paused = false;
    state.finished = false;
    state.evals = 0;
    state.iteration = 0;
    state.points = state.base.concat(state.extra);
    state.n = state.points.length;
    state.custom = state.extra.length > 0 || state.instance === 'random';
    state.bounds = getBounds(state.points);
    buildDistanceMatrix();
    initializePopulation();
    state.running = true;
    state.beePhase = 0;
    if (ui.pause) {
      ui.pause.disabled = false;
      ui.pause.textContent = text('Pause', 'مکث');
    }
    if (ui.reset) ui.reset.hidden = state.extra.length === 0;
    updateReadout();
    scheduleStep(state.generation);
    drawMap();
  }

  function hbalsStep() {
    const order = state.costs.map((_, i) => i).sort((a, b) => state.costs[a] - state.costs[b]);
    const newPopulation = [];
    const newCosts = [];
    for (let r = 0; r < 3; r++) {
      const idx = order[r];
      const [tour, cost] = searchSite(state.population[idx], state.costs[idx], 8, 1, 0.7, 20, 0.1, 3);
      newPopulation.push(tour);
      newCosts.push(cost);
    }
    for (let r = 3; r < 12; r++) {
      const idx = order[r];
      const [tour, cost] = searchSite(state.population[idx], state.costs[idx], 4, 1, 0.3, 10, 0, 0);
      newPopulation.push(tour);
      newCosts.push(cost);
    }
    for (let r = 12; r < 20; r++) {
      const tour = randomTour();
      newPopulation.push(tour);
      newCosts.push(tourLength(tour));
    }
    state.population = newPopulation;
    state.costs = newCosts;
    const bestIndex = state.costs.indexOf(Math.min(...state.costs));
    if (state.costs[bestIndex] < state.bestCost) {
      state.best = state.population[bestIndex].slice();
      state.bestCost = state.costs[bestIndex];
    }
    state.iteration++;
  }

  function scheduleStep(generation) {
    if (generation !== state.generation || !state.running || state.paused || state.finished) return;
    state.timer = window.setTimeout(() => {
      if (generation !== state.generation || !state.running || state.paused || state.finished) return;
      try {
        hbalsStep();
        if (state.iteration >= state.iterationLimit) {
          state.running = false;
          state.finished = true;
          if (ui.pause) ui.pause.disabled = true;
        }
        updateReadout();
        drawMap();
        if (state.running) scheduleStep(generation);
      } catch (err) {
        state.running = false;
        state.finished = true;
        setStatus(text('The preview stopped because the browser encountered an error.', 'پیش‌نمایش به‌دلیل بروز خطا در مرورگر متوقف شد.'));
        console.error('HBALS preview error:', err);
      }
    }, reducedMotion ? 1 : 24);
  }

  function setStatus(value, ok = false) {
    if (!ui.status) return;
    ui.status.textContent = value;
    ui.status.classList.toggle('ok', ok);
  }

  function updateReadout() {
    const inst = instanceByName[state.instance];
    const known = state.custom ? null : inst?.bks;
    if (ui.dsname) ui.dsname.textContent = state.instance === 'random'
      ? text('Random cities', 'شهرهای تصادفی')
      : `${state.instance}${state.extra.length ? ` + ${state.extra.length}` : ''}`;
    if (ui.iteration) ui.iteration.textContent = `${state.iteration}/${state.iterationLimit}`;
    if (ui.length) ui.length.textContent = Number.isFinite(state.bestCost) ? fmtInt(state.bestCost) : '—';
    if (ui.known) ui.known.textContent = known ? fmtInt(known) : '—';
    if (ui.gap) ui.gap.textContent = known ? `${((state.bestCost / known - 1) * 100).toFixed(2)}%` : '—';
    if (ui.evals) ui.evals.textContent = fmtEval(state.evals);
    if (ui.progress) ui.progress.style.width = `${Math.min(100, state.iteration / state.iterationLimit * 100)}%`;
    if (ui.progressLabel) ui.progressLabel.textContent = `${state.iteration} / ${state.iterationLimit} ${text('preview iterations', 'تکرار پیش‌نمایش')} · ${fmtEval(state.evals)} ${text('move evaluations', 'ارزیابی حرکت')}`;
    if (!state.finished && state.running) {
      setStatus(text('Searching with the v2 HBALS procedure…', 'جست‌وجو با روش HBALS نسخهٔ ۲ در حال اجراست…'));
    } else if (state.paused) {
      setStatus(text('Paused. Resume to continue the same search.', 'متوقف شده است. برای ادامه، از سرگیری را بزنید.'));
    } else if (state.finished) {
      if (known && Math.round(state.bestCost) <= known) {
        setStatus(text(`The browser preview reached the best-known length (${fmtInt(known)}). This is one stochastic run, not a proof of optimality.`, `پیش‌نمایش مرورگر به طول بهترین مسیر شناخته‌شده (${fmtInt(known)}) رسید. این فقط یک اجرای تصادفی است و اثبات بهینگی نیست.`), true);
      } else if (known) {
        setStatus(text(`Preview complete. The best tour is ${((state.bestCost / known - 1) * 100).toFixed(2)}% above the best-known value. Try another run to see a different stochastic outcome.`, `پیش‌نمایش تمام شد. مسیر فعلی ${((state.bestCost / known - 1) * 100).toFixed(2)}٪ بالاتر از بهترین مقدار شناخته‌شده است. برای مشاهدهٔ نتیجه‌ای تصادفی دیگر، دوباره اجرا کنید.`));
      } else {
        setStatus(text('Preview complete. Your custom instance has no published best-known value for comparison.', 'پیش‌نمایش تمام شد. برای نمونهٔ سفارشی شما مقدار بهترین مسیر شناخته‌شده‌ای جهت مقایسه وجود ندارد.'));
      }
    }
  }

  function drawMap() {
    if (!state.points.length || !state.best.length) return;
    const w = state.width || canvas.clientWidth;
    const h = state.height || canvas.clientHeight;
    ctx.clearRect(0, 0, w, h);
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';
    const routeColor = cssVar('--route') || '#C9D6EE';
    const ink = cssVar('--ink') || '#E8EDF7';
    const accent = cssVar('--accent') || '#F2B632';
    ctx.strokeStyle = routeColor;
    ctx.globalAlpha = 0.78;
    ctx.lineWidth = 1.7;
    ctx.beginPath();
    state.best.forEach((index, i) => {
      const p = screenPoint(state.points[index]);
      if (i === 0) ctx.moveTo(p[0], p[1]); else ctx.lineTo(p[0], p[1]);
    });
    ctx.closePath();
    ctx.stroke();
    ctx.globalAlpha = 1;

    const radius = state.n > 250 ? 2.2 : state.n > 150 ? 2.8 : state.n > 75 ? 3.5 : 4.2;
    state.points.forEach((point, i) => {
      const [px, py] = screenPoint(point);
      ctx.beginPath();
      ctx.arc(px, py, i >= state.base.length ? radius + 1.3 : radius, 0, Math.PI * 2);
      ctx.fillStyle = i >= state.base.length ? accent : '#FFFFFF';
      ctx.strokeStyle = i >= state.base.length ? accent : ink;
      ctx.lineWidth = i >= state.base.length ? 2.2 : 1.2;
      ctx.fill();
      ctx.stroke();
    });

    if (!reducedMotion && !state.paused) state.beePhase += Math.max(0.045, state.n / 1600);
    const beeCount = 4;
    ctx.fillStyle = accent;
    ctx.strokeStyle = ink;
    ctx.lineWidth = 1.25;
    for (let b = 0; b < beeCount; b++) {
      const phase = (state.beePhase + b * state.best.length / beeCount) % state.best.length;
      const i = Math.floor(phase), f = phase - i;
      const a = screenPoint(state.points[state.best[i]]);
      const z = screenPoint(state.points[state.best[(i + 1) % state.best.length]]);
      ctx.beginPath();
      ctx.arc(a[0] + (z[0] - a[0]) * f, a[1] + (z[1] - a[1]) * f, 5, 0, Math.PI * 2);
      ctx.fill(); ctx.stroke();
    }
  }

  function selectInstance(name) {
    state.instance = name;
    state.extra = [];
    if (name === 'random') {
      state.base = Array.from({ length: 30 }, () => [20 + Math.random() * 960, 20 + Math.random() * 660]);
      state.bounds = { minX: 0, maxX: 1000, minY: 0, maxY: 700 };
    } else {
      state.base = instanceByName[name].coords.map(p => [p[0], p[1]]);
      state.bounds = getBounds(state.base);
    }
    buildPicker();
    resizeCanvas();
    initializeSearch();
  }

  function addCity(x, y) {
    if (state.points.length >= 400 || !Number.isFinite(state.transform.scale)) return;
    const t = state.transform;
    state.extra.push([(x - t.ox) / t.scale, (t.oy - y) / t.scale]);
    state.bounds = getBounds(state.base.concat(state.extra));
    fitPoints();
    initializeSearch();
  }

  function setupDemoControls() {
    if (ui.limit) {
      ui.limit.addEventListener('change', () => {
        state.iterationLimit = Math.max(10, Number(ui.limit.value) || 80);
        initializeSearch();
      });
    }
    ui.run?.addEventListener('click', initializeSearch);
    ui.pause?.addEventListener('click', () => {
      if (state.finished) return;
      if (state.paused) {
        state.paused = false;
        state.running = true;
        ui.pause.textContent = text('Pause', 'مکث');
        scheduleStep(state.generation);
      } else {
        state.paused = true;
        state.running = false;
        clearTimeout(state.timer);
        ui.pause.textContent = text('Resume', 'ادامه');
      }
      updateReadout();
      drawMap();
    });
    ui.reset?.addEventListener('click', () => {
      state.extra = [];
      state.bounds = getBounds(state.base);
      initializeSearch();
    });
    canvas.addEventListener('click', e => {
      const rect = canvas.getBoundingClientRect();
      addCity(e.clientX - rect.left, e.clientY - rect.top);
    });
    canvas.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        addCity(24 + Math.random() * (state.width - 48), 24 + Math.random() * (state.height - 48));
      }
    });
    document.querySelectorAll('.tryit').forEach(button => {
      button.addEventListener('click', () => {
        selectInstance(button.dataset.ds);
        $('top')?.scrollIntoView({ behavior: reducedMotion ? 'auto' : 'smooth' });
      });
    });
    window.addEventListener('resize', resizeCanvas);
    window.addEventListener('themechange', drawMap);
    window.addEventListener('langchange', updateStaticTranslations);
  }

  // -----------------------------------------------------------------------
  // Research experiment explorer: means of the saved Python run-level curves.
  // -----------------------------------------------------------------------
  function drawExperiment() {
    if (!ui.expChart || !ui.expInstance) return;
    const name = ui.expInstance.value || 'eil51';
    const inst = instanceByName[name];
    const series = DATA.curves[name] || {};
    const available = Object.keys(series).filter(m => !state.hiddenMethods.has(m));
    const c = ui.expChart;
    const r = c.getBoundingClientRect();
    if (!r.width) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = r.width, h = r.height;
    c.width = Math.round(w * dpr); c.height = Math.round(h * dpr);
    const g = c.getContext('2d');
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    g.clearRect(0, 0, w, h);

    const left = isFa() ? 54 : 58, right = 18, top = 18, bottom = 34;
    const plotW = w - left - right, plotH = h - top - bottom;
    const xAt = i => left + (i / 99) * plotW;
    // Scale to the full selected-instance data (including currently hidden methods)
    // so large early gaps are never silently clipped at an arbitrary ceiling.
    const maxGap = Math.max(100, ...Object.values(series).flat().filter(Number.isFinite));
    const yMin = -2, yMax = Math.log10(maxGap * 1.08);
    const yAt = value => {
      const v = Math.max(0.01, Math.min(maxGap * 1.08, value));
      return top + (yMax - Math.log10(v)) / (yMax - yMin) * plotH;
    };
    const grid = cssVar('--line') || '#2A3650';
    const muted = cssVar('--muted') || '#9FACC4';
    const ink = cssVar('--ink') || '#E8EDF7';
    g.font = `11px ${getComputedStyle(root).getPropertyValue('--display') || 'Arial'}`;
    g.textBaseline = 'middle';
    [0.01, 0.1, 1, 10, 100, 1000, 10000].filter(tick => tick <= maxGap * 1.08).forEach(tick => {
      const y = yAt(tick);
      g.strokeStyle = grid; g.lineWidth = 1;
      g.beginPath(); g.moveTo(left, y); g.lineTo(w - right, y); g.stroke();
      g.fillStyle = muted;
      g.textAlign = isFa() ? 'right' : 'left';
      g.fillText(tick < 1 ? tick.toFixed(tick === 0.01 ? 2 : 1) : String(tick), isFa() ? w - 4 : 4, y);
    });
    [0, 20, 40, 60, 80, 100].forEach(tick => {
      const x = left + tick / 100 * plotW;
      g.strokeStyle = grid; g.lineWidth = 1; g.globalAlpha = 0.45;
      g.beginPath(); g.moveTo(x, top); g.lineTo(x, top + plotH); g.stroke(); g.globalAlpha = 1;
      g.fillStyle = muted; g.textAlign = 'center';
      g.fillText(String(tick), x, h - 15);
    });
    g.fillStyle = muted; g.textAlign = 'center';
    g.fillText(text('Equal-budget used (%)', 'درصد بودجهٔ برابر مصرف‌شده'), left + plotW / 2, h - 2);
    g.save();
    g.translate(isFa() ? w - 6 : 12, top + plotH / 2);
    g.rotate(-Math.PI / 2);
    g.textAlign = 'center';
    g.fillText(text('Mean gap to BKS (%) · log scale', 'میانگین فاصله از BKS (درصد) · مقیاس لگاریتمی'), 0, 0);
    g.restore();

    available.forEach(method => {
      const values = series[method];
      if (!values?.length) return;
      g.strokeStyle = palette[method] || '#888';
      g.lineWidth = method === 'HBALS' ? 2.8 : 2.0;
      g.lineJoin = 'round'; g.lineCap = 'round';
      g.beginPath();
      values.forEach((v, i) => {
        const x = xAt(i), y = yAt(v);
        if (i === 0) g.moveTo(x, y); else g.lineTo(x, y);
      });
      g.stroke();
      const endX = xAt(99), endY = yAt(values[99]);
      g.fillStyle = palette[method] || '#888';
      g.beginPath(); g.arc(endX, endY, method === 'HBALS' ? 3.2 : 2.4, 0, Math.PI * 2); g.fill();
    });

    if (ui.expMeta) {
      const budget = inst.budget / 1e6;
      const runCount = inst.group === 'main' ? 20 : 10;
      const runLabel = inst.group === 'main'
        ? text('runs per method · plain BA: 10', 'اجرا برای هر روش · زنبور ساده: ۱۰')
        : text('runs per method', 'اجرا برای هر روش');
      ui.expMeta.innerHTML = `
        <span><b>${inst.n}</b><small>${text('cities', 'شهر')}</small></span>
        <span><b>${fmtInt(inst.bks)}</b><small>${text('best-known length', 'طول بهترین مسیر شناخته‌شده')}</small></span>
        <span><b>${budget.toFixed(1)}M</b><small>${text('move-evaluation budget', 'بودجهٔ ارزیابی حرکت')}</small></span>
        <span><b>${runCount}</b><small>${runLabel}</small></span>`;
    }
    if (ui.expNote) {
      ui.expNote.textContent = text(
        'Each line is the mean of the saved run-level best-so-far curves, sampled at 1% increments of the same per-instance evaluation budget. The logarithmic y-axis auto-scales to include the full range of every method for the selected instance; the browser demo above is a separate, shorter interactive preview.',
        'هر خط میانگین منحنی بهترین‌مقدار-تا-آن‌لحظه در اجراهای ذخیره‌شده است که در گام‌های ۱٪ از بودجهٔ ارزیابی یکسان هر نمونه نمونه‌برداری شده است. محور عمودی لگاریتمی است و برای نمایش کامل دامنهٔ همهٔ روش‌ها در نمونهٔ انتخاب‌شده به‌صورت خودکار تنظیم می‌شود؛ دمو مرورگر در بالا یک پیش‌نمایش تعاملی کوتاه‌تر و جداگانه است.'
      );
    }
    if (ui.expLegend) {
      ui.expLegend.replaceChildren();
      Object.keys(series).forEach(method => {
        const b = document.createElement('button');
        b.type = 'button';
        b.className = 'exp-legend-item';
        b.setAttribute('aria-pressed', state.hiddenMethods.has(method) ? 'false' : 'true');
        b.innerHTML = `<i style="--series:${palette[method] || '#888'}"></i><span>${method}</span>`;
        b.addEventListener('click', () => {
          if (state.hiddenMethods.has(method)) state.hiddenMethods.delete(method);
          else state.hiddenMethods.add(method);
          drawExperiment();
        });
        ui.expLegend.append(b);
      });
    }
  }

  function buildAblationTable() {
    if (!ui.ablationTable) return;
    const labels = {
      HBALS: ['Full HBALS', 'HBALS کامل'],
      'HBALS+adaptive': ['Adaptive neighbourhood', 'همسایگی تطبیقی'],
      'HBALS-ngh3': ['Neighbourhood size = 3', 'اندازهٔ همسایگی = ۳'],
      'HBALS-noNN': ['No nearest-neighbour seeds', 'بدون بذر همسایهٔ نزدیک'],
      'HBALS-noRev': ['No segment reversal', 'بدون وارون‌سازی قطعه'],
      'HBALS-noSelLS': ['No selected-site 2-opt', 'بدون 2-opt در سایت‌های منتخب'],
      'HBALS-noEliteLS': ['No elite-site 2-opt', 'بدون 2-opt در سایت‌های نخبه'],
      'HBALS-noScouts': ['No scout bees', 'بدون زنبورهای دیده‌بان']
    };
    const ordered = DATA.ablation.slice().sort((a, b) => Number(b.variant === 'HBALS') - Number(a.variant === 'HBALS'));
    ui.ablationTable.innerHTML = ordered.map(row => {
      const label = labels[row.variant] || [row.variant, row.variant];
      const name = text(label[0], label[1]);
      const delta = row.delta === 0 ? '—' : `${row.delta > 0 ? '+' : ''}${row.delta.toFixed(3)} pp`;
      return `<tr${row.variant === 'HBALS' ? ' class="baseline-row"' : ''}><td>${name}</td><td>${row.mean_gap.toFixed(3)}%</td><td>${delta}</td></tr>`;
    }).join('');
  }

  // Wire up and start the interactive benchmark.
  ui.iterationLimit = Number(ui.limit?.value || 80);
  buildPicker();
  fillExperimentPicker();
  ui.expInstance?.addEventListener('change', drawExperiment);
  setupDemoControls();
  buildAblationTable();
  updateStaticTranslations();
  selectInstance('eil51');
  drawExperiment();
  window.addEventListener('langchange', buildAblationTable);
  window.addEventListener('resize', () => drawExperiment());
})();
