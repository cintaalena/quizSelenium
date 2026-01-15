import os
import time
import uuid
import pytest

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait


# =========================
# KONFIGURASI
# =========================
BASE_URL = os.getenv("BASE_URL", "http://localhost/quiz-pengupil-main/quiz-pengupil-main")
REGISTER_URL = f"{BASE_URL}/register.php"
TIMEOUT = int(os.getenv("SELENIUM_TIMEOUT", "10"))

REGISTER_SUCCESS_TEXT = os.getenv("REGISTER_SUCCESS_TEXT", "berhasil")
REGISTER_FAIL_TEXT = os.getenv("REGISTER_FAIL_TEXT", "gagal")


# =========================
# DRIVER (Incognito)
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


def assert_register_success(driver):
    current = driver.current_url.lower()
    if "register.php" not in current:
        return
    assert page_has_text(driver, REGISTER_SUCCESS_TEXT.lower()), (
        f"Register dianggap gagal. URL masih register.php dan tidak menemukan text '{REGISTER_SUCCESS_TEXT}'."
    )


def assert_register_fail(driver):
    current = driver.current_url.lower()
    if "register.php" in current:
        return
    assert page_has_text(driver, REGISTER_FAIL_TEXT.lower()), (
        f"Register seharusnya gagal. Tapi URL berubah dan tidak menemukan text '{REGISTER_FAIL_TEXT}'."
    )


def find_first_existing(driver, candidates):
    for by, loc in candidates:
        elems = driver.find_elements(by, loc)
        if elems:
            return elems[0]
    raise Exception(f"Elemen tidak ditemukan. Candidates: {candidates}")


def fill_register_form(driver, nama, email, username, password, repassword):
    """
    Mengisi form register sesuai field pada UI:
    Nama, Alamat Email, Username, Password, Re-Password
    """
    nama_el = find_first_existing(driver, [
        (By.NAME, "nama"),
        (By.ID, "nama"),
        (By.NAME, "name"),
        (By.ID, "name"),
        # fallback: input text pertama
        (By.XPATH, "(//input[@type='text'])[1]"),
    ])
    email_el = find_first_existing(driver, [
        (By.NAME, "email"),
        (By.ID, "email"),
        (By.XPATH, "//input[@type='email']"),
        # fallback: input text kedua jika email dibuat text biasa
        (By.XPATH, "(//input[@type='text'])[2]"),
    ])
    username_el = find_first_existing(driver, [
        (By.NAME, "username"),
        (By.ID, "username"),
        (By.XPATH, "(//input[@type='text'])[3]"),
    ])
    password_el = find_first_existing(driver, [
        (By.NAME, "password"),
        (By.ID, "password"),
        (By.XPATH, "(//input[@type='password'])[1]"),
    ])
    repassword_el = find_first_existing(driver, [
        (By.NAME, "repassword"),
        (By.ID, "repassword"),
        (By.NAME, "re_password"),
        (By.ID, "re_password"),
        (By.XPATH, "(//input[@type='password'])[2]"),
    ])

    # isi
    nama_el.clear()
    nama_el.send_keys(nama)

    email_el.clear()
    email_el.send_keys(email)

    username_el.clear()
    username_el.send_keys(username)

    password_el.clear()
    password_el.send_keys(password)

    repassword_el.clear()
    repassword_el.send_keys(repassword)


def submit_register(driver):
    btn = find_first_existing(driver, [
        (By.CSS_SELECTOR, "button[type='submit']"),
        (By.CSS_SELECTOR, "input[type='submit']"),
        (By.XPATH, "//button[contains(., 'Register')]"),
        (By.XPATH, "//button[contains(., 'Daftar')]"),
    ])
    btn.click()


# =========================
# TESTCASE REGISTER (update: nama/email ikut diuji)
# =========================
def test_TC_R_01_register_valid(driver):
    """
    TC-R-01: registrasi valid (semua field terisi)
    """
    driver.get(REGISTER_URL)
    wait_ready(driver)

    u = f"user_{uuid.uuid4().hex[:8]}"
    fill_register_form(
        driver,
        nama="User Otomatis",
        email=f"{u}@mail.com",
        username=u,
        password="pass123",
        repassword="pass123",
    )
    submit_register(driver)
    time.sleep(1)

    assert_register_success(driver)


def test_TC_R_02_register_nama_empty(driver):
    """
    TC-R-02: nama kosong (harus ditolak)
    """
    driver.get(REGISTER_URL)
    wait_ready(driver)

    u = f"user_{uuid.uuid4().hex[:8]}"
    fill_register_form(
        driver,
        nama="",
        email=f"{u}@mail.com",
        username=u,
        password="pass123",
        repassword="pass123",
    )
    submit_register(driver)
    time.sleep(1)

    assert_register_fail(driver)


def test_TC_R_03_register_email_empty(driver):
    """
    TC-R-03: email kosong (harus ditolak)
    """
    driver.get(REGISTER_URL)
    wait_ready(driver)

    u = f"user_{uuid.uuid4().hex[:8]}"
    fill_register_form(
        driver,
        nama="User Otomatis",
        email="",
        username=u,
        password="pass123",
        repassword="pass123",
    )
    submit_register(driver)
    time.sleep(1)

    assert_register_fail(driver)


def test_TC_R_04_register_username_empty(driver):
    """
    TC-R-04: username kosong (harus ditolak)
    """
    driver.get(REGISTER_URL)
    wait_ready(driver)

    fill_register_form(
        driver,
        nama="User Otomatis",
        email="user@mail.com",
        username="",
        password="pass123",
        repassword="pass123",
    )
    submit_register(driver)
    time.sleep(1)

    assert_register_fail(driver)


def test_TC_R_05_register_password_empty(driver):
    """
    TC-R-05: password kosong (harus ditolak)
    """
    driver.get(REGISTER_URL)
    wait_ready(driver)

    u = f"user_{uuid.uuid4().hex[:8]}"
    fill_register_form(
        driver,
        nama="User Otomatis",
        email=f"{u}@mail.com",
        username=u,
        password="",
        repassword="",
    )
    submit_register(driver)
    time.sleep(1)

    assert_register_fail(driver)


def test_TC_R_06_register_sql_injection_username(driver):
    """
    TC-R-06: SQL Injection pada username
    Expected Result:
    Sistem RENTAN, data berhasil tersimpan ke database
    """
    driver.get(REGISTER_URL)
    wait_ready(driver)

    fill_register_form(
        driver,
        nama="User Otomatis",
        email="injection@mail.com",
        username="' OR '1'='1",
        password="pass123",
        repassword="pass123",
    )
    submit_register(driver)
    time.sleep(1)

    # Expected: berhasil (menandakan kerentanan)
    assert_register_success(driver)

def test_TC_R_07_register_repassword_empty(driver):
    """
    TC-R-07: Re-Password kosong (harus ditolak)
    """
    driver.get(REGISTER_URL)
    wait_ready(driver)

    u = f"user_{uuid.uuid4().hex[:8]}"
    fill_register_form(
        driver,
        nama="User Otomatis",
        email=f"{u}@mail.com",
        username=u,
        password="pass123",
        repassword="",
    )
    submit_register(driver)
    time.sleep(1)

    assert_register_fail(driver)


def test_TC_R_08_register_password_mismatch(driver):
    """
    TC-R-08: Password tidak sama dengan Re-Password (harus ditolak)
    """
    driver.get(REGISTER_URL)
    wait_ready(driver)

    u = f"user_{uuid.uuid4().hex[:8]}"
    fill_register_form(
        driver,
        nama="User Otomatis",
        email=f"{u}@mail.com",
        username=u,
        password="pass123",
        repassword="pass124",
    )
    submit_register(driver)
    time.sleep(1)

    assert_register_fail(driver)


def test_TC_R_09_register_email_invalid_no_at(driver):
    """
    TC-R-09: Format email tidak valid (tanpa '@') (harus ditolak)
    """
    driver.get(REGISTER_URL)
    wait_ready(driver)

    u = f"user_{uuid.uuid4().hex[:8]}"
    fill_register_form(
        driver,
        nama="User Otomatis",
        email="usergmail.com",
        username=u,
        password="pass123",
        repassword="pass123",
    )
    submit_register(driver)
    time.sleep(1)

    assert_register_fail(driver)


def test_TC_R_10_register_email_invalid_no_domain(driver):
    """
    TC-R-10: Format email tidak valid (tanpa domain) (harus ditolak)
    """
    driver.get(REGISTER_URL)
    wait_ready(driver)

    u = f"user_{uuid.uuid4().hex[:8]}"
    fill_register_form(
        driver,
        nama="User Otomatis",
        email="user@",
        username=u,
        password="pass123",
        repassword="pass123",
    )
    submit_register(driver)
    time.sleep(1)

    assert_register_fail(driver)


def test_TC_R_11_register_email_duplicate(driver):
    """
    TC-R-11: Email sudah terdaftar (harus ditolak / gagal)
    """
    driver.get(REGISTER_URL)
    wait_ready(driver)

    # Pakai email yang sama untuk 2 registrasi
    shared_email = f"dup_{uuid.uuid4().hex[:6]}@mail.com"

    # Registrasi pertama (harus berhasil)
    u1 = f"user_{uuid.uuid4().hex[:8]}"
    fill_register_form(driver, "User Otomatis", shared_email, u1, "pass123", "pass123")
    submit_register(driver)
    time.sleep(1)
    assert_register_success(driver)

    # Registrasi kedua dengan email sama (harus gagal)
    driver.get(REGISTER_URL)
    wait_ready(driver)
    u2 = f"user_{uuid.uuid4().hex[:8]}"
    fill_register_form(driver, "User Otomatis", shared_email, u2, "pass123", "pass123")
    submit_register(driver)
    time.sleep(1)
    assert_register_fail(driver)


def test_TC_R_12_register_username_duplicate(driver):
    """
    TC-R-12: Username sudah terdaftar (harus ditolak / gagal)
    """
    driver.get(REGISTER_URL)
    wait_ready(driver)

    # Pakai username yang sama untuk 2 registrasi
    shared_username = f"userdup_{uuid.uuid4().hex[:6]}"

    # Registrasi pertama (harus berhasil)
    fill_register_form(
        driver,
        nama="User Otomatis",
        email=f"{shared_username}@mail.com",
        username=shared_username,
        password="pass123",
        repassword="pass123",
    )
    submit_register(driver)
    time.sleep(1)
    assert_register_success(driver)

    # Registrasi kedua dengan username sama (harus gagal)
    driver.get(REGISTER_URL)
    wait_ready(driver)
    fill_register_form(
        driver,
        nama="User Otomatis",
        email=f"{shared_username}_{uuid.uuid4().hex[:4]}@mail.com",
        username=shared_username,
        password="pass123",
        repassword="pass123",
    )
    submit_register(driver)
    time.sleep(1)
    assert_register_fail(driver)


def test_TC_R_13_register_username_contains_space(driver):
    """
    TC-R-13: Username mengandung spasi (harus ditolak / atau di-trim)
    """
    driver.get(REGISTER_URL)
    wait_ready(driver)

    u = f"user {uuid.uuid4().hex[:6]}"  # ada spasi
    fill_register_form(
        driver,
        nama="User Otomatis",
        email=f"space_{uuid.uuid4().hex[:6]}@mail.com",
        username=u,
        password="pass123",
        repassword="pass123",
    )
    submit_register(driver)
    time.sleep(1)

    # Expected ideal: ditolak. Jika ternyata diterima, catat sebagai temuan validasi lemah.
    assert_register_fail(driver)


def test_TC_R_14_register_username_special_chars(driver):
    """
    TC-R-14: Username karakter spesial (harus ditolak / disanitasi)
    """
    driver.get(REGISTER_URL)
    wait_ready(driver)

    u = f"user!@#{uuid.uuid4().hex[:4]}"
    fill_register_form(
        driver,
        nama="User Otomatis",
        email=f"spec_{uuid.uuid4().hex[:6]}@mail.com",
        username=u,
        password="pass123",
        repassword="pass123",
    )
    submit_register(driver)
    time.sleep(1)

    assert_register_fail(driver)


def test_TC_R_15_register_name_too_long(driver):
    """
    TC-R-15: Nama terlalu panjang (harus ditolak / error ditangani)
    """
    driver.get(REGISTER_URL)
    wait_ready(driver)

    long_name = "A" * 300
    u = f"user_{uuid.uuid4().hex[:8]}"
    fill_register_form(
        driver,
        nama=long_name,
        email=f"{u}@mail.com",
        username=u,
        password="pass123",
        repassword="pass123",
    )
    submit_register(driver)
    time.sleep(1)

    # Expected ideal: ditolak. Kalau diterima, catat sebagai temuan (validasi panjang input).
    assert_register_fail(driver)


def test_TC_R_16_register_username_too_long(driver):
    """
    TC-R-16: Username terlalu panjang (harus ditolak / error DB ditangani)
    """
    driver.get(REGISTER_URL)
    wait_ready(driver)

    long_username = "u" * 100
    fill_register_form(
        driver,
        nama="User Otomatis",
        email=f"longu_{uuid.uuid4().hex[:6]}@mail.com",
        username=long_username,
        password="pass123",
        repassword="pass123",
    )
    submit_register(driver)
    time.sleep(1)

    assert_register_fail(driver)


def test_TC_R_17_register_password_too_short(driver):
    """
    TC-R-17: Password terlalu pendek (idealnya ditolak)
    """
    driver.get(REGISTER_URL)
    wait_ready(driver)

    u = f"user_{uuid.uuid4().hex[:8]}"
    fill_register_form(
        driver,
        nama="User Otomatis",
        email=f"{u}@mail.com",
        username=u,
        password="1",
        repassword="1",
    )
    submit_register(driver)
    time.sleep(1)

    # Expected ideal: ditolak. Jika diterima, catat sebagai kelemahan kebijakan password.
    assert_register_fail(driver)


def test_TC_R_18_register_password_with_spaces(driver):
    """
    TC-R-18: Password mengandung spasi di awal/akhir (idealnya ditolak atau diperlakukan konsisten)
    """
    driver.get(REGISTER_URL)
    wait_ready(driver)

    u = f"user_{uuid.uuid4().hex[:8]}"
    fill_register_form(
        driver,
        nama="User Otomatis",
        email=f"{u}@mail.com",
        username=u,
        password=" pass123 ",
        repassword=" pass123 ",
    )
    submit_register(driver)
    time.sleep(1)

    # Expected ideal: ditolak. Jika diterima, catat hasil aktual.
    assert_register_fail(driver)


def test_TC_R_19_register_xss_in_name(driver):
    """
    TC-R-19: XSS pada nama (harus ditolak / disanitasi)
    """
    driver.get(REGISTER_URL)
    wait_ready(driver)

    u = f"user_{uuid.uuid4().hex[:8]}"
    fill_register_form(
        driver,
        nama="<script>alert(1)</script>",
        email=f"{u}@mail.com",
        username=u,
        password="pass123",
        repassword="pass123",
    )
    submit_register(driver)
    time.sleep(1)

    # Expected ideal: ditolak. Jika diterima, catat sebagai temuan XSS/validasi input lemah.
    assert_register_fail(driver)


def test_TC_R_20_register_sql_injection_email(driver):
    """
    TC-R-20: SQL Injection pada email (harus ditolak; jika diterima = temuan)
    """
    driver.get(REGISTER_URL)
    wait_ready(driver)

    u = f"user_{uuid.uuid4().hex[:8]}"
    fill_register_form(
        driver,
        nama="User Otomatis",
        email="test@mail.com' OR '1'='1",
        username=u,
        password="pass123",
        repassword="pass123",
    )
    submit_register(driver)
    time.sleep(1)

    assert_register_fail(driver)


