# Requirements Document

## Introduction

Tài liệu này mô tả các yêu cầu chức năng cho hệ thống xác thực người dùng của FB Bot Console. Hệ thống cung cấp đăng ký, đăng nhập, đăng xuất và làm mới token thông qua backend FastAPI với JWT (access token ngắn hạn + refresh token dài hạn). Frontend gồm hai trang HTML tĩnh (`login.html`, `register.html`) tích hợp với design system glass morphism hiện có. Tất cả route dashboard được bảo vệ bởi auth guard frontend — nếu chưa xác thực sẽ redirect về `login.html`.

Hệ thống hỗ trợ hai database backend: MongoDB (khi `USE_MONGODB=true`) và SQLAlchemy/SQLite (khi `USE_MONGODB=false`). Tính năng đăng ký public có thể tắt bằng `ALLOW_REGISTER=false`.

---

## Glossary

- **AuthRouter**: FastAPI router xử lý các endpoint `/auth/*`
- **Auth_Guard**: Module JavaScript `auth.js` chạy trên frontend, kiểm tra và bảo vệ mọi trang dashboard
- **JWT_Utils**: Module Python `jwt_utils.py` tạo và xác minh JWT tokens
- **Pwd_Utils**: Module Python `pwd_utils.py` hash và verify mật khẩu bằng bcrypt
- **Auth_CRUD**: Module Python `auth_crud.py` thực hiện database operations cho User
- **Auth_Module**: Toàn bộ object `Auth` trong `auth.js` (frontend)
- **Access_Token**: JWT ngắn hạn (mặc định 60 phút), dùng để xác thực mỗi API request
- **Refresh_Token**: JWT dài hạn (mặc định 30 ngày), dùng để lấy Access_Token mới
- **DB_Adapter**: Lớp trừu tượng hoá database — route tới MongoDB hoặc SQLAlchemy tuỳ cấu hình `USE_MONGODB`
- **User**: Thực thể người dùng lưu trong database với các trường `id`, `username`, `hashed_password`, `role`, `is_active`, `created_at`
- **Dashboard_Page**: Bất kỳ trang nào trong tập hợp `dashboard.html`, `groups.html`, `schedules.html`, `topics.html`, `logs.html`, `settings.html`
- **Login_Page**: Trang `login.html`
- **Register_Page**: Trang `register.html`
- **Global_Bar**: Thanh điều hướng cố định ở trên cùng, hiển thị trên mọi trang

---

## Requirements

### Requirement 1: Đăng ký tài khoản

**User Story:** As a new user, I want to register an account, so that I can access the FB Bot Console dashboard.

#### Acceptance Criteria

1. WHEN `ALLOW_REGISTER` is `true` AND a POST request is sent to `/auth/register` with a valid username and password, THE AuthRouter SHALL create a new User and return HTTP 201 with a `UserOut` response body containing `id`, `username`, `role`, `is_active`, and `created_at`.

2. WHEN a POST request is sent to `/auth/register` with a username that already exists in the database, THE AuthRouter SHALL return HTTP 409 with detail message `"Tên đăng nhập đã tồn tại"`.

3. WHEN `ALLOW_REGISTER` is `false` AND a POST request is sent to `/auth/register`, THE AuthRouter SHALL return HTTP 403 with detail message `"Đăng ký đã bị tắt"` without accessing the database.

4. WHEN a POST request is sent to `/auth/register` with a `username` shorter than 3 characters or longer than 50 characters, THE AuthRouter SHALL return HTTP 422 (validation error) before processing the request.

5. WHEN a POST request is sent to `/auth/register` with a `password` shorter than 6 characters, THE AuthRouter SHALL return HTTP 422 (validation error) before processing the request.

6. WHEN a new User is created, THE Pwd_Utils SHALL store the password as a bcrypt hash starting with `$2b$` — the plain-text password SHALL never be persisted to the database.

7. WHEN `USE_MONGODB` is `true` AND a new User is created, THE Auth_CRUD SHALL insert a new document into the MongoDB `users` collection with a unique `username` index.

8. WHEN `USE_MONGODB` is `false` AND a new User is created, THE Auth_CRUD SHALL insert a new row into the SQLAlchemy `users` table with a unique constraint on `username`.

9. WHERE `ALLOW_REGISTER` is `false`, THE Register_Page SHALL hide the registration link and display a message directing the user to contact an administrator.

---

### Requirement 2: Đăng nhập với JWT

**User Story:** As a registered user, I want to log in with my credentials, so that I can receive tokens and access the dashboard.

#### Acceptance Criteria

1. WHEN a POST request is sent to `/auth/login` with a valid `username` and correct `password`, THE AuthRouter SHALL return HTTP 200 with a `TokenOut` body containing `access_token`, `refresh_token`, `token_type: "bearer"`, and `username`.

2. WHEN a POST request is sent to `/auth/login` with a `username` that does not exist in the database, THE AuthRouter SHALL return HTTP 401 with detail message `"Tên đăng nhập hoặc mật khẩu không đúng"`.

3. WHEN a POST request is sent to `/auth/login` with a correct `username` but incorrect `password`, THE AuthRouter SHALL return HTTP 401 with detail message `"Tên đăng nhập hoặc mật khẩu không đúng"`.

4. WHEN a POST request is sent to `/auth/login` with a valid `username` and correct `password` but `is_active` is `false` for that User, THE AuthRouter SHALL return HTTP 403 with detail message `"Tài khoản đã bị vô hiệu hoá"`.

5. WHEN login succeeds, THE JWT_Utils SHALL create an Access_Token containing `sub` (user id), `username`, `role`, and `exp` equal to current time plus `JWT_ACCESS_EXPIRE_MINUTES`.

6. WHEN login succeeds, THE JWT_Utils SHALL create a Refresh_Token containing `sub` (user id) and `exp` equal to current time plus `JWT_REFRESH_EXPIRE_DAYS` days.

7. WHEN login succeeds, THE Auth_Module SHALL store the Access_Token in `localStorage` under key `"fbbot-access-token"` and the Refresh_Token under key `"fbbot-refresh-token"`.

8. WHEN login succeeds and tokens are stored, THE Auth_Module SHALL redirect the browser to `dashboard.html`.

9. WHEN login fails with HTTP 401 or 403, THE Login_Page SHALL display the error message inside the form without redirecting.

---

### Requirement 3: Đăng xuất

**User Story:** As an authenticated user, I want to log out, so that my session is ended and tokens are removed.

#### Acceptance Criteria

1. WHEN a POST request is sent to `/auth/logout` with a valid Bearer token, THE AuthRouter SHALL return HTTP 204 No Content.

2. WHEN a POST request is sent to `/auth/logout` without a Bearer token or with an invalid token, THE AuthRouter SHALL return HTTP 401.

3. WHEN the user clicks the logout button, THE Auth_Module SHALL send POST `/auth/logout` with the current Access_Token, then remove both `"fbbot-access-token"` and `"fbbot-refresh-token"` from `localStorage`, then redirect the browser to `login.html`.

4. WHEN logout is triggered and the backend returns an error or is unreachable, THE Auth_Module SHALL still remove tokens from `localStorage` and redirect to `login.html`.

5. WHILE the user is authenticated, THE Global_Bar SHALL display a logout button and the current `username` in the user info section.

---

### Requirement 4: Bảo vệ route dashboard (Auth Guard Frontend)

**User Story:** As a system owner, I want all dashboard pages to require authentication, so that unauthenticated users cannot access the console.

#### Acceptance Criteria

1. WHEN `DOMContentLoaded` fires on any Dashboard_Page and `"fbbot-access-token"` is absent from `localStorage`, THE Auth_Guard SHALL immediately redirect the browser to `login.html` without rendering page content.

2. WHEN `DOMContentLoaded` fires on any Dashboard_Page and a token exists, THE Auth_Guard SHALL send GET `/auth/me` with the Bearer token to verify it.

3. WHEN GET `/auth/me` returns HTTP 200, THE Auth_Guard SHALL allow the page to render normally with the authenticated user's data.

4. WHEN GET `/auth/me` returns HTTP 401 AND a Refresh_Token is present in `localStorage`, THE Auth_Guard SHALL attempt to refresh the token before redirecting.

5. IF the refresh attempt fails, THEN THE Auth_Guard SHALL remove both tokens from `localStorage` and redirect to `login.html`.

6. WHEN a GET request is sent to `/auth/me` with a valid Bearer token, THE AuthRouter SHALL return HTTP 200 with a `UserOut` body containing `id`, `username`, `role`, `is_active`, and `created_at`.

7. WHEN a GET request is sent to `/auth/me` without a Bearer token or with an invalid/expired token, THE AuthRouter SHALL return HTTP 401.

8. IF the backend is unreachable when GET `/auth/me` is called, THEN THE Auth_Guard SHALL display a toast notification with message `"Không thể kết nối backend"` without redirecting, preserving the existing `localStorage` tokens.

---

### Requirement 5: Refresh token tự động

**User Story:** As an authenticated user, I want my session to be automatically renewed, so that I am not unexpectedly logged out during active use.

#### Acceptance Criteria

1. WHEN a POST request is sent to `/auth/refresh` with a valid `refresh_token` in the request body, THE AuthRouter SHALL return HTTP 200 with a new `TokenOut` containing a fresh `access_token` and `refresh_token`.

2. WHEN a POST request is sent to `/auth/refresh` with an expired or invalid `refresh_token`, THE AuthRouter SHALL return HTTP 401.

3. WHEN `/auth/refresh` returns HTTP 200, THE Auth_Module SHALL update `"fbbot-access-token"` and `"fbbot-refresh-token"` in `localStorage` with the new token values.

4. WHEN `/auth/refresh` returns HTTP 401, THE Auth_Guard SHALL remove both tokens from `localStorage` and redirect the browser to `login.html`.

5. THE JWT_Utils SHALL verify a refreshed Access_Token successfully using `verify_token()` — the token SHALL contain valid `sub`, `username`, `role`, and `exp` fields.

6. THE Auth_Module SHALL expose a `getAuthHeaders()` method that returns `{ Authorization: "Bearer <access_token>" }` where `<access_token>` is the current value from `localStorage`.

---

### Requirement 6: Bảo vệ các API router backend

**User Story:** As a system owner, I want all backend API endpoints (groups, schedules, topics, etc.) to require a valid JWT, so that the data cannot be accessed without authentication.

#### Acceptance Criteria

1. WHEN a request is sent to any protected API endpoint (e.g., `/groups/`, `/schedules/`) without a Bearer token, THE AuthRouter SHALL return HTTP 401 via the `get_current_user` dependency.

2. WHEN a request is sent to any protected API endpoint with a valid, non-expired Bearer token, THE JWT_Utils SHALL verify the token and THE AuthRouter SHALL allow the request to proceed.

3. WHEN a request is sent to any protected API endpoint with an expired Bearer token, THE JWT_Utils SHALL raise a `JWTError`, and THE AuthRouter SHALL return HTTP 401 with detail `"Token không hợp lệ hoặc đã hết hạn"`.

4. WHEN `get_current_user` resolves a valid token but the corresponding User no longer exists or has `is_active = false`, THE AuthRouter SHALL return HTTP 401 with detail `"Người dùng không tồn tại"`.

5. THE JWT_Utils `create_access_token()` function SHALL produce a token that, when decoded with `JWT_SECRET_KEY`, contains `sub`, `username`, `role`, and a non-expired `exp` field.

6. THE JWT_Utils `verify_token()` function SHALL raise `JWTError` for any token not signed with the server's `JWT_SECRET_KEY`.

---

### Requirement 7: Trang login.html

**User Story:** As an unauthenticated user, I want a login page that matches the existing design system, so that I can enter my credentials in a consistent and accessible interface.

#### Acceptance Criteria

1. THE Login_Page SHALL render a glass morphism card centered on screen with `max-width: 400px`, using CSS variables `--glass`, `--glass-border`, and `backdrop-filter: blur(var(--blur))` from `tokens.css`.

2. THE Login_Page SHALL include a username input field and a password input field, both styled with `.field` and `.field input` classes from `components.css`.

3. WHEN an input field receives focus, THE Login_Page SHALL apply `border-color: var(--accent)` and `box-shadow: 0 0 0 4px var(--accent-soft)` matching the existing focus style in `components.css`.

4. THE Login_Page SHALL include a submit button using the `.btn-primary` class from `components.css`.

5. WHEN `ALLOW_REGISTER` is served as `true` by the backend, THE Login_Page SHALL display a link to `register.html`.

6. WHEN a login error occurs, THE Login_Page SHALL display the error message in a toast notification using `.toast-container` and `.toast-error` classes from `components.css`.

7. THE Login_Page SHALL include the Global_Bar in a simplified form showing only the application logo.

8. THE Login_Page SHALL support both dark (default) and light themes by reading from `localStorage` key `"fbbot-theme"` and setting `data-theme` on `<html>`, consistent with all other pages.

9. THE Login_Page SHALL be fully accessible: all form fields SHALL have associated `<label>` elements, and the submit button SHALL be operable via keyboard (Enter key triggers submission).

---

### Requirement 8: Trang register.html

**User Story:** As a new user (when registration is enabled), I want a registration page that matches the existing design system, so that I can create an account in a consistent interface.

#### Acceptance Criteria

1. THE Register_Page SHALL render a glass morphism card centered on screen with `max-width: 400px`, using the same CSS variables and classes as the Login_Page for visual consistency.

2. THE Register_Page SHALL include a username input field and a password input field, both styled with `.field` and `.field input` classes from `components.css`.

3. WHEN a user submits the registration form with a password shorter than 6 characters, THE Register_Page SHALL display a validation error before sending any API request.

4. WHEN a user submits the registration form with a username shorter than 3 characters, THE Register_Page SHALL display a validation error before sending any API request.

5. WHEN registration succeeds (HTTP 201), THE Register_Page SHALL display a success toast notification and redirect to `login.html` after 1500 ms.

6. WHEN registration fails with HTTP 409 (duplicate username), THE Register_Page SHALL display a toast notification with the error detail from the API response.

7. WHEN registration fails with HTTP 403 (registration disabled), THE Register_Page SHALL display a message instructing the user to contact an administrator.

8. THE Register_Page SHALL include a link back to `login.html` for users who already have an account.

9. THE Register_Page SHALL support both dark and light themes identical to the Login_Page.

10. THE Register_Page SHALL be fully accessible: all form fields SHALL have associated `<label>` elements, and the submit button SHALL be operable via keyboard.

---

### Requirement 9: Dual-database compatibility

**User Story:** As a system operator, I want the authentication system to work with both MongoDB and SQLAlchemy backends, so that I can choose the database that fits my deployment.

#### Acceptance Criteria

1. WHEN `USE_MONGODB` is `true`, THE Auth_CRUD SHALL query the MongoDB `users` collection using the existing `mongo_db.py` connection pattern.

2. WHEN `USE_MONGODB` is `false`, THE Auth_CRUD SHALL query the SQLAlchemy `users` table using the existing `database.py` session pattern.

3. THE Auth_CRUD `get_user_by_username(db, username)` function SHALL return a `UserOut` object (or `None`) with the same interface regardless of which database backend is active.

4. THE Auth_CRUD `create_user(db, data)` function SHALL return a `UserOut` object with the same fields regardless of which database backend is active.

5. THE Auth_CRUD `user_exists(db, username)` function SHALL return a boolean with the same semantic regardless of which database backend is active.

---

### Requirement 10: Cấu hình và bảo mật môi trường

**User Story:** As a system operator, I want authentication to be configurable via environment variables, so that secrets and timing can be adjusted without code changes.

#### Acceptance Criteria

1. THE AuthRouter SHALL read `JWT_SECRET_KEY` from the application settings and SHALL use it as the signing key for all tokens — this value SHALL never appear in source code or logs.

2. THE JWT_Utils SHALL read `JWT_ACCESS_EXPIRE_MINUTES` from settings (default: 60) and apply it as the expiration for all Access_Tokens.

3. THE JWT_Utils SHALL read `JWT_REFRESH_EXPIRE_DAYS` from settings (default: 30) and apply it as the expiration for all Refresh_Tokens.

4. THE AuthRouter SHALL read `ALLOW_REGISTER` from settings (default: `true`) and apply it to every POST `/auth/register` request.

5. WHEN `JWT_SECRET_KEY` is not set in the environment, THE AuthRouter SHALL raise a configuration error on application startup before accepting any requests.

6. THE Pwd_Utils `hash_password()` function SHALL use bcrypt with a minimum of 12 rounds when generating password hashes.
