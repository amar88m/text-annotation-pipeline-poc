# Text Annotation Pipeline — Proof of Concept (Quality Validator & Output Generator)

This repo contains a **Proof of Concept (PoC)** for the *Quality Validator & Output Generator* that converts raw annotation outputs into a clean, ML ready training dataset. It fits into a broader GCP architecture using **Dataflow (ingestion)**, **GCS (raw store)**, **Kafka (annotation jobs)**, **Vertex AI Data Labeling (human-in-the-loop)**, **PostgreSQL (annotation store)**, **BigQuery (curated dataset)**, and **Collibra (governance)**.

---

## Architecture (High Level)

See the Mermaid diagram in **`architecture_diagram.md`**. The PoC component lives after annotations are produced and stored (PostgreSQL), and it is responsible for quality filtering and generating the curated dataset (JSONL and BigQuery table).

---

## PoC Scope & Outputs
The PoC performs the following steps:

1. **Read annotations** from `raw_annotations.csv`
2. **Quality Check 1 — Confidence**: keep only rows with `confidence_score >= 0.8`.
3. **Quality Check 2 — Agreement**: detect texts whose remaining annotators disagree; log those texts to `disagreements.log`.
4. **Emit** a clean, **JSONL** dataset `clean_training_dataset.jsonl` with one `{"text", "label"}` per line for agreed texts.
5. *(Optional)* Load curated rows into a BigQuery for downstream training (BigQuery ML).

---

## Generated Files
· **`clean_training_dataset.jsonl`** — curated, high-quality training set
· **`disagreements.log`** — list of texts with post-threshold label disagreements

---

## **Run the script**

> **Prerequisites**:
· Python 3.13.9
· pandas

```bash
pip install pandas
PS F:\git\text-annotation-pipeline-poc> & F:\git\text-annotation-pipeline-poc\.venv\Scripts\python.exe f:/git/text-annotation-pipeline-poc/src/process_annotations.py
```

The script will read `raw_annotations.csv` in the current directory and write the two output files listed above.

---

## Production Alignment (GCP)
This PoC is designed to plug into the following production components:

· **Dataflow**
  · ingests batch/stream text -> **GCS (raw)** and optionally **Kafka (raw)**.
· **Annotation Orchestrator**
  · curates jobs into Kafka **(annotation jobs)**.
· **Vertex AI Data Labeling**
  · provides the UI/workforce, exports labeled data to **GCS**.
· **ETL Loader**
  · loads exports into **PostgreSQL** as the annotation store.
· **Quality Validator**
  · reads CSV/Postgres -> applies quality checks -> emits JSONL -> (optionally) loads **BigQuery**.
· **BigQuery**
  · stores the curated dataset (managed table) for **BigQuery ML**.
· **Collibra**
  · catalogs the curated dataset, versions, lineage, and policies (no bulk data stored in Collibra).

---

## Suggested Repository Layout

```
├── architecture_diagram.md            # Mermaid diagram (GCS + Dataflow + BigQuery + Collibra)
├── design_document.md                 # System design (this architecture)
├── process_annotations.py             # PoC: confidence + agreement checks
├── raw_annotations.csv                # Sample input (provided by assignment)
├── clean_training_dataset.jsonl       # Generated output
├── disagreements.log                  # Generated output
└── ...
```

---

## Dataset Versioning & Governance
-**BigQuery**: use table **snapshots/partitions** to version curated datasets.
-**Collibra**: register dataset assets with attributes like `dataset_version`, `schema_version`, `policy_version` and link to PoC logs/exports.

> Collibra is for metadata & lineage, not for storing raw/versioned data or large metric tables.