from flask import Flask, render_template, Markup, Response, redirect, url_for, request, jsonify, session
import analysis
from bokeh.embed import components
from bokeh.layouts import layout

##################
# Data Functions #
##################

geo_data = analysis.PermitDataJson(
    geo_json_path=r"C:\Development\Python\Permit_Website\Data\Boundaries - ZIP Codes.geojson",
    permit_df_csv_path=r"C:\Development\Python\Permit_Website\Data\grouped_permit_data.csv")


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

default_script, default_div = configure_plot('total', geo_data.years[-1], geo_data)


@app.route('/', methods=['GET'])
def index():
    if request.args:
        print(request.args)
        permit_type = request.args.get('permit_type')
        year = request.args.get('year', 0)
        year = 0 if year == '' else int(year)
        if permit_type in geo_data.permit_display_to_full_name_dict and year in geo_data.years:
            script, div = configure_plot(geo_data.permit_display_to_full_name_dict[permit_type],
                                         year,
                                         geo_data)
        else:
            permit_type, year = 'total', geo_data.years[-1]
            script, div = default_script, default_div
    else:
        permit_type, year = 'total', geo_data.years[-1]
        script, div = default_script, default_div

    return render_template('homepage.html',
                           bokeh_script=script,
                           bokeh_plot=div,
                           permit_types=list(geo_data.permit_display_to_full_name_dict.keys()),
                           years=geo_data.years,
                           current_permit_type=permit_type,
                           current_year=year)
