# 3_Learning.py
import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="Learning – BB84", layout="wide")
st.title("Learning")

st.markdown(
    """
In this exercise you get a sequence of BB84 measurements **without noise and without Eve**.
Your task: for each row, enter what **Bob’s bit** would be in the ideal case. If result bit is random enter **r**.
"""
)

# -------------------------- Data generation --------------------------
POLARIZATIONS = [-45, 0, 45, 90]
BASIS = [0, 45]

# Map to expected bit based on your table
EXPECTED_TABLE = {
    (-45, 0): "r",
    (-45, 45): "0",
    (0, 0): "0",
    (0, 45): "r",
    (45, 0): "r",
    (45, 45): "1",
    (90, 0): "1",
    (90, 45): "r",
}

def generate_exercise(n: int):
    items = []
    for i in range(n):
        alice_angle = random.choice(POLARIZATIONS)
        bob_angle = random.choice(BASIS)

        expected = EXPECTED_TABLE[(alice_angle, bob_angle)]

        items.append(
            {
                "Seq #": i + 1,
                "Alice angle (°)": alice_angle,
                "Bob angle (°)": bob_angle,
                "Your input (0/1/r)": "",
                "_expected": expected,
            }
        )
    return pd.DataFrame(items)

# -------------------------- UI --------------------------
col_a, col_b = st.columns([1, 1])
with col_a:
    n = st.number_input("Number of rows (n)", min_value=6, max_value=32, value=10, step=2)
    reset = st.button("Reset")

if "learning_df" not in st.session_state or reset:
    st.session_state.learning_df = generate_exercise(int(n))

# Editable table
edited_df = st.data_editor(
    st.session_state.learning_df.drop(columns=["_expected"]),
    use_container_width=True,
    hide_index=True,
    num_rows="fixed",
    key="learning_editor",
)

check = st.button("Check")

# -------------------------- Checking --------------------------
if check:
    results = []
    correct = 0
    total = 0
    base_df = st.session_state.learning_df

    for i in range(len(base_df)):
        expected = base_df.iloc[i]["_expected"]
        user_raw = str(edited_df.iloc[i]["Your input (0/1/r)"]).strip().lower()

        total += 1
        if user_raw == expected:
            verdict = "✔ correct"
            correct += 1
        else:
            verdict = "✘ wrong"

        results.append(
            {
                "Seq #": base_df.iloc[i]["Seq #"],
                "Alice angle (°)": base_df.iloc[i]["Alice angle (°)"],
                "Bob angle (°)": base_df.iloc[i]["Bob angle (°)"],
                "Your input": user_raw,
                "Expected Bob bit": expected,
                "Result": verdict,
            }
        )

    res_df = pd.DataFrame(results)
    st.subheader("Results")
    st.dataframe(res_df, use_container_width=True, hide_index=True)

    st.markdown(f"**Scored:** {correct} / {total} | **Accuracy:** {correct/total:.0%}")
