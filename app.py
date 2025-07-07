# app.py ────────────────────────────────────────────────────────────────────
import json
import math

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import geopandas as gpd
import duckdb as ddb



# ---------- 1. Page config & dark theme ----------
st.set_page_config(
    page_title="Scottish Air Quality Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

PANEL_H = 720
TIME_H = 180

BG_DARK = "#1b1e27"
# BG_DARK = "rgba(0, 0, 0, 0)"

# Inject a bit of CSS for rounded containers / colours

st.markdown(fr"""
<style>
/* Universal style for Plotly charts ONLY */
div[data-testid="stPlotlyChart"] {{
    background   : {BG_DARK};
    border       : 1px solid #0090ff;
    border-radius: 6px;
    padding      : 10px;
    box-shadow   : 0 0 8px #00112266;
    overflow     : hidden;
}}

/* Optional: inner canvas */
div[data-testid="stPlotlyChart"] > div {{
    background: {BG_DARK} !important;
    height: 100% !important;
    width: 100% !important;
}}

/* Panel height + centering layout */
.equal-panel {{
    height: {PANEL_H}px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
}}

/* Use this ONLY for custom HTML cards (legend, future widgets) */
.card {{
    background   : {BG_DARK};
    border       : 1px solid #0090ff;
    border-radius: 6px;
    box-shadow   : 0 0 8px #00112266;
    padding      : 10px;
    overflow     : hidden;
}}

/* Legend: gradient bar with spacing inside .card */
.legend-scale {{
    width : 36px;
    height: calc(100% - 24px);
    margin: 12px;
    border-radius: 2px;
    background: linear-gradient(to top, #a8eec1, #006400);
}}
</style>
""", unsafe_allow_html=True)

# ---------- 2. Sidebar controls ----------
with st.sidebar:
    pollutant   = st.selectbox("Pollutant", ["pm25", "pm10", "no2"])
    agg_choice  = st.selectbox(
        "Aggregation",
        ["Hourly (avg by day)", "Daily (avg by week)",
         "Monthly (avg by year)"]
    )
    st.write("")


# ---------- 3. Helper st.cache wrappers ----------
@st.cache_data(show_spinner=False)
def load_geometry():
    # ─── load ward + council shapes ──────────────────────────
    MAIN_CUTOFF_LAT = 58.45  # tweak if Orkney should stay with mainland

    councils = gpd.read_parquet("data/scotland_ca_2019_simplified.parquet").to_crs(epsg=4326)
    wards = gpd.read_parquet("data/scotland_wa_2022_simplified.parquet").to_crs(epsg=4326)

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
    con = ddb.connect("data/scottish_air_quality.duckdb")
    sens = con.execute("""
        SELECT DISTINCT latitude, longitude, location_name
        FROM vw_hours
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
    """).df()
    con.close()

    return (main_councils, islands_councils, main_wards, islands_wards,
            main_w_js, islands_w_js, main_c_js, islands_c_js,
            sens, MAIN_CUTOFF_LAT)


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
        marker_line_color="black", marker_line_width=1,
        featureidkey="properties.name",
        name="Main councils"))

    # sensors that belong in main panel
    main_sens = sens[sens.latitude < MAIN_CUTOFF_LAT]
    fig.add_trace(go.Scattergeo(
        lon=main_sens.longitude, lat=main_sens.latitude,
        mode="markers", marker=dict(size=6, color="#EE4455"),
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
        marker_line_color="black", marker_line_width=1,
        featureidkey="properties.name", geo="geo2",
        name="Islands councils"))

    isle_sens = sens[sens.latitude >= MAIN_CUTOFF_LAT]
    fig.add_trace(go.Scattergeo(
        lon=isle_sens.longitude, lat=isle_sens.latitude,
        mode="markers", marker=dict(size=6, color="#EE4455"),
        geo="geo2", hovertext=isle_sens.location_name,
        name="Isl Sensors"))

    fig.update_layout(
        # MAIN panel domain (full width minus inset slice)
        geo=dict(
            domain=dict(x=[0, 0.68], y=[0, 1]),
            center=dict(lat=56.8, lon=-4.4),
            projection=dict(type="conic conformal",
                            parallels=[50, 60], rotation=dict(lon=0)),
            fitbounds="locations",
            visible=False, bgcolor=str(BG_DARK)
        ),
        geo2=dict(
            domain=dict(x=[0.62, 0.86], y=[0.55, 0.96]),
            center=dict(lat=60.35, lon=-1.24),
            projection=dict(type="conic conformal",
                            parallels=[50, 60], rotation=dict(lon=0)),
            fitbounds="locations",
            visible=False, bgcolor=str(BG_DARK),
            showland=False, showcountries=False,
            showcoastlines=False, showframe=True,
            framecolor="#0090FF", framewidth=3
        ),
        legend=dict(
            orientation="h",              # horizontal strip
            yanchor="bottom", y=1.02,     # hover just above the map
            xanchor="right",  x=0.975,        # right-aligned
            # bgcolor="rgba(0,0,0,0)",      # transparent
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
    dummy = pd.DataFrame({"x":[1,2,3], "y":[1,4,2]})
    fig = go.Figure(go.Scatter(x=dummy["x"], y=dummy["y"],
                               mode="lines", line=dict(color="#03dac6")))
    fig.update_layout(height=180, margin=dict(l=0, r=0, t=5, b=5),
                      plot_bgcolor=BG_DARK, paper_bgcolor=BG_DARK,
                      xaxis=dict(color="#8fa"), yaxis=dict(color="#8fa"))
    return fig


# ---------- 4. Layout ----------
st.markdown("<h2 style='text-align:center; color:#aad;'>Scottish Air Quality Dashboard</h2>", unsafe_allow_html=True)
st.write("")

with st.container():  # unified block so vertical spacing syncs
    _, left, center, right, _ = st.columns([1, 0.333, 3.867, 0.75, 1])

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
            map_fig.update_layout(height=PANEL_H, paper_bgcolor=BG_DARK)
            st.plotly_chart(
                map_fig,
                use_container_width=True,
                config=dict(displayModeBar=False)
            )
            # st.markdown('</div>', unsafe_allow_html=True)


    with right:
        # st.markdown('<div class="block equal-panel">', unsafe_allow_html=True)
        right_chart = go.Figure(go.Bar(y=[12, 34], x=["PM2.5","PM10"],
                                       orientation='v',
                                       marker_color=["#66ee88","#22aaee"]))
        right_chart.update_layout(height=PANEL_H, margin=dict(l=20,r=20,t=0,b=0),
                                  xaxis=dict(color="#8fa"),
                                  plot_bgcolor=BG_DARK,
                                  # paper_bgcolor="#1b1e27"
        )
        st.plotly_chart(right_chart, use_container_width=True)
        # st.markdown('</div>', unsafe_allow_html=True)

with st.container():
    # bottom full-width line chart
    _, time_chart, _ = st.columns([1, 5, 1])

    line_fig = build_line_fig(pollutant, agg_choice)
    line_fig.update_layout(height=TIME_H)
    with time_chart:
        # st.markdown("<hr>", unsafe_allow_html=True)
        # st.markdown(f'<div class="block" style="height:{TIME_H}px">', unsafe_allow_html=True)
        st.plotly_chart(line_fig, use_container_width=True)
        # st.markdown('</div>', unsafe_allow_html=True)
