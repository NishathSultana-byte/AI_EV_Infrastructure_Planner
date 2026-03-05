import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

st.set_page_config(page_title="AI EV Infrastructure Planner", layout="wide")

st.title("AI-Based EV Charging Infrastructure Planner (India)")

# ---------------------------------------------------
# LOAD EV DATA
# ---------------------------------------------------

@st.cache_data
def load_ev_data():
    return pd.read_csv("india_ev_stations.csv")

# ---------------------------------------------------
# LOAD POPULATION DATA
# ---------------------------------------------------

@st.cache_data
def load_population_data():
    return pd.read_csv("state_population_india.csv")


data = load_ev_data()

# ---------------------------------------------------
# CLEAN STATE NAMES
# ---------------------------------------------------

data["State"] = data["State"].astype(str).str.lower().str.strip()

state_corrections = {
    "mh": "maharashtra",
    "mp": "madhya pradesh",
    "gj": "gujarat",
    "rj": "rajasthan",
    "keraka": "kerala",
    "lerala": "kerala",
    "tamilnadu": "tamil nadu",
    "new delhi": "delhi"
}

data["State"] = data["State"].replace(state_corrections)

# ---------------------------------------------------
# DISPLAY RAW DATA
# ---------------------------------------------------

st.subheader("Raw EV Charging Data")

st.write(f"Total Stations Loaded: {len(data)}")

# -------------------------------
# STATE FILTER
# -------------------------------

states = sorted(data["State"].dropna().unique())

selected_state = st.selectbox(
    "Select a State to View EV Stations",
    ["All States"] + states
)

if selected_state != "All States":
    filtered_data = data[data["State"] == selected_state]
else:
    filtered_data = data

st.dataframe(filtered_data.drop(columns=["Town"], errors="ignore"))

# ---------------------------------------------------
# CLUSTERING EV STATIONS
# ---------------------------------------------------

data = data.dropna(subset=["Latitude", "Longitude"])

features = data[["Latitude", "Longitude", "Power_kW"]]

scaler = StandardScaler()
scaled_features = scaler.fit_transform(features)

k = st.slider("Select Number of Clusters", 2, 8, 4)

kmeans = KMeans(n_clusters=k, random_state=42)

data["Cluster"] = kmeans.fit_predict(scaled_features)

filtered_data["Cluster"] = data["Cluster"]

st.subheader("EV Charging Station Clusters")

fig = px.scatter_mapbox(
    data if selected_state == "All States" else filtered_data,
    lat="Latitude",
    lon="Longitude",
    color="Cluster",
    hover_name="Station_Name",
    zoom=4,
    height=600
)

fig.update_layout(mapbox_style="open-street-map")

st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------
# CLUSTER DISTRIBUTION
# ---------------------------------------------------

st.subheader("Cluster Distribution")

st.bar_chart(data["Cluster"].value_counts())

# ---------------------------------------------------
# AI SUGGESTED LOCATIONS FOR NEW EV STATIONS
# ---------------------------------------------------

st.subheader("AI Suggested Locations for New EV Charging Stations")

# Get cluster centers
centers = kmeans.cluster_centers_

# Convert centers back to original scale
centers_original = scaler.inverse_transform(centers)

suggested_locations = pd.DataFrame(
    centers_original,
    columns=["Latitude", "Longitude", "Power_kW"]
)

suggested_locations["Suggested_Station"] = [
    f"Recommended Station {i+1}" for i in range(len(suggested_locations))
]

# Show table
st.dataframe(suggested_locations)

# Plot suggested locations on map
fig_suggested = px.scatter_mapbox(
    suggested_locations,
    lat="Latitude",
    lon="Longitude",
    hover_name="Suggested_Station",
    size=[10]*len(suggested_locations),
    zoom=4,
    height=500
)

fig_suggested.update_layout(mapbox_style="open-street-map")

st.plotly_chart(fig_suggested, use_container_width=True)

# ---------------------------------------------------
# EV STATION SUMMARY
# ---------------------------------------------------

ev_summary = data.groupby("State").agg(
    Total_Stations=("Station_Name", "count"),
    Avg_Power_kW=("Power_kW", "mean")
).reset_index()

# ---------------------------------------------------
# LOAD POPULATION DATA
# ---------------------------------------------------

population_df = load_population_data()

population_df.columns = population_df.columns.str.strip()

population_df = population_df.rename(columns={
    "India/State/Union Territory": "State",
    "Population 2011": "Population",
    "Population Density (per sq.km) - 2011": "Density"
})

population_df["State"] = population_df["State"].astype(str).str.lower().str.strip()

# keep only states
population_df = population_df[population_df["Category"] == "State"]

# ---------------------------------------------------
# MERGE DATA
# ---------------------------------------------------

state_summary = population_df.merge(
    ev_summary,
    on="State",
    how="left"
)

state_summary["Total_Stations"] = state_summary["Total_Stations"].fillna(0)
state_summary["Avg_Power_kW"] = state_summary["Avg_Power_kW"].fillna(0)

# ---------------------------------------------------
# POPULATION INDEX
# ---------------------------------------------------

max_population = state_summary["Population"].max()

state_summary["Population_Index"] = (
    state_summary["Population"] / max_population
)

# ---------------------------------------------------
# DENSITY INDEX
# ---------------------------------------------------

max_density = state_summary["Density"].max()

state_summary["Density_Index"] = (
    state_summary["Density"] / max_density
)

# ---------------------------------------------------
# TRAFFIC INDEX (derived from density)
# ---------------------------------------------------

state_summary["Traffic_Density_Index"] = (
    state_summary["Density"] / 1000
)

# ---------------------------------------------------
# DEMAND ESTIMATION MODEL
# ---------------------------------------------------

state_summary["Estimated_Demand_Index"] = (
    0.35 * state_summary["Population_Index"] +
    0.25 * state_summary["Density_Index"] +
    0.20 * state_summary["Traffic_Density_Index"] +
    0.20 * (state_summary["Avg_Power_kW"] / 120)
)

threshold = state_summary["Estimated_Demand_Index"].mean()

state_summary["Infrastructure_Status"] = state_summary[
    "Estimated_Demand_Index"
].apply(lambda x: "⚠ Needs Expansion" if x < threshold else "✅ Adequate")

# ---------------------------------------------------
# SORT RESULTS
# ---------------------------------------------------

state_summary = state_summary.sort_values(
    "Estimated_Demand_Index"
).reset_index(drop=True)

state_summary.index += 1

state_summary["State"] = state_summary["State"].str.title()

# ---------------------------------------------------
# CLEAN DISPLAY TABLE
# ---------------------------------------------------

state_summary_clean = state_summary.drop(
    columns=[
        "Category",
        "Decadal Population Growth Rate - 2001-2011"
    ],
    errors="ignore"
)

# ---------------------------------------------------
# DISPLAY RESULTS
# ---------------------------------------------------

st.subheader("State-Level Infrastructure Analysis")

st.dataframe(state_summary_clean)

# ---------------------------------------------------
# INFRASTRUCTURE STATUS DISTRIBUTION
# ---------------------------------------------------

st.subheader("Infrastructure Status Distribution")

st.bar_chart(state_summary_clean["Infrastructure_Status"].value_counts())

# ---------------------------------------------------
# DEMAND VISUALIZATION
# ---------------------------------------------------

st.subheader("EV Infrastructure Demand by State")

fig2 = px.bar(
    state_summary_clean,
    x="State",
    y="Estimated_Demand_Index",
    color="Infrastructure_Status"
)

st.plotly_chart(fig2, use_container_width=True)

# ---------------------------------------------------
# EV DEMAND HEATMAP
# ---------------------------------------------------

st.subheader("EV Charging Demand Heatmap (India)")

fig_heatmap = px.density_mapbox(
    data,
    lat="Latitude",
    lon="Longitude",
    z="Power_kW",
    radius=25,
    zoom=4,
    height=600,
    mapbox_style="open-street-map",
)

st.plotly_chart(fig_heatmap, use_container_width=True)