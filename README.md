# DocChat — Chat with any PDF

A stunning RAG demo app that lets you upload PDFs, ask questions in plain English, and get AI-powered answers with highlighted source passages. Built on **[Rivestack](https://rivestack.com)** (managed PostgreSQL + pgvector).

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/template/new?referralCode=rivestack)
![Powered by Rivestack](https://img.shields.io/badge/Powered%20by-Rivestack-blue)

## Features

- **Upload PDFs** with real-time progress tracking (parsing, chunking, embedding)
- **Ask questions** about your documents in natural language
- **Source highlights** — click a source badge to see the exact passage highlighted in the PDF
- **Split-screen UI** — PDF viewer on the left, chat on the right
- **Conversation memory** — follow-up questions understand context
- **One-click deploy** to Railway via GitHub Actions

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Nuxt.js + shadcn-vue + Tailwind CSS |
| Backend | Python + FastAPI |
| Database | [Rivestack](https://rivestack.com) (PostgreSQL + pgvector) |
| Embeddings | OpenAI `text-embedding-3-small` |
| LLM | OpenAI `gpt-4o-mini` |
| PDF Parsing | PyMuPDF |
| Deploy | [Railway](https://railway.com?referralCode=rivestack) + GitHub Actions |

---

## Deploy to Railway (Recommended)

The fastest way to get DocChat running in production.

### Step 1: Get your services ready

1. **Rivestack database** — Sign up at [rivestack.com](https://rivestack.com) and create a PostgreSQL database with pgvector enabled. Copy your connection string.
2. **OpenAI API key** — Get one at [platform.openai.com](https://platform.openai.com)
3. **Railway account** — Sign up at [railway.com](https://railway.com?referralCode=rivestack)

### Step 2: Set up Railway project

1. Go to [railway.com/new](https://railway.com/new?referralCode=rivestack) and create a new project
2. Click **"Deploy from GitHub Repo"** and select this repository
3. Railway will detect two services from the monorepo. Create two services:
   - **backend** — set root directory to `/backend`
   - **frontend** — set root directory to `/frontend`

### Step 3: Configure environment variables

In the Railway dashboard, add these variables to each service:

**Backend service:**
| Variable | Value |
|----------|-------|
| `DATABASE_URL` | Your Rivestack PostgreSQL connection string |
| `OPENAI_API_KEY` | Your OpenAI API key |
| `PORT` | `8000` |

**Frontend service:**
| Variable | Value |
|----------|-------|
| `NUXT_PUBLIC_API_BASE` | Your backend Railway URL (e.g. `https://backend-xxx.up.railway.app`) |
| `PORT` | `3000` |

### Step 4: Deploy via GitHub Actions (auto-deploy on push)

1. In Railway, go to **Account Settings > Tokens** and create a project token
2. In your GitHub repo, go to **Settings > Secrets and variables > Actions**
3. Add this secret:

| Secret | Value |
|--------|-------|
| `RAILWAY_TOKEN` | Your Railway project token |

Now every push to `main` automatically deploys both services.

---

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 18+
- A [Rivestack](https://rivestack.com) PostgreSQL database
- An [OpenAI](https://platform.openai.com) API key

### 1. Clone and configure

```bash
git clone <your-repo-url>
cd rag-starter

# Backend config
cp backend/.env.example backend/.env
# Edit backend/.env with your Rivestack connection string and OpenAI key
```

### 2. Start the backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`. On first start, it auto-creates the `documents` and `chunks` tables with pgvector indexes.

### 3. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

The app runs at `http://localhost:3000`.

### Or use Docker Compose

```bash
# Set up your backend/.env first, then:
docker compose up --build
```

### 4. Use it

1. Open `http://localhost:3000`
2. Drop a PDF file onto the upload zone
3. Watch the progress bar as it parses, chunks, and embeds the document
4. Ask a question — get an answer with source badges
5. Click a source badge to see the exact passage highlighted in the PDF

---

## GitHub Actions CI/CD

The repo includes a deploy workflow at `.github/workflows/deploy.yml` that:

1. Triggers on every push to `main`
2. Deploys the **backend** service to Railway
3. Deploys the **frontend** service to Railway (after backend succeeds)

### Required GitHub Secrets

| Secret | Where to get it |
|--------|----------------|
| `RAILWAY_TOKEN` | Railway Dashboard > Account Settings > Tokens |

The `DATABASE_URL` and `OPENAI_API_KEY` are set directly in Railway's dashboard (not in GitHub secrets), so they stay in Railway's secure environment.

---

## How It Works

```
Upload PDF
    |
    +-- PyMuPDF extracts text with word-level bounding boxes
    +-- Text is chunked (512 tokens, 64 overlap) with bbox metadata
    +-- OpenAI generates embeddings for each chunk
    +-- Chunks + embeddings stored in Rivestack (pgvector)

Ask a question
    |
    +-- Query is embedded with OpenAI
    +-- pgvector finds the most similar chunks (cosine similarity)
    +-- Top chunks are sent as context to GPT-4o-mini
    +-- Answer + source bboxes returned to the frontend
         |
         +-- Clicking a source highlights the exact passage in the PDF
```

## Project Structure

```
rag-starter/
├── .github/workflows/
│   └── deploy.yml             # GitHub Actions -> Railway deploy
├── backend/
│   ├── Dockerfile
│   ├── railway.toml           # Railway build config
│   ├── app/
│   │   ├── main.py            # FastAPI app with CORS and auto-migration
│   │   ├── config.py          # Environment settings
│   │   ├── database.py        # Async SQLAlchemy + asyncpg
│   │   ├── models.py          # Document + Chunk models (pgvector)
│   │   ├── routers/
│   │   │   ├── documents.py   # Upload (SSE), list, delete, serve PDF
│   │   │   └── chat.py        # RAG chat endpoint
│   │   └── services/
│   │       ├── pdf_parser.py  # Word-level text + bbox extraction
│   │       ├── chunker.py     # Smart chunking with position mapping
│   │       ├── embeddings.py  # OpenAI embedding generation
│   │       ├── vector_search.py # pgvector similarity search
│   │       └── rag.py         # RAG pipeline orchestration
│   └── uploads/               # PDF file storage
│
├── frontend/
│   ├── Dockerfile
│   ├── railway.toml           # Railway build config
│   ├── pages/index.vue        # Split-screen layout
│   ├── components/
│   │   ├── PdfViewer.vue      # PDF renderer with highlight overlays
│   │   ├── ChatPanel.vue      # Chat messages + input
│   │   ├── UploadZone.vue     # Drag & drop with progress bar
│   │   └── ...
│   └── composables/
│       ├── useChat.ts         # Chat state management
│       ├── usePdfViewer.ts    # PDF + highlight state
│       └── useDocuments.ts    # Document CRUD + upload SSE
│
└── docker-compose.yml         # Local dev with Docker
```

---

Built with [Rivestack](https://rivestack.com) and deployed on [Railway](https://railway.com?referralCode=rivestack).

## License

MIT
