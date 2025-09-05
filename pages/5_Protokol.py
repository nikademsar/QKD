import streamlit as st

st.set_page_config(page_title="Polarisation Drift Testing Protocol", layout="wide")

st.title("Polarisation Drift Testing Protocol")

st.header("1. Introduction and Scope")
st.write("""
This protocol defines the methodology for systematically testing polarisation drift in a Quantum Key Distribution (QKD) system. 
The testing campaign is divided into three categories:
1. Long-term mechanical/environmental drift  
2. Short-term transient drift  
3. Atmospheric drift effects  

The purpose is to quantify the effect of each category on QBER and polarisation parameters, 
and to validate a compensation model under controlled and repeatable conditions.
""")

st.header("2. Definitions and Metrics")
st.write("""
- **QBER**: Quantum Bit Error Rate  
- **Δθ**: Polarisation angle deviation from nominal (degrees)  
- **DOP**: Degree of Polarisation  
- **SNR**: Signal-to-Noise Ratio of detected signal  
- **Drift rate**: Rate of polarisation change per unit time (°/s or °/min)  
- **Correlation metrics**: Relationship between environmental factors (temperature, vibration, humidity) and QBER  
- **Photon detection rate**: Counts per second at the detectors  
- **Jitter**: Timing variation in photon arrival (if time-coded pulses are used)  

All angles shall be expressed in degrees (°), and environmental metrics in SI units.
""")

st.header("3. Test Categories and Procedures")

st.subheader("3.1 Long-Term Drift")
st.write("""
**Objective:**  
Simulate permanent or semi-permanent alignment deviations due to mechanical stress or component shifts.

**Test Parameters:**  
- Alice polarisation angle (Δθ = ±1–5°)  
- Bob polarisation angle (Δθ = ±1–5°)  
- Alice/Bob horizontal angular misalignment  
- Laser x/z tilt (±2°)  
- Detector 44 x/z tilt (±2°)  

**Test Procedure:**  
1. Baseline QBER shall be measured with all optical components aligned.  
2. Each parameter shall be incrementally varied while others remain fixed.  
3. For each configuration, the system shall:  
   - Record QBER, Δθ, and environmental metrics  
   - Repeat the transmission N times to ensure repeatability  
4. Results shall be logged and used for model validation.  

**Additional Notes:**  
- Conduct tests under ambient, temperature-varied, and humidity-varied conditions.  
- Automate component adjustments where possible for precision and repeatability.  

**Requirements:**  
- REQ-LTD-001: The system shall allow mechanical adjustment of each optical component in at least 0.5° increments.  
- REQ-LTD-002: The system shall record QBER and polarisation shift for each configuration.  
- REQ-LTD-003: The long-term drift test shall be performed under both ambient and temperature-varied conditions.  
""")

st.subheader("3.2 Short-Term Drift")
st.write("""
**Objective:**  
Measure QBER impact of transient misalignments due to vibration or thermal pulses.  

**Test Events:**  
- Controlled table vibration (e.g., by shaker)  
- Brief directional force on components (e.g., tap or cable tug)  
- Localised heating (e.g., hot air source)  

**Test Procedure:**  
1. Initiate each disturbance for ≤30 seconds.  
2. QBER shall be recorded before, during, and after each event.  
3. The system shall be allowed to passively return to baseline.  
4. Each event shall be repeated 5 times to assess repeatability.  

**Additional Notes:**  
- Include vibration amplitude and frequency details.  
- Define acceptable QBER tolerance for transient events.  
- Synchronize environmental metrics with optical measurements.  

**Requirements:**  
- REQ-STD-001: The system shall sample QBER at a minimum frequency of 10 Hz during transient events.  
- REQ-STD-002: The system shall return to within 10% of baseline QBER within 5 minutes after disturbance.  
- REQ-STD-003: Environmental metrics (vibration, temperature) shall be logged synchronously with optical data.  
""")

st.subheader("3.3 Atmospheric Drift")
st.write("""
**Objective:**  
Quantify polarisation drift caused by humidity, vapour, particulates, and light interference.  

**Test Chamber:**  
A sealed plexiglass enclosure with optical access shall be used for all atmospheric tests.  

**Test Scenarios:**  
- Baseline: clean, dry air  
- Water vapour: RH levels from 20% to 95%  
- Particulates: aerosol fog or smoke  
- Light pollution: controlled visible light spectrum illumination  

**Test Procedure:**  
1. Baseline QBER, DOP, and Δθ shall be measured in dry conditions.  
2. One factor at a time shall be introduced while maintaining all others constant.  
3. For each environmental condition:  
   - Record QBER, Δθ, DOP  
   - Repeat measurements for N test messages  
4. Each factor shall be tested at 3–5 intensity levels (e.g., RH%, fog density)  
5. Test combined scenarios (humidity + light + particulates) to observe interactions.  

**Requirements:**  
- REQ-ATM-001: The test chamber shall allow controlled introduction of water vapour and particulates.  
- REQ-ATM-002: The system shall measure polarisation angle and DOP before and after each atmospheric variation.  
- REQ-ATM-003: Light interference shall be introduced in at least three intensity levels (e.g., 100 lx, 300 lx, 500 lx).  
""")

st.header("4. Control Test Procedure")
st.write("""
**Objective:**  
Confirm system repeatability under unchanged, ideal conditions.  

**Procedure:**  
- With all variables at nominal values, transmit N test messages and log QBER.  
- Repeat twice daily for 3 days.  

**Requirement:**  
- REQ-CTRL-001: The control QBER shall not vary by more than ±5% across all control trials.  

**Additional Notes:**  
- Include calibration points before and after each control test.  
- Use trend plots for QBER and Δθ over time to detect anomalies.  
""")

st.header("5. Verification and Analysis")
st.write("""
Each requirement shall be verified as follows:

| Req ID      | Verification Method        |
|-------------|-----------------------------|
| REQ-LTD-001 | Inspection + Functional Test |
| REQ-STD-002 | Test + Time Series Analysis |
| REQ-ATM-002 | Measurement Comparison |
| REQ-CTRL-001| Statistical Analysis |
""")
