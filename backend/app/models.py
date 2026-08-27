from datetime import datetime, timezone
from sqlalchemy import (
    String, Integer, Float, Boolean, Text, DateTime, ForeignKey, Table, Column, Enum as SAEnum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base
import enum


class Proficiency(str, enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    expert = "expert"


class InteractionType(str, enum.Enum):
    view = "view"
    save = "save"
    apply = "apply"
    message = "message"
    complete = "complete"
    hired = "hired"


# Association tables
user_skills = Table(
    "user_skills",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("skill_id", ForeignKey("skills.id"), primary_key=True),
    Column("proficiency", String(20), default="intermediate"),
)

gig_skills = Table(
    "gig_skills",
    Base.metadata,
    Column("gig_id", ForeignKey("gigs.id"), primary_key=True),
    Column("skill_id", ForeignKey("skills.id"), primary_key=True),
    Column("required_level", String(20), default="intermediate"),
)

mentor_skills = Table(
    "mentor_skills",
    Base.metadata,
    Column("mentor_id", ForeignKey("mentors.id"), primary_key=True),
    Column("skill_id", ForeignKey("skills.id"), primary_key=True),
)


class Domain(Base):
    __tablename__ = "domains"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    skills: Mapped[list["Skill"]] = relationship(back_populates="domain")


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    domain_id: Mapped[int] = mapped_column(ForeignKey("domains.id"))
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("skills.id"), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    domain: Mapped["Domain"] = relationship(back_populates="skills")
    parent: Mapped["Skill | None"] = relationship(remote_side=[id])


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(150))
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    trust_score: Mapped[float] = mapped_column(Float, default=0.5)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    interaction_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    skills: Mapped[list["Skill"]] = relationship(secondary=user_skills)
    interactions: Mapped[list["Interaction"]] = relationship(back_populates="user")


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    trust_score: Mapped[float] = mapped_column(Float, default=0.6)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    gigs: Mapped[list["Gig"]] = relationship(back_populates="company")


class Gig(Base):
    __tablename__ = "gigs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    budget_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    budget_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    duration_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_boosted: Mapped[bool] = mapped_column(Boolean, default=False)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    views: Mapped[int] = mapped_column(Integer, default=0)
    applications: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    company: Mapped["Company"] = relationship(back_populates="gigs")
    skills: Mapped[list["Skill"]] = relationship(secondary=gig_skills)


class Mentor(Base):
    __tablename__ = "mentors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(150))
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    availability: Mapped[str] = mapped_column(String(50), default="available")  # available / limited / unavailable
    mentees_helped: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[float] = mapped_column(Float, default=4.5)
    hourly_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    skills: Mapped[list["Skill"]] = relationship(secondary=mentor_skills)


class Interaction(Base):
    __tablename__ = "interactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    target_type: Mapped[str] = mapped_column(String(20))  # gig / mentor / company
    target_id: Mapped[int] = mapped_column(Integer)
    interaction_type: Mapped[str] = mapped_column(String(20))
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship(back_populates="interactions")
