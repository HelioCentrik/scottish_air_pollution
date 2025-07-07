# app.py ────────────────────────────────────────────────────────────────────

import streamlit as st
import plotly.graph_objects as go

from config import PANEL_H, PANEL_BG, TIME_H
from charts import build_line_fig
from maps import build_map_fig
from ui_styles import inject_dashboard_style



# ---------- 1. Page config & dark theme ----------
st.set_page_config(
    page_title="Scottish Air Quality Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

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
