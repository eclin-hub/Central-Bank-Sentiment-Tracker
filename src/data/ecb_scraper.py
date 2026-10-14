from datetime import datetime
from pathlib import Path
import re
from bs4 import BeautifulSoup
import pandas as pd
import requests

BASE_URL = "https://www.ecb.europa.eu"
ARCHIVE_URL = "https://www.ecb.europa.eu/press/govcdec/mopo/html/index.en.html"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}


def clean_statement_text(raw_html):
    soup = BeautifulSoup(raw_html, "html.parser")
    main_section = soup.find("main") or soup.find("div", class_="section") or soup.find("article")
    target = main_section if main_section else soup

    paragraphs = target.find_all("p")
    text_list = []
    for p in paragraphs:
        t = p.get_text(" ", strip=True)
        if len(t) > 50 and not t.startswith("Reproduction is permitted") and not t.startswith("ECB"):
            text_list.append(t)

    full_text = " ".join(text_list)
    full_text = re.sub(r"\s+", " ", full_text).strip()
    return full_text


def fetch_ecb_statements(limit=16):
    print("Scraping de l'archive officielle des décisions BCE...")
    response = requests.get(ARCHIVE_URL, headers=HEADERS, timeout=20)
    if response.status_code != 200:
        print(f"Erreur d'accès à l'archive BCE : HTTP {response.status_code}")
        return []

    soup = BeautifulSoup(response.content, "html.parser")
    
    # Repérer tous les liens vers les décisions de politique monétaire
    statement_links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        title = a.get_text(strip=True)
        # Filtre sur les communiqués officiels de décision de taux
        if "/press/pr/date/" in href and "monetary policy decisions" in title.lower():
            if not href.startswith("http"):
                full_link = BASE_URL + href
            else:
                full_link = href
            
            # Extraction de la date dans l'URL ou dans la balise parente
            # Format typique d'URL : /press/pr/date/2024/html/ecb.mp240411~...
            match_date = re.search(r"ecb\.mp(\d{2})(\d{2})(\d{2})", href)
            if match_date:
                yy, mm, dd = match_date.groups()
                date_str = f"20{yy}-{mm}-{dd}"
            else:
                date_str = None

            statement_links.append((date_str, title, full_link))

    # Déduplication
    seen = set()
    unique_links = []
    for d, t, l in statement_links:
        if l not in seen:
            seen.add(l)
            unique_links.append((d, t, l))

    print(f"Liens identifiés dans l'archive : {len(unique_links)}")

    records = []
    for date_str, title, link in unique_links[:limit]:
        try:
            r = requests.get(link, headers=HEADERS, timeout=15)
            if r.status_code == 200:
                body_text = clean_statement_text(r.text)
                if len(body_text) > 200:
                    # Fallback date si non trouvée dans l'URL
                    if not date_str:
                        soup_page = BeautifulSoup(r.text, "html.parser")
                        date_tag = soup_page.find("div", class_="ecb-publicationDate") or soup_page.find("p", class_="date")
                        date_str = date_tag.get_text(strip=True) if date_tag else datetime.today().strftime("%Y-%m-%d")

                    print(f"Extraction réussie : {date_str} - {title[:40]}...")
                    records.append(
                        {
                            "date": date_str,
                            "bank": "ECB",
                            "title": title,
                            "statement_text": body_text,
                            "url": link,
                        }
                    )
        except Exception as e:
            print(f"Erreur sur {link}: {e}")

    return records


def run_scraper():
    records = fetch_ecb_statements(limit=16)
    if not records:
        print("Aucun document n'a pu être extrait de l'archive.")
        return

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(by="date", ascending=True).drop_duplicates(subset=["date"]).reset_index(drop=True)

    out_path = Path("data/raw/ecb_statements.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"\nSuccès total : {len(df)} communiqués BCE enregistrés dans {out_path}")


if __name__ == "__main__":
    run_scraper()