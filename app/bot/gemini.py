# -*- coding: utf-8 -*-
"""
Cac ham goi Gemini AI: viet bai, viet comment, viet lai bai.
"""
import json
import time
import urllib.request
import urllib.error

from app.config import settings
GEMINI_API_KEY = "......."


def goi_gemini(prompt, so_lan_thu=3):
    if not settings.GEMINI_API_KEY:
        print("Loi Gemini: GEMINI_API_KEY chua duoc cau hinh. Vui long them GEMINI_API_KEY vao .env hoac bien moi truong.")
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    for lan_thu in range(so_lan_thu):
        try:
            req = urllib.request.Request(
                url, data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except urllib.error.HTTPError as e:
            chi_tiet = e.read().decode()
            print(f"Loi HTTP Gemini (lan {lan_thu+1}): {e.code} - {chi_tiet}")
            if e.code in [429, 503]:
                time.sleep(30 * (lan_thu + 1))
            else:
                break
        except Exception as e:
            print(f"Loi Gemini: {e}")
            break
    return None


def goi_gemini_viet_bai(chu_de):
    return goi_gemini(f"""Viet mot bai dang Facebook ngan (3-5 cau) bang tieng Viet co dau, 
chu de: {chu_de}. Giong van than thien, tu nhien, phu hop dang vao nhom cong dong. 
Khong dung hashtag. Khong dung dau ngoac kep o dau/cuoi.""")


def goi_gemini_viet_comment(noi_dung_bai):
    res = goi_gemini(f"""Doc bai viet Facebook sau va viet duy nhat MOT cau binh luan ngan (duoi 12 chu).
Giong dieu lich su, tich cuc, than thien tu nhien. Khong lam danh sach, khong danh so.
Bai viet: "{noi_dung_bai[:300]}" """)
    if res:
        return res.replace('"', '').replace("'", "")
    return "Bài viết hay quá chủ thớt! 👍"


def goi_gemini_viet_lai_bai(noi_dung_goc):
    return goi_gemini(f"""Hay viet lai bai Facebook sau bang ngon ngu cua ban, giu nguyen y nghia chinh 
nhung thay doi cach dien dat hoan toan, them cam xuc ca nhan. Ket qua la 1 bai hoan chinh, khong co phan giai thich.
Bai goc: "{noi_dung_goc[:500]}" """)