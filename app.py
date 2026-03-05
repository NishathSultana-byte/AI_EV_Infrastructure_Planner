import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

st.set_page_config(page_title="AI EV Infrastructure Planner", layout="wide")

st.title("AI-Based EV Charging Infrastructure Planner (India)")

# ---------------------------
# LOAD EV DATA
# ---------------------------
@st.cache_data
def load_data():
    return pd.read_csv("india_ev_stations.csv")

data = load_data()

# ---------------------------
# CLEAN STATE NAMES (VERY IMPORTANT)
# ---------------------------
data["State"] = data["State"].astype(str).str.lower().str.strip()

# Fix common abbreviations & typos
state_mapping = {
    "mh": "maharashtra",
    "mp": "madhya pradesh",
    "gj": "gujarat",
    "rj": "rajasthan",
    "keraka": "kerala",
    "lerala": "kerala",
    "new delhi": "delhi",
    "tamilnadu": "tamil nadu",
    "uttaranchal": "uttarakhand",
    "AP" :"Andhra Pardesh",
    "AndhraPardesh": "Andhra Pardesh",
    "assam": "Assam"

}

data["State"] = data["State"].replace(state_mapping)

st.subheader("Raw EV Charging Data")
st.write(f"Total Stations Loaded: {len(data)}")
st.dataframe(data)

# ---------------------------
# REMOVE MISSING COORDINATES
# ---------------------------
data = data.dropna(subset=["Latitude", "Longitude"])

# ---------------------------
# CLUSTERING
# ---------------------------
features = data[["Latitude", "Longitude", "Power_kW"]]

scaler = StandardScaler()
scaled_features = scaler.fit_transform(features)

k = st.slider("Select Number of Clusters", 2, 8, 4)

kmeans = KMeans(n_clusters=k, random_state=42)
data["Cluster"] = kmeans.fit_predict(scaled_features)

st.subheader("EV Charging Station Clusters")

fig = px.scatter_mapbox(
    data,
    lat="Latitude",
    lon="Longitude",
    color="Cluster",
    hover_name="Station_Name",
    zoom=4,
    height=600
)

fig.update_layout(mapbox_style="open-street-map")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Cluster Distribution")
st.bar_chart(data["Cluster"].value_counts())

# ---------------------------
# CREATE STATE SUMMARY
# ---------------------------
st.subheader("📊 State-Level Infrastructure Analysis")

# ---------------------------
# EV STATION SUMMARY
# ---------------------------

ev_summary = data.groupby("State").agg(
    Total_Stations=("Station_Name", "count"),
    Avg_Power_kW=("Power_kW", "mean")
).reset_index()

# ---------------------------
# LOAD POPULATION DATA
# ---------------------------

population_df = load_population_data()

population_df.columns = population_df.columns.str.strip()

population_df = population_df.rename(columns={
    "India/State/Union Territory": "State",
    "Population 2011": "Population"
})

# Keep only states
population_df = population_df[population_df["Category"] == "State"]

# Clean state names
population_df["State"] = population_df["State"].str.lower().str.strip()

# ---------------------------
# MERGE EV DATA INTO POPULATION
# ---------------------------

state_summary = population_df.merge(
    ev_summary,
    on="State",
    how="left"
)

# Fill missing EV data (states with no stations)
state_summary["Total_Stations"] = state_summary["Total_Stations"].fillna(0)
state_summary["Avg_Power_kW"] = state_summary["Avg_Power_kW"].fillna(0)

# ---------------------------
# POPULATION INDEX
# ---------------------------

max_population = state_summary["Population"].max()

state_summary["Population_Index"] = (
    state_summary["Population"] / max_population
)

# ---------------------------
# DEMAND ESTIMATION
# ---------------------------

state_summary["Estimated_Demand_Index"] = (
    state_summary["Total_Stations"] * 0.5 +
    state_summary["Avg_Power_kW"] * 0.3 +
    state_summary["Population_Index"] * 0.2
)

threshold = state_summary["Estimated_Demand_Index"].mean()

state_summary["Infrastructure_Status"] = state_summary[
    "Estimated_Demand_Index"
].apply(lambda x: "⚠ Needs Expansion" if x < threshold else "✅ Adequate")

# Sort results
state_summary = state_summary.sort_values(
    "Estimated_Demand_Index"
).reset_index(drop=True)

state_summary.index += 1

st.dataframe(state_summary)

# ---------------------------
# LOAD POPULATION DATA
# ---------------------------
@st.cache_data
def load_population_data():
    return pd.read_csv("state_population_india.csv")

population_df = load_population_data()

population_df.columns = population_df.columns.str.strip()

population_df = population_df.rename(columns={
    "India/State/Union Territory": "State",
    "Population 2011": "Population"
})

population_df["State"] = population_df["State"].astype(str).str.lower().str.strip()

# Keep both States and Union Territories
population_df = population_df[
    population_df["Category"].isin(["State", "Union Territory"])
]

# ---------------------------
# MERGE POPULATION
# ---------------------------
state_summary = state_summary.merge(
    population_df[["State", "Population"]],
    on="State",
    how="left"
)

# Instead of forcing 0, keep NaN so we can debug
state_summary["Population"] = state_summary["Population"].fillna(
    state_summary["Population"].median()
)

# ---------------------------
# POPULATION INDEX
# ---------------------------
max_population = state_summary["Population"].max()
state_summary["Population_Index"] = (
    state_summary["Population"] / max_population
)

# ---------------------------
# DEMAND ESTIMATION
# ---------------------------
state_summary["Estimated_Demand_Index"] = (
    state_summary["Total_Stations"] * 0.5 +
    state_summary["Avg_Power_kW"] * 0.3 +
    state_summary["Population_Index"] * 0.2
)

threshold = state_summary["Estimated_Demand_Index"].mean()

state_summary["Infrastructure_Status"] = state_summary[
    "Estimated_Demand_Index"
].apply(lambda x: "⚠ Needs Expansion" if x < threshold else "✅ Adequate")

# Sort
state_summary = state_summary.sort_values(
    "Estimated_Demand_Index"
).reset_index(drop=True)

state_summary.index += 1

st.subheader("State-Level Infrastructure Analysis")
st.dataframe(state_summary)

st.subheader("Infrastructure Status Distribution")
st.bar_chart(state_summary["Infrastructure_Status"].value_counts())