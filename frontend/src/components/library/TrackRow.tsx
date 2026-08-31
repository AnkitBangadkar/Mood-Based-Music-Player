import React from 'react';
import { Play, Plus } from 'lucide-react';
import { Track } from '../../api';
import { DeterministicCover } from '../common/DeterministicCover';
import { formatDuration } from '../../utils/colors';
import { useAudioPlayer } from '../../context/AudioPlayerContext';

interface TrackRowProps {
  track: Track;
  index: number;
  allTracks?: Track[];
}

export const TrackRow: React.FC<TrackRowProps> = ({ track, index, allTracks }) => {
  const { currentTrack, isPlaying, playTrack, addToQueue } = useAudioPlayer();

  const isCurrent = currentTrack?.id === track.id;

  return (
    <tr
      className={`group border-b border-background-border/30 hover:bg-background-hover/60 transition-colors text-sm ${
        isCurrent ? 'bg-brand-500/10' : ''
      }`}
      data-testid={`track-row-${track.id}`}
    >
      {/* Play / Index */}
      <td className="py-3 px-3 w-12 text-center text-xs font-mono text-gray-500">
        <div className="relative flex items-center justify-center">
          <span
            className={`group-hover:hidden group-focus-within:hidden ${
              isCurrent ? 'text-brand-400 font-semibold' : ''
            }`}
          >
            {isCurrent && isPlaying ? (
              <span className="inline-block w-2.5 h-2.5 rounded-full bg-brand-400 animate-pulse" />
            ) : (
              index + 1
            )}
          </span>
          <button
            onClick={() => playTrack(track, allTracks)}
            className="hidden group-hover:flex group-focus-within:flex items-center justify-center p-1 rounded bg-brand-500 text-background-darker hover:bg-brand-400 transition-all shadow focus-visible:ring-2 focus-visible:ring-brand-400 focus:outline-hidden"
            title="Play track"
            aria-label={`Play ${track.title}`}
          >
            <Play className="w-3 h-3 fill-current ml-0.5" />
          </button>
        </div>
      </td>

      {/* Title & Cover */}
      <td className="py-3 px-3">
        <div className="flex items-center gap-3">
          <DeterministicCover
            title={track.title}
            artist={track.artist}
            album={track.album}
            size="sm"
          />
          <div className="min-w-0">
            <p
              className={`font-medium truncate ${
                isCurrent ? 'text-brand-300 font-semibold' : 'text-gray-100'
              }`}
            >
              {track.title}
            </p>
            <p className="text-xs text-gray-400 truncate md:hidden">
              {track.artist} {track.album ? `• ${track.album}` : ''}
            </p>
          </div>
        </div>
      </td>

      {/* Artist */}
      <td className="py-3 px-3 hidden md:table-cell text-gray-300 truncate max-w-[180px]">
        {track.artist || 'Unknown Artist'}
      </td>

      {/* Album */}
      <td className="py-3 px-3 hidden lg:table-cell text-gray-400 truncate max-w-[200px]">
        {track.album || '—'}
      </td>

      {/* Genre */}
      <td className="py-3 px-3 hidden sm:table-cell">
        {track.genre ? (
          <span className="inline-block px-2 py-0.5 text-xs rounded-full bg-background-card border border-background-border text-gray-300">
            {track.genre}
          </span>
        ) : (
          <span className="text-gray-500 text-xs">—</span>
        )}
      </td>

      {/* Year */}
      <td className="py-3 px-3 hidden xl:table-cell text-xs text-gray-400 font-mono">
        {track.year ?? '—'}
      </td>

      {/* Duration */}
      <td className="py-3 px-3 text-right text-xs text-gray-400 font-mono">
        {formatDuration(track.duration_seconds)}
      </td>

      {/* Actions */}
      <td className="py-3 px-3 text-right w-16">
        <button
          onClick={() => addToQueue(track)}
          title="Add to queue"
          className="p-1.5 text-gray-400 hover:text-brand-300 hover:bg-background-hover rounded-lg transition-colors opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 focus-visible:opacity-100 focus-visible:ring-2 focus-visible:ring-brand-400 focus:outline-hidden"
          aria-label={`Add ${track.title} to queue`}
        >
          <Plus className="w-4 h-4" />
        </button>
      </td>
    </tr>
  );
};
