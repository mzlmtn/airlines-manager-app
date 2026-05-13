import streamlit as st
import math

# Sayfa düzenini mobile uyumlu ve kompakt ayarlıyoruz
st.set_page_config(page_title="AM Akıllı Filo Yöneticisi", layout="centered")

st.title("✈️ AM Akıllı Filo & Rota Yöneticisi")
st.markdown("Haftalık (168 saat) bazda hesaplama yaparak en uygun uçakları seçer, kullanım ve doluluk oranlarını analiz eder.")

# Genişletilmiş Long-Haul Uçak Veritabanı
AIRCRAFT_DB = {
    "Airbus A380-800": {"range": 15556, "speed": 903, "seats": 853, "cargo": 84},
    "Boeing 747-8I": {"range": 14815, "speed": 911, "seats": 605, "cargo": 76},
    "Boeing 747-400": {"range": 13450, "speed": 903, "seats": 660, "cargo": 65},
    "Boeing 777-300ER": {"range": 14685, "speed": 898, "seats": 550, "cargo": 71},
    "Boeing 777-200ER": {"range": 14305, "speed": 898, "seats": 440, "cargo": 59},
    "Airbus A350-1000": {"range": 14750, "speed": 903, "seats": 475, "cargo": 54},
    "Airbus A350-900XWB": {"range": 15000, "speed": 903, "seats": 440, "cargo": 45},
    "Boeing 787-9": {"range": 14140, "speed": 911, "seats": 420, "cargo": 34},
    "Boeing 787-8": {"range": 13620, "speed": 911, "seats": 381, "cargo": 28},
    "Airbus A330-300": {"range": 11750, "speed": 880, "seats": 440, "cargo": 45},
    "Boeing 767-300ER": {"range": 11070, "speed": 850, "seats": 350, "cargo": 38},
    "Boeing 767-200ER": {"range": 12220, "speed": 850, "seats": 290, "cargo": 35},
    "Airbus A321-200neo-LR": {"range": 7408, "speed": 840, "seats": 244, "cargo": 5}
}

# 1. Rota Bilgileri (Kompakt)
st.subheader("1. Rota Bilgileri")
distance = st.number_input("Rota Uzaklığı (km)", value=8000, step=100)

# 2. Demand Bilgileri (Kompakt)
st.subheader("2. Günlük Brüt Demand")
col1, col2, col3, col4 = st.columns(4)
with col1: demand_e = st.number_input("Eco", value=0, step=10)
with col2: demand_b = st.number_input("Bus", value=0, step=10)
with col3: demand_f = st.number_input("First", value=0, step=10)
with col4: demand_c = st.number_input("Cargo", value=0, step=1)

# Filtrelenmiş Uçakları Bulma
available_planes = [(n, s) for n, s in AIRCRAFT_DB.items() if s["range"] >= distance]
available_planes.sort(key=lambda x: x[1]["seats"], reverse=True)

if st.button("Filoyu Optimize Et", use_container_width=True):
    if not available_planes:
        st.error(f"Hata: {distance} km menzile uçabilecek uçak bulunamadı!")
    else:
        # Gidiş-Dönüş ve Haftalık Demand Hesaplaması
        # Günlük brut sayıyı 2'ye bölüp, haftalık toplam ihtiyacı bulmak için 7 ile çarpıyoruz
        curr_e_wk = math.ceil(demand_e / 2) * 7
        curr_b_wk = math.ceil(demand_b / 2) * 7
        curr_f_wk = math.ceil(demand_f / 2) * 7
        curr_c_wk = math.ceil(demand_c / 2) * 7
        
        st.success(f"📊 **Haftalık İşlenen Net Demand:** {curr_e_wk} Eco | {curr_b_wk} Bus | {curr_f_wk} First | {curr_c_wk} Kargo")
        
        fleet = []
        plane_counter = 1
        
        while True:
            total_eco_demand_wk = curr_e_wk + (curr_b_wk * 2) + (curr_f_wk * 4)
            if total_eco_demand_wk <= 0 and curr_c_wk <= 0:
                break
                
            chosen_name, chosen_stats, chosen_wk_flights = None, None, 1
            
            for name, stats in available_planes:
                round_trip_time = (distance * 2) / stats["speed"] if stats["speed"] > 0 else 1
                wk_flights = math.floor(168 / round_trip_time) if round_trip_time > 0 else 1
                if wk_flights < 1: continue
                
                plane_weekly_cap = stats["seats"] * wk_flights
                
                # Uçak kapasitesinin en az %80'ini dolduruyorsa seç
                if total_eco_demand_wk >= plane_weekly_cap * 0.80:
                    chosen_name, chosen_stats, chosen_wk_flights = name, stats, wk_flights
                    break
            
            if chosen_name is None:
                chosen_name, chosen_stats = available_planes[-1]
                round_trip_time = (distance * 2) / chosen_stats["speed"] if chosen_stats["speed"] > 0 else 1
                chosen_wk_flights = math.floor(168 / round_trip_time) if round_trip_time > 0 else 1
                if chosen_wk_flights < 1: chosen_wk_flights = 1
                
                if total_eco_demand_wk < (chosen_stats["seats"] * chosen_wk_flights) * 0.35:
                    st.warning(f"⚠️ Kalan demand çok düşük. Uçak kaldırmak zarar yazdıracağı için durduruldu.")
                    break

            # Konfigürasyon Hesaplama (Haftalık Sefer Sayısına Bölerek)
            config = {'Plane_Num': plane_counter, 'Name': chosen_name, 'E': 0, 'B': 0, 'F': 0, 'Cargo': 0, 'Wk_Flights': chosen_wk_flights, 'Stats': chosen_stats}
            remaining_space = chosen_stats["seats"]
            
            needed_f = math.ceil(curr_f_wk / chosen_wk_flights)
            take_f = min(needed_f, remaining_space // 4)
            config['F'] = take_f
            curr_f_wk = max(0, curr_f_wk - (take_f * chosen_wk_flights))
            remaining_space -= take_f * 4
            
            needed_b = math.ceil(curr_b_wk / chosen_wk_flights)
            take_b = min(needed_b, remaining_space // 2)
            config['B'] = take_b
            curr_b_wk = max(0, curr_b_wk - (take_b * chosen_wk_flights))
            remaining_space -= take_b * 2
            
            needed_e = math.ceil(curr_e_wk / chosen_wk_flights)
            take_e = min(needed_e, remaining_space)
            config['E'] = take_e
            curr_e_wk = max(0, curr_e_wk - (take_e * chosen_wk_flights))
            remaining_space -= take_e
            
            # Kalan boşluğu Economy ile doldur (Zararı önlemek için)
            if remaining_space > 0:
                config['E'] += remaining_space
                curr_e_wk = max(0, curr_e_wk - (remaining_space * chosen_wk_flights))
            
            needed_c = math.ceil(curr_c_wk / chosen_wk_flights)
            take_c = min(needed_c, chosen_stats["cargo"])
            config['Cargo'] = take_c
            curr_c_wk = max(0, curr_c_wk - (take_c * chosen_wk_flights))
            
            # Oran Hesaplamaları
            used_seats = (config['F'] * 4) + (config['B'] * 2) + config['E']
            config['Fill_Rate'] = (used_seats / chosen_stats["seats"]) * 100
            
            rt_time = (distance * 2) / chosen_stats["speed"]
            config['Use_Rate'] = ((chosen_wk_flights * rt_time) / 168) * 100
            
            fleet.append(config)
            plane_counter += 1

        if not fleet:
            st.info("Yerleştirilecek yeterli demand bulunamadı.")
        else:
            st.divider()
            for f in fleet:
                # Kompakt Expander Görünümü
                with st.expander(f"✈️ {f['Plane_Num']}. Uçak: {f['Name']} | Doluluk: %{f['Fill_Rate']:.1f}", expanded=True):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"**Economy:** {f['E']}")
                        st.write(f"**Business:** {f['B']}")
                        st.write(f"**First Class:** {f['F']}")
                        st.write(f"**Cargo:** {f['Cargo']} ton")
                    with c2:
                        st.write(f"🔄 **Haftalık Sefer:** {f['Wk_Flights']}")
                        st.write(f"📈 **Kullanım Oranı:** %{f['Use_Rate']:.1f}")
                        st.write(f"⏱️ **Gidiş-Dönüş:** {((distance * 2) / f['Stats']['speed']):.1f} saat")

            st.info(f"**Kalan Haftalık Demand:** {curr_e_wk} Eco, {curr_b_wk} Bus, {curr_f_wk} First, {curr_c_wk} Kargo")
