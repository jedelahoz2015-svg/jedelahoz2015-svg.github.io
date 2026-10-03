const toggle = document.querySelector('.menu-toggle');
const nav = document.querySelector('.nav-links');
function closeMenu(returnFocus = false) {
 toggle.setAttribute('aria-expanded', 'false');
 toggle.setAttribute('aria-label', 'Abrir menú');
 nav.classList.remove('is-open');
 if (returnFocus) toggle.focus();
}
toggle.addEventListener('click', () => {
 const open = toggle.getAttribute('aria-expanded') !== 'true';
 toggle.setAttribute('aria-expanded', String(open));
 toggle.setAttribute('aria-label', open ? 'Cerrar menú' : 'Abrir menú');
 nav.classList.toggle('is-open', open);
});
nav.addEventListener('click', event => {if(event.target.closest('a')) closeMenu();});
document.addEventListener('keydown', event => {if(event.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') closeMenu(true);});
document.addEventListener('click', event => {if(!event.target.closest('.nav')) closeMenu();});
matchMedia('(min-width: 1051px)').addEventListener('change', () => closeMenu());
document.getElementById('year').textContent = new Date().getFullYear();
if ('IntersectionObserver' in window) {
 const observer = new IntersectionObserver(entries => entries.forEach(entry => {
  if(entry.isIntersecting) {entry.target.classList.add('visible'); observer.unobserve(entry.target);}
 }), {threshold: .08});
 document.querySelectorAll('.reveal').forEach(el => {el.classList.add('will-reveal');observer.observe(el);});
 const sections = new IntersectionObserver(entries => entries.forEach(entry => {
  if(entry.isIntersecting) document.querySelectorAll('.nav-links a').forEach(a => {
   if(a.hash === `#${entry.target.id}`) a.setAttribute('aria-current','location'); else a.removeAttribute('aria-current');
  });
 }), {rootMargin:'-15% 0px -65% 0px'});
 document.querySelectorAll('main section[id]').forEach(el=>sections.observe(el));
}
