# -*- coding: utf-8 -*-
"""
Đăng bài lên Fanpage qua Facebook Graph API.
Nhanh, không cần Chrome, không hiển thị gì.

Cần: Page Access Token (lấy từ developers.facebook.com hoặc sync qua Selenium).
"""
import os
import requests
import uuid
from urllib.parse import urlparse
from pathlib import Path
from typing import Optional, List


GRAPH_BASE = "https://graph.facebook.com/v19.0"


def _upload_anh_graph(page_id: str, anh_path: str, access_token: str) -> Optional[str]:
    """Upload 1 ảnh (file local) lên fanpage, trả về photo_id hoặc None."""
    temp_file = None
    # If anh_path is a remote URL, download it to a temp file first
    try:
        if isinstance(anh_path, str) and anh_path.startswith(('http://', 'https://')):
            parsed = urlparse(anh_path)
            ext = Path(parsed.path).suffix or '.jpg'
            tmpdir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads', 'temp')
            os.makedirs(tmpdir, exist_ok=True)
            temp_file = os.path.join(tmpdir, f"{uuid.uuid4().hex}{ext}")
            try:
                r = requests.get(anh_path, stream=True, timeout=20)
                if not r.ok:
                    print(f"  [Graph API] Cannot download image {anh_path}: {r.status_code}")
                    return None
                with open(temp_file, 'wb') as f:
                    for chunk in r.iter_content(1024 * 8):
                        if chunk:
                            f.write(chunk)
                anh_path = temp_file
            except Exception as e:
                print(f"  [Graph API] Download image exception: {e}")
                return None

    except Exception:
        pass

    if not os.path.exists(anh_path):
        print(f"  [Graph API] Anh khong ton tai: {anh_path}")
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception:
                pass
        return None
    try:
        url = f"{GRAPH_BASE}/{page_id}/photos"
        with open(anh_path, "rb") as f:
            resp = requests.post(
                url,
                data={"access_token": access_token, "published": "false"},
                files={"source": f},
                timeout=60,
            )
        data = resp.json()
        if resp.ok and data.get("id"):
            print(f"  [Graph API] Upload anh OK: {data['id']}")
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass
            return data["id"]
        err = data.get("error", {}).get("message", str(data))
        print(f"  [Graph API] Upload anh fail: {err}")
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception:
                pass
        return None
    except Exception as e:
        print(f"  [Graph API] Upload anh exception: {e}")
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception:
                pass
        return None


def dang_bai_graph_api(
    page_id: str,
    noi_dung: str,
    access_token: str,
    anh_paths: Optional[List[str]] = None,
) -> tuple[bool, str]:
    """
    Đăng bài lên fanpage qua Graph API. Hỗ trợ đính kèm nhiều ảnh.

    - anh_paths: list đường dẫn file ảnh local. Nếu None hoặc rỗng → đăng text thuần.
    Returns: (thanh_cong: bool, chi_tiet: str)
    """
    if not page_id or not noi_dung or not access_token:
        return False, "Thiếu page_id, noi_dung hoặc access_token"

    try:
        # ── Nếu có ảnh: upload từng ảnh rồi đính vào bài ──────────────
        if anh_paths:
            photo_ids = []
            upload_errors = []
            for path in anh_paths:
                pid = _upload_anh_graph(page_id, path, access_token)
                if pid:
                    photo_ids.append(pid)
                else:
                    upload_errors.append(path)

            if photo_ids:
                # Đăng bài multi-photo: dùng /feed với attached_media
                url = f"{GRAPH_BASE}/{page_id}/feed"
                payload = {
                    "message": noi_dung,
                    "access_token": access_token,
                }
                # Thêm từng photo vào attached_media[]
                for i, photo_id in enumerate(photo_ids):
                    payload[f"attached_media[{i}]"] = f'{{"media_fbid":"{photo_id}"}}'

                resp = requests.post(url, data=payload, timeout=30)
                data = resp.json()
                if resp.ok and data.get("id"):
                    post_id = data["id"]
                    print(f"  [Graph API] Dang thanh cong (co anh): {page_id} → post_id={post_id}")
                    return True, f"SUCCESS post_id={post_id}"
                err = data.get("error", {}).get("message", str(data))
                print(f"  [Graph API] Loi dang co anh {page_id}: {err}")
                return False, f"Graph API error: {err}"

            print(f"  [Graph API] Khong upload duoc anh, huy dang text-only: {upload_errors}")
            return False, f"ERROR_GRAPH_IMAGE_UPLOAD_FAILED: {upload_errors}"

        # ── Đăng text thuần (không có ảnh) ────────────────────────────
        url = f"{GRAPH_BASE}/{page_id}/feed"
        payload = {
            "message": noi_dung,
            "access_token": access_token,
        }
        resp = requests.post(url, data=payload, timeout=30)
        data = resp.json()

        if resp.ok and data.get("id"):
            post_id = data["id"]
            print(f"  [Graph API] Dang thanh cong: {page_id} → post_id={post_id}")
            return True, f"SUCCESS post_id={post_id}"
        else:
            err = data.get("error", {})
            msg = err.get("message", str(data))
            print(f"  [Graph API] Loi {page_id}: {msg}")
            return False, f"Graph API error: {msg}"

    except Exception as e:
        return False, f"Graph API exception: {e}"


def lay_page_access_token(page_id: str, user_access_token: str) -> Optional[str]:
    """
    Đổi User Access Token → Page Access Token cho page_id cụ thể.
    Dùng endpoint /me/accounts để lấy tất cả pages và tìm đúng page.
    """
    try:
        resp = requests.get(
            f"{GRAPH_BASE}/me/accounts",
            params={"access_token": user_access_token, "limit": 100},
            timeout=15,
        )
        data = resp.json()
        for page in data.get("data", []):
            if str(page.get("id")) == str(page_id) or page.get("name", "").lower() in page_id.lower():
                return page.get("access_token")
        return None
    except Exception as e:
        print(f"[Graph API] lay_page_access_token error: {e}")
        return None


def kiem_tra_token(access_token: str) -> bool:
    """Kiểm tra token còn hạn không."""
    try:
        resp = requests.get(
            f"{GRAPH_BASE}/me",
            params={"access_token": access_token},
            timeout=10,
        )
        return resp.ok and "id" in resp.json()
    except Exception:
        return False
