"""Seed taxonomy + sample entities for the SkillBridge POC."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .models import Domain, Skill, User, Company, Gig, Mentor, user_skills, gig_skills, mentor_skills
from .auth import get_password_hash


TAXONOMY = {
    "Engineering": [
        "Backend",
        "Frontend",
        "Full-Stack",
        "DevOps",
        "Mobile",
        "Data Engineering",
        "Postgres",
        "MongoDB",
        "Redis",
        "Python",
        "TypeScript",
        "React",
        "Node.js",
        "FastAPI",
        "Docker",
        "Kubernetes",
        "AWS",
        "GraphQL",
    ],
    "Design": [
        "UI Design",
        "UX Research",
        "Product Design",
        "Figma",
        "Design Systems",
        "Prototyping",
        "Motion Design",
        "Brand Identity",
    ],
    "Data & AI": [
        "Machine Learning",
        "Deep Learning",
        "NLP",
        "Computer Vision",
        "MLOps",
        "Data Analysis",
        "SQL",
        "PyTorch",
        "TensorFlow",
        "Prompt Engineering",
    ],
    "Product & Business": [
        "Product Management",
        "Agile",
        "Growth",
        "Analytics",
        "Technical Writing",
        "Project Management",
    ],
}


async def seed_taxonomy(db: AsyncSession) -> dict[str, int]:
    """Create domains + skills. Returns name → id map."""
    name_to_id: dict[str, int] = {}
    for domain_name, skills in TAXONOMY.items():
        result = await db.execute(select(Domain).where(Domain.name == domain_name))
        domain = result.scalar_one_or_none()
        if not domain:
            domain = Domain(name=domain_name, description=f"{domain_name} domain")
            db.add(domain)
            await db.flush()
        for skill_name in skills:
            result = await db.execute(
                select(Skill).where(Skill.name == skill_name, Skill.domain_id == domain.id)
            )
            skill = result.scalar_one_or_none()
            if not skill:
                skill = Skill(name=skill_name, domain_id=domain.id)
                db.add(skill)
                await db.flush()
            name_to_id[skill_name] = skill.id
    await db.commit()
    return name_to_id


async def seed_demo_data(db: AsyncSession, skill_map: dict[str, int]):
    # Demo users
    users_data = [
        {
            "email": "alex@example.com",
            "password": "demo1234",
            "full_name": "Alex Rivera",
            "bio": "Backend engineer focused on Python & Postgres. 5 years freelancing.",
            "skills": ["Python", "Postgres", "FastAPI", "Docker", "Backend"],
        },
        {
            "email": "sam@example.com",
            "password": "demo1234",
            "full_name": "Sam Chen",
            "bio": "Full-stack React + Node specialist. Design-minded.",
            "skills": ["React", "TypeScript", "Node.js", "Frontend", "Figma"],
        },
        {
            "email": "jordan@example.com",
            "password": "demo1234",
            "full_name": "Jordan Lee",
            "bio": "ML engineer building production NLP systems.",
            "skills": ["Machine Learning", "NLP", "Python", "PyTorch", "MLOps"],
        },
    ]

    for ud in users_data:
        result = await db.execute(select(User).where(User.email == ud["email"]))
        if result.scalar_one_or_none():
            continue
        user = User(
            email=ud["email"],
            hashed_password=get_password_hash(ud["password"]),
            full_name=ud["full_name"],
            bio=ud["bio"],
            trust_score=0.75,
            is_verified=True,
            interaction_count=3,
        )
        db.add(user)
        await db.flush()
        for sname in ud["skills"]:
            sid = skill_map.get(sname)
            if sid:
                await db.execute(
                    user_skills.insert().values(user_id=user.id, skill_id=sid, proficiency="expert")
                )

    # Companies
    companies_data = [
        {"name": "Nimbus Labs", "description": "AI infrastructure startup", "verified": True, "trust": 0.9},
        {"name": "PixelForge", "description": "Product design studio", "verified": True, "trust": 0.85},
        {"name": "DataNest", "description": "Analytics platform for mid-market", "verified": False, "trust": 0.55},
        {"name": "CloudForge Inc", "description": "DevOps tooling company", "verified": True, "trust": 0.8},
    ]
    company_ids = {}
    for cd in companies_data:
        result = await db.execute(select(Company).where(Company.name == cd["name"]))
        c = result.scalar_one_or_none()
        if not c:
            c = Company(
                name=cd["name"],
                description=cd["description"],
                is_verified=cd["verified"],
                trust_score=cd["trust"],
                website=f"https://{cd['name'].lower().replace(' ', '')}.example.com",
            )
            db.add(c)
            await db.flush()
        company_ids[cd["name"]] = c.id

    # Gigs
    gigs_data = [
        {
            "title": "Build FastAPI microservice for user auth",
            "description": "Need a secure JWT-based auth service with Postgres, rate limiting, and Docker packaging. 2-week engagement.",
            "budget_min": 2500,
            "budget_max": 4000,
            "duration_days": 14,
            "company": "Nimbus Labs",
            "skills": ["Python", "FastAPI", "Postgres", "Docker", "Backend"],
            "boosted": False,
        },
        {
            "title": "React dashboard redesign with design system",
            "description": "Redesign internal analytics dashboard using existing Figma design system. TypeScript + React.",
            "budget_min": 3000,
            "budget_max": 5500,
            "duration_days": 21,
            "company": "PixelForge",
            "skills": ["React", "TypeScript", "Frontend", "Figma", "Design Systems"],
            "boosted": True,
        },
        {
            "title": "NLP pipeline for support ticket classification",
            "description": "Train and deploy a multi-label classifier for support tickets. PyTorch preferred. MLOps basics required.",
            "budget_min": 5000,
            "budget_max": 8000,
            "duration_days": 30,
            "company": "DataNest",
            "skills": ["NLP", "Machine Learning", "Python", "PyTorch", "MLOps"],
            "boosted": False,
        },
        {
            "title": "Kubernetes cost-optimization audit",
            "description": "Review existing EKS clusters, propose rightsizing and autoscaling improvements. Short engagement.",
            "budget_min": 1800,
            "budget_max": 3200,
            "duration_days": 10,
            "company": "CloudForge Inc",
            "skills": ["Kubernetes", "AWS", "DevOps", "Docker"],
            "boosted": False,
        },
        {
            "title": "Full-stack MVP: marketplace for local services",
            "description": "Next.js + Node + Postgres MVP. Need someone who can own both ends and ship fast.",
            "budget_min": 6000,
            "budget_max": 10000,
            "duration_days": 45,
            "company": "Nimbus Labs",
            "skills": ["Full-Stack", "React", "Node.js", "Postgres", "TypeScript"],
            "boosted": True,
        },
        {
            "title": "UX research + prototype for mobile onboarding",
            "description": "Run 5 user interviews and deliver interactive Figma prototype for mobile onboarding flow.",
            "budget_min": 2000,
            "budget_max": 3500,
            "duration_days": 14,
            "company": "PixelForge",
            "skills": ["UX Research", "Prototyping", "Figma", "Product Design"],
            "boosted": False,
        },
    ]

    for gd in gigs_data:
        result = await db.execute(select(Gig).where(Gig.title == gd["title"]))
        if result.scalar_one_or_none():
            continue
        gig = Gig(
            title=gd["title"],
            description=gd["description"],
            budget_min=gd["budget_min"],
            budget_max=gd["budget_max"],
            duration_days=gd["duration_days"],
            is_boosted=gd["boosted"],
            company_id=company_ids[gd["company"]],
            views=20 + hash(gd["title"]) % 80,
            applications=2 + hash(gd["title"]) % 12,
        )
        db.add(gig)
        await db.flush()
        for sname in gd["skills"]:
            sid = skill_map.get(sname)
            if sid:
                await db.execute(
                    gig_skills.insert().values(gig_id=gig.id, skill_id=sid, required_level="intermediate")
                )

    # Mentors
    mentors_data = [
        {
            "full_name": "Priya Sharma",
            "bio": "Staff backend engineer. Mentored 40+ engineers on system design & Python.",
            "skills": ["Backend", "Python", "Postgres", "FastAPI"],
            "mentees": 42,
            "rating": 4.9,
            "rate": 120,
        },
        {
            "full_name": "Marcus Okonkwo",
            "bio": "Design lead who ships design systems. Ex-FAANG.",
            "skills": ["UI Design", "Design Systems", "Figma", "Product Design"],
            "mentees": 28,
            "rating": 4.8,
            "rate": 110,
        },
        {
            "full_name": "Elena Volkov",
            "bio": "ML research engineer. Specialises in NLP productionisation.",
            "skills": ["Machine Learning", "NLP", "PyTorch", "MLOps"],
            "mentees": 19,
            "rating": 4.7,
            "rate": 130,
        },
        {
            "full_name": "Chris Tanaka",
            "bio": "DevOps consultant. Kubernetes, AWS, cost control.",
            "skills": ["DevOps", "Kubernetes", "AWS", "Docker"],
            "mentees": 35,
            "rating": 4.85,
            "rate": 115,
        },
    ]

    for md in mentors_data:
        result = await db.execute(select(Mentor).where(Mentor.full_name == md["full_name"]))
        if result.scalar_one_or_none():
            continue
        m = Mentor(
            full_name=md["full_name"],
            bio=md["bio"],
            availability="available",
            mentees_helped=md["mentees"],
            rating=md["rating"],
            hourly_rate=md["rate"],
        )
        db.add(m)
        await db.flush()
        for sname in md["skills"]:
            sid = skill_map.get(sname)
            if sid:
                await db.execute(
                    mentor_skills.insert().values(mentor_id=m.id, skill_id=sid)
                )

    await db.commit()
