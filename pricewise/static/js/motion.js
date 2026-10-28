// Two authored moments; every other interaction stays instant.
// Nothing runs for people who ask the OS to reduce motion.
(() => {
  if (!window.gsap) return;

  const moneyFormat = new Intl.NumberFormat('es-CO', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  gsap.matchMedia().add('(prefers-reduced-motion: no-preference)', () => {
    // Catalog: cards rise in once per visit. Filters and searches reload the
    // page, so replaying it on every click would slow the shopper down.
    const cards = gsap.utils.toArray('.products-grid .product-card');
    let seen = true;
    try {
      seen = sessionStorage.getItem('pw-catalog-seen') === '1';
      sessionStorage.setItem('pw-catalog-seen', '1');
    } catch (e) { /* storage blocked: skip the entrance */ }
    if (cards.length && !seen) {
      gsap.from(cards.slice(0, 12), {
        y: 14, autoAlpha: 0, duration: 0.55, ease: 'expo.out', stagger: 0.04, clearProps: 'all',
      });
    }

    // Shopping list: the estimated savings counts up to its value.
    gsap.utils.toArray('[data-count-to]').forEach((el) => {
      const finalText = el.textContent;
      const counter = { value: 0 };
      gsap.to(counter, {
        value: parseFloat(el.dataset.countTo),
        duration: 0.9,
        ease: 'expo.out',
        onUpdate: () => { el.textContent = '$' + moneyFormat.format(counter.value); },
        onComplete: () => { el.textContent = finalText; },
      });
    });
  });
})();
