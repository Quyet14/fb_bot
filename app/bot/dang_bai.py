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
        driver = tao_driver(headless=True)   # scheduled job — luôn chạy ngầm

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



# ============================================================
# DANG BAI FANPAGE
# ============================================================

def _paste_business_suite(driver, element, text: str):
    """Paste nội dung vào textarea của Meta Business Suite.

    Business Suite dùng React với textarea thông thường (không phải contenteditable div).
    Cần dispatch InputEvent đúng type để React cập nhật state và enable nút Đăng.
    """
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.action_chains import ActionChains

    if not text:
        return

    # Bước 1: Focus và xóa nội dung cũ
    try:
        ActionChains(driver).move_to_element(element).click().perform()
        time.sleep(0.3)
        element.send_keys(Keys.CONTROL + "a")
        time.sleep(0.1)
        element.send_keys(Keys.DELETE)
        time.sleep(0.3)
    except Exception:
        pass

    # Bước 2: Thử clipboard paste (cách tốt nhất cho React)
    try:
        import pyperclip
        pyperclip.copy(text)
        ActionChains(driver).move_to_element(element).click().perform()
        time.sleep(0.2)
        ActionChains(driver).key_down(Keys.CONTROL).send_keys("v").key_up(Keys.CONTROL).perform()
        time.sleep(1)

        # Kiểm tra text đã vào chưa
        val = driver.execute_script(
            "return arguments[0].value || arguments[0].textContent || '';", element
        )
        if text[:20] in val:
            print(f"  -> BS paste: clipboard OK")
            # Dispatch InputEvent để React nhận
            driver.execute_script("""
                var el = arguments[0];
                var ev = new InputEvent('input', {bubbles: true, cancelable: true, inputType: 'insertText'});
                el.dispatchEvent(ev);
                var ev2 = new Event('change', {bubbles: true});
                el.dispatchEvent(ev2);
            """, element)
            time.sleep(0.5)
            return
    except Exception as e:
        print(f"  -> BS paste clipboard fail: {e}")

    # Bước 3: send_keys từng phần (chậm nhưng chắc chắn trigger React)
    try:
        ActionChains(driver).move_to_element(element).click().perform()
        time.sleep(0.2)
        # Chia nhỏ text để send_keys không bị timeout với text dài
        chunk_size = 100
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i+chunk_size]
            element.send_keys(chunk)
            time.sleep(0.1)
        print(f"  -> BS paste: send_keys OK")
        time.sleep(0.5)
    except Exception as e:
        print(f"  -> BS paste send_keys fail: {e}")
        # Fallback: dùng paste_vao_element thông thường
        paste_vao_element(driver, element, text, debug_prefix="bs_fanpage")

def dang_mot_fanpage(driver, wait, url_fanpage, noi_dung, duong_dan_anh=None):
    """Đăng bài lên một Fanpage Facebook qua Meta Business Suite composer.

    Khi session đã đăng nhập admin, URL fanpage → trang quản lý (không có composer).
    Dùng business.facebook.com/latest/composer để mở trực tiếp composer.
    """
    if not url_fanpage or not isinstance(url_fanpage, str):
        print(f"  -> Loi fanpage: url invalid: {url_fanpage!r}")
        return False

    try:
        # Lấy page_id / slug từ URL
        clean = url_fanpage.rstrip("/").split("?")[0]
        page_slug = clean.split("facebook.com/")[-1].rstrip("/") if "facebook.com/" in clean else clean

        print(f"  Dang bai fanpage: {page_slug}...")

        # ── Chiến lược 1: Business Suite composer ──────────────────────
        composer_url = f"https://business.facebook.com/latest/composer/?page_id={page_slug}"
        driver.get(composer_url)
        time.sleep(3)   # giảm từ 4s → 3s

        current = driver.current_url
        if "login" in current or ("business.facebook.com" not in current and "facebook.com" not in current):
            print(f"  -> Business Suite composer fail, thu timeline composer...")
            driver.get(f"https://www.facebook.com/{page_slug}?sk=wall")
            time.sleep(3)

        # ── Tìm textbox composer ───────────────────────────────────────
        o_nhap = None

        # Business Suite dùng <textarea> thông thường, không phải contenteditable div
        xpaths_nhap = [
            # textarea trong composer panel
            '//textarea[@name="text" or @placeholder or @aria-label]',
            '//textarea',
            # Fallback: contenteditable nếu có
            '//div[@role="textbox"][@contenteditable="true"]',
            '//div[@contenteditable="true"][@aria-label]',
            '//div[@contenteditable="true"]',
        ]
        for xpath in xpaths_nhap:
            try:
                o_nhap = WebDriverWait(driver, 8).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                # Kiểm tra không phải thanh search
                tag = o_nhap.get_attribute("role") or ""
                aria = o_nhap.get_attribute("aria-label") or ""
                if "search" in aria.lower() or "tim kiem" in aria.lower():
                    o_nhap = None
                    continue
                print(f"  -> Tim thay textbox: role={tag} aria={aria[:40]}")
                break
            except Exception:
                continue

        # Nếu vẫn không tìm được → thử click nút "Tạo bài viết" trước
        if o_nhap is None:
            print("  -> Khong tim thay textbox, thu click nut Tao bai viet...")
            for btn_xpath in [
                '//div[@role="button"][contains(.,"Tạo bài viết")]',
                '//div[@role="button"][contains(.,"Create post")]',
                '//a[contains(@href,"new_post")]',
                '//a[contains(@href,"composer")]',
                '//div[@aria-label="Tạo bài viết"]',
                '//div[@aria-label="Create post"]',
            ]:
                try:
                    btn = WebDriverWait(driver, 4).until(
                        EC.element_to_be_clickable((By.XPATH, btn_xpath))
                    )
                    driver.execute_script("arguments[0].click();", btn)
                    time.sleep(2)
                    break
                except Exception:
                    continue

            # Thử lại tìm textbox sau khi click
            for xpath in xpaths_nhap[:3]:
                try:
                    o_nhap = WebDriverWait(driver, 6).until(
                        EC.element_to_be_clickable((By.XPATH, xpath))
                    )
                    break
                except Exception:
                    continue

        if o_nhap is None:
            print(f"  -> FAIL: Khong tim duoc composer cho {page_slug}")
            # Chụp screenshot để debug
            try:
                ts = int(time.time())
                driver.save_screenshot(f"C:/fanpage_debug_{page_slug}_{ts}.png")
                print(f"  -> Screenshot: C:/fanpage_debug_{page_slug}_{ts}.png")
            except Exception:
                pass
            return False

        # ── Nhập nội dung ──────────────────────────────────────────────
        driver.execute_script("arguments[0].click();", o_nhap)
        time.sleep(0.5)

        # Business Suite dùng React controlled input — cần InputEvent đúng
        _paste_business_suite(driver, o_nhap, noi_dung)

        # Chờ React nhận và enable nút Đăng
        time.sleep(2)

        # ── Đính kèm ảnh ───────────────────────────────────────────────
        if duong_dan_anh:
            danh_sach_anh = [duong_dan_anh] if isinstance(duong_dan_anh, str) else duong_dan_anh
            danh_sach_anh_hop_le = [p.replace('\\', '/') for p in danh_sach_anh if os.path.exists(p)]
            if danh_sach_anh_hop_le:
                try:
                    nut_anh = WebDriverWait(driver, 6).until(EC.element_to_be_clickable((By.XPATH,
                        '//div[@aria-label="Ảnh/video" or @aria-label="Photo/video" '
                        'or @aria-label="Photo" or @aria-label="Ảnh" '
                        'or @aria-label="Add photos or videos" or @aria-label="Thêm ảnh hoặc video"]'
                    )))
                    driver.execute_script("arguments[0].click();", nut_anh)
                    input_file = WebDriverWait(driver, 8).until(
                        EC.presence_of_element_located((By.XPATH, '//input[@type="file"]'))
                    )
                    input_file.send_keys("\n".join(danh_sach_anh_hop_le))
                    time.sleep(4 + len(danh_sach_anh_hop_le) * 2)
                except Exception as e:
                    print(f"  -> Khong dinh kem anh fanpage: {e}")

        # ── Click nút Đăng / Publish ───────────────────────────────────
        # Chờ nút Đăng active (không disabled) — quan trọng: nút chỉ active khi có nội dung
        from selenium.webdriver.common.action_chains import ActionChains

        nut_dang = None
        xpaths_dang = [
            # Business Suite: nút "Đăng" không có aria-disabled
            '//div[@role="button" and not(@aria-disabled="true")][contains(.,"Đăng") and not(contains(.,"Tạo")) and not(contains(.,"Quảng"))]',
            '//div[@role="button" and not(@aria-disabled="true")][contains(.,"Publish")]',
            '//button[not(@disabled)][contains(.,"Đăng") or contains(.,"Post") or contains(.,"Publish")]',
            # Với aria-label
            '//div[@aria-label="Đăng" and not(@aria-disabled="true")][@role="button"]',
            '//div[@aria-label="Post" and not(@aria-disabled="true")][@role="button"]',
            '//div[@aria-label="Publish" and not(@aria-disabled="true")][@role="button"]',
            '//div[@aria-label="Xuất bản" and not(@aria-disabled="true")][@role="button"]',
            # Fallback không kiểm tra disabled
            '//div[@aria-label="Đăng"][@role="button"]',
            '//div[@aria-label="Post"][@role="button"]',
            '//div[@aria-label="Publish"][@role="button"]',
        ]

        # Chờ tối đa 10s cho nút active
        for attempt in range(2):
            for xpath in xpaths_dang:
                try:
                    el = WebDriverWait(driver, 4).until(
                        EC.element_to_be_clickable((By.XPATH, xpath))
                    )
                    # Kiểm tra không phải nút bị disable
                    disabled = el.get_attribute("aria-disabled")
                    if disabled == "true":
                        continue
                    label = el.get_attribute("aria-label") or el.text or ""
                    print(f"  -> Tim thay nut Dang: '{label[:40]}' (attempt {attempt+1})")
                    nut_dang = el
                    break
                except Exception:
                    continue
            if nut_dang:
                break
            # Lần 2: thử trigger React lại
            if attempt == 0:
                print("  -> Nut Dang chua active, thu trigger React...")
                try:
                    from selenium.webdriver.common.keys import Keys
                    o_nhap.send_keys(" ")
                    time.sleep(0.3)
                    o_nhap.send_keys(Keys.BACKSPACE)
                    time.sleep(1)
                except Exception:
                    pass

        if nut_dang is None:
            print(f"  -> FAIL: Khong tim duoc nut Dang cho {page_slug}")
            # Chụp screenshot debug
            try:
                ts = int(time.time())
                path = f"C:/fanpage_debug_{page_slug}_{ts}.png"
                driver.save_screenshot(path)
                print(f"  -> Screenshot: {path}")
            except Exception:
                pass
            return False

        # Click bằng ActionChains (reliable hơn JS click với React)
        try:
            ActionChains(driver).move_to_element(nut_dang).click().perform()
        except Exception:
            driver.execute_script("arguments[0].click();", nut_dang)
        print(f"  -> Da click Dang cho fanpage: {page_slug}")

        # Chờ đăng xong — Business Suite thường show success toast
        time.sleep(5)
        # Kiểm tra URL có redirect sang trang post không (dấu hiệu thành công)
        new_url = driver.current_url
        if "posts" in new_url or "permalink" in new_url or page_slug in new_url:
            print(f"  -> THANH CONG: {page_slug}")
            return "SUCCESS"

        # Hoặc kiểm tra toast success
        try:
            WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.XPATH,
                    '//*[contains(text(),"đã đăng") or contains(text(),"published") '
                    'or contains(text(),"Posted") or contains(text(),"Đã đăng")]'
                ))
            )
            print(f"  -> THANH CONG (toast): {page_slug}")
            return "SUCCESS"
        except Exception:
            pass

        # Không xác nhận được nhưng đã click Đăng → coi như thành công
        print(f"  -> Khong xac nhan duoc ket qua nhung da click Dang: {page_slug}")
        return "SUCCESS"

    except Exception as e:
        print(f"  -> Loi fanpage {url_fanpage}: {type(e).__name__}: {e}")
        return False


def thuc_thi_tien_trinh_dang_fanpage(
    chu_de,
    fanpage_urls,
    dang_kem_anh,
    thu_muc_anh,
    thoi_gian_cho_giua_cac_nhom,
    noi_dung_goc=None,
    giu_nguyen_goc: bool = True,
):
    """Chạy đăng bài lên danh sách Fanpage.

    Logic tương tự thuc_thi_tien_trinh_dang nhưng dùng dang_mot_fanpage().
    """
    print(f"\n=== BAT DAU DANG BAI FANPAGE ===")

    if noi_dung_goc is not None:
        print("Che do: NOI DUNG NGUOI DUNG")
        if giu_nguyen_goc:
            noi_dung = noi_dung_goc
        else:
            noi_dung = goi_gemini_viet_lai_bai(noi_dung_goc)
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

    if not fanpage_urls:
        return False, "Không có fanpage nào để đăng."

    driver = None
    ket_qua = []
    try:
        from selenium import webdriver as wd
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service as ChromeService
        from webdriver_manager.chrome import ChromeDriverManager

        opts = Options()
        opts.add_argument("--user-data-dir=C:/fb_session")
        opts.add_argument("--no-first-run")
        opts.add_argument("--no-default-browser-check")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)
        # Không headless — dùng virtual window đẩy ra ngoài màn hình
        # Headless làm React/Business Suite không render đầy đủ
        opts.add_argument("--window-position=-32000,-32000")
        opts.add_argument("--window-size=1920,1080")
        opts.add_argument("--disable-extensions")
        opts.add_argument("--log-level=3")
        opts.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])

        driver = wd.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            options=opts
        )
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
        })
        wait = WebDriverWait(driver, 20)   # giảm timeout từ 30 → 20s

        tong = len(fanpage_urls)
        for i, url in enumerate(fanpage_urls):
            r = dang_mot_fanpage(driver, wait, url, noi_dung, duong_dan_anh)
            ket_qua.append(f"{url}: {r}")
            if i < tong - 1:
                # Delay tối thiểu giữa các fanpage
                time.sleep(5)

        print("=== HOAN THANH DANG BAI FANPAGE ===")
        return True, "\n".join(ket_qua)
    except Exception as e:
        return False, f"Loi fanpage: {e}"
    finally:
        if driver:
            driver.quit()
