# SkillBridge POC

**Skill / opportunity graph matching freelancers to gigs, mentors, and companies.**

Based on the *SkillBridge — Design & Infrastructure Plan (POC)*.  
Rule-based ranking in pure Python (cosine similarity + weighted formula).  
Optional NVIDIA NIM embeddings / chat for enrichment only — never for scoring math.

## Stack

| Layer | Choice |
|-------|--------|
| Backend | FastAPI + SQLAlchemy (async) + SQLite |
| Ranking | Native NumPy / Python (`ranking.py`) |
| Optional AI | NVIDIA NIM (OpenAI-compatible) for skill suggestions |
| Frontend | React 19 + TypeScript + Vite |
| Auth | JWT (python-jose) |

## Quick start

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env .env             # or edit backend/.env — set NVIDIA_API_KEY if you have one
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://127.0.0.1:8000/docs  
Health: http://127.0.0.1:8000/api/health

Demo accounts (seeded):

| Email | Password |
|-------|----------|
| alex@example.com | demo1234 |
| sam@example.com | demo1234 |
| jordan@example.com | demo1234 |

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173  
Vite proxies `/api` → backend.

### 3. Environment variables

All keys live in `.env` (root) and `backend/.env`:

- `APP_NAME`, `SECRET_KEY`, `DATABASE_URL`
- `NVIDIA_API_KEY` — from [build.nvidia.com/nim](https://build.nvidia.com/nim)
- `NVIDIA_BASE_URL`, `NVIDIA_EMBEDDING_MODEL`, `NVIDIA_CHAT_MODEL`
- Ranking weights `W_*`

Ranking works **without** an NVIDIA key (one-hot taxonomy vectors).  
With a key, `/api/suggest-skills` can call the chat model for UX helpers.

## Architecture notes (aligned with plan)

- **Skills taxonomy** seeded once (`Domain → Skill`).
- **Entities**: User, Gig, Mentor, Company + Interaction log.
- **Score formula** (pure Python):

  ```
  score = w1·Relevance + w2·Trust + w3·Authority
        + w4·Freshness + w5·Engagement − penalty·SpamRisk
  ```

  Relevance = cosine similarity of one-hot skill vectors.  
  Boosted gigs interleave at ~1-in-6 slots (never mixed into organic rank).

- Cold-start: popularity blend when `interaction_count < N`.
- Trust rules table (verified company, new accounts) — lightweight as specified.

## Project layout

```
skillbridge-poc/
├── .env
├── README.md
├── backend/
│   ├── .env
│   ├── requirements.txt
│   └── app/
│       ├── main.py          # FastAPI routes
│       ├── models.py        # SQLAlchemy models
│       ├── schemas.py
│       ├── ranking.py       # Pure-Python scoring
│       ├── nvidia_client.py # Optional NIM helpers
│       ├── auth.py
│       ├── seed.py
│       └── ...
└── frontend/
    ├── package.json
    └── src/
        ├── App.tsx
        ├── pages/
        ├── components/
        └── lib/
```

## Production upgrades (from plan)

- Swap SQLite → Supabase/Neon Postgres  
- Add Neo4j Aura Free for multi-hop traversal  
- Milvus Lite or pgvector for embeddings  
- Nightly job to rebuild vectors from Postgres (source of truth)

## License

POC / demo — use freely for evaluation.
