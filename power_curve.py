"""
Day 2 - Power Curve Visualization
Actual vs Theoretical Power Curve, colored by Wind Direction
"""

import pandas as pd
import plotly.express as px

CSV_PATH = "data/wind_data.csv"  # keep consistent with your actual filename

df = pd.read_csv(CSV_PATH)
df["Date/Time"] = pd.to_datetime(df["Date/Time"], format="%d %m %Y %H:%M")

# Scatter: actual power vs wind speed, colored by wind direction
fig = px.scatter(
    df,
    x="Wind Speed (m/s)",
    y="LV ActivePower (kW)",
    color="Wind Direction (°)",
    opacity=0.5,
    title="Actual Power Output vs Wind Speed (colored by Wind Direction)",
    labels={"LV ActivePower (kW)": "Actual Power (kW)"},
)

# Overlay the theoretical power curve as a line
theoretical_sorted = df.sort_values("Wind Speed (m/s)")
fig.add_scatter(
    x=theoretical_sorted["Wind Speed (m/s)"],
    y=theoretical_sorted["Theoretical_Power_Curve (KWh)"],
    mode="lines",
    name="Theoretical Power Curve",
    line=dict(color="red", width=2),
)

fig.write_html("power_curve.html")
print("Chart saved! Open power_curve.html in your project folder.")