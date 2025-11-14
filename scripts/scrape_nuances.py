import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

def scrape_nuances():
    """
    Scrape les nuances (partis) des candidats pour les élections municipales de 2020 à Paris.
    """
    base_url = "https://www.archives-resultats-elections.interieur.gouv.fr/resultats/municipales-2020/075/"
    party_mapping = {}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    # Itérer à travers les circonscriptions de Paris (de 051 à 070)
    for i in range(51, 71):
        constituency_url = f"{base_url}C1075{i:03d}.php"
        try:
            response = requests.get(constituency_url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Trouver les liens vers les listes de candidats
            links = soup.find_all('a', href=re.compile(r'C1075\d{3}SR\d{2}\.php'))
            for link in links:
                list_url = f"{base_url}{link['href']}"
                try:
                    list_response = requests.get(list_url, headers=headers)
                    list_response.raise_for_status()
                    list_soup = BeautifulSoup(list_response.content, 'html.parser')
                    
                    # Trouver la table des candidats
                    candidate_table = list_soup.find("table", {"class": "table-bordered"})
                    if candidate_table:
                        rows = candidate_table.find_all("tr")
                        for row in rows:
                            cols = row.find_all("td")
                            if len(cols) > 1:
                                candidate_name = cols[1].text.strip()
                                nuance = cols[0].text.strip()
                                party_mapping[candidate_name] = nuance
                except requests.exceptions.RequestException as e:
                    print(f"Erreur lors de la requête pour {list_url}: {e}")

        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la requête pour {constituency_url}: {e}")

    return party_mapping

if __name__ == "__main__":
    party_mapping = scrape_nuances()
    
    # Sauvegarder le mapping dans un fichier CSV
    df = pd.DataFrame(list(party_mapping.items()), columns=['Candidat', 'Nuance'])
    df.to_csv('data/elections_2020/party_mapping_nuance.csv', index=False)
    
    print("✅ Mapping des nuances créé avec succès : data/elections_2020/party_mapping_nuance.csv")
