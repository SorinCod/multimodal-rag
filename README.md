# Multimodal Document RAG

A Retrieval-Augmented Generation (RAG) pipeline for messy, real-world documents — scanned PDFs, tables, and mixed-quality scans — with a confidence-gated human review queue and citation verification.

Unlike a typical "clean PDF" RAG demo, this project is built around the assumption that real documents are imperfect: some are native-text PDFs, some are scans, some have tables, and some have OCR quality too low to trust automatically. The pipeline routes content accordingly instead of blindly embedding everything.

## Features

- **Automatic document routing** — detects whether a PDF has native, extractable text or is a scanned image, and processes it accordingly (direct extraction vs. OCR)
- **OCR without system dependencies** — uses EasyOCR (pure Python/pip, no separate binary install required, unlike Tesseract)
- **Table extraction** — detects and extracts tables with visible grid lines (Camelot, `lattice` mode), converting them into both a readable dataframe and a searchable text description
- **Confidence-gated validation** — every OCR page and every extracted table gets a confidence score; low-confidence content is routed to a human review queue instead of being trusted blindly
- **Human review queue** — a dedicated UI to inspect, correct, approve, or reject low-confidence content before it enters the knowledge base
- **Citation-verified generation** — after generating an answer, a second independent LLM call checks whether the answer is actually supported by the retrieved context, flagging unverified claims instead of trusting the first response blindly
- **Per-document search filtering** — questions can be scoped to a single uploaded document, or searched across the entire knowledge base
- **File validation** — corrupted, empty, or non-PDF files are caught explicitly with a clear error message, instead of crashing the app

## Architecture

```
Upload PDF
    │
    ▼
Native text? ──Yes──► Direct text extraction
    │
    No
    │
    ▼
OCR (EasyOCR) ──► confidence score
    │
    ▼
Validator ──► accepted (score ≥ threshold) ──► chunk + embed ──► ChromaDB
    │
    └─► needs review ──► Review Queue (manual correction) ──► approved ──► chunk + embed ──► ChromaDB

Tables (Camelot) ──► same accept/review split, in parallel

User question ──► retrieve top-k chunks (optionally filtered by document)
    │
    ▼
Generate answer (Groq) ──► Verify answer against context (Groq, second pass)
    │
    ▼
Answer + verification status + cited sources
```

## Tech stack

| Layer | Tool | Why |
|---|---|---|
| OCR | EasyOCR | Pure Python, no system binary install (portable across environments) |
| Table extraction | Camelot | Reads native PDF structure for grid-based tables |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) | Small, fast, runs locally, no API cost |
| Vector store | ChromaDB | Persistent, local, simple to run without external infra |
| Generation | Groq API (`openai/gpt-oss-120b`) | Fast inference, generous free tier |
| UI | Streamlit | Rapid iteration, no separate frontend needed |

## Installation

```bash
git clone https://github.com/SorinCod/multimodal-rag.git
cd multimodal-rag

python -m venv venv
source venv/Scripts/activate   # Windows (Git Bash)
# or: venv\Scripts\activate    # Windows (CMD)
# or: source venv/bin/activate # Mac/Linux

pip install -r requirements.txt
```

Create a `.env` file in the project root with your [Groq API key](https://console.groq.com/keys):

```
GROQ_API_KEY=your_key_here
```

## Running

```bash
streamlit run app/main.py
```

The app opens with three sections: **Upload & Process**, **Chat**, and **Review Queue**, all visible at once.

## Project structure

```
app/
├── ingestion/       # PDF parsing, OCR, table extraction, validation
├── review_queue/    # Manual review UI and queue management
├── retrieval/       # Chunking, embeddings, vector store, retriever
├── generation/      # LLM calls (answer generation + verification)
└── main.py          # Streamlit UI

tests/               # Manual test scripts for each module
data/                # Runtime data (uploaded files, vector DB) — not committed
```

## Known limitations

- **Table detection is conservative by design** — only tables with visible grid lines are detected (Camelot `lattice` mode). Borderless tables are not extracted, to avoid false positives on plain paragraphs.
- **Text and table overlap** — if a page contains both a table and surrounding paragraphs, only the table is embedded for that page (to avoid duplicate content); non-table text on that page is not separately indexed.
- **No persistence across restarts in some deployment environments** — the vector store and review queue are stored on local disk; on ephemeral hosting, they reset on restart.
- **Cold-start latency** — OCR and embedding models load on first use (a few seconds), then stay cached for the session via `@st.cache_resource`.
- **CPU-only inference** — no GPU acceleration; adequate for demo-scale usage, not high-throughput production.

## License

MIT
