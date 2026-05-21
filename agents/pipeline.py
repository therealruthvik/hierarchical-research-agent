"""Assembles the full hierarchical pipeline. No clients instantiated here."""
from google.adk.agents import ParallelAgent, SequentialAgent

from agents.manager import create_manager_agent
from agents.specialists import create_cost_agent, create_rag_agent, create_web_agent
from agents.synthesis import create_synthesis_agent


def build_pipeline() -> SequentialAgent:
    """
    Pipeline topology:

        SequentialAgent
        ├── manager_agent          → state["decomposition"]
        ├── ParallelAgent
        │   ├── rag_agent          → state["rag_findings"]
        │   ├── web_search_agent   → state["web_findings"]
        │   └── cost_analysis_agent→ state["cost_findings"]
        └── synthesis_agent        → final response (reads all state keys)
    """
    parallel_research = ParallelAgent(
        name="parallel_research",
        sub_agents=[
            create_rag_agent(),
            create_web_agent(),
            create_cost_agent(),
        ],
    )

    return SequentialAgent(
        name="research_pipeline",
        sub_agents=[
            create_manager_agent(),
            parallel_research,
            create_synthesis_agent(),
        ],
    )
