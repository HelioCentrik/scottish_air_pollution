# data.py ────────────────────────────────────────────────────────────────────
import json

import streamlit as st
import geopandas as gpd
import duckdb as ddb



# ---------- 3. Helper st.cache wrappers ----------
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
        SELECT DISTINCT latitude, longitude, location_name
        FROM vw_hours
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
    """).df()
    con.close()

    return (main_councils, islands_councils, main_wards, islands_wards,
            main_w_js, islands_w_js, main_c_js, islands_c_js,
            sens, MAIN_CUTOFF_LAT)
