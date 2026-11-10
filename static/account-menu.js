const accountMenu = document.querySelector('.account-menu');
if (accountMenu) {
  const trigger = accountMenu.querySelector('summary');
  accountMenu.addEventListener('toggle', () => {
    trigger.setAttribute('aria-expanded', String(accountMenu.open));
  });
  document.addEventListener('click', (event) => {
    if (accountMenu.open && !accountMenu.contains(event.target)) accountMenu.open = false;
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && accountMenu.open) {
      accountMenu.open = false;
      trigger.focus();
    }
  });
  accountMenu.addEventListener('focusout', (event) => {
    if (event.relatedTarget && !accountMenu.contains(event.relatedTarget)) accountMenu.open = false;
  });
}
