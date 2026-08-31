# Gemini frontend handoff

Build a React + TypeScript frontend for SoulSeek. Do not implement recommendation logic or access local file paths. Treat the backend OpenAPI document at `http://127.0.0.1:8000/openapi.json` as authoritative and keep all HTTP calls in one typed `api/` module.

## Required screens

1. **Library setup:** show `GET /api/v1/library/stats`; submit an absolute folder to `POST /api/v1/library/scans`; poll the returned `status_url` until `succeeded` or `failed`; display phase, progress, and sampled file errors.
2. **Generator:** submit `{ prompt, size }` to `POST /api/v1/playlists`; show parsed exclusions and the ordered tracks with reasons.
3. **Player:** use each track's `audio_url` directly in one persistent HTML `<audio>` element. Preserve the current queue and support previous/next/play/pause/seek.
4. **Library:** paginate/search `GET /api/v1/tracks?page=1&page_size=50&search=`.
5. **Feedback:** send `{ playlist_id, track_id, value }` to `POST /api/v1/feedback` for like/dislike/skip. Feedback is fire-and-forget after a 202 response.

## Core TypeScript shapes

```ts
type Track = {
  id: string; title: string; artist: string; album: string; genre: string;
  year: number | null; duration_seconds: number | null; audio_url: string;
};

type Playlist = {
  playlist_id: string;
  prompt: string;
  intent: { desired_text: string; exclusions: string[] };
  tracks: Array<Track & { position: number; score: number; reasons: string[] }>;
};

type Job = {
  id: string; kind: string;
  status: "queued" | "running" | "succeeded" | "failed";
  phase: string; progress: number; message: string;
  result: Record<string, unknown> | null;
  error: Record<string, unknown> | null;
  created_at: string; started_at: string | null; finished_at: string | null;
};

type ApiError = {
  error: { code: string; message: string; details: unknown; request_id: string };
};
```

## UX constraints

- Handle `409 library_not_indexed` by linking to library setup.
- Handle `409 scan_already_running` by polling `error.details.job_id`.
- Never display raw playlist scores as confidence percentages; they are internal relative ranking utilities.
- Never fabricate cover art. Use a deterministic placeholder until the API adds artwork.
- Target desktop first, remain usable on mobile, and add component/API tests with mocked HTTP responses.

