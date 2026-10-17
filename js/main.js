(() => {
  const doc = document.documentElement;
  const nav = document.getElementById('nav');
  const toggle = document.getElementById('navToggle');
  const menu = document.getElementById('navMenu');
  const links = [...document.querySelectorAll('.nav__list a')];

  document.getElementById('year').textContent = new Date().getFullYear();

  // Menú móvil
  const setMenu = (open) => {
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? 'Cerrar menú de navegación' : 'Abrir menú de navegación');
    menu.classList.toggle('is-open', open);
  };
  toggle.addEventListener('click', () => setMenu(toggle.getAttribute('aria-expanded') !== 'true'));
  links.forEach((a) => a.addEventListener('click', () => setMenu(false)));
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && menu.classList.contains('is-open')) { setMenu(false); toggle.focus(); }
  });
  matchMedia('(min-width: 1121px)').addEventListener('change', (e) => e.matches && setMenu(false));

  // Estilo de la barra al hacer scroll
  const onScroll = () => nav.classList.toggle('is-scrolled', window.scrollY > 12);
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });

  // Revelado suave
  const items = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) { entry.target.classList.add('is-visible'); io.unobserve(entry.target); }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -6% 0px' });
    items.forEach((el) => {
      const siblings = el.parentElement ? [...el.parentElement.children].filter((c) => c.classList.contains('reveal')) : [];
      el.style.setProperty('--d', `${Math.min(siblings.indexOf(el), 5) * 70}ms`);
      io.observe(el);
    });
  } else {
    items.forEach((el) => el.classList.add('is-visible'));
  }

  // Enlace activo según la sección visible
  const map = new Map(links.filter((a) => a.getAttribute('href').startsWith('#')).map((a) => [a.getAttribute('href').slice(1), a]));
  const sections = [...map.keys()].map((id) => document.getElementById(id)).filter(Boolean);
  const spy = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      links.forEach((a) => a.classList.remove('is-active'));
      map.get(entry.target.id)?.classList.add('is-active');
    });
  }, { rootMargin: '-45% 0px -50% 0px' });
  sections.forEach((s) => spy.observe(s));

  // Menú de WhatsApp: en escritorio permite elegir Web o aplicación; en móvil el enlace wa.me funciona directo
  const WA_PHONE = '573107153466';
  const WA_TEXT = encodeURIComponent('Hola, Jesús. Vi tu portafolio y me gustaría ponerme en contacto contigo.');
  const desktop = matchMedia('(hover: hover) and (pointer: fine)');
  let openMenu = null;

  const closeMenu = (returnFocus) => {
    if (!openMenu) return;
    const { menu: m, trigger, wrap } = openMenu;
    m.hidden = true;
    trigger.setAttribute('aria-expanded', 'false');
    wrap.classList.remove('is-menu-open');
    if (returnFocus) trigger.focus();
    openMenu = null;
  };

  document.querySelectorAll('[data-wa-wrap]').forEach((wrap, i) => {
    const trigger = wrap.querySelector('[data-wa]');
    const menu = document.createElement('div');
    menu.className = 'wa-menu';
    menu.id = `waMenu${i}`;
    menu.hidden = true;
    menu.setAttribute('role', 'group');
    menu.setAttribute('aria-label', 'Opciones para abrir WhatsApp');
    menu.innerHTML = `
      <p class="wa-menu__title">Contactar por WhatsApp</p>
      <a href="https://web.whatsapp.com/send?phone=${WA_PHONE}&text=${WA_TEXT}" target="_blank" rel="noopener noreferrer">Continuar en WhatsApp Web<small>Se abre en el navegador</small></a>
      <a href="https://wa.me/${WA_PHONE}?text=${WA_TEXT}" target="_blank" rel="noopener noreferrer">Abrir WhatsApp<small>Intenta abrir la aplicación instalada</small></a>`;
    wrap.appendChild(menu);
    trigger.setAttribute('aria-haspopup', 'true');
    trigger.setAttribute('aria-expanded', 'false');
    trigger.setAttribute('aria-controls', menu.id);

    trigger.addEventListener('click', (e) => {
      if (!desktop.matches) return; // móvil: sigue el enlace wa.me
      e.preventDefault();
      if (openMenu && openMenu.menu === menu) { closeMenu(); return; }
      closeMenu();
      menu.hidden = false;
      trigger.setAttribute('aria-expanded', 'true');
      wrap.classList.add('is-menu-open');
      openMenu = { menu, trigger, wrap };
      menu.querySelector('a').focus();
    });
    menu.querySelectorAll('a').forEach((a) => a.addEventListener('click', () => closeMenu()));
  });

  document.addEventListener('click', (e) => { if (openMenu && !openMenu.wrap.contains(e.target)) closeMenu(); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeMenu(true); });
})();
