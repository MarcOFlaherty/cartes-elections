import pandas as pd
import geopandas as gpd
import folium
import os

# === Chargement ===
print("📍 Chargement du GeoJSON...")

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


# === Colonnes candidats ===
colonnes_non_candidats = [
    "ID_BVOTE", "SCRUTIN", "ANNEE", "TOUR", "DATE", "NUM_CIRC", "NUM_QUARTIER", "NUM_ARROND",
    "NUM_BUREAU", "NB_PROCU", "NB_INSCR", "NB_EMARG", "NB_VOTANT", "NB_BLANC", "NB_NUL",
    "NB_EXPRIM", "ID_BVOTE_FULL", "Taux_abstention"
]
colonnes_candidats = [col for col in df_votes.columns if col not in colonnes_non_candidats]
print(f"Colonnes candidats détectées : {colonnes_candidats[:5]} …")

# === Regroupement par familles ===
print("🏅 Regroupement des votes par famille politique...")

FAMILLE_COULEURS = {
    "PS": "hotpink",
    "EELV": "green",
    "LREM Buzyn": "gold",
    "LREM Villani" : "brown",
    "LFI": "purple",
    "LR": "blue",
    "LDVD": "gray",
}

df_familles = pd.DataFrame(index=df_votes.index)
for famille in FAMILLE_COULEURS:
    colonnes_famille = [col for col in colonnes_candidats if f"({famille}" in col]
df_familles[famille] = (
    df_votes[colonnes_famille].sum(axis=1) / df_votes["NB_EXPRIM"].replace(0, pd.NA)
) * 100

# === Score majoritaire par famille ===
famille_cols = list(FAMILLE_COULEURS.keys())  # ['PS', 'EELV', 'LREM Buzyn', ...]
df_familles["Famille_majoritaire"] = df_familles[famille_cols].idxmax(axis=1)
df_familles["Score_majoritaire"] = df_familles[famille_cols].max(axis=1)
df_familles["Couleur"] = df_familles["Famille_majoritaire"].map(FAMILLE_COULEURS)


# === Fusion avec df_votes
df_votes = pd.concat([df_votes, df_familles[["Famille_majoritaire", "Score_majoritaire", "Couleur"]]], axis=1)

# === Fusion géographique ===
print("📌 Fusion des données avec géométries...")
gdf_merge = gdf_geo.merge(df_votes, on="ID_BVOTE_FULL")

# === Carte Folium ===
print("🗺️ Création de la carte...")
m = folium.Map(location=[48.8566, 2.3522], zoom_start=12, tiles="cartodb positron")

folium.GeoJson(
    gdf_merge,
    style_function=lambda feature: {
        "fillColor": feature["properties"]["Couleur"],
        "color": "black",
        "weight": 0.3,
        "fillOpacity": 0.8,
    },
    tooltip=folium.GeoJsonTooltip(
    fields=["ID_BVOTE_y", "Taux_abstention", "Famille_majoritaire", "Score_majoritaire"],
    aliases=["Bureau", "Abstention (%)", "Famille majoritaire", "Score (%)"],
    localize=True
),

).add_to(m)

# === Sauvegarde
output_file = "outputs/carte_municipales_paris_2020.html"
print(f"💾 Sauvegarde dans : {output_file}")
m.save(output_file)
print("✅ Carte enregistrée avec succès.")
