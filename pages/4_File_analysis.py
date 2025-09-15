import streamlit as st
import pandas as pd
import io
import zipfile
from collections import defaultdict

# ---------------------------- Helper: read CSV with fallback ----------------------------
def read_csv_with_fallback(file, sep=None):
    encodings_to_try = ["utf-8", "latin1", "cp1250"]
    last_error = None
    for enc in encodings_to_try:
        try:
            return pd.read_csv(file, sep=sep, engine="python", encoding=enc)
        except Exception as e:
            last_error = e
            continue
    raise last_error

# ---------------------------- Setup lookup ----------------------------
def find_setup_for_file(file_name: str, df_setup: pd.DataFrame):
    if df_setup.empty:
        return None
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

def find_environment_for_file(file_name: str, df_env: pd.DataFrame):
    if df_env.empty:
        return None
    try:
        df_env = df_env.iloc[6:].reset_index(drop=True)
        df_env.rename(columns={
            '\ufeffExactum Cloud': 'DATE',
            'Unnamed: 1': 'TIME',
            'Unnamed: 2': 'NBIOT_HUMIDITY',
            'Unnamed: 3': 'NBIOT_TEMPERATURE',
            'Unnamed: 4': 'YCT_HUMIDITY',
            'Unnamed: 5': 'YCT_TEMPERATURE',
        }, inplace=True)

        datetime_str = file_name.split("_meas_")[0]
        date_part, time_part = datetime_str.split("_")
        year, month, day = date_part.split("-")

        date = f"{int(day):02d}.{int(month):02d}.{int(year)}"
        time = time_part.replace("-", ":")[:5]

        dates = df_env.iloc[:, 0].astype(str)
        times = df_env.iloc[:, 1].astype(str).str[:5]

        match = df_env[(dates.str.contains(date)) & (times == time)]
        if not match.empty:
            return match.iloc[0].to_dict()
        return None
    except Exception as e:
        st.error(f"Error in finding environment for file: {e}")
        return None

# ---------------------------- Helpers ----------------------------
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
                'out_of_range': 0,
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
                'out_of_range': 0,
            }
            continue
        avg_pin44 = sum(pin44_values) / 2.0
        avg_pin45 = sum(pin45_values) / 2.0
        pin44_active, pin45_active, out_of_range = active_pin(avg_pin44, avg_pin45)
        results[measure_num] = {
            'total_samples': total_samples,
            'pin44_active': pin44_active,
            'pin45_active': pin45_active,
            'avg_pin44': avg_pin44,
            'avg_pin45': avg_pin45,
            'out_of_range': out_of_range,
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
            "Out of Normal Range": stats['out_of_range'],
        })
    return pd.DataFrame(rows)

def build_conclusion_dict(fname, total, pin44_count, pin44_pct,
                          pin45_count, pin45_pct, out_count, out_pct,
                          setup_info, env_info):
    row = {
        "File Name": fname,
        "Number of Measurements": total,
        "Pin44 Active (count)": pin44_count,
        "Pin44 Active (%)": pin44_pct,
        "Pin45 Active (count)": pin45_count,
        "Pin45 Active (%)": pin45_pct,
        "Out of Range (count)": out_count,
        "Out of Range (%)": out_pct,
    }
    if setup_info:
        row.update(setup_info)
    if env_info:
        row.update(env_info)
    return row

# ---------------------------- Streamlit UI ----------------------------
st.title("QDrift Measurement Analysis")

uploaded_measurements = st.file_uploader(
    "Select measurement CSV files", type="csv", accept_multiple_files=True
)
uploaded_setup = st.file_uploader("Select setup CSV file", type="csv")
uploaded_env = st.file_uploader("Select environment CSV file", type="csv")

if st.button("Run Analysis"):
    if not uploaded_measurements:
        st.warning("Please select at least one measurement file.")
    else:
        df_setup = read_csv_with_fallback(uploaded_setup) if uploaded_setup else pd.DataFrame()
        df_env = read_csv_with_fallback(uploaded_env) if uploaded_env else pd.DataFrame()

        all_conclusions = []
        zip_buffer = io.BytesIO()
        zip_file = zipfile.ZipFile(zip_buffer, "w")

        for file in uploaded_measurements:
            fname = file.name
            df = read_csv_with_fallback(file)
            measurements, cols_info, err = df_to_measurements(df)
            if err:
                st.warning(f"Error in {fname}: {err}")
                continue
            results = analyze_measurements(measurements)
            df_results = results_to_dataframe(results)

            total = len(df_results)
            pin44_count = int(df_results["Pin44 Active (1/0)"].sum())
            pin45_count = int(df_results["Pin45 Active (1/0)"].sum())
            out_count = total - pin44_count - pin45_count
            pin44_pct = round(pin44_count / total * 100, 2) if total > 0 else 0
            pin45_pct = round(pin45_count / total * 100, 2) if total > 0 else 0
            out_pct = 100 - pin44_pct - pin45_pct

            setup_info = find_setup_for_file(fname, df_setup)
            env_info = find_environment_for_file(fname, df_env)

            all_conclusions.append(
                build_conclusion_dict(fname, total,
                                      pin44_count, pin44_pct,
                                      pin45_count, pin45_pct,
                                      out_count, out_pct,
                                      setup_info, env_info)
            )

            csv_bytes = df_results.to_csv(index=False).encode("utf-8")
            zip_file.writestr(fname.replace(".csv", "_analysis.csv"), csv_bytes)

        zip_file.close()

        st.subheader("Combined Conclusions")
        df_conclusions = pd.DataFrame(all_conclusions)
        st.dataframe(df_conclusions)

        st.download_button(
            label="Download ZIP of all analyses",
            data=zip_buffer.getvalue(),
            file_name="all_analyses.zip",
            mime="application/zip"
        )

        st.download_button(
            label="Download conclusions CSV",
            data=df_conclusions.to_csv(index=False).encode("utf-8"),
            file_name="all_conclusions.csv",
            mime="text/csv"
        )
