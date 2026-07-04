# FB Bot Backend (FastAPI + PostgreSQL)

Backend API quan ly nhom, chu de, lich dang bai / repost / tuong tac cho bot Facebook.
Sau nay co the ket noi frontend (web) hoac phat trien thanh app di dong, vi day la
mot REST API doc lap.

## Cau truc thu muc

```
fb_bot_backend/
├── app/
│   ├── main.py            # Khoi tao FastAPI app, dang ky router, chay scheduler
│   ├── config.py           # Doc bien moi truong (.env)
│   ├── database.py          # Ket noi PostgreSQL, SessionLocal, Base
│   ├── models.py             # Cac bang SQLAlchemy
│   ├── schemas.py            # Pydantic schemas (request/response)
│   ├── crud.py                # Ham thao tac database
│   ├── scheduler.py           # APScheduler doc lich tu DB va dang ky job
│   ├── bot/
│   │   ├── gemini.py          # Goi Gemini AI
│   │   ├── browser.py          # Tao driver Selenium, ham tien ich
│   │   ├── dang_bai.py          # Chuc nang dang bai
│   │   ├── tuong_tac.py          # Chuc nang like / comment / share
│   │   └── repost.py             # Chuc nang lay bai va repost
│   └── routers/
│       ├── groups.py           # CRUD nhom
│       ├── topics.py            # CRUD chu de
│       ├── schedules.py          # CRUD lich dang bai / repost / tuong tac
│       ├── actions.py             # Chay thu cong tung tien trinh (run-now)
│       └── logs.py                 # Xem log hoat dong
├── requirements.txt
└── .env.example
```

## Cai dat

1. Tao database PostgreSQL:
   ```sql
   CREATE DATABASE fb_bot_db;
   CREATE USER fb_bot_user WITH PASSWORD 'matkhau';
   GRANT ALL PRIVILEGES ON DATABASE fb_bot_db TO fb_bot_user;
   ```

2. Sao chep `.env.example` thanh `.env` va dien thong tin that (DATABASE_URL,
   GEMINI_API_KEY, ...).

3. Cai thu vien:
   ```bash
   pip install -r requirements.txt
   ```

4. Chay server (lan dau chay se tu tao bang trong DB):
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. Mo tai lieu API tu sinh tai: `http://localhost:8000/docs`

## Luong su dung API co ban

1. `POST /groups` — them cac nhom Facebook (URL nhom).
2. `POST /topics` — them cac chu de bai viet.
3. `POST /schedules/dang-bai` — tao lich dang bai (chon chu de + danh sach nhom + thu/gio).
4. `POST /schedules/repost` — tao lich repost (chon nhom nguon + nhom dich + thu/gio).
5. `POST /schedules/tuong-tac` — tao lich like/comment/share (chon nhom + thu/gio).
6. `GET /logs` — xem lich su chay cua bot (thanh cong / loi / chi tiet).
7. `POST /actions/dang-bai/run-now`, `/actions/repost/run-now`,
   `/actions/tuong-tac/run-now` — chay thu ngay lap tuc khong can doi lich.
8. `GET/PUT /settings` — xem/sua gioi han like, comment, thu muc anh, thoi gian cho.

## Ghi chu quan trong

- Server chay Selenium/Chrome **tren cung may** voi backend (Selenium dieu khien
  trinh duyet that, dung profile dang nhap Facebook san co tai `C:/fb_session`
  trong `browser.py`). Neu deploy backend tren VPS Linux, can cap nhat lai
  duong dan profile va cai Chrome/Chromedriver tren VPS do.
- Scheduler duoc gioi han **chi chay 1 job cung luc** (`max_workers=1`) de tranh
  mo nhieu Chrome / xung dot phien dang nhap cung mot luc.
- Viec tu dong dang bai hang loat, tu dong like/comment/share, va lay lai noi
  dung tu nhom khac de dang lai co the vi pham Dieu khoan su dung cua Facebook
  va co nguy co bi khoa tai khoan — nen can nhac tan suat va so luong nhom khi
  van hanh thuc te.
