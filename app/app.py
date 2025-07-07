# app.py ────────────────────────────────────────────────────────────────────
import json
import math

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import geopandas as gpd
import duckdb as ddb

from ui_styles import inject_dashboard_style
from data import load_geometry



# ---------- 1. Page config & dark theme ----------
st.set_page_config(
    page_title="Scottish Air Quality Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

PAGE_BG = str("#091023")
# panel_bg = str("#1b1e27")
PANEL_BG = str("rgba(0, 0, 0, 0)")
PANEL_BORDER = str("#334466")

SENSOR_FILL = str("#f00f3c")

PANEL_H = 720
LEGEND_H = PANEL_H * 1.03
TIME_H = 180

inject_dashboard_style()

# ---------- 2. Sidebar controls ----------
with st.sidebar:
    pollutant   = st.selectbox("Pollutant", ["pm25", "pm10", "no2"])
    agg_choice  = st.selectbox(
        "Aggregation",
        ["Hourly (avg by day)", "Daily (avg by week)",
         "Monthly (avg by year)"]
    )
    st.write("")


@st.cache_data(show_spinner=False)
def build_map_fig(pollutant):
    (main_councils, islands_councils, main_wards, islands_wards,
     main_w_js, islands_w_js, main_c_js, islands_c_js,
     sens, MAIN_CUTOFF_LAT) = load_geometry()

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
    main_sens = sens[sens.latitude < MAIN_CUTOFF_LAT]
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

    isle_sens = sens[sens.latitude >= MAIN_CUTOFF_LAT]
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

@st.cache_data(show_spinner=False)
def build_line_fig(pollutant, agg_choice):
    # TODO: query DuckDB and return a line Plotly fig
    dummy = pd.DataFrame({
        "x":[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "y":[1, 4, 2, 8, 7, 13, 12, 8, 3, 4]
    })
    fig = go.Figure(go.Scatter(x=dummy["x"], y=dummy["y"],
                               mode="lines", line=dict(color="#03dac6")))
    fig.update_layout(height=180, margin=dict(l=0, r=32, t=10, b=20),
                      plot_bgcolor=PANEL_BG, paper_bgcolor=PANEL_BG,
                      xaxis=dict(color="#8fa"), yaxis=dict(color="#8fa"))
    return fig


# ---------- 4. Layout ----------
st.markdown("<h2 style='text-align:center; color:#aad;'>Scottish Air Quality Dashboard</h2>", unsafe_allow_html=True)
st.write("")

with st.container():  # unified block so vertical spacing syncs
    _, left, center, right, _ = st.columns([1, 0.4, 3.85, 0.75, 1])

    with left:
        st.markdown(
            '<div class="card equal-panel">'
            '    <div class="legend-scale"></div>'
            '</div>',
            unsafe_allow_html=True
        )

    with center:
        with st.container() as c_map:
            # st.markdown('<div class="block equal-panel">', unsafe_allow_html=True)
            map_fig = build_map_fig(pollutant)
            map_fig.update_layout(height=PANEL_H, paper_bgcolor=PANEL_BG)
            st.plotly_chart(
                map_fig,
                use_container_width=True,
                config=dict(displayModeBar=False)
            )
            # st.markdown('</div>', unsafe_allow_html=True)


    with right:
        # st.markdown('<div class="block equal-panel">', unsafe_allow_html=True)
        right_chart = go.Figure(go.Bar(y=[12, 34, 23], x=["PM2.5","PM10", "NO2"],
                                       orientation='v',
                                       marker_color=["#66ee88","#22aaee", "#eeaa66"]))
        right_chart.update_layout(height=PANEL_H, margin=dict(l=20, r=20, t=0, b=0),
                                  xaxis=dict(color="#8fa"),
                                  plot_bgcolor=PANEL_BG,
                                  paper_bgcolor="rgba(0, 0, 0, 0)"
                                  )
        st.plotly_chart(right_chart, use_container_width=True)
        # st.markdown('</div>', unsafe_allow_html=True)

with st.container():
    # bottom full-width line chart
    _, time_chart, _ = st.columns([1, 5.075, 1])

    line_fig = build_line_fig(pollutant, agg_choice)
    line_fig.update_layout(height=TIME_H)
    with time_chart:
        # st.markdown("<hr>", unsafe_allow_html=True)
        # st.markdown(f'<div class="block" style="height:{TIME_H}px">', unsafe_allow_html=True)
        st.plotly_chart(
            line_fig,
            use_container_width=True,
            config=dict(displayModeBar=False)
        )
        # st.markdown('</div>', unsafe_allow_html=True)
