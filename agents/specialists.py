"""Three specialist agents: RAG, web search, cost analysis. Run in parallel."""
from google.adk.agents import LlmAgent
from google.adk.tools import google_search

import config
from tools.rag_tools import rag_search
from tools.cost_tools import get_cost_analysis

RAG_INSTRUCTION = """You are an internal knowledge base specialist for GenAI architecture.

The session state key 'decomposition' contains the research decomposition from the manager agent.
Extract TRACK_1_RAG from it and use that as your search query for the rag_search tool.

If decomposition is not yet in state, use the conversation history to infer a good search query.

TASK:
1. Call rag_search with the Track 1 query
2. Synthesize findings into a structured report: patterns found, gaps, recommended internal references
3. Explicitly note what the internal KB does NOT cover so the synthesis agent knows what's missing

OUTPUT: Structured findings tagged with [RAG] prefix for easy identification.
"""

WEB_INSTRUCTION = """You are a market intelligence specialist for GenAI and contact center technology.

The session state key 'decomposition' contains the research decomposition from the manager agent.
Extract TRACK_2_WEB from it and use that as your search query.

TASK:
1. Call google_search with the Track 2 query
2. Search for: (a) production deployments of GenAI in call centers, (b) vendor comparison 2024-2025,
   (c) failure modes and lessons learned, (d) regulatory/compliance considerations
3. Prioritize real deployments over vendor marketing

OUTPUT: Structured findings tagged with [WEB] prefix. Include source recency where available.
"""

COST_INSTRUCTION = """You are a cloud cost and ROI specialist for GenAI deployments.

The session state key 'decomposition' contains the research decomposition from the manager agent.
Extract TRACK_3_COST from it — it contains parameters: monthly_calls, avg_tokens, model_tier.
Parse those values and pass them to get_cost_analysis.

If parameters are not specified, use conservative defaults: monthly_calls=100000, avg_tokens=2500, model_tier=mixed.

TASK:
1. Call get_cost_analysis with the extracted parameters
2. Augment with: (a) typical 12-month cost trajectory as volume scales, (b) hidden costs often missed
   (data labeling, evaluation, guardrails, human-in-loop review), (c) build vs buy comparison,
   (d) break-even timeline vs current IVR/human-agent costs
3. Flag the top 3 cost risks specific to call center GenAI

OUTPUT: Structured findings tagged with [COST] prefix. Include actionable cost controls.
"""


def create_rag_agent() -> LlmAgent:
    return LlmAgent(
        name="rag_agent",
        model=config.SPECIALIST_MODEL,
        instruction=RAG_INSTRUCTION,
        tools=[rag_search],
        output_key="rag_findings",
    )


def create_web_agent() -> LlmAgent:
    return LlmAgent(
        name="web_search_agent",
        model=config.SPECIALIST_MODEL,
        instruction=WEB_INSTRUCTION,
        tools=[google_search],
        output_key="web_findings",
    )


def create_cost_agent() -> LlmAgent:
    return LlmAgent(
        name="cost_analysis_agent",
        model=config.SPECIALIST_MODEL,
        instruction=COST_INSTRUCTION,
        tools=[get_cost_analysis],
        output_key="cost_findings",
    )
