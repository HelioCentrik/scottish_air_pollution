# app/maps.py ────────────────────────────────────────────────────────────────────
import json

import pandas as pd
import geopandas as gpd
import duckdb as ddb
import streamlit as st
from plotly import graph_objects as go
from shapely.geometry import Point

from config import SENSOR_FILL, PANEL_BG, PANEL_BORDER, PANEL_H



# def map_sensors_to_wards(sens_df: pd.DataFrame, wards_gdf: gpd.GeoDataFrame, radius_km=50):
#     # Create GeoDataFrame in lat/lon
#     sens_gdf = gpd.GeoDataFrame(
#         sens_df.copy(),
#         geometry=gpd.points_from_xy(sens_df.longitude, sens_df.latitude),
#         crs="EPSG:4326"
#     )
#
#     # Reproject both to a metric CRS (British National Grid, EPSG:27700)
#     sens_proj = sens_gdf.to_crs(epsg=27700)
#     wards_proj = wards_gdf.to_crs(epsg=27700)
#
#     # Buffer sensors to radius (in meters)
#     sens_proj["buffer"] = sens_proj.geometry.buffer(radius_km * 1000)
#
#     # Create GeoDataFrame of buffers
#     sens_buffers = sens_proj.set_geometry("buffer")
#
#     # Spatial join: which wards intersect which sensor buffer?
#     joined = gpd.sjoin(wards_proj, sens_buffers, how="inner", predicate="intersects")
#     print(joined.columns)
#
#     # Result: each row is a ward matched to a sensor
#     return joined[[
#         "location_name", "latitude", "longitude", "geometry_right", "ward_id", "label", "name"
#     ]]


@st.cache_data(show_spinner=False)
def load_geometry():
    # ─── load ward + council shapes ──────────────────────────
    MAIN_CUTOFF_LAT = 58.45  # tweak if Orkney should stay with mainland

    councils = gpd.read_parquet("../data/scotland_ca_2019_simplified.parquet").to_crs(epsg=4326)
    wards = gpd.read_parquet("../data/scotland_wa_2022_simplified.parquet").to_crs(epsg=4326)

    # ward helper cols (1-time)
    wards["ward_id"] = wards.index.astype(str)

    main_councils = councils[councils.centroid.y < MAIN_CUTOFF_LAT]
    islands_councils = councils[councils.centroid.y >= MAIN_CUTOFF_LAT]

    main_wards = wards[wards.centroid.y < MAIN_CUTOFF_LAT]
    islands_wards = wards[wards.centroid.y >= MAIN_CUTOFF_LAT]

    # Prepare GeoJSON from council & ward gdfs
    main_c_js = json.loads(main_councils.to_json())
    islands_c_js = json.loads(islands_councils.to_json())
    main_w_js = json.loads(main_wards.to_json())
    islands_w_js = json.loads(islands_wards.to_json())

    # Load sensor locations only
    con = ddb.connect("../data/scottish_air_quality.duckdb")
    sens = con.execute("""
        SELECT DISTINCT location_id, latitude, longitude, ward_id, location_name, ward_name
        FROM tbl_hours
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
    """).df()
    con.close()

    all_wards = pd.concat([main_wards, islands_wards], ignore_index=True)
    sensor_wards = sens

    return (main_councils, islands_councils, main_wards, islands_wards,
            main_w_js, islands_w_js, main_c_js, islands_c_js,
            sensor_wards, MAIN_CUTOFF_LAT)


@st.cache_data(show_spinner=False)
def build_map_fig(pollutant):
    (main_councils, islands_councils, main_wards, islands_wards,
     main_w_js, islands_w_js, main_c_js, islands_c_js,
     sensor_wards, MAIN_CUTOFF_LAT) = load_geometry()

    fig = go.Figure()

    # ── MAIN map (geo) ──────────────────────────────────────────
    fig.add_trace(go.Choropleth(
        geojson=main_w_js, locations=main_wards["ward_id"],
        z=[1] * len(main_wards), showscale=False,
        colorscale=[[0, "#77CC88"], [1, "#77CC88"]],
        marker_line_width=0, featureidkey="properties.ward_id",
        name="Main wards"))

    fig.add_trace(go.Choropleth(
        geojson=main_c_js, locations=main_councils["name"],
        z=[1] * len(main_councils), showscale=False,
        colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
        marker_line_color="black", marker_line_width=0.5,
        featureidkey="properties.name",
        name="Main councils"))

    # sensors that belong in main panel
    main_sens = sensor_wards[sensor_wards.latitude < MAIN_CUTOFF_LAT]
    fig.add_trace(go.Scattergeo(
        lon=main_sens.longitude, lat=main_sens.latitude,
        mode="markers", marker=dict(size=6, color=SENSOR_FILL),
        geo="geo", hovertext=main_sens.location_name,
        name="Sensors"))

    # ── ISLAND inset (geo2) ─────────────────────────────────────
    fig.add_trace(go.Choropleth(
        geojson=islands_w_js, locations=islands_wards["ward_id"],
        z=[1] * len(islands_wards), showscale=False,
        colorscale=[[0, "#77CC88"], [1, "#77CC88"]],
        marker_line_width=0, featureidkey="properties.ward_id",
        geo="geo2", name="Islands wards"))

    fig.add_trace(go.Choropleth(
        geojson=islands_c_js, locations=islands_councils["name"],
        z=[1] * len(islands_councils), showscale=False,
        colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
        marker_line_color="black", marker_line_width=0.5,
        featureidkey="properties.name", geo="geo2",
        name="Islands councils"))

    isle_sens = sensor_wards[sensor_wards.latitude >= MAIN_CUTOFF_LAT]
    fig.add_trace(go.Scattergeo(
        lon=isle_sens.longitude, lat=isle_sens.latitude,
        mode="markers", marker=dict(size=6, color=SENSOR_FILL),
        geo="geo2", hovertext=isle_sens.location_name,
        name="Isl Sensors"
    ))

    fig.update_layout(
        # MAIN panel domain (full width minus inset slice)
        geo=dict(
            projection=dict(type="conic conformal",
                            parallels=[54, 60], rotation=dict(lon=0)),
            domain=dict(x=[0, 0.64], y=[0, 1]),
            center=dict(lat=56.625, lon=-5.0),
            lonaxis=dict(range=[-9.0, -1.0]),
            lataxis=dict(range=[54.75, 59]),
            # fitbounds="locations",
            visible=False, bgcolor=PANEL_BG
        ),
        geo2=dict(
            framecolor=PANEL_BORDER, framewidth=4,
            projection=dict(type="conic conformal",
                            parallels=[58, 61], rotation=dict(lon=0)),
            domain=dict(x=[0.6, 0.92], y=[0.5, 0.96]),
            center=dict(lat=59.8, lon=-2.125),
            lonaxis=dict(range=[-4.0, -0.25]),
            lataxis=dict(range=[58.75, 61.0]),
            # fitbounds="locations",
            visible=False, bgcolor=PANEL_BG,
            showland=False, showcountries=False,
            showcoastlines=False, showframe=True,
        ),
        legend=dict(
            orientation="h",              # horizontal strip
            yanchor="bottom", y=1.02,     # hover just above the map
            xanchor="right",  x=0.975,        # right-aligned
            font=dict(color="#CCD")       # style to taste
        ),
        # bgcolor="#FFFFFF",
        height=PANEL_H,
        margin=dict(l=0, r=0, t=0, b=0),
        dragmode=False,
    )

    return fig
