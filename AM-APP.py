import streamlit as st
import math

st.set_page_config(page_title="AM Finans & Filo Yöneticisi", layout="centered")

st.title("✈️ AM Finansal Filo ve Rota Yöneticisi")
st.markdown("Demand aşımını önleyen **%100 Doluluk Algoritması**, Otomatik Bilet Hesaplayıcı ve İleri Düzey **Net Kâr** Analizi.")

# Genişletilmiş Uçak Veritabanı (Yakıt: L/100pax/km, Yıpranma: %/100h)
AIRCRAFT_DB = {
    "Airbus A380-800": {"range": 15556, "speed": 903, "seats": 853, "cargo": 84, "price": 403000000, "fuel": 2.05, "wear": 1.2},
    "Boeing 747-8I": {"range": 14815, "speed": 911, "seats": 605, "cargo": 76, "price": 379100000, "fuel": 2.11, "wear": 1.4},
    "Boeing 747-400": {"range": 13450, "speed": 903, "seats": 660, "cargo": 65, "price": 260000000, "fuel": 2.65, "wear": 2.1},
    "Boeing 777-300ER": {"range": 14685, "speed": 898, "seats": 550, "cargo": 71, "price": 330000000, "fuel": 2.10, "wear": 1.5},
    "Boeing 777-200ER": {"range": 14305, "speed": 898, "seats": 440, "cargo": 59, "price": 261500000, "fuel": 2.40, "wear": 1.8},
    "Airbus A350-1000": {"range": 14750, "speed": 903, "seats": 475, "cargo": 54, "price": 366500000, "fuel": 1.65, "wear": 1.1},
    "Airbus A350-900XWB": {"range": 15000, "speed": 903, "seats": 440, "cargo": 45, "price": 317400000, "fuel": 1.70, "wear": 1.1},
    "Boeing 787-9": {"range": 14140, "speed": 911, "seats": 420, "cargo": 34, "price": 264600000, "fuel": 1.80, "wear": 1.1},
    "Boeing 787-8": {"range": 13620, "speed": 911, "seats": 381, "cargo": 28, "price": 224600000, "fuel": 1.85, "wear": 1.1},
    "Airbus A330-900neo": {"range": 13334, "speed": 880, "seats": 440, "cargo": 45, "price": 296400000, "fuel": 1.95, "wear": 1.3},
    "Airbus A330-300": {"range": 11750, "speed": 880, "seats": 440, "cargo": 45, "price": 264200000, "fuel": 2.30, "wear": 1.8},
    "Boeing 767-300ER": {"range": 11070, "speed": 850, "seats": 350, "cargo": 38, "price": 197100000, "fuel": 2.50, "wear": 2.0},
    "Boeing 737-700ER": {"range": 10200, "speed": 850, "seats": 149, "cargo": 15, "price": 81000000, "fuel": 2.60, "wear": 1.7}, 
    "Airbus A310-300": {"range": 9540, "speed": 850, "seats": 275, "cargo": 33, "price": 105000000, "fuel": 2.70, "wear": 2.2},
    "Boeing 757-200": {"range": 7222, "speed": 850, "seats": 239, "cargo": 25, "price": 85000000, "fuel": 2.55, "wear": 1.9},
    "Airbus A321-200neo-LR": {"range": 7408, "speed": 840, "seats": 244, "cargo": 5, "price": 114500000, "fuel": 1.90, "wear": 1.2},
    "Boeing 737 MAX 9": {"range": 6574, "speed": 839, "seats": 220, "cargo": 6, "price": 116600000, "fuel": 1.95, "wear": 1.2}
}

# Arka Plan Sabit Gider Değerleri
AVG_FUEL_PRICE = 750 # $/1000L
ESTIMATED_TAX_RATE = 0.12 # Brüt gelirin %12'si vergi/diğer giderler

st.divider()

# UI: 1. Kısım - Rota ve Fiyatlar
st.subheader("📍 Rota ve Bilet Fiyatları")
distance = st.number_input("Rota Uzaklığı (km)", value=8000, step=100)

with st.expander("Bilet Fiyatlarını Otomatik Hesapla", expanded=True):
    st.markdown("Havayolunuzun **Comfort (Konfor)** istatistiğini girin.")
    comfort_stat = st.number_input("Comfort İstatistiği", value=0, step=50)
    
    # Formül Hesaplamaları
    comfort_multiplier = 1 + (comfort_stat / 3000)
    auto_price_e = math.floor(120 + (distance * 0.2639) * comfort_multiplier)
    auto_price_b = math.floor(160 + (distance * 0.3509) * comfort_multiplier)
    auto_price_f = math.floor(276 + (distance * 0.6068) * comfort_multiplier)
    cargo_coef = 0.47 if distance > 5000 else (0.52 if distance > 2000 else 0.56)
    auto_price_c = math.floor(200 + (distance * cargo_coef))
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: price_e = st.number_input("Eco ($)", value=auto_price_e)
    with c2: price_b = st.number_input("Bus ($)", value=auto_price_b)
    with c3: price_f = st.number_input("First ($)", value=auto_price_f)
    with c4: price_c = st.number_input("Cargo ($)", value=auto_price_c)

# UI: 2. Kısım - Demand
st.subheader("👥 Günlük Brüt Demand")
c5, c6, c7, c8 = st.columns(4)
with c5: demand_e = st.number_input("Eco Dmd", value=0, step=10)
with c6: demand_b = st.number_input("Bus Dmd", value=0, step=10)
with c7: demand_f = st.number_input("First Dmd", value=0, step=10)
with c8: demand_c = st.number_input("Cargo Dmd", value=0, step=1)

available_planes = [(n, s) for n, s in AIRCRAFT_DB.items() if s["range"] >= distance]
available_planes.sort(key=lambda x: x[1]["seats"], reverse=True)

st.write("") 
if st.button("Filoyu Optimize Et ve Net Kârı Hesapla", use_container_width=True, type="primary"):
    if not available_planes:
        st.error(f"Hata: {distance} km menzile uçabilecek uçak bulunamadı!")
    else:
        # Arka planda hesaplama için Haftalık Net Demand'e çevrilir
        curr_e_wk = math.ceil(demand_e / 2) * 7
        curr_b_wk = math.ceil(demand_b / 2) * 7
        curr_f_wk = math.ceil(demand_f / 2) * 7
        curr_c_wk = math.ceil(demand_c / 2) * 7
        
        fleet = []
        plane_counter = 1
        total_fleet_cost = 0
        total_weekly_gross = 0
        total_weekly_net = 0
        
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
                
                if total_eco_demand_wk < sm_plane_weekly_cap * 0.65:
                    st.warning("⚠️ Kalan demand bir uçağı kârlı şekilde dolduramayacak kadar düşük. Zarar oluşmaması için uçak ataması durduruldu.")
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
            
            # Operasyon ve Verimlilik Verileri
            used_seats = (config['F'] * 4) + (config['B'] * 2) + config['E']
            total_pax = config['F'] + config['B'] + config['E']
            config['Fill_Rate'] = (used_seats / chosen_stats["seats"]) * 100
            
            rt_time = (distance * 2) / chosen_stats["speed"]
            config['Use_Rate'] = ((chosen_wk_flights * rt_time) / 168) * 100
            config['Wk_Hours_Flown'] = chosen_wk_flights * rt_time
            
            # Finansal Hesaplamalar
            flight_gross_rev = (config['E'] * price_e) + (config['B'] * price_b) + (config['F'] * price_f) + (config['Cargo'] * price_c)
            weekly_gross = flight_gross_rev * chosen_wk_flights
            
            weekly_fuel_cost = ((distance * 2) * (chosen_stats["fuel"] / 100) * total_pax) * chosen_wk_flights * (AVG_FUEL_PRICE / 1000)
            weekly_other_costs = weekly_gross * ESTIMATED_TAX_RATE
            
            # Tahmini Bakım Gideri (Wear Expense)
            # Formül: (% Wear / 100) * (Haftalık Uçuş Saati / 100) * Uçak Fiyatı * Bakım Çarpanı
            weekly_maint_cost = (chosen_stats["wear"] / 100) * (config['Wk_Hours_Flown'] / 100) * (chosen_stats["price"] * 0.015)
            
            weekly_net = weekly_gross - weekly_fuel_cost - weekly_other_costs - weekly_maint_cost
            
            config['Weekly_Gross'] = weekly_gross
            config['Weekly_Net'] = weekly_net
            config['Fuel_Cost'] = weekly_fuel_cost
            config['Other_Cost'] = weekly_other_costs
            config['Maint_Cost'] = weekly_maint_cost
            
            # Birim Zaman Kârlılıkları
            config['Hourly_Profit'] = weekly_net / config['Wk_Hours_Flown'] if config['Wk_Hours_Flown'] > 0 else 0
            config['Flight_Profit'] = weekly_net / chosen_wk_flights if chosen_wk_flights > 0 else 0
            
            if weekly_net > 0:
                config['ROI_Weeks'] = chosen_stats["price"] / weekly_net
            else:
                config['ROI_Weeks'] = 0
            
            total_fleet_cost += chosen_stats["price"]
            total_weekly_gross += weekly_gross
            total_weekly_net += weekly_net
            
            fleet.append(config)
            plane_counter += 1

        if not fleet:
            st.info("Yerleştirilecek yeterli demand bulunamadı.")
        else:
            st.divider()
            
            # Finansal Özet Kartı
            st.markdown("""
            <div style="background-color: #1e1e1e; padding: 20px; border-radius: 10px; text-align: center;">
                <h3 style="margin-bottom: 5px;">💸 Toplam Filo Maliyeti</h3>
                <h2 style="color: #ff4b4b; margin-top: 0;">$ {:,.0f}</h2>
                <div style="display: flex; justify-content: space-around; margin-top: 15px;">
                    <div>
                        <h4 style="margin-bottom: 5px; color: #a0a0a0;">Brüt Haftalık Gelir</h4>
                        <h3 style="color: #ffffff; margin-top: 0;">$ {:,.0f}</h3>
                    </div>
                    <div>
                        <h4 style="margin-bottom: 5px; color: #a0a0a0;">Tahmini Net Kâr</h4>
                        <h3 style="color: #00d26a; margin-top: 0;">$ {:,.0f}</h3>
                    </div>
                </div>
            </div>
            """.format(total_fleet_cost, total_weekly_gross, total_weekly_net), unsafe_allow_html=True)
            
            if total_weekly_net > 0:
                st.caption(f"⏱️ **Gerçekçi Amortisman:** Tüm filo yaklaşık **{total_fleet_cost/total_weekly_net:.1f} oyun haftasında** maliyetini çıkarır.")
            
            st.write("")
            
            for f in fleet:
                price_str = f"$ {f['Stats']['price']:,.0f}"
                roi_str = f"{f['ROI_Weeks']:.1f} Hafta" if f['ROI_Weeks'] > 0 else "-"
                
                with st.expander(f"✈️ {f['Plane_Num']}. Uçak: {f['Name']} | Doluluk: %{f['Fill_Rate']:.1f} | Verim: %{f['Use_Rate']:.1f}", expanded=True):
                    
                    info_html = f"""
                    <div style='margin-bottom: 10px; font-size: 15px;'>
                        <b>Fiyat:</b> {price_str} &nbsp;|&nbsp; 
                        <b>Hft. Brüt:</b> ${f['Weekly_Gross']:,.0f} &nbsp;|&nbsp; 
                        <b>Hft. Net:</b> <span style='color:#00d26a; font-weight:bold;'>${f['Weekly_Net']:,.0f}</span> &nbsp;|&nbsp; 
                        <b>Amortisman:</b> {roi_str}
                    </div>
                    """
                    st.markdown(info_html, unsafe_allow_html=True)
                    
                    c_in1, c_in2, c_in3, c_in4 = st.columns(4)
                    with c_in1:
                        st.markdown("**💺 Konfigürasyon**")
                        st.write(f"- Eco: **{f['E']}**")
                        st.write(f"- Bus: **{f['B']}**")
                        st.write(f"- First: **{f['F']}**")
                        st.write(f"- Cargo: **{f['Cargo']}**")
                    with c_in2:
                        st.markdown("**💸 Giderler (Haftalık)**")
                        st.write(f"- Yakıt: **${f['Fuel_Cost']:,.0f}**")
                        st.write(f"- Vergi: **${f['Other_Cost']:,.0f}**")
                        st.write(f"- Bakım(Wear): **${f['Maint_Cost']:,.0f}**")
                    with c_in3:
                        st.markdown("**🔄 Operasyon**")
                        st.write(f"- Sefer: **{f['Wk_Flights']}**")
                        st.write(f"- Süre: **{((distance * 2) / f['Stats']['speed']):.1f}s**")
                        st.write(f"- Hacim: **{f['Wk_Hours_Flown']:.1f} saat**")
                    with c_in4:
                        st.markdown("**📊 Performans**")
                        st.write(f"- Seferlik Kâr: **${f['Flight_Profit']:,.0f}**")
                        st.write(f"- Saatlik Kâr: **${f['Hourly_Profit']:,.0f}**")

            # Kullanıcının girdiği formata (Günlük Brüt) geri çevirme işlemi
            rem_daily_e = math.floor((curr_e_wk / 7) * 2)
            rem_daily_b = math.floor((curr_b_wk / 7) * 2)
            rem_daily_f = math.floor((curr_f_wk / 7) * 2)
            rem_daily_c = math.floor((curr_c_wk / 7) * 2)
            
            st.info(f"**Kalan (Atanmayan) GÜNLÜK BRÜT Demand:** {rem_daily_e} Eco, {rem_daily_b} Bus, {rem_daily_f} First, {rem_daily_c} Kargo")
