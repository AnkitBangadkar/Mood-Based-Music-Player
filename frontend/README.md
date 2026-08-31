# SoulSeek Frontend

Local-first, AI-powered music recommendation and playback application built with React 19, TypeScript, Vite, and Tailwind CSS.

## Getting Started

### 1. Install Dependencies
```bash
npm install
```

### 2. Run Development Server
```bash
npm run dev
```
The application will launch on `http://localhost:3000`. API requests to `/api/*` are automatically proxied to the backend at `http://127.0.0.1:8000`.

### 3. Run Test Suite
```bash
npm test
```
Runs the full Vitest + React Testing Library test suite across all API states, components, and contexts.

### 4. Build for Production
```bash
npm run build
```
Type checks with `tsc` and compiles the optimized production bundle to `dist/`.

### 5. Preview Production Build
```bash
npm run preview
```

## Architecture & Conventions
- **Contract Accuracy**: All API data contracts conform strictly to the backend definitions in `src/soulseek/contracts.py` and OpenAPI specs (`/api/v1`).
- **Singleton Audio**: Persistent single `<audio>` element mounted once in `AudioPlayerProvider`, maintaining seamless playback across view transitions.
- **Accessible & Responsive**: Standard ARIA attributes (`progressbar`, `slider`, `aria-live`), focus rings, accessible names, and mobile/desktop responsive design.
- **Deterministic Cover Art**: Non-fabricated visual palettes derived deterministically from metadata hashing.
- **Score Normalization**: Relative MMR ranking scores displayed via `ScoreBadge` with explanatory utility tooltips.
