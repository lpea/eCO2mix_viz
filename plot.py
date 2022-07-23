#!/usr/bin/env python3

import argparse
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output

# Order from XLS file
COL_LABELS_XLS = ['Fioul', 'Charbon', 'Gaz', 'Nucléaire', 'Eolien', 'Solaire', 'Hydraulique', 'Pompage', 'Bioénergies', 'Ech. physiques']
# Order of display
COL_LABELS_PLOT = ['Fioul', 'Charbon', 'Gaz', 'Hydraulique', 'Nucléaire', 'Solaire', 'Eolien', 'Bioénergies', 'Import'] + ['Export', 'Pompage']
COL_LABELS_PLOT.reverse()

# Energy source <-> color mapping using CSS color names
# - https://www.w3schools.com/cssref/css_colors.asp
# - https://matplotlib.org/stable/gallery/color/named_colors.html
COLORS = {
    'Fioul': 'mediumpurple',
    'Charbon': 'darkkhaki',
    'Gaz': 'red',
    'Hydraulique': 'cornflowerblue',
    'Nucléaire': 'gold',
    'Solaire': 'orange',
    'Eolien': 'paleturquoise',
    'Bioénergies': 'mediumseagreen',
    'Import': 'darkgray',
    'Pompage': 'royalblue',
    'Export': 'lightgray',
}


def load_power_data(filepath):
    # Read input data
    # https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_table.html
    # https://pandas.pydata.org/pandas-docs/stable/user_guide/dsintro.html#dataframe
    data = pd.read_table(
        filepath,
        usecols=['Date', 'Heures'] + COL_LABELS_XLS,
        skiprows=lambda x: x > 0 and (x % 2) == 0,  # Every other row is empty, skip them (MUCH faster that loading all and calling dropna())
        skipfooter=1,                               # Skip last line (RTE disclaimer)
        parse_dates=[['Date', 'Heures']],           # Aggregate the two columns and parse as a datetime object
        engine='python',                            # Default 'c' engine does not support skipfooter
        encoding='latin-1',
    )
    data.set_index('Date_Heures', inplace=True)

    # Split 'Ech. physiques' into two series:
    # - one with positive values only (imports)
    # - one with negative values only (exports).
    ech_phy = data.pop('Ech. physiques')
    imports = ech_phy.clip(lower=0).rename('Import', inplace=True)
    exports = ech_phy.clip(upper=0).rename('Export', inplace=True)

    # Add imports and exports to data
    data = pd.concat([data, imports, exports], axis=1, copy=False)

    # Reorder columns → ['Pompage', 'Export', 'Import', ..., 'Fioul']
    return data[COL_LABELS_PLOT]


def filter_data(data, start_date, end_date, frequency):
    # Filter by date range https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#partial-string-indexing
    data_slice = data[start_date:end_date]

    # Resample data https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.Series.resample.html
    resampled = data_slice.resample(frequency).mean()
    return resampled


def plot(data):
    # plotly_express.area lacks the 'stackgroup' parameter, which is necessary to separate
    # positive and negative contributions (production vs. storage/export) distributed from either
    # side of the x-axis.

    fig = go.Figure()
    for col_name in data.columns:
        group = 2 if col_name in ['Pompage', 'Export'] else 1
        color = COLORS[col_name]
        # https://plotly.com/python-api-reference/generated/plotly.graph_objects.Scatter.html
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data[col_name],
            mode='lines',
            line={'width': 0, 'color': color},  # hide lines, set color for hover box background
            fillcolor=color,
            name=col_name,
            stackgroup=group,
            #hovertemplate=f"{col_name}<br>Date: %{{x}}<br>Puissance: %{{y}} MW<extra></extra>",  # hovermode == 'closest'
            hovertemplate=f"{col_name}: %{{y}} MW<extra></extra>",
        ))

    # Set figure properties
    # https://plotly.com/python-api-reference/generated/plotly.graph_objects.html#plotly.graph_objects.Layout
    fig.update_layout({
        'title': f"Production d'électricité par filière en France du {data.index[0]} au {data.index[-1]}",
        'xaxis': {'title': "Date"},
        'yaxis': {'title': "Puissance produite en MV"},
        'legend': {'title': "Source d'énergie"},
        'height': 700,
        'hovermode': 'x',  # ['closest', 'x', 'x unified']
    })

    return fig


def make_dash_app(data):
    # https://plotly.com/python/filled-area-plots/#filled-area-plot-in-dash
    app = Dash(__name__, external_scripts=["https://cdn.plot.ly/plotly-locale-fr-latest.js"])

    @app.callback(
        Output('graph', 'figure'),
        Input('date-range-picker', 'start_date'),
        Input('date-range-picker', 'end_date'),
        Input('frequency-dropdown', 'value'))
    def update_graph(start_date, end_date, frequency):
        filtered = filter_data(data, start_date, end_date, frequency)
        fig = plot(filtered)
        return fig

    @app.callback(
        Output('frequency-dropdown', 'options'),
        Input('date-range-picker', 'start_date'),
        Input('date-range-picker', 'end_date'))
    def update_sampling_freq_options(start_date, end_date):
        options = [
            {'label': '30 minutes', 'value': '30min'},
            {'label': '1 heure', 'value': '1H'},
            {'label': '4 heures', 'value': '4H'},
            {'label': '1 jour', 'value': '1D'},
            {'label': '1 semaine', 'value': '1W'},
        ]

        if start_date is None or end_date is None:
            return options

        span_days = pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timestamp(start_date)
        for opt in options:
            opt['disabled'] = pd.Timedelta(opt['value']) >= span_days
        return options

    data_start_date = data.index[0].date()
    data_end_date = data.index[-1].date()

    app.layout = html.Div([
        html.H4(f"Données RTE − éCO2mix consolidées de puissance ({data_start_date} → {data_end_date})"),
        html.P("Période :"),
        # https://dash.plotly.com/dash-core-components/datepickerrange
        dcc.DatePickerRange(
            id='date-range-picker',
            display_format='DD/MM/YYYY',
            min_date_allowed=data_start_date,
            max_date_allowed=data_end_date,
            start_date=data_end_date - pd.Timedelta(weeks=1),
            end_date=data_end_date,
            number_of_months_shown=6,
            updatemode='bothdates',
            first_day_of_week=1,
            clearable=True,
            reopen_calendar_on_clear=True,
            minimum_nights=0,  # Allow single-day range
        ),
        html.P("Lissage des données sur :"),
        # https://dash.plotly.com/dash-core-components/dropdown
        dcc.Dropdown(
            options=update_sampling_freq_options(start_date=None, end_date=None),
            value='1H',
            clearable=False,
            id='frequency-dropdown',
        ),
        dcc.Graph(id='graph', config=dict(locale="fr")),
    ])

    return app


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('filepath', type=str, help="path to the input data file")
    parser.add_argument('--static', action='store_true', help="produce a static graph using the matplotlib backend")
    args = parser.parse_args()

    data = load_power_data(args.filepath)

    if args.static:
        import matplotlib.pyplot as plt
        end_date = data.index[-1].date()
        start_date = end_date - pd.Timedelta(weeks=1)
        filtered = filter_data(data, start_date, end_date, '30min')
        fig = filtered.plot.area(color={k: COLORS[k] for k in data.columns}, backend='matplotlib', linewidth=0)
        plt.show()
    else:
        app = make_dash_app(data)
        app.run(debug=True)

