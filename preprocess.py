import pandas as pd
import geopandas as gpd
from shapely import wkt
import os


df = pd.read_csv('open_buildings_v3_polygons_your_own_wkt_polygon (1).csv.gz')

df = df[df['confidence'] >= 0.90]

lat_center, lon_center = 28.6139, 77.2090 
margin = 0.01 

df = df[
    (df['latitude'] >= 28.55) & (df['latitude'] <= 28.60) &
    (df['longitude'] >= 77.20) & (df['longitude'] <= 77.25)
]

df['geometry'] = df['geometry'].apply(wkt.loads)
gdf = gpd.GeoDataFrame(df, geometry='geometry', crs="EPSG:4326")

gdf['geometry'] = gdf['geometry'].simplify(0.0001, preserve_topology=True)

if not os.path.exists('assets'): os.makedirs('assets')
gdf.to_file("assets/authorized_footprints.json", driver='GeoJSON')

print(f"✅ Pre-processing complete. Reduced to {len(gdf)} buildings.")