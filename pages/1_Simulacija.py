import streamlit as st
import random
import pandas as pd
import requests

st.set_page_config(page_title="BB84 Simulacija", layout="wide")
st.title("BB84 Simulacija")

# --- Privzete vrednosti ---
n = st.number_input("Število fotonov (n)", min_value=1, max_value=10000, value=100, step=1)
eve_on = st.checkbox("Vklopi Eve", value=False)
verjetnost_suma = st.slider("Verjetnost kvantnega šuma", 0.0, 0.1, 0.02, step=0.01)

# --- QRNG API ---
def pridobi_kvantne_bite(n):
    try:
        url = f"https://qrng.anu.edu.au/API/jsonI.php?length={n}&type=uint8"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data["success"]:
                return [x % 2 for x in data["data"]]
    except:
        pass
    return [random.randint(0, 1) for _ in range(n)]

# --- Simulacija ---
if st.button("Zaženi simulacijo"):
    kvantni_biti = pridobi_kvantne_bite(n)
    indeks_kvantnega_bita = 0
    data = []

    for _ in range(n):
        # --- Alice ---
        baza_alice = random.choice(["rect", "diag"])
        bit_alice = random.choice([0, 1])
        kot_alice = {("rect", 0): 0, ("rect", 1): 90, ("diag", 0): 45, ("diag", 1): 135}[(baza_alice, bit_alice)]

        # --- Eve ---
        if eve_on:
            baza_eve = random.choice(["rect", "diag"])
            kot_eve = random.choice([0, 45, 90, 135])
            enaka_baza_eve = baza_eve == baza_alice
            bit_eve = bit_alice if enaka_baza_eve else random.choice([0, 1])
            bit_predan_bobu = bit_eve
            baza_predana_bobu = baza_eve
            kot_predan_bobu = kot_eve
        else:
            bit_predan_bobu = bit_alice
            baza_predana_bobu = baza_alice
            kot_predan_bobu = kot_alice

        # --- Bob ---
        baza_bob = random.choice(["rect", "diag"])
        kot_bob = {"rect": random.choice([0, 90]), "diag": random.choice([45, 135])}[baza_bob]
        enaka_baza = baza_predana_bobu == baza_bob

        if enaka_baza:
            bit_bob = bit_predan_bobu
            if random.random() < verjetnost_suma:
                bit_bob = 1 - bit_bob  # Šum obrne bit
                opomba_bob = "Baze enake – kvantni šum"
            else:
                opomba_bob = "Baze enake – uspešna meritev"
        else:
            bit_bob = kvantni_biti[indeks_kvantnega_bita]
            indeks_kvantnega_bita += 1
            opomba_bob = "Baze različne – naključna meritev"

        data.append({
            "Alice kot (°)": kot_alice,
            "Alice bit": bit_alice,
            "Baza Alice": baza_alice,
            "Eve vklopljena": "Da" if eve_on else "Ne",
            "Eve baza": baza_eve if eve_on else None,
            "Eve bit": bit_eve if eve_on else None,
            "Bob kot (°)": kot_bob,
            "Baza Bob": baza_bob,
            "Ujemanje baz": "Da" if enaka_baza else "Ne",
            "Bobov bit": bit_bob,
            "Bob opomba": opomba_bob
        })

    df = pd.DataFrame(data)

    st.subheader("Rezultati simulacije")

    def obarvaj_baze(val):
        if val == "Da":
            return "background-color: lightgreen; font-weight: bold"
        return ""

    def obarvaj_neusklajene_bite(row):
        if row["Ujemanje baz"] == "Da" and row["Alice bit"] != row["Bobov bit"]:
            return ['background-color: violet' if col == "Bobov bit" else '' for col in row.index]
        else:
            return ['' for _ in row.index]

    styled_df = df.style.map(obarvaj_baze, subset=["Ujemanje baz"])
    styled_df = styled_df.apply(obarvaj_neusklajene_bite, axis=1)
    st.dataframe(styled_df, use_container_width=True)

    # --- Statistika ---
    ujemajoce = df[df["Ujemanje baz"] == "Da"]
    pravilni = (ujemajoce["Alice bit"] == ujemajoce["Bobov bit"]).sum()
    stevilo_ujemanj = len(ujemajoce)
    neusklajeni = stevilo_ujemanj - pravilni

    st.subheader("Analiza rezultatov")
    st.markdown(f"""
    - **Število ujemanj baz:** `{stevilo_ujemanj} / {n}`
    - **Pravilno prebranih bitov:** `{pravilni} / {stevilo_ujemanj}`
    - **Neusklajeni biti:** `{neusklajeni} / {stevilo_ujemanj}`
    """)

    if stevilo_ujemanj > 0:
        delež_neusklajenih = neusklajeni / stevilo_ujemanj
        st.markdown(f"- **Delež neusklajenih:** `{delež_neusklajenih:.2%}`")

        if delež_neusklajenih > 0.2:
            st.error("Visok delež neusklajenosti – možna prisotnost Eve!")
        elif delež_neusklajenih > 0.11:
            st.warning("Povišan delež napak – šum ali Eve.")
        else:
            st.success("Nizek delež napak – ključ varen.")
    else:
        st.info("Ni bilo dovolj ujemanj za analizo.")

    # --- Skupni ključ ---
    if not eve_on:
        skupni_kljuc = ujemajoce["Alice bit"].tolist()
        st.session_state["skupni_kljuc"] = skupni_kljuc
        st.subheader("Skupni ključ")
        st.code("".join(map(str, skupni_kljuc)), language="text")
        st.info("Ključ bo uporabljen za šifriranje.")
    else:
        st.info("Eve je vklopljena – ključ ni shranjen.")
