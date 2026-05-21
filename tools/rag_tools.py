"""RAG tool backed by Vertex AI Search. Client is lazy-initialized — never at import time."""
from __future__ import annotations

import os
from typing import TYPE_CHECKING

import config

if TYPE_CHECKING:
    from google.cloud import discoveryengine_v1 as discoveryengine

_search_client: "discoveryengine.SearchServiceClient | None" = None


def _get_search_client() -> "discoveryengine.SearchServiceClient":
    global _search_client
    if _search_client is None:
        from google.cloud import discoveryengine_v1 as discoveryengine
        _search_client = discoveryengine.SearchServiceClient()
    return _search_client


def rag_search(query: str) -> str:
    """Search the internal knowledge base for GenAI architecture patterns, call center deployments,
    and enterprise AI best practices. Returns relevant excerpts.

    Args:
        query: The search query string.

    Returns:
        Concatenated text of top matching documents.
    """
    if not config.PROJECT_ID or not config.SEARCH_DATA_STORE_ID:
        return (
            "[RAG unavailable: GCP_PROJECT_ID or VERTEX_SEARCH_DATA_STORE_ID not set. "
            "Returning placeholder.] "
            "Knowledge base contains: LLM deployment patterns for contact centers, "
            "RAG architecture guides, agent evaluation frameworks, data privacy compliance docs."
        )

    client = _get_search_client()
    from google.cloud import discoveryengine_v1 as discoveryengine

    # Vertex AI Search data stores default to "global" region regardless of GCP_LOCATION
    search_location = os.environ.get("VERTEX_SEARCH_LOCATION", "global")
    serving_config = (
        f"projects/{config.PROJECT_ID}/locations/{search_location}"
        f"/collections/default_collection/dataStores/{config.SEARCH_DATA_STORE_ID}"
        f"/servingConfigs/default_config"
    )

    request = discoveryengine.SearchRequest(
        serving_config=serving_config,
        query=query,
        page_size=5,
        content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
            snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
                return_snippet=True,
                max_snippet_count=3,
            ),
            summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
                summary_result_count=5,
                include_citations=True,
            ),
        ),
    )

    response = client.search(request)
    snippets: list[str] = []

    for result in response.results:
        doc = result.document
        derived = doc.derived_struct_data
        for snippet in derived.get("snippets", []):
            if snippet.get("snippet"):
                snippets.append(snippet["snippet"])

    if response.summary and response.summary.summary_text:
        return f"SUMMARY: {response.summary.summary_text}\n\nSNIPPETS:\n" + "\n---\n".join(snippets)

    return "\n---\n".join(snippets) if snippets else "No relevant documents found."
