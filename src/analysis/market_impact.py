from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf


def load_sentiment_data():
    csv_path = Path("data/processed/fomc_sentiment_scored.csv")
    if not csv_path.exists():
        raise FileNotFoundError(f"{csv_path} introuvable.")

    df = pd.read_csv(csv_path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(by="date").reset_index(drop=True)
    return df


def fetch_treasury_data(start_date, end_date):
    """Récupère les rendements des emprunts d'État US à 2 ans (^2YY ou 2Y proxy)."""
    print(f"Téléchargement des données de marché ({start_date} à {end_date})...")
    # US 2-Year Treasury Note Yield
    ticker = "^2YY"
    treasury = yf.download(ticker, start=start_date, end=end_date, progress=False)

    if treasury.empty:
        # Fallback sur le 10Y (^TNX) si le ticker 2Y direct est indisponible
        print("^2YY non disponible, bascule sur ^TNX (US 10Y Yield)...")
        treasury = yf.download("^TNX", start=start_date, end=end_date, progress=False)

    # Récupération de la colonne Close
    close_series = treasury["Close"]
    if isinstance(close_series, pd.DataFrame):
        close_series = close_series.iloc[:, 0]

    df_rates = pd.DataFrame({"rate": close_series})
    df_rates.index = pd.to_datetime(df_rates.index).tz_localize(None)
    return df_rates


def plot_sentiment_vs_rates(df_sentiment, df_rates):
    """Génère le graphique superposant le sentiment Fed et les taux."""
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Axe 1 : Rendement obligataire
    color_rate = "#1f77b4"
    ax1.set_xlabel("Date", fontsize=11)
    ax1.set_ylabel("Yield (%)", color=color_rate, fontsize=11)
    ax1.plot(df_rates.index, df_rates["rate"], color=color_rate, label="Taux Trésor US", linewidth=1.8)
    ax1.tick_params(axis="y", labelcolor=color_rate)
    ax1.grid(True, linestyle="--", alpha=0.4)

    # Axe 2 : Score de sentiment net
    ax2 = ax1.twinx()
    color_sent = "#d62728"
    ax2.set_ylabel("Fed Hawk-Dove Score", color=color_sent, fontsize=11)

    # Tracé des réunions FOMC
    ax2.scatter(
        df_sentiment["date"],
        df_sentiment["net_sentiment"],
        color=color_sent,
        s=80,
        zorder=5,
        label="FOMC Statement Score",
    )
    ax2.plot(
        df_sentiment["date"],
        df_sentiment["net_sentiment"],
        color=color_sent,
        linestyle=":",
        alpha=0.6,
    )
    ax2.axhline(0, color="gray", linestyle="-", linewidth=0.8, alpha=0.7)
    ax2.tick_params(axis="y", labelcolor=color_sent)

    plt.title("Fed Sentiment Tracker vs Rendements Obligataires", fontsize=13, fontweight="bold")
    fig.tight_layout()

    out_dir = Path("notebooks")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_img = out_dir / "sentiment_vs_rates.png"
    plt.savefig(out_img, dpi=300)
    print(f"Graphique sauvegardé dans : {out_img}")
    plt.show()


def main():
    df_sent = load_sentiment_data()
    min_date = (df_sent["date"].min() - pd.Timedelta(days=15)).strftime("%Y-%m-%d")
    max_date = (df_sent["date"].max() + pd.Timedelta(days=15)).strftime("%Y-%m-%d")

    df_rates = fetch_treasury_data(min_date, max_date)
    plot_sentiment_vs_rates(df_sent, df_rates)


if __name__ == "__main__":
    main()