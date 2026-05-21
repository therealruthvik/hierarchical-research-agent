# Hierarchical Research Agent

Multi-agent GenAI research pipeline built on [Google ADK](https://google.github.io/adk-docs/). Takes a vague enterprise question and returns a structured, self-critiqued recommendation.

## Architecture

```
SequentialAgent: research_pipeline
├── manager_agent          → decomposes question → session state
├── ParallelAgent
│   ├── rag_agent          → Vertex AI Search (internal KB)
│   ├── web_search_agent   → Google Search grounding
│   └── cost_analysis_agent→ pricing estimates + ROI analysis
└── synthesis_agent        → integrates findings → self-critique → final recommendation
```

The synthesis agent follows a 3-step self-reflection loop:
1. **Draft** — initial recommendation with architecture diagram
2. **Self-critique** — challenges assumptions, missing risks, contradictions
3. **Revised recommendation** — hardened output addressing each critique

## Prerequisites

- Python 3.11+
- Google Cloud project with billing enabled
- `gcloud` CLI authenticated (`gcloud auth login`)

## Setup

### 1. GCP Resources

```bash
PROJECT=$(gcloud config get project)

# Service account
gcloud iam service-accounts create research-agent-sa \
  --display-name="Hierarchical Research Agent"

gcloud projects add-iam-policy-binding "$PROJECT" \
  --member="serviceAccount:research-agent-sa@${PROJECT}.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding "$PROJECT" \
  --member="serviceAccount:research-agent-sa@${PROJECT}.iam.gserviceaccount.com" \
  --role="roles/discoveryengine.viewer"

# Download key
mkdir -p ~/keys
gcloud iam service-accounts keys create ~/keys/research-agent-sa.json \
  --iam-account="research-agent-sa@${PROJECT}.iam.gserviceaccount.com"

# GCS bucket for RAG documents
gcloud storage buckets create gs://${PROJECT}-research-docs --location=us-central1

# Grant Vertex AI Search access to bucket
PROJECT_NUMBER=$(gcloud projects describe $PROJECT --format="value(projectNumber)")
gcloud storage buckets add-iam-policy-binding gs://${PROJECT}-research-docs \
  --member="serviceAccount:service-${PROJECT_NUMBER}@gcp-sa-discoveryengine.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"
```

### 2. Vertex AI Search Data Store

1. Upload documents to GCS: `gcloud storage cp your-docs/* gs://${PROJECT}-research-docs/`
2. Open [Vertex AI Agent Builder](https://console.cloud.google.com/gen-app-builder/data-stores)
3. Create Data Store → Cloud Storage → point at your bucket
4. Note the Data Store ID from the URL

### 3. Environment

```bash
cp .env.example .env  # or create .env manually
```

Required variables:

| Variable | Description |
|----------|-------------|
| `GOOGLE_CLOUD_PROJECT` | GCP project ID |
| `GOOGLE_CLOUD_LOCATION` | GCP region (e.g. `us-central1`) |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account JSON key |
| `GOOGLE_GENAI_USE_VERTEXAI` | Must be `true` |
| `VERTEX_SEARCH_DATA_STORE_ID` | Data store ID from Vertex AI Agent Builder |

### 4. Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

### Preflight (run before every deploy)

```bash
python preflight.py
```

All 9 checks must pass before deploying.

### Run locally

```bash
python main.py
```

Override the question:

```bash
RESEARCH_QUESTION="How should we architect GenAI for fraud detection?" python main.py
```

### ADK Web UI (agent trace viewer)

```bash
adk web
```

Opens at `http://localhost:8000` — shows full agent trace, tool calls, session state, latency per agent.

## Project Structure

```
.
├── agents/
│   ├── manager.py          # Decomposes question into 3 research tracks
│   ├── specialists.py      # RAG, web search, cost analysis agents
│   ├── synthesis.py        # Self-reflecting synthesis agent
│   └── pipeline.py         # Assembles SequentialAgent + ParallelAgent
├── tools/
│   ├── rag_tools.py        # Vertex AI Search (lazy-initialized)
│   └── cost_tools.py       # GCP pricing estimates + ROI calculator
├── config.py               # All settings, no client instantiation
├── main.py                 # Entry point
├── preflight.py            # 9-check pre-deploy validation script
├── requirements.txt        # Floor-pinned dependencies
├── .gcloudignore           # Cloud Build source upload exclusions
└── .dockerignore           # Container build exclusions
```

## Extending to New Domains

The pipeline is domain-agnostic. To retarget:

1. `agents/manager.py` — update `MANAGER_INSTRUCTION` with new domain context
2. `agents/specialists.py` — update RAG/web/cost instructions
3. `tools/cost_tools.py` — swap in domain-relevant pricing data
4. Upload domain documents to GCS and re-index the data store

`main.py`, `pipeline.py`, `preflight.py`, and `tools/rag_tools.py` require no changes.

## Teardown

```bash
PROJECT=$(gcloud config get project)

gcloud storage rm -r gs://${PROJECT}-research-docs
gcloud iam service-accounts delete \
  research-agent-sa@${PROJECT}.iam.gserviceaccount.com --quiet
rm ~/keys/research-agent-sa.json
```

Delete the Vertex AI Search data store manually in the [console](https://console.cloud.google.com/gen-app-builder/data-stores).
