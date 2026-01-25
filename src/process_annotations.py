import json
import logging
from pathlib import Path
from typing import Set

import pandas as pd


# -------------------- CONFIG --------------------
INPUT = Path("src/raw_annotations.csv")
OUT_JSONL = Path("clean_training_dataset.jsonl")
OUT_LOG = Path("disagreements.log")
CONF_THRESHOLD = 0.8

REQUIRED_COLUMNS = {"text", "annotator_id", "label", "confidence_score"}

# -------------------- LOGGING --------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)


# -------------------- FUNCTIONS --------------------
def load_and_filter(path: Path, threshold: float) -> pd.DataFrame:
    """Load CSV and filter records by confidence score."""
    try:
        if not path.exists():
            raise FileNotFoundError(f"Input file not found: {path}")

        df = pd.read_csv(path)

        if df.empty:
            raise ValueError("Input CSV is empty")

        missing = REQUIRED_COLUMNS - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")

        df = df[df["confidence_score"] >= threshold]

        logger.info("Loaded %d rows after confidence filtering", len(df))
        return df

    except pd.errors.ParserError as e:
        raise ValueError("CSV parsing failed") from e


def find_disagreements(df: pd.DataFrame) -> Set[str]:
    """Identify texts with conflicting labels."""
    if df.empty:
        return set()

    label_counts = (
        df.groupby("text", sort=False)["label"]
        .nunique()
    )

    disagreed = set(label_counts[label_counts > 1].index)
    logger.info("Found %d disagreements", len(disagreed))
    return disagreed


def write_outputs(df: pd.DataFrame, disagreed: Set[str]) -> None:
    """Write disagreements log and clean JSONL dataset."""
    try:
        # Write disagreements
        OUT_LOG.write_text(
            "\n".join(sorted(disagreed, key=str.lower)),
            encoding="utf-8"
        )

        # Remove conflicting texts
        clean = df.loc[~df["text"].isin(disagreed), ["text", "label"]]

        # One label per text (all remaining labels are identical)
        final = (
            clean
            .drop_duplicates(subset="text")
            .sort_values("text", key=lambda s: s.str.lower())
        )

        # Write JSONL
        with OUT_JSONL.open("w", encoding="utf-8") as f:
            for row in final.itertuples(index=False):
                f.write(
                    json.dumps(
                        {"text": row.text, "label": row.label},
                        ensure_ascii=False
                    ) + "\n"
                )

        logger.info(
            "Wrote %d clean records to %s",
            len(final),
            OUT_JSONL
        )

    except OSError as e:
        raise RuntimeError("Failed while writing output files") from e


# -------------------- MAIN --------------------
def main() -> None:
    logger.info("Using input file: %s", INPUT.resolve())

    try:
        df = load_and_filter(INPUT, CONF_THRESHOLD)
        disagreed = find_disagreements(df)
        write_outputs(df, disagreed)

    except Exception as e:
        logger.error("Pipeline failed: %s", e)
        raise


if __name__ == "__main__":
    main()
