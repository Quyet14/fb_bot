// ============================================================
// script.js — shared utilities cho mọi trang dashboard
// Nguyên tắc: KHÔNG inject bất cứ thứ gì nếu đã có trong HTML
// ============================================================

// ── 1. Mobile nav toggle (chỉ cho landing page index.html) ──
document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.querySelector('.nav-toggle');
  const links  = document.querySelector('.nav-links');
  if (!toggle || !links) return;
  toggle.addEventListener('click', () => {
    const open = links.style.display === 'flex';
    links.style.display          = open ? '' : 'flex';
    links.style.flexDirection    = open ? '' : 'column';
    links.style.position         = open ? '' : 'fixed';
    links.style.top              = open ? '' : '68px';
    links.style.left             = open ? '' : '16px';
    links.style.right            = open ? '' : '16px';
    links.style.background       = open ? '' : 'var(--surface, #fff)';
    links.style.border           = open ? '' : '1px solid var(--border)';
    links.style.borderRadius     = open ? '' : '16px';
    links.style.padding          = open ? '' : '16px';
    links.style.boxShadow        = open ? '' : '0 20px 40px -20px rgba(45,38,110,0.35)';
    links.style.gap              = open ? '' : '14px';
    links.style.zIndex           = open ? '' : '200';
  });
  links.querySelectorAll('a').forEach(a =>
    a.addEventListener('click', () => { links.style.display = ''; })
  );
});

// ── 2. Sidebar collapse — dùng chung key 'fbbot-sidebar' ──
// Chỉ chạy nếu trang CHƯA có inline collapse logic
// (các trang mới đã tự handle, trang cũ chưa có sẵn wrapper)
document.addEventListener('DOMContentLoaded', () => {
  if (document.body.classList.contains('page-landing')) return; // landing page
  const sidebar = document.querySelector('.sidebar');
  if (!sidebar) return;
  if (document.querySelector('.nav-brand, .hero')) return; // landing page, bỏ qua
  // Nếu đã có #sidebarWrapper trong HTML thì bỏ qua (trang mới tự handle)
  if (document.getElementById('sidebarWrapper')) return;

  // Wrap sidebar trong .sidebar-wrapper nếu chưa có
  let wrapper = sidebar.parentElement;
  if (!wrapper.classList.contains('sidebar-wrapper')) {
    wrapper = document.createElement('div');
    wrapper.className = 'sidebar-wrapper';
    sidebar.parentNode.insertBefore(wrapper, sidebar);
    wrapper.appendChild(sidebar);
  }

  // Nút toggle — tái sử dụng nếu đã tồn tại
  let btn = document.querySelector('.sidebar-toggle');
  if (!btn) {
    btn = document.createElement('button');
    btn.className = 'sidebar-toggle';
    btn.setAttribute('title', 'Thu gọn sidebar');
    btn.innerHTML = `<svg viewBox="0 0 7 12"><polyline points="5,1 1,6 5,11"/></svg>`;
    document.body.appendChild(btn);
  }

  const SIDEBAR_KEY = 'fbbot-sidebar';

  function applyCollapsed(c) {
    sidebar.classList.toggle('collapsed', c);
    wrapper.classList.toggle('collapsed', c);
    const poly = btn.querySelector('polyline');
    if (poly) poly.setAttribute('points', c ? '1,1 5,6 1,11' : '5,1 1,6 5,11');
    try { localStorage.setItem(SIDEBAR_KEY, c ? '1' : '0'); } catch (_) {}
  }

  applyCollapsed(localStorage.getItem(SIDEBAR_KEY) === '1');
  btn.addEventListener('click', () => applyCollapsed(!wrapper.classList.contains('collapsed')));
});

// ── 3. Global bar — CHỈ inject nếu trang CHƯA có .global-bar trong HTML
//      VÀ không phải landing page (index.html)
document.addEventListener('DOMContentLoaded', () => {
  if (document.body.classList.contains('page-landing')) return; // landing page
  if (document.querySelector('.global-bar')) return; // đã có, bỏ qua
  if (document.querySelector('.nav.sticky, .nav-brand, .hero')) return; // landing page, bỏ qua

  const bar = document.createElement('header');
  bar.className = 'global-bar';
  bar.innerHTML = `
    <div class="global-bar-left">
      <a class="global-bar-logo" href="/html/dashboard.html" title="Dashboard">
        <svg width="22" height="22" viewBox="0 0 26 26" fill="none">
          <rect x="1" y="1" width="24" height="24" rx="7" fill="url(#glg)" opacity="0.2"/>
          <rect x="1" y="1" width="24" height="24" rx="7" stroke="url(#glg)" stroke-width="1.5"/>
          <text x="13" y="17.5" text-anchor="middle" font-family="'Space Grotesk',sans-serif"
                font-weight="700" font-size="10" fill="url(#glg)">FB</text>
          <defs>
            <linearGradient id="glg" x1="0" y1="0" x2="26" y2="26" gradientUnits="userSpaceOnUse">
              <stop offset="0%"   stop-color="#38bdf8"/>
              <stop offset="60%"  stop-color="#a78bfa"/>
              <stop offset="100%" stop-color="#34d399"/>
            </linearGradient>
          </defs>
        </svg>
        <span class="global-bar-logo-text">FB Bot Console</span>
      </a>
      <div class="global-bar-sep"></div>
      <div class="global-status-dot">
        <span class="dot dot-success"></span>
        <span class="global-status-label">Online</span>
      </div>
    </div>
    <div class="global-bar-right">
      <button class="global-bar-btn" id="notifBtn" title="Thông báo">
        🔔<span class="notif-badge" id="notifCount" style="display:none">0</span>
      </button>
      <a href="/pages/settings.html" class="global-bar-btn" title="Cài đặt">⚙️</a>
      <button class="global-bar-btn" id="themeBtn" title="Đổi theme">🌙</button>
    </div>`;
  document.body.insertBefore(bar, document.body.firstChild);

  // wire theme button
  document.getElementById('themeBtn')?.addEventListener('click', () => {
    window.toggleTheme?.();
    const light = document.documentElement.getAttribute('data-theme') === 'light';
    const btn = document.getElementById('themeBtn');
    if (btn) btn.textContent = light ? '☀️' : '🌙';
  });
});

// ── 4. Toast system ──
function showToast(type = 'info', title = '', msg = '', duration = 4000) {
  const container = document.getElementById('toastContainer');
  if (!container) return;
  const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <span class="toast-icon">${icons[type] || '🔹'}</span>
    <div class="toast-body">
      <div class="toast-title">${title}</div>
      ${msg ? `<div class="toast-msg">${msg}</div>` : ''}
    </div>
    <span class="toast-close" onclick="this.closest('.toast').remove()">✕</span>`;
  container.appendChild(toast);
  if (duration > 0) setTimeout(() => {
    toast.classList.add('hiding');
    setTimeout(() => toast.remove(), 220);
  }, duration);
}
window.showToast = showToast;

// ── 5. Notification panel ──
let _notifItems = [];

// Tạo panel DOM ngay khi page load — không lazy — để addNotification có chỗ render
function _ensureNotifPanel() {
  if (document.getElementById('notifPanel')) return;
  const panel = document.createElement('div');
  panel.id = 'notifPanel';
  panel.className = 'notif-panel';
  panel.style.display = 'none';
  panel.innerHTML = `
    <div class="notif-panel-header">
      <h4>Thông báo</h4>
      <button class="notif-clear-btn" onclick="clearNotifications()">Xóa tất cả</button>
    </div>
    <div id="notifList" class="notif-list">
      <div class="notif-empty">Chưa có thông báo nào</div>
    </div>`;
  document.body.appendChild(panel);
}

function _renderNotifList() {
  const list = document.getElementById('notifList');
  if (!list) return;
  if (!_notifItems.length) {
    list.innerHTML = '<div class="notif-empty">Chưa có thông báo nào</div>';
    return;
  }
  list.innerHTML = _notifItems.map(n => `
    <div class="notif-item unread">
      <span class="notif-item-icon">${n.icon}</span>
      <div class="notif-item-body">
        <div class="notif-item-title">${n.title}</div>
        <div class="notif-item-msg">${n.msg}</div>
        <div class="notif-item-time">${n.time}</div>
      </div>
    </div>`).join('');
}

function toggleNotifPanel() {
  _ensureNotifPanel();
  const panel = document.getElementById('notifPanel');
  const isOpen = panel.style.display !== 'none';
  if (isOpen) {
    panel.style.display = 'none';
    return;
  }
  // Render lại danh sách mới nhất trước khi mở
  _renderNotifList();
  panel.style.display = 'flex';
  panel.style.flexDirection = 'column';
  // Định vị dưới nút chuông
  const btn = document.getElementById('notifBtn');
  if (btn) {
    const r = btn.getBoundingClientRect();
    panel.style.top   = (r.bottom + 6) + 'px';
    panel.style.right = (window.innerWidth - r.right) + 'px';
    panel.style.left  = 'auto';
  }
}
window.toggleNotifPanel = toggleNotifPanel;

function clearNotifications() {
  _notifItems = [];
  _renderNotifList();
  const badge = document.getElementById('notifCount');
  if (badge) { badge.style.display = 'none'; badge.textContent = '0'; }
}
window.clearNotifications = clearNotifications;

function addNotification(icon, title, msg) {
  _ensureNotifPanel(); // đảm bảo panel và #notifList tồn tại
  _notifItems.unshift({ icon, title, msg, time: new Date().toLocaleTimeString('vi-VN') });
  if (_notifItems.length > 20) _notifItems.pop();

  // Cập nhật badge
  const badge = document.getElementById('notifCount');
  if (badge) { badge.textContent = _notifItems.length; badge.style.display = 'flex'; }

  // Nếu panel đang mở thì render ngay, nếu đóng thì data đã lưu trong _notifItems
  const panel = document.getElementById('notifPanel');
  if (panel && panel.style.display !== 'none') {
    _renderNotifList();
  }
}
window.addNotification = addNotification;

document.addEventListener('DOMContentLoaded', () => {
  if (!document.body.classList.contains('page-landing')) {
    _ensureNotifPanel(); // tạo panel DOM sớm nhất có thể
  }
  document.getElementById('notifBtn')?.addEventListener('click', toggleNotifPanel);
  // Đóng khi click ra ngoài
  document.addEventListener('click', e => {
    const panel = document.getElementById('notifPanel');
    const btn   = document.getElementById('notifBtn');
    if (panel && panel.style.display !== 'none' &&
        !panel.contains(e.target) && !btn?.contains(e.target)) {
      panel.style.display = 'none';
    }
  });
});

// ── 6. Expose toggleTheme globally — chỉ dùng khi không có doToggleTheme (trang không phải settings) ──
window.toggleTheme = window.toggleTheme || function () {
  const next = document.documentElement.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
  document.documentElement.setAttribute('data-theme', next);
  try { localStorage.setItem('fbbot-theme', next); } catch (_) {}
};

// ── 7. Log notifications — gọi sau khi loadData xong ──
// Lưu ID log đã thông báo để tránh thông báo lại
let _seenLogIds = new Set();

function _checkNewLogsAndNotify() {
  const logs = window.state?.logs || [];
  if (!logs.length) return;

  // Lần đầu tiên load — chỉ đánh dấu đã thấy, không popup
  if (_seenLogIds.size === 0) {
    logs.forEach(l => _seenLogIds.add(l.id));
    return;
  }

  // Tìm log mới (chưa thấy lần trước)
  const newLogs = logs.filter(l => !_seenLogIds.has(l.id));
  newLogs.forEach(l => _seenLogIds.add(l.id));

  newLogs.forEach(l => {
    const loaiLabel = { dang_bai: 'Đăng bài', repost: 'Repost', tuong_tac: 'Tương tác' }[l.loai] || l.loai;
    if (l.trang_thai === 'success') {
      addNotification('✅', `${loaiLabel} thành công`, l.chi_tiet || 'Bot đã hoàn thành tác vụ.');
      showToast('success', `${loaiLabel} thành công ✅`, l.chi_tiet ? String(l.chi_tiet).slice(0, 80) : '');
    } else if (l.trang_thai === 'error') {
      addNotification('❌', `${loaiLabel} thất bại`, l.chi_tiet || 'Có lỗi xảy ra khi chạy tác vụ.');
      showToast('error', `${loaiLabel} thất bại ❌`, l.chi_tiet ? String(l.chi_tiet).slice(0, 80) : '');
    }
  });
}
window._checkNewLogsAndNotify = _checkNewLogsAndNotify;

// ── 7b. Polling tự động để nhận kết quả bot chạy theo lịch ──
let _pollingTimer = null;

function startLogPolling(intervalMs = 15000) {
  if (_pollingTimer) return; // đã chạy rồi
  _pollingTimer = setInterval(async () => {
    try {
      if (typeof window.loadData === 'function') await window.loadData();
    } catch (_) {}
  }, intervalMs);
}

// Bắt đầu polling sau khi trang load xong
document.addEventListener('DOMContentLoaded', () => {
  // Chỉ poll trên các trang dashboard (không phải landing)
  if (document.body.classList.contains('page-landing')) return;
  startLogPolling(15000); // refresh mỗi 15 giây
});

// ── 8. Health-check backend status ──
document.addEventListener('DOMContentLoaded', () => {
  const statusEl = document.getElementById('backendStatus');
  if (!statusEl) return;
  const API = window.API_BASE || 'http://127.0.0.1:8000';
  fetch(`${API}/groups`, { method: 'GET', signal: AbortSignal.timeout?.(3000) })
    .then(r => {
      statusEl.className = 'badge badge-success';
      statusEl.innerHTML = '<span class="dot dot-success"></span> Kết nối OK';
    })
    .catch(() => {
      statusEl.className = 'badge badge-danger';
      statusEl.innerHTML = '<span class="dot dot-danger"></span> Không kết nối được';
    });
});
