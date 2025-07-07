# ui_styles.py ────────────────────────────────────────────────────────────────────
import streamlit as st

import config as cnst



# Inject a bit of CSS for rounded containers / colours
def inject_dashboard_style(
        page_bg=cnst.PAGE_BG,
        panel_bg=cnst.PANEL_BG,
        border=cnst.PANEL_BORDER,
        panel_h=cnst.PANEL_H,
        legend_h=cnst.LEGEND_H
):
    st.markdown(fr"""
    <style>
    /* Tighten top padding & page margin */
    section.main > div:first-child     {{ padding-top: 0rem; }}
    div.block-container               {{ padding-top: 1.8rem }}
    
    /* Set the full page background */
    html, body, [data-testid="stAppViewContainer"], header[data-testid="stHeader"] {{
        background-color: {page_bg};
    }}
    
    /* Universal style for Plotly charts ONLY */
    div[data-testid="stPlotlyChart"] {{
        background   : {panel_bg};
        border       : 1px solid {border};
        border-radius: 6px;
        padding      : 10px;
        box-shadow   : 0 0 8px #00112266;
        overflow     : hidden;
    }}
    
    /* Optional: inner canvas */
    div[data-testid="stPlotlyChart"] > div {{
        background: {panel_bg} !important;
        height: 100% !important;
        width: 100% !important;
    }}
    
    /* Panel height + centering layout */
    .equal-panel {{
        height: {panel_h}px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }}
    
    /* Use this ONLY for custom HTML cards (legend, future widgets) */
    .card {{
        height       : {legend_h}px;
        background   : {panel_bg};
        border       : 1px solid {border};
        border-radius: 6px;
        box-shadow   : 0 0 8px #00112266;
        padding      : 10px;
        overflow     : hidden;
    }}
    
    /* Legend: gradient bar with spacing inside .card */
    .legend-scale {{
        width : 36px;
        height: 100%;
        margin: 12px;
        border-radius: 2px;
        background: linear-gradient(to top, #a8eec1, #006400);
    }}
    </style>
    """, unsafe_allow_html=True)
