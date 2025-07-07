# app/charts.py ────────────────────────────────────────────────────────────────────
import pandas as pd
import streamlit as st
from plotly import graph_objects as go

from config import PANEL_BG



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
