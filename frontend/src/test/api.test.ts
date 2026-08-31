import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { api } from '../api/client';
import { ApiError, JobResponse, ScanJobResult } from '../api/types';

describe('API Client', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it('successfully fetches health status', async () => {
    const mockHealth = {
      status: 'ok',
      version: '0.1.0',
      database: 'ok',
      encoder_id: 'qwen3-0.6b',
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: () => Promise.resolve(mockHealth),
    });

    const result = await api.getHealth();
    expect(result).toEqual(mockHealth);
    expect(global.fetch).toHaveBeenCalledWith('/api/v1/health', expect.objectContaining({
      headers: expect.any(Headers),
    }));
  });

  it('fetches library stats', async () => {
    const mockStats = {
      track_count: 42,
      missing_count: 0,
      root_count: 1,
      encoder_id: 'qwen3-0.6b',
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: () => Promise.resolve(mockStats),
    });

    const stats = await api.getLibraryStats();
    expect(stats.track_count).toBe(42);
    expect(stats.root_count).toBe(1);
  });

  it('lists tracks with pagination and search parameters', async () => {
    const mockPage = {
      items: [
        {
          id: 'trk_1',
          title: 'Midnight Echoes',
          artist: 'Luna',
          album: 'Nightfall',
          genre: 'Ambient',
          year: 2024,
          duration_seconds: 215.5,
          audio_url: '/api/v1/tracks/trk_1/audio',
        },
      ],
      page: 2,
      page_size: 10,
      total: 35,
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: () => Promise.resolve(mockPage),
    });

    const res = await api.listTracks({ page: 2, pageSize: 10, search: 'Midnight' });
    expect(res.page).toBe(2);
    expect(res.items.length).toBe(1);
    expect(global.fetch).toHaveBeenCalledWith(
      '/api/v1/tracks?page=2&page_size=10&search=Midnight',
      expect.any(Object)
    );
  });

  it('accepts 202 scan and polls job through queued -> running -> succeeded', async () => {
    const mockScanResult: ScanJobResult = {
      discovered: 10,
      added: 10,
      updated: 0,
      unchanged: 0,
      errors: 0,
      embedded: 10,
      missing: 0,
      error_samples: [],
    };

    const jobs: JobResponse[] = [
      {
        id: 'job_101',
        kind: 'library_scan',
        status: 'queued',
        phase: 'queued',
        progress: 0.0,
        message: 'Job in queue',
        result: null,
        error: null,
        created_at: new Date().toISOString(),
        started_at: null,
        finished_at: null,
      },
      {
        id: 'job_101',
        kind: 'library_scan',
        status: 'running',
        phase: 'embedding',
        progress: 0.65,
        message: 'Embedding 6/10 tracks',
        result: null,
        error: null,
        created_at: new Date().toISOString(),
        started_at: new Date().toISOString(),
        finished_at: null,
      },
      {
        id: 'job_101',
        kind: 'library_scan',
        status: 'succeeded',
        phase: 'complete',
        progress: 1.0,
        message: 'Scan complete',
        result: mockScanResult,
        error: null,
        created_at: new Date().toISOString(),
        started_at: new Date().toISOString(),
        finished_at: new Date().toISOString(),
      },
    ];

    let callCount = 0;
    global.fetch = vi.fn().mockImplementation(async (url: string) => {
      if (url.includes('/library/scans')) {
        return {
          ok: true,
          status: 202,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: () => Promise.resolve({ job_id: 'job_101', status: 'queued', status_url: '/api/v1/jobs/job_101' }),
        };
      }
      if (url.includes('/api/v1/jobs/job_101')) {
        const job = jobs[Math.min(callCount++, jobs.length - 1)];
        return {
          ok: true,
          status: 200,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: () => Promise.resolve(job),
        };
      }
      return { ok: false, status: 404 };
    });

    const accepted = await api.startScan('/music/library');
    expect(accepted.job_id).toBe('job_101');

    const progressStates: string[] = [];
    const finalJob = await api.pollJobUntilDone(
      accepted.job_id,
      (job) => progressStates.push(job.status),
      10 // fast interval for test
    );

    expect(finalJob.status).toBe('succeeded');
    expect((finalJob.result as ScanJobResult).discovered).toBe(10);
    expect(progressStates).toContain('queued');
    expect(progressStates).toContain('running');
    expect(progressStates).toContain('succeeded');
  });

  it('aborts polling and removes the pending abort listener', async () => {
    const controller = new AbortController();
    const addListener = vi.spyOn(controller.signal, 'addEventListener');
    const removeListener = vi.spyOn(controller.signal, 'removeEventListener');
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: () => Promise.resolve({
        id: 'job_abort',
        kind: 'library_scan',
        status: 'running',
        phase: 'embedding',
        progress: 0.5,
        message: 'Working',
        result: null,
        error: null,
        created_at: new Date().toISOString(),
        started_at: new Date().toISOString(),
        finished_at: null,
      }),
    });

    const polling = api.pollJobUntilDone('job_abort', undefined, 1_000, controller.signal);
    await vi.waitFor(() => {
      expect(addListener).toHaveBeenCalledWith('abort', expect.any(Function), { once: true });
    });
    controller.abort();

    await expect(polling).rejects.toThrow('Polling aborted');
    expect(removeListener).toHaveBeenCalledWith('abort', expect.any(Function));
  });

  it('handles 409 library_not_indexed error correctly', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 409,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: () =>
        Promise.resolve({
          error: {
            code: 'library_not_indexed',
            message: 'Scan the music library before generating a playlist',
            details: { encoder_id: 'qwen3-0.6b' },
            request_id: 'req_123',
          },
        }),
    });

    try {
      await api.generatePlaylist({ prompt: 'rainy night', size: 10 });
      expect.fail('Should have thrown ApiError');
    } catch (err: unknown) {
      expect(err).toBeInstanceOf(ApiError);
      const apiErr = err as ApiError;
      expect(apiErr.status).toBe(409);
      expect(apiErr.code).toBe('library_not_indexed');
      expect(apiErr.isLibraryNotIndexed).toBe(true);
      expect(apiErr.requestId).toBe('req_123');
    }
  });

  it('handles 409 scan_already_running with runningJobId extraction', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 409,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: () =>
        Promise.resolve({
          error: {
            code: 'scan_already_running',
            message: 'A library scan is already running',
            details: { job_id: 'job_active_99' },
            request_id: 'req_456',
          },
        }),
    });

    try {
      await api.startScan('/path/to/music');
      expect.fail('Should have thrown ApiError');
    } catch (err: unknown) {
      expect(err).toBeInstanceOf(ApiError);
      const apiErr = err as ApiError;
      expect(apiErr.isScanAlreadyRunning).toBe(true);
      expect(apiErr.runningJobId).toBe('job_active_99');
    }
  });

  it('handles 422 validation envelope and 500 internal error envelope', async () => {
    // 422 Validation Error
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: false,
      status: 422,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: () =>
        Promise.resolve({
          error: {
            code: 'validation_error',
            message: 'Field size must be between 1 and 50',
            details: [{ loc: ['body', 'size'], msg: 'ensure this value is greater than 0' }],
            request_id: 'req_val_422',
          },
        }),
    });

    try {
      await api.generatePlaylist({ prompt: 'jazz', size: 0 });
      expect.fail('Should have thrown 422 ApiError');
    } catch (err: unknown) {
      expect(err).toBeInstanceOf(ApiError);
      const apiErr = err as ApiError;
      expect(apiErr.status).toBe(422);
      expect(apiErr.code).toBe('validation_error');
      expect(Array.isArray(apiErr.details)).toBe(true);
      expect(apiErr.requestId).toBe('req_val_422');
    }

    // 500 Internal Error
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: false,
      status: 500,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: () =>
        Promise.resolve({
          error: {
            code: 'internal_error',
            message: 'An unexpected database error occurred',
            details: null,
            request_id: 'req_err_500',
          },
        }),
    });

    try {
      await api.getLibraryStats();
      expect.fail('Should have thrown 500 ApiError');
    } catch (err: unknown) {
      expect(err).toBeInstanceOf(ApiError);
      const apiErr = err as ApiError;
      expect(apiErr.status).toBe(500);
      expect(apiErr.code).toBe('internal_error');
      expect(apiErr.message).toBe('An unexpected database error occurred');
      expect(apiErr.requestId).toBe('req_err_500');
    }
  });

  it('handles an empty playlist and a playlist shorter than requested size', async () => {
    // Empty playlist (0 matches)
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: () =>
        Promise.resolve({
          playlist_id: 'pl_empty',
          prompt: 'completely nonexistent genre xyz',
          intent: { desired_text: 'nonexistent', exclusions: [] },
          tracks: [],
        }),
    });

    const emptyRes = await api.generatePlaylist({ prompt: 'completely nonexistent genre xyz', size: 10 });
    expect(emptyRes.tracks).toEqual([]);
    expect(emptyRes.tracks.length).toBe(0);

    // Shorter playlist (5 requested, 2 available)
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: () =>
        Promise.resolve({
          playlist_id: 'pl_short',
          prompt: 'ambient drone',
          intent: { desired_text: 'ambient drone', exclusions: [] },
          tracks: [
            {
              id: 'trk_1',
              title: 'Drone 1',
              artist: 'Artist A',
              album: 'Album A',
              genre: 'Ambient',
              year: 2023,
              duration_seconds: 300,
              audio_url: '/api/v1/tracks/trk_1/audio',
              position: 1,
              score: 0.92,
              reasons: ['matches ambient drone focus'],
            },
            {
              id: 'trk_2',
              title: 'Drone 2',
              artist: 'Artist B',
              album: 'Album B',
              genre: 'Ambient',
              year: 2024,
              duration_seconds: 280,
              audio_url: '/api/v1/tracks/trk_2/audio',
              position: 2,
              score: 0.85,
              reasons: ['similar atmospheric texture'],
            },
          ],
        }),
    });

    const shortRes = await api.generatePlaylist({ prompt: 'ambient drone', size: 5 });
    expect(shortRes.tracks.length).toBe(2);
    expect(shortRes.tracks[0].position).toBe(1);
    expect(shortRes.tracks[1].position).toBe(2);
  });

  it('submits fire-and-forget feedback accepting 202 status without duplication', async () => {
    let callCount = 0;
    global.fetch = vi.fn().mockImplementation(async () => {
      callCount++;
      return {
        ok: true,
        status: 202,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: () =>
          Promise.resolve({
            feedback_id: `fb_${callCount}`,
            accepted: true,
          }),
      };
    });

    const res = await api.sendFeedback({
      playlistId: 'pl_100',
      trackId: 'trk_1',
      value: 'like',
    });

    expect(res.feedback_id).toBe('fb_1');
    expect(res.accepted).toBe(true);
    expect(callCount).toBe(1);
    expect(global.fetch).toHaveBeenCalledTimes(1);
    expect(global.fetch).toHaveBeenCalledWith(
      '/api/v1/feedback',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          playlist_id: 'pl_100',
          track_id: 'trk_1',
          value: 'like',
        }),
      })
    );
  });
});
