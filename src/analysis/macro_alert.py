import difflib
import os
from pathlib import Path
import pandas as pd
import resend

DASHBOARD_URL = "https://cbst07.streamlit.app"


def generate_macro_impact(delta_score, current_score):
    if delta_score > 0.15:
        stance_label = "HAWKISH SHIFT"
        stance_sub = "Durcissement des conditions monétaires"
        badge_bg = "#fee2e2"
        badge_color = "#991b1b"
        delta_color = "#dc2626"
        summary = (
            "Le comité durcit son orientation sémantique par rapport au FOMC précédent. "
            "La balance des risques reste asymétrique sur l'inflation, renforçant le scénario "
            "d'un maintien prolongé des taux directeurs (Higher-for-Longer) et réduisant la probabilité "
            "d'assouplissements monétaires à court terme."
        )
        impacts = [
            ("Taux US (2Y / 10Y)", "HAUSSE (Bearish Bonds)", "Tension sur la courbe, réévaluation des trajectoires de fed funds."),
            ("Bitcoin & Crypto", "BAISSIER / PRESSION", "Sensibilité négative à la contraction de liquidité et au raffermissement du DXY."),
            ("S&P 500 & Actions", "VOLATILITÉ / CONSOLIDATION", "Compression des multiples d'évaluation P/E, rotation vers la défensive."),
            ("Gold (Or)", "CONSOLIDATION", "Taux d'intérêt réels plus élevés pénalisant les actifs sans rendement direct."),
            ("Pétrole (WTI)", "NEUTRE / BAISSIER", "Craintes sur la demande globale face au ralentissement induit."),
        ]
    elif delta_score < -0.15:
        stance_label = "DOVISH PIVOT"
        stance_sub = "Assouplissement et détente des conditions"
        badge_bg = "#dcfce7"
        badge_color = "#166534"
        delta_color = "#16a34a"
        summary = (
            "Inflexion accommodante notable de la part du FOMC. Les éléments de langage actent "
            "des progrès tangibles sur la désinflation et pointent vers un rééquilibrage du double mandat, "
            "validant les anticipations de normalisation baissière du loyer de l'argent."
        )
        impacts = [
            ("Taux US (2Y / 10Y)", "BAISSE (Bullish Bonds)", "Détente sur les rendements souverains, pentification haussière attendue."),
            ("Bitcoin & Crypto", "FORTEMENT HAUSSIER", "Sensibilité maximale à l'expansion de liquidité M2 globale et baisse du dollar."),
            ("S&P 500 & Actions", "HAUSSIER / RISK-ON", "Assouplissement des conditions de crédit, soutien direct aux valeurs de croissance."),
            ("Gold (Or)", "HAUSSIER", "Repli des rendements réels obligataires et repli corrélatif du dollar index."),
            ("Pétrole (WTI)", "HAUSSIER", "Anticipation d'un rebond de l'activité manufacturière et du cycle macro."),
        ]
    else:
        stance_label = "STATUS QUO"
        stance_sub = "Dépendance stricte aux données (Data-Dependent)"
        badge_bg = "#f1f5f9"
        badge_color = "#334155"
        delta_color = "#475569"
        summary = (
            "Orientation globalement stable et réitérée sans inflexion sémantique majeure. "
            "Le comité maintient son approche pragmatique réunion par réunion, calibrant sa politique "
            "sur les prochaines publications d'inflation (PCE) et du marché de l'emploi (NFP)."
        )
        impacts = [
            ("Taux US (2Y / 10Y)", "STABLE / RANGE", "Volatilité contenue, ajustements marginaux selon la conférence de presse."),
            ("Bitcoin & Crypto", "NEUTRE / RANGE", "Dominé par la dynamique technique interne et les flux d'ETFs spot."),
            ("S&P 500 & Actions", "ATTENTISTE", "Sensibilité reportée sur le Q&A du président de la Réserve fédérale."),
            ("Gold (Or)", "STABLE", "Maintien dans les canaux techniques récents."),
            ("Pétrole (WTI)", "NEUTRE", "Marché prioritairement guidé par les équilibres d'offre OPEP+."),
        ]

    return stance_label, stance_sub, badge_bg, badge_color, delta_color, summary, impacts


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
                changes.append(
                    f"<div style='margin-bottom: 8px; font-size: 13px; line-height: 1.5;'>"
                    f"<span style='background:#fee2e2; color:#991b1b; padding:2px 6px; border-radius:3px; font-size:11px; font-weight:700; margin-right:6px;'>- SUPPR</span> "
                    f"<span style='text-decoration:line-through; color:#64748b;'>{removed}</span><br>"
                    f"<span style='background:#dcfce7; color:#166534; padding:2px 6px; border-radius:3px; font-size:11px; font-weight:700; margin-right:6px;'>+ AJOUT</span> "
                    f"<span style='color:#0f172a; font-weight:600;'>{added}</span>"
                    f"</div>"
                )
        elif tag == "insert":
            added = " ".join(new_words[j1:j2])
            if len(added) > 10:
                changes.append(
                    f"<div style='margin-bottom: 8px; font-size: 13px; line-height: 1.5;'>"
                    f"<span style='background:#dcfce7; color:#166534; padding:2px 6px; border-radius:3px; font-size:11px; font-weight:700; margin-right:6px;'>+ AJOUT</span> "
                    f"<span style='color:#0f172a; font-weight:600;'>{added}</span>"
                    f"</div>"
                )
        elif tag == "delete":
            removed = " ".join(old_words[i1:i2])
            if len(removed) > 10:
                changes.append(
                    f"<div style='margin-bottom: 8px; font-size: 13px; line-height: 1.5;'>"
                    f"<span style='background:#fee2e2; color:#991b1b; padding:2px 6px; border-radius:3px; font-size:11px; font-weight:700; margin-right:6px;'>- SUPPR</span> "
                    f"<span style='text-decoration:line-through; color:#64748b;'>{removed}</span>"
                    f"</div>"
                )

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
        "from": "CBST Macro Desk <onboarding@resend.dev>",
        "to": [recipient_email],
        "subject": subject,
        "html": html_content,
    }

    try:
        response = resend.Emails.send(params)
        print(f"Alerte envoyée via Resend avec succès ! ID: {response.get('id')}")
    except Exception as e:
        print(f"Erreur lors de l'envoi Resend : {e}")


def run_alert(force=False):
    csv_path = Path("data/processed/fomc_sentiment_scored.csv")
    if not csv_path.exists():
        print("Fichier de données introuvable.")
        return

    df = pd.read_csv(csv_path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(by="date", ascending=False).reset_index(drop=True)

    if len(df) < 2:
        print("Pas assez de réunions enregistrées pour effectuer une comparaison.")
        return

    latest = df.iloc[0]
    previous = df.iloc[1]

    delta = latest["net_sentiment"] - previous["net_sentiment"]
    stance_label, stance_sub, badge_bg, badge_color, delta_color, summary, impacts = generate_macro_impact(
        delta, latest["net_sentiment"]
    )
    changes = extract_key_redline_changes(
        str(previous["statement_text"]), str(latest["statement_text"])
    )

    date_str = latest["date"].strftime("%d %b %Y")
    prev_date_str = previous["date"].strftime("%d %b %Y")

    subject = f"FOMC Flash Desk Note • {date_str} [{stance_label}]"

    impact_rows_html = ""
    for asset, bias, mech in impacts:
        impact_rows_html += f"""
        <tr style="border-bottom: 1px solid #f1f5f9;">
            <td style="padding: 10px 12px; font-weight: 600; color: #0f172a; font-size: 13px;">{asset}</td>
            <td style="padding: 10px 12px; font-weight: 700; font-size: 12px; color: #1e293b;">{bias}</td>
            <td style="padding: 10px 12px; color: #475569; font-size: 12px;">{mech}</td>
        </tr>
        """

    changes_html = "".join(changes) if changes else "<p style='color: #64748b; font-size: 13px;'>Aucune modification structurelle constatée.</p>"

    html_template = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head><meta charset="utf-8"></head>
    <body style="margin: 0; padding: 30px 15px; background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #0f172a;">
        <table width="100%" border="0" cellspacing="0" cellpadding="0">
            <tr>
                <td align="center">
                    <table width="640" border="0" cellspacing="0" cellpadding="0" style="background-color: #ffffff; border-radius: 8px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.04);">
                        
                        <!-- Header institutionnel -->
                        <tr>
                            <td style="background-color: #090d16; padding: 24px 30px; border-bottom: 3px solid #2563eb;">
                                <table width="100%" border="0" cellspacing="0" cellpadding="0">
                                    <tr>
                                        <td>
                                            <div style="font-size: 11px; font-weight: 700; color: #94a3b8; letter-spacing: 1.2px; text-transform: uppercase;">
                                                Institutional Macro Research • Quantitative Desk
                                            </div>
                                            <div style="font-size: 20px; font-weight: 700; color: #ffffff; margin-top: 4px; letter-spacing: -0.3px;">
                                                Central Bank Sentiment Tracker (CBST)
                                            </div>
                                        </td>
                                        <td align="right" valign="middle">
                                            <div style="background-color: #1e293b; color: #cbd5e1; font-size: 11px; padding: 4px 10px; border-radius: 4px; font-weight: 600; display: inline-block;">
                                                FOMC RELEASE
                                            </div>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>

                        <!-- Section Contenu -->
                        <tr>
                            <td style="padding: 28px 30px;">

                                <!-- Barre de métriques clés -->
                                <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; margin-bottom: 24px;">
                                    <tr>
                                        <td width="38%" style="padding: 14px 16px; border-right: 1px solid #e2e8f0;">
                                            <div style="font-size: 10px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">Biais d'Orientation</div>
                                            <div style="margin-top: 5px;">
                                                <span style="background-color: {badge_bg}; color: {badge_color}; font-size: 12px; font-weight: 800; padding: 3px 8px; border-radius: 4px; display: inline-block;">
                                                    {stance_label}
                                                </span>
                                            </div>
                                            <div style="font-size: 11px; color: #64748b; margin-top: 4px;">{stance_sub}</div>
                                        </td>
                                        <td width="31%" style="padding: 14px 16px; border-right: 1px solid #e2e8f0;">
                                            <div style="font-size: 10px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">Net Sentiment Score</div>
                                            <div style="font-size: 18px; font-weight: 800; color: #0f172a; margin-top: 3px;">
                                                {latest['net_sentiment']:+.4f}
                                            </div>
                                            <div style="font-size: 11px; color: #64748b; margin-top: 3px;">Modèle FinBERT v2.1</div>
                                        </td>
                                        <td width="31%" style="padding: 14px 16px;">
                                            <div style="font-size: 10px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">Variation vs M-1</div>
                                            <div style="font-size: 18px; font-weight: 800; color: {delta_color}; margin-top: 3px;">
                                                {delta:+.4f}
                                            </div>
                                            <div style="font-size: 11px; color: #64748b; margin-top: 3px;">Précédent ({prev_date_str})</div>
                                        </td>
                                    </tr>
                                </table>

                                <!-- Synthèse Macroéconomique -->
                                <div style="margin-bottom: 24px;">
                                    <div style="font-size: 12px; font-weight: 800; text-transform: uppercase; color: #0f172a; letter-spacing: 0.6px; margin-bottom: 8px;">
                                        Executive Assessment
                                    </div>
                                    <div style="border-left: 3px solid #2563eb; padding: 12px 16px; background-color: #f8fafc; font-size: 13.5px; line-height: 1.6; color: #1e293b; border-radius: 0 4px 4px 0;">
                                        {summary}
                                    </div>
                                </div>

                                <!-- Matrice d'Impacts Marchés -->
                                <div style="margin-bottom: 24px;">
                                    <div style="font-size: 12px; font-weight: 800; text-transform: uppercase; color: #0f172a; letter-spacing: 0.6px; margin-bottom: 8px;">
                                        Cross-Asset Transmission Grid
                                    </div>
                                    <table width="100%" border="0" cellspacing="0" cellpadding="0" style="border: 1px solid #e2e8f0; border-radius: 6px; overflow: hidden; border-collapse: collapse;">
                                        <thead>
                                            <tr style="background-color: #f1f5f9; text-align: left;">
                                                <th style="padding: 8px 12px; font-size: 11px; color: #475569; text-transform: uppercase; font-weight: 700;">Classe d'Actifs</th>
                                                <th style="padding: 8px 12px; font-size: 11px; color: #475569; text-transform: uppercase; font-weight: 700;">Biais Tactique</th>
                                                <th style="padding: 8px 12px; font-size: 11px; color: #475569; text-transform: uppercase; font-weight: 700;">Mécanisme de Transmission</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {impact_rows_html}
                                        </tbody>
                                    </table>
                                </div>

                                <!-- Redline Diff -->
                                <div style="margin-bottom: 28px;">
                                    <div style="font-size: 12px; font-weight: 800; text-transform: uppercase; color: #0f172a; letter-spacing: 0.6px; margin-bottom: 8px;">
                                        Sémantique Différentielle (Key Redline Shifts)
                                    </div>
                                    <div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 14px 16px;">
                                        {changes_html}
                                    </div>
                                </div>

                                <!-- Call to Action -->
                                <table width="100%" border="0" cellspacing="0" cellpadding="0" style="margin-top: 10px; margin-bottom: 12px;">
                                    <tr>
                                        <td align="center">
                                            <a href="{DASHBOARD_URL}" target="_blank" style="background-color: #0f172a; color: #ffffff; text-decoration: none; font-size: 13px; font-weight: 700; padding: 12px 24px; border-radius: 5px; display: inline-block; letter-spacing: 0.3px;">
                                                Ouvrir le Terminal CBST &amp; Modèles Dérivés &rarr;
                                            </a>
                                        </td>
                                    </tr>
                                </table>
                                <div style="text-align: center; font-size: 11px; color: #64748b;">
                                    Accès direct : <a href="{DASHBOARD_URL}" target="_blank" style="color: #2563eb; text-decoration: none;">{DASHBOARD_URL}</a>
                                </div>

                            </td>
                        </tr>

                        <!-- Footer institutionnel -->
                        <tr>
                            <td style="background-color: #f8fafc; padding: 18px 30px; border-top: 1px solid #e2e8f0; font-size: 11px; color: #64748b; line-height: 1.5;">
                                <div style="font-weight: 700; color: #475569; margin-bottom: 4px;">CBST AUTOMATED QUANTITATIVE PIPELINE</div>
                                Données collectées à partir des flux officiels du Board of Governors of the Federal Reserve System. 
                                Traitement NLP via FinBERT. Ce document constitue une note d'analyse quantitative algorithmique et ne représente en aucun cas un conseil en investissement.
                            </td>
                        </tr>

                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    recipient = "lin.bahic@gmail.com"
    send_resend_alert(subject, html_template, recipient_email=recipient)


if __name__ == "__main__":
    run_alert()