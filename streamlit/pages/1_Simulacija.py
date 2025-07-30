import streamlit as st
import random
import pandas as pd

st.set_page_config(page_title="BB84 Simulacija z Eve", layout="wide")
st.title("BB84 – Simulacija z več fotoni in detekcijo Eve")

n = st.number_input("Število fotonov (n)", min_value=1, max_value=100, value=100, step=1)
eve_on = st.checkbox("Vklopi Eve", value=False)

if st.button("Zaženi simulacijo"):
    data = []

    for _ in range(n):
        kot_alice = random.choice([0, 45, 90, 135])
        bit_alice = 0 if kot_alice in [0, 45] else 1
        baza_alice = "rect" if kot_alice in [0, 90] else "diag"

        if eve_on:
            kot_eve = random.choice([0, 45, 90, 135])
            baza_eve = "rect" if kot_eve in [0, 90] else "diag"
            enaka_baza_eve = baza_eve == baza_alice
            bit_eve = bit_alice if enaka_baza_eve else random.choice([0,1])
            bit_predan_bobu = bit_eve
            baza_predana_bobu = baza_eve
            kot_predan_bobu = kot_eve
        else:
            bit_predan_bobu = bit_alice
            baza_predana_bobu = baza_alice
            kot_predan_bobu = kot_alice

        kot_bob = random.choice([0, 45, 90, 135])
        baza_bob = "rect" if kot_bob in [0, 90] else "diag"
        enaka_baza = baza_predana_bobu == baza_bob

        if enaka_baza:
            bit_bob = bit_predan_bobu
            opomba_bob = "Baze enake – uspešna meritev"
        else:
            bit_bob = random.choice([0, 1])
            opomba_bob = "Baze različne – naključna meritev"

        data.append({
            "Alice kot (°)": kot_alice,
            "Alice bit": bit_alice,
            "Baza Alice": baza_alice,
            "Eve vklopljena": "Da" if eve_on else "Ne",
            "Eve kot (°)": kot_eve if eve_on else None,
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

    ujemajoce = df[df["Ujemanje baz"] == "Da"]
    pravilni = (ujemajoce["Alice bit"] == ujemajoce["Bobov bit"]).sum()
    stevilo_ujemanj = len(ujemajoce)
    neusklajeni = stevilo_ujemanj - pravilni

    st.subheader("Analiza rezultatov")
    st.markdown(f"""
    - **Skupno število poslanih fotonov:** `{n}`  
        Število kvantnih bitov (fotonov), ki jih je Alice poslala Bobu.

    - **Število ujemanj baz med Alice in Bobom:** `{stevilo_ujemanj} / {n}`  
        Le kadar Alice in Bob izbereta enako bazo (npr. oba 0°, oba 45°), lahko pravilno interpretirata bit. Vsi ostali primeri se zavržejo.

    - **Pravilno prebranih bitov (ob ujemanju baz):** `{pravilni} / {stevilo_ujemanj}`  
        To pomeni, da je Bob izmeril isti bit kot ga je Alice poslala – le pri ujemanju baz je to relevantno. 

    - **Neusklajeni biti (pri ujemajočih bazah):** `{neusklajeni} / {stevilo_ujemanj}`  
        Neujemanje pomeni, da Bob ni prebral enakega bita kot Alice – to je lahko posledica prisluškovanja (npr. Eve) ali šuma.

    """)

    if stevilo_ujemanj > 0:
        delež_neusklajenih = neusklajeni / stevilo_ujemanj
        st.markdown(f"""
    - **Delež neusklajenih bitov (med ujemajočimi bazami):** `{delež_neusklajenih:.2%}`  
        Ta delež je ključen pri detekciji prisotnosti Eve. V idealnem primeru (brez prisluškovanja in brez šuma) bi pričakovali 0 % neusklajenosti.

    """)
        if delež_neusklajenih > 0.2:
            st.error("Visok delež neusklajenosti – možna prisotnost Eve!")
            st.markdown("""
        Ko tretja oseba (Eve) prestreže in ponovno pošlje fotone, vmeša svoje naključne baze.  
        To povzroči večjo verjetnost napačnih meritev pri Bobu.

        Prag **20 %** je običajen eksperimentalni prag za zaznavo prisluškovanja – če je presežen, je ključ **nevaren**.
                """)
        elif delež_neusklajenih > 0.11:
            st.warning("Povišan delež napak – možen vpliv Eve ali šuma.")
            st.markdown("""
        Delež neusklajenih bitov presega 11 %, kar pomeni, da bi lahko bila prisotna Eve ali pa je kanal zelo šumovit.

        Priporočamo dodatno preverjanje ali korekcijo napak, preden se ključ uporabi.
                """)
        else:
            st.success("Ni znakov prisluškovanja – ključ je najverjetneje varen.")
            st.markdown("""
        Nizek delež neusklajenih bitov pomeni, da Alice in Bob lahko nadaljujeta z uporabo izbranega ključa za šifriranje.  
        Čeprav obstaja možnost naključnega šuma, je vpliv zanemarljiv.
                """)
    else:
        st.info("Ni bilo dovolj ujemajočih baz za analizo prisotnosti Eve.")
        st.markdown("""
        Če se baze Alice in Boba ne ujemajo, primerjava bitov ni možna. V tem primeru se ne da sklepati o varnosti komunikacije.
        """)

    # Ključ shrani samo če Eve ni prisotna
    if not eve_on:
        skupni_kljuc = ujemajoce["Alice bit"].tolist()
        st.session_state["skupni_kljuc"] = skupni_kljuc
        st.markdown("---")
        st.subheader("Skupni ključ")
        st.code("".join(map(str, skupni_kljuc)), language="text")
        st.info("Ta ključ bo uporabljen za šifriranje na naslednjem zavihku.")
    else:
        st.info("Eve je vklopljena – ključ ni varen in ni shranjen.")
