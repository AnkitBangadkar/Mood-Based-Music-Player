import React, { createContext, useContext, useState, useRef, useEffect, useCallback } from 'react';
import { Track, api } from '../api';
import { useNotification } from './NotificationContext';

export type RepeatMode = 'off' | 'all' | 'one';

interface AudioPlayerContextType {
  currentTrack: Track | null;
  queue: Track[];
  queueIndex: number;
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  volume: number;
  isMuted: boolean;
  repeatMode: RepeatMode;
  isShuffled: boolean;
  activePlaylistId: string | null;
  isQueueOpen: boolean;
  playTrack: (track: Track, newQueue?: Track[], playlistId?: string | null) => void;
  playPlaylist: (tracks: Track[], startIndex?: number, playlistId?: string | null) => void;
  togglePlay: () => void;
  pause: () => void;
  resume: () => void;
  playNext: () => void;
  playPrevious: () => void;
  seek: (seconds: number) => void;
  setVolume: (vol: number) => void;
  toggleMute: () => void;
  toggleShuffle: () => void;
  cycleRepeatMode: () => void;
  addToQueue: (track: Track) => void;
  removeFromQueue: (index: number) => void;
  clearQueue: () => void;
  toggleQueueDrawer: () => void;
  closeQueueDrawer: () => void;
}

const AudioPlayerContext = createContext<AudioPlayerContextType | undefined>(undefined);

export const AudioPlayerProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentTrack, setCurrentTrack] = useState<Track | null>(null);
  const [queue, setQueue] = useState<Track[]>([]);
  const [queueIndex, setQueueIndex] = useState<number>(-1);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolumeState] = useState(0.85);
  const [isMuted, setIsMuted] = useState(false);
  const [repeatMode, setRepeatMode] = useState<RepeatMode>('off');
  const [isShuffled, setIsShuffled] = useState(false);
  const [activePlaylistId, setActivePlaylistId] = useState<string | null>(null);
  const [isQueueOpen, setIsQueueOpen] = useState(false);

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const errorAdvanceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const failedTrackIdsRef = useRef(new Set<string>());
  const currentTrackRef = useRef<Track | null>(null);
  currentTrackRef.current = currentTrack;
  
  const queueRef = useRef<Track[]>([]);
  queueRef.current = queue;

  const queueIndexRef = useRef<number>(-1);
  queueIndexRef.current = queueIndex;

  const { showError, showInfo } = useNotification();

  const loadAndPlayTrack = useCallback((track: Track) => {
    if (!audioRef.current) return;
    // Use audio_url verbatim without filesystem alteration
    const url = api.getAudioUrl(track.audio_url);
    audioRef.current.src = url;
    audioRef.current.load();
    audioRef.current
      .play()
      .catch((err) => {
        // Handled via audio 'error' event or autoplay restrictions
        console.warn('Playback error:', err);
      });
  }, []);

  const playNext = useCallback(() => {
    const q = queueRef.current;
    const qIdx = queueIndexRef.current;
    if (q.length === 0) return;

    if (repeatMode === 'one' && currentTrackRef.current) {
      if (audioRef.current) {
        audioRef.current.currentTime = 0;
        audioRef.current.play().catch(console.warn);
      }
      return;
    }

    let nextIndex: number;
    if (isShuffled && q.length > 1) {
      do {
        nextIndex = Math.floor(Math.random() * q.length);
      } while (nextIndex === qIdx && q.length > 1);
    } else {
      nextIndex = qIdx + 1;
    }

    if (nextIndex < q.length) {
      const nextTrack = q[nextIndex];
      setQueueIndex(nextIndex);
      setCurrentTrack(nextTrack);
      loadAndPlayTrack(nextTrack);
    } else if (repeatMode === 'all' && q.length > 0) {
      const firstTrack = q[0];
      setQueueIndex(0);
      setCurrentTrack(firstTrack);
      loadAndPlayTrack(firstTrack);
    } else {
      setIsPlaying(false);
    }
  }, [repeatMode, isShuffled, loadAndPlayTrack]);

  const playNextRef = useRef(playNext);
  playNextRef.current = playNext;

  const skipFailedTrack = useCallback(() => {
    const q = queueRef.current;
    const currentIndex = queueIndexRef.current;
    const failedIds = failedTrackIdsRef.current;

    for (let offset = 1; offset <= q.length; offset += 1) {
      const candidateIndex = currentIndex + offset;
      const canWrap = repeatMode !== 'off';
      if (!canWrap && candidateIndex >= q.length) break;

      const nextIndex = candidateIndex % q.length;
      const nextTrack = q[nextIndex];
      if (!failedIds.has(nextTrack.id)) {
        setQueueIndex(nextIndex);
        setCurrentTrack(nextTrack);
        loadAndPlayTrack(nextTrack);
        return;
      }
    }

    setIsPlaying(false);
  }, [repeatMode, loadAndPlayTrack]);

  const skipFailedTrackRef = useRef(skipFailedTrack);
  skipFailedTrackRef.current = skipFailedTrack;

  // Create persistent single audio element once
  useEffect(() => {
    const audio = new Audio();
    audio.preload = 'auto';
    audioRef.current = audio;
    if (audio instanceof HTMLElement) {
      audio.hidden = true;
      audio.dataset.soulseekPlayer = 'true';
      document.body.appendChild(audio);
    }

    const onPlay = () => setIsPlaying(true);
    const onPause = () => setIsPlaying(false);
    const onTimeUpdate = () => {
      if (audio.currentTime !== undefined) {
        setCurrentTime(audio.currentTime);
      }
    };
    const onLoadedMetadata = () => {
      if (audio.duration && !isNaN(audio.duration)) {
        setDuration(audio.duration);
      }
    };
    const onEnded = () => {
      playNextRef.current();
    };
    const onError = () => {
      setIsPlaying(false);
      const track = currentTrackRef.current;
      const trackTitle = track?.title || 'Unknown Track';
      if (track) failedTrackIdsRef.current.add(track.id);
      showError(
        'Playback Error',
        `Unable to stream "${trackTitle}". Audio file may be missing (410) or not found (404). Advancing to next track...`
      );
      // Advance safely to the next playable item
      if (errorAdvanceTimerRef.current) clearTimeout(errorAdvanceTimerRef.current);
      errorAdvanceTimerRef.current = setTimeout(() => {
        errorAdvanceTimerRef.current = null;
        skipFailedTrackRef.current();
      }, 500);
    };

    audio.addEventListener('play', onPlay);
    audio.addEventListener('pause', onPause);
    audio.addEventListener('timeupdate', onTimeUpdate);
    audio.addEventListener('loadedmetadata', onLoadedMetadata);
    audio.addEventListener('ended', onEnded);
    audio.addEventListener('error', onError);

    return () => {
      audio.removeEventListener('play', onPlay);
      audio.removeEventListener('pause', onPause);
      audio.removeEventListener('timeupdate', onTimeUpdate);
      audio.removeEventListener('loadedmetadata', onLoadedMetadata);
      audio.removeEventListener('ended', onEnded);
      audio.removeEventListener('error', onError);
      if (errorAdvanceTimerRef.current) clearTimeout(errorAdvanceTimerRef.current);
      audio.pause();
      audio.src = '';
      if (audio instanceof HTMLElement) audio.remove();
    };
  }, [showError]);

  // Sync volume and mute
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = isMuted ? 0 : volume;
    }
  }, [volume, isMuted]);

  const playTrack = useCallback(
    (track: Track, newQueue?: Track[], playlistId?: string | null) => {
      let targetQueue = newQueue || (queue.length > 0 ? queue : [track]);
      let index = targetQueue.findIndex((t) => t.id === track.id);
      if (index === -1) {
        targetQueue = [...targetQueue, track];
        index = targetQueue.length - 1;
      }
      setQueue(targetQueue);
      setQueueIndex(index);
      setCurrentTrack(track);
      failedTrackIdsRef.current.delete(track.id);
      if (playlistId !== undefined) {
        setActivePlaylistId(playlistId);
      }
      loadAndPlayTrack(track);
    },
    [queue, loadAndPlayTrack]
  );

  const playPlaylist = useCallback(
    (tracks: Track[], startIndex: number = 0, playlistId?: string | null) => {
      if (tracks.length === 0) return;
      const safeIndex = Math.max(0, Math.min(startIndex, tracks.length - 1));
      setQueue(tracks);
      setQueueIndex(safeIndex);
      setCurrentTrack(tracks[safeIndex]);
      failedTrackIdsRef.current.clear();
      setActivePlaylistId(playlistId || null);
      loadAndPlayTrack(tracks[safeIndex]);
    },
    [loadAndPlayTrack]
  );

  const playPrevious = useCallback(() => {
    if (!audioRef.current || queue.length === 0) return;

    if (audioRef.current.currentTime > 3) {
      audioRef.current.currentTime = 0;
      return;
    }

    const prevIndex = queueIndex - 1;
    if (prevIndex >= 0) {
      const prevTrack = queue[prevIndex];
      setQueueIndex(prevIndex);
      setCurrentTrack(prevTrack);
      loadAndPlayTrack(prevTrack);
    } else if (repeatMode === 'all') {
      const lastIndex = queue.length - 1;
      const lastTrack = queue[lastIndex];
      setQueueIndex(lastIndex);
      setCurrentTrack(lastTrack);
      loadAndPlayTrack(lastTrack);
    } else {
      audioRef.current.currentTime = 0;
    }
  }, [queue, queueIndex, repeatMode, loadAndPlayTrack]);

  const togglePlay = useCallback(() => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      if (!currentTrack && queue.length > 0) {
        playTrack(queue[0], queue);
      } else if (currentTrack) {
        audioRef.current.play().catch(console.warn);
      }
    }
  }, [isPlaying, currentTrack, queue, playTrack]);

  const pause = useCallback(() => {
    if (audioRef.current) audioRef.current.pause();
  }, []);

  const resume = useCallback(() => {
    if (audioRef.current) audioRef.current.play().catch(console.warn);
  }, []);

  const seek = useCallback((seconds: number) => {
    if (audioRef.current) {
      audioRef.current.currentTime = seconds;
      setCurrentTime(seconds);
    }
  }, []);

  const setVolume = useCallback((vol: number) => {
    const clamped = Math.max(0, Math.min(1, vol));
    setVolumeState(clamped);
    if (clamped > 0 && isMuted) {
      setIsMuted(false);
    }
  }, [isMuted]);

  const toggleMute = useCallback(() => {
    setIsMuted((prev) => !prev);
  }, []);

  const toggleShuffle = useCallback(() => {
    setIsShuffled((prev) => {
      const next = !prev;
      setTimeout(() => {
        showInfo(next ? 'Shuffle Enabled' : 'Shuffle Disabled');
      }, 0);
      return next;
    });
  }, [showInfo]);

  const cycleRepeatMode = useCallback(() => {
    setRepeatMode((prev) => {
      const next: RepeatMode = prev === 'off' ? 'all' : prev === 'all' ? 'one' : 'off';
      const label = next === 'all' ? 'Repeat All' : next === 'one' ? 'Repeat Track' : 'Repeat Off';
      setTimeout(() => {
        showInfo(label);
      }, 0);
      return next;
    });
  }, [showInfo]);

  const addToQueue = useCallback(
    (track: Track) => {
      setQueue((prev) => [...prev, track]);
      showInfo('Added to Queue', `${track.title} - ${track.artist}`);
      if (!currentTrack) {
        playTrack(track, [track]);
      }
    },
    [currentTrack, playTrack, showInfo]
  );

  const removeFromQueue = useCallback((index: number) => {
    const currentQueue = queueRef.current;
    const currentIndex = queueIndexRef.current;
    if (index < 0 || index >= currentQueue.length) return;

    const nextQueue = currentQueue.filter((_, itemIndex) => itemIndex !== index);
    setQueue(nextQueue);

    if (nextQueue.length === 0) {
      setQueueIndex(-1);
      setCurrentTrack(null);
      audioRef.current?.pause();
      if (audioRef.current) audioRef.current.src = '';
      return;
    }

    if (index < currentIndex) {
      setQueueIndex(currentIndex - 1);
      return;
    }

    if (index === currentIndex) {
      const nextIndex = Math.min(index, nextQueue.length - 1);
      const nextTrack = nextQueue[nextIndex];
      setQueueIndex(nextIndex);
      setCurrentTrack(nextTrack);
      failedTrackIdsRef.current.delete(nextTrack.id);
      loadAndPlayTrack(nextTrack);
    }
  }, [loadAndPlayTrack]);

  const clearQueue = useCallback(() => {
    setQueue([]);
    setQueueIndex(-1);
    setCurrentTrack(null);
    failedTrackIdsRef.current.clear();
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.src = '';
    }
    showInfo('Queue Cleared');
  }, [showInfo]);

  const toggleQueueDrawer = useCallback(() => {
    setIsQueueOpen((prev) => !prev);
  }, []);

  const closeQueueDrawer = useCallback(() => {
    setIsQueueOpen(false);
  }, []);

  return (
    <AudioPlayerContext.Provider
      value={{
        currentTrack,
        queue,
        queueIndex,
        isPlaying,
        currentTime,
        duration,
        volume,
        isMuted,
        repeatMode,
        isShuffled,
        activePlaylistId,
        isQueueOpen,
        playTrack,
        playPlaylist,
        togglePlay,
        pause,
        resume,
        playNext,
        playPrevious,
        seek,
        setVolume,
        toggleMute,
        toggleShuffle,
        cycleRepeatMode,
        addToQueue,
        removeFromQueue,
        clearQueue,
        toggleQueueDrawer,
        closeQueueDrawer,
      }}
    >
      {children}
    </AudioPlayerContext.Provider>
  );
};

export const useAudioPlayer = (): AudioPlayerContextType => {
  const context = useContext(AudioPlayerContext);
  if (!context) {
    throw new Error('useAudioPlayer must be used within an AudioPlayerProvider');
  }
  return context;
};
