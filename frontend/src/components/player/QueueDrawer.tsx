import React from 'react';
import { X, Play, Trash2, Music2 } from 'lucide-react';
import { useAudioPlayer } from '../../context/AudioPlayerContext';
import { DeterministicCover } from '../common/DeterministicCover';
import { formatDuration } from '../../utils/colors';

export const QueueDrawer: React.FC = () => {
  const {
    queue,
    queueIndex,
    isQueueOpen,
    closeQueueDrawer,
    playTrack,
    removeFromQueue,
    clearQueue,
  } = useAudioPlayer();

  if (!isQueueOpen) return null;

  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-black/50 backdrop-blur-xs transition-opacity animate-fade-in">
      <div
        className="w-full max-w-md bg-background-card border-l border-background-border h-full flex flex-col shadow-2xl p-4 overflow-hidden"
        data-testid="queue-drawer"
        role="dialog"
        aria-label="Playback Queue"
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-background-border">
          <div className="flex items-center gap-2">
            <Music2 className="w-5 h-5 text-brand-400" />
            <h2 className="text-lg font-bold text-gray-100">Playback Queue</h2>
            <span className="text-xs bg-background-hover text-gray-400 px-2 py-0.5 rounded-full">
              {queue.length} tracks
            </span>
          </div>
          <div className="flex items-center gap-2">
            {queue.length > 0 && (
              <button
                onClick={clearQueue}
                title="Clear entire queue"
                aria-label="Clear entire playback queue"
                className="p-1.5 text-xs text-gray-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors flex items-center gap-1 focus-visible:ring-2 focus-visible:ring-brand-400 focus:outline-hidden"
              >
                <Trash2 className="w-4 h-4" />
                <span>Clear</span>
              </button>
            )}
            <button
              onClick={closeQueueDrawer}
              className="p-1.5 text-gray-400 hover:text-white hover:bg-background-hover rounded-lg transition-colors focus-visible:ring-2 focus-visible:ring-brand-400 focus:outline-hidden"
              aria-label="Close queue drawer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Tracks List */}
        <div className="flex-1 overflow-y-auto py-2 divide-y divide-background-border/40">
          {queue.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-gray-500 py-12 text-center">
              <Music2 className="w-12 h-12 stroke-1 mb-2 opacity-40" />
              <p className="text-sm font-medium">Your queue is empty</p>
              <p className="text-xs text-gray-600 mt-1">
                Generate a playlist or browse tracks to start listening
              </p>
            </div>
          ) : (
            queue.map((track, idx) => {
              const isCurrent = idx === queueIndex;
              return (
                <div
                  key={`${track.id}-${idx}`}
                  className={`group flex items-center gap-3 p-2.5 rounded-lg transition-all ${
                    isCurrent
                      ? 'bg-brand-500/15 border-l-4 border-brand-400 text-white'
                      : 'hover:bg-background-hover text-gray-300'
                  }`}
                >
                  <span className="w-5 text-center text-xs text-gray-500 font-mono">
                    {isCurrent ? (
                      <span className="inline-block w-2 h-2 rounded-full bg-brand-400 animate-pulse" />
                    ) : (
                      idx + 1
                    )}
                  </span>

                  <DeterministicCover
                    title={track.title}
                    artist={track.artist}
                    album={track.album}
                    size="sm"
                  />

                  <div className="flex-1 min-w-0">
                    <p
                      className={`text-sm font-medium truncate ${
                        isCurrent ? 'text-brand-300 font-semibold' : 'text-gray-100'
                      }`}
                    >
                      {track.title}
                    </p>
                    <p className="text-xs text-gray-400 truncate">
                      {track.artist} • {track.album}
                    </p>
                  </div>

                  <span className="text-xs text-gray-500 font-mono">
                    {formatDuration(track.duration_seconds)}
                  </span>

                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 transition-opacity">
                    {!isCurrent && (
                      <button
                        onClick={() => playTrack(track, queue)}
                        title="Play now"
                        aria-label={`Play ${track.title}`}
                        className="p-1 text-gray-400 hover:text-brand-400 hover:bg-brand-500/20 rounded focus-visible:ring-2 focus-visible:ring-brand-400 focus:outline-hidden"
                      >
                        <Play className="w-3.5 h-3.5 fill-current" />
                      </button>
                    )}
                    <button
                      onClick={() => removeFromQueue(idx)}
                      title="Remove from queue"
                      aria-label={`Remove ${track.title} from queue`}
                      className="p-1 text-gray-400 hover:text-rose-400 hover:bg-rose-500/20 rounded focus-visible:ring-2 focus-visible:ring-brand-400 focus:outline-hidden"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
