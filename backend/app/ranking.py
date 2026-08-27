"""
Pure-Python ranking engine for SkillBridge POC.

All mathematical formulas (cosine similarity, weighted score, recency decay,
trust multipliers) execute in native Python / NumPy. No LLM is used for scoring.
NVIDIA embeddings are optional and only enrich the relevance term when the API
key is present; the core formula remains deterministic and auditable.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Sequence, Dict, List, Optional, Any

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from .models import User, Gig, Mentor, Company, Skill, Interaction
from .config import get_settings

settings = get_settings()

# Explicit proficiency → weight
PROF_WEIGHT = {
    "beginner": 0.4,
    "intermediate": 0.7,
    "expert": 1.0,
}


def _one_hot_skill_vector(
    skill_ids: Sequence[int],
    all_skill_ids: Sequence[int],
    proficiency_map: Optional[Dict[int, str]] = None,
) -> np.ndarray:
    """Create a weighted one-hot vector over the full skill taxonomy."""
    idx = {sid: i for i, sid in enumerate(all_skill_ids)}
    vec = np.zeros(len(all_skill_ids), dtype=np.float64)
    for sid in skill_ids:
        if sid in idx:
            w = PROF_WEIGHT.get((proficiency_map or {}).get(sid, "intermediate"), 0.7)
            vec[idx[sid]] = w
    return vec


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Native cosine similarity. Returns 0.0 on zero vectors."""
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na < 1e-12 or nb < 1e-12:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def recency_factor(days_since: float, lam: float = 0.05) -> float:
    """Exponential decay: e^(-λ · days). Pure Python math."""
    return math.exp(-lam * max(0.0, days_since))


def edge_weight(
    explicit_base: float,
    implicit_score: float,
    trust_multiplier: float,
    days_since: float,
) -> float:
    """
    edge_weight = 0.5·explicit + 0.3·implicit·trust + 0.2·recency
    Exactly as specified in the Design Plan §3.
    """
    r = recency_factor(days_since)
    return (
        0.5 * explicit_base
        + 0.3 * implicit_score * trust_multiplier
        + 0.2 * r
    )


def compute_score(
    relevance: float,
    trust: float,
    authority: float,
    freshness: float,
    engagement: float,
    spam_risk: float = 0.0,
    weights: Optional[Dict[str, float]] = None,
) -> float:
    """
    score = w1·Rel + w2·Trust + w3·Auth + w4·Fresh + w5·Eng − penalty·Spam
    All arithmetic in native Python.
    """
    w = weights or {
        "relevance": settings.w_relevance,
        "trust": settings.w_trust,
        "authority": settings.w_authority,
        "freshness": settings.w_freshness,
        "engagement": settings.w_engagement,
        "spam": settings.spam_penalty,
    }
    raw = (
        w["relevance"] * relevance
        + w["trust"] * trust
        + w["authority"] * authority
        + w["freshness"] * freshness
        + w["engagement"] * engagement
        - w["spam"] * spam_risk
    )
    return max(0.0, min(1.0, raw))


async def _load_all_skill_ids(db: AsyncSession) -> List[int]:
    result = await db.execute(select(Skill.id).order_by(Skill.id))
    return list(result.scalars().all())


async def get_user_skill_vector(
    db: AsyncSession,
    user: User,
    all_skill_ids: List[int],
) -> np.ndarray:
    """Build long-term skill vector from explicit skills (one-hot + proficiency)."""
    # For POC we treat all attached skills as intermediate unless we store proficiency.
    skill_ids = [s.id for s in user.skills]
    return _one_hot_skill_vector(skill_ids, all_skill_ids)


async def rank_gigs_for_user(
    db: AsyncSession,
    user: User,
    limit: int = 20,
) -> List[tuple[Gig, float]]:
    """
    Rank gigs using the plan formula.
    Boosted gigs are ranked separately and interleaved at 1-in-6 slots.
    """
    all_skill_ids = await _load_all_skill_ids(db)
    user_vec = await get_user_skill_vector(db, user, all_skill_ids)

    result = await db.execute(
        select(Gig)
        .options(selectinload(Gig.skills), selectinload(Gig.company))
        .order_by(Gig.created_at.desc())
    )
    gigs = list(result.scalars().all())

    now = datetime.now(timezone.utc)
    scored: List[tuple[Gig, float]] = []
    boosted: List[tuple[Gig, float]] = []

    for gig in gigs:
        gig_skill_ids = [s.id for s in gig.skills]
        gig_vec = _one_hot_skill_vector(gig_skill_ids, all_skill_ids)
        relevance = cosine_similarity(user_vec, gig_vec)

        # Cold-start fallback
        if user.interaction_count < settings.cold_start_interactions:
            # Blend popularity
            pop = min(1.0, (gig.applications + gig.views * 0.1) / 50.0)
            relevance = 0.6 * relevance + 0.4 * pop

        trust = gig.company.trust_score if gig.company else 0.5
        authority = 0.5  # placeholder; could use company history
        days = (now - gig.created_at).total_seconds() / 86400.0 if gig.created_at else 30.0
        freshness = recency_factor(days, lam=0.03)
        engagement = min(1.0, (gig.applications * 2 + gig.views * 0.05) / 30.0)
        spam_risk = 0.0  # rules table would raise this

        score = compute_score(relevance, trust, authority, freshness, engagement, spam_risk)

        if gig.is_boosted:
            boosted.append((gig, score))
        else:
            scored.append((gig, score))

    # Sort organic by score desc
    scored.sort(key=lambda x: x[1], reverse=True)
    boosted.sort(key=lambda x: x[1], reverse=True)

    # Interleave: every 6th slot is a boosted item if available
    final: List[tuple[Gig, float]] = []
    bi = 0
    for i, item in enumerate(scored):
        if (i + 1) % 6 == 0 and bi < len(boosted):
            final.append(boosted[bi])
            bi += 1
        final.append(item)
    # Append remaining boosted
    while bi < len(boosted):
        final.append(boosted[bi])
        bi += 1

    return final[:limit]


async def rank_mentors_for_user(
    db: AsyncSession,
    user: User,
    limit: int = 10,
) -> List[tuple[Mentor, float]]:
    all_skill_ids = await _load_all_skill_ids(db)
    user_vec = await get_user_skill_vector(db, user, all_skill_ids)

    result = await db.execute(
        select(Mentor).options(selectinload(Mentor.skills))
    )
    mentors = list(result.scalars().all())

    scored: List[tuple[Mentor, float]] = []
    for m in mentors:
        m_skill_ids = [s.id for s in m.skills]
        m_vec = _one_hot_skill_vector(m_skill_ids, all_skill_ids)
        relevance = cosine_similarity(user_vec, m_vec)
        authority = min(1.0, m.mentees_helped / 20.0) * (m.rating / 5.0)
        trust = 0.7 if m.availability == "available" else 0.4
        freshness = 0.8  # mentors change slowly
        engagement = min(1.0, m.mentees_helped / 15.0)
        score = compute_score(relevance, trust, authority, freshness, engagement)
        scored.append((m, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:limit]


async def rank_companies_for_user(
    db: AsyncSession,
    user: User,
    limit: int = 10,
) -> List[tuple[Company, float]]:
    # Simple trust + verification ranking for POC; relevance via shared gigs later
    result = await db.execute(select(Company))
    companies = list(result.scalars().all())

    scored = []
    for c in companies:
        relevance = 0.5  # neutral without deeper graph
        trust = c.trust_score
        authority = 0.8 if c.is_verified else 0.4
        freshness = 0.7
        engagement = 0.5
        score = compute_score(relevance, trust, authority, freshness, engagement)
        scored.append((c, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:limit]
