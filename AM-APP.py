import streamlit as st
import math

st.set_page_config(page_title="AM Rota ve Filo Yöneticisi", layout="centered")

st.title("Airlines Manager Gelişmiş Hesaplayıcı")
st.markdown("Bu araç girilen demand'i otomatik **ikiye böler**, sefer süresini hesaplar ve A380 fazla gelirse **alternatif uçak** önerir.")

st.header("1. Uçuş Bilgileri")
col1, col2 = st.columns(2)
with col1:
    distance = st.number_input("Rota Uzaklığı (km)", value=8000, step=100)
with col2:
    speed = st.number_input("Uçak Hızı (km/h) (A380: 903)", value=903, step=10)

# Uçuş süresi ve günlük maksimum sefer (frekans) hesaplama
flight_time = distance / speed if speed > 0 else 0
daily_flights = math.floor(24 / flight_time) if flight_time > 0 else 1

# Eğer uçuş 24 saatten uzunsa bile günde en az 1 sefer yapıyormuş gibi (veya 168 saatlik haftalık döngüde) varsayıyoruz
if daily_flights < 1:
    daily_flights = 1

st.info(f"⏱️ **Uçuş Süresi:** {flight_time:.2f} Saat  |  🔁 **Bu Uçak Günde {daily_flights} Sefer Yapabilir**")

st.header("2. Uçak Kapasitesi")
col3, col4 = st.columns(2)
with col3:
    max_seats_e = st.number_input("Max Economy (Alan)", value=853, step=1)
with col4:
    max_cargo = st.number_input("Max Kargo (Ton)", value=84, step=1)

st.header("3. Brüt Rota Demand'i")
st.caption("Oyunda gördüğünüz ham sayıları girin. Hesaplama yapılırken round-trip (gidiş-dönüş) mantığı için bu sayılar otomatik 2'ye bölünecektir.")
col5, col6, col7, col8 = st.columns(4)
with col5:
    demand_e = st.number_input("Economy", value=0, step=10)
with col6:
    demand_b = st.number_input("Business", value=0, step=10)
with col7:
    demand_f = st.number_input("First", value=0, step=10)
with col8:
    demand_c = st.number_input("Cargo", value=0, step=1)

if st.button("Konfigürasyonu Hesapla ve Optimize Et"):
    # Demand'in yarısını alıyoruz
    curr_e = math.ceil(demand_e / 2)
    curr_b = math.ceil(demand_b / 2)
    curr_f = math.ceil(demand_f / 2)
    curr_c = math.ceil(demand_c / 2)
    
    st.write(f"📊 **İşleme Alınan Net Demand (1/2):** {curr_e} Eco, {curr_b} Bus, {curr_f} First, {curr_c} Kargo")
    st.divider()

    planes = []
    plane_count = 1
    
    while (curr_e > 0 or curr_b > 0 or curr_f > 0 or curr_c > 0):
        # Used_Space: Uçağın ne kadarlık economy alanının doldurulduğunu takip eder
        config = {'Plane': plane_count, 'E': 0, 'B': 0, 'F': 0, 'Cargo': 0, 'Used_Space': 0}
        remaining_space = max_seats_e
        
        # Her bir uçağın bir günde taşıyacağı yolcu sayısı, uçaktaki koltuk * günlük sefer sayısıdır.
        # Bu yüzden mevcut demand'i günlük sefer sayısına bölerek uçağa yerleştiriyoruz.
        
        # 1. First Class (1 Koltuk = 4 Alan)
        needed_f = math.ceil(curr_f / daily_flights)
        take_f = min(needed_f, remaining_space // 4)
        config['F'] = take_f
        curr_f -= take_f * daily_flights
        if curr_f < 0: curr_f = 0
        remaining_space -= take_f * 4
        config['Used_Space'] += take_f * 4
        
        # 2. Business Class (1 Koltuk = 2 Alan)
        needed_b = math.ceil(curr_b / daily_flights)
        take_b = min(needed_b, remaining_space // 2)
        config['B'] = take_b
        curr_b -= take_b * daily_flights
        if curr_b < 0: curr_b = 0
        remaining_space -= take_b * 2
        config['Used_Space'] += take_b * 2
        
        # 3. Economy Class (1 Koltuk = 1 Alan)
        needed_e = math.ceil(curr_e / daily_flights)
        take_e = min(needed_e, remaining_space)
        config['E'] = take_e
        curr_e -= take_e * daily_flights
        if curr_e < 0: curr_e = 0
        remaining_space -= take_e
        config['Used_Space'] += take_e
        
        # 4. Cargo
        needed_c = math.ceil(curr_c / daily_flights)
        take_c = min(needed_c, max_cargo)
        config['Cargo'] = take_c
        curr_c -= take_c * daily_flights
        if curr_c < 0: curr_c = 0
        
        # Uçak tamamen boşsa döngüyü kır
        if config['Used_Space'] == 0 and config['Cargo'] == 0:
            break
            
        planes.append(config)
        plane_count += 1

    if len(planes) == 0:
        st.warning("Hesaplanacak bir demand bulunamadı.")
    else:
        st.success(f"Bu rotadaki demand'i sıfırlamak için toplam **{len(planes)} adet** uçağa ihtiyacınız var.")
        
        for p in planes:
            st.subheader(f"✈️ Uçak {p['Plane']} Konfigürasyonu")
            st.write(f"- **Economy:** {p['E']} koltuk")
            st.write(f"- **Business:** {p['B']} koltuk")
            st.write(f"- **First Class:** {p['F']} koltuk")
            st.write(f"- **Cargo:** {p['Cargo']} ton")
            
            # Kapasite kontrolü ve A380 uyarısı
            if p['Used_Space'] < max_seats_e:
                empty_seats = max_seats_e - p['Used_Space']
                st.warning(f"⚠️ **Dikkat:** Bu A380'de {empty_seats} koltukluk (Economy cinsinden) boş alan kaldı. Uçağı bu şekilde uçurmak zarar yazdıracaktır.")
                st.info(f"💡 **Alternatif Uçak Önerisi:** Son kalan demand'i eritmek için piyasadan şu özelliklere sahip daha küçük bir uçak alabilirsiniz:\n"
                        f"- **Maksimum Menzil (Range):** En az {distance} km\n"
                        f"- **Max Economy Kapasitesi:** {p['Used_Space']} koltuk civarında (Veya toplam {p['Used_Space']} alan kaplayacak karma bir uçak)")
            
            st.divider()
