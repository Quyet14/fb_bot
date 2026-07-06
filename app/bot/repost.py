# -*- coding: utf-8 -*-
"""
Chuc nang repost bai (lay bai tu nhom nguon va up lai kem nhieu anh).
"""
import os
import random
import time
import urllib.request

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from app.bot.gemini import goi_gemini_viet_lai_bai
from app.bot.browser import dong_chrome, tao_driver
from app.bot.dang_bai import dang_mot_nhom
from app.config import settings as app_config


def lay_bai_tu_nhom_nguon(driver, wait, url_nhom, so_bai):
    driver.get(url_nhom)
    time.sleep(6)

    for i in range(5):
        driver.execute_script("window.scrollBy(0, 800);")
        time.sleep(3)

    danh_sach_bai = []
    try:
        bai_dang_list = driver.find_elements(By.XPATH, '//div[@role="feed"]/div')
        if not bai_dang_list:
            bai_dang_list = driver.find_elements(By.XPATH, '//div[@data-ad-preview="preview"]/ancestor::div[contains(@class,"x1yztbdb")] | //div[@role="article"]')

        for bai in bai_dang_list:
            if len(danh_sach_bai) >= so_bai:
                break
            try:
                noi_dung = bai.text.strip()
                if not noi_dung or len(noi_dung) < 50:
                    continue
                if "Bạn viết gì" in noi_dung or "Write something" in noi_dung:
                    continue
                if any(b["noi_dung"] == noi_dung for b in danh_sach_bai):
                    continue

                danh_sach_url_anh = []
                try:
                    imgs = bai.find_elements(By.XPATH, './/img[contains(@src,"scontent")]')
                    for img in imgs:
                        src = img.get_attribute("src")
                        if src and "emoji" not in src and "50x50" not in src and "36x36" not in src and "72x72" not in src:
                            if src not in danh_sach_url_anh:
                                danh_sach_url_anh.append(src)
                        if len(danh_sach_url_anh) >= 4:
                            break
                except Exception:
                    pass

                danh_sach_bai.append({
                    "noi_dung": noi_dung,
                    "danh_sach_url_anh": danh_sach_url_anh
                })

            except Exception:
                continue

    except Exception as e:
        print(f"  Loi lay bai nguon: {e}")

    return danh_sach_bai


def repost_bai_vao_nhom(driver, wait, url_nhom, noi_dung_goc, danh_sach_url_anh, thu_muc_anh):
    noi_dung_moi = goi_gemini_viet_lai_bai(noi_dung_goc)
    if not noi_dung_moi:
        noi_dung_moi = noi_dung_goc

    danh_sach_anh_tai_ve = []
    if danh_sach_url_anh:
        if not os.path.exists(thu_muc_anh):
            os.makedirs(thu_muc_anh)

        for i, url in enumerate(danh_sach_url_anh):
            try:
                ten_file = f"repost_{int(time.time())}_{i}.jpg"
                duong_dan = os.path.abspath(os.path.join(thu_muc_anh, ten_file))
                urllib.request.urlretrieve(url, duong_dan)
                danh_sach_anh_tai_ve.append(duong_dan)
            except Exception as e:
                print(f"  -> Loi tai anh thu {i+1}: {e}")

    ket_qua = dang_mot_nhom(driver, wait, url_nhom, noi_dung_moi, danh_sach_anh_tai_ve)

    for path in danh_sach_anh_tai_ve:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

    return ket_qua


def thuc_thi_tien_trinh_repost(nhom_nguon_urls, nhom_dich_urls, so_bai, thu_muc_anh):
    """Tra ve: (thanh_cong: bool, chi_tiet: str)"""
    print(f"\n=== BAT DAU REPOST BAI ===")
    driver = None
    try:
        dong_chrome()
        driver = tao_driver(headless=app_config.HEADLESS_MODE)
        wait = WebDriverWait(driver, 30)
        driver.get("https://www.facebook.com")
        time.sleep(5)

        tat_ca_bai = []
        for url in nhom_nguon_urls:
            bai_list = lay_bai_tu_nhom_nguon(driver, wait, url, so_bai)
            tat_ca_bai.extend(bai_list)

        if not tat_ca_bai:
            return False, "Khong lay duoc bai nao tu nhom nguon."

        chi_tiet = []
        for bai in tat_ca_bai[:so_bai]:
            for url_dich in nhom_dich_urls:
                ket_qua = repost_bai_vao_nhom(driver, wait, url_dich, bai["noi_dung"], bai.get("danh_sach_url_anh"), thu_muc_anh)
                chi_tiet.append(f"{url_dich}: {ket_qua}")
                time.sleep(random.randint(90, 150))

        print("=== HOAN THANH REPOST ===")
        return True, "\n".join(chi_tiet)

    except Exception as e:
        return False, f"Loi repost: {e}"
    finally:
        if driver:
            driver.quit()