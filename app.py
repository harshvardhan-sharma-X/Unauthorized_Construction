import dash
from dash import dcc, html, Input, Output, State, callback, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import json
import os
import zipfile

# --- 0. IMAGE PRE-PROCESSING (Extracting Zip) ---
IMAGE_DIR = 'assets/audit_images'
ZIP_PATH = 'assets/audit_images.zip'

if os.path.exists(ZIP_PATH):
    with zipfile.ZipFile(ZIP_PATH, 'r') as z:
        z.extractall(IMAGE_DIR)

# Create a mapping of index to filename
image_mapping = {}
if os.path.exists(IMAGE_DIR):
    for filename in os.listdir(IMAGE_DIR):
        if filename.startswith('site_'):
            try:
                # Extract index from 'site_{index}_...'
                idx = filename.split('_')[1]
                image_mapping[idx] = filename
            except IndexError:
                continue

# --- 1. DATA LOADING & PRE-PROCESSING ---
try:
    with open('assets/authorized_footprints.json') as f:
        authorized_geojson = json.load(f)
except FileNotFoundError:
    authorized_geojson = {"type": "FeatureCollection", "features": []}

try:
    with open('assets/detected_footprints.json') as f:
        detected_geojson = json.load(f)
except FileNotFoundError:
    detected_geojson = {"type": "FeatureCollection", "features": []}

try:
    # Load the AI compliance report
    compliance_df = pd.read_csv('assets/final_compliance_report.csv')
except FileNotFoundError:
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
        avg_lat, avg_lon = sum(lats)/len(lats), sum(lons)/len(lons)
        site_id = str(feature.get('properties', {}).get('id', i + 1000))
        
        # Match with AI Compliance Report
        comp_row = compliance_df[compliance_df['Site_Index'] == i]
        is_auth = comp_row.iloc[0]['Compliance_Status'] == "AUTHORIZED" if not comp_row.empty else True
        expansion = comp_row.iloc[0]['Exceedance_Percent'] if not comp_row.empty else 0.0

        real_site_data.append({
            'id': site_id,
            'index': str(i),
            'location_name': f"South Delhi Plot {site_id}",
            'lat': avg_lat, 'lon': avg_lon,
            'is_authorized': is_auth,
            'expansion_pct': expansion
        })
    except Exception: continue

df = pd.DataFrame(real_site_data)

# --- 2. INITIALIZE APP ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# --- 3. LAYOUT ---
app.layout = dbc.Container(fluid=True, children=[
    html.H1("Urban Construction Monitoring Dashboard", className="text-center my-4"),
    dcc.Store(id='data-store', data=df.to_dict('records')),

    dbc.Row([
        dbc.Col(dbc.Card([dbc.CardBody([html.H4("✅ Authorized Sites"), html.H2(id="authorized-count", className="card-text text-success")])], color="success", outline=True), width=6),
        dbc.Col(dbc.Card([dbc.CardBody([html.H4("🚨 Unauthorized Sites"), html.H2(id="unauthorized-count", className="card-text text-danger")])], color="danger", outline=True), width=6),
    ], className="mb-4"),

    html.Hr(),
    html.H3("Interactive City Map"),
    dcc.Dropdown(id="basemap-style", options=[{"label": "Clean Street View", "value": "carto-positron"}, {"label": "Satellite View", "value": "white-bg"}], value="carto-positron", clearable=False, className="mb-3 w-50"),
    dcc.Graph(id="map", config={'scrollZoom': True}, style={"height": "550px"}),

    html.Hr(),
    dbc.Row([
        dbc.Col([
            html.H4("✅ Authorized", className="text-success"),
            dash_table.DataTable(id="auth-table", columns=[{"name": "ID", "id": "id"}, {"name": "Location", "id": "location_name"}], style_header={'fontWeight': 'bold'}, page_action='none', fixed_rows={'headers': True}, style_table={'height': '400px', 'overflowY': 'auto'}),
            dcc.Dropdown(id="select-auth", placeholder="Select to Revoke...", className="mt-2"),
            dbc.Button("🚨 Flag Unauthorized", id="btn-revoke", color="danger", className="w-100 mt-2")
        ], width=6),
        dbc.Col([
            html.H4("🚩 Unauthorized", className="text-danger"),
            dash_table.DataTable(id="unauth-table", columns=[{"name": "ID", "id": "id"}, {"name": "Location", "id": "location_name"}], style_header={'fontWeight': 'bold'}, page_action='none', fixed_rows={'headers': True}, style_table={'height': '400px', 'overflowY': 'auto'}),
            dcc.Dropdown(id="select-unauth", placeholder="Select to Approve...", className="mt-2"),
            dbc.Button("✔️ Approve Construction", id="btn-approve", color="success", className="w-100 mt-2")
        ], width=6),
    ], className="mb-5"),

    html.Hr(),
    html.H3("Site Inspection Preview"),
    dcc.Dropdown(id="inspect-id", className="mb-3"),

    dbc.Row([
        dbc.Col(dcc.Graph(id="inspection-violation-map", style={"height": "350px"}), width=4),
        dbc.Col(dcc.Graph(id="inspection-authorized-map", style={"height": "350px"}), width=4),
        dbc.Col([
            html.Div(className="p-3 bg-light rounded", children=[
                html.H5(id="site-name", className="fw-bold"),
                html.Hr(),
                html.P(id="site-status", className="mb-2"),
                html.P(id="site-expansion", className="mb-2 fw-bold text-primary"),
                html.P(id="site-coords", className="text-muted small"),
                html.Hr(),
                html.H6("AI Audit Image:"),
                html.Div(id="audit-image-container", className="text-center", children=[
                    html.Img(id="site-audit-image", style={"maxWidth": "100%", "borderRadius": "5px"}),
                    html.P(id="image-status-msg", className="text-muted italic")
                ])
            ])
        ], width=4),
    ], className="mb-5"),

    dbc.Row([dbc.Col(html.Footer("Made By Team Mred", className="text-center text-muted py-4 fw-light"), width=12)])
])

# --- 4. CALLBACKS ---

@callback(
    [Output("map", "figure"), Output("authorized-count", "children"), Output("unauthorized-count", "children"),
    Output("auth-table", "data"), Output("unauth-table", "data"), Output("select-auth", "options"),
    Output("select-unauth", "options"), Output("inspect-id", "options"), Output("inspect-id", "value")],
    [Input("data-store", "data"), Input("basemap-style", "value")]
)
def update_ui(data, basemap_style):
    current_df = pd.DataFrame(data)
    fig = px.scatter_mapbox(current_df, lat="lat", lon="lon", color="is_authorized",
                            color_discrete_map={True: "green", False: "red"}, zoom=14, height=550)
    
    layers = []
    if basemap_style == "white-bg":
        layers = [{"below": 'traces', "sourcetype": "raster", "source": ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"]}]
    
    fig.update_layout(mapbox_style=basemap_style, mapbox_layers=layers, margin={"r":0,"t":0,"l":0,"b":0}, showlegend=False)
    
    # FIX: Removed 'outline' property as it is invalid for scattermapbox
    fig.update_traces(marker=dict(size=14, opacity=0.8))

    auth_df = current_df[current_df['is_authorized']]
    unauth_df = current_df[~current_df['is_authorized']]
    
    auth_opts = [{"label": f"ID: {r['id']}", "value": r['id']} for r in auth_df.to_dict('records')]
    unauth_opts = [{"label": f"ID: {r['id']}", "value": r['id']} for r in unauth_df.to_dict('records')]
    all_opts = [{"label": f"Site {r['id']}", "value": r['id']} for r in current_df.to_dict('records')]
    
    default_val = current_df['id'].iloc[0] if not current_df.empty else None
    return fig, str(len(auth_df)), str(len(unauth_df)), auth_df.to_dict('records'), unauth_df.to_dict('records'), auth_opts, unauth_opts, all_opts, default_val

@callback(
    Output("data-store", "data"), [Input("btn-revoke", "n_clicks"), Input("btn-approve", "n_clicks")],
    [State("select-auth", "value"), State("select-unauth", "value"), State("data-store", "data")], prevent_initial_call=True
)
def update_status(n_revoke, n_approve, auth_id, unauth_id, current_data):
    dff = pd.DataFrame(current_data)
    trigger = dash.callback_context.triggered[0]['prop_id'].split('.')[0]
    if trigger == "btn-revoke" and auth_id: dff.loc[dff['id'] == str(auth_id), 'is_authorized'] = False
    elif trigger == "btn-approve" and unauth_id: dff.loc[dff['id'] == str(unauth_id), 'is_authorized'] = True
    return dff.to_dict('records')

@callback(
    [Output("inspection-violation-map", "figure"), Output("inspection-authorized-map", "figure"),
    Output("site-name", "children"), Output("site-status", "children"),
    Output("site-expansion", "children"), Output("site-coords", "children"),
    Output("site-audit-image", "src"), Output("image-status-msg", "children")],
    [Input("inspect-id", "value")], [State("data-store", "data")]
)
def update_inspection(site_id, current_data):
    if not site_id: return {}, {}, "No Selection", "", "", "", "", "No Selection"
    row = pd.DataFrame(current_data).query(f"id == '{site_id}'").iloc[0]
    site_idx = str(row['index'])

    # 1. Image Logic
    img_filename = image_mapping.get(site_idx)
    if img_filename:
        img_src = f"/assets/audit_images/{img_filename}"
        status_msg = ""
    else:
        img_src = ""
        status_msg = "Image not available"

    # 2. Polygon Prep
    def get_gj(src): return {"type": "FeatureCollection", "features": [f for f in src.get('features', []) if str(f.get('properties', {}).get('id')) == str(site_id)]}
    auth_gj, det_gj = get_gj(authorized_geojson), get_gj(detected_geojson)
    sat_layer = {"sourcetype": "raster", "source": ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"], "below": "traces"}

    # Map 1: Violation
    fig_v = px.scatter_mapbox(lat=[row['lat']], lon=[row['lon']], zoom=18, height=350)
    v_layers = [sat_layer]
    if not row['is_authorized']:
        v_layers += [{"sourcetype": "geojson", "type": "fill", "source": det_gj, "color": "rgba(220, 38, 38, 0.4)", "below": "traces"},
                    {"sourcetype": "geojson", "type": "line", "source": det_gj, "color": "red", "line": {"width": 3}, "below": "traces"}]
    fig_v.update_layout(mapbox_style="white-bg", mapbox_layers=v_layers, margin={"r":0,"t":0,"l":0,"b":0})
    fig_v.update_traces(marker=dict(size=0))

    # Map 2: Authorized
    fig_a = px.scatter_mapbox(lat=[row['lat']], lon=[row['lon']], zoom=18, height=350)
    a_layers = [sat_layer, {"sourcetype": "geojson", "type": "fill", "source": auth_gj, "color": "rgba(34, 197, 94, 0.4)", "below": "traces"},
                {"sourcetype": "geojson", "type": "line", "source": auth_gj, "color": "green", "line": {"width": 2}, "below": "traces"}]
    fig_a.update_layout(mapbox_style="white-bg", mapbox_layers=a_layers, margin={"r":0,"t":0,"l":0,"b":0})
    fig_a.update_traces(marker=dict(size=0))

    status_display = html.Span("Authorized" if row['is_authorized'] else "🚨 UNAUTHORIZED", className=f"fw-bold {'text-success' if row['is_authorized'] else 'text-danger'}")
    return fig_v, fig_a, row['location_name'], status_display, f"Expansion: {row['expansion_pct']:.2f}%", f"GPS: {row['lat']:.5f}, {row['lon']:.5f}", img_src, status_msg

if __name__ == '__main__':
    app.run(debug=True)