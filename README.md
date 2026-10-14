# 🏦 Central Bank Sentiment Tracker (CBST)

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![FinBERT](https://img.shields.io/badge/NLP-FinBERT-orange)
![Resend](https://img.shields.io/badge/Alerts-Resend_API-black)
![License](https://img.shields.io/badge/License-MIT-green)

**Central Bank Sentiment Tracker (CBST)** is an institutional-grade quantitative NLP pipeline designed to monitor, score, and analyze the monetary policy stance of the Federal Reserve. By scraping official FOMC statements, processing text through **FinBERT** sentiment analysis, and evaluating automated semantic diffs, the system generates real-time cross-asset impact assessments and dispatches automated flash notes straight to the macro desk via **Resend**.

---

## 🎯 Core Features & Architecture

### 1. 🕷️ Automated Fed Scraping Pipeline
* Automatically parses official monetary policy calendars and extracts the latest FOMC press releases (`monetaryYYYYMMDDa.htm`) directly from `federalreserve.gov`.

### 2. 📊 Quantitative NLP Scoring (FinBERT)
* Applies a specialized financial transformer model (**FinBERT**) to compute granular sentiment probabilities, producing a robust `net_sentiment` score per meeting.

### 3. 🔍 Redline Semantic Differencing (`difflib`)
* Compares consecutive FOMC statements word-by-word to highlight structural shifts (**Key Redline Shifts**), capturing subtle pivots in forward guidance.

### 4. 🌐 Interactive Macro Terminal (Streamlit)
* A full-featured web dashboard deployed live at [cbst07.streamlit.app](https://cbst07.streamlit.app), featuring interactive Plotly visualizations and historical stance tracking.

### 5. 📩 Automated Desk Alerts (Resend API & GitHub Actions)
* Evaluates stance shifts ($\Delta \text{ Score}$) and maps them to a **Cross-Asset Transmission Grid** (Rates, Equities, Crypto, Gold, Oil) before sending an instant HTML flash note.

---

## 🏗️ System Architecture

~~~mermaid
graph LR
    A[🏛️ Fed Official Site] -->|Scraper Pipeline| B(📄 Raw FOMC Text)
    B -->|FinBERT NLP Model| C(📊 Sentiment Scoring CSV)
    C -->|fomc_sentiment_scored.csv| D(🐍 macro_alert.py)
    D -->|Semantic Diff & Delta| E{⚖️ Stance Classification}
    E -->|HTML Flash Note| F[📩 Resend API]
    F -->|Instant Alert| G((📬 Macro Desk Inbox))
    C -->|Dataset| H[🌐 Streamlit Dashboard app.py]
~~~

---

## 📂 Repository Structure

~~~text
├── .github/workflows/   # Automated GitHub Actions cron jobs (Fed Sniper pipeline)
├── data/
    ├── raw/             # Scraped raw statements (fomc_statements.csv)
    └── processed/       # FinBERT-scored dataset (fomc_sentiment_scored.csv)
├── src/
    ├── scraper/         # Federal Reserve web scraping utilities
    └── analysis/        # FinBERT scoring & macro_alert.py (Resend email dispatch)
├── app.py               # Streamlit interactive web terminal
├── requirements.txt     # Python dependencies
└── README.md            # Project documentation
~~~

---

## 🚀 Getting Started (Local Setup)

### 1. Clone the repository
~~~bash
git clone https://github.com/eclin-hub/Central-Bank-Sentiment-Tracker.git
cd Central-Bank-Sentiment-Tracker
~~~

### 2. Install dependencies
~~~bash
pip install -r requirements.txt
~~~

### 3. Run the Streamlit Dashboard locally
~~~bash
streamlit run app.py
~~~

---

## 👤 Author

**Lin Bahic**  
*Master 1 in Analysis and Economic Policy (APE) — Quantitative Finance, Macro & Econometrics*  
🔗 [GitHub Profile](https://github.com/eclin-hub)