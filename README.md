# ✈️ Travel AI Platform

> AI-powered travel assistant with retrieval-augmented generation (RAG), built as a full-stack portfolio project to explore the technical foundations of AI product development.

[![CI](https://github.com/YOUR_USERNAME/travel-ai-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/travel-ai-platform/actions/workflows/ci.yml)

---

## What this is

A production-shaped MVP of an AI travel assistant. Users chat with an AI about trip planning, and can upload their own documents (guides, notes, visa requirements) that the AI grounds its answers in via RAG — not just a ChatGPT wrapper, but a system with real retrieval, streaming, and auth.

Built solo, end-to-end, as a hands-on way to understand what "AI product" actually means at the architecture level — before making product decisions about one.

**[Live demo / screenshots — add yours here]**

---

## Core features

- 🔐 **Auth** — JWT-based registration/login, bcrypt password hashing
- 💬 **Streaming chat** — Server-Sent Events, tokens appear as they generate (not a spinner-then-dump)
- 📎 **RAG (Retrieval-Augmented Generation)** — upload documents, they're chunked, embedded, and semantically searched to ground AI responses in user-specific context
- 🗂️ **Multi-conversation support** — persistent chat history per user
- 🐳 **One-command deploy** — full stack (DB, cache, storage, backend, frontend) via Docker Compose
- ✅ **CI/CD** — automated tests + build verification on every push

---

## Architecture

```
Browser
   │
React (Vite) ── Nginx
   │
FastAPI
   │
┌──────────────────────────┐
│ Auth · Conversations      │
│ AI Gateway (Gemini)       │
│ RAG Pipeline               │
└──────────────────────────┘
   │
PostgreSQL (+pgvector) · Redis · MinIO
   │
Docker Compose · GitHub Actions
```

**Request flow for a chat message with RAG:**

```
User message
   → embedded (gemini-embedding-001)
   → cosine similarity search against user's document chunks (pgvector)
   → top-k relevant chunks injected into system prompt
   → streamed response from Gemini (SSE)
   → both user message + AI response persisted
```

---

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Backend | FastAPI + SQLAlchemy + Alembic | Async-native, auto-generated OpenAPI docs, mature migration tooling |
| Database | PostgreSQL + pgvector | One database for both relational data and vector search — avoids running a separate vector DB for an MVP-scale workload |
| AI provider | Google Gemini (`google-genai` SDK) | Free tier sufficient for portfolio-scale usage; same architecture would swap to OpenAI by changing one service module |
| Frontend | React + Vite + Zustand | Vite over CRA (deprecated); Zustand over Redux for a small app's state surface |
| Auth | JWT + bcrypt | Stateless auth, no session store needed |
| Infra | Docker Compose | Single-command reproducible environment |
| CI | GitHub Actions | Test + lint + build on every push, with a real Postgres service container |

---

## Quick start

```bash
git clone https://github.com/YOUR_USERNAME/travel-ai-platform.git
cd travel-ai-platform

# Add your own Gemini API key (free tier: https://aistudio.google.com/apikey)
cp .env.example .env

docker-compose up --build
```

Then open:
- **App:** http://localhost:3000
- **API docs (Swagger):** http://localhost:8000/docs
- **MinIO console:** http://localhost:9001

---

## Engineering decisions & trade-offs

A few choices worth explaining, since they reflect real product/engineering trade-offs rather than defaults:

**pgvector instead of a dedicated vector database.**
Qdrant/Weaviate/Pinecone are the "obvious" RAG choice, but for an MVP at this scale they're operational overhead without a clear benefit. Postgres already had to be in the stack; pgvector gets vector search for free with one extension and no new service to run, monitor, or back up.

**Streaming responses over simple request/response.**
The first version waited for the full AI response before showing anything — functionally fine, but it reads as "slow" even when latency is identical to a streaming version, because there's no feedback during generation. Switched to SSE so tokens appear as they're generated, matching the UX users already expect from AI chat products.

**Gemini as the AI provider, with an abstraction that doesn't care.**
Started on OpenAI, switched to Gemini's free tier to develop without burning API credits, and hit two unrelated provider-side issues along the way (a new API key format that broke the OpenAI-compatibility shim, and a model being deprecated for new accounts mid-build). The `ai.py` service module is the only place that knows which provider is in use — swapping providers is a config change, not a refactor.

**No separate microservices for a single-developer MVP.**
The original architecture sketch had Intent Router, Prompt Builder, and AI Gateway as distinct boxes. At this scale, those are responsibilities inside one FastAPI service, not separate deployables — splitting them now would add deployment complexity with no corresponding benefit. Worth revisiting if usage or team size actually demanded it.

---

## What I'd build next

- Streaming for the RAG-augmented responses to also show *which* document chunks were retrieved (transparency into what grounded the answer)
- Rate limiting per user (currently unbounded — fine for a portfolio demo, not for anything real)
- Structured evals for the RAG pipeline (retrieval precision/recall on a labeled test set) rather than manual spot-checking
- Prometheus/Grafana for basic observability

---

## Project structure

```
travel-ai-platform/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routers (auth, conversations, documents)
│   │   ├── core/         # config
│   │   ├── db/           # SQLAlchemy engine/session
│   │   ├── models/       # ORM models
│   │   ├── schemas/      # Pydantic request/response schemas
│   │   └── services/     # auth, AI (Gemini), RAG
│   ├── alembic/          # DB migrations
│   ├── tests/            # pytest suite
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/        # Login, Register, Chat
│   │   ├── store/         # Zustand stores
│   │   └── services/      # API client
│   └── Dockerfile
├── .github/workflows/    # CI pipeline
└── docker-compose.yml
```

---

## Running tests

```bash
cd backend
poetry run pytest -v
```

---

*Built by [Your Name] — [LinkedIn] · [Portfolio]*
