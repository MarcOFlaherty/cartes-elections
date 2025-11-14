import requests
from bs4 import BeautifulSoup
import pandas as pd

def scrape_party_affiliations():
    """
    Scrape les affiliations des partis pour les candidats aux élections municipales de 2020 à Paris.
    """
    base_url = "https://www.archives-resultats-elections.interieur.gouv.fr/resultats/municipales-2020/075/"
    party_mapping = {}

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    # Itérer à travers les circonscriptions de Paris (de 051 à 070)
    for i in range(51, 71):
        url = f"{base_url}C1075{i:03d}.php"
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Trouver la table des résultats
            results_table = soup.find("table", {"class": "table-bordered"})
            if results_table:
                rows = results_table.find_all("tr")
                for row in rows:
                    cols = row.find_all("td")
                    if len(cols) > 1:
                        candidate_name = cols[0].text.strip()
                        party = cols[1].text.strip()
                        party_mapping[candidate_name] = party
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la requête pour {url}: {e}")

    return party_mapping

if __name__ == "__main__":
    party_mapping = scrape_party_affiliations()
    
    # Sauvegarder le mapping dans un fichier CSV pour une utilisation ultérieure
    df = pd.DataFrame(list(party_mapping.items()), columns=['Candidat', 'Parti'])
    df.to_csv('data/elections_2020/party_mapping.csv', index=False)
    
    print("✅ Mapping des partis créé avec succès : data/elections_2020/party_mapping.csv")
