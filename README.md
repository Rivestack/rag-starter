# DocChat — Chat with any PDF

A stunning RAG demo app that lets you upload PDFs, ask questions in plain English, and get AI-powered answers with highlighted source passages. Built on **[Rivestack](https://rivestack.com)** (managed PostgreSQL + pgvector).

![Powered by Rivestack](https://img.shields.io/badge/Powered%20by-Rivestack-blue)

## Features

- **Upload PDFs** with real-time progress tracking (parsing, chunking, embedding)
- **Ask questions** about your documents in natural language
- **Source highlights** — click a source badge to see the exact passage highlighted in the PDF
- **Split-screen UI** — PDF viewer on the left, chat on the right
- **Conversation memory** — follow-up questions understand context
- **Auto-deploy** to Kubernetes via GitHub Actions

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Nuxt.js + shadcn-vue + Tailwind CSS |
| Backend | Python + FastAPI |
| Database | [Rivestack](https://rivestack.com) (PostgreSQL + pgvector) |
| Embeddings | OpenAI `text-embedding-3-small` |
| LLM | OpenAI `gpt-4o-mini` |
| PDF Parsing | PyMuPDF |
| Deploy | Kubernetes + Helm + GitHub Actions |

---

## Deploy to Kubernetes

The app auto-deploys to a Kubernetes cluster via GitHub Actions on every push to `main`.

### Prerequisites

- A Kubernetes cluster with nginx ingress controller and cert-manager
- A [Rivestack](https://rivestack.com) PostgreSQL database with pgvector enabled
- An [OpenAI](https://platform.openai.com) API key

### GitHub Secrets

Add these secrets in your GitHub repo under **Settings > Secrets and variables > Actions**:

| Secret | Description |
|--------|-------------|
| `PRD_KUBECONFIG` | Your Kubernetes cluster kubeconfig (base64 or raw YAML) |
| `GH_TOKEN` | GitHub token with `packages:write` for GHCR |
| `DATABASE_URL` | Rivestack PostgreSQL connection string |
| `OPENAI_API_KEY` | OpenAI API key |

### What happens on push

1. **`build.yml`** — Builds Docker images for backend and frontend, pushes to GHCR
2. **`deploy.yml`** — Triggered after successful build:
   - Creates `rivestack-demo` namespace
   - Creates K8s secrets from GitHub secrets (`docchat-backend-config`, `docchat-frontend-config`)
   - Creates GHCR pull secret
   - Helm deploys backend → `docchat-api.rivestack.io`
   - Helm deploys frontend → `docchat.rivestack.io`

### Helm Charts

```
deploy/
├── docchat-backend/       # FastAPI backend
│   ├── Chart.yaml
│   ├── values.yaml        # Image, resources, ingress (docchat-api.rivestack.io)
│   └── templates/
│       ├── deployment.yaml
│       ├── service.yaml
│       └── ingress.yaml
│
└── docchat-frontend/      # Nuxt.js frontend
    ├── Chart.yaml
    ├── values.yaml        # Image, resources, ingress (docchat.rivestack.io)
    └── templates/
        ├── deployment.yaml
        ├── service.yaml
        └── ingress.yaml
```

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
│   ├── build.yml              # Build Docker images -> GHCR
│   └── deploy.yml             # Helm deploy to K8s (rivestack-demo ns)
├── deploy/
│   ├── docchat-backend/       # Helm chart for backend
│   └── docchat-frontend/      # Helm chart for frontend
├── backend/
│   ├── Dockerfile
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

Built with [Rivestack](https://rivestack.com).

## License

MIT
