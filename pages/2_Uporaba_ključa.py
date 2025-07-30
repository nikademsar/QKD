import streamlit as st
import pandas as pd

def odstrani_sumnike(text):
    nadomestila = {
        'č': 'c', 'Č': 'C',
        'š': 's', 'Š': 'S',
        'ž': 'z', 'Ž': 'Z',
        'ć': 'c', 'Ć': 'c',
    }
    for znak, nadomestek in nadomestila.items():
        text = text.replace(znak, nadomestek)
    return text

st.set_page_config(page_title="Uporaba ključa", page_icon="🔐")

st.title("Uporaba ključa za šifriranje sporočila")

if "skupni_kljuc" not in st.session_state or not st.session_state["skupni_kljuc"]:
    st.warning("Najprej zaženi simulacijo v zavihku 'BB84 – Simulacija', da pridobiš ključ.")
    default_kljuc_str = ""
else:
    default_kljuc_str = ''.join(str(b) for b in st.session_state["skupni_kljuc"])

kljuc_urejen = st.text_area("Ročni vnos/urejanje ključa (v bitih 0 in 1)", value=default_kljuc_str, height=100)

with st.form("encryption_form"):
    besedilo = st.text_input("Sporočilo (ASCII znaki)", value="hello")
    submit = st.form_submit_button("Uporabi ključ")

if submit:
    kljuc_urejen = ''.join([c for c in kljuc_urejen if c in ['0', '1']])
    if not kljuc_urejen:
        st.warning("Vnesite vsaj en bit ključa za šifriranje.")
    else:
        # Posodobimo besedilo tako, da odstranimo šumnike
        besedilo_brez_sumnikov = odstrani_sumnike(besedilo)

        bit_besedila = ''.join(format(ord(znak), '08b') for znak in besedilo_brez_sumnikov)
        ponovljen_kljuc = kljuc_urejen * ((len(bit_besedila) // len(kljuc_urejen)) + 1)
        bit_kljuca = ponovljen_kljuc[:len(bit_besedila)]

        sifrirano_besedilo = ''
        analiza = []

        for i in range(len(bit_besedila)):
            b_bit = int(bit_besedila[i])
            k_bit = int(bit_kljuca[i])
            xor_bit = b_bit ^ k_bit
            sifrirano_besedilo += str(xor_bit)

            razlaga = "Ista bita → rezultat 0" if b_bit == k_bit else "Različna bita → rezultat 1"

            analiza.append({
                "Pozicija": i,
                "Bit sporočila": b_bit,
                "Bit ključa": k_bit,
                "XOR rezultat": xor_bit,
                "Razlaga": razlaga
            })

        try:
            sifrirani_znaki = ''.join(
                chr(int(sifrirano_besedilo[i:i+8], 2)) for i in range(0, len(sifrirano_besedilo), 8)
            )
        except:
            sifrirani_znaki = "(Neveljaven ASCII niz)"

        st.markdown("### 🔐 Šifrirano sporočilo")
        st.code(sifrirani_znaki, language="text")

        st.markdown("### 🧠 Razlaga bit po bit")
        df_analiza = pd.DataFrame(analiza)
        st.dataframe(df_analiza, use_container_width=True)

        st.markdown("---")
        st.info(
            "Vsak znak se pretvori v 8-bitno binarno obliko. Bit po bit se šifrira z uporabo ključa "
            "prek XOR operacije. Rezultat 0 pomeni enaka bita, 1 pomeni različna."
        )
