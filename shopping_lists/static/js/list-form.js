// Adds an empty product row to the shopping list formset and focuses it.
(function () {
  const container = document.getElementById('items-container');
  const template = document.getElementById('empty-form-template');
  const addButton = document.getElementById('add-item');
  if (!container || !template || !addButton) return;
  const totalForms = document.getElementById(addButton.dataset.totalForms);

  addButton.addEventListener('click', function () {
    const index = parseInt(totalForms.value, 10);
    container.insertAdjacentHTML('beforeend', template.innerHTML.replace(/__prefix__/g, index));
    totalForms.value = index + 1;
    container.lastElementChild.querySelector('select')?.focus();
  });
})();
