import dash
from dash import dcc, html, Input, Output, State, callback, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import json

# --- 1. DATA LOADING & PRE-PROCESSING ---
# Load Authorized Footprints
try:
    with open('assets/authorized_footprints.json') as f:
        authorized_geojson = json.load(f)
except FileNotFoundError:
    print("Error: assets/authorized_footprints.json not found.")
    authorized_geojson = {"type": "FeatureCollection", "features": []}

# Load Detected Footprints (New: AI output for actual construction)
try:
    with open('assets/detected_footprints.json') as f:
        detected_geojson = json.load(f)
except FileNotFoundError:
    print("Error: assets/detected_footprints.json not found.")
    detected_geojson = {"type": "FeatureCollection", "features": []}

# Load the AI compliance report
try:
    compliance_df = pd.read_csv('assets/final_compliance_report.csv')
except FileNotFoundError:
    print("Error: assets/final_compliance_report.csv not found.")
    compliance_df = pd.DataFrame(columns=['Site_Index', 'Compliance_Status', 'Exceedance_Percent'])

features = authorized_geojson.get('features', [])
real_site_data = []

for i, feature in enumerate(features):
    geom = feature.get('geometry', {})
    geom_type = geom.get('type')
    
    try:
        if geom_type == 'Polygon':
            coords = geom['coordinates'][0]
        elif geom_type == 'MultiPolygon':
            coords = geom['coordinates'][0][0]
        else:
            continue
        
        lons, lats = zip(*coords)
        avg_lat = sum(lats) / len(lats)
        avg_lon = sum(lons) / len(lons)
        
        # Consistent ID logic to match both GeoJSONs
        site_id = str(feature.get('properties', {}).get('id', i + 1000))
        
        # Match with AI Compliance Report
        compliance_row = compliance_df[compliance_df['Site_Index'] == i]
        if not compliance_row.empty:
            status = compliance_row.iloc[0]['Compliance_Status']
            is_auth = (status == "AUTHORIZED")
            expansion = compliance_row.iloc[0]['Exceedance_Percent']
        else:
            is_auth = True
            expansion = 0.0
            
        real_site_data.append({
            'id': site_id,
            'location_name': f"South Delhi Plot {site_id}",
            'lat': avg_lat,
            'lon': avg_lon,
            'is_authorized': is_auth,
            'expansion_pct': expansion
        })
    except (IndexError, TypeError, KeyError):
        continue

df = pd.DataFrame(real_site_data)

# --- 2. INITIALIZE APP ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# --- 3. LAYOUT ---
app.layout = dbc.Container(fluid=True, children=[
    html.H1("Urban Construction Monitoring Dashboard", className="text-center my-4"),
    dcc.Store(id='data-store', data=df.to_dict('records')),

    # Metric Cards
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H4("✅ Authorized Sites", className="card-title"),
                html.H2(id="authorized-count", className="card-text text-success")
            ])
        ], color="success", outline=True), width=6),
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H4("🚨 Unauthorized Sites", className="card-title"),
                html.H2(id="unauthorized-count", className="card-text text-danger")
            ])
        ], color="danger", outline=True), width=6),
    ], className="mb-4"),

    html.Hr(),
    html.H3("Interactive City Map"),
    dcc.Dropdown(
        id="basemap-style",
        options=[
            {"label": "Street View", "value": "open-street-map"},
            {"label": "Satellite View", "value": "white-bg"},
        ],
        value="open-street-map",
        clearable=False,
        className="mb-3 w-50"
    ),
    dcc.Graph(id="map", config={'scrollZoom': True}, style={"height": "550px"}),

    html.Hr(),
    dbc.Row([
        dbc.Col([
            html.H4("✅ Authorized", className="text-success"),
            dash_table.DataTable(
                id="auth-table", 
                columns=[{"name": "ID", "id": "id"}, {"name": "Location", "id": "location_name"}], 
                style_header={'fontWeight': 'bold', 'backgroundColor': 'white'},
                page_action='none',
                fixed_rows={'headers': True},
                style_table={'height': '400px', 'overflowY': 'auto'},
                style_cell={'textAlign': 'left'}
            ),
            dcc.Dropdown(id="select-auth", placeholder="Select Site to Revoke...", className="mt-2"),
            dbc.Button("🚨 Flag as Unauthorized", id="btn-revoke", color="danger", className="w-100 mt-2")
        ], width=6),
        dbc.Col([
            html.H4("🚩 Unauthorized", className="text-danger"),
            dash_table.DataTable(
                id="unauth-table", 
                columns=[{"name": "ID", "id": "id"}, {"name": "Location", "id": "location_name"}], 
                style_header={'fontWeight': 'bold', 'backgroundColor': 'white'},
                page_action='none',
                fixed_rows={'headers': True},
                style_table={'height': '400px', 'overflowY': 'auto'},
                style_cell={'textAlign': 'left'}
            ),
            dcc.Dropdown(id="select-unauth", placeholder="Select Site to Approve...", className="mt-2"),
            dbc.Button("✔️ Approve Construction", id="btn-approve", color="success", className="w-100 mt-2")
        ], width=6),
    ], className="mb-5"),

    html.Hr(),
    html.H3("Site Inspection Preview"),
    dcc.Dropdown(id="inspect-id", className="mb-3"),

    dbc.Row([
        # Minimap 1: Satellite + Detection Boundary (If Unauthorized)
        dbc.Col(dcc.Graph(id="inspection-satellite-map", style={"height": "350px"}), width=4),
        # Minimap 2: Satellite + Authorized Footprint
        dbc.Col(dcc.Graph(id="inspection-polygon-map", style={"height": "350px"}), width=4),
        dbc.Col([
            html.Div(className="p-3 bg-light rounded", children=[
                html.H5(id="site-name", className="fw-bold"),
                html.Hr(),
                html.P(id="site-status", className="mb-2"),
                html.P(id="site-expansion", className="mb-2 fw-bold text-primary"), # AI Expansion %
                html.P(id="site-coords", className="text-muted small")
            ])
        ], width=4),
    ], className="mb-5"),

    html.Hr(),
    dbc.Row([
        dbc.Col(
            html.Footer("Made By Team Mred", className="text-center text-muted py-4 fw-light"),
            width=12
        )
    ])
])

# --- 4. CALLBACKS ---

@callback(
    [Output("map", "figure"),
     Output("authorized-count", "children"),
     Output("unauthorized-count", "children"),
     Output("auth-table", "data"),
     Output("unauth-table", "data"),
     Output("select-auth", "options"),
     Output("select-unauth", "options"),
     Output("inspect-id", "options"),
     Output("inspect-id", "value")],
    [Input("data-store", "data"),
     Input("basemap-style", "value")]
)
def update_ui(data, basemap_style):
    current_df = pd.DataFrame(data)
    fig = px.scatter_mapbox(
        current_df, lat="lat", lon="lon",
        color="is_authorized",
        color_discrete_map={True: "green", False: "red"},
        hover_name="location_name",
        zoom=14, height=550
    )

    layers = []
    if basemap_style == "white-bg":
        layers = [{
            "below": 'traces', "sourcetype": "raster",
            "source": ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"]
        }]

    fig.update_layout(
        mapbox_style=basemap_style, mapbox_layers=layers,
        margin={"r":0,"t":0,"l":0,"b":0}, showlegend=False
    )
    fig.update_traces(marker=dict(size=14, opacity=0.8))

    auth_df = current_df[current_df['is_authorized']]
    unauth_df = current_df[~current_df['is_authorized']]
    
    auth_opts = [{"label": f"ID: {r['id']}", "value": r['id']} for r in auth_df.to_dict('records')]
    unauth_opts = [{"label": f"ID: {r['id']}", "value": r['id']} for r in unauth_df.to_dict('records')]
    all_opts = [{"label": f"Site {r['id']}", "value": r['id']} for r in current_df.to_dict('records')]
    
    default_val = current_df['id'].iloc[0] if not current_df.empty else None
    return fig, str(len(auth_df)), str(len(unauth_df)), auth_df.to_dict('records'), unauth_df.to_dict('records'), auth_opts, unauth_opts, all_opts, default_val

@callback(
    Output("data-store", "data"),
    [Input("btn-revoke", "n_clicks"), Input("btn-approve", "n_clicks")],
    [State("select-auth", "value"), State("select-unauth", "value"), State("data-store", "data")],
    prevent_initial_call=True
)
def update_status(n_revoke, n_approve, auth_id, unauth_id, current_data):
    ctx = dash.callback_context
    if not ctx.triggered: return current_data
    dff = pd.DataFrame(current_data)
    trigger = ctx.triggered[0]['prop_id'].split('.')[0]
    if trigger == "btn-revoke" and auth_id:
        dff.loc[dff['id'] == str(auth_id), 'is_authorized'] = False
    elif trigger == "btn-approve" and unauth_id:
        dff.loc[dff['id'] == str(unauth_id), 'is_authorized'] = True
    return dff.to_dict('records')

@callback(
    [Output("inspection-satellite-map", "figure"),
     Output("inspection-polygon-map", "figure"),
     Output("site-name", "children"),
     Output("site-status", "children"),
     Output("site-expansion", "children"),
     Output("site-coords", "children")],
    [Input("inspect-id", "value")],
    [State("data-store", "data")]
)
def update_inspection(site_id, current_data):
    if site_id is None or not current_data:
        return {}, {}, "No Site Selected", "", "", ""
    
    dff = pd.DataFrame(current_data)
    filtered_df = dff[dff['id'].astype(str) == str(site_id)]
    if filtered_df.empty: return {}, {}, "Not Found", "", "", ""
    row = filtered_df.iloc[0]

    # --- GeoJSON Extraction ---
    # Authorized Footprint
    selected_auth = [f for f in authorized_geojson.get('features', []) 
                     if str(f.get('properties', {}).get('id')) == str(site_id)]
    auth_geojson = {"type": "FeatureCollection", "features": selected_auth}

    # Detected Footprint (Violation Area)
    selected_detected = [f for f in detected_geojson.get('features', []) 
                         if str(f.get('properties', {}).get('id')) == str(site_id)]
    detected_geojson_feature = {"type": "FeatureCollection", "features": selected_detected}

    sat_layer = {
        "sourcetype": "raster",
        "source": ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"],
        "below": "traces"
    }

    # --- MAP 1: Satellite + Detection Boundary (Red) ---
    fig_sat = px.scatter_mapbox(lat=[row['lat']], lon=[row['lon']], zoom=18, height=350)
    
    layers_map1 = [sat_layer]
    if not row['is_authorized']:
        # Boundary-type polygon for unauthorized construction
        layers_map1.append({
            "sourcetype": "geojson", "type": "fill", "source": detected_geojson_feature, 
            "color": "rgba(220, 38, 38, 0.4)", "below": "traces"
        })
        layers_map1.append({
            "sourcetype": "geojson", "type": "line", "source": detected_geojson_feature, 
            "color": "rgb(220, 38, 38)", "line": {"width": 3}, "below": "traces"
        })

    fig_sat.update_layout(mapbox_style="white-bg", mapbox_layers=layers_map1, margin={"r":0,"t":0,"l":0,"b":0})
    fig_sat.update_traces(marker=dict(size=0))

    # --- MAP 2: Satellite + Authorized Footprint (Green) ---
    fig_poly = px.scatter_mapbox(lat=[row['lat']], lon=[row['lon']], zoom=18, height=350)
    poly_fill = {"sourcetype": "geojson", "type": "fill", "source": auth_geojson, "color": "rgba(34, 197, 94, 0.4)", "below": "traces"}
    poly_line = {"sourcetype": "geojson", "type": "line", "source": auth_geojson, "color": "rgb(34, 197, 94)", "line": {"width": 2}, "below": "traces"}

    fig_poly.update_layout(mapbox_style="white-bg", mapbox_layers=[sat_layer, poly_fill, poly_line], margin={"r":0,"t":0,"l":0,"b":0})
    fig_poly.update_traces(marker=dict(size=0))

    # --- UI Details ---
    status_text = "Authorized" if row['is_authorized'] else "🚨 UNAUTHORIZED"
    status_color = "text-success" if row['is_authorized'] else "text-danger"
    status_display = html.Span(status_text, className=f"fw-bold {status_color}")
    expansion_display = f"Expansion: {row['expansion_pct']:.2f}%"
    
    return fig_sat, fig_poly, row['location_name'], status_display, expansion_display, f"GPS: {row['lat']:.5f}, {row['lon']:.5f}"

if __name__ == '__main__':
    app.run(debug=True)