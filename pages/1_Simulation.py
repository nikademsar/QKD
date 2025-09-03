import streamlit as st
import random
import pandas as pd

st.set_page_config(page_title="BB84 Simulation", layout="wide")
st.title("BB84 Simulation")

# --- Default values ---
n = st.number_input("Number of photons (n)", min_value=1, max_value=10000, value=100, step=1)
eve_on = st.checkbox("Enable Eve", value=False)
quantum_noise_prob = st.slider("Quantum noise probability", 0.0, 0.1, 0.02, step=0.01)

# --- LED / Bit table ---
LED_TABLE = {
    (-45, 0): ("Both", "r"),
    (-45, 45): ("Transmitted", "0"),
    (0, 0): ("Transmitted", "0"),
    (0, 45): ("Both", "r"),
    (45, 0): ("Both", "r"),
    (45, 45): ("Reflected", "1"),
    (90, 0): ("Reflected", "1"),
    (90, 45): ("Both", "r"),
}

# --- QRNG / Random bits ---
def get_quantum_bits(n):
    return [random.randint(0, 1) for _ in range(n)]

# --- Simulation ---
if st.button("Run simulation"):
    quantum_bits = get_quantum_bits(n)
    quantum_bit_index = 0
    data = []

    for _ in range(n):
        # --- Alice ---
        alice_angle = random.choice([-45, 0, 45, 90])
        bob_basis = random.choice([0, 45])

        led, expected_bit = LED_TABLE[(alice_angle, bob_basis)]

        # --- Quantum noise or random measurement ---
        if expected_bit == "r":
            bob_bit = str(quantum_bits[quantum_bit_index])
            quantum_bit_index += 1
            note = "Random measurement"
        else:
            bob_bit = expected_bit
            if random.random() < quantum_noise_prob:
                bob_bit = "1" if expected_bit == "0" else "0"
                note = "Quantum noise flipped bit"
            else:
                note = "Correct measurement"

        # --- Eve ---
        if eve_on:
            note += " | Eve enabled"

        data.append({
            "Alice polarization": alice_angle,
            "Bob basis": bob_basis,
            "Which LED lights up": led,
            "Expected Bob bit": expected_bit,
            "Bob bit": bob_bit,
            "Note": note
        })

    df = pd.DataFrame(data)

    # --- Add Bases match column ---
    df["Bases match"] = df["Expected Bob bit"].apply(lambda x: "Yes" if x != "r" else "No")

    # --- Highlight functions ---
    def highlight_bases(val):
        if val == "Yes":
            return "background-color: lightgreen; font-weight: bold"
        return ""

    def highlight_mismatched_bits(row):
        if row["Bases match"] == "Yes" and row["Expected Bob bit"] != row["Bob bit"]:
            return ['background-color: violet' if col == "Bob bit" else '' for col in row.index]
        else:
            return ['' for _ in row.index]

    styled_df = df.style.map(highlight_bases, subset=["Bases match"])
    styled_df = styled_df.apply(highlight_mismatched_bits, axis=1)

    st.subheader("Simulation results")
    st.dataframe(styled_df, use_container_width=True)

    # --- Statistics ---
    correct_bits = df[df["Expected Bob bit"] != "r"]
    num_total = len(correct_bits)
    num_correct = (correct_bits["Expected Bob bit"] == correct_bits["Bob bit"]).sum()
    st.markdown(f"- **Correct bits:** {num_correct} / {num_total} ({num_correct/num_total:.2%})")

    # --- Shared key (only if Eve is off) ---
    if not eve_on:
        shared_key = df["Bob bit"].tolist()
        st.subheader("Shared key")
        st.code("".join(shared_key), language="text")
        st.info("Key will be used for encryption.")
    else:
        st.info("Eve is enabled – key not saved.")
