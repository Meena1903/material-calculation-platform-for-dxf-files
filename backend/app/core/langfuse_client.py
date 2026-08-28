"""Langfuse LLM Observability Client for BuildIQ AI Takeoff Engine.

Provides a single, globally shared Langfuse client for tracing every
NVIDIA NIM vision inference request:
  - Prompt text sent to the model
  - Raw model response content
  - Token usage (prompt, completion, total)
  - Latency in seconds
  - Errors and fallback reasons
  - Model name, temperature, max_tokens parameters

All NIM calls are wrapped with:
  - A Langfuse Trace  (one per pipeline/upload run)
  - A Langfuse Generation (one per model inference call)
  - Observation metadata (crop name, image size, project title)
"""

import time
from typing import Optional, Dict, Any

from backend.app.core.config import settings
from backend.app.core.logging_config import nim_logger

# ── Langfuse client initialisation ────────────────────────────────────────────
_langfuse_client = None
_langfuse_available = False


def _init_langfuse():
    """Lazily initialise the Langfuse client once on first use."""
    global _langfuse_client, _langfuse_available
    if _langfuse_client is not None:
        return

    if not settings.LANGFUSE_SECRET_KEY or not settings.LANGFUSE_PUBLIC_KEY:
        nim_logger.warning(
            "[LANGFUSE INIT] LANGFUSE_SECRET_KEY / LANGFUSE_PUBLIC_KEY not set in .env. "
            "LLM observability will be disabled."
        )
        _langfuse_available = False
        return

    try:
        from langfuse import Langfuse  # noqa: PLC0415

        _langfuse_client = Langfuse(
            secret_key=settings.LANGFUSE_SECRET_KEY,
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            host=settings.LANGFUSE_BASE_URL,
        )
        _langfuse_available = True
        nim_logger.info(
            f"[LANGFUSE INIT] Langfuse client initialised. "
            f"Host: {settings.LANGFUSE_BASE_URL} | "
            f"Public key: {settings.LANGFUSE_PUBLIC_KEY[:12]}..."
        )
    except ImportError:
        nim_logger.warning(
            "[LANGFUSE INIT] langfuse package not installed. Run: pip install langfuse>=2.36.0"
        )
        _langfuse_available = False
    except Exception as exc:
        nim_logger.error(f"[LANGFUSE INIT ERROR] Failed to initialise Langfuse client: {exc}")
        _langfuse_available = False


def get_langfuse():
    """Return the shared Langfuse client (or None if unavailable)."""
    _init_langfuse()
    return _langfuse_client if _langfuse_available else None


# ── Public tracing helpers ─────────────────────────────────────────────────────

def create_trace(
    name: str,
    session_id: Optional[str] = None,
    user_id: Optional[str] = "buildiq-system",
    metadata: Optional[Dict[str, Any]] = None,
):
    """
    Create a new Langfuse Trace for one pipeline/upload run.

    Returns a Langfuse Trace object (or None if Langfuse is unavailable).
    The Trace should be passed down to track_nim_generation() so all
    NIM calls within the same upload share the same trace.

    Usage:
        trace = create_trace("upload-run", session_id=request_id, metadata={"project": title})
    """
    lf = get_langfuse()
    if lf is None:
        return None
    try:
        trace = lf.trace(
            name=name,
            session_id=session_id,
            user_id=user_id,
            metadata=metadata or {},
        )
        nim_logger.info(
            f"[LANGFUSE TRACE CREATED] name='{name}' | trace_id='{trace.id}' | "
            f"session_id='{session_id}'"
        )
        return trace
    except Exception as exc:
        nim_logger.error(f"[LANGFUSE TRACE ERROR] Could not create trace: {exc}")
        return None


def track_nim_generation(
    *,
    trace,                        # Langfuse Trace object (from create_trace)
    crop_name: str,               # e.g. "schedule_table"
    model: str,                   # e.g. "meta/llama-3.2-90b-vision-instruct"
    prompt_text: str,             # The system prompt sent to the model
    image_size_kb: float,         # Approx base64 decoded image size in KB
    temperature: float,
    max_tokens: int,
    start_time: float,            # time.time() before the HTTP call
    end_time: float,              # time.time() after the HTTP call
    response_text: Optional[str], # Raw LLM output content (or None on error)
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    total_tokens: int = 0,
    success: bool = True,
    error_reason: Optional[str] = None,
    fallback_used: bool = False,
):
    """
    Log a single NVIDIA NIM vision inference call as a Langfuse Generation.

    This records:
      - The prompt and image metadata sent to the model
      - The raw model output received
      - Token usage (prompt / completion / total)
      - Wall-clock latency
      - Whether the call succeeded or fell back to ground truth
      - Model parameters (temperature, max_tokens)

    A Generation is the Langfuse primitive for one model I/O round-trip.
    It appears as a child span under the parent Trace in the Langfuse dashboard.
    """
    if trace is None:
        return  # Langfuse not configured — skip silently

    latency_s = round(end_time - start_time, 3)

    try:
        generation = trace.generation(
            name=f"nim-vision-{crop_name}",
            model=model,
            model_parameters={
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            input={
                "system_prompt": prompt_text,
                "image_crop": crop_name,
                "image_size_kb": image_size_kb,
            },
            output=response_text or error_reason or "NO_OUTPUT",
            usage={
                "input": prompt_tokens,
                "output": completion_tokens,
                "total": total_tokens,
                "unit": "TOKENS",
            },
            metadata={
                "success": success,
                "fallback_used": fallback_used,
                "error_reason": error_reason,
                "latency_seconds": latency_s,
            },
            level="DEFAULT" if success else "WARNING",
        )
        nim_logger.info(
            f"[LANGFUSE GENERATION LOGGED] crop='{crop_name}' | model='{model}' | "
            f"latency={latency_s}s | tokens(in={prompt_tokens}, out={completion_tokens}) | "
            f"success={success} | fallback={fallback_used} | generation_id='{generation.id}'"
        )
    except Exception as exc:
        nim_logger.error(f"[LANGFUSE GENERATION ERROR] Failed to log generation to Langfuse: {exc}")


def flush():
    """Flush any buffered Langfuse events to the cloud (call on app shutdown)."""
    lf = get_langfuse()
    if lf is not None:
        try:
            lf.flush()
            nim_logger.info("[LANGFUSE FLUSH] All buffered events flushed to Langfuse cloud.")
        except Exception as exc:
            nim_logger.error(f"[LANGFUSE FLUSH ERROR] {exc}")
