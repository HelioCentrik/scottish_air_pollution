from datetime import date, datetime
import time
from httpx import Timeout

import pandas as pd
from openaq import OpenAQ
from openaq.shared import exceptions as aqerr
import duckdb



API_KEY = "e5b11c17e495635d844b95a982ffba93864845a8cdb2463c9863c5ff9d5f4e28"
# BASE_URL = "https://api.openaq.org/v3/locations"
# HEADERS = {"x-scripts-key": API_KEY}

# Load location IDs from DuckDB instead of hardcoding
con = duckdb.connect("../data/scottish_air_quality.duckdb")

# load all sensor ids
sensor_all = set(con.execute("SELECT sensor_id FROM sensors").fetchdf()["sensor_id"])

# load all fully completed sensor ids
sensors_complete = set(con.execute("""
    SELECT sensor_id
    FROM measurements
    GROUP BY sensor_id
    HAVING YEAR(MAX(CAST(datetime_to AS Date))) = 2025
""").fetchdf()["sensor_id"])

# remaining sensor ids to be collected
sensor_ids = sensor_all - sensors_complete

con.close()

limit = 1000
datetime_from = date(2020, 1, 1)
datetime_to = date.today()
year_range = range(2020, datetime_to.year + 1)

data = {}
all_measurements = []

client = OpenAQ(api_key=API_KEY)

try:
    for sensor_id in sensor_ids:
        for year in year_range:
            start = datetime(year, 1, 1)
            end = datetime(year + 1, 1, 1) if year < datetime_to.year else datetime.combine(datetime_to, datetime.min.time())

            page = 1
            while True:
                try:
                    data = client.measurements.list(
                        sensors_id=sensor_id,
                        data='hours',
                        datetime_from=start,
                        datetime_to=end,
                        limit=limit,
                        page=page
                    )

                    if not data.results:
                        break

                    print(f"Page {page}: {len(data.results)} results")
                    for record in data.results:
                        # print(f"\t{record}")
                        period = record.period
                        all_measurements.append([
                            sensor_id,
                            record.value,
                            period.label,
                            period.interval,
                            period.datetime_from.utc,
                            period.datetime_to.utc
                        ])
                        # print(all_measurements[-1])
                    print(f"Sensor: {sensor_id} - {data.results[-1].period.datetime_from.utc}, {data.results[-1].period.datetime_to.utc}")
                    page += 1

                    time.sleep(1)
                except aqerr.GatewayTimeoutError as e:
                    print(f"❌ API timeout error on sensor {sensor_id}, year {year}, page {page}: {e}")
                    break
                except aqerr.ClientError as e:
                    print(f"❌ API error on sensor {sensor_id}, year {year}, page {page}: {e}")
                    break
except Exception as e:
    print(f"❌ General error: {e}")
finally:
    client.close()
    print(f"✅ Request succeeded. {len(all_measurements)} results.")

# Create dataframe
columns = ["sensor_id", "value", "label", "interval", "datetime_from", "datetime_to"]
df = pd.DataFrame(all_measurements, columns=columns)
df = df.drop_duplicates(subset=["sensor_id", "datetime_from", "datetime_to"])
df.insert(0, "measurement_id", pd.Series(range(1, len(df) + 1)))
df.to_csv("failed_append_backup.csv", index=False)

# Connect to a DuckDB file
con = duckdb.connect("../data/scottish_air_quality.duckdb")

# Create and populate 'measurements' table
# con.execute("DROP TABLE IF EXISTS measurements;")
# con.execute("""
#     CREATE TABLE measurements AS
#     SELECT
#         ROW_NUMBER() OVER () AS measurement_id,
#         *
#     FROM df;
# """)
# con.execute("""
#     CREATE UNIQUE INDEX idx_unq_measurement ON measurements(sensor_id, datetime_from, datetime_to);
# """)

# Get existing keys into a set (efficient)
existing = con.execute("""
    SELECT sensor_id, datetime_from, datetime_to
    FROM measurements
""").fetchdf()

# Merge and keep only NEW rows
df = df.merge(existing, on=["sensor_id", "datetime_from", "datetime_to"], how="left", indicator=True)
df = df[df["_merge"] == "left_only"].drop(columns=["_merge"])

con.execute("""
    CREATE TABLE IF NOT EXISTS measurements (
        measurement_id INTEGER,
        sensor_id INTEGER,
        value DOUBLE,
        label TEXT,
        interval TEXT,
        datetime_from TIMESTAMP,
        datetime_to TIMESTAMP
    )
""")
con.execute("INSERT INTO measurements SELECT * FROM df")

print(con.execute("SELECT * FROM measurements ORDER BY sensor_id, measurement_id").fetchdf())

con.close()
