import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { PlaylistView } from '../components/generator/PlaylistView';
import { NotificationProvider } from '../context/NotificationContext';
import { AudioPlayerProvider } from '../context/AudioPlayerContext';

describe('PlaylistView', () => {
  it('renders correctly', () => {
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

    render(
      <NotificationProvider>
        <AudioPlayerProvider>
          <PlaylistView playlist={mockPlaylist} />
        </AudioPlayerProvider>
      </NotificationProvider>
    );

    expect(screen.getByTestId('playlist-view')).toBeInTheDocument();
    expect(screen.getByText(/Target Focus:/i)).toBeInTheDocument();
    expect(screen.getByText('rainy evening drive')).toBeInTheDocument();
    expect(screen.getByText('-drums')).toBeInTheDocument();
    expect(screen.getByText('Rainy Street')).toBeInTheDocument();
  });
});
