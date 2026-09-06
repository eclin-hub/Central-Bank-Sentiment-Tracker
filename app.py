import difflib
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="CBST • Institutional Macro Terminal",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Style Dark Minimaliste & Typographie
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    header[data-testid="stHeader"] {
        background: rgba(15, 23, 42, 0.8);
        backdrop-filter: blur(8px);
    }
    #MainMenu, footer {visibility: hidden;}

    .metric-card {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 16px 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    .metric-label {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        color: #94a3b8;
        letter-spacing: 0.6px;
    }
    .metric-value {
        font-size: 24px;
        font-weight: 800;
        color: #f8fafc;
        margin-top: 4px;
    }
    .metric-delta {
        font-size: 12px;
        font-weight: 600;
        margin-top: 4px;
    }

    .diff-ins {
        background-color: rgba(22, 163, 74, 0.2);
        color: #4ade80;
        padding: 2px 4px;
        border-radius: 3px;
        text-decoration: none;
        font-weight: 600;
    }
    .diff-del {
        background-color: rgba(220, 38, 38, 0.2);
        color: #f87171;
        padding: 2px 4px;
        border-radius: 3px;
        text-decoration: line-through;
        font-weight: 500;
    }

    .badge-hawkish {
        background: rgba(220, 38, 38, 0.15);
        color: #ef4444;
        border: 1px solid rgba(220, 38, 38, 0.3);
        padding: 4px 10px;
        border-radius: 4px;
        font-weight: 700;
        font-size: 12px;
    }
    .badge-dovish {
        background: rgba(22, 163, 74, 0.15);
        color: #22c55e;
        border: 1px solid rgba(22, 163, 74, 0.3);
        padding: 4px 10px;
        border-radius: 4px;
        font-weight: 700;
        font-size: 12px;
    }
    .badge-neutral {
        background: rgba(148, 163, 184, 0.15);
        color: #94a3b8;
        border: 1px solid rgba(148, 163, 184, 0.3);
        padding: 4px 10px;
        border-radius: 4px;
        font-weight: 700;
        font-size: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=300)
def load_data():
    file_path = Path("data/processed/fomc_sentiment_scored.csv")
    if not file_path.exists():
        dates = pd.date_range(end=pd.Timestamp.now(), periods=12, freq="7W")
        np.random.seed(42)
        scores = np.cumsum(np.random.randn(12) * 0.15)
        df = pd.DataFrame(
            {
                "date": dates,
                "net_sentiment": scores,
                "statement_text": [
                    f"Sample statement text content for FOMC meeting {d.strftime('%B %Y')}."
                    for d in dates
                ],
            }
        )
        return df

    df = pd.read_csv(file_path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(by="date", ascending=True).reset_index(drop=True)
    return df


df = load_data()

# Sidebar
with st.sidebar:
    st.markdown("### 🏛️ **CBST Terminal**")
    st.caption("Quantitative FOMC Language Processing")
    st.markdown("---")

    min_date = df["date"].min().date()
    max_date = df["date"].max().date()
    date_range = st.date_input(
        "Période d'analyse",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    st.markdown("---")
    st.markdown("**Spécifications :**")
    st.caption(
        "• Modèle : FinBERT (Central Banking Fine-Tuned)\n"
        "• Métrique : Net Score $S = P(Positif) - P(Négatif)$\n"
        "• Échelle : $[-1.0, +1.0]$"
    )
    st.markdown("---")
    st.markdown(
        "<div style='font-size: 11px; color: #64748b;'>"
        "Pipeline automatisé via GitHub Actions & Scraper officiel de la Fed."
        "</div>",
        unsafe_allow_html=True,
    )

# Filtre temporel
if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    mask = (df["date"].dt.date >= date_range[0]) & (
        df["date"].dt.date <= date_range[1]
    )
    filtered_df = df.loc[mask].copy().reset_index(drop=True)
else:
    filtered_df = df.copy()

filtered_df["delta"] = filtered_df["net_sentiment"].diff().fillna(0)

latest_row = filtered_df.iloc[-1]
prev_row = filtered_df.iloc[-2] if len(filtered_df) > 1 else latest_row
delta = latest_row["net_sentiment"] - prev_row["net_sentiment"]

if delta > 0.10:
    stance_class = "badge-hawkish"
    stance_text = "HAWKISH SHIFT (Durcissement)"
elif delta < -0.10:
    stance_class = "badge-dovish"
    stance_text = "DOVISH PIVOT (Assouplissement)"
else:
    stance_class = "badge-neutral"
    stance_text = "STATUS QUO (Neutre)"

# Header Principal
st.markdown(
    """
    <div style="margin-bottom: 25px;">
        <div style="font-size: 12px; font-weight: 700; color: #3b82f6; text-transform: uppercase; letter-spacing: 1px;">
            Federal Reserve Intelligence • Real-Time Monitor
        </div>
        <h1 style="margin: 4px 0 6px 0; font-size: 28px; font-weight: 800; color: #f8fafc; letter-spacing: -0.5px;">
            FOMC Sentiment & Policy Stance Tracker
        </h1>
        <div style="font-size: 14px; color: #94a3b8;">
            Détection algorithmique d'inflexions sémantiques et modélisation de l'impact cross-asset par NLP.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Cartes KPI
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Dernier Net Score</div>
            <div class="metric-value">{latest_row['net_sentiment']:+.4f}</div>
            <div class="metric-delta" style="color: {'#ef4444' if delta > 0 else '#22c55e'};">
                {delta:+.4f} vs FOMC précédent
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with kpi2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Orientation Tactique</div>
            <div style="margin-top: 10px;">
                <span class="{stance_class}">{stance_text.split()[0]}</span>
            </div>
            <div class="metric-delta" style="color: #94a3b8; font-size: 11px;">
                {stance_text}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with kpi3:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Date du Communiqué</div>
            <div class="metric-value" style="font-size: 20px; line-height: 32px;">
                {latest_row['date'].strftime('%d %b %Y')}
            </div>
            <div class="metric-delta" style="color: #64748b;">
                Précédent : {prev_row['date'].strftime('%d %b %Y')}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with kpi4:
    vol = filtered_df["net_sentiment"].std()
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Volatilité Sémantique</div>
            <div class="metric-value">{vol:.3f}</div>
            <div class="metric-delta" style="color: #94a3b8;">
                Écart-type ({len(filtered_df)} FOMC analysés)
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)

# Onglets d'analyse
tab_analytics, tab_redline, tab_matrix = st.tabs(
    [
        "📈 Trajectoire & Régimes Macro",
        "🔍 Inspecteur Redline Diff (Side-by-Side)",
        "⚡ Grille de Transmission Cross-Asset",
    ]
)

with tab_analytics:
    # Calcul dynamique de l'amplitude Y pour éviter tout effet d'écrasement
    y_min = filtered_df["net_sentiment"].min()
    y_max = filtered_df["net_sentiment"].max()
    margin_y = max((y_max - y_min) * 0.25, 0.15)
    y_range = [y_min - margin_y, y_max + margin_y]

    fig = go.Figure()

    # Zone Hawkish en arrière-plan (au-dessus de 0)
    fig.add_hrect(
        y0=0,
        y1=y_range[1],
        fillcolor="rgba(239, 68, 68, 0.05)",
        line_width=0,
        annotation_text="RÉGIME HAWKISH (Restrictif)",
        annotation_position="top left",
        annotation_font=dict(color="rgba(239, 68, 68, 0.5)", size=11, family="Inter"),
    )

    # Zone Dovish en arrière-plan (en-dessous de 0)
    fig.add_hrect(
        y0=y_range[0],
        y1=0,
        fillcolor="rgba(34, 197, 94, 0.05)",
        line_width=0,
        annotation_text="RÉGIME DOVISH (Accommodant)",
        annotation_position="bottom left",
        annotation_font=dict(color="rgba(34, 197, 94, 0.5)", size=11, family="Inter"),
    )

    # Ligne de neutralité centrale bien visible
    fig.add_hline(
        y=0,
        line_color="#475569",
        line_width=1.5,
        line_dash="dot",
    )

    # Courbe principale de Net Sentiment
    fig.add_trace(
        go.Scatter(
            x=filtered_df["date"],
            y=filtered_df["net_sentiment"],
            mode="lines+markers",
            name="Net Sentiment FinBERT",
            line=dict(color="#38bdf8", width=3.5, shape="spline", smoothing=0.3),
            marker=dict(
                size=9,
                color="#0284c7",
                line=dict(color="#f8fafc", width=2),
            ),
            hovertemplate="<b>Date :</b> %{x|%d %b %Y}<br><b>Net Score :</b> %{y:+.4f}<extra></extra>",
        )
    )

    fig.update_layout(
        title=dict(
            text="<b>HISTORIQUE DU NET SENTIMENT FinBERT (ÉCHELLE DÉPLOYÉE)</b>",
            font=dict(size=14, color="#f8fafc"),
            x=0.01,
            y=0.96,
        ),
        plot_bgcolor="#090d16",
        paper_bgcolor="#090d16",
        font=dict(family="Inter, sans-serif", color="#94a3b8"),
        margin=dict(l=30, r=30, t=50, b=30),
        height=480,
        yaxis=dict(
            range=y_range,
            showgrid=True,
            gridcolor="#1e293b",
            gridwidth=1,
            zeroline=False,
            tickformat="+.2f",
            title=dict(text="Score Net", font=dict(size=12, color="#64748b")),
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor="#1e293b",
            gridwidth=1,
            tickformat="%b %Y",
            title=None,
        ),
        hovermode="x unified",
        showlegend=False,
    )

    st.plotly_chart(fig, use_container_width=True)

    # Deuxième section aérée : Chocs et Historique côte à côte
    col_bars, col_table = st.columns([1, 1])

    with col_bars:
        st.markdown("#### **Chocs Sémantiques (Delta vs M-1)**")
        delta_colors = [
            "#ef4444" if d > 0.05 else "#22c55e" if d < -0.05 else "#64748b"
            for d in filtered_df["delta"]
        ]

        fig_bar = go.Figure()
        fig_bar.add_trace(
            go.Bar(
                x=filtered_df["date"],
                y=filtered_df["delta"],
                marker_color=delta_colors,
                hovertemplate="<b>FOMC :</b> %{x|%b %Y}<br><b>Delta :</b> %{y:+.4f}<extra></extra>",
            )
        )
        fig_bar.add_hline(y=0, line_color="#334155", line_width=1)
        fig_bar.update_layout(
            plot_bgcolor="#090d16",
            paper_bgcolor="#090d16",
            font=dict(family="Inter, sans-serif", color="#94a3b8"),
            margin=dict(l=20, r=20, t=20, b=20),
            height=280,
            xaxis=dict(showgrid=False, tickformat="%b %y"),
            yaxis=dict(showgrid=True, gridcolor="#1e293b", tickformat="+.2f"),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_table:
        st.markdown("#### **Détail Numérique des Réunions**")
        st.dataframe(
            filtered_df[["date", "net_sentiment", "delta"]]
            .sort_values(by="date", ascending=False)
            .assign(
                date=lambda x: x["date"].dt.strftime("%Y-%m-%d"),
                net_sentiment=lambda x: x["net_sentiment"].map("{:+.4f}".format),
                delta=lambda x: x["delta"].map("{:+.4f}".format),
            )
            .rename(
                columns={
                    "date": "Date",
                    "net_sentiment": "Net Score",
                    "delta": "Variation Δ",
                }
            ),
            use_container_width=True,
            hide_index=True,
            height=280,
        )

with tab_redline:
    st.markdown("#### **Inspecteur Textuel Sémantique Différentiel**")
    st.caption(
        "Sélectionnez deux dates pour faire apparaître mot à mot les modifications apportées par le FOMC."
    )

    available_dates = df["date"].dt.strftime("%Y-%m-%d").tolist()[::-1]
    if len(available_dates) >= 2:
        c1, c2 = st.columns(2)
        with c1:
            d_new = st.selectbox("Communiqué Récent (T)", available_dates, index=0)
        with c2:
            d_old = st.selectbox(
                "Communiqué de Référence (T - 1)", available_dates, index=1
            )

        text_new = df.loc[
            df["date"].dt.strftime("%Y-%m-%d") == d_new, "statement_text"
        ].values[0]
        text_old = df.loc[
            df["date"].dt.strftime("%Y-%m-%d") == d_old, "statement_text"
        ].values[0]

        words_old = str(text_old).split()
        words_new = str(text_new).split()
        matcher = difflib.SequenceMatcher(None, words_old, words_new)

        diff_html = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                diff_html.append(" ".join(words_old[i1:i2]))
            elif tag == "replace":
                diff_html.append(
                    f'<span class="diff-del">{" ".join(words_old[i1:i2])}</span> '
                    f'<span class="diff-ins">{" ".join(words_new[j1:j2])}</span>'
                )
            elif tag == "delete":
                diff_html.append(
                    f'<span class="diff-del">{" ".join(words_old[i1:i2])}</span>'
                )
            elif tag == "insert":
                diff_html.append(
                    f'<span class="diff-ins">{" ".join(words_new[j1:j2])}</span>'
                )

        full_diff_text = " ".join(diff_html)

        st.markdown(
            f"""
            <div style="background-color: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 22px; line-height: 1.8; font-size: 14px; color: #e2e8f0; margin-top: 12px;">
                {full_diff_text}
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.info("Données textuelles insuffisantes pour exécuter le comparateur.")

with tab_matrix:
    st.markdown("#### **Matrice Cross-Asset & Sensibilité Macro**")
    st.caption("Conséquences tactiques attendues selon l'inflexion détectée.")

    st.markdown(
        """
        | Classe d'Actif | Biais Typique Hawkish | Biais Typique Dovish | Canal de Transmission Macro |
        | :--- | :--- | :--- | :--- |
        | **Taux US (2Y / 10Y)** | Tension à la hausse (Bearish) | Détente / Pentification (Bullish) | Réévaluation de la trajectoire des *fed funds* et prime de terme. |
        | **Bitcoin (BTC)** | Forte pression baissière | Fortement haussier | Proxy haute sensibilité à la liquidité globale M2 et au dollar. |
        | **S&P 500 (Actions)** | Compression des multiples P/E | Expansion des multiples (Risk-On) | Actualisation des flux de trésorerie futurs et conditions financières. |
        | **Gold (Or)** | Consolidation / Baisse | Rally haussier | Taux réels (TIPS yields) et corrélation inverse au Dollar Index (DXY). |
        | **Pétrole (WTI)** | Pression vendeuse | Soutien du cycle | Anticipation de croissance mondiale vs destruction de demande par resserrement. |
        """
    )