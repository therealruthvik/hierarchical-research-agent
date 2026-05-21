"""Entry point. Runner and session service are lazy-initialized inside run()."""
from __future__ import annotations

import asyncio
import os

from dotenv import load_dotenv

load_dotenv()

import config  # noqa: E402 — must load .env before config reads os.environ

# Force-set Vertex AI backend before any ADK/genai import.
# load_dotenv() populates os.environ but ADK reads these at SDK init time.
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "true")
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", config.PROJECT_ID)
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", config.LOCATION)


async def run(question: str) -> str:
    # Lazy imports — no cloud clients at module load / cold-start
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types

    from agents.pipeline import build_pipeline

    session_service = InMemorySessionService()
    pipeline = build_pipeline()

    runner = Runner(
        agent=pipeline,
        app_name=config.APP_NAME,
        session_service=session_service,
    )

    session = await session_service.create_session(
        app_name=config.APP_NAME,
        user_id="research_user",
    )

    message = types.Content(
        role="user",
        parts=[types.Part(text=question)],
    )

    final_response = ""
    # Collect last final_response — SequentialAgent emits one per sub-agent.
    # Breaking early exits before synthesis runs. Let generator exhaust naturally
    # to avoid GeneratorExit → OTel ContextVar detach crash on Python 3.14.
    async for event in runner.run_async(
        user_id="research_user",
        session_id=session.id,
        new_message=message,
    ):
        if event.author:
            print(f"[{event.author}] ", end="", flush=True)
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response = event.content.parts[0].text
                print(f"✓ final response ({len(final_response)} chars)")

    return final_response


if __name__ == "__main__":
    question = os.environ.get(
        "RESEARCH_QUESTION",
        "How should we architect GenAI for our Customer Care at Starbucks?",
    )
    print(f"Question: {question}\n{'='*60}\n")
    result = asyncio.run(run(question))
    print(result)
