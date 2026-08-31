import React, { useState, useEffect, useCallback, useTransition } from 'react';
import { Search, ChevronLeft, ChevronRight, RefreshCw, FolderPlus, Music } from 'lucide-react';
import { api, Track } from '../../api';
import { TrackRow } from './TrackRow';
import { useNotification } from '../../context/NotificationContext';

interface TrackBrowserProps {
  onNavigateToSetup: () => void;
}

export const TrackBrowser: React.FC<TrackBrowserProps> = ({ onNavigateToSetup }) => {
  const [tracks, setTracks] = useState<Track[]>([]);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [total, setTotal] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [, startTransition] = useTransition();
  const { showError } = useNotification();

  const fetchTracks = useCallback(
    async (currentPage: number, query: string, size: number) => {
      setIsLoading(true);
      try {
        const response = await api.listTracks({
          page: currentPage,
          pageSize: size,
          search: query || undefined,
        });
        setTracks(response.items);
        setTotal(response.total);
        setPage(response.page);
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Failed to fetch tracks';
        showError('Library Error', msg);
      } finally {
        setIsLoading(false);
      }
    },
    [showError]
  );

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      startTransition(() => {
        fetchTracks(page, searchQuery, pageSize);
      });
    }, 300);

    return () => clearTimeout(timer);
  }, [page, searchQuery, pageSize, fetchTracks]);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
    setPage(1); // Reset to page 1 on new search
  };

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden p-6 max-w-7xl mx-auto w-full">
      {/* Header & Search Bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-100 flex items-center gap-2">
            <span>Music Library</span>
            <span className="text-xs font-mono font-normal bg-background-card border border-background-border text-gray-400 px-2.5 py-1 rounded-full">
              {total} {total === 1 ? 'track' : 'tracks'}
            </span>
          </h1>
          <p className="text-xs text-gray-400 mt-1">
            Browse, search, and queue tracks from your indexed local collection
          </p>
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto">
          {/* Search Box */}
          <div className="relative flex-1 sm:w-80">
            <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={handleSearchChange}
              placeholder="Search by title, artist, album, or genre..."
              aria-label="Search music library"
              className="w-full bg-background-card border border-background-border rounded-xl pl-10 pr-4 py-2 text-sm text-gray-100 placeholder-gray-500 focus-visible:ring-2 focus-visible:ring-brand-400 focus:outline-hidden transition-colors"
            />
            {isLoading && (
              <RefreshCw className="w-4 h-4 text-brand-400 animate-spin absolute right-3.5 top-1/2 -translate-y-1/2" />
            )}
          </div>

          <button
            onClick={() => fetchTracks(page, searchQuery, pageSize)}
            title="Refresh tracks"
            aria-label="Refresh track list"
            className="p-2 bg-background-card border border-background-border hover:bg-background-hover text-gray-300 hover:text-white rounded-xl transition-colors shrink-0 focus-visible:ring-2 focus-visible:ring-brand-400 focus:outline-hidden"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Tracks Table Container */}
      <div className="flex-1 bg-background-card/60 border border-background-border rounded-2xl overflow-hidden flex flex-col shadow-xl">
        <div className="flex-1 overflow-y-auto">
          {isLoading && tracks.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-gray-400 gap-3">
              <RefreshCw className="w-8 h-8 animate-spin text-brand-400" />
              <p className="text-sm">Loading music library...</p>
            </div>
          ) : tracks.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-center p-8">
              <Music className="w-12 h-12 text-gray-600 mb-3 stroke-1" />
              <h3 className="text-base font-semibold text-gray-300">
                {searchQuery ? 'No matching tracks found' : 'No tracks indexed yet'}
              </h3>
              <p className="text-xs text-gray-500 max-w-sm mt-1 mb-4">
                {searchQuery
                  ? `No tracks found matching "${searchQuery}". Try a different keyword.`
                  : 'Your music library is currently empty. Run a scan to index your local audio files.'}
              </p>
              {!searchQuery && (
                <button
                  onClick={onNavigateToSetup}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-brand-500 hover:bg-brand-400 text-background-darker font-semibold text-xs shadow-lg transition-all focus-visible:ring-2 focus-visible:ring-brand-400 focus:outline-hidden"
                >
                  <FolderPlus className="w-4 h-4" />
                  <span>Go to Library Setup</span>
                </button>
              )}
            </div>
          ) : (
            <table className="w-full text-left border-collapse" data-testid="tracks-table">
              <thead>
                <tr className="border-b border-background-border text-[11px] font-semibold text-gray-400 uppercase tracking-wider bg-background-card/90 sticky top-0 z-10 backdrop-blur-xs">
                  <th className="py-3 px-3 w-12 text-center">#</th>
                  <th className="py-3 px-3">Title</th>
                  <th className="py-3 px-3 hidden md:table-cell">Artist</th>
                  <th className="py-3 px-3 hidden lg:table-cell">Album</th>
                  <th className="py-3 px-3 hidden sm:table-cell">Genre</th>
                  <th className="py-3 px-3 hidden xl:table-cell">Year</th>
                  <th className="py-3 px-3 text-right">Duration</th>
                  <th className="py-3 px-3 text-right w-16">Queue</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-background-border/20">
                {tracks.map((track, idx) => (
                  <TrackRow
                    key={track.id}
                    track={track}
                    index={(page - 1) * pageSize + idx}
                    allTracks={tracks}
                  />
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Pagination Footer */}
        {total > 0 && (
          <div className="py-3 px-6 border-t border-background-border bg-background-card/90 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-gray-400">
            <div className="flex items-center gap-2">
              <span>
                Showing <span className="font-mono text-gray-200">{(page - 1) * pageSize + 1}</span> to{' '}
                <span className="font-mono text-gray-200">
                  {Math.min(page * pageSize, total)}
                </span>{' '}
                of <span className="font-mono text-gray-200">{total}</span> tracks
              </span>
              <span className="text-gray-600">|</span>
              <label className="flex items-center gap-1.5">
                <span>Per page:</span>
                <select
                  value={pageSize}
                  onChange={(e) => {
                    setPageSize(Number(e.target.value));
                    setPage(1);
                  }}
                  aria-label="Tracks per page"
                  className="bg-background-hover border border-background-border text-gray-200 rounded-md px-2 py-0.5 text-xs focus-visible:ring-2 focus-visible:ring-brand-400 focus:outline-hidden"
                >
                  <option value={20}>20</option>
                  <option value={50}>50</option>
                  <option value={100}>100</option>
                </select>
              </label>
            </div>

            <div className="flex items-center gap-2">
              <span className="font-mono text-gray-300">
                Page {page} of {totalPages}
              </span>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1 || isLoading}
                  className="p-1.5 rounded-lg bg-background-hover border border-background-border text-gray-300 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors focus-visible:ring-2 focus-visible:ring-brand-400 focus:outline-hidden"
                  aria-label="Previous Page"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages || isLoading}
                  className="p-1.5 rounded-lg bg-background-hover border border-background-border text-gray-300 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors focus-visible:ring-2 focus-visible:ring-brand-400 focus:outline-hidden"
                  aria-label="Next Page"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
