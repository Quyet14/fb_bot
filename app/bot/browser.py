# -*- coding: utf-8 -*-
"""
Cac ham tien ich lien quan den trinh duyet: tao driver, dong chrome,
paste noi dung, lay anh ngau nhien.
"""
import os
import random
import subprocess
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager


def dong_chrome():
    try:
        subprocess.run("taskkill /f /im chrome.exe", shell=True, capture_output=True)
        time.sleep(2)
    except Exception:
        pass


def tao_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--user-data-dir=C:/fb_session")
    options.add_argument("--start-maximized")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    return webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()),
        options=options
    )


def paste_vao_element(driver, element, noi_dung, debug_prefix: str = ""):
    """Dán text vào contenteditable của Facebook (React).

    Thứ tự thử:
    1. execCommand('insertText') — trigger React input event trực tiếp
    2. pyperclip clipboard paste — fallback nếu execCommand bị block
    3. send_keys — fallback cuối
    """
    if element is None:
        raise ValueError("paste_vao_element: element is None")

    text = "" if noi_dung is None else str(noi_dung)

    # Attempt 1: execCommand insertText (React-compatible)
    try:
        driver.execute_script(
            """
            const el = arguments[0];
            const txt = arguments[1];
            el.focus();
            // Xóa nội dung cũ
            document.execCommand('selectAll', false, null);
            document.execCommand('delete', false, null);
            // Insert text — triggers React synthetic input event
            document.execCommand('insertText', false, txt);
            // Dispatch thêm input event để đảm bảo React nhận
            el.dispatchEvent(new Event('input', { bubbles: true }));
            """,
            element, text,
        )
        time.sleep(0.6)
        actual = driver.execute_script("return arguments[0].textContent || '';", element)
        if text[:15] in actual:
            print("  -> paste: execCommand OK")
            return
    except Exception as e1:
        print(f"  -> paste execCommand failed: {e1}")

    # Attempt 2: clipboard paste qua pyperclip
    try:
        import pyperclip
        from selenium.webdriver.common.keys import Keys
        pyperclip.copy(text)
        element.click()
        time.sleep(0.3)
        element.send_keys(Keys.CONTROL + "a")
        time.sleep(0.1)
        element.send_keys(Keys.CONTROL + "v")
        time.sleep(0.6)
        actual = driver.execute_script("return arguments[0].textContent || '';", element)
        if text[:15] in actual:
            print("  -> paste: clipboard OK")
            return
    except Exception as e2:
        print(f"  -> paste clipboard failed: {e2}")

    # Attempt 3: send_keys trực tiếp
    try:
        from selenium.webdriver.common.keys import Keys
        element.click()
        time.sleep(0.3)
        element.send_keys(Keys.CONTROL + "a")
        element.send_keys(Keys.DELETE)
        time.sleep(0.2)
        element.send_keys(text)
        time.sleep(0.6)
        print("  -> paste: send_keys OK")
        return
    except Exception as e3:
        try:
            if driver:
                ts = int(time.time())
                driver.save_screenshot(f"debug_{debug_prefix}_{ts}.png".replace("\\", "_"))
        except Exception:
            pass
        raise e3



def lay_anh_ngau_nhien(thu_muc_anh: str):
    try:
        if not os.path.exists(thu_muc_anh):
            os.makedirs(thu_muc_anh)
            return None

        danh_sach_anh = [
            f for f in os.listdir(thu_muc_anh)
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))
        ]

        if not danh_sach_anh:
            return None

        anh_chon = random.choice(danh_sach_anh)
        return os.path.join(thu_muc_anh, anh_chon)
    except Exception as e:
        print(f"  Loi lay anh: {e}")
        return None