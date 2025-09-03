# app.py
# Run: pip install streamlit
# then: streamlit run app.py

import streamlit as st
import json
import datetime
import pandas as pd

st.set_page_config(page_title="Polarisation Drift Testing Protocol", layout="wide")

PROTOCOL_TITLE = "Polarisation Drift Testing Protocol"

protocol = {
    "title": PROTOCOL_TITLE,
    "1 Introduction and Scope": {
        "text": (
            "This protocol defines the methodology for systematically testing polarisation drift in a Quantum Key "
            "Distribution (QKD) system. The testing campaign is divided into three categories:\n\n"
            "1. Long-term mechanical/environmental drift\n"
            "2. Short-term transient drift\n"
            "3. Atmospheric drift effects\n\n"
            "The purpose is to quantify the effect of each category on QBER and polarisation parameters, and to validate "
            "a compensation model under controlled and repeatable conditions."
        )
    },
    "2 Definitions and Metrics": {
        "bullets": [
            "QBER: Quantum Bit Error Rate",
            "Δθ: Polarisation angle deviation from nominal (degrees)",
            "DOP: Degree of Polarisation",
            "SNR: Signal-to-Noise Ratio of detected signal",
            "Drift rate: Rate of polarisation change per unit time (°/s or °/min)",
            "Correlation metrics: Relationship between environmental factors (temperature, vibration, humidity) and QBER",
            "Photon detection rate: Counts per second at the detectors",
            "Jitter: Timing variation in photon arrival (if time-coded pulses are used)"
        ],
        "note": "All angles shall be expressed in degrees (°), and environmental metrics in SI units."
    },
    "3 Test Categories and Procedures": {
        "3.1 Long-Term Drift": {
            "objective": "Simulate permanent or semi-permanent alignment deviations due to mechanical stress or component shifts.",
            "test_parameters": [
                "Alice polarisation angle (Δθ = ±1–5°)",
                "Bob polarisation angle (Δθ = ±1–5°)",
                "Alice/Bob horizontal angular misalignment",
                "Laser x/z tilt (±2°)",
                "Detector 44 x/z tilt (±2°)"
            ],
            "procedure": [
                "Baseline QBER shall be measured with all optical components aligned.",
                "Each parameter shall be incrementally varied while others remain fixed.",
                "For each configuration, the system shall record QBER, Δθ, and environmental metrics and repeat the transmission N times to ensure repeatability.",
                "Results shall be logged and used for model validation."
            ],
            "notes": [
                "Conduct tests under ambient, temperature-varied, and humidity-varied conditions.",
                "Automate component adjustments where possible for precision and repeatability."
            ],
            "requirements": [
                ("REQ-LTD-001", "The system shall allow mechanical adjustment of each optical component in at least 0.5° increments."),
                ("REQ-LTD-002", "The system shall record QBER and polarisation shift for each configuration."),
                ("REQ-LTD-003", "The long-term drift test shall be performed under both ambient and temperature-varied conditions.")
            ]
        },
        "3.2 Short-Term Drift": {
            "objective": "Measure QBER impact of transient misalignments due to vibration or thermal pulses.",
            "events": [
                "Controlled table vibration (e.g., by shaker)",
                "Brief directional force on components (e.g., tap or cable tug)",
                "Localised heating (e.g., hot air source)"
            ],
            "procedure": [
                "Initiate each disturbance for ≤30 seconds.",
                "QBER shall be recorded before, during, and after each event.",
                "The system shall be allowed to passively return to baseline.",
                "Each event shall be repeated 5 times to assess repeatability."
            ],
            "notes": [
                "Include vibration amplitude and frequency details.",
                "Define acceptable QBER tolerance for transient events.",
                "Synchronize environmental metrics with optical measurements."
            ],
            "requirements": [
                ("REQ-STD-001", "The system shall sample QBER at a minimum frequency of 10 Hz during transient events."),
                ("REQ-STD-002", "The system shall return to within 10% of baseline QBER within 5 minutes after disturbance."),
                ("REQ-STD-003", "Environmental metrics (vibration, temperature) shall be logged synchronously with optical data.")
            ]
        },
        "3.3 Atmospheric Drift": {
            "objective": "Quantify polarisation drift caused by humidity, vapour, particulates, and light interference.",
            "test_chamber": "A sealed plexiglass enclosure with optical access shall be used for all atmospheric tests.",
            "scenarios": [
                "Baseline: clean, dry air",
                "Water vapour: RH levels from 20% to 95%",
                "Particulates: aerosol fog or smoke",
                "Light pollution: controlled visible light spectrum illumination"
            ],
            "procedure": [
                "Baseline QBER, DOP, and Δθ shall be measured in dry conditions.",
                "One factor at a time shall be introduced while maintaining all others constant.",
                "For each environmental condition: record QBER, Δθ, DOP and repeat measurements for N test messages.",
                "Each factor shall be tested at 3–5 intensity levels (e.g., RH%, fog density).",
                "Test combined scenarios (humidity + light + particulates) to observe interactions."
            ],
            "requirements": [
                ("REQ-ATM-001", "The test chamber shall allow controlled introduction of water vapour and particulates."),
                ("REQ-ATM-002", "The system shall measure polarisation angle and DOP before and after each atmospheric variation."),
                ("REQ-ATM-003", "Light interference shall be introduced in at least three intensity levels (e.g., 100 lx, 300 lx, 500 lx).")
            ]
        }
    },
    "4 Control Test Procedure": {
        "objective": "Confirm system repeatability under unchanged, ideal conditions.",
        "procedure": [
            "With all variables at nominal values, transmit N test messages and log QBER.",
            "Repeat twice daily for 3 days."
        ],
        "requirement": ("REQ-CTRL-001", "The control QBER shall not vary by more than ±5% across all control trials."),
        "notes": [
            "Include calibration points before and after each control test.",
            "Use trend plots for QBER and Δθ over time to detect anomalies."
        ]
    },
    "5 Verification and Analysis": {
        "text": "Each requirement shall be verified as follows:",
        "table": [
            ("REQ-LTD-001", "Inspection + Functional Test"),
            ("REQ-STD-002", "Test + Time Series Analysis"),
            ("REQ-ATM-002", "Measurement Comparison"),
            ("REQ-CTRL-001", "Statistical Analysis")
        ]
    }
}

# ---------------- UI ----------------
st.title(PROTOCOL_TITLE)
st.write("Interaktivna aplikacija za izvajanje in dokumentacijo testov polarisation drift v QKD sistemih.")
st.markdown("---")

# Sidebar navigation
st.sidebar.header("Navigacija")
sections = [
    "Introduction & Scope",
    "Definitions & Metrics",
    "Long-Term Drift",
    "Short-Term Drift",
    "Atmospheric Drift",
    "Control Tests",
    "Verification & Analysis",
    "Export / Save"
]
sel = st.sidebar.radio("Pojdi na odsek:", sections)

# Quick controls
st.sidebar.markdown("### Hitri parametri testa")
N_repeat = st.sidebar.number_input("N (ponovitve za konfiguracijo):", min_value=1, max_value=1000, value=5)
SEQ_SECONDS = st.sidebar.number_input("Časovni okvir (s) med meritvami (če relevantno):", min_value=0.1, max_value=3600.0, value=1.0)
st.sidebar.markdown("---")

# Verification checklist storage
if "verifications" not in st.session_state:
    # Create DataFrame of all requirements
    req_list = []
    for sec_key, sec_val in protocol["3 Test Categories and Procedures"].items():
        for req in sec_val.get("requirements", []):
            req_list.append({"ReqID": req[0], "Text": req[1], "Status": False, "Comment": ""})
    # Control and others
    control_req = protocol["4 Control Test Procedure"].get("requirement")
    if control_req:
        req_list.append({"ReqID": control_req[0], "Text": control_req[1], "Status": False, "Comment": ""})
    verif_tbl = pd.DataFrame(req_list)
    st.session_state.verifications = verif_tbl

# Helper to display a requirement table with checkboxes
def show_requirements_table():
    st.subheader("Seznam zahtev (requirements)")
    df = st.session_state.verifications.copy()
    edited = df.copy()
    cols = st.columns([1,6,1,3])
    with cols[0]:
        st.markdown("**ID**")
    with cols[1]:
        st.markdown("**Opis**")
    with cols[2]:
        st.markdown("**Opravljen**")
    with cols[3]:
        st.markdown("**Komentar**")

    for i, row in df.iterrows():
        c1, c2, c3, c4 = st.columns([1,6,1,3])
        c1.write(row["ReqID"])
        c2.write(row["Text"])
        chk = c3.checkbox(" ", value=row["Status"], key=f"req_{row['ReqID']}")
        comment = c4.text_input("", value=row["Comment"], key=f"com_{row['ReqID']}")
        edited.at[i, "Status"] = chk
        edited.at[i, "Comment"] = comment

    st.session_state.verifications = edited

# Main content
if sel == "Introduction & Scope":
    st.header("1. Introduction and Scope")
    st.write(protocol["1 Introduction and Scope"]["text"])

elif sel == "Definitions & Metrics":
    st.header("2. Definitions and Metrics")
    for b in protocol["2 Definitions and Metrics"]["bullets"]:
        st.write(f"- {b}")
    st.info(protocol["2 Definitions and Metrics"]["note"])

elif sel == "Long-Term Drift":
    v = protocol["3 Test Categories and Procedures"]["3.1 Long-Term Drift"]
    st.header("3.1 Long-Term Drift")
    st.subheader("Objective")
    st.write(v["objective"])
    st.subheader("Test Parameters")
    for p in v["test_parameters"]:
        st.write(f"- {p}")
    st.subheader("Procedure")
    for p in v["procedure"]:
        st.write(f"- {p}")
    st.subheader("Notes")
    for n in v["notes"]:
        st.write(f"- {n}")
    st.subheader("Requirements")
    for req in v["requirements"]:
        st.write(f"- **{req[0]}**: {req[1]}")

    with st.expander("Run / Log a Long-Term Test"):
        st.write("Preprosta forma za beleženje ene serije dolgoročnega testa (lokalno v seji).")
        c1, c2, c3 = st.columns(3)
        with c1:
            delta_theta = st.number_input("Δθ (°):", min_value=-10.0, max_value=10.0, value=1.0, step=0.5)
            repeats = st.number_input("Repeat N times:", min_value=1, max_value=1000, value=N_repeat)
        with c2:
            temp = st.number_input("Temperature (°C):", value=22.0)
            humidity = st.number_input("Humidity (%):", value=50.0)
        with c3:
            note = st.text_input("Notes / Observations:")
        if st.button("Log measurement"):
            if "log" not in st.session_state:
                st.session_state.log = []
            st.session_state.log.append({
                "type": "long-term",
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "delta_theta": delta_theta,
                "repeats": repeats,
                "temp": temp,
                "humidity": humidity,
                "note": note
            })
            st.success("Measurement logged (in session).")

elif sel == "Short-Term Drift":
    v = protocol["3 Test Categories and Procedures"]["3.2 Short-Term Drift"]
    st.header("3.2 Short-Term Drift")
    st.subheader("Objective")
    st.write(v["objective"])
    st.subheader("Test Events")
    for p in v["events"]:
        st.write(f"- {p}")
    st.subheader("Procedure")
    for p in v["procedure"]:
        st.write(f"- {p}")
    st.subheader("Notes")
    for n in v["notes"]:
        st.write(f"- {n}")
    st.subheader("Requirements")
    for req in v["requirements"]:
        st.write(f"- **{req[0]}**: {req[1]}")

    with st.expander("Run / Log a Short-Term Event"):
        st.write("Log a transient event (≤30 s) and capture pre/during/post notes.")
        event = st.selectbox("Event type:", v["events"])
        duration = st.slider("Duration (s):", min_value=1, max_value=60, value=10)
        pre_qber = st.number_input("QBER before (%):", value=0.5, min_value=0.0, step=0.01)
        during_qber = st.number_input("QBER during (%):", value=5.0, min_value=0.0, step=0.01)
        post_qber = st.number_input("QBER after (%):", value=0.6, min_value=0.0, step=0.01)
        if st.button("Log short-term event"):
            if "log" not in st.session_state:
                st.session_state.log = []
            st.session_state.log.append({
                "type": "short-term",
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "event": event,
                "duration": duration,
                "pre_qber": pre_qber,
                "during_qber": during_qber,
                "post_qber": post_qber
            })
            st.success("Event logged (in session).")

elif sel == "Atmospheric Drift":
    v = protocol["3 Test Categories and Procedures"]["3.3 Atmospheric Drift"]
    st.header("3.3 Atmospheric Drift")
    st.subheader("Objective & Chamber")
    st.write(v["objective"])
    st.write(v["test_chamber"])
    st.subheader("Scenarios")
    for s in v["scenarios"]:
        st.write(f"- {s}")
    st.subheader("Procedure & Notes")
    for p in v["procedure"]:
        st.write(f"- {p}")
    st.subheader("Requirements")
    for req in v["requirements"]:
        st.write(f"- **{req[0]}**: {req[1]}")

    with st.expander("Run / Log an Atmospheric Scenario"):
        scen = st.selectbox("Scenario:", v["scenarios"])
        intensity = st.slider("Intensity level (1-5):", 1, 5, 3)
        measure_qber = st.number_input("Measured QBER (%):", 0.0, 100.0, 1.0)
        measure_dop = st.number_input("Measured DOP (%):", 0.0, 100.0, 90.0)
        if st.button("Log atmospheric measurement"):
            if "log" not in st.session_state:
                st.session_state.log = []
            st.session_state.log.append({
                "type": "atmospheric",
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "scenario": scen,
                "intensity": intensity,
                "qber": measure_qber,
                "dop": measure_dop
            })
            st.success("Atmospheric measurement logged (in session).")

elif sel == "Control Tests":
    st.header("4 Control Test Procedure")
    st.write(protocol["4 Control Test Procedure"]["objective"])
    st.subheader("Procedure")
    for p in protocol["4 Control Test Procedure"]["procedure"]:
        st.write(f"- {p}")
    st.write("Requirement:")
    req = protocol["4 Control Test Procedure"]["requirement"]
    st.write(f"- **{req[0]}**: {req[1]}")
    st.subheader("Notes")
    for n in protocol["4 Control Test Procedure"]["notes"]:
        st.write(f"- {n}")

    with st.expander("Run Control Test"):
        n_msgs = st.number_input("N test messages per run:", min_value=1, max_value=100000, value=100)
        repeats_day = st.number_input("Repeats per day:", min_value=1, max_value=10, value=2)
        days = st.number_input("Number of days:", min_value=1, max_value=30, value=3)
        if st.button("Log control run"):
            if "log" not in st.session_state:
                st.session_state.log = []
            st.session_state.log.append({
                "type": "control",
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "n_msgs": int(n_msgs),
                "repeats_day": int(repeats_day),
                "days": int(days)
            })
            st.success("Control run parameters logged (in session).")

elif sel == "Verification & Analysis":
    st.header("5 Verification and Analysis")
    st.write(protocol["5 Verification and Analysis"]["text"])
    st.subheader("Verification Matrix")
    verif_df = pd.DataFrame(protocol["5 Verification and Analysis"]["table"], columns=["ReqID", "Verification Method"])
    st.table(verif_df)
    st.markdown("### Requirement checklist")
    show_requirements_table()

    st.markdown("### Export verification results")
    vf = st.session_state.verifications.copy()
    csv = vf.to_csv(index=False).encode("utf-8")
    st.download_button("Download verification CSV", data=csv, file_name="verification_results.csv", mime="text/csv")
    st.download_button("Download verification JSON", data=vf.to_json(orient="records"), file_name="verification_results.json", mime="application/json")

elif sel == "Export / Save":
    st.header("Export / Save")
    st.subheader("Export full protocol")
    md_lines = [f"# {PROTOCOL_TITLE}\n"]
    # Build markdown representation
    md_lines.append("## 1. Introduction and Scope\n")
    md_lines.append(protocol["1 Introduction and Scope"]["text"] + "\n\n")
    md_lines.append("## 2. Definitions and Metrics\n")
    for b in protocol["2 Definitions and Metrics"]["bullets"]:
        md_lines.append(f"- {b}\n")
    md_lines.append("\n## 3. Test Categories and Procedures\n")
    for k, v in protocol["3 Test Categories and Procedures"].items():
        md_lines.append(f"### {k}\n")
        for kk, vv in v.items():
            if isinstance(vv, list):
                md_lines.append(f"- {kk}:\n")
                for item in vv:
                    md_lines.append(f"  - {item}\n")
            else:
                md_lines.append(f"{kk}: {vv}\n")
        md_lines.append("\n")
    md = "".join(md_lines)

    st.download_button("Download protocol as Markdown", data=md, file_name="polarisation_drift_protocol.md", mime="text/markdown")
    st.download_button("Download protocol as JSON", data=json.dumps(protocol, indent=2), file_name="polarisation_drift_protocol.json", mime="application/json")

    st.subheader("Session logs (measurements/events you've logged)")
    logs = st.session_state.get("log", [])
    if logs:
        st.write(pd.DataFrame(logs))
        st.download_button("Download session logs (CSV)", data=pd.DataFrame(logs).to_csv(index=False).encode("utf-8"),
                           file_name="session_logs.csv", mime="text/csv")
    else:
        st.info("Ni še zabeleženih meritvah (session logs). Uporabi odseke Long-Term, Short-Term ali Atmospheric za beleženje.")

st.markdown("---")
st.caption("Aplikacija: prototip za pomoč pri izvajanju in dokumentaciji testov polarisation drift. Ne nadomešča uradne laboratorijske opreme ali postopkov.")
