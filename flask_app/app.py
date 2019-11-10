from flask import Flask, render_template, request
import analysis
from bokeh.embed import components
from bokeh.layouts import layout
from urllib.parse import quote_plus
import os

##################
# Data Functions #
##################

geo_data = analysis.PermitDataJson(
    geo_json_path=f"Data{os.sep}Boundaries - ZIP Codes.geojson",
    permit_df_csv_path=f"Data{os.sep}grouped_permit_data.csv")


#########################
# Plot Layout Functions #
#########################

def configure_plot(permit_type: str, year: int, geo_data_obj:analysis.PermitDataJson):
    plot = geo_data_obj.build_plot(permit_type, year)
    plot_layout = layout(plot, sizing_mode='stretch_both')
    return components(plot_layout)


####################
#  Flask Functions #
####################

app = Flask(__name__)
app.jinja_env.filters['quote_plus'] = lambda u: quote_plus(u)

default_script, default_div = configure_plot('total', geo_data.years[-1], geo_data)


@app.route('/', methods=['GET'])
def index():
    if request.args:
        permit_type = request.args.get('permit_type')
        year = request.args.get('year', 0)
        year = 0 if year == '' else int(year)
        if permit_type in geo_data.permit_display_to_full_name_dict and year in geo_data.years:
            script, div = configure_plot(geo_data.permit_display_to_full_name_dict[permit_type],
                                         year,
                                         geo_data)
        else:
            permit_type, year = 'Total', geo_data.years[-1]
            script, div = default_script, default_div
    else:
        permit_type, year = 'Total', geo_data.years[-1]
        script, div = default_script, default_div

    permit_types = list(geo_data.permit_display_to_full_name_dict.keys())
    years = geo_data.years

    next_permit_type = permit_types[(permit_types.index(permit_type) + 1) % len(permit_types)]
    prev_permit_type = permit_types[(permit_types.index(permit_type) - 1) % len(permit_types)]

    next_year = years[(years.index(year) + 1) % len(years)]
    prev_year = years[(years.index(year) - 1) % len(years)]


    return render_template('homepage.html',
                           bokeh_script=script,
                           bokeh_plot=div,
                           permit_types=permit_types,
                           years=years,
                           current_permit_type=permit_type,
                           current_year=year,
                           next_permit_type=next_permit_type,
                           prev_permit_type=prev_permit_type,
                           next_year=next_year,
                           prev_year=prev_year)
