# Implementation Plan: User Authentication

## Overview

Thêm hệ thống xác thực người dùng vào FB Bot Console. Backend FastAPI cung cấp các endpoint `/auth/*` với JWT. Frontend bổ sung `login.html`, `register.html`, và `auth.js` tích hợp với design system glass morphism hiện có. Tất cả các trang dashboard sẽ được bảo vệ bằng auth guard frontend.

## Tasks

- [ ] 1. Cài đặt dependencies và cấu hình môi trường
  - Thêm `python-jose[cryptography]`, `passlib[bcrypt]`, `python-multipart` vào `requirements.txt`
  - Mở rộng `app/config.py` để đọc `JWT_SECRET_KEY`, `JWT_ACCESS_EXPIRE_MINUTES`, `JWT_REFRESH_EXPIRE_DAYS`, `ALLOW_REGISTER` từ `.env`
  - Thêm startup validation: raise `ValueError` nếu `JWT_SECRET_KEY` chưa được set
  - Cập nhật `.env.example` với các biến mới
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ] 2. Xây dựng lớp Auth utilities (jwt_utils.py và pwd_utils.py)
  - [ ] 2.1 Tạo `app/auth/__init__.py` (file rỗng) và `app/auth/pwd_utils.py`
    - Implement `hash_password(plain: str) -> str` dùng passlib bcrypt với 12 rounds
    - Implement `verify_password(plain: str, hashed: str) -> bool`
    - _Requirements: 1.6, 10.6_

  - [ ]* 2.2 Viết property test cho `pwd_utils`
    - **Property 1: Bcrypt hash round-trip** — với mọi plain-text password không rỗng, `hash_password(p)` bắt đầu bằng `$2b$12$` và `verify_password(p, hash_password(p)) == True`
    - **Validates: Requirements 1.6, 10.6**

  - [ ] 2.3 Tạo `app/auth/jwt_utils.py`
    - Implement `create_access_token(user_id, username, role) -> str` sử dụng `python-jose`
    - Implement `create_refresh_token(user_id) -> str`
    - Implement `verify_token(token: str) -> dict` — raise `JWTError` nếu token không hợp lệ/hết hạn
    - Implement `get_current_user(token, db) -> UserOut` FastAPI Dependency (oauth2_scheme)
    - Đọc `JWT_SECRET_KEY`, `JWT_ACCESS_EXPIRE_MINUTES`, `JWT_REFRESH_EXPIRE_DAYS` từ settings
    - _Requirements: 2.5, 2.6, 6.3, 6.5, 6.6, 10.1, 10.2, 10.3_

  - [ ]* 2.4 Viết property test cho `jwt_utils`
    - **Property 4: JWT access token create-then-verify round-trip** — với mọi `(user_id, username, role)` hợp lệ, `verify_token(create_access_token(...))` trả về payload có đúng `sub`, `username`, `role`, và `exp` trong tương lai
    - **Property 5: JWT refresh token create-then-verify round-trip** — với mọi `user_id` hợp lệ, `verify_token(create_refresh_token(user_id))` trả về `sub == user_id` và `exp` hợp lệ
    - **Property 7: Token ký bằng key sai bị reject** — `verify_token()` raise `JWTError` với mọi token không được ký bằng `JWT_SECRET_KEY`
    - **Validates: Requirements 2.5, 2.6, 5.5, 6.5, 6.6, 10.1, 10.2, 10.3**

- [ ] 3. Xây dựng Auth CRUD layer (`app/auth/auth_crud.py`)
  - [ ] 3.1 Tạo `app/auth/auth_crud.py` với nhánh MongoDB
    - Implement `get_user_by_username(db, username) -> Optional[UserOut]` dùng `mongo_db.py`
    - Implement `get_user_by_id(db, user_id) -> Optional[UserOut]`
    - Implement `create_user(db, data: UserCreate) -> UserOut` với unique username index
    - Implement `user_exists(db, username) -> bool`
    - _Requirements: 1.7, 9.1, 9.3, 9.4, 9.5_

  - [ ] 3.2 Thêm nhánh SQLAlchemy vào `auth_crud.py`
    - Thêm `User` model vào `app/models.py` (id UUID, username unique, hashed_password, role, is_active, created_at)
    - Implement các hàm tương tự 3.1 nhưng dùng SQLAlchemy Session
    - Dùng `if settings.USE_MONGODB` switch pattern giống `crud.py` hiện có
    - _Requirements: 1.8, 9.2, 9.3, 9.4, 9.5_

  - [ ]* 3.3 Viết unit tests cho `auth_crud`
    - Test `create_user()` với username trùng → phải raise lỗi hoặc trả về `None`
    - Test `user_exists()` sau khi tạo user → phải trả về `True`
    - Test `get_user_by_username()` với user không tồn tại → phải trả về `None`
    - _Requirements: 1.2, 9.3, 9.4, 9.5_

  - [ ]* 3.4 Viết property test dual-backend consistency
    - **Property 11: Auth_CRUD dual-backend interface consistency** — với mọi `UserCreate` hợp lệ, cả hai backend đều trả về `UserOut` và `bool` cùng shape và semantic
    - **Validates: Requirements 9.3, 9.4, 9.5**

- [ ] 4. Xây dựng Pydantic schemas cho Auth (`app/auth/schemas.py`)
  - Tạo `app/auth/schemas.py` với các schema: `UserCreate`, `LoginRequest`, `TokenOut`, `RefreshRequest`, `UserOut`
  - `UserCreate`: `username` Field min_length=3, max_length=50; `password` Field min_length=6
  - _Requirements: 1.4, 1.5, 2.1_

- [ ] 5. Checkpoint — Đảm bảo utils và CRUD hoạt động đúng
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Xây dựng AuthRouter (`app/routers/auth.py`)
  - [ ] 6.1 Tạo `app/routers/auth.py` và implement endpoint `POST /auth/register`
    - Kiểm tra `settings.ALLOW_REGISTER` → 403 nếu tắt
    - Kiểm tra username đã tồn tại → 409 nếu trùng
    - Hash password và tạo user qua `auth_crud`
    - Trả về `UserOut` với status 201
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

  - [ ]* 6.2 Viết property test cho `/auth/register`
    - **Property 2: Invalid registration inputs are rejected** — username ngoài [3,50] ký tự hoặc password < 6 ký tự → HTTP 422, không tạo user trong DB
    - **Property 3: Duplicate username registration is rejected** — username đã tồn tại → HTTP 409 bất kể password
    - **Validates: Requirements 1.2, 1.4, 1.5**

  - [ ] 6.3 Implement endpoint `POST /auth/login`
    - Lấy user theo username, verify password bằng `pwd_utils`
    - user không tồn tại hoặc sai password → 401 với message thống nhất
    - `is_active == False` → 403
    - Tạo access_token + refresh_token và trả về `TokenOut`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

  - [ ]* 6.4 Viết property test cho `/auth/login`
    - **Property 6: Incorrect credentials always return HTTP 401** — với mọi cặp (username, password) không hợp lệ (username không tồn tại hoặc sai password), POST `/auth/login` trả về HTTP 401
    - **Validates: Requirements 2.2, 2.3**

  - [ ] 6.5 Implement endpoint `GET /auth/me`, `POST /auth/logout`, `POST /auth/refresh`
    - `GET /auth/me`: dùng `get_current_user` dependency, trả về `UserOut`
    - `POST /auth/logout`: dùng `get_current_user` dependency, trả về 204
    - `POST /auth/refresh`: verify refresh_token, tạo lại access + refresh token mới
    - _Requirements: 3.1, 3.2, 4.6, 4.7, 5.1, 5.2, 5.5_

  - [ ]* 6.6 Viết property test cho protected endpoints và refresh
    - **Property 8: Invalid or absent token returns HTTP 401** — mọi protected endpoint được gọi không có token, token hết hạn, hoặc token malformed → HTTP 401
    - **Property 10: Refresh token produces a verifiable new access token** — với mọi refresh_token hợp lệ, `POST /auth/refresh` trả về HTTP 200 với access_token mới pass `verify_token()`
    - **Validates: Requirements 4.7, 5.1, 5.5, 6.1, 6.3**

- [ ] 7. Tích hợp AuthRouter vào ứng dụng FastAPI và bảo vệ các router khác
  - Đăng ký `auth.router` trong `app/main.py`
  - Thêm `Depends(get_current_user)` vào các router: `groups`, `topics`, `schedules`, `actions`, `logs`, `setting`, `user_contents`
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [ ] 8. Checkpoint — Đảm bảo toàn bộ backend API hoạt động đúng
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Xây dựng Frontend Auth Module (`ui-design/html/auth.js`)
  - [ ] 9.1 Tạo `ui-design/html/auth.js` với Auth object đầy đủ
    - Implement `getAccessToken()`, `getRefreshToken()`, `setTokens()`, `clearTokens()`
    - Implement `getAuthHeaders()` trả về `{ Authorization: "Bearer <token>" }`
    - Implement `login(username, password)` — POST `/auth/login`, lưu token, redirect dashboard
    - Implement `register(username, password)` — POST `/auth/register`
    - Implement `logout()` — POST `/auth/logout` + clearTokens() + redirect login
    - _Requirements: 2.7, 2.8, 3.3, 3.4, 5.3, 5.6_

  - [ ]* 9.2 Viết unit tests cho `Auth.getAuthHeaders()`
    - **Property 13: getAuthHeaders returns correct Authorization format** — với mọi access token `t` không null trong localStorage, `Auth.getAuthHeaders()` trả về `{ Authorization: "Bearer " + t }`
    - **Validates: Requirements 5.6**

  - [ ] 9.3 Implement `guardPage()` và `refreshAccessToken()` trong `auth.js`
    - `guardPage()`: kiểm tra token → gọi `GET /auth/me` → xử lý 401 với silent refresh → redirect nếu fail
    - `refreshAccessToken()`: gọi `POST /auth/refresh` → cập nhật localStorage → trả về `true/false`
    - Xử lý NetworkError: hiển thị toast "Không thể kết nối backend", không redirect
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.8, 5.3, 5.4_

  - [ ]* 9.4 Viết unit tests cho `Auth.guardPage()`
    - **Property 9: Auth guard redirects when no valid token is present** — trang Dashboard load không có token hợp lệ trong localStorage → `Auth.guardPage()` redirect về `login.html`, không render nội dung
    - **Validates: Requirements 4.1, 4.4, 4.5**

- [ ] 10. Tạo trang `login.html`
  - Tạo `ui-design/html/login.html` với glass morphism card (max-width: 400px, căn giữa)
  - Dùng CSS variables `--glass`, `--glass-border`, `backdrop-filter: blur(var(--blur))`
  - Form với username/password fields dùng class `.field`, `.field input`
  - Submit button dùng `.btn-primary`
  - Hiển thị link tới `register.html` (fetch `ALLOW_REGISTER` từ backend hoặc check config)
  - Error hiển thị dùng `.toast-container`, `.toast-error`
  - Hỗ trợ dark/light theme qua `localStorage["fbbot-theme"]` và `data-theme` trên `<html>`
  - Accessibility: tất cả input có `<label>`, Enter key submit form
  - _Requirements: 2.9, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9_

  - [ ]* 10.1 Viết unit test cho theme persistence trên login.html
    - **Property 14: Theme persistence applies correctly on auth pages** — `localStorage["fbbot-theme"] = "light"` → `data-theme="light"` trên `<html>`; absent/other → default dark
    - **Validates: Requirements 7.8, 8.9**

- [ ] 11. Tạo trang `register.html`
  - Tạo `ui-design/html/register.html` với layout tương tự `login.html`
  - Frontend validation: username < 3 ký tự → hiển thị lỗi trước khi gọi API; password < 6 ký tự → hiển thị lỗi
  - Đăng ký thành công (201) → toast success + redirect `login.html` sau 1500ms
  - Đăng ký lỗi 409 → toast lỗi với message từ API
  - Đăng ký lỗi 403 → hiển thị "Liên hệ quản trị viên để được cấp tài khoản"
  - Link quay lại `login.html`
  - Hỗ trợ dark/light theme, accessibility đầy đủ
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 8.10_

  - [ ]* 11.1 Viết unit tests cho frontend validation của register.html
    - **Property 12: Frontend input validation prevents invalid API calls** — username < 3 ký tự hoặc password < 6 ký tự → Auth module KHÔNG gửi POST request, hiển thị validation error
    - **Validates: Requirements 8.3, 8.4**

- [ ] 12. Cập nhật các trang Dashboard để tích hợp Auth Guard
  - Thêm `<script src="auth.js"></script>` và gọi `await Auth.guardPage()` trong `DOMContentLoaded` của: `dashboard.html`, `groups.html`, `schedules.html`, `topics.html`, `logs.html`, `settings.html`
  - Cập nhật `api.js`: thêm `...Auth.getAuthHeaders()` vào mọi `fetch()` request
  - Cập nhật Global_Bar trên mọi trang: hiển thị `username` và nút logout
  - Xử lý sự kiện logout button: gọi `Auth.logout()`
  - _Requirements: 3.5, 4.1, 4.2, 4.3, 5.6_

- [ ] 13. Final Checkpoint — Đảm bảo toàn bộ hệ thống hoạt động đúng
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks đánh dấu `*` là optional, có thể bỏ qua để phát triển MVP nhanh hơn
- Design sử dụng Python nên toàn bộ backend viết bằng Python; frontend dùng vanilla JavaScript
- Property tests nên dùng thư viện `hypothesis` (Python) cho backend và `fast-check` (JavaScript) cho frontend
- `app/auth/` là package mới — cần tạo `__init__.py`
- Các router hiện có (groups, schedules...) chỉ cần thêm `Depends(get_current_user)` — không thay đổi logic
- `USE_MONGODB` switch pattern giống hệt `crud.py` hiện có để đảm bảo tính nhất quán
- JWT dùng `python-jose` với thuật toán HS256

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["2.1", "4"] },
    { "id": 1, "tasks": ["2.2", "2.3"] },
    { "id": 2, "tasks": ["2.4", "3.1"] },
    { "id": 3, "tasks": ["3.2"] },
    { "id": 4, "tasks": ["3.3", "3.4", "6.1"] },
    { "id": 5, "tasks": ["6.2", "6.3"] },
    { "id": 6, "tasks": ["6.4", "6.5"] },
    { "id": 7, "tasks": ["6.6", "7"] },
    { "id": 8, "tasks": ["9.1"] },
    { "id": 9, "tasks": ["9.2", "9.3"] },
    { "id": 10, "tasks": ["9.4", "10", "11"] },
    { "id": 11, "tasks": ["10.1", "11.1", "12"] }
  ]
}
```
