import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { PlaylistGenerator } from '../components/generator/PlaylistGenerator';
import { NotificationProvider } from '../context/NotificationContext';
import { AudioPlayerProvider } from '../context/AudioPlayerContext';
import { api } from '../api/client';
import { ApiError } from '../api/types';

describe('PlaylistGenerator', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('displays 409 library_not_indexed banner and handles navigation click', async () => {
    const errorBody = {
      code: 'library_not_indexed',
      message: 'Scan the music library before generating a playlist',
      details: { encoder_id: 'qwen3-0.6b' },
      request_id: 'req_test',
    };

    vi.spyOn(api, 'generatePlaylist').mockRejectedValue(
      new ApiError(409, errorBody)
    );

    const onNavigate = vi.fn();

    render(
      <NotificationProvider>
        <AudioPlayerProvider>
          <PlaylistGenerator onNavigateToSetup={onNavigate} />
        </AudioPlayerProvider>
      </NotificationProvider>
    );

    const generateBtn = screen.getByRole('button', { name: /Generate Playlist/i });
    fireEvent.submit(generateBtn.closest('form')!);

    await waitFor(() => {
      expect(screen.getByTestId('library-not-indexed-banner')).toBeInTheDocument();
      expect(screen.getByText(/Library Not Indexed \(409\)/i)).toBeInTheDocument();
    });

    const setupBtn = screen.getByRole('button', { name: /Open Library Setup/i });
    fireEvent.click(setupBtn);
    expect(onNavigate).toHaveBeenCalled();
  });

  it('renders generated playlist with parsed intent and exclusions', async () => {
    const mockPlaylist = {
      playlist_id: 'pl_sample',
      prompt: 'rainy evening drive without drums',
      intent: {
        desired_text: 'rainy evening drive',
        exclusions: ['drums'],
      },
      tracks: [
        {
          id: 'trk_1',
          position: 1,
          title: 'Rainy Street',
          artist: 'Ambient Flow',
          album: 'Lo-Fi Chill',
          genre: 'Ambient',
          year: 2023,
          duration_seconds: 180,
          audio_url: '/api/v1/tracks/trk_1/audio',
          score: 0.892,
          reasons: ['Semantic similarity to rainy evening drive', 'Negative filter removed drums'],
        },
      ],
    };

    const spy = vi.spyOn(api, 'generatePlaylist').mockResolvedValue(mockPlaylist);

    render(
      <NotificationProvider>
        <AudioPlayerProvider>
          <PlaylistGenerator onNavigateToSetup={vi.fn()} />
        </AudioPlayerProvider>
      </NotificationProvider>
    );

    const generateBtn = screen.getByRole('button', { name: /Generate Playlist/i });
    fireEvent.submit(generateBtn.closest('form')!);

    await waitFor(() => {
      expect(spy).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(screen.getByTestId('playlist-view')).toBeInTheDocument();
      expect(screen.getByText(/Target Focus:/i)).toBeInTheDocument();
      expect(screen.getByText('-drums')).toBeInTheDocument();
      expect(screen.getByText('Rainy Street')).toBeInTheDocument();
      expect(screen.getByText('Rank Utility:')).toBeInTheDocument();
      expect(screen.getByText('0.892')).toBeInTheDocument();
    });
  });
});
