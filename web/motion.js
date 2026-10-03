export default function ({data}) {
  // Animate real page changes only. Saving a form must not replay the whole page.
  let disposed = false, context, timer;
  const semantics = () => {
    const nav = document.querySelector('.st-key-navigation');
    if (nav) { nav.setAttribute('role','navigation'); nav.setAttribute('aria-label','Your diary'); }
    document.querySelectorAll('.st-key-navigation a').forEach(link => {
      if (link.textContent.trim().endsWith(data.route)) link.setAttribute('aria-current','page');
      else link.removeAttribute('aria-current');
    });
    // Streamlit 1.64 exposes popup state on a generic date-field div. Supply
    // the missing composite role while preserving its native keyboard editor.
    document.querySelectorAll('[data-testid="stDateInputField"]:not([role])').forEach(field => {
      field.setAttribute('role','combobox');
      field.setAttribute('aria-label',field.querySelector('[role="group"][aria-label]')?.getAttribute('aria-label') || 'Diary date');
    });
  };
  semantics();
  const observer = new MutationObserver(semantics);
  observer.observe(document.querySelector('[data-testid="stMainBlockContainer"]'), {childList:true,subtree:true});
  const preference = matchMedia('(prefers-reduced-motion: reduce)');
  if (preference.matches || window.__steadyAnimatedRoute === data.route) return () => observer.disconnect();
  window.__steadyAnimatedRoute = data.route;
  const cloud = location.pathname.indexOf('/~/+/');
  const prefix = cloud >= 0 ? location.pathname.slice(0,cloud+5)
    : location.pathname.startsWith('/streamlit/') ? '/streamlit/' : '/';
  const run = () => {
    if (disposed || preference.matches || !window.gsap) return;
    const main = document.querySelector('[data-testid="stMainBlockContainer"]');
    if (!main) return;
    const cards = main.querySelectorAll('.st-key-welcome, .st-key-page-heading, .st-key-today-stats, .st-key-next-steps, .st-key-food-layout, .st-key-move-layout, .st-key-buddy-choice, .st-key-progress-stats, .st-key-settings-layout');
    context = window.gsap.context(() => {
      window.gsap.from(cards, {y:12, opacity:.4, duration:.55, stagger:.07, ease:'power2.out', clearProps:'all'});
    }, main);
  };
  if (window.gsap) timer = setTimeout(run,70);
  else {
    if (!window.__steadyGSAP) {
      window.__steadyGSAP = new Promise((resolve,reject) => {
        const script = document.createElement('script');
        script.src = new URL(prefix+'app/static/vendor/gsap.min.js',location.origin).href;
        script.onload = () => resolve(window.gsap);
        script.onerror = () => { script.remove(); window.__steadyGSAP=null; reject(new Error('Motion asset unavailable')); };
        document.head.append(script);
      });
    }
    window.__steadyGSAP.then(() => { timer=setTimeout(run,70); }).catch(() => {});
  }
  const stop = () => { if (preference.matches) context?.revert(); };
  preference.addEventListener('change',stop);
  return () => { disposed=true; clearTimeout(timer); context?.revert(); observer.disconnect(); preference.removeEventListener('change',stop); };
}
