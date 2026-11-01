// Tooltip for the price history chart: shows a point's value on hover or keyboard focus.
(function () {
  const chart = document.querySelector('.history-chart');
  if (!chart) return;
  const tooltip = chart.querySelector('.history-tooltip');

  const show = (point) => {
    tooltip.textContent = point.dataset.label;
    const box = point.getBoundingClientRect();
    const frame = chart.getBoundingClientRect();
    tooltip.style.left = `${box.left - frame.left + box.width / 2}px`;
    tooltip.style.top = `${box.top - frame.top}px`;
    tooltip.hidden = false;
  };
  const hide = () => { tooltip.hidden = true; };

  chart.querySelectorAll('circle[data-label]').forEach((point) => {
    point.addEventListener('mouseenter', () => show(point));
    point.addEventListener('focus', () => show(point));
    point.addEventListener('mouseleave', hide);
    point.addEventListener('blur', hide);
  });
})();
