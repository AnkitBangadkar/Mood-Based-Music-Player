import React from 'react';
import { Play, Sparkles, Ban, CheckCircle, Clock, Music2, Share2, HelpCircle, Timer } from 'lucide-react';
import { PlaylistResponse } from '../../api';
import { PlaylistTrackItem } from './PlaylistTrackItem';
import { FeedbackButtons } from './FeedbackButtons';
import { formatDuration } from '../../utils/colors';
import { useAudioPlayer } from '../../context/AudioPlayerContext';
import { useNotification } from '../../context/NotificationContext';

interface PlaylistViewProps {
  playlist: PlaylistResponse;
  generationMs?: number | null;
}

export const PlaylistView: React.FC<PlaylistViewProps> = ({ playlist, generationMs }) => {
  const { playPlaylist } = useAudioPlayer();
  const { showSuccess } = useNotification();

  const totalDuration = playlist.tracks.reduce(
    (acc, t) => acc + (t.duration_seconds || 0),
    0
  );

  const handlePlayAll = () => {
    if (playlist.tracks.length > 0) {
      playPlaylist(playlist.tracks, 0, playlist.playlist_id);
    }
  };

  const handleCopySummary = () => {
    const summary = `SoulSeek Playlist: "${playlist.prompt}"\nTracks (${playlist.tracks.length}):\n` +
      playlist.tracks.map((t, i) => `${i + 1}. ${t.title} - ${t.artist}`).join('\n');
    navigator.clipboard.writeText(summary);
    showSuccess('Copied to Clipboard', 'Playlist summary copied successfully.');
  };

  return (
    <div className="space-y-6 animate-fade-in" data-testid="playlist-view">
      {/* Header Banner */}
      <div className="glass-panel bg-gradient-to-r from-brand-900/40 via-background-card/90 to-indigo-950/30 border-brand-500/30 rounded-2xl p-6 relative overflow-hidden">
        <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="space-y-2 max-w-2xl">
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-brand-500/20 text-brand-300 border border-brand-500/30">
                <Sparkles className="w-3.5 h-3.5" />
                Generated Playlist
              </span>
              <span className="text-xs font-mono text-gray-500">
                ID: {playlist.playlist_id.substring(0, 8)}
              </span>
            </div>

            <h2 className="text-xl md:text-2xl font-bold text-gray-100 italic">
              "{playlist.prompt}"
            </h2>

            {/* Parsed Intent & Exclusions */}
            <div className="flex flex-wrap items-center gap-2 pt-1">
              {playlist.intent.desired_text && (
                <div className="inline-flex items-center gap-1.5 text-xs bg-background-darker/80 border border-background-border px-3 py-1 rounded-lg text-gray-300">
                  <CheckCircle className="w-3.5 h-3.5 text-brand-400" />
                  <span className="text-gray-400">Target Focus:</span>
                  <span className="font-medium text-gray-200">{playlist.intent.desired_text}</span>
                </div>
              )}

              {playlist.intent.exclusions && playlist.intent.exclusions.length > 0 && (
                <div className="inline-flex items-center gap-1.5 text-xs bg-rose-950/40 border border-rose-500/30 px-3 py-1 rounded-lg text-rose-300">
                  <Ban className="w-3.5 h-3.5 text-rose-400 shrink-0" />
                  <span className="text-rose-400 font-semibold">Exclusions:</span>
                  <div className="flex flex-wrap gap-1">
                    {playlist.intent.exclusions.map((exc, idx) => (
                      <span
                        key={idx}
                        className="bg-rose-500/20 px-1.5 py-0.5 rounded text-[11px] font-mono text-rose-200"
                      >
                        -{exc}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex flex-wrap items-center gap-3 shrink-0">
            <button
              onClick={handlePlayAll}
              disabled={playlist.tracks.length === 0}
              aria-label="Play all tracks in playlist"
              className="px-5 py-2.5 rounded-xl bg-brand-500 hover:bg-brand-400 text-background-darker font-bold text-sm shadow-lg shadow-brand-500/20 flex items-center gap-2 transition-all active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed focus-visible:ring-2 focus-visible:ring-brand-400 focus:outline-hidden"
            >
              <Play className="w-4 h-4 fill-current ml-0.5" />
              <span>Play All</span>
            </button>

            <button
              onClick={handleCopySummary}
              title="Copy playlist tracklist"
              aria-label="Copy playlist tracklist"
              className="p-2.5 rounded-xl bg-background-hover hover:bg-background-border text-gray-300 hover:text-white transition-colors border border-background-border focus-visible:ring-2 focus-visible:ring-brand-400 focus:outline-hidden"
            >
              <Share2 className="w-4 h-4" />
            </button>

            {/* Playlist-level Feedback */}
            <FeedbackButtons
              playlistId={playlist.playlist_id}
              trackId={null}
              size="md"
            />
          </div>
        </div>

        {/* Stats strip */}
        <div className="mt-4 pt-4 border-t border-background-border/40 flex items-center gap-4 text-xs text-gray-400">
          <div className="flex items-center gap-1.5">
            <Music2 className="w-4 h-4 text-brand-400" />
            <span className="font-semibold text-gray-200">{playlist.tracks.length}</span> tracks
          </div>
          <span>•</span>
          <div className="flex items-center gap-1.5">
            <Clock className="w-4 h-4 text-brand-400" />
            <span>Total Duration:</span>
            <span className="font-mono text-gray-200">{formatDuration(totalDuration)}</span>
          </div>
          {generationMs !== null && generationMs !== undefined && (
            <>
              <span>•</span>
              <div className="flex items-center gap-1.5" data-testid="generation-time">
                <Timer className="w-4 h-4 text-brand-400" />
                <span>Generated in:</span>
                <span className="font-mono text-gray-200">
                  {generationMs < 1000
                    ? `${Math.round(generationMs)} ms`
                    : `${(generationMs / 1000).toFixed(2)} s`}
                </span>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Tracks List */}
      <div className="space-y-2.5">
        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider px-1">
          Ranked Tracks & Intent Match Justifications
        </h3>

        {playlist.tracks.length === 0 ? (
          <div className="p-8 text-center bg-background-card/40 border border-background-border rounded-2xl space-y-2">
            <HelpCircle className="w-8 h-8 text-gray-500 mx-auto" />
            <p className="text-sm font-medium text-gray-300">No tracks match this criteria</p>
            <p className="text-xs text-gray-500 max-w-sm mx-auto">
              Try adjusting your prompt, broadening descriptions, or scanning more audio files into your library.
            </p>
          </div>
        ) : (
          playlist.tracks.map((track) => (
            <PlaylistTrackItem
              key={track.id}
              track={track}
              playlistId={playlist.playlist_id}
              allTracks={playlist.tracks}
            />
          ))
        )}
      </div>
    </div>
  );
};
