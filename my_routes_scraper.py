import os
import time
import random
import re
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


def extract_table_data(body, data_dict, prefix):
    """Talep/arz/fiyat verilerini tbody'den çıkarır."""
    if not body:
        return
    all_trs = body.find_all('tr', recursive=False)
    if len(all_trs) >= 1:
        tds = all_trs[0].find_all('td')
        if len(tds) >= 5:
            data_dict[f"eco_demand_{prefix}"] = tds[1].get_text(strip=True)
            data_dict[f"business_demand_{prefix}"] = tds[2].get_text(strip=True)
            data_dict[f"first_demand_{prefix}"] = tds[3].get_text(strip=True)
            data_dict[f"cargo_demand_{prefix}"] = tds[4].get_text(strip=True)
    offer_tr = body.find('tr', class_='offer')
    if offer_tr:
        tds = offer_tr.find_all('td')
        if len(tds) >= 5:
            data_dict[f"eco_offer_{prefix}"] = tds[1].get_text(strip=True)
            data_dict[f"business_offer_{prefix}"] = tds[2].get_text(strip=True)
            data_dict[f"first_offer_{prefix}"] = tds[3].get_text(strip=True)
            data_dict[f"cargo_offer_{prefix}"] = tds[4].get_text(strip=True)
    if len(all_trs) >= 3:
        tds = all_trs[2].find_all('td')
        if len(tds) >= 5:
            data_dict[f"eco_price_{prefix}"] = tds[1].get_text(strip=True)
            data_dict[f"business_price_{prefix}"] = tds[2].get_text(strip=True)
            data_dict[f"first_price_{prefix}"] = tds[3].get_text(strip=True)
            data_dict[f"cargo_price_{prefix}"] = tds[4].get_text(strip=True)


def main():
    # --- GITHUB SECRETS KONTROLÜ ---
    USER_EMAIL = os.environ.get("AIRLINES_USER")
    USER_PASS = os.environ.get("AIRLINES_PASS")

    if not USER_EMAIL or not USER_PASS:
        print("HATA: GitHub Secrets (AIRLINES_USER veya AIRLINES_PASS) bulunamadı. İşlem iptal ediliyor.")
        return

    base_url = "https://tycoon.airlines-manager.com"
    output_excel_path = "routes_output.xlsx"

    columns = [
        "departure_airport", "arrival_airport", "distance", "assigned_aircraft_count",
        "taxes", "max_category", "weekly_flight_count", "aircrafts_on_route",
        "eco_demand_today", "business_demand_today", "first_demand_today", "cargo_demand_today",
        "eco_offer_today", "business_offer_today", "first_offer_today", "cargo_offer_today",
        "eco_price_today", "business_price_today", "first_price_today", "cargo_price_today",
        "eco_demand_yesterday", "business_demand_yesterday", "first_demand_yesterday", "cargo_demand_yesterday",
        "eco_offer_yesterday", "business_offer_yesterday", "first_offer_yesterday", "cargo_offer_yesterday",
        "eco_price_yesterday", "business_price_yesterday", "first_price_yesterday", "cargo_price_yesterday"
    ]

    all_routes = []
    processed_urls = set()  # Tüm duplikeleri yakalamak için set

    # --- GITHUB ACTIONS İÇİN CHROME AYARLARI ---
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

    # Giriş sonrası sayfanın yüklenmesini bekle
    WebDriverWait(driver, 15).until(
        EC.url_contains("/home")
    )
    print("Giriş başarılı!")
    time.sleep(random.uniform(2, 3))

    page_number = 1

    while True:
        list_url = f"{base_url}/network/?classFilter=&sort=iata&page={page_number}"
        driver.get(list_url)
        time.sleep(random.uniform(1.5, 2.2))

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # FIX 1: Aramayı #displayRegular ile sınırla (sayfa genelindeki duplike elementleri önler)
        container = soup.find('div', id='displayRegular')
        if not container:
            print(f"Sayfa {page_number}: #displayRegular bulunamadı, durduruluyor.")
            break

        # FIX 2: recursive=False ile sadece doğrudan çocuk div'leri al (iç içe eşleşmeleri önler)
        route_boxes = container.find_all('div', class_='lineListBox', recursive=False)

        if not route_boxes:
            print(f"Sayfa {page_number}: Rota bulunamadı, durduruluyor.")
            break

        print(f"\nSayfa {page_number}: {len(route_boxes)} rota bulundu.")

        for idx, box in enumerate(route_boxes, 1):
            data = {col: None for col in columns}

            # --- Listing sayfasından temel bilgileri çek ---
            title_div = box.find('div', class_='title')
            if title_div:
                dep_span = title_div.find('span', class_='grey')
                if dep_span:
                    data["departure_airport"] = dep_span.get_text(strip=True)

                title_text = title_div.get_text(separator=" ", strip=True)
                if "/" in title_text:
                    data["arrival_airport"] = title_text.split("/")[-1].strip()[:3]

            content_div = box.find('div', class_='content')
            if content_div:
                dist_li = content_div.find('li', class_='li1')
                if dist_li and dist_li.find('b'):
                    data["distance"] = dist_li.find('b').get_text(strip=True)

            # --- Detay sayfası linkini bul ---
            btn_detail = box.find('a', href=re.compile(r'/network/showline/'))
            if not btn_detail:
                print(f"  [{idx}] Detay linki bulunamadı, atlanıyor.")
                continue

            detail_url = base_url + btn_detail['href']

            # FIX 3: Set ile tam duplikasyon koruması (sadece ardışık değil, tüm tekrarları yakalar)
            if detail_url in processed_urls:
                print(f"  [{idx}] Zaten işlendi, atlanıyor: {btn_detail['href']}")
                continue
            processed_urls.add(detail_url)

            route_label = f"{data.get('departure_airport', '?')}-{data.get('arrival_airport', '?')}"
            print(f"  [{idx}] {route_label} işleniyor...")

            # --- Detay sayfasına git ---
            driver.get(detail_url)

            # FIX 4: Rate limiting koruması - rastgele gecikme
            time.sleep(random.uniform(2.0, 3.0))

            # FIX 5: Hata loglanarak atlanıyor (sessiz yutma yerine)
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "todayResultsBody"))
                )
            except Exception as e:
                print(f"    HATA: Detay sayfası yüklenemedi ({route_label}) - {type(e).__name__}: {e}")
                continue

            detail_soup = BeautifulSoup(driver.page_source, 'html.parser')

            # --- Box1: Atanmış uçak sayısı, haftalık uçuş ---
            box1 = detail_soup.find('ul', id='box1')
            if box1:
                lis = box1.find_all('li')
                if len(lis) >= 2 and lis[1].find('strong'):
                    data["assigned_aircraft_count"] = lis[1].find('strong').get_text(strip=True)
                if len(lis) >= 3 and lis[2].find('strong'):
                    data["weekly_flight_count"] = lis[2].find('strong').get_text(strip=True)

            # --- Box2: Kategori, vergiler ---
            box2 = detail_soup.find('ul', id='box2')
            if box2:
                lis2 = box2.find_all('li')
                if len(lis2) >= 1:
                    cat_imgs = lis2[0].find_all('img', src=re.compile(r'/images/icons20/cat\d+\.png'))
                    if cat_imgs:
                        match = re.search(r'cat(\d+)\.png', cat_imgs[-1]['src'])
                        if match:
                            data["max_category"] = match.group(1)
                if len(lis2) >= 3 and lis2[2].find('b'):
                    data["taxes"] = lis2[2].find('b').get_text(strip=True)

            # FIX 6: Uçak listesi - iç içe span duplikasyonu önlendi
            aircraft_names = []
            for ac_box in detail_soup.select('.aircraftListView .aircraftListBox'):
                ac_title = ac_box.find('div', class_='title')
                if not ac_title:
                    continue
                main_span = ac_title.find('span', recursive=False)
                if not main_span:
                    continue
                name_span = main_span.find('span', class_='editAircraftName')
                ac_name = name_span.get_text(strip=True) if name_span else ""
                full_text = main_span.get_text(strip=True)
                model = full_text.split('/')[0].strip() if '/' in full_text else full_text
                aircraft_names.append(f"{model} ({ac_name})" if ac_name else model)

            data["aircrafts_on_route"] = ", ".join(aircraft_names)

            # --- Talep / Arz / Fiyat tabloları ---
            extract_table_data(detail_soup.find('tbody', id='todayResultsBody'), data, "today")
            extract_table_data(detail_soup.find('tbody', id='yesterdayResultsBody'), data, "yesterday")

            all_routes.append(data)

        page_number += 1

    driver.quit()

    df = pd.DataFrame(all_routes, columns=columns)
    df.to_excel(output_excel_path, index=False)
    print(f"\nİşlem tamamlandı. {len(all_routes)} rota kaydedildi → {output_excel_path}")


def human_type(element, text):
    """Her karakteri rastgele gecikmeyle yazar."""
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.05, 0.15))


if __name__ == "__main__":
    main()