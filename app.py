import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# --- PAGE CONFIG ---
st.set_page_config(page_title="City Construction Monitor", layout="wide")

# --- INITIALIZE MOCK DATA ---
# We use session_state so the data "remembers" changes when you click buttons
if 'construction_data' not in st.session_state:
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
    st.session_state.construction_data = pd.DataFrame(data)

df = st.session_state.construction_data

# --- APP HEADER ---
st.title("🏙️ Urban Construction Monitoring Dashboard")
st.markdown("Automated detection of unauthorized construction using simulated drone/satellite data.")

#The Counter
col_a,col_b = st.columns(2)

with col_a:
    st.metric("✅ Authorized Sites", (df['is_authorized'] == True).sum())

with col_b:
    st.metric("🚨 Unauthorized Sites", (df['is_authorized'] == False).sum())


# --- TOP SECTION: THE MAP ---
st.subheader("Interactive City Map")
# Initialize the map centered at the average coordinates
m = folium.Map(location=[df['lat'].mean(), df['lon'].mean()], zoom_start=11, tiles=None)
folium.TileLayer(tiles="OpenStreetMap", name="Street View", control=True, show=True).add_to(m)
folium.TileLayer(
    tiles = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attr = "Esri",
    name = "Satellite View",
    overlay = False,
    control = True,
    show = False
).add_to(m) 
folium.LayerControl(collapsed=False).add_to(m)

# Add markers based on status
for idx, row in df.iterrows():
    color = "green" if row['is_authorized'] else "red"
    folium.Marker(
        [row['lat'], row['lon']],
        popup=f"Site {row['id']}: {row['location_name']}",
        icon=folium.Icon(color=color, icon='info-sign')
    ).add_to(m)

# Render the map in Streamlit
st_folium(m, width=True, height=550)

st.divider()

# --- BOTTOM SECTION: DATA MANAGEMENT ---
col1, col2 = st.columns(2)

# --- AUTHORIZED SITES TABLE ---
with col1:
    st.success("✅ Authorized Constructions")
    auth_df = df[df['is_authorized'] == True]
    st.table(auth_df[['id', 'location_name']])
    
    selected_auth = st.selectbox("Select Site to Revoke Authorization:", auth_df['id'])
    if st.button("🚨 Flag as Unauthorized"):
        st.session_state.construction_data.loc[df['id'] == selected_auth, 'is_authorized'] = False
        st.rerun()

# --- UNAUTHORIZED SITES TABLE ---
with col2:
    st.error("🚩 Unauthorized Violations")
    unauth_df = df[df['is_authorized'] == False]
    st.table(unauth_df[['id', 'location_name']])
    
    selected_unauth = st.selectbox("Select Site to Authorize:", unauth_df['id'])
    if st.button("✔️ Approve Construction"):
        st.session_state.construction_data.loc[df['id'] == selected_unauth, 'is_authorized'] = True
        st.rerun()

st.divider()

# --- SATELLITE IMAGE VIEW ---
st.subheader("🛰️ Satellite Data Inspection")
inspect_id = st.selectbox("Choose a Site ID to view drone imagery:", df['id'])
site_row = df[df['id'] == inspect_id].iloc[0]

img_col, text_col = st.columns([2, 1])
with img_col:
    # In a real project, you would replace this with the path to your drone images
    st.image(site_row['image_url'], caption=f"Satellite View of Site {inspect_id}", use_container_width=True)
with text_col:
    st.write(f"**Location:** {site_row['location_name']}")
    st.write(f"**Status:** {'Authorized' if site_row['is_authorized'] else 'UNAUTHORIZED'}")
    st.write(f"**Coordinates:** {site_row['lat']}, {site_row['lon']}")


