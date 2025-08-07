import streamlit as st
import pandas as pd

def remove_accents(text):
    replacements = {
        'č': 'c', 'Č': 'C',
        'š': 's', 'Š': 'S',
        'ž': 'z', 'Ž': 'Z',
        'ć': 'c', 'Ć': 'c',
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return text

st.set_page_config(page_title="Key Usage")

st.title("Using the Key for Message Encryption")

if "shared_key" not in st.session_state or not st.session_state["shared_key"]:
    st.warning("Please first run the simulation in the 'BB84 – Simulation' tab to obtain the key.")
    default_key_str = ""
else:
    default_key_str = ''.join(str(b) for b in st.session_state["shared_key"])

edited_key = st.text_area("Manual input/edit key (bits 0 and 1)", value=default_key_str, height=100)

with st.form("encryption_form"):
    message = st.text_input("Message (ASCII characters)", value="hello")
    submit = st.form_submit_button("Use key")

if submit:
    edited_key = ''.join([c for c in edited_key if c in ['0', '1']])
    if not edited_key:
        st.warning("Please enter at least one bit of key for encryption.")
    else:
        # Update the message by removing accented characters
        message_no_accents = remove_accents(message)

        message_bits = ''.join(format(ord(ch), '08b') for ch in message_no_accents)
        repeated_key = edited_key * ((len(message_bits) // len(edited_key)) + 1)
        key_bits = repeated_key[:len(message_bits)]

        encrypted_bits = ''
        analysis = []

        for i in range(len(message_bits)):
            m_bit = int(message_bits[i])
            k_bit = int(key_bits[i])
            xor_bit = m_bit ^ k_bit
            encrypted_bits += str(xor_bit)

            explanation = "Same bits → result 0" if m_bit == k_bit else "Different bits → result 1"

            analysis.append({
                "Position": i,
                "Message bit": m_bit,
                "Key bit": k_bit,
                "XOR result": xor_bit,
                "Explanation": explanation
            })

        try:
            encrypted_chars = ''.join(
                chr(int(encrypted_bits[i:i+8], 2)) for i in range(0, len(encrypted_bits), 8)
            )
        except:
            encrypted_chars = "(Invalid ASCII string)"

        st.markdown("### 🔐 Encrypted message")
        st.code(encrypted_chars, language="text")

        st.markdown("### 🧠 Bit-by-bit explanation")
        df_analysis = pd.DataFrame(analysis)
        st.dataframe(df_analysis, use_container_width=True)

        st.markdown("---")
        st.info(
            "Each character is converted to an 8-bit binary form. Bit by bit encryption is done using the key "
            "via XOR operation. Result 0 means bits are the same, 1 means bits are different."
        )
