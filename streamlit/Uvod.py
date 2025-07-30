import streamlit as st

st.title("QKD - BB84 Simulacija")

st.markdown("""
### 1. Igralci:

- **Alice**: pošilja fotone (kvante svetlobe), vsak je polariziran v določeni smeri (0°, 45°, 90°, 135°).
- **Bob**: meri polarizacijo z naključno izbranim polarizatorjem (0° ali 45°).
- **Opcijsko Eve**: prestreže fotone in jih meri ter ponovno pošilja (če želiš simulirati napad).

---

### 2. Koraki v simulaciji:

1. Alice naključno izbere bazo (rectilinear ali diagonalno) in bit (0 ali 1), kar določa polarizacijo:
   - 0° (bit 0, rectilinear)
   - 90° (bit 1, rectilinear)
   - 45° (bit 0, diagonal)
   - 135° (bit 1, diagonal)

2. Bob naključno izbere bazo (0° ali 45° polarizator) in izvede meritev.

3. Če je Bob izbral isto bazo kot Alice, dobi pravilen bit.
   - Primer: Alice pošlje 45°, Bob meri z 45° → dobi 0.
   - Če pa je baza različna, je rezultat naključen.

4. Na koncu Alice in Bob primerjata baze (prek javnega kanala), in obdržita le tiste bite, kjer sta imela ujemajoče baze.

---

### Kaj pričakovati od rezultatov glede na kote polarizatorjev

Če v tvoji aplikaciji ti vpišeš kot Bobovega polarizatorja in dobiš povratno informacijo, ali si "zadel" bit, potem program simulira naslednje:

- Če je tvoj kot **ujemajoč z bazo Alice**, potem pričakuješ pravilen bit.
- Če je različen, potem bit dobiš z verjetnostjo 50%.

| Alice polarizacija | Alice baza     | Bob kot (vnešen) | Rezultat               |
|--------------------|---------------|------------------|-----------------------|
| 0°                 | rectilinear   | 0°               | pravilno (bit 0)       |
| 0°                 | rectilinear   | 45°              | naključno (0 ali 1)    |
| 45°                | diagonal      | 45°              | pravilno (bit 0)       |
| 45°                | diagonal      | 0°               | naključno              |
| 90°                | rectilinear   | 0°               | pravilno (bit 1)       |
| 135°               | diagonal      | 45°              | pravilno (bit 1)       |

""")
