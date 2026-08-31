import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { TrackBrowser } from '../components/library/TrackBrowser';
import { NotificationProvider } from '../context/NotificationContext';
import { AudioPlayerProvider } from '../context/AudioPlayerContext';
import { api } from '../api/client';

describe('TrackBrowser', () => {
  it('renders track list with pagination and search input', async () => {
    vi.spyOn(api, 'listTracks').mockResolvedValue({
      items: [
        {
          id: 'trk_10',
          title: 'Horizon Lights',
          artist: 'Tycho',
          album: 'Dive',
          genre: 'Electronic',
          year: 2011,
          duration_seconds: 240,
          audio_url: '/api/v1/tracks/trk_10/audio',
        },
      ],
      page: 1,
      page_size: 50,
      total: 1,
    });

    render(
      <NotificationProvider>
        <AudioPlayerProvider>
          <TrackBrowser onNavigateToSetup={vi.fn()} />
        </AudioPlayerProvider>
      </NotificationProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Horizon Lights')).toBeInTheDocument();
      expect(screen.getByText('Tycho')).toBeInTheDocument();
      expect(screen.getByText('Dive')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText(/Search by title/i);
    fireEvent.change(searchInput, { target: { value: 'Horizon' } });

    await waitFor(() => {
      expect(api.listTracks).toHaveBeenCalledWith(
        expect.objectContaining({
          search: 'Horizon',
        })
      );
    });
  });
});
