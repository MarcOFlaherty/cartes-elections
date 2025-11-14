"""
Fichier de configuration pour les scripts d'analyse électorale.

Ce fichier centralise les chemins de fichiers, les couleurs, 
et autres paramètres constants utilisés par les différents scripts.
"""

# --- Chemins de fichiers (Élections 2020) ---
PATH_EXCEL_2020 = "data/elections_2020/Tous_arr.xlsx"
PATH_GEOJSON_2020 = "data/geojson/bureaux_2020.geojson"
OUTPUT_FILE_2020 = "docs/outputs/1er_tour_municipales_2020.html"

# --- Couleurs et styles ---
# Utilisé pour la couche "Parti arrivé en tête"
COULEURS_PARTIS_MAJORITAIRES = {
    "PS": "hotpink",
    "EELV": "green",
    "LREM Buzyn": "gold",
    "LREM Villani": "orange",
    "LR": "blue",
    "LFI": "purple",
    "RN": "navy",
    "DVD": "lightblue",
    "DVG": "pink",
    "UDI": "skyblue",
    "LO": "darkred",
    "UPR": "blue",
    "DIV": "grey",
    "SE": "grey",
    "EXG": "darkred",
    "LREM": "gold",
    "Les écologiste": "green",
    "Marcel Campion": "grey",
}

# Utilisé pour la couche "Top 3 partis"
COULEURS_PARTIS_TOP3 = {
    "PS": "hotpink",
    "EELV": "green",
    "LREM Buzyn": "gold",
    "LREM Villani": "brown",
    "LFI": "purple",
    "LR": "blue",
    "LDVD": "gray",
    "RN": "navy",
    "DVD": "lightblue",
    "DVG": "pink",
    "UDI": "skyblue",
    "LO": "darkred",
    "UPR": "blue",
    "DIV": "grey",
    "SE": "grey",
    "EXG": "darkred",
    "LREM": "gold",
    "Les écologiste": "green",
    "Marcel Campion": "grey",
}
