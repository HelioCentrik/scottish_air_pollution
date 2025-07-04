import requests
import time
import csv

from pytz import country_names

import pandas as pd
import duckdb

API_KEY = "e5b11c17e495635d844b95a982ffba93864845a8cdb2463c9863c5ff9d5f4e28"
BASE_URL = "https://api.openaq.org/v3/locations"
HEADERS = {"x-scripts-key": API_KEY}

params = {
    # "country_id": 79,
    "limit": 1000,
    "page": 1,
    # "offset": 0,
    # "status": "active",
    "bbox": "-7.7,54.7,-0.9,60.9",
}

response = requests.get(BASE_URL, headers=HEADERS, params=params)
data = response.json()
print(f"API Status: {response.status_code}")

# Load location IDs from DuckDB instead of hardcoding
con = duckdb.connect("../data/scottish_air_quality.duckdb")
location_ids = set(con.execute("SELECT location_id FROM locations").fetchdf()["location_id"])
con.close()

locations = []
if not data.get("results"):
    print("❌ No results found.")
else:
    for loc in data["results"]:
        country = loc.get("country", {})
        locality = loc.get("locality") or ""
        lat, lon = dict(loc.get('coordinates')).values()
        provider = loc.get('provider')
        # if country.get("code") == "GB" and any(city in [loc.get("name"), locality] for city in SCOTTISH_CITIES):
        if loc.get('id') in location_ids:
            # locations.append([loc.get('id'), loc.get('name'), locality, lat, lon])
            locations.append([loc.get('id'), provider.get('name')])
            # print(locations[-1])
            # print(loc)

# locations.sort(key=lambda x: x[1])
# for loc in locations:
#     print(loc)

# Create dataframe
columns = ["location_id", "provider_name"]
df = pd.DataFrame(locations, columns=columns)

# Connect to a DuckDB file
con = duckdb.connect("../data/scottish_air_quality.duckdb")

# Create and populate 'locations' table
con.execute("DROP TABLE IF EXISTS location_providers")
con.execute("""
    CREATE TABLE location_providers AS
    SELECT * FROM df
""")

print(con.execute("SELECT location_id, provider_name FROM location_providers").fetchdf())
con.close()
