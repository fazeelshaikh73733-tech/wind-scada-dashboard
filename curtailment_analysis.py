"""
Day 3 - Curtailment / Anomaly Flagging
"""

import pandas as pd

CSV_PATH = "data/wind_data.csv"

df = pd.read_csv(CSV_PATH)
df["Date/Time"] = pd.to_datetime(df["Date/Time"], format="%d %m %Y %H:%M")

# Define "normal operating range": above cut-in, below typical cut-out
CUT_IN = 3.5       # m/s, typical cut-in speed
CUT_OUT = 25.0     # m/s, typical cut-out (safety shutdown) speed

in_operating_range = (df["Wind Speed (m/s)"] >= CUT_IN) & (df["Wind Speed (m/s)"] < CUT_OUT)

# Flag: actual power far below theoretical, despite good wind
underperforming = df["LV ActivePower (kW)"] < (0.5 * df["Theoretical_Power_Curve (KWh)"])

df["curtailment_flag"] = in_operating_range & underperforming

flagged = df[df["curtailment_flag"]]

print(f"Total records: {len(df)}")
print(f"Flagged as curtailment/anomaly candidates: {len(flagged)} ({len(flagged)/len(df)*100:.2f}%)")
print("\nSample flagged records:")
print(flagged[["Date/Time", "Wind Speed (m/s)", "LV ActivePower (kW)", "Theoretical_Power_Curve (KWh)"]].head(10))

flagged.to_csv("data/flagged_curtailment_events.csv", index=False)
print("\nSaved flagged events to data/flagged_curtailment_events.csv")
# Split into two categories
hard_shutdown = df["curtailment_flag"] & (df["LV ActivePower (kW)"] == 0)
partial_curtailment = df["curtailment_flag"] & (df["LV ActivePower (kW)"] > 0)

print(f"\nHard shutdowns (0 kW despite wind): {hard_shutdown.sum()} ({hard_shutdown.sum()/len(df)*100:.2f}%)")
print(f"Partial curtailment (reduced but nonzero): {partial_curtailment.sum()} ({partial_curtailment.sum()/len(df)*100:.2f}%)")