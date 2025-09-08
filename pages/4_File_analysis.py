import streamlit as st
import pandas as pd
import io
from collections import defaultdict
import zipfile

st.set_page_config(page_title="QDrift - Measurement Analysis", layout="wide")

st.title("Measurement Analysis")

st.write(
    "Upload one or more CSV/TSV files with measurements. "
    "The app will locate columns for measurement number and pin44/pin45, "
    "run analysis for each file separately, and allow download individually or as ZIP. "
    "All conclusions can also be exported as a combined CSV."
)

# ---------------------------- Expected input file info ----------------------------
with st.expander("Expected input file shapes (examples)"):
    st.markdown(
        """
    * Desired columns (any one of the following names):
      * meritev / measurement / measure_num / measure / id
      * pin44 / pin_44 / P44
      * pin45 / pin_45 / P45
    * If no headers, default indexes:
      * index 1 -> measurement number
      * index 3 -> pin44
      * index 4 -> pin45
    """
    )

# ---------------------------- File uploads ----------------------------
uploaded_files = st.file_uploader(
    "Choose CSV files", type=["csv", "tsv", "txt"], accept_multiple_files=True
)

# Setup file upload (optional)
st.subheader("Upload Setup File (optional)")
uploaded_setup_file = st.file_uploader(
    "Choose setup CSV file", type=["csv"], key="setup_file"
)

df_setup = pd.DataFrame()
if uploaded_setup_file is not None:
    try:
        df_setup = pd.read_csv(uploaded_setup_file, sep=None, engine="python", encoding="latin1")
        st.success("Setup file loaded successfully.")
    except Exception as e:
        st.error(f"Could not load setup file: {e}")

# Environment file upload (optional)
st.subheader("Upload Environment File (optional)")
uploaded_env_file = st.file_uploader(
    "Choose environment CSV/TSV file", type=["csv", "tsv", "txt"], key="env_file"
)

df_env = pd.DataFrame()
if uploaded_env_file is not None:
    try:
        # Skip the first 6 rows (metadata)
        df_env = pd.read_csv(uploaded_env_file, sep=None, engine="python", encoding="latin1", skiprows=6)

        # Remove trailing colons and spaces from column names
        df_env.columns = [c.strip().replace(":", "") for c in df_env.columns]

        # Combine date + time into datetime
        df_env['DATETIME'] = pd.to_datetime(df_env['DATUM'] + ' ' + df_env['CAS'], dayfirst=True, errors='coerce')

        st.success("Environment file loaded successfully.")
    except Exception as e:
        st.error(f"Could not load environment file: {e}")

# ---------------------------- Helper functions ----------------------------
def find_setup_for_file(file_name: str, df_setup: pd.DataFrame):
    try:
        base = file_name.split("_meas_")
        if len(base) != 2:
            return None
        datetime_str = base[0]
        num_measurements = int(base[1].replace(".csv", ""))
        match = df_setup[
            (df_setup["MEASUREMENT_START_DATETIME"] == datetime_str) &
            (df_setup["NUMBER_OF_MEASUREMENTS"] == num_measurements)
        ]
        if not match.empty:
            return match.iloc[0].to_dict()
        return None
    except Exception:
        return None

def try_detect_columns(df: pd.DataFrame):
    cols = [c.lower() for c in df.columns.astype(str)]
    measure_names = ['measurement', 'measure', 'measure_num', 'meritev', 'id', 'measurement_number', 'measurement_no', 'measure_no']
    pin44_names = ['pin44', 'pin_44', 'p44', 'pin 44']
    pin45_names = ['pin45', 'pin_45', 'p45', 'pin 45']

    def find_name(names_list):
        for n in names_list:
            if n in cols:
                return df.columns[cols.index(n)]
        return None

    measure_col = find_name(measure_names)
    pin44_col = find_name(pin44_names)
    pin45_col = find_name(pin45_names)

    return measure_col, pin44_col, pin45_col

def df_to_measurements(df: pd.DataFrame):
    measure_col, pin44_col, pin45_col = try_detect_columns(df)
    measurements = []

    if measure_col and pin44_col and pin45_col:
        for _, row in df.iterrows():
            try:
                mnum = row[measure_col]
                p44 = float(row[pin44_col])
                p45 = float(row[pin45_col])
                measurements.append((None, mnum, None, p44, p45))
            except Exception:
                continue
        return measurements, (measure_col, pin44_col, pin45_col), None

    # Try default indexes
    try:
        for _, row in df.iterrows():
            try:
                mnum = row.iloc[1]
                p44 = float(row.iloc[3])
                p45 = float(row.iloc[4])
                measurements.append((None, mnum, None, p44, p45))
            except Exception:
                continue
        if measurements:
            return measurements, ("index_1", "index_3", "index_4"), None
    except Exception as e:
        return [], None, str(e)

    return [], None, "Could not find suitable columns. Please check the file structure."

def active_pin(pin44, pin45):
    active = (0, 0, 1)
    try:
        if pin44 > 3000 and pin45 > 3000:
            active = (1, 0, 0)
        elif pin44 < 40 and pin45 > 180:
            active = (0, 1, 0)
    except Exception:
        active = (0, 0, 1)
    return active

def analyze_measurements(measurements):
    if not measurements:
        return {}

    measurement_groups = defaultdict(list)
    for m in measurements:
        if m is not None and len(m) > 4:
            measurement_groups[m[1]].append(m)

    results = {}
    for measure_num, group in measurement_groups.items():
        total_samples = len(group)
        if total_samples < 4:
            results[measure_num] = {
                'total_samples': total_samples,
                'pin44_active': 0,
                'pin45_active': 0,
                'avg_pin44': 0.0,
                'avg_pin45': 0.0,
            }
            continue

        third = group[2]
        fourth = group[3]
        try:
            pin44_values = [float(third[3]), float(fourth[3])]
            pin45_values = [float(third[4]), float(fourth[4])]
        except Exception:
            results[measure_num] = {
                'total_samples': total_samples,
                'pin44_active': 0,
                'pin45_active': 0,
                'avg_pin44': 0.0,
                'avg_pin45': 0.0,
            }
            continue

        avg_pin44 = sum(pin44_values) / 2.0
        avg_pin45 = sum(pin45_values) / 2.0
        pin44_active, pin45_active, _ = active_pin(avg_pin44, avg_pin45)

        results[measure_num] = {
            'total_samples': total_samples,
            'pin44_active': pin44_active,
            'pin45_active': pin45_active,
            'avg_pin44': avg_pin44,
            'avg_pin45': avg_pin45,
        }

    return results

def results_to_dataframe(results: dict):
    rows = []
    for measure_num, stats in results.items():
        rows.append({
            "Measurement Number": measure_num,
            "Total Samples": stats['total_samples'],
            "Pin44 Active (1/0)": stats['pin44_active'],
            "Pin45 Active (1/0)": stats['pin45_active'],
            "Avg Pin44 (mid points)": round(stats['avg_pin44'], 2),
            "Avg Pin45 (mid points)": round(stats['avg_pin45'], 2),
        })
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    try:
        df = df.sort_values(by="Measurement Number").reset_index(drop=True)
    except Exception:
        pass
    return df

def build_conclusion_dict(fname, total, pin44_count, pin44_pct,
                          pin45_count, pin45_pct, setup_info, df_env=None, meas_time=None):
    noise_pct = round(100.0 - pin44_pct - pin45_pct, 2)
    row = {
        "File name": fname,
        "Number of measurements": total,
        "Pin44 Active (count)": pin44_count,
        "Pin44 Active (%)": pin44_pct,
        "Pin45 Active (count)": pin45_count,
        "Pin45 Active (%)": pin45_pct,
        "Noise (%)": noise_pct,
    }

    if df_env is not None and meas_time is not None and 'DATETIME' in df_env.columns:
        df_env['TIME_DIFF'] = (df_env['DATETIME'] - meas_time).abs()
        nearest = df_env.loc[df_env['TIME_DIFF'].idxmin()]
        row['Humidity (%RH)'] = nearest.get('%RH', None)
        row['Temperature (°C)'] = nearest.get('°C', None)

    if setup_info:
        for k, v in setup_info.items():
            row[k] = v
    return row

# ---------------------------- Main processing loop ----------------------------
if uploaded_files:
    zip_buffer = io.BytesIO()
    zip_files = []
    all_conclusions = []

    for uploaded_file in uploaded_files:
        st.header(f"File: {uploaded_file.name}")
        try:
            df = pd.read_csv(uploaded_file, sep=None, engine='python')
        except Exception:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file)

        measurements, cols_info, err = df_to_measurements(df)
        if err:
            st.error(f"Error converting input data: {err}")
            continue

        st.info(f"Detected/used columns: {cols_info}")
        if not measurements:
            st.warning("Could not convert to measurement list. Check the data format.")
            continue

        st.write("Number of valid imported records:", len(measurements))
        results = analyze_measurements(measurements)
        if not results:
            st.warning("No data to analyze (maybe too few samples).")
            continue

        df_results = results_to_dataframe(results)
        st.subheader("Analysis Results")
        st.dataframe(df_results, use_container_width=True)

        # --- Counts and percentages for pins ---
        total = len(df_results)
        pin44_count = int(df_results["Pin44 Active (1/0)"].sum())
        pin45_count = int(df_results["Pin45 Active (1/0)"].sum())
        pin44_pct = round(pin44_count / total * 100, 2) if total > 0 else 0
        pin45_pct = round(pin45_count / total * 100, 2) if total > 0 else 0

        # --- Prepare CSV for individual download ---
        csv_buffer = io.StringIO()
        df_results.to_csv(csv_buffer, index=False)
        csv_bytes = csv_buffer.getvalue().encode('utf-8')
        fname_csv = uploaded_file.name.replace(".csv", "_analysis.csv")
        st.download_button("Download this analysis as CSV", data=csv_bytes, file_name=fname_csv, mime="text/csv")

        # --- Setup info ---
        setup_info = find_setup_for_file(uploaded_file.name, df_setup) if not df_setup.empty else None
        if setup_info:
            st.markdown("**Measurement Setup Parameters:**")
            for k, v in setup_info.items():
                st.write(f"- {k}: {v}")

        # --- Add to ZIP ---
        zip_files.append((fname_csv, csv_bytes))

        # --- Measurement timestamp (first measurement) ---
        meas_time = None
        if measurements:
            first_meas = measurements[0]
            meas_time = pd.to_datetime(first_meas[1], dayfirst=True, errors='coerce')

        # --- Build global conclusions ---
        all_conclusions.append(
            build_conclusion_dict(fname_csv, total,
                                  pin44_count, pin44_pct,
                                  pin45_count, pin45_pct,
                                  setup_info,
                                  df_env=df_env,
                                  meas_time=meas_time)
        )

        # --- Show summary ---
        st.subheader("Conclusion")
        st.markdown(
            f"- **File name**: {fname_csv}\n"
            f"- **Number of measurements**: {total}\n"
            f"- **Pin44 Active**: {pin44_count}× ({pin44_pct}%)\n"
            f"- **Pin45 Active**: {pin45_count}× ({pin45_pct}%)\n"
            f"- **Noise**: {round(100.0 - pin44_pct - pin45_pct, 2)}%"
        )

    # --- ZIP all analyses ---
    if len(zip_files) > 1:
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for name, data in zip_files:
                zf.writestr(name, data)
        zip_bytes = zip_buffer.getvalue()
        st.download_button(
            "Download all analyses as ZIP",
            data=zip_bytes,
            file_name="all_analyses.zip",
            mime="application/zip"
        )

    # --- Export all conclusions as one CSV ---
    if all_conclusions:
        df_conclusions = pd.DataFrame(all_conclusions)
        csv_buffer = io.StringIO()
        df_conclusions.to_csv(csv_buffer, index=False)
        csv_bytes = csv_buffer.getvalue().encode("utf-8")
        st.download_button(
            "Download all Conclusions as CSV",
            data=csv_bytes,
            file_name="all_conclusions.csv",
            mime="text/csv"
        )
else:
    st.info("Upload one or more files to start the analysis.")
