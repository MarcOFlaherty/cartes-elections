import os
import pandas as pd
import geopandas as gpd
import folium
import argparse
import config
import re
from branca.colormap import linear

# =============================================================================
# --- FONCTIONS DE TRAITEMENT DES DONNÉES ---
# =============================================================================

def extract_party_from_candidate(candidate_name):
    """
    Extrait le nom du parti à partir du nom du candidat.
    Exemple: 'Mme MAZETIER Sandrine (LREM Buzyn)' -> 'LREM Buzyn'
    """
    match = re.search(r'\((.*?)\)', candidate_name)
    if match:
        return match.group(1)
    
    # Cas spécifiques sans parenthèses
    if 'Les écologiste' in candidate_name:
        return 'Les écologiste'
    if 'Marcel Campion' in candidate_name:
        return 'Marcel Campion'
        
    return candidate_name

def charger_et_preparer_donnees(excel_path, geojson_path):
    """
    Charge les données, les nettoie, calcule les indicateurs, les fusionne
    et pré-formate certaines colonnes pour les infobulles.
    """
    print(f"📥 Chargement des données depuis {excel_path} et {geojson_path}...")

    df = pd.read_excel(excel_path)
    gdf = gpd.read_file(geojson_path)

    # Harmonisation des colonnes
    df = df.rename(columns=lambda col: col.replace("Porportion_", "Proportion_"))

    # Convertir les colonnes de type datetime ou Timestamp en string pour éviter les erreurs de sérialisation JSON
    for col in df.select_dtypes(include=['datetime64', 'datetime']).columns:
        df[col] = df[col].astype(str)

    # Créer une colonne 'id_bv' dans le DataFrame pour la fusion
    df['id_bv'] = df['NUM_ARROND'].astype(str) + '-' + df['NUM_BUREAU'].astype(str)

    # Calcul du taux d'abstention
    df["Taux_abstention"] = (1 - df["Participation"]) * 100

    # Multiplier les colonnes de proportion par 100
    part_cols = [col for col in df.columns if col.startswith("Proportion_")]
    for col in part_cols:
        df[col] = df[col] * 100
    
    # Extraire le nom du parti et le score
    df["Parti_majoritaire"] = df[part_cols].idxmax(axis=1).str.replace("Proportion_", "")
    df["Parti_majoritaire"] = df["Parti_majoritaire"].apply(extract_party_from_candidate)
    df["Score_majoritaire"] = df[part_cols].max(axis=1)
    df["Couleur"] = df["Parti_majoritaire"].map(config.COULEURS_PARTIS_MAJORITAIRES)

    # Pré-formatage pour les infobulles
    df["Taux_abstention_str"] = df["Taux_abstention"].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A")
    df["Score_majoritaire_str"] = df["Score_majoritaire"].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A")

    gdf_merge = gdf.merge(df, on="id_bv", how="left")
    # S'assurer que gdf_merge est bien un GeoDataFrame avec la colonne 'geometry' définie
    gdf_merge = gdf_merge.set_geometry('geometry')
    print(f"✅ Données fusionnées : {gdf_merge.shape[0]} bureaux de vote.")
    return gdf_merge, part_cols

def preparer_donnees_top3(gdf, part_cols):
    """Prépare les données pour la couche Top 3 en pré-calculant les scores et les couleurs."""
    
    def get_top3_and_color(row):
        scores = [(extract_party_from_candidate(col.replace("Proportion_", "")), row[col]) for col in part_cols if pd.notna(row.get(col))]
        top3_sorted = sorted(scores, key=lambda x: x[1], reverse=True)[:3]
        
        tooltip_html = f"<b>Bureau :</b> {row.get('ID_BVOTE')}<br><hr>"
        for parti, score in top3_sorted:
            tooltip_html += f"{parti} : {score:.1f}%<br>"
            
        gagnant = top3_sorted[0][0] if top3_sorted else None
        couleur = config.COULEURS_PARTIS_TOP3.get(gagnant, "#ffffff")
        
        return pd.Series([tooltip_html, couleur])

    gdf[['tooltip_top3', 'couleur_top3']] = gdf.apply(get_top3_and_color, axis=1)
    return gdf

def get_couleur_abstention(taux):
    """Retourne une couleur en fonction du taux d'abstention."""
    if pd.isna(taux): return "#d9d9d9"
    if taux < 30: return "#fef0d9"
    if taux < 40: return "#fdcc8a"
    if taux < 50: return "#fc8d59"
    if taux < 60: return "#e34a33"
    return "#b30000"

# =============================================================================
# --- FONCTIONS DE CRÉATION DES COUCHES FOLIUM (OPTIMISÉES) ---
# =============================================================================

def creer_couche_abstention(m, gdf):
    """Crée la couche pour le taux d'abstention de manière optimisée."""
    fg = folium.FeatureGroup(name="Taux d’abstention", show=True)
    
    # Filtrer les géométries invalides ou vides
    gdf_filtered = gdf[gdf.geometry.notna()]
    gdf_filtered = gdf_filtered[gdf_filtered.geometry.is_valid & ~gdf_filtered.geometry.is_empty]

    tooltip = folium.features.GeoJsonTooltip(
        fields=["ID_BVOTE", "Taux_abstention_str"],
        aliases=["Bureau :", "Taux d'abstention :"],
        sticky=True
    )

    fg.add_child(folium.GeoJson(
        gdf_filtered,
        style_function=lambda feature: {
            "fillColor": get_couleur_abstention(feature["properties"]["Taux_abstention"]),
            "color": "black", "weight": 0.3, "fillOpacity": 0.7,
        },
        tooltip=tooltip
    ))
    fg.add_to(m)
    return fg

def creer_couche_vote_majoritaire(m, gdf):
    """Crée la couche pour le parti arrivé en tête de manière optimisée."""
    fg = folium.FeatureGroup(name="Parti arrivé en tête", show=False)

    # Filtrer les géométries invalides ou vides
    gdf_filtered = gdf[gdf.geometry.notna()]
    gdf_filtered = gdf_filtered[gdf_filtered.geometry.is_valid & ~gdf_filtered.geometry.is_empty]

    tooltip = folium.features.GeoJsonTooltip(
        fields=["ID_BVOTE", "Parti_majoritaire", "Score_majoritaire_str"],
        aliases=["Bureau :", "Parti en tête :", "Part des votes :"],
        sticky=True
    )

    fg.add_child(folium.GeoJson(
        gdf_filtered,
        style_function=lambda feature: {
            "fillColor": feature["properties"].get("Couleur", "white"),
            "color": "black", "weight": 0.3, "fillOpacity": 0.8,
        },
        tooltip=tooltip
    ))
    fg.add_to(m)
    return fg

def creer_couche_top3_partis(m, gdf):
    """Crée la couche affichant le top 3 des partis de manière optimisée."""
    fg = folium.FeatureGroup(name="Top 3 partis (couleur du 1er)", show=False)

    # Filtrer les géométries invalides ou vides
    gdf_filtered = gdf[gdf.geometry.notna()]
    gdf_filtered = gdf_filtered[gdf_filtered.geometry.is_valid & ~gdf_filtered.geometry.is_empty]

    tooltip = folium.features.GeoJsonTooltip(fields=['tooltip_top3'], aliases=[''], sticky=True)

    fg.add_child(folium.GeoJson(
        gdf_filtered,
        style_function=lambda feature: {
            "fillColor": feature["properties"]["couleur_top3"],
            "color": "black", "weight": 0.2, "fillOpacity": 0.7
        },
        tooltip=tooltip
    ))
    fg.add_to(m)
    return fg

# =============================================================================
# --- FONCTION PRINCIPALE ---
# =============================================================================

def main():
    """Orchestre la création de la carte électorale."""
    parser = argparse.ArgumentParser(description="Génère une carte Folium des résultats des élections municipales 2020 à Paris.")
    parser.add_argument(
        "--excel-file",
        type=str,
        default=config.PATH_EXCEL_2020,
        help=f"Chemin vers le fichier Excel des résultats (défaut: {config.PATH_EXCEL_2020})"
    )
    parser.add_argument(
        "--geojson-file",
        type=str,
        default=config.PATH_GEOJSON_2020,
        help=f"Chemin vers le fichier GeoJSON des bureaux de vote (défaut: {config.PATH_GEOJSON_2020})"
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default=config.OUTPUT_FILE_2020,
        help=f"Chemin vers le fichier HTML de sortie pour la carte (défaut: {config.OUTPUT_FILE_2020})"
    )
    args = parser.parse_args()

    gdf_merge, part_cols = charger_et_preparer_donnees(args.excel_file, args.geojson_file)
    
    gdf_merge = preparer_donnees_top3(gdf_merge, part_cols)

    # Conversion agressive de toutes les colonnes non numériques/booléennes en string, sauf la colonne 'geometry'
    for col in gdf_merge.columns:
        if col != 'geometry' and not pd.api.types.is_numeric_dtype(gdf_merge[col]) and not pd.api.types.is_bool_dtype(gdf_merge[col]):
            gdf_merge[col] = gdf_merge[col].astype(str)

    print(f"Type of gdf_merge: {type(gdf_merge)}")
    print(f"Type of gdf_merge.geometry: {type(gdf_merge.geometry)}")

    print("🗺️ Création de la carte...")
    m = folium.Map(location=[48.8566, 2.3522], zoom_start=12, tiles="cartodb positron")

    creer_couche_abstention(m, gdf_merge)
    creer_couche_vote_majoritaire(m, gdf_merge)
    creer_couche_top3_partis(m, gdf_merge)

    folium.LayerControl(collapsed=False).add_to(m)

    os.makedirs(os.path.dirname(args.output_file), exist_ok=True)
    m.save(args.output_file)
    print(f"✅ Carte sauvegardée ici : {args.output_file}")

if __name__ == "__main__":
    main()
