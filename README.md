# Musician Evaluation System

Final-year cybersecurity capstone: an AI-driven musician performance evaluation platform with security-by-design.

## Stack
- Backend: FastAPI · PostgreSQL · Celery · Redis · Librosa
- Frontend: React + TypeScript + Vite
- Infra: Docker · AWS (ECS, S3, RDS)
- Security: JWT (RS256) · Argon2id · OWASP ASVS L2

## Quick start
```bash
docker compose up --build
```

This project uses PostgreSQL and Redis via Docker Compose for the backend.

### Frontend
```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at http://localhost:5173/ and the backend at http://localhost:8000.

## Deployment (Render)

CI/CD is handled by GitHub Actions:
- **CI** (`ci.yml`) — runs tests, lint, security scans on every push/PR to `main`
- **CD** (`deploy.yml`) — deploys to Render automatically after CI passes on `main`

### One-time Render setup

1. Push this repo to GitHub (including `render.yaml`)
2. Go to [Render Dashboard](https://dashboard.render.com) → **New → Blueprint**
3. Connect your GitHub repo — Render creates all services from `render.yaml`
4. After services are created, copy each service's **Deploy Hook URL**:
   - Render Dashboard → service → **Settings → Deploy Hook**
5. Add these as GitHub repository secrets (**Settings → Secrets → Actions**):
   - `RENDER_DEPLOY_HOOK_BACKEND`
   - `RENDER_DEPLOY_HOOK_FRONTEND`
6. Set sensitive env vars manually in the Render dashboard (never commit these):
   - Backend service → **Environment**: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `S3_BUCKET_NAME`, `AWS_REGION`

### Deploy flow
```
Push to main
    ↓
GitHub Actions CI (tests · lint · security)
    ↓ passes
GitHub Actions CD → triggers Render Deploy Hooks
    ↓
Render builds & deploys backend + frontend
```

---

## S3 audio uploads (backend)

The backend now includes a minimal S3 upload endpoint:

- `POST /api/v1/performances/upload-audio` (multipart form data: `title`, optional `description`, `audio_file`)

Set these backend environment variables to enable it:

- `AWS_REGION`
- `S3_BUCKET_NAME`
- `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` (or use IAM role/default credential chain)
- optional `S3_ENDPOINT_URL` (for LocalStack/custom endpoints)
