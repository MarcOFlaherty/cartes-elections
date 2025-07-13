import pandas as pd
import geopandas as gpd
import folium
import os

import pandas as pd
import geopandas as gpd

# Chargement du fichier Excel
df = pd.read_excel("data/elections_2020/Tous_arr.xlsx")
print("Colonnes du fichier Excel :")
print(df.columns.tolist())

# Chargement du fichier GeoJSON
gdf = gpd.read_file("data/geojson/bureaux_2020.geojson")
print("\nColonnes du fichier GeoJSON :")
print(gdf.columns.tolist())



# === Chargement des données ===
print("📥 Chargement des données...")
df = pd.read_excel("data/elections_2020/Tous_arr.xlsx")
geojson_path = "data/geojson/bureaux_2020.geojson"
gdf = gpd.read_file(geojson_path)

# Harmonisation des colonnes
df = df.rename(columns=lambda col: col.replace("Porportion_", "Proportion_"))

# Création des colonnes nécessaires
df["Taux_abstention"] = 1 - df["Participation"]
df["Taux_abstention"] = df["Taux_abstention"] * 100


# Passage en proportion
for col in df.columns:
    if col.startswith("Proportion_"):
        df[col] = df[col] * 100


# Fusion
gdf_merge = gdf.merge(df, left_on="id_bv", right_on="ID_BVOTE", how="left")


print(f"✅ Fusion réussie : {gdf_merge.shape}")

# === Fonction couleur abstention ===
def couleur_abstention(taux):
    if pd.isna(taux): return "#d9d9d9"
    elif taux < 30: return "#fef0d9"
    elif taux < 40: return "#fdcc8a"
    elif taux < 50: return "#fc8d59"
    elif taux < 60: return "#e34a33"
    else: return "#b30000"

# === Détection du parti majoritaire
FAMILLE_COULEURS = {
    "(PS)": "hotpink",
    "(EELV)": "green",
    "(LREM Buzyn)": "gold",
    "(LREM Villani)": "orange",
    "(LR)": "blue",
    "LFI": "purple"
}

# Trouver le parti avec la plus forte proportion
part_cols = [col for col in df.columns if col.startswith("Proportion_")]
df["Parti_majoritaire"] = df[part_cols].idxmax(axis=1).str.replace("Proportion_", "")
df["Score_majoritaire"] = df[part_cols].max(axis=1)
df["Couleur"] = df["Parti_majoritaire"].map(FAMILLE_COULEURS)

# Mettre à jour gdf_merge
gdf_merge = gdf.merge(df, left_on="id_bv", right_on="ID_BVOTE", how="left")


# === Création de la carte ===
print("🗺️ Création de la carte...")
m = folium.Map(location=[48.8566, 2.3522], zoom_start=12, tiles="cartodb positron")

# === Couche 1 : Abstention ===
fg_abstention = folium.FeatureGroup(name="Taux d’abstention")
for _, row in gdf_merge.iterrows():
    tooltip = f"Bureau : {row.get('ID_BVOTE')}<br>Taux d'abstention : {row.get('Taux_abstention', 0):.1f}%"
    folium.GeoJson(
        row.geometry,
        style_function=lambda x, taux=row.get("Taux_abstention", 0): {
            "fillColor": couleur_abstention(taux),
            "color": "black",
            "weight": 0.3,
            "fillOpacity": 0.7,
        },
        tooltip=tooltip,
    ).add_to(fg_abstention)

# === Couche 2 : Vote majoritaire
fg_vote = folium.FeatureGroup(name="Parti arrivé en tête")
for _, row in gdf_merge.iterrows():
    tooltip = (
        f"<b>Bureau :</b> {row.get('ID_BVOTE')}<br>"
        f"<b>Parti en tête :</b> {row.get('Parti_majoritaire')}<br>"
        f"<b>Part des votes :</b> {row.get('Score_majoritaire', 0):.1f}%"
    )

    folium.GeoJson(
        row.geometry,
        style_function=lambda x, color=row["Couleur"]: {
            "fillColor": color if pd.notna(color) else "white",
            "color": "black",
            "weight": 0.3,
            "fillOpacity": 0.8,
        },
        tooltip=tooltip,
    ).add_to(fg_vote)


# === Couche 3 : (Top 3 partis arrivés en tête) ===
fg_top3 = folium.FeatureGroup(name="Top 3 partis arrivés en tête")
part_cols = [col for col in df.columns if col.startswith("Proportion_")]

# Dictionnaire de couleurs par famille politique
COULEURS = {
    "PS": "hotpink",
    "EELV": "green",
    "LREM Buzyn": "gold",
    "LREM Villani": "brown",
    "LFI": "purple",
    "LR": "blue",
    "LDVD": "gray"
}

for _, row in gdf_merge.iterrows():
    # Récupération des scores
    scores = [(col.replace("Proportion_", ""), row[col]) for col in part_cols if not pd.isna(row[col])]
    top3 = sorted(scores, key=lambda x: x[1], reverse=True)[:3]

    # Tooltip détaillé avec top 3
    tooltip = f"<b>Bureau :</b> {row.get('ID_BVOTE')}<br><hr>"
    for parti, score in top3:
        tooltip += f"{parti} : {score:.1f}%<br>"

    # On récupère la famille gagnante depuis les colonnes calculées
    gagnant = top3[0][0] if top3 else None
    couleur = COULEURS.get(gagnant, "#ffffff")

    # Style de couleur figé
    style = {
        "fillColor": couleur,
        "color": "black",
        "weight": 0.1,
        "fillOpacity": 0.1,
    }

    folium.GeoJson(
        row.geometry,
        style_function=lambda x, style=style: style,
        tooltip=tooltip,
    ).add_to(fg_top3)


# Ajout des couches
fg_abstention.add_to(m)
fg_vote.add_to(m)
fg_top3.add_to(m)
folium.LayerControl(collapsed=False).add_to(m)

# === Sauvegarde ===
output_file = "outputs/1er_tour_municipales_2020.html"
os.makedirs("outputs", exist_ok=True)
m.save(output_file)
print(f"✅ Carte sauvegardée ici : {output_file}")
