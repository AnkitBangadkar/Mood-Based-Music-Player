# SoulSeek React Frontend

A modern, beautiful React + shadcn/ui frontend for SoulSeek - the AI-powered mood playlist generator.

## Features

- **Modern UI**: Built with React, TypeScript, Tailwind CSS, and shadcn/ui components
- **Glassmorphism Design**: Beautiful frosted glass effects and smooth animations
- **Responsive Layout**: Sidebar navigation with main content area
- **Real-time Audio Player**: Play controls, progress bar, volume, shuffle/repeat
- **Playlist Generator**: Natural language mood queries with visual results
- **Library Browser**: Search, sort, and browse your music collection
- **Scan Management**: Monitor library scanning progress with real-time updates
- **Keyboard Shortcuts**: Space (play/pause), Arrow keys (navigate, volume)

## Tech Stack

- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **Components**: shadcn/ui + Radix UI primitives
- **State Management**: Zustand
- **Icons**: Lucide React
- **Notifications**: Sonner

## Quick Start

### Development

```bash
cd frontend
npm install
npm run dev
```

The dev server will start at `http://localhost:3000` and proxy API requests to `http://localhost:8000`.

### Build for Production

```bash
cd frontend
npm run build
```

This creates a production build in `frontend/dist/` that the FastAPI backend will automatically serve.

### Using with FastAPI Backend

1. Build the frontend:
   ```bash
   cd frontend
   npm run build
   ```

2. Start the backend (from project root):
   ```bash
   python main.py
   ```

3. Open `http://localhost:8000` - the React app will be served automatically

## Project Structure

```
frontend/
├── src/
│   ├── components/          # shadcn/ui components
│   │   ├── ui/             # Button, Card, Dialog, etc.
│   │   └── Sidebar.tsx     # Main navigation
│   ├── features/           # Feature-specific components
│   │   ├── player/         # Audio player controls
│   │   ├── generator/      # Playlist generator UI
│   │   ├── library/        # Library browser
│   │   └── scan/           # Scan management
│   ├── hooks/              # Custom React hooks
│   │   ├── useAudio.ts     # Audio element management
│   │   └── usePlaylistGenerator.ts
│   ├── store/              # Zustand state stores
│   │   ├── playerStore.ts  # Audio player state
│   │   └── libraryStore.ts # Library/scan state
│   ├── types/              # TypeScript types
│   ├── lib/                # Utilities
│   ├── App.tsx             # Root component
│   └── main.tsx            # Entry point
├── dist/                   # Production build
└── package.json
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Space | Play/Pause |
| Arrow Right | Next track |
| Arrow Left | Previous track |
| Arrow Up | Volume up |
| Arrow Down | Volume down |

## Customization

### Colors

Edit `tailwind.config.cjs` to customize the color scheme:

```javascript
colors: {
  primary: {
    DEFAULT: "hsl(var(--primary))",
    foreground: "hsl(var(--primary-foreground))",
  },
  // ...
}
```

### Theme Variables

Edit `src/index.css` to modify CSS variables:

```css
:root {
  --primary: 38 92% 50%;  /* Amber/orange primary color */
  --background: 240 10% 3.9%;  /* Dark background */
  /* ... */
}
```

## Notes

- The frontend proxies API calls to the FastAPI backend during development
- Built files are automatically served by FastAPI when placed in `frontend/dist/`
- The original static frontend remains available as a fallback
