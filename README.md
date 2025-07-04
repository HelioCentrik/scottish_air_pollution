Scottish Air Pollution Dashboard
================================

This project visualizes air quality data across Scotland's 32 council areas using interactive geospatial maps. It overlays sensor data on top of simplified council boundaries and enables regional pollution analysis.

Core Goals
----------
- Load and simplify council boundary geometries (shapefiles).
- Map air quality sensor locations to regions.
- Enable choropleth-style visualizations of pollution by area.
- Prepare for timelapse-based animation of hourly data (~1.28M rows).
- Keep map visuals fast and clean (no globe, no unnecessary zooming).
- Optionally integrate illness/hospital overlays later.

Tech Stack
----------
- Python 3.12+
- GeoPandas (geometry ops)
- DuckDB (querying + fast analytics)
- Plotly (map visualization)
- Shapely (geometry handling)
- PyArrow (for Parquet support)
- Pandas (data wrangling)

Usage Notes
-----------
- Map is rendered in Plotly with Scotland-only zoom and solid background.
- Some regions have no sensors; we're currently deciding how to interpolate or label them.
- DuckDB file is excluded from zip packaging due to size.

Maintainer Notes
----------------
- Use `zip_project.bat` to create a clean project zip, excluding `.duckdb`, `.venv`, and PyCharm files.
- Be cautious of Dark Reader or other browser extensions affecting visual appearance.
- Visual load time should now be <5s. If not, simplify shapes further or profile `test_plotly.py`.

License
-------
MIT or Unlicense — TBD
