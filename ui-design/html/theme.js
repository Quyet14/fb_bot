// theme.js — source of truth duy nhất cho light/dark toggle
// Load sớm nhất, trước mọi script khác

const THEME_KEY = 'fbbot-theme';

function _applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  try { localStorage.setItem(THEME_KEY, theme); } catch (_) {}
}

function _currentTheme() {
  return document.documentElement.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
}

// Áp dụng theme từ localStorage, mặc định là light
(function () {
  try {
    const saved = localStorage.getItem(THEME_KEY);
    _applyTheme(saved === 'dark' ? 'dark' : 'light');
  } catch (_) {
    _applyTheme('light');
  }
})();

function _applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  try { localStorage.setItem(THEME_KEY, theme); } catch (_) {}
}

function _currentTheme() {
  return document.documentElement.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
}

// Hàm toggle duy nhất — tất cả nơi gọi đều dùng cái này
window.toggleTheme = function () {
  const next = _currentTheme() === 'light' ? 'dark' : 'light';
  _applyTheme(next);
  // Sync tất cả toggle buttons trên trang
  _syncAllThemeButtons(next);
};

function _syncAllThemeButtons(theme) {
  const isLight = theme === 'light';
  const lang = localStorage.getItem('fbbot-lang') || 'vi';

  // Settings toggle switch
  const ico = document.querySelector('#themeToggleSwitch .tts-icon');
  const lbl = document.getElementById('themeLabel');
  if (ico) ico.textContent = isLight ? '☀️' : '🌙';
  if (lbl) {
    lbl.textContent = isLight
      ? (lang === 'en' ? 'Light mode' : 'Chế độ sáng')
      : (lang === 'en' ? 'Dark mode'  : 'Chế độ tối');
  }
}

// Sync ngay khi DOM sẵn sàng
document.addEventListener('DOMContentLoaded', () => {
  _syncAllThemeButtons(_currentTheme());
});
