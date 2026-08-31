import React, { useRef } from 'react';
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Shuffle,
  Repeat,
  Repeat1,
  Volume2,
  VolumeX,
  ListMusic,
} from 'lucide-react';
import { useAudioPlayer } from '../../context/AudioPlayerContext';
import { DeterministicCover } from '../common/DeterministicCover';
import { FeedbackButtons } from '../generator/FeedbackButtons';
import { formatDuration } from '../../utils/colors';

export const PersistentPlayer: React.FC = () => {
  const {
    currentTrack,
    queue,
    isPlaying,
    currentTime,
    duration,
    volume,
    isMuted,
    repeatMode,
    isShuffled,
    activePlaylistId,
    togglePlay,
    playNext,
    playPrevious,
    seek,
    setVolume,
    toggleMute,
    toggleShuffle,
    cycleRepeatMode,
    toggleQueueDrawer,
  } = useAudioPlayer();

  const progressSliderRef = useRef<HTMLInputElement | null>(null);

  if (!currentTrack && queue.length === 0) {
    return (
      <div className="fixed bottom-0 left-0 right-0 h-20 bg-background-card/90 border-t border-background-border backdrop-blur-lg flex items-center justify-between px-6 z-30 text-gray-500 text-sm">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-lg bg-background-hover border border-background-border/50 flex items-center justify-center text-gray-600">
            ♪
          </div>
          <div>
            <p className="text-gray-400 font-medium">No track selected</p>
            <p className="text-xs text-gray-600">Choose a song from your library or generate a playlist</p>
          </div>
        </div>
      </div>
    );
  }

  const handleSeekChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseFloat(e.target.value);
    seek(val);
  };

  const progressPercent = duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <footer
      className="fixed bottom-0 left-0 right-0 h-24 bg-background-card/95 border-t border-background-border backdrop-blur-xl flex items-center justify-between px-4 md:px-8 z-30 shadow-2xl transition-all select-none"
      data-testid="persistent-player"
    >
      {/* Left: Current Track Details */}
      <div className="flex items-center gap-3 min-w-0 w-1/4 max-w-[280px] md:max-w-[320px]">
        {currentTrack && (
          <>
            <DeterministicCover
              title={currentTrack.title}
              artist={currentTrack.artist}
              album={currentTrack.album}
              size="md"
            />
            <div className="min-w-0 flex-1">
              <p className="text-sm font-semibold text-gray-100 truncate hover:text-brand-300 transition-colors">
                {currentTrack.title}
              </p>
              <p className="text-xs text-gray-400 truncate">
                {currentTrack.artist} {currentTrack.album ? `• ${currentTrack.album}` : ''}
              </p>
            </div>
            {activePlaylistId && (
              <div className="hidden sm:block">
                <FeedbackButtons
                  playlistId={activePlaylistId}
                  trackId={currentTrack.id}
                  size="sm"
                />
              </div>
            )}
          </>
        )}
      </div>

      {/* Center: Playback Controls & Timeline */}
      <div className="flex flex-col items-center flex-1 max-w-xl px-2 md:px-6">
        {/* Buttons */}
        <div className="flex items-center gap-4 mb-1.5">
          {/* Shuffle Toggle */}
          <button
            onClick={toggleShuffle}
            title={isShuffled ? 'Shuffle is ON' : 'Shuffle is OFF'}
            aria-label={isShuffled ? 'Disable shuffle' : 'Enable shuffle'}
            className={`p-1.5 rounded-lg transition-colors focus-visible:ring-2 focus-visible:ring-brand-400 focus:outline-hidden ${
              isShuffled
                ? 'text-brand-400 bg-brand-500/10'
                : 'text-gray-400 hover:text-gray-200 hover:bg-background-hover'
            }`}
          >
            <Shuffle className="w-4 h-4" />
          </button>

          {/* Previous */}
          <button
            onClick={playPrevious}
            title="Previous Track"
            aria-label="Previous Track"
            className="p-1.5 text-gray-300 hover:text-white hover:bg-background-hover rounded-lg transition-colors active:scale-95 focus-visible:ring-2 focus-visible:ring-brand-400 focus:outline-hidden"
          >
            <SkipBack className="w-5 h-5 fill-current" />
          </button>

          {/* Play / Pause Primary */}
          <button
            onClick={togglePlay}
            title={isPlaying ? 'Pause' : 'Play'}
            aria-label={isPlaying ? 'Pause' : 'Play'}
            className="w-10 h-10 rounded-full bg-brand-500 hover:bg-brand-400 text-background-darker flex items-center justify-center shadow-lg hover:shadow-brand-500/25 transition-all transform active:scale-95 focus-visible:ring-2 focus-visible:ring-brand-400 focus:outline-hidden"
          >
            {isPlaying ? (
              <Pause className="w-5 h-5 fill-current" />
            ) : (
              <Play className="w-5 h-5 fill-current ml-0.5" />
            )}
          </button>

          {/* Next */}
          <button
            onClick={playNext}
            title="Next Track"
            aria-label="Next Track"
            className="p-1.5 text-gray-300 hover:text-white hover:bg-background-hover rounded-lg transition-colors active:scale-95 focus-visible:ring-2 focus-visible:ring-brand-400 focus:outline-hidden"
          >
            <SkipForward className="w-5 h-5 fill-current" />
          </button>

          {/* Repeat Mode */}
          <button
            onClick={cycleRepeatMode}
            title={`Repeat: ${repeatMode}`}
            aria-label={`Cycle repeat mode (currently ${repeatMode})`}
            className={`p-1.5 rounded-lg transition-colors focus-visible:ring-2 focus-visible:ring-brand-400 focus:outline-hidden ${
              repeatMode !== 'off'
                ? 'text-brand-400 bg-brand-500/10'
                : 'text-gray-400 hover:text-gray-200 hover:bg-background-hover'
            }`}
          >
            {repeatMode === 'one' ? (
              <Repeat1 className="w-4 h-4" />
            ) : (
              <Repeat className="w-4 h-4" />
            )}
          </button>
        </div>

        {/* Progress Bar */}
        <div className="w-full flex items-center gap-2 text-[11px] font-mono text-gray-400">
          <span className="w-10 text-right">{formatDuration(currentTime)}</span>
          <div className="relative flex-1 group flex items-center h-4 cursor-pointer">
            <div className="w-full h-1.5 bg-background-hover rounded-full overflow-hidden">
              <div
                className="h-full bg-brand-400 group-hover:bg-brand-300 transition-all rounded-full"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
            <input
              ref={progressSliderRef}
              type="range"
              min={0}
              max={duration || 100}
              value={currentTime || 0}
              onChange={handleSeekChange}
              step={0.1}
              aria-label="Seek track playback position"
              aria-valuemin={0}
              aria-valuemax={Math.round(duration || 100)}
              aria-valuenow={Math.round(currentTime || 0)}
              aria-valuetext={`${formatDuration(currentTime)} of ${formatDuration(duration)}`}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer focus-visible:opacity-100 focus-visible:ring-2 focus-visible:ring-brand-400"
            />
          </div>
          <span className="w-10 text-left">{formatDuration(duration)}</span>
        </div>
      </div>

      {/* Right: Volume & Queue Actions */}
      <div className="flex items-center justify-end gap-3 w-1/4 max-w-[240px]">
        {/* Volume Slider */}
        <div className="hidden md:flex items-center gap-2 group">
          <button
            onClick={toggleMute}
            className="text-gray-400 hover:text-white p-1 transition-colors rounded-md focus-visible:ring-2 focus-visible:ring-brand-400 focus:outline-hidden"
            title={isMuted ? 'Unmute' : 'Mute'}
            aria-label={isMuted ? 'Unmute volume' : 'Mute volume'}
          >
            {isMuted || volume === 0 ? (
              <VolumeX className="w-4 h-4 text-rose-400" />
            ) : (
              <Volume2 className="w-4 h-4" />
            )}
          </button>
          <div className="w-20 relative flex items-center">
            <input
              type="range"
              min={0}
              max={1}
              step={0.01}
              value={isMuted ? 0 : volume}
              onChange={(e) => setVolume(parseFloat(e.target.value))}
              aria-label="Volume control"
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={Math.round((isMuted ? 0 : volume) * 100)}
              className="w-full h-1.5 bg-background-hover accent-brand-400 rounded-full appearance-none cursor-pointer focus-visible:ring-2 focus-visible:ring-brand-400 focus:outline-hidden"
            />
          </div>
        </div>

        {/* Queue Drawer Trigger */}
        <button
          onClick={toggleQueueDrawer}
          title="Open Queue"
          className="relative p-2 text-gray-300 hover:text-brand-300 hover:bg-background-hover rounded-lg transition-colors focus-visible:ring-2 focus-visible:ring-brand-400 focus:outline-hidden"
          aria-label={`Toggle play queue (${queue.length} items)`}
        >
          <ListMusic className="w-5 h-5" />
          {queue.length > 0 && (
            <span className="absolute -top-1 -right-1 bg-brand-500 text-background-darker font-bold text-[10px] w-4 h-4 rounded-full flex items-center justify-center">
              {queue.length > 99 ? '99+' : queue.length}
            </span>
          )}
        </button>
      </div>
    </footer>
  );
};
