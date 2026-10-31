// On phones the filters start folded unless one is active; on desktop they stay open.
(function () {
  const panel = document.querySelector('.filters-panel');
  if (!panel) return;
  const phone = window.matchMedia('(max-width: 900px)');
  const sync = () => {
    panel.open = !phone.matches || panel.dataset.hasFilters === 'true';
  };
  sync();
  phone.addEventListener('change', sync);
})();
