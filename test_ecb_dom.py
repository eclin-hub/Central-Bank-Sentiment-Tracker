import re
import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

base_url = "https://www.ecb.europa.eu"
all_statements = []

for year in [2026, 2025, 2024]:
    url = f"https://www.ecb.europa.eu/press/press_conference/monetary-policy-statement/{year}/html/index.en.html"
    r = requests.get(url, headers=headers, timeout=15)
    print(f"Année {year} : Status {r.status_code}")
    if r.status_code == 200:
        soup = BeautifulSoup(r.content, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "ecb.is" in href or "ecb.mp" in href:
                full_link = href if href.startswith("http") else base_url + href
                title = a.get_text(strip=True)
                all_statements.append((year, title, full_link))

print(f"\nTotal déclarations identifiées : {len(all_statements)}")
for yr, t, l in all_statements[:8]:
    print(f"[{yr}] {t} -> {l}")