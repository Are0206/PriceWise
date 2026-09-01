document.addEventListener('DOMContentLoaded', () => {
  const openBtn = document.getElementById('open-share-card');
  const cardOverlay = document.getElementById('share-card-overlay');
  const cardBody = document.getElementById('share-card-body-content');

  if (openBtn) {
    openBtn.addEventListener('click', () => {
      loadShareCard(openBtn.dataset.url);
    });
  }

  async function loadShareCard(url) {
    try {
      const response = await fetch(url, {
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      });

      if (!response.ok) {
        throw new Error("Error loading share card");
      }

      const html = await response.text();
      cardBody.innerHTML = html;
      cardOverlay.classList.add('active');
    } catch (error) {
      console.error(error);
    }
  }

  cardBody.addEventListener('click', (e) => {
    const closeBtn = e.target.closest('.btn-close');
    if (closeBtn) {
      cardOverlay.classList.remove('active');
      return;
    }

    const permissionLink = e.target.closest('.share-permissions-div a');
    if (permissionLink) {
      e.preventDefault();
      loadShareCard(permissionLink.href);
      return;
    }

    const copyBtn = e.target.closest('#copy-btn');
    if (copyBtn) {
      const linkInput = cardBody.querySelector('#share-link-input');
      if (linkInput) {
        linkInput.select();
        linkInput.setSelectionRange(0, 99999);
        navigator.clipboard.writeText(linkInput.value);
      }
    }
  });

  cardOverlay.addEventListener('click', (e) => {
    if (e.target === cardOverlay) {
      cardOverlay.classList.remove('active');
    }
  });
});