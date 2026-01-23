import pandas as pd
import json
from pathlib import Path

INPUT = Path("src/raw_annotations.csv")
OUT_JSONL = Path("clean_training_dataset.jsonl")
OUT_LOG = Path("disagreements.log")
CONF_THRESHOLD = 0.8

# Load CSV and Filter by Confidence
def load_and_filter(path: Path, threshold: float) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"text", "annotator_id", "label", "confidence_score"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    df = df[df["confidence_score"] >= threshold].copy()
    return df

# Identify Annotation Conflicts
def find_disagreements(df: pd.DataFrame) -> set:
    counts = df.groupby("text")["label"].nunique()
    return set(counts[counts > 1].index)

# Write Clean Dataset and Log Disagreements
def write_outputs(df: pd.DataFrame, disagreed: set):
    # This opens the log file `disagreements.log` for writing
    with OUT_LOG.open("w", encoding="utf-8") as f:
        for text in sorted(disagreed, key=lambda s: s.lower()):
            f.write(text + "\n")
    # Remove texts with disagreements to create a clean dataset
    clean = df[~df["text"].isin(disagreed)].copy()
    # For each text, all remaining labels are identical, so we pick the first one consistently
    final = (
        clean.sort_values(["text", "label"])
        .groupby(["text"], as_index=False)["label"].first()
        .sort_values("text", key=lambda s: s.str.lower())
    )
    # Write the cleaned dataset to a JSONL file, one JSON object per line
    with OUT_JSONL.open("w", encoding="utf-8") as f:
        for _, row in final.iterrows():
            f.write(json.dumps({"text": row["text"], "label": row["label"]}, ensure_ascii=False) + "\n")

def main():
    df = load_and_filter(INPUT, CONF_THRESHOLD)
    disagreed = find_disagreements(df)
    write_outputs(df, disagreed)

if __name__ == "__main__":
    main()