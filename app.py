import difflib
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="CBST - Central Bank Sentiment Tracker", layout="wide")

st.title("Central Bank Sentiment Tracker (CBST)")
st.caption("Monitoring du ton du FOMC via FinBERT et impact sur les rendements obligataires")


@st.cache_data
def load_data():
    path = Path("data/processed/fomc_sentiment_scored.csv")
    if not path.exists():
        return None
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(by="date", ascending=False).reset_index(drop=True)
    return df


@st.cache_data
def load_rates(start_date, end_date):
    # Proxy 2Y ou bascule sur 10Y (^TNX)
    ticker = "2YY=F"
    rates = yf.download(ticker, start=start_date, end=end_date, progress=False)
    if rates.empty or "Close" not in rates:
        rates = yf.download("^TNX", start=start_date, end=end_date, progress=False)
    close = rates["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    df = pd.DataFrame({"yield": close})
    df.index = pd.to_datetime(df.index).tz_localize(None)
    return df


df_sent = load_data()

if df_sent is None:
    st.error("Données introuvables. Lance d'abord les scripts de scraping et de scoring.")
    st.stop()

# Barre latérale : Sélection des dates pour le Redline Diff
st.sidebar.header("Paramètres Redline Diff")
dates_list = df_sent["date"].dt.strftime("%Y-%m-%d").tolist()

selected_new = st.sidebar.selectbox("Déclaration récente", dates_list, index=0)
selected_old = st.sidebar.selectbox(
    "Déclaration antérieure", dates_list, index=1 if len(dates_list) > 1 else 0
)

# Onglets principaux
tab_overview, tab_diff = st.tabs(["Vue marché & Sentiment", "Statement Redline (Diff)"])

with tab_overview:
    latest = df_sent.iloc[0]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Dernière réunion", latest["date"].strftime("%Y-%m-%d"))
    col2.metric("Net Sentiment Score", f"{latest['net_sentiment']:+.4f}")
    col3.metric("Classification", latest["label"])
    col4.metric(
        "Proba Hawkish / Dovish",
        f"{latest['pos_prob']:.2f} / {latest['neg_prob']:.2f}",
    )

    min_date = (df_sent["date"].min() - pd.Timedelta(days=15)).strftime("%Y-%m-%d")
    max_date = (df_sent["date"].max() + pd.Timedelta(days=15)).strftime("%Y-%m-%d")
    df_rates = load_rates(min_date, max_date)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df_rates.index,
            y=df_rates["yield"],
            name="US Treasury Yield (%)",
            line=dict(color="#2962FF", width=2),
            yaxis="y1",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df_sent["date"],
            y=df_sent["net_sentiment"],
            name="Fed Net Score",
            mode="lines+markers",
            marker=dict(size=9, color="#D50000"),
            line=dict(color="#D50000", dash="dot"),
            yaxis="y2",
        )
    )

    fig.update_layout(
        title="Trajectoire du sentiment de la Fed vs Taux US",
        xaxis=dict(title="Date"),
        yaxis=dict(title="Yield (%)", side="left"),
        yaxis2=dict(
            title="Hawk-Dove Net Score",
            side="right",
            overlaying="y",
            showgrid=False,
            range=[-1, 1],
        ),
        legend=dict(orientation="h", y=1.1),
        height=500,
    )
    st.plotly_chart(fig, width="stretch")

with tab_diff:
    st.subheader(f"Comparaison : {selected_old} vs {selected_new}")
    row_new = df_sent[df_sent["date"].dt.strftime("%Y-%m-%d") == selected_new].iloc[0]
    row_old = df_sent[df_sent["date"].dt.strftime("%Y-%m-%d") == selected_old].iloc[0]

    old_text = str(row_old["statement_text"]).splitlines()
    new_text = str(row_new["statement_text"]).splitlines()

    differ = difflib.HtmlDiff(wrapcolumn=70)
    diff_html = differ.make_table(
        old_text,
        new_text,
        fromdesc=f"FOMC {selected_old}",
        todesc=f"FOMC {selected_new}",
        context=True,
        numlines=2,
    )

    styled_html = f"""
    <style>
    table.diff {{font-family: monospace; font-size: 13px; width: 100%; border-collapse: collapse;}}
    .diff_add {{background-color: #c8e6c9;}}
    .diff_chg {{background-color: #fff9c4;}}
    .diff_sub {{background-color: #ffcdd2;}}
    </style>
    {diff_html}
    """
    st.components.v1.html(styled_html, height=600, scrolling=True)