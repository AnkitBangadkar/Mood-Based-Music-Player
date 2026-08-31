import React from 'react';
import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AudioPlayerProvider, useAudioPlayer } from '../context/AudioPlayerContext';
import { NotificationProvider } from '../context/NotificationContext';
import { Track } from '../api';
import { MockAudio } from './setup';

const mockTrack1: Track = {
  id: 'trk_1',
  title: 'Track One',
  artist: 'Artist A',
  album: 'Album X',
  genre: 'Lo-Fi',
  year: 2024,
  duration_seconds: 200,
  audio_url: '/api/v1/tracks/trk_1/audio',
};

const mockTrack2: Track = {
  id: 'trk_2',
  title: 'Track Two',
  artist: 'Artist B',
  album: 'Album Y',
  genre: 'Ambient',
  year: 2023,
  duration_seconds: 150,
  audio_url: '/api/v1/tracks/trk_2/audio',
};

const mockTrack3: Track = {
  id: 'trk_3',
  title: 'Track Three',
  artist: 'Artist C',
  album: 'Album Z',
  genre: 'Chillhop',
  year: 2022,
  duration_seconds: 180,
  audio_url: '/api/v1/tracks/trk_3/audio',
};

const wrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <NotificationProvider>
    <AudioPlayerProvider>{children}</AudioPlayerProvider>
  </NotificationProvider>
);

describe('AudioPlayerContext', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('initializes with empty queue and idle playback state', () => {
    const { result } = renderHook(() => useAudioPlayer(), { wrapper });

    expect(result.current.currentTrack).toBeNull();
    expect(result.current.queue).toEqual([]);
    expect(result.current.isPlaying).toBe(false);
    expect(result.current.repeatMode).toBe('off');
    expect(result.current.isShuffled).toBe(false);
  });

  it('maintains exactly ONE singleton audio object across next/prev, seek, queue replacement, and track removal', () => {
    const { result } = renderHook(() => useAudioPlayer(), { wrapper });

    // Initial audio element created
    expect(MockAudio.instances.length).toBe(1);
    const singletonAudio = MockAudio.instances[0];

    // 1. Play track & initialize queue
    act(() => {
      result.current.playTrack(mockTrack1, [mockTrack1, mockTrack2, mockTrack3], 'pl_1');
    });
    expect(MockAudio.instances.length).toBe(1);
    expect(singletonAudio.src).toContain('/api/v1/tracks/trk_1/audio');

    // 2. Next track
    act(() => {
      result.current.playNext();
    });
    expect(MockAudio.instances.length).toBe(1);
    expect(result.current.currentTrack?.id).toBe('trk_2');
    expect(singletonAudio.src).toContain('/api/v1/tracks/trk_2/audio');

    // 3. Seek
    act(() => {
      result.current.seek(45);
    });
    expect(MockAudio.instances.length).toBe(1);
    expect(singletonAudio.currentTime).toBe(45);

    // 4. Previous track
    act(() => {
      singletonAudio.currentTime = 1; // within 3s to trigger actual prev track
      result.current.playPrevious();
    });
    expect(MockAudio.instances.length).toBe(1);
    expect(result.current.currentTrack?.id).toBe('trk_1');

    // 5. Replace entire queue with new playlist
    act(() => {
      result.current.playPlaylist([mockTrack3, mockTrack2], 0, 'pl_2');
    });
    expect(MockAudio.instances.length).toBe(1);
    expect(result.current.currentTrack?.id).toBe('trk_3');

    // 6. Remove track from queue
    act(() => {
      result.current.removeFromQueue(1);
    });
    expect(MockAudio.instances.length).toBe(1);
    expect(result.current.queue.length).toBe(1);

    // 7. Clear queue
    act(() => {
      result.current.clearQueue();
    });
    expect(MockAudio.instances.length).toBe(1);
  });

  it('uses audio_url verbatim without constructing filesystem paths', () => {
    const { result } = renderHook(() => useAudioPlayer(), { wrapper });
    const singletonAudio = MockAudio.instances[0];

    act(() => {
      result.current.playTrack(mockTrack1);
    });

    expect(singletonAudio.src).toBe('/api/v1/tracks/trk_1/audio');
    expect(singletonAudio.src).not.toContain('/home/');
    expect(singletonAudio.src).not.toContain('.mp3');
  });

  it('handles playback failure (404/410) and advances safely to the next playable item', async () => {
    vi.useFakeTimers();
    const { result } = renderHook(() => useAudioPlayer(), { wrapper });
    const singletonAudio = MockAudio.instances[0];

    act(() => {
      result.current.playPlaylist([mockTrack1, mockTrack2], 0, 'pl_error');
    });
    expect(result.current.currentTrack?.id).toBe('trk_1');

    // Simulate 410 Missing / 404 Not Found error event on the audio element
    act(() => {
      singletonAudio.error = { code: 4, message: 'Audio file missing or not found' };
      singletonAudio.dispatchEvent(new Event('error'));
    });

    // Advance fake timers for error debounce / next track transition
    act(() => {
      vi.advanceTimersByTime(600);
    });

    // Successfully advanced to next track (mockTrack2)
    expect(result.current.currentTrack?.id).toBe('trk_2');
    expect(singletonAudio.src).toContain('/api/v1/tracks/trk_2/audio');

    vi.useRealTimers();
  });

  it('skips a broken track even when repeat-one is enabled and stops after all candidates fail', () => {
    vi.useFakeTimers();
    const { result } = renderHook(() => useAudioPlayer(), { wrapper });
    const singletonAudio = MockAudio.instances[0];

    act(() => {
      result.current.playPlaylist([mockTrack1, mockTrack2], 0);
      result.current.cycleRepeatMode(); // off -> all
    });
    act(() => result.current.cycleRepeatMode()); // all -> one

    act(() => singletonAudio.dispatchEvent(new Event('error')));
    act(() => vi.advanceTimersByTime(600));
    expect(result.current.currentTrack?.id).toBe('trk_2');

    act(() => singletonAudio.dispatchEvent(new Event('error')));
    act(() => vi.advanceTimersByTime(600));
    expect(result.current.currentTrack?.id).toBe('trk_2');
    expect(result.current.isPlaying).toBe(false);

    vi.useRealTimers();
  });

  it('keeps the active track and queue index consistent when the current item is removed', () => {
    const { result } = renderHook(() => useAudioPlayer(), { wrapper });

    act(() => result.current.playPlaylist([mockTrack1, mockTrack2, mockTrack3], 1));
    act(() => result.current.removeFromQueue(1));

    expect(result.current.queue.map((track) => track.id)).toEqual(['trk_1', 'trk_3']);
    expect(result.current.queueIndex).toBe(1);
    expect(result.current.currentTrack?.id).toBe('trk_3');
  });

  it('manages queue operations: add, remove, shuffle, and cycle repeat mode', () => {
    const { result } = renderHook(() => useAudioPlayer(), { wrapper });

    act(() => {
      result.current.playTrack(mockTrack1, [mockTrack1]);
    });

    act(() => {
      result.current.addToQueue(mockTrack2);
    });
    expect(result.current.queue.length).toBe(2);

    act(() => {
      result.current.toggleShuffle();
    });
    expect(result.current.isShuffled).toBe(true);

    act(() => {
      result.current.cycleRepeatMode(); // off -> all
    });
    expect(result.current.repeatMode).toBe('all');

    act(() => {
      result.current.cycleRepeatMode(); // all -> one
    });
    expect(result.current.repeatMode).toBe('one');

    act(() => {
      result.current.cycleRepeatMode(); // one -> off
    });
    expect(result.current.repeatMode).toBe('off');
  });
});
