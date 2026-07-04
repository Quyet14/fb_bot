// Light/dark theme toggle.
// The actual theme is applied as early as possible by a tiny inline
// script in <head> (before CSS loads) to avoid a flash of the wrong
// theme. This file only wires up the visible toggle button.

const THEME_KEY = 'fbbot-theme';

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  try {
    localStorage.setItem(THEME_KEY, theme);
  } catch (error) {
    // localStorage may be unavailable (private mode, etc.) — theme
    // still applies for this page load, it just won't persist.
  }
}

function currentTheme() {
  return document.documentElement.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
}

function syncToggleLabel(button) {
  const theme = currentTheme();
  if (button.classList.contains('theme-toggle-settings')) {
    const iconEl = button.querySelector('.tts-icon');
    const labelEl = button.querySelector('.tts-label');
    if (iconEl) iconEl.textContent = theme === 'light' ? '☀️' : '🌙';
    if (labelEl) labelEl.textContent = theme === 'light' ? 'Chế độ sáng' : 'Chế độ tối';
    button.setAttribute('aria-pressed', String(theme === 'light'));
    return;
  }
  const iconEl = button.querySelector('.icon');
  const labelEl = button.querySelector('.label');
  if (iconEl) iconEl.textContent = theme === 'light' ? '🌙' : '☀️';
  if (labelEl) labelEl.textContent = theme === 'light' ? 'Chế độ tối' : 'Chế độ sáng';
  button.setAttribute('aria-pressed', String(theme === 'light'));
}

function initThemeToggle() {
  // Sidebar toggle (các trang thường)
  const sidebarBtn = document.querySelector('#themeToggle');
  if (sidebarBtn) {
    syncToggleLabel(sidebarBtn);
    sidebarBtn.addEventListener('click', () => {
      applyTheme(currentTheme() === 'light' ? 'dark' : 'light');
      syncToggleLabel(sidebarBtn);
    });
  }

  // Switch trong settings page
  const switchBtn = document.querySelector('#themeToggleSwitch');
  if (switchBtn) {
    syncToggleLabel(switchBtn);
    switchBtn.addEventListener('click', () => {
      applyTheme(currentTheme() === 'light' ? 'dark' : 'light');
      syncToggleLabel(switchBtn);
    });
  }
}

document.addEventListener('DOMContentLoaded', initThemeToggle);

// Sidebar collapse/expand toggle
const SIDEBAR_KEY = 'fbbot-sidebar';

function initSidebarToggle() {
  const sidebar = document.querySelector('.sidebar');
  if (!sidebar) return;

  // Click logo → reload trang
  const logo = sidebar.querySelector('.sidebar-logo');
  if (logo) {
    logo.style.cursor = 'pointer';
    logo.title = 'Nhấn để tải lại trang';
    logo.addEventListener('click', () => location.reload());
  }

  // Wrap sidebar trong .sidebar-wrapper nếu chưa có
  let wrapper = sidebar.parentElement;
  if (!wrapper.classList.contains('sidebar-wrapper')) {
    wrapper = document.createElement('div');
    wrapper.className = 'sidebar-wrapper';
    sidebar.parentNode.insertBefore(wrapper, sidebar);
    wrapper.appendChild(sidebar);
  }

  const btn = document.createElement('button');
  btn.className = 'sidebar-toggle';
  btn.setAttribute('aria-label', 'Thu/mở sidebar');
  btn.innerHTML = `<svg viewBox="0 0 8 10"><polyline points="6,1 2,5 6,9"/></svg>`;
  document.body.appendChild(btn); // append vào body vì fixed

  const collapsed = localStorage.getItem(SIDEBAR_KEY) === 'collapsed';
  if (collapsed) {
    sidebar.classList.add('collapsed');
    wrapper.classList.add('collapsed');
    btn.querySelector('svg').style.transform = 'rotate(180deg)';
  }

  btn.addEventListener('click', () => {
    const isNowCollapsed = sidebar.classList.toggle('collapsed');
    wrapper.classList.toggle('collapsed', isNowCollapsed);
    btn.querySelector('svg').style.transform = isNowCollapsed ? 'rotate(180deg)' : '';
    try {
      localStorage.setItem(SIDEBAR_KEY, isNowCollapsed ? 'collapsed' : 'expanded');
    } catch (_) {}
  });
}

// Inject global topbar (thông báo + cài đặt) vào mọi trang
document.addEventListener('DOMContentLoaded', () => {
  if (!document.querySelector('#globalBar')) {
    const bar = document.createElement('div');
    bar.id = 'globalBar';
    bar.className = 'global-bar';
    bar.innerHTML = `
      <div class="global-bar-left">
        <a class="global-bar-logo" href="/html/index.html" onclick="location.reload();return false;" title="Về trang chủ">
          <svg width="22" height="22" viewBox="0 0 26 26" fill="none">
            <rect x="1" y="1" width="24" height="24" rx="7" fill="url(#glg)" opacity="0.2"/>
            <rect x="1" y="1" width="24" height="24" rx="7" stroke="url(#glg)" stroke-width="1.5"/>
            <text x="13" y="17.5" text-anchor="middle" font-family="'Space Grotesk',sans-serif" font-weight="700" font-size="10" fill="url(#glg)">FB</text>
            <defs>
              <linearGradient id="glg" x1="0" y1="0" x2="26" y2="26" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stop-color="#38bdf8"/>
                <stop offset="60%" stop-color="#a78bfa"/>
                <stop offset="100%" stop-color="#34d399"/>
              </linearGradient>
            </defs>
          </svg>
          <span class="global-bar-logo-text">FB Bot</span>
        </a>
      </div>
      <div class="global-bar-right">
        <span id="globalBotStatus" class="badge badge-idle" style="font-size:12px;">
          <span class="dot dot-idle"></span> Kiểm tra...
        </span>
        <button class="global-bar-btn" id="globalNotifBell" title="Thông báo" onclick="if(typeof toggleNotifPanel==='function')toggleNotifPanel()">
          🔔
          <span class="notif-badge" id="notifCount" style="display:none;">0</span>
        </button>
        <a href="/pages/settings.html" class="global-bar-btn" title="Cài đặt">⚙️</a>
      </div>
    `;
    document.body.insertBefore(bar, document.body.firstChild);
  }

  if (!document.querySelector('#toastContainer')) {
    const tc = document.createElement('div');
    tc.id = 'toastContainer';
    tc.className = 'toast-container';
    document.body.appendChild(tc);
  }

  if (!document.querySelector('#notifPanel')) {
    const np = document.createElement('div');
    np.id = 'notifPanel';
    np.className = 'notif-panel';
    np.style.display = 'none';
    np.innerHTML = `
      <div class="notif-panel-header">
        <h4>Thông báo</h4>
        <button onclick="if(typeof clearNotifications==='function')clearNotifications()" class="notif-clear-btn">Xóa tất cả</button>
      </div>
      <div id="notifList" class="notif-list">
        <div class="notif-empty">Chưa có thông báo nào</div>
      </div>`;
    document.body.appendChild(np);
  }
});

// ── Pull-to-refresh ──
(function initPullToRefresh() {
  let startY = 0;
  let pulling = false;
  let indicator = null;

  function getIndicator() {
    if (!indicator) {
      indicator = document.createElement('div');
      indicator.id = 'pullIndicator';
      indicator.innerHTML = '↓ Kéo để tải lại';
      indicator.style.cssText = `
        position:fixed; top:-48px; left:50%; transform:translateX(-50%);
        background:var(--surface-2); border:1px solid var(--border-soft);
        color:var(--text-muted); font-size:13px; font-weight:600;
        padding:10px 20px; border-radius:999px; z-index:9998;
        transition:top 0.2s ease; pointer-events:none;
        box-shadow:0 4px 16px rgba(0,0,0,0.3);
      `;
      document.body.appendChild(indicator);
    }
    return indicator;
  }

  document.addEventListener('touchstart', e => {
    if (window.scrollY === 0) {
      startY = e.touches[0].clientY;
      pulling = true;
    }
  }, { passive: true });

  document.addEventListener('touchmove', e => {
    if (!pulling) return;
    const dy = e.touches[0].clientY - startY;
    if (dy > 10) {
      const ind = getIndicator();
      const progress = Math.min(dy / 80, 1);
      ind.style.top = `${Math.min(dy * 0.4 - 24, 16)}px`;
      ind.innerHTML = progress >= 1 ? '↑ Thả để tải lại' : `↓ Kéo để tải lại`;
    }
  }, { passive: true });

  document.addEventListener('touchend', e => {
    if (!pulling) return;
    pulling = false;
    const dy = e.changedTouches[0].clientY - startY;
    const ind = getIndicator();
    if (dy > 80) {
      ind.innerHTML = '⟳ Đang tải...';
      setTimeout(() => {
        ind.style.top = '-48px';
        location.reload();
      }, 400);
    } else {
      ind.style.top = '-48px';
    }
  });
})();

document.addEventListener('DOMContentLoaded', initSidebarToggle);
