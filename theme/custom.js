(function () {
  function normalizeName(label) {
    if (!label) {
      return '';
    }
    return label.replace(/\s+info$/, '').trim();
  }

  function applyItemNames() {
    const cards = document.querySelectorAll("[role='listitem'].card");
    for (const card of cards) {
      const button = card.querySelector('button[aria-label], div[aria-label]');
      if (!button) {
        continue;
      }

      const name = normalizeName(button.getAttribute('aria-label') || card.getAttribute('aria-label'));
      if (!name) {
        continue;
      }

      button.classList.add('bub-item-button');

      let label = card.querySelector('.bub-item-name');
      if (!label) {
        label = document.createElement('div');
        label.className = 'bub-item-name';
        card.appendChild(label);
      }

      if (label.textContent !== name) {
        label.textContent = name;
      }

      card.setAttribute('data-bub-name-ready', '1');
    }
  }

  const observer = new MutationObserver(applyItemNames);

  function start() {
    applyItemNames();
    observer.observe(document.body, { childList: true, subtree: true });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start, { once: true });
  } else {
    start();
  }
})();
