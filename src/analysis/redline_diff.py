import difflib
from pathlib import Path
import pandas as pd


def load_statements():
    csv_path = Path("data/processed/fomc_sentiment_scored.csv")
    if not csv_path.exists():
        raise FileNotFoundError(f"{csv_path} introuvable.")

    df = pd.read_csv(csv_path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(by="date", ascending=False).reset_index(drop=True)
    return df


def generate_html_diff(old_text, new_text, old_date, new_date, output_path):
    """Génère un fichier HTML visuel comparant deux déclarations consécutives."""
    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()

    differ = difflib.HtmlDiff(wrapcolumn=80)
    html_content = differ.make_file(
        old_lines,
        new_lines,
        fromdesc=f"FOMC Statement: {old_date}",
        todesc=f"FOMC Statement: {new_date}",
        context=True,
        numlines=2,
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Diff HTML sauvegardé : {output_path}")


def display_terminal_diff(old_text, new_text, old_date, new_date):
    """Affiche un résumé console des phrases modifiées, ajoutées ou retirées."""
    print(f"\n{'='*70}")
    print(f"REDLINE DIFF : {old_date} -> {new_date}")
    print(f"{'='*70}\n")

    old_words = old_text.split()
    new_words = new_text.split()

    matcher = difflib.SequenceMatcher(None, old_words, new_words)

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "replace":
            removed = " ".join(old_words[i1:i2])
            added = " ".join(new_words[j1:j2])
            print(f"[-] SUPPRIMÉ : {removed}")
            print(f"[+] REMPLACÉ PAR : {added}\n")
        elif tag == "delete":
            removed = " ".join(old_words[i1:i2])
            print(f"[-] SUPPRIMÉ : {removed}\n")
        elif tag == "insert":
            added = " ".join(new_words[j1:j2])
            print(f"[+] AJOUTÉ : {added}\n")


def main():
    df = load_statements()
    if len(df) < 2:
        print("Il faut au moins deux communiqués pour effectuer une comparaison.")
        return

    # Par défaut : comparaison entre la réunion la plus récente et la précédente
    latest_stmt = df.iloc[0]
    previous_stmt = df.iloc[1]

    date_new = latest_stmt["date"].strftime("%Y-%m-%d")
    date_old = previous_stmt["date"].strftime("%Y-%m-%d")

    display_terminal_diff(
        str(previous_stmt["statement_text"]),
        str(latest_stmt["statement_text"]),
        date_old,
        date_new,
    )

    out_dir = Path("notebooks")
    out_dir.mkdir(parents=True, exist_ok=True)
    html_file = out_dir / f"diff_{date_old}_vs_{date_new}.html"

    generate_html_diff(
        str(previous_stmt["statement_text"]),
        str(latest_stmt["statement_text"]),
        date_old,
        date_new,
        html_file,
    )


if __name__ == "__main__":
    main()