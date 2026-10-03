
"""
Day 1 - SCADA CSV Inspector
Wind Farm SCADA Performance & Smart Grid Analytics Dashboard
"""

import pandas as pd

# --- Config ---
CSV_PATH = "data/wind_data.csv"

def load_and_inspect(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    print("=" * 60)
    print("SHAPE:", df.shape)
    print("=" * 60)

    print("\nCOLUMN NAMES:")
    print(df.columns.tolist())

    print("\nDATA TYPES:")
    print(df.dtypes)

    print("\nFIRST 5 ROWS:")
    print(df.head())

    print("\nMISSING VALUES PER COLUMN:")
    print(df.isna().sum())

    print("\nBASIC STATISTICS:")
    print(df.describe(include="all").T)

    return df

def check_datetime_column(df: pd.DataFrame, candidate_cols=("Date/Time", "DateTime", "timestamp", "Time")):
    for col in candidate_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
            print(f"\nParsed '{col}' as datetime. Range: {df[col].min()} to {df[col].max()}")
            return col
    print("\nNo obvious datetime column found — check df.columns manually.")
    return None

if __name__ == "__main__":
    df = load_and_inspect(CSV_PATH)
    dt_col = check_datetime_column(df)