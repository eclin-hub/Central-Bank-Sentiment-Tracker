import requests
from bs4 import BeautifulSoup

# URL d'un communiqué officiel récent du FOMC
url = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    soup = BeautifulSoup(response.content, "html.parser")
    # Trouver le titre principal de la page
    title = soup.find("h3") or soup.find("h2")
    print("Connexion réussie au site de la Fed !")
    if title:
        print("Titre repéré :", title.get_text(strip=True))
else:
    print(f"Erreur de connexion : code {response.status_code}")