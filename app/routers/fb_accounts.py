# -*- coding: utf-8 -*-
"""
Router quản lý tài khoản Facebook được liên kết.
Lưu cookie/session Facebook của từng tài khoản để bot có thể
đăng nhập và lấy danh sách fanpage mà tài khoản đó quản lý.

Endpoints:
  GET    /fb-accounts/             — danh sách tài khoản đã liên kết
  POST   /fb-accounts/             — thêm tài khoản mới (username + password)
  DELETE /fb-accounts/{account_id} — xóa tài khoản
  POST   /fb-accounts/{account_id}/sync-fanpages — dùng Selenium lấy fanpage
  GET    /fb-accounts/{account_id}/fanpages      — danh sách fanpage của tài khoản
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone

from app.mongo_db import get_collection
from app.dependencies import get_user_id

router = APIRouter(prefix="/fb-accounts", tags=["Tai khoan Facebook"])

# ── Collections ──────────────────────────────────────────────
def _accounts_col():
    return get_collection("fb_accounts")

def _counters_col():
    return get_collection("counters")

def _next_id(name: str) -> int:
    doc = _counters_col().find_one_and_update(
        {"_id": name}, {"$inc": {"seq": 1}}, upsert=True, return_document=True
    )
    return int(doc.get("seq", 0))


# ── Schemas ───────────────────────────────────────────────────
class FbAccountCreate(BaseModel):
    ten_hien_thi: str          # tên hiển thị để nhận biết
    email_or_phone: str        # email hoặc số điện thoại đăng nhập FB
    password: str              # mật khẩu FB (lưu để bot tự đăng nhập)

class FbAccountOut(BaseModel):
    id: int
    ten_hien_thi: str
    email_or_phone: str
    trang_thai: str            # "chua_lien_ket" | "da_lien_ket" | "loi"
    tao_luc: datetime
    lan_sync_cuoi: Optional[datetime] = None
    so_fanpage: int = 0

class FanpageInfo(BaseModel):
    page_id: str
    ten: str
    the_loai: Optional[str] = None
    avatar_url: Optional[str] = None
    url: Optional[str] = None
    page_access_token: Optional[str] = None   # Page Access Token để đăng qua Graph API


def _fmt_account(doc) -> FbAccountOut:
    if not doc:
        return None
    fanpages = doc.get("fanpages") or []
    return FbAccountOut(
        id=int(doc["id"]),
        ten_hien_thi=doc.get("ten_hien_thi", ""),
        email_or_phone=doc.get("email_or_phone", ""),
        trang_thai=doc.get("trang_thai", "chua_lien_ket"),
        tao_luc=doc.get("tao_luc", datetime.now(timezone.utc)),
        lan_sync_cuoi=doc.get("lan_sync_cuoi"),
        so_fanpage=len(fanpages),
    )


# ── Endpoints ─────────────────────────────────────────────────
@router.get("/", response_model=List[FbAccountOut])
def list_accounts(user_id: str = Depends(get_user_id)):
    docs = list(_accounts_col().find({"user_id": user_id}).sort("id", 1))
    return [_fmt_account(d) for d in docs]


@router.post("/", response_model=FbAccountOut, status_code=201)
def add_account(data: FbAccountCreate, user_id: str = Depends(get_user_id)):
    existing = _accounts_col().find_one({"email_or_phone": data.email_or_phone, "user_id": user_id})
    if existing:
        raise HTTPException(400, "Tài khoản với email/SĐT này đã được thêm")
    payload = {
        "id": _next_id("fb_accounts"),
        "user_id": user_id,
        "ten_hien_thi": data.ten_hien_thi,
        "email_or_phone": data.email_or_phone,
        "password": data.password,          # lưu plain — chỉ dùng local/self-hosted
        "trang_thai": "chua_lien_ket",
        "fanpages": [],
        "tao_luc": datetime.now(timezone.utc),
        "lan_sync_cuoi": None,
    }
    _accounts_col().insert_one(payload)
    return _fmt_account(payload)


class FbAccountUpdate(BaseModel):
    ten_hien_thi: Optional[str] = None
    email_or_phone: Optional[str] = None
    password: Optional[str] = None


@router.put("/{account_id}", response_model=FbAccountOut)
def update_account(account_id: int, data: FbAccountUpdate, user_id: str = Depends(get_user_id)):
    """Cập nhật thông tin tài khoản (tên, email/SĐT, mật khẩu)."""
    doc = _accounts_col().find_one({"id": account_id, "user_id": user_id})
    if not doc:
        raise HTTPException(404, "Không tìm thấy tài khoản")
    patch: dict = {}
    if data.ten_hien_thi is not None:
        patch["ten_hien_thi"] = data.ten_hien_thi
    if data.email_or_phone is not None:
        # Kiểm tra trùng với tài khoản khác của cùng user
        dup = _accounts_col().find_one({"email_or_phone": data.email_or_phone, "user_id": user_id, "id": {"$ne": account_id}})
        if dup:
            raise HTTPException(400, "Email/SĐT này đã được dùng bởi tài khoản khác")
        patch["email_or_phone"] = data.email_or_phone
    if data.password is not None and data.password.strip():
        patch["password"] = data.password.strip()
    if patch:
        _accounts_col().update_one({"id": account_id, "user_id": user_id}, {"$set": patch})
    updated = _accounts_col().find_one({"id": account_id, "user_id": user_id})
    return _fmt_account(updated)


@router.delete("/{account_id}", status_code=204)
def delete_account(account_id: int, user_id: str = Depends(get_user_id)):
    result = _accounts_col().delete_one({"id": account_id, "user_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(404, "Không tìm thấy tài khoản")


@router.get("/{account_id}/fanpages", response_model=List[FanpageInfo])
def get_fanpages(account_id: int, user_id: str = Depends(get_user_id)):
    doc = _accounts_col().find_one({"id": account_id, "user_id": user_id})
    if not doc:
        raise HTTPException(404, "Không tìm thấy tài khoản")
    return [FanpageInfo(**fp) for fp in (doc.get("fanpages") or [])]


@router.get("/{account_id}/status")
def get_account_status(account_id: int, user_id: str = Depends(get_user_id)):
    """Trả về trạng thái tài khoản để UI polling."""
    doc = _accounts_col().find_one({"id": account_id, "user_id": user_id})
    if not doc:
        raise HTTPException(404, "Không tìm thấy tài khoản")
    fanpages = doc.get("fanpages") or []
    return {
        "id": account_id,
        "trang_thai": doc.get("trang_thai", "chua_lien_ket"),
        "so_fanpage": len(fanpages),
        "lan_sync_cuoi": doc.get("lan_sync_cuoi"),
        "fanpages": [{"page_id": fp["page_id"], "ten": fp["ten"], "url": fp.get("url","")} for fp in fanpages],
    }


@router.post("/{account_id}/sync-fanpages")
def sync_fanpages(account_id: int, background_tasks: BackgroundTasks, user_id: str = Depends(get_user_id)):
    """
    Kích hoạt đồng bộ fanpage trong background.
    Bot sẽ mở Chrome hiển thị để người dùng có thể xử lý 2FA.
    """
    doc = _accounts_col().find_one({"id": account_id, "user_id": user_id})
    if not doc:
        raise HTTPException(404, "Không tìm thấy tài khoản")
    _accounts_col().update_one({"id": account_id, "user_id": user_id}, {"$set": {"trang_thai": "dang_sync"}})
    background_tasks.add_task(_do_sync_fanpages, account_id, doc, user_id)
    return {"message": "Chrome đang mở. Xử lý xác minh nếu có, bot sẽ tự lấy fanpage."}


@router.post("/{account_id}/add-fanpage-manual")
def add_fanpage_manual(account_id: int, data: FanpageInfo, user_id: str = Depends(get_user_id)):
    """Thêm fanpage thủ công (khi auto-sync không tìm được)."""
    doc = _accounts_col().find_one({"id": account_id, "user_id": user_id})
    if not doc:
        raise HTTPException(404, "Không tìm thấy tài khoản")
    fanpages = doc.get("fanpages") or []
    # Kiểm tra trùng
    if any(fp.get("page_id") == data.page_id for fp in fanpages):
        raise HTTPException(400, "Fanpage đã tồn tại")
    fanpages.append(data.model_dump())
    _accounts_col().update_one(
        {"id": account_id, "user_id": user_id},
        {"$set": {"fanpages": fanpages, "trang_thai": "da_lien_ket"}}
    )
    return {"message": f"Đã thêm fanpage '{data.ten}'", "total": len(fanpages)}


@router.delete("/{account_id}/fanpages/{page_id}", status_code=204)
def remove_fanpage(account_id: int, page_id: str, user_id: str = Depends(get_user_id)):
    """Xóa một fanpage khỏi tài khoản."""
    doc = _accounts_col().find_one({"id": account_id, "user_id": user_id})
    if not doc:
        raise HTTPException(404, "Không tìm thấy tài khoản")
    fanpages = [fp for fp in (doc.get("fanpages") or []) if fp.get("page_id") != page_id]
    _accounts_col().update_one({"id": account_id, "user_id": user_id}, {"$set": {"fanpages": fanpages}})


class TokenUpdate(BaseModel):
    user_access_token: str   # Long-lived User Access Token


@router.post("/{account_id}/update-tokens")
def update_page_tokens(account_id: int, data: TokenUpdate, user_id: str = Depends(get_user_id)):
    """
    Dùng User Access Token để lấy Page Access Token cho tất cả fanpage.
    Lưu vào DB để đăng bài qua Graph API (nhanh, không cần Chrome).
    
    Cách lấy User Access Token:
    1. Vào https://developers.facebook.com/tools/explorer/
    2. Chọn app → Generate User Access Token
    3. Cấp quyền: pages_manage_posts, pages_read_engagement
    """
    from app.bot.graph_api import lay_page_access_token, kiem_tra_token

    doc = _accounts_col().find_one({"id": account_id, "user_id": user_id})
    if not doc:
        raise HTTPException(404, "Không tìm thấy tài khoản")

    if not kiem_tra_token(data.user_access_token):
        raise HTTPException(400, "User Access Token không hợp lệ hoặc đã hết hạn")

    fanpages = doc.get("fanpages") or []
    updated = 0
    for fp in fanpages:
        token = lay_page_access_token(fp["page_id"], data.user_access_token)
        if token:
            fp["page_access_token"] = token
            updated += 1

    _accounts_col().update_one(
        {"id": account_id, "user_id": user_id},
        {"$set": {"fanpages": fanpages, "user_access_token": data.user_access_token}}
    )
    return {"message": f"Đã cập nhật token cho {updated}/{len(fanpages)} fanpage", "updated": updated}


@router.post("/{account_id}/fanpages/{page_id}/set-token")
def set_page_token_manual(account_id: int, page_id: str, token: str, user_id: str = Depends(get_user_id)):
    """Nhập thủ công Page Access Token cho một fanpage cụ thể."""
    doc = _accounts_col().find_one({"id": account_id, "user_id": user_id})
    if not doc:
        raise HTTPException(404, "Không tìm thấy tài khoản")
    fanpages = doc.get("fanpages") or []
    found = False
    for fp in fanpages:
        if fp.get("page_id") == page_id:
            fp["page_access_token"] = token
            found = True
            break
    if not found:
        raise HTTPException(404, "Không tìm thấy fanpage")
    _accounts_col().update_one({"id": account_id, "user_id": user_id}, {"$set": {"fanpages": fanpages}})
    return {"message": "Đã lưu Page Access Token"}


def _do_sync_fanpages(account_id: int, doc: dict, user_id: str):
    """
    Background task: mở Chrome hiển thị, tự điền email/pass rồi chờ
    người dùng xử lý 2FA/checkpoint (nếu có). Sau khi đăng nhập xong
    sẽ tự động scrape danh sách fanpage.
    """
    try:
        from app.bot.browser import tao_driver
        from app.config import settings
        import time
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.options import Options
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service as ChromeService
        from webdriver_manager.chrome import ChromeDriverManager

        email = doc["email_or_phone"]
        password = doc["password"]

        # ── Tạo driver HIỂN THỊ (không headless, không đẩy ra ngoài màn hình) ──
        opts = Options()
        opts.add_argument("--user-data-dir=C:/fb_session_sync")  # session riêng để không đụng bot
        opts.add_argument("--start-maximized")
        opts.add_argument("--no-first-run")
        opts.add_argument("--no-default-browser-check")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)
        # KHÔNG thêm --headless và KHÔNG đẩy cửa sổ ra ngoài màn hình

        driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            options=opts
        )
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
        })

        fanpages = []
        try:
            # Điền thông tin đăng nhập
            driver.get("https://www.facebook.com/login")
            time.sleep(3)

            try:
                driver.find_element(By.ID, "email").clear()
                driver.find_element(By.ID, "email").send_keys(email)
                driver.find_element(By.ID, "pass").clear()
                driver.find_element(By.ID, "pass").send_keys(password)
                driver.find_element(By.NAME, "login").click()
            except Exception as e:
                print(f"[sync_fanpages] fill login error: {e}")

            # Chờ tối đa 120 giây để người dùng xử lý 2FA/checkpoint/captcha
            print("[sync_fanpages] Waiting for login... (max 120s)")
            logged_in = False
            for _ in range(24):   # 24 * 5s = 120s
                time.sleep(5)
                url = driver.current_url
                # Đăng nhập thành công khi URL không còn /login hay /checkpoint
                if not any(x in url for x in ["/login", "/checkpoint", "/two_step"]):
                    logged_in = True
                    print(f"[sync_fanpages] Logged in! URL: {url}")
                    break

            if not logged_in:
                print("[sync_fanpages] Login timeout or failed")
                _accounts_col().update_one(
                    {"id": account_id},
                    {"$set": {"trang_thai": "loi", "lan_sync_cuoi": datetime.now(timezone.utc)}}
                )
                return

            # Scrape fanpage từ facebook.com/pages/?category=your_pages
            time.sleep(2)
            fanpages = []
            seen_ids = set()

            driver.get("https://www.facebook.com/pages/?category=your_pages")
            time.sleep(6)

            # Cuộn để load thêm page cards
            last_height = 0
            for _ in range(8):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            # Dùng JS chính xác: tìm card page theo cấu trúc DOM của Facebook
            # Mỗi card page có: ảnh đại diện + tên page (heading) + nút "Tạo bài viết"
            page_data = driver.execute_script("""
                var results = [];
                var seen = {};

                // Chiến lược 1: Tìm các div chứa nút "Tạo bài viết" hoặc "Create post"
                // Đây là dấu hiệu chắc chắn nhất của card page bạn quản lý
                var createBtns = document.querySelectorAll(
                    'a[href*="new_post"], div[role="button"]'
                );

                // Chiến lược 2: Tìm tất cả <a> có href chứa facebook.com/{slug}
                // và nằm trong cùng container với nút "Tạo bài viết"
                // Dùng approach: lấy heading gần nút "Tạo bài viết"
                var allContainers = document.querySelectorAll(
                    'div[data-pagelet], div[role="feed"] > div, ' +
                    'div[role="main"] > div > div > div'
                );

                // Chiến lược đơn giản nhất: lấy link có href là URL fanpage
                // và text là heading (h1-h4 hoặc [role=heading]) bên trong link đó
                var pageLinks = document.querySelectorAll('a[href]');
                pageLinks.forEach(function(a) {
                    var href = (a.href || '').split('?')[0].split('#')[0];
                    if (!href || !href.includes('facebook.com')) return;

                    // Bỏ qua link hệ thống
                    var systemPaths = [
                        '/home','/friends','/groups','/marketplace','/watch',
                        '/gaming','/events','/reels','/search','/notifications',
                        '/messages','/stories','/settings','/help','/policies',
                        '/login','/checkpoint','/bookmarks','/saved','/profile',
                        '/ads','/business','/photo','/video','/pages/?',
                        'new_post','create','inbox','insights','/?',
                        '/pg/','messenger','l.facebook','m.facebook'
                    ];
                    for (var i = 0; i < systemPaths.length; i++) {
                        if (href.indexOf(systemPaths[i]) !== -1) return;
                    }

                    // Lấy tên page từ heading con trực tiếp trong thẻ <a>
                    var heading = a.querySelector(
                        '[role="heading"], h1, h2, h3, h4, h5, ' +
                        '[class*="x1heor9g"], [class*="xt0psk2"]'
                    );
                    var name = '';
                    if (heading) {
                        name = (heading.innerText || heading.textContent || '').trim();
                    }
                    // Nếu không có heading con, thử lấy span con đầu tiên có text
                    if (!name) {
                        var spans = a.querySelectorAll('span');
                        for (var s = 0; s < spans.length; s++) {
                            var t = (spans[s].innerText || spans[s].textContent || '').trim();
                            // Tên page hợp lệ: không phải số, không phải "Tạo bài viết"
                            if (t && t.length > 2 && t.length < 100 &&
                                !['Tạo bài viết','Create post','Quảng cáo','Advertise',
                                  'Xem thêm','See more','Khám phá','Hộp thư'].includes(t)) {
                                name = t;
                                break;
                            }
                        }
                    }
                    if (!name || name.length < 2 || name.length > 150) return;

                    // Bỏ qua text là thông báo (chứa "phút", "giờ", "Chưa đọc")
                    var noiseWords = ['phút','giờ','ngày','tuần','Chưa đọc','đang chờ',
                                      'trả lời','tin nhắn','thông báo','lượt thích',
                                      'người theo','đăng nhập'];
                    for (var n = 0; n < noiseWords.length; n++) {
                        if (name.indexOf(noiseWords[n]) !== -1) return;
                    }

                    // Lấy page_id/slug từ URL
                    var clean = href.replace(/\\/+$/, '');
                    var pageId;
                    if (clean.indexOf('/pages/') !== -1) {
                        var parts = clean.split('/pages/')[1].split('/');
                        pageId = parts[parts.length - 1] || parts[0];
                    } else {
                        pageId = clean.split('facebook.com/')[1] || clean;
                    }
                    pageId = pageId.replace(/\\/+$/, '');
                    if (!pageId || pageId.length < 2) return;

                    if (seen[pageId]) return;
                    seen[pageId] = true;

                    results.push({
                        page_id: pageId,
                        ten: name,
                        url: clean
                    });
                });

                return results;
            """)

            for item in (page_data or []):
                pid = item.get("page_id","")
                name = item.get("ten","").strip()
                url = item.get("url","")
                if pid and name and pid not in seen_ids:
                    seen_ids.add(pid)
                    fanpages.append({
                        "page_id": pid,
                        "ten": name,
                        "url": url,
                        "the_loai": None,
                        "avatar_url": None,
                    })

            print(f"[sync_fanpages] Total found: {len(fanpages)} fanpages")
            for fp in fanpages:
                print(f"  · {fp['ten']} | {fp['url']}")

            # ── Lấy Page Access Token qua Graph API dùng cookie FB ──────
            # Sau khi đăng nhập, lấy access_token từ session hiện tại
            user_token = None
            try:
                # Facebook lưu access token trong localStorage hoặc có thể lấy qua /me endpoint
                # Dùng JavaScript để lấy từ cookie datr + c_user
                cookies = driver.get_cookies()
                # Thử gọi endpoint lấy token không cần app_id
                token_resp = driver.execute_script("""
                    try {
                        // Thử lấy token từ Facebook internal API
                        var result = null;
                        // Gọi /me/accounts để lấy page tokens
                        var xhr = new XMLHttpRequest();
                        xhr.open('GET', 'https://www.facebook.com/api/graphql/', false);
                        return null;
                    } catch(e) { return null; }
                """)

                # Cách đáng tin cậy hơn: dùng requests với cookie session
                import requests
                cookie_dict = {c['name']: c['value'] for c in cookies}

                # Lấy token từ Facebook API với cookie
                resp = requests.get(
                    "https://www.facebook.com/api/graphql/",
                    params={
                        "doc_id": "6628537733865",  # GraphQL doc_id cho pages
                        "variables": '{"count":25}',
                    },
                    cookies=cookie_dict,
                    headers={
                        "User-Agent": driver.execute_script("return navigator.userAgent"),
                        "X-FB-Friendly-Name": "PagesManagerHomePageQuery",
                    },
                    timeout=15
                )

                # Thử lấy token theo cách khác: endpoint chính thức với cookie
                resp2 = requests.get(
                    "https://www.facebook.com/v19.0/me/accounts",
                    params={"access_token": ""},
                    cookies=cookie_dict,
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=15
                )
                data2 = resp2.json()
                if data2.get("data"):
                    # Có token — lưu vào từng fanpage
                    page_token_map = {str(p["id"]): p.get("access_token","") for p in data2["data"]}
                    for fp in fanpages:
                        pid = fp.get("page_id","")
                        if pid in page_token_map and page_token_map[pid]:
                            fp["page_access_token"] = page_token_map[pid]
                    user_token = data2.get("data", [{}])[0].get("access_token")
                    print(f"[sync_fanpages] Got tokens for {len(page_token_map)} pages via /me/accounts")

            except Exception as e_token:
                print(f"[sync_fanpages] Token extraction warn (ok to ignore): {e_token}")

            # Nếu vẫn không tìm được, chụp screenshot để debug
            if not fanpages:
                try:
                    import os
                    ts = int(time.time())
                    path = f"C:/fb_sync_debug_{account_id}_{ts}.png"
                    driver.save_screenshot(path)
                    print(f"[sync_fanpages] Screenshot saved: {path}")
                    # Lưu HTML để debug
                    html_path = f"C:/fb_sync_debug_{account_id}_{ts}.html"
                    with open(html_path, "w", encoding="utf-8") as f:
                        f.write(driver.page_source)
                    print(f"[sync_fanpages] HTML saved: {html_path}")
                except Exception as e_ss:
                    print(f"[sync_fanpages] screenshot error: {e_ss}")

        finally:
            driver.quit()

        _accounts_col().update_one(
            {"id": account_id, "user_id": user_id},
            {"$set": {
                "trang_thai": "da_lien_ket" if fanpages else "da_lien_ket_0",
                "fanpages": fanpages,
                "lan_sync_cuoi": datetime.now(timezone.utc),
                **({"user_access_token": user_token} if user_token else {}),
            }}
        )

    except Exception as e:
        print(f"[sync_fanpages] FATAL account={account_id}: {e}")
        _accounts_col().update_one(
            {"id": account_id, "user_id": user_id},
            {"$set": {"trang_thai": "loi", "lan_sync_cuoi": datetime.now(timezone.utc)}}
        )
