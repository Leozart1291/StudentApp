
  const profileBtn = document.getElementById("profileBtn");
  const dropdownMenu = document.getElementById("dropdownMenu");

  if (profileBtn) {
    profileBtn.addEventListener("click", () => {
      dropdownMenu.classList.toggle("show");
    });

    window.addEventListener("click", (e) => {
      if (!profileBtn.contains(e.target)) {
        dropdownMenu.classList.remove("show");
      }
    });
  }


(function () {
  const btn = document.getElementById('uiMenuBtn');
  const menu = document.getElementById('uiDropdown');

  const darkBtn = document.getElementById('uiDarkBtn');
  const contrastBtn = document.getElementById('uiContrastBtn');

  const darkState = document.getElementById('uiDarkState');
  const contrastState = document.getElementById('uiContrastState');

  const fontBtns = document.querySelectorAll('.ui-font-btn');

  if (!btn || !menu) return;

  const save = (k, v) => localStorage.setItem(k, String(v));
  const load = (k, d) => (localStorage.getItem(k) ?? d);

  function setExpanded(isOpen){
    btn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
  }

  function openMenu(){
    menu.style.display = 'block';
    setExpanded(true);
  }

  function closeMenu(){
    menu.style.display = 'none';
    setExpanded(false);
  }

  btn.addEventListener('click', (e) => {
    e.stopPropagation();
    const isOpen = menu.style.display === 'block';
    isOpen ? closeMenu() : openMenu();
  });

  document.addEventListener('click', () => closeMenu());

  function applyStates(){
    const isDark = document.body.classList.contains('theme-dark');
    const isContrast = document.body.classList.contains('theme-contrast');

    darkState.textContent = isDark ? 'ON' : 'OFF';
    contrastState.textContent = isContrast ? 'ON' : 'OFF';
  }

  // load saved
  const savedDark = load('ui_dark', '0') === '1';
  const savedContrast = load('ui_contrast', '0') === '1';
  const savedFont = load('ui_font', 'normal'); // normal|lg|xl

  if (savedContrast) {
    document.body.classList.add('theme-contrast');
    document.body.classList.remove('theme-dark');
  } else if (savedDark) {
    document.body.classList.add('theme-dark');
  }

  document.body.classList.remove('font-lg', 'font-xl');
  if (savedFont === 'lg') document.body.classList.add('font-lg');
  if (savedFont === 'xl') document.body.classList.add('font-xl');

  applyStates();

  // dark toggle
  darkBtn?.addEventListener('click', () => {
    // если включен контраст — сначала выключаем контраст
    if (document.body.classList.contains('theme-contrast')) {
      document.body.classList.remove('theme-contrast');
      save('ui_contrast', '0');
    }

    const on = !document.body.classList.contains('theme-dark');
    document.body.classList.toggle('theme-dark', on);
    save('ui_dark', on ? '1' : '0');
    applyStates();
    updateHeroImage();
  });

  // contrast toggle (жёсткий режим)
  contrastBtn?.addEventListener('click', () => {
    const on = !document.body.classList.contains('theme-contrast');
    document.body.classList.toggle('theme-contrast', on);

    // контраст главнее: темный выключаем
    if (on) {
      document.body.classList.remove('theme-dark');
      save('ui_dark', '0');
    }

    save('ui_contrast', on ? '1' : '0');
    applyStates();
    updateHeroImage();
  });

  // font
  fontBtns.forEach(b => {
    b.addEventListener('click', () => {
      const mode = b.getAttribute('data-font') || 'normal';
      document.body.classList.remove('font-lg', 'font-xl');
      if (mode === 'lg') document.body.classList.add('font-lg');
      if (mode === 'xl') document.body.classList.add('font-xl');
      save('ui_font', mode);
    });
  });

})();



  // =======================
// HERO IMAGE SWITCH
// =======================

function updateHeroImage() {
  const heroImg = document.getElementById('heroImage');
  if (!heroImg) return;

  const isContrast = document.body.classList.contains('theme-contrast');
  const isDark = document.body.classList.contains('theme-dark');

  if (isContrast) {
    heroImg.src = "/static/images/hero_contrast.png";
  } else if (isDark) {
    heroImg.src = "/static/images/hero_dark.png";
  } else {
    heroImg.src = "/static/images/hero_light.png";
  }
}
