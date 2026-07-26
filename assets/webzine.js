/* S21 Phone Webzine — shared chrome + mobile drawer */
(() => {
  const root = document.documentElement;
  const saved = localStorage.getItem('s21-webzine-theme');
  if (saved) root.setAttribute('data-theme', saved);

  const spine = document.getElementById('spineFill');
  const topBtn = document.getElementById('wzTop');
  const themeBtns = document.querySelectorAll('[data-theme-toggle]');

  const onScroll = () => {
    const max = document.documentElement.scrollHeight - innerHeight;
    if (spine) spine.style.height = (max > 0 ? (scrollY / max) * 100 : 0) + '%';
    if (topBtn) topBtn.classList.toggle('show', scrollY > 480);
  };
  addEventListener('scroll', onScroll, { passive: true });
  onScroll();
  if (topBtn) topBtn.onclick = () => scrollTo({ top: 0, behavior: 'smooth' });

  const toggleTheme = () => {
    const n = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    root.setAttribute('data-theme', n);
    localStorage.setItem('s21-webzine-theme', n);
  };
  themeBtns.forEach(b => b.addEventListener('click', toggleTheme));

  // Mobile nav drawer
  const nav = document.querySelector('.wz-nav');
  const burger = document.querySelector('.wz-burger, [data-nav-toggle]');
  let backdrop = document.querySelector('.wz-nav-backdrop');
  if (nav && burger) {
    if (!backdrop) {
      backdrop = document.createElement('button');
      backdrop.type = 'button';
      backdrop.className = 'wz-nav-backdrop';
      backdrop.setAttribute('aria-label', 'Close menu');
      document.body.appendChild(backdrop);
    }
    const close = () => {
      nav.classList.remove('open');
      backdrop.classList.remove('show');
      burger.setAttribute('aria-expanded', 'false');
      document.body.style.overflow = '';
    };
    const open = () => {
      nav.classList.add('open');
      backdrop.classList.add('show');
      burger.setAttribute('aria-expanded', 'true');
      document.body.style.overflow = 'hidden';
    };
    burger.addEventListener('click', (e) => {
      e.stopPropagation();
      nav.classList.contains('open') ? close() : open();
    });
    backdrop.addEventListener('click', close);
    nav.querySelectorAll('a').forEach(a => a.addEventListener('click', close));
    addEventListener('keydown', (e) => { if (e.key === 'Escape') close(); });
  }

  // copy buttons
  document.querySelectorAll('[data-copy]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const sel = btn.getAttribute('data-copy');
      const el = document.querySelector(sel);
      const text = el ? el.innerText : btn.getAttribute('data-copy-text') || '';
      try { await navigator.clipboard.writeText(text); }
      catch {
        const ta = document.createElement('textarea');
        ta.value = text; document.body.appendChild(ta); ta.select();
        document.execCommand('copy'); ta.remove();
      }
      const old = btn.textContent;
      btn.textContent = 'Copied';
      setTimeout(() => { btn.textContent = old; }, 1400);
    });
  });

  /* —— Doc web-app: section accordion + search + copy —— */
  const prose = document.getElementById('wzProse');
  if (prose) {
    const headings = [...prose.querySelectorAll(':scope > h2')];
    headings.forEach((h2, i) => {
      const sec = document.createElement('div');
      sec.className = 'wz-sec open';
      sec.dataset.sec = String(i);
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'wz-sec-h';
      btn.setAttribute('aria-expanded', 'true');
      const ico = document.createElement('span');
      ico.className = 'wz-sec-ico';
      ico.setAttribute('aria-hidden', 'true');
      ico.textContent = '+';
      const titleWrap = document.createElement('div');
      titleWrap.appendChild(h2.cloneNode(true));
      btn.appendChild(titleWrap);
      btn.appendChild(ico);
      const body = document.createElement('div');
      body.className = 'wz-sec-b';
      const inner = document.createElement('div');
      inner.className = 'wz-sec-i';
      // move siblings until next h2
      let n = h2.nextSibling;
      const move = [];
      while (n && !(n.nodeType === 1 && n.tagName === 'H2')) {
        move.push(n);
        n = n.nextSibling;
      }
      move.forEach(node => inner.appendChild(node));
      body.appendChild(inner);
      sec.appendChild(btn);
      sec.appendChild(body);
      h2.replaceWith(sec);
      btn.addEventListener('click', () => {
        const on = !sec.classList.contains('open');
        sec.classList.toggle('open', on);
        btn.setAttribute('aria-expanded', on ? 'true' : 'false');
      });
    });

    const setAll = (open) => {
      prose.querySelectorAll('.wz-sec').forEach(sec => {
        sec.classList.toggle('open', open);
        const b = sec.querySelector('.wz-sec-h');
        if (b) b.setAttribute('aria-expanded', open ? 'true' : 'false');
      });
    };
    document.getElementById('wzFoldAll')?.addEventListener('click', () => setAll(false));
    document.getElementById('wzExpandAll')?.addEventListener('click', () => setAll(true));

    document.getElementById('wzCopy')?.addEventListener('click', async () => {
      const text = prose.innerText;
      try { await navigator.clipboard.writeText(text); }
      catch {
        const ta = document.createElement('textarea');
        ta.value = text; document.body.appendChild(ta); ta.select();
        document.execCommand('copy'); ta.remove();
      }
      const btn = document.getElementById('wzCopy');
      if (btn) { const o = btn.textContent; btn.textContent = 'Copied'; setTimeout(() => btn.textContent = o, 1200); }
    });

    const search = document.getElementById('wzSearch');
    search?.addEventListener('input', () => {
      const q = search.value.trim().toLowerCase();
      // clear marks
      prose.querySelectorAll('mark.wz-hit').forEach(m => {
        const t = document.createTextNode(m.textContent);
        m.replaceWith(t);
      });
      prose.normalize();
      if (!q) {
        prose.querySelectorAll('.wz-sec').forEach(s => s.classList.remove('wz-hide'));
        return;
      }
      prose.querySelectorAll('.wz-sec').forEach(sec => {
        const text = sec.innerText.toLowerCase();
        const hit = text.includes(q);
        sec.classList.toggle('wz-hide', !hit);
        if (hit) {
          sec.classList.add('open');
          sec.querySelector('.wz-sec-h')?.setAttribute('aria-expanded', 'true');
        }
      });
    });
  }

})();