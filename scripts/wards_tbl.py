# scripts/wards_tbl.py
import json

import pandas as pd
import geopandas as gpd
import duckdb as ddb



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

# Load locations with lat/lon only
con = ddb.connect("../data/scottish_air_quality.duckdb")
loc = con.execute("""
    SELECT DISTINCT location_id, longitude, latitude
    FROM vw_hours
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL
""").df()
con.close()

all_wards = pd.concat([main_wards, islands_wards], ignore_index=True)

radius_km = 12

# Create GeoDataFrame in lat/lon
loc_gdf = gpd.GeoDataFrame(
    loc.copy(),
    geometry=gpd.points_from_xy(loc.longitude, loc.latitude),
    crs="EPSG:4326"
)

# Reproject both to a metric CRS (British National Grid, EPSG:27700)
loc_proj = loc_gdf.to_crs(epsg=27700)
wards_proj = all_wards.to_crs(epsg=27700)

# Buffer sensors to radius (in meters)
loc_proj["buffer"] = loc_proj.geometry.buffer(radius_km * 1000)

# Create GeoDataFrame of buffers
loc_buffers = loc_proj.set_geometry("buffer")

# Spatial join: which wards intersect which sensor buffer?
location_wards = gpd.sjoin(wards_proj, loc_buffers, how="inner", predicate="intersects")
ward_data = location_wards[[
    "location_id", "geoid", "ward_id", "label", "name"
]]
print(f"Wards:\n"
      f"Columns: {ward_data.columns}\n"
      f"{len(ward_data.values)} records.\n"
      f"Wards:\n{ward_data.values}")

con = ddb.connect("../data/scottish_air_quality.duckdb")
con.execute("DROP TABLE IF EXISTS location_wards")
con.register("location_wards_df", ward_data)
con.execute("""
    CREATE TABLE location_wards AS
    SELECT
        location_id,
        geoid AS geo_id,
        ward_id,
        label AS ward_label,
        name AS ward_name
    FROM location_wards_df
""").df()
con.close()
