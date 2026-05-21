"""Synthesis agent: integrates parallel findings, then self-reflects before final output."""
from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext

import config

SYNTHESIS_INSTRUCTION = """You are a senior GenAI solutions architect producing a final recommendation.

You have access to a tool `get_all_findings` that retrieves the outputs of three parallel research agents.
Call it first to load all research context.

SYNTHESIS PROCESS — follow this exact sequence:

## STEP 1: DRAFT
Produce a structured draft recommendation covering:
- Recommended architecture pattern (with diagram in ASCII or Mermaid)
- Core components and their roles
- Data flow: how a call moves through the system
- Integration points with existing call center infrastructure (CTI, CRM, WFM)
- Build vs buy decision for each component
- Phased rollout (Pilot → Scale → Optimize)

## STEP 2: SELF-CRITIQUE
Challenge your own draft with these questions:
1. **Assumptions**: What assumptions does this draft make that may not hold for this customer?
2. **Missing risks**: What failure modes or edge cases did I not address?
3. **Contradictions**: Do any of the three research tracks contradict each other? Which source wins and why?
4. **Overconfidence**: Where am I recommending something I'm not actually confident about?
5. **Customer fit**: Is this generic advice or does it actually address the specific question asked?

List your critiques explicitly. Do not hide them.

## STEP 3: REVISED RECOMMENDATION
Produce the final recommendation, directly addressing each critique from Step 2.

FORMAT:
```
=== DRAFT ===
[your draft]

=== SELF-CRITIQUE ===
[your honest critique]

=== FINAL RECOMMENDATION ===
[revised, hardened recommendation]

=== CONFIDENCE & CAVEATS ===
[what you're confident about vs. what requires customer-specific validation]
```
"""


def get_all_findings(tool_context: ToolContext) -> dict:
    """Retrieve aggregated findings from all specialist research agents.

    Returns:
        Dictionary with keys: decomposition, rag_findings, web_findings, cost_findings.
    """
    state = tool_context.state
    return {
        "decomposition": state.get("decomposition", "[Manager decomposition not found]"),
        "rag_findings": state.get("rag_findings", "[RAG findings not found]"),
        "web_findings": state.get("web_findings", "[Web findings not found]"),
        "cost_findings": state.get("cost_findings", "[Cost findings not found]"),
    }


def create_synthesis_agent() -> LlmAgent:
    return LlmAgent(
        name="synthesis_agent",
        model=config.ORCHESTRATOR_MODEL,
        instruction=SYNTHESIS_INSTRUCTION,
        tools=[get_all_findings],
    )
