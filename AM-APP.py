import streamlit as st
import math

st.set_page_config(page_title="AM Akıllı Filo Yöneticisi", layout="centered")

st.title("Airlines Manager: Akıllı Filo Yöneticisi")
st.markdown("Bu araç **A380-800'ü önceliklendirerek** demand'i eritmeye başlar. Kalan demand azaldığında, zarar etmeni engellemek için veritabanındaki **diğer uygun uçaklara** otomatik geçiş yapar.")

# Oyun içi popüler Long Haul (ve Medium) Uçak Veritabanı
AIRCRAFT_DB = {
    "Airbus A380-800": {"range": 15556, "speed": 903, "seats": 853, "cargo": 84},
    "Boeing 747-400": {"range": 13450, "speed": 903, "seats": 660, "cargo": 65},
    "Boeing 777-300ER": {"range": 14685, "speed": 898, "seats": 550, "cargo": 71},
    "Boeing 787-8": {"range": 13620, "speed": 911, "seats": 381, "cargo": 28},
    "Boeing 767-200ER": {"range": 12220, "speed": 850, "seats": 290, "cargo": 35},
    "Airbus A321-200neo-LR": {"range": 7408, "speed": 840, "seats": 244, "cargo": 5}
}

st.header("1. Rota Bilgileri")
distance = st.number_input("Rota Uzaklığı (km)", value=8000, step=100)

st.header("2. Brüt Rota Demand'i")
st.caption("Oyunda gördüğünüz ham sayıları girin (Sistem otomatik 2'ye bölecektir).")
col1, col2, col3, col4 = st.columns(4)
with col1:
    demand_e = st.number_input("Economy", value=0, step=10)
with col2:
    demand_b = st.number_input("Business", value=0, step=10)
with col3:
    demand_f = st.number_input("First", value=0, step=10)
with col4:
    demand_c = st.number_input("Cargo", value=0, step=1)

# Filtrelenmiş Uçakları Bulma
available_planes = []
for name, stats in AIRCRAFT_DB.items():
    if stats["range"] >= distance:
        available_planes.append((name, stats))

# Uçakları kapasitelerine (seats) göre büyükten küçüğe sırala
available_planes.sort(key=lambda x: x[1]["seats"], reverse=True)

if st.button("Akıllı Konfigürasyonu Hesapla"):
    if not available_planes:
        st.error(f"Hata: {distance} km menzile uçabilecek bir uçak veritabanında bulunamadı!")
    else:
        # Demand'in yarısını alıyoruz (Gidiş-Dönüş hesaplaması için)
        curr_e = math.ceil(demand_e / 2)
        curr_b = math.ceil(demand_b / 2)
        curr_f = math.ceil(demand_f / 2)
        curr_c = math.ceil(demand_c / 2)
        
        st.write(f"📊 **İşleme Alınan Net Demand (1/2):** {curr_e} Eco, {curr_b} Bus, {curr_f} First, {curr_c} Kargo")
        st.divider()

        fleet = []
        plane_counter = 1
        
        # Algoritma: Tüm demand eriyene kadar devam et
        while True:
            total_eco_demand = curr_e + (curr_b * 2) + (curr_f * 4)
            if total_eco_demand <= 0 and curr_c <= 0:
                break
                
            chosen_name = None
            chosen_stats = None
            chosen_df = 1
            
            # En uygun uçağı seçme mantığı
            for name, stats in available_planes:
                flight_time = distance / stats["speed"] if stats["speed"] > 0 else 1
                df = math.floor(24 / flight_time) if flight_time > 0 else 1
                if df < 1: df = 1
                
                plane_daily_cap = stats["seats"] * df
                
                # Eğer kalan demand, bu uçağın kapasitesinin en az %85'ini dolduruyorsa (yani max %15 eksiye düşeceksek) uçağı seç!
                if total_eco_demand >= plane_daily_cap * 0.85:
                    chosen_name = name
                    chosen_stats = stats
                    chosen_df = df
                    break
            
            # Eğer hiçbir uçak %85 dolmuyorsa (demand çok azalmışsa), mecburen en küçük uçağı seç
            if chosen_name is None:
                chosen_name, chosen_stats = available_planes[-1]
                flight_time = distance / chosen_stats["speed"] if chosen_stats["speed"] > 0 else 1
                chosen_df = math.floor(24 / flight_time) if flight_time > 0 else 1
                if chosen_df < 1: chosen_df = 1
                
                # Ekstra Kontrol: Eğer en küçük uçak bile %40'tan az doluyorsa (çok büyük zarar yazacaksa), döngüyü kır.
                if total_eco_demand < (chosen_stats["seats"] * chosen_df) * 0.40:
                    st.warning(f"⚠️ Kalan demand çok düşük ({total_eco_demand} alan). Yeni bir uçak kaldırmak zarar yazdıracağı için algoritma durduruldu.")
                    break

            # --- UÇAK İÇİ KOLTUK YERLEŞTİRME ---
            config = {'Plane_Num': plane_counter, 'Name': chosen_name, 'E': 0, 'B': 0, 'F': 0, 'Cargo': 0, 'Flights': chosen_df}
            remaining_space = chosen_stats["seats"]
            
            # 1. First Class
            needed_f = math.ceil(curr_f / chosen_df)
            take_f = min(needed_f, remaining_space // 4)
            config['F'] = take_f
            curr_f -= take_f * chosen_df
            remaining_space -= take_f * 4
            if curr_f < 0: curr_f = 0
            
            # 2. Business Class
            needed_b = math.ceil(curr_b / chosen_df)
            take_b = min(needed_b, remaining_space // 2)
            config['B'] = take_b
            curr_b -= take_b * chosen_df
            remaining_space -= take_b * 2
            if curr_b < 0: curr_b = 0
            
            # 3. Economy Class
            needed_e = math.ceil(curr_e / chosen_df)
            take_e = min(needed_e, remaining_space)
            config['E'] = take_e
            curr_e -= take_e * chosen_df
            remaining_space -= take_e
            
            # Kural: Oyunda uçakta boşluk bırakılamaz. Eğer yerleştirme sonrası uçağın alanında boşluk kaldıysa, bunu eksiye düşme pahasına Economy'ye bas.
            if remaining_space > 0:
                config['E'] += remaining_space
                curr_e -= remaining_space * chosen_df
                
            if curr_e < 0: curr_e = 0
            
            # 4. Kargo
            needed_c = math.ceil(curr_c / chosen_df)
            take_c = min(needed_c, chosen_stats["cargo"])
            config['Cargo'] = take_c
            curr_c -= take_c * chosen_df
            if curr_c < 0: curr_c = 0
            
            fleet.append(config)
            plane_counter += 1

        # Sonuçları Yazdırma
        if len(fleet) == 0:
            st.warning("Yerleştirilecek yeterli demand bulunamadı.")
        else:
            st.success(f"Optimum filo oluşturuldu! Toplam **{len(fleet)} adet** uçak kullanılacak.")
            
            for f in fleet:
                st.subheader(f"✈️ Uçak {f['Plane_Num']}: {f['Name']}")
                st.write(f"⏱️ **Günlük Sefer Sayısı:** {f['Flights']}")
                st.write(f"- **Economy:** {f['E']} koltuk")
                st.write(f"- **Business:** {f['B']} koltuk")
                st.write(f"- **First Class:** {f['F']} koltuk")
                st.write(f"- **Cargo:** {f['Cargo']} ton")
                st.divider()
                
            st.info(f"**Karşılanamayan / Kalan Demand:** {curr_e} Eco, {curr_b} Bus, {curr_f} First, {curr_c} Kargo")
