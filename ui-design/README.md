# FB Bot Console

Admin panel tĩnh (HTML/CSS/JS thuần, không build step) để quản lý nhóm,
chủ đề, lịch đăng bài và xem log hoạt động của bot Facebook.

## Cấu trúc thư mục

```
├── html/                  # Trang chủ + tài nguyên dùng chung
│   ├── index.html         # Dashboard
│   ├── api.js             # Gọi API backend (fetch + fallback port)
│   ├── app.js             # State, render, xử lý sự kiện
│   ├── theme.js           # Bật/tắt chế độ sáng · tối
│   ├── styles.css         # File gốc — chỉ @import các phần dưới
│   └── css/
│       ├── tokens.css     # Màu sắc, font, spacing (2 theme: dark/light)
│       ├── base.css       # Reset, khung trang (sidebar/main/topbar)
│       ├── components.css # Nút, thẻ, bảng, form, badge trạng thái
│       └── responsive.css # Breakpoint cho màn hình nhỏ
├── pages/
│   ├── groups.html        # Quản lý nhóm
│   ├── topics.html        # Quản lý chủ đề
│   ├── schedules.html     # Quản lý lịch đăng bài/repost/tương tác
│   └── logs.html          # Nhật ký hoạt động
├── server/
│   └── server.py          # HTTP server tĩnh, phục vụ toàn bộ thư mục gốc
└── README.md
```

Vì tất cả các trang dùng script thường (`<script src="...">`, không phải
`type="module"`), thứ tự nạp file quan trọng: `theme.js` → `api.js` →
`app.js`. Nếu thêm file JS mới cần thêm biến/hàm dùng chung ở các trang
khác, nạp nó **trước** `app.js`.

## Chạy thử

```bash
python3 server/server.py
```

Server sẽ tự map `/` và `/index.html` sang `/html/index.html`, phục vụ
toàn bộ repo làm root tĩnh — không cần cấu hình gì thêm.

## Hệ thống màu & theme sáng/tối

Toàn bộ màu sắc đi qua **CSS variable (token)** khai báo trong
`html/css/tokens.css`, không có màu "hard-code" ở component nào khác.
Điều này giúp việc đổi theme chỉ là đổi giá trị của token, không phải sửa
từng nút/từng bảng.

- **Theme mặc định (tối)**: nền tối `#0a0e18`, chữ sáng, hợp với dùng lâu
  buổi tối, đỡ chói.
- **Theme sáng**: nền gần trắng `#f4f6fb`, chữ tối `#16202f`. Các màu
  "channel" (tím = Nhóm, vàng = Chủ đề, xanh lá = Lịch, hồng = Logs) được
  làm **đậm/tối hơn** so với bản dark, để khi đặt trên nền trắng vẫn đạt
  tỷ lệ tương phản ≥ 4.5:1 với nền — đủ chuẩn WCAG AA cho văn bản thường,
  giúp người dùng lớn tuổi hoặc khiếm thị màu nhẹ vẫn đọc rõ.
- Nút bật/tắt nằm ngay dưới logo trong sidebar, lưu lựa chọn vào
  `localStorage` (`fbbot-theme`) nên lần sau mở lại vẫn giữ đúng theme.
  Một đoạn script nhỏ trong `<head>` đọc `localStorage` **trước khi**
  CSS load, để tránh hiện tượng nháy sai theme (FOUC).

### Thêm 1 màu / token mới
Sửa `html/css/tokens.css` — thêm ở cả block `:root` (dark) và
`:root[data-theme='light']` (light) để hai theme đồng bộ.

### Thêm 1 trang mới
1. Copy cấu trúc `<head>` (đoạn script chống-FOUC + `<link>` +
   3 thẻ `<script defer>`) và khối `<aside class="sidebar">` từ một trang
   có sẵn trong `pages/`.
2. Thêm class `page-<ten-trang>` vào `<body>` rồi định nghĩa
   `--accent`/`--accent-soft` cho nó trong `tokens.css` nếu muốn trang có
   màu riêng.
3. Thêm class `active` vào link tương ứng trong sidebar.

## Việc nên làm tiếp (đã phát hiện, chưa sửa vì ngoài phạm vi lần này)

- `app.js` gọi `updatePostSchedule`, `updateRepostSchedule`,
  `updateInteractSchedule` khi bấm "Sửa" ở trang Lịch, nhưng `api.js`
  chưa định nghĩa 3 hàm này — nút Sửa lịch sẽ báo lỗi. Cần thêm 3 hàm
  tương ứng (giống mẫu `updateGroup`/`updateTopic`) vào `api.js`.
