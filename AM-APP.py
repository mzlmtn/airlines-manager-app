import streamlit as st
import math

st.set_page_config(page_title="AM Finans & Filo Yöneticisi", layout="wide")

st.title("✈️ AM Finansal Filo ve Rota Yöneticisi")
st.markdown("Demand aşımını önleyen **%100 Doluluk Algoritması** ve Oyun İçi Formüllerle **Otomatik Bilet Hesaplayıcı**.")

# Çok Daha Geniş Uçak Veritabanı
AIRCRAFT_DB = {
    "Airbus A380-800": {"range": 15556, "speed": 903, "seats": 853, "cargo": 84, "price": 403000000},
    "Boeing 747-8I": {"range": 14815, "speed": 911, "seats": 605, "cargo": 76, "price": 379100000},
    "Boeing 747-400": {"range": 13450, "speed": 903, "seats": 660, "cargo": 65, "price": 260000000},
    "Boeing 777-300ER": {"range": 14685, "speed": 898, "seats": 550, "cargo": 71, "price": 330000000},
    "Boeing 777-200ER": {"range": 14305, "speed": 898, "seats": 440, "cargo": 59, "price": 261500000},
    "Airbus A350-1000": {"range": 14750, "speed": 903, "seats": 475, "cargo": 54, "price": 366500000},
    "Airbus A350-900XWB": {"range": 15000, "speed": 903, "seats": 440, "cargo": 45, "price": 317400000},
    "Boeing 787-9": {"range": 14140, "speed": 911, "seats": 420, "cargo": 34, "price": 264600000},
    "Boeing 787-8": {"range": 13620, "speed": 911, "seats": 381, "cargo": 28, "price": 224600000},
    "Airbus A330-900neo": {"range": 13334, "speed": 880, "seats": 440, "cargo": 45, "price": 296400000},
    "Airbus A330-300": {"range": 11750, "speed": 880, "seats": 440, "cargo": 45, "price": 264200000},
    "Boeing 767-300ER": {"range": 11070, "speed": 850, "seats": 350, "cargo": 38, "price": 197100000},
    "Airbus A310-300": {"range": 9540, "speed": 850, "seats": 275, "cargo": 33, "price": 105000000},
    "Boeing 757-200": {"range": 7222, "speed": 850, "seats": 239, "cargo": 25, "price": 85000000},
    "Airbus A321-200neo-LR": {"range": 7408, "speed": 840, "seats": 244, "cargo": 5, "price": 114500000},
    "Boeing 737 MAX 9": {"range": 6574, "speed": 839, "seats": 220, "cargo": 6, "price": 116600000}
}

col_main1, col_main2 = st.columns([1, 1])

with col_main1:
    st.subheader("1. Rota ve Demand Bilgileri")
    distance = st.number_input("Rota Uzaklığı (km)", value=8000, step=100)
    
    st.markdown("**Günlük Brüt Demand**")
    c1, c2, c3, c4 = st.columns(4)
    with c1: demand_e = st.number_input("Eco Dmd", value=0, step=10)
    with c2: demand_b = st.number_input("Bus Dmd", value=0, step=10)
    with c3: demand_f = st.number_input("First Dmd", value=0, step=10)
    with c4: demand_c = st.number_input("Cargo Dmd", value=0, step=1)

with col_main2:
    st.subheader("2. Finansal Veriler (Otomatik)")
    st.markdown("Havayolunuzun **Comfort (Konfor)** istatistiğini girin. Bilet fiyatları uzaklığa göre otomatik hesaplanacaktır.")
    comfort_stat = st.number_input("Comfort İstatistiği (Araştırmalardan gelen)", value=0, step=50)
    
    # Tersine Mühendislik Tycoon İdeal (Audit) Fiyat Formülleri
    comfort_multiplier = 1 + (comfort_stat / 3000)
    auto_price_e = math.floor(120 + (distance * 0.2639) * comfort_multiplier)
    auto_price_b = math.floor(160 + (distance * 0.3509) * comfort_multiplier)
    auto_price_f = math.floor(276 + (distance * 0.6068) * comfort_multiplier)
    
    # Cargo katsayısı uzaklığa göre değişir. LH (Long Haul > 5000km) için 0.47
    cargo_coef = 0.47 if distance > 5000 else (0.52 if distance > 2000 else 0.56)
    auto_price_c = math.floor(200 + (distance * cargo_coef))
    
    st.info("💡 **Tersine Mühendislik ile Bulunan İdeal (Audit) Fiyatlar:**")
    c5, c6, c7, c8 = st.columns(4)
    with c5: price_e = st.number_input("Eco ($)", value=auto_price_e)
    with c6: price_b = st.number_input("Bus ($)", value=auto_price_b)
    with c7: price_f = st.number_input("First ($)", value=auto_price_f)
    with c8: price_c = st.number_input("Cargo ($)", value=auto_price_c)

available_planes = [(n, s) for n, s in AIRCRAFT_DB.items() if s["range"] >= distance]
available_planes.sort(key=lambda x: x[1]["seats"], reverse=True)

if st.button("Filoyu Optimize Et ve Kârı Hesapla", use_container_width=True):
    if not available_planes:
        st.error(f"Hata: {distance} km menzile uçabilecek uçak bulunamadı!")
    else:
        curr_e_wk = math.ceil(demand_e / 2) * 7
        curr_b_wk = math.ceil(demand_b / 2) * 7
        curr_f_wk = math.ceil(demand_f / 2) * 7
        curr_c_wk = math.ceil(demand_c / 2) * 7
        
        st.success(f"📊 **Hedef Haftalık Net Demand:** {curr_e_wk} Eco | {curr_b_wk} Bus | {curr_f_wk} First | {curr_c_wk} Kargo")
        
        fleet = []
        plane_counter = 1
        total_fleet_cost = 0
        total_weekly_revenue = 0
        
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
                
                if plane_weekly_cap <= total_eco_demand_wk:
                    chosen_name, chosen_stats, chosen_wk_flights = name, stats, wk_flights
                    break
            
            if chosen_name is None:
                smallest_name, smallest_stats = available_planes[-1]
                round_trip_time = (distance * 2) / smallest_stats["speed"] if smallest_stats["speed"] > 0 else 1
                sm_wk_flights = math.floor(168 / round_trip_time) if round_trip_time > 0 else 1
                if sm_wk_flights < 1: sm_wk_flights = 1
                sm_plane_weekly_cap = smallest_stats["seats"] * sm_wk_flights
                
                if total_eco_demand_wk < sm_plane_weekly_cap * 0.70:
                    st.warning("⚠️ Kalan demand bir uçağı kârlı şekilde dolduramayacak kadar düşük. Negatif demand/zarar oluşmaması için uçak ataması durduruldu.")
                    break
                else:
                    chosen_name, chosen_stats, chosen_wk_flights = smallest_name, smallest_stats, sm_wk_flights

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
            
            if remaining_space > 0:
                config['E'] += remaining_space
                curr_e_wk = max(0, curr_e_wk - (remaining_space * chosen_wk_flights))
            
            needed_c = math.ceil(curr_c_wk / chosen_wk_flights)
            take_c = min(needed_c, chosen_stats["cargo"])
            config['Cargo'] = take_c
            curr_c_wk = max(0, curr_c_wk - (take_c * chosen_wk_flights))
            
            used_seats = (config['F'] * 4) + (config['B'] * 2) + config['E']
            config['Fill_Rate'] = (used_seats / chosen_stats["seats"]) * 100
            
            rt_time = (distance * 2) / chosen_stats["speed"]
            config['Use_Rate'] = ((chosen_wk_flights * rt_time) / 168) * 100
            
            flight_revenue = (config['E'] * price_e) + (config['B'] * price_b) + (config['F'] * price_f) + (config['Cargo'] * price_c)
            weekly_plane_rev = flight_revenue * chosen_wk_flights
            
            config['Weekly_Rev'] = weekly_plane_rev
            
            if weekly_plane_rev > 0:
                config['ROI_Weeks'] = chosen_stats["price"] / weekly_plane_rev
            else:
                config['ROI_Weeks'] = 0
            
            total_fleet_cost += chosen_stats["price"]
            total_weekly_revenue += weekly_plane_rev
            
            fleet.append(config)
            plane_counter += 1

        if not fleet:
            st.info("Yerleştirilecek yeterli demand bulunamadı.")
        else:
            st.divider()
            
            col_sum1, col_sum2, col_sum3 = st.columns(3)
            with col_sum1:
                st.markdown(f"### 💸 Filo Maliyeti\n:red[**$ {total_fleet_cost:,.0f}**]")
            with col_sum2:
                st.markdown(f"### 📈 Brüt Hft. Gelir\n:green[**$ {total_weekly_revenue:,.0f}**]")
            with col_sum3:
                if total_weekly_revenue > 0:
                    st.markdown(f"### ⏱️ Ortalama Amortisman\n**{total_fleet_cost/total_weekly_revenue:.1f} Hafta**")
                else:
                    st.markdown("### ⏱️ Ortalama Amortisman\n**Bilet fiyatı girilmedi**")
            
            st.divider()
            
            for f in fleet:
                price_str = f"$ {f['Stats']['price']:,.0f}"
                rev_str = f"$ {f['Weekly_Rev']:,.0f}" if f['Weekly_Rev'] > 0 else "Bilet Fiyatı Gerekli"
                roi_str = f"{f['ROI_Weeks']:.1f} Oyun Haftası" if f['ROI_Weeks'] > 0 else "-"
                
                with st.expander(f"✈️ {f['Plane_Num']}. Uçak: {f['Name']} | Doluluk: %{f['Fill_Rate']:.1f}", expanded=True):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.write("**Konfigürasyon**")
                        st.write(f"- Eco: **{f['E']}**")
                        st.write(f"- Bus: **{f['B']}**")
                        st.write(f"- First: **{f['F']}**")
                        st.write(f"- Cargo: **{f['Cargo']}** ton")
                    with c2:
                        st.write("**Operasyon**")
                        st.write(f"- Hft. Sefer: **{f['Wk_Flights']}**")
                        st.write(f"- Uçak Fiyatı: **{price_str}**")
                        st.write(f"- Hft. Gelir: **:green[{rev_str}]**")
                    with c3:
                        st.write("**Verimlilik**")
                        st.write(f"- Kullanım: **%{f['Use_Rate']:.1f}**")
                        st.write(f"- Gidiş-Dönüş: **{((distance * 2) / f['Stats']['speed']):.1f}s**")
                        st.write(f"- **Amortisman:** **{roi_str}**")

            st.info(f"**Atanmayan Kalan Haftalık Demand:** {curr_e_wk} Eco, {curr_b_wk} Bus, {curr_f_wk} First, {curr_c_wk} Kargo")
