import streamlit as st

st.title("QKD - BB84 Simulation")

st.markdown("""
### What is Quantum Key Distribution (QKD)?

**Quantum Key Distribution** (QKD) is a method by which two parties (commonly called Alice and Bob) share a secret encryption key over a quantum channel. The special feature of QKD is that it guarantees **information-theoretic security**, as it is based on the laws of **quantum mechanics** rather than just mathematical assumptions.

* In the case of interception (e.g., by Eve), the system detects it because **quantum states cannot be measured without disturbance**.
* Fundamental concepts:

  * **Superposition**: a quantum particle (e.g., photon) can exist in multiple states simultaneously.
  * **Measurement disturbs the state**: when someone measures a quantum particle, it "collapses" into one of the possible states.
  * **No-cloning theorem**: quantum states cannot be copied without errors.

---

### BB84 Protocol – step by step

BB84 is the first and best-known QKD protocol developed by **Charles Bennett** and **Gilles Brassard** in 1984.

#### Step 1: Alice generates random bits and bases

* For each bit, she randomly chooses:

  * **Bit**: `0` or `1`
  * **Basis**:

    * **Rectilinear** (|, −): 0° or 90°
    * **Diagonal** (/ , \\): 45° or 135°
* Alice sends a photon polarized in one of **four possible polarizations**:

  * `0` → 0°, 45°
  * `1` → 90°, 135°

#### Step 2: Alice sends photons through the quantum channel

* Each photon travels through the **quantum channel** to Bob.
* Quantum property: the photon "carries" polarization but cannot be observed without changing it.

#### Step 3: Bob measures the photons

* Bob randomly chooses a basis (rectilinear or diagonal) for each photon.
* If he chooses the same basis as Alice:

  * **Measurement is correct** → he gets the same bit.
* If he chooses the wrong basis:

  * **Measurement is random** → 50% chance to get the correct or incorrect bit.

#### Step 4: Basis comparison

* After measurements, Alice and Bob **publicly reveal which bases** they used (but not the bit values).
* They keep only the bits where their bases **matched**.

  * This is called the **raw key**.

#### Step 5: Detecting Eve (optional)

* If Eve eavesdrops, she must **perform measurements** but doesn't know which basis to choose.
* Consequently:

  * She introduces errors in quantum measurements.
  * Alice and Bob can check the **error rate** in the key.
  * If the error rate exceeds a threshold → **eavesdropping is detected**.

#### Step 6: Error correction and key extraction

* Alice and Bob correct any errors (e.g., using ECC algorithms).
* They apply **privacy amplification** – a process reducing the impact of any intercepted bits.

---

### Why does BB84 work?

BB84 works because of three key quantum principles:

1. **Measurement disturbs the quantum state**
2. **Quantum states cannot be distinguished without knowledge of the basis**
3. **Quantum states cannot be cloned without errors**

Because of this, Alice and Bob can detect any eavesdropping and thus guarantee **unconditional security** (in theory).

---

### Example simulation:

| Alice polarization | Alice basis  | Bob basis         | Result             |
| ------------------ | ----------- | ---------------- | ------------------ |
| 0°                 | rectilinear | rectilinear (0°) | correct (bit 0)    |
| 0°                 | rectilinear | diagonal (45°)   | random (0 or 1)    |
| 45°                | diagonal    | rectilinear (0°) | random (0 or 1)    |
| 45°                | diagonal    | diagonal (45°)   | correct (bit 0)    |
| 90°                | rectilinear | rectilinear (0°) | correct (bit 1)    |
| 90°                | rectilinear | diagonal (45°)   | random (0 or 1)    |
| 135°               | diagonal    | rectilinear (0°) | random (0 or 1)    |
| 135°               | diagonal    | diagonal (45°)   | correct (bit 1)    |

""")
