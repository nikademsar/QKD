import streamlit as st
import pandas as pd
import zipfile
from collections import defaultdict
from io import BytesIO

# ---------------------------- Helper functions ----------------------------
def read_csv_with_fallback(file_like, sep=None):
    encodings_to_try = ["utf-8", "latin1", "cp1250"]
    last_error = None
    for enc in encodings_to_try:
        try:
            if hasattr(file_like, "seek"):
                file_like.seek(0)
            return pd.read_csv(file_like, sep=sep, engine="python", encoding=enc, header=0)
        except Exception as e:
            last_error = e
    raise last_error

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

def find_environment_for_file(file_name: str, env_files):
    for env_file in env_files:
        try:
            df_env = read_csv_with_fallback(env_file, sep=',')
        except Exception:
            continue
        if df_env.empty:
            continue
        try:
            df_env = df_env.iloc[6:].reset_index(drop=True)
            new_columns = [
                "DATE",
                "TIME",
                "HUMIDITY_BOX",
                "TEMPERATURE_BOX",
                "HUMIDITY_ROOM",
                "TEMPERATURE_ROOM",
            ]
            df_env.columns = new_columns[:len(df_env.columns)]

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
        except Exception:
            continue
    return None

def try_detect_columns(df: pd.DataFrame):
    cols = [c.lower() for c in df.columns.astype(str)]
    measure_names = ['measurement','measure','measure_num','meritev','id','measurement_number','measurement_no','measure_no']
    pin44_names = ['pin44','pin_44','p44','pin 44']
    pin45_names = ['pin45','pin_45','p45','pin 45']
    def find_name(names_list):
        for n in names_list:
            if n in cols:
                return df.columns[cols.index(n)]
        return None
    return (find_name(measure_names), find_name(pin44_names), find_name(pin45_names))

def df_to_measurements(df: pd.DataFrame):
    measure_col, pin44_col, pin45_col = try_detect_columns(df)
    measurements = []
    if measure_col and pin44_col and pin45_col:
        for _, row in df.iterrows():
            try:
                measurements.append((None, row[measure_col], None,
                                     float(row[pin44_col]), float(row[pin45_col])))
            except Exception:
                continue
        return measurements, (measure_col, pin44_col, pin45_col), None
    try:
        for _, row in df.iterrows():
            try:
                measurements.append((None, row.iloc[1], None,
                                     float(row.iloc[3]), float(row.iloc[4])))
            except Exception:
                continue
        if measurements:
            return measurements, ("index_1","index_3","index_4"), None
    except Exception as e:
        return [], None, str(e)
    return [], None, "Could not find suitable columns."

def active_pin(pin44, pin45):
    try:
        if pin44 > 3000 and pin45 > 3000:
            return (1,0,0)
        elif pin44 < 40 and pin45 > 180:
            return (0,1,0)
    except Exception:
        pass
    return (0,0,1)

def analyze_measurements(measurements):
    if not measurements:
        return {}
    measurement_groups = defaultdict(list)
    for m in measurements:
        if m and len(m) > 4:
            measurement_groups[m[1]].append(m)
    results = {}
    for measure_num, group in measurement_groups.items():
        total_samples = len(group)
        if total_samples < 4:
            results[measure_num] = dict(total_samples=total_samples,
                                        pin44_active=0,pin45_active=0,
                                        avg_pin44=0.0,avg_pin45=0.0,
                                        out_of_range=0)
            continue
        try:
            pin44_values = [float(group[2][3]), float(group[3][3])]
            pin45_values = [float(group[2][4]), float(group[3][4])]
        except Exception:
            results[measure_num] = dict(total_samples=total_samples,
                                        pin44_active=0,pin45_active=0,
                                        avg_pin44=0.0,avg_pin45=0.0,
                                        out_of_range=0)
            continue
        avg_pin44 = sum(pin44_values)/2.0
        avg_pin45 = sum(pin45_values)/2.0
        p44,p45,out = active_pin(avg_pin44, avg_pin45)
        results[measure_num] = dict(total_samples=total_samples,
                                    pin44_active=p44,pin45_active=p45,
                                    avg_pin44=avg_pin44,avg_pin45=avg_pin45,
                                    out_of_range=out)
    return results

def results_to_dataframe(results: dict):
    rows = []
    for mnum, s in results.items():
        rows.append({
            "MEASUREMENT_NUMBER": mnum,
            "TOTAL_SAMPLES": s['total_samples'],
            "PIN44_ACTIVE_(1/0)": s['pin44_active'],
            "PIN45_ACTIVE_(1/0)": s['pin45_active'],
            "AVG_PIN44_(MID_POINTS)": round(s['avg_pin44'],2),
            "AVG_PIN45_(MID_POINTS)": round(s['avg_pin45'],2),
            "OUT_OF_NORMAL_RANGE": s['out_of_range'],
        })
    return pd.DataFrame(rows).sort_values(by="MEASUREMENT_NUMBER").reset_index(drop=True) if rows else pd.DataFrame()

def build_conclusion_dict(fname, total, pin44_count, pin44_pct,
                          pin45_count, pin45_pct, out_count, out_pct,
                          setup_info, env_info):
    row = {
        "FILE_NAME": fname,
        "NUMBER_OF_MEASUREMENTS": total,
        "PIN44_ACTIVE_(COUNT)": pin44_count,
        "PIN44_ACTIVE_(%)": pin44_pct,
        "PIN45_ACTIVE_(COUNT)": pin45_count,
        "PIN45_ACTIVE_(%)": pin45_pct,
        "OUT_OF_RANGE_(COUNT)": out_count,
        "OUT_OF_RANGE_(%)": out_pct,
    }
    if setup_info:
        row.update(setup_info)
    if env_info:
        row.update(env_info)
    return row

# ---------------------------- Streamlit App ----------------------------
st.set_page_config(layout="wide")
st.title("QDrift Analysis (Session-State)")

setup_file = st.file_uploader("Upload Setup CSV", type="csv")
env_files = st.file_uploader("Upload Environment CSV files", type="csv", accept_multiple_files=True)
measurement_files = st.file_uploader("Upload Measurement CSV files", type="csv", accept_multiple_files=True)

run_analysis = st.button("Run Analysis")

# Inicializacija session state
if "conclusions" not in st.session_state:
    st.session_state["conclusions"] = None
if "zip_data" not in st.session_state:
    st.session_state["zip_data"] = None

if run_analysis:
    if not (measurement_files and setup_file):
        st.error("Please upload setup and measurement files.")
    else:
        try:
            df_setup = read_csv_with_fallback(setup_file)
            df_setup.columns = df_setup.columns.str.strip().str.replace('\ufeff','')
        except Exception as e:
            st.error(f"Error loading setup CSV: {e}")
            df_setup = pd.DataFrame()

        all_conclusions = []
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for file in measurement_files:
                fname = file.name
                try:
                    df = read_csv_with_fallback(file)
                except Exception as e:
                    st.error(f"Error reading {fname}: {e}")
                    continue

                measurements, cols_info, err = df_to_measurements(df)
                if err:
                    st.warning(f"Column detection error in {fname}: {err}")
                    continue

                results = analyze_measurements(measurements)
                if not results:
                    st.warning(f"Not enough samples in {fname}")
                    continue

                df_results = results_to_dataframe(results)
                total = len(df_results)
                pin44_count = int(df_results["PIN44_ACTIVE_(1/0)"].sum())
                pin45_count = int(df_results["PIN45_ACTIVE_(1/0)"].sum())
                out_count = total - pin44_count - pin45_count
                pin44_pct = round(pin44_count / total * 100, 2) if total > 0 else 0
                pin45_pct = round(pin45_count / total * 100, 2) if total > 0 else 0
                out_pct = 100 - pin44_pct - pin45_pct

                setup_info = find_setup_for_file(fname, df_setup)
                if setup_info is None:
                    setup_info = {col: None for col in df_setup.columns}

                env_info = find_environment_for_file(fname, env_files)
                if env_info is None and env_files:
                    try:
                        df_env_template = read_csv_with_fallback(env_files[0], sep=',')
                        df_env_template = df_env_template.iloc[6:].reset_index(drop=True)
                        new_columns = [
                            "DATE",
                            "TIME",
                            "HUMIDITY_BOX",
                            "TEMPERATURE_BOX",
                            "HUMIDITY_ROOM",
                            "TEMPERATURE_ROOM",
                        ]
                        df_env_template.columns = new_columns[:len(df_env_template.columns)]
                        env_info = {col: None for col in df_env_template.columns}
                    except Exception:
                        env_info = {}

                conclusion = build_conclusion_dict(fname, total, pin44_count, pin44_pct,
                                                   pin45_count, pin45_pct, out_count,
                                                   out_pct, setup_info, env_info)
                all_conclusions.append(conclusion)

                csv_bytes = df_results.to_csv(index=False).encode("utf-8")
                zf.writestr(fname.replace(".csv", "_analysis.csv"), csv_bytes)

                with st.expander(f"Analysis for {fname}"):
                    st.dataframe(df_results)
                    for k, v in conclusion.items():
                        st.write(f"**{k}:** {v}")

        if all_conclusions:
            df_conclusions = pd.DataFrame(all_conclusions)
            # shranimo v session state
            st.session_state["conclusions"] = df_conclusions
            st.session_state["zip_data"] = zip_buffer.getvalue()

# Prikaz shranjenih rezultatov tudi po kliku download
if st.session_state["conclusions"] is not None:
    st.subheader("Conclusions")
    st.dataframe(st.session_state["conclusions"])
    st.download_button(
        "Download All Analyses (ZIP)",
        data=st.session_state["zip_data"],
        file_name="all_analyses.zip",
        mime="application/zip"
    )
    st.download_button(
        "Download Combined Conclusions (CSV)",
        data=st.session_state["conclusions"].to_csv(index=False).encode("utf-8"),
        file_name="all_conclusions.csv",
        mime="text/csv"
    )