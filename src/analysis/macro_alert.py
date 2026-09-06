import os
import difflib
from pathlib import Path
import pandas as pd
import resend


def generate_macro_impact(delta_score, current_score):
    if delta_score > 0.15:
        stance = "HAWKISH SHIFT (Durcissement du ton)"
        summary = (
            "La Fed durcit sa communication par rapport à la réunion précédente. "
            "Le risque de maintien des taux élevés (Higher for Longer) ou d'un report des baisses augmente."
        )
        impacts = {
            "Taux US (2Y/10Y)": "HAUSSE (Yields UP, pression vendeuse sur les Treasuries)",
            "Bitcoin (BTC)": "BAISSIER (Sensibilité négative au dollar fort et repli de la liquidité)",
            "S&P 500": "PRESSION / VOLATILITÉ (Compression des multiples de valorisation PE)",
            "Gold (Or)": "BAISSIER / CONSOLIDATION (Taux réels plus attractifs)",
            "Pétrole (WTI)": "PLUTÔT BAISSIER (Craintes accrues sur la demande globale)",
        }
    elif delta_score < -0.15:
        stance = "DOVISH PIVOT (Assouplissement du ton)"
        summary = (
            "La Fed adoucit sa communication. Les éléments de langage pointent vers "
            "une confiance accrue dans la désinflation et une ouverture vers des baisses de taux."
        )
        impacts = {
            "Taux US (2Y/10Y)": "BAISSE (Yields DOWN, rally sur les emprunts d'État)",
            "Bitcoin (BTC)": "FORTEMENT HAUSSIER (Catalyseur majeur d'expansion de liquidité)",
            "S&P 500": "HAUSSIER (Détente des conditions financières et taux d'actualisation)",
            "Gold (Or)": "HAUSSIER (Affaiblissement du dollar et repli des rendements réels)",
            "Pétrole (WTI)": "HAUSSIER (Anticipation de reprise de l'activité économique)",
        }
    else:
        stance = "STATUS QUO / NEUTRE (Ton inchangé)"
        summary = (
            "Communication quasiment identique à la réunion précédente. "
            "La Fed réitère sa dépendance stricte aux données macroéconomiques à venir (Data-dependent)."
        )
        impacts = {
            "Taux US (2Y/10Y)": "STABLE (Réaction limitée aux ajustements marginaux)",
            "Bitcoin (BTC)": "NEUTRE (Suit la dynamique technique et les flux de marché)",
            "S&P 500": "ATTENTISTE (Réaction concentrée sur la conférence de presse)",
            "Gold (Or)": "CONSOLIDATION dans les ranges récents",
            "Pétrole (WTI)": "NEUTRE (Dominé par les fondamentaux physiques et OPEP)",
        }

    return stance, summary, impacts


def extract_key_redline_changes(old_text, new_text, max_changes=4):
    old_words = old_text.split()
    new_words = new_text.split()
    matcher = difflib.SequenceMatcher(None, old_words, new_words)

    changes = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "replace":
            removed = " ".join(old_words[i1:i2])
            added = " ".join(new_words[j1:j2])
            if len(removed) > 10 or len(added) > 10:
                changes.append(f"• <b>Remplacé</b> : « <i>{removed}</i> » ➔ « <b>{added}</b> »")
        elif tag == "insert":
            added = " ".join(new_words[j1:j2])
            if len(added) > 10:
                changes.append(f"• <b>Ajouté</b> : « <b>{added}</b> »")
        elif tag == "delete":
            removed = " ".join(old_words[i1:i2])
            if len(removed) > 10:
                changes.append(f"• <b>Supprimé</b> : « <s>{removed}</s> »")

        if len(changes) >= max_changes:
            break

    return changes


def send_resend_alert(subject, html_content, recipient_email, api_key=None):
    """Envoie l'alerte via l'API Resend."""
    api_key = api_key or os.getenv("RESEND_API_KEY")
    if not api_key:
        print("\n--- Aperçu du contenu Email ---")
        print(f"Sujet : {subject}")
        print("Variable RESEND_API_KEY manquante. L'email n'a pas été envoyé.")
        return

    resend.api_key = api_key

    params = {
        "from": "CBST Fed Alert <onboarding@resend.dev>",
        "to": [recipient_email],
        "subject": subject,
        "html": html_content,
    }

    try:
        response = resend.Emails.send(params)
        print(f"Alerte envoyée via Resend avec succès ! ID: {response.get('id')}")
    except Exception as e:
        print(f"Erreur lors de l'envoi Resend : {e}")


def run_alert():
    csv_path = Path("data/processed/fomc_sentiment_scored.csv")
    if not csv_path.exists():
        print("Fichier de données introuvable.")
        return

    df = pd.read_csv(csv_path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(by="date", ascending=False).reset_index(drop=True)

    if len(df) < 2:
        print("Pas assez de réunions pour comparer.")
        return

    latest = df.iloc[0]
    previous = df.iloc[1]

    delta = latest["net_sentiment"] - previous["net_sentiment"]
    stance, summary, impacts = generate_macro_impact(delta, latest["net_sentiment"])
    changes = extract_key_redline_changes(
        str(previous["statement_text"]), str(latest["statement_text"])
    )

    date_str = latest["date"].strftime("%Y-%m-%d")
    prev_date_str = previous["date"].strftime("%Y-%m-%d")

    subject = f"🚨 CBST Flash : FOMC {date_str} [{stance}]"

    impacts_html = "".join([f"<li><b>{asset}</b> : {desc}</li>" for asset, desc in impacts.items()])
    changes_html = "".join([f"<li>{c}</li>" for c in changes]) if changes else "<li>Aucun changement structurel majeur.</li>"

    html_template = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #111; line-height: 1.5; max-width: 650px; margin: auto; padding: 20px;">
        <div style="background-color: #0d1b2a; color: white; padding: 15px; border-radius: 8px;">
            <h2 style="margin: 0;">CBST • Central Bank Sentiment Tracker</h2>
            <p style="margin: 5px 0 0 0; font-size: 14px; opacity: 0.85;">Alerte FOMC en temps réel - Analyse sémantique & Marchés</p>
        </div>

        <div style="margin-top: 20px; padding: 15px; background: #f4f6f8; border-radius: 8px;">
            <p><b>Date FOMC :</b> {date_str} (précédent : {prev_date_str})</p>
            <p><b>Net Sentiment Score :</b> <span style="font-size: 18px; font-weight: bold;">{latest['net_sentiment']:+.4f}</span> (Variation : <b>{delta:+.4f}</b>)</p>
            <p><b>Orientation globale :</b> <span style="color: {'#d90429' if delta > 0.15 else '#008000' if delta < -0.15 else '#2b2d42'}; font-weight: bold;">{stance}</span></p>
        </div>

        <h3>📝 Synthèse Macro</h3>
        <p style="background: #ffffff; padding: 12px; border-left: 4px solid #0077b6;">{summary}</p>

        <h3>🔍 Modifications Clés du Communiqué (Redline Diff)</h3>
        <ul>{changes_html}</ul>

        <h3>⚡ Impact Attendu sur les Marchés</h3>
        <ul>{impacts_html}</ul>

        <div style="margin-top: 30px; font-size: 12px; color: #777; border-top: 1px solid #ddd; padding-top: 10px;">
            Généré automatiquement par le pipeline CBST (FinBERT & Fed Scraper).
        </div>
    </body>
    </html>
    """

    # Mets ici l'email avec lequel tu as créé ton compte Resend
    recipient = "lin.bahic@gmail.com"
    send_resend_alert(subject, html_template, recipient_email=recipient)


if __name__ == "__main__":
    run_alert()