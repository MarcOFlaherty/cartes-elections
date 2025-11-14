import os
import pandas as pd
import glob

def get_party_from_candidate_name(candidate_name, party_mapping):
    """
    Trouve le parti d'un candidat à partir de son nom.
    """
    # Chercher une correspondance exacte dans le mapping
    if candidate_name in party_mapping:
        return party_mapping[candidate_name]
    
    # Essayer de trouver une correspondance partielle
    for name, party in party_mapping.items():
        if name in candidate_name:
            return party
            
    # Essayer d'inférer le parti du nom
    if "EELV" in candidate_name: return "EELV"
    if "LREM" in candidate_name: return "LREM"
    if "LR" in candidate_name: return "LR"
    if "PS" in candidate_name: return "PS"
    if "LFI" in candidate_name: return "LFI"
    
    return "Sans étiquette"

def process_second_tour_data():
    """
    Traite les données du second tour des élections municipales de 2020 à Paris.
    """
    # --- 1. Charger le mapping des partis ---
    party_mapping_df = pd.read_csv("data/elections_2020/party_mapping.csv")
    party_mapping = dict(zip(party_mapping_df['Candidat'], party_mapping_df['Parti']))

    # --- 2. Obtenir la liste des fichiers ---
    files = glob.glob("data/elections_2020/second_tour/*.xls")
    
    # --- 3. Traiter chaque fichier ---
    all_dfs = []
    for file in files:
        df = pd.read_excel(file, header=0)
        
        # Extraire le numéro de l'arrondissement du nom du fichier
        arrondissement = file.split("Ardt_")[1].split("_")[0]
        df["NUM_ARROND"] = int(arrondissement)
        
        # Extraire le numéro du bureau de vote
        df["NUM_BUREAU"] = df["ID_BVOTE"].apply(lambda x: int(x.split("-")[1]) if isinstance(x, str) else x)

        # Traiter les colonnes des candidats
        candidate_cols = [col for col in df.columns if col.startswith('M.') or col.startswith('Mme')]
        party_votes = {}
        for col in candidate_cols:
            candidate_name = col
            party = get_party_from_candidate_name(candidate_name, party_mapping)
            if party not in party_votes:
                party_votes[party] = df[col]
            else:
                party_votes[party] += df[col]
        
        for party, votes in party_votes.items():
            df[f"Proportion_{party}"] = votes / df["NB_EXPRIM"]
            
        all_dfs.append(df)
        
    # --- 4. Consolider les données ---
    consolidated_df = pd.concat(all_dfs, ignore_index=True)
    
    # --- 5. Sauvegarder le fichier consolidé ---
    consolidated_df.to_excel("data/elections_2020/Tous_arr_2nd_tour_final.xlsx", index=False)
    print("✅ Fichier consolidé 'Tous_arr_2nd_tour_final.xlsx' créé avec succès.")

if __name__ == "__main__":
    process_second_tour_data()
