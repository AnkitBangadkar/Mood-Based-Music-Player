import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { LibrarySetup } from '../components/library/LibrarySetup';
import { LibraryScanProvider } from '../context/LibraryScanContext';
import { NotificationProvider } from '../context/NotificationContext';
import { api } from '../api/client';
import { ScanJobResult } from '../api/types';

describe('LibrarySetup', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders library stats and handles scan job lifecycle with counters and sampled error path/message', async () => {
    vi.spyOn(api, 'getLibraryStats').mockResolvedValue({
      track_count: 50,
      missing_count: 2,
      root_count: 1,
      encoder_id: 'qwen3-0.6b',
    });

    const startScanSpy = vi.spyOn(api, 'startScan').mockResolvedValue({
      job_id: 'job_scan_1',
      status: 'queued',
      status_url: '/api/v1/jobs/job_scan_1',
    });

    const mockScanResult: ScanJobResult = {
      discovered: 50,
      added: 48,
      updated: 0,
      unchanged: 0,
      errors: 2,
      embedded: 48,
      missing: 0,
      error_samples: [
        {
          path: '/music/corrupted_header.mp3',
          message: 'invalid audio frame header at offset 0',
        },
      ],
    };

    const pollJobSpy = vi.spyOn(api, 'pollJobUntilDone').mockImplementation(
      async (jobId, onProgress) => {
        onProgress?.({
          id: jobId,
          kind: 'library_scan',
          status: 'running',
          phase: 'encoding',
          progress: 0.75,
          message: 'Encoding track embeddings (37/50)',
          result: null,
          error: null,
          created_at: new Date().toISOString(),
          started_at: new Date().toISOString(),
          finished_at: null,
        });

        return {
          id: jobId,
          kind: 'library_scan',
          status: 'succeeded',
          phase: 'completed',
          progress: 1.0,
          message: 'Scan completed successfully',
          result: mockScanResult,
          error: null,
          created_at: new Date().toISOString(),
          started_at: new Date().toISOString(),
          finished_at: new Date().toISOString(),
        };
      }
    );

    render(
      <NotificationProvider>
        <LibraryScanProvider>
          <LibrarySetup />
        </LibraryScanProvider>
      </NotificationProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('50')).toBeInTheDocument();
      expect(screen.getByText('2')).toBeInTheDocument();
      expect(screen.getByText('qwen3-0.6b')).toBeInTheDocument();
    });

    const startBtn = screen.getByRole('button', { name: /Start Ingestion Scan/i });
    fireEvent.submit(startBtn.closest('form')!);

    await waitFor(() => {
      expect(startScanSpy).toHaveBeenCalledWith('/home/esscrimson/code/SoulSeek/songs_for_research');
      expect(pollJobSpy).toHaveBeenCalledWith('job_scan_1', expect.any(Function), 800, expect.any(AbortSignal));
    });

    await waitFor(() => {
      expect(screen.getByTestId('scan-counters')).toBeInTheDocument();
      expect(screen.getByText(/Discovered/i)).toBeInTheDocument();
      expect(screen.getByText(/Added/i)).toBeInTheDocument();
      expect(screen.getAllByText('48').length).toBe(2);
      expect(screen.getByTestId('error-samples-section')).toBeInTheDocument();
      expect(screen.getByText(/corrupted_header\.mp3/i)).toBeInTheDocument();
      expect(screen.getByText(/invalid audio frame header at offset 0/i)).toBeInTheDocument();
    });
  });

  it('handles failed scan job displaying Job.error payload', async () => {
    vi.spyOn(api, 'getLibraryStats').mockResolvedValue({
      track_count: 0,
      missing_count: 0,
      root_count: 0,
      encoder_id: 'qwen3-0.6b',
    });

    const startScanSpy = vi.spyOn(api, 'startScan').mockResolvedValue({
      job_id: 'job_failed_1',
      status: 'queued',
      status_url: '/api/v1/jobs/job_failed_1',
    });

    const pollJobSpy = vi.spyOn(api, 'pollJobUntilDone').mockImplementation(
      async (jobId, onProgress) => {
        onProgress?.({
          id: jobId,
          kind: 'library_scan',
          status: 'running',
          phase: 'discovering',
          progress: 0.05,
          message: 'Discovering audio files',
          result: null,
          error: null,
          created_at: new Date().toISOString(),
          started_at: new Date().toISOString(),
          finished_at: null,
        });

        await new Promise((resolve) => setTimeout(resolve, 20));

        return {
          id: jobId,
          kind: 'library_scan',
          status: 'failed',
          phase: 'discovering',
          progress: 0.05,
          message: 'Failed to access directory',
          result: null,
          error: {
            code: 'scan_root_unreadable',
            message: 'Permission denied accessing /root/music',
          },
          created_at: new Date().toISOString(),
          started_at: new Date().toISOString(),
          finished_at: new Date().toISOString(),
        };
      }
    );

    render(
      <NotificationProvider>
        <LibraryScanProvider>
          <LibrarySetup />
        </LibraryScanProvider>
      </NotificationProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('qwen3-0.6b')).toBeInTheDocument();
    });

    const startBtn = screen.getByRole('button', { name: /Start Ingestion Scan/i });
    fireEvent.submit(startBtn.closest('form')!);

    await waitFor(() => {
      expect(startScanSpy).toHaveBeenCalledWith('/home/esscrimson/code/SoulSeek/songs_for_research');
      expect(pollJobSpy).toHaveBeenCalledWith('job_failed_1', expect.any(Function), 800, expect.any(AbortSignal));
    });

    await waitFor(() => {
      expect(screen.getByTestId('scan-error-banner')).toBeInTheDocument();
      expect(screen.getByText('Scan Job Error')).toBeInTheDocument();
      expect(screen.getAllByText(/Permission denied accessing \/root\/music/i).length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText(/Code: scan_root_unreadable/i)).toBeInTheDocument();
    });
  });
});
