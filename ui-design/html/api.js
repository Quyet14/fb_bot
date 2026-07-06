const API_BASE_CANDIDATES = [
  `http://${window.location.hostname}:8000`,
  `http://${window.location.hostname}:8005`
];

function makeApiUrl(path, base) {
  return path.startsWith('http://') || path.startsWith('https://') ? path : `${base}${path}`;
}

async function fetchJson(url, options = {}) {
  const candidates = API_BASE_CANDIDATES.map(base => makeApiUrl(url, base));
  let lastError = null;

  // Đính kèm Authorization header nếu có token
  const authHeaders = (typeof Auth !== 'undefined') ? Auth.getAuthHeaders() : {};
  options.headers = { ...authHeaders, ...options.headers };

  for (const candidate of candidates) {
    try {
      const res = await fetch(candidate, options);
      if (res.status === 204) return null;
      // Nếu 401 → token hết hạn, thử silent refresh rồi retry
      if (res.status === 401 && typeof Auth !== 'undefined') {
        const refreshed = await Auth.refreshAccessToken();
        if (refreshed) {
          options.headers = { ...Auth.getAuthHeaders(), ...options.headers };
          const retry = await fetch(candidate, options);
          if (retry.status === 204) return null;
          if (!retry.ok) {
            const text = await retry.text();
            throw new Error(`API error ${retry.status}: ${text}`);
          }
          return retry.json();
        }
        // Refresh thất bại → redirect login
        Auth.clearTokens();
        Auth._redirectToLogin();
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
      if (error instanceof TypeError || error.message.includes('Failed to fetch')) {
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
