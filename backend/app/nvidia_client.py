"""
Optional NVIDIA NIM client for embeddings / lightweight enrichment.

Embeddings may be used to enrich relevance scores.
Chat models are used only for non-scoring helpers (e.g. skill suggestion text).
All ranking mathematics remain in pure Python (see ranking.py).
"""
from __future__ import annotations

from typing import List, Optional
import httpx
from openai import OpenAI

from .config import get_settings

settings = get_settings()


def _client() -> Optional[OpenAI]:
    if not settings.nvidia_api_key or not settings.nvidia_api_key.startswith("nvapi-"):
        return None
    return OpenAI(
        api_key=settings.nvidia_api_key,
        base_url=settings.nvidia_base_url,
    )


async def get_embeddings(texts: List[str], input_type: str = "query") -> Optional[List[List[float]]]:
    """
    Call NVIDIA embedding endpoint (OpenAI-compatible).
    Returns None if key is missing or call fails — ranking falls back to one-hot.
    """
    client = _client()
    if client is None:
        return None
    try:
        # Some NVIDIA embedding models accept extra body for input_type
        resp = client.embeddings.create(
            model=settings.nvidia_embedding_model,
            input=texts,
            extra_body={"input_type": input_type} if "embed" in settings.nvidia_embedding_model.lower() else {},
        )
        return [d.embedding for d in resp.data]
    except Exception:
        return None


async def suggest_skills_from_text(description: str, available_skills: List[str]) -> List[str]:
    """
    Lightweight helper: ask the chat model to pick relevant skill names from a list.
    This is NOT used in scoring; only for UX suggestions.
    """
    client = _client()
    if client is None:
        return []
    skill_list = ", ".join(available_skills[:80])
    prompt = (
        f"Given this gig or profile description:\n\n{description[:800]}\n\n"
        f"Select up to 5 skill names that best match from this list only:\n{skill_list}\n\n"
        "Reply with a comma-separated list of exact skill names, nothing else."
    )
    try:
        resp = client.chat.completions.create(
            model=settings.nvidia_chat_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.2,
        )
        text = resp.choices[0].message.content or ""
        chosen = [s.strip() for s in text.split(",") if s.strip()]
        # Keep only those that exist in the taxonomy
        available_set = set(available_skills)
        return [c for c in chosen if c in available_set][:5]
    except Exception:
        return []
