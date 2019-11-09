import json
import pandas as pd
from collections import OrderedDict
from bokeh.models import GeoJSONDataSource, AdaptiveTicker, LinearColorMapper, ColorBar
from bokeh.palettes import Viridis6 as Palette
from bokeh.plotting import figure


class DataGeoJson:
    def __init__(self, geo_json_path: str):
        self.geo_json_path = geo_json_path
        self.geo_object = json.load(open(self.geo_json_path, 'rt'))

    def add_feature_by_zip(self, field_name: str, zip_code_to_data_dict: dict, default=0):
        for feature in self.geo_object['features']:
            feature['properties'][field_name] = zip_code_to_data_dict.get(int(feature['properties']['zip']), default)

    def to_json(self):
        return json.dumps(self.geo_object)


class PermitDataJson(DataGeoJson):
    def __init__(self, geo_json_path: str, permit_df_csv_path: str):

        self.permit_df = pd.read_csv(permit_df_csv_path)
        self.years = sorted(list(self.permit_df.issue_date_year.unique()))
        self.permit_types = sorted(list(self.permit_df.permit_type.unique()))
        self.min_max_dict = {}
        self.permit_display_to_full_name_dict = OrderedDict([(p.replace('PERMIT - ', '').title(), p)
                                                             for p in self.permit_types + ['total']])

        super().__init__(geo_json_path)

        for (year, permit_type), df in self.permit_df.groupby(['issue_date_year', 'permit_type']):
            field_nm = self.build_field(year, permit_type)

            data_dict = {int(zip_code): count for zip_code, count
                         in df[['zip_code', 'permit_issue_count']].groupby('zip_code').permit_issue_count.sum().items()}

            self.min_max_dict[field_nm] = (min(data_dict.values()), max(data_dict.values()))
            self.add_feature_by_zip(field_nm, data_dict)

        for year, df in self.permit_df.groupby(['issue_date_year']):
            field_nm = self.build_field(year, 'total')
            data_dict = {int(zip_code): count for zip_code, count
                         in df[['zip_code', 'permit_issue_count']].groupby('zip_code').permit_issue_count.sum().items()}
            self.min_max_dict[field_nm] = (min(data_dict.values()), max(data_dict.values()))
            self.add_feature_by_zip(field_nm, data_dict)

    def build_data_source(self, year: int, permit_type: str):
        target_field = self.build_field(year, permit_type)
        return dict(target_field=target_field,
                    column_data_source=GeoJSONDataSource(geojson=self.to_json()),
                    min_count=self.min_max_dict[target_field][0],
                    max_count=self.min_max_dict[target_field][1])

    @staticmethod
    def build_field(year: int, permit_type: str):
        return f"{''.join([c for c in permit_type.lower() if c.isalnum()])}__{year}"

    def build_plot(self, permit_type: str, year: int):
        assert (permit_type == 'total' or permit_type in self.permit_types)
        assert (year in self.years)

        plot_info = self.build_data_source(year, permit_type)

        color_mapper = LinearColorMapper(palette=Palette, low=plot_info['min_count'], high=plot_info['max_count'])
        clean_title = f"{permit_type.replace('PERMIT - ', '').title()} - {year}"

        p = figure(
            title=clean_title, tools='hover,zoom_in, zoom_out',
            x_axis_location=None, y_axis_location=None,
            tooltips=[
                ("Zip Code", "@zip"), (clean_title, f"@{plot_info['target_field']}")
            ],
        )

        p.grid.grid_line_color = None
        p.hover.point_policy = "follow_mouse"

        p.patches('xs', 'ys', source=plot_info['column_data_source'],
                  fill_color={'field': f"{plot_info['target_field']}", 'transform': color_mapper},
                  fill_alpha=0.7, line_color="white", line_width=0.5)

        color_bar = ColorBar(color_mapper=color_mapper,
                             ticker=AdaptiveTicker(),
                             border_line_color=None,
                             location=(0, 0))

        p.outline_line_color = None

        p.add_layout(color_bar, 'right')
        p.toolbar.logo = None
        p.toolbar_location = None

        return p
