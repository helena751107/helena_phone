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
})();
