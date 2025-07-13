import os
import pandas as pd
import geopandas as gpd
import folium

# === Chargement du fond de carte GeoJSON ===
print("📍 Chargement du GeoJSON...")
geojson_path = "data/geojson/bureaux_2020.geojson"
gdf_geo = gpd.read_file(geojson_path)
print(f"✅ GeoJSON chargé : {gdf_geo.shape}")

# Harmonisation
gdf_geo = gdf_geo.rename(columns={"id_bv": "ID_BVOTE", "arrondissement": "NUM_ARROND"})
gdf_geo["ID_BVOTE_FULL"] = gdf_geo["NUM_ARROND"].astype(str) + "-" + gdf_geo["ID_BVOTE"].astype(str)

# === Fusion des fichiers CSV ===
print("🔁 Fusion des CSV arrondissement par arrondissement...")
csv_folder = "data/elections_2020"
df_votes = pd.DataFrame()

for i in range(1, 21):
    file_path = os.path.join(csv_folder, f"Arr_{i}.csv")
    df_i = pd.read_csv(file_path, encoding="utf-8-sig", sep=";")
    df_i["NUM_ARROND"] = i
    df_votes = pd.concat([df_votes, df_i], ignore_index=True)

print(f"✅ Données fusionnées : {df_votes.shape}")

# Nettoyage
df_votes = df_votes[df_votes["ID_BVOTE"].notna()]
df_votes["ID_BVOTE_FULL"] = (
    df_votes["NUM_ARROND"].astype(str) + "-"
    + df_votes["NUM_ARROND"].astype(str) + "-"
    + df_votes["ID_BVOTE"].astype(int).astype(str)
)

# === Taux d’abstention
df_votes["Taux_abstention"] = (df_votes["NB_INSCR"] - df_votes["NB_VOTANT"]) / df_votes["NB_INSCR"] * 100

# === Fusion avec la géométrie
print("📌 Fusion avec le GeoDataFrame...")
gdf_merge = gdf_geo.merge(df_votes, on="ID_BVOTE_FULL", how="left")
print(f"✅ Fusion réussie : {gdf_merge.shape}")

# 🧼 Nettoyage des colonnes dupliquées après fusion
gdf_merge = gdf_merge.rename(columns={
    "ID_BVOTE_x": "ID_BVOTE",
    "Taux_abstention_y": "Taux_abstention"
})

# === Détection des colonnes candidats
colonnes_non_candidats = [
    "ID_BVOTE", "SCRUTIN", "ANNEE", "TOUR", "DATE", "NUM_CIRC", "NUM_QUARTIER", "NUM_ARROND",
    "NUM_BUREAU", "NB_PROCU", "NB_INSCR", "NB_EMARG", "NB_VOTANT", "NB_BLANC", "NB_NUL",
    "NB_EXPRIM", "ID_BVOTE_FULL", "Taux_abstention"
]
colonnes_candidats = [col for col in df_votes.columns if col not in colonnes_non_candidats]
print(f"Colonnes candidats détectées : {colonnes_candidats[:5]} …")

# === Regroupement par famille politique
print("🏅 Regroupement des votes par famille politique...")

FAMILLE_COULEURS = {
    "PS": "hotpink",
    "EELV": "green",
    "LREM Buzyn": "gold",
    "LREM Villani": "brown",
    "LFI": "purple",
    "LR": "blue",
    "LDVD": "gray",
}

df_familles = pd.DataFrame(index=df_votes.index)

for famille in FAMILLE_COULEURS:
    colonnes_famille = [col for col in colonnes_candidats if f"({famille}" in col]
    df_familles[famille] = (
        df_votes[colonnes_famille].apply(pd.to_numeric, errors="coerce").sum(axis=1) /
        pd.to_numeric(df_votes["NB_EXPRIM"], errors="coerce").replace(0, pd.NA)
    ) * 100

df_familles = df_familles.apply(pd.to_numeric, errors="coerce")

# 🏆 Calcul du gagnant et de son score
colonnes_scores = list(FAMILLE_COULEURS.keys())
df_familles["Famille_majoritaire"] = df_familles[colonnes_scores].idxmax(axis=1)
df_familles["Score_majoritaire"] = df_familles[colonnes_scores].max(axis=1)
df_familles["Couleur"] = df_familles["Famille_majoritaire"].map(FAMILLE_COULEURS)

# Fusion des familles dans les données
df_votes = pd.concat([df_votes, df_familles[["Famille_majoritaire", "Score_majoritaire", "Couleur"]]], axis=1)
gdf_merge = gdf_merge.merge(
    df_votes[["ID_BVOTE_FULL", "Famille_majoritaire", "Score_majoritaire", "Taux_abstention", "Couleur"]],
    on="ID_BVOTE_FULL",
    how="left"
)

# === Fonction couleur abstention
def couleur_abstention(taux):
    if taux < 30:
        return "#fef0d9"
    elif taux < 40:
        return "#fdcc8a"
    elif taux < 50:
        return "#fc8d59"
    elif taux < 60:
        return "#e34a33"
    else:
        return "#b30000"

# === Nettoyage des colonnes de fusion (évite KeyError dans la carte)
if "Taux_abstention_y" in gdf_merge.columns:
    gdf_merge["Taux_abstention"] = gdf_merge["Taux_abstention_y"]
elif "Taux_abstention_x" in gdf_merge.columns:
    gdf_merge["Taux_abstention"] = gdf_merge["Taux_abstention_x"]



# === Création carte
print("🗺️ Création de la carte...")
m = folium.Map(location=[48.8566, 2.3522], zoom_start=12, tiles="cartodb positron")

# Couche 1 – Vote majoritaire
fg_vote = folium.FeatureGroup(name="Vote majoritaire")
folium.GeoJson(
    gdf_merge,
    style_function=lambda feature: {
        "fillColor": feature["properties"]["Couleur"],
        "color": "black",
        "weight": 0.3,
        "fillOpacity": 0.8,
    },
    tooltip=folium.GeoJsonTooltip(
        fields=["ID_BVOTE", "Famille_majoritaire", "Score_majoritaire"],
        aliases=["Bureau", "Famille majoritaire", "Score (%)"],
        localize=True,
    ),
).add_to(fg_vote)

# Couche 2 – Taux d'abstention
fg_abstention = folium.FeatureGroup(name="Abstention")
folium.GeoJson(
    gdf_merge,
    style_function=lambda feature: {
        "fillColor": couleur_abstention(feature["properties"]["Taux_abstention"]),
        "color": "black",
        "weight": 0.3,
        "fillOpacity": 0.7,
    },
    tooltip=folium.GeoJsonTooltip(
        fields=["ID_BVOTE", "Taux_abstention"],
        aliases=["Bureau", "Abstention (%)"],
        localize=True,
    ),
).add_to(fg_abstention)

# Ajout des couches à la carte
fg_vote.add_to(m)
fg_abstention.add_to(m)
folium.LayerControl(collapsed=False).add_to(m)

# === Sauvegarde
output_file = "outputs/carte_municipales_paris_2020.html"
print(f"💾 Sauvegarde dans : {output_file}")
m.save(output_file)
print("✅ Carte enregistrée avec succès.")
