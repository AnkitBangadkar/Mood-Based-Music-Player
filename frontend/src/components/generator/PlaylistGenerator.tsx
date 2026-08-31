import React, { useState } from 'react';
import {
  Sparkles,
  Sliders,
  AlertCircle,
  FolderPlus,
  RefreshCw,
  Lightbulb,
  Music,
} from 'lucide-react';
import { api, PlaylistResponse, ApiError } from '../../api';
import { PlaylistView } from './PlaylistView';
import { useNotification } from '../../context/NotificationContext';

interface PlaylistGeneratorProps {
  onNavigateToSetup: () => void;
}

const SAMPLE_PROMPTS = [
  'rainy evening drive',
  'late night lofi study session without vocals',
  'high energy electronic workout',
  'melancholic acoustic indie folk',
  'warm nostalgic 80s synthwave without drums',
  'chill jazz coffee morning',
];

export const PlaylistGenerator: React.FC<PlaylistGeneratorProps> = ({ onNavigateToSetup }) => {
  const [prompt, setPrompt] = useState('rainy evening drive');
  const [size, setSize] = useState<number>(20);
  const [playlist, setPlaylist] = useState<PlaylistResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLibraryNotIndexed, setIsLibraryNotIndexed] = useState(false);
  const [generationMs, setGenerationMs] = useState<number | null>(null);

  const { showError, showSuccess } = useNotification();

  const handleGenerate = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const cleanPrompt = prompt.trim();
    if (cleanPrompt.length < 2) {
      setError('Please enter a prompt with at least 2 characters');
      return;
    }

    setIsLoading(true);
    setError(null);
    setIsLibraryNotIndexed(false);
    setGenerationMs(null);
    const startedAt = performance.now();

    try {
      const response = await api.generatePlaylist({
        prompt: cleanPrompt,
        size,
      });
      setPlaylist(response);
      setGenerationMs(performance.now() - startedAt);
      showSuccess(
        'Playlist Generated',
        `Retrieved ${response.tracks.length} tracks matching "${cleanPrompt}"`
      );
    } catch (err: unknown) {
      if (err instanceof ApiError && err.isLibraryNotIndexed) {
        setIsLibraryNotIndexed(true);
        setError('The music library is not indexed yet. Please scan your library before generating playlists.');
      } else {
        const errorMsg = err instanceof Error ? err.message : 'Failed to generate playlist';
        setError(errorMsg);
        showError('Generator Error', errorMsg);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-y-auto p-6 max-w-5xl mx-auto w-full space-y-6">
      {/* Page Title */}
      <div>
        <h1 className="text-2xl font-bold text-gray-100 flex items-center gap-2">
          <Sparkles className="w-6 h-6 text-brand-400" />
          <span>Natural Language Playlist Generator</span>
        </h1>
        <p className="text-xs text-gray-400 mt-1">
          Describe the mood, vibe, tempo, or negative exclusions (e.g. “without vocals”) to create a cohesive playlist
        </p>
      </div>

      {/* 409 Library Not Indexed Alert Banner */}
      {isLibraryNotIndexed && (
        <div
          className="p-5 rounded-2xl bg-amber-950/40 border border-amber-500/40 shadow-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 animate-fade-in"
          data-testid="library-not-indexed-banner"
          role="alert"
        >
          <div className="flex items-start gap-3">
            <AlertCircle className="w-6 h-6 text-amber-400 shrink-0 mt-0.5" />
            <div>
              <h3 className="text-sm font-bold text-amber-200">Library Not Indexed (409)</h3>
              <p className="text-xs text-amber-300/90 mt-0.5 max-w-xl">
                The neural recommender requires indexed tracks and vector embeddings. Scan your local music folder first.
              </p>
            </div>
          </div>
          <button
            onClick={onNavigateToSetup}
            className="px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-background-darker font-bold text-xs shadow transition-all flex items-center gap-1.5 shrink-0 focus-visible:ring-2 focus-visible:ring-brand-400 focus:outline-hidden"
          >
            <FolderPlus className="w-4 h-4" />
            <span>Open Library Setup</span>
          </button>
        </div>
      )}

      {/* Prompt Form Card */}
      <div className="bg-background-card border border-background-border rounded-2xl p-6 shadow-xl space-y-5">
        <form onSubmit={handleGenerate} className="space-y-4" aria-label="Playlist generator form">
          <div>
            <label htmlFor="playlist-prompt-input" className="block text-xs font-semibold text-gray-300 mb-1.5">
              Natural Language Prompt & Exclusions
            </label>
            <div className="relative">
              <input
                id="playlist-prompt-input"
                type="text"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="e.g. rainy evening drive, upbeat workout without metal, cozy acoustic afternoon"
                maxLength={500}
                disabled={isLoading}
                aria-required="true"
                aria-invalid={!!error && !isLibraryNotIndexed}
                className="w-full bg-background-darker border border-background-border rounded-xl px-4 py-3 text-sm text-gray-100 placeholder-gray-600 focus-visible:ring-2 focus-visible:ring-brand-400 focus:outline-hidden transition-colors shadow-inner"
              />
              <span className="absolute right-3 top-3 text-[11px] font-mono text-gray-600">
                {prompt.length}/500
              </span>
            </div>
            {error && !isLibraryNotIndexed && (
              <p className="text-xs text-rose-400 mt-1.5 flex items-center gap-1">
                <AlertCircle className="w-3.5 h-3.5" />
                {error}
              </p>
            )}
          </div>

          {/* Prompt Suggestion Chips */}
          <div className="flex flex-wrap items-center gap-2 pt-1">
            <span className="text-xs text-gray-500 flex items-center gap-1">
              <Lightbulb className="w-3.5 h-3.5 text-amber-400/80" />
              <span>Try:</span>
            </span>
            {SAMPLE_PROMPTS.map((sample) => (
              <button
                key={sample}
                type="button"
                onClick={() => setPrompt(sample)}
                className="text-xs px-2.5 py-1 rounded-lg bg-background-hover text-gray-300 hover:text-brand-300 hover:bg-brand-500/10 border border-background-border transition-colors truncate max-w-xs focus-visible:ring-2 focus-visible:ring-brand-400 focus:outline-hidden"
              >
                {sample}
              </button>
            ))}
          </div>

          {/* Size Slider & Controls */}
          <div className="pt-3 border-t border-background-border/40 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="w-full sm:w-72 space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-gray-300 flex items-center gap-1.5">
                  <Sliders className="w-3.5 h-3.5 text-brand-400" />
                  Playlist Size:
                </span>
                <span className="font-mono text-brand-300 font-bold bg-background-darker px-2 py-0.5 rounded border border-background-border">
                  {size} tracks
                </span>
              </div>
              <input
                type="range"
                min={1}
                max={50}
                value={size}
                onChange={(e) => setSize(Number(e.target.value))}
                aria-label="Playlist Size Slider"
                aria-valuemin={1}
                aria-valuemax={50}
                aria-valuenow={size}
                className="w-full h-1.5 bg-background-darker accent-brand-400 rounded-full appearance-none cursor-pointer focus-visible:ring-2 focus-visible:ring-brand-400 focus:outline-hidden"
              />
              <div className="flex justify-between text-[10px] text-gray-600 font-mono">
                <span>1 track</span>
                <span>25 tracks</span>
                <span>50 tracks</span>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading || prompt.trim().length < 2}
              className="w-full sm:w-auto px-8 py-3 rounded-xl bg-brand-500 hover:bg-brand-400 text-background-darker font-bold text-sm shadow-xl shadow-brand-500/25 disabled:opacity-40 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2 active:scale-95 focus-visible:ring-2 focus-visible:ring-brand-400 focus:outline-hidden"
            >
              {isLoading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Synthesizing Intent & Ranking...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Generate Playlist</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Loading Skeleton */}
      {isLoading && (
        <div className="bg-background-card/50 border border-background-border rounded-2xl p-8 text-center space-y-4 animate-pulse">
          <div className="flex justify-center">
            <Sparkles className="w-10 h-10 text-brand-400 animate-spin" />
          </div>
          <h3 className="text-base font-semibold text-gray-200">
            Semantic Embedding & MMR Diversification in Progress...
          </h3>
          <p className="text-xs text-gray-400 max-w-md mx-auto">
            Extracting desired intent, applying negative lexical filters, calculating vector cosine similarity, and composing diversified track sequence.
          </p>
        </div>
      )}

      {/* Generated Playlist Display */}
      {playlist && !isLoading && (
        <PlaylistView playlist={playlist} generationMs={generationMs} />
      )}

      {/* Empty Initial State */}
      {!playlist && !isLoading && !isLibraryNotIndexed && (
        <div className="bg-background-card/30 border border-background-border/50 rounded-2xl p-12 text-center text-gray-500 space-y-3">
          <Music className="w-12 h-12 stroke-1 mx-auto opacity-30 text-brand-400" />
          <h3 className="text-sm font-semibold text-gray-400">Ready to discover music</h3>
          <p className="text-xs text-gray-600 max-w-sm mx-auto">
            Enter any prompt describing your desired mood, genre blend, or exclusions above to generate an intelligent playlist.
          </p>
        </div>
      )}
    </div>
  );
};
