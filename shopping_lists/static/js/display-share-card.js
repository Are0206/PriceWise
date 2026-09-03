document.addEventListener('DOMContentLoaded', () => {
  const openShareBtn = document.getElementById('open-share-card');
  const overlay = document.getElementById('card-overlay');
  const bodyContent = document.getElementById('card-body-content');

  //Abrir panel de Share
  if (openShareBtn) {
    openShareBtn.addEventListener('click', () => {
      loadShareCard(openShareBtn.dataset.url);
    });
  }

  async function loadShareCard(url) {
    try {
      const response = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
      if (!response.ok) throw new Error("Error loading share card");

      bodyContent.innerHTML = await response.text();
      overlay.classList.add('active');
    } catch (error) {
      console.error(error);
    }
  }

  //Lógica interna de la tarjeta Share
  if (bodyContent) {
    bodyContent.addEventListener('click', (e) => {

      // Cambiar permisos
      const permissionLink = e.target.closest('.share-permissions-div a');
      if (permissionLink) {
        e.preventDefault();
        loadShareCard(permissionLink.href);
      }

      // Copiar link
      const copyBtn = e.target.closest('#copy-btn');
      if (copyBtn) {
        const linkInput = bodyContent.querySelector('#share-link-input');
        if (linkInput) {
          linkInput.select();
          linkInput.setSelectionRange(0, 99999);
          navigator.clipboard.writeText(linkInput.value);
        }
      }
    });
  }

  //Cerrar al hacer clic en el fondo o en un botón de cerrar
  document.addEventListener('click', (e) => {
    if (e.target === overlay || e.target.closest('.btn-close')) {
      overlay.classList.remove('active');
    }
  });
});