import React, { useState } from 'react';
import {
  FolderSearch,
  HardDrive,
  Cpu,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  FolderOpen,
  AlertCircle,
  FileX,
  Layers,
} from 'lucide-react';
import { useLibraryScan } from '../../context/LibraryScanContext';

export const LibrarySetup: React.FC = () => {
  const {
    stats,
    isLoadingStats,
    activeJob,
    scanResult,
    errorSamples,
    isScanning,
    scanError,
    refreshStats,
    startScan,
    cancelScanning,
  } = useLibraryScan();

  const [folderPath, setFolderPath] = useState('/home/esscrimson/code/SoulSeek/songs_for_research');
  const [inputError, setInputError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!folderPath.trim()) {
      setInputError('Please enter an absolute folder path');
      return;
    }
    if (!folderPath.startsWith('/')) {
      setInputError('Path must be an absolute path starting with /');
      return;
    }
    setInputError(null);
    try {
      await startScan(folderPath.trim());
    } catch {
      // Handled in context
    }
  };

  const progressPercent = activeJob ? Math.round(activeJob.progress * 100) : 0;

  return (
    <div className="flex-1 flex flex-col h-full overflow-y-auto p-6 max-w-5xl mx-auto w-full space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-100 flex items-center gap-2">
            <FolderSearch className="w-6 h-6 text-brand-400" />
            <span>Library Setup & Ingestion</span>
          </h1>
          <p className="text-xs text-gray-400 mt-1">
            Scan your local music directories to index metadata and generate neural embeddings
          </p>
        </div>

        <button
          onClick={refreshStats}
          disabled={isLoadingStats}
          aria-label="Refresh library stats"
          className="px-3 py-2 bg-background-card border border-background-border hover:bg-background-hover focus-visible:ring-2 focus-visible:ring-brand-400 focus:outline-hidden text-gray-300 hover:text-white rounded-xl text-xs font-semibold transition-colors flex items-center gap-2"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoadingStats ? 'animate-spin' : ''}`} />
          <span>Refresh Stats</span>
        </button>
      </div>

      {/* Library Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4" data-testid="library-stats-grid">
        {/* Track Count */}
        <div className="bg-background-card border border-background-border rounded-2xl p-4 shadow-lg flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center text-brand-400 shrink-0">
            <HardDrive className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-gray-400 font-medium">Indexed Tracks</p>
            <p className="text-2xl font-bold text-gray-100 font-mono">
              {stats ? stats.track_count : '—'}
            </p>
          </div>
        </div>

        {/* Missing Files */}
        <div className="bg-background-card border border-background-border rounded-2xl p-4 shadow-lg flex items-center gap-4">
          <div className={`w-12 h-12 rounded-xl border flex items-center justify-center shrink-0 ${
            stats && stats.missing_count > 0
              ? 'bg-amber-500/10 border-amber-500/30 text-amber-400'
              : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
          }`}>
            <FileX className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-gray-400 font-medium">Missing Files</p>
            <p className="text-2xl font-bold text-gray-100 font-mono">
              {stats ? stats.missing_count : '—'}
            </p>
          </div>
        </div>

        {/* Root Count */}
        <div className="bg-background-card border border-background-border rounded-2xl p-4 shadow-lg flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 shrink-0">
            <Layers className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-gray-400 font-medium">Scan Roots</p>
            <p className="text-2xl font-bold text-gray-100 font-mono">
              {stats ? stats.root_count : '—'}
            </p>
          </div>
        </div>

        {/* Encoder ID */}
        <div className="bg-background-card border border-background-border rounded-2xl p-4 shadow-lg flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 shrink-0">
            <Cpu className="w-6 h-6" />
          </div>
          <div className="min-w-0">
            <p className="text-xs text-gray-400 font-medium">Active Encoder</p>
            <p className="text-xs font-mono font-bold text-purple-300 truncate" title={stats?.encoder_id || '—'}>
              {stats?.encoder_id || '—'}
            </p>
          </div>
        </div>
      </div>

      {/* Ingestion Trigger Form */}
      <div className="bg-background-card border border-background-border rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex items-center gap-2">
          <FolderOpen className="w-5 h-5 text-brand-400" />
          <h2 className="text-base font-bold text-gray-100">Scan Audio Directory</h2>
        </div>
        <p className="text-xs text-gray-400 leading-relaxed">
          Provide an absolute filesystem path containing your audio files (e.g. MP3, M4A, FLAC, OGG, WAV).
          The scanner will incrementally read tags, extract metadata, and generate embeddings.
        </p>
        <p className="text-xs text-amber-300/90 leading-relaxed">
          For the research corpus, select <span className="font-mono">songs_for_research</span> so its
          <span className="font-mono"> data/manifest.json</span> metadata is available.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4" aria-label="Library scan form">
          <div>
            <label htmlFor="folder-path-input" className="block text-xs font-semibold text-gray-300 mb-1.5">
              Absolute Directory Path
            </label>
            <div className="relative">
              <input
                id="folder-path-input"
                type="text"
                value={folderPath}
                onChange={(e) => setFolderPath(e.target.value)}
                placeholder="/home/user/Music"
                disabled={isScanning}
                aria-required="true"
                aria-invalid={!!inputError}
                aria-describedby={inputError ? 'path-error' : undefined}
                className="w-full bg-background-darker border border-background-border rounded-xl px-4 py-2.5 text-sm text-gray-100 font-mono placeholder-gray-600 focus-visible:ring-2 focus-visible:ring-brand-400 focus:outline-hidden transition-colors disabled:opacity-50"
              />
            </div>
            {inputError && (
              <p id="path-error" className="text-xs text-rose-400 mt-1.5 flex items-center gap-1">
                <AlertCircle className="w-3.5 h-3.5" />
                {inputError}
              </p>
            )}
          </div>

          {/* Quick preset buttons */}
          <div className="flex flex-wrap items-center gap-2 pt-1">
            <span className="text-xs text-gray-500">Quick path:</span>
            <button
              type="button"
              onClick={() => setFolderPath('/home/esscrimson/code/SoulSeek/songs_for_research')}
              className="text-xs font-mono px-2.5 py-1 rounded-lg bg-background-hover text-brand-300 hover:bg-brand-500/20 border border-background-border transition-colors focus-visible:ring-2 focus-visible:ring-brand-400 focus:outline-hidden"
            >
              songs_for_research
            </button>
          </div>

          <div className="flex items-center gap-3 pt-2">
            <button
              type="submit"
              disabled={isScanning}
              className="px-6 py-2.5 rounded-xl bg-brand-500 hover:bg-brand-400 text-background-darker font-bold text-sm shadow-lg shadow-brand-500/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2 focus-visible:ring-2 focus-visible:ring-brand-400 focus:outline-hidden"
            >
              {isScanning ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Scanning in Progress...</span>
                </>
              ) : (
                <>
                  <FolderSearch className="w-4 h-4" />
                  <span>Start Ingestion Scan</span>
                </>
              )}
            </button>

            {isScanning && (
              <button
                type="button"
                onClick={cancelScanning}
                className="px-4 py-2.5 rounded-xl bg-background-hover text-gray-300 hover:text-white text-xs font-semibold transition-colors focus-visible:ring-2 focus-visible:ring-brand-400 focus:outline-hidden"
              >
                Disconnect Polling
              </button>
            )}
          </div>
        </form>
      </div>

      {/* Active Scan Progress & Results Card */}
      {(isScanning || activeJob || scanError) && (
        <div className="bg-background-card border border-background-border rounded-2xl p-6 shadow-xl space-y-5 animate-fade-in" data-testid="scan-job-card">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              {activeJob?.status === 'succeeded' ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              ) : activeJob?.status === 'failed' ? (
                <AlertCircle className="w-5 h-5 text-rose-400" />
              ) : (
                <RefreshCw className="w-5 h-5 text-brand-400 animate-spin" />
              )}
              <h3 className="text-base font-bold text-gray-100">
                Scan Job Status
              </h3>
            </div>

            {activeJob && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500 font-mono">Job: {activeJob.id}</span>
                <span
                  className={`px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider ${
                    activeJob.status === 'succeeded'
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                      : activeJob.status === 'failed'
                      ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                      : 'bg-brand-500/20 text-brand-400 border border-brand-500/30'
                  }`}
                >
                  {activeJob.status}
                </span>
              </div>
            )}
          </div>

          {/* Phase & Progress Bar with ARIA */}
          {activeJob && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-400">
                  Phase: <span className="font-semibold text-brand-300 capitalize">{activeJob.phase || 'Queued'}</span>
                </span>
                <span className="font-mono text-gray-300 font-bold">{progressPercent}%</span>
              </div>

              {/* Progress element with proper role and ARIA attributes */}
              <div
                role="progressbar"
                aria-valuenow={progressPercent}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-label={`Scan progress: ${activeJob.phase}`}
                className="w-full h-2.5 bg-background-darker rounded-full overflow-hidden border border-background-border/50"
              >
                <div
                  className={`h-full transition-all duration-300 rounded-full ${
                    activeJob.status === 'failed'
                      ? 'bg-rose-500'
                      : activeJob.status === 'succeeded'
                      ? 'bg-emerald-500'
                      : 'bg-gradient-to-r from-brand-500 to-brand-300'
                  }`}
                  style={{ width: `${progressPercent}%` }}
                />
              </div>

              <p className="text-xs text-gray-300 pt-1 font-mono">{activeJob.message || 'Processing audio files...'}</p>
            </div>
          )}

          {/* Concrete Result Counters */}
          {scanResult && (
            <div className="pt-2 border-t border-background-border/40 space-y-3" data-testid="scan-counters">
              <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Scan Summary Counters
              </h4>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                <div className="p-2.5 bg-background-darker rounded-xl border border-background-border/50">
                  <span className="text-gray-400 block">Discovered</span>
                  <span className="font-mono font-bold text-gray-200 text-sm">{scanResult.discovered}</span>
                </div>
                <div className="p-2.5 bg-background-darker rounded-xl border border-background-border/50">
                  <span className="text-emerald-400 block">Added</span>
                  <span className="font-mono font-bold text-emerald-300 text-sm">{scanResult.added}</span>
                </div>
                <div className="p-2.5 bg-background-darker rounded-xl border border-background-border/50">
                  <span className="text-indigo-400 block">Updated</span>
                  <span className="font-mono font-bold text-indigo-300 text-sm">{scanResult.updated}</span>
                </div>
                <div className="p-2.5 bg-background-darker rounded-xl border border-background-border/50">
                  <span className="text-gray-400 block">Unchanged</span>
                  <span className="font-mono font-bold text-gray-300 text-sm">{scanResult.unchanged}</span>
                </div>
                <div className="p-2.5 bg-background-darker rounded-xl border border-background-border/50">
                  <span className="text-purple-400 block">Embedded</span>
                  <span className="font-mono font-bold text-purple-300 text-sm">{scanResult.embedded}</span>
                </div>
                <div className="p-2.5 bg-background-darker rounded-xl border border-background-border/50">
                  <span className="text-amber-400 block">Missing</span>
                  <span className="font-mono font-bold text-amber-300 text-sm">{scanResult.missing}</span>
                </div>
                <div className="p-2.5 bg-background-darker rounded-xl border border-background-border/50 sm:col-span-2">
                  <span className="text-rose-400 block">Errors</span>
                  <span className="font-mono font-bold text-rose-300 text-sm">{scanResult.errors}</span>
                </div>
              </div>
            </div>
          )}

          {/* Failed Job Error Display */}
          {scanError && (
            <div className="p-3.5 rounded-xl bg-rose-950/40 border border-rose-500/30 text-rose-300 text-xs flex items-start gap-2.5" data-testid="scan-error-banner">
              <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold">Scan Job Error</p>
                <p className="text-rose-200 mt-0.5">{scanError}</p>
                {activeJob?.error && typeof activeJob.error === 'object' && 'code' in activeJob.error && (
                  <p className="text-[11px] font-mono text-rose-400/80 mt-1">
                    Code: {String(activeJob.error.code)}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Sampled File Errors Display */}
          {errorSamples.length > 0 && (
            <div className="mt-4 p-4 rounded-xl bg-amber-950/30 border border-amber-500/30 space-y-2.5" data-testid="error-samples-section">
              <div className="flex items-center justify-between">
                <p className="text-xs font-bold text-amber-300 flex items-center gap-1.5">
                  <AlertTriangle className="w-4 h-4" />
                  <span>Sampled File Ingestion Errors ({errorSamples.length})</span>
                </p>
              </div>
              <div className="max-h-48 overflow-y-auto text-xs font-mono space-y-2 bg-black/40 p-3 rounded-lg border border-amber-500/20">
                {errorSamples.map((sample, i) => (
                  <div key={i} className="space-y-0.5 border-b border-amber-500/10 pb-1.5 last:border-b-0 last:pb-0">
                    <p className="text-amber-300 font-semibold truncate" title={sample.path}>
                      📄 {sample.path}
                    </p>
                    <p className="text-amber-200/80 text-[11px] pl-4">
                      ↳ {sample.message}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
