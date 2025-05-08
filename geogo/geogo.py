"""Main module."""

import ipyleaflet
import geopandas as gpd
import datetime as dt


class Map(ipyleaflet.Map):
    def __init__(self, center=[20, 0], zoom=2, height="600px", **kwargs):

        super().__init__(center=center, zoom=zoom, **kwargs)
        self.layout.height = height
        self.scroll_wheel_zoom = True

    def add_basemap(self, basemap="OpenStreetMap.Mapnik"):
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
                style={"color": row["color"], "weight": 3, "weight": 8},
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
        return list(zip(storms, years))

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
            basin (str): The basin of the storm. Defaults to 'north_atlantic'.
            options (list, optional): A list of basemap options to display in the dropdown.
                Defaults to ["OpenStreetMap.Mapnik", "OpenTopoMap", "Esri.WorldImagery"].
            source (str): The source of the storm data. Defaults to 'hurdat'.
            position (str): The position of the widget on the map. Defaults to 'topright'.
            legend (bool): Whether to show a legend. Defaults to True.
        """
        import ipywidgets as widgets
        import tropycal.tracks as tracks
        from ipyleaflet import WidgetControl

        if options is None:
            options = ["OpenStreetMap.Mapnik", "OpenTopoMap", "Esri.WorldImagery"]

        widget_toggle = widgets.ToggleButton(
            value=True,
            icon="globe",
            tooltip="Show/Hide storm & basemap",
            layout=widgets.Layout(width="38px", height="38px"),
        )

        storm_list = [
            ("Wilma", 2005),
            ("Katrina", 2005),
            ("Rita", 2005),
            ("Sandy", 2012),
            ("Hermine", 2016),
            ("Matthew", 2016),
            ("Otto", 2016),
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

        controls_box = widgets.VBox([storm_dropdown])
        controls_box.layout.display = "flex" if widget_toggle.value else "none"

        widget_control = WidgetControl(
            widget=widgets.VBox([widget_toggle, controls_box]), position=position
        )
        self.add(widget_control)

        def toggle_controls(change):
            controls_box.layout.display = "flex" if change["new"] else "none"

        widget_toggle.observe(toggle_controls, names="value")

        if legend:
            import ipywidgets as widgets
            from ipyleaflet import WidgetControl

            category_colors = {
                "TD": "#6baed6",
                "TS": "#3182bd",
                "Category 1": "#31a354",
                "Category 2": "#addd8e",
                "Category 3": "#fdae6b",
                "Category 4": "#fd8d8c",
                "Category 5": "#e31a1c",
            }

            legend_items = []
            for label, color in category_colors.items():
                legend_items.append(
                    f"<div style='margin-bottom:2px;'><span style='display:inline-block;width:12px;height:12px;background:{color};margin-right:6px;'></span>{label}</div>"
                )

            legend_html = widgets.HTML(
                value=f"<div style='padding:4px 8px;font-size:13px;line-height:1.4;'><b>Storm<br>Categories</b><hr style='margin:4px 0;'/>"
                + "".join(legend_items)
                + "</div>"
            )

            toggle_legend_btn = widgets.ToggleButton(
                value=True,
                icon="list",
                tooltip="Show/Hide legend",
                layout=widgets.Layout(width="38px", height="38px"),
            )

            legend_box = widgets.VBox([toggle_legend_btn, legend_html])

            def toggle_legend_display(change):
                legend_html.layout.display = "block" if change["new"] else "none"

            toggle_legend_btn.observe(toggle_legend_display, names="value")

            legend_control = WidgetControl(widget=legend_box, position="bottomright")
            self.add(legend_control)

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
        legend=True,
        custom_legend=None,
        position="bottomleft",
    ):
        """Adds a WMS layer with time control to the map.
        Args:
            url (str): The WMS service URL. Defaults to "https://gibs.earthdata.nasa.gov/wms/epsg3857/best/wms.cgi".
            layers (str): The layers to display. Defaults to "MODIS_Aqua_L3_Land_Surface_Temp_Daily_Day".
            time (str): The time parameter for the WMS request. Defaults to "2020-07-05".
            format (str): The image format. Defaults to "image/png".
            transparent (bool): Whether the layer is transparent. Defaults to True.
            attribution (str): Attribution text. Defaults to "NASA GIBS".
            name (str): Name of the layer. Defaults to "Time WMS Layer".
            legend (bool): Whether to show a legend. Defaults to True.
            custom_legend (dict, optional): Custom legend items. Defaults to None.
            position (str): Position of the legend on the map. Defaults to "bottomleft".
        """
        from ipyleaflet import WMSLayer, WidgetControl
        import ipywidgets as widgets
        from datetime import date

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

        date_picker = widgets.DatePicker(
            description="Select Date",
            value=date.fromisoformat(time),
            layout=widgets.Layout(width="200px"),
        )

        def update_time(change):
            if change["new"]:
                new_date = change["new"].isoformat()
                wms_layer.url = f"{url}?TIME={new_date}"

        date_picker.observe(update_time, names="value")

        date_control = WidgetControl(widget=date_picker, position="topright")
        self.add_control(date_control)

        if legend:
            built_in_legends = {
                "MODIS_Aqua_L3_Land_Surface_Temp_Daily_Day": {
                    "< -10°C": "#313695",
                    "-10 to 0°C": "#4575b4",
                    "0 to 10°C": "#74add1",
                    "10 to 20°C": "#abd9e9",
                    "20 to 30°C": "#fdae61",
                    "> 30°C": "#d73027",
                }
            }

            legend_items = custom_legend or built_in_legends.get(layers)

            if legend_items:
                title_html = (
                    "<div style='text-align:center; font-size:12px; font-weight:bold;'>"
                    f"{layers.replace('_', ' ')}".replace(
                        "MODIS Aqua L3", "MODIS Aqua L3<br>Land Surface Temp"
                    )
                    + "</div><hr style='margin:2px 0;'>"
                )

                legend_html = widgets.HTML()
                legend_html.value = (
                    f"<div style='font-size:12px; line-height:1.4em; max-width:160px;'>"
                    f"{title_html}"
                )

                for label, color in legend_items.items():
                    legend_html.value += (
                        f"<div style='display:flex; align-items:center; justify-content:center; margin:2px 0;'>"
                        f"<span style='display:inline-block;width:12px;height:12px;"
                        f"background:{color};margin-right:6px;border:1px solid #ccc;'></span>"
                        f"<span style='text-align:center;'>{label}</span>"
                        f"</div>"
                    )
                legend_html.value += "</div>"

                legend_box = widgets.VBox([legend_html])
                legend_box.layout.display = "flex"
                legend_box.layout.padding = "2px 6px"

                toggle_button = widgets.ToggleButton(
                    value=True,
                    tooltip="Toggle Legend",
                    icon="list",
                    layout=widgets.Layout(width="26px", height="26px", padding="0"),
                )

                def toggle_visibility(change):
                    legend_box.layout.display = "flex" if change["new"] else "none"

                toggle_button.observe(toggle_visibility, names="value")

                widget = widgets.VBox([toggle_button, legend_box])
                control = WidgetControl(widget=widget, position=position)
                self.add_control(control)
            else:
                print(f"No legend available for layer: {layers}")

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
