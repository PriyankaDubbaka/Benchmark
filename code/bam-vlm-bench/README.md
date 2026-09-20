# BAM VLM PDF Extraction Benchmark (PW2)

A production-ready benchmark testing platform designed for **BAM (Bundesanstalt für Materialforschung und -prüfung)** to evaluate open-source Vision-Language Models (VLMs) on structured data extraction and evidence retrieval from technical certificate PDFs.

---

## Key Features

1. **API Key & Endpoint Management in UI**:
   - Dedicated UI page to input, save, test, and manage API keys.
   - Built specifically for organization GPU setups: support for **Department On-Premise GPU endpoints** (vLLM, TGI, Ollama) alongside cloud API providers (Together AI, Fireworks AI, Mistral AI, Groq, DeepSeek, HuggingFace, OpenRouter).
   - Real-time connection testing (`Test Connection` button) to verify credentials against endpoints.

2. **Open-Source VLM Models with Vision Capabilities**:
   - Evaluates strictly open-source models with high-resolution image/document reasoning:
     - **Qwen2.5-VL (72B & 7B Instruct)**: SOTA for dense OCR and complex tabular extraction.
     - **Pixtral Large (124B) & Pixtral (12B)**: Native multi-resolution and arbitrary aspect ratio preservation.
     - **Llama 3.2 Vision (90B & 11B)**: General document VQA on Together AI, Fireworks, and Groq LPU.
     - **InternVL3 (78B)**: Dynamic tile splitting for scientific charts and tables.
     - **Phi-4 Multimodal (5.6B)**: Compact, MIT-licensed high-density document extractor.
     - **DeepSeek-VL2**: Vision-language MoE architecture.
     - **Idefics3 (8B), Florence-2 Large, GOT-OCR2.0**: Specialized OCR and bounding box models.
     - **BAM Internal GPU Cluster (vLLM)**: Private, on-premise hosted VLM instances.

3. **Master Copy Ground Truth Baseline**:
   - Complete data model (`DocumentAnnotation`, `ExtractionRecord`, `RetrievalQuery`) serving as the frozen ground truth baseline.
   - Initial master copy covers the 8-page **BAM-S005c V2** certificate with **27 elemental mass-fraction records** across `%` and `mg/kg` units, expanded uncertainty ($k=2$, ~95% confidence), certification status, and calculated oxide formulas.
   - Additional templates provided for `BAM-D001`, `BAM-K009a`, `BAM-K001`, and `BAM-U130`.

4. **Rigorous Metrological Scoring (PW2 Track E & PW4 Track R)**:
   - **Track E (Extraction)**: Exact-record Precision, Recall, F1 score, and per-field attribute accuracy (value, unit, uncertainty, status, oxide formula, page). Decimal values undergo normalization (e.g. `0.587` vs `.587`).
   - **Track R (Retrieval)**: nDCG@1/3/5, MRR@1/3/5, Recall@1/3/5, and complete-evidence success rate across 16 domain queries.

5. **Interactive Results Comparison**:
   - Side-by-side leaderboard with Master Copy at 100% baseline.
   - Interactive Bar Charts (F1 Score comparison) and Radar Charts (per-field attribute adherence).
   - One-click CSV and JSON data export.

---

## Architecture Overview

```
                                  ┌────────────────────────┐
                                  │  Dataset PDF Documents │
                                  │  (BAM Certificates)    │
                                  └───────────┬────────────┘
                                              │
                                              ▼
                                  ┌────────────────────────┐
                                  │     PDF Processor      │
                                  │ (Page Image Rendering) │
                                  └───────────┬────────────┘
                                              │
                       ┌──────────────────────┴──────────────────────┐
                       ▼                                             ▼
          ┌─────────────────────────┐                   ┌─────────────────────────┐
          │ Department On-Premise   │                   │ Cloud VLM Providers     │
          │ GPU Cluster (vLLM/TGI)  │                   │ (Together, Fireworks,   │
          │ [BAM Internal Endpoint] │                   │  Mistral, Groq, HF)     │
          └────────────┬────────────┘                   └────────────┬────────────┘
                       └──────────────────────┬──────────────────────┘
                                              │
                                              ▼
                                  ┌────────────────────────┐
                                  │   Structured Output    │
                                  │ (Normalized Extraction)│
                                  └───────────┬────────────┘
                                              │
                                              ▼
    ┌────────────────────────┐    ┌────────────────────────┐
    │  Master Copy Baseline  │───▶│     Scoring Engine     │
    │ (Ground Truth Annot.)  │    │  (Exact P/R/F1, nDCG)  │
    └────────────────────────┘    └───────────┬────────────┘
                                              │
                                              ▼
                                  ┌────────────────────────┐
                                  │   Interactive Web UI   │
                                  │  (Leaderboard & Radar) │
                                  └────────────────────────┘
```

---

## Project Structure

```
code/bam-vlm-bench/
├── .env.example                 # Template for API keys & custom base URLs
├── requirements.txt             # Python backend dependencies
├── README.md                    # Project documentation (this file)
│
├── backend/                     # FastAPI Backend Application
│   ├── main.py                  # Entry point & CORS configuration
│   ├── config.py                # Environment settings
│   ├── models/
│   │   ├── annotations.py       # Master Copy schema (ExtractionRecord, DocumentAnnotation)
│   │   ├── predictions.py       # Model prediction and raw response schemas
│   │   ├── scoring.py           # Evaluation score structures (P/R/F1, nDCG, MRR)
│   │   └── api_keys.py          # Key management and status schemas
│   ├── services/
│   │   ├── pdf_processor.py     # PDF to page image converter (Poppler + PIL fallback)
│   │   ├── scorer.py            # Rigorous evaluation metric implementation
│   │   ├── vlm_runner.py        # Prompt orchestration and JSON extraction
│   │   ├── benchmark.py         # Background benchmark execution manager
│   │   └── providers/           # Provider adapters (OpenAI-compatible VLM endpoints)
│   ├── routers/
│   │   ├── api_keys.py          # API key & Base URL endpoints (GET/POST/DELETE/TEST)
│   │   ├── models.py            # VLM models catalog and availability filtering
│   │   ├── documents.py         # PDF documents and Master Copy inspector
│   │   ├── benchmarks.py        # Benchmark execution and real-time polling
│   │   └── results.py           # Leaderboard, comparison, and CSV/JSON export
│   └── data/
│       ├── annotations/         # Master Copy JSON annotations (bam-s005c-v2.json, etc.)
│       └── manifests/           # Document registry
│
├── frontend/                    # Modern React / Vite / Tailwind UI
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── api/client.ts        # Axios API client
│       ├── components/Layout.tsx# Navigation layout with sidebar
│       └── pages/
│           ├── Dashboard.tsx    # High-level statistics and quick actions
│           ├── ApiKeysPage.tsx  # API key & Department GPU endpoint configuration
│           ├── ModelsPage.tsx   # Catalog of open-source VLM models
│           ├── DocumentsPage.tsx# Certificate browser & Master Copy ground truth inspector
│           ├── BenchmarkRunPage.tsx # Multi-step execution wizard with live progress
│           └── ResultsPage.tsx  # Leaderboard table, F1 bar charts, and radar charts
│
└── results/                     # Output directory for persisted benchmark runs
```

---

## Execution Guide

### Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **Poppler** (recommended for rendering high-resolution PDF page images)
  - **Windows**: Download the binary zip from [poppler-windows releases](https://github.com/oschwartz10612/poppler-windows/releases), extract to a folder (e.g. `C:\Program Files\poppler`), and add its `bin` folder to your system `PATH`.
  - **Linux (Ubuntu/Debian)**: `sudo apt-get install poppler-utils`
  - **macOS**: `brew install poppler`

---

### Step 1: Set Up Backend

```bash
# Navigate to the benchmark project
cd code/bam-vlm-bench

# Create and activate virtual environment
python -m venv venv

# Windows PowerShell / CMD:
venv\Scripts\activate

# Linux / macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start backend server
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be live at:
- **API Base**: `http://localhost:8000/api`
- **Interactive OpenAPI Documentation**: `http://localhost:8000/docs`

---

### Step 2: Set Up Frontend

Open a new terminal window:

```bash
# Navigate to frontend directory
cd code/bam-vlm-bench/frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```

The UI will be accessible in your web browser at:
- `http://localhost:5173`

---

## How to Configure Your Department's GPU API Keys

1. Open `http://localhost:5173/api-keys` in your browser.
2. Locate the card:
   - If your department hosts models internally: Use the **Department On-Premise GPU (vLLM / TGI)** card.
     - Enter your department-issued API Key.
     - Enter the internal cluster URL in the **Custom Base URL** field (e.g. `http://gpu-cluster.bam.de:8000/v1` or `http://10.x.x.x:8000/v1`).
   - If using cloud provider keys: Find the respective card (Together AI, Fireworks AI, Mistral AI, Groq, etc.), input the key, and click **Save**.
3. Click **Test Connection** on any card to verify that the endpoint is reachable and authenticates properly.
4. Credentials are automatically synced to `code/bam-vlm-bench/.env` and securely masked in the interface.

---

## How to Run a Benchmark

1. Navigate to **Run Benchmark** (`/benchmark`).
2. **Step 1: Select Certificate**: Choose `BAM-S005c V2 (Glass Reference Material)` (which has a verified Master Copy ground truth annotation) or any of the other registered certificates.
3. **Step 2: Select Models**: Pick one or more open-source VLMs (e.g., `Qwen2.5-VL 72B`, `Pixtral Large 124B`, `Llama 3.2 Vision 90B`, or your `Department GPU Cluster`).
4. **Step 3: Select Tasks**: Choose **Technical Extraction** (PW2 Track E) and/or **Evidence Retrieval** (PW4 Track R).
5. **Step 4: Launch**: Click **Launch Benchmark**. Watch live progress bar updates as PDF pages are converted and sent to the VLM inference engines.
6. Upon completion, a summary card shows exact precision, recall, F1, and exact records recovered. Click **Compare All Results** to explore visual charts on the Results page.

---

## Ground Truth Master Copy Schema

The Master Copy files are stored in `backend/data/annotations/`. Example excerpt from `bam-s005c-v2.json`:

```json
{
  "schema_version": "1.0",
  "document_id": "bam-s005c-v2",
  "annotation_status": "machine_assisted_draft",
  "scope": "Elemental mass-fraction rows in summary tables on pages 1 and 2",
  "extraction_records": [
    {
      "element": "Al",
      "value": "0.587",
      "unit": "%",
      "expanded_uncertainty": "0.018",
      "coverage_factor": 2,
      "status": "certified",
      "oxide_formula": "Al2O3",
      "oxide_value": "1.109",
      "source_page": 1
    },
    {
      "element": "Fe",
      "value": "295",
      "unit": "mg/kg",
      "expanded_uncertainty": "7",
      "coverage_factor": 2,
      "status": "certified",
      "oxide_formula": "Fe2O3",
      "oxide_value": "422",
      "source_page": 1
    }
  ]
}
```

---

## Scoring Contract (PW2 Metrological Standard)

- **Element Match**: Records match on the case-sensitive elemental symbol (e.g., `Al`, `Fe`, `Si`).
- **Exact Field Matching**: A true positive requires:
  - $\text{value}$ equals reference value under decimal normalization (`33.1` equals `33.10`).
  - $\text{unit}$ matches exactly (`%` vs `mg/kg`).
  - $\text{expanded\_uncertainty}$ matches reference ($k=2$).
  - $\text{status}$ correctly identifies `certified` vs `information_only` (e.g. $P$ and $Se$ on page 2).
  - Calculated $\text{oxide\_formula}$ and $\text{oxide\_value}$ match when present.
- **Precision, Recall & F1**:
  $$\text{Precision} = \frac{\text{Exact Matched Records}}{\text{Total Predicted Records}}, \quad \text{Recall} = \frac{\text{Exact Matched Records}}{\text{Total Gold Reference Records}}$$
  $$F_1 = 2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}$$
- **Retrieval Metrics**: Evaluated at $k \in \{1, 3, 5\}$ using $\text{nDCG}@k = \frac{\text{DCG}@k}{\text{IDCG}@k}$ where gain is $2^{\text{grade}} - 1$, and Reciprocal Rank ($\text{MRR}$).

---

## Adding New Certificates to the Benchmark

1. Place the raw PDF into the `dataset/` folder.
2. In `backend/data/annotations/`, copy one of the template files (e.g. `bam-d001.json`) to `<new_doc_id>.json`.
3. Fill in the `extraction_records` according to the summary tables on the certificate.
4. Set `"annotation_status": "expert_validated"` or `"machine_assisted_draft"`.
5. The document will automatically appear in the UI with a "Ground Truth Ready" badge.
