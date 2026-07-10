const _HOST = window.location && window.location.hostname ? window.location.hostname : '127.0.0.1';
const _SAME_ORIGIN_API = window.location && window.location.origin && window.location.protocol !== 'file:'
  ? `${window.location.origin}/api`
  : null;
const API_BASE_CANDIDATES = [
  // Ưu tiên config từ window.FBBOT_API_URL nếu được set
  ...(window.FBBOT_API_URL ? [window.FBBOT_API_URL] : []),
  ...(_SAME_ORIGIN_API ? [_SAME_ORIGIN_API] : []),
  `http://${_HOST}:8000`,
  `http://${_HOST}:8005`,
  'http://127.0.0.1:8000',
  'http://127.0.0.1:8005',
  'http://localhost:8000',
  'http://localhost:8005'
];
const API_CANDIDATES_FAST = (() => {
  const isLocalHost = ['localhost', '127.0.0.1'].includes(_HOST) || /^192\.168\.|^10\.|^172\.(1[6-9]|2\d|3[01])\./.test(_HOST);
  if (isLocalHost) return API_BASE_CANDIDATES;
  return API_BASE_CANDIDATES.filter(base =>
    (window.FBBOT_API_URL && base === window.FBBOT_API_URL) ||
    (_SAME_ORIGIN_API && base === _SAME_ORIGIN_API)
  );
})();

function makeApiUrl(path, base) {
  return path.startsWith('http://') || path.startsWith('https://') ? path : `${base}${path}`;
}

async function fetchJson(url, options = {}) {
  const candidates = API_CANDIDATES_FAST.map(base => makeApiUrl(url, base));
  let lastError = null;
  const timeoutMs = options.timeoutMs || 1200;
  delete options.timeoutMs;

  // Đính kèm Authorization header — ưu tiên Auth object, fallback đọc trực tiếp localStorage
  let token = null;
  if (typeof Auth !== 'undefined' && Auth.getAccessToken) {
    token = Auth.getAccessToken();
  } else {
    token = localStorage.getItem('fbbot-access-token');
  }
  const authHeaders = token ? { Authorization: `Bearer ${token}` } : {};
  // Thêm header để bypass ngrok browser warning
  options.headers = { 
    'ngrok-skip-browser-warning': 'true',
    ...authHeaders, 
    ...options.headers 
  };

  // Debug: log nếu không có token
  if (!token) {
    console.warn('[fetchJson] No token for:', url);
  }

  for (const candidate of candidates) {
    try {
      // Per-candidate timeout to avoid long hang when a backend is unreachable
      const controller = new AbortController();
      const to = setTimeout(() => controller.abort(), timeoutMs);
      const res = await fetch(candidate, { ...options, signal: controller.signal });
      clearTimeout(to);
      if (res.status === 204) return null;
      if (res.status === 401) {
        // Thử silent refresh
        const refreshFn = typeof Auth !== 'undefined' ? () => Auth.refreshAccessToken() : null;
        const refreshed = refreshFn ? await refreshFn() : false;
        if (refreshed) {
          const newToken = typeof Auth !== 'undefined' ? Auth.getAccessToken() : localStorage.getItem('fbbot-access-token');
          if (newToken) options.headers = { ...options.headers, Authorization: `Bearer ${newToken}` };
          const retry = await fetch(candidate, options);
          if (retry.status === 204) return null;
          if (!retry.ok) {
            const text = await retry.text();
            throw new Error(`API error ${retry.status}: ${text}`);
          }
          return retry.json();
        }
        // Refresh thất bại → redirect login
        if (typeof Auth !== 'undefined') {
          Auth.clearTokens();
          Auth._redirectToLogin();
        } else {
          localStorage.removeItem('fbbot-access-token');
          localStorage.removeItem('fbbot-refresh-token');
          window.location.href = window.location.pathname.includes('/pages/') ? '../html/login.html' : 'login.html';
        }
        return null;
      }
      if (!res.ok) {
        const text = await res.text();
        throw new Error(`API error ${res.status}: ${text}`);
      }

      const contentType = res.headers.get('content-type') || '';
      if (contentType.includes('application/json')) {
        return res.json();
      }

      const text = await res.text();
      return text ? JSON.parse(text) : null;
    } catch (error) {
      lastError = error;
      // Nếu lỗi mạng, thử port khác.
      // Abort errors and network failures should try the next candidate
      if (error.name === 'AbortError' || error instanceof TypeError || (error.message && error.message.includes('Failed to fetch'))) {
        continue;
      }
      throw error;
    }
  }

  throw lastError || new Error('Không thể kết nối với backend');
}

async function loadGroups() {
  return fetchJson('/groups/');
}

async function createGroup(payload) {
  return fetchJson('/groups/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
}

async function updateGroup(groupId, payload) {
  return fetchJson(`/groups/${groupId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
}

async function deleteGroup(groupId) {
  return fetchJson(`/groups/${groupId}`, { method: 'DELETE' });
}

async function loadTopics() {
  return fetchJson('/topics/');
}

async function loadUserContents() {
  return fetchJson('/user-contents/');
}

async function createUserContent(payload) {
  return fetchJson('/user-contents/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
}

async function deleteUserContent(contentId) {
  return fetchJson(`/user-contents/${contentId}`, { method: 'DELETE' });
}


async function createTopic(payload) {
  return fetchJson('/topics/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
}

async function updateTopic(topicId, payload) {
  return fetchJson(`/topics/${topicId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
}

async function deleteTopic(topicId) {
  return fetchJson(`/topics/${topicId}`, { method: 'DELETE' });
}

async function createPostSchedule(payload) {
  return fetchJson('/schedules/dang-bai', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
}

async function updatePostSchedule(scheduleId, payload) {
  return fetchJson(`/schedules/dang-bai/${scheduleId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
}


async function createRepostSchedule(payload) {
  return fetchJson('/schedules/repost', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
}

async function createInteractSchedule(payload) {
  return fetchJson('/schedules/tuong-tac', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
}

async function deletePostSchedule(scheduleId) {
  return fetchJson(`/schedules/dang-bai/${scheduleId}`, { method: 'DELETE' });
}

async function deleteRepostSchedule(scheduleId) {
  return fetchJson(`/schedules/repost/${scheduleId}`, { method: 'DELETE' });
}

async function deleteInteractSchedule(scheduleId) {
  return fetchJson(`/schedules/tuong-tac/${scheduleId}`, { method: 'DELETE' });
}

async function loadSchedules() {
  const [posts, reposts, interacts] = await Promise.all([
    fetchJson('/schedules/dang-bai'),
    fetchJson('/schedules/repost'),
    fetchJson('/schedules/tuong-tac')
  ]);
  return { posts, reposts, interacts };
}

async function loadLogs() {
  return fetchJson('/logs/');
}

async function loadSettings() {
  return fetchJson('/settings/');
}

async function saveSettingsApi(payload) {
  return fetchJson('/settings/', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
}

async function selectImageDirectory() {
  return fetchJson('/settings/select-image-dir', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    timeoutMs: 300000
  });
}

async function loadLanguage() {
  try {
    const s = await loadSettings();
    return s?.ngon_ngu || 'vi';
  } catch (_) { return 'vi'; }
}

async function saveLanguage(lang) {
  return saveSettingsApi({ ngon_ngu: lang });
}

async function loadLanguage() {
  try {
    const s = await loadSettings();
    return s?.ngon_ngu || 'vi';
  } catch (_) { return 'vi'; }
}

async function saveLanguage(lang) {
  return saveSettingsApi({ ngon_ngu: lang });
}
