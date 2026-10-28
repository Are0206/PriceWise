// Quick "Agregar a lista": saves in the background so the shopper keeps their
// place in the catalog. Without JavaScript the forms still post and reload.
(() => {
  const status = document.createElement('p');
  status.className = 'visually-hidden';
  status.setAttribute('role', 'status');
  document.body.append(status);

  document.addEventListener('submit', async (event) => {
    const form = event.target.closest('.add-to-list-form');
    if (!form) return;
    event.preventDefault();

    const button = form.querySelector('button');
    const label = button.textContent;
    button.disabled = true;
    try {
      const response = await fetch(form.action, {
        method: 'POST',
        body: new FormData(form),
        headers: { 'X-Requested-With': 'fetch' },
      });
      if (!response.ok) throw new Error(response.status);
      const data = await response.json();
      status.textContent = data.message;
      button.textContent = `Agregado (${data.quantity})`;
      button.classList.add('is-added');
      setTimeout(() => {
        button.textContent = label;
        button.classList.remove('is-added');
        form.closest('details').open = false;
      }, 1200);
    } catch (error) {
      status.textContent = 'No se pudo agregar el producto. Intenta de nuevo.';
      button.textContent = 'Error, reintenta';
      setTimeout(() => { button.textContent = label; }, 1800);
    } finally {
      button.disabled = false;
    }
  });

  // Only one menu open at a time; Escape or a click outside closes it.
  const closeMenus = (except) => {
    document.querySelectorAll('.add-to-list[open]').forEach((menu) => {
      if (menu !== except) menu.open = false;
    });
  };
  document.addEventListener('toggle', (event) => {
    if (event.target.matches?.('.add-to-list') && event.target.open) closeMenus(event.target);
  }, true);
  document.addEventListener('click', (event) => {
    if (!event.target.closest('.add-to-list')) closeMenus();
  });
  document.addEventListener('keydown', (event) => {
    if (event.key !== 'Escape') return;
    const open = document.querySelector('.add-to-list[open]');
    if (open) {
      open.open = false;
      open.querySelector('summary').focus();
    }
  });
})();
