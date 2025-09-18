import pandas as pd
import zipfile
from collections import defaultdict
import os

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

def find_environment_for_file(file_name: str, env_files: list[str]):
    for env_file in env_files:
        df_env = read_csv_with_fallback(env_file, sep=None) if os.path.exists(env_file) else pd.DataFrame()
        if df_env.empty:
            return None
        try:
            # Odstrani prve 6 vrstic in ponastavi index
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
            time = time_part.replace("-", ":")[:5]  # samo ure in minute

            # Pretvori prvi dve stolpca v string
            dates = df_env.iloc[:, 0].astype(str)
            times = df_env.iloc[:, 1].astype(str).str[:5]

            match = df_env[(dates.str.contains(date)) & (times == time)]
            if not match.empty:
                return match.iloc[0].to_dict()
            return None
        except Exception as e:
            print(f"Error in find_environment_for_file: {e}")
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
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    try:
        df = df.sort_values(by="Measurement Number").reset_index(drop=True)
    except Exception:
        pass
    return df

def build_conclusion_dict(fname, total, pin44_count, pin44_pct,
                          pin45_count, pin45_pct, out_count, out_pct,
                          setup_info, env_info):
    row = {
        "File name": fname,
        "Number of measurements": total,
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

# ---------------------------- MAIN ----------------------------
if __name__ == "__main__":
    measurement_files = [
        r"L:\AstroMetriQ\QDrift\logs\logs_measurements\2025-09-15_14-20-12_meas_10000.csv",
        r"L:\AstroMetriQ\QDrift\logs\logs_measurements\2025-07-23_14-22-52_meas_10000.csv"
    ]
    setup_file = r"L:\AstroMetriQ\QDrift\measurements_setup.csv"
    env_files = [
        r"L:\AstroMetriQ\QDrift\environment\okolje_julij.csv",
        r"L:\AstroMetriQ\QDrift\environment\okolje_september-17.csv"
    ]

    df_setup = read_csv_with_fallback(setup_file, sep=None) if os.path.exists(setup_file) else pd.DataFrame()

    all_conclusions = []
    zip_files = []

    for filepath in measurement_files:
        fname = os.path.basename(filepath)
        print(f"\n=== Processing file: {fname} ===")

        try:
            df = read_csv_with_fallback(filepath, sep=None)
        except Exception as e:
            print(f"Error reading file {fname}: {e}")
            continue

        measurements, cols_info, err = df_to_measurements(df)
        if err:
            print(f"Error converting input data: {err}")
            continue

        print(f"Detected/used columns: {cols_info}")
        print(f"Number of valid imported records: {len(measurements)}")

        results = analyze_measurements(measurements)
        if not results:
            print("No data to analyze (maybe too few samples).")
            continue

        df_results = results_to_dataframe(results)
        print(df_results)

        total = len(df_results)
        pin44_count = int(df_results["Pin44 Active (1/0)"].sum())
        pin45_count = int(df_results["Pin45 Active (1/0)"].sum())
        out_count = total - pin44_count - pin45_count
        pin44_pct = round(pin44_count / total * 100, 2) if total > 0 else 0
        pin45_pct = round(pin45_count / total * 100, 2) if total > 0 else 0
        out_pct = 100 - pin44_pct - pin45_pct

        print(f"Conclusion for {fname}:")
        print(f"- Measurements: {total}")
        print(f"- Pin44 Active: {pin44_count} ({pin44_pct}%)")
        print(f"- Pin45 Active: {pin45_count} ({pin45_pct}%)")
        print(f"- Noise: {out_count} ({out_pct}%)")

        setup_info = find_setup_for_file(fname, df_setup)
        env_info = find_environment_for_file(fname, env_files)  # vrne slovar

        out_csv_name = fname.replace(".csv", "_analysis.csv")
        df_results.to_csv(out_csv_name, index=False)
        print(f"Saved analysis to {out_csv_name}")

        csv_bytes = df_results.to_csv(index=False).encode("utf-8")
        zip_files.append((out_csv_name, csv_bytes))

        all_conclusions.append(
            build_conclusion_dict(fname, total,
                                  pin44_count, pin44_pct,
                                  pin45_count, pin45_pct,
                                  out_count, out_pct,
                                  setup_info, env_info)
        )

    if len(zip_files) > 1:
        with zipfile.ZipFile("../all_analyses.zip", "w") as zf:
            for name, data in zip_files:
                zf.writestr(name, data)
        print("Saved ZIP with all analyses: all_analyses.zip")

    if all_conclusions:
        df_conclusions = pd.DataFrame(all_conclusions)
        df_conclusions.to_csv("all_conclusions.csv", index=False)
        print("Saved combined conclusions: all_conclusions.csv")