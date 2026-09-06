from datetime import timedelta
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf

# Définition de l'univers d'actifs macroélectif
TICKERS = {
    "US_10Y": "^TNX",       # Rendement US 10 ans (points de base)
    "SPX": "^GSPC",          # S&P 500 (% de variation)
    "DXY": "DX-Y.NYB",       # US Dollar Index (% de variation)
    "BTC": "BTC-USD",        # Bitcoin (% de variation)
    "GOLD": "GC=F",          # Or Spot / Futures (% de variation)
}


def load_fomc_scores():
    csv_path = Path("data/processed/fomc_sentiment_scored.csv")
    if not csv_path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {csv_path}")

    df = pd.read_csv(csv_path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(by="date", ascending=True).reset_index(drop=True)
    df["delta_sentiment"] = df["net_sentiment"].diff().fillna(0.0)
    return df


def download_market_history(start_date, end_date):
    """Télécharge l'historique complet pour tous les tickers sur la fenêtre globale."""
    print(f"Téléchargement des données de marché de {start_date.date()} à {end_date.date()}...")
    market_data = {}
    
    for name, ticker in TICKERS.items():
        try:
            hist = yf.download(
                ticker,
                start=start_date - timedelta(days=10),
                end=end_date + timedelta(days=15),
                progress=False,
                auto_adjust=False,
            )
            if not hist.empty:
                # Gérer le multi-index si retourné par yfinance
                if isinstance(hist.columns, pd.MultiIndex):
                    close_series = hist["Close"][ticker]
                else:
                    close_series = hist["Close"]
                close_series.index = pd.to_datetime(close_series.index).tz_localize(None)
                market_data[name] = close_series.sort_index()
        except Exception as e:
            print(f"Erreur téléchargement {name} ({ticker}): {e}")

    return market_data


def get_reaction(price_series, event_date, asset_name):
    """Calcule la réaction à J+1 et J+5 ouvrés par rapport à la veille (J-1)."""
    # Recherche du cours de référence à la clôture la plus proche avant ou au jour de l'annonce
    past_prices = price_series[price_series.index <= event_date]
    if past_prices.empty:
        return np.nan, np.nan
    base_price = past_prices.iloc[-1]

    # Cours à +1 jour ouvré et +5 jours ouvrés
    future_prices = price_series[price_series.index > event_date]
    if len(future_prices) < 1:
        return np.nan, np.nan

    p_1d = future_prices.iloc[0]
    p_5d = future_prices.iloc[min(4, len(future_prices) - 1)]

    # Calcul : Variation absolue en bps pour les taux d'intérêt, pourcentage pour les autres
    if asset_name in ["US_10Y", "US_2Y"]:
        ret_1d = (p_1d - base_price) * 10.0  # TNX est coté en x10 (4.25% = 42.50) -> conversion en points de base
        ret_5d = (p_5d - base_price) * 10.0
    else:
        ret_1d = ((p_1d - base_price) / base_price) * 100.0
        ret_5d = ((p_5d - base_price) / base_price) * 100.0

    return round(float(ret_1d), 2), round(float(ret_5d), 2)


def run_event_study():
    fomc_df = load_fomc_scores()

    min_date = fomc_df["date"].min()
    max_date = fomc_df["date"].max()

    market_data = download_market_history(min_date, max_date)

    records = []
    for _, row in fomc_df.iterrows():
        event_d = row["date"]
        rec = {
            "date": event_d.strftime("%Y-%m-%d"),
            "net_sentiment": round(row["net_sentiment"], 4),
            "delta_sentiment": round(row["delta_sentiment"], 4),
        }

        for asset in TICKERS.keys():
            if asset in market_data:
                r1, r5 = get_reaction(market_data[asset], event_d, asset)
                rec[f"{asset}_ret_1d"] = r1
                rec[f"{asset}_ret_5d"] = r5
            else:
                rec[f"{asset}_ret_1d"] = np.nan
                rec[f"{asset}_ret_5d"] = np.nan

        records.append(rec)

    results_df = pd.DataFrame(records)

    out_path = Path("data/processed/fomc_market_reactions.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(out_path, index=False)
    print(f"Dataset d'Event Study généré avec succès : {out_path} ({len(results_df)} réunions traitées)")

    # Calcul et affichage d'un aperçu des corrélations rapides
    ret_cols = [c for c in results_df.columns if "_ret_1d" in c]
    corr = results_df[["delta_sentiment"] + ret_cols].corr()["delta_sentiment"].drop("delta_sentiment")
    print("\n--- Corrélation de Pearson (Delta FinBERT vs Réaction J+1) ---")
    for asset, val in corr.items():
        print(f"{asset.replace('_ret_1d', ''):10s} : {val:+.3f}")


if __name__ == "__main__":
    run_event_study()