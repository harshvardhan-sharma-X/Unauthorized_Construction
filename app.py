import dash
from dash import dcc, html, Input, Output, State, callback, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px

import json  

# Load the pre-processed GeoJSON once when the app starts
with open('assets/authorized_footprints.json') as f:
    authorized_geojson = json.load(f)


# ── Initialize app ───────────────────────────────────────────────────────────────
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP,"https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"],
                meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}])

app.index_string = """
<!DOCTYPE html>
<html>
<head>
    {%metas%}
    <title>Urban Construction Monitoring</title>
    {%favicon%}
    {%css%}
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>

        /* Remove table row selection highlight */
.dash-spreadsheet td.cell--selected,
.dash-spreadsheet td.focused,
.dash-spreadsheet tr.row--selected td {
    background-color: transparent !important;
    box-shadow: none !important;
    border: none !important;
}

.dash-spreadsheet td:focus {
    outline: none !important;
    background-color: transparent !important;
}
        .card {
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .card:hover {
                    transform: translateY(-8px);
                    box-shadow: 0 20px 40px rgba(0,0,0,0.12);
        }
        body {
            font-family: 'Inter', sans-serif;
            background-color: #f5f7fb;
            color: #1f2937;
        }
        body::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-image: 
        radial-gradient(circle at 20% 50%, rgba(59, 130, 246, 0.03) 0%, transparent 50%),
        radial-gradient(circle at 80% 80%, rgba(139, 92, 246, 0.03) 0%, transparent 50%);
    pointer-events: none;
    z-index: -1;
}

body::after {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, #3b82f6, #8b5cf6, #ec4899);
    z-index: 9999;
}

        h1 {
            font-weight: 700;
            letter-spacing: -0.5px;
        }

        h3 {
            font-weight: 600;
            margin-bottom: 1rem;
        }

        /* Cards */
        .card {
            border-radius: 14px;
            border: none;
            background: white;
            box-shadow: 0 8px 24px rgba(0,0,0,0.06);
        }

        .card-title {
            font-size: 0.8rem;
            font-weight: 600;
            color: #6b7280;
            letter-spacing: 1px;
            text-transform: uppercase;
        }

        .card-text {
            font-size: 2.7rem;
            font-weight: 700;
        }

        .text-success {
            color: #16a34a !important;
        }

        .text-danger {
            color: #dc2626 !important;
        }

        hr {
    border: none;
    height: 2px;
    background: linear-gradient(90deg, transparent, #e5e7eb, transparent);
    margin: 3rem 0;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

        /* Dropdown */
        .Select-control {
            border-radius: 10px !important;
            border: 1px solid #d1d5db !important;
            padding: 6px;
        }

        /* Buttons */
        .btn {
    border-radius: 10px;
    font-weight: 600;
    letter-spacing: 0.3px;
    position: relative;
    overflow: hidden;
    transition: all 0.3s ease;
}

        .btn::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.4);
            transform: translate(-50%, -50%);
            transition: width 0.6s, height 0.6s;
        }

        .btn:active::before {
            width: 300px;
            height: 300px;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 24px rgba(0,0,0,0.15);
        }

        .btn-danger {
            background-color: #ef4444;
            border: none;
        }

        .btn-success {
            background-color: #22c55e;
            border: none;
        }

        /* Tables */
        .dash-table-container {
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 6px 16px rgba(0,0,0,0.05);
        }

        /* Map */
        #map {
            border-radius: 16px;
            box-shadow: 0 12px 30px rgba(0,0,0,0.08);
            cursor: grab;
        }

        #map:active {
            cursor: grabbing;
        }

       /* Image */
        #site-image {
            border-radius: 12px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }

        #site-image:hover {
            transform: scale(1.03);
            box-shadow: 0 16px 40px rgba(0,0,0,0.15);
        }

        /* Fade-in animation on page load */
        .container-fluid > * {
            animation: fadeInUp 0.6s ease-out backwards;
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        /* Stagger the animations */
        .container-fluid > *:nth-child(1) { animation-delay: 0.1s; }
        .container-fluid > *:nth-child(2) { animation-delay: 0.2s; }
        .container-fluid > *:nth-child(3) { animation-delay: 0.3s; }
        .container-fluid > *:nth-child(4) { animation-delay: 0.4s; }
        .container-fluid > *:nth-child(5) { animation-delay: 0.5s; }
        .container-fluid > *:nth-child(6) { animation-delay: 0.6s; }

    </style>
</head>
<body>
    {%app_entry%}
    <footer>
        {%config%}
        {%scripts%}
        {%renderer%}
    </footer>
</body>

</html>
"""


# ── Mock data (same as yours) ────────────────────────────────────────────────────
if 'construction_data' not in globals():
    data = {
        'id': [101, 102, 103, 104],
        'location_name': ['Downtown Plaza', 'North Suburb', 'East Industrial', 'West Riverside'],
        'lat': [28.6139, 28.7041, 28.5355, 28.6500],
        'lon': [77.2090, 77.1025, 77.3910, 77.0500],
        'is_authorized': [True, False, False, True],
        'image_url': [
            'https://via.placeholder.com/400x300.png?text=Site+101+Authorized',
            'https://via.placeholder.com/400x300.png?text=Site+102+Violation',
            'https://via.placeholder.com/400x300.png?text=Site+103+Violation',
            'https://via.placeholder.com/400x300.png?text=Site+104+Authorized'
        ]
    }
    df = pd.DataFrame(data)
else:
    df = globals()['construction_data']

# We'll use a dcc.Store to hold the data (replaces session_state)
store = dcc.Store(id='data-store', data=df.to_dict('records'))

# ── Layout ───────────────────────────────────────────────────────────────────────
app.layout = dbc.Container(fluid=True, children=[
    html.H1("Urban Construction Monitoring Dashboard", className="text-center my-4"),
    html.P("AI-assisted identification and monitoring of unauthorized construction activities", className="text-center text-muted mb-4"),

    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H4("✅ Authorized Sites", className="card-title"),
                html.H2(id="authorized-count", children=str(df['is_authorized'].sum()), className="card-text text-success")
            ])
        ], color="success", outline=True), width=6, md=6),

        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H4("🚨 Unauthorized Sites", className="card-title"),
                html.H2(id="unauthorized-count", children=str((~df['is_authorized']).sum()), className="card-text text-danger")
            ])
        ], color="danger", outline=True), width=6, md=6),
    ], className="mb-5"),

    html.Hr(),

    html.H3("Interactive City Map"),
    dcc.Dropdown(
        id="basemap-style",
        options=[
            {"label": "Street View",      "value": "streets"},
            {"label": "Satellite View",   "value": "satellite"},
            {"label": "Hybrid (Sat + Streets)", "value": "satellite-streets"},
        ],
        value="streets",   # default
        clearable=False,
        className="mb-3 w-50"   # adjust width as you like
    ),
    dcc.Graph(
        id="map", 
        config={'scrollZoom': True},
        style={"height": "550px"}
    ),

    html.Hr(),

    dbc.Row([
        # Authorized column
        dbc.Col([
            html.H4("✅ Authorized Constructions", className="text-success"),
            dash_table.DataTable(
                id="auth-table",
                columns=[{"name": "ID", "id": "id"}, {"name": "Location", "id": "location_name"}],
                data=[],                     # start empty – callback will fill it
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left', 'padding': '5px'},
                style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
                cell_selectable=False,
                row_selectable=False,
            ),
            dcc.Dropdown(
                id="select-auth",
                options=[{"label": f"{row['id']} - {row['location_name']}", "value": row['id']}
                        for _, row in df[df['is_authorized']].iterrows()],
                placeholder="Select Site to Revoke...",
                className="mb-2"
            ),
            dbc.Button("🚨 Flag as Unauthorized", id="btn-revoke", color="danger", className="w-100")
        ], width=6),

        # Unauthorized column
        dbc.Col([
            html.H4("🚩 Unauthorized Violations", className="text-danger"),
            dash_table.DataTable(
                id="unauth-table",
                columns=[{"name": "ID", "id": "id"}, {"name": "Location", "id": "location_name"}],
                data=[],                     # start empty – callback will fill it
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left', 'padding': '5px'},
                style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
                cell_selectable=False,
                row_selectable=False,
            ),
            dcc.Dropdown(
                id="select-unauth",
                options=[{"label": f"{row['id']} - {row['location_name']}", "value": row['id']}
                        for _, row in df[~df['is_authorized']].iterrows()],
                placeholder="Select Site to Approve...",
                className="mb-2"
            ),
            dbc.Button("✔️ Approve Construction", id="btn-approve", color="success", className="w-100")
        ], width=6),
    ], className="mb-5"),

    html.Hr(),

    html.H3("Site Inspection Preview"),
    dcc.Dropdown(
        id="inspect-id",
        options=[{"label": f"{i} - {name}", "value": i} for i, name in zip(df['id'], df['location_name'])],
        value=df['id'].iloc[0],
        className="mb-3"
    ),

    dbc.Row([
        dbc.Col(html.Img(id="site-image", style={"width": "100%", "borderRadius": "8px"}), width=8),
        dbc.Col([
            html.H5(id="site-name"),
            html.P(id="site-status"),
            html.P(id="site-coords")
        ], width=4),
    ]),
    
    store  # hidden store
])

# ── Callbacks ────────────────────────────────────────────────────────────────────

@callback(
    [Output("map", "figure"),
    Output("authorized-count", "children"),
    Output("unauthorized-count", "children"),
    Output("auth-table", "data"),
    Output("unauth-table", "data"),
    Output("select-auth", "options"),
    Output("select-unauth", "options")],
    [Input("data-store", "data"),
    Input("basemap-style", "value")],
)
def update_all(data, basemap_style):
    df = pd.DataFrame(data)
    
    # Plotly map (recommended replacement for Folium)
    fig = px.scatter_mapbox(
        df,
        lat="lat", lon="lon",
        color="is_authorized",
        color_discrete_map={True: "green", False: "red"},
        hover_name="location_name",
        hover_data={"id": True, "lat": False, "lon": False},
        zoom=10,
        height=550
    )

    current_style = "carto-positron" if basemap_style == "streets" else "white-bg"

    layers = []

    # 1. BASE LAYER: Satellite Raster (Bottom)
    layers.append({
        "below": 'traces',
        "sourcetype": "raster",
        "source": ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"],
        "visible": basemap_style in ["satellite", "satellite-streets"]
    })

    # 2. MIDDLE LAYER: Reliable Authorized Polygons
    if authorized_geojson:
        layers.append({
            "sourcetype": "geojson",
            "source": authorized_geojson,
            "type": "fill",
            # rgba color allows you to set opacity (0.5 = 50%)
            "color": "rgba(0, 255, 0, 0.5)", 
            "below": "traces" 
        })

    # 3. TOP LAYER: Hybrid Labels (Streets/Names)
    layers.append({
        "below": 'traces',
        "sourcetype": "raster",
        "source": ["https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}"],
        "visible": basemap_style == "satellite-streets"
    })

    # 4. Apply the Layout
    fig.update_layout(
        showlegend=False,
        mapbox_style="carto-positron" if basemap_style == "streets" else "white-bg", 
        mapbox_layers=layers,
        margin={"r":0,"t":0,"l":0,"b":0},
    )

    fig.update_traces(marker=dict(size=18))

    # 5. Prepare Dashboard Statistics and Tables
    auth_count = str(df['is_authorized'].sum())
    unauth_count = str((~df['is_authorized']).sum())
    
    auth_df = df[df['is_authorized']][['id', 'location_name']].to_dict('records')
    unauth_df = df[~df['is_authorized']][['id', 'location_name']].to_dict('records')
    
    auth_opts = [{"label": f"{r['id']} - {r['location_name']}", "value": r['id']} for r in auth_df]
    unauth_opts = [{"label": f"{r['id']} - {r['location_name']}", "value": r['id']} for r in unauth_df]
    
    return fig, auth_count, unauth_count, auth_df, unauth_df, auth_opts, unauth_opts


@callback(
    Output("data-store", "data"),
    [Input("btn-revoke", "n_clicks"),
    Input("btn-approve", "n_clicks")],
    [State("select-auth", "value"),
    State("select-unauth", "value"),
    State("data-store", "data")],
    prevent_initial_call=True
)
def update_status(n_revoke, n_approve, auth_id, unauth_id, current_data):
    df = pd.DataFrame(current_data)
    
    ctx = dash.callback_context
    if not ctx.triggered:
        return current_data
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == "btn-revoke" and auth_id:
        df.loc[df['id'] == auth_id, 'is_authorized'] = False
    elif button_id == "btn-approve" and unauth_id:
        df.loc[df['id'] == unauth_id, 'is_authorized'] = True
    
    return df.to_dict('records')


@callback(
    [Output("site-image", "src"),
    Output("site-name", "children"),
    Output("site-status", "children"),
    Output("site-coords", "children")],
    Input("inspect-id", "value"),
    State("data-store", "data")
)
def update_inspection(site_id, current_data):
    if not site_id:
        return "", "", "", ""
    
    df = pd.DataFrame(current_data)
    row = df[df['id'] == site_id].iloc[0]
    
    status = "Authorized" if row['is_authorized'] else "**UNAUTHORIZED**"
    color = "text-success" if row['is_authorized'] else "text-danger"
    
    return (
        row['image_url'],
        f"Site {site_id} - {row['location_name']}",
        html.Span(status, className=color),
        f"Coordinates: {row['lat']}, {row['lon']}"
    )


if __name__ == '__main__':
    app.run(debug=True)
