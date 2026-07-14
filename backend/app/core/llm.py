"""Optional LLM phrasing layer with a hard grounding guarantee.

The agents in this system compute every fact deterministically from the
database. The LLM's ONLY job is to phrase those already-computed facts in
natural language — it never sees the raw database and never invents numbers.

If ``GROQ_API_KEY`` is not configured (or the call fails), ``phrase`` returns
``None`` and callers fall back to their own template-based wording. The system
is fully functional with no LLM configured.
"""
from __future__ import annotations

import json
import logging

from app.core.config import settings

logger = logging.getLogger("inventory.llm")

# The grounding contract, enforced in the system prompt.
_SYSTEM_PROMPT = (
    "You are a retail business assistant. You will be given a JSON object of "
    "FACTS that were computed from the store's database, and a task. "
    "Write a concise, friendly answer using ONLY those facts. "
    "Never invent numbers, product names, or figures that are not present in "
    "the FACTS. If the facts do not contain the answer, say you don't have "
    "that information. Do not show the raw JSON. Keep it brief."
)


def llm_enabled() -> bool:
    """True when an LLM backend is configured."""
    return bool(settings.GROQ_API_KEY)


def phrase(task: str, facts: dict | list) -> str | None:
    """Ask the LLM to phrase ``facts`` for ``task``. None if unavailable.

    The facts are passed as JSON in the user message; the system prompt forbids
    going beyond them. Any error degrades gracefully to None so the caller can
    use its deterministic template instead.
    """
    if not llm_enabled():
        return None

    try:
        # Imported lazily so the package is an optional dependency.
        from groq import Groq
    except ImportError:
        logger.warning("GROQ_API_KEY set but 'groq' package not installed.")
        return None

    try:
        client = Groq(api_key=settings.GROQ_API_KEY)
        completion = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"TASK: {task}\n\n"
                        f"FACTS (the only information you may use):\n"
                        f"{json.dumps(facts, default=str)}"
                    ),
                },
            ],
            temperature=0.2,
            max_tokens=400,
        )
        return completion.choices[0].message.content
    except Exception as exc:  # noqa: BLE001 — degrade gracefully on any error
        logger.warning("LLM phrasing failed, falling back to template: %s", exc)
        return None
