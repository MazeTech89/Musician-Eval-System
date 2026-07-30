# Frontend

This README covers frontend-only details. For full-stack run instructions, see the root [README.md](C:/Users/Admin/Documents/Repos/Musician-Eval-System.worktrees/update-status-summary/README.md).

## What it does
- User authentication (login/register)
- Clear invalid-credentials feedback on failed login
- Role-based dashboard
- Protected routes
- Responsive Tailwind UI
- API integration with the backend

## Tech stack
- React 18
- TypeScript
- Vite
- React Router
- Tailwind CSS
- Axios
- Lucide React

## Scripts

```bash
npm install
npm run dev
npm run build
npm run preview
npm run lint
```

## Environment

The frontend expects the backend API at `http://localhost:8000`.
The Vite dev server proxies API requests to the backend.

## Structure

```text
src/
├── components/
├── contexts/
├── pages/
├── App.tsx
├── main.tsx
├── index.css
└── App.css
```