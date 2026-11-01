// Opens the share / delete cards of a shopping list in a native <dialog>.
// showModal() traps focus, makes the page behind inert and closes on Escape.
document.addEventListener('DOMContentLoaded', () => {
  const dialog = document.getElementById('card-dialog');
  const body = document.getElementById('card-body-content');
  if (!dialog || !body) return;
  let opener = null;

  const errorCard = `
    <div class="delete-wrapper">
      <h2 class="delete-title" id="card-title">No se pudo abrir</h2>
      <p class="delete-text">Revisa tu conexión e inténtalo de nuevo.</p>
      <div class="delete-buttons-div"><button type="button" class="btn btn--outline btn-close">Cerrar</button></div>
    </div>`;

  document.querySelectorAll('[data-card-url]').forEach((link) => {
    link.addEventListener('click', async (event) => {
      event.preventDefault();
      opener = link;
      try {
        const response = await fetch(link.dataset.cardUrl, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        body.innerHTML = await response.text();
      } catch (error) {
        console.error(error);
        body.innerHTML = errorCard;
      }
      dialog.showModal();
      body.querySelector('.btn-close')?.focus();
    });
  });

  // Return focus to the button that opened the card.
  dialog.addEventListener('close', () => opener?.focus());

  dialog.addEventListener('click', async (event) => {
    // A click on the backdrop lands on the dialog element itself.
    if (event.target === dialog) {
      dialog.close();
      return;
    }
    if (event.target.closest('.btn-close')) {
      event.preventDefault();
      dialog.close();
      return;
    }
    const copyButton = event.target.closest('#copy-btn');
    if (copyButton) {
      const input = body.querySelector('#share-link-input');
      const status = body.querySelector('#copy-status');
      try {
        await navigator.clipboard.writeText(input.value);
        copyButton.textContent = '¡Copiado!';
        if (status) status.textContent = 'El enlace quedó copiado.';
      } catch (error) {
        // Clipboard access can be blocked; leave the link selected so it can be copied by hand.
        input.select();
        if (status) status.textContent = 'No se pudo copiar automáticamente. El enlace quedó seleccionado: cópialo con Ctrl+C o Cmd+C.';
      }
      setTimeout(() => { copyButton.textContent = 'Copiar'; }, 2500);
    }
  });
});
