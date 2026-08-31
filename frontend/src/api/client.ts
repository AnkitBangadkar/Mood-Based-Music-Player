import {
  ApiError,
  ApiErrorResponse,
  FeedbackRequest,
  FeedbackResponse,
  HealthResponse,
  JobAcceptedResponse,
  JobResponse,
  LibraryStatsResponse,
  PlaylistRequest,
  PlaylistResponse,
  ScanRequest,
  TrackPageResponse,
} from './types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

function waitForNextPoll(intervalMs: number, signal?: AbortSignal): Promise<void> {
  return new Promise<void>((resolve, reject) => {
    if (signal?.aborted) {
      reject(new Error('Polling aborted'));
      return;
    }

    const onAbort = () => {
      clearTimeout(timeout);
      signal?.removeEventListener('abort', onAbort);
      reject(new Error('Polling aborted'));
    };
    const timeout = setTimeout(() => {
      signal?.removeEventListener('abort', onAbort);
      resolve();
    }, intervalMs);

    signal?.addEventListener('abort', onAbort, { once: true });
  });
}

function generateRequestId(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return 'req_' + Math.random().toString(36).substring(2, 11);
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  const headers = new Headers(options.headers || {});
  
  if (!headers.has('Accept')) {
    headers.set('Accept', 'application/json');
  }
  
  if (options.body && !headers.has('Content-Type') && typeof options.body === 'string') {
    headers.set('Content-Type', 'application/json');
  }

  if (!headers.has('X-Request-ID')) {
    headers.set('X-Request-ID', generateRequestId());
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorData: ApiErrorResponse | null = null;
    try {
      errorData = await response.json();
    } catch {
      // JSON parse failed, fallback below
    }

    if (errorData?.error) {
      throw new ApiError(response.status, errorData.error);
    }

    throw new ApiError(response.status, {
      code: `http_${response.status}`,
      message: response.statusText || `Request failed with status ${response.status}`,
      details: null,
      request_id: headers.get('X-Request-ID') || 'unknown',
    });
  }

  // 202 / 204 may return empty or JSON
  if (response.status === 204) {
    return {} as T;
  }

  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    return response.json() as Promise<T>;
  }

  return response.text() as unknown as Promise<T>;
}

export const api = {
  /**
   * Health check endpoint
   */
  async getHealth(): Promise<HealthResponse> {
    return request<HealthResponse>('/api/v1/health');
  },

  /**
   * Fetch library stats
   */
  async getLibraryStats(): Promise<LibraryStatsResponse> {
    return request<LibraryStatsResponse>('/api/v1/library/stats');
  },

  /**
   * Paginated list of tracks with optional search
   */
  async listTracks(params: {
    page?: number;
    pageSize?: number;
    search?: string;
  } = {}): Promise<TrackPageResponse> {
    const searchParams = new URLSearchParams();
    if (params.page !== undefined) searchParams.set('page', String(params.page));
    if (params.pageSize !== undefined) searchParams.set('page_size', String(params.pageSize));
    if (params.search && params.search.trim()) searchParams.set('search', params.search.trim());

    const queryString = searchParams.toString();
    const endpoint = `/api/v1/tracks${queryString ? `?${queryString}` : ''}`;
    return request<TrackPageResponse>(endpoint);
  },

  /**
   * Submit an absolute folder path for background scanning and indexing
   */
  async startScan(root: string): Promise<JobAcceptedResponse> {
    const payload: ScanRequest = { root };
    return request<JobAcceptedResponse>('/api/v1/library/scans', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  /**
   * Fetch job status
   */
  async getJob(jobId: string): Promise<JobResponse> {
    return request<JobResponse>(`/api/v1/jobs/${jobId}`);
  },

  /**
   * Poll a scan job until it reaches succeeded or failed
   */
  async pollJobUntilDone(
    jobId: string,
    onProgress?: (job: JobResponse) => void,
    intervalMs: number = 800,
    signal?: AbortSignal
  ): Promise<JobResponse> {
    while (true) {
      if (signal?.aborted) {
        throw new Error('Polling aborted');
      }

      const job = await this.getJob(jobId);
      if (onProgress) {
        onProgress(job);
      }

      if (job.status === 'succeeded' || job.status === 'failed') {
        return job;
      }

      await waitForNextPoll(intervalMs, signal);
    }
  },

  /**
   * Generate natural language playlist
   */
  async generatePlaylist(req: PlaylistRequest): Promise<PlaylistResponse> {
    return request<PlaylistResponse>('/api/v1/playlists', {
      method: 'POST',
      body: JSON.stringify(req),
    });
  },

  /**
   * Send like/dislike/skip feedback (fire-and-forget 202 accepted)
   */
  async sendFeedback(req: {
    playlistId: string;
    trackId?: string | null;
    value: 'like' | 'dislike' | 'skip';
  }): Promise<FeedbackResponse> {
    const payload: FeedbackRequest = {
      playlist_id: req.playlistId,
      track_id: req.trackId ?? null,
      value: req.value,
    };
    return request<FeedbackResponse>('/api/v1/feedback', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  /**
   * Formats audio URL for streaming
   */
  getAudioUrl(audioUrl: string): string {
    if (audioUrl.startsWith('http://') || audioUrl.startsWith('https://')) {
      return audioUrl;
    }
    return `${API_BASE_URL}${audioUrl.startsWith('/') ? '' : '/'}${audioUrl}`;
  },
};
