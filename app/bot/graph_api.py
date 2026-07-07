# -*- coding: utf-8 -*-
"""
Đăng bài lên Fanpage qua Facebook Graph API.
Nhanh, không cần Chrome, không hiển thị gì.

Cần: Page Access Token (lấy từ developers.facebook.com hoặc sync qua Selenium).
"""
import requests
from typing import Optional


GRAPH_BASE = "https://graph.facebook.com/v19.0"


def dang_bai_graph_api(
    page_id: str,
    noi_dung: str,
    access_token: str,
    anh_url: Optional[str] = None,
) -> tuple[bool, str]:
    """
    Đăng bài lên fanpage qua Graph API.
    
    Returns: (thanh_cong: bool, chi_tiet: str)
    """
    if not page_id or not noi_dung or not access_token:
        return False, "Thiếu page_id, noi_dung hoặc access_token"

    try:
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
