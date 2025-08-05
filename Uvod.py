import streamlit as st

st.title("QKD - BB84 Simulacija")

st.markdown("""
### Kaj je kvantna distribucija ključa (QKD)?

**Kvantna distribucija ključa** (QKD, angl. *Quantum Key Distribution*) je metoda, s katero dve osebi (običajno imenovani Alice in Bob) delita skrivni šifrirni ključ preko kvantnega kanala. Posebnost QKD je, da zagotavlja **informacijsko varnost**, saj temelji na zakonih **kvantne mehanike** in ne le na matematičnih predpostavkah.

* V primeru prestrezanja (npr. s strani Eve) sistem to zazna, ker **kvantnih stanj ni mogoče meriti brez motenja**.
* Temeljni pojmi:

  * **Superpozicija**: kvantni delec (npr. foton) lahko obstaja v več stanjih hkrati.
  * **Meritev poruši stanje**: ko nekdo izmeri kvantni delec, ta "kolapsira" v eno izmed možnosti.
  * **No-cloning theorem**: kvantnih stanj ni mogoče kopirati brez napake.

---

### Protokol BB84 – koraki natančno

BB84 je prvi in najbolj znan QKD protokol, ki sta ga razvila **Charles Bennett** in **Gilles Brassard** leta 1984.

#### Korak 1: Alice generira naključne bite in baze

* Za vsak bit naključno izbere:

  * **Bit**: `0` ali `1`
  * **Bazo**:

    * **Rectilinear** (|, −): 0° ali 90°
    * **Diagonal** (/ , \\): 45° ali 135°
* Alice torej vsakič pošlje foton z eno od **štirih možnih polarizacij**:

  * `0` → 0°, 45°
  * `1` → 90°, 135°

#### Korak 2: Alice pošlje fotone po kvantnem kanalu

* Vsak foton potuje skozi **kvantni kanal** do Boba.
* Kvantna lastnost: foton "nosi" polarizacijo, vendar se ne more gledati, ne da bi se spremenil.

#### Korak 3: Bob meri fotone

* Bob za vsak foton naključno izbere eno bazo (rectilinear ali diagonal).
* Če izbere isto bazo kot Alice:

  * **Meritev je pravilna** → dobi enak bit.
* Če izbere napačno bazo:

  * **Meritev je naključna** → z 50 % verjetnostjo dobi pravilen ali napačen bit.

#### Korak 4: Primerjava baz

* Po meritvah Alice in Bob **javnosti razkrijeta, katere baze** sta uporabila (ne pa vrednosti bitov).
* Obdržita le tiste bite, kjer sta imela **ujemajočo bazo**.

  * To imenujemo **surovi ključ** (*raw key*).

#### Korak 5: Odkrivanje Eve (opcija)

* Če Eve prisluškuje, mora **izvesti meritev** → a ne ve, katero bazo izbrati.
* Posledično:

  * V kvantnih meritev vnaša napake.
  * Alice in Bob lahko preverita **napako v vzorcu** ključa.
  * Če napaka presega določen prag → **prisluškovanje je zaznano**.

#### Korak 6: Korekcija napak in ekstrakcija ključa

* Alice in Bob popravita morebitne napake (npr. z algoritmi ECC).
* Uporabita **privacy amplification** – postopek, ki zmanjša vpliv morebitno prestreženih bitov.

---

### Zakaj BB84 deluje?

BB84 deluje zaradi treh ključnih kvantnih zakonitosti:

1. **Meritev poruši kvantno stanje**
2. **Ne moremo razlikovati kvantnih stanj brez znanja baze**
3. **Ni mogoče klonirati kvantnega stanja brez napake**

Zaradi tega lahko Alice in Bob zaznata vsako prisluškovanje in s tem zagotovita **nepogojno varnost** (v teoriji).

---

### Primer simulacije:

| Alice polarizacija | Alice baza  | Bob baza         | Rezultat            |
| ------------------ | ----------- | ---------------- | ------------------- |
| 0°                 | rectilinear | rectilinear (0°) | pravilno (bit 0)    |
| 0°                 | rectilinear | diagonal (45°)   | naključno (0 ali 1) |
| 45°                | diagonal    | rectilinear (0°) | naključno (0 ali 1) |
| 45°                | diagonal    | diagonal (45°)   | pravilno (bit 0)    |
| 90°                | rectilinear | rectilinear (0°) | pravilno (bit 1)    |
| 90°                | rectilinear | diagonal (45°)   | naključno (0 ali 1) |
| 135°               | diagonal    | rectilinear (0°) | naključno (0 ali 1) |
| 135°               | diagonal    | diagonal (45°)   | pravilno (bit 1)    |

""")
