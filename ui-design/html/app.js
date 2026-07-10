const state = { groups: [], topics: [], schedules: { posts: [], reposts: [], interacts: [] }, logs: [] };
window.state = state; // expose để health check đọc được

function setStatus(message, isError = false) {
  const status = document.querySelector('#status');
  if (!status) return;
  if (!isError) {
    // Chỉ hiện lỗi, không hiện thông báo thành công
    status.textContent = '';
    status.style.display = 'none';
    return;
  }
  status.style.display = 'inline-block';
  status.textContent = message;
  status.style.color = 'var(--danger)';
}

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function parseIds(value) {
  return String(value || '')
    .split(',')
    .map(item => Number(item.trim()))
    .filter(Boolean);
}

// Dashboard log detail formatter — hiện tên nhóm/page, ẩn URL
function _dashFormatDetail(raw) {
  if (!raw) return '—';
  // Parse multi-line: "Tên: SUCCESS" | "Tên: False" | "Tên: no_token_skip"
  const lines = raw.split('\n').map(l => l.trim()).filter(Boolean);
  const parsed = lines.map(line => {
    const sep = line.indexOf(': ');
    if (sep === -1) return null;
    let name = line.slice(0, sep).trim();
    const rest = line.slice(sep + 2).trim().toUpperCase();
    // Clean URL thành slug
    if (/https?:\/\/(www\.)?facebook\.com\//i.test(name)) {
      const slug = name.replace(/https?:\/\/(www\.)?facebook\.com\//i, '').split('/')[0].split('?')[0];
      name = slug || name;
    }
    // Xác định result
    let icon = '·';
    if (rest === 'SUCCESS' || rest.startsWith('SUCCESS:') || rest === 'TRUE') {
      icon = '<span style="color:var(--success)">✓</span>';
    } else if (rest === 'FALSE' || rest === 'NONE' || rest.startsWith('ERROR')) {
      icon = '<span style="color:var(--danger)">✗</span>';
    } else if (rest.startsWith('PENDING')) {
      icon = '<span style="color:var(--warning)">⏳</span>';
    } else if (rest === 'NO_TOKEN_SKIP') {
      icon = '<span style="color:var(--text-faint)">⊘</span>';
    }
    return { name: escapeHtml(name), icon };
  }).filter(Boolean);
  if (!parsed.length) return escapeHtml(raw.slice(0, 60)) + (raw.length > 60 ? '…' : '');
  // Giới hạn 2 item đầu tiên cho dashboard
  return parsed.slice(0, 2).map(p => `${p.icon} ${p.name}`).join(' <span style="color:var(--border)">·</span> ')
    + (parsed.length > 2 ? ` <span style="color:var(--text-faint)">+${parsed.length - 2}</span>` : '');
}

function renderGroups() {
  const tbody = document.querySelector('#groupsTable tbody');
  if (!tbody) return;
  tbody.innerHTML = state.groups.map(group => `
    <tr>
      <td>${escapeHtml(group.ten)}</td>
      <td>${escapeHtml(group.url)}</td>
      <td>${escapeHtml(group.ghi_chu || '')}</td>
      <td>
        <button data-action="edit-group" data-id="${group.id}">Sửa</button>
        <button data-action="delete-group" data-id="${group.id}">Xóa</button>
      </td>
    </tr>
  `).join('');
}

function renderTopics() {
  const tbody = document.querySelector('#topicsTable tbody');
  if (!tbody) return;
  tbody.innerHTML = state.topics.map(topic => `
    <tr>
      <td>${escapeHtml(topic.ten)}</td>
      <td>${escapeHtml(topic.mo_ta || '')}</td>
      <td>
        <button data-action="edit-topic" data-id="${topic.id}">Sửa</button>
        <button data-action="delete-topic" data-id="${topic.id}">Xóa</button>
      </td>
    </tr>
  `).join('');
}

function renderScheduleForm() {
  const topicSelect = document.querySelector('#scheduleTopicId');
  if (topicSelect) {
    topicSelect.innerHTML = ['<option value="">-- Chọn chủ đề --</option>', ...state.topics.map(topic => `<option value="${topic.id}">${escapeHtml(topic.ten)}</option>`)].join('');
  }
}


function updateScheduleFormFields() {
  const type = document.querySelector('#scheduleType')?.value || 'dang-bai';
  const postFields = document.querySelector('#schedulePostFields');
  const repostFields = document.querySelector('#scheduleRepostFields');
  const interactFields = document.querySelector('#scheduleInteractFields');
  if (postFields) postFields.style.display = type === 'dang-bai' ? 'grid' : 'none';
  if (repostFields) repostFields.style.display = type === 'repost' ? 'grid' : 'none';
  if (interactFields) interactFields.style.display = type === 'tuong-tac' ? 'grid' : 'none';

  // Toggle theo mode đăng bài (topic vs content)
  const mode = document.querySelector('#scheduleDangBaiMode')?.value || 'topic';
  const topicField = document.querySelector('#scheduleTopicField');
  const contentTextField = document.querySelector('#scheduleContentTextField');
  const giuNguyenField = document.querySelector('#scheduleGiuNguyenGocField');

  if (topicField) topicField.style.display = mode === 'topic' ? 'flex' : 'none';
  if (contentTextField) contentTextField.style.display = mode === 'content' ? 'flex' : 'none';
  if (giuNguyenField) giuNguyenField.style.display = mode === 'content' ? 'flex' : 'none';
}



function renderSchedules() {
  const root = document.querySelector('#schedulesRoot');
  if (!root) return;

  const renderCard = (title, items, deleteAction, editAction, renderItem) => {
    const header = `
      <div class="card-schedule-header">
        <span class="type-dot"></span>
        <h3>${escapeHtml(title)}</h3>
        <span class="count">${items.length}</span>
      </div>`;
    const body = items.length
      ? `<div class="schedule-list">${items.map(item => `
          <div class="schedule-item">
            <span class="schedule-status-dot"></span>
            <div class="schedule-item-info">${renderItem(item)}</div>
            <div class="schedule-actions">
              <button data-action="${editAction}" data-id="${item.id}" class="btn-secondary">Sửa</button>
              <button data-action="${deleteAction}" data-id="${item.id}" class="btn-danger">Xóa</button>
            </div>
          </div>`).join('')}</div>`
      : `<div class="schedule-list"><div class="empty-state">Chưa có lịch nào</div></div>`;
    return `<div class="card card-schedule">${header}${body}</div>`;
  };

  root.innerHTML = [
    renderCard('Lịch đăng bài', state.schedules.posts, 'delete-post-schedule', 'edit-post-schedule', item => `
      <div class="time">${escapeHtml(item.thu)} · ${escapeHtml(item.gio)}</div>
      <div class="detail">${item.topic?.ten ? escapeHtml(item.topic.ten) : item.content?.noi_dung ? escapeHtml(item.content.noi_dung.substring(0, 60)) + (item.content.noi_dung.length > 60 ? '…' : '') : 'Chưa có chủ đề'}</div>
      <div class="group-tag">${item.groups?.length ? item.groups.map(g => escapeHtml(g.ten)).join(', ') : 'Không có nhóm'}</div>
    `),
    renderCard('Lịch repost', state.schedules.reposts, 'delete-repost-schedule', 'edit-repost-schedule', item => `
      <div class="time">${escapeHtml(item.thu)} · ${escapeHtml(item.gio)}</div>
      <div class="detail">Số bài: ${escapeHtml(String(item.so_bai || 1))}</div>
      <div class="group-tag">${item.nhom_nguon?.length ? item.nhom_nguon.map(g => escapeHtml(g.ten)).join(', ') : 'Không có nhóm nguồn'}</div>
    `),
    renderCard('Lịch tương tác', state.schedules.interacts, 'delete-interact-schedule', 'edit-interact-schedule', item => `
      <div class="time">${escapeHtml(item.thu)} · ${escapeHtml(item.gio)}</div>
      <div class="group-tag">${item.groups?.length ? item.groups.map(g => escapeHtml(g.ten)).join(', ') : 'Không có nhóm'}</div>
    `)
  ].join('');
}


function renderLogs() {
  const tbody = document.querySelector('#logsTable tbody');
  if (!tbody) return;

  if (!state.logs.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="4" style="text-align:center; color:var(--text-muted); padding:24px 12px;">
          Chưa có log hoạt động nào. Khi bot chạy đăng bài, repost hoặc tương tác, dữ liệu sẽ hiện ở đây.
        </td>
      </tr>`;
    return;
  }

  tbody.innerHTML = state.logs.map(log => `
    <tr>
      <td>${escapeHtml(log.bat_dau || '')}</td>
      <td>${escapeHtml(log.loai || '')}</td>
      <td>${escapeHtml(log.trang_thai || '')}</td>
      <td>${escapeHtml(log.chi_tiet || '')}</td>
    </tr>
  `).join('');
}

function renderDashboardSummary() {
  // Dashboard nâng cao (index.html mới)
  if (document.querySelector('#dashboardRecentLogs')) {
    _renderDashboardEnhanced();
    return;
  }

  // Dashboard cũ fallback
  const groupCountEl = document.querySelector('#dashboardGroupCount');
  const scheduleCountEl = document.querySelector('#dashboardScheduleCount');
  const todayCountEl = document.querySelector('#dashboardTodayCount');
  const recentListEl = document.querySelector('#dashboardRecentList');
  if (!groupCountEl && !scheduleCountEl && !todayCountEl && !recentListEl) return;

  const totalSchedules = (state.schedules.posts?.length || 0) + (state.schedules.reposts?.length || 0) + (state.schedules.interacts?.length || 0);
  const today = new Date().toISOString().slice(0, 10);
  const todayLogs = (state.logs || []).filter(log => String(log.bat_dau || '').startsWith(today)).length;

  if (groupCountEl) groupCountEl.textContent = String(state.groups?.length || 0);
  if (scheduleCountEl) scheduleCountEl.textContent = String(totalSchedules);
  if (todayCountEl) todayCountEl.textContent = String(todayLogs);

  if (recentListEl) {
    const recentItems = [
      ...(state.schedules.posts || []).map(item => ({ ...item, type: 'Đăng bài' })),
      ...(state.schedules.reposts || []).map(item => ({ ...item, type: 'Repost' })),
      ...(state.schedules.interacts || []).map(item => ({ ...item, type: 'Tương tác' }))
    ]
      .sort((a, b) => String(a.gio || '').localeCompare(String(b.gio || '')))
      .slice(0, 5);

    recentListEl.innerHTML = recentItems.length
      ? recentItems.map(item => `
          <tr>
            <td>${escapeHtml(item.type)}</td>
            <td style="font-family: var(--font-mono);">${escapeHtml(`${item.thu || ''} · ${item.gio || ''}`)}</td>
            <td><span class="badge badge-success"><span class="dot dot-success"></span>${item.active ? 'Đang hoạt động' : 'Tạm dừng'}</span></td>
          </tr>`).join('')
      : '<tr><td colspan="3">Chưa có lịch nào</td></tr>';
  }
}

function _renderDashboardEnhanced() {
  const groupCountEl = document.querySelector('#dashboardGroupCount');
  const scheduleCountEl = document.querySelector('#dashboardScheduleCount');
  const todayCountEl = document.querySelector('#dashboardTodayCount');
  const errorCountEl = document.querySelector('#dashboardErrorCount');

  const totalSchedules = (state.schedules.posts?.length || 0)
    + (state.schedules.reposts?.length || 0)
    + (state.schedules.interacts?.length || 0);
  const today = new Date().toISOString().slice(0, 10);
  const todayLogs = (state.logs || []).filter(l => String(l.bat_dau || '').startsWith(today));
  const todayOk = todayLogs.filter(l => l.trang_thai === 'success').length;
  const todayErr = todayLogs.filter(l => l.trang_thai === 'error').length;

  if (groupCountEl) groupCountEl.textContent = String(state.groups?.length || 0);
  if (scheduleCountEl) scheduleCountEl.textContent = String(totalSchedules);
  if (todayCountEl) todayCountEl.textContent = String(todayOk);
  if (errorCountEl) errorCountEl.textContent = String(todayErr);

  const statusBadge = document.querySelector('#botStatus');
  if (statusBadge) {
    if (todayErr === 0 && todayOk > 0) {
      statusBadge.className = 'badge badge-success';
      statusBadge.innerHTML = '<span class="dot dot-success"></span> Bot hoạt động tốt';
    } else if (todayErr > 0) {
      statusBadge.className = 'badge badge-warning';
      statusBadge.innerHTML = '<span class="dot dot-warning"></span> Có lỗi xảy ra';
    } else {
      statusBadge.className = 'badge badge-idle';
      statusBadge.innerHTML = '<span class="dot dot-idle"></span> Chưa có hoạt động';
    }
  }

  const logsEl = document.querySelector('#dashboardRecentLogs');
  if (logsEl) {
    const recent = (state.logs || []).slice(0, 8);
    if (!recent.length) {
      logsEl.innerHTML = `<tr><td colspan="4" style="text-align:center;color:var(--text-faint);padding:20px;">Chưa có hoạt động nào</td></tr>`;
    } else {
      const TYPE_MAP = {
        dang_bai:'📝 Đăng bài', 'dang-bai':'📝 Đăng bài', post:'📝 Đăng bài',
        repost:'🔁 Repost',
        tuong_tac:'💬 Tương tác', 'tuong-tac':'💬 Tương tác', interact:'💬 Tương tác',
        fanpage:'📄 Fanpage', fanpage_v2:'📄 Fanpage',
      };
      logsEl.innerHTML = recent.map(log => {
        const statusClass = log.trang_thai === 'success' ? 'dot-success' : log.trang_thai === 'error' ? 'dot-danger' : 'dot-warning';
        const time = String(log.bat_dau || '').replace('T', ' ').slice(0, 16);
        const typeKey = String(log.loai || '').toLowerCase();
        const typeLabel = TYPE_MAP[typeKey] || escapeHtml(log.loai || '—');
        const detail = _dashFormatDetail(log.chi_tiet || '');
        return `<tr>
          <td style="font-family:var(--font-mono);font-size:12px;color:var(--text-faint);white-space:nowrap;">${escapeHtml(time)}</td>
          <td style="font-size:12.5px;">${typeLabel}</td>
          <td><span class="dot ${statusClass}" style="display:inline-block;margin-right:4px;"></span><span style="font-size:12.5px;">${escapeHtml(log.trang_thai || '')}</span></td>
          <td style="max-width:240px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12.5px;">${detail}</td>
        </tr>`;
      }).join('');
    }
  }

  // Fix Bug 1 & 3: Declare upcomingEl at the start of this block
  const upcomingEl = document.querySelector('#dashboardUpcoming');
  if (upcomingEl) {
    const all = [
      ...(state.schedules.posts || []).map(s => ({ ...s, loai: '📝 Đăng bài' })),
      ...(state.schedules.reposts || []).map(s => ({ ...s, loai: '🔁 Repost' })),
      ...(state.schedules.interacts || []).map(s => ({ ...s, loai: '💬 Tương tác' })),
    ].filter(s => s.active).sort((a, b) => String(a.gio || '').localeCompare(String(b.gio || '')));

    if (!all.length) {
      upcomingEl.innerHTML = `<div style="text-align:center;color:var(--text-faint);font-size:13px;padding:16px;">Chưa có lịch nào</div>`;
    } else {
      upcomingEl.innerHTML = all.slice(0, 5).map(s => {
        const desc = s.topic?.ten || (s.content?.noi_dung ? s.content.noi_dung.slice(0, 40) + '…' : '');
        return `<div class="upcoming-item">
          <span class="upcoming-dot"></span>
          <span class="upcoming-time">${escapeHtml(s.thu || '')} ${escapeHtml(s.gio || '')}</span>
          <span class="upcoming-desc">${desc ? escapeHtml(desc) : (s.groups?.map(g => g.ten).join(', ') || '')}</span>
          <span class="upcoming-type">${s.loai}</span>
        </div>`;
      }).join('');
    }
  }

  // Bug 4 fix: fill summary panel elements directly so they update whenever _renderDashboardEnhanced runs
  const summaryGroupsEl = document.getElementById('summaryGroups');
  const summaryTopicsEl = document.getElementById('summaryTopics');
  const summarySchedulesEl = document.getElementById('summarySchedules');
  const summaryLogsEl = document.getElementById('summaryLogs');
  if (summaryGroupsEl || summaryTopicsEl || summarySchedulesEl || summaryLogsEl) {
    const gCount = state.groups?.length ?? 0;
    const tCount = state.topics?.length ?? 0;
    const sTotal = (state.schedules?.posts?.length || 0) + (state.schedules?.reposts?.length || 0) + (state.schedules?.interacts?.length || 0);
    const lCount = state.logs?.length ?? 0;
    if (summaryGroupsEl) summaryGroupsEl.textContent = gCount + ' nhóm';
    if (summaryTopicsEl) summaryTopicsEl.textContent = tCount + ' chủ đề';
    if (summarySchedulesEl) summarySchedulesEl.textContent = sTotal + ' lịch';
    if (summaryLogsEl) summaryLogsEl.textContent = lCount + ' bản ghi';
  }
}

async function loadData() {
  try {
    const [groups, topics, userContents, schedules, logs] = await Promise.all([
      loadGroups(),
      loadTopics(),
      loadUserContents(),
      loadSchedules(),
      loadLogs(),
    ]);
    state.groups = groups;
    state.topics = topics;
    state.userContents = userContents;
    state.schedules = schedules;
    state.logs = logs;

    renderGroups();
    renderTopics();
    renderScheduleForm();
    updateScheduleFormFields();
    renderSchedules();
    renderLogs();
    renderDashboardSummary();
    if (typeof _checkNewLogsAndNotify === 'function') _checkNewLogsAndNotify();
    if (document.querySelector('#logsTable') && !state.logs.length) {
      setStatus('Chưa có log hoạt động. Hãy chạy một tác vụ bot để tạo bản ghi.', false);
    } else {
      setStatus('Đã tải dữ liệu từ backend.');
    }
  } catch (error) {
    console.error('Failed to load data', error);
    const message = error.message || 'Không thể kết nối backend';
    setStatus(message, true);
    // Hiển thị toast lỗi để user biết
    if (typeof showToast === 'function') {
      showToast('error', 'Lỗi tải dữ liệu', message.slice(0, 120));
    }
    // Nếu 401 - redirect login
    if (message.includes('401') || message.includes('Not authenticated') || message.includes('Unauthorized')) {
      if (typeof Auth !== 'undefined') {
        const refreshed = await Auth.refreshAccessToken();
        if (!refreshed) {
          Auth.clearTokens();
          Auth._redirectToLogin();
        } else {
          setTimeout(loadData, 500); // retry sau refresh
        }
      }
    }
  }
}

async function handleAddGroup(event) {
  event.preventDefault();
  const ten = document.querySelector('#groupName')?.value?.trim();
  const url = document.querySelector('#groupUrl')?.value?.trim();
  const ghi_chu = document.querySelector('#groupNote')?.value?.trim();
  if (!ten || !url) return;
  try {
    await createGroup({ ten, url, ghi_chu });
    await loadData();
    document.querySelector('#groupForm')?.reset();
    setStatus('Đã thêm nhóm thành công.');
  } catch (error) {
    console.error('Failed to create group', error);
    setStatus(error.message || 'Không thể thêm nhóm', true);
  }
}

async function handleAddTopic(event) {
  event.preventDefault();
  const ten = document.querySelector('#topicName')?.value?.trim();
  const mo_ta = document.querySelector('#topicDesc')?.value?.trim();
  if (!ten) return;
  try {
    await createTopic({ ten, mo_ta });
    await loadData();
    document.querySelector('#topicForm')?.reset();
    setStatus('Đã thêm chủ đề thành công.');
  } catch (error) {
    console.error('Failed to create topic', error);
    setStatus(error.message || 'Không thể thêm chủ đề', true);
  }
}

async function handleScheduleFormSubmit(event) {
  event.preventDefault();
  const type = document.querySelector('#scheduleType')?.value || 'dang-bai';
  const thu = document.querySelector('#scheduleThu')?.value?.trim();
  const gio = document.querySelector('#scheduleGio')?.value?.trim();
  try {
    if (type === 'dang-bai') {
      const topicIdRaw = document.querySelector('#scheduleTopicId')?.value;
      const topicId = topicIdRaw ? Number(topicIdRaw) : 0;

      const groupIds = parseIds(document.querySelector('#scheduleGroupIds')?.value || '');
      const dangKemAnh = Boolean(document.querySelector('#scheduleDangKemAnh')?.checked);

      const mode = document.querySelector('#scheduleDangBaiMode')?.value || 'topic';
      const contentText = mode === 'content' ? document.querySelector('#scheduleContentText')?.value?.trim() : '';
      const giuNguyenGoc = mode === 'content' ? Boolean(document.querySelector('#scheduleGiuNguyenGoc')?.checked) : true;

      if (!thu || !gio || !groupIds.length) {
        setStatus('Vui lòng nhập đủ thứ và nhóm.', true);
        return;
      }

      const imageMode = document.querySelector('input[name="schedImageMode"]:checked')?.value || 'random';
      const imagePaths = dangKemAnh && imageMode === 'manual'
        ? (typeof window.getSchedImageSelection === 'function' ? window.getSchedImageSelection() : (window._sched_selectedPaths ? [...window._sched_selectedPaths] : []))
        : [];

      if (mode === 'content') {
        if (!contentText) {
          setStatus('Vui lòng nhập nội dung bài đăng.', true);
          return;
        }
        const savedContent = await createUserContent({ noi_dung: contentText });
        await createPostSchedule({
          thu,
          gio,
          content_id: savedContent.id,
          giu_nguyen_goc: giuNguyenGoc,
          dang_kem_anh: dangKemAnh,
          image_mode: imageMode,
          image_paths: imagePaths,
          active: true,
          group_ids: groupIds,
        });
      } else {
        if (!topicId) {
          setStatus('Vui lòng chọn chủ đề.', true);
          return;
        }
        await createPostSchedule({
          thu,
          gio,
          topic_id: topicId,
          dang_kem_anh: dangKemAnh,
          image_mode: imageMode,
          image_paths: imagePaths,
          active: true,
          group_ids: groupIds,
        });
      }

    } else if (type === 'repost') {
      const soBai = Number(document.querySelector('#scheduleSoBai')?.value || 1);
      const nhomNguonIds = parseIds(document.querySelector('#scheduleNhomNguonIds')?.value || '');
      const nhomDichIds = parseIds(document.querySelector('#scheduleNhomDichIds')?.value || '');
      if (!thu || !gio) {
        setStatus('Vui lòng nhập đủ thứ và giờ.', true);
        return;
      }
      await createRepostSchedule({ thu, gio, so_bai: soBai, active: true, nhom_nguon_ids: nhomNguonIds, nhom_dich_ids: nhomDichIds });
    } else {
      const groupIds = parseIds(document.querySelector('#scheduleGroupIdsInteract')?.value || '');
      if (!thu || !gio) {
        setStatus('Vui lòng nhập đủ thứ và giờ.', true);
        return;
      }
      await createInteractSchedule({ thu, gio, active: true, group_ids: groupIds });
    }

    document.querySelector('#scheduleForm')?.reset();
    if (typeof window._resetSchedImagePicker === 'function') window._resetSchedImagePicker();
    updateScheduleFormFields();
    await loadData();
    const loaiLabel = type === 'dang-bai' ? 'Đăng bài' : type === 'repost' ? 'Repost' : 'Tương tác';
    if (typeof showToast === 'function') showToast('success', `Tạo lịch thành công! 📅`, `Lịch ${loaiLabel} đã được lưu và kích hoạt.`);
    if (typeof addNotification === 'function') addNotification('📅', `Đã lên lịch ${loaiLabel}`, `Lịch chạy vào ${thu} lúc ${gio} đã được kích hoạt.`);
  } catch (error) {
    console.error('Failed to create schedule', error);
    if (typeof showToast === 'function') showToast('error', 'Không thể tạo lịch', error.message || '');
    if (typeof addNotification === 'function') addNotification('❌', 'Tạo lịch thất bại', error.message || '');
    setStatus(error.message || 'Không thể tạo lịch', true);
  }
}

async function handleEditOrDelete(event) {
  const button = event.target.closest('button[data-action]');

  if (!button) return;
  const action = button.dataset.action;
  const id = button.dataset.id;

  if (action === 'delete-group') {
    await deleteGroup(id);
    await loadData();
    if (typeof showToast === 'function') showToast('info', 'Đã xóa nhóm');
  } else if (action === 'delete-topic') {
    await deleteTopic(id);
    await loadData();
    if (typeof showToast === 'function') showToast('info', 'Đã xóa chủ đề');
  } else if (action === 'delete-post-schedule') {
    await deletePostSchedule(id);
    await loadData();
    if (typeof showToast === 'function') showToast('info', 'Đã xóa lịch đăng bài');
  } else if (action === 'delete-repost-schedule') {
    await deleteRepostSchedule(id);
    await loadData();
    if (typeof showToast === 'function') showToast('info', 'Đã xóa lịch repost');
  } else if (action === 'delete-interact-schedule') {
    await deleteInteractSchedule(id);
    await loadData();
    if (typeof showToast === 'function') showToast('info', 'Đã xóa lịch tương tác');
  } else if (action === 'edit-post-schedule') {
    const schedule = state.schedules.posts.find(item => String(item.id) === String(id));
    if (!schedule) return;
    openEditPostModal(schedule);
  } else if (action === 'edit-repost-schedule') {
    const schedule = state.schedules.reposts.find(item => String(item.id) === String(id));
    if (!schedule) return;
    const thu = prompt('Thứ mới', schedule.thu || '');
    const gio = prompt('Giờ mới', schedule.gio || '');
    const so_bai = Number(prompt('Số bài mới', String(schedule.so_bai || 1)) || schedule.so_bai || 1);
    if (thu !== null && gio !== null) {
      await updateRepostSchedule(id, { thu, gio, so_bai });
      await loadData();
      setStatus('Đã cập nhật lịch repost.');
    }
  } else if (action === 'edit-interact-schedule') {
    const schedule = state.schedules.interacts.find(item => String(item.id) === String(id));
    if (!schedule) return;
    const thu = prompt('Thứ mới', schedule.thu || '');
    const gio = prompt('Giờ mới', schedule.gio || '');
    if (thu !== null && gio !== null) {
      await updateInteractSchedule(id, { thu, gio });
      await loadData();
      setStatus('Đã cập nhật lịch tương tác.');
    }
  } else if (action === 'edit-group') {
    const group = state.groups.find(g => String(g.id) === String(id));
    if (!group) return;
    openEditGroupModal(group);
  } else if (action === 'edit-topic') {
    const topic = state.topics.find(t => String(t.id) === String(id));
    if (!topic) return;
    openEditTopicModal(topic);
  }
}

// ============================================================
// MODAL SỬA NHÓM
// ============================================================
let _editingGroupId = null;

function openEditGroupModal(group) {
  _editingGroupId = group.id;
  const modal = document.querySelector('#editGroupModal');
  if (!modal) return;
  document.querySelector('#editGroupTen').value = group.ten || '';
  document.querySelector('#editGroupUrl').value = group.url || '';
  document.querySelector('#editGroupGhiChu').value = group.ghi_chu || '';
  modal.style.display = 'flex';
}

async function submitEditGroup() {
  if (!_editingGroupId) return;
  const ten = document.querySelector('#editGroupTen').value.trim();
  const url = document.querySelector('#editGroupUrl').value.trim();
  const ghi_chu = document.querySelector('#editGroupGhiChu').value.trim();
  if (!ten || !url) { alert('Vui lòng nhập tên và URL nhóm.'); return; }
  try {
    await updateGroup(_editingGroupId, { ten, url, ghi_chu });
    document.querySelector('#editGroupModal').style.display = 'none';
    _editingGroupId = null;
    await loadData();
    setStatus('Đã cập nhật nhóm.');
  } catch (err) {
    alert('Lỗi: ' + (err.message || 'Không thể cập nhật nhóm'));
  }
}

// ============================================================
// MODAL SỬA CHỦ ĐỀ
// ============================================================
let _editingTopicId = null;

function openEditTopicModal(topic) {
  _editingTopicId = topic.id;
  const modal = document.querySelector('#editTopicModal');
  if (!modal) return;
  document.querySelector('#editTopicTen').value = topic.ten || '';
  document.querySelector('#editTopicMoTa').value = topic.mo_ta || '';
  modal.style.display = 'flex';
}

async function submitEditTopic() {
  if (!_editingTopicId) return;
  const ten = document.querySelector('#editTopicTen').value.trim();
  const mo_ta = document.querySelector('#editTopicMoTa').value.trim();
  if (!ten) { alert('Vui lòng nhập tên chủ đề.'); return; }
  try {
    await updateTopic(_editingTopicId, { ten, mo_ta });
    document.querySelector('#editTopicModal').style.display = 'none';
    _editingTopicId = null;
    await loadData();
    setStatus('Đã cập nhật chủ đề.');
  } catch (err) {
    alert('Lỗi: ' + (err.message || 'Không thể cập nhật chủ đề'));
  }
}

// ============================================================
// MODAL SỬA LỊCH ĐĂNG BÀI
// ============================================================
let _editingPostId = null;

function openEditPostModal(schedule) {
  _editingPostId = schedule.id;
  const modal = document.querySelector('#editPostModal');
  if (!modal) return;

  document.querySelector('#editThu').value = schedule.thu || '';
  document.querySelector('#editGio').value = schedule.gio || '';
  document.querySelector('#editDangKemAnh').checked = !!schedule.dang_kem_anh;
  if (typeof window.setEditSchedImageState === 'function') {
    window.setEditSchedImageState({
      enabled: !!schedule.dang_kem_anh,
      mode: schedule.image_mode || 'random',
      paths: schedule.image_paths || [],
    });
  }

  // Populate topic select
  const topicSel = document.querySelector('#editTopicId');
  if (topicSel) {
    topicSel.innerHTML = ['<option value="">-- Chọn chủ đề --</option>',
      ...state.topics.map(t => `<option value="${t.id}">${escapeHtml(t.ten)}</option>`)
    ].join('');
  }

  // Xác định mode hiện tại
  const mode = schedule.content ? 'content' : 'topic';
  document.querySelector('#editMode').value = mode;

  if (mode === 'topic' && schedule.topic) {
    if (topicSel) topicSel.value = String(schedule.topic.id);
  }
  if (mode === 'content' && schedule.content) {
    document.querySelector('#editContentText').value = schedule.content.noi_dung || '';
    document.querySelector('#editGiuNguyen').checked = schedule.giu_nguyen_goc !== false;
  }

  document.querySelector('#editGroupIds').value = (schedule.groups || []).map(g => g.id).join(',');

  toggleEditModeFields(mode);
  modal.style.display = 'flex';
  document.querySelector('#editMode').onchange = () => toggleEditModeFields(document.querySelector('#editMode').value);
}

function toggleEditModeFields(mode) {
  const topicField = document.querySelector('#editTopicField');
  const contentField = document.querySelector('#editContentField');
  const giuNguyenField = document.querySelector('#editGiuNguyenField');
  if (topicField) topicField.style.display = mode === 'topic' ? '' : 'none';
  if (contentField) contentField.style.display = mode === 'content' ? '' : 'none';
  if (giuNguyenField) giuNguyenField.style.display = mode === 'content' ? '' : 'none';
}

function closeEditModal() {
  const modal = document.querySelector('#editPostModal');
  if (modal) modal.style.display = 'none';
  _editingPostId = null;
}

async function submitEditPost() {
  if (!_editingPostId) return;
  const thu = document.querySelector('#editThu').value.trim();
  const gio = document.querySelector('#editGio').value.trim();
  const mode = document.querySelector('#editMode').value;
  const groupIds = parseIds(document.querySelector('#editGroupIds').value || '');
  const dangKemAnh = document.querySelector('#editDangKemAnh').checked;
  const imageMode = document.querySelector('input[name="editSchedImageMode"]:checked')?.value || 'random';
  const imagePaths = dangKemAnh && imageMode === 'manual'
    ? (typeof window.getEditSchedImageSelection === 'function' ? window.getEditSchedImageSelection() : [])
    : [];

  if (!thu || !gio) { alert('Vui lòng nhập thứ và giờ.'); return; }
  if (!groupIds.length) { alert('Vui lòng nhập ít nhất 1 nhóm ID.'); return; }

  if (dangKemAnh && imageMode === 'manual' && !imagePaths.length) {
    alert('Vui long chon it nhat 1 anh hoac chuyen sang Random.');
    return;
  }

  const payload = {
    thu,
    gio,
    dang_kem_anh: dangKemAnh,
    image_mode: imageMode,
    image_paths: imagePaths,
    group_ids: groupIds,
  };

  try {
    if (mode === 'topic') {
      const topicId = Number(document.querySelector('#editTopicId').value);
      if (!topicId) { alert('Vui lòng chọn chủ đề.'); return; }
      payload.topic_id = topicId;
      payload.content_id = null;
    } else {
      const contentText = document.querySelector('#editContentText').value.trim();
      if (!contentText) { alert('Vui lòng nhập nội dung.'); return; }
      const saved = await createUserContent({ noi_dung: contentText });
      payload.content_id = saved.id;
      payload.topic_id = null;
      payload.giu_nguyen_goc = document.querySelector('#editGiuNguyen').checked;
    }

    await updatePostSchedule(_editingPostId, payload);
    closeEditModal();
    await loadData();
    setStatus('Đã cập nhật lịch đăng bài.');
  } catch (err) {
    console.error('submitEditPost error:', err);
    alert('Lỗi: ' + (err.message || 'Không thể cập nhật lịch'));
  }
}

function handleCreateRoute() {
  const params = new URLSearchParams(window.location.search);
  if (params.get('mode') !== 'create') return;

  const form = document.querySelector('#scheduleForm');
  const input = document.querySelector('#scheduleThu');
  if (!form || !input) return;

  setTimeout(() => {
    form.scrollIntoView({ behavior: 'smooth', block: 'start' });
    input.focus();
  }, 120);
}



function init() {
  // Đảm bảo Auth được load trước
  if (typeof Auth === 'undefined') {
    console.error('[app.js] Auth not loaded — auth.js must be loaded before app.js');
    setStatus('Lỗi: không load được auth.js. Vui lòng refresh trang.', true);
    return;
  }

  // Kiểm tra token ngay — nếu không có thì redirect luôn không cần gọi API
  const token = Auth.getAccessToken();
  if (!token) {
    console.warn('[app.js] No token found, redirecting to login');
    Auth._redirectToLogin();
    return;
  }

  // Chờ Auth guard trước khi load data — tránh 401 khi chưa có token
  Auth.guardPage().then(ok => {
    if (!ok) return; // guardPage đã redirect sang login
    _initAfterAuth();
  }).catch(err => {
    console.error('[app.js] guardPage error:', err);
    setStatus('Lỗi xác thực. Vui lòng đăng nhập lại.', true);
    Auth._redirectToLogin();
  });
}

function _initAfterAuth() {
  loadData();
  handleCreateRoute();
  document.querySelector('#groupForm')?.addEventListener('submit', handleAddGroup);
  document.querySelector('#topicForm')?.addEventListener('submit', handleAddTopic);
  document.querySelector('#scheduleForm')?.addEventListener('submit', handleScheduleFormSubmit);
  document.querySelector('#scheduleType')?.addEventListener('change', updateScheduleFormFields);
  document.querySelector('#groupsTable')?.addEventListener('click', handleEditOrDelete);
  document.querySelector('#topicsTable')?.addEventListener('click', handleEditOrDelete);
  document.querySelector('#schedulesRoot')?.addEventListener('click', handleEditOrDelete);
  document.querySelector('#scheduleDangBaiMode')?.addEventListener('change', updateScheduleFormFields);
}

document.addEventListener('DOMContentLoaded', init);


// ============================================================
// DASHBOARD NÂNG CAO
// ============================================================
function renderDashboardEnhanced() {
  // Stats
  const groupCountEl = document.querySelector('#dashboardGroupCount');
  const scheduleCountEl = document.querySelector('#dashboardScheduleCount');
  const todayCountEl = document.querySelector('#dashboardTodayCount');
  const errorCountEl = document.querySelector('#dashboardErrorCount');
  if (!groupCountEl) return;

  const totalSchedules = (state.schedules.posts?.length || 0)
    + (state.schedules.reposts?.length || 0)
    + (state.schedules.interacts?.length || 0);
  const today = new Date().toISOString().slice(0, 10);
  const todayLogs = (state.logs || []).filter(l => String(l.bat_dau || '').startsWith(today));
  const todayOk = todayLogs.filter(l => l.trang_thai === 'success').length;
  const todayErr = todayLogs.filter(l => l.trang_thai === 'error').length;

  if (groupCountEl) groupCountEl.textContent = String(state.groups?.length || 0);
  if (scheduleCountEl) scheduleCountEl.textContent = String(totalSchedules);
  if (todayCountEl) todayCountEl.textContent = String(todayOk);
  if (errorCountEl) errorCountEl.textContent = String(todayErr);

  // Bot status badge
  const statusBadge = document.querySelector('#botStatus');
  if (statusBadge) {
    if (todayErr === 0 && todayOk > 0) {
      statusBadge.className = 'badge badge-success';
      statusBadge.innerHTML = '<span class="dot dot-success"></span> Bot hoạt động tốt';
    } else if (todayErr > 0) {
      statusBadge.className = 'badge badge-warning';
      statusBadge.innerHTML = '<span class="dot dot-warning"></span> Có lỗi xảy ra';
    } else {
      statusBadge.className = 'badge badge-idle';
      statusBadge.innerHTML = '<span class="dot dot-idle"></span> Chưa có hoạt động';
    }
  }

  // Recent logs table
  const logsEl = document.querySelector('#dashboardRecentLogs');
  if (logsEl) {
    const recent = (state.logs || []).slice(0, 8);
    if (!recent.length) {
      logsEl.innerHTML = `<tr><td colspan="4" style="text-align:center;color:var(--text-faint);padding:20px;">Chưa có hoạt động nào</td></tr>`;
    } else {
      const TYPE_MAP = {
        dang_bai:'📝 Đăng bài', 'dang-bai':'📝 Đăng bài', post:'📝 Đăng bài',
        repost:'🔁 Repost',
        tuong_tac:'💬 Tương tác', 'tuong-tac':'💬 Tương tác', interact:'💬 Tương tác',
        fanpage:'📄 Fanpage', fanpage_v2:'📄 Fanpage',
      };
      logsEl.innerHTML = recent.map(log => {
        const statusClass = log.trang_thai === 'success' ? 'dot-success' : log.trang_thai === 'error' ? 'dot-danger' : 'dot-warning';
        const time = String(log.bat_dau || '').replace('T', ' ').slice(0, 16);
        const typeKey = String(log.loai || '').toLowerCase();
        const typeLabel = TYPE_MAP[typeKey] || escapeHtml(log.loai || '—');
        const detail = _dashFormatDetail(log.chi_tiet || '');
        return `<tr>
          <td style="font-family:var(--font-mono);font-size:12px;color:var(--text-faint);white-space:nowrap;">${escapeHtml(time)}</td>
          <td style="font-size:12.5px;">${typeLabel}</td>
          <td><span class="dot ${statusClass}" style="display:inline-block;margin-right:4px;"></span><span style="font-size:12.5px;">${escapeHtml(log.trang_thai || '')}</span></td>
          <td style="max-width:240px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12.5px;">${detail}</td>
        </tr>`;
      }).join('');
    }
  }

  // Upcoming schedules
  const upcomingEl = document.querySelector('#dashboardUpcoming');
  if (upcomingEl) {
    const all = [
      ...(state.schedules.posts || []).map(s => ({ ...s, loai: '📝 Đăng bài' })),
      ...(state.schedules.reposts || []).map(s => ({ ...s, loai: '🔁 Repost' })),
      ...(state.schedules.interacts || []).map(s => ({ ...s, loai: '💬 Tương tác' })),
    ].filter(s => s.active).sort((a, b) => String(a.gio || '').localeCompare(String(b.gio || '')));

    if (!all.length) {
      upcomingEl.innerHTML = `<div style="text-align:center;color:var(--text-faint);font-size:13px;padding:16px;">Chưa có lịch nào</div>`;
    } else {
      upcomingEl.innerHTML = all.slice(0, 5).map(s => {
        const desc = s.topic?.ten || (s.content?.noi_dung ? s.content.noi_dung.slice(0, 40) + '…' : '');
        return `<div class="upcoming-item">
          <span class="upcoming-dot"></span>
          <span class="upcoming-time">${escapeHtml(s.thu || '')} ${escapeHtml(s.gio || '')}</span>
          <span class="upcoming-desc">${desc ? escapeHtml(desc) : (s.groups?.map(g => g.ten).join(', ') || '')}</span>
          <span class="upcoming-type">${s.loai}</span>
        </div>`;
      }).join('');
    }
  }

  // Bug 4 fix: fill summary panel elements directly
  const summaryGroupsEl = document.getElementById('summaryGroups');
  const summaryTopicsEl = document.getElementById('summaryTopics');
  const summarySchedulesEl = document.getElementById('summarySchedules');
  const summaryLogsEl = document.getElementById('summaryLogs');
  if (summaryGroupsEl || summaryTopicsEl || summarySchedulesEl || summaryLogsEl) {
    const gCount = state.groups?.length ?? 0;
    const tCount = state.topics?.length ?? 0;
    const sTotal = (state.schedules?.posts?.length || 0) + (state.schedules?.reposts?.length || 0) + (state.schedules?.interacts?.length || 0);
    const lCount = state.logs?.length ?? 0;
    if (summaryGroupsEl) summaryGroupsEl.textContent = gCount + ' nhóm';
    if (summaryTopicsEl) summaryTopicsEl.textContent = tCount + ' chủ đề';
    if (summarySchedulesEl) summarySchedulesEl.textContent = sTotal + ' lịch';
    if (summaryLogsEl) summaryLogsEl.textContent = lCount + ' bản ghi';
  }
}

// ============================================================
// SETTINGS PAGE
// ============================================================
async function loadSettingsPage() {
  const statusEl = document.querySelector('#status');
  try {
    const cfg = await loadSettings();
    if (!cfg) return;
    const wtEl  = document.querySelector('#settingWaitTime');
    const llEl  = document.querySelector('#settingLikeLimit');
    const clEl  = document.querySelector('#settingCommentLimit');
    const imgEl = document.querySelector('#settingImageDir');
    const hlEl  = document.querySelector('#settingHeadless');
    const hlLbl = document.querySelector('#headlessLabel');
    if (wtEl)  wtEl.value   = cfg.thoi_gian_cho_giua_cac_nhom || '';
    if (llEl)  llEl.value   = cfg.gioi_han_like || '';
    if (clEl)  clEl.value   = cfg.gioi_han_comment || '';
    if (imgEl) imgEl.value  = cfg.thu_muc_anh || '';
    if (hlEl)  hlEl.checked = !!cfg.headless_mode;
    if (hlLbl) {
      const lang = localStorage.getItem('fbbot-lang') || 'vi';
      hlLbl.textContent = cfg.headless_mode
        ? (lang === 'en' ? 'Enabled' : 'Đang bật')
        : (lang === 'en' ? 'Disabled' : 'Đang tắt');
    }

    const backendEl = document.querySelector('#backendStatus');
    if (backendEl) {
      backendEl.className = 'badge badge-success';
      backendEl.innerHTML = '<span class="dot dot-success"></span> Đang kết nối';
    }
  } catch (err) {
    const backendEl = document.querySelector('#backendStatus');
    if (backendEl) {
      backendEl.className = 'badge badge-danger';
      backendEl.innerHTML = '<span class="dot dot-danger"></span> Mất kết nối';
    }
    if (statusEl) { statusEl.textContent = 'Không thể tải cài đặt: ' + (err.message || ''); statusEl.style.color = 'var(--danger)'; }
  }
}

async function saveSettings() {
  const payload = {};
  const wtEl  = document.querySelector('#settingWaitTime');
  const llEl  = document.querySelector('#settingLikeLimit');
  const clEl  = document.querySelector('#settingCommentLimit');
  const imgEl = document.querySelector('#settingImageDir');
  const hlEl  = document.querySelector('#settingHeadless');

  if (wtEl?.value)  payload.thoi_gian_cho_giua_cac_nhom = Number(wtEl.value);
  if (llEl?.value)  payload.gioi_han_like    = Number(llEl.value);
  if (clEl?.value)  payload.gioi_han_comment = Number(clEl.value);
  if (imgEl)         payload.thu_muc_anh      = imgEl.value.trim();
  if (hlEl)         payload.headless_mode    = hlEl.checked;

  const saveBtn = document.querySelector('#saveSettingsBtn');
  try {
    await saveSettingsApi(payload);
    if (saveBtn) {
      const orig = saveBtn.innerHTML;
      saveBtn.innerHTML = '✅ Đã lưu';
      saveBtn.disabled = true;
      setTimeout(() => { saveBtn.innerHTML = orig; saveBtn.disabled = false; }, 2000);
    }
    if (typeof showToast === 'function') showToast('success', 'Đã lưu cài đặt');
  } catch (err) {
    setStatus('❌ Lỗi: ' + (err.message || 'Không thể lưu cài đặt'), true);
  }
}

async function chooseImageDirectory() {
  const host = window.location.hostname;
  const canOpenServerDialog = ['localhost', '127.0.0.1'].includes(host) || /^192\.168\.|^10\.|^172\.(1[6-9]|2\d|3[01])\./.test(host);
  if (!canOpenServerDialog) {
    const msg = 'Qua ngrok/dien thoai khong mo duoc hop thoai folder local. Hay nhap duong dan tren may dang chay bot.';
    if (typeof showToast === 'function') showToast('info', 'Nhap duong dan thu muc', msg);
    else alert(msg);
    document.querySelector('#settingImageDir')?.focus();
    return;
  }
  const imgEl = document.querySelector('#settingImageDir');
  const btn = document.querySelector('button[onclick="chooseImageDirectory()"]');
  const oldText = btn?.innerHTML;
  try {
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = 'Đang mở...';
    }
    const result = await selectImageDirectory();
    if (result?.path && imgEl) {
      imgEl.value = result.path;
      imgEl.focus();
    }
  } catch (err) {
    if (typeof showToast === 'function') showToast('error', 'Không mở được chọn thư mục', err.message || '');
    else alert('Không mở được chọn thư mục: ' + (err.message || ''));
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = oldText || '📁 Chọn thư mục';
    }
  }
}

function syncImageDirectoryPickerMode() {
  const host = window.location.hostname;
  const canOpenServerDialog = ['localhost', '127.0.0.1'].includes(host) || /^192\.168\.|^10\.|^172\.(1[6-9]|2\d|3[01])\./.test(host);
  const btn = document.querySelector('#chooseImageDirBtn');
  if (!btn) return;
  if (!canOpenServerDialog) {
    btn.textContent = 'Nhập tay';
    btn.title = 'Trình duyệt từ xa không thể chọn thư mục local. Nhập đường dẫn trên máy chạy bot.';
  }
}

// Auto-load settings page
document.addEventListener('DOMContentLoaded', () => {
  if (document.querySelector('#settingWaitTime')) {
    syncImageDirectoryPickerMode();
    loadSettingsPage();
  }
});

// ============================================================
// TOAST NOTIFICATION SYSTEM
// ============================================================
const _toastIcons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
const _toastDurations = { success: 3500, error: 6000, warning: 5000, info: 4000 };

function showToast(type, title, msg = '', duration = null) {
  const container = document.querySelector('#toastContainer');
  if (!container) return;

  const d = duration || _toastDurations[type] || 4000;
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.style.position = 'relative';
  toast.innerHTML = `
    <span class="toast-icon">${_toastIcons[type] || 'ℹ️'}</span>
    <div class="toast-body">
      <div class="toast-title">${escapeHtml(title)}</div>
      ${msg ? `<div class="toast-msg">${escapeHtml(msg)}</div>` : ''}
    </div>
    <span class="toast-close" onclick="this.closest('.toast').remove()">✕</span>
    <div class="toast-progress" style="animation-duration:${d}ms;"></div>
  `;
  toast.addEventListener('click', () => _dismissToast(toast));
  container.appendChild(toast);
  setTimeout(() => _dismissToast(toast), d);

  // Thêm vào notification panel nếu có
  _addToNotifPanel(type, title, msg);
}

function _dismissToast(toast) {
  if (!toast || !toast.parentNode) return;
  toast.classList.add('hiding');
  setTimeout(() => toast.remove(), 220);
}

// ============================================================
// NOTIFICATION PANEL
// ============================================================
const _notifications = [];

function _addToNotifPanel(type, title, msg) {
  _notifications.unshift({ type, title, msg, time: new Date(), unread: true });
  _renderNotifPanel();
  _updateNotifBadge();
}

function _renderNotifPanel() {
  const list = document.querySelector('#notifList');
  if (!list) return;
  if (!_notifications.length) {
    list.innerHTML = '<div class="notif-empty">Chưa có thông báo nào</div>';
    return;
  }
  list.innerHTML = _notifications.slice(0, 30).map((n, i) => {
    const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
    const timeStr = n.time.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
    return `<div class="notif-item ${n.unread ? 'unread' : ''}" onclick="_markRead(${i})">
      <span class="notif-item-icon">${icons[n.type] || 'ℹ️'}</span>
      <div class="notif-item-body">
        <div class="notif-item-title">${escapeHtml(n.title)}</div>
        ${n.msg ? `<div class="notif-item-msg">${escapeHtml(n.msg)}</div>` : ''}
        <div class="notif-item-time">${timeStr}</div>
      </div>
    </div>`;
  }).join('');
}

function _markRead(idx) {
  if (_notifications[idx]) _notifications[idx].unread = false;
  _renderNotifPanel();
  _updateNotifBadge();
}

function _updateNotifBadge() {
  const badge = document.querySelector('#notifCount');
  if (!badge) return;
  const unread = _notifications.filter(n => n.unread).length;
  badge.textContent = String(unread);
  badge.style.display = unread > 0 ? 'flex' : 'none';
}

function toggleNotifPanel() {
  const panel = document.querySelector('#notifPanel');
  if (!panel) return;
  const isVisible = panel.style.display !== 'none';
  panel.style.display = isVisible ? 'none' : 'flex';
  if (!isVisible) {
    // Mark all read khi mở panel
    _notifications.forEach(n => n.unread = false);
    _renderNotifPanel();
    _updateNotifBadge();
  }
}

function clearNotifications() {
  _notifications.length = 0;
  _renderNotifPanel();
  _updateNotifBadge();
}

// Đóng panel khi click ngoài
document.addEventListener('click', e => {
  const panel = document.querySelector('#notifPanel');
  const bell = document.querySelector('#notifBell');
  if (panel && bell && !panel.contains(e.target) && !bell.contains(e.target)) {
    panel.style.display = 'none';
  }
});

// ============================================================
// RELOAD
// ============================================================
async function reloadDashboard() {
  const icon = document.querySelector('#reloadIcon');
  if (icon) { icon.style.animation = 'spin 0.6s linear infinite'; icon.style.display = 'inline-block'; }
  try {
    await loadData();
    showToast('success', 'Đã tải lại dữ liệu');
  } catch (e) {
    showToast('error', 'Không thể tải lại', e.message || '');
  } finally {
    if (icon) { icon.style.animation = ''; }
  }
}

// ============================================================
// HOOK VÀO loadData ĐỂ PHÁT THÔNG BÁO TỪ LOGS
// ============================================================
let _lastKnownLogId = null;

function _checkNewLogsAndNotify() {
  if (!state.logs || !state.logs.length) return;
  const latest = state.logs[0];
  if (_lastKnownLogId === null) {
    // Lần đầu load — ghi nhớ id mới nhất, không thông báo
    _lastKnownLogId = latest.id;
    return;
  }
  if (latest.id === _lastKnownLogId) return;

  // Có log mới kể từ lần load trước
  const newLogs = state.logs.filter(l => l.id > _lastKnownLogId);
  _lastKnownLogId = state.logs[0].id;

  newLogs.forEach(log => {
    const loaiLabel = { dang_bai: 'Đăng bài', repost: 'Repost', tuong_tac: 'Tương tác' }[log.loai] || log.loai;
    if (log.trang_thai === 'success') {
      const detail = log.chi_tiet || '';
      const isPending = detail.includes('PENDING');
      const isUnconfirmed = detail.includes('ERROR_UNCONFIRMED');
      if (isPending) {
        showToast('warning', `${loaiLabel} — Chờ duyệt`, 'Bài đăng đang chờ quản trị viên duyệt.');
      } else if (isUnconfirmed) {
        showToast('warning', `${loaiLabel} — Chưa xác nhận`, 'Đã click Đăng nhưng không xác nhận được kết quả.');
      } else {
        showToast('success', `${loaiLabel} thành công! 🎉`, detail.slice(0, 80));
      }
    } else if (log.trang_thai === 'error') {
      showToast('error', `${loaiLabel} thất bại`, (log.chi_tiet || '').slice(0, 100));
    }
  });
}

// Patch loadData để gọi _checkNewLogsAndNotify sau mỗi lần load
// Không override function — gọi trực tiếp từ loadData

// ============================================================
// HEALTH CHECK — API & DATABASE
// ============================================================
const _healthState = { api: null, db: null };

async function _checkHealth() {
  // Thử gọi một endpoint nhẹ để kiểm tra API
  let apiOk = false;
  let dbOk = false;

  try {
    const res = await Promise.race([
      fetch(`http://${window.location.hostname}:8000/groups/`),
      new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), 5000))
    ]);
    apiOk = res.ok || res.status < 500;
    // Nếu API trả về dữ liệu => DB cũng OK (MongoDB connected)
    dbOk = res.ok;
  } catch (_) {
    // Thử port 8005
    try {
      const res2 = await Promise.race([
        fetch(`http://${window.location.hostname}:8005/groups/`),
        new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), 5000))
      ]);
      apiOk = res2.ok || res2.status < 500;
      dbOk = res2.ok;
    } catch (_2) {
      apiOk = false;
      dbOk = false;
    }
  }

  // API status thay đổi
  if (_healthState.api !== null && _healthState.api !== apiOk) {
    if (apiOk) {
      if (typeof showToast === 'function') showToast('success', '🟢 Kết nối API', 'Backend đã hoạt động trở lại.');
    } else {
      if (typeof showToast === 'function') showToast('error', '🔴 Mất kết nối API', 'Không thể kết nối tới backend server.', 8000);
    }
  }
  // DB status thay đổi
  if (_healthState.db !== null && _healthState.db !== dbOk) {
    if (dbOk) {
      if (typeof showToast === 'function') showToast('success', '🟢 Database OK', 'MongoDB kết nối thành công.');
    } else {
      if (typeof showToast === 'function') showToast('warning', '⚠️ Database lỗi', 'Backend kết nối được nhưng DB có vấn đề.', 8000);
    }
  }

  _healthState.api = apiOk;
  _healthState.db = dbOk;

  // Cập nhật badge trạng thái trên dashboard
  const backendBadge = document.querySelector('#backendStatus');
  if (backendBadge) {
    backendBadge.className = apiOk ? 'badge badge-success' : 'badge badge-danger';
    backendBadge.innerHTML = apiOk
      ? '<span class="dot dot-success"></span> Đang kết nối'
      : '<span class="dot dot-danger"></span> Mất kết nối';
  }

  // Cập nhật global bar
  const apiDot = document.querySelector('#globalApiStatus');
  const dbDot = document.querySelector('#globalDbStatus');
  const botBadge = document.querySelector('#globalBotStatus');

  if (apiDot) {
    const dotEl = apiDot.querySelector('.dot');
    if (dotEl) {
      dotEl.className = `dot ${apiOk ? 'dot-success' : 'dot-danger'}`;
    }
    apiDot.title = apiOk ? 'API: Đang kết nối' : 'API: Mất kết nối';
  }

  if (dbDot) {
    const dotEl = dbDot.querySelector('.dot');
    if (dotEl) {
      dotEl.className = `dot ${dbOk ? 'dot-success' : 'dot-warning'}`;
    }
    dbDot.title = dbOk ? 'Database: OK' : 'Database: Lỗi';
  }

  if (botBadge) {
    if (!apiOk) {
      botBadge.className = 'badge badge-danger';
      botBadge.innerHTML = '<span class="dot dot-danger"></span> Offline';
    } else {
      // Cập nhật từ state nếu có
      const today = new Date().toISOString().slice(0, 10);
      const todayLogs = (window.state?.logs || []).filter(l => String(l.bat_dau || '').startsWith(today));
      const hasErr = todayLogs.some(l => l.trang_thai === 'error');
      const hasOk = todayLogs.some(l => l.trang_thai === 'success');
      if (hasErr) {
        botBadge.className = 'badge badge-warning';
        botBadge.innerHTML = '<span class="dot dot-warning"></span> Có lỗi xảy ra';
      } else if (hasOk) {
        botBadge.className = 'badge badge-success';
        botBadge.innerHTML = '<span class="dot dot-success"></span> Hoạt động tốt';
      } else {
        botBadge.className = 'badge badge-idle';
        botBadge.innerHTML = '<span class="dot dot-idle"></span> Sẵn sàng';
      }
    }
  }
}

// Chạy health check ngay khi tải trang, sau đó mỗi 30 giây
document.addEventListener('DOMContentLoaded', () => {
  // Delay nhẹ để không đụng với loadData()
  setTimeout(_checkHealth, 1500);
  setInterval(_checkHealth, 30000);
});
