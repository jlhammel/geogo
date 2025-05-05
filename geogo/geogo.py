"""Main module."""

import ipyleaflet
import geopandas as gpd
import localtileserver
import ipywidgets
import tropycal
import datetime as dt
import cartopy


class Map(ipyleaflet.Map):
    def __init__(self, center=[20, 0], zoom=2, height="600px", **kwargs):

        super().__init__(center=center, zoom=zoom, **kwargs)
        self.layout.height = height
        self.scroll_wheel_zoom = True

    def add_basemap(self, basemap="Esri.WorldImagery"):
        """Add basemap to the map.

        Args:
            basemap (str, optional): Basemap name. Defaults to "Esri.WorldImagery".
        """

        url = eval(f"ipyleaflet.basemaps.{basemap}").build_url()
        layer = ipyleaflet.TileLayer(url=url, name=basemap)
        self.add(layer)

    def add_tropycal_storm(
        self,
        name_or_tuple,
        basin="north_atlantic",
        source="hurdat",
        zoom_to_layer=True,
    ):
        """Adds a storm track to the map using Tropycal.
        Args:
            name_or_tuple (str or tuple): The name of the storm or a tuple containing the name and year.
            basin (str, optional): The basin of the storm. Defaults to 'north_atlantic'.
            source (str, optional): The source of the storm data. Defaults to 'hurdat'.
            zoom_to_layer (bool, optional): Whether to zoom to the layer after adding it. Defaults to True.
        """
        import tropycal.tracks as tracks
        import geopandas as gpd
        from shapely.geometry import Point, LineString
        import pandas as pd

        category_colors = {
            "TD": "#6baed6",
            "TS": "#3182bd",
            "C1": "#31a354",
            "C2": "#addd8e",
            "C3": "#fdae6b",
            "C4": "#fd8d3c",
            "C5": "#e31a1c",
        }

        def get_category(vmax):
            if vmax < 39:
                return "TD"
            elif vmax < 74:
                return "TS"
            elif vmax < 96:
                return "C1"
            elif vmax < 111:
                return "C2"
            elif vmax < 130:
                return "C3"
            elif vmax < 157:
                return "C4"
            else:
                return "C5"

        dataset = tracks.TrackDataset(basin=basin, source=source)
        storm = dataset.get_storm(name_or_tuple)

        df = pd.DataFrame(
            {
                "datetime": storm.dict["time"],
                "lat": storm.dict["lat"],
                "lon": storm.dict["lon"],
                "vmax": storm.dict["vmax"],
                "mslp": storm.dict["mslp"],
                "type": storm.dict["type"],
                "id": storm.dict["id"],
                "name": storm.dict["name"],
            }
        )

        df["category"] = df["vmax"].apply(get_category)
        df["color"] = df["category"].map(category_colors)
        df["geometry"] = [Point(xy) for xy in zip(df.lon, df.lat)]
        gdf_points = gpd.GeoDataFrame(df, crs="EPSG:4326")

        segments = []
        for i in range(len(gdf_points) - 1):
            seg = LineString(
                [gdf_points.geometry.iloc[i], gdf_points.geometry.iloc[i + 1]]
            )
            color = gdf_points.color.iloc[i]
            segments.append({"geometry": seg, "color": color})

        gdf_line = gpd.GeoDataFrame(segments, crs="EPSG:4326")
        for _, row in gdf_line.iterrows():
            self.add_gdf(
                gpd.GeoDataFrame([row], crs="EPSG:4326"),
                style={"color": row["color"], "weight": 3},
                zoom_to_layer=False,
            )

        if zoom_to_layer:
            self.fit_bounds(
                gdf_points.total_bounds[[1, 0, 3, 2]].reshape(2, 2).tolist()
            )

    def get_storm_options(self, basin="north_atlantic", source="hurdat"):
        from tropycal import tracks

        dataset = tracks.TrackDataset(basin=basin, source=source)
        storms = dataset.keys
        years = [dataset.get_storm(storm).season for storm in storms]
        return list(zip(storms, years))  # [(storm_name, year), ...]

    def add_storm_wg(
        self,
        basin="north_atlantic",
        options=None,
        source="hurdat",
        position="topright",
        legend=True,
    ):
        """Adds a storm widget to the map.
        Args:
            basin (str): The basin of the storm. Defaults to "north_atlantic".
            options (list, optional): A list of basemap options to display in the dropdown.
                Defaults to ["OpenStreetMap.Mapnik", "OpenTopoMap", "Esri.WorldImagery", "CartoDB.DarkMatter"].
            source (str): The source of the storm data. Defaults to "hurdat".
            position (str): The position of the widget on the map. Defaults to "topright".
            legend (bool): Whether to show a legend for storm categories. Defaults to True.
        """
        import ipywidgets as widgets
        import tropycal.tracks as tracks
        from ipyleaflet import LegendControl, WidgetControl

        if options is None:
            options = ["OpenStreetMap", "OpenTopoMap", "Esri.WorldImagery"]

        toggle_button = widgets.ToggleButton(
            value=True,
            icon="globe",
            tooltip="Show/Hide storm & basemap",
            layout=widgets.Layout(width="38px", height="38px"),
        )

        basemap_dropdown = widgets.Dropdown(
            options=options,
            value=options[0],
            description="Basemap:",
            style={"description_width": "initial"},
            layout=widgets.Layout(width="250px", height="38px"),
        )

        def on_basemap_change(change):
            if change["new"]:
                self.layers = self.layers[:-2]
                self.add_basemap(change["new"])

        basemap_dropdown.observe(on_basemap_change, names="value")

        storm_list = [
            ("Wilma", 2005),
            ("Katrina", 2005),
            ("Rita", 2005),
            ("Sandy", 2012),
            ("Gert", 2016),
            ("Hermine", 2016),
            ("Matthew", 2016),
            ("Otto", 2016),
            ("Patricia", 2015),
            ("Nate", 2017),
            ("Harvey", 2017),
            ("Irma", 2017),
            ("Michael", 2018),
            ("Dorian", 2019),
            ("Lorenzo", 2019),
            ("Laura", 2020),
            ("Ida", 2021),
            ("Ian", 2022),
            ("Nicole", 2022),
            ("Lee", 2023),
            ("Ophelia", 2023),
            ("Franklin", 2023),
            ("Elsa", 2021),
            ("Fiona", 2022),
            ("Sally", 2020),
            ("Teddy", 2020),
            ("Zeta", 2020),
            ("Helene", 2024),
        ]
        storm_options = [(f"{s[0]} ({s[1]})", (s[0].lower(), s[1])) for s in storm_list]
        default_value = storm_options[0][1]

        storm_dropdown = widgets.Dropdown(
            options=storm_options,
            value=default_value,
            description="Storm:",
            style={"description_width": "initial"},
            layout=widgets.Layout(width="250px", height="38px"),
        )

        self._storm_dataset = tracks.TrackDataset(basin=basin, source=source)
        self._current_storm = None

        def on_storm_change(change):
            if change["type"] == "change" and change["name"] == "value":
                storm_name, storm_year = change["new"]
                self.layers = self.layers[:3]
                if hasattr(self, "_storm_layer") and self._storm_layer in self.layers:
                    self.remove_layer(self._storm_layer)
                self._storm_layer = self.add_tropycal_storm(
                    (storm_name, storm_year), basin=basin, source=source
                )

        storm_dropdown.observe(on_storm_change, names="value")

        controls_box = widgets.VBox([basemap_dropdown, storm_dropdown])

        def toggle_visibility(change):
            controls_box.layout.display = "flex" if change["new"] else "none"

        toggle_button.observe(toggle_visibility, names="value")

        controls_box.layout.display = "flex" if toggle_button.value else "none"

        unified_widget = widgets.VBox([toggle_button, controls_box])
        control = WidgetControl(widget=unified_widget, position=position)
        self.add(control)

        if legend:
            category_colors = {
                "TD": "#6baed6",
                "TS": "#3182bd",
                "Category 1": "#31a354",
                "Category 2": "#addd8e",
                "Category 3": "#fdae6b",
                "Category 4": "#fd8d3c",
                "Category 5": "#e31a1c",
            }
            legend_control = LegendControl(
                legend=category_colors, title="Storm Categories", position="bottomright"
            )
            self.add_control(legend_control)

    def add_wms_layer(
        self,
        url,
        layers,
        format="image/png",
        transparent=True,
        **kwargs,
    ):
        """Adds a WMS layer to the map.

        Args:
            url (str): The WMS service URL.
            layers (str): The layers to display.
            **kwargs: Additional keyword arguments for the ipyleaflet.WMSLayer layer.
        """
        from ipywidgets import DatePicker, Layout
        from datetime import date

        layers = ipyleaflet.WMSLayer(
            url=url, layers=layers, format=format, transparent=transparent, **kwargs
        )

    def add_time_wms_layer(
        self,
        url="https://gibs.earthdata.nasa.gov/wms/epsg3857/best/wms.cgi",
        layers="MODIS_Aqua_L3_Land_Surface_Temp_Daily_Day",
        time="2020-07-05",
        format="image/png",
        transparent=True,
        attribution="NASA GIBS",
        name="Time WMS Layer",
    ):
        """Adds a time-enabled WMS layer to the map.

        Args:
            m (Map): ipyleaflet Map instance.
            url (str): WMS service URL (GIBS or compatible).
            layers (str): Name of the WMS layer.
            time (str): Date in 'YYYY-MM-DD' format.
            format (str): MIME type of the image layer.
            transparent (bool): If background should be transparent.
            attribution (str): Attribution text.
            name (str): Display name for the layer.

        Returns:
            WMSLayer: The added WMS layer.
        """
        from ipyleaflet import WMSLayer

        time_url = f"{url}?TIME={time}"

        wms_layer = WMSLayer(
            url=time_url,
            layers=layers,
            format=format,
            transparent=transparent,
            attribution=attribution,
            name=name,
        )

        self.add_layer(wms_layer)
        return wms_layer

    def add_geojson(
        self,
        data,
        zoom_to_layer=True,
        hover_style={"color": "yellow", "fillOpacity": 0.5},
        **kwargs,
    ):
        """Adds a GeoJSON layer to the map.

        Args:
            data (_type_): _file path, GeoDataFrame, or GeoJSON dictionary.
            zoom_to_layer (bool, optional): Zoom in to the layer on the map. Defaults to True.
            hover_style (dict, optional): Changes color when hover over place on map. Defaults to {"color": "yellow", "fillOpacity": 0.5}.
        """
        import json

        if isinstance(data, str):
            gdf = gpd.read_file(data)
            geojson = gdf.__geo_interface__
        elif isinstance(data, dict):
            geojson = data
            gdf = gpd.GeoDataFrame.from_features(geojson["features"], crs="EPSG:4326")
        layer = ipyleaflet.GeoJSON(data=geojson, hover_style=hover_style, **kwargs)
        self.add_layer(layer)

        if zoom_to_layer:
            bounds = gdf.total_bounds
            self.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

    def add_shp(self, data, **kwargs):
        """Adds a shapefile to the map.

        Args:
            data (str): The file path to the shapefile.
            **kwargs: Additional keyword arguments for the GeoJSON layer.
        """

        gdf = gpd.read_file(data)
        gdf = gdf.to_crs(epsg=4326)
        geojson = gdf.__geo_interface__
        self.add_geojson(geojson, **kwargs)

    def add_gdf(self, gdf, **kwargs):
        """Adds a GeoDataFrame to the map.

        Args:
            gdf (geopandas.GeoDataFrame): The GeoDataFrame to add.
            **kwargs: Additional keyword arguments for the GeoJSON layer.
        """
        gdf = gdf.to_crs(epsg=4326)
        geojson = gdf.__geo_interface__
        self.add_geojson(geojson, **kwargs)

    def add_vector(self, data, **kwargs):
        """Adds vector data to the map.

        Args:
            data (str, geopandas.GeoDataFrame, or dict): The vector data. Can be a file path, GeoDataFrame, or GeoJSON dictionary.
            **kwargs: Additional keyword arguments for the GeoJSON layer.

        Raises:
            ValueError: If the data type is invalid.
        """

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
        """Adds a layer control widget to the map."""
        control = ipyleaflet.LayersControl(position="topright")
        self.add_control(control)

    def add_raster(self, filepath, **kwargs):
        """Adds a raster layer to the map.
        Args:
            filepath (str): The file path to the raster file.
            **kwargs: Additional keyword arguments for the ipyleaflet.TileLayer layer.
        """
        from localtileserver import TileClient, get_leaflet_tile_layer

        client = TileClient(filepath)
        tile_layer = get_leaflet_tile_layer(client, **kwargs)

        self.add(tile_layer)
        self.center = client.center()
        self.zoom = client.default_zoom

    def add_image(self, image, bounds=None, **kwargs):
        """Adds an image to the map.

        Args:
            image (str): The file path to the image.
            bounds (list, optional): The bounds for the image. Defaults to None.
            **kwargs: Additional keyword arguments for the ipyleaflet.ImageOverlay layer.
        """

        if bounds is None:
            bounds = [[-90, -180], [90, 180]]
        overlay = ipyleaflet.ImageOverlay(url=image, bounds=bounds, **kwargs)
        self.add(overlay)

    def add_video(self, video, bounds=None, **kwargs):
        """Adds a video to the map.

        Args:
            video (str): The file path to the video.
            bounds (list, optional): The bounds for the video. Defaults to None.
            **kwargs: Additional keyword arguments for the ipyleaflet.VideoOverlay layer.
        """

        if bounds is None:
            bounds = [[-90, -180], [90, 180]]
        overlay = ipyleaflet.VideoOverlay(url=video, bounds=bounds, **kwargs)
        self.add(overlay)

    # def add_split_map(self, left_date, right_date, **kwargs):
    #     """Adds a split map to the map.

    #     Args:
    #         left_layer (ipyleaflet.Layer): The layer for the left side of the split map.
    #         right_layer (ipyleaflet.Layer): The layer for the right side of the split map.
    #         **kwargs: Additional keyword arguments for the ipyleaflet.SplitMapControl layer.
    #     """
    #     from ipyleaflet import TileLayer, SplitMapControl

    #     left_layer = TileLayer(
    #         url=f"https://map1.vis.earthdata.nasa.gov/wmts-webmerc/MODIS_Aqua_L3_EVI_16Day/default/{left_date}/GoogleMapsCompatible_Level9/{{z}}/{{y}}/{{x}}.jpg",
    #         layers='MODIS_Aqua_L3_EVI_16Day',
    #         format="image/png",
    #         transparent=True,
    #     )

    #     right_layer = TileLayer(
    #         url=f"https://map1.vis.earthdata.nasa.gov/wmts-webmerc/MODIS_Aqua_L3_EVI_16Day/default/{right_date}/GoogleMapsCompatible_Level9/{{z}}/{{y}}/{{x}}.jpg",
    #         layers='MODIS_Aqua_L3_EVI_16Day',
    #         format="image/png",
    #         transparent=True,
    #     )
    #     print(left_layer.url)

    #     print(right_layer.url)
    #     control = SplitMapControl(
    #         left_layer=left_layer, right_layer=right_layer, **kwargs
    #     )
    #     self.add_control(control)

    #     import ipywidgets as widgets
    #     from datetime import date

    #     left_date_picker = widgets.DatePicker(
    #         description="Left Date",
    #         value=date.fromisoformat(left_date),
    #         layout=widgets.Layout(width="200px"),
    #     )

    #     right_date_picker = widgets.DatePicker(
    #         description="Right Date",
    #         value=date.fromisoformat(right_date),
    #         layout=widgets.Layout(width="200px"),
    #     )

    #     toggle = widgets.ToggleButton(
    #         value=True,
    #         icon="globe",
    #         tooltip="Show/Hide storm selector",
    #         layout=widgets.Layout(width="38px", height="38px"),
    #     )
    #     widget_box = widgets.HBox([toggle, left_date_picker, right_date_picker])

    #     def on_date_change(change):
    #         if change["name"] == "value" and change["new"] is not None:
    #             new_left_date = left_date_picker.value.isoformat()
    #             new_right_date = right_date_picker.value.isoformat()

    #             left_layer.url = (
    #                 f"https://map1.vis.earthdata.nasa.gov/wmts-webmerc/MODIS_Aqua_L3_EVI_16Day/default/"
    #                 f"{new_left_date}/GoogleMapsCompatible_Level9/{{z}}/{{y}}/{{x}}.jpg"
    #             )

    #             right_layer.url = (
    #                 f"https://map1.vis.earthdata.nasa.gov/wmts-webmerc/MODIS_Aqua_L3_EVI_16Day/default/"
    #                 f"{new_right_date}/GoogleMapsCompatible_Level9/{{z}}/{{y}}/{{x}}.jpg"
    #     )

    #     def on_toggle(change):
    #         if change["name"] == "value" and change["new"]:
    #             left_date_picker.layout.display = "flex"
    #             right_date_picker.layout.display = "flex"
    #         else:
    #             left_date_picker.layout.display = "none"
    #             right_date_picker.layout.display = "none"

    #     toggle.observe(on_toggle)

    #     left_date_picker.observe(on_date_change)
    #     right_date_picker.observe(on_date_change)

    #     widget_box = widgets.HBox([left_date_picker, right_date_picker])
    #     self.add_widget(widget_box, position="topright")

    # def add_basemap_gui(self, options=None, position="topright"):
    #     """Adds a graphical user interface (GUI) for selecting basemaps.

    #     Args:
    #         options (list, optional): A list of basemap options to display in the dropdown.
    #             Defaults to ["OpenStreetMap.Mapnik", "OpenTopoMap", "Esri.WorldImagery", "CartoDB.DarkMatter"].
    #         position (str, optional): The position of the widget on the map. Defaults to "topright".

    #     Behavior:
    #         - A toggle button is used to show or hide the dropdown and close button.
    #         - The dropdown allows users to select a basemap from the provided options.
    #         - The close button removes the widget from the map.

    #     Event Handlers:
    #         - `on_toggle_change`: Toggles the visibility of the dropdown and close button.
    #         - `on_button_click`: Closes and removes the widget from the map.
    #         - `on_dropdown_change`: Updates the map's basemap when a new option is selected.
    #     """
    #     if options is None:
    #         options = [
    #             "OpenStreetMap",
    #             "OpenTopoMap",
    #             "Esri.WorldImagery",
    #         ]
    #     toggle = ipywidgets.ToggleButton(
    #         value=True,
    #         button_style="",
    #         tooltip="Click me",
    #         icon="map",
    #     )
    #     toggle.layout = ipywidgets.Layout(width="38px", height="38px")

    #     dropdown = ipywidgets.Dropdown(
    #         options=options,
    #         value=options[0],
    #         description="Basemap:",
    #         style={"description_width": "initial"},
    #     )

    #     dropdown.layout = ipywidgets.Layout(width="250px", height="38px")

    #     button = ipywidgets.Button(
    #         icon="times",
    #     )
    #     button.layout = ipywidgets.Layout(width="38px", height="38px")

    #     hbox = ipywidgets.HBox([toggle, dropdown, button])

    #     def on_toggle_change(change):
    #         if change["new"]:
    #             hbox.children = [toggle, dropdown, button]
    #         else:
    #             hbox.children = [toggle]

    #     toggle.observe(on_toggle_change, names="value")

    #     def on_button_click(b):
    #         hbox.close()
    #         toggle.close()
    #         dropdown.close()
    #         button.close()

    #     button.on_click(on_button_click)

    #     def on_dropdown_change(change):
    #         if change["new"]:
    #             self.layers = self.layers[:-2]
    #             self.add_basemap(change["new"])

    #     dropdown.observe(on_dropdown_change, names="value")

    #     control = ipyleaflet.WidgetControl(widget=hbox, position=position)
    #     self.add(control)

    # def add_widget(self, widget, position="topright", **kwargs):
    #     """Add a widget to the map.

    #     Args:
    #         widget (ipywidgets.Widget): The widget to add.
    #         position (str, optional): Position of the widget. Defaults to "topright".
    #         **kwargs: Additional keyword arguments for the WidgetControl.
    #     """
    #     control = ipyleaflet.WidgetControl(widget=widget, position=position, **kwargs)
    #     self.add(control)

    # to get the points
    # for category, group in gdf_points.groupby("category"):
    #     self.add_gdf(
    #         group,
    #         style={
    #             "color": category_colors[category],
    #             "radius": 6,
    #             "fillOpacity": 0.7,
    #         },
    #         zoom_to_layer=False,
    #     )
