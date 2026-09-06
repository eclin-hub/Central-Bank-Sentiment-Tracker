import re
from pathlib import Path
import pandas as pd
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

MODEL_NAME = "ProsusAI/finbert"


def split_sentences(text):
    """Découpe un texte en phrases sans dépendance réseau externe."""
    if not isinstance(text, str) or not text.strip():
        return []
    # Découpe sur ponctuation suivie d'un espace ou d'un saut de ligne
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in sentences if len(s.strip()) > 5]


def load_model():
    """Charge le tokenizer et le modèle FinBERT."""
    print(f"Chargement du modèle {MODEL_NAME}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    model.eval()
    return tokenizer, model


def score_text(text, tokenizer, model):
    """Découpe en phrases et calcule le score Hawk-Dove agrégé."""
    sentences = split_sentences(text)
    if not sentences:
        return 0.0, 0.0, 0.0, 0.0

    inputs = tokenizer(
        sentences, padding=True, truncation=True, max_length=128, return_tensors="pt"
    )

    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=1)

    labels = model.config.id2label
    pos_idx = [k for k, v in labels.items() if v.lower() == "positive"][0]
    neg_idx = [k for k, v in labels.items() if v.lower() == "negative"][0]
    neu_idx = [k for k, v in labels.items() if v.lower() == "neutral"][0]

    pos_prob = probs[:, pos_idx].mean().item()
    neg_prob = probs[:, neg_idx].mean().item()
    neu_prob = probs[:, neu_idx].mean().item()

    # Score net : Positif (Hawkish) - Négatif (Dovish)
    net_score = pos_prob - neg_prob

    return round(net_score, 4), round(pos_prob, 4), round(neg_prob, 4), round(neu_prob, 4)


def main():
    input_path = Path("data/raw/fomc_statements.csv")
    if not input_path.exists():
        raise FileNotFoundError(f"{input_path} introuvable. Lance le scraper d'abord.")

    df = pd.read_csv(input_path)
    tokenizer, model = load_model()

    print(f"\nCalcul du sentiment pour {len(df)} déclarations...\n")
    net_scores = []
    pos_scores = []
    neg_scores = []
    neu_scores = []

    for idx, row in df.iterrows():
        text = str(row["statement_text"])
        net, pos, neg, neu = score_text(text, tokenizer, model)
        net_scores.append(net)
        pos_scores.append(pos)
        neg_scores.append(neg)
        neu_scores.append(neu)

        date_str = str(row["date"])[:10]
        label = "Hawkish" if net > 0.05 else ("Dovish" if net < -0.05 else "Neutre")
        print(f"[{date_str}] Score net : {net:+0.4f} ({label:<7}) | Pos: {pos:.2f} | Neg: {neg:.2f}")

    df["net_sentiment"] = net_scores
    df["label"] = [
        "Hawkish" if s > 0.05 else ("Dovish" if s < -0.05 else "Neutre")
        for s in net_scores
    ]
    df["pos_prob"] = pos_scores
    df["neg_prob"] = neg_scores
    df["neu_prob"] = neu_scores

    out_dir = Path("data/processed")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "fomc_sentiment_scored.csv"
    df.to_csv(out_path, index=False, encoding="utf-8")
    print(f"\nFichier généré avec succès : {out_path}")


if __name__ == "__main__":
    main()