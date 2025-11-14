import pandas as pd

def create_party_mapping():
    """
    Crée un mapping des candidats et de leurs partis à partir des données du premier tour.
    """
    df = pd.read_excel("data/elections_2020/Tous_arr.xlsx")
    
    party_mapping = {}
    
    # Extraire les noms des candidats des colonnes "Proportion_"
    candidate_cols = [col for col in df.columns if col.startswith("Proportion_")]
    for col in candidate_cols:
        candidate_name = col.replace("Proportion_", "")
        # Extraire le parti du nom du candidat (supposant un format comme "NOM Prénom (Parti)")
        if "(" in candidate_name and ")" in candidate_name:
            party = candidate_name.split("(")[1].split(")")[0]
            party_mapping[candidate_name] = party
            
    return party_mapping

if __name__ == "__main__":
    party_mapping = create_party_mapping()
    
    # Sauvegarder le mapping dans un fichier CSV
    df = pd.DataFrame(list(party_mapping.items()), columns=['Candidat', 'Parti'])
    df.to_csv('data/elections_2020/party_mapping.csv', index=False)
    
    print("✅ Mapping des partis créé avec succès : data/elections_2020/party_mapping.csv")
