const root = document.documentElement;
const langBtn = document.getElementById('langBtn');
const menuBtn = document.getElementById('menuBtn');
const mobileMenu = document.getElementById('mobileMenu');
let lang = localStorage.getItem('vs-lang') || 'tr';

function setDetailLanguage(next) {
  lang = next;
  root.lang = next;
  document.querySelectorAll('[data-tr][data-en]').forEach(el => {
    el.textContent = next === 'tr' ? el.dataset.tr : el.dataset.en;
  });
  if (langBtn) langBtn.textContent = next === 'tr' ? 'EN' : 'TR';
  localStorage.setItem('vs-lang', next);
}
setDetailLanguage(lang);
if (langBtn) langBtn.addEventListener('click', () => setDetailLanguage(lang === 'tr' ? 'en' : 'tr'));

function closeMenu() {
  if (!menuBtn || !mobileMenu) return;
  menuBtn.classList.remove('active');
  mobileMenu.classList.remove('open');
  menuBtn.setAttribute('aria-expanded', 'false');
  mobileMenu.setAttribute('aria-hidden', 'true');
  document.body.classList.remove('menu-open');
}
if (menuBtn && mobileMenu) {
  menuBtn.addEventListener('click', () => {
    const open = !mobileMenu.classList.contains('open');
    menuBtn.classList.toggle('active', open);
    mobileMenu.classList.toggle('open', open);
    menuBtn.setAttribute('aria-expanded', String(open));
    mobileMenu.setAttribute('aria-hidden', String(!open));
    document.body.classList.toggle('menu-open', open);
  });
  mobileMenu.querySelectorAll('a').forEach(a => a.addEventListener('click', closeMenu));
}

const io = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      io.unobserve(entry.target);
    }
  });
}, { threshold: 0.1 });
document.querySelectorAll('.reveal').forEach(el => io.observe(el));

const year = document.getElementById('year');
if (year) year.textContent = new Date().getFullYear();

const glow = document.querySelector('.cursor-glow');
if (glow) window.addEventListener('pointermove', e => {
  glow.style.left = `${e.clientX}px`;
  glow.style.top = `${e.clientY}px`;
}, { passive: true });

const lightbox = document.getElementById('lightbox');
const lightboxImg = lightbox?.querySelector('img');
const lightboxClose = lightbox?.querySelector('.lightbox-close');
function closeLightbox() {
  if (!lightbox) return;
  lightbox.classList.remove('open');
  document.body.style.overflow = '';
  if (lightboxImg) lightboxImg.src = '';
}
document.querySelectorAll('.screenshot-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const img = btn.querySelector('img');
    if (!lightbox || !lightboxImg || !img) return;
    lightboxImg.src = img.src;
    lightboxImg.alt = img.alt;
    lightbox.classList.add('open');
    document.body.style.overflow = 'hidden';
  });
});
if (lightboxClose) lightboxClose.addEventListener('click', closeLightbox);
if (lightbox) lightbox.addEventListener('click', e => { if (e.target === lightbox) closeLightbox(); });
window.addEventListener('keydown', e => { if (e.key === 'Escape') closeLightbox(); });
