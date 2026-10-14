import time
import requests
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def fetch_hyperliquid_candles(coin: str = "HYPE", interval: str = "1h", lookback_days: int = 30) -> pd.DataFrame:
    url = "https://api.hyperliquid.xyz/info"
    headers = {"Content-Type": "application/json"}
    end_time = int(time.time() * 1000)
    start_time = end_time - (lookback_days * 24 * 3600 * 1000)
    
    payload = {
        "type": "candleSnapshot",
        "req": {
            "coin": coin,
            "interval": interval,
            "startTime": start_time,
            "endTime": end_time
        }
    }
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    if not data:
        raise ValueError(f"Données introuvables pour {coin}")
    
    df = pd.DataFrame(data)
    df["t"] = pd.to_datetime(df["t"], unit="ms")
    df["c"] = df["c"].astype(float)
    df.rename(columns={"t": "timestamp", "c": "close"}, inplace=True)
    df.sort_values("timestamp", inplace=True)
    return df[["timestamp", "close"]]

def calibrate_market_dynamics(df: pd.DataFrame, freq_hours: int = 1):
    S0 = df["close"].iloc[-1]
    df["log_ret"] = np.log(df["close"] / df["close"].shift(1))
    periods_per_year = (24 / freq_hours) * 365
    sigma = df["log_ret"].std() * np.sqrt(periods_per_year)
    return S0, sigma

def run_liquidation_simulation(
    S0: float,
    sigma: float,
    leverage: float,
    horizon_days: int,
    mu: float = 0.0,
    annual_funding: float = 0.10,
    maintenance_margin: float = 0.02,
    take_profit_pct: float = 0.20,
    n_sims: int = 50_000,
    steps_per_day: int = 24
):
    T = horizon_days / 365.0
    n_steps = horizon_days * steps_per_day
    dt = T / n_steps
    
    liq_price = S0 * (1.0 - (1.0 / leverage) + maintenance_margin)
    tp_price = S0 * (1.0 + take_profit_pct)
    net_drift = mu - annual_funding
    
    Z = np.random.standard_normal((n_steps, n_sims))
    drift_step = (net_drift - 0.5 * sigma**2) * dt
    diffusion_step = sigma * np.sqrt(dt) * Z
    
    log_paths = np.vstack([np.zeros(n_sims), np.cumsum(drift_step + diffusion_step, axis=0)])
    paths = S0 * np.exp(log_paths)
    
    hit_liq = paths <= liq_price
    hit_tp = paths >= tp_price
    
    first_liq_idx = np.where(hit_liq.any(axis=0), np.argmax(hit_liq, axis=0), n_steps + 1)
    first_tp_idx = np.where(hit_tp.any(axis=0), np.argmax(hit_tp, axis=0), n_steps + 1)
    
    prob_liq_total = np.mean(first_liq_idx <= n_steps) * 100
    prob_tp_before_liq = np.mean((first_tp_idx < first_liq_idx) & (first_tp_idx <= n_steps)) * 100
    
    return {
        "S0": S0, "sigma": sigma, "liq_price": liq_price, "tp_price": tp_price,
        "prob_liq_total": prob_liq_total, "prob_tp_before_liq": prob_tp_before_liq,
        "paths": paths, "horizon_days": horizon_days, "leverage": leverage
    }

if __name__ == "__main__":
    print("-> Récupération des données HYPE...")
    df = fetch_hyperliquid_candles("HYPE", interval="1h", lookback_days=30)
    current_price, sigma = calibrate_market_dynamics(df)
    
    print(f"Prix actuel (S0) : {current_price:.3f} $")
    print(f"Volatilité annualisée (30j) : {sigma * 100:.2f} %")
    
    res = run_liquidation_simulation(
        S0=current_price,
        sigma=sigma,
        leverage=3.0,
        horizon_days=14,
        take_profit_pct=0.25,
        n_sims=50_000
    )
    
    print(f"Prix de liquidation : {res['liq_price']:.2f} $")
    print(f"Risque de liquidation : {res['prob_liq_total']:.2f} %")
    print(f"Probabilité TP avant liquidation : {res['prob_tp_before_liq']:.2f} %")
    
    plt.figure(figsize=(9, 5))
    t_grid = np.linspace(0, res["horizon_days"], res["paths"].shape[0])
    plt.plot(t_grid, res["paths"][:, :80], color="steelblue", alpha=0.15)
    plt.axhline(res["liq_price"], color="crimson", linestyle="--", label="Liquidation")
    plt.axhline(res["tp_price"], color="forestgreen", linestyle="--", label="Take Profit (+25%)")
    plt.title(f"Simulation Monte-Carlo HYPE (Levier x{res['leverage']})")
    plt.xlabel("Jours")
    plt.ylabel("Prix ($)")
    plt.legend()
    plt.show()
