import osmnx as ox
import streamlit as st

@st.cache_data
def calculate_state_traffic(state_name, state_data):
    try:
        north = state_data["Latitude"].max()
        south = state_data["Latitude"].min()
        east = state_data["Longitude"].max()
        west = state_data["Longitude"].min()

        G = ox.graph_from_bbox(north, south, east, west, network_type="drive")
        edges = ox.graph_to_gdfs(G, nodes=False)

        total_road_length = edges["length"].sum() / 1000

        lat_diff = north - south
        lon_diff = east - west
        approx_area = (lat_diff * 111) * (lon_diff * 111)

        if approx_area == 0:
            return 0

        density = total_road_length / approx_area
        return density

    except:
        return 0