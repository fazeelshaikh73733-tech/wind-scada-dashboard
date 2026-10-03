"""
Wind Farm SCADA Performance & Smart Grid Analytics Dashboard
"""

import streamlit as st
import pandas as pd
import plotly.express as px

CSV_PATH = "data/wind_data.csv"
CUT_IN, CUT_OUT = 3.5, 25.0

st.set_page_config(page_title="Wind Farm SCADA Dashboard", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv(CSV_PATH)
    df["Date/Time"] = pd.to_datetime(df["Date/Time"], format="%d %m %Y %H:%M")
    in_range = (df["Wind Speed (m/s)"] >= CUT_IN) & (df["Wind Speed (m/s)"] < CUT_OUT)
    underperforming = df["LV ActivePower (kW)"] < (0.5 * df["Theoretical_Power_Curve (KWh)"])
    df["curtailment_flag"] = in_range & underperforming
    df["event_type"] = "Normal"
    df.loc[df["curtailment_flag"] & (df["LV ActivePower (kW)"] == 0), "event_type"] = "Hard Shutdown"
    df.loc[df["curtailment_flag"] & (df["LV ActivePower (kW)"] > 0), "event_type"] = "Partial Curtailment"
    return df

df_full = load_data()

st.title("🌬️ Wind Farm SCADA Performance & Smart Grid Analytics")

with st.expander("ℹ️ About this dashboard: Einspeisemanagement & anomaly detection"):
    st.markdown("""
    Under Germany's **EEG (Erneuerbare-Energien-Gesetz)**, grid operators can order wind farms to reduce
    feed-in (**Einspeisemanagement**) when the local grid is congested. This dashboard distinguishes two
    types of underperformance relative to a turbine's theoretical power curve:

    - **Hard Shutdown** — actual power is exactly 0 kW despite operational wind speeds, typically indicating
      a fault, maintenance event, or safety shutdown rather than a grid order.
    - **Partial Curtailment** — actual power is reduced but non-zero, more consistent with a genuine
      grid-ordered feed-in reduction.
    """)

# --- Sidebar filters ---
st.sidebar.header("Filters")
min_date, max_date = df_full["Date/Time"].min().date(), df_full["Date/Time"].max().date()
date_range = st.sidebar.date_input("Date range", (min_date, max_date), min_value=min_date, max_value=max_date)

ws_min, ws_max = float(df_full["Wind Speed (m/s)"].min()), float(df_full["Wind Speed (m/s)"].max())
wind_speed_range = st.sidebar.slider("Wind speed range (m/s)", ws_min, ws_max, (ws_min, ws_max))

event_types = st.sidebar.multiselect(
    "Event types to include",
    options=["Normal", "Hard Shutdown", "Partial Curtailment"],
    default=["Normal", "Hard Shutdown", "Partial Curtailment"],
)

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
    mask_date = (df_full["Date/Time"].dt.date >= start_date) & (df_full["Date/Time"].dt.date <= end_date)
else:
    mask_date = pd.Series(True, index=df_full.index)

mask_ws = df_full["Wind Speed (m/s)"].between(wind_speed_range[0], wind_speed_range[1])
mask_event = df_full["event_type"].isin(event_types)

df = df_full[mask_date & mask_ws & mask_event]

# --- KPI row ---
hard_shutdown = (df["event_type"] == "Hard Shutdown").sum()
partial_curtailment = (df["event_type"] == "Partial Curtailment").sum()
capacity_factor = df["LV ActivePower (kW)"].sum() / df["Theoretical_Power_Curve (KWh)"].sum() * 100 if len(df) else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Capacity Factor", f"{capacity_factor:.1f}%")
col2.metric("Records (filtered)", f"{len(df):,}")
col3.metric("Hard Shutdowns", f"{hard_shutdown:,}", f"{hard_shutdown/len(df)*100:.2f}%" if len(df) else "0%")
col4.metric("Partial Curtailment", f"{partial_curtailment:,}", f"{partial_curtailment/len(df)*100:.2f}%" if len(df) else "0%")

st.divider()

# --- Power curve chart ---
st.subheader("Power Curve: Actual vs Theoretical")
fig_curve = px.scatter(
    df, x="Wind Speed (m/s)", y="LV ActivePower (kW)",
    color="event_type", opacity=0.5,
    color_discrete_map={"Normal": "steelblue", "Hard Shutdown": "red", "Partial Curtailment": "orange"},
)
theoretical_sorted = df.sort_values("Wind Speed (m/s)")
fig_curve.add_scatter(
    x=theoretical_sorted["Wind Speed (m/s)"],
    y=theoretical_sorted["Theoretical_Power_Curve (KWh)"],
    mode="lines", name="Theoretical Curve", line=dict(color="black", width=2),
)
st.plotly_chart(fig_curve, use_container_width=True)

st.divider()

# --- Time-series view (with 7-day rolling average) ---
st.subheader("Power Output Over Time")
df_daily = df.set_index("Date/Time").resample("D").agg({
    "LV ActivePower (kW)": "mean",
    "event_type": lambda x: (x != "Normal").sum()
}).rename(columns={"event_type": "Flagged Events (daily count)"})
df_daily["7-day rolling avg"] = df_daily["LV ActivePower (kW)"].rolling(7).mean()

fig_ts = px.line(
    df_daily, y=["LV ActivePower (kW)", "7-day rolling avg"],
    title="Daily Average Power Output (with 7-day rolling average)",
    labels={"value": "Power (kW)", "variable": ""},
)
st.plotly_chart(fig_ts, use_container_width=True)

fig_events = px.bar(
    df_daily, y="Flagged Events (daily count)",
    title="Daily Count of Flagged Events (shutdowns + curtailment)",
)
st.plotly_chart(fig_events, use_container_width=True)

st.divider()

# --- Monthly wind speed vs flagged events comparison ---
st.subheader("Monthly Pattern: Wind Speed vs Flagged Events")

df_monthly = df.set_index("Date/Time").resample("ME").agg(
    avg_wind_speed=("Wind Speed (m/s)", "mean"),
    flagged_count=("curtailment_flag", "sum"),
)
df_monthly.index = df_monthly.index.strftime("%b %Y")

fig_monthly = px.bar(
    df_monthly, x=df_monthly.index, y="flagged_count",
    labels={"flagged_count": "Flagged Events", "x": "Month"},
    title="Monthly Flagged Events (bars) vs Average Wind Speed (line)",
)
fig_monthly.add_scatter(
    x=df_monthly.index, y=df_monthly["avg_wind_speed"],
    mode="lines+markers", name="Avg Wind Speed (m/s)",
    yaxis="y2", line=dict(color="black", width=2),
)
fig_monthly.update_layout(
    yaxis2=dict(title="Avg Wind Speed (m/s)", overlaying="y", side="right"),
)
st.plotly_chart(fig_monthly, use_container_width=True)

st.divider()

# --- Flagged events table ---
st.subheader("Flagged Curtailment / Anomaly Events")
st.dataframe(
    df[df["curtailment_flag"]][["Date/Time", "Wind Speed (m/s)", "LV ActivePower (kW)", "Theoretical_Power_Curve (KWh)", "event_type"]],
    use_container_width=True,
)