// ============================================================
// i18n.js — Internationalization (vi / en)
// Cách dùng: đặt data-i18n="key" trên element,
//            gọi applyLang(lang) để áp dụng dịch.
// ============================================================

const TRANSLATIONS = {
  vi: {
    // Nav
    'nav.dashboard':  'Dashboard',
    'nav.groups':     'Nhóm',
    'nav.topics':     'Chủ Đề',
    'nav.schedules':  'Lịch Nhóm',
    'nav.logs':       'Logs',
    'nav.settings':   'Cài đặt',

    // Global bar
    'bar.online':     'Online',

    // Dashboard
    'dash.title':          'Dashboard',
    'dash.sub':            'Theo dõi hoạt động của bot và quản lý toàn bộ hệ thống từ đây.',
    'dash.eyebrow':        'Tổng quan',
    'dash.bot_running':    'Hệ thống đang hoạt động',
    'dash.bot_sub':        'Tất cả dịch vụ online',
    'dash.no_data':        'Chưa có dữ liệu',
    'dash.stat_groups':    'Nhóm FB',
    'dash.stat_schedules': 'Lịch chạy',
    'dash.stat_today':     'Thành công hôm nay',
    'dash.stat_errors':    'Lỗi hôm nay',
    'dash.managing':       'đang quản lý',
    'dash.total_sched':    'tổng lịch',
    'dash.runs_ok':        'lần chạy OK',
    'dash.need_check':     'cần xem lại',
    'dash.quick_groups':   'Quản lý nhóm',
    'dash.quick_topics':   'Chủ đề AI',
    'dash.quick_schedules':'Lịch đăng',
    'dash.quick_logs':     'Xem Logs',
    'dash.quick_create':   'Tạo lịch mới',
    'dash.recent':         'Hoạt động gần đây',
    'dash.see_all':        'Xem tất cả →',
    'dash.upcoming':       'Lịch sắp chạy',
    'dash.manage':         'Quản lý →',
    'dash.summary':        'Tóm tắt hệ thống',

    // Groups
    'groups.title':       'Quản lý nhóm',
    'groups.sub':         'Danh sách các nhóm Facebook bot đăng bài, repost và tương tác.',
    'groups.eyebrow':     'Quản lý',
    'groups.add':         'Thêm nhóm mới',
    'groups.name_ph':     'Tên nhóm (VD: Cộng đồng mua bán HN)',
    'groups.url_ph':      'facebook.com/groups/...',
    'groups.note_ph':     'Ghi chú (không bắt buộc)',
    'groups.save':        '＋ Lưu nhóm',
    'groups.list':        'Danh sách nhóm',
    'groups.total':       'Tổng nhóm',
    'groups.active':      'Đang hoạt động',
    'groups.running':     'Lịch đang chạy',
    'groups.edit':        '✏️ Sửa',
    'groups.delete':      '🗑 Xóa',
    'groups.view_card':   '⊞ Thẻ',
    'groups.view_table':  '☰ Bảng',
    'groups.modal_title': '✏️ Sửa nhóm',
    'groups.cancel':      'Hủy',
    'groups.save_btn':    '💾 Lưu',

    // Topics
    'topics.title':    'Quản lý chủ đề',
    'topics.sub':      'Các chủ đề nội dung để bot tự chọn khi lên lịch đăng bài.',
    'topics.eyebrow':  'Nội dung',
    'topics.add':      'Thêm chủ đề mới',
    'topics.name_ph':  'VD: Mẹo nấu ăn, Review công nghệ...',
    'topics.desc_ph':  'Mô tả để AI hiểu rõ hơn khi viết nội dung (không bắt buộc)',
    'topics.save':     '＋ Lưu chủ đề',
    'topics.list':     'Danh sách chủ đề',
    'topics.total':    'Tổng chủ đề',
    'topics.with_desc':'Có mô tả',
    'topics.in_sched': 'Dùng trong lịch',
    'topics.no_desc':  'Chưa có mô tả',

    // Schedules
    'sched.title':    'Quản lý lịch',
    'sched.sub':      'Tạo và theo dõi lịch đăng bài, repost, tương tác theo thứ và giờ.',
    'sched.eyebrow':  'Tự động hoá',
    'sched.create':   '➕ Tạo lịch mới',
    'sched.post':     '📝 Đăng bài',
    'sched.repost':   '🔁 Repost',
    'sched.interact': '💬 Tương tác',
    'sched.day_ph':   'Thứ 2, Thứ 3, Chủ nhật...',
    'sched.time_ph':  '08:00',
    'sched.mode':     'Kiểu đăng',
    'sched.by_topic': '🏷️ Theo chủ đề (AI viết)',
    'sched.by_content':'📝 Nội dung tự soạn',
    'sched.topic_lbl':'Chủ đề',
    'sched.content_ph':'Nhập nội dung bạn muốn đăng...',
    'sched.groups_ph':'1, 2, 3',
    'sched.keep_orig':'Giữ nguyên gốc',
    'sched.with_img': 'Đính kèm ảnh',
    'sched.num_posts':'Số bài repost',
    'sched.src_grp':  'Nhóm nguồn (ID)',
    'sched.dst_grp':  'Nhóm đích (ID)',
    'sched.grp_ids':  'Nhóm tương tác (ID)',
    'sched.submit':   '✓ Tạo lịch',
    'sched.day_label':'Thứ trong tuần',
    'sched.time_label':'Giờ chạy',

    // Logs
    'logs.title':    'Logs hoạt động',
    'logs.sub':      'Lịch sử chạy của bot: đăng bài, repost, tương tác theo thời gian thực.',
    'logs.eyebrow':  'Nhật ký',
    'logs.total':    'Tổng log',
    'logs.success':  'Thành công',
    'logs.error':    'Lỗi',
    'logs.today':    'Hôm nay',
    'logs.all':      'Tất cả',
    'logs.refresh':  '🔄 Làm mới',
    'logs.search_ph':'🔍 Tìm kiếm log...',
    'logs.live':     'Live',
    'logs.activity': 'Nhật ký hoạt động',
    'logs.no_error': 'Không có lỗi nào — bot đang chạy tốt!',
    'logs.empty':    'Không tìm thấy log nào.',

    // Settings
    'settings.title':      'Cài đặt hệ thống',
    'settings.sub':        'Cấu hình hoạt động của bot và các thông số mặc định.',
    'settings.eyebrow':    'Cấu hình',
    'settings.ui':         'Giao diện',
    'settings.ui_desc':    'Tuỳ chỉnh giao diện hiển thị của ứng dụng.',
    'settings.theme':      'Chủ đề màu sắc',
    'settings.theme_desc': 'Chuyển giữa giao diện tối (mặc định) và sáng.',
    'settings.dark':       'Chế độ tối',
    'settings.light':      'Chế độ sáng',
    'settings.lang':       'Ngôn ngữ giao diện',
    'settings.lang_desc':  'Chọn ngôn ngữ hiển thị cho toàn bộ ứng dụng.',
    'settings.sidebar':    'Sidebar thu gọn',
    'settings.sidebar_desc':'Thu gọn thanh điều hướng để có thêm không gian làm việc.',
    'settings.toggle_sidebar':'⇔ Chuyển đổi',
    'settings.bot':        'Hành vi Bot',
    'settings.bot_desc':   'Thời gian chờ và giới hạn tương tác giữa các nhóm.',
    'settings.wait':       'Thời gian chờ giữa các nhóm',
    'settings.wait_desc':  'Giây bot chờ sau khi đăng vào một nhóm trước khi chuyển sang nhóm tiếp theo.',
    'settings.wait_unit':  'giây',
    'settings.like':       'Giới hạn like / phiên',
    'settings.like_desc':  'Số lượt like tối đa bot thực hiện trong mỗi lần tương tác.',
    'settings.like_unit':  'lượt',
    'settings.comment':    'Giới hạn comment / phiên',
    'settings.comment_desc':'Số comment tối đa bot thực hiện trong mỗi lần tương tác.',
    'settings.comment_unit':'comment',
    'settings.media':      'Thư mục ảnh',
    'settings.media_desc': 'Đường dẫn thư mục chứa ảnh bot sẽ đính kèm khi đăng bài.',
    'settings.img_dir':    'Đường dẫn thư mục ảnh',
    'settings.img_ph':     'C:/fb_images',
    'settings.reset':      '↺ Đặt lại',
    'settings.save':       '💾 Lưu cài đặt',
    'settings.system':     'Thông tin hệ thống',
    'settings.system_desc':'Phiên bản, trạng thái kết nối và thông tin runtime.',
    'settings.version':    'Phiên bản',
    'settings.backend':    'Backend API',
    'settings.db':         'Database',
    'settings.checking':   'Đang kiểm tra...',
    'settings.conn_ok':    'Kết nối OK',
    'settings.conn_fail':  'Không kết nối được',
    'settings.nav_ui':     '🎨 Giao diện',
    'settings.nav_bot':    '🤖 Hành vi Bot',
    'settings.nav_media':  '🖼️ Media',
    'settings.nav_system': 'ℹ️ Thông tin hệ thống',
    'settings.menu_title': 'Mục cài đặt',
    'settings.groups':     'Nhóm',
    'settings.topics':     'Chủ đề',
    'settings.schedules':  'Lịch',
    'settings.logs_label': 'Logs',
    'settings.headless':      'Chế độ headless (ẩn trình duyệt)',
    'settings.headless_desc': 'Bot chạy ẩn hoàn toàn, không hiện cửa sổ Chrome. Khuyến nghị bật khi đã test ổn định.',
    'settings.headless_off':  'Đang tắt',
    'settings.headless_on':   'Đang bật',

    // Common
    'common.cancel':  'Hủy',
    'common.save':    '💾 Lưu',
    'common.edit':    '✏️ Sửa',
    'common.delete':  '🗑 Xóa',
    'common.add':     '➕ Thêm',
    'common.loading': 'Đang tải...',
    'common.empty':   'Chưa có dữ liệu',
    'common.success': 'Thành công',
    'common.error':   'Lỗi',
    'common.bot_running': 'Bot đang chạy',
    'common.version': 'v1.0.0 · API online',
    'common.name':    'Tên',
    'common.url':     'URL',
    'common.note':    'Ghi chú',
    'common.desc':    'Mô tả',
    'common.actions': 'Thao tác',
    'common.time':    'Thời gian',
    'common.type':    'Loại',
    'common.status':  'Trạng thái',
    'common.detail':  'Chi tiết',
  },

  en: {
    // Nav
    'nav.dashboard':  'Dashboard',
    'nav.groups':     'Groups',
    'nav.topics':     'Topics',
    'nav.schedules':  'Schedules',
    'nav.logs':       'Logs',
    'nav.settings':   'Settings',

    // Global bar
    'bar.online':     'Online',

    // Dashboard
    'dash.title':          'Dashboard',
    'dash.sub':            'Monitor bot activity and manage the entire system from here.',
    'dash.eyebrow':        'Overview',
    'dash.bot_running':    'System is running',
    'dash.bot_sub':        'All services online',
    'dash.no_data':        'No data yet',
    'dash.stat_groups':    'FB Groups',
    'dash.stat_schedules': 'Schedules',
    'dash.stat_today':     'Success today',
    'dash.stat_errors':    'Errors today',
    'dash.managing':       'managing',
    'dash.total_sched':    'total',
    'dash.runs_ok':        'runs OK',
    'dash.need_check':     'need review',
    'dash.quick_groups':   'Manage Groups',
    'dash.quick_topics':   'AI Topics',
    'dash.quick_schedules':'Schedules',
    'dash.quick_logs':     'View Logs',
    'dash.quick_create':   'New Schedule',
    'dash.recent':         'Recent Activity',
    'dash.see_all':        'View all →',
    'dash.upcoming':       'Upcoming Schedules',
    'dash.manage':         'Manage →',
    'dash.summary':        'System Summary',

    // Groups
    'groups.title':       'Manage Groups',
    'groups.sub':         'Facebook groups the bot will post, repost and interact with.',
    'groups.eyebrow':     'Management',
    'groups.add':         'Add new group',
    'groups.name_ph':     'Group name (e.g. Buy & Sell Community)',
    'groups.url_ph':      'facebook.com/groups/...',
    'groups.note_ph':     'Note (optional)',
    'groups.save':        '＋ Save group',
    'groups.list':        'Group list',
    'groups.total':       'Total groups',
    'groups.active':      'Active',
    'groups.running':     'Running schedules',
    'groups.edit':        '✏️ Edit',
    'groups.delete':      '🗑 Delete',
    'groups.view_card':   '⊞ Cards',
    'groups.view_table':  '☰ Table',
    'groups.modal_title': '✏️ Edit Group',
    'groups.cancel':      'Cancel',
    'groups.save_btn':    '💾 Save',

    // Topics
    'topics.title':    'Manage Topics',
    'topics.sub':      'Content topics the bot picks when scheduling posts.',
    'topics.eyebrow':  'Content',
    'topics.add':      'Add new topic',
    'topics.name_ph':  'E.g. Cooking tips, Tech reviews...',
    'topics.desc_ph':  'Description to help AI understand the topic (optional)',
    'topics.save':     '＋ Save topic',
    'topics.list':     'Topic list',
    'topics.total':    'Total topics',
    'topics.with_desc':'Has description',
    'topics.in_sched': 'Used in schedules',
    'topics.no_desc':  'No description yet',

    // Schedules
    'sched.title':    'Manage Schedules',
    'sched.sub':      'Create and track post, repost, interaction schedules by day and time.',
    'sched.eyebrow':  'Automation',
    'sched.create':   '➕ Create new schedule',
    'sched.post':     '📝 Post',
    'sched.repost':   '🔁 Repost',
    'sched.interact': '💬 Interact',
    'sched.day_ph':   'Mon, Tue, Sun...',
    'sched.time_ph':  '08:00',
    'sched.mode':     'Post mode',
    'sched.by_topic': '🏷️ By topic (AI writes)',
    'sched.by_content':'📝 Custom content',
    'sched.topic_lbl':'Topic',
    'sched.content_ph':'Enter content to post...',
    'sched.groups_ph':'1, 2, 3',
    'sched.keep_orig':'Keep original',
    'sched.with_img': 'Attach image',
    'sched.num_posts':'Number of posts',
    'sched.src_grp':  'Source groups (ID)',
    'sched.dst_grp':  'Target groups (ID)',
    'sched.grp_ids':  'Interact groups (ID)',
    'sched.submit':   '✓ Create schedule',
    'sched.day_label':'Day of week',
    'sched.time_label':'Run time',

    // Logs
    'logs.title':    'Activity Logs',
    'logs.sub':      'Bot run history: posts, reposts, interactions in real-time.',
    'logs.eyebrow':  'Journal',
    'logs.total':    'Total logs',
    'logs.success':  'Success',
    'logs.error':    'Errors',
    'logs.today':    'Today',
    'logs.all':      'All',
    'logs.refresh':  '🔄 Refresh',
    'logs.search_ph':'🔍 Search logs...',
    'logs.live':     'Live',
    'logs.activity': 'Activity log',
    'logs.no_error': 'No errors — bot is running well!',
    'logs.empty':    'No logs found.',

    // Settings
    'settings.title':      'System Settings',
    'settings.sub':        'Configure bot behavior and default parameters.',
    'settings.eyebrow':    'Configuration',
    'settings.ui':         'Interface',
    'settings.ui_desc':    'Customize the application display.',
    'settings.theme':      'Color theme',
    'settings.theme_desc': 'Switch between dark (default) and light mode.',
    'settings.dark':       'Dark mode',
    'settings.light':      'Light mode',
    'settings.lang':       'Interface language',
    'settings.lang_desc':  'Choose the display language for the entire application.',
    'settings.sidebar':    'Collapse sidebar',
    'settings.sidebar_desc':'Collapse the navigation bar to gain more workspace.',
    'settings.toggle_sidebar':'⇔ Toggle',
    'settings.bot':        'Bot Behavior',
    'settings.bot_desc':   'Wait time and interaction limits between groups.',
    'settings.wait':       'Wait time between groups',
    'settings.wait_desc':  'Seconds the bot waits after posting to a group before moving to the next.',
    'settings.wait_unit':  'sec',
    'settings.like':       'Like limit / session',
    'settings.like_desc':  'Maximum likes the bot performs per interaction session.',
    'settings.like_unit':  'likes',
    'settings.comment':    'Comment limit / session',
    'settings.comment_desc':'Maximum comments the bot performs per interaction session.',
    'settings.comment_unit':'comments',
    'settings.media':      'Image folder',
    'settings.media_desc': 'Path to the folder containing images the bot attaches when posting.',
    'settings.img_dir':    'Image folder path',
    'settings.img_ph':     'C:/fb_images',
    'settings.reset':      '↺ Reset',
    'settings.save':       '💾 Save settings',
    'settings.system':     'System Information',
    'settings.system_desc':'Version, connection status and runtime info.',
    'settings.version':    'Version',
    'settings.backend':    'Backend API',
    'settings.db':         'Database',
    'settings.checking':   'Checking...',
    'settings.conn_ok':    'Connected OK',
    'settings.conn_fail':  'Cannot connect',
    'settings.nav_ui':     '🎨 Interface',
    'settings.nav_bot':    '🤖 Bot Behavior',
    'settings.nav_media':  '🖼️ Media',
    'settings.nav_system': 'ℹ️ System Info',
    'settings.menu_title': 'Settings sections',
    'settings.groups':     'Groups',
    'settings.topics':     'Topics',
    'settings.schedules':  'Schedules',
    'settings.logs_label': 'Logs',
    'settings.headless':      'Headless mode (hide browser)',
    'settings.headless_desc': 'Bot runs completely hidden, no Chrome window. Recommended once stable.',
    'settings.headless_off':  'Disabled',
    'settings.headless_on':   'Enabled',

    // Common
    'common.cancel':  'Cancel',
    'common.save':    '💾 Save',
    'common.edit':    '✏️ Edit',
    'common.delete':  '🗑 Delete',
    'common.add':     '➕ Add',
    'common.loading': 'Loading...',
    'common.empty':   'No data yet',
    'common.success': 'Success',
    'common.error':   'Error',
    'common.bot_running': 'Bot running',
    'common.version': 'v1.0.0 · API online',
    'common.name':    'Name',
    'common.url':     'URL',
    'common.note':    'Note',
    'common.desc':    'Description',
    'common.actions': 'Actions',
    'common.time':    'Time',
    'common.type':    'Type',
    'common.status':  'Status',
    'common.detail':  'Detail',
  }
};

// ── Áp dụng bản dịch lên toàn bộ DOM ──
function applyLang(lang) {
  const dict = TRANSLATIONS[lang] || TRANSLATIONS['vi'];
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    const val = dict[key];
    if (!val) return;
    // placeholder
    if (el.hasAttribute('placeholder')) {
      el.setAttribute('placeholder', val);
    } else {
      el.textContent = val;
    }
  });
  // Cập nhật lang attribute trên html
  document.documentElement.setAttribute('lang', lang === 'vi' ? 'vi' : 'en');
  // Lưu local để dùng ngay khi reload (trước khi API trả về)
  try { localStorage.setItem('fbbot-lang', lang); } catch (_) {}
}

// ── t() — dịch một key đơn lẻ trong JS ──
function t(key) {
  const lang = localStorage.getItem('fbbot-lang') || 'vi';
  const dict = TRANSLATIONS[lang] || TRANSLATIONS['vi'];
  return dict[key] || key;
}
window.t = t;
window.applyLang = applyLang;

// ── Tự động áp dụng ngôn ngữ khi load trang ──
// Dùng localStorage trước (instant), sau đó sync với DB
(function initLang() {
  const saved = localStorage.getItem('fbbot-lang') || 'vi';
  applyLang(saved);

  // Sau khi DOM + API sẵn sàng, sync với DB
  document.addEventListener('DOMContentLoaded', async () => {
    try {
      if (typeof loadLanguage === 'function') {
        const dbLang = await loadLanguage();
        if (dbLang && dbLang !== saved) {
          applyLang(dbLang);
        }
      }
    } catch (_) {}
  });
})();
