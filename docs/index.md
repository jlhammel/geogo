# Welcome to geogo


[![image](https://img.shields.io/pypi/v/geogo.svg)](https://pypi.python.org/pypi/geogo)
[![GEOGO logo](https://raw.githubusercontent.com/jlhammel/geogo/main/docs/GEOGO.png)](https://github.com/jlhammel/geogo/blob/main/docs/GEOGO.png)

**A python package for geospatial analysis and mapping hurricane tracks**


-   Free software: MIT License
-   GitHub repo: https://github.com/jlhammel/geogo
-   Documentation: <https://jlhammel.github.io/geogo>

-   Geogo is a Python package meant for climatologists to analyze hurricane data from HURDAT2. Geogo uses ipyleaflet to create interactive maps for analysis. This package will allow you to use WMS, raster, geojson, image, and video files to further understand the impact of past hurricanes. Using interactive maps, hurricane track data from the Python package tropycal, and NASA GIBS data the user can track the hurricane and analyze the landscape around the impacted areas.

## Requirements:
- fiona
- folium
- geopandas
- ipyleaflet
- leafmap
- localtileserver
- mapclassify
- matplotlib
- numpy
- tropycal

## Features

- Process geospatial data
- Track past hurricanes impacting the Americas
- Analyse hurricanes using images, raster, video, WMS and geojson files

## Usage
```python
import geogo
import os
```
- Install from GitHub
  ```python
  pip install git+https://github.com/jlhammel/geogo
  ```