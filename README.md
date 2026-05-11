# Musician Evaluation System

Final-year cybersecurity capstone: an AI-driven musician performance evaluation platform with security-by-design.

## Stack
- Backend: FastAPI · PostgreSQL · Celery · Redis · Librosa
- Frontend: React + TypeScript + Vite
- Infra: Docker · AWS (ECS, S3, RDS)
- Security: JWT (RS256) · Argon2id · OWASP ASVS L2

## Quick start
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload

### Frontend
`ash
cd frontend
npm install
npm run dev
``n
The frontend will be available at http://localhost:5173/ and the backend at http://localhost:8000.
