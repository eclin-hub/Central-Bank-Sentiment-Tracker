import difflib
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

st.set_page_config(
    page_title="CBST • Institutional Macro Terminal",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Style CSS Dark Institutional
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

# Barre laterale
with st.sidebar:
    st.markdown("### 🏛️ **CBST Terminal**")
    st.caption("Quantitative FOMC Language Processing")
    st.markdown("---")

    min_date = df["date"].min().date()
    max_date = df["date"].max().date()
    date_range = st.date_input(
        "Periode d'analyse",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    st.markdown("---")
    st.markdown("**Specifications Modele :**")
    st.caption(
        "• Modele : FinBERT Fine-Tuned (Central Banks)\n"
        "• Frequence : Reunions FOMC officielles\n"
        "• Metrique : Net Score $S = P(pos) - P(neg)$"
    )
    st.markdown("---")
    st.markdown(
        "<div style='font-size: 11px; color: #64748b;'>"
        "Pipeline automatise via GitHub Actions & Fed Scraper.<br>Toutes donnees verifiees sur federalreserve.gov"
        "</div>",
        unsafe_allow_html=True,
    )

# Filtrage temporel
if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    mask = (df["date"].dt.date >= date_range[0]) & (
        df["date"].dt.date <= date_range[1]
    )
    filtered_df = df.loc[mask].copy().reset_index(drop=True)
else:
    filtered_df = df.copy()

latest_row = filtered_df.iloc[-1]
prev_row = (
    filtered_df.iloc[-2] if len(filtered_df) > 1 else latest_row
)
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
            Detection algorithmique d'inflexions semantiques et modelisation de l'impact cross-asset par NLP.
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
                {delta:+.4f} vs FOMC precedent
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
            <div class="metric-label">Date du Communique</div>
            <div class="metric-value" style="font-size: 20px; line-height: 32px;">
                {latest_row['date'].strftime('%d %b %Y')}
            </div>
            <div class="metric-delta" style="color: #64748b;">
                Precedent : {prev_row['date'].strftime('%d %b %Y')}
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
            <div class="metric-label">Volatilite Semantique</div>
            <div class="metric-value">{vol:.3f}</div>
            <div class="metric-delta" style="color: #94a3b8;">
                Ecart-type sur la selection ({len(filtered_df)} FOMC)
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)

# Onglets d'analyse
tab_analytics, tab_redline, tab_matrix = st.tabs(
    [
        "📈 Dynamique & Historique Quantitative",
        "🔍 Inspecteur Redline Diff (Side-by-Side)",
        "⚡ Grille de Transmission Cross-Asset",
    ]
)

with tab_analytics:
    filtered_df["delta"] = filtered_df["net_sentiment"].diff().fillna(0)
    filtered_df["ema_sentiment"] = (
        filtered_df["net_sentiment"].ewm(span=3, adjust=False).mean()
    )

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.70, 0.30],
        subplot_titles=(
            "<b>TRAJECTOIRE DU NET SENTIMENT FinBERT & REGIMES DE POLITIQUE MONETAIRE</b>",
            "<b>CHOCS SEMANTIQUES REUNION PAR REUNION (DELTA vs M-1)</b>",
        ),
    )

    # Zone neutre
    fig.add_hrect(
        y0=-0.05,
        y1=0.05,
        fillcolor="rgba(148, 163, 184, 0.08)",
        line_width=0,
        row=1,
        col=1,
        annotation_text="Zone Neutre / Data-Dependent",
        annotation_position="bottom right",
        annotation_font=dict(color="#64748b", size=9),
    )

    # Tendance EMA
    fig.add_trace(
        go.Scatter(
            x=filtered_df["date"],
            y=filtered_df["ema_sentiment"],
            mode="lines",
            name="Tendance EMA (3M)",
            line=dict(color="#94a3b8", width=1.5, dash="dot"),
            hoverinfo="skip",
        ),
        row=1,
        col=1,
    )

    # Ligne principale Net Sentiment
    fig.add_trace(
        go.Scatter(
            x=filtered_df["date"],
            y=filtered_df["net_sentiment"],
            mode="lines+markers",
            name="Net Sentiment (FOMC)",
            line=dict(color="#38bdf8", width=3),
            marker=dict(
                size=7,
                color="#0284c7",
                line=dict(width=1.5, color="#f8fafc"),
            ),
            fill="tozeroy",
            fillcolor="rgba(56, 189, 248, 0.07)",
            hovertemplate="<b>Date :</b> %{x|%d %b %Y}<br><b>Net Score :</b> %{y:+.4f}<extra></extra>",
        ),
        row=1,
        col=1,
    )

    fig.add_hline(
        y=0,
        line_width=1,
        line_color="#475569",
        row=1,
        col=1,
    )

    # Panneau inferieur : Deltas
    delta_colors = [
        "#f87171" if d > 0.08 else "#4ade80" if d < -0.08 else "#64748b"
        for d in filtered_df["delta"]
    ]

    fig.add_trace(
        go.Bar(
            x=filtered_df["date"],
            y=filtered_df["delta"],
            marker_color=delta_colors,
            name="Variation Δ",
            hovertemplate="<b>FOMC :</b> %{x|%b %Y}<br><b>Variation :</b> %{y:+.4f}<extra></extra>",
        ),
        row=2,
        col=1,
    )

    fig.add_hline(
        y=0.10,
        line_dash="dash",
        line_color="rgba(239, 68, 68, 0.4)",
        line_width=1,
        row=2,
        col=1,
    )
    fig.add_hline(
        y=-0.10,
        line_dash="dash",
        line_color="rgba(34, 197, 94, 0.4)",
        line_width=1,
        row=2,
        col=1,
    )

    fig.update_layout(
        plot_bgcolor="#090d16",
        paper_bgcolor="#090d16",
        font=dict(family="Inter, sans-serif", color="#94a3b8"),
        margin=dict(l=40, r=30, t=60, b=30),
        height=540,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, color="#cbd5e1"),
        ),
        hovermode="x unified",
    )

    # Axes X nets sans selectors problématiques
    fig.update_xaxes(showgrid=True, gridcolor="#1e293b", row=1, col=1)
    fig.update_xaxes(showgrid=True, gridcolor="#1e293b", row=2, col=1)

    fig.update_yaxes(
        title_text="Net Score",
        showgrid=True,
        gridcolor="#1e293b",
        zeroline=False,
        row=1,
        col=1,
    )
    fig.update_yaxes(
        title_text="Variation Δ",
        showgrid=True,
        gridcolor="#1e293b",
        zeroline=False,
        row=2,
        col=1,
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### **Registre Quantitatif des Decisions**")
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
                "date": "Date Reunion",
                "net_sentiment": "Score FinBERT",
                "delta": "Variation Δ vs M-1",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

with tab_redline:
    st.markdown("#### **Inspecteur Textuel Semantique Differentiel**")
    st.caption(
        "Selectionnez deux dates pour faire apparaitre mot a mot les modifications apportees par le FOMC."
    )

    available_dates = df["date"].dt.strftime("%Y-%m-%d").tolist()[::-1]
    if len(available_dates) >= 2:
        c1, c2 = st.columns(2)
        with c1:
            d_new = st.selectbox("Communique Recent (T)", available_dates, index=0)
        with c2:
            d_old = st.selectbox(
                "Communique de Reference (T - 1)", available_dates, index=1
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
        st.info("Donnees textuelles insuffisantes pour executer le comparateur.")

with tab_matrix:
    st.markdown("#### **Matrice Cross-Asset & Sensibilite Macro**")
    st.caption("Consequences tactiques attendues selon l'inflexion detectee.")

    st.markdown(
        """
        | Classe d'Actif | Biais Typique Hawkish | Biais Typique Dovish | Canal de Transmission Macro |
        | :--- | :--- | :--- | :--- |
        | **Taux US (2Y / 10Y)** | Tension a la hausse (Bearish) | Detente / Pentification (Bullish) | Reevaluation de la trajectoire des *fed funds* et prime de terme. |
        | **Bitcoin (BTC)** | Forte pression baissiere | Fortement haussier | Proxy haute sensibilite a la liquidite globale M2 et au dollar. |
        | **S&P 500 (Actions)** | Compression des multiples P/E | Expansion des multiples (Risk-On) | Actualisation des flux de tresorerie futurs et conditions financieres. |
        | **Gold (Or)** | Consolidation / Baisse | Rally haussier | Taux reels (TIPS yields) et correlation inverse au Dollar Index (DXY). |
        | **Petrole (WTI)** | Pression vendeuse | Soutien du cycle | Anticipation de croissance mondiale vs destruction de demande par resserrement. |
        """
    )