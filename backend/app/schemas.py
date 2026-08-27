from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List


# ---------- Auth ----------
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str
    bio: Optional[str] = None
    skill_ids: List[int] = []


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    bio: Optional[str]
    trust_score: float
    is_verified: bool
    interaction_count: int
    created_at: datetime
    skills: List["SkillOut"] = []

    class Config:
        from_attributes = True


# ---------- Taxonomy ----------
class DomainOut(BaseModel):
    id: int
    name: str
    description: Optional[str]

    class Config:
        from_attributes = True


class SkillOut(BaseModel):
    id: int
    name: str
    domain_id: int
    parent_id: Optional[int]
    description: Optional[str]

    class Config:
        from_attributes = True


# ---------- Company / Gig / Mentor ----------
class CompanyOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    website: Optional[str]
    is_verified: bool
    trust_score: float

    class Config:
        from_attributes = True


class GigOut(BaseModel):
    id: int
    title: str
    description: str
    budget_min: Optional[float]
    budget_max: Optional[float]
    duration_days: Optional[int]
    is_boosted: bool
    company: CompanyOut
    skills: List[SkillOut] = []
    views: int
    applications: int
    created_at: datetime
    score: Optional[float] = None  # ranking score when returned in feed

    class Config:
        from_attributes = True


class MentorOut(BaseModel):
    id: int
    full_name: str
    bio: Optional[str]
    availability: str
    mentees_helped: int
    rating: float
    hourly_rate: Optional[float]
    skills: List[SkillOut] = []
    score: Optional[float] = None

    class Config:
        from_attributes = True


class InteractionCreate(BaseModel):
    target_type: str  # gig | mentor | company
    target_id: int
    interaction_type: str  # view | save | apply | message | complete | hired


class RankedFeed(BaseModel):
    gigs: List[GigOut]
    mentors: List[MentorOut]
    companies: List[CompanyOut]


class SkillSelect(BaseModel):
    skill_ids: List[int]
