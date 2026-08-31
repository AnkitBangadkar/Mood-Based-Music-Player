import React from 'react';
import { Play, Plus, Tag } from 'lucide-react';
import { PlaylistTrackResponse } from '../../api';
import { DeterministicCover } from '../common/DeterministicCover';
import { ScoreBadge } from '../common/ScoreBadge';
import { FeedbackButtons } from './FeedbackButtons';
import { formatDuration } from '../../utils/colors';
import { useAudioPlayer } from '../../context/AudioPlayerContext';

interface PlaylistTrackItemProps {
  track: PlaylistTrackResponse;
  playlistId: string;
  allTracks: PlaylistTrackResponse[];
}

export const PlaylistTrackItem: React.FC<PlaylistTrackItemProps> = ({
  track,
  playlistId,
  allTracks,
}) => {
  const { currentTrack, isPlaying, playTrack, addToQueue } = useAudioPlayer();

  const isCurrent = currentTrack?.id === track.id;

  return (
    <div
      className={`content-auto group p-3.5 rounded-xl border transition-all duration-200 ${
        isCurrent
          ? 'bg-brand-500/10 border-brand-500/40 shadow-lg shadow-brand-950/20'
          : 'bg-background-card/70 hover:bg-background-hover/90 hover:-translate-y-0.5 hover:shadow-lg border-white/5 hover:border-brand-400/20'
      }`}
      data-testid={`playlist-track-${track.id}`}
    >
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        {/* Track Main Info */}
        <div className="flex items-center gap-3.5 flex-1 min-w-0">
          {/* Position & Play */}
          <div className="relative flex items-center justify-center w-8 text-center shrink-0">
            <span
              className={`text-xs font-mono font-bold text-gray-500 group-hover:hidden group-focus-within:hidden ${
                isCurrent ? 'text-brand-400' : ''
              }`}
            >
              {isCurrent && isPlaying ? (
                <span className="inline-block w-2.5 h-2.5 rounded-full bg-brand-400 animate-pulse" />
              ) : (
                `#${track.position}`
              )}
            </span>
            <button
              onClick={() => playTrack(track, allTracks, playlistId)}
              className="hidden group-hover:flex group-focus-within:flex items-center justify-center w-7 h-7 rounded-full bg-brand-500 text-background-darker hover:bg-brand-400 transition-all shadow focus-visible:ring-2 focus-visible:ring-brand-400 focus:outline-hidden"
              title="Play track"
              aria-label={`Play ${track.title}`}
            >
              <Play className="w-3.5 h-3.5 fill-current ml-0.5" />
            </button>
          </div>

          {/* Cover */}
          <DeterministicCover
            title={track.title}
            artist={track.artist}
            album={track.album}
            size="md"
          />

          {/* Title / Artist / Album */}
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <h4
                className={`font-semibold text-sm truncate ${
                  isCurrent ? 'text-brand-300' : 'text-gray-100'
                }`}
              >
                {track.title}
              </h4>
              {track.year && (
                <span className="text-[11px] font-mono text-gray-500 shrink-0">
                  ({track.year})
                </span>
              )}
            </div>
            <p className="text-xs text-gray-400 truncate mt-0.5">
              <span className="text-gray-300 font-medium">{track.artist}</span>
              {track.album ? ` • ${track.album}` : ''}
              {track.genre ? ` • ${track.genre}` : ''}
            </p>
          </div>
        </div>

        {/* Badges & Actions */}
        <div className="flex flex-wrap items-center justify-between sm:justify-end gap-2 w-full sm:w-auto shrink-0 pl-11 sm:pl-0">
          {/* Relative Utility Score (Never confidence percentage!) */}
          <ScoreBadge score={track.score} />

          {/* Duration */}
          <span className="text-xs text-gray-400 font-mono">
            {formatDuration(track.duration_seconds)}
          </span>

          {/* Action: Add to Queue */}
          <button
            onClick={() => addToQueue(track)}
            title="Add to queue"
            className="p-1.5 text-gray-400 hover:text-brand-300 hover:bg-background-hover rounded-lg transition-colors focus-visible:ring-2 focus-visible:ring-brand-400 focus:outline-hidden"
            aria-label={`Add ${track.title} to queue`}
          >
            <Plus className="w-4 h-4" />
          </button>

          {/* Fire-and-forget Feedback (Like / Dislike / Skip) */}
          <FeedbackButtons
            playlistId={playlistId}
            trackId={track.id}
            size="sm"
          />
        </div>
      </div>

      {/* Reasons breakdown */}
      {track.reasons && track.reasons.length > 0 && (
        <div className="mt-2.5 pt-2 border-t border-background-border/30 flex flex-wrap items-center gap-1.5 pl-11">
          <Tag className="w-3 h-3 text-brand-400/70 shrink-0" />
          <span className="text-[11px] text-gray-400 mr-1">Match factors:</span>
          {track.reasons.map((reason, idx) => (
            <span
              key={idx}
              className="text-[11px] px-2 py-0.5 rounded-md bg-background-darker/70 border border-background-border/50 text-gray-300"
            >
              {reason}
            </span>
          ))}
        </div>
      )}
    </div>
  );
};
