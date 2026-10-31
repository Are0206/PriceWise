// Turns the stacked Wrapped cards into stories: one card at a time.
// Without this script every card stays visible, one below the other.
(function () {
  const root = document.getElementById('wrapped');
  if (!root) return;
  const cards = [...root.querySelectorAll('.wrapped-card')];
  const progress = root.querySelector('.wrapped-progress');
  if (cards.length < 2) return;

  root.classList.add('wrapped--stories');
  const bars = cards.map(() => progress.appendChild(document.createElement('span')));
  let current = 0;

  const show = (index) => {
    current = Math.max(0, Math.min(cards.length - 1, index));
    cards.forEach((card, i) => {
      card.classList.toggle('is-current', i === current);
      card.toggleAttribute('hidden', i !== current);
    });
    bars.forEach((bar, i) => bar.classList.toggle('is-done', i <= current));
    cards[current].querySelector('h2')?.focus({ preventScroll: true });
  };

  root.addEventListener('click', (event) => {
    if (event.target.closest('a, button')) return;
    const box = root.getBoundingClientRect();
    show(event.clientX - box.left < box.width / 3 ? current - 1 : current + 1);
  });

  const panel = document.getElementById('shoppingListPanel');

  document.addEventListener('keydown', (event) => {
    // Leave keys alone while the user types in the search bar, presses a control,
    // or has the lists panel open (its own Escape closes it).
    if (event.defaultPrevented) return;
    if (event.target.closest?.('input, select, textarea, button, a, [contenteditable]')) return;
    if (panel && !panel.inert) return;
    if (event.key === 'ArrowRight' || event.key === ' ') {
      event.preventDefault();
      show(current + 1);
    } else if (event.key === 'ArrowLeft') {
      event.preventDefault();
      show(current - 1);
    } else if (event.key === 'Escape') {
      window.location.href = '/?open_lists=true';
    }
  });

  show(0);
})();
