/**
 * Strict TypeScript types for SoulSeek API.
 * Conforms to docs/FRONTEND_HANDOFF.md and src/soulseek/contracts.py
 */

export interface Track {
  id: string;
  title: string;
  artist: string;
  album: string;
  genre: string;
  year: number | null;
  duration_seconds: number | null;
  audio_url: string;
}

export interface TrackPageResponse {
  items: Track[];
  page: number;
  page_size: number;
  total: number;
}

export interface ParsedIntentResponse {
  desired_text: string;
  exclusions: string[];
}

export interface PlaylistTrackResponse extends Track {
  position: number;
  score: number;
  reasons: string[];
}

export interface PlaylistResponse {
  playlist_id: string;
  prompt: string;
  intent: ParsedIntentResponse;
  tracks: PlaylistTrackResponse[];
}

export interface PlaylistRequest {
  prompt: string;
  size?: number;
}

export interface ScanRequest {
  root: string;
}

export interface JobAcceptedResponse {
  job_id: string;
  status: 'queued';
  status_url: string;
}

export interface ScanErrorSample {
  path: string;
  message: string;
}

export interface ScanJobResult {
  discovered: number;
  added: number;
  updated: number;
  unchanged: number;
  errors: number;
  embedded: number;
  missing: number;
  error_samples: ScanErrorSample[];
}

export interface JobResponse {
  id: string;
  kind: string;
  status: 'queued' | 'running' | 'succeeded' | 'failed';
  phase: string;
  progress: number; // 0.0 to 1.0
  message: string;
  result: ScanJobResult | Record<string, unknown> | null;
  error: Record<string, unknown> | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
}

export interface LibraryStatsResponse {
  track_count: number;
  missing_count: number;
  root_count: number;
  encoder_id: string;
}

export interface HealthResponse {
  status: 'ok';
  version: string;
  database: 'ok';
  encoder_id: string;
}

export type FeedbackValue = 'like' | 'dislike' | 'skip';

export interface FeedbackRequest {
  playlist_id: string;
  track_id?: string | null;
  value: FeedbackValue;
}

export interface FeedbackResponse {
  feedback_id: string;
  accepted: true;
}

export interface ApiErrorBody {
  code: string;
  message: string;
  details?: Record<string, unknown> | unknown[] | null;
  request_id: string;
}

export interface ApiErrorResponse {
  error: ApiErrorBody;
}

export class ApiError extends Error {
  public readonly status: number;
  public readonly code: string;
  public readonly details: Record<string, unknown> | unknown[] | null;
  public readonly requestId: string;

  constructor(status: number, body: ApiErrorBody) {
    super(body.message || `API Error ${status}`);
    this.name = 'ApiError';
    this.status = status;
    this.code = body.code || 'unknown_error';
    this.details = body.details ?? null;
    this.requestId = body.request_id || 'unknown';
  }

  get isLibraryNotIndexed(): boolean {
    return this.status === 409 && this.code === 'library_not_indexed';
  }

  get isScanAlreadyRunning(): boolean {
    return this.status === 409 && this.code === 'scan_already_running';
  }

  get runningJobId(): string | null {
    if (this.isScanAlreadyRunning && this.details && typeof this.details === 'object' && 'job_id' in this.details) {
      return String((this.details as Record<string, unknown>).job_id);
    }
    return null;
  }
}
