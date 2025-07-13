import pandas as pd
import geopandas as gpd
import folium
import os

print("📍 Chargement du fond de carte...")

# Chargement du fond de carte GeoJSON
geojson_path = "data/geojson/bureaux_2020.geojson"
gdf_geo = gpd.read_file(geojson_path)
print(f"✅ GeoJSON chargé : {gdf_geo.shape}")

# Harmonisation des colonnes pour fusion
gdf_geo = gdf_geo.rename(columns={"id_bv": "ID_BVOTE", "arrondissement": "NUM_ARROND"})
gdf_geo["ID_BVOTE_FULL"] = gdf_geo["NUM_ARROND"].astype(str) + "-" + gdf_geo["ID_BVOTE"].astype(str)

# Préparation des données de vote
print("🔁 Fusion des CSV arrondissement par arrondissement...")
csv_folder = "data/elections_2020"
df_votes = pd.DataFrame()

for i in range(1, 21):
    file_path = os.path.join(csv_folder, f"Arr_{i}.csv")
    df_i = pd.read_csv(file_path, encoding="utf-8-sig", sep=";")
    df_i["NUM_ARROND"] = i
    df_votes = pd.concat([df_votes, df_i], ignore_index=True)

print(f"✅ Données fusionnées : {df_votes.shape}")

# Construction d'un identifiant unique pour le merge
df_votes = df_votes[df_votes["ID_BVOTE"].notna()]  # on enlève les lignes vides
df_votes["ID_BVOTE_FULL"] = (
    df_votes["NUM_ARROND"].astype(str) + "-"
    + df_votes["NUM_ARROND"].astype(str) + "-"
    + df_votes["ID_BVOTE"].astype(int).astype(str)
)

# Calcul du taux d’abstention
df_votes["Taux_abstention"] = (df_votes["NB_INSCR"] - df_votes["NB_VOTANT"]) / df_votes["NB_INSCR"] * 100

# Fusion des données géographiques et de vote
print("📌 Fusion avec le GeoDataFrame...")
gdf_merge = gdf_geo.merge(df_votes, on="ID_BVOTE_FULL")
print(f"✅ Fusion réussie : {gdf_merge.shape}")

# Création de la carte Folium
print("🗺️ Création de la carte...")
carte = folium.Map(location=[48.8566, 2.3522], zoom_start=12, tiles="cartodbpositron")

# Ajout d'une couche pour le taux d’abstention
folium.Choropleth(
    geo_data=gdf_merge,
    name="Taux d’abstention",
    data=gdf_merge,
    columns=["ID_BVOTE_FULL", "Taux_abstention"],
    key_on="feature.properties.ID_BVOTE_FULL",
    fill_color="Reds",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name="Taux d’abstention (%)",
).add_to(carte)



# Ajout des popups cliquables persistants et survolables
for _, row in gdf_merge.iterrows():
    bureau_id = row["ID_BVOTE_FULL"]
    arr, _, num = bureau_id.split("-")
    bureau_clean = f"{arr}-{num}"

    full_info = (
        f"<b>Bureau :</b> {bureau_clean}<br>"
        f"<b>Inscrits :</b> {int(row['NB_INSCR']):,}".replace(",", " ") + "<br>"
        f"<b>Votants :</b> {int(row['NB_VOTANT']):,}".replace(",", " ") + "<br>"
        f"<b>Abstention :</b> {round(row['Taux_abstention'])} %"
    )

    geojson = folium.GeoJson(
        row["geometry"],
        style_function=lambda x: {"fillColor": "#00000000", "weight": 0},
        highlight_function=lambda x: {"weight": 2, "color": "black"},
        tooltip=folium.Tooltip(full_info, sticky=False),  # affiché au survol
        popup=folium.Popup(full_info, max_width=300)      # affiché au clic et reste ouvert
    )
    geojson.add_to(carte)




# 📁 Création dossier output si nécessaire
os.makedirs("output", exist_ok=True)



# Sauvegarde de la carte
os.makedirs("output", exist_ok=True)
output_path = "output/carte_municipales_paris_2020.html"
carte.save(output_path)
print(f"✅ Carte sauvegardée dans le fichier : {output_path}")

