import pandas as pd
import geopandas as gpd
from shapely import wkt
import os

# 1. Load the CSV
df = pd.read_csv('open_buildings_v3_polygons_your_own_wkt_polygon (1).csv.gz')

# --- NEW: FILTER FOR RELIABLE BUILDINGS ONLY ---
# Google recommends starting by filtering out buildings below 
# the 90% precision threshold for the best quality.
df = df[df['confidence'] >= 0.90]

# 2. AGGRESSIVE FILTERING (Narrow this to your EXACT 1-2km project area)
# These coordinates should match the center of your 'buildings.jpg'
lat_center, lon_center = 28.6139, 77.2090 
margin = 0.01  # Approximately 1km radius

df = df[
    (df['latitude'] >= 28.55) & (df['latitude'] <= 28.60) &
    (df['longitude'] >= 77.20) & (df['longitude'] <= 77.25)
]

# 3. Convert to Geometries
df['geometry'] = df['geometry'].apply(wkt.loads)
gdf = gpd.GeoDataFrame(df, geometry='geometry', crs="EPSG:4326")

# 4. HEAVY SIMPLIFICATION
# This reduces the number of points in each polygon drastically
gdf['geometry'] = gdf['geometry'].simplify(0.0001, preserve_topology=True)

# 5. Save the lightweight file
if not os.path.exists('assets'): os.makedirs('assets')
gdf.to_file("assets/authorized_footprints.json", driver='GeoJSON')

print(f"✅ Pre-processing complete. Reduced to {len(gdf)} buildings.")