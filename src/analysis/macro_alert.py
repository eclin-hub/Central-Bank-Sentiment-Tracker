import difflib
import os
from pathlib import Path
import pandas as pd
import resend

DASHBOARD_URL = "https://central-bank-sentiment-tracker.streamlit.app"


def generate_macro_impact(delta_score, current_score):
    if delta_score > 0.15:
        stance = "HAWKISH SHIFT (Durcissement du ton)"
        summary = (
            "La Fed durcit sa communication par rapport a la reunion precedente. "
            "Le risque de maintien des taux eleves (Higher for Longer) ou d'un report des baisses augmente."
        )
        impacts = {
            "Taux US (2Y/10Y)": "HAUSSE (Yields UP, pression vendeuse sur les Treasuries)",
            "Bitcoin (BTC)": "BAISSIER (Sensibilite negative au dollar fort et repli de la liquidite)",
            "S&P 500": "PRESSION / VOLATILITE (Compression des multiples de valorisation PE)",
            "Gold (Or)": "BAISSIER / CONSOLIDATION (Taux reels plus attractifs)",
            "Petrole (WTI)": "PLUTOT BAISSIER (Craintes accrues sur la demande globale)",
        }
    elif delta_score < -0.15:
        stance = "DOVISH PIVOT (Assouplissement du ton)"
        summary = (
            "La Fed adoucit sa communication. Les elements de langage pointent vers "
            "une confiance accrue dans la desinflation et une ouverture vers des baisses de taux."
        )
        impacts = {
            "Taux US (2Y/10Y)": "BAISSE (Yields DOWN, rally sur les emprunts d'Etat)",
            "Bitcoin (BTC)": "FORTEMENT HAUSSIER (Catalyseur majeur d'expansion de liquidite)",
            "S&P 500": "HAUSSIER (Detente des conditions financieres et taux d'actualisation)",
            "Gold (Or)": "HAUSSIER (Affaiblissement du dollar et repli des rendements reels)",
            "Petrole (WTI)": "HAUSSIER (Anticipation de reprise de l'activite economique)",
        }
    else:
        stance = "STATUS QUO / NEUTRE (Ton inchange)"
        summary = (
            "Communication quasiment identique a la reunion precedente. "
            "La Fed reitere sa dependance stricte aux donnees macroeconomiques a venir (Data-dependent)."
        )
        impacts = {
            "Taux US (2Y/10Y)": "STABLE (Reaction limitee aux ajustements marginaux)",
            "Bitcoin (BTC)": "NEUTRE (Suit la dynamique technique et les flux de marche)",
            "S&P 500": "ATTENTISTE (Reaction concentree sur la conference de presse)",
            "Gold (Or)": "CONSOLIDATION dans les ranges recents",
            "Petrole (WTI)": "NEUTRE (Domine par les fondamentaux physiques et OPEP)",
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
                changes.append(f"• <b>Remplace</b> : « <i>{removed}</i> » ➔ « <b>{added}</b> »")
        elif tag == "insert":
            added = " ".join(new_words[j1:j2])
            if len(added) > 10:
                changes.append(f"• <b>Ajoute</b> : « <b>{added}</b> »")
        elif tag == "delete":
            removed = " ".join(old_words[i1:i2])
            if len(removed) > 10:
                changes.append(f"• <b>Supprime</b> : « <s>{removed}</s> »")

        if len(changes) >= max_changes:
            break

    return changes


def send_resend_alert(subject, html_content, recipient_email, api_key=None):
    api_key = api_key or os.getenv("RESEND_API_KEY")
    if not api_key:
        print("Variable RESEND_API_KEY manquante.")
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
        print(f"Alerte envoyee via Resend avec succes ! ID: {response.get('id')}")
    except Exception as e:
        print(f"Erreur lors de l'envoi Resend : {e}")


def run_alert(force=False):
    csv_path = Path("data/processed/fomc_sentiment_scored.csv")
    if not csv_path.exists():
        print("Fichier de donnees introuvable.")
        return

    df = pd.read_csv(csv_path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(by="date", ascending=False).reset_index(drop=True)

    if len(df) < 2:
        print("Pas assez de reunions enregistrees pour effectuer une comparaison.")
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

    subject = f"🚨 CBST Flash [V2] : FOMC {date_str} [{stance}]"

    impacts_html = "".join([f"<li style='margin-bottom: 6px;'><b>{asset}</b> : {desc}</li>" for asset, desc in impacts.items()])
    changes_html = "".join([f"<li style='margin-bottom: 6px;'>{c}</li>" for c in changes]) if changes else "<li>Aucun changement structurel majeur.</li>"

    html_template = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #111; line-height: 1.6; max-width: 650px; margin: auto; padding: 20px;">
        <div style="background-color: #0d1b2a; color: white; padding: 20px; border-radius: 8px; text-align: center;">
            <h2 style="margin: 0; font-size: 22px; letter-spacing: 0.5px;">CBST • Central Bank Sentiment Tracker</h2>
            <p style="margin: 6px 0 0 0; font-size: 13px; opacity: 0.85;">Alerte FOMC en direct - NLP FinBERT &amp; Grille Macro</p>
        </div>

        <div style="margin-top: 20px; padding: 16px; background: #f8f9fa; border-radius: 8px; border: 1px solid #e9ecef;">
            <p style="margin: 0 0 8px 0;"><b>Date FOMC :</b> {date_str} (precedent : {prev_date_str})</p>
            <p style="margin: 0 0 8px 0;"><b>Net Sentiment Score :</b> <span style="font-size: 18px; font-weight: bold; color: #0d1b2a;">{latest['net_sentiment']:+.4f}</span> (Variation : <b>{delta:+.4f}</b>)</p>
            <p style="margin: 0;"><b>Orientation globale :</b> <span style="color: {'#d90429' if delta > 0.15 else '#2b9348' if delta < -0.15 else '#495057'}; font-weight: bold;">{stance}</span></p>
        </div>

        <h3 style="color: #0d1b2a; border-bottom: 2px solid #e9ecef; padding-bottom: 6px; margin-top: 24px;">📝 Synthese Macro</h3>
        <p style="background: #ffffff; padding: 14px; border-left: 4px solid #0077b6; margin: 0; background-color: #f1f7fa; border-radius: 0 6px 6px 0;">{summary}</p>

        <h3 style="color: #0d1b2a; border-bottom: 2px solid #e9ecef; padding-bottom: 6px; margin-top: 24px;">🔍 Modifications Cles du Communique (Redline Diff)</h3>
        <ul style="padding-left: 20px;">{changes_html}</ul>

        <h3 style="color: #0d1b2a; border-bottom: 2px solid #e9ecef; padding-bottom: 6px; margin-top: 24px;">⚡ Impact Attendu sur les Marches</h3>
        <ul style="padding-left: 20px;">{impacts_html}</ul>

        <hr style="border: 0; border-top: 1px solid #ddd; margin: 30px 0 20px 0;">

        <div style="text-align: center; margin: 25px 0;">
            <p style="font-size: 15px; margin-bottom: 10px; font-weight: bold;">Acceder au dashboard interactif complet :</p>
            <a href="{DASHBOARD_URL}" target="_blank" style="color: #0066cc; text-decoration: underline; font-size: 16px; font-weight: bold;">
                {DASHBOARD_URL}
            </a>
        </div>

        <div style="margin-top: 30px; font-size: 11px; color: #888; border-top: 1px solid #eee; padding-top: 12px; text-align: center;">
            Pipeline CBST automatise • Donnees issues des publications officielles de la Reserve federale.
        </div>
    </body>
    </html>
    """

    recipient = "lin.bahic@gmail.com"
    send_resend_alert(subject, html_template, recipient_email=recipient)


if __name__ == "__main__":
    run_alert()
