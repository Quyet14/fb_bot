# -*- coding: utf-8 -*-
"""
Chuc nang auto Like + Comment + Share.
"""
import random
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from app.bot.gemini import goi_gemini_viet_comment
from app.bot.browser import dong_chrome, tao_driver, paste_vao_element


def tuong_tac_mot_nhom(driver, wait, url_nhom, gioi_han_like, gioi_han_comment):
    print(f"  Tuong tac trong nhom: {url_nhom}...")
    driver.get(url_nhom)
    time.sleep(5)

    driver.execute_script("window.scrollTo(0, 500);")
    time.sleep(4)

    so_like = 0
    so_comment = 0

    try:
        bai_dang_list = driver.find_elements(By.XPATH, '//div[@role="feed"]//div[@role="article"] | //div[@data-testid="fbfeed_story"]')
        print(f"  Tim thay {len(bai_dang_list)} khoi bai dang")

        for bai in bai_dang_list:
            if so_like >= gioi_han_like and so_comment >= gioi_han_comment:
                break

            try:
                noi_dung_bai = "Bài viết ngẫu nhiên"
                try:
                    text_el = bai.find_element(By.XPATH, './/div[@data-ad-preview="preview"] | .//div[@dir="auto"]')
                    if len(text_el.text) > 15:
                        noi_dung_bai = text_el.text
                except Exception:
                    pass

                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", bai)
                time.sleep(3)

                if so_like < gioi_han_like:
                    time.sleep(random.randint(5, 15))
                    try:
                        nut_like = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@aria-label="Thích" or @aria-label="Like"][@role="button"]')))
                        driver.execute_script("arguments[0].click();", nut_like)
                        so_like += 1
                        time.sleep(2)
                    except Exception:
                        pass

                if so_comment < gioi_han_comment:
                    time.sleep(random.randint(10, 20))
                    try:
                        comment_text = goi_gemini_viet_comment(noi_dung_bai)
                        o_nhap = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@contenteditable="true"][@role="textbox"]')))
                        paste_vao_element(driver, o_nhap, comment_text)
                        time.sleep(1.5)
                        o_nhap.send_keys(Keys.RETURN)
                        time.sleep(2)
                        so_comment += 1
                    except Exception:
                        pass

                try:
                    time.sleep(random.randint(5, 10))
                    nut_share = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[contains(@aria-label, "Chia sẻ") or contains(@aria-label, "Share")][@role="button"]')))
                    driver.execute_script("arguments[0].click();", nut_share)
                    time.sleep(3)

                    try:
                        nut_share_ngay = driver.find_element(By.XPATH, '//span[contains(text(),"Chia sẻ ngay") or contains(text(),"Share now") or contains(text(),"Chia sẻ công khai ngay")]')
                        driver.execute_script("arguments[0].click();", nut_share_ngay)
                    except Exception:
                        nut_len_tin = wait.until(EC.element_to_be_clickable((By.XPATH, '//span[contains(text(),"Chia sẻ lên bảng tin") or contains(text(),"Share to Feed") or contains(text(),"Viết bài")]')))
                        driver.execute_script("arguments[0].click();", nut_len_tin)
                        time.sleep(3)
                        nut_dang_share = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@role="dialog"]//div[@aria-label="Đăng" or @aria-label="Post"][@role="button"]')))
                        driver.execute_script("arguments[0].click();", nut_dang_share)
                    time.sleep(3)
                except Exception:
                    pass

            except Exception:
                continue

    except Exception as e:
        print(f"  Loi tuong tac: {e}")

    return so_like, so_comment


def thuc_thi_tien_trinh_tuong_tac(nhom_urls, gioi_han_like, gioi_han_comment):
    """Tra ve: (thanh_cong: bool, chi_tiet: str)"""
    print(f"\n=== BAT DAU TIEN TRINH TUONG TAC ===")
    driver = None
    try:
        dong_chrome()
        driver = tao_driver()
        wait = WebDriverWait(driver, 30)
        driver.get("https://www.facebook.com")
        time.sleep(5)

        chi_tiet = []
        for url in nhom_urls:
            so_like, so_comment = tuong_tac_mot_nhom(driver, wait, url, gioi_han_like, gioi_han_comment)
            chi_tiet.append(f"{url}: {so_like} like, {so_comment} comment")
            time.sleep(10)

        print("=== HOAN THANH PHIEN TUONG TAC ===")
        return True, "\n".join(chi_tiet)
    except Exception as e:
        return False, f"Loi tuong tac: {e}"
    finally:
        if driver:
            driver.quit()