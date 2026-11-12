(() => {
  'use strict';
  const root = document.documentElement;
  const $ = (selector, scope = document) => scope.querySelector(selector);
  const $$ = (selector, scope = document) => [...scope.querySelectorAll(selector)];
  const DATA = window.HBALS_V2_DATA;
  const methods = ['HBALS', 'ILS-2opt', 'GA-2opt', 'ACO-2opt', 'MS-2opt', 'BA'];
  const colors = {
    HBALS: '#D9AD6D', 'ILS-2opt': '#78B9DC', 'GA-2opt': '#7FC69C',
    'ACO-2opt': '#D88C70', 'MS-2opt': '#AE9ADB', BA: '#D77C91'
  };

  function toast(message) {
    const node = $('#toast');
    if (!node) return;
    node.textContent = message;
    node.classList.add('show');
    clearTimeout(toast.timer);
    toast.timer = setTimeout(() => node.classList.remove('show'), 2200);
  }

  function renderResults() {
    if (!DATA) return;
    const tbody = $('#main-results-table tbody');
    if (tbody) {
      tbody.innerHTML = DATA.main.map(row => `<tr>
        <td><strong>${row.instance}</strong></td><td>${row.n}</td><td>${Number(row.bks).toLocaleString('en-US')}</td>
        ${methods.map(method => `<td class="${method === 'HBALS' ? 'hbals-cell' : ''}">${row.methods[method] ? row.methods[method].mean_gap.toFixed(3) : '—'}</td>`).join('')}
      </tr>`).join('');
    }
    const largeBody = $('.large-results tbody');
    if (largeBody) {
      const largeMethods = ['HBALS', 'ILS-2opt', 'GA-2opt', 'ACO-2opt'];
      largeBody.innerHTML = DATA.large.map(row => `<tr>
        <td><strong>${row.instance}</strong></td><td>${row.n}</td><td>${Number(row.bks).toLocaleString('en-US')}</td>
        ${largeMethods.map(method => `<td class="${method === 'HBALS' ? 'hbals-cell' : ''}">${row.methods[method].mean_gap.toFixed(3)}</td>`).join('')}
      </tr>`).join('');
    }
    renderMeanChart();
  }

  function renderMeanChart() {
    const node = $('#mean-gap-chart');
    if (!node || !DATA?.metadata?.main_mean_gap) return;
    const gaps = DATA.metadata.main_mean_gap;
    const max = Math.max(...Object.values(gaps));
    node.innerHTML = methods.map(method => {
      const value = gaps[method];
      const width = 8 + (Math.log1p(value) / Math.log1p(max)) * 92;
      return `<div class="mean-row ${method === 'HBALS' ? 'primary' : ''}">
        <span class="mean-label" style="--series:${colors[method]}">${method}</span>
        <span class="mean-track"><i class="mean-fill" style="width:${width}%;--bar-color:${colors[method]}"></i></span>
        <strong class="mean-value">${value.toFixed(3)}%</strong>
      </div>`;
    }).join('');
  }

  function updateLanguage(lang, persist = true) {
    const next = lang === 'fa' ? 'fa' : 'en';
    root.lang = next;
    root.dir = next === 'fa' ? 'rtl' : 'ltr';
    $$('[data-en][data-fa]').forEach(el => {
      const value = el.dataset[next];
      if (value !== undefined) el.innerHTML = value;
    });
    const button = $('#lang-toggle');
    if (button) {
      button.textContent = next === 'fa' ? 'EN' : 'FA';
      button.setAttribute('aria-label', next === 'fa' ? 'Switch to English' : 'تغییر زبان به فارسی');
    }
    if (persist) {
      try { localStorage.setItem('hbals-lang', next); } catch (_) {}
    }
    if (next === 'fa' && !$('#vazirmatn-font')) {
      const link = document.createElement('link');
      link.id = 'vazirmatn-font'; link.rel = 'stylesheet';
      link.href = 'https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;500;600;700;800&display=swap';
      document.head.append(link);
    }
    window.dispatchEvent(new Event('langchange'));
    window.dispatchEvent(new Event('resize'));
  }

  function updateTheme(theme, persist = true) {
    const next = theme === 'light' ? 'light' : 'dark';
    root.dataset.theme = next;
    const button = $('#theme-toggle');
    if (button) {
      $('.theme-icon', button).textContent = next === 'dark' ? '◐' : '◑';
      button.setAttribute('aria-label', next === 'dark' ? 'Switch to light theme' : 'Switch to dark theme');
    }
    if (persist) {
      try { localStorage.setItem('hbals-theme', next); } catch (_) {}
    }
    window.dispatchEvent(new Event('themechange'));
  }

  function setupNavigation() {
    const menu = $('#menu-toggle');
    const nav = $('#main-nav');
    if (menu && nav) {
      menu.addEventListener('click', () => {
        const open = nav.classList.toggle('open');
        menu.setAttribute('aria-expanded', String(open));
        menu.textContent = open ? '×' : '☰';
      });
      $$('a', nav).forEach(link => link.addEventListener('click', () => {
        nav.classList.remove('open'); menu.setAttribute('aria-expanded', 'false'); menu.textContent = '☰';
      }));
    }
    const sections = $$('main section[id]');
    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
          if (!entry.isIntersecting) return;
          const id = entry.target.id;
          $$('.main-nav a').forEach(link => link.classList.toggle('active', link.getAttribute('href') === `#${id}`));
        });
      }, { rootMargin: '-28% 0px -62% 0px' });
      sections.forEach(section => observer.observe(section));
    }
    const back = $('#back-top');
    window.addEventListener('scroll', () => {
      if (back) back.classList.toggle('visible', window.scrollY > 550);
    }, { passive: true });
    back?.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
  }

  function setupCopyCitation() {
    const button = $('#copy-citation');
    const bib = $('#bibtex-code');
    const status = $('#citation-status');
    if (!button || !bib) return;
    button.addEventListener('click', async () => {
      let copied = false;
      try {
        await navigator.clipboard.writeText(bib.textContent.trim());
        copied = true;
      } catch (_) {
        const area = document.createElement('textarea');
        area.value = bib.textContent.trim(); area.style.position = 'fixed'; area.style.opacity = '0';
        document.body.append(area); area.select();
        try { copied = document.execCommand('copy'); } catch (_) {}
        area.remove();
      }
      const message = copied ? (root.lang === 'fa' ? 'استناد کپی شد' : 'BibTeX copied') : (root.lang === 'fa' ? 'کپی ناموفق بود' : 'Copy was not available');
      if (status) status.textContent = message;
      toast(message);
    });
  }

  function setupReveal() {
    if (!('IntersectionObserver' in window) || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const targets = $$('.section-block, .metric-strip, .publication-card, .hero-visual');
    const observer = new IntersectionObserver(entries => entries.forEach(entry => {
      if (entry.isIntersecting) { entry.target.classList.add('revealed'); observer.unobserve(entry.target); }
    }), { threshold: 0.06, rootMargin: '0px 0px -30px 0px' });
    targets.forEach(target => { target.classList.add('reveal-ready'); observer.observe(target); });
  }

  $('#lang-toggle')?.addEventListener('click', () => updateLanguage(root.lang === 'fa' ? 'en' : 'fa'));
  $('#theme-toggle')?.addEventListener('click', () => updateTheme(root.dataset.theme === 'dark' ? 'light' : 'dark'));
  setupNavigation();
  setupCopyCitation();
  setupReveal();
  renderResults();
  updateLanguage(root.lang || 'en', false);
  updateTheme(root.dataset.theme || 'dark', false);
  const year = $('#year');
  if (year) year.textContent = new Date().getFullYear();
})();
