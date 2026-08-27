from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from .config import get_settings
from .database import init_db, get_db, AsyncSessionLocal
from .models import User, Skill, Domain, Gig, Mentor, Company, Interaction
from .schemas import (
    UserCreate, UserOut, Token, SkillOut, DomainOut,
    GigOut, MentorOut, CompanyOut, InteractionCreate, RankedFeed, SkillSelect,
)
from .auth import (
    get_password_hash, verify_password, create_access_token, get_current_user,
)
from .ranking import rank_gigs_for_user, rank_mentors_for_user, rank_companies_for_user
from .seed import seed_taxonomy, seed_demo_data
from .nvidia_client import suggest_skills_from_text

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    async with AsyncSessionLocal() as db:
        skill_map = await seed_taxonomy(db)
        await seed_demo_data(db, skill_map)
    yield


app = FastAPI(
    title=settings.app_name,
    description="SkillBridge POC — skill/opportunity graph matching freelancers to gigs, mentors & companies",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Auth ----------
@app.post("/api/auth/register", response_model=UserOut)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name,
        bio=payload.bio,
        trust_score=0.5,
    )
    db.add(user)
    await db.flush()

    if payload.skill_ids:
        skills = await db.execute(select(Skill).where(Skill.id.in_(payload.skill_ids)))
        user.skills = list(skills.scalars().all())

    await db.refresh(user, attribute_names=["skills"])
    return user


@app.post("/api/auth/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    token = create_access_token({"sub": str(user.id)})
    return Token(access_token=token)


@app.get("/api/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return current_user


@app.post("/api/me/skills", response_model=UserOut)
async def update_my_skills(
    payload: SkillSelect,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    skills = await db.execute(select(Skill).where(Skill.id.in_(payload.skill_ids)))
    current_user.skills = list(skills.scalars().all())
    await db.flush()
    await db.refresh(current_user, attribute_names=["skills"])
    return current_user


# ---------- Taxonomy ----------
@app.get("/api/domains", response_model=List[DomainOut])
async def list_domains(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Domain).order_by(Domain.name))
    return list(result.scalars().all())


@app.get("/api/skills", response_model=List[SkillOut])
async def list_skills(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Skill).order_by(Skill.name))
    return list(result.scalars().all())


# ---------- Ranked feeds ----------
@app.get("/api/feed", response_model=RankedFeed)
async def get_feed(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    gigs_scored = await rank_gigs_for_user(db, current_user, limit=12)
    mentors_scored = await rank_mentors_for_user(db, current_user, limit=6)
    companies_scored = await rank_companies_for_user(db, current_user, limit=6)

    def gig_out(g: Gig, score: float) -> GigOut:
        return GigOut(
            id=g.id,
            title=g.title,
            description=g.description,
            budget_min=g.budget_min,
            budget_max=g.budget_max,
            duration_days=g.duration_days,
            is_boosted=g.is_boosted,
            company=CompanyOut.model_validate(g.company),
            skills=[SkillOut.model_validate(s) for s in g.skills],
            views=g.views,
            applications=g.applications,
            created_at=g.created_at,
            score=round(score, 4),
        )

    def mentor_out(m: Mentor, score: float) -> MentorOut:
        return MentorOut(
            id=m.id,
            full_name=m.full_name,
            bio=m.bio,
            availability=m.availability,
            mentees_helped=m.mentees_helped,
            rating=m.rating,
            hourly_rate=m.hourly_rate,
            skills=[SkillOut.model_validate(s) for s in m.skills],
            score=round(score, 4),
        )

    return RankedFeed(
        gigs=[gig_out(g, s) for g, s in gigs_scored],
        mentors=[mentor_out(m, s) for m, s in mentors_scored],
        companies=[CompanyOut.model_validate(c) for c, _ in companies_scored],
    )


@app.get("/api/gigs", response_model=List[GigOut])
async def list_gigs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    scored = await rank_gigs_for_user(db, current_user, limit=30)
    out = []
    for g, score in scored:
        out.append(
            GigOut(
                id=g.id,
                title=g.title,
                description=g.description,
                budget_min=g.budget_min,
                budget_max=g.budget_max,
                duration_days=g.duration_days,
                is_boosted=g.is_boosted,
                company=CompanyOut.model_validate(g.company),
                skills=[SkillOut.model_validate(s) for s in g.skills],
                views=g.views,
                applications=g.applications,
                created_at=g.created_at,
                score=round(score, 4),
            )
        )
    return out


@app.get("/api/mentors", response_model=List[MentorOut])
async def list_mentors(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    scored = await rank_mentors_for_user(db, current_user, limit=20)
    return [
        MentorOut(
            id=m.id,
            full_name=m.full_name,
            bio=m.bio,
            availability=m.availability,
            mentees_helped=m.mentees_helped,
            rating=m.rating,
            hourly_rate=m.hourly_rate,
            skills=[SkillOut.model_validate(s) for s in m.skills],
            score=round(score, 4),
        )
        for m, score in scored
    ]


@app.get("/api/companies", response_model=List[CompanyOut])
async def list_companies(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Company).order_by(Company.name))
    return list(result.scalars().all())


# ---------- Interactions ----------
@app.post("/api/interactions", status_code=201)
async def log_interaction(
    payload: InteractionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.target_type not in ("gig", "mentor", "company"):
        raise HTTPException(400, "Invalid target_type")
    if payload.interaction_type not in ("view", "save", "apply", "message", "complete", "hired"):
        raise HTTPException(400, "Invalid interaction_type")

    inter = Interaction(
        user_id=current_user.id,
        target_type=payload.target_type,
        target_id=payload.target_id,
        interaction_type=payload.interaction_type,
        weight=1.0,
    )
    db.add(inter)
    current_user.interaction_count += 1

    # Side-effect: bump counters on gigs
    if payload.target_type == "gig":
        result = await db.execute(select(Gig).where(Gig.id == payload.target_id))
        gig = result.scalar_one_or_none()
        if gig:
            if payload.interaction_type == "view":
                gig.views += 1
            elif payload.interaction_type == "apply":
                gig.applications += 1

    return {"ok": True}


# ---------- Optional NVIDIA helper ----------
@app.post("/api/suggest-skills")
async def suggest_skills(
    description: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Skill.name))
    names = list(result.scalars().all())
    suggested = await suggest_skills_from_text(description, names)
    return {"suggested": suggested}


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "app": settings.app_name,
        "nvidia_configured": bool(settings.nvidia_api_key and settings.nvidia_api_key.startswith("nvapi-")),
    }
