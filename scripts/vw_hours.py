from operator import index

import duckdb



con = duckdb.connect("../data/scottish_air_quality.duckdb")

# df = con.execute("""
#     SELECT * FROM measurements LIMIT 10;
# """).fetchdf()

print(con.execute("""
    CREATE OR REPLACE VIEW vw_hours AS
    SELECT
        loc.location_id,
        loc.location_name,
        loc.locality,
        loc.latitude,
        loc.longitude,
        wrd.geo_id,
        wrd.ward_id,
        wrd.ward_label,
        wrd.ward_name,
        sen.sensor_id,
        sen.parameter_name,
        sen.display_name,
        sen.units,
        meas.measurement_id,
        meas.value,
        meas.datetime_from,
        meas.datetime_to,
        loc.provider,
        CAST(meas.datetime_from AS Date) AS "date_from",
        strftime(CAST(meas.datetime_from AS Datetime), '%H') AS "hour_of_day",
        strftime(CAST(meas.datetime_from AS Date), '%w') AS "day_of_week_num",
        strftime(CAST(meas.datetime_from AS Date), '%A') AS "day_of_week",
        strftime(CAST(meas.datetime_from AS Date), '%-m') AS "month_num",
        strftime(CAST(meas.datetime_from AS Date), '%B') AS "month_name"
    FROM locations loc
        INNER JOIN location_wards wrd
            ON loc.location_id = wrd.location_id
        INNER JOIN sensors sen
            ON loc.location_id = sen.location_id
        INNER JOIN measurements meas
            ON sen.sensor_id = meas.sensor_id;
"""))

print(con.execute("SELECT COUNT(*) FROM vw_hours").fetchdf())
# print(df.head(5).to_string(index=False))

con.close()
