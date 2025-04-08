"""This module provides a custom Map class that extends the folium.Map class"""

import folium
import folium.plugins
import os


class Map(folium.Map):
    def __init__(self, center=(0, 0), zoom=2, **kwargs):
        super().__init__(location=center, zoom_start=zoom, **kwargs)

    def add_basemap(self, basemap="OpenTopoMap"):
        """Add basemap to the map.

        Args:
            basemap (str, optional): Basemap name. Defaults to "OpenTopoMap".
        """

        url = eval(f"folium.basemaps.{basemap}").build_url()
        layer = folium.TileLayer(url=url, name=basemap)
        self.add(layer)

    def add_geojson(
        self,
        data,
        zoom_to_layer=True,
        hover_style=None,
        **kwargs,
    ):
        """Add a GeoJSON layer to the map.

        Args:
            data (_type_): _file path, GeoDataFrame, or GeoJSON dictionary.
            zoom_to_layer (bool, optional): Zoom in to the layer on the map. Defaults to True.
            hover_style (_type_, optional): Changes color when hover over place on map.. Defaults to None.
        """
        import geopandas as gpd

        if hover_style is None:
            hover_style = {"color": "yellow", "fillOpacity": 0.2}

        if isinstance(data, str):
            gdf = gpd.read_file(data)
            geojson = gdf.__geo_interface__
        elif isinstance(data, dict):
            geojson = data

        geojson = folium.GeoJson(data=geojson, **kwargs)
        geojson.add_to(self)

    def add_shp(self, data, **kwargs):
        """Add a shapefile to the map.

        Args:
            data (_type_): The file path to the shapefile.
        """
        import geopandas as gpd

        gdf = gpd.read_file(data)
        gdf = gdf.to_crs(epsg=4326)
        geojson = gdf.__geo_interface__
        self.add_geojson(geojson, **kwargs)

    def add_gdf(self, gdf, **kwargs):
        """Add a GeoDataFrame to the map.

        Args:
            gdf (_type_): The GeoDataFrame to add.
        """
        gdf = gdf.to_crs(epsg=4326)
        geojson = gdf.__geo_interface__
        self.add_geojson(geojson, **kwargs)

    def add_vector(self, data, **kwargs):
        """Add vector data to the map.

        Args:
            data (_type_): _file path, GeoDataFrame, or GeoJSON dictionary.

        Raises:
            ValueError: If the data type is invalid.
        """
        import geopandas as gpd

        if isinstance(data, str):
            gdf = gpd.read_file(data)
            self.add_gdf(gdf, **kwargs)
        elif isinstance(data, gpd.GeoDataFrame):
            self.add_gdf(data, **kwargs)
        elif isinstance(data, dict):
            self.add_geojson(data, **kwargs)
        else:
            raise ValueError("Invalid data type")

    def add_layer_control(self):
        """Adds a layer control to the map."""
        folium.LayerControl().add_to(self)

    # def add_split_map(self, left="openstreetmap", right="cartodbpositron", **kwargs):
    #     """Add split map to compare two maps.

    #     Args:
    #         left (str, optional): Map type on the left of the map. Defaults to 'openstreetmap'.
    #         right (str, optional): Map type on the right of the map. Defaults to 'cartodbpositron'.
    #     """
    #     layer_right = folium.TileLayer(left, **kwargs)
    #     layer_left = folium.TileLayer(right, **kwargs)

    #     sbs = folium.plugins.SideBySideLayers(
    #         layer_left=layer_left, layer_right=layer_right
    #     )

    #     layer_left.add_to(self)
    #     layer_right.add_to(self)
    #     sbs.add_to(self)

    # def add_raster(self, left, right, **kwargs):
    #     """Add raster data to maps.

    #     Args:
    #         left (_type_): Add raster data to the left of the map.
    #         right (_type_):Add raster data to the right of the map.
    #     """
    #     from localtileserver import TileClient, get_folium_tile_layer

    #     right_layer = get_folium_tile_layer(right, **kwargs)
    #     left_layer = get_folium_tile_layer(left, **kwargs)

    #     sbs = folium.plugins.SideBySideLayers(
    #         layer_left=left_layer, layer_right=right_layer
    #     )

    #     left_layer.add_to(self)
    #     right_layer.add_to(self)
    #     sbs.add_to(self)

    def add_split_map(self, left="openstreetmap", right="cartodbpositron", **kwargs):
        """Adds a split map to the map.

        Args:
            left (str, optional): The tile layer for the left side of the split map. Defaults to "openstreetmap".
            right (str, optional): The tile layer for the right side of the split map. Defaults to "cartodbpositron".
        """
        from localtileserver import get_folium_tile_layer

        if left.startswith("http") or os.path.exists(left):
            layer_left = get_folium_tile_layer(left, **kwargs)
        else:
            layer_left = folium.TileLayer(left, overlay=True, **kwargs)
        if right.startswith("http") or os.path.exists(right):
            layer_right = get_folium_tile_layer(right, **kwargs)
        else:
            layer_right = folium.TileLayer(right, overlay=True, **kwargs)

        sbs = folium.plugins.SideBySideLayers(
            layer_left=layer_left, layer_right=layer_right
        )

        layer_left.add_to(self)
        layer_right.add_to(self)
        sbs.add_to(self)
