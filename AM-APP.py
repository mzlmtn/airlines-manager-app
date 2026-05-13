import streamlit as st

# iPhone ekranına uygun, kompakt sayfa yapısı
st.set_page_config(page_title="AM Fleet Configurator", layout="centered")

st.title("A380-800 Rota ve Filo Hesaplayıcı")

# Uçak Kapasite Tanımları (Oyun içi maksimum limitler)
st.header("1. Uçak Kapasitesi")
col1, col2 = st.columns(2)
with col1:
    # A380-800 için genelde full economy 853'tür.
    max_seats_e = st.number_input("Max Economy (Alan)", value=853, step=1)
with col2:
    max_cargo = st.number_input("Max Kargo (Ton)", value=84, step=1)

# Rota Demand Bilgileri
st.header("2. Kalan Rota Demand'i")
col3, col4, col5, col6 = st.columns(4)
with col3:
    demand_e = st.number_input("Economy", value=0, step=10)
with col4:
    demand_b = st.number_input("Business", value=0, step=10)
with col5:
    demand_f = st.number_input("First", value=0, step=10)
with col6:
    demand_c = st.number_input("Cargo", value=0, step=1)

# Optimizasyon ve Hesaplama Algoritması
if st.button("Konfigürasyonu Hesapla"):
    planes = []
    plane_count = 1
    
    curr_e = demand_e
    curr_b = demand_b
    curr_f = demand_f
    curr_c = demand_c
    
    # Demand bitene kadar uçak eklemeye devam et
    while (curr_e > 0 or curr_b > 0 or curr_f > 0 or curr_c > 0):
        config = {'Plane': plane_count, 'E': 0, 'B': 0, 'F': 0, 'Cargo': 0}
        remaining_space = max_seats_e
        
        # 1. Öncelik: First Class (1 Koltuk = 4 Economy Boşluğu)
        take_f = min(curr_f, remaining_space // 4)
        config['F'] = take_f
        curr_f -= take_f
        remaining_space -= take_f * 4
        
        # 2. Öncelik: Business Class (1 Koltuk = 2 Economy Boşluğu)
        take_b = min(curr_b, remaining_space // 2)
        config['B'] = take_b
        curr_b -= take_b
        remaining_space -= take_b * 2
        
        # 3. Öncelik: Economy Class (1 Koltuk = 1 Economy Boşluğu)
        take_e = min(curr_e, remaining_space)
        config['E'] = take_e
        curr_e -= take_e
        remaining_space -= take_e
        
        # 4. Kargo (Yolcu kapasitesinden bağımsızdır)
        take_c = min(curr_c, max_cargo)
        config['Cargo'] = take_c
        curr_c -= take_c
        
        # Eğer uçak tamamen boş kaldıysa döngüyü kır
        if config['E'] == 0 and config['B'] == 0 and config['F'] == 0 and config['Cargo'] == 0:
            break
            
        planes.append(config)
        plane_count += 1
        
    # UI Üzerinde Sonuçları Yazdırma
    if len(planes) == 0:
        st.warning("Hesaplanacak bir demand girilmedi.")
    else:
        st.success(f"Demand'i eksiye düşürmeden karşılamak için toplam **{len(planes)} adet** uçağa ihtiyacınız var.")
        
        for p in planes:
            st.subheader(f"Uçak {p['Plane']} Konfigürasyonu")
            st.write(f"- **Economy:** {p['E']} koltuk")
            st.write(f"- **Business:** {p['B']} koltuk")
            st.write(f"- **First Class:** {p['F']} koltuk")
            st.write(f"- **Cargo:** {p['Cargo']} ton")
            st.divider()