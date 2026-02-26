document.addEventListener('DOMContentLoaded', () => {
  const uiMenuBtn = document.getElementById('uiMenuBtn');
  const uiDropdown = document.getElementById('uiDropdown');
  const uiDarkBtn = document.getElementById('uiDarkBtn');
  const uiContrastBtn = document.getElementById('uiContrastBtn');
  const uiDarkState = document.getElementById('uiDarkState');
  const uiContrastState = document.getElementById('uiContrastState');
  const fontBtns = document.querySelectorAll('.ui-font-btn');

  if (!uiMenuBtn || !uiDropdown) return;

  const LS_THEME = 'ui_theme';
  const LS_FONT  = 'ui_font';

  // ✅ 1) ФУНКЦИЯ СМЕНЫ ЛОГО
  function updateLogo() {
    const logo = document.getElementById('siteLogo');
    if (!logo) return;

    if (document.body.classList.contains('theme-contrast')) {
      logo.src = "/static/images/StudentAppW.png";
    } else if (document.body.classList.contains('theme-dark')) {
      logo.src = "/static/images/StudentAppW.png";
    } else {
      logo.src = "/static/images/StudentApp.png";
    }
  }

  function setTheme(theme) {
    document.body.classList.remove('theme-dark', 'theme-contrast');
    if (theme === 'dark') document.body.classList.add('theme-dark');
    if (theme === 'contrast') document.body.classList.add('theme-contrast');
    localStorage.setItem(LS_THEME, theme || '');
    if (uiDarkState) uiDarkState.textContent = theme === 'dark' ? 'ON' : 'OFF';
    if (uiContrastState) uiContrastState.textContent = theme === 'contrast' ? 'ON' : 'OFF';

    updateLogo(); // ✅ 2) МЕНЯЕМ ЛОГО ПРИ СМЕНЕ ТЕМЫ
  }

  function setFont(size) {
    document.body.classList.remove('font-lg', 'font-xl');
    if (size === 'lg') document.body.classList.add('font-lg');
    if (size === 'xl') document.body.classList.add('font-xl');
    localStorage.setItem(LS_FONT, size || 'normal');
  }

  function closeUiMenu() {
    uiDropdown.style.display = 'none';
    uiMenuBtn.setAttribute('aria-expanded', 'false');
  }

  function toggleUiMenu() {
    const isOpen = uiDropdown.style.display === 'block';
    uiDropdown.style.display = isOpen ? 'none' : 'block';
    uiMenuBtn.setAttribute('aria-expanded', isOpen ? 'false' : 'true');
  }

  uiMenuBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    toggleUiMenu();
  });

  document.addEventListener('click', (e) => {
    if (!uiDropdown.contains(e.target) && !uiMenuBtn.contains(e.target)) closeUiMenu();
  });

  if (uiDarkBtn) uiDarkBtn.addEventListener('click', () => {
    setTheme(document.body.classList.contains('theme-dark') ? '' : 'dark');
  });

  if (uiContrastBtn) uiContrastBtn.addEventListener('click', () => {
    setTheme(document.body.classList.contains('theme-contrast') ? '' : 'contrast');
  });

  fontBtns.forEach(btn => {
    btn.addEventListener('click', () => setFont(btn.dataset.font));
  });

  setTheme(localStorage.getItem(LS_THEME) || '');
  setFont(localStorage.getItem(LS_FONT) || 'normal');

  updateLogo(); // ✅ 3) ПРИ ЗАГРУЗКЕ СРАЗУ ВЫСТАВИТЬ ПРАВИЛЬНОЕ ЛОГО
});