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

# --- Simulation ---
if st.button("Run simulation"):
    quantum_bits = get_quantum_bits(n)
    quantum_bit_index = 0
    data = []

    for _ in range(n):
        # --- Alice ---
        alice_basis = random.choice(["rect", "diag"])
        alice_bit = random.choice([0, 1])
        alice_angle = {("rect", 0): 0, ("rect", 1): 90, ("diag", 0): 45, ("diag", 1): 135}[(alice_basis, alice_bit)]

        # --- Eve ---
        if eve_on:
            eve_basis = random.choice(["rect", "diag"])
            eve_angle = random.choice([0, 45, 90, 135])
            eve_same_basis = eve_basis == alice_basis
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
        bases_match = basis_sent_to_bob == bob_basis

        if bases_match:
            bob_bit = bit_sent_to_bob
            if random.random() < quantum_noise_prob:
                bob_bit = 1 - bob_bit  # Noise flips the bit
                bob_note = "Bases match – quantum noise"
            else:
                bob_note = "Bases match – successful measurement"
        else:
            bob_bit = quantum_bits[quantum_bit_index]
            quantum_bit_index += 1
            bob_note = "Bases differ – random measurement"

        data.append({
            "Alice angle (°)": alice_angle,
            "Alice bit": alice_bit,
            "Alice basis": alice_basis,
            "Eve enabled": "Yes" if eve_on else "No",
            "Eve basis": eve_basis if eve_on else None,
            "Eve bit": eve_bit if eve_on else None,
            "Bob angle (°)": bob_angle,
            "Bob basis": bob_basis,
            "Bases match": "Yes" if bases_match else "No",
            "Bob bit": bob_bit,
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
    matching_bases = df[df["Bases match"] == "Yes"]
    correct = (matching_bases["Alice bit"] == matching_bases["Bob bit"]).sum()
    num_matches = len(matching_bases)
    mismatches = num_matches - correct

    st.subheader("Results analysis")
    st.markdown(f"""
    - **Number of matching bases:** `{num_matches} / {n}`
    - **Correctly received bits:** `{correct} / {num_matches}`
    - **Mismatched bits:** `{mismatches} / {num_matches}`
""")

    if num_matches > 0:
        mismatch_rate = mismatches / num_matches
        st.markdown(f"- **Mismatch rate:** `{mismatch_rate:.2%}`")

        if mismatch_rate > 0.2:
            st.error("High mismatch rate – possible presence of Eve!")
        elif mismatch_rate > 0.11:
            st.warning("Increased error rate – noise or Eve.")
        else:
            st.success("Low error rate – key is secure.")
    else:
        st.info("Not enough matches for analysis.")

    # --- Shared key ---
    if not eve_on:
        shared_key = matching_bases["Alice bit"].tolist()
        st.session_state["shared_key"] = shared_key
        st.subheader("Shared key")
        st.code("".join(map(str, shared_key)), language="text")
        st.info("Key will be used for encryption.")
    else:
        st.info("Eve is enabled – key not saved.")
