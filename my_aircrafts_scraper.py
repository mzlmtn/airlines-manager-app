import os
import time
import random
import re
import pandas as pd
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


def human_type(element, text):
    """Her karakteri rastgele gecikmeyle yazar."""
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.05, 0.15))


def get_info_by_label(container, label_text):
    """
    Verilen element içinde belirtilen metni (label_text) arar.
    O metnin bulunduğu tag'in içindeki veya bir üst kapsayıcısındaki ilk <b> tag'inin metnini döndürür.
    """
    if not container:
        return None

    text_node = container.find(string=re.compile(label_text, re.IGNORECASE))

    if text_node:
        parent = text_node.parent
        b_tag = parent.find('b')
        if b_tag:
            return b_tag.get_text(strip=True)

        grandparent = parent.parent
        if grandparent:
            b_tag = grandparent.find('b')
            if b_tag:
                return b_tag.get_text(strip=True)

    return None


def get_metadata(driver, base_url):
    """
    Scrape sonrası /home sayfasına giderek metadata çeker:
    - Oyun tarihi (#header_dateTime): "Mon, 10/30/2062, 14:47:31" → "14_30_10_2062"
    - Gerçek tarih (Türkiye saati): "47_14_23_05_2026"
    - Para miktarı (#ressource3)
    - Structural profit D-1 (dashboard)
    """
    driver.get(f"{base_url}/home")
    time.sleep(random.uniform(2, 3))

    home_soup = BeautifulSoup(driver.page_source, 'html.parser')

    # 1. Oyun tarihi
    game_date_str = "00_00_00_0000"
    header_date_el = home_soup.find(id='header_dateTime')
    if header_date_el:
        date_text = header_date_el.get_text(strip=True)
        date_match = re.search(r'(\d+)/(\d+)/(\d+),\s*(\d+):(\d+):(\d+)', date_text)
        if date_match:
            month = date_match.group(1).zfill(2)
            day = date_match.group(2).zfill(2)
            year = date_match.group(3)
            hour = date_match.group(4).zfill(2)
            game_date_str = f"{hour}_{day}_{month}_{year}"

    # 2. Gerçek tarih (Türkiye saati, UTC+3)
    turkey_tz = timezone(timedelta(hours=3))
    now = datetime.now(turkey_tz)
    real_date_str = now.strftime("%M_%H_%d_%m_%Y")

    # 3. Para miktarı
    money_str = "0"
    money_el = home_soup.find(id='ressource3')
    if money_el:
        money_str = money_el.get_text(strip=True)

    # 4. Structural profit D-1
    profit_str = "0"
    profit_el = home_soup.select_one(
        '#dashboardContent > div:nth-child(2) > div.indexModule.companyStats.en > div.content > div:nth-child(6) > span'
    )
    if profit_el:
        profit_str = profit_el.get_text(strip=True)

    return game_date_str, real_date_str, money_str, profit_str


def sanitize_filename(name):
    """Dosya adından Windows'da geçersiz karakterleri temizler."""
    return re.sub(r'[<>:"/\\|?*]', '', name)


def main():
    # --- GITHUB SECRETS KONTROLÜ ---
    USER_EMAIL = os.environ.get("AIRLINES_USER")
    USER_PASS = os.environ.get("AIRLINES_PASS")

    if not USER_EMAIL or not USER_PASS:
        print("HATA: GitHub Secrets (AIRLINES_USER veya AIRLINES_PASS) bulunamadı.")
        return

    # --- AYARLAR ---
    TEST_LIMIT = None
    base_url = "https://tycoon.airlines-manager.com"

    columns = [
        "aircraft_model", "aircraft_name", "range", "use", "cargo",
        "eco_seats", "business_seats", "first_seats", "hub", "wear",
        "age", "capacity_pax", "category", "takeoff_distance",
        "consumption", "speed", "purchase_price", "cumulative_result", "flight_hours"
    ]

    all_aircrafts = []
    scraped_count = 0

    # --- CHROME AYARLARI ---
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=chrome_options)

    # --- OTOMATİK GİRİŞ ---
    print("\n--- OTOMATİK GİRİŞ YAPILIYOR ---")
    driver.get(base_url)
    time.sleep(random.uniform(2, 3))

    username_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "username"))
    )
    human_type(username_field, USER_EMAIL)
    time.sleep(random.uniform(0.5, 1.5))

    password_field = driver.find_element(By.ID, "password")
    human_type(password_field, USER_PASS)
    time.sleep(random.uniform(0.5, 1.0))

    login_btn = driver.find_element(By.ID, "loginSubmit")
    login_btn.click()

    WebDriverWait(driver, 15).until(EC.url_contains("/home"))
    print("Giriş başarılı!")
    time.sleep(random.uniform(2, 3))

    print("Veri kazıma işlemi başlıyor...\n")

    # --- UÇAK SCRAPING ---
    page_number = 1
    stop_scraping = False

    while not stop_scraping:
        list_url = f"{base_url}/aircraft?page={page_number}"
        print(f"--- SAYFA {page_number} taranıyor: {list_url} ---")

        driver.get(list_url)
        time.sleep(random.uniform(1.7, 2.3))

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        aircraft_boxes = soup.find_all('div', class_='aircraftListBox')

        if not aircraft_boxes:
            print(f"Sayfa {page_number}'de uçak bulunamadı. Tarama tamamlandı!")
            break

        print(f"Sayfa {page_number} üzerinde {len(aircraft_boxes)} adet uçak bulundu.")

        page_aircrafts_data = []

        for box in aircraft_boxes:
            if TEST_LIMIT is not None and scraped_count >= TEST_LIMIT:
                stop_scraping = True
                break

            aircraft_data = {col: None for col in columns}

            # 1. aircraft_model
            title_div = box.find('div', class_='title')
            if title_div:
                main_span = title_div.find('span', recursive=False)
                if main_span and main_span.contents:
                    aircraft_data["aircraft_model"] = str(main_span.contents[0]).replace('/', '').strip()

            # 2. aircraft_name
            name_span = box.find('span', class_='editAircraftName')
            if name_span and name_span.find('span'):
                aircraft_data["aircraft_name"] = name_span.find('span').get_text(strip=True)

            # Detay URL
            btn_detail = box.find('a', class_='BtnDetailAvion')
            detail_url = base_url + btn_detail['href'] if btn_detail else None
            aircraft_data["_detail_url"] = detail_url

            content_div = box.find('div', class_='content')

            # 3-11. Liste sayfasından çekilenler
            aircraft_data["range"] = get_info_by_label(content_div, "Range")
            aircraft_data["use"] = get_info_by_label(content_div, "Use")
            aircraft_data["cargo"] = get_info_by_label(content_div, "Cargo")

            seats_raw = get_info_by_label(content_div, "Seats")
            if seats_raw:
                match = re.search(r"\((\d+)/(\d+)/(\d+)\)", seats_raw)
                if match:
                    aircraft_data["eco_seats"] = match.group(1)
                    aircraft_data["business_seats"] = match.group(2)
                    aircraft_data["first_seats"] = match.group(3)

            hub_raw = get_info_by_label(content_div, "Hub")
            if hub_raw:
                aircraft_data["hub"] = hub_raw.replace('/', '').strip()

            aircraft_data["wear"] = get_info_by_label(content_div, "Wear")
            aircraft_data["age"] = get_info_by_label(content_div, "Age")

            page_aircrafts_data.append(aircraft_data)
            scraped_count += 1

        # --- DETAY SAYFALARI ---
        for idx, data in enumerate(page_aircrafts_data):
            detail_link = data.pop("_detail_url", None)

            if not detail_link:
                all_aircrafts.append(data)
                continue

            print(f"  -> Uçak {idx + 1}/{len(page_aircrafts_data)} detayı çekiliyor: {data['aircraft_name']}")
            driver.get(detail_link)
            time.sleep(random.uniform(1.0, 1.3))

            detail_soup = BeautifulSoup(driver.page_source, 'html.parser')

            data["capacity_pax"] = get_info_by_label(detail_soup, "Capacity")

            right_panel = detail_soup.find('div', id='aircraftCharacteristicRight')
            if right_panel:
                cat_img = right_panel.find('img', src=re.compile(r'/images/icons20/cat\d+\.png'))
                if cat_img:
                    match = re.search(r'cat(\d+)\.png', cat_img['src'])
                    if match:
                        data["category"] = match.group(1)

            data["takeoff_distance"] = get_info_by_label(detail_soup, "Takeoff distance")
            data["consumption"] = get_info_by_label(detail_soup, "Consumption")
            data["speed"] = get_info_by_label(detail_soup, "Speed :")
            data["purchase_price"] = get_info_by_label(detail_soup, "Purchase price")
            data["cumulative_result"] = get_info_by_label(detail_soup, "Cumulative result")
            data["flight_hours"] = get_info_by_label(detail_soup, "Flight hours")

            all_aircrafts.append(data)

        if not stop_scraping:
            page_number += 1

    # --- SCRAPE SONRASI: METADATA ÇEK VE DOSYA İSİMLENDİR ---
    print("\n--- Metadata çekiliyor (oyun tarihi, para, structural profit) ---")
    game_date, real_date, money, profit = get_metadata(driver, base_url)
    print(f"  Oyun tarihi: {game_date}")
    print(f"  Gerçek tarih: {real_date}")
    print(f"  Para: {money}")
    print(f"  Structural profit D-1: {profit}")

    output_filename = sanitize_filename(f"aircrafts {game_date} {real_date} {money} {profit}.xlsx")
    print(f"  Dosya adı: {output_filename}")

    driver.quit()
    print("\nExcel dosyası oluşturuluyor...")

    df = pd.DataFrame(all_aircrafts, columns=columns)

    try:
        df.to_excel(output_filename, index=False)
        print(f"BAŞARILI! Toplam {len(df)} uçak kaydedildi → {output_filename}")
    except Exception as e:
        print(f"Dosya kaydedilirken hata oluştu: {e}")


if __name__ == "__main__":
    main()
