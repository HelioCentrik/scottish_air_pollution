import requests
import time
import csv

from openaq import OpenAQ
from pytz import country_names

import pandas as pd
import openaq
import duckdb



API_KEY = "e5b11c17e495635d844b95a982ffba93864845a8cdb2463c9863c5ff9d5f4e28"
# BASE_URL = "https://api.openaq.org/v3/locations"
# HEADERS = {"x-scripts-key": API_KEY}

client = OpenAQ(api_key=API_KEY)

limit = 1000
page = 1
bbox = [-7.7,54.7,-0.9,60.9]
data = {}

try:
    client = OpenAQ(api_key=API_KEY)
    data = client.locations.list(bbox=bbox, limit=limit, page=page)
except Exception as e:
    print("❌ General error:", e)
else:
    print(f"✅ Request succeeded. {len(data.results)} results.")

# Load location IDs from DuckDB instead of hardcoding
con = duckdb.connect("../data/scottish_air_quality.duckdb")
location_ids = set(con.execute("SELECT location_id FROM locations").fetchdf()["location_id"])
con.close()

sensors = []

if not data.results:
    print("❌ No results found.")
else:
    for loc in data.results:
        country = loc.country
        locality = loc.locality or ""
        lat, lon = (loc.coordinates.latitude, loc.coordinates.longitude)
        if loc.id in location_ids:
            for sensor in loc.sensors:
                param = sensor.parameter
                sensors.append([sensor.id, loc.id, param.id, param.name, param.display_name, param.units])

            # print(loc)

sensors.sort(key=lambda x: (x[1], x[2]))
for s in sensors:
    print(s)

# # Create dataframe
# columns = ["sensor_id", "location_id", "parameter_id", "parameter_name", "display_name", "units"]
# df = pd.DataFrame(sensors, columns=columns)
#
# # Connect to a DuckDB file
# con = data.connect("../scottish_air_quality.data")
#
# # Create and populate 'locations' table
# con.execute("DROP TABLE IF EXISTS sensors")
# con.execute("""
#     CREATE TABLE sensors AS
#     SELECT * FROM df
# """)
#
# print(con.execute("SELECT * FROM sensors ORDER BY location_id, parameter_id").fetchdf())

client.close()
