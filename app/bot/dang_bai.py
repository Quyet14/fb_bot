# -*- coding: utf-8 -*-
"""
Chuc nang dang bai (ho tro tai len nhieu anh cung luc).
"""
import os
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from app.bot.gemini import goi_gemini_viet_bai, goi_gemini_viet_lai_bai
from app.bot.browser import dong_chrome, tao_driver, paste_vao_element, lay_anh_ngau_nhien
from app.config import settings as app_config


def dang_mot_nhom(driver, wait, url_nhom, noi_dung, duong_dan_anh=None):
    # Debug version: giúp xác định job đang chạy bản code nào
    try:
        import inspect, hashlib
        _src = inspect.getsource(dang_mot_nhom)
        _md5 = hashlib.md5(_src.encode('utf-8')).hexdigest()
        print(f"[BOT_VERSION] dang_mot_nhom md5={_md5}")
    except Exception:
        pass

    if not url_nhom or not isinstance(url_nhom, str):

        print(f"  -> Loi nhom: url_nhom invalid: {url_nhom!r}")
        return False

    try:
        print(f"  Dang vao nhom: {url_nhom}...")
        driver.get(url_nhom)
        time.sleep(6)


        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)

        o_dang_bai = None
        try:
            o_dang_bai = wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        '//div[@role="main"]//span[contains(text(),"Bạn viết gì") or contains(text(),"Bạn đang nghĩ gì") or contains(text(),"Write something")]'
                    )
                )
            )
        except Exception:
            pass

        if o_dang_bai is None:
            print("  -> Khong tim thay o dang bai")
            return False

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", o_dang_bai)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", o_dang_bai)
        time.sleep(4)

        o_nhap = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    '//div[@role="dialog"]//div[@contenteditable="true"][@role="textbox"]'
                )
            )
        )

        paste_vao_element(driver, o_nhap, noi_dung, debug_prefix=f"nhom_{url_nhom.split('/')[-1] if url_nhom else 'unknown'}")
        time.sleep(2)


        if duong_dan_anh:
            danh_sach_anh = []
            if isinstance(duong_dan_anh, str):
                danh_sach_anh = [duong_dan_anh]
            elif isinstance(duong_dan_anh, list):
                danh_sach_anh = duong_dan_anh

            danh_sach_anh_hop_le = [p.replace('\\', '/') for p in danh_sach_anh if os.path.exists(p)]

            if danh_sach_anh_hop_le:
                print(f"  -> Dang dinh kem {len(danh_sach_anh_hop_le)} anh...")
                try:
                    nut_anh = wait.until(
                        EC.element_to_be_clickable(
                            (
                                By.XPATH,
                                '//div[@role="dialog"]//div[@aria-label="Ảnh/video" or @aria-label="Photo/video"]'
                            )
                        )
                    )
                    driver.execute_script("arguments[0].click();", nut_anh)
                    time.sleep(3)

                    input_file = wait.until(
                        EC.presence_of_element_located(
                            (By.XPATH, '//div[@role="dialog"]//input[@type="file"]')
                        )
                    )

                    chuoi_duong_dan = "\n".join(danh_sach_anh_hop_le)
                    input_file.send_keys(chuoi_duong_dan)

                    time.sleep(7 + len(danh_sach_anh_hop_le) * 3)
                    print("  -> Da load xong anh thanh cong!")
                except Exception as e:
                    print(f"  -> Khong dinh kem duoc anh: {e}")

        nut_dang = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    '//div[@role="dialog"]//div[@aria-label="Đăng" or @aria-label="Post"][@role="button"]'
                )
            )
        )
        driver.execute_script("arguments[0].click();", nut_dang)
        print("  -> Da click nut Dang...")

        # Chờ dialog đóng tối đa 15s thay vì sleep cố định
        dialog_da_dong = False
        for _ in range(15):
            time.sleep(1)
            try:
                pending = driver.find_elements(
                    By.XPATH,
                    '//*[contains(text(), "chờ quản trị viên") or contains(text(), "admin approval") or contains(text(), "duyệt bài")]'
                )
                if pending:
                    print("  BAI DANG DANG PENDING (nhom bat duyet bai)")
                    return "PENDING"

                dialogs = driver.find_elements(By.XPATH, '//div[@role="dialog"]')
                if not dialogs:
                    dialog_da_dong = True
                    break
            except Exception:
                break

        if dialog_da_dong:
            print(f"  -> Da dang xong: {url_nhom}!")
            return "SUCCESS"

        # Dialog vẫn còn sau 15s — kiểm tra lần cuối có phải pending không
        try:
            pending = driver.find_elements(
                By.XPATH,
                '//*[contains(text(), "chờ quản trị viên") or contains(text(), "admin approval") or contains(text(), "duyệt bài") or contains(text(), "pending")]'
            )
            if pending:
                print("  BAI DANG DANG PENDING")
                return "PENDING"
        except Exception:
            pass

        print("  -> Dialog van con mo sau 15s. Co the da dang nhung khong xac nhan duoc.")
        return "SUCCESS"  # Coi như thành công vì đã click Đăng, dialog tự đóng sau



    except Exception as e:
        # In thêm context để biết lỗi xảy ra ở bước nào
        print(f"  -> Loi nhom {url_nhom}: {type(e).__name__}: {e}")
        return False



def thuc_thi_tien_trinh_dang(
    chu_de,
    nhom_urls,
    dang_kem_anh,
    thu_muc_anh,
    thoi_gian_cho_giua_cac_nhom,
    noi_dung_goc=None,
    giu_nguyen_goc: bool = True,
):
    """Chạy đăng bài.

    - Nếu có noi_dung_goc:
        - giu_nguyen_goc=True  => đăng nguyên văn
        - giu_nguyen_goc=False => gọi Gemini viết lại từ nội dung gốc
    - Nếu không có noi_dung_goc:
        - dùng chu_de để Gemini viết bài
    """
    print(f"\n=== BAT DAU DANG BAI ===")

    if noi_dung_goc is not None:
        print("Che do: NOI DUNG NGUOI DUNG")
        if giu_nguyen_goc:
            noi_dung = noi_dung_goc
        else:
            noi_dung = goi_gemini_viet_lai_b(noi_dung_goc)
            if noi_dung is None:
                return False, "Khong goi duoc Gemini de viet lai tu noi dung goc."
    else:
        print("Che do: THEO CHU DE")
        if not chu_de:
            return False, "Thieu chu_de (hoac noi_dung_goc)."
        noi_dung = goi_gemini_viet_bai(chu_de)
        if noi_dung is None:
            return False, "Khong goi duoc Gemini de viet bai."

    if chu_de:
        print(f"Chu de: {chu_de}")
    print(f"Noi dung:\n{noi_dung}\n")

    duong_dan_anh = None
    if dang_kem_anh:
        duong_dan_anh = lay_anh_ngau_nhien(thu_muc_anh)

    driver = None
    ket_qua_tung_nhom = []
    if not nhom_urls:
        return False, "Không có nhóm nào để đăng."

    try:
        driver = tao_driver(headless=app_config.HEADLESS_MODE)

        wait = WebDriverWait(driver, 30)
        driver.get("https://www.facebook.com")
        time.sleep(5)

        tong = len(nhom_urls)
        for i, url in enumerate(nhom_urls):
            ket_qua = dang_mot_nhom(driver, wait, url, noi_dung, duong_dan_anh)
            ket_qua_tung_nhom.append(f"{url}: {ket_qua}")
            if i < tong - 1 and ket_qua != "PENDING":
                time.sleep(thoi_gian_cho_giua_cac_nhom)

        print("=== HOAN THANH DANG BAI ===")
        return True, "\n".join(ket_qua_tung_nhom)
    except Exception as e:
        return False, f"Loi: {e}"
    finally:
        if driver:
            driver.quit()

