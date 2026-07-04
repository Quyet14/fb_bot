# Plan sửa lỗi “sửa rồi mà vẫn giữ nguyên cái cũ”

## Information Gathered
- UI các trang (`groups.html`, `schedules.html`, `topics.html`, `logs.html`) đang load:
  - `styles.css?v=2`, `theme.js?v=2` (có version)
  - nhưng **`api.js` và `app.js` không có version** → rất dễ bị trình duyệt cache bản cũ.
- `ui-design/html/index.html` có version cho `api.js/app.js` nhưng trang khác thì không.
- Backend có nhánh theo `settings.USE_MONGODB`, và `main.py` chạy `nap_lai_toan_bo_lich()` + `scheduler.start()` ở `startup`.
- UI gọi backend qua `ui-design/html/api.js` bằng `API_BASE_CANDIDATES` (có thể nhầm port/nhầm backend nếu cấu hình khác).

## Plan
1) **UI fix cache**: cập nhật các file HTML trang UI để thêm `?v=` vào script tags `../html/api.js` và `../html/app.js` (và nếu cần thì `theme.js`). (Đã làm: v=3)

2) **UI kiểm tra**: hard refresh (Ctrl+F5) để đảm bảo tải file mới.
3) **Backend fix**: restart server FastAPI sau thay đổi Python để chắc chắn code scheduler/crud/routers đang chạy bản mới.
4) Nếu vẫn thấy “cũ”, kiểm tra `settings.USE_MONGODB` để chắc chắn bạn đang sửa đúng tầng data.

## Dependent Files to be edited
- `ui-design/pages/groups.html`
- `ui-design/pages/topics.html`
- `ui-design/pages/schedules.html`
- `ui-design/pages/logs.html`
- (có thể) `ui-design/html/index.html` nếu cần đồng bộ version

## Followup steps
- Hard refresh browser.
- Restart backend FastAPI.
- Nếu dùng Mongo, xác nhận `settings.USE_MONGODB=True`.

