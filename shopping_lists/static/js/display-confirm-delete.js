document.addEventListener('DOMContentLoaded', () => {
  const openDeleteBtn = document.getElementById('open-delete-card');
  const overlay = document.getElementById('card-overlay');
  const bodyContent = document.getElementById('card-body-content');

  // 1. Abrir panel de Delete
  if (openDeleteBtn) {
    openDeleteBtn.addEventListener('click', () => {
      loadDeleteCard(openDeleteBtn.dataset.url);
    });
  }

  async function loadDeleteCard(url) {
    try {
      const response = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
      if (!response.ok) throw new Error("Error loading delete card");

      bodyContent.innerHTML = await response.text();
      overlay.classList.add('active');
    } catch (error) {
      console.error(error);
    }
  }
});