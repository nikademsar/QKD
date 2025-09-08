import streamlit as st
import random
import pandas as pd
import requests

st.set_page_config(page_title="BB84 Simulation", layout="wide")
st.title("BB84 Simulation")

# --- Default values ---
n = st.number_input("Number of photons (n)", min_value=1, max_value=10000, value=100, step=1)
eve_on = st.checkbox("Enable Eve", value=False)
quantum_noise_prob = st.slider("Quantum noise probability", 0.0, 0.1, 0.02, step=0.01)

# --- QRNG API ---
def get_quantum_bits(n):
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

# --- Helper: LED/bit truth table lookup ---
def table_outcome(alice_angle_deg, bob_basis):
    """
    Return (led, outcome_bit or 'Random') according to the provided truth table.
    bob_basis: 'rect' or 'diag'
    """
    # Use 0° for rectilinear lookup, 45° for diagonal lookup
    bob_lookup = 0 if bob_basis == "rect" else 45

    # Normalize Alice's diagonal 135° as -45° for the table keys
    a = alice_angle_deg % 180
    if a == 135:
        a = -45

    table = {
        (-45, 0): ("Both", "Random"),
        (-45, 45): ("Transmitted", 0),
        (0, 0): ("Transmitted", 0),
        (0, 45): ("Both", "Random"),
        (45, 0): ("Both", "Random"),
        (45, 45): ("Reflected", 1),
        (90, 0): ("Reflected", 1),
        (90, 45): ("Both", "Random"),
    }
    return table.get((a, bob_lookup), ("Both", "Random"))

# --- Simulation ---
if st.button("Run simulation"):
    quantum_bits = get_quantum_bits(n)
    quantum_bit_index = 0
    data = []

    for _ in range(n):
        # --- Alice ---
        alice_basis = random.choice(["rect", "diag"])
        alice_bit = random.choice([0, 1])

        # IMPORTANT: Align Alice's encoding with the truth table
        # rect: 0 -> 0°, 1 -> 90°  (already consistent)
        # diag: 0 -> 135°(-45°), 1 -> 45° (swapped to match the table bit mapping)
        alice_angle = {
            ("rect", 0): 0,
            ("rect", 1): 90,
            ("diag", 0): 135,
            ("diag", 1): 45,
        }[(alice_basis, alice_bit)]

        # --- Eve ---
        if eve_on:
            eve_basis = random.choice(["rect", "diag"])
            eve_angle = random.choice([0, 45, 90, 135])
            eve_same_basis = eve_basis == alice_basis
            # If Eve uses same basis, she forwards Alice's bit; else effectively randomizes
            eve_bit = alice_bit if eve_same_basis else random.choice([0, 1])
            bit_sent_to_bob = eve_bit
            basis_sent_to_bob = eve_basis
            angle_sent_to_bob = eve_angle
        else:
            bit_sent_to_bob = alice_bit
            basis_sent_to_bob = alice_basis
            angle_sent_to_bob = alice_angle

        # --- Bob ---
        bob_basis = random.choice(["rect", "diag"])
        bob_angle = {"rect": random.choice([0, 90]), "diag": random.choice([45, 135])}[bob_basis]

        # Determine LED/bit outcome by the truth table using the photon reaching Bob
        led, outcome = table_outcome(angle_sent_to_bob, bob_basis)

        if outcome == "Random":
            # For mismatched bases (per table), Bob's bit is random
            bob_bit_pre_noise = quantum_bits[quantum_bit_index]
            quantum_bit_index += 1
            bob_note = f"{led} – random outcome"
        else:
            bob_bit_pre_noise = outcome
            bob_note = f"{led} – deterministic outcome"

        # Apply quantum noise (flip with given probability)
        bob_bit = bob_bit_pre_noise
        if random.random() < quantum_noise_prob:
            bob_bit = 1 - bob_bit
            bob_note += " + quantum noise"

        bases_match = (basis_sent_to_bob == bob_basis)

        data.append({
            "Alice basis": alice_basis,
            "Bob basis": bob_basis,
            "Alice angle (°)": alice_angle,
            "Photon to Bob (°)": angle_sent_to_bob,
            "Bob angle (°)": bob_angle,
            "Alice bit": alice_bit,
            "Bob bit (pre-noise)": bob_bit_pre_noise,
            "Bob bit": bob_bit,
            "LED": led,
            "Outcome": "Random" if outcome == "Random" else "Deterministic",
            "Bases match": "Yes" if bases_match else "No",
            "Bob note": bob_note
        })

    df = pd.DataFrame(data)

    st.subheader("Simulation results")

    def highlight_bases(val):
        if val == "Yes":
            return "background-color: lightgreen; font-weight: bold"
        return ""

    def highlight_mismatched_bits(row):
        if row["Bases match"] == "Yes" and row["Alice bit"] != row["Bob bit"]:
            return ['background-color: violet' if col == "Bob bit" else '' for col in row.index]
        else:
            return ['' for _ in row.index]

    styled_df = df.style.map(highlight_bases, subset=["Bases match"])
    styled_df = styled_df.apply(highlight_mismatched_bits, axis=1)
    st.dataframe(styled_df, use_container_width=True)

    # --- Statistics ---
    st.subheader("Results analysis")

    # Only matching bases contribute to the sifted key
    matching_bases = df[df["Bases match"] == "Yes"]
    num_matches = len(matching_bases)

    # Correct means Alice bit == Bob bit (after noise) when bases match
    correct = (matching_bases["Alice bit"] == matching_bases["Bob bit"]).sum()
    mismatches = num_matches - correct

    st.markdown(f"""
- **Number of matching bases:** `{num_matches} / {n}`
- **Correctly received bits:** `{correct} / {num_matches if num_matches else 1}`
- **Mismatched bits:** `{mismatches} / {num_matches if num_matches else 1}`
""")

    if num_matches > 0:
        mismatch_rate = mismatches / num_matches
        st.markdown(f"- **Mismatch rate (QBER on sifted key):** `{mismatch_rate:.2%}`")

        # Expected error ~ quantum_noise_prob (since only matching bases are kept)
        expected_rate = quantum_noise_prob
        tolerance_warn = 0.02  # 2% over expected -> warn
        tolerance_alert = 0.05  # 5% over expected -> alert

        if mismatch_rate > expected_rate + tolerance_alert:
            st.error(f"Observed error exceeds noise by >{tolerance_alert:.0%} — possible Eve!")
        elif mismatch_rate > expected_rate + tolerance_warn:
            st.warning(f"Observed error exceeds noise by >{tolerance_warn:.0%} — noise spike or Eve.")
        else:
            st.success("Observed error consistent with configured noise — key likely secure.")
    else:
        st.info("Not enough matches for analysis.")

    # --- Shared key ---
    # Save only when Eve is off
    if not eve_on:
        shared_key = matching_bases["Alice bit"].tolist()
        st.session_state["shared_key"] = shared_key
        st.subheader("Shared key")
        st.code("".join(map(str, shared_key)), language="text")
        st.info("Key will be used for encryption.")
    else:
        st.info("Eve is enabled — key not saved.")
