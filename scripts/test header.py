import pandas as pd
import os

path = "data/elections_2020"

for i in range(1, 21):
    file_path = os.path.join(path, f"Arr_{i}.csv")
    df = pd.read_csv(file_path, encoding="utf-8-sig")
    print(f"\n👉 Colonnes de Arr_{i}.csv :")
    print(df.columns.tolist())

# Chargement du fond de carte GeoJSON
geojson_path = "data/geojson/bureaux_2020.geojson"
gdf_geo = gpd.read_file(geojson_path)
print(f"✅ GeoJSON chargé : {gdf_geo.shape}")

print("📋 Colonnes disponibles dans le GeoDataFrame :", gdf_geo.columns.tolist())

