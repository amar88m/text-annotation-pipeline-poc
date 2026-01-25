# Design Document - Text Annotation Pipeline

## 1. Architectural Diagram
Please see `architecture_diagram.md` for the data flow from ingestion to  BigQuery

## 2. Components & Data Flow (High-Level)

1. **Raw Text Ingestion Service (GCP Dataflow)**
   · Sources: support tickets, chat logs, emails
   · Ingests both batch and streaming text
   · Stores raw data in **GCS** for replay, audits, and backfill
   · Optionally publishes events to **Kafka Raw Text Topic** for real-time processing
2. **Annotation Orchestrator & Queue**
   · Consumes raw events from GCS/Kafka
   · Creates annotation-ready tasks (sampling, filtering, shaping)
   · Publishes tasks into the **Kafka Annotation Jobs Topic** for human labeling workflows
3. **Annotation Tooling (Vertex AI Data Labeling)**
   · Managed human-in-the-loop annotation platform
   · Annotators label text examples through Vertex AI UI
   · Exported labeled data is loaded into **PostgreSQL**
4. **Annotation Store (OLTP DB)**
   · **PostgreSQL** with ACID guarantees and JSONB for flexible annotation metadata.
   · Stores: text, annotator_id, label, confidence_score, policy_version, timestamps.
5. **Quality Validator & Output Generator (Core Logic)**
   · Loads annotations (CSV extract or PostgreSQL view)
   · Quality Check 1: Keep only annotations with `confidence_score` >= 0.8
   · Quality Check 2: After filtering, detect label disagreements and log them to `disagreements.log`
   · Emits `clean_training_dataset.jsonl` (one record per agreed text)
   · Deterministic and auditable
   · Loads curated rows into a **BigQuery**.
6. **Curated Dataset (BigQuery)**
   · Clean dataset stored as a **BigQuery**
   · Supports dataset versioning using snapshots or partitioning.
   · Ideal for downstream ML, analytics, and reproducibility.
7. **Metadata, Lineage, & Governance (Collibra)**
   · Registers the curated BigQuery dataset as a governed data asset.
   · Captures metadata: dataset_version, schema version, policy version, source span, confidence thresholds.
   · Tracks upstream/downstream lineage.
   · Does not store raw or versioned data-stores metadata & catalog entries.
8. **Model Training Jobs**
   · Downstream consumers (**BigQuery ML**) train models using curated BigQuery tables.
   · Training metadata (metrics, parameters) can be linked back to Collibra.

---

## 3. Technology Justification (Why These Choices?)

· **Dataflow (Ingestion)**: Manages scalable ETL pipelines, supports both streaming and batch.
· **Kafka (Annotation Queue)**: Reliable task distribution, backpressure handling, and fan-out for annotation workloads.
· **Vertex AI Labeling**: Production-ready human annotation UI with workforce management and GCS exports.
· **PostgreSQL (Annotation Store)**: Strong consistency, schema control, JSONB metadata flexibility
· **Quality Validator**: Implements required PoC logic for filtering, agreement checks, and deterministic training output generation
· **BigQuery**: Fully managed, highly durable storage layer supporting SQL analytics, snapshots, and ML integration
· **Collibra**: Enterprise governance hub for dataset metadata, lineage, ownership, policies, and auditability

---

## 4. Data Governance & Lineage

- **Dataset Versioning:** Each curated export corresponds to a BigQuery snapshot or partition, with version metadata logged in Collibra.
- **Lineage Capture:** Collibra models data flow from raw → annotation → curated dataset → training.
- **Reproducibility:** BigQuery table snapshots ensure reproducible training data. PoC output is deterministic.
- **Auditability:** Store `disagreements.log`, annotation assignments, annotator metadata, and policy versions.

---

## **5.PoC Scope**
· Read CSV input
· Apply confidence & agreement checks
· Write `clean_training_dataset.json`
· Write `disagreements.log`