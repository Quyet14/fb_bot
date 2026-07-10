// ============================================================
// auth.js — Frontend Auth Module
// Quản lý JWT token lifecycle và bảo vệ trang dashboard
// ============================================================

const Auth = {
  KEY_ACCESS:  'fbbot-access-token',
  KEY_REFRESH: 'fbbot-refresh-token',
  KEY_USER:    'fbbot-user',

  getAccessToken()  { return localStorage.getItem(this.KEY_ACCESS); },
  getRefreshToken() { return localStorage.getItem(this.KEY_REFRESH); },
  getUser()         { try { return JSON.parse(localStorage.getItem(this.KEY_USER) || 'null'); } catch { return null; } },

  setTokens(access, refresh, user) {
    localStorage.setItem(this.KEY_ACCESS, access);
    localStorage.setItem(this.KEY_REFRESH, refresh);
    if (user) localStorage.setItem(this.KEY_USER, JSON.stringify(user));
  },

  clearTokens() {
    localStorage.removeItem(this.KEY_ACCESS);
    localStorage.removeItem(this.KEY_REFRESH);
    localStorage.removeItem(this.KEY_USER);
  },

  getAuthHeaders() {
    const token = this.getAccessToken();
    if (!token) return {};
    return { Authorization: `Bearer ${token}` };
  },

  // ── Tìm API base ──────────────────────────────────────────
  _apiBase: null,
  async _findApiBase() {
    if (this._apiBase) return this._apiBase;

    // Nếu đang truy cập qua ngrok hoặc từ xa → dùng API ngrok nếu có
    const isExternal = !['localhost','127.0.0.1'].includes(window.location.hostname);
    if (isExternal && window.FBBOT_API_URL) {
      this._apiBase = window.FBBOT_API_URL;
      return this._apiBase;
    }

    const sameOriginApi = window.location && window.location.origin && window.location.protocol !== 'file:'
      ? `${window.location.origin}/api`
      : null;
    const candidates = [
      ...(sameOriginApi ? [sameOriginApi] : []),
      `http://${window.location.hostname}:8000`,
      `http://${window.location.hostname}:8005`,
    ];
    for (const base of candidates) {
      try {
        const r = await fetch(`${base}/`, { signal: AbortSignal.timeout(2000) });
        if (r.ok) { this._apiBase = base; return base; }
      } catch (_) {}
    }
    this._apiBase = candidates[0];
    return candidates[0];
  },

  async _fetch(path, options = {}) {
    const base = await this._findApiBase();
    options.headers = { 
      'Content-Type': 'application/json',
      'ngrok-skip-browser-warning': 'true',
      ...options.headers 
    };
    const res = await fetch(`${base}${path}`, options);
    return res;
  },

  // ── Đăng nhập ─────────────────────────────────────────────
  async login(username, password) {
    const res = await this._fetch('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || `Đăng nhập thất bại (${res.status})`);
    }
    const data = await res.json();
    this.setTokens(data.access_token, data.refresh_token, { username: data.username });
    // Redirect về dashboard — luôn dùng path tuyệt đối từ server root
    window.location.href = '/dashboard';
  },

  // ── Đăng ký ───────────────────────────────────────────────
  async register(username, password, confirmPassword, email, fullName) {
    const res = await this._fetch('/auth/register', {
      method: 'POST',
      body: JSON.stringify({
        username,
        password,
        confirm_password: confirmPassword,
        email: email || undefined,
        full_name: fullName || undefined,
      }),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || `Đăng ký thất bại (${res.status})`);
    }
    return res.json();
  },

  // ── Refresh access token ──────────────────────────────────
  async refreshAccessToken() {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) return false;
    try {
      const res = await this._fetch('/auth/refresh', {
        method: 'POST',
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      if (!res.ok) return false;
      const data = await res.json();
      this.setTokens(data.access_token, data.refresh_token, this.getUser());
      return true;
    } catch (_) {
      return false;
    }
  },

  // ── Đăng xuất ─────────────────────────────────────────────
  async logout() {
    try {
      const token = this.getAccessToken();
      if (token) {
        await this._fetch('/auth/logout', {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
        });
      }
    } catch (_) {}
    this.clearTokens();
    this._redirectToLogin();
  },

  _redirectToLogin() {
    window.location.href = '/login';
  },

  // ── Guard: bảo vệ trang dashboard ─────────────────────────
  async guardPage() {
    const token = this.getAccessToken();
    if (!token) {
      this._redirectToLogin();
      return false;
    }
    try {
      const base = await this._findApiBase();
      const res = await fetch(`${base}/auth/me`, {
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        signal: AbortSignal.timeout(5000),
      });

      if (res.ok) {
        const user = await res.json();
        this.setTokens(token, this.getRefreshToken(), user);
        return true; // OK — cho phép trang render
      }

      if (res.status === 401) {
        // Thử silent refresh
        const refreshed = await this.refreshAccessToken();
        if (refreshed) return true;
        this.clearTokens();
        this._redirectToLogin();
        return false;
      }

      // Lỗi khác (403, 500...) — vẫn cho phép nếu có token
      return true;
    } catch (_) {
      // Backend không khả dụng — cho phép nếu token tồn tại (offline mode)
      console.warn('[Auth] guardPage: không thể kết nối backend, cho qua với token hiện có.');
      if (typeof showToast === 'function') {
        showToast('warning', 'Không thể kết nối backend', 'Một số tính năng có thể không hoạt động.');
      }
      return true;
    }
  },

  // ── Render tên user — đã tích hợp vào global-bar HTML, không cần inject động
  _renderUserInBar(user) {},
};

window.Auth = Auth;
