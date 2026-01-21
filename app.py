import dash
from dash import dcc, html, Input, Output, State, callback, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import json 

# --- 1. DATA LOADING & PRE-PROCESSING ---
# Load the pre-processed GeoJSON once when the app starts
try:
    with open('assets/authorized_footprints.json') as f:
        authorized_geojson = json.load(f)
except FileNotFoundError:
    print("Error: assets/authorized_footprints.json not found.")
    authorized_geojson = {"type": "FeatureCollection", "features": []}

features = authorized_geojson['features']
real_site_data = []

for i, feature in enumerate(features):
    # Handling coordinate extraction
    geom_type = feature['geometry']['type']
    if geom_type == 'Polygon':
        coords = feature['geometry']['coordinates'][0]
    elif geom_type == 'MultiPolygon':
        coords = feature['geometry']['coordinates'][0][0]
    else:
        continue

    lons, lats = zip(*coords)
    avg_lat = sum(lats) / len(lats)
    avg_lon = sum(lons) / len(lons)
    
    # Ensure ID exists; default to index if missing
    site_id = feature['properties'].get('id', i + 1000)
    
    real_site_data.append({
        'id': site_id,
        'location_name': f"South Delhi Plot {site_id}",
        'lat': avg_lat,
        'lon': avg_lon,
        'is_authorized': True,
        'image_url': f"assets/site_{site_id}_preview.png"
    })

# Primary DataFrame for the app
df = pd.DataFrame(real_site_data)

# --- 2. INITIALIZE APP ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Store the data in dcc.Store
store = dcc.Store(id='data-store', data=df.to_dict('records'))

# --- 3. LAYOUT ---
app.layout = dbc.Container(fluid=True, children=[
    html.H1("Urban Construction Monitoring Dashboard", className="text-center my-4"),
    
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
            {"label": "Street View", "value": "streets"},
            {"label": "Satellite View", "value": "satellite"},
            {"label": "Hybrid (Sat + Streets)", "value": "satellite-streets"},
        ],
        value="streets",
        clearable=False,
        className="mb-3 w-50"
    ),
    dcc.Graph(id="map", config={'scrollZoom': True}, style={"height": "550px"}),

    html.Hr(),
    dbc.Row([
        dbc.Col([
            html.H4("✅ Authorized", className="text-success"),
            dash_table.DataTable(id="auth-table", columns=[{"name": "ID", "id": "id"}, {"name": "Location", "id": "location_name"}], style_header={'fontWeight': 'bold'}),
            dcc.Dropdown(id="select-auth", placeholder="Select Site to Revoke...", className="mt-2"),
            dbc.Button("🚨 Flag as Unauthorized", id="btn-revoke", color="danger", className="w-100 mt-2")
        ], width=6),
        dbc.Col([
            html.H4("🚩 Unauthorized", className="text-danger"),
            dash_table.DataTable(id="unauth-table", columns=[{"name": "ID", "id": "id"}, {"name": "Location", "id": "location_name"}], style_header={'fontWeight': 'bold'}),
            dcc.Dropdown(id="select-unauth", placeholder="Select Site to Approve...", className="mt-2"),
            dbc.Button("✔️ Approve Construction", id="btn-approve", color="success", className="w-100 mt-2")
        ], width=6),
    ], className="mb-5"),

    html.Hr(),
    html.H3("Site Inspection Preview"),
    dcc.Dropdown(
        id="inspect-id",
        options=[{"label": f"{r['id']} - {r['location_name']}", "value": r['id']} for r in real_site_data],
        value=real_site_data[0]['id'] if real_site_data else None,
        className="mb-3"
    ),

    dbc.Row([
        # Minimap 1: Pure Satellite View
        dbc.Col(dcc.Graph(id="inspection-satellite-map", style={"height": "350px"}), width=4),
        # Minimap 2: Satellite + Authorized Polygon
        dbc.Col(dcc.Graph(id="inspection-polygon-map", style={"height": "350px"}), width=4),
        # Details
        dbc.Col([
            html.Div(className="p-3 bg-light rounded", children=[
                html.H5(id="site-name", className="fw-bold"),
                html.Hr(),
                html.P(id="site-status", className="mb-2"),
                html.P(id="site-coords", className="text-muted small")
            ])
        ], width=4),
    ]),
    store
])

# --- 4. CALLBACKS ---

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
    current_df = pd.DataFrame(data)
    
    fig = px.scatter_mapbox(
        current_df, lat="lat", lon="lon",
        color="is_authorized",
        color_discrete_map={True: "green", False: "red"},
        hover_name="location_name",
        zoom=14, height=550
    )

    layers = [
        {
            "below": 'traces', "sourcetype": "raster",
            "source": ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"],
            "visible": basemap_style in ["satellite", "satellite-streets"]
        },
        {
            "below": 'traces', "sourcetype": "raster",
            "source": ["https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}"],
            "visible": basemap_style == "satellite-streets"
        }
    ]

    fig.update_layout(
        mapbox_style="carto-positron" if basemap_style == "streets" else "white-bg", 
        mapbox_layers=layers, margin={"r":0,"t":0,"l":0,"b":0}, showlegend=False
    )
    fig.update_traces(marker=dict(size=12, opacity=0.7))

    # Prep table data
    auth_df = current_df[current_df['is_authorized']]
    unauth_df = current_df[~current_df['is_authorized']]
    
    auth_opts = [{"label": f"{r['id']} - {r['location_name']}", "value": r['id']} for r in auth_df.to_dict('records')]
    unauth_opts = [{"label": f"{r['id']} - {r['location_name']}", "value": r['id']} for r in unauth_df.to_dict('records')]
    
    return fig, str(len(auth_df)), str(len(unauth_df)), auth_df.to_dict('records'), unauth_df.to_dict('records'), auth_opts, unauth_opts

@callback(
    Output("data-store", "data"),
    [Input("btn-revoke", "n_clicks"), Input("btn-approve", "n_clicks")],
    [State("select-auth", "value"), State("select-unauth", "value"), State("data-store", "data")],
    prevent_initial_call=True
)
def update_status(n_revoke, n_approve, auth_id, unauth_id, current_data):
    dff = pd.DataFrame(current_data)
    ctx = dash.callback_context
    trigger = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger == "btn-revoke" and auth_id:
        dff.loc[dff['id'] == auth_id, 'is_authorized'] = False
    elif trigger == "btn-approve" and unauth_id:
        dff.loc[dff['id'] == unauth_id, 'is_authorized'] = True
    
    return dff.to_dict('records')

@callback(
    [Output("inspection-satellite-map", "figure"),
    Output("inspection-polygon-map", "figure"),
    Output("site-name", "children"),
    Output("site-status", "children"),
    Output("site-coords", "children")],
    Input("inspect-id", "value"),
    State("data-store", "data")
)
def update_inspection(site_id, current_data):
    if not site_id:
        return {}, {}, "No Site Selected", "", ""
    
    # 1. Get the data row for the selected site
    dff = pd.DataFrame(current_data)
    # Ensure site_id comparison matches types (casting to string for safety)
    row = dff[dff['id'].astype(str) == str(site_id)].iloc[0]
    
    # 2. Extract the specific GeoJSON feature for this site
    selected_features = [f for f in authorized_geojson['features'] 
                        if str(f['properties'].get('id')) == str(site_id)]
    
    preview_geojson = {"type": "FeatureCollection", "features": selected_features}

    # Helper to generate layers
    def get_layers(show_polygon=False):
        layers = [{
            "sourcetype": "raster",
            "source": ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"],
            "below": "traces"
        }]
        
        if show_polygon and selected_features:
            layers.append({
                "sourcetype": "geojson",
                "type": "fill",
                "source": preview_geojson,
                "color": "rgba(34, 197, 94, 0.5)", # Green semi-transparent fill
                "outlinecolor": "rgb(34, 197, 94)",
                "below": "traces"
            })
        return layers

    # 3. Create Figure 1: Pure Satellite
    fig_sat = px.scatter_mapbox(lat=[row['lat']], lon=[row['lon']], zoom=18, height=350)
    fig_sat.update_layout(
        mapbox_style="white-bg",
        mapbox_layers=get_layers(show_polygon=False),
        margin={"r":0,"t":0,"l":0,"b":0},
        showlegend=False
    )
    fig_sat.update_traces(marker=dict(size=0)) # Hide the center point marker

    # 4. Create Figure 2: Satellite + Polygon
    fig_poly = px.scatter_mapbox(lat=[row['lat']], lon=[row['lon']], zoom=18, height=350)
    fig_poly.update_layout(
        mapbox_style="white-bg",
        mapbox_layers=get_layers(show_polygon=True),
        margin={"r":0,"t":0,"l":0,"b":0},
        showlegend=False
    )
    fig_poly.update_traces(marker=dict(size=0))

    # 5. Metadata and Status
    status_text = "Authorized" if row['is_authorized'] else "🚨 UNAUTHORIZED"
    status_color = "text-success" if row['is_authorized'] else "text-danger"
    status_display = html.Span(status_text, className=f"fw-bold {status_color}")
    coords_display = f"GPS: {row['lat']:.5f}, {row['lon']:.5f}"
    
    return fig_sat, fig_poly, row['location_name'], status_display, coords_display

    # Common layout for minimaps
    def get_minimap_layout(has_poly=False):
        layers = [{
            "below": 'traces',
            "sourcetype": "raster",
            "source": ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"]
        }]
    
        # Add polygon layer if requested and features exist
        if has_poly and selected_feature:
            layers.append({
                "sourcetype": "geojson",
                "type": "fill",
                "source": preview_geojson,
                "color": "rgba(34, 197, 94, 0.6)", # Increased opacity slightly for visibility
                "below": "traces"
            })
        return layers

    # Figure 1: Sat
    fig_sat = px.scatter_mapbox(lat=[row['lat']], lon=[row['lon']], zoom=18, height=350)
    fig_sat.update_layout(mapbox_style="white-bg", mapbox_layers=get_minimap_layout(), margin={"r":0,"t":0,"l":0,"b":0})
    fig_sat.update_traces(marker=dict(size=0))

    # Figure 2: Poly
    fig_poly = px.scatter_mapbox(lat=[row['lat']], lon=[row['lon']], zoom=18, height=350)
    fig_poly.update_layout(mapbox_style="white-bg", mapbox_layers=get_minimap_layout(True), margin={"r":0,"t":0,"l":0,"b":0})
    fig_poly.update_traces(marker=dict(size=0))

    status = "Authorized" if row['is_authorized'] else "🚨 UNAUTHORIZED"
    color = "text-success" if row['is_authorized'] else "text-danger"
    
    return fig_sat, fig_poly, row['location_name'], html.Span(status, className=f"fw-bold {color}"), f"GPS: {row['lat']:.5f}, {row['lon']:.5f}"

if __name__ == '__main__':
    app.run(debug=True)