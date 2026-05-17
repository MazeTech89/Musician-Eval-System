# Musician Evaluation System

Final-year cybersecurity capstone: an AI-driven musician performance evaluation platform with security-by-design.

## Tech Stack
- Backend: FastAPI, SQLAlchemy, PostgreSQL, Pydantic, Python-Jose, Argon2id, Celery, Redis, Librosa
- Frontend: React, TypeScript, Vite, Tailwind CSS, React Router, Axios, Lucide React
- Testing: Pytest, Playwright, FastAPI TestClient
- Infrastructure: Docker Compose, PostgreSQL, Redis
- Security: JWT access/refresh, role-based access control, Argon2 password hashing, OWASP-aligned patterns

## Progress
- ✅ Backend auth flow fixed and validated: registration, login, JWT access token, refresh token, `/auth/me`
- ✅ Backend role serialization and `UserResponse` response handling corrected
- ✅ Backend auth unit tests passed: `24 passed`
- ✅ Frontend auth flow validated: register, login, logout, protected routes
- ✅ Frontend build successful and UI smoke test added with Playwright
- ✅ Browser-based interactive validation completed in VS Code
- ✅ Documentation updated with current setup, progress, and test coverage

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
