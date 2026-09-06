import re
from pathlib import Path
from urllib.parse import urljoin
import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.federalreserve.gov"
CALENDAR_URL = f"{BASE_URL}/monetarypolicy/fomccalendars.htm"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def fetch_statement_links():
    """Extrait uniquement les liens des FOMC Statements (communiqués officiels)."""
    res = requests.get(CALENDAR_URL, headers=HEADERS)
    res.raise_for_status()
    soup = BeautifulSoup(res.content, "html.parser")

    records = []

    # Les statements FOMC suivent le format strict: monetaryYYYYMMDDa.htm
    pattern = re.compile(r"monetary(\d{8})a\.htm", re.IGNORECASE)

    for a in soup.find_all("a", href=True):
        href = a["href"]
        match = pattern.search(href)
        if match:
            date_str = match.group(1)
            full_url = urljoin(BASE_URL, href)
            records.append({"date": date_str, "url": full_url})

    if not records:
        raise ValueError("Aucun statement au format monetaryYYYYMMDDa.htm trouvé.")

    df = pd.DataFrame(records).drop_duplicates(subset=["url"])
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
    df = df.sort_values(by="date", ascending=False).reset_index(drop=True)
    return df


def parse_statement_text(url):
    """Extrait et nettoie les paragraphes du communiqué."""
    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200:
        return ""

    soup = BeautifulSoup(res.content, "html.parser")
    article = (
        soup.find("div", id="article")
        or soup.find("div", class_="col-xs-12")
        or soup.find("main")
    )

    if not article:
        return ""

    paragraphs = article.find_all("p")
    text_content = []

    for p in paragraphs:
        txt = p.get_text(strip=True)
        if not txt:
            continue
        # Arrêt avant les métadonnées de bas de page
        if "Voting for the monetary policy action" in txt:
            text_content.append(txt)
            break
        if "For media inquiries" in txt or "Last Update:" in txt:
            break
        text_content.append(txt)

    return "\n\n".join(text_content)


def main():
    print("Scraping des déclarations officielles du FOMC...")
    df_links = fetch_statement_links()
    print(f"{len(df_links)} FOMC Statements uniques détectés.")

    # On extrait les 15 déclarations les plus récentes
    sample_size = min(15, len(df_links))
    print(f"Extraction des {sample_size} derniers communiqués...")

    texts = []
    for idx, row in df_links.head(sample_size).iterrows():
        date_fmt = row["date"].strftime("%Y-%m-%d")
        print(f"-> Extraction : {date_fmt}")
        body = parse_statement_text(row["url"])
        texts.append(body)

    df_sample = df_links.head(sample_size).copy()
    df_sample["statement_text"] = texts

    out_dir = Path("data/raw")
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "fomc_statements.csv"
    df_sample.to_csv(csv_path, index=False, encoding="utf-8")
    print(f"\nFichier prêt : {csv_path}")


if __name__ == "__main__":
    main()