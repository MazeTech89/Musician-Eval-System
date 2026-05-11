# Musician Evaluation System - Frontend

React + TypeScript frontend for the Musician Evaluation System.

## Features

- User authentication (login/register)
- Role-based dashboard
- Protected routes
- Responsive design with Tailwind CSS
- API integration with backend

## Tech Stack

- React 18
- TypeScript
- Vite
- React Router
- Tailwind CSS
- Axios for API calls
- Lucide React for icons

## Getting Started

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start development server:
   ```bash
   npm run dev
   ```

3. Build for production:
   ```bash
   npm run build
   ```

## Project Structure

```
src/
├── components/          # Reusable components
├── contexts/           # React contexts (Auth)
├── pages/             # Page components
├── App.tsx           # Main app component
├── main.tsx         # App entry point
├── index.css       # Global styles
└── App.css        # Additional styles
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Environment

The frontend expects the backend API to be running on `http://localhost:8000`. The Vite config includes proxy settings for API calls.</content>
<parameter name="filePath">c:\5. Implementation\Code\IMTMPES\dev\Musician-Eval-System\frontend\README.md