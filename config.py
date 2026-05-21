import os

# Model names — verify at https://cloud.google.com/vertex-ai/generative-ai/docs/models
# before every deploy. These deprecate without notice.
# Override via env vars to avoid code changes on model rotation.
ORCHESTRATOR_MODEL = os.environ.get("ORCHESTRATOR_MODEL", "gemini-2.5-flash")
SPECIALIST_MODEL = os.environ.get("SPECIALIST_MODEL", "gemini-2.5-flash")

# GCP — ADK reads GOOGLE_CLOUD_PROJECT / GOOGLE_CLOUD_LOCATION natively
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", os.environ.get("GCP_PROJECT_ID", ""))
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", os.environ.get("GCP_LOCATION", "us-central1"))

# Vertex AI Search — RAG backend
SEARCH_DATA_STORE_ID = os.environ.get("VERTEX_SEARCH_DATA_STORE_ID", "")

# App identity
APP_NAME = "hierarchical_research_agent"

REQUIRED_ENV_VARS = [
    "GOOGLE_CLOUD_PROJECT",
    "GOOGLE_CLOUD_LOCATION",
    "GOOGLE_GENAI_USE_VERTEXAI",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "VERTEX_SEARCH_DATA_STORE_ID",
]
