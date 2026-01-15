import os
import time
import pytest

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait


# =========================
# KONFIGURASI
# =========================
BASE_URL = os.getenv(
    "BASE_URL",
    "http://localhost/quiz-pengupil-main/quiz-pengupil-main"
)
LOGIN_URL = f"{BASE_URL}/login.php"
TIMEOUT = int(os.getenv("SELENIUM_TIMEOUT", "10"))

# Akun existing (SESUIAI PERMINTAAN)
VALID_USERNAME = "user01"
VALID_PASSWORD = "pass123"

LOGIN_SUCCESS_TEXT = os.getenv("LOGIN_SUCCESS_TEXT", "logout")
LOGIN_FAIL_TEXT = os.getenv("LOGIN_FAIL_TEXT", "gagal")


# =========================
# DRIVER (INCOGNITO)
# =========================
def create_chrome_driver(headless: bool = False):
    options = ChromeOptions()
    options.add_argument("--incognito")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    if headless:
        options.add_argument("--headless=new")

    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1280, 720)
    return driver


@pytest.fixture
def driver():
    headless = os.getenv("HEADLESS", "0") == "1"
    drv = create_chrome_driver(headless=headless)
    yield drv
    drv.quit()


# =========================
# HELPER
# =========================
def wait_ready(driver):
    WebDriverWait(driver, TIMEOUT).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )


def page_has_text(driver, text_lower: str) -> bool:
    return text_lower in driver.page_source.lower()


def assert_login_success(driver):
    current = driver.current_url.lower()
    if "login.php" not in current:
        return
    assert page_has_text(driver, LOGIN_SUCCESS_TEXT.lower()), (
        f"Login gagal: tidak menemukan teks '{LOGIN_SUCCESS_TEXT}'."
    )


def assert_login_fail(driver):
    current = driver.current_url.lower()
    if "login.php" in current:
        return
    assert page_has_text(driver, LOGIN_FAIL_TEXT.lower()), (
        f"Login seharusnya gagal, tapi URL berubah dan teks gagal tidak ditemukan."
    )


def find_first_existing(driver, candidates):
    for by, loc in candidates:
        elems = driver.find_elements(by, loc)
        if elems:
            return elems[0]
    raise Exception(f"Elemen tidak ditemukan. Candidates: {candidates}")


def fill_login_form(driver, username, password):
    inputs = driver.find_elements(By.CSS_SELECTOR, "form input")

    inputs[0].clear()
    inputs[0].send_keys(username)

    inputs[1].clear()
    inputs[1].send_keys(password)

    driver.find_element(
        By.CSS_SELECTOR,
        "form button, form input[type='submit']"
    ).click()

def submit_login(driver):
    btn = find_first_existing(driver, [
        (By.CSS_SELECTOR, "button[type='submit']"),
        (By.CSS_SELECTOR, "input[type='submit']"),
        (By.XPATH, "//button[contains(., 'Login')]"),
        (By.XPATH, "//button[contains(., 'Masuk')]"),
    ])
    btn.click()

# =========================
# TESTCASE LOGIN
# =========================
def test_TC_L_01_login_valid(driver):
    """
    TC-L-01: Login dengan username & password valid
    """
    driver.get(LOGIN_URL)
    wait_ready(driver)

    fill_login_form(driver, VALID_USERNAME, VALID_PASSWORD)
    submit_login(driver)
    time.sleep(1)

    assert_login_success(driver)


def test_TC_L_02_login_wrong_password(driver):
    """
    TC-L-02: Password salah
    """
    driver.get(LOGIN_URL)
    wait_ready(driver)

    fill_login_form(driver, VALID_USERNAME, "salah123")
    submit_login(driver)
    time.sleep(1)

    assert_login_fail(driver)


def test_TC_L_03_login_username_empty(driver):
    """
    TC-L-03: Username kosong
    """
    driver.get(LOGIN_URL)
    wait_ready(driver)

    fill_login_form(driver, "", VALID_PASSWORD)
    submit_login(driver)
    time.sleep(1)

    assert_login_fail(driver)


def test_TC_L_04_login_sql_injection(driver):
    """
    TC-L-04: SQL Injection pada login
    Expected Result: SQL Injection ditolak (tidak boleh berhasil login)
    """
    driver.get(LOGIN_URL)
    wait_ready(driver)

    fill_login_form(driver, "' OR '1'='1", "pass123")
    submit_login(driver)
    time.sleep(1)

    # ---- DETEKSI "INJECTION BERHASIL" (harus bikin test FAIL) ----
    current = driver.current_url.lower()
    login_form_still_exists = len(driver.find_elements(By.CSS_SELECTOR, "input[type='password']")) > 0

    # Jika URL keluar dari login.php ATAU form login hilang => berarti login sukses => SECURITY FAIL
    assert ("login.php" in current) and login_form_still_exists, (
        "FAIL: SQL Injection berhasil login (indikator: URL berubah atau form login hilang)."
    )

def test_TC_L_05_login_password_empty(driver):
    """
    TC-L-05: Password kosong
    """
    driver.get(LOGIN_URL)
    wait_ready(driver)

    fill_login_form(driver, VALID_USERNAME, "")
    submit_login(driver)
    time.sleep(1)

    assert_login_fail(driver)


def test_TC_L_06_login_username_and_password_empty(driver):
    """
    TC-L-06: Username dan password kosong
    """
    driver.get(LOGIN_URL)
    wait_ready(driver)

    fill_login_form(driver, "", "")
    submit_login(driver)
    time.sleep(1)

    assert_login_fail(driver)


def test_TC_L_07_login_username_with_spaces(driver):
    """
    TC-L-07: Username mengandung spasi di awal/akhir (leading/trailing)
    """
    driver.get(LOGIN_URL)
    wait_ready(driver)

    fill_login_form(driver, f" {VALID_USERNAME} ", VALID_PASSWORD)
    submit_login(driver)
    time.sleep(1)

    # Idealnya ditolak kalau sistem tidak melakukan trim.
    # Jika ternyata berhasil, catat sebagai perilaku sistem.
    assert_login_fail(driver)


def test_TC_L_08_login_password_with_spaces(driver):
    """
    TC-L-08: Password mengandung spasi di awal/akhir
    """
    driver.get(LOGIN_URL)
    wait_ready(driver)

    fill_login_form(driver, VALID_USERNAME, f" {VALID_PASSWORD} ")
    submit_login(driver)
    time.sleep(1)

    assert_login_fail(driver)


def test_TC_L_09_login_username_case_sensitivity(driver):
    """
    TC-L-09: Uji case sensitivity pada username (User01 vs user01)
    """
    driver.get(LOGIN_URL)
    wait_ready(driver)

    fill_login_form(driver, "User01", VALID_PASSWORD)
    submit_login(driver)
    time.sleep(1)

    # Umumnya username case-sensitive -> ditolak
    assert_login_fail(driver)


def test_TC_L_10_login_password_case_sensitivity(driver):
    """
    TC-L-10: Uji case sensitivity pada password (PASS123 vs pass123)
    """
    driver.get(LOGIN_URL)
    wait_ready(driver)

    fill_login_form(driver, VALID_USERNAME, "PASS123")
    submit_login(driver)
    time.sleep(1)

    assert_login_fail(driver)


def test_TC_L_11_login_username_special_char(driver):
    """
    TC-L-11: Username mengandung karakter spesial
    """
    driver.get(LOGIN_URL)
    wait_ready(driver)

    fill_login_form(driver, f"{VALID_USERNAME}!", VALID_PASSWORD)
    submit_login(driver)
    time.sleep(1)

    assert_login_fail(driver)


def test_TC_L_12_login_password_special_char(driver):
    """
    TC-L-12: Password ditambah karakter spesial
    """
    driver.get(LOGIN_URL)
    wait_ready(driver)

    fill_login_form(driver, VALID_USERNAME, f"{VALID_PASSWORD}!")
    submit_login(driver)
    time.sleep(1)

    assert_login_fail(driver)


def test_TC_L_13_login_sql_injection_password(driver):
    """
    TC-L-13: SQL Injection pada password (harus ditolak)
    """
    driver.get(LOGIN_URL)
    wait_ready(driver)

    fill_login_form(driver, VALID_USERNAME, "' OR '1'='1")
    submit_login(driver)
    time.sleep(1)

    # Ditolak -> tetap di login.php dan form masih ada
    current = driver.current_url.lower()
    login_form_still_exists = len(driver.find_elements(By.CSS_SELECTOR, "input[type='password']")) > 0
    assert ("login.php" in current) and login_form_still_exists, (
        "FAIL: SQL Injection berhasil login lewat password (indikator: URL berubah atau form login hilang)."
    )


def test_TC_L_14_login_sql_injection_both_fields(driver):
    """
    TC-L-14: SQL Injection pada username & password (harus ditolak)
    """
    driver.get(LOGIN_URL)
    wait_ready(driver)

    fill_login_form(driver, "' OR '1'='1", "' OR '1'='1")
    submit_login(driver)
    time.sleep(1)

    current = driver.current_url.lower()
    login_form_still_exists = len(driver.find_elements(By.CSS_SELECTOR, "input[type='password']")) > 0
    assert ("login.php" in current) and login_form_still_exists, (
        "FAIL: SQL Injection berhasil login (kedua field) (indikator: URL berubah atau form login hilang)."
    )


def test_TC_L_15_login_xss_username(driver):
    """
    TC-L-15: XSS pada username (harus ditolak / disanitasi)
    """
    driver.get(LOGIN_URL)
    wait_ready(driver)

    fill_login_form(driver, "<script>alert(1)</script>", VALID_PASSWORD)
    submit_login(driver)
    time.sleep(1)

    assert_login_fail(driver)


def test_TC_L_16_login_xss_password(driver):
    """
    TC-L-16: XSS pada password (harus ditolak / disanitasi)
    """
    driver.get(LOGIN_URL)
    wait_ready(driver)

    fill_login_form(driver, VALID_USERNAME, "<script>alert(1)</script>")
    submit_login(driver)
    time.sleep(1)

    assert_login_fail(driver)


def test_TC_L_17_login_username_very_long(driver):
    """
    TC-L-17: Username sangat panjang (200 char)
    """
    driver.get(LOGIN_URL)
    wait_ready(driver)

    long_user = "u" * 200
    fill_login_form(driver, long_user, VALID_PASSWORD)
    submit_login(driver)
    time.sleep(1)

    assert_login_fail(driver)


def test_TC_L_18_login_password_very_long(driver):
    """
    TC-L-18: Password sangat panjang (500 char)
    """
    driver.get(LOGIN_URL)
    wait_ready(driver)

    long_pass = "p" * 500
    fill_login_form(driver, VALID_USERNAME, long_pass)
    submit_login(driver)
    time.sleep(1)

    assert_login_fail(driver)


def test_TC_L_19_login_non_existing_user(driver):
    """
    TC-L-19: Username tidak terdaftar
    """
    driver.get(LOGIN_URL)
    wait_ready(driver)

    fill_login_form(driver, "user_tidak_ada_123", "pass123")
    submit_login(driver)
    time.sleep(1)

    assert_login_fail(driver)


def test_TC_L_20_login_bruteforce_simple(driver):
    """
    TC-L-20: Brute force sederhana (ulang login salah beberapa kali)
    Expected Result ideal: sistem membatasi percobaan (rate limiting / lockout)
    Catatan: Jika tidak ada pembatasan, test ini bisa tetap PASS namun dicatat sebagai kelemahan keamanan.
    """
    driver.get(LOGIN_URL)
    wait_ready(driver)

    for _ in range(5):
        fill_login_form(driver, VALID_USERNAME, "salah123")
        submit_login(driver)
        time.sleep(0.7)

        # kembali ke login.php jika ada redirect
        if "login.php" not in driver.current_url.lower():
            driver.get(LOGIN_URL)
            wait_ready(driver)

    # Minimal: setelah percobaan salah, tetap tidak boleh login
    assert_login_fail(driver)




